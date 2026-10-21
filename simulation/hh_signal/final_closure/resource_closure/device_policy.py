"""Pure, fail-closed review of complete administrator device/mount snapshots.

No inventory query, device open, ioctl, format, mount or authorization occurs.
Inputs are UNATTESTED even when internally consistent; policy success never
authorizes an operation. A later acquisition/helper requires independent review.
"""
from __future__ import annotations
import hashlib
import json
import os
import posixpath
import re
from .mount_attestation import parse_mountinfo

MAX_BYTES = 131072
MAX_NODES = 128
MM = re.compile(r'(0|[1-9][0-9]{0,9}):(0|[1-9][0-9]{0,9})\Z')
HEX = re.compile(r'[0-9a-f]{64}\Z')


class PolicyError(ValueError):
    pass


def need(ok, reason):
    if not ok:
        raise PolicyError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode()


def text(value, maximum=256):
    return (type(value) is str and 0 < len(value) <= maximum and
            all(32 <= ord(c) < 127 for c in value))


def integer(value, minimum=0):
    return type(value) is int and minimum <= value < 2**63


def path(value):
    return (text(value, 512) and value.startswith('/') and not value.startswith('//')
            and posixpath.normpath(value) == value and '\\' not in value)


def bounded(value):
    try:
        raw = canonical(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise PolicyError('INVALID_SNAPSHOT_JSON') from error
    need(len(raw) <= MAX_BYTES, 'SNAPSHOT_BOUND')
    return hashlib.sha256(raw).hexdigest()


def same(left, right):
    """JSON type-sensitive equality; bool/float are not integer identities."""
    return canonical(left) == canonical(right)


def result(kind, digest, **fields):
    return dict(status=kind, snapshot_sha256=digest,
                evidence_origin='UNATTESTED_INPUT_CONSISTENCY_ONLY',
                operation_authorized=False, runtime_verified=False,
                FULL_LAUNCH_ENVELOPE_VERIFIED=False, **fields)


def _unique(values, predicate, reason):
    need(type(values) is list and len(values) <= MAX_NODES and
         all(predicate(x) for x in values) and len(set(values)) == len(values), reason)
    return set(values)


def review_device(snapshot, contract):
    digest = bounded({'snapshot': snapshot, 'contract': contract})
    need(type(snapshot) is dict and type(contract) is dict, 'OBJECT_REQUIRED')
    need(snapshot.get('schema') == 'DEVICE_GRAPH_REVIEW_V1' and
         snapshot.get('complete') is True and
         snapshot.get('host_mapping_complete') is True and
         snapshot.get('all_mount_namespaces_complete') is True,
         'INCOMPLETE_GRAPH_OR_NAMESPACE_INVENTORY')
    ns = snapshot.get('namespace')
    need(type(ns) is dict and set(ns) == {'dev', 'inode', 'boot_id', 'collector_start_ns'} and
         all(integer(ns[k], 1) for k in ('dev', 'inode', 'collector_start_ns')) and
         text(ns['boot_id']), 'DEVICE_NAMESPACE_ANCHOR_REQUIRED')
    nodes = snapshot.get('nodes')
    need(type(nodes) is list and 0 < len(nodes) <= MAX_NODES, 'NODE_BOUND')
    graph = {}
    node_fields = {'id', 'diskseq', 'devpath', 'kind', 'parent', 'holders', 'slaves',
                   'by_ids', 'serial', 'wwn', 'bytes', 'host_id', 'host_ancestors',
                   'thin', 'sparse', 'snapshot', 'expandable', 'mount_refs',
                   'raw_uid', 'raw_gid', 'raw_mode'}
    for node in nodes:
        need(type(node) is dict and set(node) == node_fields, 'NODE_FIELDS')
        identity = node['id']
        need(type(identity) is str and MM.fullmatch(identity) and
             identity not in graph, 'DEVICE_ID')
        need(integer(node['diskseq'], 1) and path(node['devpath']) and
             node['devpath'].startswith('/dev/') and integer(node['bytes'], 1),
             'DEVICE_INSTANCE_OR_SIZE')
        need(node['kind'] in ('disk', 'part', 'dm', 'loop'), 'UNKNOWN_DEVICE_KIND')
        need(node['parent'] is None or type(node['parent']) is str and
             MM.fullmatch(node['parent']), 'PARENT_ID')
        for field in ('holders', 'slaves'):
            _unique(node[field], lambda x: type(x) is str and bool(MM.fullmatch(x)),
                    'RELATION_IDS')
        _unique(node['by_ids'], lambda x: path(x) and x.startswith('/dev/disk/by-id/'),
                'BY_ID_PATHS')
        need(text(node['serial']) and text(node['wwn']) and text(node['host_id']),
             'MISSING_STABLE_IDENTITY')
        host_parents = _unique(node['host_ancestors'], text, 'HOST_ANCESTORS')
        need(node['host_id'] not in host_parents, 'SELF_HOST_ANCESTOR')
        for field in ('thin', 'sparse', 'snapshot', 'expandable'):
            need(type(node[field]) is bool, 'UNKNOWN_BACKING_PROPERTY')
        _unique(node['mount_refs'], lambda x: text(x, 512), 'MOUNT_REFERENCES')
        need(all(integer(node[f]) for f in ('raw_uid', 'raw_gid', 'raw_mode')),
             'RAW_DEVICE_METADATA')
        graph[identity] = node
    aliases = set()
    for node in graph.values():
        for alias in [node['devpath'], *node['by_ids']]:
            need(alias not in aliases, 'DEVICE_ALIAS_COLLISION')
            aliases.add(alias)
    edges = {identity: set() for identity in graph}
    for identity, node in graph.items():
        refs = set(node['holders']) | set(node['slaves'])
        if node['parent']:
            refs.add(node['parent'])
        need(identity not in refs and refs <= graph.keys(), 'DANGLING_OR_SELF_RELATION')
    for identity, node in graph.items():
        parent = node['parent']
        refs = set(node['holders']) | set(node['slaves']) | ({parent} if parent else set())
        need(identity not in refs and refs <= graph.keys(), 'DANGLING_OR_SELF_RELATION')
        for other in refs:
            edges[identity].add(other)
            edges[other].add(identity)
        for holder in node['holders']:
            need(identity in graph[holder]['slaves'], 'NONRECIPROCAL_HOLDER')
        for slave in node['slaves']:
            need(identity in graph[slave]['holders'], 'NONRECIPROCAL_SLAVE')
        seen = {identity}
        cursor = parent
        while cursor:
            need(cursor not in seen, 'PARENT_CYCLE')
            seen.add(cursor)
            cursor = graph[cursor]['parent']
    for node in graph.values():
        if node['kind'] == 'part':
            need(node['parent'] is not None and graph[node['parent']]['kind'] == 'disk',
                 'PARTITION_PARENT_MISSING_OR_NONDISK')
        if node['kind'] == 'disk':
            need(node['parent'] is None, 'WHOLE_DISK_CANNOT_HAVE_PARTITION_PARENT')

    candidate = contract.get('candidate')
    need(type(candidate) is str and candidate in graph, 'CANDIDATE_ABSENT')
    protected = _unique(contract.get('protected_guest_ids'),
                        lambda x: type(x) is str and x in graph, 'PROTECTED_INVENTORY')
    need(contract.get('protected_inventory_complete') is True and
         contract.get('root_guest_id') in protected and protected,
         'ROOT_OR_HISTORICAL_INVENTORY_INCOMPLETE')

    def component(start):
        reached, pending = set(), [start]
        while pending:
            current = pending.pop()
            if current not in reached:
                reached.add(current)
                pending.extend(edges[current] - reached)
        return reached

    members = component(candidate)
    forbidden = set().union(*(component(p) for p in protected))
    need(not members & forbidden, 'ROOT_OR_PROTECTED_TOPOLOGY_INTERSECTION')
    need(all(graph[x]['kind'] == 'disk' for x in members) and len(members) == 1,
         'STACKED_PARTITION_DM_LOOP_OR_DEPENDENT_DEVICE_UNSUPPORTED')
    node = graph[candidate]
    host = {node['host_id'], *node['host_ancestors']}
    protected_host = _unique(contract.get('protected_host_ids'), text,
                             'PROTECTED_HOST_INVENTORY')
    need(protected_host and contract.get('protected_host_inventory_complete') is True,
         'PROTECTED_HOST_INCOMPLETE')
    for identity in forbidden:
        other = graph[identity]
        protected_host |= {other['host_id'], *other['host_ancestors']}
    need(not host & protected_host, 'PROTECTED_HOST_BACKING_INTERSECTION')
    need(not any(node[f] for f in ('thin', 'sparse', 'snapshot', 'expandable')),
         'GROWABLE_OR_UNBOUNDED_BACKING')
    need(not node['mount_refs'], 'CANDIDATE_REFERENCED_BY_MOUNT')
    expected = contract.get('expected')
    need(type(expected) is dict and set(expected) ==
         {'diskseq', 'bytes', 'host_id', 'serial', 'wwn', 'by_id'}, 'EXPECTED_IDENTITY')
    need(all(node[k] == expected[k] and type(node[k]) is type(expected[k])
             for k in ('diskseq', 'bytes', 'host_id', 'serial', 'wwn')),
         'EXPECTED_IDENTITY_MISMATCH')
    need(expected['by_id'] in node['by_ids'], 'GUEST_BY_ID_MISMATCH')
    need((node['raw_uid'], node['raw_gid'], node['raw_mode']) == (0, 0, 0o600),
         'RAW_DEVICE_ACCESS_POLICY')
    provenance = contract.get('disposable_provisioning_receipt_sha256')
    need(type(provenance) is str and HEX.fullmatch(provenance),
         'DISPOSABLE_PROVENANCE_REQUIRED_SIGNATURES_ARE_NOT_PROVENANCE')
    return result('PASS_DEVICE_GRAPH_POLICY_ONLY', digest,
                  related_guest_ids=sorted(members), host_ids=sorted(host),
                  protected_guest_ids=sorted(forbidden),
                  privileged_consumer='NOT_IMPLEMENTED_REVIEWED_FD_HELPER_REQUIRED')


def review_mount(snapshot, contract):
    digest = bounded({'snapshot': snapshot, 'contract': contract})
    need(type(snapshot) is dict and type(contract) is dict, 'OBJECT_REQUIRED')
    need(snapshot.get('schema') == 'MOUNT_TARGET_REVIEW_V1' and
         snapshot.get('complete') is True and snapshot.get('other_jobs_complete') is True,
         'INCOMPLETE_MOUNT_SNAPSHOT')
    ns = contract.get('namespace')
    need(type(ns) is dict and set(ns) == {'dev', 'inode', 'boot_id', 'collector_start_ns'} and
         all(integer(ns[k], 1) for k in ('dev', 'inode', 'collector_start_ns')) and
         text(ns['boot_id']), 'NAMESPACE_CONTRACT')
    need(same(snapshot.get('namespace_before'), ns) and
         same(snapshot.get('namespace_after'), ns),
         'NAMESPACE_CHANGED_OR_UNBOUND')
    target = contract.get('mountpoint')
    need(path(target) and target != '/' and target.startswith('/srv/atlas-hh/'),
         'NONCANONICAL_OR_UNREVIEWED_MOUNTPOINT')
    raw = snapshot.get('mountinfo')
    need(type(raw) is str, 'MOUNTINFO_REQUIRED')
    try:
        rows = parse_mountinfo(raw.encode('utf-8'))
    except ValueError as error:
        raise PolicyError('MOUNTINFO_REJECTED:' + str(error)) from error
    need(not any(x['path'] == target or x['path'].startswith(target + '/') for x in rows),
         'EXISTING_LEAF_NESTED_OR_BIND_MOUNT')
    covering = [x for x in rows if target.startswith(x['path'].rstrip('/') + '/')]
    need(covering, 'NO_PARENT_MOUNT')
    parent_mount = max(covering, key=lambda x: len(x['path']))
    need(parent_mount['root'] == '/', 'BIND_ANCESTOR_UNSUPPORTED')
    expected_parent = contract.get('parent_mount')
    fields = ('id', 'dev', 'root', 'path', 'filesystem_type')
    need(type(expected_parent) is dict and set(expected_parent) == set(fields) and
         same(expected_parent, {f: parent_mount[f] for f in fields}), 'PARENT_FILESYSTEM_CHANGED')
    need(snapshot.get('findmnt_exact') == [] and snapshot.get('findmnt_nested') == [] and
         same(snapshot.get('findmnt_covering'), expected_parent),
         'FINDMNT_MOUNTINFO_DISAGREEMENT')
    paths, cursor = [], target
    while True:
        paths.append(cursor)
        if cursor == '/':
            break
        cursor = posixpath.dirname(cursor)
    observations = snapshot.get('path_before')
    need(type(observations) is list and len(observations) == len(paths) and
         same(observations, snapshot.get('path_after')), 'PATH_CHANGED_OR_INCOMPLETE')
    need([x.get('path') for x in observations if type(x) is dict] == list(reversed(paths)),
         'ANCESTOR_ORDER_OR_COVERAGE')
    for row in observations:
        need(set(row) == {'path', 'uid', 'gid', 'mode', 'dev', 'inode',
                          'is_directory', 'is_symlink', 'empty'}, 'PATH_FIELDS')
        need(row['is_directory'] is True and row['is_symlink'] is False and
             all(integer(row[k]) for k in ('uid', 'gid', 'mode', 'dev', 'inode')) and
             row['dev'] > 0 and row['inode'] > 0 and type(row['empty']) is bool,
             'UNKNOWN_PATH_METADATA')
        need(row['uid'] == 0 and row['gid'] == 0 and row['mode'] & 0o022 == 0,
             'ANCESTOR_OWNERSHIP_OR_WRITABLE')
        relevant = [m for m in rows if row['path'] == m['path'] or
                    row['path'].startswith(m['path'].rstrip('/') + '/')]
        need(relevant, 'PATH_MOUNT_BINDING')
        covering_row = max(relevant, key=lambda m: len(m['path']))
        need(row['dev'] == os.makedev(*map(int, covering_row['dev'].split(':'))),
             'PATH_DEVICE_MOUNTINFO_MISMATCH')
        if row['path'] == target:
            need(row['mode'] == 0o700 and row['empty'], 'LEAF_MODE_OR_CONTENTS')
    jobs = snapshot.get('other_job_mounts')
    need(type(jobs) is list and len(jobs) <= MAX_NODES, 'OTHER_JOBS_BOUND')
    for item in jobs:
        need(type(item) is dict and set(item) == {'path', 'job'} and
             path(item['path']) and text(item['job']), 'OTHER_JOB_FIELDS')
        ref = item['path']
        need(not (ref == target or ref.startswith(target + '/') or
                  target.startswith(ref.rstrip('/') + '/')), 'OTHER_JOB_PATH_REFERENCE')
    return result('PASS_MOUNT_TARGET_POLICY_ONLY', digest,
                  parent_mount=expected_parent, namespace=ns,
                  path_race_closed=False, privileged_mount_authorized=False)

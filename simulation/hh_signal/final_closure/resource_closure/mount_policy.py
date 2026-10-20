"""Independent pure policy decisions over a bounded mountinfo capture.

Only the existing grammar parser is shared. No inventory/allow decision from
mount_attestation is reused. Imports perform no file, proc, nsfs or device read.
load_policy is explicit and byte-pinned. All successful results describe data
predicates only; no JSON receipt authenticates a live kernel or grants approval.
"""
from __future__ import annotations

import hashlib
import json
import posixpath
import re
from pathlib import Path

from . import mount_attestation as grammar
from . import namespace_attestation

DEFAULT_POLICY_PATH = Path(__file__).resolve().parent / 'config/mount_policy.json'
POLICY_SHA256 = '51760a6b9eb7857ef0aa2a96a1e4812d9edc1bd103ec37376b22df7f8ff27713'
POLICY_SEMANTIC_SHA256 = '3d8702e9695d753daf18c3969c5438a855ee00ec44ec3cccd30032b7418a2681'
MAX_POLICY_BYTES = 16384
MAX_PROJECTION_BYTES = 16384


class PolicyError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def _plain(value, depth=0, budget=None):
    if budget is None:
        budget = [2048]
    budget[0] -= 1
    if depth > 32 or budget[0] < 0:
        return False
    if type(value) is dict:
        return len(value) <= 256 and all(type(k) is str and len(k) <= 2048 and
                                       _plain(v, depth + 1, budget) for k, v in value.items())
    if type(value) is list:
        return len(value) <= 256 and all(_plain(v, depth + 1, budget) for v in value)
    if type(value) is str:
        return len(value) <= 2048
    if type(value) is int:
        return -(2**64) < value < 2**64
    return type(value) in (bool, type(None))


def _reviewed(policy):
    return (type(policy) is dict and _plain(policy) and
            sha(canonical(policy)) == POLICY_SEMANTIC_SHA256)


def load_policy(*, raw=None, path=DEFAULT_POLICY_PATH):
    """Explicit bounded source read, or caller-supplied exact reviewed bytes.

    Neither import nor verify performs an implicit policy-file read. Keeping
    this loader separate also prevents patched proc fixtures from reading an
    unexpected JSON path. The returned dict is checked again by verify.
    """
    if raw is None:
        with Path(path).open('rb') as stream:
            raw = stream.read(MAX_POLICY_BYTES + 1)
    if type(raw) is not bytes or len(raw) > MAX_POLICY_BYTES or sha(raw) != POLICY_SHA256:
        raise PolicyError('P00_POLICY_BYTE_IDENTITY')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PolicyError('P00_DUPLICATE_POLICY_KEY')
            result[key] = value
        return result
    try:
        policy = json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
    except (UnicodeError, ValueError) as error:
        raise PolicyError('P00_INVALID_POLICY_JSON') from error
    if not _reviewed(policy):
        raise PolicyError('P00_POLICY_SEMANTIC_IDENTITY')
    return policy


def _inside(path, parent):
    return parent == '/' or path == parent or path.startswith(parent + '/')


def _ns_identity(proof):
    row = proof['namespaces']['mnt']
    return {key: row[key] for key in ('dev', 'inode')}


def _identity(value):
    return (type(value) is dict and set(value) == {'dev', 'inode'} and
            all(type(value[key]) is int and value[key] > 0 for key in value))


def _propagation(row):
    tags = {}
    for token in row['optional']:
        if token == 'unbindable':
            key, number = token, None
        elif re.fullmatch(r'(shared|master|propagate_from):[1-9][0-9]{0,9}', token):
            key, text = token.split(':')
            number = int(text)
            if number > 0xFFFFFFFF:
                return 'INVALID'
        else:
            return 'UNSUPPORTED'
        if key in tags:
            return 'INVALID'
        tags[key] = number
    if 'unbindable' in tags and len(tags) != 1:
        return 'INVALID'
    if 'propagate_from' in tags and 'master' not in tags:
        return 'INVALID'
    if 'shared' in tags:
        return 'SHARED_SLAVE' if 'master' in tags else 'SHARED'
    if 'master' in tags:
        return 'SLAVE'
    return 'UNBINDABLE' if 'unbindable' in tags else 'PRIVATE'


def classify(row, repo, policy):
    """Classification conveys no permission, even for exact kernel API paths."""
    path = row['path']
    if path in policy['private_tmpfs']:
        return 'private_tmpfs'
    if _inside(path, repo):
        return 'source'
    if any(_inside(path, root) for root in policy['kernel_api_prefixes']):
        return 'kernel_api'
    if (path in policy['user_runtime_wsl_exact'] or
            any(_inside(path, root) for root in policy['user_runtime_wsl_prefixes'])):
        return 'user_runtime_wsl'
    return 'persistent' if row['filesystem_type'] in policy['persistent_types'] else 'unknown'


def validate_private_facts(facts, row, cap, raw_sha256, namespace):
    """Validate numerical/snapshot bindings only, never provenance labels."""
    keys = {'schema', 'raw_sha256', 'mount_id', 'mount_namespace', 'statvfs'}
    if type(facts) is not dict or not _plain(facts) or set(facts) != keys:
        return False
    if (facts['schema'] != 'PHASE7I_PRIVATE_TMPFS_FACTS_V1' or
            facts['raw_sha256'] != raw_sha256 or
            type(facts['mount_id']) is not int or facts['mount_id'] != row['id'] or
            not _identity(facts['mount_namespace']) or facts['mount_namespace'] != namespace):
        return False
    vfs = facts['statvfs']
    fields = {'f_blocks', 'f_frsize', 'f_files', 'f_bfree', 'f_ffree', 'f_flag'}
    return (type(vfs) is dict and set(vfs) == fields and
            all(type(x) is int and x >= 0 for x in vfs.values()) and
            vfs['f_frsize'] > 0 and vfs['f_blocks'] * vfs['f_frsize'] == cap['bytes'] and
            vfs['f_files'] == cap['inodes'] and vfs['f_bfree'] <= vfs['f_blocks'] and
            vfs['f_ffree'] <= vfs['f_files'] and vfs['f_flag'] & 1 == 0 and
            vfs['f_flag'] & 14 == 14)


def validate_guard_probe(probe, *, policy, controller_pid):
    """Pure fixed-six-syscall schema validator; no runtime authentication."""
    if not _reviewed(policy) or not _plain(probe):
        return False
    expected = policy['denial_transcript']
    fields = {'schema', 'scope', 'status', 'pid', 'program_sha256', 'checks', 'all_denied',
              'host_write_or_device_access_tested', 'FULL_LAUNCH_ENVELOPE_VERIFIED'}
    if (type(probe) is not dict or set(probe) != fields or
            probe['schema'] != expected['probe_schema'] or probe['scope'] != 'VOLATILE_DIAGNOSTIC_ONLY' or
            probe['status'] != 'PASS_FIXED_INVALID_TARGET_DENIALS' or
            type(controller_pid) is not int or controller_pid <= 0 or
            type(probe['pid']) is not int or probe['pid'] != controller_pid or
            probe['program_sha256'] != expected['program_sha256'] or probe['all_denied'] is not True or
            probe['host_write_or_device_access_tested'] is not False or
            probe['FULL_LAUNCH_ENVELOPE_VERIFIED'] is not False):
        return False
    rows = probe['checks']
    expected = expected['cases']
    if type(rows) is not list or len(rows) != len(expected):
        return False
    observed = set()
    for row in rows:
        if (type(row) is not dict or set(row) != {'case_id', 'syscall', 'target', 'return_code', 'errno'} or
                type(row['case_id']) is not str or row['case_id'] not in expected or row['case_id'] in observed):
            return False
        case = expected[row['case_id']]
        if (row['syscall'] != case['syscall'] or row['target'] != case['target'] or
                type(row['return_code']) is not int or row['return_code'] != -1 or
                type(row['errno']) is not int or row['errno'] != 1):
            return False
        observed.add(row['case_id'])
    return observed == set(expected)


def validate_denial_transcript(value, *, policy, raw_sha256, namespace_proof,
                               mount_ids, source_revision, controller_pid):
    """Exact source-level receipt schema; cannot prove any call actually ran.

    A reviewed source producer exists, pending separately authorized live
    validation. Its probes use invalid targets only; they do not test proc
    writes or real devices. JSON cannot authenticate the calls' physical origin.
    """
    keys = {'schema', 'raw_sha256', 'source_revision', 'mount_namespace',
            'namespace_proof_sha256', 'mount_ids', 'collector_source_sha256', 'probe'}
    if (not _reviewed(policy) or not _plain(namespace_proof) or
            type(value) is not dict or set(value) != keys or not _plain(value)):
        return False
    try:
        namespace_attestation.validate(namespace_proof)
    except (ValueError, KeyError, TypeError, AttributeError):
        return False
    if (type(source_revision) is not str or not re.fullmatch(r'[0-9a-f]{40}', source_revision) or
            value['schema'] != policy['denial_transcript']['schema'] or
            value['raw_sha256'] != raw_sha256 or value['source_revision'] != source_revision or
            not _identity(value['mount_namespace']) or
            value['mount_namespace'] != _ns_identity(namespace_proof) or
            value['namespace_proof_sha256'] != sha(canonical(namespace_proof)) or
            type(value['mount_ids']) is not list or
            any(type(x) is not int for x in value['mount_ids']) or
            value['mount_ids'] != sorted(mount_ids) or
            value['collector_source_sha256'] != policy['denial_transcript']['producer_source_sha256']):
        return False
    return validate_guard_probe(value['probe'], policy=policy, controller_pid=controller_pid)


def verify(raw, repo, *, policy, capture_complete=True, namespace_proof=None,
           private_facts=None, kernel_api_transcript=None, source_revision=None, controller_pid=None):
    """Independently apply every reviewed rule; perform no implicit reads.

    A source-predicate PASS is neither runtime proof nor persistent capacity.
    namespace_proof/private_facts/denial data are caller-supplied observations;
    this pure function cannot authenticate their physical origin.
    """
    result = {'schema': 'PHASE7I_CLASSIFIED_MOUNT_VERIFICATION_V1',
              'policy_sha256': POLICY_SHA256, 'status': 'FAIL_POLICY',
              'capture_complete': (capture_complete is True and type(raw) is bytes and
                                   len(raw) <= 16384 and raw.endswith(b'\n') and
                                   grammar.OVERFLOW_MARKER not in raw),
              'raw_sha256': sha(raw[:16384]) if type(raw) is bytes else None,
              'mounts': [], 'violations': [], 'projection_complete': True,
              'runtime_status': 'NOT_EXECUTED_OR_UNVERIFIED',
              'kernel_api_runtime': 'UNKNOWN_PRODUCER_NOT_LIVE_VALIDATED',
              'denial_transcript_validates_data_only': True,
              'collector_implemented': True,
              'collector_live_validated': False,
              'persistent_hard_capacity_verified': False,
              'source_content_identity_check_required': True,
              'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED': False,
              'FULL_LAUNCH_ENVELOPE_VERIFIED': False}
    failures = []
    def issue(rule, code, mount_id=None, missing=False):
        failures.append({'rule': rule, 'code': code, 'mount_id': mount_id,
                         'disposition': 'BLOCKED' if missing else 'FAIL'})
    def finish():
        if len(failures) > 32 or len(canonical(result | {'violations': failures})) > MAX_PROJECTION_BYTES:
            result['projection_complete'] = False
            result['mount_rows_omitted'] = len(result['mounts'])
            result['violation_rows_omitted'] = len(failures)
            result['mounts'] = []
            failures[:] = [{'rule': 'P09', 'code': 'SAFE_PROJECTION_BOUND_EXCEEDED',
                            'mount_id': None, 'disposition': 'FAIL'}]
        result['violations'] = failures
        result['status'] = ('FAIL_POLICY' if any(x['disposition'] == 'FAIL' for x in failures)
                            else 'BLOCKED_REQUIRED_EVIDENCE' if failures
                            else 'PASS_SOURCE_POLICY_PREREQUISITES')
        return result
    if not _reviewed(policy):
        issue('P00', 'UNREVIEWED_OR_MUTATED_POLICY')
        return finish()
    if (type(raw) is not bytes or type(capture_complete) is not bool or not capture_complete or
            not raw.endswith(b'\n')):
        issue('P01', 'INCOMPLETE_OR_NON_LF_CAPTURE')
        return finish()
    try:
        rows = grammar.parse_mountinfo(raw)
    except grammar.MountInfoError as error:
        issue('P01', str(error))
        return finish()
    repo = str(repo)
    if (not repo.startswith('/') or repo.startswith('//') or posixpath.normpath(repo) != repo or
            any(ord(x) < 32 for x in repo)):
        issue('P04', 'CANONICAL_SOURCE_PATH_REQUIRED')
        return finish()
    if any(_inside(repo, path) or _inside(path, repo) for path in policy['private_tmpfs']):
        issue('P04', 'SOURCE_AND_PRIVATE_TMPFS_OVERLAP')
    root_rows = [row for row in rows if row['path'] == '/']
    if len(root_rows) != 1:
        issue('P02', 'EXACT_VISIBLE_ROOT_REQUIRED')
        return finish()
    root_id = root_rows[0]['id']
    by_id = {row['id']: row for row in rows}
    # Parent may be outside a chroot/mount namespace only for its visible root.
    for row in rows:
        current, seen = row, set()
        while current['id'] != root_id:
            if current['id'] in seen:
                issue('P02', 'MOUNT_GRAPH_CYCLE', row['id'])
                break
            seen.add(current['id'])
            if current['parent'] not in by_id:
                issue('P02', 'NONROOT_PARENT_OUTSIDE_CAPTURE', row['id'])
                break
            current = by_id[current['parent']]
        if row['id'] == root_id:
            if row['parent'] in by_id and row['parent'] != root_id:
                issue('P02', 'VISIBLE_ROOT_PARENT_CYCLE', row['id'])
        else:
            covering = [item for item in rows if item['id'] != row['id'] and _inside(row['path'], item['path'])]
            parent = max(covering, key=lambda item: len(item['path']))
            if parent['id'] != row['parent']:
                issue('P02', 'HIDDEN_OR_OVERRIDDEN_MOUNT_GRAPH', row['id'])
    ns = None
    if namespace_proof is None or (type(namespace_proof) is dict and
            (namespace_proof.get('status') != 'PASS_READONLY_NAMESPACE_IDENTITY' or
             namespace_proof.get('readback_complete') is not True)):
        issue('P07', 'NAMESPACE_EVIDENCE_MISSING_OR_UNKNOWN', missing=True)
    else:
        try:
            if not _plain(namespace_proof):
                raise ValueError('BOUNDED_NAMESPACE_DATA_REQUIRED')
            namespace_attestation.validate(namespace_proof)
            ns = _ns_identity(namespace_proof)
        except (ValueError, KeyError, TypeError, AttributeError):
            issue('P07', 'NAMESPACE_EVIDENCE_INVALID')
    if private_facts is None:
        private_facts = {}
    elif type(private_facts) is not dict or len(private_facts) > 2 or not _plain(private_facts):
        issue('P03', 'UNBOUNDED_OR_EXCESS_PRIVATE_READBACK')
        private_facts = {}
    seen_private, api_ids = set(), []
    counts = {name: 0 for name in ('private_tmpfs', 'source', 'kernel_api', 'user_runtime_wsl', 'persistent', 'unknown')}
    for row in rows:
        group = classify(row, repo, policy)
        counts[group] += 1
        state = _propagation(row)
        result['mounts'].append({'id': row['id'], 'parent': row['parent'], 'class': group,
                                 'path_sha256': sha(row['path'].encode()),
                                 'mount_ro': 'ro' in row['mount_options'], 'propagation': state})
        if state not in ('PRIVATE', 'UNBINDABLE'):
            issue('P05', 'UNCONTAINED_OR_UNKNOWN_PROPAGATION:' + state, row['id'])
        if group == 'private_tmpfs':
            seen_private.add(row['path'])
            identity = policy['private_identity']
            if (row['filesystem_type'] != identity['filesystem_type'] or row['root'] != identity['root'] or
                    row['source'] != identity['source'] or not row['dev'].startswith('0:') or
                    not set(identity['mount_flags']) <= set(row['mount_options']) or
                    'rw' not in row['superblock_options']):
                issue('P03', 'PRIVATE_TMPFS_IDENTITY_OR_FLAGS', row['id'])
            if row['path'] not in private_facts or ns is None:
                issue('P03', 'PRIVATE_TMPFS_BOUND_READBACK_REQUIRED', row['id'], missing=True)
            elif not validate_private_facts(private_facts[row['path']], row, policy['private_tmpfs'][row['path']],
                                            result['raw_sha256'], ns):
                issue('P03', 'PRIVATE_TMPFS_BOUND_READBACK_INVALID', row['id'])
        elif 'rw' in row['mount_options']:
            issue('P06', 'NONPRIVATE_WRITABLE_MOUNT', row['id'])
        if group == 'source' and row['path'] != repo:
            issue('P04', 'UNREVIEWED_SOURCE_SUBTREE_OVERMOUNT', row['id'])
        if any(row['path'] != path and _inside(row['path'], path) for path in policy['private_tmpfs']):
            issue('P04', 'PRIVATE_TMPFS_SUBTREE_OVERMOUNT', row['id'])
        if group == 'kernel_api':
            api_ids.append(row['id'])
            expected = policy['kernel_api_roots'].get(row['path'])
            if (expected is None or row['filesystem_type'] not in expected['types'] or
                    row['root'] not in expected['roots'] or row['source'] not in expected['sources']):
                issue('P07', 'UNREVIEWED_KERNEL_API_MOUNT_IDENTITY', row['id'])
    result['class_counts'] = counts
    for path in policy['private_tmpfs']:
        if path not in seen_private:
            issue('P03', 'EXACT_PRIVATE_TMPFS_REQUIRED:' + path)
    if set(private_facts) - set(policy['private_tmpfs']):
        issue('P03', 'UNREVIEWED_EXTRA_PRIVATE_READBACK')
    covering = [row for row in rows if _inside(repo, row['path'])]
    source_mount = max(covering, key=lambda row: len(row['path']))
    result['source_covering_mount_id'] = source_mount['id']
    if 'ro' not in source_mount['mount_options']:
        issue('P04', 'SOURCE_COVERED_BY_WRITABLE_MOUNT', source_mount['id'])
    if api_ids:
        if kernel_api_transcript is None or ns is None or source_revision is None or controller_pid is None:
            issue('P08', 'KERNEL_API_DENIAL_TRANSCRIPT_OR_SOURCE_BINDING_REQUIRED', missing=True)
        elif not validate_denial_transcript(kernel_api_transcript, policy=policy,
                    raw_sha256=result['raw_sha256'], namespace_proof=namespace_proof,
                    mount_ids=api_ids, source_revision=source_revision, controller_pid=controller_pid):
            issue('P08', 'KERNEL_API_DENIAL_TRANSCRIPT_INVALID')
    else:
        result['kernel_api_runtime'] = 'NOT_PRESENT_IN_SUPPLIED_CAPTURE'
    return finish()

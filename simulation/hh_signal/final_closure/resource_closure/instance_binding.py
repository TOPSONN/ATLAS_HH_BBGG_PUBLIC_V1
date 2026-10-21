"""Review a proposed pinned-instance transaction; NEVER run privileged tools.

O_EXCL/flock/path rechecks are not a proof that all host writers are excluded.
The proposed helper must own the FD through use and consume that exact FD.
No such helper is deployed by this source. Existing path-reopening recipes
are categorically denied even after an internally consistent model review.
"""
import os
from .device_policy import need, bounded, integer, text, result, same, review_device, review_mount, HEX, parse_mountinfo

PHASES = ('acquire', 'before_operation', 'after_operation', 'before_release')
FIELDS = {'fd_number', 'st_dev', 'st_ino', 'st_rdev', 'diskseq', 'size_bytes',
          'host_instance', 'by_id_target', 'boot_id', 'namespace_inode',
          'helper_start_ns', 'lease_nonce'}


def review_transaction(records, plan):
    digest = bounded({'records': records, 'plan': plan})
    need(type(plan) is dict and type(records) is list and len(records) == 4,
         'TRANSACTION_SHAPE')
    need(plan.get('schema') == 'PINNED_DEVICE_HELPER_PROPOSAL_V1' and
         plan.get('consumer') == 'SAME_FD_IN_PROCESS_REVIEWED_HELPER',
         'PATH_REOPENING_OR_EXTERNAL_TOOL_CONSUMER_REJECTED')
    need(integer(plan.get('exact_size_bytes'), 4096), 'PLAN_SIZE')
    reviewed = review_device(plan.get('device_snapshot'), plan.get('device_contract'))
    mount_review = review_mount(plan.get('mount_snapshot'), plan.get('mount_contract'))
    need(same(plan['device_snapshot']['namespace'], mount_review['namespace']),
         'DEVICE_MOUNT_NAMESPACE_CONTRADICTION')
    mount_rows = parse_mountinfo(plan['mount_snapshot']['mountinfo'].encode('utf-8'))
    roots = [row for row in mount_rows if row['path'] == '/']
    need(len(roots) == 1 and roots[0]['dev'] == plan['device_contract']['root_guest_id'],
         'DEVICE_GRAPH_ROOT_MOUNT_CONTRADICTION')
    need(not any(row['dev'] in reviewed['related_guest_ids'] for row in mount_rows),
         'CANDIDATE_MOUNT_REFERENCE_CONTRADICTION')
    volatile = {'proc', 'sysfs', 'cgroup2', 'devtmpfs', 'devpts', 'tmpfs',
                'mqueue', 'securityfs', 'pstore', 'bpf', 'debugfs', 'tracefs',
                'configfs', 'fusectl', 'hugetlbfs', 'autofs', 'binfmt_misc',
                'nsfs', 'rpc_pipefs'}
    protected = set(plan['device_contract']['protected_guest_ids'])
    need(all(row['dev'] in protected or row['filesystem_type'] in volatile
             for row in mount_rows), 'MOUNTED_STORAGE_PROTECTED_INVENTORY_INCOMPLETE')
    need(type(plan.get('device_policy_sha256')) is str and
         HEX.fullmatch(plan['device_policy_sha256']) and
         plan['device_policy_sha256'] == reviewed['snapshot_sha256'], 'DEVICE_POLICY_BINDING')
    need(plan.get('mount_policy_sha256') == mount_review['snapshot_sha256'],
         'MOUNT_POLICY_BINDING')
    expected = plan.get('expected_identity')
    need(type(expected) is dict and set(expected) == FIELDS, 'REVIEWED_IDENTITY_REQUIRED')
    candidate = next(n for n in plan['device_snapshot']['nodes']
                     if n['id'] == plan['device_contract']['candidate'])
    need(expected['diskseq'] == candidate['diskseq'] and
         expected['st_rdev'] == os.makedev(*map(int, candidate['id'].split(':'))) and
         expected['by_id_target'] == candidate['devpath'] and
         expected['host_instance'] == candidate['host_id'] and
         expected['size_bytes'] == candidate['bytes'], 'REVIEWED_IDENTITY_DEVICE_MISMATCH')
    namespace = mount_review['namespace']
    need(type(expected['namespace_inode']) is int and
         expected['namespace_inode'] == namespace['inode'] and
         expected['boot_id'] == namespace['boot_id'] and
         integer(expected['helper_start_ns'], 1) and
         expected['helper_start_ns'] >= namespace['collector_start_ns'],
         'REVIEWED_IDENTITY_NAMESPACE_MISMATCH')
    need(plan.get('kernel_exclusive_claim_required') is True and
         plan.get('host_hotplug_exclusion_required') is True and
         plan.get('all_host_writers_excluded_required') is True,
         'EXCLUSIVITY_REQUIREMENTS_MISSING')
    need([r.get('phase') for r in records if type(r) is dict] == list(PHASES),
         'EXACT_TRANSACTION_ORDER')
    first, times = None, []
    for record in records:
        need(set(record) == {'phase', 'identity', 'monotonic_ns', 'fd_held',
                             'exclusive_claim_held', 'hotplug_exclusion_held'},
             'TRANSACTION_FIELDS')
        identity = record['identity']
        need(type(identity) is dict and set(identity) == FIELDS, 'IDENTITY_FIELDS')
        for key in ('fd_number', 'st_dev', 'st_ino', 'st_rdev', 'diskseq', 'size_bytes',
                    'namespace_inode', 'helper_start_ns'):
            need(integer(identity[key], 1 if key != 'fd_number' else 0), 'IDENTITY_NUMBER')
        need(all(text(identity[k], 512) for k in
                 ('host_instance', 'by_id_target', 'boot_id', 'lease_nonce')),
             'IDENTITY_TEXT')
        need(identity['size_bytes'] == plan.get('exact_size_bytes') and
             identity['host_instance'] == plan.get('expected_host_instance'),
             'PLAN_INSTANCE_MISMATCH')
        need(same(identity, expected), 'REVIEWED_IDENTITY_MISMATCH')
        need(record['fd_held'] is True and record['exclusive_claim_held'] is True and
             record['hotplug_exclusion_held'] is True, 'LEASE_GAP_OR_UNKNOWN')
        need(integer(record['monotonic_ns'], 1), 'CLOCK_VALUE')
        times.append(record['monotonic_ns'])
        if first is None:
            first = identity
        need(first == identity, 'DEVICE_INSTANCE_CHANGED_DESPITE_PATH_OR_MM')
    need(all(b > a for a, b in zip(times, times[1:])), 'REPLAY_OR_NONMONOTONIC_PHASE')
    need(first['helper_start_ns'] <= times[0], 'HELPER_START_AFTER_ACQUISITION')
    return result('PASS_PINNED_INSTANCE_MODEL_ONLY', digest,
                  TOCTOU_RUNTIME_CLOSED=False,
                  helper_implementation='NOT_DEPLOYED',
                  all_host_writer_exclusion='UNATTESTED',
                  actual_exclusive_open_or_operation=False)


def privileged_operation(*args, **kwargs):
    raise PermissionError('NOT_APPROVED_NO_PRIVILEGED_CONSUMER_IMPLEMENTED')

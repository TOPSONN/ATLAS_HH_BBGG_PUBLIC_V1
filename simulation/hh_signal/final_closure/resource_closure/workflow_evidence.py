"""Pure numerical receipt checks; JSON cannot establish execution or authorization.

No I/O, imports of executors, service calls, namespace operations or approval
objects. Even a well-formed runtime-labelled receipt never enables FULL flags.
Independent raw provenance and human authorization belong to separate gates.
All times are integer CLOCK_MONOTONIC nanoseconds; CPU usage is microseconds.
"""
from __future__ import annotations
import json
import re

PHASES = ('pre_provisioning', 'source_git_preflight', 'dependency_hashing',
          'worker_creation_monitoring', 'inert_build_preparation',
          'receipt_writing', 'postflight_validation', 'failure_cleanup')
LIMITS = {'cpu_usec': 4_000_000, 'wall_ns': 13_000_000_000,
          'memory_bytes': 536_870_912, 'swap_bytes': 0, 'disk_bytes': 16_777_216}
EVENTS = ('low', 'high', 'max', 'oom', 'oom_kill', 'oom_group_kill')
MAX_BYTES = 65_536
MAX_INTEGER = 2**63 - 1


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def integer(value, label, minimum=0):
    require(type(value) is int and minimum <= value <= MAX_INTEGER,
            'INVALID_INTEGER:' + label)
    return value


def keys(value, required, optional=()):
    require(type(value) is dict, 'OBJECT_REQUIRED')
    require(set(required) <= set(value) <= set(required) | set(optional),
            'MISSING_OR_EXTRA_FIELDS')


def _tree(value, depth=0, budget=None):
    if budget is None:
        budget = [0]
    budget[0] += 1
    require(depth <= 16 and budget[0] <= 4096, 'RECEIPT_STRUCTURE_BOUND')
    if type(value) is dict:
        require(len(value) <= 64 and all(type(k) is str and len(k) <= 96 for k in value),
                'RECEIPT_KEY_BOUND')
        for item in value.values():
            _tree(item, depth + 1, budget)
    elif type(value) is list:
        require(len(value) <= 64, 'RECEIPT_LIST_BOUND')
        for item in value:
            _tree(item, depth + 1, budget)
    elif type(value) is str:
        require(len(value) <= 4096 and '\x00' not in value, 'RECEIPT_STRING_BOUND')
    elif type(value) is int:
        integer(value, 'tree')
    else:
        require(value is None or type(value) is bool, 'NONINTEGER_OR_NONJSON_VALUE')


def loads(raw):
    """Strict bounded JSON loader, including duplicate-key/NaN/float rejection."""
    require(type(raw) is bytes and len(raw) <= MAX_BYTES, 'JSON_BYTE_BOUND')

    def pairs(rows):
        result = {}
        for name, value in rows:
            require(name not in result, 'DUPLICATE_JSON_KEY')
            result[name] = value
        return result

    def forbidden(value):
        raise ValueError('NONINTEGER_JSON_NUMBER:' + value)

    result = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
                        parse_float=forbidden, parse_constant=forbidden)
    _tree(result)
    return result


def _identity(receipt, expected):
    keys(expected, ('schema', 'source_revision', 'run_id', 'unit', 'aggregate_cgroup',
                    'controller_pid', 'child_pid', 'not_before_ns', 'not_after_ns', 'limits'))
    require(expected['schema'] == 'PHASE7I_WORKFLOW_EXPECTED_V1', 'EXPECTED_SCHEMA')
    require(type(expected['source_revision']) is str and
            re.fullmatch(r'[0-9a-f]{40}', expected['source_revision']), 'SOURCE_REVISION')
    require(type(expected['run_id']) is str and re.fullmatch(r'[0-9a-f]{32}', expected['run_id']),
            'RUN_ID')
    unit = expected['unit']
    require(type(unit) is str and re.fullmatch(r'atlas-hh-phase7i-[a-z0-9-]{1,80}\.service', unit),
            'UNIT_IDENTITY')
    cgroup = expected['aggregate_cgroup']
    pattern = (r'/user\.slice/user-([0-9]+)\.slice/user@\1\.service/app\.slice/' + re.escape(unit))
    require(type(cgroup) is str and re.fullmatch(pattern, cgroup), 'AGGREGATE_CGROUP_PATH')
    integer(expected['controller_pid'], 'controller_pid', 1)
    integer(expected['child_pid'], 'child_pid', 1)
    require(expected['controller_pid'] != expected['child_pid'], 'DISTINCT_CHILD_PID_REQUIRED')
    integer(expected['not_before_ns'], 'not_before_ns')
    integer(expected['not_after_ns'], 'not_after_ns')
    require(expected['not_after_ns'] > expected['not_before_ns'], 'FRESHNESS_WINDOW')
    require(type(expected['limits']) is dict and expected['limits'] == LIMITS and
            all(type(v) is int for v in expected['limits'].values()), 'FIXED_LIMITS_REQUIRED')
    for name in ('source_revision', 'run_id', 'unit'):
        require(receipt[name] == expected[name], 'STALE_OR_FOREIGN_IDENTITY:' + name)


def verify(receipt, expected):
    """Return numerical PASS/UNKNOWN/FAIL, always with runtime/full gates closed.

    ``None`` resource observations are missing measurements, never zero.
    Inputs are untrusted observations. ``PASS_NUMERICAL_AUDIT`` means only that
    supplied numbers and identities are internally consistent with the fixed
    fixture contract. It never proves they came from a real authorized run.
    """
    result = {'schema': 'PHASE7I_WORKFLOW_NUMERICAL_REVIEW_V1', 'status': 'FAIL',
              'errors': [], 'unknown': [], 'measurements': {
                  'aggregate_CPU_observed_lower_bound_usec': None,
                  'cumulative_CPU_max_observed_usec': None,
                  'CPU_activation_and_cleanup_covered': False,
                  'aggregate_wall_observed_ns': None,
                  'peak_RAM_observed_lower_bound_bytes': None,
                  'memory_peak_complete': False,
                  'max_observed_swap_current_bytes': None,
                  'allocated_disk_observed_bytes': None,
                  'nominal_CPU_rate_budget_usec': None},
              'cleanup': 'UNKNOWN',
              'runtime_acceptance': 'NOT_ESTABLISHED_BY_PURE_JSON_VERIFIER',
              'external_gates': ['RAW_EXECUTION_PROVENANCE', 'EXPLICIT_HUMAN_AUTHORIZATION',
                                 'MOUNT_NAMESPACE_AND_PERSISTENT_CAPACITY_PROOF',
                                 'REQUIRED_REAL_POSITIVE_NEGATIVE_TESTS'],
              'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED': False,
              'FULL_LAUNCH_ENVELOPE_VERIFIED': False}

    def unknown(reason):
        if reason not in result['unknown']:
            result['unknown'].append(reason)

    def number(value, name):
        if value is None:
            unknown('MISSING:' + name)
            return None
        return integer(value, name)

    def stamp(value, name):
        value = integer(value, name)
        require(expected['not_before_ns'] <= value <= expected['not_after_ns'],
                'STALE_OR_FUTURE_TIMESTAMP:' + name)
        return value

    def same_group(value):
        require(type(value) is str and value == expected['aggregate_cgroup'],
                'FOREIGN_OR_EXTRA_CGROUP_PATH')

    def pids(value):
        require(type(value) is list and len(value) <= 16, 'PID_LIST_BOUND')
        for value_pid in value:
            integer(value_pid, 'observed_pid', 1)
        require(len(value) == len(set(value)), 'DUPLICATE_PID')
        return value

    try:
        _tree(receipt)
        _tree(expected)
        require(len(json.dumps(receipt, separators=(',', ':'), allow_nan=False).encode()) <= MAX_BYTES,
                'RECEIPT_BYTE_BOUND')
        keys(receipt, ('schema', 'source_revision', 'run_id', 'unit', 'evidence_kind',
                       'receipt_complete', 'phases', 'members', 'timeline', 'observations',
                       'controller_final', 'manager_cleanup', 'disk'))
        require(receipt['schema'] == 'PHASE7I_WORKFLOW_EVIDENCE_V1', 'RECEIPT_SCHEMA')
        require(receipt['evidence_kind'] in ('SYNTHETIC', 'UNVERIFIED_RUNTIME'), 'EVIDENCE_KIND')
        result['evidence_kind'] = receipt['evidence_kind']
        require(type(receipt['receipt_complete']) is bool, 'RECEIPT_COMPLETE_BOOLEAN')
        if not receipt['receipt_complete']:
            unknown('INCOMPLETE_RECEIPT')
        _identity(receipt, expected)
        members = receipt['members']
        keys(members, ('controller', 'child'))
        for name in members:
            keys(members[name], ('pid', 'cgroup'))
            require(type(members[name]['pid']) is int and
                    members[name]['pid'] == expected[name + '_pid'], 'FOREIGN_MEMBER_PID')
            same_group(members[name]['cgroup'])
        timeline = receipt['timeline']
        keys(timeline, ('clock', 'activation_start_ns', 'main_entered_ns',
                        'main_exit_ns', 'cleanup_complete_ns'))
        require(timeline['clock'] == 'CLOCK_MONOTONIC_NS', 'CLOCK_OR_TIME_UNIT')
        times = [stamp(timeline[name], name) for name in
                 ('activation_start_ns', 'main_entered_ns', 'main_exit_ns', 'cleanup_complete_ns')]
        require(times == sorted(times) and times[0] < times[1] < times[2] <= times[3],
                'TIMELINE_ORDER')
        wall = times[3] - times[0]
        result['measurements']['aggregate_wall_observed_ns'] = wall
        require(wall <= LIMITS['wall_ns'], 'FULL_WALL_BUDGET_EXCEEDED')
        phases = receipt['phases']
        require(type(phases) is list and [x.get('name') if type(x) is dict else None
                                         for x in phases] == list(PHASES), 'EXACT_EIGHT_PHASE_SEQUENCE')
        previous = times[1]
        for phase in phases:
            keys(phase, ('name', 'start_ns', 'end_ns', 'aggregate_cgroup', 'completed'))
            same_group(phase['aggregate_cgroup'])
            start, end = stamp(phase['start_ns'], 'phase_start'), stamp(phase['end_ns'], 'phase_end')
            require(previous <= start <= end <= times[2], 'PHASE_OVERLAP_OR_OUTSIDE_MAIN')
            require(type(phase['completed']) is bool, 'PHASE_COMPLETION_BOOLEAN')
            if not phase['completed']:
                unknown('INCOMPLETE_PHASE:' + phase['name'])
            previous = end
        observations = receipt['observations']
        require(type(observations) is list and 2 <= len(observations) <= 64,
                'RESOURCE_OBSERVATION_BOUND')
        observation_fields = ('cpu_usage_usec', 'cpu_max', 'cpu_max_burst_usec', 'memory_max_bytes',
                              'memory_current_bytes', 'memory_peak_bytes', 'swap_max_bytes',
                              'swap_current_bytes', 'memory_events')
        cpu, peaks, swaps, event_rows, stamps = [], [], [], [], []
        for row in observations:
            keys(row, ('at_ns', 'aggregate_cgroup'), observation_fields)
            same_group(row['aggregate_cgroup'])
            at = stamp(row['at_ns'], 'resource_observation')
            require(times[0] <= at <= times[3], 'RESOURCE_OBSERVATION_OUTSIDE_JOB_WINDOW')
            require(not stamps or at > stamps[-1], 'NONMONOTONIC_RESOURCE_OBSERVATIONS')
            stamps.append(at)
            value = number(row.get('cpu_usage_usec'), 'cpu_usage_usec')
            if value is not None:
                result['measurements']['cumulative_CPU_max_observed_usec'] = max(
                    result['measurements']['cumulative_CPU_max_observed_usec'] or 0, value)
                require(value <= LIMITS['cpu_usec'], 'CUMULATIVE_CPU_USAGE_OVER_CAP')
                require(not cpu or value >= cpu[-1][1], 'CPU_COUNTER_RESET_OR_STALE')
                cpu.append((at, value))
            maximum = row.get('cpu_max')
            if maximum is None:
                unknown('MISSING:cpu_max')
            else:
                require(type(maximum) is str and maximum == '3000 10000', 'CPU_RATE_READBACK_MISMATCH')
            burst = number(row.get('cpu_max_burst_usec'), 'cpu_max_burst_usec')
            require(burst is None or burst == 0, 'CPU_BURST_READBACK_MISMATCH')
            memory_max = number(row.get('memory_max_bytes'), 'memory_max_bytes')
            require(memory_max is None or memory_max == LIMITS['memory_bytes'], 'MEMORY_MAX_MISMATCH')
            current = number(row.get('memory_current_bytes'), 'memory_current_bytes')
            require(current is None or current <= LIMITS['memory_bytes'], 'MEMORY_CURRENT_OVER_LIMIT')
            peak = number(row.get('memory_peak_bytes'), 'memory_peak_bytes')
            if peak is not None:
                require(peak <= LIMITS['memory_bytes'] and (current is None or peak >= current),
                        'MEMORY_PEAK_INVALID_OR_OVER_LIMIT')
                require(not peaks or peak >= peaks[-1], 'MEMORY_PEAK_RESET_OR_STALE')
                peaks.append(peak)
            swap_max = number(row.get('swap_max_bytes'), 'swap_max_bytes')
            require(swap_max is None or swap_max == 0, 'SWAP_MAX_MISMATCH')
            swap = number(row.get('swap_current_bytes'), 'swap_current_bytes')
            if swap is not None:
                require(swap == 0, 'SWAP_USAGE_OBSERVED')
                swaps.append(swap)
            events = row.get('memory_events')
            if events is None:
                unknown('MISSING:memory_events')
            else:
                keys(events, EVENTS)
                for name, count in events.items():
                    integer(count, 'memory.events.' + name)
                    require(not event_rows or count >= event_rows[-1][1][name],
                            'MEMORY_EVENT_COUNTER_RESET_OR_STALE')
                event_rows.append((at, events))
        if len(cpu) >= 2:
            delta = cpu[-1][1] - cpu[0][1]
            result['measurements']['aggregate_CPU_observed_lower_bound_usec'] = delta
            require(delta <= LIMITS['cpu_usec'], 'AGGREGATE_CPU_BUDGET_EXCEEDED')
        complete_cpu = len(cpu) == len(observations) and cpu[0][0] == times[0] and cpu[-1][0] == times[3]
        if not complete_cpu:
            unknown('CPU_ACTIVATION_OR_CLEANUP_COUNTER_MISSING')
        else:
            require(cpu[0][1] == 0, 'NONZERO_FRESH_CGROUP_BASELINE')
            result['measurements']['CPU_activation_and_cleanup_covered'] = True
        if stamps[0] != times[0] or stamps[-1] != times[3]:
            unknown('RESOURCE_BOUNDARY_COVERAGE_INCOMPLETE')
        result['measurements']['nominal_CPU_rate_budget_usec'] = (wall * 3000 + 9_999_999) // 10_000_000 + 3000
        result['CPU_rate_interpretation'] = 'NOMINAL_RATE_ARITHMETIC_ONLY_NOT_CUMULATIVE_HARD_ENFORCEMENT'
        result['measurements']['peak_RAM_observed_lower_bound_bytes'] = max(peaks) if peaks else None
        result['measurements']['memory_peak_complete'] = len(peaks) == len(observations)
        result['measurements']['max_observed_swap_current_bytes'] = max(swaps) if swaps else None
        if event_rows:
            if event_rows[0][0] == times[0]:
                require(not any(event_rows[0][1].values()), 'NONZERO_FRESH_MEMORY_EVENT_BASELINE')
            else:
                unknown('MEMORY_EVENT_ACTIVATION_BASELINE_MISSING')
            require(not any(event_rows[-1][1][k] for k in ('oom', 'oom_kill', 'oom_group_kill')),
                    'OOM_EVENT_IN_COMPLETED_WORKFLOW')
        final = receipt['controller_final']
        if final is None:
            unknown('CONTROLLER_FINAL_OBSERVATION_MISSING')
        else:
            keys(final, ('at_ns', 'aggregate_cgroup', 'controller_alive', 'cgroup_populated', 'pids'))
            same_group(final['aggregate_cgroup'])
            at = stamp(final['at_ns'], 'controller_final')
            require(previous <= at <= times[2] and final['controller_alive'] is True and
                    final['cgroup_populated'] is True and expected['controller_pid'] in pids(final['pids']),
                    'LIVE_CONTROLLER_CANNOT_CLAIM_EMPTY_OR_POSTMORTEM')
        cleanup = receipt['manager_cleanup']
        if cleanup is None:
            unknown('MANAGER_KERNEL_POSTMORTEM_CLEANUP_MISSING')
        else:
            keys(cleanup, ('at_ns', 'aggregate_cgroup', 'observer', 'controller_alive',
                           'cgroup_populated', 'pids'))
            same_group(cleanup['aggregate_cgroup'])
            require(cleanup['observer'] in ('systemd_manager', 'independent_kernel_observer'),
                    'INDEPENDENT_POSTMORTEM_OBSERVER_REQUIRED')
            require(stamp(cleanup['at_ns'], 'manager_cleanup') == times[3] and
                    cleanup['controller_alive'] is False and cleanup['cgroup_populated'] is False and
                    pids(cleanup['pids']) == [], 'RESIDUAL_OR_INCOMPLETE_POSTMORTEM_CLEANUP')
            result['cleanup'] = 'SUPPLIED_POSTMORTEM_RECEIPT_CONSISTENT_NOT_AUTHENTICATED'
        disk = receipt['disk']
        keys(disk, ('scope',), ('allocated_bytes', 'hard_limit_bytes', 'inode_count', 'inode_limit'))
        require(disk['scope'] in ('VOLATILE_ONLY', 'PERSISTENT_UNVERIFIED'), 'DISK_SCOPE')
        allocated = number(disk.get('allocated_bytes'), 'allocated_disk_bytes')
        disk_limit = number(disk.get('hard_limit_bytes'), 'disk_hard_limit_bytes')
        inode_count = number(disk.get('inode_count'), 'inode_count')
        inode_limit = number(disk.get('inode_limit'), 'inode_limit')
        require(allocated is None or allocated <= LIMITS['disk_bytes'], 'ALLOCATED_DISK_OVER_LIMIT')
        require(disk_limit is None or disk_limit <= LIMITS['disk_bytes'], 'DISK_BOUND_OVER_CONTRACT')
        require(allocated is None or disk_limit is None or allocated <= disk_limit, 'DISK_USAGE_OVER_BOUND')
        require(inode_count is None or inode_limit is None or inode_count <= inode_limit, 'INODE_USAGE_OVER_BOUND')
        result['measurements']['allocated_disk_observed_bytes'] = allocated
        result['persistent_capacity_acceptance'] = 'NOT_ESTABLISHED_BY_DECLARED_NUMBERS_OR_VOLATILE_SCOPE'
        result['status'] = 'UNKNOWN' if result['unknown'] else 'PASS_NUMERICAL_AUDIT'
    except (ValueError, KeyError, TypeError, UnicodeError, OverflowError) as error:
        result['errors'].append(str(error)[:512])
        result['status'] = 'FAIL'
    return result

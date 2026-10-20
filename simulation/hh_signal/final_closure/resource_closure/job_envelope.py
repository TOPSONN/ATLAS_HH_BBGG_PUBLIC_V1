"""Same-process early-stop proposal; no timer, kernel read or exit on import.

Future execution needs separate exact-source authorization. SIGALRM/Python can
be delayed, blocked or killed; this is NOT an atomic aggregate CPU kill or hard
real-time deadline. Main-origin excludes manager activation. A real manager
postmortem and capacity/accounting proof remain independent mandatory gates.

Primary semantics: Linux6.6 cgroup-v2 cpu.stat/memory.events/cgroup.events;
systemd255 org.freedesktop.systemd1 timestamps are microseconds, CPUUsageNSec
is nanoseconds; KillMode=control-group belongs to the manager, not this parser.
"""
from __future__ import annotations
import copy
import hashlib
import os
import re
import signal
import threading
import time

CPU_CAP_USEC = 4_000_000
CPU_STOP_USEC = 3_000_000
WALL_CAP_NS = 13_000_000_000
MAIN_STOP_NS = 10_000_000_000
RAM_CAP = 536_870_912
PERIOD_SECONDS = .01
MAX_INTEGER = 2**63 - 1
EVENTS = ('low', 'high', 'max', 'oom', 'oom_kill', 'oom_group_kill')
EFFECTIVE = {'cpu.max': '3000 10000', 'cpu.max.burst': '0',
             'memory.max': str(RAM_CAP), 'memory.swap.max': '0',
             'memory.oom.group': '1', 'pids.max': '16'}
RAW_NAMES = tuple(EFFECTIVE) + ('cpu.stat', 'memory.current', 'memory.peak',
    'memory.swap.current', 'memory.events', 'cgroup.events', 'cgroup.procs')
KIND = 'SAME_PROCESS_EARLY_STOP_NOT_ATOMIC_HARD_REALTIME'
_OWNER = None


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= MAX_INTEGER


def decimal(text, label):
    need(type(text) is str and re.fullmatch(r'[0-9]{1,19}', text) is not None,
         'INVALID_DECIMAL:' + label)
    value = int(text)
    need(integer(value), 'INTEGER_RANGE:' + label)
    return value


def identity(value):
    need(type(value) is dict and set(value) == {'dev', 'inode'} and
         all(integer(x, 1) for x in value.values()), 'CGROUP_IDENTITY_TYPE')
    return dict(value)


def group_path(value):
    need(type(value) is str and re.fullmatch(
        r'/sys/fs/cgroup/user\.slice/user-([0-9]+)\.slice/user@\1\.service/app\.slice/'
        r'atlas-hh-phase7i-[a-z0-9-]{1,80}\.service', value) is not None,
        'FIXED_AGGREGATE_PATH_REQUIRED')
    return value


def text(raw, label, cap=4096):
    need(type(raw) is bytes and 0 < len(raw) <= cap and raw.endswith(b'\n'),
         'BOUNDED_COMPLETE_KERNEL_TEXT:' + label)
    value = raw.decode('ascii', 'strict')
    need('\x00' not in value and '\r' not in value, 'KERNEL_TEXT_ENCODING:' + label)
    return value


def pairs(raw, label, required, allowed=None):
    result = {}
    for row in text(raw, label).splitlines():
        fields = row.split()
        need(len(fields) == 2 and fields[0] not in result, 'KERNEL_KEY_SHAPE:' + label)
        result[fields[0]] = decimal(fields[1], label)
    need(set(required) <= set(result) <= set(allowed or required), 'KERNEL_KEYS:' + label)
    return result


def parse_cgroup_raw(raw, *, aggregate_cgroup, cgroup_identity, reader_pid,
                     sample_start_ns, sample_end_ns):
    """Pure strict raw decoder, not evidence that a real kernel was queried."""
    group_path(aggregate_cgroup)
    identity(cgroup_identity)
    need(integer(reader_pid, 1) and integer(sample_start_ns) and integer(sample_end_ns) and
         sample_start_ns <= sample_end_ns, 'SAMPLE_IDENTITY_OR_CLOCK')
    need(type(raw) is dict and set(raw) == set(RAW_NAMES), 'EXACT_KERNEL_FILE_SET')
    for name, expected in EFFECTIVE.items():
        need(text(raw[name], name).strip() == expected, 'EFFECTIVE_LIMIT_MISMATCH:' + name)
    cpu = pairs(raw['cpu.stat'], 'cpu.stat', ('usage_usec', 'user_usec', 'system_usec'),
                ('usage_usec', 'user_usec', 'system_usec', 'nr_periods', 'nr_throttled',
                 'throttled_usec', 'nr_bursts', 'burst_usec',
                 'core_sched.force_idle_usec'))  # WSL6.6.87.2 rstat.c CONFIG_SCHED_CORE
    events = pairs(raw['memory.events'], 'memory.events', EVENTS)
    cg = pairs(raw['cgroup.events'], 'cgroup.events', ('populated', 'frozen'))
    need(cg['populated'] in (0, 1) and cg['frozen'] in (0, 1), 'CGROUP_EVENT_BOOLEAN')
    values = {}
    for name in ('memory.current', 'memory.peak', 'memory.swap.current'):
        if raw[name] is None and name == 'memory.peak':
            values[name] = None
        else:
            values[name] = decimal(text(raw[name], name).strip(), name)
    # An empty process file is a valid postmortem observation, not missing data.
    process_raw = raw['cgroup.procs']
    need(type(process_raw) is bytes and len(process_raw) <= 4096 and
         (not process_raw or process_raw.endswith(b'\n')), 'CGROUP_PROCESS_TEXT')
    pids = [decimal(row, 'cgroup.procs') for row in process_raw.decode('ascii').splitlines()]
    need(len(pids) <= 16 and all(x > 0 for x in pids) and len(pids) == len(set(pids)),
         'CGROUP_PROCESS_BOUND_OR_DUPLICATE')
    need(bool(pids) == bool(cg['populated']), 'CGROUP_POPULATED_PROCESS_CONTRADICTION')
    return {'schema': 'PHASE7I_JOB_KERNEL_SNAPSHOT_V1',
            'aggregate_cgroup': aggregate_cgroup, 'cgroup_identity': dict(cgroup_identity),
            'reader_pid': reader_pid, 'sample_start_ns': sample_start_ns,
            'sample_end_ns': sample_end_ns, 'cpu_usage_usec': cpu['usage_usec'],
            'memory_current_bytes': values['memory.current'],
            'memory_peak_bytes': values['memory.peak'],
            'swap_current_bytes': values['memory.swap.current'], 'memory_events': events,
            'populated': bool(cg['populated']), 'pids': pids,
            'raw_sha256': {name: hashlib.sha256(value).hexdigest() if value is not None else None
                           for name, value in raw.items()}}


def validate_snapshot(sample):
    need(type(sample) is dict and set(sample) == {'schema','aggregate_cgroup','cgroup_identity',
        'reader_pid','sample_start_ns','sample_end_ns','cpu_usage_usec','memory_current_bytes',
        'memory_peak_bytes','swap_current_bytes','memory_events','populated','pids','raw_sha256'} and
        sample['schema'] == 'PHASE7I_JOB_KERNEL_SNAPSHOT_V1', 'KERNEL_SNAPSHOT_SCHEMA')
    group_path(sample['aggregate_cgroup']); identity(sample['cgroup_identity'])
    need(all(integer(sample[k]) for k in ('sample_start_ns','sample_end_ns','cpu_usage_usec',
        'memory_current_bytes','swap_current_bytes')) and integer(sample['reader_pid'],1) and
        sample['sample_start_ns'] <= sample['sample_end_ns'], 'KERNEL_SNAPSHOT_NUMBERS')
    peak = sample['memory_peak_bytes']
    need(peak is None or integer(peak) and peak >= sample['memory_current_bytes'], 'KERNEL_SNAPSHOT_PEAK')
    events = sample['memory_events']
    need(type(events) is dict and set(events) == set(EVENTS) and
         all(integer(value) for value in events.values()), 'KERNEL_SNAPSHOT_MEMORY_EVENTS')
    pids = sample['pids']
    need(type(pids) is list and len(pids) <= 16 and all(integer(x,1) for x in pids) and
         len(pids) == len(set(pids)) and type(sample['populated']) is bool and
         bool(pids) == sample['populated'], 'KERNEL_SNAPSHOT_PROCESSES')
    hashes = sample['raw_sha256']
    need(type(hashes) is dict and set(hashes) == set(RAW_NAMES) and all(
        type(v) is str and re.fullmatch(r'[0-9a-f]{64}',v) or k == 'memory.peak' and v is None
        for k,v in hashes.items()), 'KERNEL_SNAPSHOT_RAW_HASHES')
    need((peak is None) == (hashes['memory.peak'] is None), 'KERNEL_SNAPSHOT_MISSING_PEAK_BINDING')
    return True


class FixedCgroupReader:
    """Future fixed own-unit reads only; construction has no kernel side effect.

    Root must retain existing unit sandbox/cap properties. Each call rechecks
    current PID/membership/UID, directory identity, effective limits and bounds.
    Missing peak is returned as None; missing other data never becomes zero.
    """
    def __init__(self, unit, aggregate_cgroup, cgroup_identity, controller_pid):
        group_path(aggregate_cgroup)
        need(aggregate_cgroup.rsplit('/', 1)[1] == unit and integer(controller_pid, 1),
             'READER_UNIT_OR_PID')
        self.unit, self.aggregate, self.pid = unit, aggregate_cgroup, controller_pid
        self.identity = identity(cgroup_identity)

    @staticmethod
    def _read(path, cap=4096):
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            chunks, total = [], 0
            while True:
                value = os.read(fd, min(4096, cap + 1 - total))
                need(type(value) is bytes, 'KERNEL_READ_BYTES_REQUIRED')
                if not value:
                    break
                chunks.append(value)
                total += len(value)
                need(total <= cap, 'KERNEL_READ_BOUND')
            return b''.join(chunks)
        finally:
            os.close(fd)

    def __call__(self):
        start = time.monotonic_ns()
        need(os.getpid() == self.pid, 'READER_CURRENT_PID_CHANGED')
        uid = os.getuid()
        expected = ('/sys/fs/cgroup/user.slice/user-%d.slice/user@%d.service/app.slice/'
                    % (uid, uid)) + self.unit
        need(expected == self.aggregate, 'READER_OWN_USER_AGGREGATE_REQUIRED')
        membership = text(self._read('/proc/self/cgroup'), 'self/cgroup')
        need(membership == '0::' + self.aggregate[len('/sys/fs/cgroup'):] + '\n',
             'READER_CURRENT_MEMBERSHIP_CHANGED')
        before = os.stat(self.aggregate)
        need({'dev': before.st_dev, 'inode': before.st_ino} == self.identity,
             'READER_CGROUP_IDENTITY_CHANGED')
        raw = {}
        for name in RAW_NAMES:
            try:
                raw[name] = self._read(self.aggregate + '/' + name)
            except FileNotFoundError:
                if name != 'memory.peak':
                    raise
                raw[name] = None
        after = os.stat(self.aggregate)
        need({'dev': after.st_dev, 'inode': after.st_ino} == self.identity,
             'READER_CGROUP_IDENTITY_CHANGED_DURING_READ')
        return parse_cgroup_raw(raw, aggregate_cgroup=self.aggregate,
            cgroup_identity=self.identity, reader_pid=self.pid,
            sample_start_ns=start, sample_end_ns=time.monotonic_ns())


class EnvelopeAbort(BaseException):
    def __init__(self, fault):
        super().__init__(fault['reason'])
        self.envelope_fault = copy.deepcopy(fault)


class EnvelopeState:
    """Pure latch. Thresholds reserve budget; observation is not hard enforcement."""
    def __init__(self, main_origin_ns, aggregate_cgroup, controller_pid):
        need(integer(main_origin_ns) and integer(controller_pid, 1), 'ENVELOPE_ORIGIN_OR_PID')
        self.origin, self.aggregate, self.pid = main_origin_ns, group_path(aggregate_cgroup), controller_pid
        self.fault = None
        self.last = None
        self.samples = 0

    def fail(self, reason, detail='', cpu=None, elapsed=None):
        if self.fault is None:
            status = 124 if reason.startswith('CPU_') else 125 if reason.startswith('MAIN_WALL_') else 126
            self.fault = {'schema': 'PHASE7I_JOB_ENVELOPE_FAULT_V1', 'reason': reason,
                'exit_status': status, 'observed_cpu_usec': cpu,
                'observed_main_elapsed_ns': elapsed, 'detail': str(detail)[:256],
                'enforcement_kind': KIND, 'FULL_LAUNCH_ENVELOPE_VERIFIED': False}
        return copy.deepcopy(self.fault)

    def observe(self, sample):
        if self.fault is not None:
            return copy.deepcopy(self.fault)
        cpu = elapsed = None
        try:
            validate_snapshot(sample)
            need(sample['aggregate_cgroup'] == self.aggregate and
                 type(sample['reader_pid']) is int and sample['reader_pid'] == self.pid,
                 'KERNEL_SNAPSHOT_CURRENT_IDENTITY')
            current_id = identity(sample['cgroup_identity'])
            start, end = sample['sample_start_ns'], sample['sample_end_ns']
            need(integer(start) and integer(end) and self.origin <= start <= end,
                 'KERNEL_SNAPSHOT_CLOCK')
            cpu = sample['cpu_usage_usec']
            need(integer(cpu), 'CPU_COUNTER_TYPE')
            elapsed = end - self.origin
            if self.last is not None:
                need(start >= self.last['sample_end_ns'] and
                     current_id == self.last['cgroup_identity'], 'STALE_OR_CHANGED_SNAPSHOT')
                if cpu < self.last['cpu_usage_usec']:
                    return self.fail('COUNTER_RESET', cpu=cpu, elapsed=elapsed)
            need(sample['populated'] is True and type(sample['pids']) is list and
                 all(integer(x, 1) for x in sample['pids']) and
                 self.pid in sample['pids'] and len(sample['pids']) <= 16 and
                 len(set(sample['pids'])) == len(sample['pids']), 'LIVE_CONTROLLER_MEMBERSHIP')
            current, peak, swap = (sample[key] for key in
                ('memory_current_bytes', 'memory_peak_bytes', 'swap_current_bytes'))
            need(integer(current) and integer(swap), 'MEMORY_CURRENT_OR_SWAP_TYPE')
            if peak is None:
                return self.fail('READBACK_UNKNOWN', 'MISSING_MEMORY_PEAK', cpu, elapsed)
            need(integer(peak) and peak >= current, 'MEMORY_PEAK_TYPE_OR_ORDER')
            events = sample['memory_events']
            need(type(events) is dict and set(events) == set(EVENTS) and
                 all(integer(x) for x in events.values()), 'MEMORY_EVENT_SCHEMA')
            if self.last is not None:
                need(peak >= self.last['memory_peak_bytes'] and
                     all(events[k] >= self.last['memory_events'][k] for k in EVENTS),
                     'MEMORY_COUNTER_RESET')
            self.samples += 1
            self.last = copy.deepcopy(sample)
            if cpu > CPU_CAP_USEC:
                return self.fail('CPU_CAP_EXCEEDED', cpu=cpu, elapsed=elapsed)
            if cpu >= CPU_STOP_USEC:
                return self.fail('CPU_EARLY_STOP', cpu=cpu, elapsed=elapsed)
            if elapsed > WALL_CAP_NS:
                return self.fail('MAIN_WALL_CAP_EXCEEDED', cpu=cpu, elapsed=elapsed)
            if elapsed >= MAIN_STOP_NS:
                return self.fail('MAIN_WALL_EARLY_STOP', cpu=cpu, elapsed=elapsed)
            if current > RAM_CAP or peak > RAM_CAP or swap or any(events[k] for k in ('oom','oom_kill','oom_group_kill')):
                return self.fail('RAM_OR_SWAP_OR_OOM', cpu=cpu, elapsed=elapsed)
            return None
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            return self.fail('READBACK_INVALID', error, cpu if integer(cpu) else None,
                             elapsed if integer(elapsed) else None)

    def summary(self):
        return {'schema': 'PHASE7I_JOB_EARLY_STOP_SUMMARY_V1', 'enforcement_kind': KIND,
            'samples': self.samples, 'first_fault': copy.deepcopy(self.fault),
            'main_origin_ns': self.origin, 'main_origin_excludes_manager_activation': True,
            'CPU_stop_usec': CPU_STOP_USEC, 'CPU_contract_cap_usec': CPU_CAP_USEC,
            'Main_stop_ns': MAIN_STOP_NS, 'whole_job_wall_contract_ns': WALL_CAP_NS,
            'atomic_cgroup_total_CPU_kill': False, 'hard_realtime_deadline': False,
            'manager_postmortem_required': True, 'FULL_LAUNCH_ENVELOPE_VERIFIED': False}


class PeriodicEnvelope:
    """Future main-thread ITIMER_REAL adapter; tests mock every signal/timer/read.

    No thread is created. Active prior ITIMER_REAL is refused untouched. Root's
    real emergency callback must use fixed os._exit(124/125/126), no blocking
    stdout/files; only the manager can clean up after controller loss/OOM.
    """
    def __init__(self, state, reader, emergency_stop=None):
        need(type(state) is EnvelopeState and callable(reader) and
             (emergency_stop is None or callable(emergency_stop)), 'ENVELOPE_ADAPTER_ARGUMENTS')
        self.state, self.reader, self.callback = state, reader, emergency_stop
        self.owned = False
        self.in_handler = False
        self.previous_handler = self.previous_timer = None

    def _trip(self, fault):
        if self.owned:
            try:
                signal.setitimer(signal.ITIMER_REAL, 0, 0)
            except BaseException as error:
                self.state.fault.setdefault('alarm_disable_error', type(error).__name__)
        if self.callback is not None:
            try:
                self.callback(copy.deepcopy(self.state.fault))
            except BaseException as error:
                error.envelope_fault = copy.deepcopy(self.state.fault)
                raise
        raise EnvelopeAbort(self.state.fault)

    def _handler(self, signum, frame):
        if not self.owned or _OWNER is not self or self.in_handler or self.state.fault is not None:
            return
        self.in_handler = True
        try:
            try:
                fault = self.state.observe(self.reader())
            except Exception as error:
                fault = self.state.fail('READBACK_INVALID', type(error).__name__ + ':' + str(error))
            if fault is not None:
                self._trip(fault)
        finally:
            self.in_handler = False

    def check_latched(self):
        if self.state.fault is not None:
            raise EnvelopeAbort(self.state.fault)

    def assert_active_timer(self):
        """Read-only borrow check; never reset/pause this or a foreign timer."""
        self.check_latched()
        try:
            need(threading.current_thread() is threading.main_thread() and self.owned and
                 _OWNER is self and signal.getsignal(signal.SIGALRM) == self._handler,
                 'WATCHDOG_HANDLER_OR_OWNER_CHANGED')
            timer = signal.getitimer(signal.ITIMER_REAL)
            need(type(timer) is tuple and len(timer) == 2 and
                 all(type(value) in (int,float) for value in timer) and
                 0 < timer[0] <= PERIOD_SECONDS + .000001 and timer[1] == PERIOD_SECONDS,
                 'WATCHDOG_TIMER_CHANGED_OR_INACTIVE')
        except (ValueError, TypeError, OSError) as error:
            raise EnvelopeAbort(self.state.fail('WATCHDOG_IDENTITY_OR_TIMER_CHANGED',error)) from error
        return True

    def check_now(self):
        self.assert_active_timer()
        try:
            fault = self.state.observe(self.reader())
        except Exception as error:
            fault = self.state.fail('READBACK_INVALID',type(error).__name__ + ':' + str(error))
        if fault is not None:
            self._trip(fault)
        return copy.deepcopy(self.state.last)

    def arm(self):
        global _OWNER
        need(threading.current_thread() is threading.main_thread(), 'MAIN_THREAD_REQUIRED')
        need(not self.owned and _OWNER is None and self.state.fault is None,
             'ENVELOPE_TIMER_ALREADY_ACTIVE_OR_FAULTED')
        previous = signal.getitimer(signal.ITIMER_REAL)
        need(type(previous) is tuple and len(previous) == 2 and
             all(type(x) in (int, float) and x == 0 for x in previous),
             'EXISTING_ITIMER_REAL_MUST_BE_INACTIVE')
        # A real own-cgroup read/limit validation must succeed before arming.
        fault = self.state.observe(self.reader())
        if fault is not None:
            self._trip(fault)
        self.previous_timer = previous
        self.previous_handler = signal.getsignal(signal.SIGALRM)
        need(self.previous_handler is signal.SIG_DFL or self.previous_handler is signal.SIG_IGN or
             callable(self.previous_handler), 'PREVIOUS_ALARM_HANDLER_NOT_RESTORABLE')
        signal.signal(signal.SIGALRM, self._handler)
        self.owned, _OWNER = True, self
        try:
            signal.setitimer(signal.ITIMER_REAL, PERIOD_SECONDS, PERIOD_SECONDS)
        except BaseException as error:
            try:
                self.close()
            except BaseException as cleanup:
                error.envelope_cleanup_unknown = type(cleanup).__name__
            raise
        return self

    def summary(self):
        return self.state.summary()

    def close(self):
        global _OWNER
        if not self.owned:
            return
        errors = []
        try:
            need(threading.current_thread() is threading.main_thread() and _OWNER is self and
                 signal.getsignal(signal.SIGALRM) == self._handler,
                 'ALARM_OWNER_THREAD_OR_HANDLER_LOST_NO_MUTATION')
        except BaseException as error:
            raise EnvelopeAbort(self.state.fail('TIMER_RESTORE_UNKNOWN',error)) from error
        try:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
        except BaseException as error:
            errors.append(type(error).__name__)
        if not errors:
            try:
                signal.signal(signal.SIGALRM, self.previous_handler)
            except BaseException as error:
                errors.append(type(error).__name__)
        if not errors:
            self.owned = False
            _OWNER = None
        if errors:
            fault = self.state.fail('TIMER_RESTORE_UNKNOWN', ','.join(errors))
            raise EnvelopeAbort(fault)


MANAGER_FIELDS = ('Id', 'InvocationID', 'ControlGroup', 'ActiveState', 'SubState', 'Result',
    'InactiveExitTimestampMonotonic', 'InactiveEnterTimestampMonotonic', 'CPUUsageNSec',
    'MemoryPeak', 'MemorySwapPeak', 'ExecMainPID', 'ExecMainCode', 'ExecMainStatus')


def parse_manager_raw(raw):
    """Pure fixed-property systemd255 show/raw decoder; no bus/process calls."""
    rows = {}
    for line in text(raw, 'manager', 8192).splitlines():
        need('=' in line, 'MANAGER_PROPERTY_SHAPE')
        key, value = line.split('=', 1)
        need(key in MANAGER_FIELDS and key not in rows, 'MANAGER_PROPERTY_DUPLICATE_OR_EXTRA')
        rows[key] = value
    need(set(rows) == set(MANAGER_FIELDS), 'MANAGER_REQUIRED_PROPERTY_MISSING')
    need(re.fullmatch(r'atlas-hh-phase7i-[a-z0-9-]{1,80}\.service', rows['Id']) and
         re.fullmatch(r'[0-9a-f]{32}', rows['InvocationID']), 'MANAGER_UNIT_OR_INVOCATION')
    group_path('/sys/fs/cgroup' + rows['ControlGroup'])
    need((rows['ActiveState'], rows['SubState']) in (('inactive','dead'),('failed','failed')),
         'MANAGER_NOT_POSTMORTEM')
    need(rows['Result'] in ('success','exit-code','signal','core-dump','timeout','watchdog',
         'start-limit-hit','resources','protocol','oom-kill'), 'MANAGER_RESULT_UNREVIEWED')
    for key in ('InactiveExitTimestampMonotonic','InactiveEnterTimestampMonotonic',
                'CPUUsageNSec','MemoryPeak','MemorySwapPeak','ExecMainPID','ExecMainCode','ExecMainStatus'):
        value = rows[key]
        rows[key] = None if value in ('[not set]','[notset]','infinity','18446744073709551615','') \
            else decimal(value, key)
        if key in ('InactiveExitTimestampMonotonic','InactiveEnterTimestampMonotonic','ExecMainPID') and rows[key] == 0:
            rows[key] = None
    return {'schema': 'PHASE7I_MANAGER_RAW_VALUES_V1', 'fields': rows,
            'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'authenticates_kernel_or_authorization': False}


def validate_postmortem(manager_raw, final_sample, expected):
    """Pure raw/numerical audit only; missing final group is UNKNOWN, not empty.

    Expected: unit, invocation_id, aggregate_cgroup, cgroup_identity,
    controller_pid, not_before_ns, not_after_ns. External raw capture authority,
    its CPU/storage/control-plane accounting and source binding remain separate.
    """
    result = {'schema': 'PHASE7I_POSTMORTEM_NUMERICAL_REVIEW_V1', 'status': 'UNKNOWN',
        'reason': None, 'CPU_observed_upper_ns': None, 'wall_observed_upper_ns': None,
        'enforcement_kind': KIND, 'raw_execution_origin_authenticated': False,
        'manager_control_plane_capacity_accounted': False,
        'FULL_LAUNCH_ENVELOPE_VERIFIED': False}
    try:
        need(type(expected) is dict and set(expected) == {'unit','invocation_id','aggregate_cgroup',
            'cgroup_identity','controller_pid','not_before_ns','not_after_ns'}, 'POSTMORTEM_EXPECTED_SCHEMA')
        group_path(expected['aggregate_cgroup']); identity(expected['cgroup_identity'])
        need(integer(expected['controller_pid'],1) and integer(expected['not_before_ns']) and
             integer(expected['not_after_ns']) and expected['not_after_ns'] > expected['not_before_ns'],
             'POSTMORTEM_EXPECTED_CLOCK_OR_PID')
        rows = parse_manager_raw(manager_raw)['fields']
        need(rows['Id'] == expected['unit'] and rows['InvocationID'] == expected['invocation_id'] and
             '/sys/fs/cgroup' + rows['ControlGroup'] == expected['aggregate_cgroup'],
             'POSTMORTEM_MANAGER_IDENTITY')
        if final_sample is None or any(rows[k] is None for k in
                ('InactiveExitTimestampMonotonic','InactiveEnterTimestampMonotonic','CPUUsageNSec',
                 'MemoryPeak','MemorySwapPeak','ExecMainPID')):
            result['reason'] = 'MISSING_MANAGER_OR_FINAL_KERNEL_OBSERVATION'
            return result
        need(rows['ExecMainPID'] == expected['controller_pid'], 'POSTMORTEM_MAIN_PID')
        start, end = rows['InactiveExitTimestampMonotonic'], rows['InactiveEnterTimestampMonotonic']
        need(0 < start < end and expected['not_before_ns'] <= start * 1000 and
             (end + 1) * 1000 <= expected['not_after_ns'], 'POSTMORTEM_MANAGER_TIMESTAMPS')
        need(type(final_sample) is dict and final_sample.get('schema') == 'PHASE7I_JOB_KERNEL_SNAPSHOT_V1' and
             final_sample['aggregate_cgroup'] == expected['aggregate_cgroup'] and
             identity(final_sample['cgroup_identity']) == expected['cgroup_identity'],
             'POSTMORTEM_KERNEL_IDENTITY')
        validate_snapshot(final_sample)
        need(integer(final_sample['sample_start_ns']) and integer(final_sample['sample_end_ns']) and
             end * 1000 <= final_sample['sample_start_ns'] <= final_sample['sample_end_ns'] <= expected['not_after_ns'],
             'POSTMORTEM_CAPTURE_CLOCK')
        need(final_sample['populated'] is False and final_sample['pids'] == [],
             'POSTMORTEM_RESIDUAL_PROCESSES')
        cpu = final_sample['cpu_usage_usec']
        need(integer(cpu), 'POSTMORTEM_CPU_TYPE')
        if final_sample['memory_peak_bytes'] is None:
            result['reason'] = 'MISSING_FINAL_MEMORY_PEAK'
            return result
        # Conservative +999ns counter quantization; +1us timestamp interval.
        result['CPU_observed_upper_ns'] = max(rows['CPUUsageNSec'], cpu * 1000) + 999
        result['wall_observed_upper_ns'] = (end - start + 1) * 1000
        need(result['CPU_observed_upper_ns'] <= CPU_CAP_USEC * 1000, 'POSTMORTEM_CPU_OVER_CAP')
        need(result['wall_observed_upper_ns'] <= WALL_CAP_NS, 'POSTMORTEM_FULL_WALL_OVER_CAP')
        need(integer(final_sample['memory_peak_bytes']) and
             max(rows['MemoryPeak'], final_sample['memory_peak_bytes']) <= RAM_CAP,
             'POSTMORTEM_RAM_OVER_CAP')
        need(rows['MemorySwapPeak'] == 0 and type(final_sample['swap_current_bytes']) is int and
             final_sample['swap_current_bytes'] == 0, 'POSTMORTEM_SWAP_OBSERVED')
        result['manager_result'] = rows['Result']
        result['OOM_events_observed'] = sum(final_sample['memory_events'][k] for k in ('oom','oom_kill','oom_group_kill'))
        result['normal_workflow_exit_observed'] = (rows['ActiveState'] == 'inactive' and
            rows['SubState'] == 'dead' and rows['Result'] == 'success' and rows['ExecMainCode'] == 1 and
            rows['ExecMainStatus'] == 0 and result['OOM_events_observed'] == 0)
        result['cleanup_values_consistent'] = True
        result['status'] = 'PASS_RAW_NUMERICAL_ONLY'
        result['reason'] = 'NOT_AUTHENTICATED_EXECUTION_OR_FULL_ENVELOPE'
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeError) as error:
        result.update(status='FAIL', reason=str(error)[:256])
    return result

"""Single-service inert lifecycle controller; persistent storage remains blocked.

No new kernel invocation is authorized by the recovery source. It runs no compiler, loader, MG5,
authorization or resource stress. Production and the 47-case campaign require
an independently verified persistent capacity sink and remain hard blocked.
"""
from __future__ import annotations
import argparse, base64, functools, hashlib, json, os, re, resource, signal, stat, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from simulation.hh_signal.final_closure.resource_closure import mount_attestation, namespace_attestation, controller_io, mount_policy, controller_guard, storage_transport, job_envelope
WORK = Path('/var/tmp')
UNIT = 'atlas-hh-phase7i-s4-capacity-01.service'
_CONTEXT = None
_INHERITED_CHILD = False
_ACTIVE_ENVELOPE = None
PHASES = ('pre_provisioning', 'source_git_preflight', 'dependency_hashing',
          'worker_creation_monitoring', 'inert_build_preparation',
          'receipt_writing', 'postflight_validation', 'failure_cleanup')
ZERO = dict(MG5_invocations=0, model_imports=0, new_ME_calls=0,
            new_integrals=0, new_events=0, Pythia_invocations=0,
            Delphes_invocations=0, human_authorizations_created=0)
EFFECTIVE = {'cpu.max': '3000 10000', 'cpu.max.burst': '0',
             'memory.max': '536870912', 'memory.swap.max': '0',
             'memory.oom.group': '1', 'pids.max': '16'}
LIMITS = {'AS': (resource.RLIMIT_AS, 536870912),
          'CPU': (resource.RLIMIT_CPU, 2),
          'FSIZE': (resource.RLIMIT_FSIZE, 65536),
          'CORE': (resource.RLIMIT_CORE, 0)}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def diagnostic_claims_safe(value, depth=0):
    require(depth <= 32, 'CHILD_DIAGNOSTIC_DEPTH_BOUND')
    if type(value) is dict:
        for key, item in value.items():
            if key in ('FULL_LAUNCH_ENVELOPE_VERIFIED', 'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED'):
                require(item is False, 'CHILD_DIAGNOSTIC_FULL_CLAIM_FORBIDDEN')
            diagnostic_claims_safe(item, depth + 1)
    elif type(value) is list:
        for item in value:
            diagnostic_claims_safe(item, depth + 1)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1048576), b''):
            h.update(part)
    return h.hexdigest()


def lifecycle_bounds():
    # Type=exec: single Main activation + runtime; no ExecStartPre/StopPost.
    # Include stop and conservative final group termination intervals.
    # Conservative extra stop interval included. Scheduler/timer latency has
    # no hard realtime guarantee; actual elapsed readback is still mandatory.
    stages = {'pre_start': 0, 'main_activation': 1, 'main_runtime': 8,
              'main_stop': .5, 'stop_post': 0, 'final_group_kill': .5}
    seconds = sum(stages.values())
    return {'timer_budget_seconds': seconds, 'stage_budgets_seconds': stages,
            'quota_duration_CPU_upper_seconds': .3 * seconds + .003,
            'aggregate_wall_cap_seconds': 13, 'aggregate_CPU_cap_seconds': 4,
            'timer_scheduling_overrun_not_a_realtime_guarantee': True}


def mount_row(path, lines):
    try:
        values = mount_attestation.parse_mountinfo(('\n'.join(lines) + '\n').encode())
    except mount_attestation.MountInfoError as error:
        raise ValueError('EXACT_MOUNT_REQUIRED:' + str(path)) from error
    values = [r for r in values if r['path'] == str(path)]
    require(len(values) == 1, 'EXACT_MOUNT_REQUIRED:' + str(path))
    value = values[0]
    require(value['filesystem_type'] == 'tmpfs', 'TMPFS_REQUIRED')
    require({'rw', 'nosuid', 'nodev', 'noexec'} <= set(value['mount_options']), 'TMPFS_FLAGS')
    return value


def load_child_context(aggregate):
    path = WORK / 'controller' / 'namespace_handoff.json'
    require(Path.cwd() == path.parent, 'CHILD_HANDOFF_FIXED_WORKING_DIRECTORY')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid()
                and info.st_size <= 8192, 'CHILD_HANDOFF_PRIVATE_REGULAR_BOUND')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(8193)
        require(len(raw) <= 8192 and len(raw) == info.st_size, 'CHILD_HANDOFF_READ_BOUND')
    finally:
        os.close(fd)
    document = controller_io.decode_records(raw)
    require(len(document) == 1, 'ONE_CHILD_HANDOFF_REQUIRED')
    value = document[0]
    require(set(value) == {'schema', 'parent_pid', 'aggregate_cgroup', 'namespace', 'guard'} and
            value['schema'] == 'PHASE7I_INHERITED_NAMESPACE_HANDOFF_V1' and
            type(value['parent_pid']) is int and value['parent_pid'] == os.getppid() and
            value['aggregate_cgroup'] == str(aggregate), 'CHILD_HANDOFF_PARENT_BOUNDARY')
    namespace_attestation.validate(value['namespace'])
    controller_guard.validate_guard(value['guard'])
    require(value['guard']['pid'] == value['parent_pid'], 'CHILD_GUARD_PARENT_PID')
    return {'namespace': value['namespace'], 'guard': value['guard']}


def namespace_and_guard(aggregate, policy, stage):
    global _CONTEXT
    producer = Path(controller_guard.__file__)
    require(sha(producer) == policy['denial_transcript']['producer_source_sha256'] and
            controller_guard.program_identity() == policy['denial_transcript']['program_sha256'],
            'EXACT_REVIEWED_CONTROLLER_GUARD_SOURCE_REQUIRED')
    if _CONTEXT is None and _INHERITED_CHILD:
        _CONTEXT = load_child_context(aggregate)
    if _CONTEXT is None:
        namespace = namespace_attestation.collect()
        emit({'kind': 'NAMESPACE_READBACK', 'stage': stage, 'proof': namespace})
        # The only nsfs owner/type ioctls precede the stricter ALL-ioctl filter.
        namespace_attestation.validate(namespace)
        guard = controller_guard.install()
        _CONTEXT = {'namespace': namespace, 'guard': guard}
    else:
        namespace = controller_guard.collect_inherited_namespace(_CONTEXT['namespace'])
        emit({'kind': 'NAMESPACE_READBACK', 'stage': stage, 'proof': namespace})
        guard = controller_guard.readback(_CONTEXT['guard'])
    controller_guard.validate_guard(guard)
    require(guard['pid'] == os.getpid(), 'ACTUAL_CURRENT_PID_GUARD_REQUIRED')
    probe = controller_guard.probe()
    emit({'kind': 'GUARD_DENIAL_READBACK', 'stage': stage, 'guard': guard, 'probe': probe})
    require(probe['status'] == 'PASS_FIXED_INVALID_TARGET_DENIALS' and
            probe['all_denied'] is True and probe['pid'] == os.getpid(),
            'FIXED_INVALID_TARGET_SYSCALL_REFUSAL_REQUIRED')
    return namespace, guard, probe


def attestation(stage):
    mount_raw = mount_attestation.read_bounded()
    # Full local raw capture precedes parser/guard failures; never auto-publish.
    mount_capture = mount_attestation.emit_evidence(mount_raw, stage, emit)
    inventory = mount_attestation.inventory(mount_raw, str(REPO))
    emit({'kind': 'MOUNT_INVENTORY_SAFE', 'stage': stage, 'inventory': inventory})
    require(inventory['status'] == 'PASS_POLICY_PREREQUISITES_ONLY',
            'UNACCOUNTED_WRITABLE_MOUNT_OR_INVALID_MOUNTINFO')
    rows = Path('/proc/self/cgroup').read_text().splitlines()
    require(len(rows) == 1 and rows[0].startswith('0::/'), 'CGROUP_V2_REQUIRED')
    relative = Path(rows[0][3:])
    parts = relative.parts
    prefix = ('/', 'user.slice', 'user-%d.slice' % os.getuid(),
              'user@%d.service' % os.getuid(), 'app.slice')
    require(parts[:5] == prefix, 'OWN_USER_SERVICE_SLICE_REQUIRED')
    require(len(parts) >= 6 and parts[5] == UNIT, 'OWN_SERVICE_CGROUP_REQUIRED')
    require(parts.count(UNIT) == 1 and parts[-1] in (UNIT, 'control'), 'OWN_SERVICE_CGROUP_REQUIRED')
    index = parts.index(UNIT)
    require(parts[index + 1:] in ((), ('control',)), 'UNREVIEWED_CGROUP_DESCENDANT')
    aggregate = Path('/sys/fs/cgroup').joinpath(*parts[1:index + 1])
    leaf = Path('/sys/fs/cgroup').joinpath(*parts[1:])
    values = {key: (aggregate / key).read_text().strip() for key in EFFECTIVE}
    require(values == EFFECTIVE, 'KERNEL_EFFECTIVE_LIMIT_MISMATCH')
    limits = {}
    for name, (kind, maximum) in LIMITS.items():
        limits[name] = list(resource.getrlimit(kind))
        require(limits[name] == [maximum, maximum], 'HARD_RLIMIT_MISMATCH:' + name)
    require(len(os.sched_getaffinity(0)) == 1, 'ONE_CPU_REQUIRED')
    require(os.statvfs(REPO).f_flag & os.ST_RDONLY, 'SOURCE_READONLY_REQUIRED')
    require(os.statvfs(aggregate).f_flag & os.ST_RDONLY, 'CGROUP_READONLY_REQUIRED')
    lines = mount_raw.decode('utf-8', errors='strict').splitlines()
    mounts = []
    vfs_facts = {}
    for path, size, inodes in ((WORK, 8388608, 1024), (Path('/tmp'), 1048576, 256)):
        mount_row(path, lines)
        v = os.statvfs(path)
        require(v.f_blocks * v.f_frsize == size and v.f_files == inodes, 'TMPFS_CAP_MISMATCH')
        vfs_facts[str(path)] = {k: getattr(v, k) for k in
                               ('f_blocks', 'f_frsize', 'f_files', 'f_bfree', 'f_ffree', 'f_flag')}
        mounts.append({'path': str(path), 'capacity_bytes': size, 'inodes': inodes,
                       'free_bytes': v.f_bfree * v.f_frsize, 'free_inodes': v.f_ffree})
    parsed_mounts = mount_attestation.parse_mountinfo(mount_raw)
    writable = sorted(r['path'] for r in parsed_mounts if 'rw' in r['mount_options'])
    require(writable == sorted([str(WORK), '/tmp']), 'UNACCOUNTED_WRITABLE_MOUNT')
    raw = {}
    for key in ('cpu.stat', 'memory.current', 'memory.peak', 'memory.swap.current',
                'cgroup.events', 'cgroup.procs'):
        try:
            raw[key] = (aggregate / key).read_text().strip()
        except FileNotFoundError:
            raw[key] = None
    policy = mount_policy.load_policy()
    # A new live invocation is still separately gated. Every call below is
    # mocked by the source/offline suite; no import installs a filter.
    namespace, guard, probe = namespace_and_guard(aggregate, policy, stage)
    namespace_attestation.validate(namespace)
    raw_sha = hashlib.sha256(mount_raw).hexdigest()
    ns_identity = {key: namespace['namespaces']['mnt'][key] for key in ('dev', 'inode')}
    facts = {row['path']: {'schema': 'PHASE7I_PRIVATE_TMPFS_FACTS_V1',
             'raw_sha256': raw_sha, 'mount_id': row['id'], 'mount_namespace': ns_identity,
             'statvfs': vfs_facts[row['path']]} for row in parsed_mounts if row['path'] in vfs_facts}
    revision = _current_revision()
    api_ids = sorted(row['id'] for row in parsed_mounts
                     if mount_policy.classify(row, str(REPO), policy) == 'kernel_api')
    transcript = {'schema': 'PHASE7I_KERNEL_API_DENIAL_TRANSCRIPT_V1',
        'raw_sha256': raw_sha, 'source_revision': revision, 'mount_namespace': ns_identity,
        'namespace_proof_sha256': hashlib.sha256(canonical(namespace)).hexdigest(),
        'mount_ids': api_ids, 'collector_source_sha256': sha(Path(controller_guard.__file__)),
        'probe': probe}
    classified = mount_policy.verify(mount_raw, str(REPO), policy=policy,
        capture_complete=mount_capture['complete'], namespace_proof=namespace,
        private_facts=facts, kernel_api_transcript=transcript,
        source_revision=revision, controller_pid=os.getpid())
    emit({'kind': 'CLASSIFIED_MOUNT_POLICY_SAFE', 'stage': stage, 'verification': classified})
    require(classified['status'] == 'PASS_SOURCE_POLICY_PREREQUISITES',
            'CLASSIFIED_MOUNT_POLICY_REQUIRED:' + classified['status'])
    cpu = dict(x.split() for x in raw['cpu.stat'].splitlines())
    return {'stage': stage, 'pid': os.getpid(), 'membership': str(relative),
            'aggregate_cgroup': str(aggregate), 'leaf_cgroup': str(leaf),
            'mount_namespace_inode': os.stat('/proc/self/ns/mnt').st_ino,
            'namespace': namespace, 'guard': guard, 'guard_probe': probe,
            'classified_mount_policy': {'status': classified['status'],
                'policy_sha256': classified['policy_sha256'],
                'projection_sha256': hashlib.sha256(canonical(classified)).hexdigest()},
            'source_revision': revision,
            'mount_capture': mount_capture,
            'mount_inventory_sha256': hashlib.sha256(canonical(inventory)).hexdigest(),
            'effective': values, 'limits': limits, 'mounts': mounts,
            'writable_mounts': writable, 'raw': raw,
            'CPU_usage_usec': int(cpu['usage_usec']),
            'memory_peak_bytes': int(raw['memory.peak']) if raw['memory.peak'] is not None else None,
            'LISTEN_FDS': os.environ.get('LISTEN_FDS'),
            'LISTEN_FDNAMES': os.environ.get('LISTEN_FDNAMES')}


def emit(value):
    controller_io.emit(value)


def persistent_storage_gate(receipt=None):
    # No receipt, flags or environment variable is an OS capacity enforcement
    # capability. A future backend must inspect the real dedicated/quota mount.
    raise ValueError('PERSISTENT_ALLOCATED_DISK_HARD_BOUND_NOT_IMPLEMENTED')


def run_full_campaign(*args, **kwargs):
    persistent_storage_gate()


def run_formal_build(*args, **kwargs):
    raise ValueError('FORMAL_BUILD_NOT_AUTHORIZED_AND_STORAGE_BOUND_UNVERIFIED')


def child():
    proof = attestation('inert_child')
    # A child and parent coexist in the same aggregate cgroup while measured.
    time.sleep(.12)
    emit({'kind': 'CHILD_RECEIPT', 'proof': proof, **ZERO})


class PhaseLog(list):
    """Contiguous Main phase observations, never manager/activation cleanup."""
    def __init__(self, aggregate, start_ns):
        super().__init__()
        self.aggregate = aggregate
        self.last_ns = start_ns

    def append(self, value):
        require(len(self) < len(PHASES) and value.get('phase') == PHASES[len(self)],
                'EXACT_EIGHT_PHASE_SEQUENCE_REQUIRED')
        now = time.monotonic_ns()
        require(now >= self.last_ns, 'MONOTONIC_PHASE_CLOCK_REQUIRED')
        value = dict(value, name=value['phase'], start_ns=self.last_ns, end_ns=now,
                     aggregate_cgroup=self.aggregate, completed=True)
        super().append(value)
        self.last_ns = now


def _terminate_for_envelope_fault(fault):
    code = fault.get('exit_status') if type(fault) is dict else None
    if type(code) is not int or code not in (124, 125, 126):
        code = 126
    os._exit(code)


def _make_job_envelope(origin_ns):
    """Future unit-only adapter; construction does not authorize execution."""
    with Path('/proc/self/cgroup').open('rb') as stream:
        raw = stream.read(4097)
    require(len(raw) <= 4096, 'OWN_CGROUP_READ_BOUND')
    uid = os.getuid()
    relative = '/user.slice/user-%d.slice/user@%d.service/app.slice/%s' % (uid, uid, UNIT)
    require(raw == ('0::' + relative + '\n').encode(),
            'ENVELOPE_EXACT_MAIN_CGROUP_REQUIRED')
    aggregate = Path('/sys/fs/cgroup' + relative)
    info = aggregate.stat(follow_symlinks=False)
    require(stat.S_ISDIR(info.st_mode), 'ENVELOPE_CGROUP_DIRECTORY_REQUIRED')
    identity = {'dev': info.st_dev, 'inode': info.st_ino}
    state = job_envelope.EnvelopeState(origin_ns, str(aggregate), os.getpid())
    reader = job_envelope.FixedCgroupReader(UNIT, str(aggregate), identity, os.getpid())
    # No blocking stdout/file write in the alarm handler. The fixed exit code
    # is independently observed by the manager; raw fault remains volatile.
    # Manager group cleanup and durable receipt storage are separate gates.
    return job_envelope.PeriodicEnvelope(state, reader,
        emergency_stop=_terminate_for_envelope_fault)


def _blocked_record(action, error):
    return {'kind': 'BLOCKED', 'action': action, 'reason': str(error)[:1024],
            'pipe_cleanup': getattr(error, 'controller_pipe_cleanup_status', None),
            'completed_main_phases': getattr(error, 'controller_completed_phases', None),
            'process_cleanup': getattr(error, 'controller_process_cleanup_status', None),
            'scratch_cleanup': getattr(error, 'controller_scratch_cleanup_status', None),
            'job_envelope_fault': getattr(error, 'envelope_fault', None),
            'job_envelope_cleanup': getattr(error, 'envelope_cleanup_status', None),
            'envelope_close_pending': _ACTIVE_ENVELOPE is not None,
            'FULL_LAUNCH_ENVELOPE_VERIFIED': False, **ZERO}


def monitored_workflow(function):
    """One same-process alarm spans blocking Git/hash/worker/receipt/cleanup."""
    @functools.wraps(function)
    def wrapped():
        global _ACTIVE_ENVELOPE
        require(_ACTIVE_ENVELOPE is None, 'REENTRANT_ENVELOPE_FORBIDDEN')
        monitor = _make_job_envelope(time.monotonic_ns())
        _ACTIVE_ENVELOPE = monitor
        original = None
        try:
            monitor.arm()
            result = function()
            monitor.check_latched()
            return result
        except BaseException as error:
            original = error
            # After a successful arm, failure formatting/writing remains under
            # the same timer. Admission failures are necessarily pre-arm.
            # Mark attempted before writing: an output failure cannot retry
            # after the reserved terminal budget has been consumed.
            error.controller_terminal_attempted = True
            try:
                emit(_blocked_record('workflow', error))
            except BaseException as output_error:
                error.controller_terminal_write_status = {
                    'status': 'UNKNOWN', 'error_type': type(output_error).__name__}
            raise
        finally:
            try:
                monitor.close()
            except BaseException as cleanup:
                target = original if original is not None else cleanup
                target.envelope_cleanup_status = {
                    'status': 'UNKNOWN', 'error_type': type(cleanup).__name__}
                # A failed restoration may leave an unknown/foreign timer.
                # End this Main; never continue unmonitored business work.
                _terminate_for_envelope_fault({'exit_status': 126})
                if original is None:
                    raise
            finally:
                _ACTIVE_ENVELOPE = None
    return wrapped


def _current_revision():
    # Every HEAD lookup shares the active Main watchdog when present. The
    # inert child uses the default bounded guard; both keep a one-second limit.
    from simulation.hh_signal.final_closure.integration_runtime.git_precheck import GitGuard
    with GitGuard(REPO, wall=1, command=1, status=1, outer_watchdog=_ACTIVE_ENVELOPE) as guard:
        raw = guard.git('rev-parse', 'HEAD')
    require(re.fullmatch(rb'[0-9a-f]{40}\n', raw) is not None, 'CURRENT_REVISION_ENCODING')
    return raw[:-1].decode('ascii')


@monitored_workflow
def workflow():
    start = time.monotonic()
    start_ns = time.monotonic_ns()
    initial = attestation('main_before_preprovision')
    records = PhaseLog(initial['aggregate_cgroup'], start_ns)
    tree = WORK / 'controller'
    created = False
    failure = None
    try:
        tree.mkdir(mode=0o700)
        created = True
        records.append({'phase': PHASES[0], 'location': str(tree), 'persistent_writes': 0})
        sys.path.insert(0, str(REPO))
        from simulation.hh_signal.final_closure.integration_runtime.contract import check_revision
        revision = _current_revision()
        checked = check_revision(revision, full=True, outer_watchdog=_ACTIVE_ENVELOPE)
        preflight = checked['git_preflight']
        records.append({'phase': PHASES[1], 'revision': revision,
                        'git_preflight': {k: preflight[k] for k in
                            ('status', 'index_sha256', 'wall_seconds', 'CPU_seconds')},
                        'tracked_files': preflight['tracked_files'],
                        'critical_files': len(preflight['critical_source_sha256']),
                        'full_preflight_receipt_sha256': hashlib.sha256(canonical(preflight)).hexdigest(),
                        'physics_sha256': checked['physics_sha256']})
        # No compiler execution, dynamic loader test, native build or imports.
        # Include all executable shared objects mapped in this Python process.
        paths = {Path('/usr/bin/python3').resolve(), Path('/usr/bin/git'), Path(__file__).resolve()}
        for line in Path('/proc/self/maps').read_text().splitlines():
            fields = line.split()
            if len(fields) == 6 and fields[5].startswith('/'):
                paths.add(Path(fields[5]))
        require(len(paths) <= 64, 'DEPENDENCY_INVENTORY_BOUND')
        identities = [{'path': str(p), 'sha256': sha(p)} for p in sorted(paths)]
        records.append({'phase': PHASES[2], 'identities': identities})
        handoff = {'schema': 'PHASE7I_INHERITED_NAMESPACE_HANDOFF_V1',
            'parent_pid': os.getpid(), 'aggregate_cgroup': initial['aggregate_cgroup'],
            'namespace': initial['namespace'], 'guard': initial['guard']}
        handoff_raw = canonical(handoff) + b'\n'
        require(len(handoff_raw) <= 8192, 'CHILD_HANDOFF_SIZE_BOUND')
        with (tree / 'namespace_handoff.json').open('xb') as stream:
            stream.write(handoff_raw)
        proc = subprocess.Popen(['/usr/bin/python3', '-I', '-B', str(HERE / 'full_controller.py'),
                                 'inert-child'], cwd=tree, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        child_failure = None
        try:
            output, errors = controller_io.collect_child(proc, timeout=1)
            require(len(output) <= 65536 and len(errors) <= 8192,
                    'INERT_CHILD_FAILED_OR_OUTPUT_BOUND')
            child_records = controller_io.decode_records(output)
            require(child_records and len(child_records) <= 24, 'CHILD_PROTOCOL_RECORD_BOUND')
            # Validate even a rejected terminal before it can be re-emitted.
            for child_record in child_records:
                diagnostic_claims_safe(child_record)
            for child_record in child_records[:-1]:
                require(type(child_record) is dict and child_record.get('kind') in (
                    'PRIVATE_MOUNTINFO_RAW', 'MOUNTINFO_CAPTURE_SAFE_METADATA',
                    'MOUNT_INVENTORY_SAFE', 'NAMESPACE_READBACK', 'LOCAL_PRIVATE_EVIDENCE_BUFFERED',
                    'CLASSIFIED_MOUNT_POLICY_SAFE', 'GUARD_DENIAL_READBACK'),
                    'UNREVIEWED_CHILD_DIAGNOSTIC_RECORD')
                diagnostic_claims_safe(child_record)
                emit({'kind': 'CHILD_DIAGNOSTIC_RECORD', 'record': child_record})
            if errors:
                emit({'kind': 'PRIVATE_CHILD_STDERR', 'base64': base64.b64encode(errors).decode(),
                      'sha256': hashlib.sha256(errors).hexdigest()})
            if proc.returncode != 0:
                emit({'kind': 'CHILD_TERMINAL_REJECTED', 'exit_status': proc.returncode,
                      'terminal_record': child_records[-1]})
            require(proc.returncode == 0 and not errors, 'INERT_CHILD_FAILED_OR_OUTPUT_BOUND')
            detail = child_records[-1]
            diagnostic_claims_safe(detail)
            require(detail.get('kind') == 'CHILD_RECEIPT', 'CHILD_TERMINAL_RECEIPT_MISSING')
            require(detail['proof']['aggregate_cgroup'] == initial['aggregate_cgroup'],
                    'SIBLING_CHILD_CGROUP_FORBIDDEN')
            require(detail['proof']['mount_namespace_inode'] == initial['mount_namespace_inode'],
                    'CHILD_MOUNT_NAMESPACE_CHANGED')
            namespace_attestation.validate(detail['proof']['namespace'], initial['namespace'])
            proof = detail['proof']
            require(type(proof.get('pid')) is int and proof['pid'] == proc.pid,
                    'CHILD_ACTUAL_PID_REQUIRED')
            controller_guard.validate_guard(proof.get('guard'))
            child_guard = proof['guard']
            require(child_guard['pid'] == proc.pid and
                    child_guard['origin'] == 'CURRENT_PROCESS_INHERITED_READBACK' and
                    child_guard.get('parent_pid') == initial['pid'] and
                    child_guard['filter_count_after'] >= initial['guard']['filter_count_after'],
                    'CHILD_CURRENT_GUARD_READBACK_REQUIRED')
            current = proof['namespace'].get('current_identity_facts', {})
            require(proof['namespace'].get('owner_evidence') ==
                    'OWNER_INHERITED_BY_SAME_NAMESPACE_IDENTITY' and
                    proof['namespace'].get('type_evidence') ==
                    'CACHED_FROM_INITIAL_NSFS_TYPE_READBACK' and
                    type(current.get('pid')) is int and current['pid'] == proc.pid,
                    'CHILD_CURRENT_NAMESPACE_FACTS_REQUIRED')
            rebuilt_namespace = controller_guard.inherit_namespace(initial['namespace'], current)
            require(canonical(rebuilt_namespace) == canonical(proof['namespace']),
                    'CHILD_NAMESPACE_CURRENT_AND_CACHED_FIELDS_DISAGREE')
            require(proof.get('source_revision') == revision, 'CHILD_SOURCE_REVISION_MISMATCH')
            child_policy = proof.get('classified_mount_policy', {})
            require(child_policy.get('status') == 'PASS_SOURCE_POLICY_PREREQUISITES' and
                    child_policy.get('policy_sha256') == mount_policy.POLICY_SHA256,
                    'CHILD_CLASSIFIED_MOUNT_POLICY_REQUIRED')
            policy = mount_policy.load_policy()
            require(mount_policy.validate_guard_probe(proof.get('guard_probe'),
                    policy=policy, controller_pid=proc.pid),
                    'CHILD_CURRENT_GUARD_PROBES_REQUIRED')
            records.append({'phase': PHASES[3], 'child': detail})
        except BaseException as error:
            child_failure = error
            raise
        finally:
            cleanup_errors = []
            try:
                needs_stop = proc.poll() is None
            except BaseException as error:
                cleanup_errors.append(type(error).__name__)
                needs_stop = True
            if needs_stop:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except BaseException as error:
                    cleanup_errors.append(type(error).__name__)
                # Attempt wait even if group termination itself failed.
                try:
                    proc.wait(timeout=.2)
                except BaseException as error:
                    cleanup_errors.append(type(error).__name__)
            if cleanup_errors:
                proof = {'status': 'UNKNOWN', 'errors': cleanup_errors,
                         'manager_cleanup_still_required': True}
                if child_failure is not None:
                    child_failure.controller_process_cleanup_status = proof
                else:
                    error = ValueError('CHILD_GROUP_CLEANUP_UNVERIFIED')
                    error.controller_process_cleanup_status = proof
                    raise error
        (tree / 'inert_preparation.txt').write_text('NO COMPILER OR NATIVE DISPATCH\n')
        records.append({'phase': PHASES[4], 'compiler_invocations': 0})
        receipt = {'kind': 'VOLATILE_WORKFLOW_RECEIPT', 'phases': records, **ZERO}
        data = canonical(receipt)
        require(len(data) <= 24576, 'VOLATILE_RECEIPT_BOUND')
        (tree / 'receipt.json').write_bytes(data)
        wire = storage_transport.encode_transport({
            'controller.json': data,
            'namespace.json': canonical(initial['namespace']),
            'mountinfo.bin': controller_io.mount_capture(initial['mount_capture']['raw_sha256'],
                                                         'main_before_preprovision')},
            source_revision=revision)
        require(len(wire) <= 65536, 'FIXED_VOLATILE_TRANSPORT_FILE_BOUND')
        (tree / 'receipt.transport').write_bytes(wire)
        transport, artifacts = storage_transport.verify_transport(wire, expected_revision=revision)
        require(artifacts['controller.json'] == data, 'INDEPENDENT_TRANSPORT_READBACK_MISMATCH')
        records.append({'phase': PHASES[5], 'bytes': len(data), 'sha256': sha(tree / 'receipt.json'),
                        'logical_transport': transport,
                        'storage': 'PRIVATE_SIZE_AND_INODE_CAPPED_TMPFS'})
        after = check_revision(revision, full=True, outer_watchdog=_ACTIVE_ENVELOPE)
        require(after['source_identity'] == checked['source_identity'], 'SOURCE_CHANGED')
        require(sha(tree / 'receipt.json') == hashlib.sha256(data).hexdigest(), 'RECEIPT_CHANGED')
        with (tree / 'receipt.transport').open('rb') as stream:
            reread = stream.read(65537)
        require(len(reread) <= 65536 and reread == wire, 'VOLATILE_TRANSPORT_CHANGED')
        storage_transport.verify_transport(reread, expected_revision=revision)
        records.append({'phase': PHASES[6], 'source_preserved': True, 'receipt_integrity': True})
    except BaseException as error:
        failure = error
        error.controller_completed_phases = [row['phase'] for row in records]
        raise
    finally:
        try:
            if created:
                # Fixed known files only; no recursive deletion/path traversal.
                for name in ('inert_preparation.txt', 'receipt.json', 'receipt.transport', 'namespace_handoff.json'):
                    (tree / name).unlink(missing_ok=True)
                tree.rmdir()
        except BaseException as cleanup_error:
            if failure is None:
                raise
            # Do not emit a nonterminal record from finally: the output
            # budget may be the original failure. Reserved BLOCKED emits once.
            failure.controller_scratch_cleanup_status = {
                'status': 'UNKNOWN', 'original_reason': str(failure)[:512],
                'cleanup_error_type': type(cleanup_error).__name__}
    final = attestation('main_after_cleanup')
    records.append({'phase': PHASES[7], 'fixed_scratch_removed': True})
    emit({'kind': 'MAIN_LIFECYCLE_RECEIPT', 'status': 'PASS_VOLATILE_DIAGNOSTIC',
          'proof_initial': initial, 'proof_final': final,
          'records': records, 'main_elapsed_seconds': time.monotonic() - start,
          'main_entered_ns': start_ns, 'main_receipt_ready_ns': time.monotonic_ns(),
          'controller_still_alive': True, 'manager_cleanup_verified': False,
          'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED': False,
          'FULL_LAUNCH_ENVELOPE_VERIFIED': False,
          'persistent_output_hard_bound': 'BLOCKED',
          'io_scope': controller_io.summary(),
          'job_envelope': _ACTIVE_ENVELOPE.summary(),
          'resource_matrix_cases_executed': 0, **ZERO})


def properties():
    # Proposed architecture has one ExecStart only; internal pre/post share
    # the same namespace. Inherited child does not re-enter manager ns caches.
    # Keep PrivateUsers/Network/IPC and every existing security property.
    return ['Type=exec', 'RemainAfterExit=no', 'Restart=no', 'NotifyAccess=none',
            'RuntimeRandomizedExtraSec=0', 'TimeoutStartFailureMode=kill',
            'TimeoutStopFailureMode=kill', 'CPUAccounting=yes', 'MemoryAccounting=yes',
            'TasksAccounting=yes', 'MemoryMax=536870912', 'MemorySwapMax=0',
            'OOMPolicy=kill', 'CPUQuota=30%', 'CPUQuotaPeriodSec=10000us',
            'RuntimeMaxSec=8s', 'TimeoutStartSec=1s', 'TimeoutStopSec=0.5s',
            'KillMode=control-group', 'KillSignal=SIGKILL', 'FinalKillSignal=SIGKILL',
            'SendSIGKILL=yes', 'TasksMax=16', 'CPUAffinity=' + str(min(os.sched_getaffinity(0))),
            'LimitCPU=2', 'LimitAS=536870912', 'LimitFSIZE=65536', 'LimitCORE=0',
            'LimitNOFILE=128', 'PrivateUsers=yes', 'PrivateNetwork=yes', 'PrivateIPC=yes',
            'ProtectSystem=strict', 'ProtectHome=read-only', 'ProtectControlGroups=yes',
            'NoNewPrivileges=yes', 'RestrictNamespaces=yes', 'CapabilityBoundingSet=',
            'ReadOnlyPaths=/dev /proc /sys',
            'InaccessiblePaths=/run/user/' + str(os.getuid()),
            'TemporaryFileSystem=' + str(WORK) + ':rw,size=8388608,nr_inodes=1024,nodev,nosuid,noexec',
            'TemporaryFileSystem=/tmp:rw,size=1048576,nr_inodes=256,nodev,nosuid,noexec',
            'WorkingDirectory=' + str(REPO), 'StandardInput=null',
            'Environment=PATH=/usr/bin:/bin LANG=C.UTF-8 HOME=' + str(Path.home()) +
            ' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 GIT_OPTIONAL_LOCKS=0 TMPDIR=/tmp TMP=/tmp TEMP=/tmp',
            'UnsetEnvironment=LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONINSPECT GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE',
            ]


def launch_command():
    return ['/usr/bin/systemd-run', '--user', '--quiet', '--wait', '--pipe', '--unit', UNIT,
            *[v for prop in properties() for v in ('--property', prop)],
            '/usr/bin/python3', '-I', '-B', str(HERE / 'full_controller.py'), 'namespace-inspection']


def main(argv=None):
    global _CONTEXT, _INHERITED_CHILD
    _CONTEXT = None
    _INHERITED_CHILD = False
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('action', choices=('launch-live-diagnostic', 'stage-pre', 'stage-post',
                                         'workflow', 'inert-child', 'full-campaign', 'BUILD_ONLY',
                                         'namespace-inspection', 'describe-diagnostic', 'describe-volatile-workflow'))
    args = parser.parse_args(argv)
    _INHERITED_CHILD = args.action == 'inert-child'
    # CLI spelling does not establish a private same-service output channel.
    controller_io.reset(private_pipe=False)
    try:
        if args.action == 'describe-volatile-workflow':
            command = launch_command()
            command[-1] = 'workflow'
            emit({'kind': 'PROPOSED_S4_ARGV_ONLY', 'execution_authorized': False,
                  'argv': command, 'scope': 'S4_VOLATILE_ONLY_NORMAL_ONCE',
                  'guard_installs': 1, 'maximum_invalid_target_syscalls': 18,
                  'persistent_capacity': 'BLOCKED', 'controller_loss_durable_receipt': 'UNKNOWN',
                  'cumulative_CPU_early_stop_usec': 3000000,
                  'main_origin_wall_early_stop_ns': 10000000000,
                  'periodic_same_process_seconds': .01,
                  'atomic_cgroup_CPU_hard_kill_verified': False,
                  'activation_cleanup_wall_verified': False,
                  'FULL_LAUNCH_ENVELOPE_VERIFIED': False, **ZERO})
            return 0
        if args.action == 'describe-diagnostic':
            emit({'kind': 'PROPOSED_ARGV_ONLY', 'execution_authorized': False,
                  'argv': launch_command(), 'unit': UNIT, 'bounds': lifecycle_bounds(),
                  'scope': 'One namespace/mount inspection, one S4 guard install and at most six invalid-target syscall probes; no child or eight-phase workflow.',
                  'guard_installs': 1, 'maximum_invalid_target_syscalls': 6,
                  'FULL_LAUNCH_ENVELOPE_VERIFIED': False, **ZERO})
            return 0
        if args.action == 'launch-live-diagnostic':
            raise ValueError('NEW_KERNEL_ATTEMPT_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION')
        if args.action == 'BUILD_ONLY':
            run_formal_build()
        elif args.action == 'full-campaign':
            run_full_campaign()
        elif args.action == 'workflow':
            workflow()
        elif args.action == 'namespace-inspection':
            proof = attestation('single_main_internal_pre')
            emit({'kind': 'INSPECTION_ONLY_COMPLETE', 'proof': proof,
                  'EIGHT_PHASE_WORKFLOW_COMPLETED': False,
                  'FULL_LAUNCH_ENVELOPE_VERIFIED': False,
                  'persistent_capacity': 'BLOCKED', **ZERO})
        elif args.action == 'inert-child':
            child()
        else:
            emit({'kind': args.action.upper().replace('-', '_'),
                  'proof': attestation(args.action),
                  'service_result': os.environ.get('SERVICE_RESULT'), **ZERO})
        return 0
    except BaseException as error:
        if not getattr(error, 'controller_terminal_attempted', False):
            emit(_blocked_record(args.action, error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

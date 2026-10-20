"""Fixed worker transport inside an enforced user-service cgroup/namespace.

The service contains all business imports, preflight, compilation-like fixtures,
loader, receipts, postflight and export. The host only provisions a fixed finite
transport, observes cgroup counters, and terminates that exact unit. The systemd
control plane and this observer are not included in payload CPU/RAM accounting.
Formal BUILD_ONLY is unconditionally blocked: full host-controller resource
containment is not implemented. Private TTY transport code is a proposal only.
"""
from __future__ import annotations
import fcntl, hashlib, json, os, re, stat, subprocess, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PHASES = ('preflight', 'compile', 'loader', 'receipt', 'postflight', 'export')
MODES = ('cpu', 'ram', 'wall', 'disk', 'abnormal')
CASES = ('normal',) + tuple(a+'_'+b for a in PHASES for b in MODES) + (
    'aggregate_cpu', 'orphan', 'controller_loss', 'pids', 'source_write',
    'cgroup_write', 'namespace_escape', 'stdout_overflow', 'disk_inodes',
    'tmp_disk', 'tmp_inodes', 'chunk_overflow', 'legacy_missing_approval', 'archive_bound', 'allocation_bypass', 'job_lock')
ZERO = {'MG5_invocations': 0, 'new_ME_calls': 0, 'new_integrals': 0,
        'new_hard_events': 0, 'new_Pythia_events': 0, 'new_Delphes_events': 0}
PROFILE_FIXTURE = {'schema_version': 1, 'profile_id': 'PHASE7I_RESOURCE_FIXTURE_V1', 'execution_scope': 'HARMLESS_FIXED_FIXTURES_ONLY', 'aggregate_CPU_seconds': 4, 'aggregate_wall_seconds': 13, 'unit_start_seconds': 2, 'unit_run_seconds': 10, 'unit_stop_seconds': 0.1, 'cpu_quota_percent': 30, 'cpu_quota_period_usec': 10000, 'cpu_burst_usec': 0, 'CPU_watchdog_stop_usec': 2500000, 'aggregate_memory_bytes': 536870912, 'swap_bytes': 0, 'per_process_address_space_bytes': 536870912, 'per_process_CPU_seconds': 2, 'work_tmpfs_bytes': 8388608, 'tmp_tmpfs_bytes': 1048576, 'work_tmpfs_inodes': 1024, 'tmp_tmpfs_inodes': 256, 'work_executable': False, 'per_regular_file_bytes': 65536, 'artifact_chunks': 2, 'host_stream_files': 2, 'host_metadata_files': 4, 'host_metadata_bytes': 65536, 'source_control_reserve_bytes': 0, 'canary_bytes': 64, 'aggregate_disk_bytes': 16777216, 'max_tasks': 16, 'poll_seconds': 0.02, 'RAM_profile_review_status': 'PENDING_HUMAN_REVIEW_BEFORE_SERVICE_EXECUTION', 'new_ME_calls': 0, 'new_integrals': 0, 'new_events': 0, 'artifact_index_files': 1, 'formal_build_execution_authorized': False, 'host_allocation_granule_bytes': 4096, 'campaign_lock_allocated_reserve_bytes': 4096, 'campaign_lock_reserve_in_source_control': False}
PROFILE_BUILD = {'schema_version': 1, 'profile_id': 'PHASE7I_BUILD_ONLY_PROPOSAL_V1', 'execution_scope': 'SOURCE_PROPOSAL_ONLY_NOT_AUTHORIZED', 'aggregate_CPU_seconds': 14400, 'aggregate_wall_seconds': 14400, 'unit_start_seconds': 10, 'unit_run_seconds': 14300, 'unit_stop_seconds': 2, 'cpu_quota_percent': 99, 'cpu_quota_period_usec': 10000, 'cpu_burst_usec': 0, 'CPU_watchdog_stop_usec': 13600000000, 'aggregate_memory_bytes': 2147483648, 'swap_bytes': 0, 'per_process_address_space_bytes': 2147483648, 'per_process_CPU_seconds': 14300, 'work_tmpfs_bytes': 2147483648, 'tmp_tmpfs_bytes': 268435456, 'work_tmpfs_inodes': 65536, 'tmp_tmpfs_inodes': 16384, 'work_executable': True, 'per_regular_file_bytes': 67108864, 'artifact_chunks': 32, 'host_stream_files': 2, 'host_metadata_files': 4, 'host_metadata_bytes': 65536, 'source_control_reserve_bytes': 67108864, 'canary_bytes': 64, 'aggregate_disk_bytes': 5368709120, 'max_tasks': 16, 'poll_seconds': 0.02, 'RAM_profile_review_status': 'PENDING_HUMAN_REVIEW_BEFORE_SERVICE_EXECUTION', 'new_ME_calls': 0, 'new_integrals': 0, 'new_events': 0, 'artifact_index_files': 1, 'formal_build_execution_authorized': False, 'formal_build_entrypoint_requires_new_explicit_authorization': True, 'work_tmpfs_proposal_review_status': 'PENDING_EXACT_SOURCE_HUMAN_BUILD_ONLY_REVIEW', 'host_allocation_granule_bytes': 4096, 'campaign_lock_allocated_reserve_bytes': 4096, 'campaign_lock_reserve_in_source_control': True}
UNIT_PATTERN = r'atlas-hh-phase7i-resource-[0-9a-f]{32}\.service'
METADATA_NAMES = ('launch.json', 'result.json', 'handoff.json', 'failure.json')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def load_profile(mode='fixture'):
    require(mode in ('fixture', 'BUILD_ONLY'), 'UNREVIEWED_EXECUTION_MODE')
    expected = PROFILE_FIXTURE if mode == 'fixture' else PROFILE_BUILD
    path = HERE/'config'/('fixture_profile.json' if mode == 'fixture' else 'build_profile.json')
    value = json.loads(path.read_text())
    require(value == expected and set(value) == set(expected) and
            all(type(value[k]) is type(v) for k, v in expected.items()), 'RESOURCE_PROFILE_DRIFT')
    bounds = profile_bounds(value)
    require(bounds['nominal_kernel_CPU_upper_seconds'] < value['aggregate_CPU_seconds'],
            'CPU_RATE_DURATION_PRODUCT_EXCEEDS_AGGREGATE_CAP')
    require(bounds['maximum_data_disk_bytes'] < value['aggregate_disk_bytes'],
            'FIXED_TRANSPORT_DISK_ENVELOPE_EXCEEDS_CAP')
    return value


def profile_bounds(p):
    # cpu.max.burst must additionally attest to zero in the actual worker.
    cpu = ((p['unit_start_seconds'] + p['unit_run_seconds'] + p['unit_stop_seconds']) *
           p['cpu_quota_percent']/100 + p['cpu_quota_period_usec']/1000000 *
           p['cpu_quota_percent']/100)
    disk = (p['work_tmpfs_bytes'] + p['tmp_tmpfs_bytes'] +
            (p['artifact_chunks'] + p['artifact_index_files'] + p['host_stream_files']) * p['per_regular_file_bytes'] +
            p['host_metadata_files'] * p['host_metadata_bytes'] +
            p['source_control_reserve_bytes'] + p['host_allocation_granule_bytes'] +
            (0 if p['campaign_lock_reserve_in_source_control'] else p['campaign_lock_allocated_reserve_bytes']))
    require(not p['campaign_lock_reserve_in_source_control'] or
            p['source_control_reserve_bytes'] >= p['campaign_lock_allocated_reserve_bytes'],
            'CAMPAIGN_MUTEX_RESERVE_MISSING')
    return {'nominal_kernel_CPU_upper_seconds': cpu, 'maximum_data_disk_bytes': disk,
            'scope': 'payload cgroup plus fixed data transports; excludes host control-plane resource usage'}


def source_snapshot():
    paths = set(HERE.glob('*.py')) | set((HERE/'config').glob('*.json'))
    runtime = HERE.parent/'integration_runtime'
    paths |= {p for p in runtime.glob('*') if p.is_file() and not p.name.startswith('test_') and p.suffix in ('.py', '.f', '.f90', '.c')}
    paths |= {HERE.parent/'guard_correction/native_checks_corrected.f',
              HERE.parent/'config/physics_contract.json'}
    require(len(paths) <= 96 and all(p.stat().st_size <= 262144 for p in paths), 'SOURCE_SNAPSHOT_BOUND')
    rows = [{'path': p.relative_to(REPO).as_posix(), 'sha256': digest(p), 'bytes': p.stat().st_size}
            for p in sorted(paths)]
    return {'identity': canonical(rows), 'paths': rows}


def host_env():
    uid = str(os.getuid())
    return {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'HOME': str(Path.home()),
            'XDG_RUNTIME_DIR': '/run/user/'+uid,
            'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/'+uid+'/bus',
            'GIT_OPTIONAL_LOCKS': '0', 'PYTHONDONTWRITEBYTECODE': '1'}


def fresh(path, mode='fixture'):
    p = Path(path)
    root = Path.home()/'simulations'/('hh_phase7i_resource_closure' if mode == 'fixture' else 'hh_final_closure')
    require(p.is_absolute() and '..' not in p.parts and p != root and p.is_relative_to(root) and
            re.fullmatch(r'[A-Za-z0-9_./-]+', str(p)) and not p.exists() and p.parent.is_dir() and
            not any(q.is_symlink() for q in (p, *p.parents)), 'FRESH_REAL_OUTPUT_REQUIRED')
    return p


def new_json(path, value):
    p = Path(path)
    require(p.name in METADATA_NAMES, 'HOST_METADATA_PATH_NOT_FIXED')
    raw = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    require(len(raw) <= 65536, 'HOST_METADATA_BOUND')
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    require(p.stat().st_blocks*512 <= 65536, 'HOST_METADATA_ALLOCATED_BOUND')


def _regular_empty(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(fd)


def artifact_names(profile):
    return tuple('chunk_'+format(i, '02d')+'.bin' for i in range(profile['artifact_chunks']))


def campaign_lock_path():
    return Path.home()/'simulations/.resource_envelope.lock'


def prepare_campaign_lock():
    # Fixed zero-byte host transport, created only on an actual later launch.
    # The manager and worker receive it readonly. The WORKER holds flock, never
    # this controller, so loss of a controller cannot release the campaign lock.
    path = campaign_lock_path()
    require(path.parent.is_dir() and not any(p.is_symlink() for p in (path, *path.parents)),
            'UNSAFE_CAMPAIGN_LOCK_NAMESPACE')
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        try:
            created = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(created)
        fd = os.open(path, flags)
    try:
        facts = os.fstat(fd); current = path.lstat()
        require(stat.S_ISREG(facts.st_mode) and facts.st_nlink == 1 and facts.st_uid == os.getuid() and
                facts.st_size == 0 and facts.st_blocks*512 <= 4096 and
                (facts.st_dev, facts.st_ino) == (current.st_dev, current.st_ino) and
                (fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE) == os.O_RDONLY,
                'CAMPAIGN_LOCK_IDENTITY_OR_READONLY_DRIFT')
        return {'path': str(path), 'device': facts.st_dev, 'inode': facts.st_ino,
                'uid': facts.st_uid, 'links': facts.st_nlink, 'bytes': 0,
                'allocated_bytes': facts.st_blocks*512, 'descriptor_access': 'read-only'}
    finally:
        os.close(fd)


def properties(output, mode='fixture', *, human_tty=None):
    p = load_profile(mode); output = Path(output); work = output/'work'
    uid = str(os.getuid())
    work_flags = 'rw,size='+str(p['work_tmpfs_bytes'])+',nr_inodes='+str(p['work_tmpfs_inodes'])+',nodev,nosuid'
    work_flags += ',exec' if p['work_executable'] else ',noexec'
    tmp_flags = 'rw,size='+str(p['tmp_tmpfs_bytes'])+',nr_inodes='+str(p['tmp_tmpfs_inodes'])+',nodev,nosuid,noexec'
    result = ['Type=exec', 'RemainAfterExit=yes', 'CPUAccounting=yes', 'MemoryAccounting=yes',
        'TasksAccounting=yes', 'MemoryMax='+str(p['aggregate_memory_bytes']), 'MemorySwapMax=0',
        'OOMPolicy=kill', 'CPUQuota='+str(p['cpu_quota_percent'])+'%',
        'CPUQuotaPeriodSec='+str(p['cpu_quota_period_usec'])+'us',
        'RuntimeMaxSec='+str(p['unit_run_seconds'])+'s',
        'TimeoutStartSec='+str(p['unit_start_seconds'])+'s',
        'TimeoutStopSec='+str(p['unit_stop_seconds'])+'s',
        'KillMode=control-group', 'KillSignal=SIGKILL', 'FinalKillSignal=SIGKILL', 'SendSIGKILL=yes',
        'TasksMax='+str(p['max_tasks']), 'CPUAffinity='+str(min(os.sched_getaffinity(0))),
        'LimitCPU='+str(p['per_process_CPU_seconds']), 'LimitAS='+str(p['per_process_address_space_bytes']),
        'LimitFSIZE='+str(p['per_regular_file_bytes']), 'LimitNOFILE=128', 'LimitCORE=0',
        'PrivateUsers=yes', 'PrivateNetwork=yes', 'PrivateIPC=yes', 'ProtectSystem=strict',
        'ProtectHome=read-only', 'ProtectControlGroups=yes', 'NoNewPrivileges=yes',
        'RestrictNamespaces=yes', 'CapabilityBoundingSet=', 'ReadOnlyPaths=/dev /proc /sys',
        'InaccessiblePaths=/run/user/'+uid+' /var/tmp',
        'TemporaryFileSystem='+str(work)+':'+work_flags,
        'TemporaryFileSystem=/tmp:'+tmp_flags,
        'WorkingDirectory='+str(work), 'StandardInput=null',
        'StandardOutput=file:'+str(output/'stdout.log'), 'StandardError=file:'+str(output/'stderr.log'),
        'Environment=PATH=/usr/bin:/bin LANG=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 '
        'GIT_OPTIONAL_LOCKS=0 TMPDIR=/tmp TMP=/tmp TEMP=/tmp HOME='+str(Path.home())]
    # The manager opens existing ordinary files before the readonly namespace.
    # No ReadWritePaths: that would shadow the tmpfs and invalidate its quota.
    result += ['OpenFile='+str(output/name)+':'+name[:-4]+':' for name in (*artifact_names(p), 'index.bin')]
    if human_tty is not None:
        require(mode == 'BUILD_ONLY' and re.fullmatch(r'/dev/pts/[0-9]+', human_tty['path']),
                'HUMAN_TTY_TRANSPORT_FORBIDDEN_IN_FIXTURES')
        result.append('OpenFile='+human_tty['path']+':human_tty:')
    result.append('OpenFile='+str(campaign_lock_path())+':campaign_lock:read-only')
    return result


def fixed_command(case, output, mode, source_identity, unit, *, revision=None, human_tty=None):
    require(case in CASES, 'UNREVIEWED_FIXTURE_CASE')
    require(mode in ('fixture', 'BUILD_ONLY'), 'UNREVIEWED_EXECUTION_MODE')
    require(re.fullmatch(r'[0-9a-f]{64}', source_identity) is not None, 'INVALID_SOURCE_IDENTITY')
    require(re.fullmatch(UNIT_PATTERN, unit) is not None, 'FOREIGN_UNIT_FORBIDDEN')
    command = ['/usr/bin/systemd-run', '--user', '--quiet', '--unit', unit,
            *[v for prop in properties(output, mode, human_tty=human_tty) for v in ('--property', prop)],
            '/usr/bin/python3', '-I', '-B', str(HERE/'worker.py'), '--mode', mode,
            '--case', case, '--source-identity', source_identity]
    if mode == 'BUILD_ONLY':
        require(case == 'normal' and re.fullmatch(r'[0-9a-f]{40}', revision or '') and human_tty,
                'EXACT_REVISION_AND_REAL_MANUAL_TTY_REQUIRED')
        command += ['--revision', revision, '--tty-rdev', str(human_tty['rdev']),
                    '--tty-inode', str(human_tty['inode'])]
    else:
        require(revision is None and human_tty is None, 'FIXTURE_CANNOT_TRANSPORT_HUMAN_AUTHORIZATION')
    return command


def unit_properties(unit, timeout=2):
    require(re.fullmatch(UNIT_PATTERN, unit) is not None, 'FOREIGN_UNIT_FORBIDDEN')
    fields = ('Id,LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,MainPID,'
        'ExecMainStartTimestampMonotonic,ExecMainExitTimestampMonotonic,ControlGroup,CPUUsageNSec,'
        'MemoryPeak,MemoryCurrent,TasksCurrent,RuntimeMaxUSec,CPUQuotaPerSecUSec,CPUQuotaPeriodUSec,'
        'MemoryMax,MemorySwapMax,TasksMax,LimitCPU,LimitAS,LimitFSIZE,KillMode,KillSignal,'
        'ProtectSystem,ProtectControlGroups,PrivateUsers,TemporaryFileSystem,OpenFile,CPUAffinity')
    done = subprocess.run(['/usr/bin/systemctl', '--user', 'show', unit, '--property='+fields],
                          env=host_env(), capture_output=True, text=True, timeout=timeout)
    require(len(done.stdout) < 32768 and len(done.stderr) < 2048, 'SYSTEMD_STATUS_BOUND')
    return dict(line.split('=', 1) for line in done.stdout.splitlines() if '=' in line)


def owned_cgroup(unit, relative):
    require(re.fullmatch(UNIT_PATTERN, unit) is not None, 'FOREIGN_UNIT_FORBIDDEN')
    root = Path('/sys/fs/cgroup/user.slice')/('user-'+str(os.getuid())+'.slice')/('user@'+str(os.getuid())+'.service')/'app.slice'
    require(relative == '/'+str(root.relative_to('/sys/fs/cgroup'))+'/'+unit, 'FOREIGN_CGROUP_FORBIDDEN')
    return Path('/sys/fs/cgroup')/relative.lstrip('/')


def cgroup_read(path):
    result = {}
    for name in ('cpu.stat', 'memory.peak', 'memory.events', 'memory.oom.group', 'cgroup.procs',
                 'cgroup.events', 'pids.events', 'cpu.max', 'cpu.max.burst', 'memory.max',
                 'memory.swap.max', 'pids.max'):
        try:
            result[name] = (Path(path)/name).read_text()[:4096]
        except (OSError, ValueError):
            pass
    return result


def cpu_usec(snapshot):
    return int(dict(line.split() for line in snapshot.get('cpu.stat', '').splitlines()).get('usage_usec', 0))


def kill_owned(unit, cgroup=None):
    require(re.fullmatch(UNIT_PATTERN, unit) is not None, 'FOREIGN_UNIT_FORBIDDEN')
    if cgroup is not None:
        require(Path(cgroup) == owned_cgroup(unit, '/'+str(Path(cgroup).relative_to('/sys/fs/cgroup'))),
                'FOREIGN_CGROUP_FORBIDDEN')
    if cgroup is not None and (Path(cgroup)/'cgroup.kill').exists():
        (Path(cgroup)/'cgroup.kill').write_text('1')
    else:
        subprocess.run(['/usr/bin/systemctl', '--user', 'kill', '--kill-whom=all', '--signal=SIGKILL', unit],
                       env=host_env(), capture_output=True, timeout=2)


def wait_empty(cgroup, deadline):
    if cgroup is None:
        return True
    while True:
        snapshot = cgroup_read(cgroup)
        populated = dict(line.split() for line in snapshot.get('cgroup.events', '').splitlines()).get('populated', '0')
        if not snapshot.get('cgroup.procs', '').strip() and populated == '0':
            return True
        if time.monotonic() >= deadline:
            return False
        kill_owned(Path(cgroup).name, cgroup)
        time.sleep(.01)


def records(path, cap=65536):
    path = Path(path)
    if not path.exists():
        return []
    require(path.stat().st_size <= cap, 'HOST_STREAM_BOUND')
    result = []
    for line in path.read_text(errors='replace').splitlines():
        if len(line) > 16384:
            continue
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def project_build_record(row):
    encoded = json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(len(encoded) <= 8192, 'PAYLOAD_RECORD_BOUND')
    if len(encoded) <= 2048:
        return row
    projected = {'kind': row.get('kind'), 'metadata_projection_only': True,
                 'full_record_sha256': hashlib.sha256(encoded).hexdigest(),
                 'full_record_location': 'capped stdout/stderr journal; canonical JSON record SHA256'}
    priority = ('valid', 'mode', 'pid', 'source_identity', 'profile_identity',
                'native_zero_ME_verified', 'new_ME_calls', 'new_integrals',
                'retained_physical_events', 'status', 'command_index',
                'commands_completed', 'completed_replicas', 'reason')
    for key in priority:
        value = row.get(key)
        if key not in row or type(value) not in (str, bool, int, float) or isinstance(value, str) and len(value) > 512:
            continue
        candidate = dict(projected, **{key: value})
        if len(json.dumps(candidate, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= 2048:
            projected = candidate
    require(len(json.dumps(projected, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= 2048,
            'BUILD_METADATA_PROJECTION_BOUND')
    return projected


def build_record_summary(path, cap):
    # Final transport is finite and quiescent after cgroup teardown. Stream it
    # rather than materializing every command/checkpoint in the host receipt.
    # The complete raw journal remains in its capped file with its own SHA256.
    path = Path(path)
    if not path.exists():
        return {'records': [], 'record_count': 0, 'canonical_JSONL_sha256': hashlib.sha256(b'').hexdigest(),
                'build_entered': False, 'zero_ME_verified': False}
    require(path.stat().st_size <= cap, 'HOST_STREAM_BOUND')
    selected = {}; count = 0; h = hashlib.sha256(); entered = False; proven = False
    with path.open('rb') as stream:
        for raw in stream:
            if len(raw) > 16384:
                continue
            try:
                row = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(row, dict):
                continue
            encoded = json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            require(len(encoded) <= 8192, 'PAYLOAD_RECORD_BOUND')
            h.update(encoded+b'\n'); count += 1; kind = row.get('kind')
            if kind == 'ATTESTED' and 'first_attested' not in selected:
                selected['first_attested'] = (count, project_build_record(row))
            if kind == 'BUILD_CHECKPOINT':
                selected['last_checkpoint'] = (count, project_build_record(row))
            if kind in ('BUILD_ONLY_COMPLETE', 'COMPLETE', 'FAILED', 'BUILD_FAILED'):
                selected['last_terminal'] = (count, project_build_record(row))
            if kind in ('BUILD_PREPARE_ENTERED', 'BUILD_ONLY_COMPLETE'):
                entered = True
            if (kind == 'BUILD_ONLY_COMPLETE' and row.get('native_zero_ME_verified') is True and
                    all(type(row.get(key)) is int and row[key] == 0 for key in
                        ('new_ME_calls', 'new_integrals', 'retained_physical_events'))):
                proven = True
    return {'records': [row for _, row in sorted(selected.values(), key=lambda item: item[0])],
            'record_count': count, 'canonical_JSONL_sha256': h.hexdigest(),
            'build_entered': entered, 'zero_ME_verified': proven,
            'selection': 'first ATTESTED, last BUILD_CHECKPOINT, last COMPLETE/FAILED terminal; selected rows max2048B; full capped journal retained'}


def _payload_observations(output, p):
    rows = []
    for name in (*artifact_names(p), 'index.bin', 'stdout.log', 'stderr.log'):
        q = output/name; s = q.lstat()
        require(stat.S_ISREG(s.st_mode) and not q.is_symlink() and s.st_nlink == 1,
                'HOST_OUTPUT_NOT_UNIQUE_REGULAR_FILE')
        require(s.st_size <= p['per_regular_file_bytes'], 'HOST_OUTPUT_FILE_CAP_EXCEEDED')
        allocated = s.st_blocks*512
        require(allocated <= p['per_regular_file_bytes'], 'HOST_OUTPUT_ALLOCATED_CAP_EXCEEDED')
        rows.append({'path': name, 'bytes': s.st_size, 'allocated_bytes': allocated, 'sha256': digest(q)})
    return rows


def _start(case, output, *, mode='fixture', revision=None, human_tty=None):
    require(mode in ('fixture', 'BUILD_ONLY') and case in CASES, 'UNREVIEWED_FIXTURE_CASE')
    require(mode == 'fixture' or case == 'normal' and human_tty is not None, 'MANUAL_BUILD_ENTRY_REQUIRED')
    p = load_profile(mode); output = fresh(output, mode)
    require(os.statvfs(output.parent).f_frsize == p['host_allocation_granule_bytes'], 'UNREVIEWED_HOST_ALLOCATION_GRANULE')
    campaign_lock = prepare_campaign_lock()
    snapshot = source_snapshot(); unit = 'atlas-hh-phase7i-resource-'+uuid.uuid4().hex+'.service'
    output.mkdir(mode=0o700); (output/'work').mkdir(mode=0o700)
    for name in (*artifact_names(p), 'index.bin', 'stdout.log', 'stderr.log'):
        _regular_empty(output/name)
    canary = output/'readonly_canary.txt'
    with canary.open('xb') as stream:
        stream.write(b'INERT_READ_ONLY_CANARY\n'.ljust(p['canary_bytes'], b'.'))
    cmd = fixed_command(case, output, mode, snapshot['identity'], unit, revision=revision, human_tty=human_tty)
    start = time.monotonic()
    handoff = {'schema_version': 1, 'unit': unit, 'output': str(output), 'mode': mode, 'case': case,
        'start_monotonic': start, 'deadline': start+p['aggregate_wall_seconds'],
        'controller_pid': os.getpid(), 'controller_start_ticks': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
        'source_snapshot': snapshot, 'profile': p, 'revision': revision, 'human_tty_transport': human_tty,
        'campaign_lock_identity': campaign_lock,
        'canary_sha256': digest(canary),
        'transport_inodes': {name: (output/name).stat().st_ino
                             for name in (*artifact_names(p), 'index.bin', 'stdout.log', 'stderr.log')}}
    try:
        done = subprocess.run(cmd, env=host_env(), capture_output=True, text=True,
                              timeout=p['unit_start_seconds']+1)
        require(len(done.stdout) <= 2048 and len(done.stderr) <= 4096, 'LAUNCH_DIAGNOSTIC_BOUND')
        require(done.returncode == 0, 'SERVICE_LAUNCH_FAILED:'+done.stderr[:1000])
        new_json(output/'launch.json', {'handoff': handoff, 'command': cmd, 'launch_exit': done.returncode})
        return handoff
    except BaseException as exc:
        # A manager call may time out after creating the unit: always kill only
        # our exact unit, preserving its failed fresh workspace and diagnostics.
        cg = None
        try:
            q = unit_properties(unit)
            if q.get('ControlGroup'):
                cg = owned_cgroup(unit, q['ControlGroup'])
            kill_owned(unit, cg)
            subprocess.run(['/usr/bin/systemctl', '--user', 'stop', unit], env=host_env(),
                           capture_output=True, timeout=2)
        finally:
            empty = wait_empty(cg, handoff['deadline'])
            new_json(output/'failure.json', {'status': 'FAILED_LAUNCH_PRESERVED', 'reason': str(exc),
                'unit': unit, 'empty_cgroup_after_cleanup': empty, 'new_ME_calls': 0,
                'new_integrals': 0, 'new_events': 0})
        raise


def start_job(case, output, *, mode='fixture'):
    require(mode == 'fixture', 'BUILD_ONLY_REQUIRES_SEPARATE_MANUAL_START_BUILD')
    return _start(case, output, mode=mode)


def _current_human_tty():
    # Resolve the operator's actual controlling PTY, not manager /dev/tty.
    # No character is read and no review capability is created on this host.
    fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        require(os.isatty(fd) and os.tcgetpgrp(fd) == os.getpgrp(), 'FOREGROUND_CONTROLLING_HUMAN_TTY_REQUIRED')
        tty_nr = int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[4])
        require(tty_nr > 0, 'CONTROLLING_TTY_DEVICE_REQUIRED')
        nodes = []
        for node in Path('/dev/pts').iterdir():
            if not re.fullmatch(r'[0-9]+', node.name) or node.is_symlink():
                continue
            facts = node.stat()
            if stat.S_ISCHR(facts.st_mode) and facts.st_rdev == tty_nr:
                nodes.append((node, facts))
        require(len(nodes) == 1, 'UNAMBIGUOUS_CURRENT_HUMAN_PTY_REQUIRED')
        node, facts = nodes[0]
        return fd, {'path': str(node), 'rdev': facts.st_rdev, 'inode': facts.st_ino}
    except BaseException:
        os.close(fd)
        raise


def start_build(output, revision):
    # Full host setup/controller/postprocessing containment is not implemented.
    # This cannot be enabled by flags, environment, receipt, or a TTY response.
    raise ValueError('COMPLETE_CONTROLLER_RESOURCE_ENVELOPE_NOT_IMPLEMENTED')


def _start_build_transport_proposal(output, revision):
    # Non-executed transport design only. Never bypass the public full-controller
    # block using this private helper. A future repaired worker would request
    # manual exact-scope confirmation after new external BUILD_ONLY approval
    # and constructs HumanReview in that same PID. Transport grants nothing.
    # This entry performs neither binary review nor physical restart.
    require(re.fullmatch(r'[0-9a-f]{40}', revision or '') is not None, 'EXACT_REVIEWED_REVISION_REQUIRED')
    fd, tty = _current_human_tty()  # before host output or unit creation
    try:
        return _start('normal', output, mode='BUILD_ONLY', revision=revision, human_tty=tty)
    finally:
        os.close(fd)


def _validate_handoff(h):
    require(h['mode'] in ('fixture', 'BUILD_ONLY') and h['case'] in CASES, 'UNREVIEWED_HANDOFF')
    require(h['mode'] == 'fixture' or h['case'] == 'normal', 'UNREVIEWED_BUILD_HANDOFF')
    p = load_profile(h['mode']); require(h['profile'] == p, 'HANDOFF_PROFILE_DRIFT')
    require(re.fullmatch(UNIT_PATTERN, h['unit']) is not None, 'FOREIGN_UNIT_FORBIDDEN')
    output = Path(h['output']); root = Path.home()/'simulations'/('hh_phase7i_resource_closure' if h['mode'] == 'fixture' else 'hh_final_closure')
    require(output.is_absolute() and '..' not in output.parts and output != root and output.is_relative_to(root)
            and not any(q.is_symlink() for q in (output, *output.parents)), 'FOREIGN_OUTPUT_FORBIDDEN')
    require(h['deadline'] == h['start_monotonic']+p['aggregate_wall_seconds'], 'HANDOFF_DEADLINE_DRIFT')
    require(source_snapshot() == h['source_snapshot'], 'RESOURCE_SOURCE_CHANGED_DURING_FIXTURE')
    if h['case'] == 'controller_loss':
        require(h['controller_pid'] != os.getpid(), 'CONTROLLER_LOSS_REQUIRES_SEPARATE_OBSERVER')
        original = Path('/proc')/str(h['controller_pid'])/'stat'
        try:
            ticks = original.read_text().rsplit(')', 1)[1].split()[19]
        except FileNotFoundError:
            ticks = None
        require(ticks != h['controller_start_ticks'], 'ORIGINAL_CONTROLLER_STILL_ALIVE')
    return output, p


def monitor_job(handoff):
    h = handoff; output, p = _validate_handoff(h); unit = h['unit']
    cgroup = None; initial = None; observed = []; last = {}; stop = None; leftovers = []
    try:
        while True:
            left = h['deadline']-time.monotonic()
            if left <= 0:
                stop = 'TOTAL_WALL_EARLY_STOP'; kill_owned(unit, cgroup); break
            last = unit_properties(unit, timeout=min(2, max(.05, left)))
            if last.get('ControlGroup'):
                cgroup = owned_cgroup(unit, last['ControlGroup']); value = cgroup_read(cgroup)
                observed.append(value)
                if initial is None:
                    initial = value
                if h['case'] != 'controller_loss' and cpu_usec(value) >= p['CPU_watchdog_stop_usec']:
                    stop = 'AGGREGATE_CPU_EARLY_STOP'; kill_owned(unit, cgroup); break
            if last.get('SubState') == 'exited' or last.get('ActiveState') in ('failed', 'inactive') or last.get('LoadState') == 'not-found':
                break
            time.sleep(p['poll_seconds'])
        if cgroup is not None:
            # Observe escaped group members before killing the entire cgroup.
            leftovers = [int(v) for v in cgroup_read(cgroup).get('cgroup.procs', '').split()]
            if leftovers and stop is None:
                stop = 'RESIDUAL_CGROUP_PROCESSES'
        last = unit_properties(unit)
    finally:
        if cgroup is not None:
            kill_owned(unit, cgroup)
            require(wait_empty(cgroup, h['deadline']), 'RESIDUAL_PROCESS_AFTER_CGROUP_KILL')
            # Capture cached final cgroup statistics after every payload task
            # has gone, before stopping/unloading the transient unit.
            final = unit_properties(unit)
            if final.get('LoadState') != 'not-found':
                last = final
        subprocess.run(['/usr/bin/systemctl', '--user', 'stop', unit], env=host_env(),
                       capture_output=True, text=True, timeout=2)
        require(wait_empty(cgroup, h['deadline']), 'RESIDUAL_PROCESS_AFTER_CGROUP_KILL')
    elapsed = time.monotonic()-h['start_monotonic']
    if h['mode'] == 'fixture':
        logs = records(output/'stdout.log', p['per_regular_file_bytes'])
        errors = records(output/'stderr.log', p['per_regular_file_bytes'])
        stdout_summary = stderr_summary = None
    else:
        stdout_summary = build_record_summary(output/'stdout.log', p['per_regular_file_bytes'])
        stderr_summary = build_record_summary(output/'stderr.log', p['per_regular_file_bytes'])
        logs, errors = stdout_summary['records'], stderr_summary['records']
    cpu = max([cpu_usec(v) for v in observed] +
              [int(last.get('CPUUsageNSec', '0'))//1000 if last.get('CPUUsageNSec', '0').isdigit() else 0])
    peak = max([int(v.get('memory.peak', '0')) for v in observed] +
               [int(last.get('MemoryPeak', '0')) if last.get('MemoryPeak', '0').isdigit() else 0])
    require(source_snapshot() == h['source_snapshot'], 'RESOURCE_SOURCE_CHANGED_DURING_FIXTURE')
    require(digest(output/'readonly_canary.txt') == h['canary_sha256'], 'READONLY_CANARY_WAS_MODIFIED')
    require(not list((output/'work').iterdir()), 'WORK_TMPFS_SHADOWED_HOST_DIRECTORY')
    for name, inode in h['transport_inodes'].items():
        require((output/name).stat().st_ino == inode, 'HOST_TRANSPORT_INODE_REPLACED')
    transport = _payload_observations(output, p)
    canary_allocated = (output/'readonly_canary.txt').stat().st_blocks*512
    require(canary_allocated <= p['host_allocation_granule_bytes'], 'HOST_CANARY_ALLOCATED_BOUND')
    allocated_upper = (p['work_tmpfs_bytes']+p['tmp_tmpfs_bytes']+sum(row['allocated_bytes'] for row in transport)+
                       p['host_metadata_files']*p['host_metadata_bytes']+p['source_control_reserve_bytes']+canary_allocated+
                       (0 if p['campaign_lock_reserve_in_source_control'] else p['campaign_lock_allocated_reserve_bytes']))
    require(allocated_upper <= profile_bounds(p)['maximum_data_disk_bytes'] < p['aggregate_disk_bytes'],
            'ACTUAL_ALLOCATED_DATA_DISK_BOUND_EXCEEDED')
    proof = [row for row in logs if row.get('kind') == 'ATTESTED']
    require(proof and proof[0].get('valid') is True, 'EFFECTIVE_KERNEL_LIMIT_ATTESTATION_MISSING')
    require(cpu <= p['aggregate_CPU_seconds']*1000000, 'ACTUAL_AGGREGATE_CPU_EXCEEDED')
    # Host observation/stop latency is reported separately; payload timestamps
    # must independently pass the original wall ceiling, never this allowance.
    a, b = last.get('ExecMainStartTimestampMonotonic', ''), last.get('ExecMainExitTimestampMonotonic', '')
    native_wall = (int(b)-int(a))/1000000 if a.isdigit() and b.isdigit() and int(b) >= int(a) > 0 else None
    require(native_wall is not None and native_wall <= p['aggregate_wall_seconds'], 'ACTUAL_PAYLOAD_WALL_MISSING_OR_EXCEEDED')
    require(elapsed <= p['aggregate_wall_seconds']+.5, 'HOST_CLEANUP_WALL_OVERRUN')
    result = {'schema_version': 1, 'evidence_class': 'SYNTHETIC_METHOD_ONLY', 'case': h['case'],
        'unit': unit, 'profile': p, 'initial_cgroup': initial, 'last_unit_properties': last,
        'max_observed_CPU_usec': cpu, 'max_observed_memory_bytes': peak,
        'payload_wall_seconds': native_wall, 'elapsed_including_host_cleanup_seconds': elapsed,
        'resource_stop': stop, 'residual_pids_detected': leftovers, 'residual_processes_after_cleanup': [],
        'stdout_records': logs, 'stderr_records': errors, 'last_observed_cgroup': observed[-1] if observed else {},
        'source_snapshot_identity': h['source_snapshot']['identity'], 'host_work_directory_empty': True,
        'canary_preserved': True, 'cgroup_empty_and_unpopulated_verified': True,
        'controller_pid': h['controller_pid'], 'observer_pid': os.getpid(),
        'controller_exited_verified': h['case'] == 'controller_loss',
        'observer_is_separate_process': h['case'] == 'controller_loss',
        'host_payload_files': transport, 'bounds': profile_bounds(p),
        'measured_host_payload_allocated_bytes': sum(row['allocated_bytes'] for row in transport),
        'actual_data_disk_upper_bytes': allocated_upper, 'host_canary_allocated_bytes': canary_allocated,
        'formal_build_mode_launched': h['mode'] == 'BUILD_ONLY',
        'formal_build_executed': h['mode'] == 'BUILD_ONLY' and stdout_summary['build_entered'],
        'full_parser_or_physics_authorized': False}
    if h['mode'] == 'fixture':
        result.update(ZERO)
    else:
        proven = stdout_summary['zero_ME_verified']
        result['stdout_record_summary'] = {k: v for k, v in stdout_summary.items() if k != 'records'}
        result['stderr_record_summary'] = {k: v for k, v in stderr_summary.items() if k != 'records'}
        result.update({key: 0 if proven else None for key in ZERO})
        result['zero_ME_evidence_verified'] = proven
    new_json(output/'result.json', result)
    return result


def run_job(case, output, *, mode='fixture'):
    return monitor_job(start_job(case, output, mode=mode))

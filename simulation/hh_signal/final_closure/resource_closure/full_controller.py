"""Single-service inert lifecycle controller; persistent storage remains blocked.

Only launch-live-diagnostic is executable. It runs no compiler, loader, MG5,
authorization or resource stress. Production and the 47-case campaign require
an independently verified persistent capacity sink and remain hard blocked.
"""
from __future__ import annotations
import argparse, hashlib, json, os, resource, signal, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
WORK = Path('/var/tmp')
UNIT = 'atlas-hh-phase7i-full-controller-live-01.service'
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


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1048576), b''):
            h.update(part)
    return h.hexdigest()


def lifecycle_bounds():
    # Type=exec: one Pre start timeout + main activation timeout + runtime;
    # StopPost and remaining group termination each receive TimeoutStopSec.
    # Conservative extra stop interval included. Scheduler/timer latency has
    # no hard realtime guarantee; actual elapsed readback is still mandatory.
    stages = {'pre_start': 1, 'main_activation': 1, 'main_runtime': 8,
              'main_stop': .5, 'stop_post': .5, 'final_group_kill': .5}
    seconds = sum(stages.values())
    return {'timer_budget_seconds': seconds, 'stage_budgets_seconds': stages,
            'quota_duration_CPU_upper_seconds': .3 * seconds + .003,
            'aggregate_wall_cap_seconds': 13, 'aggregate_CPU_cap_seconds': 4,
            'timer_scheduling_overrun_not_a_realtime_guarantee': True}


def mount_row(path, lines):
    values = [x.split() for x in lines if len(x.split()) > 6 and x.split()[4] == str(path)]
    require(len(values) == 1, 'EXACT_MOUNT_REQUIRED:' + str(path))
    value = values[0]
    require(value[value.index('-') + 1] == 'tmpfs', 'TMPFS_REQUIRED')
    require({'rw', 'nosuid', 'nodev', 'noexec'} <= set(value[5].split(',')), 'TMPFS_FLAGS')
    return value


def attestation(stage):
    rows = Path('/proc/self/cgroup').read_text().splitlines()
    require(len(rows) == 1 and rows[0].startswith('0::/'), 'CGROUP_V2_REQUIRED')
    relative = Path(rows[0][3:])
    parts = relative.parts
    prefix = ('/', 'user.slice', 'user-%d.slice' % os.getuid(),
              'user@%d.service' % os.getuid(), 'app.slice')
    require(parts[:5] == prefix, 'OWN_USER_SERVICE_SLICE_REQUIRED')
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
    lines = Path('/proc/self/mountinfo').read_text().splitlines()
    mounts = []
    for path, size, inodes in ((WORK, 8388608, 1024), (Path('/tmp'), 1048576, 256)):
        mount_row(path, lines)
        v = os.statvfs(path)
        require(v.f_blocks * v.f_frsize == size and v.f_files == inodes, 'TMPFS_CAP_MISMATCH')
        mounts.append({'path': str(path), 'capacity_bytes': size, 'inodes': inodes,
                       'free_bytes': v.f_bfree * v.f_frsize, 'free_inodes': v.f_ffree})
    writable = sorted(x.split()[4] for x in lines if 'rw' in x.split()[5].split(','))
    require(writable == sorted([str(WORK), '/tmp']), 'UNACCOUNTED_WRITABLE_MOUNT')
    raw = {}
    for key in ('cpu.stat', 'memory.current', 'memory.peak', 'memory.swap.current',
                'cgroup.events', 'cgroup.procs'):
        try:
            raw[key] = (aggregate / key).read_text().strip()
        except FileNotFoundError:
            raw[key] = None
    cpu = dict(x.split() for x in raw['cpu.stat'].splitlines())
    return {'stage': stage, 'pid': os.getpid(), 'membership': str(relative),
            'aggregate_cgroup': str(aggregate), 'leaf_cgroup': str(leaf),
            'mount_namespace_inode': os.stat('/proc/self/ns/mnt').st_ino,
            'effective': values, 'limits': limits, 'mounts': mounts,
            'writable_mounts': writable, 'raw': raw,
            'CPU_usage_usec': int(cpu['usage_usec']),
            'memory_peak_bytes': int(raw['memory.peak']) if raw['memory.peak'] is not None else None,
            'LISTEN_FDS': os.environ.get('LISTEN_FDS'),
            'LISTEN_FDNAMES': os.environ.get('LISTEN_FDNAMES')}


def emit(value):
    raw = canonical(value) + b'\n'
    require(len(raw) <= 32768, 'BOUNDED_RECORD_REQUIRED')
    while raw:
        written = os.write(1, raw)
        require(written > 0, 'SHORT_RECEIPT_WRITE')
        raw = raw[written:]


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


def workflow():
    start = time.monotonic()
    initial = attestation('main_before_preprovision')
    records = []
    tree = WORK / 'controller'
    created = False
    failure = None
    try:
        tree.mkdir(mode=0o700)
        created = True
        records.append({'phase': PHASES[0], 'location': str(tree), 'persistent_writes': 0})
        sys.path.insert(0, str(REPO))
        from simulation.hh_signal.final_closure.integration_runtime.contract import check_revision
        revision = subprocess.run(['/usr/bin/git', 'rev-parse', 'HEAD'], cwd=REPO,
                                  capture_output=True, text=True, timeout=1, check=True).stdout.strip()
        checked = check_revision(revision, full=True)
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
        proc = subprocess.Popen(['/usr/bin/python3', '-I', '-B', str(HERE / 'full_controller.py'),
                                 'inert-child'], cwd=tree, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        try:
            output, errors = proc.communicate(timeout=1)
            require(proc.returncode == 0 and not errors and len(output) <= 8192,
                    'INERT_CHILD_FAILED_OR_OUTPUT_BOUND')
            detail = json.loads(output)
            require(detail['proof']['aggregate_cgroup'] == initial['aggregate_cgroup'],
                    'SIBLING_CHILD_CGROUP_FORBIDDEN')
            require(detail['proof']['mount_namespace_inode'] == initial['mount_namespace_inode'],
                    'CHILD_MOUNT_NAMESPACE_CHANGED')
            records.append({'phase': PHASES[3], 'child': detail})
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=.2)
        (tree / 'inert_preparation.txt').write_text('NO COMPILER OR NATIVE DISPATCH\n')
        records.append({'phase': PHASES[4], 'compiler_invocations': 0})
        receipt = {'kind': 'VOLATILE_WORKFLOW_RECEIPT', 'phases': records, **ZERO}
        data = canonical(receipt)
        require(len(data) <= 24576, 'VOLATILE_RECEIPT_BOUND')
        (tree / 'receipt.json').write_bytes(data)
        records.append({'phase': PHASES[5], 'bytes': len(data), 'sha256': sha(tree / 'receipt.json'),
                        'storage': 'PRIVATE_SIZE_AND_INODE_CAPPED_TMPFS'})
        after = check_revision(revision, full=True)
        require(after['source_identity'] == checked['source_identity'], 'SOURCE_CHANGED')
        require(sha(tree / 'receipt.json') == hashlib.sha256(data).hexdigest(), 'RECEIPT_CHANGED')
        records.append({'phase': PHASES[6], 'source_preserved': True, 'receipt_integrity': True})
    except BaseException as error:
        failure = error
        raise
    finally:
        try:
            if created:
                # Fixed known files only; no recursive deletion/path traversal.
                for name in ('inert_preparation.txt', 'receipt.json'):
                    (tree / name).unlink(missing_ok=True)
                tree.rmdir()
        except BaseException as cleanup_error:
            if failure is None:
                raise
            emit({'kind': 'CLEANUP_FAILED', 'original_reason': str(failure)[:512],
                  'cleanup_reason': str(cleanup_error)[:512], **ZERO})
    records.append({'phase': PHASES[7], 'fixed_scratch_removed': True})
    emit({'kind': 'MAIN_LIFECYCLE_RECEIPT', 'status': 'PASS_VOLATILE_DIAGNOSTIC',
          'proof_initial': initial, 'proof_final': attestation('main_after_cleanup'),
          'records': records, 'main_elapsed_seconds': time.monotonic() - start,
          'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED': False,
          'FULL_LAUNCH_ENVELOPE_VERIFIED': False,
          'persistent_output_hard_bound': 'BLOCKED', 'resource_matrix_cases_executed': 0, **ZERO})


def properties():
    # New protocol uses no OpenFile and no mutable host transport paths. Each
    # Exec command gets a separate namespace; scratch is intentionally unshared.
    executable = '/usr/bin/python3 -I -B ' + str(HERE / 'full_controller.py')
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
            'ExecStartPre=' + executable + ' stage-pre',
            'ExecStopPost=' + executable + ' stage-post']


def launch_command():
    return ['/usr/bin/systemd-run', '--user', '--quiet', '--wait', '--pipe', '--unit', UNIT,
            *[v for prop in properties() for v in ('--property', prop)],
            '/usr/bin/python3', '-I', '-B', str(HERE / 'full_controller.py'), 'workflow']


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('action', choices=('launch-live-diagnostic', 'stage-pre', 'stage-post',
                                         'workflow', 'inert-child', 'full-campaign', 'BUILD_ONLY'))
    args = parser.parse_args(argv)
    if args.action == 'launch-live-diagnostic':
        # Minimal fixed activation only: no source/hash/provision/result work.
        # Fixed unit identity refuses accidental concurrent/replacement runs.
        os.execv('/usr/bin/systemd-run', launch_command())
    try:
        if args.action == 'BUILD_ONLY':
            run_formal_build()
        elif args.action == 'full-campaign':
            run_full_campaign()
        elif args.action == 'workflow':
            workflow()
        elif args.action == 'inert-child':
            child()
        else:
            emit({'kind': args.action.upper().replace('-', '_'),
                  'proof': attestation(args.action),
                  'service_result': os.environ.get('SERVICE_RESULT'), **ZERO})
        return 0
    except BaseException as error:
        emit({'kind': 'BLOCKED', 'action': args.action, 'reason': str(error)[:1024],
              'FULL_LAUNCH_ENVELOPE_VERIFIED': False, **ZERO})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

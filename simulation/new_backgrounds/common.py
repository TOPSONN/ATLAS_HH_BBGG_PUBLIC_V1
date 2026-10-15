"""Explicit one-use human authorization and bounded local subprocess policy."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import ctypes
import json
import math
import os
import re
import shutil
import signal
import subprocess
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
BASE = '05cff9a5d991ba6782b339bc41932ae4da296d8c'
ACK = 'PHASE6G_THREE_NEW_BACKGROUNDS_FULL_CHAIN_1K_V1'
GIB = 1024**3
CAMPAIGN = REPO/'.local/phase6g_backgrounds/campaigns'
AUTHORIZATION_SOURCE_SHA256 = '65b25230b2c50c1c4c7bb253887a8934268732dfca8be9b05eb8aed18fd22d91'
PROCESSES = {'zh': {'label':'B04_ZH','pythia_seed':610401,'delphes_seed':610501},
             'tth':{'label':'B05_TTH','pythia_seed':610402,'delphes_seed':610502},
             'bbgj':{'label':'B06_BBGJ','pythia_seed':610403,'delphes_seed':610503}}


class Blocked(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Blocked(message)


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def strict_json(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2*1024**2,
            'missing/unsafe/oversized JSON receipt')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(_):
        raise Blocked('nonfinite JSON value')
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique, parse_constant=invalid)
    def finite_tree(item):
        if type(item) is float:
            require(math.isfinite(item), 'nonfinite JSON numeric overflow')
        if isinstance(item, dict):
            for nested in item.values():
                finite_tree(nested)
        elif isinstance(item, list):
            for nested in item:
                finite_tree(nested)
    finite_tree(value)
    require(type(value) is dict, 'JSON object required')
    return value


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    with temporary.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')
    os.replace(temporary, path)



def request(args):
    require(args.process in PROCESSES and type(args.events) is int and args.events==1000,
            'only reviewed zh/tth/bbgj with1000 source events per explicit command are supported')
    require(type(args.seed) is int and 1<=args.seed<=900000000,'invalid MG5 seed')
    require(type(args.energy) in (int,float) and args.energy==13000,'only13000GeV is frozen')
    require(type(args.dry_run) is bool,'literal dry-run flag required')
    for value,ceiling,name in ((args.max_hours,4,'hours'),(args.max_disk_gb,10,'GiB')):
        require(type(value) in (int,float) and math.isfinite(value) and 0<value<=ceiling,'bounded positive '+name+' cap required')
    require(args.output is not None,'fresh explicit local output is required')
    return {'process':args.process,'events':1000,'seed':args.seed,'energy_gev':13000,
            'output':str(Path(args.output).expanduser().resolve()),'max_hours':float(args.max_hours),
            'max_disk_gb':float(args.max_disk_gb)}


def bridge_identity(repo=REPO):
    repo=Path(repo);folder=repo/'simulation/new_backgrounds'
    bundle=strict_json(repo/'simulation/zh_pilot/config/bundle.json')
    paths=[repo/'simulation/zh_pilot/config/bundle.json']
    for entry in bundle['files']:
        path=repo/entry['path'];require(sha_file(path)==entry['sha256'],'frozen Phase6F card/config changed');paths.append(path)
    paths.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.cxx','.hxx','.json','.dat','.mg5','.cmnd','.sh'} and
                 not {'tests','evidence','__pycache__'} & set(p.relative_to(folder).parts))
    for name in ('simulation/mg5/scripts','simulation/pythia8/scripts','simulation/pythia8/include','simulation/pythia8/src',
                 'simulation/delphes/scripts','simulation/delphes/include','simulation/zh_pilot/scripts'):
        paths.extend(p for p in (repo/name).glob('*') if p.is_file() and p.suffix in {'.py','.cxx','.hxx','.sh'})
    paths.extend([repo/'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl',repo/'simulation/pythia8/config/baseline_shower.cmnd'])
    entries=[]
    for path in sorted(set(paths)):
        require(not path.is_symlink() and path.resolve().is_relative_to(repo.resolve()),'unsafe executable source binding')
        entries.append({'path':path.relative_to(repo).as_posix(),'sha256':sha_file(path)})
    return hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(',',':')).encode()).hexdigest(),entries


def reserve_campaign(output,requested,identity):
    """One attempt per exact fresh output; batch authorization tracked separately."""
    marker=Path(output)/'source_attempt_reservation.json'
    record={'schema_version':1,'status':'RESERVED_ONE_SOURCE_ATTEMPT_NOT_GENERATION_PROOF','campaign_id':str(uuid.uuid4()),
            'authorization_command':ACK,'authorization_source_sha256':AUTHORIZATION_SOURCE_SHA256,
            'request':requested,'bridge_sha256':identity,'reviewed_base_head':BASE,'source_event_ceiling':1000,
            'created_at_utc':datetime.now(timezone.utc).isoformat()}
    with marker.open('x',encoding='utf-8',newline='\n') as stream:json.dump(record,stream,indent=2,allow_nan=False);stream.write('\n')
    return record


def tree_bytes(directory,readonly_roots=()):
    directory=Path(directory).resolve();roots=[directory,*[Path(p).resolve() for p in readonly_roots]];size=0
    for path in directory.rglob('*'):
        if path.is_symlink():
            target=path.resolve();require(any(target.is_relative_to(root) for root in roots),'output symlink escapes reviewed roots')
            require(target.exists() or target.is_relative_to(directory),'dangling installed-resource symlink');size+=path.lstat().st_size
        elif path.is_file():size+=path.stat().st_size
    return size

def availability(output, requested):
    ancestor = Path(output)
    while not ancestor.exists():
        ancestor = ancestor.parent
    require(Path('/proc/meminfo').is_file(), 'BLOCKED_RESOURCES: Linux resource accounting required')
    mem = {line.split(':')[0]: int(line.split()[1])*1024 for line in
           Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:', 'MemTotal:'))}
    cpus = len(os.sched_getaffinity(0))
    free = shutil.disk_usage(ancestor).free
    require(cpus >= 1 and mem['MemAvailable'] >= 2*GIB and free >= requested['max_disk_gb']*GIB+512*1024**2,
            'BLOCKED_RESOURCES: require one CPU, 2 GiB available RAM and budget plus512MiB free')
    return {'logical_cpus_available': cpus, 'workers': 1, 'memory_available_bytes': mem['MemAvailable'],
            'memory_total_bytes': mem['MemTotal'], 'disk_free_bytes': free,
            'projected_runtime_seconds': 'UNKNOWN', 'projected_peak_memory_bytes': 'UNKNOWN',
            'projected_output_bytes': 'UNKNOWN',
            'scope': 'current availability and conservative minimums, not a ZH capacity benchmark'}


class Monitor:
    """Enforced elapsed stop; polled aggregate-output/RAM stop with retained partials."""
    def __init__(self, output, requested, env=None, started=None, readonly_roots=()):
        self.output, self.requested = Path(output), requested
        self.started = time.monotonic() if started is None else started
        self.peak_rss = 0
        self.peak_disk = 0
        self.executions = []
        self.env = dict(os.environ if env is None else env)
        self.env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                        NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', MAKEFLAGS='-j1',
                        PYTHONDONTWRITEBYTECODE='1')
        self.stopped = False
        self.handlers = {}
        self.readonly_roots = tuple(readonly_roots)
        self.subreaper_original = None
        self.known_processes = {}
        self.baseline_children = set()

    def install_signals(self):
        def stop(*_):
            self.stopped = True
        self.handlers = {sig: signal.signal(sig, stop) for sig in (signal.SIGINT, signal.SIGTERM)}

    def restore_signals(self):
        for sig, handler in self.handlers.items():
            signal.signal(sig, handler)
        if self.subreaper_original is not None:
            ctypes.CDLL(None, use_errno=True).prctl(36, self.subreaper_original, 0, 0, 0)
            self.subreaper_original = None

    def enable_subreaper(self):
        if self.subreaper_original is None:
            library = ctypes.CDLL(None, use_errno=True)
            previous = ctypes.c_int()
            require(library.prctl(37, ctypes.byref(previous), 0, 0, 0) == 0 and
                    library.prctl(36, 1, 0, 0, 0) == 0,
                    'BLOCKED_RESOURCES: Linux child-subreaper supervision unavailable')
            self.subreaper_original = previous.value

    @staticmethod
    def process_stats():
        rows = {}
        for path in Path('/proc').glob('[0-9]*/stat'):
            try:
                fields = path.read_text().rsplit(')', 1)[1].split()
                rows[int(path.parent.name)] = {'state': fields[0], 'parent': int(fields[1]),
                    'group': int(fields[2]), 'start': int(fields[19])}
            except (OSError, ValueError, IndexError):
                pass
        return rows

    def owned_processes(self, leader):
        rows = self.process_stats()
        owned = {pid for pid, start in self.known_processes.items()
                 if pid in rows and rows[pid]['start'] == start}
        if leader in rows and (leader not in self.known_processes or rows[leader]['start'] == self.known_processes[leader]):
            owned.add(leader)
        # The subreaper adopts even an escaped session that forks and exits
        # between samples. Exclude any pre-existing unrelated direct children.
        owned |= {pid for pid, row in rows.items() if row['parent'] == os.getpid()
                  and pid not in self.baseline_children}
        changed = True
        while changed:
            before = len(owned)
            verified_group = any(rows[pid]['group'] == leader for pid in owned)
            owned |= {pid for pid, row in rows.items() if row['parent'] in owned or (verified_group and row['group'] == leader)}
            changed = len(owned) != before
        for pid in owned:
            self.known_processes[pid] = rows[pid]['start']
        return {pid: rows[pid] for pid in owned}

    def observe_processes(self, leader):
        owned = self.owned_processes(leader)
        require(not any(row['state'] != 'Z' and row['group'] != leader for row in owned.values()),
                'FAILED_ESCAPED_SESSION: child left supervised process group')
        rss = 0
        for pid in owned:
            try:
                line = next(v for v in Path(f'/proc/{pid}/status').read_text().splitlines() if v.startswith('VmRSS:'))
                rss += int(line.split()[1])*1024
            except (OSError, StopIteration, ValueError):
                pass
        return rss

    def check(self):
        require(not self.stopped and not (self.output/'STOP').exists(), 'PARTIAL_STOPPED')
        require(time.monotonic()-self.started < self.requested['max_hours']*3600, 'PARTIAL_TIMEOUT')
        size = tree_bytes(self.output, self.readonly_roots)
        self.peak_disk = max(self.peak_disk, size)
        # A reserve lets monitoring stop before the nominal output ceiling.
        reserve = min(256*1024**2, int(self.requested['max_disk_gb']*GIB/20))
        require(size < self.requested['max_disk_gb']*GIB-reserve and
                shutil.disk_usage(self.output).free >= 256*1024**2, 'PARTIAL_DISK_LIMIT')

    @staticmethod
    def process_tree(pid):
        values = {}
        for path in Path('/proc').glob('[0-9]*/stat'):
            try:
                tail = path.read_text().rsplit(')', 1)[1].split()
                values[int(path.parent.name)] = (int(tail[1]), int(tail[2]))
            except (OSError, ValueError, IndexError):
                continue
        related = {pid}
        changed = True
        while changed:
            before = len(related)
            related |= {p for p, (parent, group) in values.items() if parent in related or group == pid}
            changed = len(related) != before
        return related

    @classmethod
    def process_tree_rss(cls, pid):
        rss = 0
        for process in cls.process_tree(pid):
            try:
                line = next(v for v in Path(f'/proc/{process}/status').read_text().splitlines() if v.startswith('VmRSS:'))
                rss += int(line.split()[1])*1024
            except (OSError, StopIteration, ValueError):
                pass
        return rss

    @staticmethod
    def group_members(pid):
        members = set()
        for path in Path('/proc').glob('[0-9]*/stat'):
            try:
                fields = path.read_text().rsplit(')', 1)[1].split()
                # A dead zombie is not an executing descendant.
                if int(fields[2]) == pid and fields[0] != 'Z':
                    members.add(int(path.parent.name))
            except (OSError, ValueError, IndexError):
                continue
        return members

    def terminate_group(self, child):
        # Kill group even when its original leader has already exited.
        targets = self.owned_processes(child.pid)
        for sig in (signal.SIGTERM, signal.SIGKILL):
            # TERM handlers may fork into a new session. Discover descendants
            # again before KILL, keeping start-time identity checks.
            targets.update(self.owned_processes(child.pid))
            if any(row['group'] == child.pid for row in targets.values()):
                try:
                    os.killpg(child.pid, sig)
                except ProcessLookupError:
                    pass
            current = self.process_stats()
            for pid, row in targets.items():
                if pid == os.getpid():
                    continue
                if pid not in current or current[pid]['start'] != row['start']:
                    continue
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            if sig == signal.SIGTERM:
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired as error:
            raise ValueError('FAILED_CHILD_CLEANUP: leader survived KILL') from error
        deadline=time.monotonic()+2
        while True:
            targets.update(self.owned_processes(child.pid))
            current=self.process_stats()
            for pid,row in targets.items():
                if pid!=os.getpid() and pid in current and current[pid]['start']==row['start'] and current[pid]['state']!='Z':
                    try:os.kill(pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                if pid!=child.pid:
                    try:os.waitpid(pid,os.WNOHANG)
                    except ChildProcessError:pass
            alive={pid:row for pid,row in self.owned_processes(child.pid).items() if row['state']!='Z'}
            if not alive:break
            require(time.monotonic()<deadline,'FAILED_CHILD_CLEANUP: owned descendants survived KILL')
            time.sleep(.05)

    def run_command(self, argv, cwd, stage, env=None, expected_exit_code=0):
        require(os.name == 'posix', 'Linux process-group supervision required')
        require(re.fullmatch('[a-z0-9_]+', stage) is not None, 'unsafe stage name')
        require(type(expected_exit_code) is int and expected_exit_code in (0,2), 'invalid expected stage exit')
        if expected_exit_code == 2:
            require(stage in ('shower_background_missing_authorization','validate_background_hepmc3_missing_authorization') and
                    len(argv) == 1 and Path(argv[0]).name == stage.removesuffix('_missing_authorization'),
                    'nonzero exit is permitted only for named no-argument native authorization probes')
        self.check()
        self.enable_subreaper()
        self.known_processes = {}
        self.baseline_children = {pid for pid, row in self.process_stats().items() if row['parent'] == os.getpid()}
        log_path = self.output/'logs'/f'{stage}.log'
        log_path.parent.mkdir(exist_ok=True)
        require(not log_path.exists(), 'stage already attempted; automatic retries forbidden')
        began = time.monotonic()
        peak = 0
        child = None
        failure = None
        child_env = dict(self.env)
        if env:
            child_env.update(env)
        # Caller-specific library paths cannot relax threading/scratch policy.
        for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                    'VECLIB_MAXIMUM_THREADS', 'MAKEFLAGS', 'PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX', 'TMPDIR'):
            if key in self.env:
                child_env[key] = self.env[key]
        with log_path.open('xb') as log:
            try:
                child = subprocess.Popen(list(argv), cwd=cwd, env=child_env, stdout=log,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                initial = self.process_stats().get(child.pid)
                if initial:
                    self.known_processes[child.pid] = initial['start']
                while child.poll() is None:
                    peak = max(peak, self.observe_processes(child.pid))
                    self.peak_rss = max(self.peak_rss, peak)
                    self.check()
                    memory = next(line for line in Path('/proc/meminfo').read_text().splitlines()
                                  if line.startswith('MemAvailable:'))
                    require(int(memory.split()[1])*1024 >= 256*1024**2, 'PARTIAL_MEMORY_PRESSURE')
                    time.sleep(.2)
                require(not any(row['state'] != 'Z' for row in self.owned_processes(child.pid).values()),
                        'FAILED_ORPHANED_STAGE: live descendant after leader exit')
            except BaseException as error:
                failure = error
                if child:
                    try:
                        self.terminate_group(child)
                    except (OSError,ValueError,subprocess.SubprocessError) as cleanup_error:
                        failure=ValueError(str(error)+'; '+str(cleanup_error))
        result = {'stage': stage, 'argv': list(argv), 'exit_code': child.returncode if child else None,
                  'expected_exit_code': expected_exit_code,
                  'log_path': str(log_path), 'elapsed_seconds': time.monotonic()-began,
                  'peak_process_tree_rss_bytes': peak or 'UNKNOWN', 'log_sha256': sha_file(log_path),
                  'failure': str(failure) if failure else None}
        self.executions.append(result)
        if failure:
            raise failure
        self.check()
        require(child.returncode == expected_exit_code, 'FAILED_STAGE: '+stage+'; retained actual log')
        return result

    def metrics(self):
        return {'elapsed_seconds': time.monotonic()-self.started,
                'peak_sampled_process_tree_rss_bytes': self.peak_rss or 'UNKNOWN',
                'observed_output_bytes': tree_bytes(self.output, self.readonly_roots), 'peak_observed_output_bytes': self.peak_disk,
                'scope': 'actual polled process-tree RSS/output; unsampled instantaneous peaks UNKNOWN',
                'monitor_interval_seconds': .2, 'subprocesses': self.executions}

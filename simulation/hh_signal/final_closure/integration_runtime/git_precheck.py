"""Full tracked-worktree verification with a separate, finite Git budget.

This module cannot dispatch an integrator. Keep status semantics; plumbing-only
shortcuts are deliberately not used as a cleanliness certificate.
"""
import hashlib, math, os, re, resource, signal, stat, subprocess, tempfile, threading, time
from pathlib import Path

COMMAND_SECONDS = 30
STATUS_SECONDS = 120
PREFLIGHT_SECONDS = 180
PREFLIGHT_CPU_SECONDS = 30
OUTPUT_BYTES = 1024 * 1024
EXPECTED_REMOTE = 'https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1.git'

class GitPrecheckError(ValueError):
    def __init__(self, reason, diagnostics=()):
        super().__init__(reason)
        self.diagnostics = list(diagnostics)

def require(ok, reason):
    if not ok: raise GitPrecheckError(reason)

def sha(data): return hashlib.sha256(data).hexdigest()

class GitGuard:
    """SIGALRM bounds the whole preflight, including Python filesystem reads.

    Per-command wall/CPU/stream limits are independent of that watchdog. A
    timeout/error always kills and reaps the command's entire process group.
    These limits do not touch the later physical integration Budget.
    """
    def __init__(self, repo, *, wall=PREFLIGHT_SECONDS, cpu=PREFLIGHT_CPU_SECONDS,
                 command=COMMAND_SECONDS, status=STATUS_SECONDS):
        self.repo=Path(repo);self.wall=wall;self.cpu=cpu;self.command=command;self.status=status
        self.records=[];self.child_cpu=0.;self.active=None
    def __enter__(self):
        require(threading.current_thread() is threading.main_thread(), 'GIT_PREFLIGHT_MAIN_THREAD_REQUIRED')
        require(signal.getitimer(signal.ITIMER_REAL)==(0.,0.), 'EXISTING_WALL_WATCHDOG')
        self.start=time.monotonic();self.own=time.process_time()
        self.handler=signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM,self.alarm)
        signal.setitimer(signal.ITIMER_REAL,self.wall)
        return self
    def alarm(self, *_): raise GitPrecheckError('GIT_PREFLIGHT_WALL_WATCHDOG',self.records)
    def __exit__(self, typ, exc, tb):
        try:
            if self.active is not None:self.kill(self.active)
        finally:
            if isinstance(exc,GitPrecheckError):exc.diagnostics=list(self.records)
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,self.handler)
    @staticmethod
    def kill(child):
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait(timeout=3)
    def spent_cpu(self):return self.child_cpu+time.process_time()-self.own
    def check(self):
        require(time.monotonic()-self.start<self.wall,'GIT_PREFLIGHT_WALL_WATCHDOG')
        require(self.spent_cpu()<self.cpu,'GIT_PREFLIGHT_CPU_BUDGET')
    def git(self,*args):
        self.check()
        forbidden=('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_NAMESPACE')
        require(not any(os.environ.get(k) for k in forbidden),'UNSAFE_GIT_ENVIRONMENT')
        env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','LC_ALL':'C'}
        limit=self.status if args and args[0]=='status' else self.command
        remaining=max(1,math.ceil(self.cpu-self.spent_cpu()))
        def limits():
            resource.setrlimit(resource.RLIMIT_CPU,(remaining,remaining))
            resource.setrlimit(resource.RLIMIT_FSIZE,(OUTPUT_BYTES,OUTPUT_BYTES))
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        start=time.monotonic();reason=None;out=b'';err=b'';code=None;usage=None
        with tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
            try:
                child=subprocess.Popen(['git','-C',str(self.repo),*args],env=env,stdout=stdout,stderr=stderr,
                    start_new_session=True,preexec_fn=limits)
                self.active=child
                while True:
                    pid,ws,ru=os.wait4(child.pid,os.WNOHANG)
                    if pid:
                        code=os.waitstatus_to_exitcode(ws);usage=ru;child.returncode=code
                        self.child_cpu+=ru.ru_utime+ru.ru_stime;break
                    self.check()
                    if time.monotonic()-start>=limit:raise GitPrecheckError('GIT_COMMAND_TIMEOUT:'+args[0])
                    fields=(Path('/proc')/str(child.pid)/'stat')
                    try:
                        values=fields.read_text().rsplit(')',1)[1].split()
                        active_cpu=(int(values[11])+int(values[12]))/os.sysconf('SC_CLK_TCK')
                        require(self.spent_cpu()+active_cpu<self.cpu,'GIT_PREFLIGHT_CPU_BUDGET')
                    except FileNotFoundError:pass
                    require(os.fstat(stdout.fileno()).st_size<OUTPUT_BYTES and os.fstat(stderr.fileno()).st_size<OUTPUT_BYTES,'GIT_OUTPUT_CAP')
                    time.sleep(.02)
                self.check()
            except BaseException as exc:
                reason=str(exc)
                raise
            finally:
                if self.active is not None:
                    self.kill(self.active)
                    if code is None:code=self.active.returncode
                    self.active=None
                stdout.seek(0);stderr.seek(0);out=stdout.read(OUTPUT_BYTES);err=stderr.read(OUTPUT_BYTES)
                row={'argv':list(args),'exit':code,'reason':reason,'timed_out':bool(reason and ('TIMEOUT' in reason or 'WALL_WATCHDOG' in reason)),
                     'wall_seconds':time.monotonic()-start,
                     'CPU_seconds':None if usage is None else usage.ru_utime+usage.ru_stime,
                     'kernel_ru_maxrss_bytes':None if usage is None else usage.ru_maxrss*1024,
                     'stdout_bytes':len(out),'stderr_bytes':len(err),'stdout_sha256':sha(out),'stderr_sha256':sha(err),
                     'stderr_excerpt':err[:512].decode('utf-8','replace'),'group_cleanup':True}
                self.records.append(row)
        require(code==0,'GIT_SUBPROCESS_FAILURE:'+args[0]+':'+str(code))
        require(not err,'GIT_UNEXPECTED_DIAGNOSTIC:'+args[0])
        require(len(out)<OUTPUT_BYTES,'GIT_OUTPUT_CAP')
        return out

def regular_bytes(repo,relative):
    path=Path(relative)
    require(not path.is_absolute() and '..' not in path.parts,'UNSAFE_TRACKED_PATH')
    full=repo/path
    require(not any(q.is_symlink() for q in [full,*full.parents]),'UNEXPECTED_SYMLINK')
    info=full.lstat()
    require(stat.S_ISREG(info.st_mode) and os.access(full,os.R_OK),'INACCESSIBLE_TRACKED_FILE')
    require(info.st_size<=OUTPUT_BYTES,'CRITICAL_FILE_SIZE_CAP')
    return full.read_bytes()

def verify_checkout(repo,revision,required,physics_path,physics_sha,*,remote=EXPECTED_REMOTE,guard_options=None):
    """No reduced path filter: both status scans cover the entire tracked tree.

    Critical paths additionally match exact reviewed blob bytes. Index/HEAD and
    critical hashes are checked again after the scan to detect intervening edits.
    This is a bounded observation, not an atomic lock against a later writer.
    """
    require(re.fullmatch('[0-9a-f]{40}',revision or '') is not None,'EXACT_REVIEWED_REVISION_REQUIRED')
    repo=Path(repo)
    require(repo.resolve()==repo and not repo.is_symlink(),'REPOSITORY_ROOT_SYMLINK')
    with GitGuard(repo,**(guard_options or {})) as guard:
        require(guard.git('rev-parse','HEAD').decode().strip()==revision,'REVIEWED_REVISION_MISMATCH')
        require(Path(guard.git('rev-parse','--show-toplevel').decode().strip()).resolve()==repo,'REPOSITORY_ROOT_MISMATCH')
        require(Path(guard.git('rev-parse','--absolute-git-dir').decode().strip()).resolve()==repo/'.git','UNREVIEWED_GIT_LAYOUT')
        require(guard.git('config','--get','remote.origin.url').decode().strip()==remote,'REPOSITORY_REMOTE_MISMATCH')
        required=list(required() if callable(required) else required)
        settings=guard.git('config','--get-regexp',r'^core\.(filemode|fsmonitor|ignorestat)$').decode().splitlines()
        require(not any(s.startswith('core.fsmonitor ') and s.split(' ',1)[1].lower() not in ['false','0','no','off'] for s in settings),'UNREVIEWED_FSMONITOR')
        index=sha(regular_bytes(repo,'.git/index'))
        entries=guard.git('ls-files','--stage','-z').split(b'\0');tracked=set();metadata={}
        for entry in entries:
            if not entry:continue
            meta,name=entry.split(b'\t',1);mode,oid,stage=meta.split()
            require(stage==b'0' and mode in [b'100644',b'100755'],'UNMERGED_SYMLINK_OR_SUBMODULE_INDEX')
            rel=os.fsdecode(name);tracked.add(rel)
            full=repo/rel
            require(not any(q.is_symlink() for q in [full,*full.parents]) and stat.S_ISREG(full.lstat().st_mode) and os.access(full,os.R_OK),'INACCESSIBLE_OR_SYMLINK_TRACKED_PATH')
            s=full.lstat();metadata[rel]=(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        tags=guard.git('ls-files','-v','-z').split(b'\0')
        require(all(not row or (row[:1]==b'H') for row in tags),'HIDDEN_INDEX_FLAGS')
        monitored=guard.git('ls-files','-f','-z').split(b'\0')
        require(all(not row or row[:1]==b'H' for row in monitored),'FSMONITOR_VALID_INDEX_FLAGS')
        require((set(required)|{physics_path})<=tracked,'MISSING_REQUIRED_TRACKED_PATH')
        expected={name:sha(guard.git('cat-file','blob',revision+':'+name)) for name in sorted(set(required)|{physics_path})}
        require(expected[physics_path]==physics_sha,'REVIEWED_PHYSICS_CONTRACT_DRIFT')
        initial={name:sha(regular_bytes(repo,name)) for name in expected}
        require(initial==expected,'REVIEWED_CRITICAL_BYTES_DRIFT')
        require(not guard.git('status','--porcelain','--untracked-files=no'),'DIRTY_TRACKED_CHECKOUT')
        require(not guard.git('status','--porcelain','--untracked-files=no'),'DIRTY_TRACKED_CHECKOUT')
        require({name:sha(regular_bytes(repo,name)) for name in expected}==initial,'CRITICAL_INPUT_RACE')
        for rel,before in metadata.items():
            s=(repo/rel).lstat()
            require((s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==before,'TRACKED_METADATA_RACE')
        require(sha(regular_bytes(repo,'.git/index'))==index,'GIT_INDEX_CHANGED_DURING_PREFLIGHT')
        require(guard.git('rev-parse','HEAD').decode().strip()==revision,'HEAD_CHANGED_DURING_PREFLIGHT')
        guard.check()
        return {'status':'PASS_FULL_TRACKED_PREFLIGHT','tracked_files':len(tracked),'index_sha256':index,
            'critical_source_sha256':initial,'commands':guard.records,'wall_seconds':time.monotonic()-guard.start,
            'CPU_seconds':guard.spent_cpu(),'limits':{'command_seconds':guard.command,'status_seconds':guard.status,
                'overall_wall_seconds':guard.wall,'overall_CPU_seconds':guard.cpu},
            'atomicity':'repeated checks detect observed changes; a later concurrent write remains possible; no execution authorization'}

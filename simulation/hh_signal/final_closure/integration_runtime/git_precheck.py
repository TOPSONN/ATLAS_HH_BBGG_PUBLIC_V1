"""Full tracked-worktree verification with a separate, finite Git budget.

This module cannot dispatch an integrator. Keep status semantics; plumbing-only
shortcuts are deliberately not used as a cleanliness certificate.
"""
import hashlib, math, os, re, resource, selectors, signal, stat, subprocess, tempfile, threading, time
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
                 command=COMMAND_SECONDS, status=STATUS_SECONDS, outer_watchdog=None):
        self.outer_watchdog=outer_watchdog;self.borrowed=False
        self.repo=Path(repo);self.wall=wall;self.cpu=cpu;self.command=command;self.status=status
        self.records=[];self.child_cpu=0.;self.active=None
    def __enter__(self):
        require(threading.current_thread() is threading.main_thread(), 'GIT_PREFLIGHT_MAIN_THREAD_REQUIRED')
        self.start=time.monotonic();self.own=time.process_time()
        if self.outer_watchdog is not None:
            from simulation.hh_signal.final_closure.resource_closure.job_envelope import PeriodicEnvelope
            require(type(self.outer_watchdog) is PeriodicEnvelope,'UNREVIEWED_OUTER_WATCHDOG')
            require(self.outer_watchdog.assert_active_timer() is True,'OUTER_WATCHDOG_NOT_ACTIVE')
            self.borrowed=True
        else:
            require(signal.getitimer(signal.ITIMER_REAL)==(0.,0.), 'EXISTING_WALL_WATCHDOG')
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
            if not self.borrowed:
                signal.setitimer(signal.ITIMER_REAL,0)
                signal.signal(signal.SIGALRM,self.handler)
    @staticmethod
    def kill(child):
        primary=None
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        except BaseException as exc:primary=exc
        try:child.wait(timeout=3)
        except BaseException as exc:
            if primary is None:raise
            primary.git_wait_error=type(exc).__name__
        if primary is not None:raise primary
    def spent_cpu(self):return self.child_cpu+time.process_time()-self.own
    def check(self):
        if self.outer_watchdog is not None:
            require(self.outer_watchdog.assert_active_timer() is True,'OUTER_WATCHDOG_NOT_ACTIVE')
        require(time.monotonic()-self.start<self.wall,'GIT_PREFLIGHT_WALL_WATCHDOG')
        require(self.spent_cpu()<self.cpu,'GIT_PREFLIGHT_CPU_BUDGET')
    def git(self,*args,stdin_bytes=None):
        self.check()
        require(stdin_bytes is None or isinstance(stdin_bytes,bytes) and len(stdin_bytes)<=65536,'GIT_INPUT_CAP')
        forbidden=('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_NAMESPACE')
        require(not any(os.environ.get(k) for k in forbidden),'UNSAFE_GIT_ENVIRONMENT')
        env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','LC_ALL':'C'}
        limit=self.status if args and args[0]=='status' else self.command
        remaining=max(1,math.ceil(self.cpu-self.spent_cpu()))
        def limits():
            self.child_limits(remaining)
        if self.outer_watchdog is not None:
            return self.git_pipes(args,env,stdin_bytes,limit,limits)
        start=time.monotonic();reason=None;out=b'';err=b'';code=None;usage=None
        with tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
            try:
                child=subprocess.Popen(['git','-C',str(self.repo),*args],env=env,stdout=stdout,stderr=stderr,
                    stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
                    start_new_session=True,preexec_fn=limits)
                self.active=child
                if stdin_bytes is not None:child.stdin.write(stdin_bytes);child.stdin.close()
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
                    if self.active.stdin is not None and not self.active.stdin.closed:self.active.stdin.close()
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
                if stdin_bytes is not None:row.update(stdin_bytes=len(stdin_bytes),stdin_sha256=sha(stdin_bytes))
                self.records.append(row)
        require(code==0,'GIT_SUBPROCESS_FAILURE:'+args[0]+':'+str(code))
        require(not err,'GIT_UNEXPECTED_DIAGNOSTIC:'+args[0])
        require(len(out)<OUTPUT_BYTES,'GIT_OUTPUT_CAP')
        return out

    @staticmethod
    def child_limits(remaining):
        """Never raise an inherited finite soft or hard limit in the child."""
        for which,requested in [(resource.RLIMIT_CPU,remaining),
                (resource.RLIMIT_FSIZE,OUTPUT_BYTES),(resource.RLIMIT_CORE,0)]:
            soft,hard=resource.getrlimit(which)
            bound=min([requested]+[v for v in (soft,hard) if v!=resource.RLIM_INFINITY])
            resource.setrlimit(which,(bound,bound))

    def git_pipes(self,args,env,stdin_bytes,limit,limits):
        """Borrowed-envelope Git streams stay in bounded incremental RAM.

        This does not alter the inherited file-size limit or reduce the full
        checkout/status/blob scope. No temporary regular output files exist.
        """
        start=time.monotonic();reason=None;code=None;usage=None
        buffers={'stdout':bytearray(),'stderr':bytearray()};offset=0
        child=None;cleanup_error=None;cleanup_reason=None;cleanup_wait_error=None;fd_errors=[];selector_error=None
        selector=selectors.DefaultSelector()
        try:
            child=subprocess.Popen(['git','-C',str(self.repo),*args],env=env,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
                start_new_session=True,preexec_fn=limits,bufsize=0)
            self.active=child
            for name in ('stdout','stderr'):
                stream=getattr(child,name);os.set_blocking(stream.fileno(),False)
                selector.register(stream,selectors.EVENT_READ,name)
            if stdin_bytes is not None:
                os.set_blocking(child.stdin.fileno(),False)
                if stdin_bytes:selector.register(child.stdin,selectors.EVENT_WRITE,'stdin')
                else:child.stdin.close()
            while selector.get_map() or code is None:
                self.check()
                if time.monotonic()-start>=limit:raise GitPrecheckError('GIT_COMMAND_TIMEOUT:'+args[0])
                if code is None:
                    pid,ws,ru=os.wait4(child.pid,os.WNOHANG)
                    if pid:
                        code=os.waitstatus_to_exitcode(ws);usage=ru;child.returncode=code
                        self.child_cpu+=ru.ru_utime+ru.ru_stime
                    else:
                        fields=Path('/proc')/str(child.pid)/'stat'
                        try:
                            values=fields.read_text().rsplit(')',1)[1].split()
                            active_cpu=(int(values[11])+int(values[12]))/os.sysconf('SC_CLK_TCK')
                            require(self.spent_cpu()+active_cpu<self.cpu,'GIT_PREFLIGHT_CPU_BUDGET')
                        except FileNotFoundError:pass
                for key,mask in selector.select(.02):
                    stream=key.fileobj;name=key.data
                    if name=='stdin':
                        try:
                            block=stdin_bytes[offset:offset+4096]
                            written=os.write(stream.fileno(),block)
                            require(type(written) is int and 0<written<=len(block),'INVALID_GIT_PIPE_WRITE')
                            offset+=written
                        except BrokenPipeError:raise GitPrecheckError('GIT_INPUT_CLOSED_BEFORE_COMPLETE')
                        except BlockingIOError:continue
                        if offset==len(stdin_bytes):selector.unregister(stream);stream.close()
                    else:
                        try:data=os.read(stream.fileno(),4096)
                        except BlockingIOError:continue
                        require(type(data) is bytes and len(data)<=4096,'INVALID_GIT_PIPE_READ')
                        if not data:selector.unregister(stream);stream.close();continue
                        room=OUTPUT_BYTES-len(buffers[name])
                        buffers[name].extend(data[:room])
                        require(len(data)<room,'GIT_OUTPUT_CAP')
            self.check()
        except BaseException as exc:
            reason=str(exc)
            raise
        finally:
            if child is not None:
                try:self.kill(child)
                except BaseException as exc:
                    cleanup_error=type(exc).__name__;cleanup_reason=str(exc)[:256]
                    cleanup_wait_error=getattr(exc,'git_wait_error',None)
                if code is None:code=child.returncode
                for name in ('stdin','stdout','stderr'):
                    stream=getattr(child,name,None)
                    if stream is not None and not stream.closed:
                        try:stream.close()
                        except BaseException as exc:fd_errors.append(type(exc).__name__)
            self.active=None
            try:selector.close()
            except BaseException as exc:selector_error=type(exc).__name__
            cleanup_complete=cleanup_error is None and not fd_errors and selector_error is None
            out=bytes(buffers['stdout']);err=bytes(buffers['stderr'])
            row={'argv':list(args),'exit':code,'reason':reason,
                 'timed_out':bool(reason and ('TIMEOUT' in reason or 'WALL_WATCHDOG' in reason)),
                 'wall_seconds':time.monotonic()-start,
                 'CPU_seconds':None if usage is None else usage.ru_utime+usage.ru_stime,
                 'kernel_ru_maxrss_bytes':None if usage is None else usage.ru_maxrss*1024,
                 'stdout_bytes':len(out),'stderr_bytes':len(err),'stdout_sha256':sha(out),'stderr_sha256':sha(err),
                 'stderr_excerpt':err[:512].decode('utf-8','replace'),'group_cleanup':cleanup_complete,
                 'group_termination':'CONFIRMED' if cleanup_error is None else 'UNKNOWN',
                 'fd_cleanup':'UNKNOWN' if fd_errors else 'CONFIRMED',
                 'selector_cleanup':'UNKNOWN' if selector_error else 'CONFIRMED',
                 'capture_mode':'BOUNDED_PIPE_RAM','child_limit_policy':'NEVER_RAISE_INHERITED_LIMITS'}
            if cleanup_error is not None:
                row.update(cleanup_error=cleanup_error,cleanup_reason=cleanup_reason)
                if cleanup_wait_error is not None:row['cleanup_wait_error']=cleanup_wait_error
            if fd_errors:row['fd_cleanup_errors']=fd_errors[:3]
            if selector_error is not None:row['selector_cleanup_error']=selector_error
            if stdin_bytes is not None:row.update(stdin_bytes=len(stdin_bytes),stdin_sha256=sha(stdin_bytes))
            self.records.append(row)
            if not cleanup_complete and reason is None:
                raise GitPrecheckError('GIT_GROUP_CLEANUP_FAILED',self.records)
        require(code==0,'GIT_SUBPROCESS_FAILURE:'+args[0]+':'+str(code))
        require(not err,'GIT_UNEXPECTED_DIAGNOSTIC:'+args[0])
        require(len(out)<OUTPUT_BYTES,'GIT_OUTPUT_CAP')
        return out

    def blob_hashes(self,revision,names,sizes):
        """Same exact blobs, bounded batches; no status or hash scope reduction."""
        batches=[];batch=[];size=0
        for name in names:
            require('\n' not in name and '\r' not in name,'UNSAFE_BATCH_BLOB_PATH')
            amount=sizes[name]+128
            require(amount<OUTPUT_BYTES-65536,'CRITICAL_BATCH_FILE_SIZE_CAP')
            if batch and (size+amount>=OUTPUT_BYTES-65536 or len(batch)>=128):
                batches.append(batch);batch=[];size=0
            batch.append(name);size+=amount
        if batch:batches.append(batch)
        hashes={}
        for batch in batches:
            requests=''.join(revision+':'+name+'\n' for name in batch).encode()
            data=self.git('cat-file','--batch',stdin_bytes=requests)
            hashes.update(parse_blob_batch(data,batch))
        return hashes

def parse_blob_batch(data,names):
    offset=0;result={}
    for name in names:
        end=data.find(b'\n',offset);require(end>=offset,'TRUNCATED_GIT_BLOB_HEADER')
        fields=data[offset:end].split();require(len(fields)==3 and re.fullmatch(b'[0-9a-f]{40}',fields[0]) and
            fields[1]==b'blob' and fields[2].isdigit(),'MISSING_OR_INVALID_GIT_BLOB')
        size=int(fields[2]);require(size<OUTPUT_BYTES,'GIT_BLOB_SIZE_CAP');offset=end+1
        require(offset+size<len(data) and data[offset+size:offset+size+1]==b'\n','TRUNCATED_GIT_BLOB_BODY')
        body=data[offset:offset+size];offset+=size+1
        require(hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest().encode()==fields[0],'GIT_BLOB_HEADER_IDENTITY_DRIFT')
        result[name]=sha(body)
    require(offset==len(data),'UNEXPECTED_GIT_BATCH_PAYLOAD')
    return result

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
        critical_names=sorted(set(required)|{physics_path})
        expected=guard.blob_hashes(revision,critical_names,{name:metadata[name][3] for name in critical_names})
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

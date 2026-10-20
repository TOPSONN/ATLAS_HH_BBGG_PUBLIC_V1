"""Unprivileged kernel write envelope and bounded process-group supervisor."""
import ctypes,fcntl,hashlib,math,os,platform,resource,selectors,signal,stat,subprocess,time
from pathlib import Path
from .contract import *

class PathRule(ctypes.Structure):
    _pack_=1
    _fields_=[('access',ctypes.c_uint64),('fd',ctypes.c_int32)]

def landlock(files,scratch):
    require(platform.machine()=='x86_64','UNREVIEWED_LANDLOCK_ARCHITECTURE')
    c=ctypes.CDLL(None,use_errno=True)
    abi=c.syscall(444,0,0,1)
    require(abi>=3,'LANDLOCK_ABI3_REQUIRED')
    rights=sum(1<<i for i in [1,*range(4,15)])
    attr=ctypes.c_uint64(rights);fd=c.syscall(444,ctypes.byref(attr),8,0)
    require(fd>=0,'LANDLOCK_RULESET_CREATION')
    try:
        for path,access in [(p,(1<<1)|(1<<14)) for p in files]+[(scratch,(1<<1)|(1<<5)|(1<<8)|(1<<14))]:
            pfd=os.open(path,os.O_PATH|os.O_CLOEXEC|os.O_NOFOLLOW)
            try:
                rule=PathRule(access,pfd)
                require(c.syscall(445,fd,1,ctypes.byref(rule),0)==0,'LANDLOCK_ALLOWLIST_RULE')
            finally:os.close(pfd)
        require(c.prctl(38,1,0,0,0)==0,'NO_NEW_PRIVILEGES')
        require(c.syscall(446,fd,0)==0,'LANDLOCK_RESTRICTION_FAILED')
    finally:os.close(fd)

def disk_bytes(root,pid=None):
    total=0;anonymous={}
    for p in Path(root).rglob('*'):
        require(not p.is_symlink(),'RUNTIME_SYMLINK')
        if p.is_file():total+=p.stat().st_size
    if pid:
        for p in (Path('/proc')/str(pid)/'fd').glob('*'):
            try:
                s=p.stat()
                if stat.S_ISREG(s.st_mode) and s.st_nlink==0:anonymous[(s.st_dev,s.st_ino)]=s.st_size
            except (FileNotFoundError,PermissionError):pass
    return total+sum(anonymous.values()),len(anonymous)

class Budget:
    def __init__(self,root,wall=14400,cpu=14400,disk=5*1024**3):
        self.root=Path(root);self.start=time.monotonic();self.cpu_start=resource.getrusage(resource.RUSAGE_CHILDREN)
        self.own_start=time.process_time();self.wall=wall;self.cpu=cpu;self.disk=disk;self.peak_disk=0;self.peak_anonymous=0
    def used_cpu(self):
        r=resource.getrusage(resource.RUSAGE_CHILDREN)
        return r.ru_utime+r.ru_stime-self.cpu_start.ru_utime-self.cpu_start.ru_stime+time.process_time()-self.own_start
    def remaining(self):
        return self.wall-(time.monotonic()-self.start),self.cpu-self.used_cpu()
    def check(self,pid=None):
        wall,cpu=self.remaining()
        if pid:
            try:
                fields=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
                cpu-=(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK')
            except FileNotFoundError:pass
        require(wall>(5 if pid else 0) and cpu>(5 if pid else 0),'RESOURCE_TIME_RESERVE_CEILING')
        size,anon=disk_bytes(self.root,pid)
        if self.root.parent==Path.home()/'simulations/hh_final_closure':
            for p in self.root.parent.glob('authorized_bridge_review_*'):
                if p.is_dir() and p!=self.root:size+=disk_bytes(p)[0]
            size+=64*1024**2  # reserved source, evidence and Git overhead
        self.peak_disk=max(size,self.peak_disk);self.peak_anonymous=max(anon,self.peak_anonymous)
        require(anon<=9,'RESOURCE_UNLINKED_DESCRIPTOR_ENVELOPE')
        # Stop conservatively at 2GiB, retaining 3GiB headroom below the human
        # ceiling for monitored/in-flight files. No disk budget increase.
        require(size<min(self.disk,2*1024**3),'RESOURCE_DISK_RESERVE_CEILING')
        return wall,cpu

def capability(seed,revision):
    fd=os.memfd_create('hh-supervisor',os.MFD_ALLOW_SEALING|os.MFD_CLOEXEC)
    os.write(fd,f'{CONTROL_MAGIC} {os.getpid()} {seed} {PHYSICS_SHA} {revision}\n'.encode())
    fcntl.fcntl(fd,fcntl.F_ADD_SEALS,fcntl.F_SEAL_SEAL|fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_GROW|fcntl.F_SEAL_WRITE)
    return fd

def supervise(argv,work,env,stdin,budget,*,control_fd=None,method_only=False):
    """The public execution path supplies only a hash-verified native binary.

    method_only is available to unit fixtures; it is not a CLI generation mode.
    Raw stdout/stderr are hashed in memory and discarded, never event artifacts.
    Only HI_/H_IO/HH_PRE_SAMPLING scalar protocol records survive.
    """
    work=Path(work);scratch=work/'temporary';require(scratch.is_dir(),'MISSING_PRIVATE_SCRATCH')
    wall,cpu=budget.check();require(cpu>3,'RESOURCE_CPU_RESERVE')
    allowed=[work/n for n in NAMED]
    require(all(p.is_file() and not p.is_symlink() for p in allowed),'MISSING_OUTPUT_INODES')
    parent_pid=os.getpid()
    def setup():
        require(ctypes.CDLL(None).prctl(1,signal.SIGKILL,0,0,0)==0,'PARENT_DEATH_KILL_REQUIRED')
        if os.getppid()!=parent_pid:os._exit(99)
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        limit=max(1,math.floor(cpu-2))
        hard=resource.getrlimit(resource.RLIMIT_CPU)[1]
        if hard!=resource.RLIM_INFINITY:limit=min(limit,hard)
        resource.setrlimit(resource.RLIMIT_CPU,(limit,limit))
        hard=resource.getrlimit(resource.RLIMIT_FSIZE)[1];filecap=FILE_CAP if hard==resource.RLIM_INFINITY else min(FILE_CAP,hard)
        resource.setrlimit(resource.RLIMIT_FSIZE,(filecap,filecap))
        resource.setrlimit(resource.RLIMIT_NOFILE,(32,32))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        hard=resource.getrlimit(resource.RLIMIT_AS)[1];memorycap=2*1024**3 if hard==resource.RLIM_INFINITY else min(2*1024**3,hard)
        resource.setrlimit(resource.RLIMIT_AS,(memorycap,memorycap))
        if not method_only:resource.setrlimit(resource.RLIMIT_NPROC,(0,0))
        landlock(allowed,scratch)
    child=subprocess.Popen(list(map(str,argv)),cwd=work,env={**env,'TMPDIR':str(scratch),
        'OMP_NUM_THREADS':'1','OMP_THREAD_LIMIT':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
        **({'HH_SUPERVISOR_FD':str(control_fd)} if control_fd is not None else {})},
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,
        preexec_fn=setup,pass_fds=(() if control_fd is None else (control_fd,)))
    selector=selectors.DefaultSelector();buffers={};hashes={};sizes={};records=[];diagnostics=[];failure=None;start=time.monotonic()
    for name,stream in [('stdout',child.stdout),('stderr',child.stderr)]:
        os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,name)
        buffers[name]=b'';hashes[name]=hashlib.sha256();sizes[name]=0
    try:
        child.stdin.write(stdin.encode());child.stdin.close()
        while selector.get_map() or child.poll() is None:
            budget.check(child.pid)
            tasks=Path('/proc')/str(child.pid)/'task'
            if tasks.exists():require(len(list(tasks.iterdir()))<=1,'UNAPPROVED_WORKER_OR_THREAD')
            for key,_ in selector.select(.05):
                data=os.read(key.fileobj.fileno(),65536);name=key.data
                if not data:selector.unregister(key.fileobj);continue
                hashes[name].update(data);sizes[name]+=len(data)
                require(sizes[name]<16*1024**2,'RAW_STREAM_SIZE_CAP')
                buffers[name]+=data;require(len(buffers[name])<131072,'RAW_LINE_SIZE_CAP')
                while b'\n' in buffers[name]:
                    raw,buffers[name]=buffers[name].split(b'\n',1);s=raw.decode('utf-8','replace').strip()
                    if s.startswith(('STOP ','Fortran runtime error:')):
                        require(len(s)<4096 and len(diagnostics)<32,'DIAGNOSTIC_CAP');diagnostics.append(s)
                    if s.startswith(('HI_','H_IO ','HH_PRE_SAMPLING_CONFIG_PASS')):
                        if s.startswith(('HI_ME_ENTRY ','HI_ME_RETURN ')):
                            tag=s.split()[0]
                            records[:]=[row for row in records if row.split()[0]!=tag]
                        require(len(s)<4096 and len(records)<2048,'SCALAR_PROTOCOL_CAP');records.append(s)
                        if s.startswith('HI_FAILURE'):raise ValueError(s)
            for p in scratch.iterdir():
                # Fortran may briefly create a scratch inode before unlinking.
                # It may not retain a named scratch object past this bound.
                if p.exists():require(time.time()-p.stat().st_mtime<.25,'NAMED_SCRATCH_RETAINED')
        child.wait();require(child.returncode==0,'NATIVE_EXIT:'+str(child.returncode))
    except BaseException as exc:failure=exc
    finally:
        # Kill the whole group even when its leader exited; reap the leader.
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait();selector.close();child.stdout.close();child.stderr.close()
        if not child.stdin.closed:child.stdin.close()
    receipt={'exit':child.returncode,'pid':child.pid,'process_group_kill_cleanup':True,'wall_seconds':time.monotonic()-start,
        'execution_class':'METHOD_ONLY' if method_only else 'REAL_NATIVE_SUPERVISED',
        'records':records,'raw_streams_retained':False,'raw_stream_bytes':sizes,
        'bounded_runtime_errors':diagnostics,
        'raw_stream_SHA256':{k:v.hexdigest() for k,v in hashes.items()},'failure':None if failure is None else str(failure)}
    if failure:raise StageFailure(receipt) from failure
    budget.check();require(not list(scratch.iterdir()),'NAMED_SCRATCH_POSTCONDITION')
    return receipt

class StageFailure(ValueError):
    def __init__(self,receipt):super().__init__(receipt['failure']);self.receipt=receipt

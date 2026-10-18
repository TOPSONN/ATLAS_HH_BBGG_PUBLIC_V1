"""Bounded sequential compile/link/entry-denial children, never physical launch."""
import ctypes,hashlib,os,resource,signal,subprocess,time
from .contract import require

def invoke(argv,cwd,env,budget,expected=0):
    budget.check();started=time.monotonic();usage=resource.getrusage(resource.RUSAGE_CHILDREN);parent=os.getpid()
    def setup():
        require(ctypes.CDLL(None).prctl(1,signal.SIGKILL,0,0,0)==0,'BUILD_PARENT_DEATH_GUARD')
        if os.getppid()!=parent:os._exit(99)
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    p=subprocess.Popen(list(map(str,argv)),cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,start_new_session=True,preexec_fn=setup)
    failure=None;out=err=''
    try:
        while True:
            try:out,err=p.communicate(timeout=.2);break
            except subprocess.TimeoutExpired:
                budget.check(p.pid);require(time.monotonic()-started<60,'BUILD_COMMAND_WALL_CEILING')
                # Compiler drivers spend CPU in f951/cc1/ld descendants which
                # RUSAGE_CHILDREN reports only after reaping. All inherit one
                # core; elapsed time is a conservative live group-CPU bound.
                require(budget.remaining()[1]>time.monotonic()-started+5,'BUILD_AGGREGATE_CPU_RESERVE')
    except BaseException as exc:failure=exc
    finally:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait()
        if failure:
            out,err=p.communicate(timeout=2)
        p.stdout.close();p.stderr.close()
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    measurement={'argv':list(map(str,argv)),'pid':p.pid,'exit':p.returncode,'wall_seconds':time.monotonic()-started,
        'child_CPU_seconds':after.ru_utime+after.ru_stime-usage.ru_utime-usage.ru_stime,'process_group_kill_cleanup':True,
        'stdout_sha256':hashlib.sha256(out.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(err.encode()).hexdigest(),
        'failure':None if failure is None else str(failure)}
    try:
        if failure:raise failure
        budget.check();require(len(out.encode())+len(err.encode())<=64*1024**2,'BUILD_LOG_CAP')
        require(p.returncode==expected,'BUILD_CHILD_FAILED:'+str(p.returncode)+':'+err[-2000:])
    except BaseException as exc:
        exc.build_measurement=measurement
        raise
    return subprocess.CompletedProcess(argv,p.returncode,out,err),measurement

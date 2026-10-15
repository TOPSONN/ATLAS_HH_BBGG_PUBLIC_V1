"""Bounded future native driver bridge; current authorization always denies."""
import math,os,resource,signal,subprocess,time
from pathlib import Path
from .contract import deny_execution,lock,require,sha,validate_source_inventory
from .controller import command_guard
from .writers import output_audit,workspace_envelope

def execute(binary,expected_sha,work,source_root,source_inventory,*,used_wall=0,used_cpu=0,used_disk=0):
    # Always raises in Phase7F, before touching files or starting a process.
    # The native executable independently has STOP80 before its first ME call.
    deny_execution('runtime integration bridge')
    binary=Path(binary);work=Path(work);caps=lock()['administrative_ceilings']
    command_guard([binary.name]);require(sha(binary)==expected_sha,'UNVERIFIED_NATIVE_BINARY')
    workspace_envelope(source_root,source_inventory,work)
    wall=caps['aggregate_wall_seconds']-used_wall;cpu=caps['aggregate_CPU_seconds']-used_cpu
    disk=caps['additional_disk_bytes']-used_disk
    require(wall>0 and cpu>0 and disk>0,'AGGREGATE_BUDGET_EXHAUSTED')
    def child_setup():
        os.setsid();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(cpu),math.ceil(cpu)))
        resource.setrlimit(resource.RLIMIT_FSIZE,(min(disk,64*1024**2),min(disk,64*1024**2)))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    start=time.monotonic();log=work/'native_stage_stdout.txt'
    with log.open('xb') as stream:
        child=subprocess.Popen([str(binary)],cwd=work,stdout=stream,stderr=subprocess.STDOUT,preexec_fn=child_setup,
            env={**os.environ,'HH_PREFLIGHT_ONLY':'0','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
        try:
            while child.poll() is None:
                require(time.monotonic()-start<wall,'AGGREGATE_WALLTIME_CAP')
                audit=workspace_envelope(source_root,source_inventory,work)
                require(sum(r['bytes'] for r in audit['files'])<disk,'AGGREGATE_DISK_CAP')
                time.sleep(.1)
            require(child.returncode==0,'NATIVE_STAGE_FAILED')
        finally:
            if child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait()
    return workspace_envelope(source_root,source_inventory,work)

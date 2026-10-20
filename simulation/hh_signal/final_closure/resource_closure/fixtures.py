"""Fixed harmless resource fixtures: no compiler, loader, MG5 or HH dispatch."""
from __future__ import annotations
import argparse,errno,json,mmap,os,resource,signal,subprocess,sys,time
from pathlib import Path
PHASES=('preflight','compile','loader','receipt','postflight','export')
MODES=('cpu','ram','wall','disk','abnormal')
SPECIALS=('aggregate_cpu','orphan','controller_loss','pids','source_write',
 'cgroup_write','namespace_escape','stdout_overflow','disk_inodes','tmp_disk',
 'tmp_inodes','chunk_overflow','legacy_missing_approval','archive_bound','allocation_bypass','job_lock')
CASES=('normal',)+tuple(p+'_'+m for p in PHASES for m in MODES)+SPECIALS
ZERO={'MG5_invocations':0,'model_imports':0,'new_ME_calls':0,'new_integrals':0,
 'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,
 'retained_physical_LHE_events':0,'formal_build_executed':False,
 'physical_restart_authorized':False,'human_authorization_created':False}
def require(ok,message):
 if not ok:raise ValueError(message)
def spec(case):
 require(type(case) is str and case in CASES,'FIXED_HARMLESS_CASE_REQUIRED')
 if case=='normal':return {'phase':None,'mode':'normal'}
 for phase in PHASES:
  if case.startswith(phase+'_'):return {'phase':phase,'mode':case[len(phase)+1:]}
 return {'phase':'loader' if case=='orphan' else 'export' if case in
  ('chunk_overflow','archive_bound') else 'preflight','mode':case}
def emit_raw(kind,**value):
 line=json.dumps({'kind':kind,**value},sort_keys=True,separators=(',',':'),allow_nan=False)
 require(len(line.encode())<=8192,'FIXTURE_RECORD_BOUND');print(line,flush=True)
def burn():
 while True:pass
def resident_block():
 # Two resident 300MiB blocks exceed aggregate512MiB; neither exceeds AS512MiB.
 data=mmap.mmap(-1,300*1024**2,flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS)
 for offset in range(0,len(data),4096):data[offset]=1
 return data
def disk_fill(root,*,inodes=False,emit=emit_raw):
 root=Path(root);require(root.is_dir(),'PRIVATE_FIXTURE_DIRECTORY_REQUIRED')
 prefix='inert_%d_'%os.getpid()
 try:
  for index in range(4096 if inodes else 2048):
   with (root/(prefix+str(index))).open('xb') as stream:
    if not inodes:stream.write(b'X'*65536)
  raise ValueError('PRIVATE_TMPFS_LIMIT_NOT_ENFORCED')
 except OSError as error:
  if error.errno!=errno.ENOSPC:raise
  stat=os.statvfs(root);emit('LIMIT_ERROR',check='TMPFS_INODES' if inodes else 'TMPFS_BYTES',
   errno=error.errno,root=str(root),tmpfs_free_inodes=stat.f_ffree,
   tmpfs_used_bytes=(stat.f_blocks-stat.f_bfree)*stat.f_frsize)
  raise
def action(mode,*,work=None,emit=emit_raw):
 require(mode in MODES,'FIXED_HARMLESS_ACTION_REQUIRED')
 if mode=='cpu':burn()
 elif mode=='wall':time.sleep(60)
 elif mode=='ram':
  child=os.fork()
  if child==0:
   data=resident_block()
   while True:time.sleep(1)
  data=resident_block();os.waitpid(child,0)
  raise ValueError('AGGREGATE_RAM_LIMIT_NOT_ENFORCED')
 elif mode=='disk':disk_fill(Path.cwd() if work is None else work,emit=emit)
 else:os._exit(87)
def expected_write_denial(target,text,emit,check):
 try:
  with Path(target).open('w') as stream:stream.write(text)
 except OSError as error:
  require(error.errno in (errno.EROFS,errno.EACCES,errno.EPERM),'UNEXPECTED_WRITE_DENIAL_ERRNO')
  emit('CONTAINED',check=check,errno=error.errno);return
 raise ValueError('OUTSIDE_PRIVATE_NAMESPACE_WRITE_ALLOWED')
def special(case,ctx):
 emit=ctx['emit'];work=Path(ctx['work'])
 if case in ('aggregate_cpu','controller_loss'):
  for _ in range(3):
   if os.fork()==0:burn()
  emit('BUSY_CHILDREN_STARTED',count=3)
  while True:time.sleep(1)
 elif case=='orphan':
  child=os.fork()
  if child==0:os.setsid();time.sleep(60);os._exit(0)
  emit('ORPHAN_CREATED',pid=child,setsid=True);os._exit(0)
 elif case=='pids':
  children=[]
  try:
   for _ in range(32):
    child=os.fork()
    if child==0:time.sleep(60);os._exit(0)
    children.append(child)
  except OSError as error:
   require(error.errno==errno.EAGAIN,'UNEXPECTED_TASK_LIMIT_ERRNO')
   emit('CONTAINED',check='TASKS_MAX',errno=error.errno,created=len(children));return
  raise ValueError('TASKS_MAX_NOT_ENFORCED')
 elif case=='source_write':
  expected_write_denial(ctx['source_canary'],'INERT_FORBIDDEN_CHANGE',emit,'READONLY_CANARY')
 elif case=='cgroup_write':
  cg=Path(ctx['cgroup_path']);expected_write_denial(cg/'cpu.max',
   (cg/'cpu.max').read_text(),emit,'CGROUP_READONLY')
 elif case=='namespace_escape':
  done=subprocess.run(['/usr/bin/unshare','--user','--map-root-user','--mount',
   '/usr/bin/true'],capture_output=True,timeout=1)
  require(done.returncode!=0,'NAMESPACE_ESCAPE_ALLOWED')
  emit('CONTAINED',check='NAMESPACE_ESCAPE_DENIED',exit=done.returncode)
 elif case=='stdout_overflow':
  while True:os.write(1,b'X'*4096)
 elif case in ('disk_inodes','tmp_disk','tmp_inodes'):
  disk_fill('/tmp' if case.startswith('tmp_') else work,
   inodes=case.endswith('inodes'),emit=emit)
 elif case=='chunk_overflow':
  fds=ctx.get('chunk_fds',())
  require(len(fds)==2 and all(type(fd) is int and fd>=3 for fd in fds),
   'FIXED_TWO_CHUNK_DESCRIPTORS_REQUIRED')
  try:
   for _ in range(32):os.write(fds[0],b'X'*4096)
  except OSError as error:
   require(error.errno==errno.EFBIG,'UNEXPECTED_CHUNK_LIMIT_ERRNO')
   emit('LIMIT_ERROR',check='EXPORT_FILE_CAP',errno=error.errno);raise
  raise ValueError('CHUNK_FILE_LIMIT_NOT_ENFORCED')
 elif case=='legacy_missing_approval':
  callback=ctx.get('legacy_missing_approval')
  require(callable(callback),'LEGACY_DENIAL_CALLBACK_REQUIRED')
  require(callback(ctx) is True,'LEGACY_MISSING_APPROVAL_NOT_REJECTED')
  emit('CONTAINED',check='LEGACY_MISSING_APPROVAL')
 elif case=='job_lock':
  callback=ctx.get('job_lock');require(callable(callback),'JOB_LOCK_PROBE_CALLBACK_REQUIRED')
  facts=callback(ctx)
  require(type(facts) is dict,'BOUNDED_JOB_LOCK_PROBE_FACTS_REQUIRED')
  emit('CONTAINED',check='JOB_LOCK',job_lock_probe=facts)
 elif case=='allocation_bypass':
  callback=ctx.get('allocation_bypass')
  require(callable(callback),'ALLOCATION_BYPASS_CALLBACK_REQUIRED')
  facts=callback(ctx)
  require(type(facts) is dict,'BOUNDED_ALLOCATION_PROBE_FACTS_REQUIRED')
  emit('CONTAINED',check='ALLOCATION_BYPASS',allocation_probe=facts)
 elif case=='archive_bound':
  callback=ctx.get('archive_bound');require(callable(callback),'ARCHIVE_BOUND_CALLBACK_REQUIRED')
  try:callback(ctx)
  except ValueError as error:
   require(str(error)=='ARCHIVE_CAPACITY','UNEXPECTED_ARCHIVE_REJECTION')
   emit('CONTAINED',check='ARCHIVE_BOUND',reason='ARCHIVE_CAPACITY');return
  raise ValueError('ARCHIVE_CAPACITY_NOT_ENFORCED')
 else:raise ValueError('UNKNOWN_FIXED_SPECIAL')
def run_fixture(case,ctx):
 """ctx has fixed worker callbacks, work, emit, canary, cgroup, chunk_fds.
 compile/loader negative actions require the fixed child_action(mode,ctx).
 """
 selected=spec(case);callbacks=ctx['phase_callbacks']
 require(set(callbacks)==set(PHASES) and all(callable(callbacks[p]) for p in PHASES),
  'EXACT_SIX_PHASE_CALLBACKS_REQUIRED')
 emit=ctx['emit']
 for phase in PHASES:
  emit('ENTER',phase=phase)
  if selected['phase']==phase and case!='normal':
   mode=selected['mode']
   if mode in MODES:
    child=ctx.get('child_action')
    if phase in ('compile','loader'):
     require(callable(child),'FIXED_CHILD_ACTION_CALLBACK_REQUIRED')
     emit('INJECTED',phase=phase,mode=mode,execution_site='child')
     child(mode,ctx);raise ValueError('ADVERSARIAL_CHILD_RETURNED_SUCCESS')
    emit('INJECTED',phase=phase,mode=mode,execution_site='supervisor')
    action(mode,work=ctx['work'],emit=emit)
    raise ValueError('ADVERSARIAL_ACTION_RETURNED_SUCCESS')
   if case=='orphan':callbacks[phase](ctx)
   special(case,ctx)
   emit('NEGATIVE_COMPLETE',case=case)
   return {'status':'EXPECTED_DENIAL_REACHED','case':case,**ZERO}
  callbacks[phase](ctx);emit('EXIT',phase=phase)
 emit('COMPLETE',all_six_phases=True,**ZERO)
 return {'status':'HARMLESS_FULL_WORKFLOW_COMPLETE',**ZERO}
def require_child_envelope():
 # Child actions are unreachable through this CLI until kernel confinement is
 # live. This is an engineering boundary, not a human authorization capability.
 repo=Path(__file__).resolve().parents[4]
 sys.path.insert(0,str(repo))
 from simulation.hh_signal.final_closure.resource_closure import backend
 profile=backend.load_profile('fixture')
 rows=Path('/proc/self/cgroup').read_text().splitlines()
 require(len(rows)==1 and rows[0].startswith('0::'),'CHILD_UNIFIED_CGROUP_REQUIRED')
 relative=rows[0][3:];cg=backend.owned_cgroup(Path(relative).name,relative)
 raw=backend.cgroup_read(cg)
 expected={'cpu.max':str(profile['cpu_quota_percent']*profile['cpu_quota_period_usec']//100)+' '+str(profile['cpu_quota_period_usec']),
  'cpu.max.burst':'0','memory.max':str(profile['aggregate_memory_bytes']),
  'memory.swap.max':'0','memory.oom.group':'1','pids.max':str(profile['max_tasks'])}
 require(all(raw.get(k,'').strip()==v for k,v in expected.items()),'CHILD_EFFECTIVE_CGROUP_MISMATCH')
 for limit,target in ((resource.RLIMIT_AS,profile['per_process_address_space_bytes']),
                      (resource.RLIMIT_CPU,profile['per_process_CPU_seconds']),
                      (resource.RLIMIT_FSIZE,profile['per_regular_file_bytes'])):
  require(resource.getrlimit(limit)==(target,target),'CHILD_INHERITED_HARD_LIMIT_MISMATCH')
 cwd=Path.cwd()
 work=next((p for p in (cwd,*cwd.parents) if p.name=='work'),None)
 require(work is not None and not any(p.is_symlink() for p in (cwd,*cwd.parents)),
         'CHILD_OWNED_WORK_ANCESTOR_REQUIRED')
 writable=[]
 for line in Path('/proc/self/mountinfo').read_text().splitlines():
  fields=line.split()
  if 'rw' in fields[5].split(','):writable.append(fields[4])
 require(set(writable)=={str(work),'/tmp'},'CHILD_UNACCOUNTED_WRITABLE_MOUNT')
 for path,cap in ((work,profile['work_tmpfs_bytes']),(Path('/tmp'),profile['tmp_tmpfs_bytes'])):
  stat=os.statvfs(path);require(stat.f_blocks*stat.f_frsize==cap,'CHILD_PRIVATE_TMPFS_CAP_MISMATCH')
 require(bool(os.statvfs(repo).f_flag&os.ST_RDONLY) and
         bool(os.statvfs(cg).f_flag&os.ST_RDONLY),'CHILD_READONLY_NAMESPACE_REQUIRED')
 return True

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--action',required=True,choices=MODES);args=parser.parse_args()
 require_child_envelope()
 signal.signal(signal.SIGXFSZ,signal.SIG_DFL);signal.signal(signal.SIGXCPU,signal.SIG_DFL)
 try:action(args.action)
 except OSError as error:
  emit_raw('CHILD_FAILED',errno=error.errno,reason=type(error).__name__)
  return 73 if error.errno==errno.ENOSPC else 78
 return 0
if __name__=='__main__':raise SystemExit(main())

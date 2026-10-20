"""Inert full supervisor workflow. NEVER imports or dispatches MG5/model/ME.
Real readonly source preflight, fixed child stand-in, receipt writing and real
postflight hashing all execute inside the same systemd cgroup/mount namespace.
"""
from __future__ import annotations
import argparse,errno,hashlib,json,mmap,os,resource,signal,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from envelope import PROFILE,PHASES,CASES,REPO,load_profile,source_snapshot,require
RUNTIME=Path('/home/btu/simulations/hh_phase13/run_01/runtime_01/private/mg5')
TREE_SHA='d1d4976a39c5fbd08e3a7fa4db7e42c525c40c84f7be701c1dead3f81afb9e61'
def emit(kind,**value):
 raw=json.dumps({'kind':kind,**value},sort_keys=True,separators=(',',':'))+'\n';require(len(raw)<16384,'SCALAR_RECORD_BOUND');print(raw,flush=True)
def attest():
 load_profile();cgname=Path('/proc/self/cgroup').read_text().strip().split(':',2)[2];cg=Path('/sys/fs/cgroup')/cgname.lstrip('/')
 stat=os.statvfs('.');capacity=stat.f_blocks*stat.f_frsize
 facts={'cgroup':cgname,'cpu.max':(cg/'cpu.max').read_text().strip(),'cpu.max.burst':(cg/'cpu.max.burst').read_text().strip(),'memory.max':(cg/'memory.max').read_text().strip(),'memory.swap.max':(cg/'memory.swap.max').read_text().strip(),'memory.oom.group':(cg/'memory.oom.group').read_text().strip(),'pids.max':(cg/'pids.max').read_text().strip(),'work_capacity_bytes':capacity,'repository_readonly':bool(os.statvfs(REPO).f_flag&os.ST_RDONLY),'cgroup_readonly':bool(os.statvfs(cg).f_flag&os.ST_RDONLY),'AS':list(resource.getrlimit(resource.RLIMIT_AS)),'CPU':list(resource.getrlimit(resource.RLIMIT_CPU)),'FSIZE':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'uid_map':Path('/proc/self/uid_map').read_text().strip(),'namespace_mount':os.readlink('/proc/self/ns/mnt')}
 valid=(facts['cpu.max']=='3000 10000' and facts['cpu.max.burst']=='0' and facts['memory.max']=='536870912' and facts['memory.swap.max']=='0' and facts['memory.oom.group']=='1' and facts['pids.max']=='8' and capacity==8388608 and facts['repository_readonly'] and facts['cgroup_readonly'] and facts['AS']==[536870912]*2 and facts['CPU']==[2]*2 and facts['FSIZE']==[65536]*2)
 emit('ATTESTED',valid=valid,**facts);require(valid,'EFFECTIVE_KERNEL_LIMIT_MISMATCH');return cg

def burn():
 while True:pass
def resident_block():
 # Fault one byte per page, so all 300 MiB are resident/charged without a
 # redundant whole-array memset. Two blocks still exceed memory.max; neither
 # process approaches its unchanged 512 MiB virtual-address ceiling.
 data=mmap.mmap(-1,300*1024**2,flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS)
 for offset in range(0,len(data),4096):data[offset]=1
 return data

def action(mode):
 if mode=='cpu':burn()
 elif mode=='wall':time.sleep(60)
 elif mode=='ram':
  # Each process remains below RLIMIT_AS; only aggregate cgroup memory.max
  # can stop the combined allocation. No host-wide uncontrolled allocation.
  pid=os.fork()
  if pid==0:
   data=resident_block()
   while True:time.sleep(1)
  data=resident_block()
  os.waitpid(pid,0)
 elif mode=='disk':
  for i in range(1024):
   with open('disk_%04d'%i,'xb') as stream:stream.write(b'X'*65536)
  raise ValueError('DISK_CAP_DID_NOT_STOP_WRITES')
 elif mode=='abnormal':os._exit(87)
 else:raise ValueError('UNKNOWN_INERT_ACTION')

def runtime_identity():
 sys.path.insert(0,str(REPO/'analysis/phase13/source'))
 from runtime_layout import inspect_tree
 m=inspect_tree(RUNTIME,{'max_single_file_bytes':64*1024**2,'max_entries':10000,'max_total_regular_bytes':512*1024**2})
 require(m['content_manifest_sha256']==TREE_SHA,'FROZEN_RUNTIME_DRIFT');return m['content_manifest_sha256']
def launch_child(mode):
 with open('child_stdout.log','xb') as out,open('child_stderr.log','xb') as err:
  # Reserve bounded diagnostic blocks BEFORE testing ENOSPC. Child output can
  # then report errno even when the private tmpfs has no free blocks left.
  for stream in (out,err):stream.write(b'\0'*65536);stream.flush();stream.seek(0)
  p=subprocess.Popen(['/usr/bin/python3','-I','-B',str(Path(__file__).with_name('fixture_child.py')),'--mode',mode],stdout=out,stderr=err,start_new_session=True)
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGKILL);p.wait();raise ValueError('CHILD_WALL_STOP')
  details=[]
  for name in ('child_stdout.log','child_stderr.log'):
   for line in Path(name).read_text(errors='replace').splitlines():
    try:v=json.loads(line)
    except ValueError:continue
    if isinstance(v,dict):details.append(v)
  emit('CHILD_RESULT',mode=mode,exit=p.returncode,details=details[:8])
  require(p.returncode==0,'INERT_CHILD_EXIT:'+str(p.returncode))
 return {'status':'INERT_READONLY_CHILD_COMPLETED','exit':p.returncode}

def main():
 a=argparse.ArgumentParser();a.add_argument('--case',choices=CASES,required=True);a.add_argument('--canary',type=Path,required=True);a.add_argument('--source-identity',required=True);args=a.parse_args()
 signal.signal(signal.SIGXFSZ,signal.SIG_DFL);signal.signal(signal.SIGXCPU,signal.SIG_DFL)
 cg=attest();require(source_snapshot()['identity']==args.source_identity,'FROZEN_SOURCE_SNAPSHOT_MISMATCH')
 for name in ('tmp','home'):Path(name).mkdir()
 before=None;child=None
 for phase in PHASES:
  emit('ENTER',phase=phase)
  if args.case==phase+'_abnormal':os._exit(87)
  if args.case.startswith(phase+'_'):
   mode=args.case[len(phase)+1:]
   if phase=='child':launch_child(mode)
   else:action(mode)
  if phase=='preflight':
   status=subprocess.check_output(['git','-C',str(REPO),'status','--porcelain','--untracked-files=no'],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},timeout=2)
   require(not status,'DIRTY_TRACKED_SOURCE');before=runtime_identity()
   if args.case=='source_write':
    try:args.canary.write_text('INERT_FORBIDDEN_CHANGE')
    except OSError as e:
     require(e.errno in (errno.EROFS,errno.EACCES,errno.EPERM),'UNEXPECTED_WRITE_ERROR');emit('CONTAINED',check='READONLY_CANARY',errno=e.errno);return
    raise ValueError('READONLY_SOURCE_GUARD_FAILED')
   if args.case=='cgroup_write':
    try:(cg/'cpu.max').write_text('max 10000')
    except OSError as e:
     require(e.errno in (errno.EROFS,errno.EACCES,errno.EPERM),'UNEXPECTED_CGROUP_ERROR');emit('CONTAINED',check='CGROUP_READONLY',errno=e.errno);return
    raise ValueError('CGROUP_SELF_MODIFICATION_ALLOWED')
   if args.case=='namespace_escape':
    done=subprocess.run(['/usr/bin/unshare','--user','--map-root-user','--mount','/usr/bin/true'],capture_output=True,timeout=1)
    require(done.returncode!=0,'NAMESPACE_ESCAPE_ALLOWED');emit('CONTAINED',check='NAMESPACE_ESCAPE_DENIED',exit=done.returncode);return
   if args.case=='aggregate_cpu':
    for i in range(3):
     if os.fork()==0:burn()
    while True:time.sleep(1)
   if args.case=='controller_loss':
    for i in range(3):
     if os.fork()==0:burn()
    while True:time.sleep(1)
   if args.case=='pids':
    children=[]
    try:
     for i in range(32):
      pid=os.fork()
      if pid==0:time.sleep(60);os._exit(0)
      children.append(pid)
    except OSError as e:require(e.errno==errno.EAGAIN,'UNEXPECTED_FORK_ERROR');emit('CONTAINED',check='TASKS_MAX',created=len(children))
    return
   if args.case=='stdout_overflow':
    while True:os.write(1,b'X'*4096)
   if args.case=='disk_inodes':
    for i in range(2048):Path('inode_%04d'%i).touch()
   if args.case=='legacy_missing_approval':
    done=subprocess.run(['/usr/bin/python3','-B',str(REPO/'analysis/phase13/scripts/run_parser_review.py'),'--package','/nonexistent/fixture_only_package'],capture_output=True,text=True,timeout=2)
    require(done.returncode==2 and 'MISSING_NEW_EXPLICIT_USER_APPROVAL' in done.stdout,'LEGACY_APPROVAL_BOUNDARY_FAILED');emit('CONTAINED',check='LEGACY_MISSING_APPROVAL',exit=2);return
  elif phase=='child':
   child=launch_child('normal')
   if args.case=='orphan':
    pid=os.fork()
    if pid==0:os.setsid();time.sleep(60);os._exit(0)
    emit('ORPHAN_CREATED',pid=pid);os._exit(0)
  elif phase=='receipt':
   with Path('workflow_receipt.json').open('x') as stream:json.dump({'evidence_class':'SYNTHETIC_METHOD_ONLY','preflight_runtime_sha256':before,'child':child,'MG5_invocations':0},stream)
   require(Path('workflow_receipt.json').stat().st_size<65536,'RECEIPT_BOUND')
  else:
   require(runtime_identity()==before,'POSTFLIGHT_RUNTIME_CHANGED');require(source_snapshot()['identity']==args.source_identity,'POSTFLIGHT_SOURCE_CHANGED')
  emit('EXIT',phase=phase)
 emit('COMPLETE',all_four_phases=True,MG5_invocations=0,new_ME_calls=0,new_integrals=0,new_events=0,tmpfs_used_bytes=(os.statvfs('.').f_blocks-os.statvfs('.').f_bfree)*os.statvfs('.').f_frsize)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if isinstance(e,SystemExit):raise
  emit('FAILED',reason=type(e).__name__+':'+str(e)[:300],errno=getattr(e,'errno',None),tmpfs_used_bytes=(os.statvfs('.').f_blocks-os.statvfs('.').f_bfree)*os.statvfs('.').f_frsize,tmpfs_free_inodes=os.statvfs('.').f_ffree);sys.exit(73 if isinstance(e,OSError) and e.errno==errno.ENOSPC else 78)

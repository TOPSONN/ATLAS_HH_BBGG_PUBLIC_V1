"""Bounded ordinary-file engineering ledger, not production durable evidence."""
from pathlib import Path
import contextlib,json,os,stat,time,uuid
from .contract import canonical,load,need,no_links,sha,STATES

MAX_EVENTS=128
MAX_EVENT=32768
MAX_RUN_BYTES=64*1024**2
def budget(run):
 total=0;count=0
 for p in run.rglob('*'):
  no_links(p)
  if p.is_file():
   count+=1;total+=p.stat().st_size
   need(count<=4096 and total<=MAX_RUN_BYTES,'ENGINEERING_LOGICAL_RUN_BOUND')
 return {'logical_bytes':total,'files':count,'allocated_blocks_enforced':False}
def create_json(path,value):
 raw=canonical(value)+b'\n';need(len(raw)<=2*1024**2,'RECEIPT_BYTE_BOUND')
 no_links(path)
 with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 need(Path(path).read_bytes()==raw,'REOPEN_MISMATCH')
 return sha(raw)
def sync_dir(path):
 if os.name=='nt':return 'NOT_AVAILABLE_VIA_THIS_WINDOWS_ADAPTER'
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:os.close(fd)
 return 'ACK_ORDINARY_FILESYSTEM_ONLY_NOT_POWER_LOSS_PROOF'
@contextlib.contextmanager
def lock(run):
 no_links(run);p=run/'controller.lock'
 if not p.exists():
  try:
   with p.open('xb') as f:f.write(b'0');f.flush();os.fsync(f.fileno())
  except FileExistsError:pass
 no_links(p);f=p.open('r+b');held=False
 try:
  need(stat.S_ISREG(os.fstat(f.fileno()).st_mode) and p.stat().st_size==1,'LOCK_FILE_METADATA')
  if os.name=='nt':
   import msvcrt
   try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
   except OSError:raise ValueError('CONCURRENT_CONTROLLER_DENIED')
  else:
   import fcntl
   try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise ValueError('CONCURRENT_CONTROLLER_DENIED')
  held=True;yield
 finally:
  if held:
   if os.name=='nt':
    import msvcrt
    f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
   else:
    import fcntl
    fcntl.flock(f.fileno(),fcntl.LOCK_UN)
  f.close()
def manifest(folder):
 rows=[];total=0
 for p in sorted(folder.rglob('*')):
  no_links(p)
  if not p.is_file():continue
  size=p.stat().st_size;total+=size
  need(size<=2*1024**2 and total<=MAX_RUN_BYTES,'STAGE_OUTPUT_BYTE_BOUND')
  rows.append({'path':p.relative_to(folder).as_posix(),'bytes':size,'sha256':sha(p.read_bytes())})
 need(len(rows)<=128,'STAGE_OUTPUT_FILE_BOUND')
 return rows
def events(run):
 folder=run/'ledger';need(folder.is_dir(),'LEDGER_MISSING');paths=sorted(folder.iterdir())
 need(len(paths)<=MAX_EVENTS,'LEDGER_EVENT_BOUND');rows=[];previous='0'*64
 for i,p in enumerate(paths,1):
  no_links(p);need(p.name==f'{i:06d}.json' and p.is_file() and p.stat().st_size<=MAX_EVENT,'LEDGER_SEQUENCE_OR_SIZE')
  raw=p.read_bytes();v=load(p,MAX_EVENT)
  need(type(v) is dict and v.get('sequence')==i and v.get('previous_sha256')==previous and v.get('status') in STATES,'LEDGER_CHAIN')
  need(v['run_id']==run.name,'FOREIGN_RUN_EVENT')
  need(type(v['started_monotonic_ns']) is int and (v['finished_monotonic_ns'] is None or v['finished_monotonic_ns']>=v['started_monotonic_ns']),'EVENT_CLOCK')
  previous=sha(raw);rows.append(v)
 return rows
def append(run,source,stage,status,*,start=None,command=None,exit_status=None,outputs=None,reason=None,next_stage=None,child_pid=None,observations=None):
 budget(run)
 need(status in STATES,'UNKNOWN_STAGE_STATE');rows=events(run);need(len(rows)<MAX_EVENTS,'LEDGER_FULL')
 before='0'*64 if not rows else sha((run/'ledger'/f'{len(rows):06d}.json').read_bytes())
 now=time.monotonic_ns();v={'schema':'HH_MASTER_LEDGER_EVENT_V1','run_id':run.name,'sequence':len(rows)+1,
  'previous_sha256':before,'exact_source_revision':source['revision'],'source_sha256':source['source_sha256'],
  'input_sha256':sha(canonical({'frozen_inputs_sha256':source['inputs_sha256'],'host_capture':source.get('host_capture')})),'stage_id':stage,'status':status,
  'started_monotonic_ns':start or now,'finished_monotonic_ns':None if status=='RUNNING' else now,
  'clock_domain':'MONOTONIC_PER_INVOCATION_NOT_CROSS_BOOT_DURATION','command':command,
  'argv_identity':None if command is None else sha(canonical(command)),
  'real_subprocess_exit_status':exit_status,'child_pid':child_pid,'output_directory':'stages/'+stage,
  'output_manifest':outputs,'test_counts':None,'resource_observations':observations,
  'failure_reason':reason,'gate_classification':status,'authorization_reference':None,'next_resumable_stage':next_stage}
 raw=canonical(v)+b'\n';need(len(raw)<=MAX_EVENT,'LEDGER_EVENT_BYTE_BOUND')
 create_json(run/'ledger'/f'{len(rows)+1:06d}.json',v);sync_dir(run/'ledger');return v
def latest(run):
 out={}
 for r in events(run):out[r['stage_id']]=r
 return out
def verify(run):
 rows=events(run);state=latest(run)
 for stage,row in state.items():
  if row['status']=='RUNNING':continue
  if row['output_manifest'] is not None:
   need(manifest(run/'stages'/stage)==row['output_manifest'],'PREVIOUS_OUTPUT_DRIFT')
 return {'status':'PASS_SOURCE_ONLY','ledger_events':len(rows),'stage_count':len(state),
  'interrupted':[s for s,r in state.items() if r['status']=='RUNNING'],
  'ordinary_file_fsync':'ACK_NOT_CAPACITY_OR_POWER_LOSS_VERIFICATION','directory_fsync':sync_dir(run/'ledger')}

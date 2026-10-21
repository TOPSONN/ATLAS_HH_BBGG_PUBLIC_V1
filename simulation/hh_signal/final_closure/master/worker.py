"""One fixed safe task per child. All subprocess/native execution is denied."""
import ctypes,json,os,sys,traceback
from pathlib import Path
from .contract import PROGRESS,RUN_ID,SAFE,canonical,load,need,no_links,sha
from .ledger import create_json

def main():
 need(len(sys.argv)==3,'FIXED_SAFE_WORKER_ARGV')
 stage,where=sys.argv[1:];need(stage in {s for s,_ in SAFE},'NO_LIVE_STAGE_DISPATCH')
 run=no_links(Path(where));need(run.parent==PROGRESS and RUN_ID.fullmatch(run.name),'FIXED_PROGRESS_RUN_REQUIRED')
 context=load(run/'context.json');out=run/'stages'/stage
 no_links(out);need(out.is_dir() and not any(out.iterdir()),'NEW_EMPTY_STAGE_REQUIRED')
 audit={'denied':[],'directory_fd_or_numeric_open_events':0}
 def guard(event,args):
  if event in ('subprocess.Popen','os.system','os.fork','os.exec','ctypes.dlopen','fcntl.ioctl','resource.setrlimit','socket.connect','os.kill'):
   audit['denied'].append(event);raise RuntimeError('SAFE_WORKER_FORBIDDEN_DISPATCH')
  if event=='open':
   path,mode,flags=args
   write=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
   if isinstance(path,int):audit['directory_fd_or_numeric_open_events']+=1
   elif write:
    p=Path(os.fsdecode(path)).absolute();no_links(p)
    if not p.is_relative_to(out):audit['denied'].append('WRITE_OUTSIDE_STAGE');raise RuntimeError('WRITE_OUTSIDE_SAFE_STAGE')
 sys.addaudithook(guard)
 try:
  from .tasks import TASKS
  value=TASKS[stage](out,context)
  value['safe_worker_audit']=audit
  need(not audit['denied'],'FORBIDDEN_OPERATION_ATTEMPT')
  create_json(out/'stage_result.json',value)
  print(json.dumps({'stage':stage,'status':value['status'],'scope':'SAFE_ENGINEERING_AND_READ_ONLY'}));return 0
 except BaseException as error:
  private=traceback.format_exc()[-8192:]
  (out/'local_failure_trace.txt').write_text(private,encoding='utf-8')
  create_json(out/'stage_result.json',{'status':'FAIL','failure_reason':type(error).__name__,
   'private_trace_sha256':sha(private.encode()),'safe_worker_audit':audit,'live_execution':False})
  print(json.dumps({'stage':stage,'status':'FAIL','reason':type(error).__name__}));return 2
if __name__=='__main__':raise SystemExit(main())

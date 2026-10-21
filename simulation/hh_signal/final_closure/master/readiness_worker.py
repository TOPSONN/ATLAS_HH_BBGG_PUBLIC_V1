"""Fixed G1-G7 pure/read-existing-evidence child; no kernel or external process."""
import ctypes,json,os,sys,traceback
from pathlib import Path
from .contract import need,no_links,load,sha
from .ledger import create_json
from .readiness_runner import STAGES,PROGRESS,RUN_ID
def main():
 need(len(sys.argv)==3,'FIXED_WORKER_ARGV');stage,where=sys.argv[1:];need(stage in STAGES,'NO_LIVE_STAGE')
 run=no_links(Path(where));need(run.parent==PROGRESS and RUN_ID.fullmatch(run.name),'FIXED_PRIVATE_RUN')
 c=load(run/'context.json');out=run/'stages'/stage;no_links(out);need(out.is_dir() and not any(out.iterdir()),'FRESH_STAGE')
 audit={'denied':[],'numeric_open_visibility_limit':0}
 def guard(event,args):
  if event in ('subprocess.Popen','os.system','os.fork','os.exec','ctypes.dlopen','fcntl.ioctl','resource.setrlimit','socket.connect','os.kill'):
   audit['denied'].append(event);raise RuntimeError('SAFE_WORKER_FORBIDDEN')
  if event=='open':
   path,mode,flags=args
   if isinstance(path,int):audit['numeric_open_visibility_limit']+=1;return
   p=Path(os.fsdecode(path)).absolute();no_links(p)
   if str(p).startswith(('/proc/','/sys/')):raise RuntimeError('NO_LIVE_KERNEL_READ_IN_ENGINEERING_CHILD')
   write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or isinstance(flags,int) and bool(flags&(os.O_CREAT|os.O_WRONLY|os.O_RDWR|os.O_TRUNC))
   if write and not p.is_relative_to(out):audit['denied'].append('WRITE_OUTSIDE_STAGE');raise RuntimeError('WRITE_OUTSIDE_STAGE')
 sys.addaudithook(guard)
 try:
  from .readiness_stages import TASKS
  v=TASKS[stage](out,c);v['safe_worker_audit']=audit;need(not audit['denied'],'AUDIT_DENIAL')
  create_json(out/'stage_result.json',v);print(json.dumps({'stage':stage,'status':v['status'],'live_dispatches':0}));return 0
 except BaseException as e:
  trace=traceback.format_exc()[-8192:];(out/'local_failure_trace.txt').write_text(trace,encoding='utf-8')
  create_json(out/'stage_result.json',{'status':'FAIL','evidence':{'actual_acceptance':None,'blockers':[type(e).__name__]},'trace_sha256':sha(trace.encode()),'safe_worker_audit':audit})
  print(json.dumps({'stage':stage,'status':'FAIL','reason':type(e).__name__}));return 2
if __name__=='__main__':raise SystemExit(main())

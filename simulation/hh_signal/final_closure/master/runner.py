"""Resumable source/read-only DAG. No authorization parser or live executor."""
import argparse,json,os,subprocess,sys,threading,time,uuid
from pathlib import Path
from .contract import BASE,HERE,LIVE,PROGRESS,REPO,RUN_ID,SAFE,binding_identity,canonical,load,need,no_links,plan,sha,source_binding
from . import ledger

BOOTSTRAP='import sys;sys.path.insert(0,sys.argv.pop(1));from simulation.hh_signal.final_closure.master.worker import main;raise SystemExit(main())'
MAX_SNAPSHOTS=64
MAX_EXPORTS=16
def run_path(run_id):
 need(type(run_id) is str and RUN_ID.fullmatch(run_id),'EXACT_RUN_ID_REQUIRED')
 return no_links(PROGRESS/run_id)
def new_run(capture=None):
 no_links(PROGRESS);PROGRESS.mkdir(parents=True,exist_ok=True)
 need(len([p for p in PROGRESS.iterdir() if p.is_dir() and RUN_ID.fullmatch(p.name)])<16,'ENGINEERING_RUN_COUNT_BOUND')
 context=source_binding(capture);run=run_path(str(uuid.uuid4()));run.mkdir(mode=0o700)
 for n in ('ledger','stages','snapshots','exports'):(run/n).mkdir()
 context['run_directory']=str(run);context['scope_identity']=binding_identity(context)
 ledger.create_json(run/'context.json',context);ledger.sync_dir(run);return run
def check(run):
 ledger.budget(run)
 context=load(run/'context.json');need(context['run_directory']==str(run),'RUN_PATH_REBINDING')
 current=source_binding(None if context['host_capture'] is None else context['host_capture']['path'])
 need(binding_identity(current)==context['scope_identity'],'RESUME_SOURCE_OR_INPUT_DRIFT')
 ledger.verify(run);return context
def child(run,stage):
 started=time.monotonic_ns()
 out=run/'stages'/stage;out.mkdir()
 argv=[sys.executable,'-I','-B','-c',BOOTSTRAP,str(REPO),stage,str(run)]
 p=subprocess.Popen(argv,cwd=REPO,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 chunks=[];count=0;overflow=threading.Event()
 def drain():
  nonlocal count
  while True:
   data=p.stdout.read(4096)
   if not data:break
   room=max(0,65536-count);chunks.append(data[:room]);count+=len(data)
   if count>65536:
    overflow.set()
    try:p.kill()
    except OSError:pass
    break
 t=threading.Thread(target=drain,daemon=True);t.start();timed_out=False
 try:p.wait(timeout=120)
 except subprocess.TimeoutExpired:
  timed_out=True;p.kill();p.wait(timeout=10)
 t.join(timeout=5);need(not t.is_alive(),'CHILD_PIPE_CLEANUP_UNKNOWN')
 p.stdout.close();raw=b''.join(chunks)
 with (out/'safe_child_log.txt').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 need(not timed_out and not overflow.is_set(),'SAFE_CHILD_TIMEOUT_OR_LOG_BOUND')
 v=load(out/'stage_result.json');need(v['status'] in {'PASS_SOURCE_ONLY','PASS_READ_ONLY_OBSERVED','BLOCKED_OS_CAPABILITY','BLOCKED_AUTHORIZATION','BLOCKED_INPUT','FAIL','UNKNOWN'},'CHILD_STAGE_CLASSIFICATION')
 if p.returncode!=0:v['status']='FAIL'
 return {'status':v['status'],'exit_status':p.returncode,'pid':p.pid,'argv':argv,
  'observations':{'owned_child_exited':p.returncode is not None,'stdout_bytes':len(raw),'wall_timeout_seconds':120,
   'observed_safe_child_wall_seconds':(time.monotonic_ns()-started)/1e9,
   'limits_kind':'SOFT_SAFE_ENGINEERING_TIMEOUT_AND_RETAINED_LOG_LIMIT_NOT_OS_ENVELOPE','CPU_seconds':None,'RAM_peak_bytes':None,'kernel_disk_bytes':None},
  'manifest':ledger.manifest(out)}
def state(run):
 rows=ledger.latest(run);return {s:r['status'] for s,r in rows.items()}
def snapshots(run,context):
 ledger.budget(run)
 states=state(run);v={'schema':'HH_MASTER_PROGRESS_V1','run_id':run.name,'source_revision':context['revision'],
  'source_sha256':context['source_sha256'],'scope':'SAFE_ENGINEERING_AND_READ_ONLY','stages':states,
  'safe_stage_count':len(SAFE),'safe_children_completed':sum(s in states for s,_ in SAFE),
  'new_live_dispatches':0,'GENUINE_ME_CALLS':None,'GENUINE_INTEGRALS':None,'LHE_EVENTS':None,'HEPMC3_EVENTS':None,'DELPHES_ROOT_EVENTS':None,
  'CPU_kernel_observation':None,'RAM_kernel_observation':None,'disk_kernel_observation':None,
  'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'FORMAL_BUILD_ONLY_AUTHORIZED':False,'PHYSICAL_RESTART_AUTHORIZED':False,
  'architecture_selected':None,'B_V2_user_accepted':False,'G8_ROLLBACK':'NOT_STARTED_NOT_NEEDED',
  'next_safe_resumable_action':'resume-safe verifies identical identities and skips recorded stages; new external inputs/source require a fresh run',
  'unresolved_prior_child':any(x=='RUNNING' for x in states.values())}
 blocked={s:c for s,c in states.items() if c.startswith('BLOCKED') or c in ('UNKNOWN','FAIL')}
 files={'MASTER_PROGRESS.json':v,'MASTER_BLOCKERS.json':{'stages':blocked,'unexecuted_measurements':None},
  'MASTER_SOURCE_MANIFEST.json':{'revision':context['revision'],'source_sha256':context['source_sha256'],'source_rows':context['source_rows'],
   'frozen_input_count':context['input_count'],'frozen_input_rows_sha256':context['inputs_sha256'],'frozen_input_manifest_sha256':context['frozen_input_manifest_sha256'],
   'host_input_sha256':None if context['host_capture'] is None else context['host_capture']['sha256']},
  'MASTER_TEST_SUMMARY.json':{'current_safe_stage_results':states,'prior_612_81':'PRESERVED_BASELINE; FINAL_CI_REQUIRED_FOR_NEW_SOURCE','new_test_counts':None}}
 index=len(list((run/'snapshots').iterdir()))+1;need(index<=MAX_SNAPSHOTS,'SNAPSHOT_COUNT_BOUND')
 folder=run/'snapshots'/f'{index:04d}';folder.mkdir()
 for name,value in files.items():ledger.create_json(folder/name,value)
 status='# MASTER安全進度\n\n'+f'Run {run.name}\n\nExact source {context["revision"]}\n\n'+'\n'.join(f'- {s}: {c}' for s,c in states.items())+'\n\n沒有live dispatcher；未執行kernel/physics的數值保持null。\n'
 (folder/'MASTER_STATUS_ZH_TW.md').write_text(status,encoding='utf-8')
 (folder/'MASTER_NEXT_AUTHORIZATION.md').write_text('# 最小外部動作\n\n先在相同使用者一般權限context完成受審Windows唯讀acquisition；不能啟動未知/停止guest。B1–B8與VM成本歸屬需逐條明確決策。裝置provisioning、S4、full-resource、BUILD_ONLY、binary人類review、physical restart、SM1000各自需要新的exact-source/exact-scope授權。目前沒有任何執行批准。\n',encoding='utf-8')
 for p in folder.iterdir():
  target=run/p.name;temp=run/(p.name+'.tmp_'+uuid.uuid4().hex)
  with temp.open('xb') as f:f.write(p.read_bytes());f.flush();os.fsync(f.fileno())
  no_links(target);os.replace(temp,target)
 ledger.sync_dir(run);return v
def execute(run):
 with ledger.lock(run):
  context=check(run);previous=ledger.latest(run)
  interrupted=[s for s,r in previous.items() if r['status']=='RUNNING']
  if interrupted:
   # Do not guess PID ownership, child exit, or repeat an interrupted task.
   for s in interrupted:ledger.append(run,context,s,'UNKNOWN',reason='PREVIOUS_SAFE_CHILD_EXIT_UNVERIFIED_NO_AUTOMATIC_RETRY')
   snapshots(run,context);return {'run_id':run.name,'status':'UNKNOWN','reason':'INTERRUPTED_RUN_REQUIRES_EXTERNAL_CLEANUP_REVIEW'}
  if any(r.get('failure_reason')=='PREVIOUS_SAFE_CHILD_EXIT_UNVERIFIED_NO_AUTOMATIC_RETRY' or str(r.get('failure_reason','')).startswith('SAFE_CHILD_DISPATCH_OR_CLEANUP_UNKNOWN:') for r in previous.values()):
   return {'run_id':run.name,'status':'UNKNOWN','reason':'PREVIOUS_CHILD_CLEANUP_UNVERIFIED'}
  for i,(stage,dependencies) in enumerate(SAFE):
   done=ledger.latest(run)
   if stage in done:continue
   unmet=[s for s in dependencies if done.get(s,{}).get('status') not in ('PASS_SOURCE_ONLY','PASS_READ_ONLY_OBSERVED')]
   if unmet:
    ledger.append(run,context,stage,'BLOCKED_INPUT',reason='DEPENDENCY_NOT_VERIFIED:'+','.join(unmet));snapshots(run,context);continue
   argv=[sys.executable,'-I','-B','-c',BOOTSTRAP,str(REPO),stage,str(run)];start=time.monotonic_ns()
   ledger.append(run,context,stage,'RUNNING',start=start,command=argv)
   try:
    v=child(run,stage)
    ledger.append(run,context,stage,v['status'],start=start,command=v['argv'],exit_status=v['exit_status'],
     outputs=v['manifest'],child_pid=v['pid'],observations=v['observations'],
     reason='SAFE_CHILD_FAILURE' if v['status']=='FAIL' else None,next_stage=SAFE[i+1][0] if i+1<len(SAFE) else None)
   except Exception as error:
    ledger.append(run,context,stage,'UNKNOWN',start=start,command=argv,reason='SAFE_CHILD_DISPATCH_OR_CLEANUP_UNKNOWN:'+type(error).__name__)
    snapshots(run,context);return {'run_id':run.name,'status':'UNKNOWN','reason':'SAFE_CHILD_CLEANUP_REVIEW_REQUIRED'}
   need(binding_identity(source_binding(None if context['host_capture'] is None else context['host_capture']['path']))==context['scope_identity'],'SOURCE_OR_INPUT_CHANGED_DURING_RUN')
   snapshots(run,context)
  for stage in LIVE:
   if stage not in ledger.latest(run):ledger.append(run,context,stage,'BLOCKED_INPUT' if stage in ('BINARY_REVIEW','PHASE7I_FOUR_REPLICAS','PHASE7K_CORRECTED_ANALYSIS','PHASE7L_FINAL_REPORT') else 'BLOCKED_AUTHORIZATION',reason='NO_LIVE_DISPATCHER; EXACT_INPUT_CAPABILITY_AND_SEPARATE_HUMAN_AUTHORIZATION_REQUIRED')
  v=snapshots(run,context);return {'run_id':run.name,'status':'FAIL' if any(c=='FAIL' for c in v['stages'].values()) else 'PASS_SOURCE_ONLY','safe_stages_recorded':v['safe_children_completed'],
   'safe_failures':[s for s,c in v['stages'].items() if c=='FAIL'],'live_dispatches':0,'ledger':ledger.verify(run)}
def export(run):
 with ledger.lock(run):
  context=check(run);need(len(list((run/'exports').iterdir()))<MAX_EXPORTS,'EXPORT_COUNT_BOUND')
  folder=run/'exports'/str(uuid.uuid4());folder.mkdir()
  for name in ('MASTER_PROGRESS.json','MASTER_BLOCKERS.json','MASTER_SOURCE_MANIFEST.json','MASTER_TEST_SUMMARY.json','MASTER_STATUS_ZH_TW.md','MASTER_NEXT_AUTHORIZATION.md'):
   need((run/name).is_file(),'PROGRESS_SNAPSHOT_REQUIRED');(folder/name).write_bytes((run/name).read_bytes())
  public=[]
  for stage,row in ledger.latest(run).items():
   public.append({k:row[k] for k in ('stage_id','status','exact_source_revision','argv_identity','real_subprocess_exit_status','output_manifest','resource_observations','failure_reason','authorization_reference')})
  ledger.create_json(folder/'PUBLIC_STAGE_RECEIPTS.json',{'stages':public,'actual_native_dispatch':False,'unexecuted_physics_measurements':None})
  # Only explicit known JSON summaries; no raw inventory, event rows or private traces.
  for stage,names in {'G1_REAL_INVENTORY':['G1_HOST_INVENTORY.json','G1_GUEST_INVENTORY.json','G1_CGROUP_CAPABILITIES.json','G1_STORAGE_TOPOLOGY.json','G1_LOGGING_BOUNDARIES.json','G1_EVIDENCE_COMPLETENESS.json'],
   'G2_ARCHITECTURE_DECISION':['ARCHITECTURE_A_FEASIBILITY.json','ARCHITECTURE_B_V2_REVIEW.json'],
   'INDEPENDENT_NUMERICAL_CHECK':['INDEPENDENT_KAPPA_CHECK.json'],'SCIENTIFIC_METHOD_PREFLIGHT':['SCIENTIFIC_METHOD_PREFLIGHT.json'],
   'ROOT_SELECTION_SCHEMA_REVIEW':['ROOT_SELECTION_SCHEMA_REVIEW.json']}.items():
   if ledger.latest(run).get(stage,{}).get('status') in ('FAIL','UNKNOWN','BLOCKED_INPUT','RUNNING'):continue
   for name in names:
    p=run/'stages'/stage/name
    if p.is_file():(folder/name).write_bytes(p.read_bytes())
  ledger.create_json(folder/'EXPORT_MANIFEST.json',ledger.manifest(folder))
  return {'status':'PASS_SOURCE_ONLY','run_id':run.name,'local_export':str(folder),'not_authorization':True}
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False,description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
 sub.add_parser('plan',allow_abbrev=False)
 start=sub.add_parser('run-safe',allow_abbrev=False);start.add_argument('--host-capture',type=Path)
 for mode in ('resume-safe','status','verify','export-review'):
  x=sub.add_parser(mode,allow_abbrev=False);x.add_argument('--run-id',required=True)
 a=p.parse_args(argv)
 try:
  if a.mode=='plan':v=plan()
  elif a.mode=='run-safe':v=execute(new_run(a.host_capture))
  else:
   run=run_path(a.run_id)
   if a.mode=='resume-safe':v=execute(run)
   elif a.mode=='status':check(run);v=load(run/'MASTER_PROGRESS.json')
   elif a.mode=='verify':check(run);v=ledger.verify(run)
   else:v=export(run)
  print(json.dumps(v,indent=2));return 2 if v.get('status') in ('FAIL','UNKNOWN') or v.get('safe_failures') else 0
 except Exception as error:
  print(json.dumps({'status':'FAIL','reason':type(error).__name__,'execution_authorized':False}));return 2
if __name__=='__main__':raise SystemExit(main())

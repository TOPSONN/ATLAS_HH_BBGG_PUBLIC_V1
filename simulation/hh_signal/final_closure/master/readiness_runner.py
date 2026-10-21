"""Versioned G1-G7 safe profile reusing Master child, lock, ledger and manifests.

Only fixed pure/read-existing-evidence children. No live or approval interface.
Engineering and actual acceptance are separate in every resulting stage.
"""
import argparse,json,os,sys,time,uuid
from pathlib import Path
from . import ledger,runner
from .contract import REPO,canonical,git,load,need,no_links,sha,RUN_ID

BASE='8b071a4cdca472ef7c9cb78f40b894864ca30374'
PROGRESS=REPO/'.local/readiness_progress_v1'
STAGES=('R0_IDENTITIES','G1_HOST','G1_GUEST','G2_ARCHITECTURE','G3_GUARDS','G4_PROVISIONING','G5_FORMAT_REVIEW','G6_GEOMETRY','G7_ENVIRONMENT')
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv.pop(1));from simulation.hh_signal.final_closure.master.readiness_worker import main;raise SystemExit(main())'

def binding(capture,running=None,guest=None):
 need(not git('status','--porcelain','--untracked-files=no'),'TRACKED_SOURCE_DIRTY')
 old=load(REPO/'reports/phase7i_g1_association_repair/source_manifest.json')
 names={r['path'] for r in old['files']}
 names|={p.relative_to(REPO).as_posix() for p in (REPO/'simulation/hh_signal/final_closure/master').glob('*') if p.suffix in ('.py','.ps1','.cpp','.json')}
 names|={'.github/workflows/hh_signal_g1_g7_engineering.yml'}
 source=[]
 for name in sorted(names):
  p=no_links(REPO/name);need(p.is_file() and p.stat().st_size<=131072,'SOURCE_BOUND');source.append({'path':name,'sha256':sha(p.read_bytes())})
 from ..src.contracts import input_identity
 inputs=[{'path':r['path'],'sha256':r['sha256']} for r in input_identity()]
 external={}
 for name,p in (('host',capture),('running',running),('guest',guest)):
  if p is None:external[name]=None;continue
  p=no_links(Path(p));need(p.is_file() and p.stat().st_size<=262144,'EXTERNAL_BOUND');external[name]={'path':str(p),'sha256':sha(p.read_bytes())}
 need(external['host'] is not None,'EXACT_EXISTING_HOST_CAPTURE_REQUIRED')
 v={'schema':'HH_G1_G7_SAFE_CONTEXT_V1','revision':git('rev-parse','HEAD').decode().strip(),'base':BASE,
  'source_rows':source,'source_sha256':sha(canonical(source)),'inputs_sha256':sha(canonical(inputs)),
  'frozen_inputs':inputs,'host_capture':external['host'],'external':external,'scope':'G1_G7_SAFE_ENGINEERING_NO_LIVE_DISPATCH'}
 v['scope_identity']=sha(canonical(v));return v

def run_path(run_id):
 need(type(run_id) is str and RUN_ID.fullmatch(run_id),'RUN_ID');return no_links(PROGRESS/run_id)
def check(run):
 ledger.budget(run);context=load(run/'context.json');need(context['run_directory']==str(run),'RUN_REBINDING')
 current=binding(*[None if context['external'][n] is None else context['external'][n]['path'] for n in ('host','running','guest')])
 need(current['scope_identity']==context['scope_identity'],'SOURCE_INPUT_CONFIGURATION_DRIFT_NEW_RUN_REQUIRED')
 ledger.verify(run)
 for event in ledger.events(run):
  need(event['stage_id'] in STAGES and event['exact_source_revision']==context['revision'] and event['source_sha256']==context['source_sha256'],'FOREIGN_STAGE_OR_SOURCE')
  expected=[sys.executable,'-I','-B','-c',BOOTSTRAP,str(REPO),event['stage_id'],str(run)]
  need(event['command']==expected and event['argv_identity']==sha(canonical(expected)),'FIXED_FULL_COMMAND_IDENTITY')
  need(event['authorization_reference'] is None,'AUTHORIZATION_RECONSTRUCTION_FORBIDDEN')
  if event['status'] in ('PASS_SOURCE_ONLY','PASS_READ_ONLY_OBSERVED'):need(event['real_subprocess_exit_status']==0,'FAILED_CHILD_CANNOT_PASS')
 return context
def new_run(capture,running=None,guest=None):
 no_links(PROGRESS);need(PROGRESS.is_dir(),'PREPARED_PRIVATE_PROGRESS_REQUIRED')
 if os.name!='nt':need(PROGRESS.stat().st_uid==os.getuid() and PROGRESS.stat().st_mode&0o777==0o700,'PRIVATE_PROGRESS_MODE')
 # Windows setup is separate, reviewed workspace ACL preparation, not host config.
 need(len([p for p in PROGRESS.iterdir() if p.is_dir()])<16,'RUN_COUNT_BOUND')
 c=binding(capture,running,guest);run=run_path(str(uuid.uuid4()));run.mkdir(mode=0o700)
 for n in ('ledger','stages','exports'):(run/n).mkdir(mode=0o700)
 c['run_directory']=str(run);ledger.create_json(run/'context.json',c);return run
def execute(run):
 with ledger.lock(run):
  c=check(run);last=ledger.latest(run)
  if any(r['status'] in ('RUNNING','UNKNOWN','FAIL') for r in last.values()):
   return {'run_id':run.name,'status':'UNKNOWN','reason':'UNRESOLVED_PREVIOUS_CHILD_NO_AUTOMATIC_RETRY'}
  for index,stage in enumerate(STAGES):
   if stage in ledger.latest(run):continue
   command=[sys.executable,'-I','-B','-c',BOOTSTRAP,str(REPO),stage,str(run)];start=time.monotonic_ns()
   ledger.append(run,c,stage,'RUNNING',start=start,command=command)
   try:
    v=runner.child(run,stage,bootstrap=BOOTSTRAP)
    ledger.append(run,c,stage,v['status'],start=start,command=v['argv'],exit_status=v['exit_status'],outputs=v['manifest'],child_pid=v['pid'],observations=v['observations'],next_stage=STAGES[index+1] if index+1<len(STAGES) else None)
   except Exception as e:
    ledger.append(run,c,stage,'UNKNOWN',start=start,command=command,reason='CHILD_EXIT_OR_CLEANUP_UNKNOWN:'+type(e).__name__)
    return {'run_id':run.name,'status':'UNKNOWN','reason':'NO_RETRY_CLEANUP_REVIEW_REQUIRED'}
   check(run)
   if v['status'] in ('FAIL','UNKNOWN'):return {'run_id':run.name,'status':'FAIL','failed_stage':stage}
  return {'run_id':run.name,'status':'PASS_SOURCE_ONLY','stages':len(STAGES),'actual_live_dispatches':0,'ledger':ledger.verify(run)}
def status(run):
 c=check(run);latest=ledger.latest(run);rows=[]
 for stage in STAGES:
  event=latest.get(stage)
  result=None if not event else load(run/'stages'/stage/'stage_result.json')['evidence']
  rows.append({'stage':stage,'source_readiness':'NOT_STARTED' if event is None else event['status'],
   'actual_OS_acceptance':None if result is None else result.get('actual_acceptance'),
   'actual_subprocess_exit':None if event is None else event['real_subprocess_exit_status'],
   'blockers':[] if result is None else result.get('blockers',[])})
 return {'schema':'HH_G1_G7_PROGRESS_V1','run_id':run.name,'source_revision':c['revision'],
  'source_sha256':c['source_sha256'],'stages':rows,'kernel_tests_actually_executed':0,
  'kernel_CPU':None,'kernel_RAM':None,'kernel_disk':None,'new_ME_calls':None,'new_integrals':None,
  'S4_EXECUTED':False,'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'FORMAL_BUILD_ONLY_AUTHORIZED':False,
  'next_safe_action':'REVIEW_FROZEN_PACKAGES; NEW_EVIDENCE_REQUIRES_FRESH_RUN'}
def export(run):
 with ledger.lock(run):
  c=check(run);need(len(list((run/'exports').iterdir()))<16,'EXPORT_BOUND')
  target=run/'exports'/str(uuid.uuid4());target.mkdir(mode=0o700)
  for stage in STAGES:
   row=ledger.latest(run).get(stage)
   if not row or row['status'] not in ('PASS_SOURCE_ONLY','PASS_READ_ONLY_OBSERVED','BLOCKED_AUTHORIZATION','BLOCKED_OS_CAPABILITY'):continue
   for p in (run/'stages'/stage).iterdir():
    if p.suffix=='.json' and p.name!='stage_result.json':
     value=load(p);need('private_raw' not in value,'RAW_EXPORT_FORBIDDEN');ledger.create_json(target/p.name,value)
  ledger.create_json(target/'G1_G7_MASTER_PROGRESS.json',status(run))
  ledger.create_json(target/'G1_G7_SOURCE_MANIFEST.json',{'revision':c['revision'],'files':c['source_rows'],'input_count':len(c['frozen_inputs']),'inputs_sha256':c['inputs_sha256']})
  ledger.create_json(target/'EXPORT_MANIFEST.json',ledger.manifest(target))
  return {'status':'PASS_SOURCE_ONLY','run_id':run.name,'local_export':str(target),'live_dispatches':0}
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);sub=p.add_subparsers(dest='mode',required=True)
 sub.add_parser('plan',allow_abbrev=False)
 r=sub.add_parser('run-safe',allow_abbrev=False);r.add_argument('--host-capture',type=Path,required=True);r.add_argument('--running-receipt',type=Path);r.add_argument('--guest-capture',type=Path)
 for name in ('resume-safe','status','verify','export-review'):sub.add_parser(name,allow_abbrev=False).add_argument('--run-id',required=True)
 a=p.parse_args(argv)
 try:
  if a.mode=='plan':v={'schema':'HH_G1_G7_SAFE_PLAN_V1','stages':list(STAGES),'live_dispatcher':False,'source_and_actual_acceptance_separate':True}
  elif a.mode=='run-safe':v=execute(new_run(a.host_capture,a.running_receipt,a.guest_capture))
  else:
   run=run_path(a.run_id)
   if a.mode=='resume-safe':v=execute(run)
   elif a.mode=='status':v=status(run)
   elif a.mode=='verify':check(run);v=ledger.verify(run)
   else:v=export(run)
  print(json.dumps(v,indent=2));return 2 if v.get('status') in ('FAIL','UNKNOWN') else 0
 except (ValueError,OSError,KeyError,TypeError):print(json.dumps({'status':'FAIL','reason':'SAFE_PROFILE_VALIDATION','execution_authorized':False}));return 2
if __name__=='__main__':raise SystemExit(main())

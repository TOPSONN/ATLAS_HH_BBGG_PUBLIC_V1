"""Sixteen bounded source-only workers. No guest collector dispatch in this DAG."""
import argparse,hashlib,json,os,subprocess,sys,time,unittest,uuid
from pathlib import Path
from . import manager_dependency_contract as c,manager_provider_publication as pub,manager_provider_docs as docs,manager_dependency_tests as dep_tests,manager_native_tests as native_tests,ledger
from .contract import REPO,no_links
from ..src.contracts import input_identity
PROGRESS=REPO/'.local/native_provider_v1';A=REPO.parent
STAGES=('P00_EXACT_SOURCE_BASELINE','P01_HISTORICAL_EVIDENCE_GUARD','P02_NATIVE_FS_AUDIT','P03_POSITIVE_FIXTURE_ENVIRONMENT','P04_ELF_STATIC_PARSER','P05_LOADER_ALIAS_RESOLUTION','P06_TRANSITIVE_DEPENDENCY_GRAPH','P07_PYTHON_IMPORT_CLOSURE','P08_RUNTIME_MAPPING_EVIDENCE_CONTRACT','P09_NATIVE_COLLECTOR_SOURCE','P10_SOURCE_CAPSULE_INTEGRATION','P11_INDEPENDENT_VALIDATOR','P12_SECURITY_NEGATIVE_TESTS','P13_MANAGER_GATE_INTEGRATION','P14_HUMAN_APPROVAL_PACKET','P15_PUBLICATION_AND_FINAL_VERIFICATION')
BOOT='import sys;sys.path.insert(0,sys.argv.pop(1));from simulation.hh_signal.final_closure.master.manager_provider_runner import worker;raise SystemExit(worker(sys.argv[1],sys.argv[2]))'
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def load(path):return json.loads(Path(path).read_bytes())
def identity(folder):
 rows=[(p.relative_to(folder).as_posix(),c.sha(p.read_bytes())) for p in sorted(folder.rglob('*')) if p.is_file()];return {'files':len(rows),'sha256':c.sha(json.dumps(rows,separators=(',',':')).encode())}
def preserved():
 old=Path('C:/HH/.local/phase7i_g2_manager_security_v1');prior=Path('C:/HH/.local/phase7i_g2_tool_binding_v1')
 roots={'PR46_checkpoint':old/'source/.local/manager_security_v1/a56d570b-f323-408e-98f3-c1c28b535433','PR46_delivery_reports':old/'delivery_reports','version_execution':prior/'version_only_execution_01','PR45_checkpoint':prior/'source/.local/tool_binding_review_v1/3bc2b439-3182-4bbe-a667-1f7405691028'}
 return {n:identity(p) for n,p in roots.items()}
def binding():
 c.need(not git('status','--porcelain','--untracked-files=no'),'TRACKED_SOURCE_DIRTY');c.need(git('merge-base',pub.BASE,'HEAD').decode().strip()==pub.BASE,'EXACT_PR46_ANCESTRY')
 old=load(REPO/'reports/phase7i_g2_manager_security/SOURCE_MANIFEST.json');hashes={r['path']:r['sha256'] for r in old['files']};names=set(hashes)|pub.EXACT
 rows=[{'path':n,'sha256':c.sha((REPO/n).read_bytes())} for n in sorted(names)];frozen=[{'path':r['path'],'sha256':r['sha256']} for r in input_identity()];c.need(len(frozen)==1019,'FROZEN_INPUT_COUNT')
 history=load(A/'preservation_before.json');return {'schema':'G2_NATIVE_PROVIDER_SAFE_CONTEXT_V1','revision':git('rev-parse','HEAD').decode().strip(),'base':pub.BASE,'source_rows':rows,'source_sha256':c.sha(c.canonical(rows)),'inputs_sha256':c.sha(c.canonical({'frozen':frozen,'history':history})),'frozen_inputs':1019,'history':history,'live_dispatches':0}
def check(run):
 no_links(run);context=load(run/'context.json');current=binding()
 for k in ('revision','source_sha256','inputs_sha256'):c.need(current[k]==context[k],'EXACT_SOURCE_INPUT_DRIFT_NEW_RUN_REQUIRED')
 ledger.verify(run)
 for event in ledger.events(run):c.need(event['stage_id'] in STAGES and event['exact_source_revision']==context['revision'] and event['authorization_reference'] is None,'FOREIGN_STAGE_OR_AUTHORIZATION')
 return context
def source_hashes():return {n:c.sha((REPO/pub.PREFIX/n).read_bytes()) for n in c.CLOSURE}
class LimitedLog:
 def __init__(self,stream,budget):self.stream=stream;self.budget=budget
 def write(self,text):
  size=len(text.encode('utf-8'))
  if self.budget['bytes']+size>60000:self.budget['overflow']=True;return len(text)
  self.budget['bytes']+=size;return self.stream.write(text)
 def flush(self):return self.stream.flush()
def worker(run_id,stage):
 budget={'bytes':0,'overflow':False};sys.stdout=LimitedLog(sys.stdout,budget);sys.stderr=LimitedLog(sys.stderr,budget)
 try:
  c.need(stage in STAGES and str(uuid.UUID(run_id))==run_id,'FIXED_STAGE_ID');run=PROGRESS/run_id;context=check(run);out=run/'stages'/stage;c.need(not out.exists(),'NO_STAGE_RETRY');out.mkdir()
  outputs=docs.artifacts(stage,context,source_hashes());i=STAGES.index(stage);tests=None;blockers=[]
  if i==0:
   from . import manager_scope_contract as original
   for n,h in original.ORIGINAL_SHA.items():c.need(c.sha((REPO/pub.PREFIX/n).read_bytes())==h,'ORIGINAL_DIAGNOSTIC_CHANGED')
   c.need(c.sha((REPO/'simulation/hh_signal/final_closure/config/physics_contract.json').read_bytes())=='a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb','PHYSICS_CONTRACT')
  if i==1:c.need(preserved()==context['history'],'HISTORICAL_EVIDENCE_DRIFT')
  if i==3:blockers.append('USER_WSL_NOT_EXECUTED; CI_NATIVE_POSITIVE_RESULT_SEPARATE')
  if i==6:
   blobs,roots,edges,aliases=dep_tests.graph_fixture(True);value=dep_tests.p.graph(blobs,roots,edges,aliases);c.need(value['status']=='PASS_STATIC_ELF_GRAPH' and not value['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED'],'STATIC_LEVEL_ESCALATION')
  if i==11:c.need(native_tests.checked_fixture()['status']=='PASS_TEST_FIXTURE_ONLY','INDEPENDENT_VALIDATOR')
  if i==12:
   suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(m) for m in (dep_tests,native_tests)]);r=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite);tests={'run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped)};c.need(r.wasSuccessful(),'FOCUSED_TESTS')
  if i==13:blockers.append('COMPLETE_FUTURE_CHILD_LIFECYCLE_EVIDENCE_NOT_IMPLEMENTED')
  if i==14:blockers.append('NEW_INDEPENDENT_B_THEN_A_APPROVAL_ABSENT; NO_LIVE_DISPATCH')
  if i==15:outputs['G2_PUBLICATION_AUDIT.json']=dict(pub.audit(),scope='SOURCE_COMMIT_SNAPSHOT; DELIVERY_AUDIT_EXTERNAL_AFTER_REPORT_COMMIT')
  c.need(not budget['overflow'],'SAFE_LOG_BOUND_EXCEEDED')
  for name,value in outputs.items():
   c.need(name in pub.STAGE_NAMES,'EXACT_STAGE_ARTIFACT');raw=value.encode() if isinstance(value,str) else c.canonical(value)+b'\n';pub.validate(pub.REPORTS+name,raw);(out/name).open('xb').write(raw)
  result={'status':'PASS_SOURCE_ONLY','source_revision':context['revision'],'stage':stage,'source_sha256':context['source_sha256'],'input_sha256':context['inputs_sha256'],'test_results':tests,'evidence_level':'SOURCE_OR_INERT_FIXTURE_ONLY','actual_user_guest_data':None,'blockers':blockers,'actual_live_dispatches':0,'next_safe_stage':STAGES[i+1] if i+1<len(STAGES) else None}
  ledger.create_json(out/'stage_result.json',result);print(json.dumps({'status':result['status'],'stage':stage}));return 0
 except (ValueError,OSError,KeyError,TypeError):print('{"status":"FAIL_SAFE_NATIVE_SOURCE_WORKER","live_dispatches":0}');return 2
def execute(run):
 with ledger.lock(run):
  context=check(run);latest=ledger.latest(run)
  if any(r['status']!='PASS_SOURCE_ONLY' for r in latest.values()):return {'status':'BLOCKED_UNRESOLVED_SAFE_CHILD_NO_RETRY','run_id':run.name}
  for i,stage in enumerate(STAGES):
   if stage in latest:continue
   argv=[sys.executable,'-I','-B','-c',BOOT,str(REPO),run.name,stage];started=time.monotonic_ns();ledger.append(run,context,stage,'RUNNING',start=started,command=argv)
   log_path=run/'exports'/(stage+'.log');status='UNKNOWN';code=None
   with log_path.open('xb') as log:
    child=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
    try:code=child.wait(timeout=120);status='PASS_SOURCE_ONLY' if code==0 else 'FAIL'
    except subprocess.TimeoutExpired:
     child.kill()
     try:code=child.wait(timeout=1)
     except subprocess.TimeoutExpired:code=None
   c.need(log_path.stat().st_size<=65536,'SAFE_RETAINED_LOG_BOUND')
   folder=run/'stages'/stage;manifest=ledger.manifest(folder) if folder.is_dir() else None
   ledger.append(run,context,stage,status,start=started,command=argv,exit_status=code,outputs=manifest,next_stage=STAGES[i+1] if i+1<len(STAGES) else None,observations={'log_sha256':c.sha(log_path.read_bytes()),'log_bytes':log_path.stat().st_size,'child_soft_timeout_seconds':120,'CPU':None,'RAM':None,'kernel_disk':None,'hard_envelope':False})
   if status!='PASS_SOURCE_ONLY':return {'status':'FAIL_OR_UNKNOWN_NO_AUTOMATIC_RETRY','stage':stage,'run_id':run.name}
   check(run)
  return {'status':'PASS_SOURCE_ENGINEERING_WITH_NATIVE_LIVE_BLOCKERS','run_id':run.name,'stages':16,'ledger':ledger.verify(run),'live_dispatches':0}
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('mode',choices=('run-safe','verify','status','resume-safe'));p.add_argument('--run-id');a=p.parse_args(argv)
 try:
  if a.mode=='run-safe':
   c.need(PROGRESS.is_dir(),'PREPARED_ENGINEERING_PROGRESS_REQUIRED');c.need(len(list(PROGRESS.iterdir()))<16,'RUN_COUNT_BOUND');context=binding();run=PROGRESS/str(uuid.uuid4());run.mkdir()
   for name in ('ledger','stages','exports'):(run/name).mkdir()
   ledger.create_json(run/'context.json',context);value=execute(run)
  else:
   c.need(str(uuid.UUID(a.run_id))==a.run_id,'RUN_ID');run=PROGRESS/a.run_id;check(run)
   value=execute(run) if a.mode=='resume-safe' else dict(ledger.verify(run),run_id=run.name,source_revision=load(run/'context.json')['revision'],actual_user_guest_data=None,live_dispatches=0)
  print(json.dumps(value,indent=2));return 0 if value['status'].startswith('PASS') else 2
 except (ValueError,OSError,KeyError,TypeError):print('{"status":"FAIL_SAFE_NATIVE_PROFILE","live_dispatches":0}');return 2
if __name__=='__main__':raise SystemExit(main())

"""Thirteen bounded safe stages; no manager dispatcher in this engineering DAG."""
import argparse,ast,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
from . import tool_binding_runner as old,diagnostic_plan as prior,readiness_runner as engine,readiness_worker as worker,readiness_stages
from . import manager_scope_contract as contract,manager_scope_docs as docs,manager_scope_tests as tests
from .contract import REPO,canonical,sha,load,need,git,no_links,RUN_ID
from .ledger import create_json
BASE=contract.BASE;PREFIX='simulation/hh_signal/final_closure/master/';PROGRESS=REPO/'.local/manager_security_v1'
STAGES=('S0_EXACT_SOURCE_AND_HISTORY','S1_PRESERVED_VERSION_RECEIPT_REVIEW','S2_SCOPE_ACL_ROOT_CAUSE','S3_NATIVE_PRIVATE_STORAGE_DESIGN','S4_SCOPE_INPUT_FD_PINNING','S5_REVIEWED_SOURCE_STAGING','S6_MINIMUM_DEPENDENCY_CLOSURE','S7_MANAGER_FIXED_ARGV_REVIEW','S8_BUS_FALLBACK_AND_SESSION_REVIEW','S9_INDEPENDENT_RECEIPT_VALIDATOR','S10_NEGATIVE_TESTS','S11_MANAGER_APPROVAL_PACKET','S12_PUBLICATION_AND_PRESERVATION')
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv.pop(1));from simulation.hh_signal.final_closure.master.manager_scope_runner import worker_main;raise SystemExit(worker_main())'
def evidence(path):
 path=no_links(Path(path));need(path.stat().st_size<=16384,'EVIDENCE_INDEX_BOUND');index=load(path);need(index['schema']=='HH_G2_MANAGER_SECURITY_EXISTING_INPUTS_V1','EVIDENCE_INDEX')
 need(set(index['files'])=={'observation','version_receipt','version_scope','version_text','approval_binding','retrospective_record','acl'},'EXACT_EXISTING_EVIDENCE_SET')
 for row in index['files'].values():
  p=no_links(Path(row['path']));need(p.is_file() and p.stat().st_size<=131072 and sha(p.read_bytes())==row['sha256'],'EXTERNAL_EVIDENCE_BYTES')
 return index
def binding(host,running=None,guest=None,*,index_path):
 index=evidence(index_path);c=old.binding(host,running,guest,observation=index['files']['observation']['path'])
 need(git('merge-base',BASE,'HEAD').decode().strip()==BASE,'EXACT_PR45_ANCESTRY')
 previous=load(REPO/'reports/phase7i_g2_tool_binding/SOURCE_MANIFEST.json')['files'];hashes={r['path']:r['sha256'] for r in previous}
 names=set(hashes)|{p.relative_to(REPO).as_posix() for p in (REPO/PREFIX).glob('manager_scope_*.py')}|{'.github/workflows/g2_manager_security.yml'}
 c['source_rows']=[engine.source_row(n,hashes) for n in sorted(names)];c['source_sha256']=sha(canonical(c['source_rows']))
 c['prior_input_sha256']=c['inputs_sha256'];c['inputs_sha256']=sha(canonical({'prior_inputs':c['prior_input_sha256'],'reviewed_evidence_index_sha256':sha(Path(index_path).read_bytes())}))
 c['manager_security_evidence']={'path':str(Path(index_path)),'sha256':sha(Path(index_path).read_bytes()),'files':index['files']};c['base']=BASE;c['scope']='G2_MANAGER_PREEXECUTION_SECURITY_V1_SOURCE_ONLY';c.pop('scope_identity');c['scope_identity']=sha(canonical(c));return c
def raw(c,name):return Path(c['manager_security_evidence']['files'][name]['path']).read_bytes()
def emit(out,name,v):
 if isinstance(v,str):(out/name).open('xb').write(v.encode())
 else:create_json(out/name,v)
def done(finding,blockers=()):return {'status':'PASS_SOURCE_ONLY','evidence':{'actual_acceptance':None,'finding':finding,'remaining_blockers':list(blockers)},'live_execution':False}
def version(c):
 from . import tool_binding_review as r,tool_binding_version_probe as p
 receipt=raw(c,'version_receipt');scope=raw(c,'version_scope');text=raw(c,'version_text');record=load(Path(c['manager_security_evidence']['files']['approval_binding']['path']));external=load(Path(c['manager_security_evidence']['files']['retrospective_record']['path']))
 need(sha(receipt)=='a5a114a7099b0ddf9c8a0c9735501986e1e77b250d615705ac0211b830e090cc' and sha(scope)=='41723b055e30886c3b32ead6d838c4ecae7b4ea1a2aafba4ca747f1192ca3a6f','EXACT_CONSUMED_RECEIPT_SCOPE')
 need(sha(text)=='0e76645d07be2eb646f2cc44163b8a34db3f3ad38cfe07c42105845df37e2e02' and sha(raw(c,'retrospective_record'))=='09c7e3b9b4380d0dd40fdea6a618f997180925ae0b1ab7b3f0d7b0cc0902ca62','HISTORICAL_AUTHORIZATION_IDENTITY')
 s=r.c.load(scope);empty=r.c.load(scope);empty['authorization_reference']=None
 need(empty==p.pending('55777dd8a21964dd87c7294550bd51cef73e5fa8',{n:s['source_sha256'][n] for n in p.EXTRA}),'PENDING_GENERATOR_IDENTITY')
 need(record['scope_sha256']==sha(scope) and record['authorization_reference']==sha(text) and external['historical_authorization_reference']==sha(text) and external['pending_scope_canonical_sha256']==sha(canonical(empty)),'EXTERNAL_APPROVAL_SCOPE_CHAIN')
 v=r.review_version_receipt(receipt,sha(receipt),scope,sha(scope),sha(text));need(v['status']=='OBSERVED_CLIENT_V255_NOT_MANAGER_ATTESTATION','EXISTING_REAL_RECEIPT_VALIDATION');return v
def t0(out,c):
 from ..src.contracts import input_identity
 need(len(input_identity())==1019,'FROZEN_INPUTS');need(sha((REPO/'simulation/hh_signal/final_closure/config/physics_contract.json').read_bytes())=='a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb','PHYSICS_CONTRACT')
 for n,h in contract.ORIGINAL_SHA.items():need(sha((REPO/PREFIX/n).read_bytes())==h,'ORIGINAL_FOUR_CHANGED')
 emit(out,'G2_EXACT_SOURCE_REVIEW.json',{'source_revision':c['revision'],'base':BASE,'source_files':len(c['source_rows']),'frozen_inputs':1019,'old_source_and_data_unchanged':True,'original_four_sha256':contract.ORIGINAL_SHA,'task_B1_hash_text_issue':'57_HEX_CHARACTERS_NOT_SHA256; VERIFIED_PRIOR_64_HEX_FILE_IDENTITY_PRESERVED','new_actual_measurements':None})
 return done('PR45 ancestry and exact protected input identity')
def t1(out,c):
 v=version(c);emit(out,'G2_VERSION_RECEIPT_PRESERVATION.json',{'source_revision':c['revision'],'receipt_sha256':c['manager_security_evidence']['files']['version_receipt']['sha256'],'version_only_verdict':'PASS_ACTUAL_VERSION_ONLY_RECEIPT_VERIFIED','independent_review':v,'client_release':'255.4-1ubuntu8.18','version_approval_consumed':True,'new_live_queries':0,'scope_execution_time_acl':'UNKNOWN','current_scope_acl':'FAIL','provenance':'USER_PROVIDED_VERBATIM_APPROVAL_REPORTED','historical_reference_equals_retrospective_record':False})
 return done('Genuine consumed version receipt revalidated without execution')
def t2(out,c):
 acl=json.loads(raw(c,'acl'));need({r['kind'] for r in acl}=={'OLD_SCOPE','OLD_SOURCE'},'EXACT_WINDOWS_ACL_REVIEW')
 for row in acl:need(any(x['identity'].endswith('Authenticated Users') and 'Modify' in x['rights'] and x['type']=='Allow' for x in row['rules']),'OBSERVED_UNSAFE_WINDOWS_DACL')
 emit(out,'G2_ORIGINAL_SCOPE_ACL_FINDING.md',docs.DOCS['G2_ORIGINAL_SCOPE_ACL_FINDING.md']);return done('Current source/scope inherited DACL unsafe; old execution-time ACL remains unknown',('HISTORICAL_ACL_FAIL_PRESERVED',))
def t3(out,c):
 emit(out,'G2_SCOPE_STORAGE_SECURITY_CONTRACT.json',docs.STORAGE);emit(out,'G2_NATIVE_PRIVATE_SCOPE_IMPLEMENTATION.md',docs.DOCS['G2_NATIVE_PRIVATE_SCOPE_IMPLEMENTATION.md']);return done('Native FS, mount, ACL and FD policy implemented; not deployed',('ACTUAL_NATIVE_IDENTITIES_UNKNOWN',))
def t4(out,c):
 emit(out,'G2_SCOPE_FD_REVIEW.json',{'status':'PASS_SCOPE_STORAGE_SOURCE_ONLY','source_revision':c['revision'],'file':PREFIX+'manager_scope_fs.py','same_fd_original_bytes':True,'path_replacement_detection':True,'POSIX_ACL_policy':'REJECT_NONEMPTY_OR_UNKNOWN','actual_scope_created':False,'actual_linux_file_or_mount_id':None,'host_admin_trust_boundary':'NOT_EXCLUDED'})
 return done('Pinned original scope bytes, pre/post instance checks and exclusive create source')
def t5(out,c):emit(out,'G2_SOURCE_IMPORT_TRUST_REVIEW.md',docs.DOCS['G2_SOURCE_IMPORT_TRUST_REVIEW.md']);return done('Hash-to-import gap replaced by one memory capsule; native source staging not created',('RUNTIME_STDLIB_AND_EXTENSION_TRUST_UNKNOWN',))
def t6(out,c):emit(out,'G2_DEPENDENCY_CLOSURE_REVIEW.json',docs.DEPENDENCIES);return done('Fixed allowlist verification is not transitive closure; dispatch remains blocked',('BLOCKED_DEPENDENCY_CLOSURE',))
def t7(out,c):
 from . import diagnostic_contract as original
 need(contract.fixed_argvs()==original.argvs(1000) and contract.fixed_env()==original.environment(1000),'FIXED_ARGV_ENV_DRIFT');emit(out,'G2_MANAGER_FIXED_QUERY_REVIEW.md',docs.DOCS['G2_MANAGER_FIXED_QUERY_REVIEW.md']);return done('Original three argv, environment, properties and limits unchanged')
def t8(out,c):emit(out,'G2_BUS_AND_SESSION_REQUIREMENTS.md',docs.DOCS['G2_BUS_AND_SESSION_REQUIREMENTS.md']);return done('No-autostart source semantics reviewed; current bus/session not acquired',('CURRENT_BUS_AND_SESSION_UNKNOWN',))
def t9(out,c):
 v=tests.check_fixture();need(v['status']=='PASS_EFFECTIVE_READ_ONLY_OBSERVATION' and v['actual_job_enforcement'] is False,'SYNTHETIC_NO_ENFORCEMENT_PROMOTION')
 emit(out,'G2_INDEPENDENT_RECEIPT_VALIDATOR_RESULTS.json',{'source_revision':c['revision'],'status':'PASS_SOURCE_VALIDATOR_FIXTURES_ONLY','synthetic_complete_observation_status':v['status'],'synthetic_future_delegation':v['future_delegation'],'actual_manager_result':None,'actual_job_enforcement':False,'current_capture_dispatch_blocked_by_dependency_resolution':True,'review_method':'SAME_AGENT_SEPARATE_WORKER_AND_INDEPENDENT_PARSER_NOT_SECOND_HUMAN'})
 return done('Independent source/storage/approval/replay/property validator fixtures; no live manager data')
def t10(out,c):
 suite=unittest.defaultTestLoader.loadTestsFromModule(tests);result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite);need(result.wasSuccessful(),'NEGATIVE_TESTS_FAILED')
 emit(out,'G2_FOCUSED_TESTS.json',{'source_revision':c['revision'],'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'actual_WSL_or_manager_test':False});return done('Focused source/negative tests physically executed in safe worker')
def t11(out,c):
 from . import tool_binding_review as review
 scope=review.pending_scope(c['revision']);hashes={n:sha((REPO/PREFIX/n).read_bytes()) for n in contract.CLOSURE}
 scope['security']={'profile':contract.PROFILE,'source_closure_sha256':hashes,'runtime_manifest_sha256':None,'storage_required':'LINUX_NATIVE_FILESYSTEM_CONFIRMED','dependency_closure_required':True}
 emit(out,'G2_MANAGER_SCOPE_CANDIDATE.json',{'schema':'HH_G2_MANAGER_SCOPE_CANDIDATE_REVIEW_V1','candidate_not_executable':scope,'native_scope_identity':None,'runtime_manifest':None,'new_human_approval':None,'new_scope_actually_created':False,'dispatch_status':'BLOCKED_DEPENDENCY_CLOSURE_AND_NATIVE_DEPLOYMENT'})
 emit(out,'G2_MANAGER_AUTHORIZATION_REQUEST_ZH_TW.md',docs.DOCS['G2_MANAGER_AUTHORIZATION_REQUEST_ZH_TW.md']);emit(out,'G2_MANAGER_SINGLE_USE_COMMAND_ZH_TW.md',docs.command(c['revision'],hashes['manager_scope_bootstrap.py']))
 return done('Exact candidate source closure bound; missing runtime facts are null, no approval manufactured',('NOT_EXECUTION_READY',))
def t12(out,c):
 emit(out,'G2_SAFE_ENGINEERING_CHECKPOINT.json',{'source_revision':c['revision'],'composite_inputs_sha256':c['inputs_sha256'],'profile':'G2_MANAGER_PREEXECUTION_SECURITY_V1','actual_manager_diagnostic':None,'manager_authorization_reference':None,'manager_executed':False,'new_native_queries':0,'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'new_ME_calls':0,'new_integrals':0,'new_events':0,'next_action':'STOP_AFTER_SOURCE_REVIEW; NATIVE_IDENTITY_AND_DYNAMIC_RESOLUTION_REQUIRE_NEW_EXACT_REVIEW'})
 return done('Checkpoint source/inputs bound, stop before any new live gate')
TASKS=dict(zip(STAGES,(t0,t1,t2,t3,t4,t5,t6,t7,t8,t9,t10,t11,t12)))
def worker_main():
 with patch.multiple(worker,STAGES=STAGES,PROGRESS=PROGRESS),patch.object(readiness_stages,'TASKS',TASKS):return worker.main()
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);s=p.add_subparsers(dest='mode',required=True);a=s.add_parser('run-safe');a.add_argument('--host-capture',required=True,type=Path);a.add_argument('--guest-capture',required=True,type=Path);a.add_argument('--evidence',required=True,type=Path)
 for mode in ('status','verify','resume-safe'):s.add_parser(mode).add_argument('--run-id',required=True)
 a=p.parse_args(argv)
 try:
  if a.mode!='run-safe':need(RUN_ID.fullmatch(a.run_id) is not None,'RUN_ID')
  index=a.evidence if a.mode=='run-safe' else load(PROGRESS/a.run_id/'context.json')['manager_security_evidence']['path']
  bind=lambda host,running=None,guest=None:binding(host,running,guest,index_path=index)
  with patch.multiple(prior,BASE=BASE,PROGRESS=PROGRESS,STAGES=STAGES,BOOTSTRAP=BOOTSTRAP,binding=bind):
   args=['run-safe','--host-capture',str(a.host_capture),'--guest-capture',str(a.guest_capture)] if a.mode=='run-safe' else [a.mode,'--run-id',a.run_id]
   return prior.main(args)
 except (ValueError,OSError,KeyError,TypeError):print('{"status":"FAIL_SAFE_MANAGER_SECURITY_PROFILE","live_dispatches":0}');return 2
if __name__=='__main__':raise SystemExit(main())

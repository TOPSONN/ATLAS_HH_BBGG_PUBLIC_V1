"""Six-stage immutable source/input review; no live version/diagnostic dispatcher."""
import argparse,ast,json,sys
from pathlib import Path
from unittest.mock import patch
from . import diagnostic_plan as prior,readiness_runner as engine,readiness_worker as worker,readiness_stages
from . import tool_binding_review as review,tool_binding_docs as docs,tool_binding_version_probe as version
from .contract import REPO,load,canonical,sha,need,git,no_links,RUN_ID
from .ledger import create_json
BASE=review.BASE;PROGRESS=REPO/'.local/tool_binding_review_v1';ORIGINAL_BINDING=prior.binding
STAGES=('T0_EXACT_SOURCE_AND_NEW_INPUT','T1_ACTUAL_TOOL_BINDING','T2_VERSION_AND_DEPENDENCY_REVIEW','T3_PENDING_SCOPE_AND_COMMAND','T4_INDEPENDENT_VALIDATOR','T5_PRESERVATION_AND_PUBLICATION')
PREFIX='simulation/hh_signal/final_closure/master/'
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv.pop(1));from simulation.hh_signal.final_closure.master.tool_binding_runner import worker_main;raise SystemExit(worker_main())'
def binding(host,running=None,guest=None,*,observation):
 c=ORIGINAL_BINDING(host,running,guest);need(git('merge-base',BASE,'HEAD').decode().strip()==BASE,'EXACT_PR44_ANCESTRY')
 path=no_links(Path(observation));need(path.is_file() and path.stat().st_size<=16384,'TOOL_OBSERVATION_BOUND')
 with path.open('rb') as f:raw=f.read(16385)
 need(len(raw)<=16384,'TOOL_OBSERVATION_BOUND');expected=sha(canonical(review.observation())+b'\n');review.check_observation(raw,expected)
 old=load(REPO/'reports/phase7i_g2_effective_diagnostic/SOURCE_MANIFEST.json')['files'];hashes={r['path']:r['sha256'] for r in old}
 names=set(hashes)|{p.relative_to(REPO).as_posix() for p in (REPO/PREFIX).glob('tool_binding_*.py')}|{'.github/workflows/g2_tool_binding.yml'}
 c['source_rows']=[engine.source_row(n,hashes) for n in sorted(names)];c['source_sha256']=sha(canonical(c['source_rows']))
 c['frozen_inputs_sha256']=c['inputs_sha256'];c['tool_observation']={'path':str(path),'sha256':expected,'origin':'USER_REPORTED_NORMALIZED_STATEMENT'}
 c['inputs_sha256']=sha(canonical({'frozen_inputs_sha256':c['frozen_inputs_sha256'],'tool_observation_sha256':expected}))
 c['base']=BASE;c['scope']='NEW_TOOL_BINDING_SOURCE_ONLY_NO_LIVE_QUERY';c.pop('scope_identity');c['scope_identity']=sha(canonical(c));return c
def emit(out,name,value):
 if isinstance(value,str):(out/name).open('xb').write(value.encode())
 else:create_json(out/name,value)
def done(finding,blockers=()):return {'status':'PASS_SOURCE_ONLY','evidence':{'actual_acceptance':None,'finding':finding,'remaining_blockers':list(blockers)},'live_execution':False}
def t0(out,c):
 for n,h in review.SOURCES.items():need(sha((REPO/PREFIX/n).read_bytes())==h,'ORIGINAL_DIAGNOSTIC_SOURCE_CHANGED')
 for row in c['source_rows']:need(sha((REPO/row['path']).read_bytes())==row['sha256'],'SOURCE_DRIFT')
 raw=Path(c['tool_observation']['path']).read_bytes();review.check_observation(raw,c['tool_observation']['sha256'])
 emit(out,'G2_SOURCE_AND_INPUT_BINDING.json',{'base':BASE,'source_revision':c['revision'],'original_source_revision':review.PRIOR_SOURCE,'original_four_sha256':dict(review.SOURCES),'source_files':len(c['source_rows']),'new_observation_sha256':c['tool_observation']['sha256'],'composite_input_sha256':c['inputs_sha256'],'prior_run_rebound':False})
 return done('PR44 source identity exact; new user statement gets a fresh input/source run')
def t1(out,c):
 raw=Path(c['tool_observation']['path']).read_bytes();emit(out,'G2_ACTUAL_TOOL_BINDING.json',review.binding_report(raw,c['tool_observation']['sha256'],c['revision']))
 return done('Three missing expected hashes now bound to reported values, not independently read',('LIVE_TOOL_IDENTITY_NOT_ATTESTED',))
def t2(out,c):
 for name in ('G2_INSTALLED_VERSION_REVIEW.md','G2_DEPENDENCY_CLOSURE.md'):emit(out,name,docs.DOCS[name])
 extra={n:sha((REPO/PREFIX/n).read_bytes()) for n in version.EXTRA}
 emit(out,'G2_PENDING_VERSION_SCOPE_REVIEW.json',{'schema':'HH_G2_VERSION_ONLY_REVIEW_V1','source_revision':c['revision'],'tool_sha256':dict(review.TOOLS),'source_sha256':dict(review.SOURCES,**extra),'argv':['/usr/bin/systemctl','--version'],'environment':review.c.environment(1000),'uid':1000,'gid':1000,'authorization_reference':None,'execution_authorized':False,'actual_output':None,'output_directory_path_sha256':sha(version.VERSION_OUTPUT.encode()),'parent_verified':None,'query_executed':False,'limits':dict(review.LIMITS)})
 return done('Client binary version and interpreter/dynamic closure remain unknown; minimum version-only proposal prepared',('INSTALLED_VERSION_UNKNOWN','DEPENDENCY_CLOSURE_UNKNOWN','PRIVATE_PARENT_UNKNOWN'))
def t3(out,c):
 scope=review.pending_scope(c['revision']);result=review.scope_review(scope)
 emit(out,'G2_SINGLE_USE_SCOPE_REVIEW.json',dict(result,source_revision=c['revision'],original_source_sha256=dict(review.SOURCES),tool_sha256=dict(review.TOOLS),uid=1000,gid=1000,limits=dict(review.LIMITS),output_directory_path_sha256=sha(review.OUTPUT.encode()),private_parent_verified=None))
 emit(out,'G2_FIXED_ARGV_ENV_COMPARISON.json',{'argvs':scope['argvs'],'environment':scope['environment'],'comparison_to_PR44':'BYTE_CANONICAL_EQUAL','changed_commands':0,'version_only_is_separate_scope':True})
 emit(out,'G2_PREEXECUTION_STOP_RULES.md',docs.DOCS['G2_PREEXECUTION_STOP_RULES.md'])
 command='# 單次Ubuntu操作方案（等待獨立批准，現在不可執行）\n\n三個expected binary hashes已由使用者回報填入；完整diagnostic的installed version、dependency closure、bus及private parent仍BLOCKED。此文件不是授權。沒有產生human reference。\n\n## 最小下一個版本query\n\n真正child argv固定為：\n\n```text\n/usr/bin/systemctl --version\n```\n\n這行不是可略過wrapper的建議：必須使用本PR已審tool_binding_version_probe，先驗exact source、三個ELF hash、UID/GID、Python3.12.3及私有parent，pin ELF FD後以原5s/1s wrapper執行。獨立批准後的entry point：\n\n```bash\n/usr/bin/python3 -I -B -c \'import sys;sys.path.insert(0,sys.argv[1]);from simulation.hh_signal.final_closure.master.tool_binding_version_probe import main;raise SystemExit(main(["--scope",sys.argv[2]]))\' "$REVIEWED_EXACT_SOURCE" "$INDEPENDENTLY_APPROVED_VERSION_SCOPE"\n```\n\n兩個變數目前不是已核准值；本機另有完整exact-path命令與pending scope，authorization_reference=null，因此原樣執行會在任何live read之前BLOCKED。scope外部批准與source hash須另核，不能手填任意hash假裝人類授權。原/usr/bin/timeout不執行。\n\n## 原三條完整diagnostic\n\n保留PR44固定argv/env，entry point為同樣exact source中的diagnostic_capture --scope。候選pending scope已在本機exclusive保存，UID/GID與三個tool digest及原四source digest固定；authorization_reference=null、execution_authorized=false。installed family、依賴閉合、sockets及private parent核實之前，不提供會跳過這些門檻的批准方案。\n\n```bash\n/usr/bin/python3 -I -B -c \'import sys;sys.path.insert(0,sys.argv[1]);from simulation.hh_signal.final_closure.master.diagnostic_capture import main;raise SystemExit(main(["--scope",sys.argv[2]]))\' "$REVIEWED_EXACT_SOURCE" "$INDEPENDENTLY_APPROVED_DIAGNOSTIC_SCOPE"\n```\n\n這是等待資料與獨立批准的精確entry contract，不是execution-ready命令。原三條argv見G2_FIXED_ARGV_ENV_COMPARISON.json；真tool/source values見G2_ACTUAL_TOOL_BINDING.json。執行前必須保留此exact source revision `'+c['revision']+'`；任何來源/輸入變更用fresh run。\n'
 emit(out,'G2_USER_EXECUTION_COMMAND_ZH_TW.md',command)
 return done('Pending full scope has exact observed hashes but remains blocked; no authorization manufactured',result['remaining_blockers'])
def t4(out,c):
 from .tool_binding_tests import version_fixture,elf_fixture
 from .tool_binding_elf import inspect
 from .diagnostic_tests import fixture,review as independent
 s,v=fixture();v['queries'][1]={'argv':s['argvs'][1],'skipped':'NO_EXISTING_OWNED_SOCKET'};missing=independent(s,v);need(missing['status']=='UNKNOWN_MANAGER_STATE','MISSING_BUS_UPGRADE')
 version_result=review.version_result(version_fixture());facts=inspect(elf_fixture())
 emit(out,'G2_INDEPENDENT_VALIDATOR_RESULTS.json',{'scope':'SYNTHETIC_VERSION_ELF_AND_ORIGINAL_RECEIPT_VALIDATORS_ONLY','source_revision':c['revision'],'original_independent_validator_sha256':review.SOURCES['diagnostic_validate.py'],'synthetic_missing_bus_status':missing['status'],'synthetic_version_family_match':version_result['verified'],'synthetic_ELF_closure_verified':facts['transitive_dynamic_closure_verified'],'actual_manager_state':None,'actual_version_result':None,'review_method':'SAME_AGENT_SEPARATE_STAGE_PROCESS_NO_SECOND_HUMAN','actual_user_query_executed':False})
 return done('Synthetic results cannot establish manager state or dependency closure')
def t5(out,c):
 emit(out,'G2_NEXT_ACTUAL_OS_ACTION.md',docs.DOCS['G2_NEXT_ACTUAL_OS_ACTION.md'])
 emit(out,'G2_BINDING_CHECKPOINT.json',{'source_revision':c['revision'],'observation_sha256':c['tool_observation']['sha256'],'TOOL_IDENTITY_OBSERVED':True,'TOOL_IDENTITY_VERIFIED':False,'INSTALLED_SYSTEMD_VERSION_VERIFIED':False,'DIAGNOSTIC_SOURCE_READY':True,'DIAGNOSTIC_EXECUTION_AUTHORIZED':False,'DIAGNOSTIC_ACTUALLY_EXECUTED':False,'G2_MANAGER_STATE_VERIFIED':False,'G2_CGROUP_DELEGATION_VERIFIED':False,'G2_ARCHITECTURE_ACCEPTED':False,'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'actual_version':None,'actual_CPU':None,'actual_RAM':None,'actual_wall':None,'actual_disk':None,'new_ME_calls':0,'new_integrals':0,'new_events':0})
 return done('Safe review complete; stop at new independent version-only approval boundary')
TASKS=dict(zip(STAGES,(t0,t1,t2,t3,t4,t5)))
def worker_main():
 with patch.multiple(worker,STAGES=STAGES,PROGRESS=PROGRESS),patch.object(readiness_stages,'TASKS',TASKS):return worker.main()
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);s=p.add_subparsers(dest='mode',required=True)
 a=s.add_parser('run-safe',allow_abbrev=False);a.add_argument('--host-capture',required=True,type=Path);a.add_argument('--guest-capture',required=True,type=Path);a.add_argument('--tool-observation',required=True,type=Path)
 for mode in ('status','verify','resume-safe'):s.add_parser(mode,allow_abbrev=False).add_argument('--run-id',required=True)
 a=p.parse_args(argv)
 try:
  if a.mode!='run-safe':need(RUN_ID.fullmatch(a.run_id) is not None,'RUN_ID')
  observation=a.tool_observation if a.mode=='run-safe' else load(PROGRESS/a.run_id/'context.json')['tool_observation']['path']
  bind=lambda host,running=None,guest=None:binding(host,running,guest,observation=observation)
  with patch.multiple(prior,BASE=BASE,PROGRESS=PROGRESS,STAGES=STAGES,BOOTSTRAP=BOOTSTRAP,binding=bind):
   args=['run-safe','--host-capture',str(a.host_capture),'--guest-capture',str(a.guest_capture)] if a.mode=='run-safe' else [a.mode,'--run-id',a.run_id]
   return prior.main(args)
 except (OSError,ValueError,KeyError,TypeError):print('{"status":"FAIL_SAFE_TOOL_BINDING_PROFILE","live_dispatches":0}');return 2
if __name__=='__main__':raise SystemExit(main())

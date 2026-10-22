"""Meaningful read-existing/source preparation, never live diagnostic execution."""
import ast,json
from pathlib import Path
from . import diagnostic_contract as d,diagnostic_docs as docs,g2_catalogue as old,g2_stages
from .contract import REPO,PHYSICS,GUARD,sha,canonical,load,need
from .ledger import create_json
from .diagnostic_plan import STAGES
PREFIX='simulation/hh_signal/final_closure/master/'
def emit(out,name,value):
 if isinstance(value,str):
  raw=value.encode();need(len(raw)<=131072,'DOCUMENT_BOUND');(out/name).open('xb').write(raw)
 else:create_json(out/name,value)
def done(finding,blockers=()):return {'status':'PASS_SOURCE_ONLY','evidence':{'actual_acceptance':None,'new_technical_finding':finding,'blockers':list(blockers),'next_safe_action':'REVIEW_PRELIMINARY_TOOL_QUERY_ONLY'},'live_execution':False}
def document(out,name):emit(out,name,docs.DOCS[name])
def d0(out,c):
 for row in c['source_rows']:need(sha((REPO/row['path']).read_bytes())==row['sha256'],'SOURCE_HASH')
 for name in ('host','guest'):g2_stages.external(c,name)
 prior=load(REPO/'reports/phase7i_g2_actual_capability/SAFE_STAGE_RECEIPTS.json')
 need(prior['source_revision']=='d1ec58c011f4f534ed04ba67de8c6ef95afa503c' and prior['run_id']=='7424d623-514b-4511-a8a8-9d9b1656787e','PRIOR_RUN_IDENTITY')
 emit(out,'D0_PRESERVED_EVIDENCE.json',{'base':c['base'],'source_revision':c['revision'],'source_sha256':c['source_sha256'],'external_sha256':{n:c['external'][n]['sha256'] for n in ('host','guest')},'prior_run_not_rebound':True,'new_G1_capture':False,'current_guest_freshness':'UNKNOWN'})
 return done('PR43 exact evidence reused; old boot/session freshness remains unknown')
def d1(out,c):
 sources={n:sha((REPO/PREFIX/n).read_bytes()) for n in d.SOURCE_NAMES}
 emit(out,'G2_DIAGNOSTIC_TOOL_MANIFEST.json',{'schema':'HH_G2_PENDING_TOOL_BINDING_V1','source_revision':c['revision'],'source_sha256':sources,
  'tool_sha256':{p:None for p in d.TOOLS},'resolved_tool_identity':'UNKNOWN_REQUIRES_USER_HASH_ONLY_QUERY','actual_version':'UNKNOWN','runtime_dependency_closure':'UNATTESTED_DYNAMIC_LIBRARIES_AND_PYTHON_STDLIB','systemd_review_family':'255_ONLY_NOT_INSTALLED_VERSION_ATTESTATION','execution_ready':False})
 command="/usr/bin/python3 -I -B -c 'import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[1]); b=p.open(\"rb\").read(131073); assert len(b)<=131072 and hashlib.sha256(b).hexdigest()==sys.argv[2], \"SOURCE_HASH_MISMATCH\"; exec(compile(b,str(p),\"exec\"),{\"__name__\":\"__main__\",\"__file__\":str(p)})' \"$DIAG_ROOT/"+PREFIX+"diagnostic_tools.py\" '"+sources['diagnostic_tools.py']+"'"
 emit(out,'G2_DIAGNOSTIC_COMMAND_ZH_TW.md','# 最小下一步：hash-only bootstrap，完整diagnostic未批准\n\n先另審此單次query，只在已開啟的Ubuntu非root session操作，不啟動WSL。DIAG_ROOT須指向此exact source checkout；它不是tool hash占位值。工具身分仍UNKNOWN。\n\n```bash\nDIAG_ROOT="$(pwd -P)"\n'+command+'\n```\n\n只讀三個ELF、link/stat/owner/mode與目前Python版本/UID/GID，不執行systemctl或timeout、不讀proc/sys inventory、不寫receipt、不連bus/network。來源hash是此source的真值。Python自身尚屬bootstrap觀察，不是root-of-trust attestation；查到的SHA及version仍須獨立source/family審查。輸出為HASH_ONLY_OBSERVED_NOT_ATTESTED；不得拿它批准後續query。若錯誤先保留一次輸出，不重試。\n\n完整adapter必須等三個binary真值、resolved identity、source revision/hash、UID/GID、private parent與獨立human scope reference核實後另審。現在沒有可執行的完整scope，無假hash、無預先授權。\n')
 return done('Exact hash-only probe available; three live binary hashes genuinely UNKNOWN',('BLOCKED_TOOL_IDENTITY','BLOCKED_AUTHORIZATION'))
def d2(out,c):document(out,'G2_MANAGER_ARGV_REVIEW_ZH_TW.md');return done('v255 user private socket has internal default-user fallback; fixed poisoned address required',('INSTALLED_VERSION_HASH_REVIEW',))
def d3(out,c):document(out,'G2_DELEGATION_OBSERVABLES_ZH_TW.md');return done('Existing user service Delegate/accounting are distinct from future protected groups',('UNKNOWN_EFFECTIVE_DELEGATION',))
def d4(out,c):
 document(out,'G2_DIAGNOSTIC_STOP_RULES.md')
 scope={'schema':'HH_G2_DIAGNOSTIC_SCOPE_PROPOSAL_V1','source_revision':c['revision'],'source_sha256':{n:sha((REPO/PREFIX/n).read_bytes()) for n in d.SOURCE_NAMES},
  'tool_sha256':{p:None for p in d.TOOLS},'uid':None,'gid':None,'authorization_reference':None,'execution_authorized':False,
  'argv_templates':[['/usr/bin/systemctl','--no-pager','--no-ask-password',mode,'show','--property=Version','--property=SystemState'] for mode in ('--system','--user')]+[['/usr/bin/systemctl','--no-pager','--no-ask-password','--system','show','user@REVIEWED_NONROOT_UID.service']+['--property='+p for p in d.PROPS]],
  'limits':{'child_seconds':5,'cleanup_seconds':1,'adapter_soft_seconds':30,'per_child_bytes':8192,'aggregate_bytes':32768,'receipt_bytes':131072,'max_levels':8},
  'fixed_private_output_required':True,'output_path_binding':'USER_PRIVATE_EXACT_SCOPE_REQUIRED_NOT_PUBLIC_HOST_PATH','no_autostart_fallback':True,
  'actual_queries':0,'diagnostic_adapter_executed':False,'hard_resource_envelope':False}
 emit(out,'G2_DIAGNOSTIC_SCOPE.json',scope)
 for name in d.SOURCE_NAMES:ast.parse((REPO/PREFIX/name).read_bytes())
 return done('Pinned ELF child, pidfd/unreaped group cleanup, bounded streams and exclusive receipt source implemented',('ACTUAL_TOOL_BINDING_AND_SINGLE_USE_SCOPE',))
def d5(out,c):
 from .diagnostic_tests import fixture,review
 s,r=fixture();good=review(s,r);need(good['status']=='UNKNOWN_DELEGATION' and not good['actual_job_enforcement'],'VALIDATOR_CEILING')
 r['autostart_fallback']=True;bad=review(s,r);need(bad['status']=='FAIL_SOURCE_OR_RECEIPT_MISMATCH','NEGATIVE_FALLBACK')
 emit(out,'G2_VALIDATOR_SOURCE_REVIEW.json',{'independent_of_capture_parser':True,'original_bytes_sha_required':True,'duplicate_keys_and_canonical_numbers':True,'synthetic_positive_status':good['status'],'synthetic_negative_status':bad['status'],'actual_user_system_measurement':False,'missing_delegation_never_PASS':True,'review_method':'SAME_AGENT_SEPARATE_WORKER_PROCESS_NOT_SECOND_HUMAN'})
 return done('Independent validator preserves observed manager vs unknown future delegation')
def d6(out,c):
 rows=docs.clause_review();paths=('simulation/hh_signal/final_closure/resource_closure/config/b_v2_research_execution_terms.json',PREFIX+'b_v2_cost_assignment.json',PREFIX+'readiness_observer_amendment.json')
 for name,h in zip(paths,(old.TERMS,old.VM,old.OBSERVER)):
  raw=(REPO/name).read_bytes();need(sha(raw)==h,'ORIGINAL_B_DOCUMENT');value=load(REPO/name);need(value['user_accepted'] is False and value['execution_authorized'] is False,'NO_INFERRED_ACCEPTANCE')
 emit(out,'G2_B1_B8_DECISION_REVIEW.json',{'A':'A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST','B_V2':'CONDITIONAL_REVIEW_ONLY_ASYNC_OWNERSHIP_UNRESOLVED','unchanged_document_sha256':[old.TERMS,old.VM,old.OBSERVER],'clauses':rows,'all_accepted':False})
 text='# B1–B8 逐條人類決策\n\n三份原文件不改；全部未接受。\n\n'
 for row in rows:text+='## '+row['clause']+'\n\n'+'\n\n'.join(k+'：'+str(value) for k,value in row.items() if k!='clause')+'\n\n'
 emit(out,'G2_B1_B8_DECISION_REVIEW_ZH_TW.md',text.rstrip()+'\n');return done('B1 needs separate async cost amendment; no implied acceptance')
def d7(out,c):document(out,'G2_ASYNC_KERNEL_COST_AMENDMENT_PROPOSAL_V1.md');return done('Fixed journal/disk blocks cannot prove asynchronous CPU ownership',('BLOCKED_OS_CAPABILITY_ASYNC_COST',))
def d8(out,c):
 document(out,'G3_PROTOCOL_TO_DEPLOYMENT_GAPS.md')
 emit(out,'G3_SOURCE_PRESERVATION.json',{'paths':[{'path':PREFIX+n,'sha256':sha((REPO/PREFIX/n).read_bytes())} for n in ('g2_protocol.py','g2_protocol_tests.py')],'existing_protocol_modified':False,'actual_collector':False,'actual_observer':False,'deployment_status':'BLOCKED_OS_CAPABILITY'})
 return done('No reproducible new defect in PR43 protocol; diagnostic is not protected native deployment',('BLOCKED_OS_CAPABILITY',))
def d9(out,c):
 emit(out,'G4_G7_MINIMUM_CAPABILITY_PATH.json',{'qualified_device':None,'rows':[
  {'gate':'G4','requires':'Exact disposable whole device, host/guest/same-instance exclusivity, no root/history/thin/sparse device','depends_on':['HOST_GUEST_CURRENT_IDENTITY','ARCHITECTURE_APPROVAL'],'status':'BLOCKED_OS_CAPABILITY'},
  {'gate':'G5','requires':'Reviewed same-instance consumer and exact approved format geometry/tool identity','depends_on':['G4'],'status':'BLOCKED_OS_CAPABILITY'},
  {'gate':'G6','requires':'Actual allocated blocks/inodes, metadata/journal/failure slots and durability readback','depends_on':['G5'],'status':'BLOCKED_OS_CAPABILITY'},
  {'gate':'G7','requires':'Mount namespace, protected collector UID, delegated parent/sibling groups, final observer','depends_on':['G2_EFFECTIVE_CAPABILITY','G3_PROTECTED_ACQUIRER','G6'],'status':'BLOCKED_OS_CAPABILITY'}],
  'provisioning':False,'format':False,'readback':False,'mount':False,'ready_for_S4':False})
 return done('No qualified fixed device; D2 observation cannot bypass G4 through G7')
def d10(out,c):
 document(out,'SCIENTIFIC_CONTINUATION_FEASIBILITY_ZH_TW.md')
 from ..src.contracts import input_identity
 need(sha((REPO/'simulation/hh_signal/final_closure/config/physics_contract.json').read_bytes())==PHYSICS,'PHYSICS')
 need(sha((REPO/'simulation/hh_signal/final_closure/guard_correction/native_checks_corrected.f').read_bytes())==GUARD,'GUARD')
 emit(out,'FROZEN_SCIENCE_PREFLIGHT.json',{'physics_sha256':PHYSICS,'guard_sha256':GUARD,'frozen_inputs':len(input_identity()),'new_cards':False,'B_C_separation_preserved':True,'seeds':[910001,910019,910037,910061],'exploratory_scope_authorized':False,'new_ME_calls':0,'new_integrals':0,'new_events':0})
 return done('Physics remains frozen; exploratory sandbox would require a separate weaker scope')
def d11(out,c):
 emit(out,'DIAGNOSTIC_PREPARATION_CHECKPOINT.json',{'source_revision':c['revision'],'source_sha256':c['source_sha256'],'profile':'NEW_DIAGNOSTIC_PREPARATION_V1','tool_binding':'UNKNOWN','next_safe_action':'REVIEW_EXACT_HASH_ONLY_COMMAND','new_acquisition':False,'diagnostic_executed':False,'S4_EXECUTED':False,'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'FORMAL_BUILD_ONLY_AUTHORIZED':False,'PHYSICAL_RESTART_AUTHORIZED':False,'actual_kernel_CPU':None,'actual_kernel_RAM':None,'actual_kernel_wall':None,'actual_kernel_disk':None})
 return done('All source-only stages finished; stop rather than retry blocked live tools')
TASKS=dict(zip(STAGES,(d0,d1,d2,d3,d4,d5,d6,d7,d8,d9,d10,d11)))

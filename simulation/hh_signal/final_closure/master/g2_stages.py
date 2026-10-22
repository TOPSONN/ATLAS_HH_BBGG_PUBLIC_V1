"""Fixed read-existing/pure stages for the G2 decision and protocol review."""
import ast,json
from pathlib import Path
from .contract import REPO,PHYSICS,GUARD,LIMITS,load,need,canonical,sha
from .ledger import create_json
from . import g2_catalogue as cat
from . import g2_protocol as protocol
from .g2_protocol_tests import fixture,negative_cases
from .g2_runner import STAGES

PREFIX='simulation/hh_signal/final_closure/master/'
def emit(out,name,value):
 if isinstance(value,str):
  raw=value.encode('utf-8');need(len(raw)<=131072,'DOCUMENT_BOUND')
  with (out/name).open('xb') as f:f.write(raw)
 else:create_json(out/name,value)
def docs(out,*names):
 for name in names:emit(out,name,cat.DOCS[name])
def done(e):return {'status':'PASS_SOURCE_ONLY','evidence':dict(e,actual_acceptance=None),'live_execution':False}
def external(c,name):
 row=c['external'][name];raw=Path(row['path']).read_bytes();need(len(raw)<=262144 and sha(raw)==row['sha256'],'IMMUTABLE_EXTERNAL_DRIFT');return load(row['path'])
def levels(*,observed=False,implemented=True):
 return {'SOURCE_IMPLEMENTED':implemented,'SOURCE_TESTED':'SYNTHETIC_OR_PURE_ONLY','OS_INTERFACE_OBSERVED':observed,
  'OS_CAPABILITY_SUPPORTED':'DOCUMENTED_API_IN_REPORTED_FAMILY_NOT_INSTALLED_BINARY_ATTESTATION',
  'EFFECTIVE_CONFIGURATION_VERIFIED':'UNKNOWN_FOR_NEW_JOB','ACTUAL_JOB_ENFORCEMENT_VERIFIED':False,
  'BLOCKED_AUTHORIZATION':True,'UNKNOWN':['CURRENT_MANAGER_PRIVILEGES','CURRENT_DELEGATION','CURRENT_FRESHNESS']}
def cpu_rows(observed):
 names=('cpu.max','cpu.stat','cpu.weight','cgroup.controllers','cgroup.subtree_control','cgroup.procs','CPUAccounting','CPUQuota','hierarchical_membership','delegation','final_cumulative_CPU')
 pure={'cpu.max','cpu.stat','cgroup.procs','hierarchical_membership','final_cumulative_CPU'}
 capture={'cgroup.controllers','cgroup.subtree_control'}
 rows=[]
 for n in names:
  implemented=n in pure|capture
  row=dict(capability=n,**levels(observed=n in observed,implemented=implemented),meaning='CPU_RATE_LIMIT' if n in ('cpu.max','CPUQuota') else 'RELATIVE_WEIGHT_ONLY' if n=='cpu.weight' else 'ACCOUNTING_OR_OWNERSHIP_NOT_LIFETIME_HARD_KILL')
  row.update(SOURCE_TESTED='PURE_VALIDATOR_FIXTURES' if n in pure else 'EXISTING_GENERIC_CAPTURE_FIXTURES_ONLY' if n in capture else 'NO_G2_IMPLEMENTATION_TO_TEST',
   source_layer='PURE_VALIDATOR' if n in pure else 'EXISTING_READONLY_COLLECTOR_ONLY' if n in capture else 'DOCUMENTED_INTERFACE_OR_LEGACY_PROPOSAL_ONLY',
   G2_NATIVE_JOB_ACQUIRER_IMPLEMENTED=False,G2_CONFIGURATION_MUTATOR_IMPLEMENTED=False)
  rows.append(row)
 return rows
def r0(out,c):
 from ..src.contracts import input_identity
 from ..guard_correction.overlay import source
 need(sha((REPO/'simulation/hh_signal/final_closure/config/physics_contract.json').read_bytes())==PHYSICS and sha(source().encode())==GUARD,'FROZEN_PHYSICS_GUARD_DRIFT')
 for row in c['source_rows']:need(sha((REPO/row['path']).read_bytes())==row['sha256'],'SOURCE_MANIFEST_DRIFT')
 inputs=input_identity();need(len(inputs)==1019,'FROZEN_INPUT_COUNT')
 for n in ('host','guest'):external(c,n)
 value={'base_revision':c['base'],'source_revision':c['revision'],'source_sha256':c['source_sha256'],'source_files':len(c['source_rows']),
  'frozen_inputs':len(inputs),'physics_contract_sha256':PHYSICS,'corrected_guard_sha256':GUARD,'new_G1_capture':False,
  'external_sha256':{n:c['external'][n]['sha256'] for n in ('host','guest')},'runtime_enforcement':False}
 emit(out,'G2_EXACT_BASE_AND_EVIDENCE.json',value);return done(value)

def r1(out,c):
 from ..resource_closure import g1_acquisition as g
 host=external(c,'host');g.validate_host(host);hp=g.public_projection(host)
 need(len(hp['coverage'])==13 and all(r['status']=='REPORTED_UNATTESTED' for r in hp['coverage']),'ACCEPTED_HOST_COVERAGE_DRIFT')
 counts={row['item']:row['row_count'] for row in hp['coverage']}
 need(counts['disk_partition_links']==4 and counts['partition_volume_links']==1,'ACCEPTED_ASSOCIATION_EDGE_COUNT')
 prior=load(REPO/'reports/g1_guest_v2_counter_repair/G1_GUEST_VALIDATION.json')
 need(prior['raw_sha256']==c['external']['guest']['sha256'] and prior['review']['status']=='PASS_READ_ONLY_OBSERVED','ACCEPTED_GUEST_REPORT_BINDING')
 guest=external(c,'guest');need(guest['source_sha256']==prior['collector_source_sha256'],'GUEST_COLLECTOR_IDENTITY')
 missing=prior['review']['missing_counter_names'];need(len(missing)==10 and not prior['review']['nonroot_missing_counter_names'],'ACCEPTED_MISSING_INTERFACE_DRIFT')
 raw_rows={r['path']:r for r in guest['records']}
 need(all(raw_rows[guest['cgroup_lineage'][-1]+'/'+n]['status']=='UNKNOWN' and raw_rows[guest['cgroup_lineage'][-1]+'/'+n].get('reason')=='FileNotFoundError' for n in missing),'ROOT_ABSENCE_OBSERVATION_CHANGED')
 source={f:cat.MEM for f in missing if f.startswith('memory.')}
 source.update({'cgroup.events':cat.CORE,'cgroup.type':cat.CORE,'cpu.max':cat.LINUX,'pids.max':cat.LINUX})
 value={'host_coverage':'13/13 REPORTED_UNATTESTED','disk_partition_edges':4,'partition_logical_edges':1,
  'guest_validation':'PASS_READ_ONLY_OBSERVED','lineage_count':2,'nonroot_missing':0,'root_missing_count':10,
  'root_missing_interfaces':[{'field':n,'raw_state':'UNKNOWN_FILE_NOT_FOUND','upstream_nonroot_only':True,'source':source[n],
   'classification':'EXPECTED_UPSTREAM_INTERFACE_ABSENCE_NOT_DEPLOYMENT_FAILURE'} for n in missing],
  'root_classification_basis':'Linux v6.6 upstream flags/docs; installed Microsoft kernel build not attested',
  'unlimited_observed_group_is_not_proof_new_group_cannot_be_constrained':True,
  'freshness':'UNKNOWN','effective_manager':'UNKNOWN','new_queries':0,'guest_raw_sha256':prior['raw_sha256']}
 emit(out,'G1_FINAL_EVIDENCE_RECONCILIATION.json',value);return {'status':'PASS_READ_ONLY_OBSERVED','evidence':dict(value,actual_acceptance=None),'live_execution':False}

def r2(out,c):
 guest=external(c,'guest');leaf=guest['cgroup_lineage'][0]
 observed={r['path'].rsplit('/',1)[-1] for r in guest['records'] if r['status']=='REPORTED_UNATTESTED' and r['path'].startswith(leaf+'/')}
 rows=cpu_rows(observed)
 value={'rows':rows,'nominal_CPU_usec':{'S4':4000000,'BUILD':14400000000},'shared_budget_not_per_role':True,
  'original_A_zero_overshoot_supported_by_standard_interfaces':False,'new_job_permission':'UNKNOWN_NOT_TESTED','actual_CPU_usec':None}
 emit(out,'G2_CPU_CAPABILITY_MATRIX.json',value);docs(out,'G2_CPU_ACCOUNTING_PROTOCOL.md','G2_CPU_FAILURE_MODEL.md');return done({'blockers':['EFFECTIVE_MANAGER_DELEGATION_AND_TRUSTED_CAPTURE','LIVE_CUMULATIVE_STOP_TESTS'],**levels(observed=True)})

def r3(out,c):
 work=2147483648;private=268435456;total=protocol.checked_add(work,private)
 value={'observed_memory_max':'UNLIMITED','observed_swap_max':'UNLIMITED','observation_scope':'HISTORICAL_SHELL_GROUP_ONLY',
  'new_dedicated_job_cannot_be_constrained_inferred':False,'S4_RAM_bytes':536870912,'BUILD_RAM_bytes':2147483648,'swap_bytes':0,
  'BUILD_tmpfs_ceiling_sum_bytes':total,'BUILD_tmpfs_full_minus_RAM_bytes':total-2147483648,
  'BUILD_full_fill_possible_under_RAM':False,'runtime_resident_allocation':None,'actual_memory_peak_bytes':None,'actual_swap_bytes':None,
  'standard_memory_max_guarantees_literal_zero_transient_overshoot':False,'levels':levels(observed=True)}
 value['interface_levels']={n:levels(observed=n!='memory.events.local') for n in ('memory.max','memory.current','memory.peak','memory.events','memory.events.local','memory.swap.max','memory.swap.current')}
 emit(out,'G2_MEMORY_SWAP_ACTUAL_GAP.json',value);docs(out,'G2_MEMORY_CHARGING_AND_TMPFS.md','G2_OOM_AND_COLLECTOR_SURVIVAL.md');return done({'blockers':['BUILD_RESIDENT_PLAN_AND_REAL_MEASUREMENTS','ACTUAL_EFFECTIVE_SWAP_ZERO_AND_ANCESTORS'],**levels(observed=True)})

def r4(out,c):
 rows,contract=fixture();value={'clock':'SAME_BOOT_MONOTONIC_NS_WITH_SAMPLE_WINDOWS','phase_order':list(protocol.PHASES),
  'S4_wall_ns':13000000000,'BUILD_wall_ns':14400000000000,'Main_PID_exit_is_terminal_proof':False,
  'RuntimeMaxSec_is_full_lifecycle':False,'real_time_scheduling_guarantee':False,'actual_admission_to_cleanup_ns':None,
  'source_state_machine':'g2_protocol.stop_decision','executable_OS_actions':False}
 emit(out,'G2_WALL_LIFECYCLE_CONTRACT.json',value)
 tests=[]
 for event in protocol.FAILURES+('OBSERVER_LOST',):
  r=protocol.stop_decision('RUNNING',event,cpu_usec=0,elapsed_ns=1,stop_elapsed_ns=0,c=contract)
  tests.append({'event':event,'result':r,'evidence_kind':'SYNTHETIC'})
 emit(out,'G2_TIMEOUT_NEGATIVE_TESTS.json',{'scope':'SYNTHETIC_SOURCE_ONLY','cases':tests,'actual_kernel_timeout_test':False})
 docs(out,'G2_CONTROLLER_STOP_STATE_MACHINE.md');return done({'blockers':['INDEPENDENT_MANAGER_DEADLINE_AND_FINAL_OBSERVER_DEPLOYMENT'],'state_machine_implemented':True,'actual_wall_ns':None})

def r5(out,c):
 from .readiness_stages import resource_ledger
 ledger=resource_ledger();roles=[]
 for old in ledger['roles']:
  owner=old['B_V2_proposed_owner'];external_role=owner in ledger['external_roles']
  roles.append({'role':old['role'],'original_A_owner':'ONE_ALL_HOST_GUEST_TOTAL','B_proposed_owner':owner,
   'CPU_charged_to':owner,'RAM_charged_to':owner,'disk_charged_to':'JOB_FIXED_CAPACITY_FOR_ALL_JOB_WRITES' if 'job_parent' in owner else owner,
   'wall_lifecycle_inclusion':'ADMISSION_TO_FINAL_READBACK' if not external_role else 'EXTERNAL_NONZERO_COST_UNMEASURED',
   'observable_counters':'PARENT_CPU_STAT_MEMORY_EVENTS_IF_DEPLOYED' if not external_role else 'NO_CURRENT_JOINT_ATTESTED_COUNTER',
   'available_enforcer':'DOCUMENTED_CGROUP_SEMANTICS_NOT_DEPLOYED' if not external_role else 'JOINT_ENFORCER_NOT_IMPLEMENTED',
   'CPU_actual':None,'RAM_actual':None,'disk_actual':None,'actual_evidence':'G1_INVENTORY_OR_SOURCE_ONLY','external_or_unknown':external_role})
  if owner=='job_parent_fixed_device':roles[-1].update(CPU_charged_to='WRITER_PARENT_PLUS_ASYNC_KERNEL_UNVERIFIED',RAM_charged_to='MEMCG_WITH_UNVERIFIED_KERNEL_PORTIONS',
   external_or_unknown=True,available_enforcer='FIXED_STORAGE_POLICY_ONLY_NO_ASYNC_KERNEL_CPU_ATTESTATION')
 value={'verdict':'A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST','reason_not_based_on_unlimited_shell_alone':True,
  'all_platforms_impossible_claimed':False,'roles':roles,'per_role_duplicate_full_budgets':False,'live_enforcement_verified':False}
 emit(out,'G2_ARCHITECTURE_A_REAL_FEASIBILITY.json',value)
 emit(out,'G2_A_MISSING_HARD_GUARANTEES.json',{'guarantees':['JOINT_WINDOWS_GUEST_VMM_CPU_RAM','ZERO_DELAY_CUMULATIVE_CPU_STOP','ZERO_TRANSIENT_RAM_OVERSHOOT',
  'FULL_CONTROL_PLANE_ALLOCATED_DISK','INDEPENDENT_COLLECTOR_POST_EXIT_RAW_EVIDENCE','ALL_ROLE_CLEANUP_WITH_FINAL_CPU_WALL'],
  'actual_measurements':None,'strict_A_preserved':True,'global_technical_impossibility_claimed':False})
 docs(out,'G2_HOST_GUEST_ACCOUNTING_GAP.md');return done({'A_verdict':value['verdict'],'blockers':cat.BLOCKERS})

def r6(out,c):
 paths=('simulation/hh_signal/final_closure/resource_closure/config/b_v2_research_execution_terms.json',PREFIX+'b_v2_cost_assignment.json',PREFIX+'readiness_observer_amendment.json')
 for path,h in zip(paths,(cat.TERMS,cat.VM,cat.OBSERVER)):
  need(sha((REPO/path).read_bytes())==h,'EXACT_B_PROPOSAL_HASH');v=load(REPO/path)
  need(v['user_accepted'] is False and v['execution_authorized'] is False,'NO_ACCEPTANCE_OR_AUTHORIZATION_BY_SOURCE')
 rows=cat.clause_rows()
 emit(out,'G2_B_V2_CLAUSE_REVIEW.json',{'status':'PROPOSED_NOT_ACCEPTED','terms_sha256':cat.TERMS,'VM_cost_assignment_sha256':cat.VM,
  'observer_supplement_sha256':cat.OBSERVER,'clauses':rows,'user_accepted':False,'execution_authorized':False,
  'attachment_terms_literal_length':57,'attachment_terms_literal_valid_SHA256':False,'original_terms_modified':False})
 text='# B1–B8 逐條決策\n\n全部NOT_ACCEPTED；本表提供可理解的選擇，沒有自動接受。\n\n'
 for row in rows:
  text+='## '+row['clause']+'\n\n'+'\n\n'.join(k+'：'+str(v) for k,v in row.items() if k not in ('clause','user_accepted','execution_authorized'))+'\n\n'
 emit(out,'G2_B1_TO_B8_DECISIONS_ZH_TW.md',text.rstrip('\n')+'\n')
 docs(out,'G2_PATH_A_VS_B_COMPARISON.md','G2_RECOMMENDED_ARCHITECTURE_ZH_TW.md','G2_MINIMUM_DECISION_REQUIRED.md')
 # Non-executable proposal. Missing binary identity is explicit, not bypassed.
 emit(out,'G2_EFFECTIVE_STATE_DIAGNOSTIC_PROPOSAL.json',{'status':'REQUIRES_SEPARATE_EXACT_SCOPE_REVIEW_NOT_EXECUTION_READY',
  'single_use':True,'distro_start_allowed':False,'privilege':'EXISTING_NONROOT_SESSION_ONLY',
  'missing_observables':['CURRENT_BOOT_MEMBERSHIP','SYSTEM_MANAGER_VERSION_STATE','USER_MANAGER_BUS_HEALTH','EFFECTIVE_DELEGATION_AND_ANCESTORS','TOOL_BINARY_IDENTITIES'],
  'fixed_candidate_argvs':[['/usr/bin/systemctl','--system','--no-pager','show','--property=Version','--property=SystemState'],
   ['/usr/bin/systemctl','--user','--no-pager','show','--property=Version','--property=SystemState']],
  'expected_systemctl_sha256':None,'proposal_source_sha256':sha(Path(__file__).read_bytes()),
  'input_policy':'FIXED_CURRENT_USER_BUS_SOCKET_MUST_ALREADY_EXIST_AND_BE_UID_OWNED; NO_AUTOSTART_FALLBACK',
  'output_bytes_per_child':8192,'aggregate_output_bytes':32768,'wall_seconds_per_child':5,'cleanup':'NO_RETRY_IF_GROUP_OR_PIPE_EXIT_UNKNOWN',
  'private_output_policy':'EXCLUSIVE_CREATE_UID_0700_DIRECTORY_0600_FILES_NO_LINKS',
  'side_effect_risks':['CONNECTING_MANAGER_MAY_CREATE_CONTROL_PLANE_LOGS','SUBPROCESS_RESOURCES_NONZERO'],
  'implementation_and_complete_tool_binding_ready':False,'execution_authorized':False})
 return done({'recommendation':'B_V2_PLUS_EXACT_VM_AND_OBSERVER_REVIEW','user_accepted':False,'blockers':cat.BLOCKERS})

def r7(out,c):
 rows,contract=fixture();positive=protocol.review_trace(rows,contract);cases=negative_cases();need(all(r['status']=='PASS_REJECTED' for r in cases),'G3_SEMANTIC_NEGATIVE_REGRESSION')
 emit(out,'G3_RESOURCE_TRACE_TEST_RESULTS.json',{'evidence_kind':'SYNTHETIC_ONLY','positive':positive,'negative_cases':cases,
  'actual_CPU_usec':None,'actual_RAM_peak_bytes':None,'actual_wall_ns':None,'new_kernel_tests':0})
 emit(out,'G3_REMAINING_RUNTIME_CAPABILITIES.json',{'protected_acquirer_implemented':False,'trusted_expected_contract_issuance_deployed':False,
  'actual_cgroup_creation':False,'observer_actually_deployed':False,'live_reader_migration_complete':False,
  'needs':['PROTECTED_UID_FD_AND_PEER_IDENTITY','ACTUAL_HIERARCHICAL_COUNTER_CAPTURE','INDEPENDENT_MANAGER_DEADLINE',
   'SAME_INSTANCE_PARENT_LIFETIME','FULL_JOB_MEMBERSHIP_AND_MIGRATION_CLOSURE','FIXED_SLOT_COMMIT_AND_RAW_POSTMORTEM','REAL_FAILURE_TESTS'],
  'old_runtime_changed':False,'new_source_verifier_ready':True})
 docs(out,'G3_REAL_GAP_CLOSURE.md','G3_FINAL_OBSERVER_PROTOCOL.md');return done({'source_protocol_ready':True,'blockers':['TRUSTED_NATIVE_ACQUISITION_AND_MANAGER_NOT_DEPLOYED']})

def r8(out,c):
 from .readiness_tests import fs
 from .readiness_validation import geometry
 data,profile=fs();v=geometry(data,profile)
 source_math={'device_bytes':4194304,'block_size':1024,'block_count':4096,'inode_count':128,'inode_size':256,
  'inode_table_bytes':32768,'internal_journal_blocks':1024,'internal_journal_bytes':1048576,'fixed_slots_bytes':32768,
  'default_journal_source_allows_4096_blocks':True,'JBD2_minimum_blocks':1024,'core_geometry_source_compatible':True,
  'installed_mke2fs_config_and_features_verified':False,'real_mkfs_executed':False,'live_readback':None,
  'source_fixture_geometry_status':v['status'],'source_versions':['e2fsprogs1.47.0','Linux6.6'],'actual_device_identity':None}
 emit(out,'G5_EXT4_CORE_GEOMETRY_SOURCE_REVIEW.json',source_math)
 rows=[]
 for gate,ready,missing in [('G4',False,'QUALIFIED_WHOLE_DEVICE_HOST_MAPPING_AND_ALL_WRITER_EXCLUSION'),('G5',False,'PINNED_TOOL_CONFIG_FEATURES_DEVICE_AND_FORMAT_APPROVAL'),
  ('G6',False,'REAL_FS_ALLOCATED_BACKING_INODE_JOURNAL_RESERVE_AND_DURABILITY'),('G7',False,'EFFECTIVE_MANAGER_NAMESPACE_UIDS_COUNTERS_LOGS_OBSERVER_AND_CLEANUP')]:
  rows.append({'gate':gate,'source_verifier_available':True,'OS_API_documented':True,'deployment_ready':ready,'missing':missing,'actual_measurement':None,'execution_authorized':False})
 emit(out,'G4_G7_DEPLOYMENT_FEASIBILITY_MATRIX.json',{'rows':rows,'qualified_device_available':'UNKNOWN_NO_QUALIFIED_CANDIDATE','target':None,
  'ordinary_larger_disk_is_not_exact_4MiB_device':True,'current_WSL_all_devices_infeasible_claimed':False,'G7_READY_FOR_S4':False})
 docs(out,'G4_G7_MINIMUM_OS_CAPABILITIES.md','G4_G7_NEXT_APPROVALS.md');return done({'blockers':['QUALIFIED_FIXED_DEVICE_AND_ADMIN_SCOPE','EFFECTIVE_RESOURCE_AND_EVIDENCE_DEPLOYMENT'],'G7_READY_FOR_S4':False})

def r9(out,c):
 from . import tasks
 from ..guard_correction.overlay import source,restore,ORIGINAL_SHA256
 need(sha(source().encode())==GUARD and sha(restore(source()).encode())==ORIGINAL_SHA256,'SCIENTIFIC_GUARD_REVERSAL')
 physics=load(REPO/'simulation/hh_signal/final_closure/config/physics_contract.json')
 expected={'process':'g g > h h [noborn=QCD]','PDF':'cteq6l1','alpha_s_MZ':0.13,'running_loops':1,'sqrt_s_GeV':13000,'muR_muF':'mHH/2','HEFT':False}
 need(all(physics[k]==v for k,v in expected.items()),'SCIENTIFIC_CONFIG_DRIFT')
 future=load(REPO/'metadata/phase7_final_route_a_build_contract.json');need(future['seeds']==[910001,910019,910037,910061] and future['guard_sha256']==GUARD,'FIXED_SEEDS_GUARD')
 builder=(REPO/'simulation/hh_signal/final_closure/integration_runtime/build.py').read_text()
 reader=(REPO/'simulation/hh_signal/final_closure/integration_runtime/route_a.py').read_text()
 need('from ..guard_correction.overlay import source as corrected_guard_source' in builder and 'corrected_guard.write_text(corrected_guard_source())' in builder and 'FULL_SOURCE_OR_GUARD_BINDING_DRIFT' in reader,'ACTUAL_ACTIVE_BUILDER_READER_SOURCE')
 root=tasks.root_review(out,c)['evidence'];need(root['source_sha256'],'ROOT_SOURCE_BINDING')
 files=['simulation/hh_signal/final_closure/config/physics_contract.json','simulation/hh_signal/final_closure/guard_correction/native_checks_corrected.f',
  'metadata/phase7_final_route_a_build_contract.json','reports/phase7e_source_identity_audit.md','reports/phase7e_integration_and_candidate_audit.md',
  'reports/phase7i_route_a_activation.md','simulation/hh_signal/final_closure/evidence/root_object_readback.json',
  'simulation/hh_signal/final_closure/integration_runtime/build.py','simulation/hh_signal/final_closure/integration_runtime/route_a.py']
 v={'status':'PASS_FROZEN_SOURCE_PREFLIGHT_ONLY','physics_contract_sha256':PHYSICS,'corrected_guard_sha256':GUARD,'physics':physics,
  'seeds':future['seeds'],'retained_physical_LHE_events':0,'existing_source_identities':[{'path':n,'sha256':sha((REPO/n).read_bytes())} for n in files],
  'new_scientific_card_or_guard_problem_identified':False,'new_ME_calls':0,'new_integrals':0,'new_events':0,'corrected_integral_pb':None,
  'actual_installed_binary_or_dependencies_revalidated':False,'historical_STOP92_predicate':'UNKNOWN_PRESERVED',
  'historical_B_C_separate':True,'C1000_is_original_CTEQ_target':False,'BR_applied_once_required':True,'new_ROOT_readback':False}
 emit(out,'PHASE7I_FROZEN_PHYSICS_IDENTITY.json',v)
 emit(out,'PHASE7I_SCIENTIFIC_RESTART_PREFLIGHT.md','''# Scientific restart preflight\n\n沒有發現新的frozen physics-card或corrected-guard source問題。目標仍gg→HH full finite mt/mb、LO loop-induced no-Born、CTEQ6L1、alpha_s(MZ)=0.130一圈、13TeV、kl=kt=1、muR=muF=mHH/2；四seeds與獨立grid/integration-only設定保留。沒有新截面或積分結論。\n\n既有source activation已接入Route-A builder與strict reader；不能引用較早guard-correction metadata的NOT_MIGRATED就宣稱現在仍未接入。反之source接入不等於實際corrected binary、loader、完整receipt與zero-ME preflight已驗收。舊STOP92真實失敗predicate仍UNKNOWN，不能靠source推測歷史scalar。\n\nB100與C1000原卡／source events／weights分開；C實際為NNPDF23 LO/two-loop，不能重標為本CTEQ6L1/one-loop目標。保留既有sumW、BR一次、sampling covariance與ESS限制；不以舊D reweight推得新目標物理率。ROOT6.40.04/C++20既有7000-entry收據與frozen selection source僅重新核文件/hash；本輪未啟動ROOT或開新event檔，也未重驗安裝中的generator/native依賴。\n\nsignal/background normalization仍依原有source weights與sample適用範圍，無新luminosity、K-factor、photon-fake或ATLAS systematic宣稱。真實physics仍依賴OS封裝、exact build、native PDF/alpha/seed/scale、ME/grid/error/tail/writer/zero-retention gates。\n''')
 emit(out,'PHASE7I_FIRST_APPROVED_RUN_DEPENDENCIES.md','''# First approved run dependencies\n\n先完成架構決策與實際job resource/evidence/capacity/cleanup驗收；再對exact executable source作獨立BUILD_ONLY審核與人類終端確認。build後核對所有binary/immutable sources/toolchain/dynamic dependencies與完整receipt身份；取得新的binary review，再審zero-ME/native configuration與Stage A seed910001的獨立physical scope。Stage A失敗即停，不換seed或重置aggregate4h CPU/wall與5GiB。其餘三approved-seed候選不自動執行；現階段所有execution authorization均false。\n\n保留既有source-only四輪adaptation／三輪measurement／initial250等提案及4固定seeds，不將此表視為新積分授權。獨立grids、真ME/PDF/alpha_s/seed provenance、error/replica dispersion/tail diagnostics與zero retained LHE須由未來真實run驗證。\n''')
 return done({'scientific_preflight':'PASS_FROZEN_SOURCE_ONLY_NO_NEW_SOURCE_PROBLEM_IDENTIFIED','blockers':['OS_ACCEPTANCE','EXACT_BUILD_BINARY_NATIVE_AND_PHYSICAL_APPROVAL']})

def r10(out,c):
 from .g2_independent import review
 rows,contract=fixture();v=review(rows,contract)
 files=[PREFIX+n for n in ('g2_protocol.py','g2_runner.py','g2_worker.py','g2_stages.py','g2_catalogue.py','g2_independent.py')]
 tree=ast.parse((REPO/(PREFIX+'g2_protocol.py')).read_text())
 need(not any(isinstance(n,ast.Import) and any(a.name in ('os','subprocess','socket','ctypes','signal') for a in n.names) for n in ast.walk(tree)),'PURE_PROTOCOL_IMPORT')
 emit(out,'G2_INDEPENDENT_SOURCE_REVIEW.json',{'status':'PASS_INDEPENDENT_PROCESS_AND_ALGORITHM_SUBSET','separate_human_reviewer':False,
  'method':'SAME_AGENT_SEPARATE_STAGE_PROCESS_AND_INDEPENDENT_INTEGER_OBSERVER_ORACLE_PLUS_AST','independent':v,
  'source_hashes':[{'path':n,'sha256':sha((REPO/n).read_bytes())} for n in files],
  'negative_case_scope':'SYNTHETIC_ONLY; NAMED_SUBCASES_OVERLAP_UNIT_SUITE','actual_kernel_acceptance':False})
 return done({'independent_oracle_subset_passed':True,'blockers':['LIVE_TRUSTED_CAPTURE_AND_DEPLOYMENT_NOT_EXECUTED']})

def r11(out,c):
 emit(out,'G2_RELEASE_CHECKPOINT.json',{'status':'SAFE_ENGINEERING_STAGE_COMPLETE','source_revision':c['revision'],'source_sha256':c['source_sha256'],
  'source_rows':c['source_rows'],'external_sha256':{n:c['external'][n]['sha256'] for n in ('host','guest')},
  'stage_count':12,'source_CI_status':'PENDING_POST_PUBLICATION','publication_audit':'REQUIRED_BEFORE_EVERY_PUSH',
  'run_rebinding_allowed':False,'previous_run_preserved':True,'new_kernel_dispatches':0,'actual_CPU_RAM_wall_disk':None,
  'S4_EXECUTED':False,'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'FORMAL_BUILD_ONLY_AUTHORIZED':False,'PHYSICAL_RESTART_AUTHORIZED':False})
 return done({'blockers':cat.BLOCKERS,'all_safe_review_stages_complete':True,'new_live_dispatches':0})

TASKS=dict(zip(STAGES,
 (r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11)))

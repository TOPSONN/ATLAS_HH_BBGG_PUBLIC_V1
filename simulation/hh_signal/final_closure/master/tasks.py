"""Closed list of nonphysical methods. No build/import-model/live executor."""
import csv,hashlib,math,os,shutil
from decimal import Decimal,localcontext
from pathlib import Path
from .contract import BASE,GUARD,HERE,LIMITS,PHYSICS,REPO,canonical,load,need,sha
from .ledger import create_json

def result(status,value):return {'status':status,'evidence':value,'live_execution':False}
def write(out,name,value):create_json(out/name,value)
def g0(out,context):
 from ..src.contracts import input_identity
 from ..guard_correction.overlay import source
 inputs=input_identity();physics=REPO/'simulation/hh_signal/final_closure/config/physics_contract.json'
 need(sha(physics.read_bytes())==PHYSICS and sha(source().encode())==GUARD,'SCIENTIFIC_IDENTITY_DRIFT')
 old=load(REPO/'reports/phase7i_g1_g2_feasibility/source_manifest.json')
 changed=[]
 for row in old['files']:
  if sha((REPO/row['path']).read_bytes())!=row['sha256']:changed.append(row['path'])
 need(set(changed)<=({'.github/workflows/'+n+'.yml' for n in ('hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure','hh_signal_resource_closure')}|{'simulation/hh_signal/final_closure/src/contracts.py'}),'PR38_SOURCE_CHANGED_OUTSIDE_EXPLICIT_DELTA')
 v={'exact_source_revision':context['revision'],'base':BASE,'frozen_inputs':len(inputs),
  'unchanged_scientific_and_data_inputs':sum('compatibility_scope' not in r for r in inputs),
  'CI_only_compatibility':[r for r in inputs if 'compatibility_scope' in r],
  'physics_contract_sha256':PHYSICS,'corrected_scientific_guard_sha256':GUARD,
  'source_manifest_sha256':context['source_sha256'],'nominal_limits':LIMITS,
  'historical_data_overwritten':False,'new_ME_calls':None,'new_integrals':None,'new_events':None}
 write(out,'BASELINE_IDENTITY.json',v);return result('PASS_SOURCE_ONLY',v)
def g1(out,context):
 host=context.get('host_capture')
 if host is None:
  projection={'running_distro_state':'UNKNOWN','coverage':[],'host_identity_confidence':'UNKNOWN'}
 else:
  from ..resource_closure.g1_acquisition import load as parse,public_projection
  raw=Path(host['path']).read_bytes();need(sha(raw)==host['sha256'],'HOST_INPUT_DRIFT')
  v=parse(raw);expected=sha((REPO/'simulation/hh_signal/final_closure/resource_closure/g1_windows_inventory.ps1').read_bytes())
  need(v['collector_sha256']==expected,'HOST_COLLECTOR_SOURCE_DRIFT')
  projection=public_projection(v);projection['raw_capture_sha256']=sha(raw)
  projection['acquisition_trust']='UNATTESTED_JSON; ACTUAL_LOCAL_OBSERVATION_REQUIRES_SEPARATE_COMMAND_RECEIPT'
 unknown={'status':'UNKNOWN','actual_guest_dispatch':False,'kernel':None,'boot':None,'namespace':None,'user_manager':None}
 outputs={'G1_HOST_INVENTORY.json':projection,'G1_GUEST_INVENTORY.json':unknown,
  'G1_CGROUP_CAPABILITIES.json':{'status':'UNKNOWN','effective_limits':None,'delegation':None,'kernel_tests':None},
  'G1_STORAGE_TOPOLOGY.json':{'status':'UNKNOWN','complete_host_guest_mapping':False,'safe_candidate':None,'capacity_enforced':None},
  'G1_LOGGING_BOUNDARIES.json':{'status':'UNKNOWN','manager_health':None,'journald_paths':None,'rsyslog_paths':None},
  'G1_EVIDENCE_COMPLETENESS.json':{'status':'BLOCKED_OS_CAPABILITY','host_capture_available':host is not None,
   'reported_unattested':sum(r['status']=='REPORTED_UNATTESTED' for r in projection['coverage']),
   'unknown':sum(r['status']=='UNKNOWN' for r in projection['coverage']),
   'host_attested':False,'guest_complete':False,'running_state':projection['running_distro_state'],
   'next_action':'SAME_USER_NON_ELEVATED_READ_ONLY_ADAPTER_IN_ACCESSIBLE_HOST_CONTEXT; NO_WSL_START'}}
 for n,v in outputs.items():write(out,n,v)
 return result('BLOCKED_OS_CAPABILITY',outputs['G1_EVIDENCE_COMPLETENESS.json'])
def g2(out,context):
 proposal=load(HERE/'b_v2_cost_assignment.json')
 need(proposal['status']=='PROPOSED_NOT_ACCEPTED' and proposal['user_accepted'] is False,'AMENDMENT_NOT_ACCEPTED_BY_CODE')
 a={'verdict':'A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST','original_limits':LIMITS,
  'missing_capabilities':['JOINT_HOST_GUEST_HARD_AGGREGATE','ATTESTED_DEVICE_BACKING','REAL_CAPACITY_AND_COLLECTOR_ISOLATION','KERNEL_CLEANUP_EVIDENCE'],
  'zero_overshoot_guarantee':'NOT_PROVEN_BY_STANDARD_CGROUP_OR_NON_REALTIME_TIMERS','live_execution_authorized':False}
 write(out,'ARCHITECTURE_A_FEASIBILITY.json',a);write(out,'ARCHITECTURE_B_V2_REVIEW.json',proposal)
 (out/'RESOURCE_BOUNDARY_COMPARISON.md').write_text('# Resource boundary\n\nA includes every host/guest role. Proposed B excludes exactly manager_journal, launcher and host_backing; VM residual cost assignment requires explicit human acceptance. Worker/controller/collector remain one job pool. Nominal caps unchanged; enforcement semantics are weaker and disclosed.\n',encoding='utf-8')
 (out/'RECOMMENDED_DEPLOYMENT_PATH.md').write_text('# Deployment path\n\nFirst resolve non-elevated inventory access. Then review every B clause plus exact VM-cost assignment, or choose a different controlled A platform. Provision a verified P1-safe independent whole-device and collector/control identities only under separate exact-target approval. Kernel tests, S4, build, binary review, restart and event generation each remain separately gated.\n',encoding='utf-8')
 return result('BLOCKED_AUTHORIZATION',{'A':a['verdict'],'B':'PROPOSED_NOT_ACCEPTED','external_roles':proposal['external_roles']})
def g3(out,context):
 from .same_instance import InertFDLease,privileged_operation
 p=out/'inert_input.txt';p.write_bytes(b'INERT SAME INSTANCE SOURCE TEST\n');h=sha(p.read_bytes())
 with InertFDLease(p,h,offline_fixture_only=True) as lease:
  need(lease.consume()==p.read_bytes(),'INERT_CONSUMER')
  try:lease.consume()
  except ValueError:replay=True
  else:raise ValueError('REPLAY_ACCEPTED')
 try:privileged_operation('format')
 except PermissionError:denied=True
 else:raise ValueError('PRIVILEGED_ADAPTER_PRESENT')
 names=('device_policy.py','instance_binding.py','evidence_slots.py')
 rows=[{'path':'simulation/hh_signal/final_closure/resource_closure/'+n,'sha256':sha((REPO/'simulation/hh_signal/final_closure/resource_closure'/n).read_bytes())} for n in names]
 old=load(REPO/'reports/phase7i_g1_g2_feasibility/source_manifest.json')['files'];expected={r['path']:r['sha256'] for r in old}
 need(all(expected[r['path']]==r['sha256'] for r in rows),'OLD_POLICY_REDESIGNED')
 v={'same_FD_inert_reader_executed':True,'replay_rejected':replay,'privileged_consumer_denied':denied,
  'old_policy_hashes':rows,'actual_device_open':False,'format_or_mount':False,'runtime_helper_deployed':False,
  'host_exclusivity':'UNKNOWN','TOCTOU_RUNTIME_CLOSED':False,'evidence_slots':'EXISTING_8X4096_UNCHANGED; PRODUCTION_NOT_DEPLOYED'}
 write(out,'HELPER_SOURCE_REVIEW.json',v);return result('PASS_SOURCE_ONLY',v)
def audit_inputs(out,context):
 from ..src.controller import audit,validate_evidence
 v={'audit':audit(),'validate':validate_evidence()}
 write(out,'EXISTING_INPUT_REPRODUCIBILITY.json',v);return result('PASS_SOURCE_ONLY',v)
def numerical(out,context):
 from ..src.existing_analysis import derive
 v=derive(out)
 return result('PASS_SOURCE_ONLY',{'status':v['status'],'independent_source_events':v['original_events'],'historical_ME_rows':v['ME_rows'],
  'benchmarks':v['benchmarks'],'corrected_target':None,'combined_physical_background':None,'significance':None})
def independent(out,context):
 """Decimal implementation independently recomputes sums, ESS and covariance."""
 source=REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7d_klambda/event_reweights.csv'
 report=Path(context['run_directory'])/'stages/EXISTING_NUMERICAL_REPORT'
 with source.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
 with (report/'kappa_benchmarks.csv').open(encoding='utf-8',newline='') as f:prior=list(csv.DictReader(f))
 columns={Decimal(str(k)):{} for k in (-1,0,1,2,2.5,5)}
 for r in rows:
  k=Decimal(r['kappa_lambda']);i=int(r['source_event_index']);w=Decimal(r['source_contribution_pb'])
  need(w.is_finite() and i not in columns[k],'DUPLICATE_OR_NONFINITE_SOURCE');columns[k][i]=w
 need(all(set(v)==set(range(1,1001)) for v in columns.values()),'SHARED_1000_EVENT_COHORT')
 summaries=[];matrix={}
 with localcontext() as c:
  c.prec=50
  for k,values in columns.items():
   w=list(values.values());s=sum(w);q=sum(x*x for x in w);a=sum(abs(x) for x in w);ess=s*s/q
   ref=next(r for r in prior if Decimal(r['kappa_lambda'])==k)
   need(math.isclose(float(ess),float(ref['input_ESS']),rel_tol=1e-11),'INDEPENDENT_ESS_MISMATCH')
   need(math.isclose(float(s),float(ref['sum_w']),rel_tol=1e-11),'INDEPENDENT_SUMW_MISMATCH')
   summaries.append({'kappa_lambda':str(k),'source_events':1000,'sumW':str(s),'sumW2':str(q),'sum_abs_W':str(a),
    'ESS':str(ess),'maximum_absolute_weight_fraction':str(max(abs(x) for x in w)/a),
    'negative_weights':sum(x<0 for x in w),'support':'INCONCLUSIVE_REWEIGHTING' if k in (Decimal('2.5'),Decimal(5)) else 'PER_BIN_SUPPORT_REQUIRED',
    'corrected_absolute_rate_pb':None})
  for k,a in columns.items():
   for l,b in columns.items():
    ma=sum(a.values())/1000;mb=sum(b.values())/1000
    matrix[k,l]=Decimal(1000)/999*sum((a[i]-ma)*(b[i]-mb) for i in range(1,1001))
 with (report/'cross_kappa_input_covariance.csv').open(encoding='utf-8',newline='') as f:cov=list(csv.DictReader(f))
 need(len(cov)==36,'COVARIANCE_SIZE')
 for r in cov:need(math.isclose(float(matrix[Decimal(r['kappa_a']),Decimal(r['kappa_b'])]),float(r['input_sampling_covariance_pb2']),rel_tol=1e-10,abs_tol=1e-30),'INDEPENDENT_COVARIANCE_MISMATCH')
 v={'method':'DECIMAL50_SEPARATE_IMPLEMENTATION','summaries':summaries,'covariance_entries_verified':36,
  'independent_source_events':1000,'weight_rows':6000,'rows_are_independent_events':False,'absolute_rate_validated':False,
  'corrected_integrals':None,'shared_event_covariance_preserved':True}
 write(out,'INDEPENDENT_KAPPA_CHECK.json',v);return result('PASS_SOURCE_ONLY',v)
def scientific(out,context):
 from ..guard_correction.overlay import source,restore,ORIGINAL_SHA256
 from ..guard_correction.methods import independent_arithmetic
 text=source();need(sha(text.encode())==GUARD and sha(restore(text).encode())==ORIGINAL_SHA256,'GUARD_REVERSAL')
 physics=load(REPO/'simulation/hh_signal/final_closure/config/physics_contract.json')
 need(physics['PDF']=='cteq6l1' and physics['running_loops']==1 and physics['muR_muF']=='mHH/2','FROZEN_PHYSICS')
 v={'guard_sha256':GUARD,'physics':physics,'guard_reversible_source':True,'native_scale_owner':'native scale/q; MODEL MU_R remains model reference91.188',
  'guard_scalar_arithmetic':independent_arithmetic(),
  'installed_model_or_toolchain_readback':'UNKNOWN_NO_GUEST_ACCESS','native_guard_or_ME_executed':False,
  'historical_C1000':'NNPDF23_LO_TWO_LOOP_UNCHANGED_NOT_RENAMED_CTEQ','corrected_target_integral_pb':None,
  'four_replica_plan':{'seeds':[910001,910019,910037,910061],'independent_grids':4,'adaptation_rounds':4,'measurement_rounds':3,'initial_target':250,'accuracy':0,'actual_results':None}}
 write(out,'SCIENTIFIC_METHOD_PREFLIGHT.json',v);return result('PASS_SOURCE_ONLY',v)
def root_review(out,context):
 header=REPO/'simulation/delphes/include/Physics.hxx';analysis=REPO/'simulation/delphes/src/analyze_delphes.cxx'
 h=header.read_text();a=analysis.read_text()
 need('pt>25&&a<2.37&&!(a>1.37&&a<1.52)' in h and 'pt>25&&std::abs(eta)<2.5' in h,'FIDUCIAL_SOURCE_CHANGED')
 need('selected_photons[0].native_pt>35' in a and 'j.btag&1' in a,'SELECTION_SOURCE_CHANGED')
 old=load(REPO/'simulation/hh_signal/final_closure/evidence/root_object_readback.json')
 need(old['status']=='PASS_READ_ONLY_EXISTING_7000_ROOT_ENTRIES','HISTORICAL_ROOT_RECEIPT')
 v={'ROOT_required':'6.40.04','language':'C++20','source_sha256':[{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p.read_bytes())} for p in (header,analysis)],
  'selection':{'leading_photon_pt_gt_GeV':35,'subleading_photon_pt_gt_GeV':25,'photon_abs_eta_lt':2.37,'exclude_open_crack':[1.37,1.52],
   'jet_pt_gt_GeV':25,'jet_abs_eta_lt':2.5,'bit0_tags_ge':2,'mgg_inclusive_GeV':[105,160]},
  'existing_ROOT_readback':'HISTORICAL_RECEIPT_ONLY_NOT_RERUN','actual_ROOT_execution_this_run':False,'current_ROOT_runtime':'UNKNOWN',
  'new_ROOT_events':None,'plots':'NOT_GENERATED; ROOT_ONLY_WHEN_RUNTIME_AVAILABLE; LOCAL_APPROVAL_BEFORE_PUSH'}
 write(out,'ROOT_SELECTION_SCHEMA_REVIEW.json',v);return result('PASS_SOURCE_ONLY',v)
def packages(out,context):
 scope=load(REPO/'reports/phase7i_autonomous_controller_recovery/proposed_kernel_scope.json')
 need(len(scope['argv'])==104,'HISTORICAL_S4_ARGV_CHANGED')
 for stage in ('S4','FULL_RESOURCE','BUILD_ONLY','BINARY_REVIEW','STAGE_A','FOUR_REPLICAS','SM1000','ROOT_PLOTS'):
  v={'schema':'HH_MASTER_REVIEW_REQUEST_NOT_AUTHORIZATION_V1','stage':stage,'exact_source_revision':context['revision'],
   'source_sha256':context['source_sha256'],'human_approved':False,'execution_authorized':False,
   'review_ready_for_execution':False,'physics_contract_sha256':PHYSICS,'guard_sha256':GUARD,
   'actual_binary_identity':None,'actual_device_identity':None,'actual_execution_workspace':None,
   'blockers':['G1_IDENTITY','ARCHITECTURE_NOT_ACCEPTED','FIXED_STORAGE','EFFECTIVE_CONTROLS','SEPARATE_EXACT_SCOPE_HUMAN_AUTHORIZATION'],
   'nominal_limits':LIMITS,'automatic_retry':False}
  if stage=='S4':v.update(historical_argv_tokens=104,historical_argv_sha256=scope['argv_sha256'],
   old_argv_is_current_authorization=False,current_executable_argv=None,reason='No verified Linux checkout/device/unit identities; do not invent executable paths or reuse old104-token approval.')
  if stage=='BUILD_ONLY':v.update(proposed_builds=4,proposed_zero_ME_preflights=8,proposed_denied_entry_tests=4,actual_results=None)
  if stage in ('STAGE_A','FOUR_REPLICAS'):v.update(seeds=[910001] if stage=='STAGE_A' else [910001,910019,910037,910061],retained_events=0,aggregate_budget_reset_per_replica=False,actual_results=None)
  if stage=='SM1000':v.update(seed=20261123,events=1000,max_workers=2,wall_seconds=43200,disk_bytes=20*1024**3,actual_counts={'LHE':None,'HepMC3':None,'ROOT':None})
  write(out,stage+'_REVIEW_REQUEST.json',v)
 return result('PASS_SOURCE_ONLY',{'review_requests':8,'executable_approval_packages_ready':False,'authorization_created':False})
def report(out,context):
 v={'scope':'PUBLIC_OPEN_DATA_INDEPENDENT_STUDY','ENGINEERING_VALIDATED':'SOURCE_ONLY_WITH_LIMITS',
  'NUMERICALLY_VALIDATED':'EXISTING_DATA_ONLY_PENDING_INDEPENDENT_STAGE_RECEIPT','PHYSICALLY_VALIDATED':False,'COLLABORATION_APPROVED':False,
  'corrected_cross_section_pb':None,'corrected_SM1000':None,'new_ME_calls':None,'new_integrals':None,
  'systematics_complete':False,'luminosity':None,'discovery_significance':None,
  'report_sections':['model_and_guard','PDF_alpha_scales','STOP92_history','integration_UNEXECUTED','corrected_signal_UNEXECUTED',
   'ROOT_schema_source','frozen_selection','shared_event_covariance','low_ESS','background_caveats','resource_boundaries','reproducibility','remaining_external_gates']}
 write(out,'PHASE7L_SCIENTIFIC_REPORT_STATE.json',v);return result('PASS_SOURCE_ONLY',v)

TASKS={'G0_SOURCE_BASELINE':g0,'G1_REAL_INVENTORY':g1,'G2_ARCHITECTURE_DECISION':g2,'G3_DEVICE_AND_HELPER_REVIEW':g3,
 'EXISTING_INPUT_AUDIT':audit_inputs,'EXISTING_NUMERICAL_REPORT':numerical,'INDEPENDENT_NUMERICAL_CHECK':independent,
 'SCIENTIFIC_METHOD_PREFLIGHT':scientific,'ROOT_SELECTION_SCHEMA_REVIEW':root_review,'FUTURE_REVIEW_PACKAGES':packages,'PHASE7L_SAFE_REPORT':report}

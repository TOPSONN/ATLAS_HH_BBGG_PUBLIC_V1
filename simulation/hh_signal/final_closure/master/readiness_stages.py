"""Fixed read-existing-input and pure-verifier G1-G7 task implementations."""
import json
from pathlib import Path
from .contract import REPO,LIMITS,PHYSICS,GUARD,load,sha,need,canonical
from .ledger import create_json
from . import readiness_validation as v

def emit(out,name,value):create_json(out/name,value)
def result(evidence):return {'status':'PASS_SOURCE_ONLY','evidence':evidence,'live_execution':False}
def external(c,name):
 r=c['external'][name]
 if r is None:return None
 raw=Path(r['path']).read_bytes();need(sha(raw)==r['sha256'],'EXTERNAL_INPUT_DRIFT');return load(r['path'])
def identities(out,c):
 from ..guard_correction.overlay import source
 need(sha((REPO/'simulation/hh_signal/final_closure/config/physics_contract.json').read_bytes())==PHYSICS and sha(source().encode())==GUARD,'SCIENTIFIC_GUARD_DRIFT')
 e={'source_revision':c['revision'],'frozen_input_count':len(c['frozen_inputs']),'physics_sha256':PHYSICS,'guard_sha256':GUARD,
  'actual_acceptance':None,'blockers':[],'scope':'SAFE_ENGINEERING_ONLY'}
 emit(out,'BASELINE_IDENTITY.json',e);return result(e)
def host(out,c):
 from ..resource_closure import g1_acquisition as g
 raw=external(c,'host');g.validate_host(raw)
 need(raw['collector_sha256']==sha((REPO/'simulation/hh_signal/final_closure/resource_closure/g1_windows_inventory.ps1').read_bytes()),'HOST_COLLECTOR_SOURCE')
 p=g.public_projection(raw);p.pop('host_capture_schema',None)
 need(len(p['coverage'])==13 and all(x['status']=='REPORTED_UNATTESTED' for x in p['coverage']),'HOST_13_QUERY_COVERAGE')
 p.update(raw_capture_sha256=c['external']['host']['sha256'],status='PASS_REPORTED_UNATTESTED',actual_acceptance='HOST_QUERY_COVERAGE_ONLY',blockers=['HOST_ATTESTATION_NOT_ESTABLISHED'])
 emit(out,'G1_HOST_ACCEPTANCE.json',p);return {'status':'PASS_READ_ONLY_OBSERVED','evidence':p,'live_execution':False}
def guest(out,c):
 current=external(c,'running');g=external(c,'guest')
 state='UNKNOWN_NO_CURRENT_OBSERVATION' if current is None else current.get('state','UNKNOWN')
 e={'status':'BLOCKED_AUTHORIZATION','last_host_running_state':'NONE_RUNNING_REPORTED_UNATTESTED',
  'current_running_query_state':state,'current_running_query_sha256':None if current is None else c['external']['running']['sha256'],
  'already_open_shell_available':False,'guest_collection_executed':False,'actual_acceptance':None,
  'blockers':['CURRENT_GUEST_SESSION_UNVERIFIED','SEPARATE_STARTUP_OR_EXISTING_SESSION_SCOPE_REQUIRED']}
 if g is not None:
  e.update(v.guest_review(g,sha((REPO/'simulation/hh_signal/final_closure/master/guest_v2.py').read_bytes()),
   sha((REPO/'simulation/hh_signal/final_closure/resource_closure/g1_guest_inventory.py').read_bytes())))
  e['guest_collection_executed']=False;e['existing_raw_guest_capture_reviewed']=True
  e['blockers']=['UNATTESTED_INPUT_NOT_LIVE_SESSION_PROOF'];e['actual_acceptance']=None
 emit(out,'G1_GUEST_OBSERVATION.json',e)
 for name in ('G1_BOOT_NAMESPACE_BINDING.json','G1_CGROUP_EFFECTIVE_STATE.json','G1_STORAGE_GRAPH.json','G1_MANAGER_LOG_STATE.json'):
  emit(out,name,{'status':'UNKNOWN','actual_measurement':None,'guest_capture_available':g is not None,'blockers':e['blockers'],
   'source_verifier_available':True,'actual_acceptance':None})
 emit(out,'G1_COMPLETE_COVERAGE.json',{'host_queries':13,'guest_complete':False,'kernel_acceptance':None,'host_attested':False})
 return result(e)

def resource_ledger():
 roles={'worker':'job_parent','controller':'job_parent','collector':'job_parent','scientific_helpers':'job_parent',
  'manager':'manager_journal','journald':'manager_journal','rsyslog':'manager_journal','launcher':'launcher',
  'hypervisor':'host_backing','VM_runtime_residual':'host_backing','host_backing':'host_backing',
  'filesystem_metadata':'job_parent_fixed_device','journal':'job_parent_fixed_device','failure_reserve':'job_parent_fixed_device',
  'postmortem_cleanup':'job_parent','final_after_collector_exit_observer':'manager_journal'}
 return {'status':'PROPOSED_NOT_ACCEPTED','original_A_all_roles_one_pool':True,'B_V2_weaker_than_original':True,
  'user_accepted':False,'nominal_limits':LIMITS,'per_role_duplicate_budget_forbidden':True,
  'roles':[{'role':name,'A_owner':'original_shared_aggregate','B_V2_proposed_owner':owner,
   'CPU_actual':None,'RAM_actual':None,'disk_actual':None,'deployed':False} for name,owner in roles.items()],
  'external_roles':['manager_journal','launcher','host_backing'],'VM_cost_assignment_sha256':sha((REPO/'simulation/hh_signal/final_closure/master/b_v2_cost_assignment.json').read_bytes())}
def architecture(out,c):
 terms=load(REPO/'simulation/hh_signal/final_closure/resource_closure/config/b_v2_research_execution_terms.json')
 cost=load(REPO/'simulation/hh_signal/final_closure/master/b_v2_cost_assignment.json')
 observer=load(REPO/'simulation/hh_signal/final_closure/master/readiness_observer_amendment.json')
 need(terms['user_accepted'] is False and cost['user_accepted'] is False,'NO_ACCEPTANCE_BY_CODE')
 need(observer['user_accepted'] is False and observer['execution_authorized'] is False,'NO_OBSERVER_ACCEPTANCE_BY_CODE')
 capabilities=['JOINT_HOST_GUEST_CUMULATIVE_CPU','INDEPENDENT_ADMISSION_TO_CLEANUP_WALL','AGGREGATE_RAM_SWAP',
  'ALL_ALLOCATED_BLOCKS_INODES_METADATA','FIXED_HOST_BACKING','BOUNDED_MANAGER_LOGS',
  'COLLECTOR_DEATH_SURVIVAL','ORPHAN_CGROUP_CLEANUP','ZERO_TRANSIENT_OVERSHOOT']
 matrix={'verdict':'A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST','capabilities':[
  {'requirement':n,'actual_state':'UNKNOWN_NOT_DEPLOYED','raw_kernel_evidence':None} for n in capabilities],
  'technical_impossibility_claimed':False,'standard_semantics_gap':'CPU_RATE_IS_NOT_LIFETIME_QUOTA; MEMORY_AND_NONREALTIME_STOP_CAN_OVERSHOOT'}
 emit(out,'ARCHITECTURE_A_ACTUAL_CAPABILITY_MATRIX.json',matrix);emit(out,'HOST_GUEST_RESOURCE_LEDGER.json',resource_ledger())
 emit(out,'B_V2_CLAUSE_REVIEW.json',{'status':'G2_ENGINEERING_DECISION_PACKAGE_READY','terms_sha256':sha(canonical(terms)),
  'terms_raw_sha256':sha((REPO/'simulation/hh_signal/final_closure/resource_closure/config/b_v2_research_execution_terms.json').read_bytes()),
  'cost_assignment_raw_sha256':sha((REPO/'simulation/hh_signal/final_closure/master/b_v2_cost_assignment.json').read_bytes()),
  'post_exit_observer_supplement_raw_sha256':sha((REPO/'simulation/hh_signal/final_closure/master/readiness_observer_amendment.json').read_bytes()),
  'clauses':[{'clause':x['id'],'decision':'NOT_ACCEPTED','status':'REVIEWED_PROPOSAL'} for x in terms['clauses']],
  'recommendation':'REVIEW_B_V2_PLUS_EXACT_VM_COST_ASSIGNMENT_FIRST; NO_DEPLOYMENT_YET','user_accepted':False})
 return result({'actual_acceptance':None,'blockers':['B1_B8_AND_VM_COST_ASSIGNMENT_NOT_ACCEPTED','NO_VERIFIED_A_HARD_ENFORCER']})

def guards(out,c):
 from .tasks import g3 as existing_inert_fd_check
 prior=existing_inert_fd_check(out,c)
 need(prior['status']=='PASS_SOURCE_ONLY','EXISTING_INERT_FD_REGRESSION')
 from .readiness_tests import pure_cases
 results=pure_cases();need(all(x['passed'] for x in results),'PURE_NEGATIVE_REGRESSION')
 graph=v.device_adapter(external(c,'host'),external(c,'guest'))
 emit(out,'G3_DEVICE_ADAPTER_STATUS.json',graph)
 emit(out,'G3_NEGATIVE_TEST_RESULTS.json',{'scope':'ACTUAL_PURE_FIXTURE_CALLS_NOT_KERNEL','cases':results,'tests':len(results),'failures':0})
 emit(out,'G3_UNDEPLOYED_CAPABILITIES.json',{'privileged_helper':False,'host_writer_lease':False,'same_fd_ext4_consumer':False,
  'collector_identity':None,'mount_api_support':None,'TOCTOU_RUNTIME_CLOSED':False})
 emit(out,'G3_COLLECTOR_SECURITY_MATRIX.json',{'collector_UID':None,'worker_UID':None,'controller_UID':None,
  'socket_authentication':'REQUIRE_SO_PEERCRED_PLUS_PID_START_BOOT_INVOCATION_BINDING; NOT_DEPLOYED',
  'worker_evidence_FD_allowed':False,'slots':{'count':8,'each_bytes':4096,'failure_slots':2},
  'death_domains':'COLLECTOR_SEPARATE_CHILD_CGROUP_WITHIN_SAME_PARENT_BUDGET','runtime_verified':False})
 return result({'actual_acceptance':None,'source_tests_executed':len(results),'blockers':['NO_PROVEN_HOST_EXCLUSIVITY','NO_PRIVILEGED_CONSUMER_DEPLOYED']})

def capacity():
 return {'S4':{'ceiling_bytes':16*1024**2,'work_bytes':8*1024**2,'private_bytes':1024**2,'fixed_device_bytes':4*1024**2,'unclosed_remainder_bytes':3*1024**2},
  'BUILD':{'ceiling_bytes':5*1024**3,'work_bytes':2*1024**3,'private_bytes':256*1024**2,'fixed_device_bytes':2*1024**3,'unclosed_remainder_bytes':768*1024**2},
  'failure_slots_inside_fixed_device_bytes':32768,'internal_journal_already_inside_device':True,
  'remainder_hard_enforced':False,'host_control_plane_costs':'UNMEASURED_NOT_FREE',
  'BUILD_tmpfs_sum_can_be_filled_under_2GiB_RAM':False,'allocated_blocks_verified':None}
def provisioning(out,c):
 emit(out,'G4_CAPACITY_BUDGET.json',capacity())
 return result({'actual_acceptance':None,'device_identity':None,'backend_selection':'DEDICATED_FIXED_CAPACITY_INDEPENDENT_WHOLE_DEVICE_PENDING_ADMIN_IDENTITY',
  'provisioning_authorized':False,'actually_executed':False,'blockers':['NO_REVIEWED_DISPOSABLE_DEVICE','NO_ADMIN_APPROVAL','NO_HOST_EXCLUSIVITY']})
def formatting(out,c):
 profile={'device_bytes':4194304,'block_size':1024,'block_count':4096,'inode_count':128,'inode_size':256,'journal_blocks':1024,
  'source_instance_sha256':None,'status':'PROPOSED_UNEXECUTED_NOT_KNOWN_MKE2FS_COMPATIBLE'}
 emit(out,'G5_FORMAT_GEOMETRY_PLAN.json',profile)
 emit(out,'G5_DEVICE_INSTANCE_CONTRACT.json',{'phases':['acquire','before_operation','after_operation','before_release'],
  'required':['host_instance','guest_major_minor','diskseq','bytes','fd_identity','mount_namespace','boot_id','helper_identity','lease_identity','device_policy_sha256','mount_policy_sha256'],
  'path_reopening_allowed':False,'privileged_consumer_deployed':False,'format_ready':False})
 return result({'actual_acceptance':None,'format_authorized':False,'format_executed':False,'blockers':['G4_NOT_PROVISIONED','SAME_INSTANCE_CONSUMER_AND_HOST_EXCLUSIVITY_MISSING','NO_FORMAT_APPROVAL']})
def readback(out,c):
 emit(out,'G6_READBACK_PLAN.json',{'status':'NOT_EXECUTED_DEPENDS_ON_G5','allocated_blocks':None,'inodes':None,'journal':None,
  'durability':None,'verifier_source':'readiness_validation.geometry','dry_run_not_live_readback':True})
 return result({'actual_acceptance':None,'blockers':['G5_NOT_EXECUTED']})
def environment(out,c):
 emit(out,'G7_ENVIRONMENT_PLAN.json',{'status':'G7_SOURCE_AND_DEPLOYMENT_PLAN_READY','mount_authorized':False,'mount_executed':False,
  'collector_source_protocol_reviewed':True,'collector_deployed':False,'cgroup_enforcement':None,'cleanup_enforcement':None,
  'ready_for_S4':False,'kernel_negative_tests':None,'live_dispatcher':False,
  'resource_verifier':'readiness_validation.resource_trace','wall_origin':'ADMISSION_BEFORE_ACTIVATION','wall_end':'COLLECTOR_FINALIZED_AFTER_DESCENDANT_CLEANUP',
  'CPU_semantics':'PARENT_CUMULATIVE_DELTA_AND_RATE; NO_ZERO_LATENCY_HARD_LIFETIME_CAP_CLAIM',
  'OOM_boundary':'WORKER_CONTROLLER_SEPARATE_FROM_COLLECTOR; OUTER_OOM_MAY_KILL_COLLECTOR',
  'manager_logs':'SHARED_EXTERNAL_ONLY_IF_B_V2_ACCEPTED; EFFECTIVE_ROUTING_UNKNOWN'})
 return result({'actual_acceptance':None,'blockers':['G2_UNACCEPTED','G4_G6_NOT_DEPLOYED','NO_MOUNT_APPROVAL','COLLECTOR_UNDEPLOYED','KERNEL_NORMAL_AND_FAILURE_EVIDENCE_MISSING']})
TASKS=dict(zip(('R0_IDENTITIES','G1_HOST','G1_GUEST','G2_ARCHITECTURE','G3_GUARDS','G4_PROVISIONING','G5_FORMAT_REVIEW','G6_GEOMETRY','G7_ENVIRONMENT'),
 (identities,host,guest,architecture,guards,provisioning,formatting,readback,environment)))

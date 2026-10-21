"""PR40 fixed-base bounded source/review delta, every commit and changed index."""
import json,re
from unittest.mock import patch
from ..resource_closure import g1_publication as privacy
original=privacy.original
BASE='8b071a4cdca472ef7c9cb78f40b894864ca30374'
PREFIX='simulation/hh_signal/final_closure/master/'
REPORTS='reports/phase7i_g1_g7_engineering/'
SOURCE_NAMES={'runner.py','history.py','guest_v2.py','readiness_validation.py','readiness_runner.py','readiness_stages.py',
 'readiness_worker.py','readiness_tests.py','readiness_guest_tests.py','readiness_publication.py',
 'prepare_readiness_private.ps1','capacity_crosscheck.cpp','readiness_scheduler_tests.py','readiness_observer_amendment.json'}
EXACT={PREFIX+n for n in SOURCE_NAMES}|{'.github/workflows/'+n+'.yml' for n in (
 'hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure','hh_signal_g1_g7_engineering')}
REPORT_NAMES={'G1_HOST_ACCEPTANCE.json','G1_GUEST_OBSERVATION.json','G1_BOOT_NAMESPACE_BINDING.json','G1_CGROUP_EFFECTIVE_STATE.json',
 'G1_STORAGE_GRAPH.json','G1_MANAGER_LOG_STATE.json','G1_COMPLETE_COVERAGE.json','G1_BLOCKERS_ZH_TW.md','G1_GUEST_STARTUP_AUTHORIZATION_REQUEST.md',
 'ARCHITECTURE_A_ACTUAL_CAPABILITY_MATRIX.json','B_V2_CLAUSE_BY_CLAUSE_REVIEW.md','HOST_GUEST_RESOURCE_LEDGER.json',
 'ARCHITECTURE_RECOMMENDATION_ZH_TW.md','ARCHITECTURE_DECISION_REQUEST.md','B_V2_CLAUSE_REVIEW.json',
 'G3_DEVICE_ADAPTER_REVIEW.md','G3_SAME_INSTANCE_HELPER_DESIGN.md','G3_COLLECTOR_SECURITY_MATRIX.json',
 'G3_RESOURCE_CONTROL_DESIGN.md','G3_NEGATIVE_TEST_RESULTS.json','G3_UNDEPLOYED_CAPABILITIES.json','G3_DEVICE_ADAPTER_STATUS.json',
 'G4_EXACT_DEVICE_IDENTITY_REQUEST.md','G4_PROVISIONING_PREREQUISITES.md','G4_CAPACITY_BUDGET.json','G4_ADMIN_EXECUTION_SCOPE.md','G4_ROLLBACK_PLAN.md',
 'G5_FORMATTING_REVIEW_PACKET.md','G5_DEVICE_INSTANCE_CONTRACT.json','G5_FORMAT_GEOMETRY_PLAN.json','G5_OPERATION_STOP_RULES.md',
 'G6_READBACK_PLAN.json','G6_VERIFICATION_PROTOCOL.md','G7_ENVIRONMENT_PLAN.json','G7_MOUNT_COLLECTOR_REVIEW.md',
 'G1_G7_MASTER_PROGRESS.json','G1_G7_MASTER_STATUS_ZH_TW.md','G1_G7_MASTER_BLOCKERS.json','G1_G7_RESOURCE_LEDGER.json',
 'G1_G7_SOURCE_MANIFEST.json','G1_G7_TEST_RESULTS.json','G1_G7_NEXT_AUTHORIZATION.md','FINAL_REPORT_ZH_TW.md',
 'BASELINE_IDENTITY.json','HELPER_SOURCE_REVIEW.json','PUBLIC_STAGE_RECEIPTS.json','preservation.json','failure_history.json','source_review.json','cpp_crosscheck.json'}
def allowed(name):return name in EXACT or name in {REPORTS+n for n in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(original,'allowed_path',allowed),patch.object(privacy,'REPORTS',REPORTS):row=privacy.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode('utf-8')
  if re.search(r'PHASE7I_G1_(?:HOST|GUEST)_CAPTURE_V[0-9]+|HH_G1_GUEST_READONLY_V2',text):raise ValueError('PRIVATE_CAPTURE_SCHEMA')
  if re.search(r'(?i)"(?:device_id|antecedent|dependent|records|block_graph|by_ids|serial|wwn)"\s*:',text):raise ValueError('PRIVATE_TOPOLOGY_OR_RAW_COUNTERS')
 return row
def audit(repo=original.REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):return original.audit(repo,base=BASE)
def main():
 try:v=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_G1_G7_PUBLICATION','reason':str(e)[:512]}));return 2
 print(json.dumps(v,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

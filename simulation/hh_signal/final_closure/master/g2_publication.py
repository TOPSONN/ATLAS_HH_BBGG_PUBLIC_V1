"""Exact PR42 source/decision delta; inspect every commit and changed index."""
import json,re
from unittest.mock import patch
from . import guest_counter_publication as previous
privacy=previous.privacy;original=previous.original
BASE='6126b315834715983481802f35630742accf1d88'
PREFIX='simulation/hh_signal/final_closure/master/'
REPORTS='reports/phase7i_g2_actual_capability/'
SOURCE_NAMES={'g2_protocol.py','g2_protocol_tests.py','g2_runner.py','g2_worker.py','g2_stages.py','g2_catalogue.py',
 'g2_independent.py','g2_engine_tests.py','g2_publication.py','g2_publication_tests.py','ledger.py','history.py'}
EXACT={PREFIX+n for n in SOURCE_NAMES}|{'.github/workflows/'+n+'.yml' for n in ('hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure','g2_actual_capability')}
STAGE_NAMES={'G2_EXACT_BASE_AND_EVIDENCE.json','G1_FINAL_EVIDENCE_RECONCILIATION.json','G2_CPU_CAPABILITY_MATRIX.json',
 'G2_CPU_ACCOUNTING_PROTOCOL.md','G2_CPU_FAILURE_MODEL.md','G2_MEMORY_SWAP_ACTUAL_GAP.json','G2_MEMORY_CHARGING_AND_TMPFS.md',
 'G2_OOM_AND_COLLECTOR_SURVIVAL.md','G2_WALL_LIFECYCLE_CONTRACT.json','G2_CONTROLLER_STOP_STATE_MACHINE.md','G2_TIMEOUT_NEGATIVE_TESTS.json',
 'G2_ARCHITECTURE_A_REAL_FEASIBILITY.json','G2_HOST_GUEST_ACCOUNTING_GAP.md','G2_A_MISSING_HARD_GUARANTEES.json',
 'G2_B_V2_CLAUSE_REVIEW.json','G2_B1_TO_B8_DECISIONS_ZH_TW.md','G2_PATH_A_VS_B_COMPARISON.md','G2_RECOMMENDED_ARCHITECTURE_ZH_TW.md',
 'G2_MINIMUM_DECISION_REQUIRED.md','G2_EFFECTIVE_STATE_DIAGNOSTIC_PROPOSAL.json','G3_REAL_GAP_CLOSURE.md','G3_RESOURCE_TRACE_TEST_RESULTS.json',
 'G3_FINAL_OBSERVER_PROTOCOL.md','G3_REMAINING_RUNTIME_CAPABILITIES.json','G4_G7_DEPLOYMENT_FEASIBILITY_MATRIX.json',
 'G4_G7_MINIMUM_OS_CAPABILITIES.md','G4_G7_NEXT_APPROVALS.md','G5_EXT4_CORE_GEOMETRY_SOURCE_REVIEW.json',
 'PHASE7I_SCIENTIFIC_RESTART_PREFLIGHT.md','PHASE7I_FROZEN_PHYSICS_IDENTITY.json','PHASE7I_FIRST_APPROVED_RUN_DEPENDENCIES.md',
 'ROOT_SELECTION_SCHEMA_REVIEW.json','G2_INDEPENDENT_SOURCE_REVIEW.json','G2_RELEASE_CHECKPOINT.json'}
REPORT_NAMES=STAGE_NAMES|{'FINAL_REPORT_ZH_TW.md','FINAL_STATUS.json','SOURCE_MANIFEST.json','SAFE_STAGE_RECEIPTS.json',
 'PRESERVATION.json','TEST_RESULTS.json','CPP_ARITHMETIC.json','ENGINEERING_FAILURE_HISTORY.json'}
def allowed(name):return name in EXACT or name in {REPORTS+n for n in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(original,'allowed_path',allowed),patch.object(privacy,'REPORTS',REPORTS):row=privacy.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode('utf-8')
  if re.search(r'PHASE7I_G1_(?:HOST|GUEST)_CAPTURE_V[0-9]+|HH_G1_GUEST_READONLY_V2|[A-Za-z]:[\\/](?:Users|HH)[\\/]',text):raise ValueError('PRIVATE_CAPTURE_OR_HOST_PATH')
  decoder=json.JSONDecoder()
  positions=[m.start() for m in re.finditer(r'[\{\[\"]',text)]
  if len(positions)>8192:raise ValueError('PUBLICATION_FRAME_BOUND')
  for pos in positions:
   try:v,_=decoder.raw_decode(text,pos)
   except (ValueError,RecursionError):continue
   previous.reject_capture(v)
 return row
def audit(repo=original.REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):return original.audit(repo,base=BASE)
def main():
 try:r=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_G2_PUBLICATION','reason':str(e)[:512]}));return 2
 print(json.dumps(r,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

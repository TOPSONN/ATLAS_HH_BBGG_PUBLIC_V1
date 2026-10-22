"""Exact PR43 bounded publication; no raw actual diagnostic receipt allowed."""
import json,re
from unittest.mock import patch
from . import g2_publication as prior
BASE='d66585fdb29c6d9262f9059ac27aaca45ed84704'
PREFIX='simulation/hh_signal/final_closure/master/';REPORTS='reports/phase7i_g2_effective_diagnostic/'
NAMES={'diagnostic_tools','diagnostic_contract','diagnostic_capture','diagnostic_validate','diagnostic_tests','diagnostic_docs','diagnostic_plan','diagnostic_worker','diagnostic_stages','diagnostic_publication','diagnostic_plan_tests'}
EXACT={PREFIX+n+'.py' for n in NAMES}|{PREFIX+'history.py'}|{'.github/workflows/'+n+'.yml' for n in ('hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure','g2_effective_diagnostic')}
STAGE_NAMES={'D0_PRESERVED_EVIDENCE.json','G2_DIAGNOSTIC_TOOL_MANIFEST.json','G2_DIAGNOSTIC_COMMAND_ZH_TW.md','G2_MANAGER_ARGV_REVIEW_ZH_TW.md','G2_DELEGATION_OBSERVABLES_ZH_TW.md',
 'G2_DIAGNOSTIC_STOP_RULES.md','G2_DIAGNOSTIC_SCOPE.json','G2_VALIDATOR_SOURCE_REVIEW.json','G2_B1_B8_DECISION_REVIEW.json','G2_B1_B8_DECISION_REVIEW_ZH_TW.md',
 'G2_ASYNC_KERNEL_COST_AMENDMENT_PROPOSAL_V1.md','G3_PROTOCOL_TO_DEPLOYMENT_GAPS.md','G3_SOURCE_PRESERVATION.json','G4_G7_MINIMUM_CAPABILITY_PATH.json',
 'SCIENTIFIC_CONTINUATION_FEASIBILITY_ZH_TW.md','FROZEN_SCIENCE_PREFLIGHT.json','DIAGNOSTIC_PREPARATION_CHECKPOINT.json'}
REPORT_NAMES=STAGE_NAMES|{'FINAL_REPORT_ZH_TW.md','FINAL_STATUS.json','SOURCE_MANIFEST.json','SAFE_STAGE_RECEIPTS.json','PRESERVATION.json','TEST_RESULTS.json','INDEPENDENT_REVIEW.json'}
def allowed(path):return path in EXACT or path in {REPORTS+n for n in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(prior,'REPORTS',REPORTS),patch.object(prior,'allowed',allowed):row=prior.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode('utf-8')
  if re.search(r'"schema"\s*:\s*"HH_G2_EFFECTIVE_DIAGNOSTIC_V1"',text):raise ValueError('RAW_DIAGNOSTIC_RECEIPT')
  if re.search(r'"(?:boot_id|namespace_inodes|membership|before|after|stdout_b64|stderr_b64)"\s*:',text):raise ValueError('RAW_DIAGNOSTIC_IDENTITY_OR_OUTPUT')
 return row
def audit(repo=prior.original.REPO):
 with patch.object(prior.original,'allowed_path',allowed),patch.object(prior.original,'validate_payload',validate):return prior.original.audit(repo,base=BASE)
def main():
 try:v=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_DIAGNOSTIC_PUBLICATION','reason':str(e)[:160]}));return 2
 print(json.dumps(v,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

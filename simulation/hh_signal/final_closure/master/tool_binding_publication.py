"""Exact PR44 source/CI plus sanitized review allowlist, all intermediate payloads."""
import json,re
from unittest.mock import patch
from . import diagnostic_publication as old
BASE='a0176ad0c684ea3f8a2d879090a1649485f225a4';PREFIX='simulation/hh_signal/final_closure/master/';REPORTS='reports/phase7i_g2_tool_binding/'
NAMES={'tool_binding_review','tool_binding_elf','tool_binding_version_probe','tool_binding_tests','tool_binding_docs','tool_binding_runner','tool_binding_publication'}
EXACT={PREFIX+n+'.py' for n in NAMES}|{PREFIX+'history.py'}|{'.github/workflows/'+n+'.yml' for n in ('hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure','g2_tool_binding')}
STAGE_NAMES={'G2_SOURCE_AND_INPUT_BINDING.json','G2_ACTUAL_TOOL_BINDING.json','G2_INSTALLED_VERSION_REVIEW.md','G2_DEPENDENCY_CLOSURE.md','G2_PENDING_VERSION_SCOPE_REVIEW.json',
 'G2_SINGLE_USE_SCOPE_REVIEW.json','G2_FIXED_ARGV_ENV_COMPARISON.json','G2_PREEXECUTION_STOP_RULES.md','G2_USER_EXECUTION_COMMAND_ZH_TW.md','G2_INDEPENDENT_VALIDATOR_RESULTS.json','G2_NEXT_ACTUAL_OS_ACTION.md','G2_BINDING_CHECKPOINT.json'}
REPORT_NAMES=STAGE_NAMES|{'FINAL_REPORT_ZH_TW.md','FINAL_STATUS.json','SOURCE_MANIFEST.json','SAFE_STAGE_RECEIPTS.json','PRESERVATION.json','TEST_RESULTS.json','INDEPENDENT_REVIEW.json'}
def allowed(name):return name in EXACT or name in {REPORTS+n for n in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(old,'REPORTS',REPORTS),patch.object(old,'allowed',allowed):v=old.validate(name,raw,mode)
 if name.startswith(REPORTS) and re.search(r'"schema"\s*:\s*"HH_G2_VERSION_ONLY_RECEIPT_V1"',raw.decode()):raise ValueError('RAW_VERSION_RECEIPT_FORBIDDEN')
 return v
def audit(repo=old.prior.original.REPO):
 with patch.object(old.prior.original,'allowed_path',allowed),patch.object(old.prior.original,'validate_payload',validate):return old.prior.original.audit(repo,base=BASE)
def main():
 try:v=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_TOOL_BINDING_PUBLICATION','reason':str(e)[:120]}));return 2
 print(json.dumps(v,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

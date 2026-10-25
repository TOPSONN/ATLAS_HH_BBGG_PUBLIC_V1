"""Exact new source and sanitized reports; every outgoing intermediate snapshot."""
import json,re
from unittest.mock import patch
from . import tool_binding_publication as prior
BASE='0edd24ed6cfba314e8f3632a0e61bd6265b7dbfa';PREFIX=prior.PREFIX;REPORTS='reports/phase7i_g2_manager_security/'
NAMES={'manager_scope_fs','manager_scope_contract','manager_scope_loader','manager_scope_capture','manager_scope_validate','manager_scope_bootstrap','manager_scope_tests','manager_scope_runner','manager_scope_docs','manager_scope_publication'}
EXACT={PREFIX+n+'.py' for n in NAMES}|{PREFIX+'history.py'}|{'.github/workflows/'+n+'.yml' for n in ('g2_manager_security','hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure')}
STAGE_NAMES={'G2_EXACT_SOURCE_REVIEW.json','G2_VERSION_RECEIPT_PRESERVATION.json','G2_ORIGINAL_SCOPE_ACL_FINDING.md','G2_SCOPE_STORAGE_SECURITY_CONTRACT.json','G2_NATIVE_PRIVATE_SCOPE_IMPLEMENTATION.md','G2_SCOPE_FD_REVIEW.json','G2_SOURCE_IMPORT_TRUST_REVIEW.md','G2_DEPENDENCY_CLOSURE_REVIEW.json','G2_MANAGER_FIXED_QUERY_REVIEW.md','G2_BUS_AND_SESSION_REQUIREMENTS.md','G2_INDEPENDENT_RECEIPT_VALIDATOR_RESULTS.json','G2_FOCUSED_TESTS.json','G2_MANAGER_SCOPE_CANDIDATE.json','G2_MANAGER_AUTHORIZATION_REQUEST_ZH_TW.md','G2_MANAGER_SINGLE_USE_COMMAND_ZH_TW.md','G2_SAFE_ENGINEERING_CHECKPOINT.json'}
REPORT_NAMES=STAGE_NAMES|{'G2_MANAGER_PREFLIGHT_FINAL_REPORT_ZH_TW.md','FINAL_STATUS.json','SOURCE_MANIFEST.json','SAFE_STAGE_RECEIPTS.json','PRESERVATION.json','TEST_RESULTS.json','INDEPENDENT_REVIEW.json'}
original=prior.old.prior.original
def allowed(name):return name in EXACT or name in {REPORTS+n for n in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(prior,'REPORTS',REPORTS),patch.object(prior,'allowed',allowed):v=prior.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode();
  if re.search(r'"schema"\s*:\s*"HH_G2_MANAGER_SECURITY_RECEIPT_V1"',text) or '我批准 ATLAS_HH_BBGG_PUBLIC_V1' in text or '"approval_text":' in text or '"verbatim_approval_text":' in text:raise ValueError('PRIVATE_RECEIPT_OR_APPROVAL_FORBIDDEN')
 return v
def audit(repo=original.REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):return original.audit(repo,base=BASE)
def main():
 try:v=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_MANAGER_SECURITY_PUBLICATION','reason':str(e)[:120]}));return 2
 print(json.dumps(v,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

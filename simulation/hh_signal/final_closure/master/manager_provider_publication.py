"""V1 provider delta gate: exact source, reports, every outgoing version/index."""
import json,re
from unittest.mock import patch
from . import manager_scope_publication as prior
BASE='21ffb4889dff3d910634df50ca514a05a2976267';PREFIX=prior.PREFIX;REPORTS='reports/phase7i_g2_native_dependency/'
NAMES={'manager_dependency_contract','manager_elf','manager_dependency_provider','manager_dependency_io','manager_dependency_validate','manager_native_contract','manager_native_evidence','manager_capsule_v2','manager_dependency_tests','manager_native_tests','manager_provider_runner','manager_provider_docs','manager_provider_publication'}
EXACT={PREFIX+n+'.py' for n in NAMES}|{PREFIX+'manager_scope_fs.py',PREFIX+'history.py',PREFIX+'manager_statfs_abi.cpp'}|{'.github/workflows/'+n+'.yml' for n in ('g2_native_dependency','hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure')}
STAGE_NAMES={'G2_ELF_DEPENDENCY_PROVIDER_REPORT.md','G2_ELF_TRANSITIVE_GRAPH_CONTRACT.json','G2_DYNAMIC_RESOLUTION_LIMITATIONS.md','G2_PYTHON_RUNTIME_IMPORT_CONTRACT.json','G2_NATIVE_EXT4_POSITIVE_VALIDATION.md','G2_NATIVE_STORAGE_ATTESTATION_PLAN.json','G2_SOURCE_CAPSULE_V2_REVIEW.md','G2_RUNTIME_DEPENDENCY_EVIDENCE_SCOPE.json','G2_NATIVE_READ_ONLY_COLLECTOR_REVIEW.md','G2_COLLECTOR_SINGLE_USE_COMMAND_ZH_TW.md','G2_COLLECTOR_STOP_RULES.md','G2_MANAGER_DISPATCH_GATE_AUDIT.md','G2_INDEPENDENT_EVIDENCE_VALIDATOR_RESULTS.json','G2_PUBLICATION_AUDIT.json','G2_NEXT_USER_APPROVAL_REQUEST_ZH_TW.md'}
REPORT_NAMES=STAGE_NAMES|{'G2_CI_RESULTS.json','FINAL_REPORT_ZH_TW.md','FINAL_STATUS.json','SOURCE_MANIFEST.json','SAFE_STAGE_RECEIPTS.json','PRESERVATION.json','TEST_RESULTS.json','INDEPENDENT_REVIEW.json'}
original=prior.original
def allowed(n):return n in EXACT or n in {REPORTS+r for r in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(prior,'REPORTS',REPORTS),patch.object(prior,'allowed',allowed):row=prior.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode();forbidden=r'"schema"\s*:\s*"(?:HH_G2_NATIVE_DEPENDENCY_EVIDENCE_V1|HH_G2_NATIVE_FINITE_STAGE_RECEIPT_V1)"|"(?:approval_text|verbatim_approval_text|ancestor_table|sessionid|loginuid)"\s*:'
  if re.search(forbidden,text):raise ValueError('PRIVATE_NATIVE_EVIDENCE_FORBIDDEN')
 return row
def audit(repo=original.REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):return original.audit(repo,base=BASE)
def main():
 try:v=audit()
 except (ValueError,OSError) as exc:print(json.dumps({'status':'FAIL_NATIVE_PROVIDER_PUBLICATION','reason':str(exc)[:120]}));return 2
 print(json.dumps(v,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

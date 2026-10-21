"""PR38 stacked delta; audit every intermediate and index, sanitize reports."""
import json
from unittest.mock import patch
from .contract import BASE,REPO
from ..resource_closure import g1_publication as privacy
original=privacy.original
PREFIX='simulation/hh_signal/final_closure/master/'
REPORTS='reports/phase7i_master_unattended/'
SOURCE_NAMES={'__init__.py','__main__.py','contract.py','ledger.py','history.py','same_instance.py','tasks.py',
 'worker.py','runner.py','publication.py','test_master.py','test_publication.py','ci_smoke.py','b_v2_cost_assignment.json','USER_GUIDE_ZH_TW.md'}
EXACT={PREFIX+n for n in SOURCE_NAMES}|{'simulation/hh_signal/final_closure/src/contracts.py',
 '.github/workflows/hh_signal_campaign.yml','.github/workflows/hh_signal_readiness.yml',
 '.github/workflows/hh_signal_final_closure.yml','.github/workflows/hh_signal_master_unattended.yml'}
REPORT_NAMES={'MASTER_PROGRESS.json','MASTER_STATUS_ZH_TW.md','MASTER_BLOCKERS.json','MASTER_SOURCE_MANIFEST.json',
 'MASTER_TEST_SUMMARY.json','MASTER_NEXT_AUTHORIZATION.md','MASTER_REPORT_ZH_TW.md','PUBLIC_STAGE_RECEIPTS.json',
 'G1_HOST_INVENTORY.json','G1_GUEST_INVENTORY.json','G1_CGROUP_CAPABILITIES.json','G1_STORAGE_TOPOLOGY.json',
 'G1_LOGGING_BOUNDARIES.json','G1_EVIDENCE_COMPLETENESS.json','ARCHITECTURE_A_FEASIBILITY.json','ARCHITECTURE_B_V2_REVIEW.json',
 'INDEPENDENT_KAPPA_CHECK.json','SCIENTIFIC_METHOD_PREFLIGHT.json','ROOT_SELECTION_SCHEMA_REVIEW.json',
 'preservation.json','validation.json','independent_review.json','failure_history.json','ci_validation.json'}
def allowed(name):return name in EXACT or name in {REPORTS+n for n in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(privacy,'REPORTS',REPORTS):return privacy.validate(name,raw,mode)
def audit(repo=REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):return original.audit(repo,base=BASE)
def main():
 try:r=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_MASTER_PUBLICATION','reason':str(e)[:512]}));return 2
 print(json.dumps(r,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

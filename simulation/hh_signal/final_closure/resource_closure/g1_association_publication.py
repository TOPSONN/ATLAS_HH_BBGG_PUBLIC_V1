"""Fixed PR39 repair scope; no raw capture or figures in any outgoing commit."""
import json,re
from unittest.mock import patch
from . import g1_publication as privacy
original=privacy.original
BASE='b2bd49b68c3a439eeef24b7b2e134f1746bf5fb9'
PREFIX='simulation/hh_signal/final_closure/resource_closure/'
REPORTS='reports/phase7i_g1_association_repair/'
EXACT={PREFIX+n for n in ('g1_windows_inventory.ps1','g1_acquisition.py','g1_associations.py',
 'g1_association_publication.py','tests/test_g1_associations.py','tests/g1_association_offline.ps1')}|{
 'simulation/hh_signal/final_closure/master/history.py',
 '.github/workflows/hh_signal_campaign.yml','.github/workflows/hh_signal_readiness.yml',
 '.github/workflows/hh_signal_final_closure.yml','.github/workflows/hh_signal_resource_closure.yml',
 '.github/workflows/hh_signal_g1_association_repair.yml'}
REPORT_NAMES={'REVIEW_ZH_TW.md','USER_COMMAND_ZH_TW.md','validation.json','source_manifest.json',
 'preservation.json','bound_diagnosis.json','powershell_offline.json','G1_PUBLIC_PROJECTION.json','capture_status.json'}
def allowed(name):return name in EXACT or name in {REPORTS+n for n in REPORT_NAMES}
def validate(name,raw,mode='100644'):
 with patch.object(original,'allowed_path',allowed),patch.object(privacy,'REPORTS',REPORTS):row=privacy.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode('utf-8')
  if re.search(r'PHASE7I_G1_(?:HOST|GUEST)_CAPTURE_V[0-9]+',text):raise ValueError('PRIVATE_CAPTURE_SCHEMA')
  if re.search(r'(?i)"(?:device_id|antecedent|dependent|synthetic_edges|synthetic_volume_edges)"\s*:',text):raise ValueError('PRIVATE_OR_FIXTURE_TOPOLOGY_NOT_PUBLIC')
 return row
def audit(repo=original.REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):return original.audit(repo,base=BASE)
def main():
 try:result=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_G1_REPAIR_PUBLICATION','reason':str(e)[:512]}));return 2
 print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

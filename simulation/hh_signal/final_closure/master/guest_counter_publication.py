"""Fixed PR41 base and exact source/sanitized-report publication scope."""
import json,re
from unittest.mock import patch
from ..resource_closure import g1_publication as privacy
original=privacy.original
BASE='1ee91a8b4aa974a80c0b5a73c35e2c0e34204fee'
PREFIX='simulation/hh_signal/final_closure/master/'
REPORTS='reports/g1_guest_v2_counter_repair/'
SOURCE_NAMES={'readiness_validation.py','guest_counter_review.py','guest_counter_tests.py',
 'guest_counter_publication.py','guest_counter_publication_tests.py','history.py'}
EXACT={PREFIX+n for n in SOURCE_NAMES}|{'.github/workflows/'+n+'.yml' for n in (
 'hh_signal_campaign','hh_signal_readiness','hh_signal_final_closure','g1_guest_v2_counter_repair')}
REPORT_NAMES={'FINAL_REPORT_ZH_TW.md','G1_GUEST_VALIDATION.json','OLD_FAILURE_DIAGNOSTIC.json',
 'SOURCE_MANIFEST.json','PRESERVATION.json','TEST_RESULTS.json','INDEPENDENT_REVIEW.json','G2_CAPABILITY_ANALYSIS_ZH_TW.md'}
def allowed(name):return name in EXACT or name in {REPORTS+n for n in REPORT_NAMES}
PRIVATE_KEYS={'device_id','antecedent','dependent','records','block_graph','by_ids','serial','wwn','boot_id','mount_namespace','cgroup_lineage'}
def reject_capture(value,depth=0):
 if depth>16:raise ValueError('PUBLICATION_NESTING_BOUND')
 if isinstance(value,dict):
  if value.get('schema')=='HH_G1_GUEST_READONLY_V2' or any(str(k).lower() in PRIVATE_KEYS for k in value):raise ValueError('PRIVATE_TOPOLOGY_OR_RAW_IDENTITY')
  for v in value.values():reject_capture(v,depth+1)
 elif isinstance(value,list):
  for v in value:reject_capture(v,depth+1)
 elif isinstance(value,str):
  try:v=json.loads(value)
  except (ValueError,RecursionError):return
  reject_capture(v,depth+1)
def validate(name,raw,mode='100644'):
 with patch.object(original,'allowed_path',allowed),patch.object(privacy,'REPORTS',REPORTS):row=privacy.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode('utf-8')
  if re.search(r'PHASE7I_G1_(?:HOST|GUEST)_CAPTURE_V[0-9]+|HH_G1_GUEST_READONLY_V2',text):raise ValueError('PRIVATE_CAPTURE_SCHEMA')
  if re.search(r'(?i)"(?:device_id|antecedent|dependent|records|block_graph|by_ids|serial|wwn|boot_id|mount_namespace|cgroup_lineage)"\s*:',text):raise ValueError('PRIVATE_TOPOLOGY_OR_RAW_IDENTITY')
  decoder=json.JSONDecoder()
  for match in re.finditer(r'[\{\[\"]',text):
   try:value,_=decoder.raw_decode(text,match.start())
   except (ValueError,RecursionError):continue
   reject_capture(value)
 return row
def audit(repo=original.REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):return original.audit(repo,base=BASE)
def main():
 try:r=audit()
 except (ValueError,OSError) as e:print(json.dumps({'status':'FAIL_COUNTER_REPAIR_PUBLICATION','reason':str(e)[:512]}));return 2
 print(json.dumps(r,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

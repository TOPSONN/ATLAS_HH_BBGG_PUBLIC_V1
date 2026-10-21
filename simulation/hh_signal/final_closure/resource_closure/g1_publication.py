"""PR37 delta gate: source + redacted evidence, every intermediate and index."""
import json,re
from unittest.mock import patch
from . import publication as original, admin_publication as prior

BASE='80f78fafa5fb835a35d9a58537360c1726cf2eea'
PREFIX=prior.PREFIX
REPORTS='reports/phase7i_g1_g2_feasibility/'
EXACT={PREFIX+n for n in ('g1_acquisition.py','g1_guest_inventory.py','g1_windows_inventory.ps1',
 'g1_publication.py','tests/test_g1_acquisition.py','tests/test_g1_publication.py',
 'config/b_v2_research_execution_terms.json')}|original.WORKFLOWS
DENIED_KEYS={'serial','serialnumber','wwn','pnpdeviceid','basepath','stdout','stderr',
 'error_message','observations','block_relations','by_ids','path_metadata','raw_inventory',
 'credentials','password','access_token'}

def allowed(name):
 return name in EXACT or (name.startswith(REPORTS) and
  prior.allowed(name.replace(REPORTS,prior.REPORTS,1)))

def reject_raw(value,depth=0):
 if depth>16:raise ValueError('PUBLICATION_NESTING_BOUND')
 if isinstance(value,dict):
  if value.get('schema') in ('PHASE7I_G1_HOST_CAPTURE_V1','PHASE7I_G1_GUEST_CAPTURE_V1'):
   raise ValueError('PRIVATE_HOST_OR_GUEST_CAPTURE_FORBIDDEN')
  for key,child in value.items():
   if str(key).lower() in DENIED_KEYS:raise ValueError('PRIVATE_INVENTORY_FIELD_FORBIDDEN')
   reject_raw(child,depth+1)
 elif isinstance(value,list):
  for child in value:reject_raw(child,depth+1)
 elif isinstance(value,str):
  if re.search(r'(?i)S-1-5-21-[0-9-]+',value):raise ValueError('PRIVATE_SID_FORBIDDEN')
  text=value.strip()
  if text.startswith(('{','[','"')):
   try:decoded=json.loads(text)
   except (ValueError,RecursionError):return
   reject_raw(decoded,depth+1)

def validate(name,raw,mode='100644'):
 row=prior.validate(name,raw,mode)
 if name.startswith(REPORTS):
  text=raw.decode('utf-8')
  if re.search(r'(?i)S-1-5-21-[0-9-]+|PHASE7I_G1_(?:HOST|GUEST)_CAPTURE_V1|"(?:serial(?:number)?|wwn|PNPDeviceID|BasePath|observations|stdout|stderr|error_message)"\s*:',text):
   raise ValueError('PRIVATE_RAW_INVENTORY_OR_SID')
  if re.search(r'(?im)^\s*(?:serial(?:number)?|wwn|pnpdeviceid|basepath)\s*[:=]\s*\S+',text):
   raise ValueError('PRIVATE_INVENTORY_TEXT_FIELD')
  if name.lower().endswith('.json'):reject_raw(json.loads(text))
  # Check JSON/JSONL frames and nested serialized payloads in Markdown/text.
  decoder=json.JSONDecoder();positions=[m.start() for m in re.finditer(r'[\{\[\"]',text)]
  if len(positions)>8192:raise ValueError('PUBLICATION_FRAME_COUNT_BOUND')
  for start in positions:
   try:decoded,_=decoder.raw_decode(text,start)
   except (ValueError,RecursionError):continue
   reject_raw(decoded)
 return row

def audit(repo=original.REPO):
 with patch.object(original,'allowed_path',allowed),patch.object(original,'validate_payload',validate):
  return original.audit(repo,base=BASE)

def main():
 try:result=audit()
 except (ValueError,OSError) as error:
  print(json.dumps({'status':'FAIL_G1_PUBLICATION','reason':str(error)[:1024]}));return 2
 print(json.dumps(result,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())

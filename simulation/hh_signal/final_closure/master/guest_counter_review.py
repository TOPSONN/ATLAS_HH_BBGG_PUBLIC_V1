"""Offline review of an existing capture. No collector or runtime dispatcher."""
import argparse,hashlib,json,re,stat
from pathlib import Path
from .contract import need
from .readiness_validation import guest_review

MAX_BYTES=262144
def unique_object(items):
 result={}
 for key,value in items:
  need(key not in result,'DUPLICATE_JSON_FIELD');result[key]=value
 return result

def review_bytes(raw,expected_raw,source,legacy):
 need(type(raw) is bytes and len(raw)<=MAX_BYTES,'RAW_BYTE_BOUND')
 need(type(expected_raw) is str and re.fullmatch('[0-9a-f]{64}',expected_raw),'RAW_SHA256_SYNTAX')
 digest=hashlib.sha256(raw).hexdigest();need(digest==expected_raw,'RAW_SHA256_MISMATCH')
 value=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_object)
 result=guest_review(value,source,legacy)
 return {'raw_sha256':digest,'collector_source_sha256':source,'legacy_collector_source_sha256':legacy,
  'validator_source_sha256':hashlib.sha256(Path(__file__).with_name('readiness_validation.py').read_bytes()).hexdigest(),
  'review':result,'raw_capture_modified':False,'new_capture_executed':False,'historical_run_rebound':False,
  'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'FORMAL_BUILD_ONLY_AUTHORIZED':False}

def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 p.add_argument('--input',type=Path,required=True);p.add_argument('--expected-raw-sha256',required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:
  need(stat.S_ISREG(a.input.lstat().st_mode),'INPUT_REGULAR_FILE_REQUIRED')
  with a.input.open('rb') as f:raw=f.read(MAX_BYTES+1)
  root=Path(__file__).parents[1]
  sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
  result=review_bytes(raw,a.expected_raw_sha256,sha(Path(__file__).with_name('guest_v2.py')),
   sha(root/'resource_closure/g1_guest_inventory.py'))
  output=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode('utf-8')
  need(len(output)<=16384,'SANITIZED_OUTPUT_BOUND')
  with a.output.open('xb') as f:f.write(output)
  print(json.dumps({'status':result['review']['status'],'sanitized_sha256':hashlib.sha256(output).hexdigest(),
   'lineage_count':result['review']['lineage_count'],'raw_sha256':result['raw_sha256']}));return 0
 except (OSError,ValueError,KeyError,TypeError,RecursionError):
  # Exception text may contain private input paths/values. Never echo it.
  print(json.dumps({'status':'BLOCKED_OFFLINE_REVIEW','raw_capture_modified':False}));return 2

if __name__=='__main__':raise SystemExit(main())

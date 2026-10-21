"""Strict G1 capture interpretation. JSON never authenticates a host or authorizes work."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, re, uuid
from pathlib import Path
from . import device_policy as policy, instance_binding

MAX_BYTES=262144
HOST_KEYS={'runtime','wsl_version','running_distros','os_memory','hypervisor','features',
 'disk_drives','partitions','logical_disks','disk_partition_links','partition_volume_links',
 'storage_disks','registered_distro_backing'}
STATES={'REPORTED_UNATTESTED','UNKNOWN'}
ERRORS={'ACCESS_DENIED','QUERY_FAILED','OUTPUT_BOUND','QUERY_TIMEOUT','CLEANUP_UNKNOWN',
 'NATIVE_QUERY_NONZERO','ACQUISITION_DEADLINE','STOPPED_AFTER_CLEANUP_UNKNOWN'}

def check(ok,reason):
 if not ok:raise ValueError(reason)

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def no_duplicates(rows):
 result={}
 for key,value in rows:
  check(key not in result,'DUPLICATE_JSON_KEY');result[key]=value
 return result

def load(raw):
 check(type(raw) is bytes and len(raw)<=MAX_BYTES,'CAPTURE_BYTE_BOUND')
 return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=no_duplicates,
  parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))

def validate_host(value):
 check(type(value) is dict and value.get('schema')=='PHASE7I_G1_HOST_CAPTURE_V1','HOST_SCHEMA')
 check(len(canonical(value))<=MAX_BYTES,'CAPTURE_BYTE_BOUND')
 check(type(value.get('capture_id')) is str and str(uuid.UUID(value['capture_id']))==value['capture_id'],'CAPTURE_UUID')
 check(type(value.get('collector_sha256')) is str and re.fullmatch('[a-f0-9]{64}',value['collector_sha256']),'COLLECTOR_HASH')
 check(value.get('administrator') is False and type(value.get('distro_launches')) is int and value['distro_launches']==0 and
       type(value.get('privileged_actions')) is int and value['privileged_actions']==0,'UNAUTHORIZED_SCOPE')
 check(value.get('trust')=='REPORTED_UNATTESTED' and value.get('host_guest_mapping_complete') is False and
       value.get('protected_storage_complete') is False,'SELF_ATTESTATION_FORBIDDEN')
 try:times=[dt.datetime.fromisoformat(value[k].replace('Z','+00:00')) for k in ('started_utc','ended_utc')]
 except (ValueError,TypeError,AttributeError,KeyError):raise ValueError('INVALID_CAPTURE_TIME') from None
 check(all(t.utcoffset() is not None for t in times) and times[1]>=times[0],'CAPTURE_TIME_ORDER')
 rows=value.get('observations')
 check(type(rows) is list and len(rows)==len(HOST_KEYS),'OBSERVATION_COVERAGE')
 check(all(type(r) is dict for r in rows) and {r.get('key') for r in rows}==HOST_KEYS,'OBSERVATION_KEYS')
 for row in rows:
  check(row.get('status') in STATES and type(row.get('interface')) is str and 0<len(row['interface'])<=128,'OBSERVATION_ORIGIN')
  check(row.get('error_code') is None or row['error_code'] in ERRORS,'ERROR_CODE')
  if 'data' in row:check(type(row['data']) is list and len(row['data'])<=128 and len(canonical(row['data']))<=65536,'OBSERVATION_BOUND')
  if row['status']=='REPORTED_UNATTESTED':
   check(row.get('error_code') is None,'REPORTED_OBSERVATION_CANNOT_CONTAIN_ERROR')
   check(type(row.get('data')) is list,'DATA_REQUIRED')
  if row['key'] in ('wsl_version','running_distros') and row.get('data'):
   native=row['data'][0]
   check(type(native) is dict and type(native.get('exit_code')) is int,'NATIVE_EXIT')
   check(native['exit_code']==0 or row['status']=='UNKNOWN','NONZERO_NATIVE_MUST_BE_UNKNOWN')
 return value

def public_projection(value):
 """An allowlist projection: never echo a serial, path, error message or raw row."""
 validate_host(value)
 rows={r['key']:r for r in value['observations']}
 native=rows['running_distros'];running='UNKNOWN';count=None
 if native['status']=='REPORTED_UNATTESTED' and native['data']:
  text=native['data'][0].get('stdout')
  check(type(text) is str and len(text)<=32768,'RUNNING_LIST_BOUND')
  names=[s.strip() for s in text.splitlines() if s.strip()]
  count=len(names);running='RUNNING_REPORTED_UNATTESTED' if names else 'NONE_RUNNING_REPORTED_UNATTESTED'
 coverage=[{'item':k,'status':rows[k]['status'],'row_count':len(rows[k].get('data',[])),
            'error_code':rows[k].get('error_code')} for k in sorted(HOST_KEYS)]
 return {'schema':'PHASE7I_G1_PUBLIC_PROJECTION_V1','capture_sha256':hashlib.sha256(canonical(value)).hexdigest(),
  'capture_digest_basis':'CANONICAL_CAPTURE_NOT_RAW_FILE','collector_sha256':value['collector_sha256'],
  'coverage':coverage,'running_distro_state':running,'running_distro_count':count,
  'host_identity_confidence':'REPORTED_UNATTESTED','guest_identity_confidence':'UNKNOWN',
  'protected_storage_complete':False,'host_guest_mapping_complete':False,
  'A_verdict':'A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST','B_status':'PROPOSED_NOT_ACCEPTED',
  'execution_authorized':False,'FULL_LAUNCH_ENVELOPE_VERIFIED':False}

def existing_policy_decisions(value):
 """The actual partial acquisition cannot be inflated into an eligible device."""
 validate_host(value)
 incomplete={'schema':'DEVICE_GRAPH_REVIEW_V1','complete':False,'host_mapping_complete':False,
  'all_mount_namespaces_complete':False,'nodes':[],
  'actual_host_capture_sha256':hashlib.sha256(canonical(value)).hexdigest()}
 calls=(('device',lambda:policy.review_device(incomplete,{})),
        ('mount',lambda:policy.review_mount({'schema':'MOUNT_TARGET_REVIEW_V1','complete':False},{})),
        ('transaction',lambda:instance_binding.review_transaction([],{})))
 results=[]
 for name,call in calls:
  try:call()
  except policy.PolicyError as error:results.append({'policy':name,'status':'REJECTED_INCOMPLETE_REAL_ACQUISITION','reason':str(error)})
  else:raise ValueError('UNEXPECTED_POLICY_ACCEPTANCE')
 return results

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--capture',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:
  with a.capture.open('rb') as stream:raw=stream.read(MAX_BYTES+1)
  v=load(raw);out=public_projection(v);out['raw_capture_sha256']=hashlib.sha256(raw).hexdigest()
  # This binds reported source bytes, never authenticates execution/origin.
  expected=hashlib.sha256(Path(__file__).with_name('g1_windows_inventory.ps1').read_bytes()).hexdigest()
  check(v['collector_sha256']==expected,'COLLECTOR_SOURCE_IDENTITY_MISMATCH')
  out['reported_collector_hash_matches_reviewed_source']=True
  out['existing_policy_decisions']=existing_policy_decisions(v)
  with a.output.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2);stream.write('\n')
 except (ValueError,TypeError,KeyError,OSError,OverflowError,RecursionError):
  print(json.dumps({'status':'FAIL_G1_CAPTURE_VALIDATION','execution_authorized':False}));return 2
 print(json.dumps({'status':'PROJECTED_UNATTESTED','coverage_items':len(out['coverage']),
                  'running_distro_state':out['running_distro_state'],'execution_authorized':False}))
 return 0

if __name__=='__main__':raise SystemExit(main())

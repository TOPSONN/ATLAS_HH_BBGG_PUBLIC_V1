"""V2 source/observation contracts; no boolean can attest a future child."""
import hashlib,json,re,posixpath
BASE='21ffb4889dff3d910634df50ca514a05a2976267'
CAP=131072;FILE_CAP=16*1024**2;TOTAL_FILE_CAP=64*1024**2;MAX_FILES=64;MAX_EDGES=512;MAX_MODULES=128;MAX_ALIASES=8
ORIGINAL=('diagnostic_capture.py','diagnostic_contract.py','diagnostic_tools.py','diagnostic_validate.py')
RUNTIME={'manager_scope_fs.py','manager_elf.py','manager_dependency_contract.py','manager_dependency_provider.py','manager_dependency_validate.py','manager_dependency_io.py','manager_native_contract.py','manager_native_evidence.py','manager_capsule_v2.py'}
CLOSURE=set(ORIGINAL)|RUNTIME
SCHEMA='HH_G2_NATIVE_DEPENDENCY_EVIDENCE_V1';CAPSULE_SCHEMA='HH_G2_SOURCE_CAPSULE_V2'
CONSUMED={'0e76645d07be2eb646f2cc44163b8a34db3f3ad38cfe07c42105845df37e2e02','09c7e3b9b4380d0dd40fdea6a618f997180925ae0b1ab7b3f0d7b0cc0902ca62'}
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(v):need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'SHA256_REQUIRED')
def path(v):
 need(type(v) is str and v.startswith('/') and len(v)<=512 and '\\' not in v and '\x00' not in v and all(x not in ('','.','..') for x in v.split('/')[1:]),'EXACT_ABSOLUTE_PATH');return v
def u64(v):need(type(v) is int and 0<=v<=2**64-1,'U64_REQUIRED');return v
def load(raw,cap=CAP):
 need(type(raw) is bytes and 0<len(raw)<=cap,'JSON_BYTE_BOUND')
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
  return out
 def integer(v):need(re.fullmatch('0|[1-9][0-9]*',v) is not None,'UNSIGNED_CANONICAL_INTEGER');return u64(int(v))
 def bad(_):raise ValueError('NONCANONICAL_JSON_NUMBER')
 return json.loads(raw,object_pairs_hook=pairs,parse_int=integer,parse_float=bad,parse_constant=bad)
def alias_target(link,target):
 path(link);need(type(target) is str and 0<len(target)<=512 and '\x00' not in target and '\\' not in target,'ALIAS_TARGET')
 components=[] if target.startswith('/') else link.split('/')[1:-1]
 for part in target.split('/'):
  if part in ('','.'):continue
  if part=='..':need(bool(components),'ALIAS_ROOT_ESCAPE');components.pop()
  else:components.append(part)
 return path('/'+'/'.join(components))
def pending_runtime_manifest(revision,hashes):
 from . import diagnostic_contract as original
 need(re.fullmatch('[0-9a-f]{40}',revision) is not None and set(hashes)==CLOSURE,'V2_MANIFEST_SOURCE')
 for value in hashes.values():digest(value)
 return {'schema':'HH_G2_MANAGER_RUNTIME_MANIFEST_V2','source_revision':revision,'source_closure_sha256':dict(hashes),'argvs':original.argvs(1000),'environment':original.environment(1000),'native_stage_receipt_sha256':None,'native_observation_receipt_sha256':None,'validated_dependencies':None,'new_manager_approval_record_sha256':None,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False,'execution_authorized':False}

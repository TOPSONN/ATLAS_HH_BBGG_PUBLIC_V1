"""Fixed DAG and identities. An input, flag, or receipt cannot grant execution."""
from pathlib import Path
import hashlib,json,re,subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
PROGRESS=REPO/'.local/master_progress_v1'
BASE='806d05b294fb4acedb1eca2fc420cd8af4b0d147'
PHYSICS='a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb'
GUARD='404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123'
STATES={'NOT_STARTED','RUNNING','PASS_SOURCE_ONLY','PASS_READ_ONLY_OBSERVED','PASS_KERNEL_VERIFIED',
 'BLOCKED_AUTHORIZATION','BLOCKED_OS_CAPABILITY','BLOCKED_INPUT','FAIL','UNKNOWN','COMPLETE'}
SAFE=(('G0_SOURCE_BASELINE',()),('G1_REAL_INVENTORY',('G0_SOURCE_BASELINE',)),
 ('G2_ARCHITECTURE_DECISION',('G0_SOURCE_BASELINE',)),('G3_DEVICE_AND_HELPER_REVIEW',('G0_SOURCE_BASELINE',)),
 ('EXISTING_INPUT_AUDIT',('G0_SOURCE_BASELINE',)),('EXISTING_NUMERICAL_REPORT',('G0_SOURCE_BASELINE',)),
 ('INDEPENDENT_NUMERICAL_CHECK',('EXISTING_NUMERICAL_REPORT',)),('SCIENTIFIC_METHOD_PREFLIGHT',('G0_SOURCE_BASELINE',)),
 ('ROOT_SELECTION_SCHEMA_REVIEW',('G0_SOURCE_BASELINE',)),('FUTURE_REVIEW_PACKAGES',('G0_SOURCE_BASELINE',)),
 ('PHASE7L_SAFE_REPORT',('G0_SOURCE_BASELINE',)))
LIVE=('G4_ADMIN_PROVISIONING','G5_FORMATTING','G6_POST_FORMAT_READBACK','G7_MOUNT_AND_COLLECTOR',
 'S4_REAL_CONTROLLER','FULL_RESOURCE_ACCEPTANCE','BUILD_ONLY','BINARY_REVIEW','PHYSICAL_RESTART',
 'PHASE7I_STAGE_A','PHASE7I_FOUR_REPLICAS','PHASE7J_SM1000','PHASE7K_CORRECTED_ANALYSIS','PHASE7L_FINAL_REPORT')
RUN_ID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z')
LIMITS={'S4':{'CPU_seconds':4,'wall_seconds':13,'RAM_bytes':536870912,'swap_bytes':0,'disk_bytes':16777216,'jobs':1,'workers':1},
 'BUILD':{'CPU_seconds':14400,'wall_seconds':14400,'RAM_bytes':2147483648,'swap_bytes':0,'disk_bytes':5368709120,'jobs':1,'workers':1}}
def need(ok,reason):
 if not ok:raise ValueError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def load(path,cap=2*1024**2):
 with Path(path).open('rb') as f:raw=f.read(cap+1)
 need(len(raw)<=cap,'INPUT_BYTE_BOUND')
 def pairs(rows):
  value={}
  for k,v in rows:need(k not in value,'DUPLICATE_JSON_KEY');value[k]=v
  return value
 def bad(v):raise ValueError('NONFINITE_JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def no_links(path):
 path=Path(path)
 need(path.is_absolute() and '..' not in path.parts,'CANONICAL_PATH_REQUIRED')
 for p in (path,*path.parents):
  if p.exists() or p.is_symlink():
   need(not p.is_symlink() and not (getattr(p.lstat(),'st_file_attributes',0)&0x400),'REPARSE_OR_SYMLINK')
 return path
def git(*args):
 v=subprocess.run(['git','-C',str(REPO),*args],capture_output=True,timeout=30)
 need(v.returncode==0 and len(v.stdout)<=262144 and len(v.stderr)<=4096,'READONLY_GIT_FAILED')
 return v.stdout
def source_binding(capture=None):
 need(not git('status','--porcelain','--untracked-files=no'),'TRACKED_WORKTREE_DIRTY')
 revision=git('rev-parse','HEAD').decode().strip();need(re.fullmatch('[0-9a-f]{40}',revision) is not None,'REVISION')
 old=load(REPO/'reports/phase7i_g1_g2_feasibility/source_manifest.json')
 names={r['path'] for r in old['files']}
 names|={p.relative_to(REPO).as_posix() for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md') and '__pycache__' not in p.parts}
 names|={'.github/workflows/hh_signal_master_unattended.yml','simulation/hh_signal/final_closure/src/contracts.py'}
 rows=[]
 for name in sorted(names):
  p=no_links(REPO/name);need(p.stat().st_size<=16*1024**2,'SOURCE_FILE_BOUND')
  rows.append({'path':name,'sha256':sha(p.read_bytes())})
 host=None
 if capture is not None:
  p=no_links(Path(capture));need(p.is_file() and p.stat().st_size<=262144,'HOST_CAPTURE_BOUND')
  host={'path':str(p),'sha256':sha(p.read_bytes())}
 from ..src.contracts import input_identity
 inputs=input_identity()
 input_rows=[{'path':r['path'],'sha256':r['sha256']} for r in inputs]
 value={'revision':revision,'source_rows':rows,'source_sha256':sha(canonical(rows)),
  'inputs_sha256':sha(canonical(input_rows)),'input_count':len(input_rows),
  'frozen_input_manifest_sha256':sha((REPO/'simulation/hh_signal/final_closure/config/source_inputs.json').read_bytes()),
  'host_capture':host,'scope':'SAFE_ENGINEERING_AND_READ_ONLY'}
 return value
def binding_identity(v):
 return sha(canonical({k:v[k] for k in ('revision','source_sha256','inputs_sha256','host_capture','scope')}))
def plan():
 return {'schema':'HH_MASTER_SAFE_PLAN_V1','scope':'SAFE_ENGINEERING_AND_READ_ONLY',
  'safe_DAG':[{'stage_id':s,'dependencies':list(d),'evidence_ceiling':'SOURCE_OR_READ_ONLY_ONLY'} for s,d in SAFE],
  'formal_live_dependency_chain':list(LIVE),'live_dispatch_implemented':False,'authorization_accepted':False,
  'G8_ROLLBACK':'NOT_STARTED; ONLY_IF_NEEDED_AND_SEPARATELY_AUTHORIZED','nominal_limits':LIMITS,
  'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'FORMAL_BUILD_ONLY_AUTHORIZED':False}

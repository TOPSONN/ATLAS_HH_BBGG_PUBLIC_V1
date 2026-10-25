"""Standalone same-byte capsule V2 entry; pending launch stops before guest reads."""
import hashlib,importlib.abc,importlib.util,json,os,re,stat,sys,types
PACKAGE='_hh_g2_native_v2';CAP=131072
NAMES={'diagnostic_capture.py','diagnostic_contract.py','diagnostic_tools.py','diagnostic_validate.py','manager_scope_fs.py','manager_elf.py','manager_dependency_contract.py','manager_dependency_provider.py','manager_dependency_validate.py','manager_dependency_io.py','manager_native_contract.py','manager_native_evidence.py','manager_capsule_v2.py'}
def need(ok,why):
 if not ok:raise ValueError(why)
class Capsule(importlib.abc.MetaPathFinder,importlib.abc.Loader):
 def __init__(self,raws,hashes):
  need(set(raws)==set(hashes)==NAMES,'EXACT_CAPSULE_V2_CLOSURE');self.codes={}
  for name,raw in raws.items():
   need(type(raw) is bytes and 0<len(raw)<=CAP and hashlib.sha256(raw).hexdigest()==hashes[name],'CAPSULE_V2_SOURCE_HASH');self.codes[name]=compile(raw,'reviewed-memory://'+name,'exec',dont_inherit=True)
 def find_spec(self,fullname,path=None,target=None):
  if not fullname.startswith(PACKAGE+'.'):return None
  name=fullname[len(PACKAGE)+1:]+'.py';need(name in self.codes,'NO_CAPSULE_PATH_FALLBACK');return importlib.util.spec_from_loader(fullname,self,origin='reviewed-memory://'+name)
 def create_module(self,spec):return None
 def exec_module(self,module):
  name=module.__name__.split('.')[-1]+'.py';module.__file__='reviewed-memory://'+name;exec(self.codes[name],module.__dict__)
 def __enter__(self):
  need(not any(n==PACKAGE or n.startswith(PACKAGE+'.') for n in sys.modules),'PRELOADED_CAPSULE_V2');p=types.ModuleType(PACKAGE);p.__path__=[];sys.modules[PACKAGE]=p;sys.meta_path.insert(0,self);return self
 def __exit__(self,*args):
  sys.meta_path.remove(self)
  for n in list(sys.modules):
   if n==PACKAGE or n.startswith(PACKAGE+'.'):del sys.modules[n]
def read_source(path,digest,held):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC);held.append(fd);s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=CAP,'SOURCE_FILE_INSTANCE');raw=bytearray()
 while True:
  b=os.read(fd,min(65536,CAP+1-len(raw)))
  if not b:break
  raw.extend(b);need(len(raw)<=CAP,'SOURCE_READ_BOUND')
 after=os.fstat(fd);need(all(getattr(s,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_mode')) and hashlib.sha256(raw).hexdigest()==digest,'SOURCE_READ_DRIFT');return bytes(raw)
def launch(root,scope_raw,record_raw,scope_sha,record_sha):
 for value in (scope_sha,record_sha,globals().get('EXTERNAL_ENTRY_SHA256')):need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'STOP_PENDING_NEW_INDEPENDENT_APPROVAL')
 need(record_sha not in ('0e76645d07be2eb646f2cc44163b8a34db3f3ad38cfe07c42105845df37e2e02','09c7e3b9b4380d0dd40fdea6a618f997180925ae0b1ab7b3f0d7b0cc0902ca62'),'CONSUMED_APPROVAL')
 need(hashlib.sha256(scope_raw).hexdigest()==scope_sha and hashlib.sha256(record_raw).hexdigest()==record_sha and len(scope_raw)<=CAP and len(record_raw)<=CAP,'INPUT_BYTE_CHAIN');scope=json.loads(scope_raw);record=json.loads(record_raw)
 need(scope['authorization_reference']==record_sha and scope['execution_authorized'] is False and record['provenance']=='USER_PROVIDED_VERBATIM_APPROVAL_REPORTED' and record['operation']==scope['operation'] and record['operation'] in ('NATIVE_STAGE_ONCE','NATIVE_READ_ONLY_ONCE') and record['maximum_attempts']==1 and record['manager_authorized'] is False,'STOP_INVALID_EXTERNAL_APPROVAL_BEFORE_SOURCE_READ')
 need(scope['source_revision']==record['source_revision']==globals().get('EXTERNAL_SOURCE_REVISION'),'EXACT_EXECUTABLE_REVISION')
 pending=dict(scope,authorization_reference=None);canonical=json.dumps(pending,sort_keys=True,separators=(',',':'),allow_nan=False).encode();need(hashlib.sha256(canonical).hexdigest()==record['pending_scope_sha256'],'PENDING_SCOPE_CHAIN')
 hashes=scope['source_closure_sha256'];need(set(hashes)==NAMES and hashes['manager_capsule_v2.py']==EXTERNAL_ENTRY_SHA256,'EXTERNAL_ENTRY_SOURCE_CHAIN')
 need(type(root) is str and root==scope['source_input_root'] and root.startswith('/') and '..' not in root.split('/'),'FIXED_SOURCE_ROOT');held=[]
 try:
  raws={n:read_source(root+'/'+n,hashes[n],held) for n in sorted(NAMES)}
  with Capsule(raws,hashes):
   module=__import__(PACKAGE+'.manager_native_evidence',fromlist=['execute']);return module.execute(scope_raw,record_raw,scope_sha,record_sha,raws)
 finally:
  for fd in held:os.close(fd)
def manager_dispatch_gate(manifest,inputs=None):
 """V2 evidence gate is versioned separately; V1 receipt/schema is never rebound."""
 from . import manager_dependency_contract as c,manager_dependency_provider as provider,manager_dependency_validate as validator,diagnostic_contract as original
 need(manifest['schema']=='HH_G2_MANAGER_RUNTIME_MANIFEST_V2' and set(manifest['source_closure_sha256'])==NAMES,'V2_RUNTIME_MANIFEST_REQUIRED')
 need(manifest['argvs']==original.argvs(1000) and manifest['environment']==original.environment(1000),'PRESERVED_MANAGER_ARGV_ENV')
 need(type(inputs) is dict and set(inputs)=={'stage','observation'} and manifest['new_manager_approval_record_sha256'] is not None,'BLOCKED_RAW_NATIVE_EVIDENCE_OR_NEW_MANAGER_APPROVAL')
 c.digest(manifest['new_manager_approval_record_sha256']);need(manifest['new_manager_approval_record_sha256'] not in c.CONSUMED,'CONSUMED_MANAGER_APPROVAL')
 stage=validator.stage_review(**inputs['stage']);observation=validator.review(**inputs['observation'])
 need(stage['status']=='PASS_ACTUAL_PRIVATE_SOURCE_AND_PENDING_SCOPE_STAGED_WITH_LIMITS' and observation['status']=='PASS_READ_ONLY_OBSERVED_WITH_LIMITS','BLOCKED_INDEPENDENT_NATIVE_EVIDENCE')
 return provider.manager_gate(manifest['validated_dependencies'])

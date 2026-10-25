"""Standalone capsule bootstrap. Entry bytes must first be externally hash-bound.

No checkout sys.path insertion. Pending arguments stop before native reads.
"""
import hashlib,importlib.abc,importlib.util,json,os,re,stat,sys,types
CAP=131072;PACKAGE='_hh_g2_frozen'
NAMES={'diagnostic_capture.py','diagnostic_contract.py','diagnostic_tools.py','diagnostic_validate.py','manager_scope_fs.py','manager_scope_contract.py','manager_scope_loader.py','manager_scope_capture.py','manager_scope_validate.py','manager_scope_bootstrap.py'}
def need(ok,why):
 if not ok:raise ValueError(why)
def load(raw):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'DUPLICATE_BOOTSTRAP_KEY');d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs)
def initial(path,digest,mode,pins):
 need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None,'BLOCKED_PENDING_REVIEW')
 fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC);pins.append(fd);before=os.fstat(fd)
 need(stat.S_ISREG(before.st_mode) and before.st_uid==1000 and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==mode and 0<before.st_size<=CAP,'BOOTSTRAP_INSTANCE')
 raw=bytearray()
 while True:
  b=os.read(fd,min(65536,CAP+1-len(raw)))
  if not b:break
  raw.extend(b);need(len(raw)<=CAP,'BOOTSTRAP_BOUND')
 after=os.fstat(fd);need(all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink')),'BOOTSTRAP_READ_DRIFT')
 need(hashlib.sha256(raw).hexdigest()==digest,'BOOTSTRAP_HASH');return bytes(raw),{'st_dev':before.st_dev,'st_ino':before.st_ino,'st_mtime_ns':before.st_mtime_ns,'st_ctime_ns':before.st_ctime_ns}
class Capsule(importlib.abc.MetaPathFinder,importlib.abc.Loader):
 def __init__(self,raws,root):
  need(set(raws)==NAMES,'EXACT_FROZEN_CLOSURE');self.codes={n:compile(b,root+'/'+n,'exec',dont_inherit=True) for n,b in raws.items()};self.root=root
 def find_spec(self,fullname,path=None,target=None):
  if not fullname.startswith(PACKAGE+'.'):return None
  name=fullname[len(PACKAGE)+1:]+'.py';need(name in self.codes,'CAPSULE_IMPORT_CLOSURE')
  return importlib.util.spec_from_loader(fullname,self,origin=self.root+'/'+name)
 def create_module(self,spec):return None
 def exec_module(self,module):
  name=module.__name__.split('.')[-1]+'.py';module.__file__=self.root+'/'+name;exec(self.codes[name],module.__dict__)
 def __enter__(self):
  need(not any(n==PACKAGE or n.startswith(PACKAGE+'.') for n in sys.modules),'PRELOADED_CAPSULE_REJECTED')
  package=types.ModuleType(PACKAGE);package.__path__=[];sys.modules[PACKAGE]=package;sys.meta_path.insert(0,self);return self
 def __exit__(self,*args):
  sys.meta_path.remove(self)
  for name in list(sys.modules):
   if name==PACKAGE or name.startswith(PACKAGE+'.'):del sys.modules[name]
def launch(manifest_path,scope_path,approval_path,manifest_sha,scope_sha,approval_sha):
 for h in (manifest_sha,scope_sha,approval_sha):need(type(h) is str and re.fullmatch('[0-9a-f]{64}',h) is not None,'BLOCKED_PENDING_REVIEW')
 need(approval_sha not in ('0e76645d07be2eb646f2cc44163b8a34db3f3ad38cfe07c42105845df37e2e02','09c7e3b9b4380d0dd40fdea6a618f997180925ae0b1ab7b3f0d7b0cc0902ca62'),'CONSUMED_VERSION_APPROVAL')
 need(type(globals().get('EXTERNAL_BOOTSTRAP_SHA256')) is str and re.fullmatch('[0-9a-f]{64}',EXTERNAL_BOOTSTRAP_SHA256) is not None,'BLOCKED_COLD_START_BINDING')
 need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and sys.version_info[:3]==(3,12,3),'ISOLATED_REVIEWED_INTERPRETER')
 need(os.getuid()==os.geteuid()==os.getgid()==os.getegid()==1000,'NONROOT_UID_GID')
 need(not any(n==PACKAGE or n.startswith(PACKAGE+'.') for n in sys.modules),'NO_PRELOADED_CAPSULE')
 pins=[]
 try:
  manifest_raw,manifest_id=initial(manifest_path,manifest_sha,0o600,pins);m=load(manifest_raw);root=m['source_store']['path']
  need(set(m['source_closure_sha256'])==NAMES and m['source_closure_sha256']['manager_scope_bootstrap.py']==EXTERNAL_BOOTSTRAP_SHA256,'COLD_START_SOURCE_MANIFEST_BINDING')
  scope_raw,scope_id=initial(scope_path,scope_sha,0o600,pins);approval_raw,approval_id=initial(approval_path,approval_sha,0o600,pins)
  raws={};ids={}
  for name,h in m['source_closure_sha256'].items():
   need(re.fullmatch(r'[a-z_]+\.py',name) is not None,'SOURCE_FILENAME');raws[name],ids[name]=initial(root+'/'+name,h,0o400,pins)
  with Capsule(raws,root):
   module=__import__(PACKAGE+'.manager_scope_capture',fromlist=['run'])
   return module.run(manifest_raw,scope_raw,approval_raw,manifest_sha,scope_sha,approval_sha,{'runtime_manifest.json':manifest_id,'scope.json':scope_id,'approval.json':approval_id},ids)
 finally:
  for fd in pins:os.close(fd)
def main(argv=None):
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False)
 for name in ('manifest','scope','approval','manifest-sha256','scope-sha256','approval-sha256'):p.add_argument('--'+name)
 a=p.parse_args(argv)
 try:
  result=launch(a.manifest,a.scope,a.approval,a.manifest_sha256,a.scope_sha256,a.approval_sha256);print(json.dumps(result));return 0 if result['status']=='CAPTURED_UNATTESTED_READ_ONLY_SECURITY_BOUND' else 2
 except (OSError,ValueError,KeyError,TypeError):print('{"status":"BLOCKED_MANAGER_SECURITY_OR_AUTHORIZATION","automatic_retry":false}');return 2
if __name__=='__main__':raise SystemExit(main())

"""Compile only approved pinned bytes; never fall back to a checkout import path."""
import os,stat,sys
from . import manager_scope_fs as fs,manager_scope_contract as c
PACKAGE='_hh_g2_frozen'
def pin_sources(store,hashes):
 c.need(isinstance(store,fs.Store) and set(hashes)==c.CLOSURE,'SECURE_SOURCE_STORE')
 pins=[]
 try:
  for name in sorted(hashes):pins.append(store.pin(name,hashes[name],0o400))
  return pins,{p.name:p.raw for p in pins}
 except BaseException:
  for p in pins:p.close()
  raise
def stage_sources(store,raws,hashes):
 c.need(isinstance(store,fs.Store) and set(raws)==set(hashes)==c.CLOSURE,'STAGE_MINIMUM_CLOSURE_ONLY')
 c.need(all(type(raws[n]) is bytes and fs.sha(raws[n])==hashes[n] for n in hashes),'STAGE_INPUT_SHA256')
 pins=[]
 try:
  for n in sorted(raws):pins.append(store.write_new(n,raws[n],0o400))
  return {'status':'STAGED_REVIEWED_BYTES_SOURCE_ONLY','files':len(pins),'source_store':store.proof(),'no_project_move':True}
 finally:
  for p in pins:p.close()
def dependency_check(manifest):
 """A fixed external allowlist is necessary, not an automatic whole-host closure proof."""
 deps=manifest['dependencies'];c.need(deps['status']=='EXTERNALLY_REVIEWED_FIXED_CLOSURE','BLOCKED_DEPENDENCY_CLOSURE')
 files={row['path']:row for row in deps['files']};checked={}
 for path,row in files.items():
  c.need(path.startswith(('/usr/','/lib/','/lib64/')) and '..' not in path.split('/'),'DEPENDENCY_PATH')
  # Only resolved regular paths are allowed: aliases need an independently reviewed entry.
  parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
  try:
   for component in path.split('/')[1:-1]:
    nxt=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);os.close(parent);parent=nxt
    s=os.fstat(parent);c.need(s.st_uid==0 and not s.st_mode&0o022,'DEPENDENCY_PARENT')
   fd=os.open(path.split('/')[-1],os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
   try:
    s=os.fstat(fd);c.need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o6022 and s.st_nlink==1 and s.st_size<=64*1024**2,'ROOT_DEPENDENCY_INSTANCE')
    fs.no_acl(fd,False);raw=fs.bounded_fd(fd,64*1024**2);c.need(fs.sha(raw)==row['sha256'] and fs.same(s,os.fstat(fd)),'DEPENDENCY_DRIFT');checked[path]=row['sha256']
   finally:os.close(fd)
  finally:os.close(parent)
 for name,expected in deps['required_import_origins'].items():
  module=sys.modules.get(name);c.need(module is not None,'REQUIRED_RUNTIME_IMPORT_NOT_LOADED')
  origin=getattr(getattr(module,'__spec__',None),'origin',None)
  if expected in ('built-in','frozen'):c.need(origin==expected,'FROZEN_RUNTIME_ORIGIN')
  else:c.need(origin==expected and expected in checked,'RUNTIME_IMPORT_ORIGIN_NOT_BOUND')
 # Unknown loaded file modules cannot be implicitly trusted after capsule imports.
 for name,module in list(sys.modules.items()):
  if name==PACKAGE or name.startswith(PACKAGE+'.'):continue
  origin=getattr(getattr(module,'__spec__',None),'origin',None)
  if origin not in (None,'built-in','frozen'):c.need(origin in checked,'UNLISTED_LOADED_MODULE')
 actual=os.stat('/proc/self/exe');expected=os.stat('/usr/bin/python3.12')
 c.need((actual.st_dev,actual.st_ino)==(expected.st_dev,expected.st_ino) and checked.get('/usr/bin/python3.12')==c.TOOLS['/usr/bin/python3'],'RUNNING_INTERPRETER_INSTANCE')
 return {'status':'FIXED_EXTERNAL_ALLOWLIST_MATCHED_WITH_LIMITS','file_count':len(checked),'host_attestation':False,'automatic_dependency_discovery':False,'transitive_mapping_attested':False}

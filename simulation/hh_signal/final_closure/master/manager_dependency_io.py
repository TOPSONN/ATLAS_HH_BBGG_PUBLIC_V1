"""Reviewed aliases are explicit data; every other symlink is rejected."""
import os,stat
from . import manager_dependency_contract as c,manager_scope_fs as fs
class AliasPin:
 def __init__(self,path,aliases,expected_sha=None,owner=0):
  c.path(path);c.need(type(aliases) is dict and len(aliases)<=c.MAX_ALIASES,'ALIAS_ALLOWLIST_BOUND');self.fds=[];self.lookups=[];self.aliases=[];self.owner=owner;self.fd=None;self.requested=path;self.namespace=os.stat('/proc/self/ns/mnt').st_ino
  if expected_sha is not None:c.digest(expected_sha)
  pending=path.split('/')[1:];current=[];hops=0
  try:
   root=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);self.fds.append(root);parent=root;s=os.fstat(root);c.need(s.st_uid==0 and not s.st_mode&0o022,'ROOT_ANCESTOR_MODE');fs.no_acl(root,True);self.lookups.append((None,None,root,fs.ident(s)))
   while pending:
    component=pending.pop(0);p='/'+'/'.join(current+[component]);before=os.stat(component,dir_fd=parent,follow_symlinks=False)
    if stat.S_ISLNK(before.st_mode):
     hops+=1;c.need(hops<=c.MAX_ALIASES and p in aliases,'UNREVIEWED_SYMLINK');link=os.open(component,os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);self.fds.append(link);c.need(fs.same(before,os.fstat(link)) and before.st_uid==0,'ALIAS_INSTANCE_OR_OWNER')
     target=os.readlink('',dir_fd=link);c.need(target==aliases[p],'ALIAS_TARGET_SUBSTITUTION');self.lookups.append((parent,component,link,fs.ident(before)));self.aliases.append({'path':p,'target':target,'identity':fs.ident(before)})
     pending=c.alias_target(p,target).split('/')[1:]+pending;parent=root;current=[];continue
    flags=os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC
    if pending:flags|=os.O_DIRECTORY
    fd=os.open(component,flags,dir_fd=parent);self.fds.append(fd);s=os.fstat(fd);c.need(fs.same(before,s),'ALIAS_OPEN_INSTANCE_RACE');self.lookups.append((parent,component,fd,fs.ident(s)))
    c.need(s.st_uid==owner and not s.st_mode&0o6022,'DEPENDENCY_OWNER_OR_WRITABLE_MODE');fs.no_acl(fd,bool(pending))
    if pending:c.need(stat.S_ISDIR(s.st_mode),'DEPENDENCY_ANCESTOR_TYPE');parent=fd;current.append(component)
    else:
     c.need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=c.FILE_CAP,'DEPENDENCY_FILE_TYPE_LINK_SIZE');self.fd=fd;self.physical='/'+'/'.join(current+[component]);self.raw=fs.bounded_fd(fd,c.FILE_CAP)
   c.need(self.fd is not None,'DEPENDENCY_FINAL_FILE');self.digest=c.sha(self.raw)
   if expected_sha is not None:c.need(self.digest==expected_sha,'DEPENDENCY_HASH_DRIFT')
   self.verify()
  except BaseException:self.close();raise
 def verify(self):
  c.need(os.stat('/proc/self/ns/mnt').st_ino==self.namespace,'DEPENDENCY_MOUNT_NAMESPACE_DRIFT')
  for parent,name,fd,identity in self.lookups:
   s=os.fstat(fd);c.need(fs.ident(s)==identity,'DEPENDENCY_INSTANCE_DRIFT')
   if parent is not None:c.need(fs.ident(os.stat(name,dir_fd=parent,follow_symlinks=False))==identity,'DEPENDENCY_PATH_REPLACEMENT')
   if not stat.S_ISLNK(s.st_mode):fs.no_acl(fd,stat.S_ISDIR(s.st_mode))
  os.lseek(self.fd,0,os.SEEK_SET);c.need(fs.bounded_fd(self.fd,c.FILE_CAP)==self.raw,'DEPENDENCY_SAME_FD_BYTES_DRIFT');return True
 def proof(self):
  self.verify();s=os.fstat(self.fd);identity=fs.ident(s);identity.update(device_major=os.major(s.st_dev),device_minor=os.minor(s.st_dev))
  return {'requested':self.requested,'physical':self.physical,'sha256':self.digest,'identity':identity,'aliases':self.aliases,'ancestor_instances':[{'identity':i,'type':'SYMLINK' if stat.S_ISLNK(i['st_mode']) else 'DIRECTORY' if stat.S_ISDIR(i['st_mode']) else 'FILE'} for _,_,_,i in self.lookups],'acl':'ABSENT_BY_SAME_FD','mount_namespace_inode':self.namespace,'bytes_equality_rechecked':True}
 def close(self):
  for fd in reversed(self.fds):os.close(fd)
  self.fds=[];self.fd=None
def alias_observation(path):
 """Exact fixed-link metadata only: do not follow an unapproved target."""
 c.path(path);parent_path,name=path.rsplit('/',1);parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);held=[parent]
 try:
  s=os.fstat(parent);c.need(s.st_uid==0 and not s.st_mode&0o022,'ALIAS_ROOT_ANCESTOR');fs.no_acl(parent,True)
  for part in parent_path.split('/')[1:]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);held.append(fd);s=os.fstat(fd);c.need(s.st_uid==0 and not s.st_mode&0o022,'ALIAS_PARENT_MODE');fs.no_acl(fd,True);parent=fd
  fd=os.open(name,os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);held.append(fd);s=os.fstat(fd);c.need(stat.S_ISLNK(s.st_mode) and s.st_uid==0 and 0<s.st_size<=512,'ALIAS_TYPE_OWNER');target=os.readlink('',dir_fd=fd);c.need(fs.same(s,os.stat(name,dir_fd=parent,follow_symlinks=False)),'ALIAS_METADATA_RACE')
  return {'path':path,'target':target,'identity':fs.ident(s),'target_followed':False}
 finally:
  for fd in reversed(held):os.close(fd)

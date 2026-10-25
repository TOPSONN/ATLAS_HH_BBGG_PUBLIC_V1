"""Linux-native descriptor bindings. Never chmod, mount, install, or run a child."""
import ctypes,errno,hashlib,os,re,stat,sys
def need(ok,why):
 if not ok:raise ValueError(why)
sha=lambda b:hashlib.sha256(b).hexdigest()
CAP=131072
def ident(s):return {k:getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')}
def same(a,b):return ident(a)==ident(b)
def bounded_fd(fd,cap=CAP):
 out=bytearray()
 while True:
  chunk=os.read(fd,min(65536,cap+1-len(out)))
  if not chunk:break
  out.extend(chunk);need(len(out)<=cap,'BOUNDED_FD_READ')
 return bytes(out)
def no_acl(fd,is_dir):
 need(hasattr(os,'getxattr'),'UNKNOWN_POSIX_ACL_API')
 for name in ('system.posix_acl_access','system.posix_acl_default') if is_dir else ('system.posix_acl_access',):
  try:value=os.getxattr(fd,name)
  except OSError as e:
   need(e.errno==getattr(errno,'ENODATA',None),'UNKNOWN_POSIX_ACL_SUPPORT');continue
  need(not value,'EXTENDED_OR_INHERITED_ACL_REJECTED')
def checked_stat(s,uid,directory=False,private=True,mode=None,allow_empty=False):
 need((stat.S_ISDIR if directory else stat.S_ISREG)(s.st_mode),'FILE_TYPE')
 need(s.st_uid==uid if private else s.st_uid in (0,uid),'OWNER')
 need(not s.st_mode&0o6022,'UNSAFE_WRITABLE_OR_SPECIAL_MODE')
 if mode is not None:need(stat.S_IMODE(s.st_mode)==mode,'EXACT_PRIVATE_MODE')
 if not directory:need(s.st_nlink==1 and (0 if allow_empty else 1)<=s.st_size<=CAP,'HARDLINK_OR_SIZE')
def read_proc(path,cap):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:return bounded_fd(fd,cap)
 finally:os.close(fd)
def classify(magic,name):
 if magic==0xef53 and name=='ext4':return 'LINUX_NATIVE_FILESYSTEM_CONFIRMED'
 if name in ('9p','drvfs','cifs','smb3','ntfs','fuseblk'):return 'DRVFS_OR_WINDOWS_BACKED'
 return 'UNKNOWN_FILESYSTEM'
def fs_identity(fd):
 need(sys.platform=='linux' and ctypes.sizeof(ctypes.c_long)==8,'UNKNOWN_NATIVE_STATFS_ABI')
 need(os.uname().machine=='x86_64','UNKNOWN_NATIVE_STATFS_MACHINE')
 class StatFS(ctypes.Structure):
  _fields_=[('kind',ctypes.c_long),('block_size',ctypes.c_long),('blocks',ctypes.c_ulong*5),('fsid',ctypes.c_int*2),('name_length',ctypes.c_long),('fragment_size',ctypes.c_long),('flags',ctypes.c_long),('spare',ctypes.c_long*4)]
 need(ctypes.sizeof(StatFS)==120,'UNKNOWN_NATIVE_STATFS_LAYOUT')
 libc=ctypes.CDLL(None,use_errno=True);value=StatFS();call=libc.fstatfs;call.argtypes=[ctypes.c_int,ctypes.POINTER(StatFS)];call.restype=ctypes.c_int
 need(call(fd,ctypes.byref(value))==0,'UNKNOWN_FSTATFS')
 info=read_proc('/proc/self/fdinfo/'+str(fd),8192).decode('ascii');matches=re.findall(r'^mnt_id:\s*([0-9]+)$',info,re.M);need(len(matches)==1,'FD_MOUNT_ID')
 mount_id=int(matches[0]);rows=[]
 for line in read_proc('/proc/self/mountinfo',65536).decode('ascii').splitlines():
  fields=line.split();split=fields.index('-') if '-' in fields else -1
  if fields and fields[0]==str(mount_id):
   need(split>=6 and len(fields)>=split+4,'MOUNTINFO_FORMAT');rows.append((fields,split))
 need(len(rows)==1,'EXACT_MOUNT_ID');fields,split=rows[0];s=os.fstat(fd)
 need(fields[2]==str(os.major(s.st_dev))+':'+str(os.minor(s.st_dev)),'MOUNT_DEVICE_BINDING')
 return {'classification':classify(value.kind,fields[split+1]),'fs_type':fields[split+1],'fs_magic':value.kind,'fsid':''.join('%08x'%(n&0xffffffff) for n in value.fsid),'mount_id':mount_id,'device':s.st_dev,'mount_root':fields[3],'mount_namespace_inode':os.stat('/proc/self/ns/mnt').st_ino}
def check_fs(actual,expected):
 need(type(expected) is dict and expected.get('classification')=='LINUX_NATIVE_FILESYSTEM_CONFIRMED','UNKNOWN_APPROVED_FILESYSTEM_IDENTITY')
 for key in ('fs_magic','mount_id','device','mount_namespace_inode'):need(type(expected.get(key)) is int and expected[key]>0,'FILESYSTEM_NUMERIC_IDENTITY')
 need(type(expected.get('fsid')) is str and re.fullmatch('[0-9a-f]{16}',expected['fsid']) is not None,'FILESYSTEM_ID_REQUIRED')
 need(actual==expected and actual['classification']=='LINUX_NATIVE_FILESYSTEM_CONFIRMED','FILESYSTEM_OR_MOUNT_SUBSTITUTION')
class Pinned:
 def __init__(self,store,name,fd,raw,started):self.store=store;self.name=name;self.fd=fd;self.raw=raw;self.started=started
 def verify(self):
  self.store.verify();current=os.fstat(self.fd);look=os.stat(self.name,dir_fd=self.store.fd,follow_symlinks=False)
  need(same(self.started,current) and same(current,look),'FILE_REPLACEMENT_OR_MUTATION')
  lookup_fd=os.open(self.name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=self.store.fd)
  try:need(fs_identity(lookup_fd)==fs_identity(self.fd),'FILE_MOUNT_SUBSTITUTION')
  finally:os.close(lookup_fd)
  no_acl(self.fd,False)
  os.lseek(self.fd,0,os.SEEK_SET);need(bounded_fd(self.fd)==self.raw,'SAME_FD_CONTENT_DRIFT')
  need(same(current,os.fstat(self.fd)),'POST_READ_IDENTITY_CHANGE');return True
 def close(self):
  if self.fd is not None:os.close(self.fd);self.fd=None
class Store:
 def __init__(self,path,policy,private=True):
  need(sys.platform=='linux','LINUX_NATIVE_ONLY');need(type(policy) is dict and type(policy.get('uid')) is int and policy['uid']>0,'EXPECTED_UID')
  need(type(policy.get('filesystem')) is dict and type(policy.get('directory_identity')) is dict,'UNKNOWN_APPROVED_STORAGE')
  need(set(policy['directory_identity'])=={'st_dev','st_ino','st_uid'} and all(type(v) is int and v>=0 for v in policy['directory_identity'].values()),'DIRECTORY_NUMERIC_IDENTITY')
  need(type(path) is str and path.startswith('/') and path!='/' and all(p not in ('','.','..') for p in path.split('/')[1:]),'ABSOLUTE_COMPONENT_PATH')
  self.path=path;self.policy=policy;self.chain=[];self.private=private;self.fd=None
  root=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);self.chain.append((None,None,root,os.fstat(root)))
  try:
   checked_stat(os.fstat(root),policy['uid'],True,False);no_acl(root,True)
   for name in path.split('/')[1:]:
    parent=self.chain[-1][2];fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);s=os.fstat(fd);self.chain.append((parent,name,fd,s))
    checked_stat(s,policy['uid'],True,False);no_acl(fd,True)
   self.fd=self.chain[-1][2];s=os.fstat(self.fd);checked_stat(s,policy['uid'],True,private,0o700 if private else None)
   need({k:getattr(s,k) for k in ('st_dev','st_ino','st_uid')}==policy['directory_identity'],'DIRECTORY_INSTANCE_BINDING')
   check_fs(fs_identity(self.fd),policy['filesystem']);self.verify()
  except BaseException:self.close();raise
 def verify(self):
  need(self.fd is not None,'CLOSED_DIRECTORY')
  for parent,name,fd,before in self.chain:
   now=os.fstat(fd);need((before.st_dev,before.st_ino,before.st_uid,stat.S_IMODE(before.st_mode))==(now.st_dev,now.st_ino,now.st_uid,stat.S_IMODE(now.st_mode)),'ANCESTOR_INSTANCE_OR_MODE_DRIFT')
   checked_stat(now,self.policy['uid'],True,False);no_acl(fd,True)
   if parent is not None:
    look=os.stat(name,dir_fd=parent,follow_symlinks=False);need((look.st_dev,look.st_ino)==(now.st_dev,now.st_ino) and stat.S_ISDIR(look.st_mode),'ANCESTOR_PATH_SUBSTITUTION')
    lookup_fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
    try:need(fs_identity(lookup_fd)==fs_identity(fd),'ANCESTOR_MOUNT_SUBSTITUTION')
    finally:os.close(lookup_fd)
  checked_stat(os.fstat(self.fd),self.policy['uid'],True,self.private,0o700 if self.private else None)
  check_fs(fs_identity(self.fd),self.policy['filesystem']);return True
 def pin(self,name,digest,mode=0o600):
  need(type(name) is str and re.fullmatch('[A-Za-z0-9_.-]{1,100}',name) is not None and name not in ('.','..'),'SINGLE_COMPONENT')
  self.verify();fd=os.open(name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=self.fd)
  try:
   before=os.fstat(fd);checked_stat(before,self.policy['uid'],mode=mode);no_acl(fd,False)
   need(before.st_dev==os.fstat(self.fd).st_dev,'FILE_DEVICE_SUBSTITUTION');check_fs(fs_identity(fd),self.policy['filesystem'])
   raw=bounded_fd(fd);need(sha(raw)==digest,'ORIGINAL_BYTE_SHA256');p= Pinned(self,name,fd,raw,before);p.verify();return p
  except BaseException:os.close(fd);raise
 def write_new(self,name,raw,mode=0o600):
  need(type(raw) is bytes and 0<len(raw)<=CAP and mode in (0o400,0o600),'CREATE_BOUND_OR_MODE')
  need(re.fullmatch('[A-Za-z0-9_.-]{1,100}',name) is not None and name not in ('.','..'),'SINGLE_COMPONENT');self.verify()
  fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,mode,dir_fd=self.fd)
  try:
   checked_stat(os.fstat(fd),self.policy['uid'],mode=mode,allow_empty=True);no_acl(fd,False);view=memoryview(raw)
   while view:
    written=os.write(fd,view);need(type(written) is int and 0<written<=len(view),'WRITE_NO_PROGRESS_OR_INVALID_COUNT');view=view[written:]
   os.fsync(fd)
  finally:os.close(fd)
  os.fsync(self.fd);return self.pin(name,sha(raw),mode)
 def proof(self):
  self.verify();return {'filesystem':fs_identity(self.fd),'directory_identity':self.policy['directory_identity'],'mode':stat.S_IMODE(os.fstat(self.fd).st_mode),'posix_acl':'ABSENT_CONFIRMED_BY_FD_XATTR','ancestors_bound':len(self.chain),'host_admin_excluded':False}
 def close(self):
  for _,_,fd,_ in reversed(self.chain):os.close(fd)
  self.chain=[];self.fd=None
def create_private(parent,name):
 need(isinstance(parent,Store) and not parent.private and re.fullmatch('[A-Za-z0-9_-]{1,80}',name) is not None,'APPROVED_PARENT_AND_NAME');parent.verify()
 os.mkdir(name,0o700,dir_fd=parent.fd);fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent.fd)
 try:
  s=os.fstat(fd);checked_stat(s,parent.policy['uid'],True,True,0o700);no_acl(fd,True);check_fs(fs_identity(fd),parent.policy['filesystem']);os.fsync(parent.fd)
  policy={'uid':parent.policy['uid'],'filesystem':parent.policy['filesystem'],'directory_identity':{k:getattr(s,k) for k in ('st_dev','st_ino','st_uid')}}
 finally:os.close(fd)
 return Store(parent.path+'/'+name,policy)

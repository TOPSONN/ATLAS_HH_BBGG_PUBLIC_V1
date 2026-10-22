"""Hash-only bootstrap: no subprocess, bus, proc/sys query or output file."""
import hashlib,json,os,stat,sys
from pathlib import Path
TOOLS=('/usr/bin/systemctl','/usr/bin/python3','/usr/bin/timeout')
MAX_BINARY=64*1024*1024
def identity(path):
 p=Path(path);chain=[]
 for _ in range(8):
  s=p.lstat()
  if not stat.S_ISLNK(s.st_mode):break
  if s.st_uid!=0:raise ValueError('LINK_OWNER')
  target=os.readlink(p);chain.append({'path':str(p),'target':target,'uid':s.st_uid,'mode':stat.S_IMODE(s.st_mode)})
  p=(p.parent/target if not target.startswith('/') else Path(target)).absolute()
 else:raise ValueError('LINK_DEPTH')
 p=p.resolve(strict=True)
 if not str(p).startswith(('/usr/bin/','/bin/')):raise ValueError('TOOL_LOCATION')
 for parent in p.parents:
  s=parent.stat()
  if s.st_uid!=0 or s.st_mode&0o022:raise ValueError('TOOL_PARENT')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  before=os.fstat(fd)
  if not stat.S_ISREG(before.st_mode) or before.st_uid!=0 or before.st_mode&0o6022 or not before.st_mode&0o111 or not 0<before.st_size<=MAX_BINARY:raise ValueError('UNSAFE_ELF')
  h=hashlib.sha256();size=0;header=b''
  while True:
   b=os.read(fd,1024*1024)
   if not b:break
   if not header:header=b[:20]
   size+=len(b)
   if size>MAX_BINARY:raise ValueError('BINARY_BOUND')
   h.update(b)
  after=os.fstat(fd)
  fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
  if any(getattr(before,n)!=getattr(after,n) for n in fields) or size!=before.st_size or header[:4]!=b'\x7fELF':raise ValueError('BINARY_DRIFT_OR_TYPE')
  if Path(path).resolve(strict=True)!=p:raise ValueError('LINK_DRIFT')
  return {'path':path,'resolved':str(p),'sha256':h.hexdigest(),'bytes':size,'uid':before.st_uid,'gid':before.st_gid,
   'mode':stat.S_IMODE(before.st_mode),'elf_class':header[4],'elf_machine':int.from_bytes(header[18:20],'little'),'links':chain}
 finally:os.close(fd)
def probe():
 if sys.platform!='linux' or os.getuid()==0 or os.getuid()!=os.geteuid() or os.getgid()!=os.getegid():raise ValueError('EXISTING_NONROOT_LINUX_REQUIRED')
 v={'schema':'HH_G2_TOOL_OBSERVATION_V1','status':'HASH_ONLY_OBSERVED_NOT_ATTESTED','uid':os.getuid(),'gid':os.getgid(),
  'python_version':list(sys.version_info[:3]),'tools':[identity(p) for p in TOOLS],
  'executed_other_tools':0,'bus_queries':0,'kernel_inventory_queries':0,'execution_authorized':False}
 if Path(sys.executable).resolve()!=Path('/usr/bin/python3').resolve():raise ValueError('INTERPRETER_IDENTITY')
 a=os.stat('/proc/self/exe');b=os.stat('/usr/bin/python3')
 if (a.st_dev,a.st_ino)!=(b.st_dev,b.st_ino):raise ValueError('RUNNING_INTERPRETER_REPLACED')
 return v
if __name__=='__main__':
 try:print(json.dumps(probe(),sort_keys=True))
 except (OSError,ValueError) as e:print(json.dumps({'status':'BLOCKED_TOOL_IDENTITY','reason':str(e)[:160]}));raise SystemExit(2)

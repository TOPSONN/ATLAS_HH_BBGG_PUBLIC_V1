"""PROPOSED read-only Linux collector; run only in a separately allowed session.

No subprocess, device open, ioctl, service call, startup or configuration write.
V1 remains unchanged. V2 replaces silently sliced relations with whole-set failure,
anchors boot/cgroup/mount namespace twice, and records ownership on pinned reads.
"""
import argparse,hashlib,json,os,platform,posixpath,stat,sys,time,uuid
from pathlib import Path
from ..resource_closure.g1_guest_inventory import FILES,CGFILES

MAX=262144;PAYLOAD=196608;ROW_MAX=768
CG=tuple(dict.fromkeys((*CGFILES,'memory.events','cgroup.procs')))

def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)

def bounded_names(path,maximum):
 """Never return a truncated relation set. No unbounded listdir materialization."""
 values=[]
 with os.scandir(path) as entries:
  for e in entries:
   need(len(values)<maximum,'ENUMERATION_BOUND');values.append(e.name)
 return sorted(values)

class Reader:
 def __init__(self):self.rows=[];self.used=0
 def read(self,path,limit=8192):
  need(len(self.rows)<ROW_MAX,'ROW_BOUND')
  row={'path':str(path),'status':'UNKNOWN'};self.rows.append(row)
  try:
   need(sys.platform=='linux','LINUX_READ_INTERFACE_NOT_EXECUTED')
   need(self.used+limit<=PAYLOAD,'AGGREGATE_RETAINED_BYTE_BOUND')
   pin=os.open(path,os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC)
   try:
    before=os.fstat(pin);need(stat.S_ISREG(before.st_mode),'NONREGULAR_REJECTED')
    fd=os.open('/proc/self/fd/'+str(pin),os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as stream:
     after=os.fstat(stream.fileno());need((before.st_dev,before.st_ino)==(after.st_dev,after.st_ino),'INPUT_INSTANCE_CHANGED')
     raw=stream.read(limit+1)
   finally:os.close(pin)
   need(len(raw)<=limit,'FILE_BYTE_BOUND');text=raw.decode('utf-8');self.used+=len(raw)
   row.update(status='REPORTED_UNATTESTED',text=text,sha256=sha(raw),uid=before.st_uid,
    mode=stat.S_IMODE(before.st_mode),dev=before.st_dev,inode=before.st_ino,bytes=len(raw))
   return text
  except (OSError,UnicodeError,ValueError) as e:
   row['reason']=str(e) if isinstance(e,ValueError) else type(e).__name__;return None

def anchor(reader,label):
 s=os.stat('/proc/self/ns/mnt')
 return {'label':label,'boot_id':reader.read('/proc/sys/kernel/random/boot_id',128),
  'cgroup':reader.read('/proc/self/cgroup',2048),'mount_namespace':{'dev':s.st_dev,'inode':s.st_ino},
  'pid':os.getpid(),'uid':os.getuid(),'gid':os.getgid(),'monotonic_ns':time.monotonic_ns()}

def acquire():
 need(sys.platform=='linux','EXISTING_ALLOWED_LINUX_SESSION_REQUIRED')
 need(os.getuid()!=0,'NONROOT_GUEST_REQUIRED')
 r=Reader();start=time.monotonic_ns();before=anchor(r,'before')
 for name in FILES:
  if name not in ('/proc/sys/kernel/random/boot_id','/proc/self/cgroup'):r.read(name,32768 if name.endswith('mountinfo') else 8192)
 cg=before['cgroup'];lineage=[]
 matches=[] if cg is None else [s[3:] for s in cg.splitlines() if s.startswith('0::')]
 if len(matches)==1 and matches[0].startswith('/') and posixpath.normpath(matches[0])==matches[0] and '..' not in matches[0].split('/'):
  parts=matches[0].strip('/').split('/') if matches[0]!='/' else []
  if len(parts)<=16:
   for n in range(len(parts),-1,-1):
    parent='/sys/fs/cgroup'+('/'+'/'.join(parts[:n]) if n else '');lineage.append(parent)
    for field in CG:r.read(parent+'/'+field,2048)
 block=[];by_ids=[];configs=[]
 for directory in ('/etc/systemd/journald.conf.d','/etc/rsyslog.d'):
  try:
   for name in bounded_names(directory,32):
    if name.endswith('.conf'):r.read(directory+'/'+name)
  except (OSError,ValueError) as e:configs.append({'scope':directory,'status':'UNKNOWN','reason':type(e).__name__})
 try:
  for name in bounded_names('/sys/class/block',128):
   base=Path('/sys/class/block')/name
   try:
    holders=bounded_names(base/'holders',128);slaves=bounded_names(base/'slaves',128)
    block.append({'name':name,'sysfs_path':str(base.resolve()),'holders':holders,'slaves':slaves,'relation_complete':True})
   except (OSError,ValueError) as e:
    block.append({'name':name,'relation_complete':False,'status':'UNKNOWN','reason':type(e).__name__})
   for field in ('dev','size','diskseq','partition','device/serial','device/wwid','device/model'):r.read(base/field,1024)
 except (OSError,ValueError) as e:configs.append({'scope':'BLOCK_ENUMERATION','status':'UNKNOWN','reason':type(e).__name__})
 try:by_ids=[{'name':n,'target':os.readlink('/dev/disk/by-id/'+n)} for n in bounded_names('/dev/disk/by-id',128)]
 except (OSError,ValueError) as e:configs.append({'scope':'BY_ID_ENUMERATION','status':'UNKNOWN','reason':type(e).__name__})
 metadata=[]
 for name in ('/run/systemd/system','/run/user/'+str(os.getuid())+'/bus','/run/systemd/users/'+str(os.getuid()),'/var/log/journal','/run/log/journal','/var/log/syslog'):
  try:
   s=os.lstat(name);metadata.append({'path':name,'uid':s.st_uid,'dev':s.st_dev,'inode':s.st_ino,'mode':stat.S_IMODE(s.st_mode),'is_symlink':stat.S_ISLNK(s.st_mode)})
  except OSError:metadata.append({'path':name,'status':'UNKNOWN'})
 after=anchor(r,'after')
 return {'schema':'HH_G1_GUEST_READONLY_V2','capture_id':str(uuid.uuid4()),'source_sha256':sha(Path(__file__).read_bytes()),
  'legacy_source_sha256':sha(Path(__file__).parents[1].joinpath('resource_closure/g1_guest_inventory.py').read_bytes()),
  'started_monotonic_ns':start,'ended_monotonic_ns':time.monotonic_ns(),'kernel_release':platform.release(),
  'anchor_before':before,'anchor_after':after,'cgroup_lineage':lineage,'records':r.rows,
  'block_graph':block,'by_ids':by_ids,'configuration_gaps':configs,'path_metadata':metadata,
  'manager_state_basis':'FILE_CONFIG_READBACK_ONLY_EFFECTIVE_BUS_STATE_UNKNOWN',
  'host_mapping_complete':False,'trust':'REPORTED_UNATTESTED','retained_payload_bytes':r.used,
  'whole_job_enforcement':None,'limits_kind':'LOGICAL_OUTPUT_BOUNDS_NOT_HARD_CPU_RAM_WALL'}

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--output-directory',type=Path,required=True);p.add_argument('--expected-script-sha256',required=True);args=p.parse_args()
 try:
  need(sys.platform=='linux','NO_DISTRO_STARTUP_IMPLEMENTED')
  need(os.getuid()!=0,'NONROOT_GUEST_REQUIRED')
  need(sha(Path(__file__).read_bytes())==args.expected_script_sha256,'SOURCE_HASH')
  d=args.output_directory;need(d.is_absolute() and d.resolve()==d,'OUTPUT_PATH')
  st=d.lstat();need(stat.S_ISDIR(st.st_mode) and st.st_uid==os.getuid() and stat.S_IMODE(st.st_mode)==0o700,'PRIVATE_UID_0700')
  dirfd=os.open(d,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
  try:
   pinned=os.fstat(dirfd);need((st.st_dev,st.st_ino)==(pinned.st_dev,pinned.st_ino),'OUTPUT_DIRECTORY_SUBSTITUTION')
   value=acquire();raw=(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n').encode();need(len(raw)<=MAX,'CAPTURE_BYTE_BOUND')
   name='guest_'+value['capture_id']+'.json';fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=dirfd)
   with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
   fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=dirfd)
   with os.fdopen(fd,'rb') as f:need(f.read(MAX+1)==raw,'REOPEN_MISMATCH')
   os.fsync(dirfd)
  finally:os.close(dirfd)
  print(json.dumps({'status':'CAPTURED_UNATTESTED','local_receipt':str(d/name),'sha256':sha(raw),'runtime_acceptance':False}));return 0
 except (OSError,ValueError,UnicodeError):print(json.dumps({'status':'FAIL_READONLY_CAPTURE','runtime_acceptance':False}));return 2
if __name__=='__main__':raise SystemExit(main())

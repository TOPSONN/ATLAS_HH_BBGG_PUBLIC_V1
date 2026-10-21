"""Read only from an ALREADY OPEN Linux shell. Never launches WSL or services.

No subprocess, device open, ioctl, quota call, mount or configuration mutation.
File data is reported, not attested. Missing query/namespace/host links stay UNKNOWN.
"""
import argparse, hashlib, json, os, platform, posixpath, stat, sys, time, uuid
from pathlib import Path

MAX=262144
FILES=('/proc/1/comm','/proc/self/cgroup','/proc/self/mountinfo','/proc/filesystems',
 '/proc/meminfo','/proc/sys/kernel/random/boot_id','/etc/os-release',
 '/etc/systemd/journald.conf','/etc/rsyslog.conf','/etc/fstab')
CGFILES=('cpu.max','cpu.stat','memory.max','memory.current','memory.peak',
 'memory.swap.max','memory.swap.current','cgroup.controllers','cgroup.subtree_control',
 'cgroup.type','cgroup.events','pids.max')

def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 p.add_argument('--output-directory',type=Path,required=True)
 p.add_argument('--expected-script-sha256',required=True)
 a=p.parse_args()
 if sys.platform!='linux':raise ValueError('EXISTING_LINUX_SHELL_REQUIRED_NO_WSL_LAUNCH')
 source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 if a.expected_script_sha256!=source:raise ValueError('REVIEWED_SOURCE_HASH_MISMATCH')
 directory=a.output_directory
 # Require a separately prepared private directory; no mkdir before validation.
 info=directory.lstat()
 if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
  raise ValueError('PRIVATE_CURRENT_UID_0700_DIRECTORY_REQUIRED')
 # Output must resolve without any symlink ancestor.
 if directory.absolute()!=directory.resolve():raise ValueError('PRIVATE_PATH_SYMLINK')
 rows=[];used=0;begin=time.monotonic_ns()
 def read(name,limit=8192):
  nonlocal used
  if used+limit>196608:
   rows.append({'path':name,'status':'UNKNOWN','reason':'AGGREGATE_RETAINED_BYTE_BOUND'});return None
  try:
   # Pin metadata first, reject nonregular nodes before a data-open. Reopen the
   # SAME regular-file instance through procfd, not an untrusted path again.
   pin=os.open(name,os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC)
   try:
    info=os.fstat(pin)
    if not stat.S_ISREG(info.st_mode):raise ValueError('NONREGULAR_INPUT_REJECTED')
    fd=os.open('/proc/self/fd/'+str(pin),os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as stream:
     after=os.fstat(stream.fileno())
     if (after.st_dev,after.st_ino)!=(info.st_dev,info.st_ino):raise ValueError('INPUT_INSTANCE_CHANGED')
     raw=stream.read(limit+1)
   finally:os.close(pin)
   if len(raw)>limit:raise ValueError('FILE_BYTE_BOUND')
   text=raw.decode('utf-8');used+=len(raw)
   rows.append({'path':name,'status':'REPORTED_UNATTESTED','sha256':hashlib.sha256(raw).hexdigest(),'text':text})
   return text
  except (OSError,UnicodeError,ValueError) as error:
   rows.append({'path':name,'status':'UNKNOWN','reason':type(error).__name__});return None
 def namespace():
  s=os.stat('/proc/self/ns/mnt');return {'dev':s.st_dev,'inode':s.st_ino}
 ns_before=namespace()
 for name in FILES:read(name,32768 if name.endswith('mountinfo') else 8192)
 cg=next((x.get('text','') for x in rows if x['path']=='/proc/self/cgroup'),'')
 matches=[x[3:] for x in cg.splitlines() if x.startswith('0::')]
 if len(matches)==1:
  relative=matches[0]
  if relative.startswith('/') and posixpath.normpath(relative)==relative and '..' not in relative.split('/'):
   parts=relative.strip('/').split('/') if relative!='/' else []
   if len(parts)<=16:
    for length in range(len(parts),-1,-1):
     parent='/sys/fs/cgroup'+('/'+'/'.join(parts[:length]) if length else '')
     for name in CGFILES:read(parent+'/'+name,2048)
   else:rows.append({'path':'cgroup_lineage','status':'UNKNOWN','reason':'DEPTH_BOUND'})
 for base in ('/etc/systemd/journald.conf.d','/etc/rsyslog.d'):
  try:
   names=sorted(os.listdir(base))
   if len(names)>32:raise ValueError('CONFIG_FILE_COUNT_BOUND')
   for name in names:
    if name.endswith('.conf'):read(base+'/'+name,8192)
  except (OSError,ValueError) as error:rows.append({'path':base,'status':'UNKNOWN','reason':type(error).__name__})
 disks=[]
 try:
  names=sorted(os.listdir('/sys/class/block'))
  if len(names)>128:raise ValueError('BLOCK_DEVICE_COUNT_BOUND')
  for name in names:
   base=Path('/sys/class/block')/name
   disks.append({'name':name,'sysfs_path':str(base.resolve()),
    'holders':sorted(os.listdir(base/'holders'))[:129],
    'slaves':sorted(os.listdir(base/'slaves'))[:129]})
   for field in ('dev','size','diskseq','partition','device/serial','device/wwid','device/model'):
    read(str(base/field),1024)
 except (OSError,ValueError) as error:rows.append({'path':'/sys/class/block','status':'UNKNOWN','reason':type(error).__name__})
 by_ids=[]
 try:
  names=sorted(os.listdir('/dev/disk/by-id'))
  if len(names)>128:raise ValueError('BY_ID_COUNT_BOUND')
  by_ids=[{'name':n,'target':os.readlink('/dev/disk/by-id/'+n)} for n in names]
 except (OSError,ValueError) as error:rows.append({'path':'/dev/disk/by-id','status':'UNKNOWN','reason':type(error).__name__})
 metadata=[]
 for name in ('/run/systemd/system','/run/user/'+str(os.getuid())+'/bus',
              '/run/systemd/users/'+str(os.getuid()),'/var/log/journal','/run/log/journal','/var/log/syslog'):
  try:
   s=os.lstat(name);metadata.append({'path':name,'dev':s.st_dev,'inode':s.st_ino,'uid':s.st_uid,'mode':stat.S_IMODE(s.st_mode),'blocks':getattr(s,'st_blocks',None)})
  except OSError:metadata.append({'path':name,'status':'UNKNOWN'})
 ns_after=namespace()
 value={'schema':'PHASE7I_G1_GUEST_CAPTURE_V1','capture_id':str(uuid.uuid4()),'collector_sha256':source,
  'pid':os.getpid(),'uid':os.getuid(),'kernel_release':platform.release(),'machine':platform.machine(),
  'started_monotonic_ns':begin,'ended_monotonic_ns':time.monotonic_ns(),
  'namespace_before':ns_before,'namespace_after':ns_after,'namespace_consistent':ns_before==ns_after,
  'observations':rows,'block_relations':disks,'by_ids':by_ids,'path_metadata':metadata,
  'trust':'REPORTED_UNATTESTED','host_mapping_complete':False,'protected_storage_complete':False,
  'findmnt_independent_readback':'UNKNOWN_NOT_EXECUTED','user_manager_bus_health':'UNKNOWN_NOT_CONNECTED',
  'quota_enforcement':'UNKNOWN_NO_QUOTA_SYSCALL','whole_job_enforcement':'UNKNOWN_NOT_TESTED',
  'limits':'RETAINED_BYTE_AND_ENUMERATION_BOUNDS; NOT_A_KERNEL_MEMORY_OR_WALL_ENVELOPE'}
 raw=(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n').encode()
 if len(raw)>MAX:raise ValueError('CAPTURE_BYTE_BOUND')
 output=directory/('guest_'+value['capture_id']+'.json')
 fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 if output.read_bytes()!=raw:raise ValueError('CAPTURE_REOPEN_MISMATCH')
 print(json.dumps({'status':'CAPTURED_UNATTESTED_READ_ONLY','local_receipt':str(output),
  'sha256':hashlib.sha256(raw).hexdigest(),'host_mapping_complete':False,'execution_authorized':False}))

if __name__=='__main__':main()

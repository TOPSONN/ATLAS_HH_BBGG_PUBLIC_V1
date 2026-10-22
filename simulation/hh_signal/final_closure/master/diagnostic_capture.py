"""Separately authorized Linux adapter. Never called by the safe DAG or CI."""
import base64,os,selectors,signal,stat,subprocess,sys,time
from pathlib import Path
from . import diagnostic_contract as c,diagnostic_tools as tools

def read_fixed(path,cap=c.READ_CAP,dir_fd=None):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=dir_fd)
 try:
  b=os.read(fd,cap+1);c.need(len(b)<=cap,'READ_BOUND');text=b.decode('ascii')
  c.need(all(ch in '\n\t' or 32<=ord(ch)<=126 for ch in text),'READ_CONTROL_CHARACTER');return text
 finally:os.close(fd)
def start_ticks(pid):
 s=read_fixed(f'/proc/{pid}/stat',4096);return int(s[s.rfind(')')+2:].split()[19])
def snapshot():
 uid=os.getuid();gid=os.getgid();c.need(uid>0 and uid==os.geteuid() and gid==os.getegid(),'NONROOT_IDENTITY')
 status=read_fixed('/proc/self/status',8192)
 c.need('\nThreads:\t1\n' in status,'SINGLE_THREAD_REQUIRED')
 membership=read_fixed('/proc/self/cgroup');lines=membership.splitlines();c.need(len(lines)==1 and lines[0].startswith('0::/'),'UNIFIED_CGROUP_REQUIRED')
 path=lines[0][3:];c.need('..' not in path.split('/') and len(path)<=512,'CGROUP_PATH')
 mounts=read_fixed('/proc/self/mountinfo',65536).splitlines()
 matches=[x for x in mounts if len(x.split())>6 and x.split()[4]=='/sys/fs/cgroup' and ' - cgroup2 ' in x]
 c.need(len(matches)==1,'CGROUP2_MOUNT_IDENTITY')
 root=Path('/sys/fs/cgroup');p=root/path.lstrip('/');levels=[]
 while True:
  c.need(len(levels)<c.MAX_LEVELS and not p.is_symlink(),'LINEAGE_BOUND_OR_LINK')
  group_fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
  try:
   st=os.fstat(group_fd);row={'path':str(p.relative_to(root)),'device':st.st_dev,'inode':st.st_ino,'uid':st.st_uid,'gid':st.st_gid,'mode':stat.S_IMODE(st.st_mode),'fields':{}}
   for name in c.CG_FIELDS:
    try:row['fields'][name]={'status':'OBSERVED','text':read_fixed(name,dir_fd=group_fd)}
    except OSError as e:row['fields'][name]={'status':'UNKNOWN','errno':e.errno}
  finally:os.close(group_fd)
  levels.append(row)
  if p==root:break
  p=p.parent
 result={'monotonic_ns':time.monotonic_ns(),'boot_id':read_fixed('/proc/sys/kernel/random/boot_id',64).strip(),
  'uid':uid,'gid':gid,'pid':os.getpid(),'start_ticks':start_ticks(os.getpid()),'membership':path,
  'namespace_inodes':{n:os.stat('/proc/self/ns/'+n).st_ino for n in ('mnt','cgroup','pid')},
  'pid1_comm':read_fixed('/proc/1/comm',64).strip(),'pid1_start_ticks':start_ticks(1),'levels':levels}
 c.need(len(c.canonical(result))<=32768,'SNAPSHOT_RETAINED_BOUND');return result

def socket_ready(path,uid):
 try:
  p=Path(path)
  for ancestor in (p.parent,*p.parent.parents):
   s=ancestor.lstat();c.need(not stat.S_ISLNK(s.st_mode) and s.st_uid in (0,uid) and not s.st_mode&0o002,'SOCKET_PARENT')
  s=p.lstat();return stat.S_ISSOCK(s.st_mode) and s.st_uid==uid
 except OSError:return False

def child(argv,fd,env):
 """At most one pinned ELF child, 5s soft + 1s cleanup; no numeric-PID fallback."""
 c.need(sys.platform=='linux' and hasattr(os,'pidfd_open') and signal.getsignal(signal.SIGCHLD)==signal.SIG_DFL,'PIDFD_AND_DEFAULT_SIGCHLD_REQUIRED')
 began=time.monotonic_ns();p=subprocess.Popen(argv,executable=f'/proc/self/fd/{fd}',pass_fds=(fd,),env=env,
  stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True)
 identity=None;pidfd=None;sel=selectors.DefaultSelector();chunks={'stdout':bytearray(),'stderr':bytearray()};why=None;cleanup='UNKNOWN'
 try:
  identity=start_ticks(p.pid);c.need(os.getpgid(p.pid)==p.pid,'OWNED_PROCESS_GROUP')
  pidfd=os.pidfd_open(p.pid);sel.register(pidfd,selectors.EVENT_READ,'exit')
  for name,pipe in (('stdout',p.stdout),('stderr',p.stderr)):
   os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,name)
  deadline=time.monotonic()+5;open_pipes=2;exited=False
  while open_pipes and time.monotonic()<deadline and why is None:
   for key,_ in sel.select(min(.05,max(0,deadline-time.monotonic()))):
    if key.data=='exit':exited=True;sel.unregister(pidfd);continue
    data=os.read(key.fileobj.fileno(),4096)
    if not data:sel.unregister(key.fileobj);open_pipes-=1;continue
    remaining=c.PER_CHILD-sum(map(len,chunks.values()));chunks[key.data].extend(data[:remaining])
    if len(data)>remaining:why='OUTPUT_BOUND';break
   if exited and open_pipes and why is None:
    # Keep draining available data until the same fixed deadline; no new process.
    pass
  if open_pipes and why is None:why='TIMEOUT_OR_INHERITED_PIPE'
 finally:
  # Direct child remains unreaped: no poll()/wait() before this identity check.
  try:
   c.need(identity is not None and start_ticks(p.pid)==identity and os.getpgid(p.pid)==p.pid,'CHILD_IDENTITY_UNKNOWN')
   os.killpg(p.pid,signal.SIGKILL)
   p.wait(timeout=1)
   try:os.killpg(p.pid,0)
   except ProcessLookupError:cleanup='VERIFIED_GROUP_ABSENT'
  except (OSError,ValueError,subprocess.TimeoutExpired):cleanup='UNKNOWN'
  sel.close()
  if pidfd is not None:os.close(pidfd)
  p.stdout.close();p.stderr.close()
 code=p.returncode
 return {'argv':argv,'environment_sha256':c.sha(c.canonical(env)),'start_ns':began,'end_ns':time.monotonic_ns(),
  'pid':p.pid,'start_ticks':identity,'exit_code':code if code is not None and code>=0 else None,
  'exit_signal':-code if code is not None and code<0 else None,'cleanup':cleanup,'stop_reason':why,
  'stdout_b64':base64.b64encode(chunks['stdout']).decode(),'stderr_b64':base64.b64encode(chunks['stderr']).decode(),
  'stdout_bytes':len(chunks['stdout']),'stderr_bytes':len(chunks['stderr'])}

def private_output(scope):
 p=Path(scope['output']);parent=p.parent
 for item in (parent,*parent.parents):
  st=item.lstat();c.need(stat.S_ISDIR(st.st_mode) and st.st_uid in (0,scope['uid']) and not st.st_mode&0o022,'PRIVATE_PARENT_PERMISSIONS')
 parent_fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  os.mkdir(p.name,0o700,dir_fd=parent_fd)
  fd=os.open(p.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent_fd)
  st=os.fstat(fd);c.need(st.st_uid==scope['uid'] and stat.S_IMODE(st.st_mode)==0o700,'PRIVATE_DIRECTORY')
  return fd
 finally:os.close(parent_fd)
def write_private(folder,name,raw):
 c.need(name in ('attempt.json','receipt.json','receipt.sha256') and len(raw)<=c.RECEIPT_CAP,'RECEIPT_BOUND')
 fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=folder)
 try:
  remaining=memoryview(raw)
  while remaining:remaining=remaining[os.write(fd,remaining):]
  os.fsync(fd)
 finally:os.close(fd)
 os.fsync(folder)

def capture(scope):
 c.checked_scope(scope) # Unknown identity/approval stops before any live snapshot.
 c.need(sys.platform=='linux' and tuple(sys.version_info[:2])==(3,12),'REVIEWED_PYTHON312_LINUX')
 for n,digest in scope['source_sha256'].items():c.need(c.sha((Path(__file__).parent/n).read_bytes())==digest,'SOURCE_IDENTITY')
 c.need(os.getuid()==scope['uid'] and os.geteuid()==scope['uid'] and os.getgid()==scope['gid'] and os.getegid()==scope['gid'],'UID_GID_BINDING')
 observed=[tools.identity(p) for p in c.TOOLS]
 c.need(all(r['sha256']==scope['tool_sha256'][r['path']] for r in observed),'BLOCKED_TOOL_IDENTITY')
 c.need(Path(sys.executable).resolve()==Path('/usr/bin/python3').resolve(),'PYTHON_EXECUTABLE')
 current=os.stat('/proc/self/exe');expected=os.stat('/usr/bin/python3')
 c.need((current.st_dev,current.st_ino)==(expected.st_dev,expected.st_ino),'RUNNING_PYTHON_REPLACED')
 folder=private_output(scope);start=time.monotonic_ns();rows=[];before=None;after=None;failure=None
 write_private(folder,'attempt.json',c.canonical({'scope_sha256':c.sha(c.canonical(scope)),'source_revision':scope['source_revision'],'single_use_consumed':True})+b'\n')
 try:
  before=snapshot();c.need(before['pid1_comm']=='systemd','PID1_NOT_SYSTEMD')
  for i,argv in enumerate(scope['argvs']):
   c.need(time.monotonic_ns()-start<=30_000_000_000,'ADAPTER_SOFT_TIME')
   path=f'/run/user/{scope["uid"]}/systemd/private' if i==1 else '/run/dbus/system_bus_socket'
   owner=scope['uid'] if i==1 else 0
   if not socket_ready(path,owner):rows.append({'argv':argv,'skipped':'NO_EXISTING_OWNED_SOCKET'});continue
   fd=os.open('/usr/bin/systemctl',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
   try:
    h=tools.hashlib.sha256();size=0
    while True:
     block=os.read(fd,1024*1024)
     if not block:break
     size+=len(block);c.need(size<=tools.MAX_BINARY,'BINARY_BOUND');h.update(block)
    c.need(h.hexdigest()==scope['tool_sha256']['/usr/bin/systemctl'],'PINNED_TOOL_DRIFT')
    row=child(argv,fd,scope['environment']);rows.append(row)
   finally:os.close(fd)
   c.need(row['cleanup']=='VERIFIED_GROUP_ABSENT','NO_RETRY_UNKNOWN_CLEANUP')
   c.need(row['stop_reason'] is None,'STOP_ON_OUTPUT_OR_TIME_GATE')
  after=snapshot()
 except (OSError,ValueError) as e:failure=str(e)[:160]
 try:
  receipt={'schema':c.SCHEMA,'scope_sha256':c.sha(c.canonical(scope)),'source_sha256':scope['source_sha256'],
   'source_revision':scope['source_revision'],'tool_sha256':{r['path']:r['sha256'] for r in observed},
   'before':before,'queries':rows,'after':after,'failure':failure,'authorization_reference':scope['authorization_reference'],
   'start_ns':start,'end_ns':time.monotonic_ns(),'autostart_fallback':False,'hard_resource_envelope':False}
  raw=c.canonical(receipt)+b'\n';write_private(folder,'receipt.json',raw);write_private(folder,'receipt.sha256',(c.sha(raw)+'\n').encode())
  return {'status':'CAPTURED_UNATTESTED_READ_ONLY' if failure is None else 'PARTIAL_CAPTURE_STOPPED','sha256':c.sha(raw),'automatic_retry':False}
 finally:os.close(folder)

def main(argv=None):
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--scope',required=True,type=Path);a=p.parse_args(argv)
 try:
  raw=a.scope.read_bytes();v=capture(c.load(raw));print(c.canonical(v).decode());return 0 if v['status']=='CAPTURED_UNATTESTED_READ_ONLY' else 2
 except (OSError,ValueError,KeyError,TypeError):print('{"status":"BLOCKED_SOURCE_TOOL_OR_AUTHORIZATION","automatic_retry":false}');return 2
if __name__=='__main__':raise SystemExit(main())

"""Fail-closed Linux x86_64 read-only guard and fixed harmless resource fixtures.
No MG5 command, arbitrary executable dispatcher, model import or physics operation.
"""
from __future__ import annotations
import ctypes,errno,hashlib,json,os,platform,resource,signal,socket,stat,time
from pathlib import Path

LIMITS={"cpu_seconds":2,"wall_seconds":3,"address_space_bytes":536870912,"output_file_bytes":65536}
COUNTERS={"new_MG5_processes":0,"new_ME_calls":0,"new_integrals":0,
          "new_hard_events":0,"new_pythia_events":0,"new_delphes_events":0}
FIXTURES=("read_approved","write_installed_config","write_runtime_config","write_escape_symlink",
          "fork","exec","network","cpu_spin","wall_sleep","memory_overflow",
          "stdout_overflow","stderr_overflow","orphan_cleanup")
libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long
libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
libc.prctl.restype=ctypes.c_int

def require(ok,reason):
 if not ok:raise ValueError(reason)
def checked(result,name):
 if result<0:raise OSError(ctypes.get_errno(),name)
 return result
def prctl(option,arg=0):return checked(libc.prctl(option,arg,0,0,0),"prctl")
def landlock_abi():
 require(platform.system()=="Linux" and platform.machine()=="x86_64","UNSUPPORTED_KERNEL_ARCHITECTURE")
 return checked(libc.syscall(444,0,0,1),"LANDLOCK_ABI_UNAVAILABLE")
class Ruleset(ctypes.Structure):_fields_=[("handled_access_fs",ctypes.c_uint64)]
class PathRule(ctypes.Structure):_fields_=[("allowed_access",ctypes.c_uint64),("parent_fd",ctypes.c_int32)]
class Filter(ctypes.Structure):_fields_=[("code",ctypes.c_ushort),("jt",ctypes.c_ubyte),("jf",ctypes.c_ubyte),("k",ctypes.c_uint32)]
class Program(ctypes.Structure):_fields_=[("length",ctypes.c_ushort),("filters",ctypes.POINTER(Filter))]
def validated_limits(limits):
 require(set(limits)==set(LIMITS) and all(type(limits[key]) is int and limits[key]==value for key,value in LIMITS.items()),"UNREVIEWED_RESOURCE_LIMITS")
 return dict(limits)
def readonly_roots(roots):
 require(1<=len(roots)<=32,"READ_ROOT_COUNT")
 result=[]
 for value in roots:
  path=Path(value);require(path.is_absolute() and ".." not in path.parts,"UNSAFE_READ_ROOT")
  path=path.resolve(strict=True);require(str(path)!="/" and (path.is_dir() or path.is_file()),"UNSAFE_READ_ROOT")
  if path not in result:result.append(path)
 return result
def _landlock(roots):
 abi=landlock_abi();require(abi>=3,"LANDLOCK_ABI3_REQUIRED")
 handled=(1<<15)-1
 attributes=Ruleset(handled)
 ruleset=checked(libc.syscall(444,ctypes.byref(attributes),ctypes.sizeof(attributes),0),"LANDLOCK_CREATE")
 try:
  for path in roots:
   fd=os.open(str(path),os.O_PATH|os.O_CLOEXEC)
   try:
    allowed=(1<<2)|((1<<3) if path.is_dir() else 0)
    rule=PathRule(allowed,fd)
    checked(libc.syscall(445,ruleset,1,ctypes.byref(rule),0),"LANDLOCK_ADD_RULE")
   finally:os.close(fd)
  checked(libc.syscall(446,ruleset,0),"LANDLOCK_RESTRICT")
 finally:os.close(ruleset)
 return abi
def _seccomp_program():
 # seccomp_data: nr0, arch4, instruction_pointer8, args16...
 # Every unknown syscall kills the process. Writes are limited to existing fd1/2.
 LD=0x20;JEQ=0x15;JSET=0x45;RET=0x06;ALLOW=0x7fff0000;KILL=0x80000000
 rows=[(LD,0,0,4),(JEQ,1,0,0xc000003e),(RET,0,0,KILL),(LD,0,0,0)]
 plain=(0,3,4,5,6,8,9,10,11,12,13,14,15,17,19,21,24,25,28,35,39,60,63,79,89,98,99,
        102,104,107,108,110,111,118,120,158,186,202,204,219,228,230,231,262,267,269,
        271,273,274,302,318,332,334)
 for number in plain:rows.extend(((JEQ,0,1,number),(RET,0,0,ALLOW)))
 # write(fd1 or fd2) only; no writev, pwrite, sendfile, splice or io_uring.
 rows.extend(((JEQ,0,5,1),(LD,0,0,16),(JEQ,2,0,1),(JEQ,1,0,2),(RET,0,0,KILL),(RET,0,0,ALLOW)))
 # open/openat permit read-only flags; O_TMPFILE includes O_DIRECTORY bit.
 forbidden=os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_TRUNC|os.O_APPEND|0x400000
 for number,offset in ((2,24),(257,32)):
  rows.extend(((JEQ,0,4,number),(LD,0,0,offset),(JSET,0,1,forbidden),(RET,0,0,KILL),(RET,0,0,ALLOW)))
 # Only read-only terminal queries; setting termios or arbitrary device ioctls kills.
 rows.extend(((JEQ,0,6,16),(LD,0,0,24),(JEQ,3,0,0x5401),(JEQ,2,0,0x5413),
              (JEQ,1,0,0x541b),(RET,0,0,KILL),(RET,0,0,ALLOW)))
 # fcntl: F_GETFD, F_GETFL, F_GETOWN only.
 rows.extend(((JEQ,0,6,72),(LD,0,0,24),(JEQ,3,0,1),(JEQ,2,0,3),
              (JEQ,1,0,9),(RET,0,0,KILL),(RET,0,0,ALLOW)))
 rows.append((RET,0,0,KILL))
 return rows
def _seccomp():
 rows=_seccomp_program();array=(Filter*len(rows))(*(Filter(*row) for row in rows))
 program=Program(len(rows),array)
 checked(libc.prctl(22,2,ctypes.cast(ctypes.pointer(program),ctypes.c_void_p).value,0,0),"SECCOMP_INSTALL")
 return len(rows)
def install(read_roots,limits=None):
 """Irreversibly confine THIS child. Caller must preopen separate bounded logs.
 This is a guard primitive, not an authorization or a generic execution command.
 """
 limits=validated_limits(LIMITS if limits is None else limits);roots=readonly_roots(read_roots)
 logs=[os.fstat(fd) for fd in (1,2)]
 require(all(stat.S_ISREG(row.st_mode) and row.st_size<=65536 for row in logs),"PREOPENED_BOUNDED_REGULAR_LOGS_REQUIRED")
 require((logs[0].st_dev,logs[0].st_ino)!=(logs[1].st_dev,logs[1].st_ino),"SEPARATE_STDOUT_STDERR_REQUIRED")
 resource.setrlimit(resource.RLIMIT_AS,(limits["address_space_bytes"],)*2)
 resource.setrlimit(resource.RLIMIT_CPU,(limits["cpu_seconds"],)*2)
 resource.setrlimit(resource.RLIMIT_FSIZE,(65536,65536))
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
 signal.signal(signal.SIGXFSZ,signal.SIG_DFL);signal.signal(signal.SIGXCPU,signal.SIG_DFL)
 prctl(38,1) # PR_SET_NO_NEW_PRIVS
 abi=_landlock(roots);instructions=_seccomp()
 return {"landlock_ABI":abi,"landlock_readonly":True,"seccomp_default":"KILL_PROCESS",
         "seccomp_instruction_count":instructions,"no_new_privs":True,"read_roots":[str(p) for p in roots],
         "write_fds":[1,2],"fork_clone_exec_network_forbidden":True,"limits":limits}
def _record(value):
 os.write(1,(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode())
def _fixture(name,targets):
 if name=="read_approved":
  data=Path(targets["runtime_config"]).read_bytes()
  _record({"fixture_read_bytes":len(data),"fixture_read_sha256":hashlib.sha256(data).hexdigest()})
 elif name.startswith("write_"):
  key={"write_installed_config":"installed_config","write_runtime_config":"runtime_config","write_escape_symlink":"escape_symlink"}[name]
  with open(targets[key],"wb") as stream:stream.write(b"INERT_FORBIDDEN_WRITE")
 elif name=="fork":os.fork()
 elif name=="exec":os.execv("/bin/true",["/bin/true"])
 elif name=="network":
  descriptor=socket.socket(socket.AF_INET,socket.SOCK_STREAM);descriptor.close()
 elif name=="cpu_spin":
  while True:pass
 elif name=="wall_sleep":time.sleep(30)
 elif name=="memory_overflow":
  try:bytearray(1024*1024*1024)
  except MemoryError:_record({"MemoryError_contained":True});os._exit(73)
 elif name in ("stdout_overflow","stderr_overflow"):
  fd=1 if name=="stdout_overflow" else 2
  while True:os.write(fd,b"X"*4096)
 else:raise ValueError("UNREVIEWED_FIXTURE")
def _log_summary(path):
 data=path.read_bytes();records=[]
 for line in data.splitlines():
  if len(line)<=4096:
   try:value=json.loads(line)
   except (ValueError,UnicodeDecodeError):continue
   if isinstance(value,dict):records.append(value)
 return {"path":str(path),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"records":records}
def _wait_group(group,seconds=0.5):
 end=time.monotonic()+seconds;reaped=[]
 while True:
  try:pid,status,usage=os.wait4(-group,os.WNOHANG)
  except ChildProcessError:break
  if pid:reaped.append({"pid":pid,"wait_status":status,"CPU_seconds":usage.ru_utime+usage.ru_stime});continue
  if time.monotonic()>=end:break
  time.sleep(.01)
 return reaped
def execute_fixture(name,output_dir,read_roots,targets):
 """Only fixed inert fixtures; intentionally no arbitrary executable argument."""
 require(name in FIXTURES,"UNREVIEWED_FIXTURE");roots=readonly_roots(read_roots)
 output=Path(output_dir);require(output.is_absolute() and not output.exists() and not output.is_symlink(),"FRESH_FIXTURE_OUTPUT_REQUIRED")
 output.mkdir(mode=0o700);stdout=output/"stdout.log";stderr=output/"stderr.log"
 outfd=os.open(stdout,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);errfd=os.open(stderr,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 old_subreaper=ctypes.c_int()
 if name=="orphan_cleanup":
  checked(libc.prctl(37,ctypes.addressof(old_subreaper),0,0,0),"GET_SUBREAPER");prctl(36,1)
 expected_parent=os.getpid();started=time.monotonic();pid=os.fork()
 if pid==0:
  try:
   os.setsid();prctl(1,signal.SIGKILL)
   if os.getppid()!=expected_parent:os._exit(79)
   nullfd=os.open("/dev/null",os.O_RDONLY);os.dup2(nullfd,0);os.dup2(outfd,1);os.dup2(errfd,2)
   for entry in os.listdir("/proc/self/fd"):
    if int(entry)>2:
     try:os.close(int(entry))
     except OSError:pass
   if name=="orphan_cleanup":
    orphan=os.fork() # ONLY this hardcoded fixture, before installing the guard.
    if orphan==0:
     guard=install(roots);_record({"orphan_guard":guard,"orphan_pid":os.getpid()})
     while True:time.sleep(30)
    guard=install(roots);_record({"guard":guard,"orphan_pid":orphan,"pre_guard_fixture_fork_only":True});os._exit(0)
   guard=install(roots);_record({"guard":guard});_fixture(name,targets);os._exit(0)
  except BaseException as error:
   try:_record({"guard_or_fixture_error":type(error).__name__,"reason":str(error)[:300]})
   except BaseException:pass
   os._exit(78)
 os.close(outfd);os.close(errfd);timed_out=False;status=None;usage=None
 while status is None:
  child,observed,observed_usage=os.wait4(pid,os.WNOHANG)
  if child:status=observed;usage=observed_usage;break
  if time.monotonic()-started>=LIMITS["wall_seconds"]:
   timed_out=True
   try:os.killpg(pid,signal.SIGKILL)
   except ProcessLookupError:os.kill(pid,signal.SIGKILL)
   _,status,usage=os.wait4(pid,0);break
  time.sleep(.01)
 group_kill_sent=False
 try:os.killpg(pid,signal.SIGKILL);group_kill_sent=True
 except ProcessLookupError:pass
 reaped=_wait_group(pid)
 if name=="orphan_cleanup":prctl(36,old_subreaper.value)
 wall=time.monotonic()-started;logs={"stdout":_log_summary(stdout),"stderr":_log_summary(stderr)}
 records=logs["stdout"]["records"];guards=[r["guard"] for r in records if "guard" in r]
 exit_code=os.waitstatus_to_exitcode(status);death_signal=-exit_code if exit_code<0 else None
 mechanism_ok=bool(guards) and guards[0]["landlock_ABI"]>=3 and guards[0]["seccomp_default"]=="KILL_PROCESS"
 if name=="read_approved":expected=exit_code==0 and not timed_out
 elif name in ("write_installed_config","write_runtime_config","write_escape_symlink","fork","exec","network"):expected=death_signal==signal.SIGSYS and not timed_out
 elif name=="cpu_spin":expected=death_signal in (signal.SIGKILL,signal.SIGXCPU) and not timed_out and usage.ru_utime+usage.ru_stime>=1.5
 elif name=="wall_sleep":expected=timed_out and death_signal==signal.SIGKILL
 elif name=="memory_overflow":expected=exit_code==73 and any(r.get("MemoryError_contained") is True for r in records)
 elif name in ("stdout_overflow","stderr_overflow"):expected=death_signal==signal.SIGXFSZ and max(logs["stdout"]["bytes"],logs["stderr"]["bytes"])==65536
 else:
  declared={r["orphan_pid"] for r in records if "orphan_pid" in r}
  expected=exit_code==0 and group_kill_sent and len(declared)==1 and {r["pid"] for r in reaped}==declared
 require(all(logs[key]["bytes"]<=LIMITS["output_file_bytes"] for key in logs),"LOG_CAP_FAILURE")
 return {"schema_version":1,"evidence_class":"SYNTHETIC_METHOD_ONLY","fixture":name,
         "status":"PASS_EXPECTED_CONTAINMENT" if mechanism_ok and expected else "FAIL_CLOSED_FIXTURE",
         "guard_installed":mechanism_ok,"exit_code":exit_code,"signal":death_signal,"wall_watchdog_triggered":timed_out,
         "wall_seconds":wall,"CPU_seconds":usage.ru_utime+usage.ru_stime,"maxrss_KiB":usage.ru_maxrss,
         "process_group_kill_sent":group_kill_sent,"reaped_group_children":reaped,"logs":logs,
         "limits":dict(LIMITS),"max_guarded_children":1,"parser_execution_authorized":False,"new_baseline_approved":False,**COUNTERS}

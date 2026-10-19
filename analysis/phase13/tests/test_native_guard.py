"""Portable tests of the syscall policy, not actual kernel-enforcement evidence."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
PHASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("phase13_native_guard",PHASE/"source/native_guard.py")
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def evaluate(number,args=(),arch=0xc000003e):
 data={0:number,4:arch}
 for index,value in enumerate(args):data[16+8*index]=value
 pc=0;acc=0;rows=g._seccomp_program()
 for unused in range(1000):
  code,jt,jf,k=rows[pc]
  if code==0x20:acc=data.get(k,0)&0xffffffff;pc+=1
  elif code==0x15:pc+=1+(jt if acc==k else jf)
  elif code==0x45:pc+=1+(jt if acc&k else jf)
  elif code==0x06:return k
  else:raise AssertionError("unexpected BPF opcode")
 raise AssertionError("nonterminating filter")
ALLOW=0x7fff0000
KILL=0x80000000
class GuardPolicyTests(unittest.TestCase):
 def test_exact_four_field_resource_profile(self):
  self.assertEqual(g.validated_limits(g.LIMITS),{"cpu_seconds":2,"wall_seconds":3,"address_space_bytes":536870912,"output_file_bytes":65536})
 def test_resource_increase_rejected(self):
  for key in g.LIMITS:
   values=dict(g.LIMITS);values[key]+=1
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"UNREVIEWED_RESOURCE_LIMITS"):g.validated_limits(values)
 def test_boolean_resource_counter_is_rejected(self):
  values=dict(g.LIMITS);values["cpu_seconds"]=True
  with self.assertRaises(ValueError):g.validated_limits(values)
 def test_missing_extra_resource_fields_are_rejected(self):
  values=dict(g.LIMITS);values.pop("cpu_seconds")
  with self.assertRaises(ValueError):g.validated_limits(values)
  values=dict(g.LIMITS);values["workers"]=1
  with self.assertRaises(ValueError):g.validated_limits(values)
 def test_non_native_arch_and_x32_numbers_are_killed(self):
  self.assertEqual(evaluate(0,arch=0x40000003),KILL)
  self.assertEqual(evaluate(0x40000000),KILL)
 def test_unknown_syscall_default_kills(self):
  self.assertEqual(evaluate(9999),KILL)
 def test_read_only_basic_syscalls_allowed(self):
  for number in (0,3,5,8,9,11,12,17,39,60,202,228,231,262,267,318,332):
   with self.subTest(number=number):self.assertEqual(evaluate(number),ALLOW)
 def test_writes_only_preopened_stdout_stderr(self):
  self.assertEqual(evaluate(1,(1,)),ALLOW);self.assertEqual(evaluate(1,(2,)),ALLOW)
  for fd in (0,3,99):self.assertEqual(evaluate(1,(fd,)),KILL)
 def test_alternate_output_syscalls_are_killed(self):
  for number in (18,20,40,275,276,277,278,425,426,427):
   with self.subTest(number=number):self.assertEqual(evaluate(number),KILL)
 def test_readonly_open_and_openat_flags(self):
  self.assertEqual(evaluate(2,(0,os.O_RDONLY|os.O_CLOEXEC)),ALLOW)
  self.assertEqual(evaluate(257,(-100,0,os.O_RDONLY|os.O_DIRECTORY)),ALLOW)
 def test_write_create_truncate_append_flags_kill(self):
  for flags in (os.O_WRONLY,os.O_RDWR,os.O_CREAT,os.O_EXCL,os.O_TRUNC,os.O_APPEND,getattr(os,"O_TMPFILE",0x410000)):
   with self.subTest(flags=flags):
    self.assertEqual(evaluate(2,(0,flags)),KILL);self.assertEqual(evaluate(257,(-100,0,flags)),KILL)
 def test_openat2_cannot_bypass_flag_inspection(self):
  self.assertEqual(evaluate(437),KILL)
 def test_fork_clone_vfork_exec_are_killed(self):
  for number in (56,57,58,59,322,435):
   with self.subTest(number=number):self.assertEqual(evaluate(number),KILL)
 def test_network_socket_and_socketpair_are_killed(self):
  for number in (41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,288):
   with self.subTest(number=number):self.assertEqual(evaluate(number),KILL)
 def test_mutating_filesystem_calls_are_killed(self):
  for number in (76,77,82,83,84,85,86,87,88,90,91,92,93,94,133,188,189,190,197,198,199,258,259,260,263,264,265,266,268,280,316):
   with self.subTest(number=number):self.assertEqual(evaluate(number),KILL)
 def test_readonly_ioctl_queries_allowed(self):
  for operation in (0x5401,0x5413,0x541b):
   self.assertEqual(evaluate(16,(1,operation)),ALLOW)
 def test_terminal_and_device_writing_ioctl_kills(self):
  for operation in (0x5402,0x5412,0x5414,0x1234):
   self.assertEqual(evaluate(16,(1,operation)),KILL)
 def test_readonly_fcntl_allowed_and_setting_or_dup_killed(self):
  for operation in (1,3,9):self.assertEqual(evaluate(72,(1,operation)),ALLOW)
  for operation in (0,2,4,8,1030):self.assertEqual(evaluate(72,(1,operation)),KILL)
 def test_landlock_abi2_fails_closed_before_ruleset_creation(self):
  with patch.object(g,"landlock_abi",return_value=2),self.assertRaisesRegex(ValueError,"LANDLOCK_ABI3_REQUIRED"):g._landlock([])
 def test_read_roots_reject_all_filesystem_or_relative_paths(self):
  for value in ("/","relative","/tmp/../"):
   with self.subTest(value=value),self.assertRaises(ValueError):g.readonly_roots([value])
 def test_empty_or_excessive_read_roots_rejected(self):
  for values in ([],["/tmp"]*33):
   with self.assertRaises(ValueError):g.readonly_roots(values)
 def test_approved_root_is_resolved_and_deduplicated(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);link=root/"alias";link.symlink_to(root)
   self.assertEqual(g.readonly_roots([root,link]),[root.resolve()])
 def test_unknown_fixture_rejected_without_output_or_fork(self):
  with tempfile.TemporaryDirectory() as temp:
   target=Path(temp)/"new"
   with patch.object(g.os,"fork",side_effect=AssertionError("must not fork")),self.assertRaisesRegex(ValueError,"UNREVIEWED_FIXTURE"):
    g.execute_fixture("MG5",target,[Path(temp)],{})
   self.assertFalse(target.exists())
 def test_install_bad_limits_rejected_before_kernel_actions(self):
  with patch.object(g,"_landlock",side_effect=AssertionError("must not restrict")),self.assertRaises(ValueError):
   g.install([],{"cpu_seconds":100})
 def test_fixture_enum_contains_no_physics_dispatch(self):
  self.assertEqual(len(g.FIXTURES),13)
  self.assertTrue(all("mg5" not in value.lower() and "generate" not in value for value in g.FIXTURES))
  self.assertTrue(all(type(value) is int and value==0 for value in g.COUNTERS.values()))
if __name__=="__main__":unittest.main()

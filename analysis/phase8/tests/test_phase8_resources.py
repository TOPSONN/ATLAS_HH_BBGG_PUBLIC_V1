import importlib.util,json,signal,sys,tempfile,time,unittest
from pathlib import Path
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(SCRIPTS));import run_full_analysis as runner
class ResourceTests(unittest.TestCase):
 def test_contains_and_terminates_timed_process_group(self):
  old=runner.CEILINGS.copy()
  try:
   with tempfile.TemporaryDirectory() as td:
    p=Path(td);build=p/'build';build.mkdir();runner.CEILINGS.update(wall_seconds=.1,cpu_seconds=10,disk_bytes=1024*1024)
    with self.assertRaises(TimeoutError):runner.execute([sys.executable,'-c','import time; time.sleep(10)'],'inert_timeout',p,build)
    row=json.loads((p/'inert_timeout_execution.json').read_text());self.assertEqual(row['resource_failure'],'AGGREGATE_WALL_LIMIT');self.assertEqual(row['exit_code'],-signal.SIGTERM);self.assertLess(row['wall_seconds'],3)
  finally:runner.CEILINGS.clear();runner.CEILINGS.update(old)
 def test_disk_gate_runs_no_child(self):
  old=runner.CEILINGS.copy()
  try:
   with tempfile.TemporaryDirectory() as td:
    p=Path(td);build=p/'build';build.mkdir();(build/'inert_bytes').write_bytes(b'1234');runner.CEILINGS['disk_bytes']=3
    with self.assertRaisesRegex(RuntimeError,'RESOURCE_LIMITS'):runner.execute([sys.executable,'-c','raise Exception("must not run")'],'disk',p,build)
    self.assertFalse((p/'disk.log').exists())
  finally:runner.CEILINGS.clear();runner.CEILINGS.update(old)
 def test_receipts_not_overwritten(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);build=p/'build';build.mkdir();(p/'old_execution.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'OVERWRITE'):runner.execute([sys.executable,'-c','pass'],'old',p,build)
class OrphanContainmentTests(unittest.TestCase):
 def test_leader_exit_descendant_is_failed_and_killed(self):
  import os
  with tempfile.TemporaryDirectory(prefix='phase8_inert_orphan_') as td:
   p=Path(td);build=p/'build';build.mkdir();pidfile=p/'inert_child.json'
   child='import time; time.sleep(60)'
   parent="import subprocess,sys,json,os,pathlib; child=subprocess.Popen([sys.executable,'-c',"+repr(child)+"]); pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid':child.pid,'pgid':os.getpgrp()}))"
   try:
    with self.assertRaisesRegex(RuntimeError,'ORPHAN_PROCESS_GROUP_REMAINS'):
     runner.execute([sys.executable,'-c',parent,str(pidfile)],'inert_orphan',p,build)
    receipt=json.loads((p/'inert_orphan_execution.json').read_text())
    self.assertEqual(receipt['exit_code'],0)
    self.assertEqual(receipt['resource_failure'],'ORPHAN_PROCESS_GROUP_REMAINS')
    child_info=json.loads(pidfile.read_text());self.assertEqual(runner.group_members(child_info['pgid']),[])
   finally:
    if pidfile.exists():
     info=json.loads(pidfile.read_text())
     if runner.group_members(info['pgid']):
      try:os.killpg(info['pgid'],signal.SIGKILL)
      except ProcessLookupError:pass
 def test_all_missing_prefix_is_rejected_before_dispatch(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory(prefix='phase8_inert_preflight_') as td:
   p=Path(td);build=p/'build';build.mkdir();manifest=p/'full.json';manifest.write_text('{}')
   argv=['phase8','--manifest',str(manifest),'--build',str(build),'--result',str(p),'--action','all']
   with patch.object(sys,'argv',argv),patch.object(runner,'execute',side_effect=AssertionError('must not dispatch')):
    with self.assertRaisesRegex(ValueError,'MISSING_VERIFIED_PREFIX_MANIFEST'):runner.main()
   self.assertFalse((p/'.phase8_analysis.lock').exists())

if __name__=='__main__':unittest.main()
"""Failure/control tests; no fabricated Monte Carlo acceptance or generation."""
from argparse import Namespace
from contextlib import redirect_stderr
from pathlib import Path
import io
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO))
from simulation.new_backgrounds import common,controller


class Controls(unittest.TestCase):
    def args(self):return Namespace(process='zh',events=1000,seed=20261104,energy=13000,output=Path('/unexecuted'),max_hours=4,max_disk_gb=10,dry_run=True)
    def test_unreviewed_counts_process_energy_and_seed_reject(self):
        for key,value in [('events',100),('events',10000),('events',True),('process','bbgg'),('energy',14000),('seed',0),('seed',900000001)]:
            args=self.args();setattr(args,key,value)
            with self.assertRaises(ValueError):common.request(args)
    def test_relaxed_nonfinite_and_missing_output_reject(self):
        for key,value in [('max_hours',4.1),('max_disk_gb',10.1),('max_hours',float('nan')),('max_disk_gb',True),('output',None)]:
            args=self.args();setattr(args,key,value)
            with self.assertRaises(ValueError):common.request(args)
    def test_invalid_request_never_checks_environment_or_starts_child(self):
        with patch.object(controller,'verify_environment') as verify,patch.object(subprocess,'Popen') as child,redirect_stderr(io.StringIO()):
            code=controller.main(['--process','zh','--events','10000','--seed','1','--energy','13000','--output','/unexecuted'])
        self.assertEqual(code,2);verify.assert_not_called();child.assert_not_called()
    def test_old_phase6f_shell_guard_exactly_preserved(self):
        path='simulation/zh_pilot/scripts/generate_pilot.sh'
        original=subprocess.check_output(['git','-C',str(REPO),'show',common.BASE+':'+path])
        self.assertEqual((REPO/path).read_bytes(),original)
    def test_duplicate_and_nonfinite_receipts_reject(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            path=Path(folder)/'invalid.json'
            for raw in ('{"status":1,"status":2}','{"x":NaN}','{"x":1e309}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):common.strict_json(path)
    def test_recovery_rejects_other_failures_partial_counts_or_downstream_attempts(self):
        """Invalid control receipts only; no event fixtures or physics PASS."""
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            run=Path(folder)/'failed';run.mkdir()
            args=self.args();args.output=Path(folder)/'fresh';req=common.request(args)
            original=dict(req,output=str(run.resolve()))
            template={'status':'PARTIAL_PHYSICAL_CHAIN','failure':'Actual complete run card differs from reviewed request',
                      'MG5_events_generated':1000,'Pythia_events_attempted':0,'Pythia_events_written':0,
                      'HepMC_validated_events':0,'Delphes_ROOT_entries':0,'stages_attempted':[], 'request':original}
            cases=[]
            for key,value in [('status','PASS_FULL_CHAIN_MODEL_SCOPE'),('failure','mass-shell failure'),
                              ('MG5_events_generated',999),('Pythia_events_attempted',1),('Delphes_ROOT_entries',1),
                              ('stages_attempted',[{'stage':'shower_background_prefix10'}])]:
                failed=copy.deepcopy(template);failed[key]=value;cases.append(failed)
            for failed in cases:
                with patch.object(controller,'strict_json',side_effect=[failed,{'request':original}]),patch.object(subprocess,'Popen') as child:
                    with self.assertRaises(ValueError):controller.preserved_source(run,req,{})
                    child.assert_not_called()
    def test_second_fresh_recovery_output_cannot_reserve_same_source(self):
        """Exclusive control registry only; no source events or physical acceptance."""
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            registry=Path(folder)/'registry'
            with patch.object(controller,'CAMPAIGN',registry),patch.object(subprocess,'Popen') as child:
                source={'source_sha256':'a'*64};campaign={'campaign_id':'invalid-control-only','bridge_sha256':'b'*64}
                first=controller.reserve_existing_source_once(source,campaign,Path(folder)/'first')
                with self.assertRaises(FileExistsError):controller.reserve_existing_source_once(source,campaign,Path(folder)/'second')
                self.assertEqual(common.sha_file(first['path']),first['sha256']);child.assert_not_called()
    def test_chain_continuation_rejects_modified_manifest_without_children(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            run=Path(folder)/'invalid';run.mkdir();(run/'run_manifest.json').write_text('{"status":"INVALID_CONTROL_ONLY"}')
            args=self.args();args.output=Path(folder)/'fresh'
            with patch.object(subprocess,'Popen') as child:
                with self.assertRaisesRegex(ValueError,'immutable B04'):controller.preserved_chain(run,common.request(args),{})
                child.assert_not_called()
    def test_chain_continuation_rejects_output_inside_preserved_chain(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            run=Path(folder)/'invalid';run.mkdir();args=self.args();args.output=run/'would_modify_old_tree'
            with patch.object(subprocess,'Popen') as child:
                with self.assertRaisesRegex(ValueError,'separate'):controller.preserved_chain(run,common.request(args),{})
                self.assertFalse(args.output.exists());child.assert_not_called()
    def test_detector_continuation_rejects_modified_receipt_without_children(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            run=Path(folder)/'invalid';run.mkdir();(run/'run_manifest.json').write_text('{"status":"INVALID_CONTROL_ONLY"}')
            args=self.args();args.output=Path(folder)/'fresh'
            with patch.object(subprocess,'Popen') as child:
                with self.assertRaisesRegex(ValueError,'immutable diagnosed B04'):controller.preserved_detector(run,common.request(args),{})
                child.assert_not_called()
    def test_detector_continuation_rejects_overlapping_output(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            run=Path(folder)/'invalid';run.mkdir();args=self.args();args.output=run/'would_modify_old_tree'
            with patch.object(subprocess,'Popen') as child:
                with self.assertRaisesRegex(ValueError,'separate'):controller.preserved_detector(run,common.request(args),{})
                self.assertFalse(args.output.exists());child.assert_not_called()
    def test_detector_continuation_has_exclusive_source_registry(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            with patch.object(controller,'CAMPAIGN',Path(folder)/'registry'),patch.object(subprocess,'Popen') as child:
                source={'source_sha256':'c'*64,'retained_shower':{'status':'INVALID_CONTROL_ONLY'}}
                campaign={'campaign_id':'invalid-control-only','bridge_sha256':'d'*64}
                first=controller.reserve_existing_source_once(source,campaign,Path(folder)/'first')
                self.assertTrue(Path(first['path']).name.startswith('root_numeric_continuation_'))
                with self.assertRaises(FileExistsError):controller.reserve_existing_source_once(source,campaign,Path(folder)/'second')
                child.assert_not_called()


@unittest.skipUnless(sys.platform.startswith('linux'),'Linux resource failure controls')
class Supervision(unittest.TestCase):
    def test_stop_marker_prevents_any_child(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            output=Path(folder);(output/'STOP').touch();args=Controls().args();args.output=output
            monitor=common.Monitor(output,common.request(args))
            with patch.object(subprocess,'Popen') as child:
                with self.assertRaisesRegex(ValueError,'STOPPED'):monitor.run_command([sys.executable,'-c','pass'],output,'blocked_child')
            child.assert_not_called();monitor.restore_signals()
    def test_failed_benign_child_keeps_actual_log(self):
        scratch=REPO/'.local/phase6g_backgrounds/controller_tests';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            output=Path(folder);args=Controls().args();args.output=output;monitor=common.Monitor(output,common.request(args))
            try:
                with self.assertRaises(ValueError):monitor.run_command([sys.executable,'-c','raise SystemExit(7)'],output,'failed_benign')
                self.assertEqual(monitor.executions[0]['exit_code'],7);self.assertTrue(Path(monitor.executions[0]['log_path']).is_file())
            finally:monitor.restore_signals()


if __name__=='__main__':unittest.main()

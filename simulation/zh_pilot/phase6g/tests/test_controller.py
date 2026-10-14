"""METHOD_ONLY authorization/resource tests; no generator/event execution."""
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone, timedelta
from pathlib import Path
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from simulation.zh_pilot.phase6g import common, controller


class Fixture(unittest.TestCase):
    def setUp(self):
        scratch = REPO/'.local/phase6g/test_scratch';scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.folder = Path(self.temp.name)
        self.args = Namespace(process='zh', events=100, seed=20261104, energy=13000,
                              output=self.folder/'run', dry_run=False, max_hours=2, max_disk_gb=5)
    def tearDown(self):
        self.temp.cleanup()
    def ticket(self):
        # Deliberately fake bridge: cannot authorize the real installed bridge.
        now = datetime.now(timezone.utc)
        value = {'schema_version':1, 'status':'EXPLICIT_USER_AUTHORIZATION',
            'authorization_command':common.ACK, 'request':common.request(self.args),
            'ticket_id':'00000000-0000-4000-8000-000000000001', 'bridge_sha256':'0'*64,
            'reviewed_base_head':common.BASE, 'authorized_at_utc':now.isoformat(),
            'expires_at_utc':(now+timedelta(hours=24)).isoformat()}
        path = self.folder/'method_ticket.json';path.write_text(json.dumps(value))
        return path, value


class Methods(Fixture):
    def test_exact_bounded_request(self):
        self.assertEqual(common.request(self.args)['events'], 100)
        self.assertIs(type(common.request(self.args)['max_hours']), float)
    def test_larger_and_smaller_source_counts_rejected(self):
        for count in (10, 99, 101, 1000, 1000000, True):
            self.args.events=count
            with self.assertRaises(ValueError):common.request(self.args)
    def test_other_process_energy_and_seed_rejected(self):
        for field, value in (('process','bbgg'),('energy',14000),('seed',0),('seed',900000001),('seed',True)):
            args=Namespace(**vars(self.args));setattr(args,field,value)
            with self.assertRaises(ValueError):common.request(args)
    def test_nonfinite_and_relaxed_resource_caps_rejected(self):
        for field, value in (('max_hours',3),('max_disk_gb',6),('max_hours',float('nan')),
                             ('max_disk_gb',float('inf')),('max_hours',0),('max_disk_gb',True)):
            args=Namespace(**vars(self.args));setattr(args,field,value)
            with self.assertRaises(ValueError):common.request(args)
    def test_physical_output_must_be_explicit(self):
        self.args.output=None
        with self.assertRaises(ValueError):common.request(self.args)
        self.args.dry_run=True
        self.assertIsNone(common.request(self.args)['output'])
    def test_method_ticket_exact_request_and_bridge(self):
        path,value=self.ticket()
        self.assertEqual(common.validate_ticket(path,value['request'],'0'*64),value)
        with self.assertRaises(ValueError):common.validate_ticket(path,value['request'],'1'*64)
        modified=dict(value['request'], seed=42)
        with self.assertRaises(ValueError):common.validate_ticket(path,modified,'0'*64)
    def test_wrong_authorization_token_and_fixture_status_rejected(self):
        for field,value in (('authorization_command','yes'),('status','METHOD_ONLY'),('schema_version',True)):
            path,ticket=self.ticket();ticket[field]=value;path.write_text(json.dumps(ticket))
            with self.assertRaises(ValueError):common.validate_ticket(path,common.request(self.args),'0'*64)
    def test_expired_future_and_short_remaining_ticket_rejected(self):
        path,ticket=self.ticket();now=datetime.now(timezone.utc)
        for start,end in ((now-timedelta(days=2),now-timedelta(days=1)),
                          (now+timedelta(hours=1),now+timedelta(hours=2)),
                          (now-timedelta(hours=1),now+timedelta(minutes=10))):
            ticket.update(authorized_at_utc=start.isoformat(),expires_at_utc=end.isoformat())
            path.write_text(json.dumps(ticket))
            with self.assertRaises(ValueError):common.validate_ticket(path,common.request(self.args),'0'*64)
    def test_unknown_or_duplicate_receipt_keys_rejected(self):
        path,ticket=self.ticket();ticket['approval']=True;path.write_text(json.dumps(ticket))
        with self.assertRaises(ValueError):common.validate_ticket(path,common.request(self.args),'0'*64)
        path.write_text('{"status":1,"status":2}')
        with self.assertRaises(ValueError):common.strict_json(path)
    def test_numeric_json_overflow_rejected(self):
        path=self.folder/'overflow.json';path.write_text('{"value":1e309}')
        with self.assertRaises(ValueError):common.strict_json(path)
    def test_one_use_claim_and_exact_retained_bytes(self):
        path,ticket=self.ticket();sha=common.sha_file(path)
        actual,claimed,hash_=common.claim_ticket(path,ticket['request'],'0'*64)
        self.assertFalse(path.exists());self.assertEqual(actual,ticket)
        self.assertEqual(hash_,sha);self.assertEqual(common.sha_file(claimed),sha)
        with self.assertRaises(ValueError):common.validate_ticket(path,ticket['request'],'0'*64)
    def test_no_implicit_authorization_issuer(self):
        with self.assertRaises(ValueError):
            common.issue_ticket(self.folder/'bad.json',common.request(self.args),'0'*64,'yes')
        self.assertFalse((self.folder/'bad.json').exists())
    def test_non_dry_rejects_before_environment_output_or_subprocess(self):
        with (patch.dict(os.environ, {}, clear=True), patch.object(controller,'verify_environment') as verify,
              patch.object(subprocess,'Popen') as process, redirect_stderr(io.StringIO()) as errors):
            rc=controller.main(['--process','zh','--events','100','--seed','20261104','--energy','13000',
                                '--output',str(self.args.output)])
        self.assertEqual(rc,2);self.assertIn('NOT_AUTHORIZED',errors.getvalue())
        verify.assert_not_called();process.assert_not_called();self.assertFalse(self.args.output.exists())
    def test_method_ticket_cannot_enable_live_controller(self):
        path,_=self.ticket()
        with (patch.dict(os.environ, {'PHASE6G_AUTHORIZATION_FILE':str(path)}),
              patch.object(controller,'verify_environment') as verify, redirect_stderr(io.StringIO())):
            rc=controller.main(['--process','zh','--events','100','--seed','20261104','--energy','13000',
                                '--output',str(self.args.output)])
        self.assertEqual(rc,2);verify.assert_not_called();self.assertFalse(self.args.output.exists())
    def test_dry_run_with_bad_caps_rejects_before_environment(self):
        with patch.object(controller,'verify_environment') as verify, redirect_stderr(io.StringIO()):
            rc=controller.main(['--process','zh','--events','100','--seed','42','--energy','13000',
                                '--dry-run','--max-hours','3'])
        self.assertEqual(rc,2);verify.assert_not_called()
    def test_failed_downstream_counters_are_preserved(self):
        output=self.folder/'observed';full=output/'pythia/full100';full.mkdir(parents=True)
        (full/'run_summary.json').write_text(json.dumps({'N_written':100,'N_shower_failed':0}))
        (full/'zh_hepmc_validation.json').write_text(json.dumps({'N_readback':3,'N_passed_validation':2,'N_failed_validation':1}))
        native=output/'delphes';native.mkdir()
        (native/'native_validation.json').write_text(json.dumps({'ROOT_entries':100,'processed':2,'invalid':1}))
        state={'MG5_events_generated':0,'Pythia_events_written':0,'HepMC_validated_events':0,'Delphes_ROOT_entries':0}
        executions=[{'stage':k} for k in ('zh_shower_full100','zh_reader_full100','delphes_full100')]
        controller.preserve_observed_counters(output,state,executions)
        self.assertEqual(state['Pythia_events_written'],100);self.assertEqual(state['HepMC_validated_events'],2)
        self.assertEqual(state['Delphes_ROOT_entries'],100)
        self.assertEqual(state['actual_partial_observations']['Delphes_native_readback']['invalid'],1)
    def test_missing_attempted_stage_counters_are_unknown(self):
        output=self.folder/'missing';output.mkdir()
        state={'MG5_events_generated':0,'Pythia_events_written':0,'HepMC_validated_events':0,'Delphes_ROOT_entries':0}
        controller.preserve_observed_counters(output,state,[{'stage':'mg5_100_event_generation'},
            {'stage':'zh_shower_full100'},{'stage':'zh_reader_full100'},{'stage':'delphes_full100'}])
        self.assertTrue(all(str(value).startswith('UNKNOWN') for key,value in state.items() if key!='actual_partial_observations'))
    def test_campaign_reservation_is_one_attempt_not_authority(self):
        path=self.folder/'method_campaign.json'
        value=common.reserve_campaign(common.request(self.args),'method-ticket','0'*64,path)
        self.assertEqual(common.sha_file(path),value['sha256'])
        self.assertIn('NOT_GENERATION_PROOF',common.strict_json(path)['status'])
        with self.assertRaises(ValueError):common.reserve_campaign(common.request(self.args),'other-ticket','0'*64,path)
    def test_campaign_marker_never_enables_missing_authorization(self):
        with (patch.dict(os.environ, {}, clear=True), patch.object(controller,'CAMPAIGN') as campaign,
              patch.object(controller,'verify_environment') as verify, redirect_stderr(io.StringIO()) as errors):
            campaign.exists.return_value=True
            rc=controller.main(['--process','zh','--events','100','--seed','42','--energy','13000'])
        self.assertEqual(rc,2);self.assertIn('NOT_AUTHORIZED',errors.getvalue());verify.assert_not_called()


@unittest.skipUnless(sys.platform.startswith('linux'), 'Linux supervision; executed separately in WSL/CI')
class LinuxResources(Fixture):
    # Inherit fixture helpers, not its test cases.
    def run_benign(self, code, name='method_child', hours=.01, disk=.01):
        output=self.folder/'benign';output.mkdir()
        req=common.request(self.args);req.update(max_hours=hours,max_disk_gb=disk)
        monitor=common.Monitor(output,req)
        try:
            result=monitor.run_command([sys.executable,'-c',code],output,name)
            return result,monitor
        finally:
            monitor.restore_signals()
    def test_successful_benign_child_has_log_and_sampled_metrics(self):
        result,monitor=self.run_benign('import time;print("METHOD_ONLY");time.sleep(.3)')
        self.assertEqual(result['exit_code'],0);self.assertEqual(len(monitor.executions),1)
        self.assertTrue(Path(result['log_path']).is_file());self.assertIsInstance(monitor.metrics()['elapsed_seconds'],float)
    def test_failed_benign_child_preserves_attempt(self):
        output=self.folder/'failed';output.mkdir();monitor=common.Monitor(output,common.request(self.args))
        try:
            with self.assertRaises(ValueError):monitor.run_command([sys.executable,'-c','raise SystemExit(7)'],output,'method_failure')
            self.assertEqual(monitor.executions[0]['exit_code'],7)
            self.assertTrue(Path(monitor.executions[0]['log_path']).exists())
        finally:monitor.restore_signals()
    def test_named_native_missing_authorization_probe_expected_exit(self):
        output=self.folder/'negative_probe';output.mkdir();monitor=common.Monitor(output,common.request(self.args))
        binary=output/'zh_shower';binary.write_text('#!'+sys.executable+'\nprint("METHOD_ONLY_AUTH_PROBE")\nraise SystemExit(2)\n');binary.chmod(0o700)
        try:
            result=monitor.run_command([str(binary)],output,'zh_shower_missing_authorization',expected_exit_code=2)
            self.assertEqual(result['exit_code'],2)
            with self.assertRaises(ValueError):monitor.run_command([str(binary)],output,'other_stage',expected_exit_code=2)
            with self.assertRaises(ValueError):monitor.run_command([str(binary),'physical_arguments'],output,'zh_shower_missing_authorization',expected_exit_code=2)
        finally:monitor.restore_signals()
    def test_native_probe_unexpected_success_and_physical_failure_are_fatal(self):
        output=self.folder/'unexpected_probe';output.mkdir();monitor=common.Monitor(output,common.request(self.args))
        binary=output/'validate_zh_hepmc3';binary.write_text('#!'+sys.executable+'\nraise SystemExit(0)\n');binary.chmod(0o700)
        try:
            with self.assertRaises(ValueError):monitor.run_command([str(binary)],output,'validate_zh_hepmc3_missing_authorization',expected_exit_code=2)
            with self.assertRaises(ValueError):monitor.run_command([sys.executable,'-c','raise SystemExit(2)'],output,'method_failed_physical')
        finally:monitor.restore_signals()
    def test_elapsed_cap_terminates_benign_child_and_records_failure(self):
        output=self.folder/'timeout';output.mkdir();req=common.request(self.args);req['max_hours']=.00008
        monitor=common.Monitor(output,req)
        try:
            with self.assertRaisesRegex(ValueError,'TIMEOUT'):
                monitor.run_command([sys.executable,'-c','import time;time.sleep(20)'],output,'method_timeout')
            self.assertIn('TIMEOUT',monitor.executions[0]['failure'])
        finally:monitor.restore_signals()
    def test_term_handler_new_escaped_descendant_is_discovered_and_killed(self):
        output=self.folder/'term_fork';output.mkdir();pidfile=output/'born_after_term'
        code=('import os,signal,subprocess,sys,time\n'
              'def handle(*args):\n'
              ' child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(20)"],start_new_session=True)\n'
              f' open({str(pidfile)!r},"w").write(str(child.pid))\n'
              ' os._exit(0)\n'
              'signal.signal(signal.SIGTERM,handle)\ntime.sleep(20)\n')
        req=common.request(self.args);req['max_hours']=.00035;monitor=common.Monitor(output,req)
        try:
            with self.assertRaisesRegex(ValueError,'TIMEOUT'):monitor.run_command([sys.executable,'-c',code],output,'method_term_fork')
            self.assertTrue(pidfile.exists());pid=int(pidfile.read_text())
            actual=common.Monitor.process_stats().get(pid)
            self.assertTrue(actual is None or actual['state']=='Z','new escaped descendant still executes')
            self.assertEqual(len(monitor.executions),1)
        finally:monitor.restore_signals()
    def test_leader_exit_orphan_is_terminated(self):
        code='import subprocess,sys;subprocess.Popen([sys.executable,"-c","import time;time.sleep(20)"])'
        output=self.folder/'orphan';output.mkdir();monitor=common.Monitor(output,common.request(self.args))
        try:
            with self.assertRaisesRegex(ValueError,'ORPHANED'):
                monitor.run_command([sys.executable,'-c',code],output,'method_orphan')
            self.assertIn('ORPHANED',monitor.executions[0]['failure'])
        finally:monitor.restore_signals()
    def test_escaped_session_is_owned_and_terminated(self):
        code='import subprocess,sys,time;subprocess.Popen([sys.executable,"-c","import time;time.sleep(20)"],start_new_session=True);time.sleep(.4)'
        output=self.folder/'escape';output.mkdir();monitor=common.Monitor(output,common.request(self.args))
        try:
            with self.assertRaisesRegex(ValueError,'ESCAPED_SESSION'):
                monitor.run_command([sys.executable,'-c',code],output,'method_escape')
            self.assertIn('ESCAPED_SESSION',monitor.executions[0]['failure'])
        finally:monitor.restore_signals()
    def test_internal_symlinks_count_once_and_escaping_links_reject(self):
        output=self.folder/'links';output.mkdir();target=output/'data';target.write_bytes(b'abc')
        link=output/'internal';link.symlink_to(target)
        self.assertEqual(common.tree_bytes(output),3+link.lstat().st_size)
        external=self.folder/'outside';external.write_bytes(b'x');(output/'escape').symlink_to(external)
        with self.assertRaises(ValueError):common.tree_bytes(output)
    def test_verified_readonly_installed_link_is_not_followed(self):
        output=self.folder/'links';output.mkdir();installed=self.folder/'installed';installed.mkdir()
        data=installed/'data';data.write_bytes(b'old');link=output/'pdfdata';link.symlink_to(data)
        self.assertEqual(common.tree_bytes(output,(installed,)),link.lstat().st_size)
        self.assertEqual(data.read_bytes(),b'old')
    def test_stop_marker_blocks_before_child(self):
        output=self.folder/'stop';output.mkdir();(output/'STOP').touch()
        monitor=common.Monitor(output,common.request(self.args))
        with patch.object(subprocess,'Popen') as process:
            with self.assertRaisesRegex(ValueError,'STOPPED'):
                monitor.run_command([sys.executable,'-c','pass'],output,'method_stopped')
        process.assert_not_called()


if __name__=='__main__':unittest.main()

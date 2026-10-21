"""Ordinary-file and mocked scheduler tests; no kernel/physics deployment."""
import contextlib,copy,hashlib,io,json,os,sys,tempfile,time,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from . import contract as c,history,ledger,runner,same_instance,tasks

class Fixture(unittest.TestCase):
 def setUp(self):
  root=c.REPO/'.local/master_test_fixtures';root.mkdir(parents=True,exist_ok=True)
  self.tmp=tempfile.TemporaryDirectory(dir=root);self.root=Path(self.tmp.name)
  self.run=self.root/str(uuid.uuid4());self.run.mkdir()
  for n in ('ledger','stages','snapshots','exports'):(self.run/n).mkdir()
  self.context={'revision':'a'*40,'source_sha256':'b'*64,'source_rows':[],
   'host_capture':None,'scope':'SAFE_ENGINEERING_AND_READ_ONLY','run_directory':str(self.run)}
  self.context['scope_identity']=c.binding_identity(self.context);ledger.create_json(self.run/'context.json',self.context)
 def tearDown(self):self.tmp.cleanup()
 def event(self,status='PASS_SOURCE_ONLY',**kwargs):return ledger.append(self.run,self.context,'G0_SOURCE_BASELINE',status,**kwargs)

class LedgerTests(Fixture):
 def test_ledger_exclusive_no_replace_and_hash_chain(self):
  self.event('RUNNING');self.event();rows=ledger.events(self.run);self.assertEqual(len(rows),2)
  with self.assertRaises(FileExistsError):ledger.create_json(self.run/'ledger/000001.json',{})
  self.assertNotEqual(rows[1]['previous_sha256'],'0'*64)
 def test_torn_event_is_preserved_and_rejected(self):
  self.event();p=self.run/'ledger/000002.json';p.write_bytes(b'{"torn":')
  with self.assertRaises(ValueError):ledger.events(self.run)
  self.assertEqual(p.read_bytes(),b'{"torn":')
 def test_changed_previous_frame_rejected(self):
  self.event('RUNNING');self.event();p=self.run/'ledger/000001.json';v=c.load(p);v['child_pid']=999;p.write_bytes(c.canonical(v)+b'\n')
  with self.assertRaisesRegex(ValueError,'CHAIN'):ledger.events(self.run)
 def test_foreign_run_or_nonmonotonic_endpoint_rejected(self):
  for field,value in [('run_id',str(uuid.uuid4())),('finished_monotonic_ns',1)]:
   self.event();p=self.run/'ledger/000001.json';v=c.load(p);v[field]=value;p.write_bytes(c.canonical(v)+b'\n')
   with self.assertRaises(ValueError):ledger.events(self.run)
   p.unlink()
 def test_output_tamper_and_extra_file_rejected(self):
  out=self.run/'stages/G0_SOURCE_BASELINE';out.mkdir();p=out/'x.json';p.write_bytes(b'{}')
  self.event(outputs=ledger.manifest(out));p.write_bytes(b'{"changed":true}')
  with self.assertRaisesRegex(ValueError,'OUTPUT_DRIFT'):ledger.verify(self.run)
 def test_second_controller_lock_is_denied_and_release_reusable(self):
  with ledger.lock(self.run):
   with self.assertRaisesRegex(ValueError,'CONCURRENT'):
    with ledger.lock(self.run):pass
  with ledger.lock(self.run):pass
 def test_state_vocabulary_and_event_cap_fail_closed(self):
  with self.assertRaisesRegex(ValueError,'UNKNOWN_STAGE'):self.event('PHYSICS_PASS')
  with patch.object(ledger,'MAX_EVENTS',1):
   self.event()
   with self.assertRaisesRegex(ValueError,'LEDGER_FULL'):self.event()
 def test_nonfinite_duplicate_and_oversized_json_rejected(self):
  p=self.root/'bad.json'
  for data in (b'{"a":1,"a":2}',b'{"a":NaN}',b'x'*101):
   p.write_bytes(data)
   with self.assertRaises(ValueError):c.load(p,100)
 def test_whole_run_logical_bound_is_explicitly_not_kernel_capacity(self):
  self.assertFalse(ledger.budget(self.run)['allocated_blocks_enforced'])
  with patch.object(ledger,'MAX_RUN_BYTES',1):
   with self.assertRaisesRegex(ValueError,'LOGICAL_RUN_BOUND'):ledger.budget(self.run)

class SchedulerTests(Fixture):
 def patched(self):return patch.object(runner,'source_binding',return_value=self.context)
 def fake_child(self,run,stage):
  out=run/'stages'/stage;out.mkdir();ledger.create_json(out/'stage_result.json',{'status':'PASS_SOURCE_ONLY'})
  return {'status':'PASS_SOURCE_ONLY','argv':['INERT_SAFE_METHOD'],'exit_status':0,'pid':123,
   'manifest':ledger.manifest(out),'observations':{'kernel':None}}
 def test_resume_skips_successful_identical_stage(self):
  self.event()
  with self.patched(),patch.object(runner,'SAFE',(('G0_SOURCE_BASELINE',()),)),patch.object(runner,'LIVE',()),patch.object(runner,'child') as child:
   r=runner.execute(self.run);child.assert_not_called();self.assertEqual(r['status'],'PASS_SOURCE_ONLY')
 def test_resume_source_drift_rejected_before_dispatch(self):
  changed=copy.deepcopy(self.context);changed['revision']='c'*40
  with patch.object(runner,'source_binding',return_value=changed),patch.object(runner,'child') as child:
   with self.assertRaisesRegex(ValueError,'RESUME_SOURCE'):runner.execute(self.run)
   child.assert_not_called()
 def test_interrupted_stage_becomes_unknown_without_automatic_retry(self):
  self.event('RUNNING')
  with self.patched(),patch.object(runner,'child') as child:
   r=runner.execute(self.run);self.assertEqual(r['status'],'UNKNOWN');child.assert_not_called()
  self.assertEqual(ledger.latest(self.run)['G0_SOURCE_BASELINE']['status'],'UNKNOWN')
 def test_cleanup_unknown_remains_sticky_across_resume(self):
  self.event('UNKNOWN',reason='SAFE_CHILD_DISPATCH_OR_CLEANUP_UNKNOWN:TimeoutError')
  with self.patched(),patch.object(runner,'child') as child:
   self.assertEqual(runner.execute(self.run)['status'],'UNKNOWN');child.assert_not_called()
 def test_blocked_inventory_does_not_block_independent_safe_task(self):
  ledger.append(self.run,self.context,'G1_REAL_INVENTORY','BLOCKED_OS_CAPABILITY');self.event()
  with self.patched(),patch.object(runner,'SAFE',(('G1_REAL_INVENTORY',('G0_SOURCE_BASELINE',)),('G2_ARCHITECTURE_DECISION',('G0_SOURCE_BASELINE',)))),patch.object(runner,'LIVE',()),patch.object(runner,'child',side_effect=self.fake_child) as child:
   runner.execute(self.run);self.assertEqual(child.call_count,1);self.assertEqual(child.call_args.args[1],'G2_ARCHITECTURE_DECISION')
 def test_failed_stage_is_not_retried_or_promoted(self):
  self.event('FAIL')
  with self.patched(),patch.object(runner,'SAFE',(('G0_SOURCE_BASELINE',()),)),patch.object(runner,'LIVE',()),patch.object(runner,'child') as child:
   r=runner.execute(self.run);self.assertEqual(r['safe_failures'],['G0_SOURCE_BASELINE']);self.assertEqual(r['status'],'FAIL');child.assert_not_called()
 def test_live_chain_records_blockers_without_child_dispatch(self):
  with self.patched(),patch.object(runner,'SAFE',()),patch.object(runner,'child') as child:
   runner.execute(self.run);child.assert_not_called()
  rows=ledger.latest(self.run);self.assertTrue(all(rows[s]['status'].startswith('BLOCKED') for s in c.LIVE))
 def test_unknown_run_id_path_traversal_rejected(self):
  for value in ('../../x','latest','a'*40,str(uuid.uuid4())+'/x'):
   with self.assertRaises(ValueError):runner.run_path(value)
 def test_snapshot_growth_is_bounded_without_overwriting_old_snapshot(self):
  with patch.object(runner,'MAX_SNAPSHOTS',1):
   runner.snapshots(self.run,self.context);before=(self.run/'snapshots/0001/MASTER_PROGRESS.json').read_bytes()
   with self.assertRaisesRegex(ValueError,'SNAPSHOT_COUNT_BOUND'):runner.snapshots(self.run,self.context)
   self.assertEqual((self.run/'snapshots/0001/MASTER_PROGRESS.json').read_bytes(),before)
 def test_cli_flags_env_and_json_never_unlock_live(self):
  for argv in (['run-safe','--yes'],['run-safe','--full-auto'],['run-safe','--authorization','INERT'],['BUILD_ONLY']):
   with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):runner.main(argv)
  with patch.dict(os.environ,{'HH_FULL_AUTO':'1','HH_AUTHORIZED':'true'}):self.assertFalse(c.plan()['live_dispatch_implemented'])
  self.assertNotIn('BUILD_ONLY',tasks.TASKS)

class InputCompatibilityTests(unittest.TestCase):
 def test_exact_pr38_plus_master_route_passes(self):
  raw=(c.REPO/history.CAMPAIGN).read_bytes().replace(b'\r\n',b'\n')
  v=history.reviewed_workflow_delta(history.CAMPAIGN,raw,history.FROZEN)
  self.assertIn('CI',v['compatibility_scope'])
 def test_scientific_path_or_unreviewed_workflow_change_rejected(self):
  raw=(c.REPO/history.CAMPAIGN).read_bytes()
  for path,data,expected in [('cards/run_card.dat',raw,history.FROZEN),(history.CAMPAIGN,raw+b'\n# unreviewed',history.FROZEN),(history.CAMPAIGN,raw,'0'*64)]:
   with self.assertRaises(ValueError):history.reviewed_workflow_delta(path,data,expected)
 def test_cost_assignment_remains_explicit_unaccepted_and_three_roles(self):
  v=c.load(c.HERE/'b_v2_cost_assignment.json');self.assertFalse(v['user_accepted']);self.assertFalse(v['execution_authorized'])
  self.assertEqual(set(v['external_roles']),{'manager_journal','launcher','host_backing'});self.assertIn('VMM/hypervisor',v['assignment_proposed_for_explicit_review']['host_backing'])

class InertHelperTests(Fixture):
 def file(self):
  p=self.root/'inert.txt';p.write_bytes(b'INERT');return p,c.sha(b'INERT')
 def test_same_fd_consumption_replay_and_closed_fd(self):
  p,h=self.file()
  with same_instance.InertFDLease(p,h,offline_fixture_only=True) as lease:
   self.assertEqual(lease.consume(),b'INERT')
   with self.assertRaises(ValueError):lease.consume()
  with self.assertRaises(ValueError):lease.consume()
 def test_invalid_transfer_hash_or_concurrent_lease_rejected(self):
  p,h=self.file()
  with self.assertRaises(ValueError):same_instance.InertFDLease(p,'0'*64,offline_fixture_only=True)
  with same_instance.InertFDLease(p,h,offline_fixture_only=True):
   with self.assertRaisesRegex(ValueError,'CONFLICTING'):same_instance.InertFDLease(p,h,offline_fixture_only=True)
 def test_in_place_change_detected_and_privileged_entry_denied(self):
  p,h=self.file()
  with same_instance.InertFDLease(p,h,offline_fixture_only=True) as lease:
   p.write_bytes(b'ALTER')
   with self.assertRaises(ValueError):lease.consume()
  with self.assertRaises(PermissionError):same_instance.privileged_operation('format')
  with self.assertRaises(ValueError):same_instance.InertFDLease(p,h)

class PortableReferenceAuditTests(Fixture):
 def test_existing_reference_audit_never_imports_physical_reweight_backend(self):
  out=self.root/'portable_audit';out.mkdir()
  with patch.dict(sys.modules,{'simulation.hh_signal.campaign.reweight':None}):
   v=tasks.audit_inputs(out,self.context)
  self.assertEqual(v['status'],'PASS_SOURCE_ONLY')
  self.assertEqual(v['evidence']['observed_input_bindings'],1019)
  self.assertFalse(v['live_execution'])

if __name__=='__main__':unittest.main()

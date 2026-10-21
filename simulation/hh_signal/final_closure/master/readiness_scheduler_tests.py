"""Mock children and ordinary-file checkpoints; no live controller/worker test."""
import contextlib,copy,io,json,sys,tempfile,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from . import readiness_runner as r,ledger,readiness_publication as p
from .contract import canonical,load,sha

class SchedulerTests(unittest.TestCase):
 def setUp(self):
  root=r.REPO/'.local/readiness_test_fixtures';root.mkdir(parents=True,exist_ok=True)
  self.tmp=tempfile.TemporaryDirectory(dir=root);self.run=Path(self.tmp.name)/str(uuid.uuid4());self.run.mkdir()
  for name in ('ledger','stages','exports'):(self.run/name).mkdir()
  self.c={'revision':'a'*40,'source_sha256':'b'*64,'inputs_sha256':'c'*64,'host_capture':None,
   'external':{'host':None,'guest':None,'running':None},'run_directory':str(self.run),'scope_identity':'d'*64}
  ledger.create_json(self.run/'context.json',self.c)
 def tearDown(self):self.tmp.cleanup()
 def command(self,stage):return [sys.executable,'-I','-B','-c',r.BOOTSTRAP,str(r.REPO),stage,str(self.run)]
 def child(self,run,stage,**kwargs):
  out=run/'stages'/stage;out.mkdir();ledger.create_json(out/'stage_result.json',{'status':'PASS_SOURCE_ONLY','evidence':{'actual_acceptance':None,'blockers':['FIXTURE_ONLY']}})
  return {'status':'PASS_SOURCE_ONLY','argv':self.command(stage),'exit_status':0,'manifest':ledger.manifest(out),'pid':123,'observations':{'kernel_CPU':None,'fixture_only':True}}
 def mock_binding(self):return patch.object(r,'binding',return_value={'scope_identity':self.c['scope_identity']})
 def event(self,**kwargs):return ledger.append(self.run,self.c,r.STAGES[0],'PASS_SOURCE_ONLY',command=self.command(r.STAGES[0]),exit_status=0,**kwargs)
 def test_complete_checkpoint_resume_skips_all_mock_children(self):
  with self.mock_binding(),patch.object(r.runner,'child',side_effect=self.child) as child:
   self.assertEqual(r.execute(self.run)['stages'],9);self.assertEqual(child.call_count,9)
   before=[p.read_bytes() for p in sorted((self.run/'ledger').iterdir())]
   r.execute(self.run);self.assertEqual(child.call_count,9);self.assertEqual(before,[p.read_bytes() for p in sorted((self.run/'ledger').iterdir())])
 def test_unresolved_child_no_retry(self):
  ledger.append(self.run,self.c,r.STAGES[0],'RUNNING',command=self.command(r.STAGES[0]))
  with self.mock_binding(),patch.object(r.runner,'child') as child:self.assertEqual(r.execute(self.run)['status'],'UNKNOWN');child.assert_not_called()
 def test_source_or_external_drift_denied(self):
  with patch.object(r,'binding',return_value={'scope_identity':'e'*64}):
   with self.assertRaisesRegex(ValueError,'DRIFT'):r.check(self.run)
 def test_changed_full_command_and_fake_approval_fail(self):
  self.event();path=self.run/'ledger/000001.json'
  original=load(path)
  for key,value in [('command',['UNREVIEWED']),('authorization_reference','FAKE_HUMAN_APPROVAL'),('real_subprocess_exit_status',1)]:
   bad=copy.deepcopy(original);bad[key]=value;path.write_bytes(canonical(bad)+b'\n')
   with self.mock_binding():
    with self.assertRaises(ValueError):r.check(self.run)
  path.write_bytes(canonical(original)+b'\n')
 def test_partial_receipt_and_extra_file_rejected(self):
  with self.mock_binding(),patch.object(r.runner,'child',side_effect=self.child):r.execute(self.run)
  out=self.run/'stages'/r.STAGES[0];(out/'unexpected.json').write_bytes(b'{}')
  with self.mock_binding():
   with self.assertRaisesRegex(ValueError,'OUTPUT_DRIFT'):r.check(self.run)
 def test_source_pass_keeps_actual_acceptance_null(self):
  with self.mock_binding(),patch.object(r.runner,'child',side_effect=self.child):
   r.execute(self.run);s=r.status(self.run)
  self.assertTrue(all(x['actual_OS_acceptance'] is None for x in s['stages']));self.assertFalse(s['FULL_LAUNCH_ENVELOPE_VERIFIED'])
 def test_publication_accepts_benign_and_rejects_raw_figures(self):
  self.assertEqual(p.validate(p.REPORTS+'G1_G7_TEST_RESULTS.json',b'{"pass":true}')['bytes'],13)
  for name,raw,mode in [(p.REPORTS+'G1_G7_TEST_RESULTS.json',b'{"records":[]}','100644'),(p.REPORTS+'FINAL_REPORT_ZH_TW.md',b'%PDF-1.0','100644'),(p.REPORTS+'private/raw.json',b'{}','100644'),(p.REPORTS+'G1_G7_TEST_RESULTS.json',b'{}','100755')]:
   with self.assertRaises(ValueError):p.validate(name,raw,mode)
 def test_native_dispatch_cli_absent(self):
  for operation in ('start-guest','provision','format','mount','S4','approve'):
   with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):r.main([operation])

if __name__=='__main__':unittest.main()

"""Mock-child G2 profile tests; old engine invariants are exercised unchanged."""
import contextlib,copy,io,unittest
from unittest.mock import patch
from . import g2_runner as g,readiness_runner as old,readiness_scheduler_tests as fixture,ledger
from .contract import canonical,load
from .g2_protocol_tests import fixture as trace_fixture
from .g2_independent import review

class ProfileTests(unittest.TestCase):
 def setUp(self):
  self.f=fixture.SchedulerTests();self.f.setUp()
  self.f.c.update(schema='HH_G2_SAFE_CONTEXT_V1',external={'host':{'sha256':'a'*64,'path':str(self.f.run/'INERT_HOST.json')},'guest':{'sha256':'b'*64,'path':str(self.f.run/'INERT_GUEST.json')},'running':None})
  (self.f.run/'context.json').write_bytes(canonical(self.f.c)+b'\n')
 def tearDown(self):self.f.tearDown()
 def invoke(self,mode='resume-safe'):
  with patch.object(g,'PROGRESS',self.f.run.parent),patch.object(g,'binding',return_value={'scope_identity':self.f.c['scope_identity']}):
   return g.invoke(mode,run_id=self.f.run.name)
 def test_real_profile_reuses_engine_and_resume_does_not_repeat_mock_children(self):
  with patch.object(old.runner,'child',side_effect=self.f.child) as child:
   r=self.invoke();self.assertEqual(r['stages'],12);self.assertEqual(child.call_count,12)
   before=[p.read_bytes() for p in sorted((self.f.run/'ledger').iterdir())]
   self.invoke();self.assertEqual(child.call_count,12)
   self.assertEqual(before,[p.read_bytes() for p in sorted((self.f.run/'ledger').iterdir())])
  self.assertTrue(all(e['external_input_sha256']=={'host':'a'*64,'guest':'b'*64} for e in ledger.events(self.f.run)))
 def test_external_scope_tampering_rejected_without_rebinding(self):
  with patch.object(old.runner,'child',side_effect=self.f.child):self.invoke()
  p=sorted((self.f.run/'ledger').iterdir())[-1];e=load(p);e['external_input_sha256']['guest']='c'*64;p.write_bytes(canonical(e)+b'\n')
  with self.assertRaisesRegex(ValueError,'EXTERNAL_OR_SCOPE_DRIFT'):self.invoke('verify')
 def test_unknown_child_does_not_retry(self):
  with patch.multiple(old,STAGES=g.STAGES,BOOTSTRAP=g.BOOTSTRAP):
   ledger.append(self.f.run,self.f.c,g.STAGES[0],'RUNNING',command=self.f.command(g.STAGES[0]))
  with patch.object(old.runner,'child') as child:
   self.assertEqual(self.invoke()['status'],'UNKNOWN');child.assert_not_called()
 def test_live_or_approval_cli_is_absent(self):
  for operation in ('S4','create-cgroup','start-guest','approve','format'):
   with self.subTest(operation=operation),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):g.main([operation])
 def test_independent_oracle_subset_detects_tail_substitution_and_overrun(self):
  rows,c=trace_fixture();self.assertEqual(review(rows,c)['CPU_usec'],800)
  for change in (lambda r:r[-1]['actor'].update(start_ticks=99),lambda r:r[-1]['raw'].update({'cpu.stat':'usage_usec 5000000\n'}),
   lambda r:r[-1]['slot_commit'].update(complete=False),lambda r:r[-1].update(cause='TIMEOUT')):
   bad=copy.deepcopy(rows);change(bad)
   with self.assertRaises(ValueError):review(bad,c)

if __name__=='__main__':unittest.main()

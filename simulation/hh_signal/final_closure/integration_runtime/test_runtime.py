"""Nonphysical, numerical and OS regression only. No genuine ME execution."""
import ctypes,fcntl,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from .contract import *
from .containment import Budget,StageFailure,capability,supervise
from .validate import seed_pair,summarize,validate_stage

class RuntimeMethods(unittest.TestCase):
    def work(self,root):
        p=Path(root);(p/'temporary').mkdir()
        for n in NAMED:(p/n).touch()
        return p
    def fixture(self,work,code,budget=None):
        return supervise([sys.executable,'-B','-c',code],work,{**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},'',
            budget or Budget(work,wall=30,cpu=30),method_only=True)
    def test_full_coherent_amplitude_and_fixed_endpoints(self):
        self.assertEqual(stage_input('adaptation').splitlines(),['250 4 4','0.0','2','0','0','1'])
        self.assertEqual(stage_input('measurement').splitlines(),['250 3 3','0.0','0','0','0','1'])
    def test_exact_revision_not_an_authorization_flag(self):
        with self.assertRaisesRegex(ValueError,'REVIEWED_REVISION_MISMATCH'):check_revision('0'*40)
    def test_unknown_stage_rejected(self):
        with self.assertRaises(ValueError):stage_input('refine')
    def test_kernel_denies_new_event_and_outside_writes(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td)
            code="from pathlib import Path\nfor n in ['events.lhe','../escape.txt']:\n try:Path(n).write_text('METHOD_ONLY')\n except PermissionError: print('HI_DENIED',n)\n else:raise SystemExit(9)\n"
            r=self.fixture(work,code)
            self.assertEqual(len(r['records']),2);self.assertFalse((work/'events.lhe').exists())
    def test_allowlisted_numeric_write_and_anonymous_scratch(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td)
            code="import tempfile,os\nfrom pathlib import Path\nPath('results.dat').write_text('1.0 0.1')\nf=tempfile.TemporaryFile(dir=os.environ['TMPDIR'])\nf.write(b'METHOD_ONLY');f.flush()\nassert os.fstat(f.fileno()).st_nlink==0\nprint('HI_METHOD_OK')\n"
            r=self.fixture(work,code);self.assertIn('HI_METHOD_OK',r['records'])
            self.assertEqual(list((work/'temporary').iterdir()),[])
    def test_raw_stdout_is_discarded(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td);r=self.fixture(work,"print('METHOD_ONLY_UNRETAINED_RAW_PAYLOAD');print('HI_OK')")
            self.assertEqual(r['records'],['HI_OK']);self.assertFalse(r['raw_streams_retained'])
            self.assertNotIn('UNRETAINED_RAW_PAYLOAD',json.dumps(r))
    def test_progress_protocol_is_bounded_and_latest(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td);r=self.fixture(work,"for i in range(5000):print('HI_ME_ENTRY',i)")
            self.assertEqual(r['records'],['HI_ME_ENTRY 4999'])
    def test_wall_budget_kills_process_group(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td)
            code="import subprocess,time\nfrom pathlib import Path\nc=subprocess.Popen(['/bin/sleep','30'])\nPath('results.dat').write_text(str(c.pid))\nprint('HI_CHILD',c.pid,flush=True)\ntime.sleep(30)"
            with self.assertRaises(StageFailure) as caught:self.fixture(work,code,Budget(work,wall=5.3,cpu=30))
            self.assertIn('RESOURCE_TIME',str(caught.exception))
            pid=int((work/'results.dat').read_text())
            for _ in range(20):
                p=Path(f'/proc/{pid}/stat')
                if not p.exists() or p.read_text().rsplit(')',1)[1].split()[0]=='Z':break
                time.sleep(.05)
            else:self.fail('surviving running descendant')
    def test_live_CPU_is_in_aggregate_budget(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td)
            with self.assertRaises(StageFailure) as caught:self.fixture(work,'while True:pass',Budget(work,wall=30,cpu=5.2))
            self.assertIn('RESOURCE_TIME',str(caught.exception))
    def test_parent_death_kills_native_child(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td)
            childcode="from pathlib import Path;import os,time;Path('results.dat').write_text(str(os.getpid()));time.sleep(30)"
            code='from simulation.hh_signal.final_closure.integration_runtime.containment import *;import sys;'+\
                'supervise([sys.executable,"-B","-c",'+repr(childcode)+'],'+repr(str(work))+',os.environ,"",Budget('+repr(str(work))+',wall=30,cpu=30),method_only=True)'
            parent=subprocess.Popen([sys.executable,'-B','-c',code],cwd=REPO,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            native=None
            try:
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    s=(work/'results.dat').read_text()
                    if s:native=int(s);break
                    time.sleep(.01)
                self.assertIsNotNone(native)
                parent.kill();parent.wait(timeout=5)
                for _ in range(50):
                    q=Path(f'/proc/{native}/stat')
                    if not q.exists() or q.read_text().rsplit(')',1)[1].split()[0]=='Z':break
                    time.sleep(.01)
                else:self.fail('native child survived supervisor death')
            finally:
                if parent.poll() is None:parent.kill();parent.wait(timeout=5)
                parent.stderr.close()
                if native:
                    try:os.kill(native,9)
                    except ProcessLookupError:pass
    def test_disk_budget_failure_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            work=self.work(td)
            code="from pathlib import Path\nimport time\nPath('results.dat').write_bytes(b'0'*2000000)\ntime.sleep(3)"
            with self.assertRaises(StageFailure) as caught:self.fixture(work,code,Budget(work,wall=30,cpu=30,disk=1000000))
            self.assertIn('RESOURCE_DISK',str(caught.exception));self.assertTrue(caught.exception.receipt['process_group_kill_cleanup'])
    def test_source_fixture_cannot_be_genuine_stage(self):
        with self.assertRaisesRegex(ValueError,'METHOD_FIXTURE'):
            validate_stage({'execution_class':'METHOD_ONLY'},910001,'adaptation',Path('.'))
    def test_four_replicas_do_not_automatically_pass_convergence(self):
        r=[{'seed':s,'measurement':{'sigma_pb':x,'native_internal_error_pb':.01}} for s,x in zip(SEEDS,[1.,2.,3.,4.])]
        a=summarize(r);self.assertEqual(a['mean_pb'],2.5);self.assertEqual(a['final_verdict'],'INCONCLUSIVE_CONVERGENCE')
        self.assertAlmostEqual(a['between_replica_SE_pb'],(5/3)**.5/2)
        self.assertFalse(a['within_and_between_errors_combined'])
    def test_replica_replacement_or_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):summarize([{'seed':910001}]*4)
    def test_eight_RANMAR_stream_pairs_are_distinct(self):
        pairs={seed_pair(s,0,m*3157,1) for s in SEEDS for m in [0,1]};self.assertEqual(len(pairs),8)
    def test_scalar_nan_rejected(self):
        from .validate import number
        for value in ['NaN','Inf','-Inf']:
            with self.assertRaises(ValueError):number(value)
    def test_approval_token_not_a_CLI_option(self):
        from .run import main
        with self.assertRaises(SystemExit):main(['execute-reviewed','--output','/invalid','--authorization','AUTHORIZE_PHASE7_FINAL_INTEGRATION_ONLY'])
    def test_sealed_capability_has_no_editable_path(self):
        fd=capability(910001,'a'*40)
        try:
            self.assertEqual(os.fstat(fd).st_nlink,0)
            self.assertTrue(fcntl.fcntl(fd,fcntl.F_GET_SEALS)&fcntl.F_SEAL_WRITE)
            with self.assertRaises(PermissionError):os.pwrite(fd,b'bad',0)
        finally:os.close(fd)

if __name__=='__main__':unittest.main()

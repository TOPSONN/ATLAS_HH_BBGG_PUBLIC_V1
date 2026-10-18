"""Failure detection methods; never genuine ME or integration."""
import contextlib,io,unittest,ctypes,os,shutil,subprocess,tempfile
from pathlib import Path
from unittest.mock import patch
from . import contract,runner,overlay,review

class Semantics(unittest.TestCase):
    def test_exact_float_bit_comparison(self):
        a='H_R SUM 3FF0000000000000 0000000000000000 0000000000000000 0000000000000000'
        self.assertTrue(runner.compare(a,a)['equal'])
        self.assertFalse(runner.compare(a,a.replace('3FF0000000000000','3FF0000000000001'))['equal'])

    def test_missing_tail_or_candidate_records(self):
        for tag in ['H_CANDIDATE 1 1','H_TAIL 100 10 1 10','H_ACCEPT 1 T','H_ITERATION 1 2 500']:
            self.assertFalse(runner.compare('H_START\n'+tag,'H_START')['equal'])

    def test_rng_grid_stop_arithmetic_first_divergence(self):
        for prefix in ['H_RNG_XRAN1','H_RNG_RAN1','H_RNG_RANMAR','H_BIN','H_POINT','H_R SUM']:
            r=runner.compare('H_START\n'+prefix+' 1','H_START\n'+prefix+' 2')
            self.assertEqual(r['first_record'],1)

    def test_equal_nan_is_rejected(self):
        line='H_R SUM 7FF8000000000000'
        with self.assertRaisesRegex(ValueError,'NONFINITE'):runner.compare(line,line)

    def test_empty_trace_is_not_pass(self):
        with self.assertRaisesRegex(ValueError,'MISSING_NATIVE_TRACE'):runner.compare('','')

    def test_missing_source_identity(self):
        with patch.object(overlay,'lock',return_value={'frozen_runtime_sources':[],'runtime_build_auxiliary':[]}):
            with self.assertRaisesRegex(ValueError,'MISSING_OR_CHANGED_NATIVE_IDENTITY'):overlay.sources(Path('.'))

    def test_anchor_drift_fails_before_execution(self):
        with self.assertRaisesRegex(ValueError,'NOT_UNIQUE'):overlay.replace_once('different','expected','replacement')

    def test_future_real_modes_remain_closed(self):
        for args in [['--execute'],['--authorization','AUTHORIZE_PHASE7_FINAL_INTEGRATION_ONLY']]:
            with patch.object(runner,'run',side_effect=AssertionError('physical dispatch forbidden')),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(runner.main(['--output','invalid',*args]),2)

    def test_frozen_tolerance_and_endpoints(self):
        p=contract.policy();self.assertEqual(p['comparison']['absolute_tolerance'],0)
        self.assertEqual(p['comparison']['relative_tolerance'],0)
        self.assertEqual(p['adaptation']['iterations'],4);self.assertEqual(p['measurement']['iterations'],3)
        self.assertEqual(p['adaptation']['accuracy'],0.)

    @unittest.skipUnless(os.name=='posix' and shutil.which('cc'),'POSIX C compiler required')
    def test_independent_descriptor_lease_rejects_unlinked_rebind(self):
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            root=Path(tmp);library=root/'check.so'
            runner.command(['cc','-shared','-fPIC','-O0',str(contract.HERE/'src/anonymous_io.c'),'-o',str(library)],root,dict(os.environ))
            lib=ctypes.CDLL(str(library))
            with patch.dict(os.environ,{'TMPDIR':str(root)}):
                fd=lib.hh_reference_fd();self.assertGreaterEqual(fd,0)
                self.assertEqual(lib.hh_remember_fd(fd,25),1);self.assertEqual(lib.hh_check_fd(fd,25),1)
                os.close(fd)
                for i in range(100):
                    other=os.open(root/('unrelated_'+str(i)),os.O_CREAT|os.O_RDWR,0o600);os.unlink(root/('unrelated_'+str(i)))
                    self.assertEqual(lib.hh_check_fd(other,25),0);os.close(other)
                self.assertEqual(lib.hh_release_unit(25),0)

if __name__=='__main__':unittest.main()

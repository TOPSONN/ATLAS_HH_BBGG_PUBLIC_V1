"""Negative API/source checks; no approvals, services or physics dispatch."""
import ast,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from simulation.hh_signal.final_closure.resource_closure import worker,backend
from simulation.hh_signal.final_closure.integration_runtime import approval,build,route_a

class WorkerAdapterTests(unittest.TestCase):
    def test_unenclosed_direct_builder_rejected_before_source_work(self):
        with self.assertRaisesRegex(ValueError,'FULL_BUILD_RESOURCE_ENCLOSURE_REQUIRED'):
            worker.require_build_enclosure(Path('/home/btu/simulations/hh_final_closure/no_output_created'))
    def test_missing_human_review_still_first_gate(self):
        p=Path.home()/'simulations/hh_final_closure/inert_negative_never_created'
        with self.assertRaisesRegex(ValueError,'SEPARATE_HUMAN_REVIEW_REQUIRED_NOT_EDITABLE_DATA'):
            build.prepare(p,revision='0'*40)
        self.assertFalse(p.exists())
    def test_bad_fd_cannot_issue_review(self):
        for value in (-1,None,'3',True):
            with self.assertRaisesRegex(ValueError,'PINNED_HUMAN_TERMINAL_REQUIRED'):
                approval.confirm_fd({},value)
    def test_regular_file_cannot_issue_review(self):
        with tempfile.TemporaryFile() as f:
            with self.assertRaisesRegex(ValueError,'PINNED_HUMAN_TERMINAL_REQUIRED'):
                approval.confirm_fd({},f.fileno())
    def test_unwrapped_loader_fails_before_subprocess(self):
        with patch('subprocess.check_output',side_effect=AssertionError('dispatch forbidden')):
            with self.assertRaisesRegex(ValueError,'ENCLOSED_LOADER_RUNNER_REQUIRED'):
                route_a.dependencies('/never/executed')
    def test_loader_reader_rejects_unresolved_output(self):
        class Result:stdout='libmissing => not found'
        with self.assertRaisesRegex(ValueError,'UNRESOLVED_SHARED_LIBRARY'):
            route_a.dependencies('/never/executed',runner=lambda argv:Result())
    def test_descriptor_env_cannot_replace_pinned_transport(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'PINNED_DESCRIPTOR_TRANSPORT_REQUIRED'):
                worker.descriptors(backend.load_profile(), 'fixture')
    def test_future_profile_preserves_original_aggregate_caps(self):
        p=backend.load_profile('BUILD_ONLY');b=backend.profile_bounds(p)
        self.assertEqual((p['aggregate_CPU_seconds'],p['aggregate_wall_seconds'],p['aggregate_disk_bytes']),
                         (14400,14400,5*1024**3))
        self.assertLess(b['maximum_data_disk_bytes'],5*1024**3)
        self.assertLess(b['nominal_kernel_CPU_upper_seconds'],14400)
    def test_worker_main_keeps_single_canonical_module(self):
        source=Path(worker.__file__).read_text()
        self.assertIn("sys.modules['simulation.hh_signal.final_closure.resource_closure.worker']=sys.modules[__name__]",source)
    def test_no_fixture_can_call_manual_confirmation(self):
        module=ast.parse(Path(worker.__file__).read_text())
        node=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='run_fixture')
        calls=[n for n in ast.walk(node) if isinstance(n,ast.Call)]
        self.assertFalse(any(isinstance(n.func,ast.Name) and n.func.id in ('confirm','confirm_fd','HumanReview','run_build') for n in calls))
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in ('confirm','confirm_fd','HumanReview') for n in calls))
    def test_build_exit_zero_requires_complete_envelope_evidence(self):
        from simulation.hh_signal.final_closure.integration_runtime.run import enclosed_build_complete
        import copy
        row={'last_unit_properties':{'Result':'success','ExecMainStatus':'0'},'resource_stop':None,
             'formal_build_mode_launched':True,'formal_build_executed':True,'zero_ME_evidence_verified':True,
             'cgroup_empty_and_unpopulated_verified':True,'residual_processes_after_cleanup':[],
             'new_ME_calls':0,'new_integrals':0,'new_hard_events':0}
        self.assertTrue(enclosed_build_complete(row))
        for key,value in [('resource_stop','STOP'),('zero_ME_evidence_verified',False),
                          ('formal_build_executed',False),('cgroup_empty_and_unpopulated_verified',False),
                          ('new_ME_calls',None),('new_integrals',False),('new_hard_events',1),
                          ('residual_processes_after_cleanup',[123])]:
            bad=copy.deepcopy(row);bad[key]=value;self.assertFalse(enclosed_build_complete(bad),key)
        for key,value in [('Result','exit-code'),('ExecMainStatus','2')]:
            bad=copy.deepcopy(row);bad['last_unit_properties'][key]=value
            self.assertFalse(enclosed_build_complete(bad))
    def test_denied_physical_cli_does_not_create_history_receipts(self):
        from simulation.hh_signal.final_closure.integration_runtime.run import main
        import contextlib,io
        with tempfile.TemporaryDirectory() as folder:
            with contextlib.redirect_stdout(io.StringIO()) as stream:
                code=main(['execute-reviewed','--output',folder,'--reviewed-revision','0'*40])
            self.assertEqual(code,2);self.assertEqual(list(Path(folder).iterdir()),[])
            data=json.loads(stream.getvalue());self.assertEqual(data['new_ME_calls'],0)
            self.assertIn('PHYSICAL_ENCLOSURE',data['reason'])
    def test_source_adapter_syntax(self):
        for f in (worker.HERE.parent/'integration_runtime').glob('*.py'):
            ast.parse(f.read_text(),str(f))

if __name__=='__main__':unittest.main()

"""Failure-path methods use synthetic metadata, never simulated collisions."""
import contextlib,copy,io,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import contract,controller,writers

def runtime_fixture():
    return {'PDF':'cteq6l1','PDSUBLABEL':['cteq6l1']*2,'alpha_s_MZ':.13,'running_loops':1,'PDFSUP':[10042]*2,
        **{k:910001 for k in ['requested_seed','compiled_seed','native_base_seed','launch_seed','banner_seed','run_identity_seed']},
        'stage_offsets':{'iproc':0,'moffset':0},'alpha_values':[{'Q_GeV':q,'alpha_s':1/(1/.13+(23/3)/(2*math.pi)*math.log(q/91.188))}
            for q in [91.188,125,250,500,1000]],'probe_sha256':contract.sha(contract.HERE/'src/initialization_probe.f'),
        'source_manifest_sha256':contract.sha(contract.HERE/'configuration_lock.json')}

def card_fixture():
    return '\n'.join(v+' = '+k for k,v in {**contract.lock()['card_contract'],'iseed':'910001'}.items())

def include_fixture():
    return """      pdlabel='cteq6l1'
      pdsublabel(1)='cteq6l1'
      pdsublabel(2)='cteq6l1'
      iseed=910001
      nevents=0
      ebeam(1)=6500d0
      ebeam(2)=6500d0
      scalefact=.5d0
      dynamical_scale_choice=4
      fixed_ren_scale=.false.
      fixed_fac_scale1=.false.
      fixed_fac_scale2=.false.
"""

class Guards(unittest.TestCase):
    def test_valid_synthetic_contract(self):
        card=card_fixture();contract.verify_cards(card,card,card,include_fixture(),910001)
        contract.verify_runtime(runtime_fixture(),910001)

    def test_wrong_compiled_pdf(self):
        card=card_fixture()
        with self.assertRaisesRegex(ValueError,'COMPILED_PDF'):
            contract.verify_cards(card,card,card,include_fixture().replace("pdlabel='cteq6l1'","pdlabel='nn23lo1'"),910001)

    def test_inconsistent_pdf_labels(self):
        c=card_fixture()
        with self.assertRaisesRegex(ValueError,'COMPILED_PDF'):
            contract.verify_cards(c,c,c,include_fixture().replace("pdsublabel(2)='cteq6l1'","pdsublabel(2)='nn23lo1'"),910001)

    def test_wrong_alpha_order_and_numeric_curve(self):
        r=runtime_fixture();r['running_loops']=2
        with self.assertRaisesRegex(ValueError,'ALPHA_RUNNING'):contract.verify_runtime(r,910001)
        r=runtime_fixture();r['alpha_values'][2]['alpha_s']*=1.01
        with self.assertRaisesRegex(ValueError,'NUMERICAL_ALPHA'):contract.verify_runtime(r,910001)

    def test_header_runtime_disagreement(self):
        r=runtime_fixture();r['PDFSUP']=[247000]*2
        with self.assertRaisesRegex(ValueError,'HEADER_RUNTIME'):contract.verify_runtime(r,910001)

    def test_seed_reset(self):
        c=card_fixture()
        with self.assertRaisesRegex(ValueError,'SEED_RESET'):
            contract.verify_cards(c,c.replace('910001','0'),c,include_fixture(),910001)

    def test_continuation_effective_seed_mismatch(self):
        for key in ['native_base_seed','compiled_seed','launch_seed','banner_seed','run_identity_seed']:
            r=runtime_fixture();r[key]=21
            with self.assertRaisesRegex(ValueError,'SEED_MISMATCH'):contract.verify_runtime(r,910001)

    def test_missing_evidence_fails_closed(self):
        r=runtime_fixture();del r['probe_sha256']
        with self.assertRaisesRegex(ValueError,'MISSING_RUNTIME'):contract.verify_runtime(r,910001)

    def test_stale_or_cross_replica_grid(self):
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            root=Path(tmp);(root/'ftn26').write_text('SYNTHETIC_GRID_IDENTIFIER_ONLY')
            with self.assertRaisesRegex(ValueError,'STALE_GRID'):controller.grid_start(root,'survey')
            with self.assertRaisesRegex(ValueError,'CROSS_REPLICA'):controller.grid_start(root,'measurement',{'workspace':'different'})

    def test_unreviewed_native_writer(self):
        with self.assertRaisesRegex(ValueError,'UNREVIEWED_NATIVE_WRITER'):writers.suppress_writers('UNSAFE_SYNTHETIC_SOURCE')

    def test_unexpected_event_extension_or_disguised_record(self):
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            root=Path(tmp);p=root/'events.lhe';p.write_text('METHOD_ONLY_UNEXPECTED_EXTENSION')
            with self.assertRaisesRegex(ValueError,'UNEXPECTED_PHYSICAL'):writers.output_audit(root)
            p.unlink();p=root/'unexpected.data';p.write_bytes(b'\0<event>METHOD_ONLY_BOUNDARY_FIXTURE</event>')
            with self.assertRaisesRegex(ValueError,'DISGUISED_OUTPUT'):writers.output_audit(root)

    def test_method_controller_detects_unsafe_writer(self):
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            root=Path(tmp)
            def mock_writer():(root/'events.dat').write_text('METHOD_ONLY_NOT_PHYSICAL_DATA')
            mock_writer.METHOD_ONLY=True
            with self.assertRaisesRegex(ValueError,'UNEXPECTED_PHYSICAL'):controller.exercise_stage(root,mock_writer)

    def test_unauthorized_execute_before_io(self):
        with patch.object(controller,'safe_output',side_effect=AssertionError('no I/O allowed')):
            with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(controller.main(['--output','invalid','--execute']),2)

    def test_existing_output_overwrite(self):
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            with patch.object(controller,'safe_output',return_value=Path(tmp)):
                with self.assertRaisesRegex(ValueError,'OVERWRITE'):controller.prepare(tmp)

    def test_command_allowlist(self):
        controller.command_guard(['hh_integral_guarded','--seed','910001'])
        for name in controller.FORBIDDEN:
            with self.assertRaises(ValueError):controller.command_guard(['hh_integral_guarded',name])
        with self.assertRaises(ValueError):controller.command_guard(['arbitrary_executable'])

    def test_aggregate_budget_no_auto_expansion(self):
        def fixture():pass
        fixture.METHOD_ONLY=True
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            for kwargs in [{'elapsed_seconds':14400},{'cpu_seconds':14400},{'disk_bytes':5*1024**3}]:
                with self.assertRaisesRegex(ValueError,'RESOURCE_CEILING'):controller.exercise_stage(tmp,fixture,**kwargs)
            with self.assertRaisesRegex(ValueError,'NATIVE_EXECUTOR'):controller.exercise_stage(tmp,lambda:None)
        from .runtime_bridge import execute
        with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):execute(None,None,None,None,None)

    def test_within_between_replica_errors_separate(self):
        rows=[{'seed':s,'integrand_lock':'METHOD_ONLY','independent_grid':True,'sigma':v,'error':.1}
            for s,v in zip(contract.SEEDS,[1.,2.,3.,4.])]
        result=controller.convergence_method(rows)
        self.assertAlmostEqual(result['within_run_propagated_error_of_mean'],.05)
        self.assertGreater(result['between_replica_standard_error'],.6)
        rows[0]['integrand_lock']='different'
        with self.assertRaises(ValueError):controller.convergence_method(rows)

    def test_legacy_launches_are_closed_before_tool_access(self):
        from simulation.hh_signal.campaign import production,launch_adapter
        with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):production.generate_source(None,None,None,None,None,None)
        with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):launch_adapter.main()
        from simulation.hh_signal.campaign import controller as old
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            target=Path(tmp)/'must_not_be_created'
            with patch.object(old,'STATE',target),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as stopped:
                    old.main(['--phase','7b','--output',str(Path.home()/'simulations/hh_signal_runs/guard_test')])
                self.assertEqual(stopped.exception.code,2)
            self.assertFalse(target.exists())

    def test_source_tamper_and_missing_inventory(self):
        with tempfile.TemporaryDirectory(dir=contract.REPO) as tmp:
            p=Path(tmp)/'source.txt';p.write_text('METHOD_ONLY_SOURCE')
            with self.assertRaisesRegex(ValueError,'SOURCE_OR_CARD_CHANGED'):
                contract.validate_source_inventory([{'path':'source.txt','sha256':'0'*64}],tmp)
            with self.assertRaises(ValueError):contract.validate_source_inventory([],tmp)
            rows=[{'path':'source.txt','sha256':contract.sha(p)}];work=Path(tmp)/'runtime';work.mkdir()
            (Path(tmp)/'unexpected_outside.dat').write_text('METHOD_ONLY_UNEXPECTED_WRITE')
            with self.assertRaisesRegex(ValueError,'OUTSIDE_RUNTIME'):writers.workspace_envelope(tmp,rows,work)

if __name__=='__main__':unittest.main()

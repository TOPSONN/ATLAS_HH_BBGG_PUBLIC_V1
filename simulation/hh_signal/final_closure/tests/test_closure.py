import contextlib,io,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from ..src import contracts as c,controller,existing_analysis
from simulation.hh_signal.integration_audit.audit import save

class Closure(unittest.TestCase):
    def test_physical_modes_and_cli_tokens_are_denied_with_receipt(self):
        for mode in ['integration','corrected-signal']:
            with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
                out=Path(tmp)/'denied'
                with patch.object(controller,'safe_output',return_value=out),patch.object(controller,'input_identity',return_value=[{'METHOD_ONLY':True}]):
                    r=controller.execute(mode,out,authorization='AUTHORIZE_PHASE7_FINAL_INTEGRATION_ONLY')
                self.assertEqual(r['status'],'DENIED');self.assertTrue((out/'receipt.json').exists())
                self.assertEqual(r['new_integrals'],0);self.assertEqual(r['new_independent_events'],0)

    def test_safe_resume_rejects_output_tamper(self):
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
            out=Path(tmp)/'audit'
            with patch.object(controller,'safe_output',return_value=out),patch.object(controller,'input_identity',return_value=[]),patch.object(controller,'audit',return_value={'METHOD_ONLY':True}),patch.object(controller,'validate_evidence',return_value={'METHOD_ONLY':True}):
                controller.execute('audit',out);self.assertIn('resume',controller.execute('audit',out,True))
                (out/'receipt.json').write_text('{}')
                with self.assertRaises((ValueError,KeyError)):controller.execute('audit',out,True)

    def test_resume_source_change_and_extra_grid_rejected(self):
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
            out=Path(tmp)/'audit'
            with patch.object(controller,'safe_output',return_value=out),patch.object(controller,'input_identity',return_value=[]),patch.object(controller,'audit',return_value={'METHOD_ONLY':True}),patch.object(controller,'validate_evidence',return_value={'METHOD_ONLY':True}):
                controller.execute('audit',out)
                with patch.object(controller,'source_identity',return_value=['CHANGED_METHOD_ONLY']):
                    with self.assertRaisesRegex(ValueError,'UNSAFE_RESUME_SOURCE_CONFIG'):controller.execute('audit',out,True)
                (out/'ftn25').write_text('METHOD_ONLY_IMPORTED_GRID')
                with self.assertRaisesRegex(ValueError,'UNSAFE_RESUME_FILE_SET'):controller.execute('audit',out,True)

    def test_original_inventory_change_detected(self):
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
            p=Path(tmp)/'source.dat';p.write_text('METHOD_ONLY')
            rows=[{'path':'source.dat','bytes':p.stat().st_size,'sha256':c.sha(p)}];c.inventory(tmp,rows)
            p.write_text('METHOD_ONLY_CHANGED')
            with self.assertRaisesRegex(ValueError,'HISTORICAL_INPUT_MODIFIED'):c.inventory(tmp,rows)

    def test_invalid_lineage_and_double_BR_are_rejected_by_original_methods(self):
        from simulation.hh_signal.campaign.analysis import background_weight_factor
        with self.assertRaises(ValueError):background_weight_factor({'scope':'MODEL_BR_ONLY','status':'PASS_MODEL_BR_WEIGHT_CLOSURE','factor':.1,'factor_applications':2})

    def test_zero_survivor_interval_not_zero_background(self):
        upper=1-.05**(1/1000);self.assertGreater(upper,0.0029);self.assertLess(upper,0.0031)

    def test_wrong_installed_model_hash_fails(self):
        from ..src.plans import verify_model_sources
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
            p=Path(tmp)/'model.py';p.write_text('METHOD_ONLY_MODEL')
            with self.assertRaisesRegex(ValueError,'WRONG_MODEL_HASH'):verify_model_sources(tmp,{'model.py':'0'*64})

    def test_no_arbitrary_event_override_option(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as r:
            controller.main(['corrected-signal','--output','invalid','--events','10000'])
        self.assertEqual(r.exception.code,2)

if __name__=='__main__':unittest.main()

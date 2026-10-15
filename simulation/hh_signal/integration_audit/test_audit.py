"""Scientific failure detection and preparation safeguards; no generation."""
import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import audit,prepare,validate

class AuditTests(unittest.TestCase):
    def test_actual_all_evidence_and_independent_running(self):
        self.assertEqual(validate.validate()['C_effective_PDF_gate'],'FAIL')

    def test_effective_pdf_not_beam_sublabel(self):
        self.assertEqual(audit.pdf_consistency({'pdlabel':'cteq6l1'},
            {'pdlabel':'nn23lo1','pdsublabel(1)':'cteq6l1','pdsublabel(2)':'cteq6l1'},'nn23lo1')['status'],
            'FAIL_EFFECTIVE_PDF_MISMATCH')
        with self.assertRaisesRegex(ValueError,'UNKNOWN_RUNTIME_PDF'):
            audit.pdf_consistency({'pdlabel':'cteq6l1'},{'pdlabel':'cteq6l1'},'unknown')

    def test_duplicate_cards_and_includes_rejected(self):
        for parser,text in [(audit.card_values,'21=iseed\n22=iseed'),
                            (audit.include_values,"      PDLABEL='cteq6l1'\n      PDLABEL='nn23lo1'")]:
            with self.assertRaisesRegex(ValueError,'DUPLICATE'):parser(text)

    def test_error_inflation_and_tail_units(self):
        b=audit.log_diagnostics((audit.EVIDENCE/'7b_G1_numeric.log').read_text())
        c=audit.log_diagnostics((audit.EVIDENCE/'7c_G1_1_numeric.log').read_text())
        self.assertAlmostEqual(b['reconstructed_error_after_native_inflation_pb'],.00018503,delta=1e-7)
        self.assertEqual(len(c['iterations']),1);self.assertEqual(c['last_summary_chi2_field'],0)
        self.assertEqual(c['overweight_candidates'],416)
        self.assertAlmostEqual(c['tail_excess_percent_of_internal_abs_weight'],1.0021788225)
        self.assertGreater(c['last_summary_preinflation_error_pb'],0)
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):audit.log_diagnostics('')

    def test_running_orders_separable_at_retained_scales(self):
        self.assertAlmostEqual(validate.alpha_nf5(91.188,1),.13)
        self.assertAlmostEqual(validate.alpha_nf5(91.188,2),.13)
        self.assertGreater(abs(validate.alpha_nf5(250,1)-validate.alpha_nf5(250,2)),.0001)
        with self.assertRaises(ValueError):validate.alpha_nf5(1,2)

    def test_actual_prepared_manifest(self):
        self.assertEqual(prepare.validate_plan(audit.EVIDENCE/'prepared_plan')['new_integrals'],0)

    def test_plan_corruption_rejected(self):
        import shutil
        with tempfile.TemporaryDirectory(dir=audit.REPO,prefix='.phase7e_test_') as tmp:
            target=Path(tmp)/'plan';shutil.copytree(audit.EVIDENCE/'prepared_plan',target)
            p=target/'run_910001.dat';p.write_text(p.read_text()+'# changed\n')
            with self.assertRaisesRegex(ValueError,'PLAN_FILE_CHANGED'):prepare.validate_plan(target)

    def test_execution_denied_before_any_file_access(self):
        with patch.object(prepare,'safe_output',side_effect=AssertionError('must not access output')):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(prepare.main(['--output','irrelevant','--execute']),2)

    def test_seed_and_cost_guards_before_mg_import(self):
        for args in [['--seeds','21','2','3','4'],['--seeds','2','2','3','4'],['--points','1000']]:
            with patch.object(prepare,'safe_output',return_value=Path('nonexistent-audit-test-output')):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(prepare.main(['--output','irrelevant',*args]),2)

    def test_unsafe_output_rejected(self):
        for path in ['relative',str(Path.home()),str(Path.home()/'simulations/hh_signal_runs')]:
            with self.assertRaisesRegex(ValueError,'UNSAFE'):prepare.safe_output(Path(path))

    def test_native_preview_requires_global_and_both_beams(self):
        # Real native writer success is bound in preparation_cli_checks.json;
        # this suite verifies no mock is mistaken for native execution.
        p=audit.read(audit.EVIDENCE/'preparation_cli_checks.json')
        self.assertEqual([r['exit_code'] for r in p['cases']],[0,2,2,2])
        for seed in audit.read(audit.EVIDENCE/'prepared_plan/plan.json')['seeds']:
            values=audit.include_values((audit.EVIDENCE/f'prepared_plan/include_preview_{seed}.txt').read_text())
            self.assertTrue(all(values[k]=='cteq6l1' for k in ['pdlabel','pdsublabel(1)','pdsublabel(2)']))

if __name__=='__main__':unittest.main()

"""SYNTHETIC_METHOD_TEST controls for the independent HF evidence validator."""
from decimal import Decimal,localcontext
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_hf_evidence import close,moments,indicator

class IndependentHFEvidenceControls(unittest.TestCase):
    def test_decimal_variance_retains_large_offset_small_variation(self):
        with localcontext() as c:
            c.prec=70
            t,s,v,e=moments([Decimal('1000000000000.001'),Decimal('1000000000000.002'),Decimal('1000000000000.003')])
            self.assertEqual(v,Decimal('.000003'))

    def test_full_original_cohort_includes_zero_contributions(self):
        with localcontext() as c:
            c.prec=70
            # 4/3 is repeating at Decimal70; allow one last-place arithmetic
            # rounding bound, far tighter than the actual evidence tolerance.
            actual=moments([Decimal('.2'),Decimal(0),Decimal(0),Decimal(0)])[2]
            self.assertLessEqual(abs(actual-Decimal('.04')),Decimal('1e-69'))

    def test_signed_cancellation_does_not_become_no_variance(self):
        t,s,v,e=moments([Decimal('.1'),Decimal('-.1')])
        self.assertEqual(t,0);self.assertEqual(e,0);self.assertEqual(v,Decimal('.04'))

    def test_undefined_ess_must_stay_empty(self):
        close('',None,'ESS')
        with self.assertRaises(ValueError):close('0',None,'ESS')

    def test_nonfinite_or_wrong_summary_rejected(self):
        for value in ('NaN','Infinity','-.3'):
            with self.assertRaises(ValueError):close(value,Decimal('.2'),'sumw_pb')

    def test_numerical_agreement_is_bounded_not_exact_float_text(self):
        close('0.20000000000000001',Decimal('.2'),'sumw_pb')
        with self.assertRaises(ValueError):close('0.20001',Decimal('.2'),'sumw_pb')

    def test_unknown_origin_category_cannot_be_accepted(self):
        h=dict(jets=[],heavy_quark_birth_counts={},hard_process_flavour='ME_LIGHT_OR_GLUON',
               shower_bottom_births=0,shower_charm_births=0,direct_gluon_splitting_count=0,
               terminal_b_hadrons=0,terminal_c_hadrons=0,unclassified_quark_births=0,
               ambiguous_hadron_assignment_ids=[],native_reproduction_pass=True)
        with self.assertRaises(ValueError):indicator(h,'SILENT_NEW_PHYSICS_CATEGORY')
        self.assertTrue(indicator(h,'NATIVE_TAGS_0'))
        self.assertFalse(indicator(h,'HAS_ME_INITIAL_HEAVY_FLAVOUR_RECORD'))

if __name__=='__main__':unittest.main()
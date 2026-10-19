import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/validate_event_covariance.py'
spec=importlib.util.spec_from_file_location('phase11_independent_event_covariance',SCRIPT)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class IndependentCovarianceTests(unittest.TestCase):
    def test_validator_does_not_import_production(self):
        text=SCRIPT.read_text()
        for forbidden in ('from detector_events','import detector_events','import hf_stratification','import ROOT','subprocess'):
            self.assertNotIn(forbidden,text)
    def test_exact_numeric_comparison(self):
        audit.same('0.125',Fraction(1,8),'fixture')
    def test_numeric_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError,'RATIONAL_MISMATCH'):
            audit.same('0.1251',Fraction(1,8),'fixture')
    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError,'RATIONAL_MISMATCH'):
            audit.same('nan',Fraction(0),'fixture')
    def test_region_integer_masks_preserve_boundaries_and_exclusivity(self):
        native=[{'stages':[True]*5,'eligible_jets':[{'native_btag_bits':1},{'native_btag_bits':1}],'observables':{'m_gamma_gamma':m}} for m in (105.,120.,130.,160.,None)]
        origins=[{} for _ in native]
        lo=audit.vector('REGION:TAG_GE2:LOW_SIDEBAND',origins,native)
        hi=audit.vector('REGION:TAG_GE2:HIGGS_LIKE',origins,native)
        high=audit.vector('REGION:TAG_GE2:HIGH_SIDEBAND',origins,native)
        missing=audit.vector('REGION:TAG_GE2:UNDEFINED_MGG',origins,native)
        self.assertEqual((lo,hi,high,missing),(1,6,8,16))
        self.assertEqual(lo&hi,0);self.assertEqual(lo|hi|high|missing,31)
    def test_region_rejects_noneligible_event(self):
        native=[{'stages':[True,True,False,False,False],'eligible_jets':[],'observables':{'m_gamma_gamma':125.}}]
        self.assertEqual(audit.vector('REGION:TAG_0:HIGGS_LIKE',[{}],native),0)
    def test_unknown_vector_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNKNOWN_VECTOR'):
            audit.vector('unreviewed',[{}],[{}])

if __name__=='__main__':unittest.main()
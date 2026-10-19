"""Synthetic method/failure-path checks; no existing ROOT files are opened."""
from copy import deepcopy
from decimal import Decimal, localcontext
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import review_phase8 as review
import readiness

class ReviewMethods(unittest.TestCase):
    evidence_class='SYNTHETIC_METHOD_TEST'
    def test_original_cohort_zeros_are_retained(self):
        self.assertEqual(review.moment(list(map(Decimal,['1','0','0','0']))),Decimal(1))
    def test_all_constant_original_cohort_has_zero_sampling_variance(self):
        self.assertEqual(review.moment([Decimal('0.1')]*100),0)
    def test_centered_covariance_supports_anticorrelation(self):
        self.assertEqual(review.covariance(list(map(Decimal,[1,2,3])),list(map(Decimal,[3,2,1]))),-3)
    def test_covariance_rejects_different_cohorts(self):
        with self.assertRaisesRegex(ValueError,'COHORT_MISMATCH'):review.covariance([Decimal(1),Decimal(2)],[Decimal(1)])
    def test_large_common_offset_retains_small_variance(self):
        with localcontext() as ctx:
            ctx.prec=70
            self.assertEqual(review.moment([Decimal('1e30')+Decimal(i) for i in (1,2,3)]),3)
    def test_tag_bit0_is_distinct_from_any_nonzero(self):
        event={'eligible_jets':[dict(pt=40,eta=0,native_btag_bits=2,tagged=False,flavour=5)],'native_btag_multiplicity':0}
        self.assertEqual(review.validate_bit0_event(event),1)
    def test_native_flavour_cannot_replace_actual_tag(self):
        event={'eligible_jets':[dict(pt=40,eta=0,native_btag_bits=0,tagged=True,flavour=5)],'native_btag_multiplicity':1}
        with self.assertRaisesRegex(ValueError,'BIT0_TAG_MISMATCH'):review.validate_bit0_event(event)
    def test_noneligible_jet_is_rejected(self):
        event={'eligible_jets':[dict(pt=25,eta=0,native_btag_bits=0,tagged=False)],'native_btag_multiplicity':0}
        with self.assertRaisesRegex(ValueError,'NON_ELIGIBLE'):review.validate_bit0_event(event)
    def test_inconsistent_tag_multiplicity_is_rejected(self):
        event={'eligible_jets':[dict(pt=40,eta=0,native_btag_bits=1,tagged=True)],'native_btag_multiplicity':0}
        with self.assertRaisesRegex(ValueError,'MULTIPLICITY_MISMATCH'):review.validate_bit0_event(event)
    def test_mass_regions_are_exclusive_at_boundaries(self):
        for mass,expected in [(104.9,'OUTSIDE_MGG'),(105,'LOW'),(119.9,'LOW'),(120,'HIGGS'),(130,'HIGGS'),(130.1,'HIGH'),(160,'HIGH'),(160.1,'OUTSIDE_MGG'),(None,'UNDEFINED_MGG')]:
            e={'stages':[True,True,True,False,False],'native_btag_multiplicity':1,'observables':{'m_gamma_gamma':mass}}
            self.assertEqual(review.region(e),('TAG_1',expected))
    def test_mass_region_requires_photon_jet_eligibility(self):
        with self.assertRaisesRegex(ValueError,'ELIGIBILITY'):review.region({'stages':[True,False,False]})
    def test_duplicate_source_ordinal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'index.dat';line='E 1 1 h 1 x 0.1 1 10\n';p.write_text('ATLAS_DELPHES_INPUT_V1\n'+line+line)
            with self.assertRaisesRegex(ValueError,'DUPLICATE_INPUT_ORDINAL'):review.event_index(p)
    def test_unknown_index_format_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'index.dat';p.write_text('not_an_index\n')
            with self.assertRaisesRegex(ValueError,'UNSUPPORTED_INPUT_INDEX'):review.event_index(p)

class ReadinessGuards(unittest.TestCase):
    evidence_class='SYNTHETIC_METHOD_TEST'
    def setUp(self):
        self.review={'status':'PASS_INDEPENDENT_SCIENCE_REVIEW_WITH_PHYSICAL_BLOCKERS','reviewed_source_revision':readiness.PHASE8_REVISION}
        self.identity={'B_effective_PDF':'cteq6l1','B_effective_running_loops':1,'C_effective_PDF':'NNPDF23_lo_as_0130_qed_mem0','C_effective_running_loops':2}
        self.nuisances=[{'physical_value':'','correlation_model':''} for _ in range(22)]
    def result(self,negative=0):return readiness.assemble(self.review,self.identity,self.nuisances,negative,{})
    def test_missing_gate_cannot_pass(self):
        gates=self.result()['gates'];del gates['FAKE_PHOTON_ESTIMATION']
        with self.assertRaisesRegex(ValueError,'MISSING_OR_UNKNOWN'):readiness.validate_readiness_gates(gates)
    def test_unknown_fake_rate_cannot_become_zero(self):
        gates=self.result()['gates'];gates['FAKE_PHOTON_ESTIMATION']['physical_numerical_value']=0
        with self.assertRaisesRegex(ValueError,'BECAME_ZERO'):readiness.validate_readiness_gates(gates)
    def test_toy_nuisance_cannot_unlock_physical_inputs(self):
        self.nuisances[0]['physical_value']='0.01'
        with self.assertRaisesRegex(ValueError,'SUBSTITUTION'):self.result()
    def test_missing_nuisance_cannot_be_numeric_zero(self):
        self.nuisances[0]['physical_value']=0
        with self.assertRaisesRegex(ValueError,'SUBSTITUTION'):self.result()
    def test_negative_event_count_is_not_a_boolean_or_negative(self):
        for invalid in (-1,True):
            with self.assertRaisesRegex(ValueError,'INVALID_NEGATIVE_SOURCE_COUNT'):self.result(negative=invalid)
    def test_missing_correlations_cannot_be_filled_by_identity(self):
        self.nuisances[0]['correlation_model']='independent'
        with self.assertRaisesRegex(ValueError,'SUBSTITUTION'):self.result()
    def test_positive_current_inputs_do_not_unlock_physical_fit(self):
        result=self.result();self.assertEqual(result['PHYSICAL_TOTAL_BACKGROUND'],'BLOCKED')
        self.assertEqual(result['PHYSICAL_SIGNIFICANCE'],'NOT_EVALUATED');self.assertFalse(result['synthetic_fit_can_unlock_physical_inference'])
        self.assertEqual(len(result['blocking_or_unknown_gates']),8)
    def test_new_signed_input_requires_explicit_signed_model(self):
        result=self.result(negative=1)
        self.assertIn('SIGNED_EXPECTATION_MODEL_IF_APPLICABLE',result['blocking_or_unknown_gates'])
    def test_effective_signal_identity_cannot_be_silently_relabelled(self):
        self.identity['C_effective_PDF']='cteq6l1'
        with self.assertRaisesRegex(ValueError,'C_EFFECTIVE_IDENTITY'):self.result()
    def test_review_of_other_source_revision_is_rejected(self):
        self.review['reviewed_source_revision']='0'*40
        with self.assertRaisesRegex(ValueError,'WRONG_SOURCE_REVISION'):self.result()
    def test_unpassed_independent_review_is_rejected(self):
        self.review['status']='PENDING'
        with self.assertRaisesRegex(ValueError,'REVIEW_NOT_PASSED'):self.result()
    def test_nuisance_inventory_cannot_omit_category(self):
        self.nuisances.pop()
        with self.assertRaisesRegex(ValueError,'NOT_22'):self.result()

if __name__=='__main__':unittest.main()
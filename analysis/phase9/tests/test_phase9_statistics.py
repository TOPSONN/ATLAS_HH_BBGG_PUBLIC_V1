"""Synthetic numerical/edge guards for Phase9D/E, no existing-file or ROOT runs."""
from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import phase9_regions as regions
import phase9_statistics as diagnostics

def event(i,value,weight=1.,tag=2):
    return {'source_event_ordinal':i,'source_event_sha256':str(i).zfill(64),'source_weight_pb':weight,'stages':[True]*5,'native_btag_multiplicity':tag,'observables':{'m_gamma_gamma':value,'m_bb':100 if tag>=2 else None,'m_HH':350 if tag>=2 else None}}

class BinomialMethods(unittest.TestCase):
    evidence_class='SYNTHETIC_METHOD_TEST'
    def test_beta_uniform(self):
        for x in (.001,.1,.5,.9,.999):self.assertAlmostEqual(diagnostics.beta_cdf(x,1,1),x,places=13)
    def test_beta_inverse_uniform(self):
        for p in (.025,.5,.975):self.assertAlmostEqual(diagnostics.beta_quantile(p,1,1),p,places=13)
    def test_cp_single_trial_edges(self):
        a=diagnostics.binomial_intervals(0,1);b=diagnostics.binomial_intervals(1,1)
        self.assertEqual(a['lower'],0);self.assertAlmostEqual(a['upper'],.975,places=13)
        self.assertAlmostEqual(b['lower'],.025,places=13);self.assertEqual(b['upper'],1)
    def test_zero_bounds_are_not_zero_rates(self):
        r=diagnostics.binomial_intervals(0,1000)
        self.assertEqual(r['wilson_lower'],0.);self.assertGreater(r['upper'],0);self.assertAlmostEqual(r['one_sided95_upper_if_zero'],1-.05**.001,places=14)
        self.assertGreater(r['upper'],r['one_sided95_upper_if_zero'])
    def test_cp_symmetry(self):
        a=diagnostics.binomial_intervals(1,1000);b=diagnostics.binomial_intervals(999,1000)
        self.assertAlmostEqual(a['lower'],1-b['upper'],places=12);self.assertAlmostEqual(a['upper'],1-b['lower'],places=12)
    def test_wilson_includes_observed_rate(self):
        for k in (0,1,143,1000):
            r=diagnostics.binomial_intervals(k,1000);self.assertLessEqual(r['wilson_lower'],r['acceptance']+1e-15);self.assertGreaterEqual(r['wilson_upper'],r['acceptance']-1e-15)
    def test_invalid_binomial_cohort_is_rejected(self):
        for k,n in ((-1,10),(11,10),(0,0),(True,10)):
            with self.assertRaisesRegex(ValueError,'INVALID_BINOMIAL_COHORT'):diagnostics.binomial_intervals(k,n)
    def test_zero_survivor_planning_is_not_finite_guarantee(self):
        plan=diagnostics.planning(diagnostics.binomial_intervals(0,1000),.2)
        self.assertIsNone(plan['point_acceptance']);self.assertIsNone(plan['required_new_independent_campaign_N_at_point']);self.assertIsNone(plan['conservative_N_at_CP95_lower_acceptance'])
    def test_planning_precision_quadratic_scaling(self):
        interval=diagnostics.binomial_intervals(1,1000)
        self.assertEqual(diagnostics.planning(interval,.2)['required_new_independent_campaign_N_at_point'],24975)
        self.assertEqual(diagnostics.planning(interval,.3)['required_new_independent_campaign_N_at_point'],11100)
        self.assertEqual(diagnostics.planning(interval,.5)['required_new_independent_campaign_N_at_point'],3996)
    def test_conservative_planning_is_larger_than_point(self):
        r=diagnostics.planning(diagnostics.binomial_intervals(1,1000),.3)
        self.assertGreater(r['conservative_N_at_CP95_lower_acceptance'],r['required_new_independent_campaign_N_at_point'])

class RegionShapeMethods(unittest.TestCase):
    evidence_class='SYNTHETIC_METHOD_TEST'
    def test_fixed_original_N_keeps_unselected_zeros(self):
        self.assertEqual(regions.fixed_n_variance([1.],4),1.)
    def test_shape_variance_includes_bin_total_covariance(self):
        h=regions.histogram([event(i,x) for i,x in enumerate((.25,.25,1.25,1.25),1)],'m_gamma_gamma',[0,1,2],4)
        self.assertAlmostEqual(h['bins'][0]['value'],.5);self.assertAlmostEqual(h['bins'][0]['variance'],1/12)
        self.assertNotAlmostEqual(h['bins'][0]['variance'],2/16)
    def test_constant_model_BR_cancels_from_shape_variance(self):
        a=regions.histogram([event(i,x) for i,x in enumerate((.25,.25,1.25,1.25),1)],'m_gamma_gamma',[0,1,2],4)
        b=regions.histogram([event(i,x,.002) for i,x in enumerate((.25,.25,1.25,1.25),1)],'m_gamma_gamma',[0,1,2],4)
        self.assertAlmostEqual(a['bins'][0]['variance'],b['bins'][0]['variance']);self.assertEqual(a['bins'][0]['value'],b['bins'][0]['value'])
    def test_flow_bins_are_part_of_normalization(self):
        h=regions.histogram([event(1,-1),event(2,.5),event(3,2)],'m_gamma_gamma',[0,1,2],3)
        self.assertAlmostEqual(h['underflow']['value'],1/3);self.assertAlmostEqual(h['bins'][0]['value'],1/3);self.assertAlmostEqual(h['overflow']['value'],1/3)
    def test_missing_is_not_zero_mass(self):
        h=regions.histogram([event(1,None),event(2,.5)],'m_gamma_gamma',[0,1,2],2)
        self.assertEqual(h['missing'],1);self.assertEqual(h['N_defined'],1);self.assertEqual(h['bins'][0]['value'],1)
    def test_empty_shape_is_undefined(self):
        h=regions.histogram([],'m_gamma_gamma',[0,1],1000)
        self.assertIsNone(h['bins'][0]['value']);self.assertIsNone(h['bins'][0]['variance']);self.assertEqual(h['bins'][0]['quality_flag'],'EMPTY_BIN')
    def test_signed_cancellation_is_not_regularized(self):
        h=regions.histogram([event(1,.5,1),event(2,1.5,-1)],'m_gamma_gamma',[0,1,2],2)
        self.assertEqual(h['status'],'UNDEFINED_EMPTY_OR_CANCELLATION');self.assertIsNone(h['bins'][0]['value'])
    def test_weighted_mean_uses_original_cohort_covariance(self):
        m=regions.weighted_mean([event(i,x) for i,x in enumerate((0.,0.,1.,1.),1)],'m_gamma_gamma',4)
        self.assertEqual(m['mean'],.5);self.assertAlmostEqual(m['mean_variance'],1/12)
    def test_no_fake_bb_candidate_in_zero_tag_region(self):
        e=event(1,125,tag=0);self.assertEqual(regions.region_key(e),('TAG_0','HIGGS'))
        e['observables']['m_bb']=0
        with self.assertRaisesRegex(ValueError,'NULL_TAG_PAIR'):regions.region_key(e)
    def test_exact_mass_boundaries(self):
        for x,expected in ((105,'LOW'),(120,'HIGGS'),(130,'HIGGS'),(160,'HIGH'),(160.01,'OUTSIDE_MGG'),(None,'UNDEFINED_MGG')):
            self.assertEqual(regions.region_key(event(1,x)),('TAG_GE2',expected))
    def test_identical_shapes_have_zero_distances(self):
        h=regions.histogram([event(1,.5),event(2,1.5)],'m_gamma_gamma',[0,1,2],2);m=regions.shape_metrics(h,h)
        self.assertAlmostEqual(m['JS_natural_log'],0);self.assertAlmostEqual(m['CDF_sup_distance'],0)
    def test_disjoint_shapes_have_ln2_JS_and_unit_CDF_distance(self):
        a=regions.histogram([event(1,.5)],'m_gamma_gamma',[0,1,2],2);b=regions.histogram([event(1,1.5)],'m_gamma_gamma',[0,1,2],2);m=regions.shape_metrics(a,b)
        self.assertAlmostEqual(m['JS_natural_log'],math.log(2));self.assertEqual(m['CDF_sup_distance'],1)
        self.assertIsNone(m['ratio_bins'][1]['ratio'])
    def test_negative_probability_shape_is_not_used_for_JS(self):
        a=regions.histogram([event(1,.5,2),event(2,1.5,-1)],'m_gamma_gamma',[0,1,2],2);b=regions.histogram([event(1,.5)],'m_gamma_gamma',[0,1,2],2)
        self.assertEqual(regions.shape_metrics(a,b)['status'],'UNSUPPORTED_SIGNED_PROBABILITY_SHAPE')
    def test_nonfinite_observable_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'NONFINITE_OBSERVABLE'):regions.histogram([event(1,float('nan'))],'m_gamma_gamma',[0,1],2)
    def test_unsorted_edges_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'INVALID_EDGES'):regions.histogram([],'m_gamma_gamma',[0,1,.5],2)

if __name__=='__main__':unittest.main()
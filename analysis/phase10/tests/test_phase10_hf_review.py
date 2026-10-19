"""Independent selected arithmetic/graph controls; no physical production."""
import importlib.util
import hashlib
import math
from pathlib import Path
import sys
import unittest
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'source'))
from hf_stratification import fixed_cov,summary,conditional,rare_exact,me_class,flags,validate_join,shape_population_pair,wilson
spec=importlib.util.spec_from_file_location('independent_phase10_review',BASE/'scripts/review_phase9.py');review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


def particle(pid,pdg,status,mothers=(),daughters=(),hadron=False):
    return dict(pythia_index=pid,pdg_id=pdg,status=status,mothers=list(mothers),daughters=list(daughters),is_hadron=hadron,terminal_b_hadron=False,terminal_c_hadron=False,p4_gev=[1.,0.,0.,1.])


def event():
    h=dict(hard_process_flavour='ME_LIGHT_OR_GLUON',heavy_quark_birth_counts={},shower_bottom_births=2,shower_charm_births=1,direct_gluon_splitting_count=1,terminal_b_hadrons=2,terminal_c_hadrons=1,unclassified_quark_births=0,ambiguous_hadron_assignment_ids=[],native_reproduction_pass=True,jets=[dict(index=0,native_flavour=5,heavy_hadron_flavour=5,tagged=True,native_attainable_labels=[4,5],sole_hadron_endpoint='UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED')])
    return dict(dataset_id='B03',source_event_index=1,source_event_sha256='a'*64,hepmc_event_sha256='b'*64,stages=[True]*5,weight_pb=.01,hard_outgoing_pdg_ids=[1,21,22,22],heavy_flavour=h)


class EventStatistics(unittest.TestCase):
    def test_fixed_n_covariance_has_nonexclusive_shared_event_term(self):
        self.assertAlmostEqual(fixed_cov([1.,0.,0.,0.],[1.,1.,0.,0.]),2/3)
    def test_fixed_n_zeros_preserved(self):
        self.assertAlmostEqual(summary([True,False,False,False],[2.]*4)['fixed_N_variance_pb2'],4.)
    def test_multiple_jets_are_one_event(self):
        f=flags(event());self.assertTrue(f['HAS_SHOWER_BOTTOM_BIRTH'] and f['HAS_SHOWER_CHARM_BIRTH'] and f['HAS_DIRECT_G_TO_HEAVY_PAIR']);self.assertTrue(f['NATIVE_TAGS_1'])
    def test_zero_has_no_finite_relative_precision(self):
        r=summary([False]*4,[2.]*4);self.assertIsNone(r['relative_source_sampling_SE']);self.assertIsNone(r['ESS']);self.assertGreater(r['zero_one_sided95_upper'],0)
    def test_wilson_zero_and_full_exact_boundary_contract(self):
        self.assertEqual(wilson(0,1000)[0],0.);self.assertEqual(wilson(1000,1000)[1],1.);self.assertGreater(wilson(0,1000)[1],0.);self.assertLess(wilson(1000,1000)[0],1.)
    def test_exact_zero_interval(self):
        lo,hi,one=rare_exact(0,1000);self.assertEqual(lo,0);self.assertAlmostEqual(hi,.0036820838968657545,14);self.assertAlmostEqual(one,.002991249545095296,14)
    def test_rare_one_interval_matches_independent_numeric(self):
        lo,hi,_=rare_exact(1,1000);self.assertAlmostEqual(lo,0.00002531748749103,13);self.assertAlmostEqual(hi,.005558924279826677,12)
    def test_conditional_empty_denominator(self):
        r=conditional([False]*4,[False]*4,[2.]*4);self.assertIsNone(r['weighted_acceptance']);self.assertIsNone(r['acceptance'])
    def test_weighted_shared_denominator(self):
        r=conditional([True,False,False,False],[True,True,False,False],[1.,2.,3.,4.]);self.assertAlmostEqual(r['weighted_acceptance'],1/3);self.assertGreater(r['weighted_acceptance_variance'],0)
    def test_signed_weight_sign_preserved(self):
        r=summary([True]*4,[2.,-1.,0.,0.]);self.assertEqual(r['sumw_pb'],1);self.assertEqual(r['sumw2_pb2'],5)
    def test_incomplete_cohort_rejected(self):
        with self.assertRaisesRegex(ValueError,'INVALID_FULL_COHORT'):summary([True],[1.,2.])
    def test_decimal_fixed_n_is_separate_formula(self):
        m=review.independent_moments([2.,0.,0.,0.]);self.assertEqual(float(m['variance']),4.)


class OriginContracts(unittest.TestCase):
    def test_me_flavour_separate_from_shower_and_native(self):
        self.assertEqual(me_class([1,21,22,22]),'ME_LIGHT_OR_GLUON');self.assertTrue(flags(event())['HARD_LIGHT_NATIVE_HEAVY'])
    def test_unknown_hadron_endpoint_must_survive(self):
        e=event();n=dict(dataset_id='B03',source_event_ordinal=1,source_event_sha256=e['source_event_sha256'],hepmc_event_sha256=e['hepmc_event_sha256'],stages=e['stages'],source_weight_pb=.01,eligible_jets=[dict(index=0,flavour=5,tagged=True)])
        validate_join(e,n);e['heavy_flavour']['jets'][0]['sole_hadron_endpoint']='GLUON_CONFIRMED'
        with self.assertRaisesRegex(ValueError,'UNKNOWN_HADRON_ENDPOINT_LOST'):validate_join(e,n)
    def test_native_boundary_not_collapsed(self):self.assertTrue(flags(event())['HAS_NATIVE_FLAVOUR_BOUNDARY_AMBIGUITY'])
    def test_me_records_take_precedence_over_same_flavour_copy(self):
        p=[particle(1,5,-21),particle(2,5,-23,[1]),particle(3,5,-51,[2])];r=review.graph_births(p)
        self.assertEqual(r['heavy_quark_birth_counts'],{'ME_INITIAL_HEAVY_FLAVOUR_RECORD':1,'ME_HEAVY_FLAVOUR_RECORD':1});self.assertEqual(r['shower_bottom_births'],0)
    def test_direct_gluon_pair_requires_both_signed_children(self):
        p=[particle(1,21,-51,(),[2,3]),particle(2,5,-51,[1]),particle(3,-5,-51,[1])];r=review.graph_births(p);self.assertEqual(r['direct_gluon_splitting_mothers'],[1]);self.assertEqual(r['shower_bottom_births'],2)
        p[2]['pdg_id']=4;self.assertEqual(review.graph_births(p)['direct_gluon_splitting_mothers'],[])
    def test_shower_status_required_for_pair_mother(self):
        p=[particle(1,21,-23,(),[2,3]),particle(2,5,-51,[1]),particle(3,-5,-51,[1])];self.assertEqual(review.graph_births(p)['direct_gluon_splitting_mothers'],[])
    def test_bit0_does_not_use_flavour_or_nonzero_bits(self):
        e=dict(photons=[dict(index=0,pt=80.,eta=0.,phi=0.),dict(index=1,pt=70.,eta=0.,phi=math.pi)],all_jets=[dict(index=0,pt=50.,eta=0.,native_btag_bits=2,flavour=5),dict(index=1,pt=40.,eta=0.,native_btag_bits=1,flavour=0)])
        stages,_,_,tags,_=review.independent_selection(e);self.assertEqual(len(tags),1);self.assertFalse(stages[3])
    def test_fiducial_strict_edges_and_open_crack(self):
        e=dict(photons=[dict(index=0,pt=35.,eta=1.37,phi=0.),dict(index=1,pt=25.,eta=1.52,phi=math.pi)],all_jets=[])
        stages,p,*_=review.independent_selection(e);self.assertEqual(len(p),1);self.assertFalse(stages[1])


class ShapePopulationContracts(unittest.TestCase):
    def events(self,values,weights=None):
        return [dict(stages=[True]*5,weight_pb=w,observables={'m_gamma_gamma':x}) for x,w in zip(values,weights or [1.]*len(values))]
    def test_same_population_shape(self):
        r=shape_population_pair(self.events([1.,2.]),self.events([1.,2.]),0,'m_gamma_gamma',[0.,1.5,3.]);self.assertAlmostEqual(r['JS_natural_log'],0);self.assertAlmostEqual(r['CDF_sup_distance'],0)
    def test_zero_support_is_undefined(self):
        r=shape_population_pair(self.events([]),self.events([1.]),0,'m_gamma_gamma',[0.,2.]);self.assertIsNone(r['JS_natural_log']);self.assertEqual(r['shape_status'],'UNDEFINED_EMPTY_OR_ZERO_WEIGHT_SUPPORT')
    def test_flow_bins_included_and_separate_source_normalization(self):
        r=shape_population_pair(self.events([-1.,4.],[1.,3.]),self.events([1.,1.]),0,'m_gamma_gamma',[0.,2.]);self.assertEqual(r['nonempty_bins_a'],2);self.assertEqual(r['source_sumw_a_pb'],4.);self.assertAlmostEqual(r['JS_natural_log'],math.log(2));self.assertFalse(r['physical_sum_allowed'])
    def test_signed_probability_not_invented(self):
        r=shape_population_pair(self.events([1.,3.],[-1.,2.]),self.events([1.]),0,'m_gamma_gamma',[0.,2.,4.]);self.assertEqual(r['shape_status'],'UNSUPPORTED_SIGNED_SHAPE');self.assertIsNone(r['JS_natural_log'])



class PublicationRevisionContracts(unittest.TestCase):
    def test_exact_three_delivery_paths_allowed(self):
        paths=set(review.EXPECTED_DELIVERY_PATHS);self.assertEqual(review.validate_delivery_boundary(paths,paths),paths)
    def test_arbitrary_executable_source_change_forbidden(self):
        with self.assertRaisesRegex(ValueError,'EXECUTED_SOURCE_CHANGED_BEYOND_DECLARED_DELIVERY'):
            review.validate_delivery_boundary(review.EXPECTED_DELIVERY_PATHS|{'analysis/phase9/scripts/phase9_origins.py'},review.EXPECTED_DELIVERY_PATHS)
    def test_tampered_delivery_allowlist_forbidden(self):
        with self.assertRaisesRegex(ValueError,'TAMPERED_DELIVERY_ALLOWLIST'):
            review.validate_delivery_boundary(review.EXPECTED_DELIVERY_PATHS,review.EXPECTED_DELIVERY_PATHS|{'analysis/phase9/scripts/phase9_origins.py'})


    def test_future_worktree_variation_is_not_historical_change(self):
        raw=b'frozen phase9 bytes\n';digest=hashlib.sha256(raw).hexdigest()
        self.assertFalse(review.verify_frozen_publication_blob(raw,raw,digest,len(raw),b'new phase10 build option\n'))
    def test_saved_remote_tamper_rejected(self):
        raw=b'frozen phase9 bytes\n'
        with self.assertRaisesRegex(ValueError,'EXACT_SAVED_REMOTE_BASE_BLOB_IDENTITY'):
            review.verify_frozen_publication_blob(raw,raw+b'changed',hashlib.sha256(raw).hexdigest(),len(raw))
    def test_base_blob_tamper_rejected(self):
        raw=b'frozen phase9 bytes\n'
        with self.assertRaisesRegex(ValueError,'EXACT_SAVED_REMOTE_BASE_BLOB_IDENTITY'):
            review.verify_frozen_publication_blob(raw+b'changed',raw,hashlib.sha256(raw).hexdigest(),len(raw))



class HistoricalHistogramSchemaContracts(unittest.TestCase):
    def fixture(self):
        h=[dict(status='DEFINED',dimension=1,numerical_content_sha256='a'*64)]*4052+[dict(status='DEFINED',dimension=2,numerical_content_sha256='b'*64)]*616+[dict(status='UNDEFINED_ILL_CONDITIONED_OR_EMPTY_SHAPE',numerical_content_sha256=None)]*132
        return dict(histograms=h,numerical_histogram_content_sha256='c'*64),dict(TH1D_count=4052,TH2D_count=616,numerical_histogram_content_sha256='c'*64)
    def test_descriptors_include_undefined_shapes_without_ROOT_objects(self):
        m,r=self.fixture();out=review.validate_historical_histogram_binding(m,r);self.assertEqual(out['logical_descriptors'],4800);self.assertEqual(out['actual_ROOT_objects'],4668);self.assertEqual(out['undefined_shape_descriptors'],132)
    def test_native_object_count_tamper_rejected(self):
        m,r=self.fixture();r['TH1D_count']+=1
        with self.assertRaisesRegex(ValueError,'HISTORICAL_ROOT_OBJECT_DESCRIPTOR_COUNT'):review.validate_historical_histogram_binding(m,r)
    def test_canonical_digest_tamper_rejected(self):
        m,r=self.fixture();r['numerical_histogram_content_sha256']='d'*64
        with self.assertRaisesRegex(ValueError,'HISTORICAL_ROOT_CANONICAL_DIGEST_CHANGED'):review.validate_historical_histogram_binding(m,r)
    def test_undefined_shape_must_not_invent_dimension(self):
        m,r=self.fixture();m['histograms'][-1]=dict(status='UNDEFINED_ILL_CONDITIONED_OR_EMPTY_SHAPE',numerical_content_sha256=None,dimension=1)
        with self.assertRaisesRegex(ValueError,'UNDEFINED_HISTOGRAM_DESCRIPTOR_BECAME_OBJECT'):review.validate_historical_histogram_binding(m,r)

if __name__=='__main__':unittest.main()

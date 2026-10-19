import copy
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from detector_events import covariance, diagnose_events, event_features, joined_records, mass_region, summarize

REGIONS={'mass_regions':[{'id':'LOW_SIDEBAND','min':105,'max':120,'min_inclusive':True,'max_inclusive':False},{'id':'HIGGS_LIKE','min':120,'max':130,'min_inclusive':True,'max_inclusive':True},{'id':'HIGH_SIDEBAND','min':130,'max':160,'min_inclusive':False,'max_inclusive':True}],'undefined_region':'UNDEFINED_MGG','outside_region':'OUTSIDE_MGG'}

def pair(ds='B01',ordinal=1,tags=2,mass=125.,weight=.1):
    flavour=5 if ds=='B01' else 4 if ds=='B02' else 0
    pdgs=[5,-5,22,22] if ds=='B01' else [4,-4,22,22] if ds=='B02' else [21,1,22,22]
    jets=[{'index':i,'native_flavour':flavour,'tagged':i<tags,'sole_hadron_endpoint':'UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED'} for i in range(2)]
    stages=[True,True,True,tags>=2,tags>=2 and mass is not None and 105<=mass<=160]
    origin={'dataset_id':ds,'source_event_index':ordinal,'source_event_sha256':ds+str(ordinal),'hepmc_event_sha256':'h'+ds+str(ordinal),'stages':stages,'weight_pb':weight,'model_br_factor':1.,'hard_outgoing_pdg_ids':pdgs,'heavy_flavour':{'jets':jets,'hard_process_flavour':'ME_BOTTOM' if flavour==5 else 'ME_CHARM' if flavour==4 else 'ME_LIGHT_OR_GLUON','heavy_quark_birth_counts':{},'shower_bottom_births':0,'shower_charm_births':1,'direct_gluon_splitting_count':0,'terminal_b_hadrons':int(flavour==5),'terminal_c_hadrons':int(flavour==4),'unclassified_quark_births':0,'ambiguous_hadron_assignment_ids':[]},'pythia_mapping':{'ambiguous_or_missing':0}}
    native={'dataset_id':ds,'source_event_ordinal':ordinal,'source_event_sha256':origin['source_event_sha256'],'hepmc_event_sha256':origin['hepmc_event_sha256'],'stages':stages[:],'source_weight_pb':weight,'model_factor_applied':0,'eligible_jets':[{'index':j['index'],'flavour':flavour,'tagged':j['tagged'],'native_btag_bits':int(j['tagged']),'pt':60.,'eta':.5} for j in jets],'native_btag_multiplicity':tags,'selected_photon_multiplicity':2,'photons':[{'index':0,'pt':45.,'eta':.5,'selected':True},{'index':1,'pt':30.,'eta':-.5,'selected':True}],'observables':{'m_gamma_gamma':mass}}
    return origin,native

class EventCovarianceTests(unittest.TestCase):
    def test_fraction_independent_moment(self):
        x=[.1,0.,.3,0.];y=[0.,.2,.3,0.]
        a=[Fraction(str(v)) for v in x];b=[Fraction(str(v)) for v in y];n=len(x)
        expected=Fraction(n,n-1)*(sum(p*q for p,q in zip(a,b))-sum(a)*sum(b)/n)
        self.assertAlmostEqual(covariance(x,y),float(expected),17)
    def test_disjoint_categories_anticorrelate(self):
        self.assertLess(covariance([1,0,0],[0,1,0]),0)
    def test_covariance_symmetric(self):
        self.assertEqual(covariance([-.2,0,.3],[0,.2,.3]),covariance([0,.2,.3],[-.2,0,.3]))
    def test_original_N_includes_failures(self):
        self.assertAlmostEqual(covariance([1,0,0,0],[1,0,0,0]),1.)
    def test_signed_weight_cancellation(self):
        result=summarize([True,True],[.1,-.1]);self.assertEqual(result['sumw_pb'],0);self.assertEqual(result['ESS_signed_sum'],0);self.assertGreater(result['fixed_N_variance_pb2'],0)
    def test_zero_is_upper_limit_not_physical_zero(self):
        result=summarize([False]*1000,[1.]*1000)
        self.assertAlmostEqual(result['zero_one_sided95_acceptance_upper'],.002991249545095296)
        self.assertIsNone(result['physical_normalization_uncertainty'])
    def test_reject_nonfinite_weight(self):
        with self.assertRaisesRegex(ValueError,'NONFINITE'):
            summarize([True,True],[1.,float('nan')])
    def test_reject_singleton_covariance(self):
        with self.assertRaisesRegex(ValueError,'ORIGINAL'):
            covariance([1.],[1.])

class FrozenRegionTests(unittest.TestCase):
    def test_exact_boundaries(self):
        expected={104.99:'OUTSIDE_MGG',105.:'LOW_SIDEBAND',119.999:'LOW_SIDEBAND',120.:'HIGGS_LIKE',130.:'HIGGS_LIKE',130.001:'HIGH_SIDEBAND',160.:'HIGH_SIDEBAND',160.01:'OUTSIDE_MGG'}
        for value,region in expected.items():self.assertEqual(mass_region(value,REGIONS),region)
    def test_null_not_zero(self):
        self.assertEqual(mass_region(None,REGIONS),'UNDEFINED_MGG');self.assertEqual(mass_region(0.,REGIONS),'OUTSIDE_MGG')
    def test_reject_nonfinite_mass(self):
        with self.assertRaisesRegex(ValueError,'NONFINITE'):
            mass_region(float('inf'),REGIONS)
    def test_reject_overlapping_regions(self):
        altered=copy.deepcopy(REGIONS);altered['mass_regions'][0]['max_inclusive']=True
        with self.assertRaisesRegex(ValueError,'OVERLAPPING'):
            mass_region(120.,altered)

class JoinAndMigrationTests(unittest.TestCase):
    def test_duplicate_source_key_rejected(self):
        a,b=pair()
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            joined_records([a,a],[b,b])
    def test_identity_tamper_rejected(self):
        a,b=pair();b['source_event_sha256']='tamper'
        with self.assertRaisesRegex(ValueError,'EVENT_JOIN'):
            joined_records([a],[b])
    def test_native_tag_bit_tamper_rejected(self):
        a,b=pair();b['eligible_jets'][0]['native_btag_bits']=0
        with self.assertRaisesRegex(ValueError,'BIT0'):
            joined_records([a],[b])
    def test_nested_stage_tamper_rejected(self):
        a,b=pair();a['stages']=[True,False,True,True,True];b['stages']=a['stages'][:]
        with self.assertRaisesRegex(ValueError,'NON_NESTED'):
            joined_records([a],[b])
    def test_weight_tamper_rejected(self):
        a,b=pair();b['source_weight_pb']=.2
        with self.assertRaisesRegex(ValueError,'WEIGHT_JOIN'):
            joined_records([a],[b])
    def test_hf_extra_branching_factor_rejected(self):
        a,b=pair();a['model_br_factor']=.002
        with self.assertRaisesRegex(ValueError,'BR_MUST'):
            joined_records([a],[b])
    def test_me_flavour_tamper_rejected(self):
        a,b=pair();a['heavy_flavour']['hard_process_flavour']='ME_LIGHT_OR_GLUON'
        with self.assertRaisesRegex(ValueError,'ME_FLAVOUR'):
            event_features(a)
    def test_unknown_origin_preserved(self):
        a,b=pair();flags=event_features(a);self.assertTrue(flags['UNKNOWN_HADRON_ENDPOINT']);self.assertFalse(flags['UNKNOWN_QUARK_BIRTH'])
    def test_three_sources_kept_separate_and_covariance_fullN(self):
        pairs=[]
        for ds in ('B01','B02','B03'):
            pairs.extend([pair(ds,1),pair(ds,2,tags=1,mass=110.,weight=-.05)])
        joined=joined_records([p[0] for p in pairs],[p[1] for p in pairs])
        counts,migration,cov,summary=diagnose_events(joined,REGIONS,require_full=False)
        self.assertEqual(set(summary),{'B01','B02','B03'})
        self.assertFalse(any(row['dataset_id']=='TOTAL' for row in cov))
        for ds,s in summary.items():
            self.assertEqual(s['exclusive_terminal_migration'],{'PASS_FINAL':1,'FAIL_TAGS':1})
            self.assertIsNone(s['cross_dataset_covariance'])
            self.assertEqual(sum(v['events'] for v in s['regions'].values()),2)
            self.assertEqual(s['stages']['04_MGG_105_160']['original_N'],2)
        self.assertTrue(all(row['original_N']==2 for row in cov))
    def test_two_fiducial_photons_insufficient_leading_pt(self):
        a,b=pair();b['photons'][0]['pt']=35.;a['stages']=[True,False,False,False,False];b['stages']=a['stages'][:]
        self.assertEqual(len(joined_records([a],[b])),1)
    def test_leading_pt_strict_boundary(self):
        a,b=pair();b['photons'][0]['pt']=35.0001
        self.assertEqual(len(joined_records([a],[b])),1)
    def test_crack_open_boundary(self):
        a,b=pair();b['photons'][0]['eta']=1.37
        self.assertEqual(len(joined_records([a],[b])),1)
        b['photons'][0]['eta']=1.37001
        with self.assertRaisesRegex(ValueError,'PHOTON_ACCEPTANCE'):
            joined_records([a],[b])
    def test_full_cohort_guard(self):
        with self.assertRaisesRegex(ValueError,'FULL_1000'):
            diagnose_events([pair()],REGIONS)
    def test_inactive_diff_is_only_comments(self):
        path=Path(__file__).resolve().parents[1]/'config/inactive_detector_diff.txt'
        self.assertTrue(all(not line.strip() or line.lstrip().startswith('#') for line in path.read_text().splitlines()))
        self.assertIn('BLOCKED_REQUIRES_REVIEWED_WRITER',path.read_text())
    def test_source_has_no_native_production_dispatch(self):
        path=Path(__file__).resolve().parents[1]/'source/detector_events.py'
        text=path.read_text()
        for forbidden in ('import ROOT','subprocess','os.system','generate_events','DelphesHepMC'):
            self.assertNotIn(forbidden,text)

if __name__=='__main__':unittest.main()
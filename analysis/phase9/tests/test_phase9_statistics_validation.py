"""SYNTHETIC_METHOD_TEST for independent Decimal70 statistical verification."""
import copy
from decimal import Decimal,localcontext
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_statistics import (bucket,compare,derive_stages,mass_region,moments,normalized_delta,number,region_for,variance)

class IndependentStatisticsControls(unittest.TestCase):
    def event(self):
        return dict(observables=dict(photon1_pT=40.,photon2_pT=30.,photon1_eta=.2,photon2_eta=.4,m_gamma_gamma=125.,m_bb=100.,m_HH=400.),
                    eligible_jets=[dict(pt=50.,eta=.2,native_btag_bits=1,tagged=True),dict(pt=40.,eta=.3,native_btag_bits=1,tagged=True)],
                    selected_photon_multiplicity=2,native_btag_multiplicity=2,stages=[True]*5)

    def test_bin_boundaries_include_flows_and_last_edge_overflow(self):
        edges=[Decimal(0),Decimal(1),Decimal(2)]
        self.assertEqual([bucket(v,edges) for v in (-1,0,.5,1,1.5,2,3)],[0,1,1,2,2,3,3])

    def test_invalid_edges_and_nonfinite_values_rejected(self):
        with self.assertRaises(ValueError):bucket(1,[Decimal(0),Decimal(0)])
        with self.assertRaises(ValueError):bucket(float('nan'),[Decimal(0),Decimal(1)])
        for value in (True,'NaN','Infinity'):
            with self.assertRaises(ValueError):number(value)

    def test_closed_form_matches_four_event_binomial_delta(self):
        with localcontext() as context:
            context.prec=70
            p,v=normalized_delta(Decimal('.4'),Decimal('.04'),Decimal('.4'),Decimal('.1'),Decimal('.01'),4)
            self.assertEqual(p,Decimal('.25'))
            self.assertLess(abs(v-Decimal('.0625')),Decimal('1e-68'))

    def test_all_mass_in_bin_has_no_ratio_fluctuation(self):
        p,v=normalized_delta(Decimal('.4'),Decimal('.04'),Decimal('.4'),Decimal('.4'),Decimal('.04'),4)
        self.assertEqual(p,1);self.assertEqual(v,0)

    def test_empirical_empty_bin_stays_defined_with_existing_denominator(self):
        p,v=normalized_delta(Decimal('.4'),Decimal('.04'),Decimal('.4'),Decimal(0),Decimal(0),4)
        self.assertEqual(p,0);self.assertEqual(v,0)

    def test_empty_or_signed_cancelling_shape_stays_undefined(self):
        self.assertEqual(normalized_delta(Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),4),(None,None))
        self.assertEqual(normalized_delta(Decimal(0),Decimal(2),Decimal(2),Decimal(1),Decimal(1),4),(None,None))
        self.assertEqual(normalized_delta(Decimal('1e-20'),Decimal(2),Decimal(2),Decimal(1),Decimal(1),4),(None,None))

    def test_invalid_squared_weight_partition_rejected(self):
        with self.assertRaises(ValueError):normalized_delta(Decimal(1),Decimal(1),Decimal(1),Decimal(1),Decimal(2),4)

    def test_original_zero_contributions_are_in_variance(self):
        s,q,a,v,e=moments([Decimal('.2')],4)
        self.assertEqual(v,Decimal('.04'));self.assertEqual(e,1)

    def test_signed_sum_zero_is_not_zero_source_uncertainty(self):
        s,q,a,v,e=moments([Decimal('.1'),Decimal('-.1')],2)
        self.assertEqual(s,0);self.assertEqual(v,Decimal('.04'));self.assertEqual(e,0)

    def test_zero_denominator_never_filled_with_zero(self):
        compare(None,None,'undefined')
        with self.assertRaises(ValueError):compare(0,None,'undefined')

    def test_invalid_original_denominator_rejected(self):
        with self.assertRaises(ValueError):variance(Decimal(1),Decimal(1),True)
        with self.assertRaises(ValueError):variance(Decimal(1),Decimal(1),1)
        with self.assertRaises(ValueError):moments([1,2,3],2)

    def test_mass_regions_are_exclusive_at_every_boundary(self):
        self.assertEqual([mass_region(m) for m in (None,104.9,105,119.9,120,130,130.1,160,160.1)],['UNDEFINED_MGG','OUTSIDE_MGG','LOW','LOW','HIGGS','HIGGS','HIGH','HIGH','OUTSIDE_MGG'])

    def test_full_stage_derivation_and_region(self):
        e=self.event();self.assertEqual(derive_stages(e),([True]*5,2));self.assertEqual(region_for(e),('TAG_GE2','HIGGS'))

    def test_bit2_alone_does_not_count_as_bit0(self):
        e=self.event()
        for j in e['eligible_jets']:j.update(native_btag_bits=2,tagged=False)
        e['native_btag_multiplicity']=0;e['stages']=[True,True,True,False,False]
        e['observables'].update(m_bb=None,m_HH=None)
        self.assertEqual(derive_stages(e)[1],0);self.assertEqual(region_for(e),('TAG_0','HIGGS'))
        e['eligible_jets'][0]['tagged']=True
        with self.assertRaises(ValueError):derive_stages(e)

    def test_null_pair_cut_boundary_and_jet_acceptance_guards(self):
        e=self.event();e['native_btag_multiplicity']=1;e['eligible_jets'][1].update(native_btag_bits=0,tagged=False)
        with self.assertRaises(ValueError):derive_stages(e)
        e=self.event();e['eligible_jets'][0]['pt']=25
        with self.assertRaises(ValueError):derive_stages(e)
        e=self.event();e['observables']['photon1_eta']=1.4
        with self.assertRaises(ValueError):derive_stages(e)
        e=self.event();e['observables']['photon1_pT']=35
        with self.assertRaises(ValueError):derive_stages(e)  # Persisted all-true stages would silently change strict cut.

    def test_mgg_outside_baseline_only_final_stage_changes(self):
        e=self.event();e['observables']['m_gamma_gamma']=160.1;e['stages']=[True,True,True,True,False]
        self.assertEqual(derive_stages(e)[0],e['stages']);self.assertEqual(region_for(e),('TAG_GE2','OUTSIDE_MGG'))

if __name__=='__main__':unittest.main()
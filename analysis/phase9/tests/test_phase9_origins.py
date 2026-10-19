"""SYNTHETIC_METHOD_TEST: ancestry join guards and correlated ratios."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import phase9_origins as origins

class DriverGuards(unittest.TestCase):
    def sample(self, i):
        hard = dict(source_event_index=i, source_event_sha256='h'+str(i), raw_weight='1.0', particles=[])
        graph = dict(event_number=i, exact_event_sha256='e'+str(i), particles={}, attributes=dict(source_event_index=str(i), source_total_events='2', source_event_content_hash='h'+str(i)))
        reco = dict(source_event_ordinal=i, source_event_sha256='h'+str(i), hepmc_event_sha256='e'+str(i), native_event_number=i, N_original=2, source_weight_pb=.5, stages=[True]*5, observables={})
        return hard, graph, reco

    def execute(self, events):
        h, g, r = zip(*events)
        dataset = dict(dataset_id='B04', N_original=2, model_br_factor=.002, lhe_path='INERT', hepmc_path='INERT')
        with patch.object(origins, 'iter_lhe', return_value=iter(h)), patch.object(origins, 'iter_hepmc', return_value=iter(g)), patch.object(origins, 'classify_photons', return_value={}):
            return list(origins.classified_events(dataset, r))

    def test_exact_full_original_cohort_passes(self):
        rows = self.execute([self.sample(1), self.sample(2)])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]['source_event_sha256'], 'h2')

    def test_hash_number_denominator_weight_and_duplicates_rejected(self):
        for key, value in [('source_event_sha256', 'WRONG'), ('hepmc_event_sha256', 'WRONG'), ('source_event_ordinal', 9), ('N_original', 2000), ('source_weight_pb', .0005)]:
            samples = [self.sample(1), self.sample(2)]
            samples[0][2][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.execute(samples)
        with self.assertRaises(ValueError): self.execute([self.sample(1), self.sample(1)])

    def test_truncated_or_extra_original_cohort_is_rejected(self):
        with self.assertRaises(ValueError): self.execute([self.sample(1)])
        with self.assertRaises(ValueError): self.execute([self.sample(1), self.sample(2), self.sample(3)])

    def test_within_stage_ratio_preserves_shared_event_covariance(self):
        events = [dict(weight_pb=1., stages=[True]), dict(weight_pb=1., stages=[True]), dict(weight_pb=1., stages=[False])]
        s = origins.conditional_origin_fraction(events, [True, False, False], 0)
        self.assertEqual(s['within_stage_event_fraction'], .5)
        self.assertEqual(s['weighted_within_stage_fraction'], .5)
        self.assertAlmostEqual(s['weighted_within_stage_fraction_event_cluster_se']**2, .1875)

    def test_no_eligible_denominator_is_explicit_null(self):
        events = [dict(weight_pb=1., stages=[False]) for _ in range(2)]
        s = origins.conditional_origin_fraction(events, [False, False], 0)
        self.assertIsNone(s['within_stage_event_fraction'])
        self.assertIsNone(s['weighted_within_stage_fraction'])
        self.assertIsNone(s['weighted_within_stage_fraction_event_cluster_se'])

    def test_signed_cancelling_denominator_is_not_repaired(self):
        events = [dict(weight_pb=1., stages=[True]), dict(weight_pb=-1., stages=[True])]
        s = origins.conditional_origin_fraction(events, [True, False], 0)
        self.assertEqual(s['stage_weight_denominator_pb'], 0)
        self.assertIsNone(s['weighted_within_stage_fraction'])

    def test_kinematic_missing_values_are_not_zero(self):
        events = [dict(stages=[True]*5, observables={'m_bb': None, 'm_gamma_gamma':125.}), dict(stages=[True]*5, observables={'m_bb': None,'m_gamma_gamma':None})]
        d = origins.kinematic_summaries(events)['00_INPUT']
        self.assertEqual(d['m_bb']['defined'], 0)
        self.assertEqual(d['m_bb']['missing'], 2)
        self.assertIsNone(d['m_bb']['mean'])
        self.assertEqual(d['m_gamma_gamma']['defined'], 1)
        self.assertEqual(d['m_gamma_gamma']['missing'], 1)

if __name__ == '__main__': unittest.main()
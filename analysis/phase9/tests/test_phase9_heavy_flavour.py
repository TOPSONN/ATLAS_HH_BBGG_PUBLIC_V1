"""SYNTHETIC_METHOD_TEST controls, not new Monte Carlo events."""
from pathlib import Path
import copy
from decimal import Decimal, localcontext
import math
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from phase9_graph import ancestors, audit_graph, enrich_with_pythia, hard_match, retain_native_particle_attributes
from phase9_heavy_flavour import births, classify_heavy_flavour, event_flags, summarize_indicator, OVERLAP_STATUS


def node(i, pdg=21, status=-51, mothers=(), daughters=(), phi=0., hadron=False, b=False, c=False):
    return dict(id=i, pythia_index=i, pdg_id=pdg, status=status, mothers=list(mothers), daughters=list(daughters),
                p4_gev=[50*math.cos(phi), 50*math.sin(phi), 0., 50.], mass_gev=0.,
                is_hadron=hadron, terminal_b_hadron=b, terminal_c_hadron=c)


def graph_from_py(nodes):
    graph = {p['id']: dict(p, status=abs(p['status'])) for p in nodes}
    return dict(particles=graph, attributes={}), {p['id']: p for p in nodes}


def reco(jets=()):
    return dict(eligible_jets=list(jets))


def jet(index=0, phi=0., flavour=5, tagged=True):
    return dict(index=index, pt=50., eta=0., phi=phi, flavour=flavour, tagged=tagged)


class HeavyFlavourControls(unittest.TestCase):
    def test_birth_counts_ignore_shifted_same_signed_heavy_line(self):
        g = {1: node(1, pdg=5, status=-23, daughters=(2,)), 2: node(2, pdg=5, mothers=(1,), daughters=(3,)), 3: node(3, pdg=5, mothers=(2,))}
        self.assertEqual(list(births(g)), [1])
        self.assertEqual(births(g)[1]['origin'], 'ME_HEAVY_FLAVOUR_RECORD')

    def test_incoming_and_outgoing_same_flavour_are_separate_me_records(self):
        g = {10: node(10, pdg=5, status=-21, daughters=(20,)),
             20: node(20, pdg=5, status=-23, mothers=(10,), daughters=(30,)),
             30: node(30, pdg=5, status=-51, mothers=(20,))}
        result = births(g)
        self.assertEqual(set(result), {10, 20})
        self.assertEqual(result[10]['origin'], 'ME_INITIAL_HEAVY_FLAVOUR_RECORD')
        self.assertEqual(result[20]['origin'], 'ME_HEAVY_FLAVOUR_RECORD')
        self.assertEqual(sum(r['origin'] == 'SHOWER_HEAVY_FLAVOUR_BIRTH' for r in result.values()), 0)

    def test_incoming_me_record_survives_same_flavour_backward_parent(self):
        g = {10: node(10, pdg=4, status=-43, daughters=(20,)),
             20: node(20, pdg=4, status=-21, mothers=(10,))}
        result = births(g)
        self.assertIn(20, result)
        self.assertEqual(result[20]['origin'], 'ME_INITIAL_HEAVY_FLAVOUR_RECORD')
        self.assertEqual(sum(r['origin'] == 'SHOWER_HEAVY_FLAVOUR_BIRTH' for r in result.values()), 1)

    def test_direct_gluon_pair_requires_both_signed_daughters(self):
        g = {10: node(10, daughters=(20, 30)), 20: node(20, pdg=5, mothers=(10,)), 30: node(30, pdg=-5, mothers=(10,))}
        self.assertEqual(births(g)[20]['direct_gluon_splitting_mothers'], [10])
        g[30]['pdg_id'] = 4
        self.assertEqual(births(g)[20]['direct_gluon_splitting_mothers'], [])

    def test_hard_gluon_is_not_proof_of_shower_splitting_vertex(self):
        g = {10: node(10, status=-23, daughters=(20, 30)), 20: node(20, pdg=5, mothers=(10,)), 30: node(30, pdg=-5, mothers=(10,))}
        self.assertEqual(births(g)[20]['direct_gluon_splitting_mothers'], [])

    def test_hadron_decay_heavy_quark_is_separate(self):
        g = {10: node(10, pdg=511, status=-83, hadron=True, daughters=(20,)), 20: node(20, pdg=4, status=-91, mothers=(10,))}
        self.assertEqual(births(g)[20]['origin'], 'HADRON_DECAY_HEAVY_QUARK')

    def test_other_status_is_explicitly_unclassified(self):
        self.assertEqual(births({20: node(20, pdg=4, status=-63)})[20]['origin'], 'OTHER_OR_UNCLASSIFIED_HEAVY_QUARK_BIRTH')

    def test_all_ancestors_retained_in_multimother_chain(self):
        g = {10: node(10, pdg=5, daughters=(30,)), 20: node(20, pdg=-5, daughters=(30,)), 30: node(30, pdg=511, hadron=True, mothers=(10, 20))}
        self.assertEqual(ancestors(g, 30), [10, 20])
        self.assertEqual(audit_graph(g)['status'], 'PASS')

    def test_graph_missing_edge_and_cycle_rejected(self):
        bad = {10: node(10, mothers=(99,))}
        self.assertEqual(audit_graph(bad)['status'], 'FAIL')
        with self.assertRaises(ValueError): ancestors(bad, 10)
        cycle = {10: node(10, mothers=(20,), daughters=(20,)), 20: node(20, mothers=(10,), daughters=(10,))}
        self.assertEqual(audit_graph(cycle)['status'], 'FAIL')
        with self.assertRaises(ValueError): ancestors(cycle, 10)

    def test_hadron_nearest_assignment_once_with_ties_unknown(self):
        graph, py = graph_from_py([node(10, pdg=511, status=-83, hadron=True, b=True)])
        result = classify_heavy_flavour(graph, reco([jet(0, -.1), jet(1, .1)]), dict(particles=[]), py)
        self.assertEqual(result['ambiguous_hadron_assignment_ids'], [10])
        self.assertTrue(all(j['heavy_hadron_flavour'] == 0 for j in result['jets']))
        result = classify_heavy_flavour(graph, reco([jet(0, -.1), jet(1, .2)]), dict(particles=[]), py)
        self.assertEqual([j['heavy_hadron_flavour'] for j in result['jets']], [5, 0])

    def test_b_c_hadron_priority_but_inclusive_flags_retained(self):
        graph, py = graph_from_py([node(10, pdg=541, status=-83, hadron=True, b=True, c=True)])
        result = classify_heavy_flavour(graph, reco([jet()]), dict(particles=[]), py)
        j = result['jets'][0]
        self.assertEqual(j['heavy_hadron_flavour'], 5)
        self.assertEqual(j['terminal_b_hadrons'], 1)
        self.assertEqual(j['terminal_c_hadrons'], 1)
        self.assertEqual(j['sole_hadron_endpoint'], 'UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED')

    def test_hard_light_does_not_imply_native_light(self):
        graph, py = graph_from_py([node(10, pdg=21, daughters=(20, 30)), node(20, pdg=5, mothers=(10,)), node(30, pdg=-5, mothers=(10,), phi=.1)])
        hard = dict(particles=[dict(pdg_id=21, status=1, p4_gev=[50, 0, 0, 50])])
        result = classify_heavy_flavour(graph, reco([jet()]), hard, py)
        self.assertEqual(result['hard_process_flavour'], 'ME_LIGHT_OR_GLUON')
        self.assertEqual(result['jets'][0]['shower_record_cone_flavour'], 5)
        self.assertTrue(event_flags(result)['HARD_LIGHT_NATIVE_HEAVY'])
        self.assertTrue(result['no_physical_background_sum'])
        self.assertEqual(result['overlap_status'], OVERLAP_STATUS)

    def test_native_labels_never_overwritten_by_diagnostic(self):
        graph, py = graph_from_py([node(10, pdg=5)])
        result = classify_heavy_flavour(graph, reco([jet(flavour=4)]), dict(particles=[]), py)
        self.assertFalse(result['native_reproduction_pass'])
        self.assertEqual(result['jets'][0]['native_flavour'], 4)
        self.assertEqual(result['jets'][0]['shower_record_cone_flavour'], 5)

    def test_native_serialized_particle_attributes_do_not_use_ordinals(self):
        graph = dict(particles={900: dict(pdg_id=22)})
        raw = b'A 900 original_pythia_status 51\nA 900 original_pythia_is_hadron 0\nA 900 original_pythia_index 17\n'
        result = retain_native_particle_attributes(graph, raw)
        self.assertEqual(result['particles'][900]['original_pythia_status'], 51)
        self.assertEqual(result['particles'][900]['original_pythia_index'], 17)
        self.assertIs(result['particles'][900]['is_hadron'], False)

    def test_partial_duplicate_or_dangling_serialized_flags_rejected(self):
        graph = dict(particles={900: dict(pdg_id=22)})
        for raw in (b'A 900 original_pythia_status 51\n',
                    b'A 900 original_pythia_status 51\nA 900 original_pythia_status 51\n',
                    b'A 17 original_pythia_status 51\n'):
            with self.assertRaises(ValueError): retain_native_particle_attributes(copy.deepcopy(graph), raw)

    def test_exact_tuple_mapping_does_not_assume_equal_ids(self):
        p = node(10, pdg=22, status=-23)
        graph = dict(particles={999: dict(p, id=999, status=23)})
        py = enrich_with_pythia(graph, dict(particles=[p], hard_photon_roots=[10]))
        self.assertEqual(graph['hard_photon_roots'], [999])
        self.assertEqual(graph['particles'][999]['original_pythia_status'], -23)
        self.assertNotIn('hard_photon_roots_status', graph)  # Driver must verify ledger first.

    def test_kinematic_match_is_not_silently_ordinal(self):
        hard = [dict(index=1, pdg_id=5, p4_gev=[50., 0., 0., 50.])]
        g = {900: node(900, pdg=5, status=23)}
        self.assertEqual(hard_match(hard, g)[1]['graph_ids'], [900])
        g[900]['p4_gev'][0] += .1
        self.assertEqual(hard_match(hard, g)[1]['status'], 'UNAVAILABLE_OR_AMBIGUOUS')

    def test_fixed_original_n_zero_contributions_included(self):
        s = summarize_indicator([True, False, False, False], [.2]*4)
        self.assertEqual(s['events'], 1)
        self.assertAlmostEqual(s['sumw_pb'], .2)
        self.assertAlmostEqual(s['source_sampling_variance_pb2'], .04)
        self.assertEqual(s['ESS'], 1)

    def test_weighted_variance_independent_decimal(self):
        values = [True, False, True, True, False]
        weights = [.2, -.1, .3, -.6, .7]
        actual = summarize_indicator(values, weights)
        with localcontext() as context:
            context.prec = 60
            xs = [Decimal(str(w)) if f else Decimal(0) for f, w in zip(values, weights)]
            n = Decimal(len(xs)); mean = sum(xs)/n
            variance = n/(n-1)*sum((x-mean)**2 for x in xs)
        self.assertAlmostEqual(actual['source_sampling_variance_pb2'], float(variance), places=15)

    def test_zero_survivors_remain_upper_interval_not_zero_bound(self):
        s = summarize_indicator([False]*1000, [.1]*1000)
        self.assertEqual(s['sumw_pb'], 0)
        self.assertIsNone(s['ESS'])
        self.assertGreater(s['fraction_wilson95_high'], 0)
        self.assertIn('NOT_PHYSICAL_XSEC', s['interval_scope'])

    def test_invalid_complete_cohort_or_nonfinite_weights_rejected(self):
        with self.assertRaises(ValueError): summarize_indicator([True], [.1])
        with self.assertRaises(ValueError): summarize_indicator([True, True], [.1, math.nan])
        with self.assertRaises(ValueError): summarize_indicator([True, True], [.1])

    def test_signed_cancellation_ess_is_zero_not_object_count(self):
        s = summarize_indicator([True, True], [.1, -.1])
        self.assertEqual(s['sumw_pb'], 0)
        self.assertEqual(s['ESS'], 0)
        self.assertGreater(s['source_sampling_variance_pb2'], 0)

if __name__ == '__main__': unittest.main()
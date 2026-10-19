"""SYNTHETIC_METHOD_TEST: graph classifications and missing-calibration guards."""
import importlib.util
import math
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import phase9_photon as p

def node(i, pdg, status=1, mothers=(), phi=0, pt=40, original=None):
    q = {'id': i, 'pdg_id': pdg, 'status': status, 'mothers': list(mothers), 'daughters': [],
         'p4_gev': [pt*math.cos(phi), pt*math.sin(phi), 0, pt], 'mass_gev': 0}
    if original is not None:
        q['original_pythia_status'] = original
    return q

def event(nodes, roots=()):
    return {'particles': {q['id']: q for q in nodes}, 'hard_photon_roots': list(roots),
            'hard_photon_roots_status': 'VERIFIED_SOURCE_LEDGER_OR_DECAY_LINEAGE'}

def reco(phi=0, index=0):
    return {'index': index, 'pt': 40, 'eta': 0, 'phi': phi, 'selected': True}

def lhe():
    return {'source_event_sha256': 'a'*64, 'particles': [{'index': 3, 'pdg_id': 22, 'status': 1, 'p4_gev': [40,0,0,40]}]}

class PhotonTests(unittest.TestCase):
    def test_hadron_pdgs(self):
        for pid in [111,221,511,521,5122,10441]: self.assertTrue(p.is_hadron(pid))
        for pid in [22,11,21,25,2212*1000000,5101,1000022]: self.assertFalse(p.is_hadron(pid))
    def test_prompt_exact_root(self):
        g=event([node(7,22,23),node(91,22,1,[7])],[7])
        r=p.classify_photons(g, {'photons':[reco()]}, lhe())
        self.assertEqual(r['reco_photons'][0]['origin'],'PROMPT_HARD_PROCESS')
        self.assertIsNone(r['calibrated_fake_probability'])
    def test_proton_ancestor_is_not_hadron_decay(self):
        g=event([node(1,2212,4),node(2,1,21,[1]),node(3,22,23,[2]),node(4,22,1,[3])],[3])
        self.assertEqual(p.photon_origin(g['particles'],4,{3})['origin'],'PROMPT_HARD_PROCESS')
    def test_hadron_decay(self):
        g=event([node(1,111,2),node(2,22,1,[1])])
        self.assertEqual(p.photon_origin(g['particles'],2,set())['origin'],'HADRON_DECAY')
    def test_hadron_chain(self):
        g=event([node(1,511,2),node(2,22,91,[1]),node(3,22,1,[2])])
        self.assertEqual(p.photon_origin(g['particles'],3,set())['origin'],'HADRON_DECAY')
    def test_electron_parent(self):
        g=event([node(1,11,51),node(2,22,1,[1],original=51)])
        self.assertEqual(p.photon_origin(g['particles'],2,set())['origin'],'ELECTRON_ASSOCIATED')
    def test_radiation_original_status(self):
        g=event([node(1,2,51),node(2,22,1,[1],original=51)])
        self.assertEqual(p.photon_origin(g['particles'],2,set())['origin'],'SHOWER_RADIATION')
    def test_hepmc_status_cannot_prove_radiation(self):
        g=event([node(1,2,51),node(2,22,51,[1])])
        self.assertEqual(p.photon_origin(g['particles'],2,set())['origin'],'UNCLASSIFIED')
    def test_kinematic_match_cannot_prove_prompt(self):
        g=event([node(2,22,23)])
        r=p.classify_photons(g,{'photons':[]},lhe())
        self.assertEqual(r['hard_photon_binding'][0]['status'],'UNIQUE')
        self.assertEqual(r['verified_hard_photon_roots'],[])
    def test_unverified_root_rejected(self):
        g=event([node(1,22)], [1]);g.pop('hard_photon_roots_status')
        with self.assertRaisesRegex(ValueError,'unverified'):p.classify_photons(g,{'photons':[]},lhe())
    def test_conflicting_origin_unknown(self):
        g=event([node(1,111,2),node(2,22,1,[1])])
        self.assertEqual(p.photon_origin(g['particles'],2,{2})['origin'],'UNCLASSIFIED')
    def test_dangling_rejected(self):
        with self.assertRaisesRegex(ValueError,'dangling'):p.photon_origin({2:node(2,22,1,[99])},2,set())
    def test_cycle_rejected(self):
        with self.assertRaisesRegex(ValueError,'cyclic'):p.photon_origin({1:node(1,22,1,[2]),2:node(2,22,1,[1])},1,set())
    def test_two_photons_in_cone_ambiguous(self):
        g=event([node(1,22,1),node(2,22,1,phi=.01)],[1,2])
        r=p.classify_photons(g,{'photons':[reco()]},lhe())
        self.assertEqual(r['reco_photons'][0]['origin'],'UNCLASSIFIED')
    def test_one_truth_two_reco_ambiguous(self):
        g=event([node(1,22,1)],[1])
        r=p.classify_photons(g,{'photons':[reco(),reco(.01,1)]},lhe())
        self.assertTrue(all(x['origin']=='UNCLASSIFIED' for x in r['reco_photons']))
    def test_electron_fallback(self):
        g=event([node(1,11,1)])
        r=p.classify_photons(g,{'photons':[reco()]},lhe())
        self.assertEqual(r['reco_photons'][0]['origin'],'ELECTRON_ASSOCIATED')
    def test_electron_photon_conflict(self):
        g=event([node(1,22,1),node(2,11,1)],[1])
        self.assertEqual(p.classify_photons(g,{'photons':[reco()]},lhe())['reco_photons'][0]['origin'],'UNCLASSIFIED')
    def test_phi_wrapping(self):
        self.assertAlmostEqual(p.delta_r(reco(-math.pi+.01),node(1,22,phi=math.pi-.01)),.02)
    def test_strict_radius(self):
        self.assertFalse(p.delta_r(reco(.2),node(1,22))<p.RADIUS)
    def test_exact_identity_guard(self):
        g=event([]);g['attributes']={'source_event_content_hash':'b'*64}
        with self.assertRaisesRegex(ValueError,'source identity'):p.classify_photons(g,{'photons':[]},lhe())
    def test_nonfinite_reco_rejected(self):
        r=reco();r['pt']=float('nan')
        with self.assertRaisesRegex(ValueError,'nonfinite'):p.classify_photons(event([]),{'photons':[r]},lhe())
    def test_duplicate_index_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):p.classify_photons(event([]),{'photons':[reco(),reco()]},lhe())
    def test_empty_match_not_fake(self):
        r=p.classify_photons(event([]),{'photons':[reco()]},lhe())
        self.assertEqual(r['reco_photons'][0]['origin'],'UNCLASSIFIED')
        self.assertEqual(r['fake_rate_status'],'BLOCKED_CALIBRATION_UNAVAILABLE')
    def test_fake_missing_guard(self):
        for c in [None,{}, {'status':'PUBLIC_PURITY_ONLY'}, {'status':'VALIDATED_COMPATIBLE_DATA_CALIBRATION'}]:
            with self.assertRaisesRegex(ValueError,'BLOCKED_CALIBRATION_UNAVAILABLE'):p.require_fake_calibration(c)
    def test_fake_complete_contract(self):
        c={k:'validated' for k in ('source_version','data_period','energy_tev','object_definition','transfer_factor_semantics','applicability','uncertainties','license')}
        c['status']='VALIDATED_COMPATIBLE_DATA_CALIBRATION'
        self.assertIs(p.require_fake_calibration(c),c)
    def test_source_class_count_closure(self):
        g=event([node(1,111,2),node(2,22,1,[1]),node(3,22,1,phi=2)],[3])
        r=p.classify_photons(g,{'photons':[reco()]},lhe())
        self.assertEqual(sum(r['stable_truth_photon_counts'].values()),2)
        self.assertEqual(sum(r['native_reco_photon_counts'].values()),1)
        self.assertEqual(sum(r['selected_reco_photon_counts'].values()),1)

if __name__=='__main__': unittest.main()
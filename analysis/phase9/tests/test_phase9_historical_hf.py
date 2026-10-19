"""HISTORICAL_EVIDENCE_AUDIT: bounded source997 graph, no full-input readback."""
from pathlib import Path
import json
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from phase9_graph import historical
from phase9_heavy_flavour import classify_heavy_flavour

class HistoricalSource997(unittest.TestCase):
    def test_published_source997_heavy_flavour_hierarchy_is_preserved(self):
        repo = Path(__file__).resolve().parents[3]
        d = json.loads((repo/'simulation/heavy_flavour_forensics/evidence/source997.json').read_text())
        self.assertEqual(d['source_event_sha256'], '322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8')
        self.assertEqual(d['hepmc_event_sha256'], '157928b854ffa4be208b4460338afea8d857446a595a56016c7e8cb994fec31f')
        graph = dict(d['hepmc_graph'], particles={int(k): v for k,v in d['hepmc_graph']['particles'].items()})
        py = historical.pythia_graph(d['pythia_graph'])
        hard = dict(particles=[dict(p, p4_gev=p['p4_and_mass_gev'][:4]) for p in d['original_hard_event']['particles']])
        reco = dict(eligible_jets=[dict(j, tagged=bool(j['btag_bit0'])) for j in d['eligible_jets']])
        result = classify_heavy_flavour(graph, reco, hard, py)
        self.assertEqual([j['hard_cone_flavour'] for j in result['jets']], [21, 2, 0, 0, 0])
        self.assertEqual([j['shower_record_cone_flavour'] for j in result['jets']], [5, 2, 21, 21, 5])
        self.assertEqual([j['heavy_hadron_flavour'] for j in result['jets']], [5, 0, 0, 0, 5])
        self.assertEqual([j['native_flavour'] for j in result['jets']], [5, 2, 21, 21, 5])
        self.assertEqual([j['tagged'] for j in result['jets']], [True, False, False, False, False])
        self.assertEqual(result['direct_gluon_splitting_count'], 1)
        self.assertEqual(result['direct_gluon_splitting_mothers'], [17])
        self.assertTrue(result['native_reproduction_pass'])

if __name__ == '__main__': unittest.main()
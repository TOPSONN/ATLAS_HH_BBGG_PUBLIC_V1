"""Independent actual997 graph regressions and explicitly synthetic API controls.

Graph/kinematic fixtures test code paths only; they are not MC or reference
physics samples. Actual regressions consume the bounded derived event997 graph
and unchanged original LHE bytes. No simulation or ROOT rewrite is performed.
"""
import copy
from decimal import Decimal, localcontext
import gzip
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import re
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("phase6e_source997", Path(__file__).resolve().parents[1] / "scripts/source997.py")
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)


def node(index, mothers=(), daughters=(), pdg=21, status=-51, p4=(10., 0., 0., 10.), mass=0., hadron=False):
    """Synthetic graph/tuple API node; no physical event interpretation."""
    return {"id": index, "pythia_index": index, "pdg_id": pdg, "status": status,
            "mothers": list(mothers), "daughters": list(daughters), "p4_gev": list(p4),
            "mass_gev": mass, "is_hadron": hadron}


def independent_ancestors(graph, index):
    visited, active = set(), set()
    def visit(pid):
        if pid in active:
            raise ValueError("cycle")
        if pid in visited:
            return
        active.add(pid)
        for parent in graph[pid]["mothers"]:
            if parent:
                visit(parent)
        active.remove(pid)
        visited.add(pid)
    visit(index)
    return visited - {index}


def independent_status(row, graph):
    if row["status"] > 0:
        return 1
    if row["status"] == -12:
        return 4
    if row["daughters"] and (row["is_hadron"] or abs(row["pdg_id"]) in (13, 15)):
        first = graph[row["daughters"][0]]
        if first["pdg_id"] != row["pdg_id"] and abs(first["status"]) in (91, 92, 93, 94):
            return 2
    return abs(row["status"]) if -200 <= row["status"] <= -11 else 0


class GraphAndMappingControls(unittest.TestCase):
    def test_ancestry_does_not_assume_numeric_or_storage_order(self):
        graph = {7: node(7, (42, 13)), 13: node(13, (42,), (7,)), 42: node(42, (), (13, 7))}
        self.assertEqual(source.ancestors(graph, 7), [13, 42])
        self.assertEqual(source.audit_graph(graph)["status"], "PASS")

    def test_cycle_upstream_of_requested_particle_is_rejected(self):
        graph = {1: node(1, (2,), (2,)), 2: node(2, (1,), (1, 3)), 3: node(3, (2,))}
        with self.assertRaises(ValueError):
            source.ancestors(graph, 3)
        self.assertEqual(source.audit_graph(graph)["status"], "FAIL")

    def test_missing_and_nonreciprocal_edges_are_rejected(self):
        graph = {1: node(1, (), (2,)), 2: node(2, (999,))}
        self.assertEqual(source.audit_graph(graph)["status"], "FAIL")
        with self.assertRaises(ValueError):
            source.ancestors(graph, 2)
        graph = {1: node(1), 2: node(2, (1,))}
        self.assertEqual(source.audit_graph(graph)["status"], "FAIL")

    def test_duplicate_reciprocal_edges_are_not_a_valid_dag(self):
        graph = {1: node(1, (), (2, 2)), 2: node(2, (1, 1))}
        self.assertEqual(source.audit_graph(graph)["status"], "FAIL")
        self.assertTrue(source.audit_graph(graph)["duplicate_edge_particle_ids"])

    def test_status_conversion_uses_decay_semantics_not_absolute_status_alone(self):
        graph = {1: node(1, (), (2,), pdg=511, status=-83, hadron=True),
                 2: node(2, (1,), pdg=211, status=91)}
        self.assertEqual(source.hepmc_status(graph[1], graph), 2)
        graph[2]["pdg_id"] = 511
        self.assertEqual(source.hepmc_status(graph[1], graph), 83)
        for status, expected in ((1, 1), (91, 1), (-12, 4), (-51, 51), (-9, 0), (-201, 0)):
            row = node(10, status=status)
            self.assertEqual(source.hepmc_status(row, {10: row}), expected)

    def test_exact_tuple_unique_match_has_no_barcode_equivalence(self):
        py = {19: node(19, pdg=5, mass=4.8)}
        hc = {70: {**node(70, pdg=5, mass=4.8), "status": 51}}
        result = source.match_pythia_hepmc(py, hc)
        self.assertEqual(result["particles"][19]["hepmc_ids"], [70])
        self.assertEqual(result["particles"][19]["status"], "UNIQUE_TUPLE_MATCH")
        changed = copy.deepcopy(hc)
        changed[70]["p4_gev"][0] = math.nextafter(10., math.inf)
        self.assertEqual(source.match_pythia_hepmc(py, changed)["particles"][19]["status"], "UNKNOWN_NO_MATCH")

    def test_both_sides_duplicate_tuples_remain_ambiguous(self):
        py = {19: node(19, pdg=5)}
        hc = {70: {**node(70, pdg=5), "status": 51}, 71: {**node(71, pdg=5), "status": 51}}
        self.assertEqual(source.match_pythia_hepmc(py, hc)["particles"][19]["status"], "UNKNOWN_AMBIGUOUS")
        py[20] = node(20, pdg=5)
        result = source.match_pythia_hepmc(py, {70: hc[70]})
        self.assertEqual(result["unique_matches"], 0)
        self.assertTrue(all(row["status"] == "UNKNOWN_AMBIGUOUS" for row in result["particles"].values()))

    def test_mapping_checks_parent_edges_after_tuple_matching(self):
        py = {19: node(19, (), (20,), pdg=5), 20: node(20, (19,), pdg=-5)}
        hc = {70: {**node(70, pdg=5), "status": 51}, 80: {**node(80, pdg=-5), "status": 51}}
        self.assertTrue(source.match_pythia_hepmc(py, hc)["mother_edge_differences"])

    def test_native_flavour_status_acceptance_and_priority(self):
        jet = {"eta": 0, "phi": 0, "flavor": 4}
        graph = {1: node(1, pdg=21, status=23), 2: node(2, pdg=-4, status=51),
                 3: node(3, pdg=5, status=1), 4: node(4, pdg=-5, status=-1),
                 5: node(5, pdg=5, status=51, p4=(1., 0., 0., 1.)),
                 6: node(6, pdg=15, status=23)}
        result = source.native_flavour(jet, graph)
        self.assertEqual(result["attainable_labels"], [4])
        self.assertEqual([row["id"] for row in result["definite_candidates"]], [1, 2])
        self.assertTrue(result["matches_native"])

    def test_native_cone_boundary_permits_only_attainable_labels(self):
        jet = {"eta": 0, "phi": 0, "flavor": 5}
        graph = {1: node(1, pdg=21, status=23),
                 2: node(2, pdg=4, status=51, p4=(10*math.cos(.4), 10*math.sin(.4), 0., 10.))}
        result = source.native_flavour(jet, graph)
        self.assertEqual(result["attainable_labels"], [4, 21])
        self.assertFalse(result["matches_native"])
        self.assertEqual(len(result["angular_boundary_candidates"]), 1)

    def test_unique_matching_maximizes_cardinality_before_nearest_distance(self):
        objects = [node(7), node(8, p4=(10*math.cos(-.2), 10*math.sin(-.2), 0, 10))]
        jets = [{"index": 4, "eta": 0, "phi": -.05}, {"index": 9, "eta": 0, "phi": .35}]
        result = source.unique_diagnostic_matching(objects, jets)
        # A greedy closest assignment 7->4 would strand object8. The maximum
        # cardinality solution is 7->9, 8->4, even though its summed R is larger.
        self.assertEqual(result["status"], "UNIQUE_OPTIMUM")
        self.assertEqual(result["cardinality"], 2)
        self.assertEqual({p["object_id"]: p["native_jet_index"] for p in result["pairs"]}, {7: 9, 8: 4})

    def test_unique_matching_minimum_sum_and_equal_optimum_unknown(self):
        objects = [node(7), node(8, p4=(10*math.cos(.3), 10*math.sin(.3), 0, 10))]
        jets = [{"index": 4, "eta": 0, "phi": .01}, {"index": 9, "eta": 0, "phi": .2}]
        result = source.unique_diagnostic_matching(objects, jets)
        self.assertEqual({p["object_id"]: p["native_jet_index"] for p in result["pairs"]}, {7: 4, 8: 9})
        self.assertAlmostEqual(result["total_delta_r"], .11)
        tied = source.unique_diagnostic_matching([node(7), node(8)], [{"index": 4, "eta": 0, "phi": .1}, {"index": 9, "eta": 0, "phi": .1}])
        self.assertEqual(tied["status"], "UNKNOWN_AMBIGUOUS_OPTIMUM")
        self.assertIsNone(tied["pairs"])
        self.assertEqual(len(tied["possible_equal_optimums"]), 2)

    def test_unique_matching_strict_radius_and_no_duplicate_objects_or_jets(self):
        obj, jet = node(7), {"index": 4, "eta": 0, "phi": .4}
        distance = source.delta_r(jet, obj)
        self.assertEqual(source.unique_diagnostic_matching([obj], [jet], radius=distance)["cardinality"], 0)
        with self.assertRaises(ValueError):
            source.unique_diagnostic_matching([obj, obj], [jet])
        with self.assertRaises(ValueError):
            source.unique_diagnostic_matching([node(7), node(8)], [jet, jet])
        for radius in (0, -1, math.nan, math.inf):
            with self.subTest(radius=radius), self.assertRaises(ValueError):
                source.unique_diagnostic_matching([obj], [jet], radius=radius)

    def test_duplicate_or_missing_source997_rows_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="phase6e_api_only_", dir=REPO) as directory:
            path = Path(directory) / "not_a_physics_ledger.jsonl"
            path.write_text('{"source_event_index":997}\n{"source_event_index":997}\n')
            with self.assertRaises(ValueError):
                source.selected_row(path)
            path.write_text('{"source_event_index":996}\n')
            with self.assertRaises(ValueError):
                source.selected_row(path)

    def test_malformed_ascii_graph_failure_fixtures(self):
        # Deliberately incomplete/invalid ASCII, never a passing physics sample.
        for raw in (b"E 997 1 1\nP 1 -99 5 1 0 0 2 1 51\n",
                    b"E 997 0 2\nP 1 0 5 1 0 0 2 1 51\nP 1 0 -5 1 0 0 2 1 51\n"):
            with self.assertRaises(ValueError):
                source.parse_hepmc(raw)


class ActualSource997GraphRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((REPO / "simulation/heavy_flavour_forensics/evidence/source997.json").read_text())
        cls.py = {row["pythia_index"]: row for row in cls.receipt["pythia_graph"]}
        cls.hc = {int(index): row for index, row in cls.receipt["hepmc_graph"]["particles"].items()}

    def test_original_lhe997_raw_hash_weight_and_light_born_identity(self):
        path = REPO / "reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), "606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030")
        with gzip.open(path, "rb") as stream:
            events = re.findall(rb"<event>.*?</event>", stream.read(), re.DOTALL)
        self.assertEqual(len(events), 1000)
        raw = events[996]
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8")
        records = [line.split() for line in raw.splitlines()[1:] if line.strip() and not line.startswith(b"#")][:7]
        self.assertEqual(float(records[0][2]), 9.4365561)
        self.assertEqual([int(line[0]) for line in records[1:]], [2, 21, 22, 22, 21, 2])
        self.assertEqual([int(line[1]) for line in records[1:]], [-1, -1, 1, 1, 1, 1])
        self.assertEqual(self.receipt["normalization_denominator"], 1000)
        self.assertEqual((self.receipt["generator_seed"], self.receipt["shower_seed"], self.receipt["delphes_seed"]), (20261022, 610203, 610303))

    def test_actual571nodes1149edges_exact_reciprocity_and_independent_dfs(self):
        for graph in (self.py, self.hc):
            self.assertEqual(len(graph), 571)
            self.assertEqual(sum(len(row["mothers"]) for row in graph.values()), 1149)
            for index, row in graph.items():
                self.assertEqual(len(row["mothers"]), len(set(row["mothers"])))
                for mother in row["mothers"]:
                    self.assertIn(index, graph[mother]["daughters"])
                for daughter in row["daughters"]:
                    self.assertIn(index, graph[daughter]["mothers"])
                self.assertEqual(set(source.ancestors(graph, index)), independent_ancestors(graph, index))
            self.assertEqual(source.audit_graph(graph)["status"], "PASS")
        self.assertEqual(source.audit_graph(self.py)["roots"], [1, 2])
        self.assertEqual(source.audit_graph(self.hc)["roots"], [1, 5])
        self.assertIn(9, self.py[3]["mothers"])

    def test_actual_unique_mapping_uses_exact_converted_tuples_and_parent_graph(self):
        candidates = {}
        for index, row in self.hc.items():
            key = (row["pdg_id"], row["status"], *(float(x).hex() for x in row["p4_gev"]), float(row["mass_gev"]).hex())
            self.assertNotIn(key, candidates)
            candidates[key] = index
        expected = {}
        for index, row in self.py.items():
            key = (row["pdg_id"], independent_status(row, self.py), *(float(x).hex() for x in row["p4_gev"]), float(row["mass_gev"]).hex())
            expected[index] = candidates[key]
        self.assertEqual(len(set(expected.values())), 571)
        for index, mapped in expected.items():
            self.assertEqual(sorted(expected[p] for p in self.py[index]["mothers"]), sorted(self.hc[mapped]["mothers"]))
        result = source.match_pythia_hepmc(self.py, self.hc)
        self.assertEqual(result["unique_matches"], 571)
        self.assertEqual(result["ambiguous_or_missing"], 0)
        self.assertEqual(result["mother_edge_differences"], [])
        self.assertEqual({i: row["hepmc_ids"][0] for i, row in result["particles"].items()}, expected)
        self.assertNotEqual(expected[2], 2)

    def test_direct_fsr_pair_birth_is_not_repeated_status_copy(self):
        self.assertEqual([(i, self.py[i]["pdg_id"], self.py[i]["status"]) for i in (7, 13, 17, 19, 20)],
                         [(7, 21, -23), (13, 21, -44), (17, 21, -51), (19, 5, -51), (20, -5, -51)])
        self.assertEqual(self.py[13]["mothers"], [7])
        self.assertEqual(self.py[17]["mothers"], [13])
        self.assertEqual(self.py[17]["daughters"], [19, 20])
        self.assertEqual(self.py[19]["mothers"], [17])
        self.assertEqual(self.py[20]["mothers"], [17])
        births = [(i, row["daughters"]) for i, row in self.py.items() if row["pdg_id"] == 21 and abs(row["status"]) == 51
                  and sorted(self.py[d]["pdg_id"] for d in row["daughters"]) == [-5, 5]]
        self.assertEqual(births, [(17, [19, 20])])
        self.assertEqual(self.receipt["origin_verdict"], "DIRECT_FSR_G_TO_B_BBAR_CONFIRMED")

    def test_terminal_heavy_hadron_geometry_and_multimother_limit(self):
        jets = {row["index"]: row for row in self.receipt["eligible_jets"]}
        self.assertEqual([self.py[i]["pdg_id"] for i in (276, 488)], [-511, 521])
        self.assertTrue(self.py[276]["terminal_b_hadron"])
        self.assertTrue(self.py[488]["terminal_b_hadron"])
        self.assertGreater(len(self.py[276]["mothers"]), 1)
        self.assertEqual(self.py[488]["mothers"], [363])
        self.assertIn(19, independent_ancestors(self.py, 276))
        self.assertIn(20, independent_ancestors(self.py, 488))
        self.assertAlmostEqual(source.delta_r(jets[0], self.py[276]), .0492422677641, places=11)
        self.assertAlmostEqual(source.delta_r(jets[4], self.py[488]), .0594148557805, places=11)
        self.assertIn("does not establish sole parton attribution", self.receipt["origin_limit"])
        for jet in jets.values():
            result = source.native_flavour(jet, self.hc)
            self.assertEqual(result["attainable_labels"], [jet["flavor"]])
            self.assertEqual(result["angular_boundary_candidates"], [])

    def test_all10_actual_leading_pairs_probabilities_and_cartesian_masses(self):
        jets = self.receipt["eligible_jets"]
        photons = self.receipt["root_readback"]["photons"][:2]
        probabilities = [Decimal(j["baseline_probability_persisted_pt"]) for j in jets]
        expected = {}
        with localcontext() as context:
            context.prec = 70
            for bits in itertools.product((False, True), repeat=5):
                tagged = [i for i, bit in enumerate(bits) if bit]
                if len(tagged) >= 2:
                    pair = tuple(tagged[:2])
                    chance = math.prod(p if bit else 1-p for p, bit in zip(probabilities, bits))
                    expected[pair] = expected.get(pair, Decimal(0)) + chance
            # Independent Cartesian summation in Decimal, using native stored
            # polar parameters; photon stored E is not the massless-P4 E.
            def vector(obj, photon=False):
                pt, eta, phi = (float(obj[k]) for k in ("pt", "eta", "phi"))
                xyz = [pt*math.cos(phi), pt*math.sin(phi), pt*math.sinh(eta)]
                m = 0 if photon else float(obj["mass"])
                e = math.sqrt(math.fsum(v*v for v in xyz) + m*abs(m))
                return [Decimal.from_float(v) for v in (*xyz, e)]
            def mass(objects):
                total = [sum(v[k] for v in objects) for k in range(4)]
                return float((total[3]**2 - sum(v*v for v in total[:3])).sqrt())
            self.assertEqual(len(self.receipt["possible_leading_tagged_pairs"]), 10)
            for pair in self.receipt["possible_leading_tagged_pairs"]:
                a, b = pair["leading_tagged_positions"]
                self.assertAlmostEqual(float(pair["probability"]), float(expected[(a,b)]), places=14)
                vectors = [vector(jets[a]), vector(jets[b])]
                self.assertAlmostEqual(pair["m_bb_gev"], mass(vectors), places=10)
                self.assertAlmostEqual(pair["m_bb_gamma_gamma_gev"], mass(vectors+[vector(p, True) for p in photons]), places=10)
            self.assertAlmostEqual(float(sum(expected.values())), float(self.receipt["event_probability_ge2"]), places=14)
            self.assertAlmostEqual(mass([vector(p, True) for p in photons]), 135.55650162670545, places=10)
        self.assertEqual(self.receipt["selection"]["N_btags"], 1)
        self.assertIsNone(self.receipt["selection"]["m_bb"])
        self.assertFalse(self.receipt["selection"]["cut_two_btags"])


if __name__ == "__main__":
    unittest.main()

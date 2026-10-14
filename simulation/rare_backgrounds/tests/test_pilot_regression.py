"""Independent all-event pilot regression; numerical replay only, no new MC.

Public JSONL rows were extracted by a separate actual ROOT reader. These tests
read that evidence and original LHE bytes, enumerate every tag configuration,
and use independent Cartesian mass/selection calculations. Native ROOT is not
opened here; its physical readback remains a hash-bound prior verification.
"""
from decimal import Decimal, localcontext
import gzip
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import platform
import re
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
PILOT = REPO / "simulation/rare_backgrounds/evidence/pilot"
SCRIPT = REPO / "simulation/rare_backgrounds/scripts/conditional_tags.py"
spec = importlib.util.spec_from_file_location("pilot_conditional_tags", SCRIPT)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
PROFILES = ("bbgg", "ccgg", "jjgg")
HOST_RELATIVE_ENVELOPE = Decimal(str(64*sys.float_info.epsilon))
EXPECTED_COUNTS = {
    "bbgg": (1000, 446, 266, 91, 28),
    "ccgg": (1000, 378, 241, 7, 1),
    "jjgg": (1000, 445, 277, 0, 0),
}
SOURCE_FILES = {
    "bbgg": "reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz",
    "ccgg": "reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz",
    "jjgg": "reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz",
}
# Independent predeclared family, deliberately not imported from the estimator.
MULTIPLIERS = {
    "baseline": ("1", "1", "1"),
    "b_down20": (".8", "1", "1"), "b_up20": ("1.2", "1", "1"),
    "c_down20": ("1", ".8", "1"), "c_up20": ("1", "1.2", "1"),
    "light_down20": ("1", "1", ".8"), "light_up20": ("1", "1", "1.2"),
    "joint_down20": (".8", ".8", ".8"), "joint_up20": ("1.2", "1.2", "1.2"),
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path, **kwargs):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(raw, **kwargs) for raw in stream]


def objects(row):
    jets = sorted((j for j in row["jets"] if float(j["pt"]) > 25 and abs(float(j["eta"])) < 2.5),
                  key=lambda j: (-float(j["pt"]), j["index"]))
    photons = sorted((p for p in row["photons"] if float(p["pt"]) > 25 and abs(float(p["eta"])) < 2.37
                      and not 1.37 < abs(float(p["eta"])) < 1.52),
                     key=lambda p: (-float(p["pt"]), p["index"]))
    photon_cut = len(photons) >= 2 and float(photons[0]["pt"]) > 35
    return jets, photons, photon_cut, photon_cut and len(jets) >= 2


def probability(jet, scenario):
    pt, flavor = float(jet["pt"]), jet["flavor"]
    if flavor == 5:
        p, category = .80 * math.tanh(.003 * pt) * (30 / (1 + .086 * pt)), 0
    elif flavor == 4:
        p, category = .20 * math.tanh(.02 * pt) * (1 / (1 + .0034 * pt)), 1
    elif flavor in (0, 1, 2, 3, 21):
        p, category = .002 + 7.3e-06 * pt, 2
    else:
        raise AssertionError("unsupported persisted flavor in actual pilot")
    return min(Decimal(1), max(Decimal(0), Decimal(str(p)) * Decimal(MULTIPLIERS[scenario][category])))


def enumerate_configurations(probabilities):
    """Independent exponential enumeration, feasible for this actual pilot."""
    assert len(probabilities) <= 12, "fixture no longer supports exhaustive enumeration"
    tail, pairs = Decimal(0), {}
    for configuration in itertools.product((0, 1), repeat=len(probabilities)):
        chance, tagged = Decimal(1), []
        for index, bit in enumerate(configuration):
            chance *= probabilities[index] if bit else 1 - probabilities[index]
            if bit:
                tagged.append(index)
        if len(tagged) >= 2:
            tail += chance
            pair = tuple(tagged[:2])
            pairs[pair] = pairs.get(pair, Decimal(0)) + chance
    return tail, pairs


def cartesian(obj, photon=False):
    # High precision energy/mass arithmetic is independent of the core's
    # binary64 construction. Trigonometric functions begin with native floats.
    pt, eta, phi = float(obj["pt"]), float(obj["eta"]), float(obj["phi"])
    x, y, z = (Decimal(str(value)) for value in (pt*math.cos(phi), pt*math.sin(phi), pt*math.sinh(eta)))
    mass = Decimal(0) if photon else Decimal(str(obj["mass"]))
    energy = (x*x + y*y + z*z + mass*abs(mass)).sqrt()
    return x, y, z, energy


def invariant_mass(vectors):
    x, y, z, energy = (sum(v[index] for v in vectors) for index in range(4))
    m2 = energy*energy - x*x - y*y - z*z
    assert m2 >= Decimal("-1e-30"), "unphysical independent Cartesian pair"
    return max(m2, Decimal(0)).sqrt()


class PilotRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = None
        cls.data, cls.bindings, cls.events, cls.summaries = {}, {}, {}, {}
        cls.metrics = {}
        cls.extraction = json.loads((PILOT/"extraction.json").read_text())
        for profile in PROFILES:
            input_path = PILOT/(profile+".jsonl")
            binding_path = PILOT/(profile+"_binding.json")
            cls.data[profile] = read_jsonl(input_path, parse_float=Decimal)
            cls.bindings[profile] = json.loads(binding_path.read_text())
            output = REPO/".local/phase6d/analytical"/profile
            if not (output/"conditional_summary.json").is_file():
                # Portable CI can replay the same already-generated numerical
                # pilot without ROOT or an additional detector event.
                if cls.temporary is None:
                    scratch = REPO/".local/phase6d"
                    scratch.mkdir(parents=True, exist_ok=True)
                    cls.temporary = tempfile.TemporaryDirectory(prefix="portable-pilot-regression-", dir=scratch)
                output = Path(cls.temporary.name)/profile
                model.analyze_file(input_path, binding_path, output)
            cls.events[profile] = read_jsonl(output/"conditional_events.jsonl")
            cls.summaries[profile] = json.loads((output/"conditional_summary.json").read_text())
            cls.metrics[profile] = {"records": len(cls.data[profile]), "input_sha256": sha(input_path),
                                    "binding_sha256": sha(binding_path), "analytic_events_sha256": sha(output/"conditional_events.jsonl"),
                                    "analytic_summary_sha256": sha(output/"conditional_summary.json"),
                                    "test_host_system": platform.system(),
                                    "output_mode": "existing frozen-core outputs" if output.is_relative_to(REPO) else "temporary portable numerical replay"}

    @classmethod
    def tearDownClass(cls):
        if cls.temporary is not None:
            # Recursive cleanup is restricted to this verified workspace
            # scratch directory, including on Windows.
            assert Path(cls.temporary.name).resolve().is_relative_to((REPO/".local/phase6d").resolve())
            cls.temporary.cleanup()

    def test_public_input_and_prior_native_full_file_hash_bindings(self):
        native = json.loads((REPO/"simulation/delphes/evidence/native_runs.json").read_text())
        full = {row["process"]:row for row in native["runs"] if row["stage"] == "stage_c"}
        for profile in PROFILES:
            binding = self.bindings[profile]
            original = full[profile]
            extracted = next(row for row in self.extraction["samples"] if row["process"] == profile)
            self.assertEqual(sha(PILOT/(profile+".jsonl")), binding["reco_sha256"])
            self.assertEqual(sha(PILOT/(profile+"_binding.json")), extracted["binding_sha256"])
            self.assertEqual(binding["root_sha256"], original["root_sha256"])
            self.assertEqual(binding["native_report_sha256"], original["native_report_sha256"])
            self.assertEqual(binding["native_scientific_content_sha256"], original["scientific_content_sha256"])
            self.assertEqual(binding["runtime_card_sha256"], original["runtime_card_sha256"])
            self.assertEqual(binding["events"], binding["normalization_denominator"])
            self.assertEqual(binding["events"], 1000)
            self.assertEqual(len(self.data[profile]), 1000)
            self.assertEqual(len(self.events[profile]), 1000)
            self.assertEqual(self.summaries[profile]["binding"], binding)
            self.assertEqual(self.summaries[profile]["input_binding_sha256"], extracted["binding_sha256"])
            self.assertEqual(binding["new_independent_physics_events"], 0)
            self.metrics[profile]["native_binding_status"] = "PASS; prior actual ROOT evidence hashes, no native ROOT opened by this test"

    def test_all_source_event_identities_and_exact_original_lhe_weights(self):
        for profile in PROFILES:
            source = REPO/SOURCE_FILES[profile]
            self.assertEqual(sha(source), self.bindings[profile]["source_mg5_sha256"])
            with gzip.open(source, "rb") as stream:
                raw = stream.read(20*1024**2+1)
            self.assertLess(len(raw), 20*1024**2)
            events = re.findall(rb"<event>.*?</event>", raw, flags=re.S)
            self.assertEqual(len(events), 1000)
            for ordinal, (original, row, result) in enumerate(zip(events, self.data[profile], self.events[profile], strict=True), 1):
                self.assertEqual(row["ordinal"], ordinal)
                self.assertEqual(row["native_event_number"], ordinal)
                self.assertEqual(row["source_event_index"], ordinal)
                self.assertEqual(row["source_event_hash"], hashlib.sha256(original).hexdigest())
                header = original[len(b"<event>"):].lstrip().splitlines()[0].split()
                weight = Decimal(header[2].decode().replace("D", "E"))/1000
                self.assertEqual(Decimal(row["source_contribution_pb"]), weight)
                self.assertEqual(Decimal(result["source_contribution_pb"]), weight)
                for key in ("ordinal", "native_event_number", "source_event_index", "source_event_hash", "input_hepmc_event_hash"):
                    self.assertEqual(result[key], row[key])
            self.metrics[profile]["original_lhe_identity_and_weight_records_checked"] = len(events)

    def test_independent_photon_cartesian_mass_and_frozen_cuts(self):
        for profile in PROFILES:
            counts = [0]*5
            max_mass_difference, mass_records = 0., 0
            for row, result in zip(self.data[profile], self.events[profile], strict=True):
                jets, photons, photon_cut, jet_cut = objects(row)
                count_tags = sum(jet["btag"]&1 for jet in jets)
                observed = jet_cut and count_tags >= 2
                with localcontext() as context:
                    context.prec = 80
                    if len(photons) >= 2:
                        mass = invariant_mass([cartesian(p, True) for p in photons[:2]])
                        self.assertAlmostEqual(float(mass), float(row["m_gamma_gamma"]), delta=1e-8+2e-12*float(mass))
                        max_mass_difference = max(max_mass_difference, abs(float(mass)-float(row["m_gamma_gamma"])))
                        mass_records += 1
                        independent_closed = math.sqrt(2*float(photons[0]["pt"])*float(photons[1]["pt"])*(
                            math.cosh(float(photons[0]["eta"])-float(photons[1]["eta"]))
                            - math.cos(float(photons[0]["phi"])-float(photons[1]["phi"]))))
                        self.assertAlmostEqual(float(mass), independent_closed, delta=1e-8+2e-12*float(mass))
                        mass_cut = Decimal(105) <= mass <= Decimal(160)
                    else:
                        self.assertIsNone(row["m_gamma_gamma"])
                        mass_cut = False
                self.assertEqual(row["cut_photons"], photon_cut)
                self.assertEqual(row["cut_jets"], jet_cut)
                self.assertEqual(row["N_jets"], len(jets))
                self.assertEqual(row["N_btags"], count_tags)
                self.assertEqual(row["cut_two_btags"], observed)
                self.assertEqual(row["cut_mgg"], observed and mass_cut)
                self.assertEqual(result["tag_independent_mgg"], mass_cut)
                for index, passed in enumerate((True, photon_cut, jet_cut, observed, observed and mass_cut)):
                    counts[index] += passed
            self.assertEqual(tuple(counts), EXPECTED_COUNTS[profile])
            self.metrics[profile]["observed_frozen_cut_counts"] = counts
            self.metrics[profile]["diphoton_cartesian_mass_records_checked"] = mass_records
            self.metrics[profile]["maximum_diphoton_mass_difference_gev"] = max_mass_difference

    def test_every_configuration_all_nine_scenarios_and_pair_mass_moments(self):
        for profile in PROFILES:
            with localcontext() as context:
                context.prec = 80
                max_dp_difference, max_q_difference, max_q_relative, max_moment_relative = (Decimal(0),)*4
                configurations, model_events, max_jets = 0, 0, 0
                totals = {scenario:{stage:{"expected_count":Decimal(0),"weighted_cross_section_pb":Decimal(0),
                                          "mbb_first_weighted":Decimal(0),"mbb_second_weighted":Decimal(0),
                                          "mbbgg_first_weighted":Decimal(0),"mbbgg_second_weighted":Decimal(0)}
                                  for stage in ("two_tags","mgg")} for scenario in MULTIPLIERS}
                for row, result in zip(self.data[profile], self.events[profile], strict=True):
                    jets, photons, _, jet_cut = objects(row)
                    self.assertLessEqual(len(jets), 12)
                    max_jets = max(max_jets, len(jets))
                    model_events += jet_cut
                    pair_masses = {}
                    if jet_cut:
                        jvec, pvec = [cartesian(j) for j in jets], [cartesian(p, True) for p in photons[:2]]
                        pair_masses = {(a,b):(invariant_mass([jvec[a],jvec[b]]), invariant_mass([jvec[a],jvec[b],*pvec]))
                                       for a in range(len(jets)) for b in range(a+1,len(jets))}
                    weight = Decimal(row["source_contribution_pb"])
                    for scenario in MULTIPLIERS:
                        probabilities = [probability(j, scenario) for j in jets]
                        q, pairs = enumerate_configurations(probabilities) if jet_cut else (Decimal(0), {})
                        # Strict arithmetic verification uses the same host's
                        # binary64 card inputs. Frozen Ubuntu probabilities
                        # are a separate cross-host math-library comparison.
                        dp = model.probability_at_least_two(probabilities) if jet_cut else Decimal(0)
                        self.assertLessEqual(abs(q-dp), Decimal("1e-44"))
                        max_dp_difference = max(max_dp_difference, abs(q-dp))
                        configurations += (2**len(jets)) if jet_cut else 0
                        actual = result["scenarios"][scenario]
                        frozen_q = Decimal(actual["stage_two_tags_probability"])
                        self.assertLessEqual(abs(q-frozen_q), abs(frozen_q)*HOST_RELATIVE_ENVELOPE+Decimal("1e-44"))
                        max_q_difference = max(max_q_difference, abs(q-frozen_q))
                        if frozen_q:
                            max_q_relative = max(max_q_relative, abs(q-frozen_q)/abs(frozen_q))
                        qgg = q if result["tag_independent_mgg"] else Decimal(0)
                        frozen_qgg = Decimal(actual["stage_mgg_probability"])
                        self.assertLessEqual(abs(qgg-frozen_qgg), abs(frozen_qgg)*HOST_RELATIVE_ENVELOPE+Decimal("1e-44"))
                        for stage, chance in (("two_tags",q),("mgg",qgg)):
                            total = totals[scenario][stage]
                            total["expected_count"] += chance
                            total["weighted_cross_section_pb"] += weight*chance
                            if stage == "two_tags" or result["tag_independent_mgg"]:
                                for (a,b), pair_probability in pairs.items():
                                    mbb, mbbgg = pair_masses[a,b]
                                    for name,mass in (("mbb",mbb),("mbbgg",mbbgg)):
                                        total[name+"_first_weighted"] += weight*pair_probability*mass
                                        total[name+"_second_weighted"] += weight*pair_probability*mass*mass
                for scenario, stages in totals.items():
                    for stage, expected in stages.items():
                        stored = self.summaries[profile]["results"][scenario][stage]
                        for key,value in expected.items():
                            actual = Decimal(stored[key])
                            if "weighted" in key and key != "weighted_cross_section_pb":
                                self.assertLessEqual(abs(actual-value), abs(value)*Decimal("2e-11")+Decimal("1e-13"))
                                if value:
                                    max_moment_relative = max(max_moment_relative, abs(actual-value)/abs(value))
                            else:
                                self.assertLessEqual(abs(actual-value), abs(value)*HOST_RELATIVE_ENVELOPE+Decimal("1e-42"))
                self.metrics[profile].update(
                    tag_model_events=model_events, maximum_eligible_jets=max_jets,
                    scenarios=9, all_event_scenario_probability_comparisons=1000*9,
                    exact_tag_configurations_enumerated=configurations,
                    maximum_same_host_dp_vs_exhaustive_probability_difference=str(max_dp_difference),
                    maximum_frozen_output_probability_difference=str(max_q_difference),
                    maximum_frozen_output_probability_relative_difference=str(max_q_relative),
                    cross_host_probability_relative_envelope=str(HOST_RELATIVE_ENVELOPE),
                    maximum_weighted_mass_moment_relative_difference=str(max_moment_relative),
                    weighted_mass_moment_comparisons=9*2*4)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Portable SOURCE_ONLY contracts and SYNTHETIC_METHOD_TEST numerical controls.

These checks cannot establish native ROOT/full local dataset readback on GitHub.
"""
import csv,hashlib,importlib.util,json,math,re,unittest
from collections import defaultdict
from decimal import Decimal,localcontext
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PACKAGE=ROOT/"analysis/phase8"
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def module(name):
    path=PACKAGE/"scripts"/(name+".py")
    spec=importlib.util.spec_from_file_location("phase8_ci_"+name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class ScientificContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=read(ROOT/"metadata/phase8_analysis_contract.json")
        cls.data=read(PACKAGE/"config/datasets.json")
        cls.selection=read(PACKAGE/"config/selection_v1.json")
        cls.edges=read(PACKAGE/"config/histogram_edges_v1.json")
        cls.observables=read(PACKAGE/"config/observables_v1.json")
        cls.post=module("postprocess")
    def test_existing_data_only_production_gates(self):
        c=self.contract;self.assertEqual(c["mode"],"EXISTING_DATA_ONLY")
        self.assertTrue(c["all_production_counters_required_zero"])
        forbidden={"NEW_ME_CALLS","NEW_INTEGRALS","NEW_HARD_EVENTS","NEW_PYTHIA_EVENTS","NEW_DELPHES_EVENTS","PHASE7I_RESTART","PHYSICAL_COMBINED_LIKELIHOOD","PHYSICAL_SIGNIFICANCE","PHYSICAL_CLS","PHYSICAL_KAPPA_LIMIT"}
        self.assertTrue(forbidden.issubset(c["prohibited_operations"]))
    def test_original_dataset_denominators(self):
        self.assertEqual([r["dataset_id"] for r in self.data["datasets"]],self.contract["datasets"])
        self.assertEqual(sum(r["N_original"] for r in self.data["datasets"]),self.contract["expected_independent_sources"])
        self.assertEqual(self.contract["expected_independent_sources"],7100)
        self.assertFalse(self.contract["kappa_rows_are_independent_events"])
    def test_signal_configurations_are_distinct(self):
        b,c=self.data["datasets"][:2]
        self.assertNotEqual(b["actual_effective_PDF"],c["actual_effective_PDF"])
        self.assertNotEqual(b["actual_alpha_running"],c["actual_alpha_running"])
        self.assertEqual((b["actual_effective_seed"],c["actual_effective_seed"]),(21,20261122))
    def test_weight_conventions_do_not_double_apply(self):
        w=self.contract["weights"]
        self.assertFalse(w["sumw2_is_sampling_variance"])
        self.assertFalse(w["conditional_tag_variance_added_to_observed_sampling_variance"])
        self.assertFalse(w["integration_error_combined_with_event_variance"])
        self.assertEqual(w["pb_to_100fb_inverse"],1000*100)
        for row in self.data["datasets"]:
            self.assertEqual(row["BR_factor_applications"],0 if row["model_br_factor"]==1 else 1)
            self.assertEqual(row["expected_cutflow"][0],row["N_original"])
    def test_observables_and_histogram_edges(self):
        names=self.observables["names"];self.assertEqual(len(names),26);self.assertEqual(len(set(names)),26)
        self.assertEqual(set(names),set(self.edges["observables"]))
        self.assertTrue(self.observables["undefined_is_null_not_zero"])
        for name,item in self.edges["observables"].items():
            values=item["edges"];self.assertGreaterEqual(len(values),2)
            self.assertTrue(all(math.isfinite(v) for v in values))
            self.assertTrue(all(a<b for a,b in zip(values,values[1:])))
            self.assertTrue(item["unit"]);self.assertTrue(item["rationale"])
        self.assertEqual(self.edges["flow_policy"],"INCLUDE_UNDERFLOW_AND_OVERFLOW_IN_SHAPE_DENOMINATOR")
    def test_fixed_selection_contract(self):
        s=self.selection
        self.assertEqual((s["photon_leading_pt"],s["photon_subleading_pt"]),(35,25))
        self.assertEqual((s["photon_max_abs_eta"],s["photon_crack_min"],s["photon_crack_max"]),(2.37,1.37,1.52))
        self.assertEqual((s["jet_min_pt"],s["jet_max_abs_eta"],s["btag_mask"]),(25,2.5,1))
        self.assertEqual((s["mgg_min"],s["mgg_max"]),(105,160));self.assertIsNone(s["mbb_cut"])
        self.assertFalse(s["official_ATLAS_calibrated"])
    def test_region_boundaries(self):
        f=self.post.mass_region
        for value,label in [(105,"LOW"),(math.nextafter(120,-math.inf),"LOW"),(120,"HIGGS"),(130,"HIGGS"),(math.nextafter(130,math.inf),"HIGH"),(160,"HIGH"),(math.nextafter(160,math.inf),"OUTSIDE_MGG"),(None,"UNDEFINED_MGG")]:self.assertEqual(f(value),label)
        with self.assertRaises(ValueError):f(float("nan"))
    def test_tag_partition_and_invalid_values(self):
        self.assertEqual([self.post.tag_region(n) for n in (0,1,2,7)],["TAG_0","TAG_1","TAG_GE2","TAG_GE2"])
        for n in (-1,.5):
            with self.assertRaises(ValueError):self.post.tag_region(n)
    def test_unknown_systematics_stay_null(self):
        rows=self.post.systematics();self.assertEqual(len(rows),22)
        for row in rows:
            self.assertIsNone(row["physical_value"]);self.assertIsNone(row["physical_constraint"])
            self.assertIsNone(row["correlation_model"]);self.assertFalse(row["toy_value_used_for_physical_data"])
            self.assertFalse(row["official_ATLAS_calibration"])
    def test_public_portable_paths(self):
        for row in self.data["datasets"]:
            for key,value in row.items():
                if key.endswith("_path"):self.assertTrue(value.startswith(("LOCAL_HOME/","REPOSITORY/")),key)
                if key.endswith("_sha256"):self.assertRegex(value,r"^[0-9a-f]{64}$")
    def test_public_payload_bounds_and_no_private_paths(self):
        paths=list(PACKAGE.rglob("*"))+list((ROOT/"metadata").glob("phase8*"))+list((ROOT/"reports").glob("phase8*"))
        private=re.compile(r"/(?:ho"+r"me|Us"+r"ers)/[^/\s]+/|[A-Za-z]:[\\/]Us"+r"ers[\\/]",re.I)
        for path in paths:
            if not path.is_file() or "__pycache__" in path.parts:continue
            self.assertLess(path.stat().st_size,25*1024*1024,str(path.relative_to(ROOT)))
            self.assertNotIn(path.suffix.lower(),(".root",".png",".pdf",".exe",".so",".lhe",".hepmc3",".jsonl"))
            self.assertIsNone(private.search(path.read_text(encoding="utf-8")),str(path.relative_to(ROOT)))
    def test_publication_and_analysis_resource_contract(self):
        p=self.contract["publication"];self.assertTrue(p["one_new_stacked_Draft_PR"])
        for key in ("unapproved_PNG_PDF","physical_ROOT_samples_native_binaries_full_event_dump","merge","force_push"):self.assertFalse(p[key])
        c=self.contract["resource_ceilings"]
        self.assertEqual((c["wall_seconds"],c["CPU_seconds"],c["additional_output_bytes"],c["concurrent_analysis_jobs"],c["workers"]),(14400,14400,2*1024**3,1,1))

class PublicNumericEvidenceTests(unittest.TestCase):
    def test_actual_published_payload_sha256(self):
        import hashlib
        directory=Path(__file__).resolve().parents[3]/'reference_samples/phase8/v1'
        manifest=json.loads((directory/'manifest.json').read_text())
        self.assertLess(sum(v['bytes'] for v in manifest['files'].values()),5*1024*1024)
        for name,expected in manifest['files'].items():
            data=(directory/name).read_bytes()
            self.assertEqual(len(data),expected['bytes'],name)
            self.assertEqual(hashlib.sha256(data).hexdigest(),expected['sha256'],name)

class IndependentNumericalMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.stat=module("independent_statistics");cls.post=module("postprocess")
    def test_fixed_N_centered_signed_variance(self):
        s=self.stat.moments([Decimal(1),Decimal(-1),Decimal(0),Decimal(0)])
        self.assertEqual(s["sumw"],0);self.assertEqual(s["sum_absw"],2);self.assertEqual(s["sumw2"],2)
        self.assertEqual(s["fixed_N_source_sampling_variance"],Decimal(8)/3)
        self.assertEqual(s["ESS"],0);self.assertEqual(s["N_negative"],1)
        self.assertAlmostEqual(self.post.summary([1,-1],4)["fixed_N_variance"],8/3)
    def test_paired_covariance_positive_semidefinite_example(self):
        a=[Decimal(1),Decimal(2),Decimal(3),Decimal(4)];b=[-x for x in a]
        aa=self.stat.covariance(a,a);bb=self.stat.covariance(b,b);ab=self.stat.covariance(a,b)
        self.assertEqual(aa,bb);self.assertEqual(ab,-aa);self.assertGreaterEqual(aa*bb-ab*ab,0)
    def test_conditional_probability_and_empty_undefined(self):
        self.assertEqual(self.stat.conditional_probability([]),0)
        self.assertEqual(self.stat.conditional_probability([{"pt":50,"flavour":5}]),0)
        jets=[{"pt":50,"flavour":5},{"pt":100,"flavour":4}]
        self.assertEqual(self.stat.conditional_probability(jets),self.stat.tag_probability(jets[0])*self.stat.tag_probability(jets[1]))
        self.assertIsNone(self.stat.moments([0,0])["ESS"])
    def test_actual_frozen_kappa_rows_are_1000_paired_sources(self):
        data=read(PACKAGE/"config/datasets.json");source=data["kappa_rows"]
        path=ROOT/source["path"].removeprefix("REPOSITORY/")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),source["sha256"])
        with path.open(newline="") as stream:rows=list(csv.DictReader(stream))
        self.assertEqual(len(rows),6000);groups=defaultdict(list)
        for row in rows:
            groups[int(row["source_event_index"])].append(row)
            self.assertTrue(Decimal(row["source_contribution_pb"]).is_finite())
        self.assertEqual(set(groups),set(range(1,1001)))
        benchmarks={Decimal(-1),Decimal(0),Decimal(1),Decimal(2),Decimal("2.5"),Decimal(5)}
        for values in groups.values():
            self.assertEqual(len(values),6);self.assertEqual({Decimal(v["kappa_lambda"]) for v in values},benchmarks)
            self.assertEqual(len({v["source_event_sha256"] for v in values}),1)

if __name__=="__main__":unittest.main(verbosity=2)

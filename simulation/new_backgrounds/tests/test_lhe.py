"""Numerical METHOD_ONLY and rejection tests; no physical sample acceptance."""
from copy import deepcopy
from decimal import Decimal
import gzip
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("background_test_lhe",REPO/"simulation/new_backgrounds/validate_lhe.py")
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def particle(pdg,status,mothers,colors,p4,mass=0):
    return [pdg,status,*mothers,*colors,*p4,mass,0,9]


def fixture_rows(process):
    """Private algebra fixtures: not generated events, never physical PASS."""
    if process=="tth":
        return [[5,1,1,235.5,1/132.507,0.13],
                particle(2,-1,(0,0),(501,0),(0,0,235.5,235.5)),
                particle(-2,-1,(0,0),(0,502),(0,0,-235.5,235.5)),
                particle(6,1,(1,2),(501,0),(0,0,0,173),173),
                particle(-6,1,(1,2),(0,502),(0,0,0,173),173),
                particle(25,1,(1,2),(0,0),(0,0,0,125),125)]
    return [[6,1,1,125,1/132.507,0.13],
            particle(21,-1,(0,0),(501,502),(0,0,100,100)),
            particle(21,-1,(0,0),(503,504),(0,0,-100,100)),
            particle(5,1,(1,2),(501,0),(50,0,0,50)),
            particle(-5,1,(1,2),(0,502),(0,50,0,50)),
            particle(22,1,(1,2),(0,0),(-50,0,0,50)),
            particle(21,1,(1,2),(503,504),(0,-50,0,50))]


def element(rows):
    value=ET.Element("event");value.text="\n"+"\n".join(" ".join(str(x) for x in row) for row in rows)+"\n";return value


class LHETests(unittest.TestCase):
    def setUp(self):
        scratch=REPO/".local/phase6g_backgrounds/tests";scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(prefix="method_only_lhe_",dir=scratch);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def physics(self,process):
        old=v.CARDS.validate_bundle()["physics"]
        return {**old,"scales":{**old["scales"],"muR_gev":v.STAGE.RUN_OVERRIDES[process].get("scale",216.188)}}
    def reject(self,rows,process,message):
        with self.assertRaisesRegex(ValueError,message):v.event_particles(element(rows),process,self.physics(process))
    def test_exact_cards_for_all_profiles_and_request_seed_bound(self):
        for alias,seed in (("zh",20261104),("tth",20261105),("bbgj",20261106)):
            cards=v.prepared_contract(seed,alias);values=v.check_cards(cards,cards,seed,alias)
            self.assertEqual(values["nevents"],1000);self.assertEqual(values["iseed"],seed)
            self.assertEqual(cards["profile"],v.PROFILES[alias])
    def test_changed_process_orders_and_j4_definition_rejected(self):
        for alias in v.PROFILES:
            card=v.prepared_contract(42,alias)["process_card"]
            with self.subTest(alias=alias),self.assertRaises(ValueError):v.process_card(card.replace("QED=", "QED=9"),process=alias)
        card=v.prepared_contract(42,"bbgj")["process_card"]
        with self.assertRaises(ValueError):v.process_card(card.replace("define j4 = g", "define j4 = b g"),expanded=True,process="bbgj")
    def test_exact_supported_nosave_flags_preserve_settings_and_duplicate_flags_reject(self):
        card="set automatic_html_opening False --no_save\nset auto_update 0 --no_save\nset nb_core 1 --no_save\nset run_mode 0 --no_save\n"+v.prepared_contract(42)["process_card"]+"output process -nojpeg\n"
        v.process_card(card,expanded=True)
        with self.assertRaises(ValueError):v.process_card(card.replace("auto_update 0", "auto_update 1"),expanded=True)
        with self.assertRaises(ValueError):v.process_card(card.replace("auto_update 0 --no_save", "auto_update 0 --no_save --no_save"),expanded=True)
    def test_any_generation_cut_scale_or_mass_change_rejected(self):
        original=v.prepared_contract(42,"bbgj")
        for key,val in (("run_card",original["run_card"].replace("25.0", "24.0")),("param_card",original["param_card"].replace("1.730000e+02", "1.720000e+02"))):
            actual=dict(original);actual[key]=val
            with self.subTest(key=key),self.assertRaises(ValueError):v.check_cards(actual,original,42,"bbgj")
    def test_only_five_exact_official_implicit_defaults_can_be_serialized(self):
        original=v.prepared_contract(42,"bbgj");actual=dict(original)
        added="".join(str(value)+" = "+key+"\n" for key,value in v.OFFICIAL_IMPLICIT_RUN_DEFAULTS.items())
        actual["run_card"]+=added
        read=v.check_cards(actual,original,42,"bbgj")
        self.assertEqual({key:read[key] for key in v.OFFICIAL_IMPLICIT_RUN_DEFAULTS},v.OFFICIAL_IMPLICIT_RUN_DEFAULTS)
        for key,value in v.OFFICIAL_IMPLICIT_RUN_DEFAULTS.items():
            wrong=not value if type(value) is bool else value+1
            bad=dict(actual);bad["run_card"]=bad["run_card"].replace(str(value)+" = "+key,str(wrong)+" = "+key)
            with self.subTest(key=key),self.assertRaises(ValueError):v.check_cards(bad,original,42,"bbgj")
        bad=dict(actual);bad["run_card"]+="0 = unreviewed_setting\n"
        with self.assertRaises(ValueError):v.check_cards(bad,original,42,"bbgj")
    def test_missing_explicit_request_or_physics_field_cannot_be_a_default(self):
        import re
        original=v.prepared_contract(42)
        for key in ("iseed","nevents","cut_decays","dsqrt_q2fact2","drab"):
            bad=dict(original);bad["run_card"]=re.sub(r"^[^\n=]*=\s*"+key+r"\b[^\n]*\n","",bad["run_card"],flags=re.M)
            with self.subTest(key=key),self.assertRaises(ValueError):v.check_cards(bad,original,42)
    def test_historical_binding_comparison_limits_repairs_and_three_nonexecuted_helpers(self):
        original=[{"path":"simulation/new_backgrounds/mg5_stage.py","sha256":"0"*64}]+[{"path":path,"sha256":digest} for path,digest in v.LEGACY_SOURCE_CHANGES.items()]
        fixed={"simulation/new_backgrounds/delphes_stage.py":v.DELPHES_REUSE_REPAIR_SHA,
               "simulation/new_backgrounds/src/analyze_background_root.cxx":v.ROOT_SIGNED_JET_REPAIR_SHA,
               "simulation/new_backgrounds/src/validate_background_hepmc3.cxx":v.READER_STATUS_CONTEXT_SHA,
               "simulation/new_backgrounds/scripts/shower_stage.py":v.SHOWER_PREFIX_REUSE_SHA}
        current=[{"path":row["path"],"sha256":fixed.get(row["path"],"1"*64 if row["path"] in v.LEGACY_SOURCE_CHANGES else row["sha256"])} for row in original]
        changes,added=v.compare_historical_source_bindings(original,current)
        self.assertEqual(len(changes),6);self.assertEqual(added,[])
        for path in v.NONEXECUTED_REVIEW_ADDITIONS:
            _,added=v.compare_historical_source_bindings(original,current+[{"path":path,"sha256":"2"*64}])
            self.assertEqual(added,[path])
        bad=deepcopy(current);bad[0]["sha256"]="3"*64
        with self.assertRaisesRegex(ValueError,"Original executed"):v.compare_historical_source_bindings(original,bad)
        with self.assertRaises(ValueError):v.compare_historical_source_bindings(original,current[1:])
        with self.assertRaises(ValueError):v.compare_historical_source_bindings(original,current+[{"path":"simulation/new_backgrounds/extra_generator.py","sha256":"2"*64}])
        wrong=deepcopy(original);wrong[1]["sha256"]="4"*64
        with self.assertRaises(ValueError):v.compare_historical_source_bindings(wrong,current)
        changed=deepcopy(current);next(row for row in changed if row["path"]=="simulation/new_backgrounds/delphes_stage.py")["sha256"]="4"*64
        with self.assertRaisesRegex(ValueError,"non-generating ROOT10/100"):v.compare_historical_source_bindings(original,changed)
        for path,label in (("simulation/new_backgrounds/src/validate_background_hepmc3.cxx","Event-context"),
                           ("simulation/new_backgrounds/scripts/shower_stage.py","non-generating prefix10"),
                           ("simulation/new_backgrounds/src/analyze_background_root.cxx","signed-jet numerical")):
            changed=deepcopy(current);next(row for row in changed if row["path"]==path)["sha256"]="4"*64
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,label):v.compare_historical_source_bindings(original,changed)
        header={"path":"simulation/new_backgrounds/include/BackgroundAncestry.hxx","sha256":"0"*64}
        with self.assertRaisesRegex(ValueError,"Original executed"):
            v.compare_historical_source_bindings(original+[header],current+[{"path":header["path"],"sha256":"4"*64}])
    def test_readonly_source_exceptions_reject_every_prior_downstream_event_counter(self):
        manifest={"scope":"METHOD_ONLY_CONTROL_METADATA","MG5_events_generated":1000,"Pythia_events_attempted":0,
                  "Pythia_events_written":0,"HepMC_validated_events":0,"Delphes_ROOT_entries":0,"stages_attempted":[]}
        v.check_original_source_only_manifest(manifest)
        for key in ("Pythia_events_attempted","Pythia_events_written","HepMC_validated_events","Delphes_ROOT_entries"):
            for value in (1,False):
                bad=deepcopy(manifest);bad[key]=value
                with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,"prior downstream"):
                    v.check_original_source_only_manifest(bad)
    def test_root_numeric_and_reuse_exceptions_require_exact_original_and_final_hashes(self):
        root="simulation/new_backgrounds/src/analyze_background_root.cxx"
        driver="simulation/new_backgrounds/delphes_stage.py"
        original=[{"path":root,"sha256":v.LEGACY_SOURCE_CHANGES[root]},{"path":driver,"sha256":v.LEGACY_SOURCE_CHANGES[driver]}]
        current=[{"path":root,"sha256":v.ROOT_SIGNED_JET_REPAIR_SHA},{"path":driver,"sha256":v.DELPHES_REUSE_REPAIR_SHA}]
        changes,_=v.compare_historical_source_bindings(original,current)
        self.assertEqual({row["role"] for row in changes},{"READ_ONLY_NATIVE_SIGNED_JET_NUMERICAL_VALIDATION_FIX_NO_MC",
                                                         "DOWNSTREAM_RELATIVE_OUTPUT_AND_NON_GENERATING_ROOT10_100_REUSE"})
        wrong=deepcopy(original);wrong[0]["sha256"]="4"*64
        with self.assertRaisesRegex(ValueError,"Original executed"):v.compare_historical_source_bindings(wrong,current)
        for index in (0,1):
            wrong=deepcopy(current);wrong[index]["sha256"]="4"*64
            with self.subTest(index=index),self.assertRaises(ValueError):v.compare_historical_source_bindings(original,wrong)
        intermediate=deepcopy(current);intermediate[1]["sha256"]=v.DELPHES_FILENAME_ONLY_SHA
        with self.assertRaisesRegex(ValueError,"non-generating ROOT10/100"):v.compare_historical_source_bindings(original,intermediate)
    def test_readonly_source_exceptions_reject_prior_attempts_even_with_zero_event_counters(self):
        manifest={"scope":"METHOD_ONLY_CONTROL_METADATA","MG5_events_generated":1000,"Pythia_events_attempted":0,
                  "Pythia_events_written":0,"HepMC_validated_events":0,"Delphes_ROOT_entries":0,"stages_attempted":[]}
        for stage in ("shower_background_prefix10","background_reader_prefix10","shower_background_full1000","delphes_prefix10"):
            bad=deepcopy(manifest);bad["stages_attempted"]=[{"stage":stage}]
            with self.subTest(stage=stage),self.assertRaisesRegex(ValueError,"prior physical"):
                v.check_original_source_only_manifest(bad)
    def test_historical_recheck_never_accepts_an_unpinned_bridge_or_fixture_source(self):
        path=self.root/"method_only_invalid_source.lhe";path.write_bytes(b"METHOD_ONLY_NOT_THE_ORIGINAL_SOURCE")
        for digest in ("0"*64,v.LEGACY_BRIDGE):
            with self.subTest(digest=digest),self.assertRaisesRegex(ValueError,"historical bridge/source"):
                v.historical_bridge_binding({"bridge_sha256":digest},path,[])
    def test_private_ttH_numerical_anchor_and_source_weight_identity(self):
        checked=v.event_particles(element(fixture_rows("tth")),"tth",self.physics("tth"))
        self.assertEqual([p["pdg_id"] for p in checked["particles"] if p["status"]==1],[6,-6,25])
        self.assertEqual(checked["closure_residual_gev"],0);self.assertEqual(checked["weight"],Decimal(1))
    def test_ttH_wrong_top_mass_or_missing_higgs_rejected(self):
        rows=fixture_rows("tth");rows[3][10]=172.5;self.reject(rows,"tth","Wrong top")
        rows=fixture_rows("tth");rows[-1][0]=22;rows[-1][10]=0;self.reject(rows,"tth","mass-shell")
    def test_ttH_source_decay_or_wrong_mothers_rejected(self):
        rows=fixture_rows("tth");rows[3][1]=2;self.reject(rows,"tth","status")
        rows=fixture_rows("tth");rows[3][2:4]=[3,3];self.reject(rows,"tth","mothers")
    def test_nonfinite_particle_or_event_weight_rejected(self):
        rows=fixture_rows("tth");rows[0][2]="NaN";self.reject(rows,"tth","Nonfinite")
        rows=fixture_rows("bbgj");rows[3][6]="Infinity";self.reject(rows,"bbgj","Nonfinite")
    def test_private_one_photon_bbgj_cut_anchor(self):
        checked=v.event_particles(element(fixture_rows("bbgj")),"bbgj",self.physics("bbgj"))
        self.assertEqual(sum(p["pdg_id"]==22 for p in checked["particles"]),1);self.assertEqual(checked["closure_residual_gev"],0)
    def test_bbgj_second_born_photon_and_bottom_jet_alias_rejected(self):
        rows=fixture_rows("bbgj");rows[-1][0]=22;rows[-1][4:6]=[0,0];self.reject(rows,"bbgj","exactly")
        rows=fixture_rows("bbgj");rows[-1][0]=5;rows[-1][5]=0;self.reject(rows,"bbgj","exactly")
    def test_bbgj_soft_bottom_photon_or_jet_rejected(self):
        for index in (3,4,5,6):
            rows=fixture_rows("bbgj");rows[index][6:10]=[x*0.1 for x in rows[index][6:10]]
            with self.subTest(index=index):self.reject(rows,"bbgj","pT/eta")
    def test_bbgj_forward_particle_rejected(self):
        rows=fixture_rows("bbgj");rows[3][8]=1000;rows[3][9]=math.hypot(50,1000);self.reject(rows,"bbgj","pT/eta")
    def test_bbgj_collinear_pairs_rejected_for_all_pair_types(self):
        for a,b in ((3,4),(3,5),(3,6),(5,6)):
            rows=fixture_rows("bbgj");rows[b][6:10]=rows[a][6:10]
            with self.subTest(pair=(a,b)):self.reject(rows,"bbgj","DeltaR")
    def test_color_and_momentum_closure_are_independent_gates(self):
        rows=fixture_rows("bbgj");rows[3][4]=777;self.reject(rows,"bbgj","color-flow")
        rows=fixture_rows("bbgj");rows[-1][7]=-60;rows[-1][9]=60;self.reject(rows,"bbgj","four-momentum")
    def test_bbgj_fixed_scale_and_beam_energy_checked(self):
        rows=fixture_rows("bbgj");rows[0][3]=216.188;self.reject(rows,"bbgj","scale")
        rows=fixture_rows("bbgj");rows[1][8:10]=[7000,7000];self.reject(rows,"bbgj","beams")
    def test_synthetic_scope_cannot_be_physically_accepted(self):
        path=self.root/"not_generated.lhe"
        path.write_text('<LesHouchesEvents version="3.0"><header><BackgroundFixtureScope>METHOD_ONLY</BackgroundFixtureScope></header><init></init><event></event></LesHouchesEvents>')
        with self.assertRaises(v.ValidationError) as caught:v.validate_file(path,expected_seed=42,card_contract=v.prepared_contract(42))
        self.assertFalse(caught.exception.report["physical_acceptance"]);self.assertIn("Synthetic",caught.exception.report["error"])
    def test_complete_gzip_crc_is_required(self):
        path=self.root/"truncated.lhe.gz";path.write_bytes(gzip.compress(b"<LesHouchesEvents/>" )[:-3])
        with self.assertRaisesRegex(ValueError,"Gzip"):v.bounded_bytes(path)
    def test_entities_and_excess_bytes_rejected(self):
        path=self.root/"bad.lhe";path.write_bytes(b'<!DOCTYPE x [<!ENTITY fake "bad">]><x/>')
        with self.assertRaisesRegex(ValueError,"DTD"):v.bounded_bytes(path)
    def test_source_validator_requires_full_original1000_and_profile(self):
        for args in ({"expected_events":100},{"expected_events":True},{"profile":"B01_BBGG"},{"expected_seed":False}):
            with self.subTest(args=args),self.assertRaises(v.ValidationError):v.validate_file(self.root/"missing",**args)
    def test_amplitude_gate_rejects_wrong_orders_or_topology(self):
        records=[{"scope":"production","initial_pdgs":[21,21],"final_pdgs":[6,-6,25],"diagram_count":8,"actual_amplitude_orders":[{"QCD":2,"QED":1}]}]
        v.validate_amplitude_records(records,"tth")
        for key,value in (("diagram_count",0),("actual_amplitude_orders",[{"QCD":0,"QED":3}]),("final_pdgs",[6,-6,22])):
            bad=deepcopy(records);bad[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.validate_amplitude_records(bad,"tth")
    def test_downstream_missing_source_and_wrong_prefix_are_not_accepted(self):
        with self.assertRaises(ValueError):v.validate_downstream_binding({"status":"METHOD_ONLY","source_total_events":100},[],expected_output_count=10,method_only=True)
        with self.assertRaises(ValueError):v.validate_downstream_binding({"status":"PASS_LHE_RECORDS","source_total_events":1000,"source_events":[]},[],expected_output_count=10)


if __name__=="__main__":unittest.main()

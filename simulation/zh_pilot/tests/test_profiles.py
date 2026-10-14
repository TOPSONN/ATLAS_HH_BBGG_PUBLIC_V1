"""Bounded synthetic METHOD_ONLY fixtures; never generated physics samples.

No fixture is published as an LHE/HepMC/ROOT reference. Temporary XML/JSON
exists only for parser/serialization/failure controls and is deleted.
"""
import copy
from decimal import Decimal
import gzip
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO=Path(__file__).resolve().parents[3]
SCRIPT=REPO/"simulation/zh_pilot/scripts/validate_profiles.py"
spec=importlib.util.spec_from_file_location("phase6f_profiles",SCRIPT)
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
CONTRACT=v.load_json(REPO/"simulation/zh_pilot/config/generator_contract.json")


def lhe_fixture(profile="ZH_ZBB_STABLE_H",weights=("1",)):
    """Analytic threshold coordinates test algebra, not a physical MC sample."""
    checker=v.module("phase6f_test_card_reader",REPO/"simulation/zh_pilot/scripts/check_generator.py")
    cards={x["id"]:(REPO/x["path"]).read_text() for x in CONTRACT["cards"]}
    root=ET.Element("LesHouchesEvents",version="3.0")
    header=ET.SubElement(root,"header")
    ET.SubElement(header,"MGVersion").text="3.5.16"
    ET.SubElement(header,"ZHFixtureScope").text="METHOD_ONLY"
    ET.SubElement(header,"MG5ProcCard").text=cards["process_stable" if profile=="ZH_STABLE" else "process_zbb"]
    run=cards["run"].replace("100 = nevents",str(len(weights))+" = nevents")
    ET.SubElement(header,"MGRunCard").text=run
    ET.SubElement(header,"slha").text=cards["param"]
    init=ET.SubElement(root,"init")
    init.text="\n2212 2212 6500 6500 0 0 10042 10042 -4 1\n1 0 1 1\n"
    ET.SubElement(init,"generator",name="MadGraph5_aMC@NLO",version="3.5.16")
    incoming=["2 -1 0 0 501 0 0 0 108.094 108.094 0 0 9", "-2 -1 0 0 0 501 0 0 -108.094 108.094 0 0 9"]
    final=["23 1 1 2 0 0 0 0 0 91.188 91.188 0 9", "25 1 1 2 0 0 0 0 0 125 125 0 9"]
    if profile=="ZH_ZBB_STABLE_H":
        final[0]=final[0].replace("23 1", "23 2")
        final += ["5 1 3 3 502 0 0 0 45.594 45.594 0 0 9", "-5 1 3 3 0 502 0 0 -45.594 45.594 0 0 9"]
    for w in weights:
        ET.SubElement(root,"event").text=f"\n{len(incoming+final)} 1 {w} 216.188 .0075 .13\n"+"\n".join(incoming+final)+"\n"
    return root


def node(pid,pdg,status,mothers,daughters,mass=0,p4=(0,0,0,1)):
    return {"id":pid,"pdg_id":pdg,"status":status,"mothers":mothers,"daughters":daughters,"mass_gev":mass,"p4_gev":list(p4)}


def graph_fixture():
    return {"fixture_scope":"METHOD_ONLY","units":{"momentum":"GEV","length":"MM"},
        "source_lhe_profile":"ZH_ZBB_STABLE_H","source_file_sha256":"1"*64,"source_event_sha256":"2"*64,"source_event_index":1,
        "source_total_events":100,"cross_section_unit":"PB","pythia_sigmaGen_unit":"MB",
        "LHE_XWGTUP_pb":"1","Pythia_Info_weight_pb":"1","converter_weight_0_pb":"1","input_contribution_pb":".01",
        "weight_names":["input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb","converter_weight_0_pb"],"weight_values":[".01","1","1","1"],
        "physical_BR_factor":".002","exclusive_contribution_pb":".00002",
        "source_cross_section_pb":"1","pythia_sigmaGen_mb":"1e-9","pythia_sigmaGen_pb":"1",
        "source_model_parameters":{"MZ_gev":"91.188","MH_gev":"125","WZ_gev":"2.441404","WH_gev":".00638233934"},
        "br_ledger":{"source_included_decay_ids":["Z_to_b_bbar"],"nominal_decay_ids_in_pythia_weight":[],
                     "missing_external_decay_ids":["H_to_gamma_gamma"],"branching_ratios":{"Z_to_b_bbar":".2","H_to_gamma_gamma":".002"}},
        "resonance_ids":{"Z":3,"H":4},"z_bottom_birth_ids":[5,6],"higgs_photon_birth_ids":[7,8],"higgs_final_photon_ids":[7,8],
        "particles":[node(1,2,21,[],[3,4]),node(2,-2,21,[],[3,4]),
                     node(3,23,2,[1,2],[5,6],91.188,(0,0,0,91.188)),node(4,25,2,[1,2],[7,8],125,(0,0,0,125)),
                     node(5,5,23,[3],[],0,(0,0,45.594,45.594)),node(6,-5,23,[3],[],0,(0,0,-45.594,45.594)),
                     node(7,22,1,[4],[],0,(62.5,0,0,62.5)),node(8,22,1,[4],[],0,(-62.5,0,0,62.5))]}


class LHEProfileMethods(unittest.TestCase):
    def validate(self,tree,profile="ZH_ZBB_STABLE_H",weights=1,gz=False):
        with tempfile.TemporaryDirectory(prefix="zh_synthetic_method_",dir=REPO) as directory:
            path=Path(directory)/("METHOD_ONLY.lhe.gz" if gz else "METHOD_ONLY.lhe")
            raw=ET.tostring(tree)
            if gz:
                with gzip.open(path,"wb") as out:out.write(raw)
            else:path.write_bytes(raw)
            return v.validate_lhe(path,profile,weights,CONTRACT,method_only=True)

    def test_both_source_topologies_method_only_and_stable_sum(self):
        for profile in ("ZH_STABLE","ZH_ZBB_STABLE_H"):
            result=self.validate(lhe_fixture(profile),profile)
            self.assertEqual(result["status"],"METHOD_ONLY")
            self.assertFalse(result["physical_acceptance"])
            self.assertLess(result["maximum_closure_residual_gev"],1e-12)
            self.assertEqual(result["events"],1)
        self.assertEqual(self.validate(lhe_fixture(),gz=True)["status"],"METHOD_ONLY")

    def test_signed_weights_preserved_over_full_original_fixture_count(self):
        result=self.validate(lhe_fixture(weights=("3","-1")),weights=2)
        self.assertEqual(result["negative_weights"],1)
        self.assertEqual(Decimal(result["nominal_weight_mean_pb"]),1)

    def test_missing_events_and_duplicate_cards_rejected(self):
        tree=lhe_fixture();tree.remove(tree.find("event"))
        with self.assertRaises(ValueError):self.validate(tree)
        tree=lhe_fixture();ET.SubElement(tree.find("header"),"MGRunCard").text="1 = nevents"
        with self.assertRaises(ValueError):self.validate(tree)

    def test_wrong_ancestry_mass_width_color_and_couplings_rejected(self):
        for before,after in (("5 1 3 3","5 1 1 2"),("91.188 91.188","91.188 90"),("0 502 0 0 -45.594","0 503 0 0 -45.594")):
            tree=lhe_fixture();event=tree.find("event");event.text=event.text.replace(before,after)
            with self.subTest(before=before),self.assertRaises(ValueError):self.validate(tree)
        for tag,before,after in (("slha","2.441404e+00","2.5e+00"),("MG5ProcCard","QED=2","QED=3"),("MGRunCard","216.188","125")):
            tree=lhe_fixture();element=tree.find("header/"+tag)
            # Card capitalization is inspected, never guessed for this failure.
            if before.lower() in element.text.lower():
                element.text=re.sub(re.escape(before),after,element.text,flags=re.I)
            else:element.text += "\nDECAY 23 2.5\n"
            with self.subTest(tag=tag),self.assertRaises(ValueError):self.validate(tree)

    def test_wrong_initial_gluon_and_source_version_rejected(self):
        tree=lhe_fixture();tree.find("event").text=tree.find("event").text.replace("2 -1", "21 -1",1)
        with self.assertRaises(ValueError):self.validate(tree)
        tree=lhe_fixture();tree.find("header/MGVersion").text="3.5.15"
        with self.assertRaises(ValueError):self.validate(tree)

    def test_undeclared_fixture_and_forced_lhe_only_acceptance_rejected(self):
        tree=lhe_fixture();tree.find("header/ZHFixtureScope").text="PHYSICAL"
        with self.assertRaises(ValueError):self.validate(tree)
        with self.assertRaises(ValueError):self.validate(lhe_fixture(),"ZH_BBGG_FORCED_DECAYS")

    def test_no_physical_acceptance_even_with_forged_pass_receipt(self):
        with self.assertRaises(ValueError):
            v.validate_lhe(Path("nonexistent.lhe"),"ZH_ZBB_STABLE_H",100,CONTRACT,receipt={"status":"PASS"})

    def test_cli_physically_executed_on_temporary_method_fixture(self):
        with tempfile.TemporaryDirectory(prefix="zh_synthetic_method_",dir=REPO) as directory:
            path=Path(directory)/"METHOD_ONLY.lhe";path.write_bytes(ET.tostring(lhe_fixture()))
            run=subprocess.run([sys.executable,"-B",str(SCRIPT),"--profile","ZH_ZBB_STABLE_H","--events","1","--lhe",str(path),"--method-only"],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)["status"],"METHOD_ONLY")
            blocked=subprocess.run([sys.executable,"-B",str(SCRIPT),"--profile","ZH_ZBB_STABLE_H","--lhe",str(path)],capture_output=True,text=True,timeout=30)
            self.assertNotEqual(blocked.returncode,0)
            self.assertIn("NOT_AUTHORIZED",blocked.stderr)

    def test_bounded_xml_entities_and_truncation_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="zh_synthetic_method_",dir=REPO) as directory:
            path=Path(directory)/"INVALID_ONLY.lhe"
            for data in (b'<!DOCTYPE x [<!ENTITY y "bad">]><LesHouchesEvents/>',ET.tostring(lhe_fixture())[:-10]):
                path.write_bytes(data)
                with self.assertRaises(ValueError):v.validate_lhe(path,"ZH_ZBB_STABLE_H",1,CONTRACT,method_only=True)


class DecayGraphWeightMethods(unittest.TestCase):
    def test_two_independent_decay_ids_and_preferred_source_ZBR_once(self):
        result=v.validate_future_record(graph_fixture(),"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)
        self.assertEqual(result["status"],"METHOD_ONLY")
        self.assertFalse(result["physical_acceptance"])
        self.assertEqual(Decimal(result["weight_check"]["external_BR_factor"]),Decimal(".002"))

    def test_wrong_photon_or_bottom_parent_rejected(self):
        for index,new_mother in ((6,3),(4,4)):
            r=graph_fixture();p=r["particles"][index];old=p["mothers"][0]
            r["particles"][old-1]["daughters"].remove(p["id"]);p["mothers"]=[new_mother]
            r["particles"][new_mother-1]["daughters"].append(p["id"])
            with self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)

    def test_cycle_missing_nonreciprocal_duplicate_and_ambiguous_lineage(self):
        mutations=[lambda r:r["particles"][6].update(mothers=[999]),
                   lambda r:r["particles"][3].update(daughters=[8]),
                   lambda r:r["particles"][3].update(mothers=[1,2,7]),
                   lambda r:r["particles"][3].update(daughters=[7,7,8]),
                   lambda r:r["particles"].append(node(9,25,2,[],[],125,(0,0,0,125)))]
        for mutate in mutations:
            r=graph_fixture();mutate(r)
            with self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)

    def test_photon_conversion_loss_retains_source_denominator(self):
        r=graph_fixture();r["higgs_final_photon_ids"]=[]
        result=v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)
        self.assertEqual(result["weight_check"]["source_total_events"],100)
        self.assertEqual(result["ancestry"]["higgs_photon_birth_ids"],[7,8])

    def test_hadron_decay_photon_is_not_a_direct_H_photon_copy(self):
        r=graph_fixture();r["particles"][6].update(status=2,daughters=[9]);r["particles"].append(node(9,511,2,[7],[10]))
        r["particles"].append(node(10,22,1,[9],[],0,(1,0,0,1)));r["higgs_final_photon_ids"]=[10]
        with self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)

    def test_final_photon_copy_must_reach_exact_declared_birth_once(self):
        # A genuine method copy chain preserves the declared birth identity.
        r=graph_fixture();r["particles"][6].update(status=2,daughters=[9])
        r["particles"].append(node(9,22,1,[7],[],0,(62.5,0,0,62.5)))
        r["higgs_final_photon_ids"]=[9,8]
        checked=v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)
        self.assertEqual(checked["ancestry"]["selected_final_photon_birth_ids"],{9:7,8:8})
        # One original H has two copy branches. The declarations refer to
        # copy9, whereas selected final photons come from copy10.
        wrong=graph_fixture();wrong["particles"][3]["daughters"]=[9,10]
        wrong["particles"][6].update(mothers=[9]);wrong["particles"][7].update(mothers=[9])
        wrong["particles"] += [node(9,25,2,[4],[7,8],125,(0,0,0,125)),
                               node(10,25,2,[4],[11,12],125,(0,0,0,125)),
                               node(11,22,1,[10],[],0,(62.5,0,0,62.5)),
                               node(12,22,1,[10],[],0,(-62.5,0,0,62.5))]
        wrong["higgs_final_photon_ids"]=[11,12]
        with self.assertRaisesRegex(ValueError,"declared H-decay birth"):
            v.validate_future_record(wrong,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)
        # A branching synthetic gamma-copy graph cannot count one birth twice.
        r["particles"][6]["daughters"].append(10)
        r["particles"].append(node(10,22,1,[7],[],0,(62.5,0,0,62.5)))
        r["higgs_final_photon_ids"]=[9,10]
        with self.assertRaisesRegex(ValueError,"same declared H-decay birth"):
            v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)

    def test_repeated_missing_or_unknown_BR_rejected(self):
        for mutate in (lambda r:r["br_ledger"].update(missing_external_decay_ids=["Z_to_b_bbar","H_to_gamma_gamma"]),
                       lambda r:r["br_ledger"].update(missing_external_decay_ids=[]),
                       lambda r:r["br_ledger"]["branching_ratios"].update(H_to_gamma_gamma="UNKNOWN"),
                       lambda r:r.update(physical_BR_factor=".0004",exclusive_contribution_pb=".000004")):
            r=graph_fixture();mutate(r)
            with self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)

    def test_measured_embedded_HBR_is_not_applied_a_second_time(self):
        r=graph_fixture();r["br_ledger"].update(nominal_decay_ids_in_pythia_weight=["H_to_gamma_gamma"],missing_external_decay_ids=[])
        r.update(Pythia_Info_weight_pb=".002",converter_weight_0_pb=".002",physical_BR_factor="1")
        r["weight_values"]=[".01","1",".002",".002"]
        self.assertEqual(v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)["weight_check"]["external_BR_factor"],"1")
        r["physical_BR_factor"]=".002"
        with self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)

    def test_signed_nominal_weight_preserved_without_positive_only_assumption(self):
        r=graph_fixture();r.update(LHE_XWGTUP_pb="-1",Pythia_Info_weight_pb="-1",converter_weight_0_pb="-1",input_contribution_pb="-.01",exclusive_contribution_pb="-.00002")
        r["weight_values"]=["-.01","-1","-1","-1"]
        self.assertEqual(Decimal(v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)["weight_check"]["exclusive_contribution_pb"]),Decimal("-.00002"))

    def test_wrong_denominator_units_nonfinite_and_columns_rejected(self):
        for key,value in (("source_total_events",99),("cross_section_unit","MB"),("Pythia_Info_weight_pb","NaN"),
                          ("converter_weight_0_pb","2"),("pythia_sigmaGen_mb","1"),("source_event_sha256","UNKNOWN")):
            r=graph_fixture();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)
        for mutate in (lambda r:r["weight_names"].__setitem__(3,"converter_nominal_pb"),lambda r:r["weight_values"].__setitem__(3,"2")):
            r=graph_fixture();mutate(r)
            with self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)

    def test_resonance_mass_width_and_synthetic_scope_required(self):
        for mutate in (lambda r:r["source_model_parameters"].update(WH_gev="UNKNOWN"),lambda r:r["particles"][3].update(mass_gev=124),
                       lambda r:r.update(fixture_scope="PHYSICAL")):
            r=graph_fixture();mutate(r)
            with self.assertRaises(ValueError):v.validate_future_record(r,"ZH_BBGG_FORCED_DECAYS",CONTRACT,method_only=True)
        with self.assertRaises(ValueError):v.validate_future_record(graph_fixture(),"ZH_BBGG_FORCED_DECAYS",CONTRACT)

    def test_Cauchy_covariance_and_independent_delta_method_derivatives(self):
        result=v.br_factor_and_variance([".2",".002"],[".02",".0001"],".000001")
        self.assertEqual(Decimal(result["factor"]),Decimal(".0004"))
        self.assertEqual(Decimal(result["first_order_variance"]),Decimal(".0000000028"))
        for covariance in (".000003","-.000003"):
            with self.assertRaises(ValueError):v.br_factor_and_variance([".2",".002"],[".02",".0001"],covariance)
        self.assertGreaterEqual(Decimal(v.br_factor_and_variance([".2",".002"],[".02",".0001"],"-.000002")["first_order_variance"]),0)


class ProposedNativeInputMethods(unittest.TestCase):
    def test_native_mass_method_no_tag_redraw_null_without_two_tags(self):
        row={"fixture_scope":"METHOD_ONLY","photons":[{"index":0,"pt":62.5,"eta":0,"phi":0,"mass":0},
             {"index":1,"pt":62.5,"eta":0,"phi":math.pi,"mass":0}],
             "jets":[{"index":0,"pt":50,"eta":0,"phi":.5,"mass":5,"btag":1,"flavor":5},
                     {"index":1,"pt":45,"eta":0,"phi":-.5,"mass":5,"btag":0,"flavor":5}]}
        result=v.future_reco_masses(row,method_only=True)
        self.assertAlmostEqual(result["m_gamma_gamma"],125)
        self.assertIsNone(result["m_bb"])
        self.assertIsNone(result["m_bb_gamma_gamma"])
        self.assertEqual(row["jets"][1]["btag"],0)
        row["jets"][1]["btag"]=1
        result=v.future_reco_masses(row,method_only=True)
        self.assertGreater(result["m_bb_gamma_gamma"],result["m_bb"]+125)
        self.assertEqual(result["status"],"METHOD_ONLY")

    def test_profile_config_no_physical_or_continuum_scope_mutation(self):
        config=v.load_json(v.CONFIG)
        self.assertEqual(v.validate_profile_config(config)["physical_validation"],"NOT_EXECUTED")
        config["physical_execution_authorized"]=True
        with self.assertRaises(ValueError):v.validate_profile_config(config)
        config=v.load_json(v.CONFIG);config["profiles"]["ZH_ZBB_STABLE_H"]["stable_lhe_pdgs"]=[5,-5,22,22]
        with self.assertRaises(ValueError):v.validate_profile_config(config)
        config=v.load_json(v.CONFIG);config["lhe_numeric_tolerances"]["closure_rtol"]="UNKNOWN"
        with self.assertRaises(ValueError):v.validate_profile_config(config)

    def test_historical_validator_bytes_unchanged(self):
        paths=["simulation/mg5/scripts/validate_lhe.py","simulation/pythia8/scripts/validate_lhe_stream.py",
               "simulation/pythia8/scripts/validate_hepmc3.py","simulation/delphes/src/analyze_delphes.cxx"]
        for path in paths:
            expected=subprocess.check_output(["git","-C",str(REPO),"show","be29be7255c5009c719190cb96f43f04bb144d8f:"+path],timeout=30)
            actual=(REPO/path).read_bytes()
            self.assertEqual(hashlib.sha256(actual).hexdigest(),hashlib.sha256(expected).hexdigest())


if __name__=="__main__":unittest.main()

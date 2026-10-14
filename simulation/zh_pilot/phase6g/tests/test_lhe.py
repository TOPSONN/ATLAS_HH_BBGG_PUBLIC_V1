"""Analytic METHOD_ONLY parser/algebra controls, never physics references.

The100 repeated threshold coordinates exercise file-count and signed-weight
algebra only. They are not independent simulated events or native acceptance.
All XML/gzip/JSON fixtures live in temporary directories and are removed.
"""
import copy
from decimal import Decimal
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO=Path(__file__).resolve().parents[4]
SCRIPT=REPO/"simulation/zh_pilot/phase6g/validate_lhe.py"
spec=importlib.util.spec_from_file_location("phase6g_lhe_validator",SCRIPT)
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def fixture(*,weights=None,expanded=True):
    cards=v.prepared_contract()
    root=ET.Element("LesHouchesEvents",version="3.0");header=ET.SubElement(root,"header")
    ET.SubElement(header,"MGVersion").text="3.5.16"
    ET.SubElement(header,"ZHFixtureScope").text="METHOD_ONLY"
    process=cards["process_card"]
    if expanded:process="set nb_core 1\nset run_mode 0\nset complex_mass_scheme False\nset gauge unitary\ndefine p = g u c d s u~ c~ d~ s~\n"+process+"output process -nojpeg\n"
    for key,tag in v.TAGS.items():ET.SubElement(header,tag).text=process if key=="process_card" else cards[key]
    ET.SubElement(header,"MGProcCard").text="# SYNTHETIC_METHOD_ONLY legacy interface placeholder\n"
    ET.SubElement(header,"MGGenerationInfo").text="# Number of Events : 100\n# Integrated weight (pb) : 1.00000000\n"
    init=ET.SubElement(root,"init")
    init.text="\n2212 2212 6500 6500 0 0 10042 10042 -4 1\n1.000000e+00 0.000000e+00 3.000000e+00 1\n"
    ET.SubElement(init,"generator",name="MadGraph5_aMC@NLO",version="3.5.16")
    rows=["2 -1 0 0 501 0 0 0 108.094 108.094 0 0 9", "-2 -1 0 0 0 501 0 0 -108.094 108.094 0 0 9",
          "23 2 1 2 0 0 0 0 0 91.188 91.188 0 9", "25 1 1 2 0 0 0 0 0 125 125 0 9",
          "5 1 3 3 502 0 0 0 45.594 45.594 0 0 9", "-5 1 3 3 0 502 0 0 -45.594 45.594 0 0 9"]
    aqed=format(float(Decimal(1)/Decimal("132.507")),".10e")
    for weight in weights or ["1"]*100:
        ET.SubElement(root,"event").text=f"\n6 1 {weight} 216.188 {aqed} .113\n"+"\n".join(rows)+"\n"
    return root


class LHERecords(unittest.TestCase):
    def check(self,root,*,gzip_file=False,method_only=True,**kwargs):
        with tempfile.TemporaryDirectory(prefix="phase6g_method_",dir=REPO/".local") as directory:
            path=Path(directory)/("METHOD_ONLY.lhe.gz" if gzip_file else "METHOD_ONLY.lhe")
            raw=ET.tostring(root)
            if gzip_file:
                with gzip.open(path,"wb") as stream:stream.write(raw)
            else:path.write_bytes(raw)
            return v.validate_file(path,method_only=method_only,**kwargs)

    def test_complete100_methods_plain_gzip_and_expanded_banner(self):
        for gz,expanded in ((False,False),(False,True),(True,True)):
            report=self.check(fixture(expanded=expanded),gzip_file=gz)
            self.assertEqual(report["status"],"METHOD_ONLY");self.assertFalse(report["physical_acceptance"])
            self.assertEqual(report["actual_events"],100);self.assertEqual(report["events_valid"],100)
            self.assertEqual(report["events_invalid"],0);self.assertEqual(report["events_not_assessed"],0)
            self.assertEqual(report["weights"]["full_original_source_denominator"],100)
            self.assertEqual(report["source_included_decay_ids"],["Z_to_b_bbar"])
            self.assertEqual(report["exclusive_physical_normalization"],"BLOCKED_BR_WEIGHT_CLOSURE")
            self.assertEqual(report["source_events"][0]["original_resonance_and_bottom_ids"],{"Z":3,"H":4,"b":5,"bbar":6})

    def test_signed_weights_source_mean_and_moments(self):
        report=self.check(fixture(weights=["3","-1"]*50))
        self.assertEqual(report["weights"]["negative_count"],50)
        self.assertEqual(Decimal(report["weights"]["mean_pb"]),1)
        self.assertEqual(Decimal(report["weights"]["sum_squared_pb2"]),500)
        self.assertEqual(report["actual_events"],100)

    def test_zero_weights_preserved(self):
        report=self.check(fixture(weights=["2","0"]*50))
        self.assertEqual(report["weights"]["zero_count"],50)
        self.assertEqual(Decimal(report["weights"]["mean_pb"]),1)

    def test_invalid_events_all_assessed_with_exact_indices(self):
        tree=fixture();events=tree.findall("event")
        events[2].text=events[2].text.replace("5 1 3 3","5 1 1 2")
        events[98].text=events[98].text.replace("-45.594 45.594","-45.594 45")
        with self.assertRaises(v.ValidationError) as caught:self.check(tree)
        report=caught.exception.report
        self.assertEqual((report["actual_events"],report["events_assessed"],report["events_valid"],report["events_invalid"],report["events_not_assessed"]),(100,100,98,2,0))
        self.assertEqual([x["source_event_index"] for x in report["event_failures"]],[3,99])
        self.assertEqual(report["status"],"FAILED_METHOD_ONLY")

    def test99_and101_input_records_cannot_change_denominator(self):
        for count in (99,101):
            with self.subTest(count=count),self.assertRaises(v.ValidationError) as caught:self.check(fixture(weights=["1"]*count))
            self.assertEqual(caught.exception.report["actual_events"],count)

    def test_no_event_and_no_generation_banner_rejected(self):
        tree=fixture()
        for event in tree.findall("event"):tree.remove(event)
        with self.assertRaises(v.ValidationError):self.check(tree)
        tree=fixture();header=tree.find("header");header.remove(header.find("MGGenerationInfo"))
        with self.assertRaises(v.ValidationError):self.check(tree)

    def test_duplicate_and_out_of_order_sections_rejected(self):
        for name in ("header","init"):
            tree=fixture();tree.append(copy.deepcopy(tree.find(name)))
            with self.subTest(name=name),self.assertRaises(v.ValidationError):self.check(tree)
        tree=fixture();tree[0],tree[1]=tree[1],tree[0]
        with self.assertRaises(v.ValidationError):self.check(tree)

    def test_banner_cards_profile_flavour_and_coupling_mutations(self):
        for old,new in (("QED=2","QED=3"),("complex_mass_scheme False","complex_mass_scheme True"),
                        (v.CARDS.PROTON,"define p = g u c d s u~ c~ d~ s~"),("nb_core 1","nb_core 2")):
            tree=fixture();card=tree.find("header/MG5ProcCard");self.assertIn(old,card.text);card.text=card.text.replace(old,new)
            with self.subTest(old=old),self.assertRaises(v.ValidationError):self.check(tree)

    def test_actual_full_run_and_param_cannot_override_frozen_physics(self):
        for tag,old,new in (("MGRunCard","216.188","125"),("MGRunCard","20261104","20261105"),
                            ("slha","2.441404e+00","2.5e+00")):
            tree=fixture();card=tree.find("header/"+tag)
            import re
            self.assertIn(old.lower(),card.text.lower());card.text=re.sub(re.escape(old),new,card.text,flags=re.I)
            with self.subTest(tag=tag),self.assertRaises(v.ValidationError):self.check(tree)

    def test_init_beams_pdf_strategy_subprocess_cross_section_rejected(self):
        for old,new in (("6500 6500","7000 6500"),("10042 10042","10043 10042"),("-4 1","4 1"),
                        ("1.000000e+00","2.000000e+00"),("0.000000e+00","NaN")):
            tree=fixture();init=tree.find("init");self.assertIn(old,init.text);init.text=init.text.replace(old,new,1)
            with self.subTest(old=old),self.assertRaises(v.ValidationError):self.check(tree)

    def test_color_mass_ancestry_gg_initial_and_alphaEW_rejected(self):
        for old,new in (("-2 -1","21 -1"),("0 502 0 0 -45.594","0 503 0 0 -45.594"),
                        ("5 1 3 3","5 1 1 2"),("125 125","125 124"),("7.5463833104e-03",".008")):
            tree=fixture();event=tree.find("event")
            if old.startswith("7."):old=event.text.splitlines()[1].split()[4]
            self.assertIn(old,event.text);event.text=event.text.replace(old,new,1)
            with self.subTest(old=old),self.assertRaises(v.ValidationError):self.check(tree)

    def test_auxiliary_weights_finite_and_unique(self):
        for values in (("1","NaN"),("1","2")):
            tree=fixture();rwgt=ET.SubElement(tree.find("event"),"rwgt")
            for value in values:ET.SubElement(rwgt,"wgt",id="same").text=value
            with self.subTest(values=values),self.assertRaises(v.ValidationError):self.check(tree)

    def test_original_event_bytes_and_hashes_not_reserialized(self):
        with tempfile.TemporaryDirectory(dir=REPO/".local") as directory:
            path=Path(directory)/"METHOD_ONLY.lhe";raw=ET.tostring(fixture());path.write_bytes(raw)
            report=v.validate_file(path,method_only=True);events=list(v.iter_lhe_events(path))
            self.assertEqual(len(events),100)
            self.assertEqual(hashlib.sha256(b"".join(e["raw"] for e in events)).hexdigest(),report["event_content_sha256"])
            self.assertEqual(events[0]["source_event_content_hash"],report["source_events"][0]["source_event_content_hash"])
            self.assertEqual(path.read_bytes(),raw)

    def test_gzip_crc_truncation_and_xml_entities_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO/".local") as directory:
            path=Path(directory)/"METHOD_ONLY.lhe.gz";raw=gzip.compress(ET.tostring(fixture()))
            for changed in (raw[:-7],raw[:-8]+bytes([raw[-8]^1])+raw[-7:]):
                path.write_bytes(changed)
                with self.assertRaises(v.ValidationError):v.validate_file(path,method_only=True)
            plain=Path(directory)/"METHOD_ONLY.lhe";plain.write_bytes(b'<!DOCTYPE x [<!ENTITY e "bad">]><LesHouchesEvents/>')
            with self.assertRaises(v.ValidationError):v.validate_file(plain,method_only=True)

    def test_bounded_decompression_rejects(self):
        from unittest.mock import patch
        with patch.object(v,"MAX_BYTES",32768),self.assertRaisesRegex(v.ValidationError,"Decompressed LHE"):
            self.check(fixture(),gzip_file=True)

    def test_xml_depth_and_element_count_are_bounded(self):
        for raw in (b"<a>"*33+b"</a>"*33,b"<a>"+b"<b/>"*10001+b"</a>"):
            with self.assertRaisesRegex(ValueError,"node/depth"):v.parse_xml(raw)

    def test_synthetic_physical_or_forged_flag_cannot_receive_pass(self):
        with self.assertRaises(v.ValidationError):self.check(fixture(),method_only=False,card_contract=v.prepared_contract(),provenance={"status":"PASS"})
        tree=fixture();tree.find("header").remove(tree.find("header/ZHFixtureScope"))
        with self.assertRaises(v.ValidationError):self.check(tree,method_only=False,card_contract=v.prepared_contract(),provenance={"status":"PASS"})
        with self.assertRaises(v.ValidationError):self.check(fixture(),method_only="false")

    def test_physical_cli_rejects_without_provenance_method_cli_executes(self):
        with tempfile.TemporaryDirectory(dir=REPO/".local") as directory:
            path=Path(directory)/"METHOD_ONLY.lhe";path.write_bytes(ET.tostring(fixture()))
            result=subprocess.run([sys.executable,"-B",str(SCRIPT),"--file",str(path),"--method-only"],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)["status"],"METHOD_ONLY")
            blocked=subprocess.run([sys.executable,"-B",str(SCRIPT),"--file",str(path)],capture_output=True,text=True,timeout=30)
            self.assertEqual(blocked.returncode,2);self.assertFalse(json.loads(blocked.stdout)["physical_acceptance"])


class IndependentLogAndBinding(unittest.TestCase):
    def test_actual_summary_display_rounding_quantum_and_ansi(self):
        text="\x1b[32m=== Results Summary for run: zh100 tag: phase6f_zh_pilot ===\x1b[0m\nCross-section : .001 +- 1.234e-5 pb\nNb of events : 100\n"
        summary=v.parse_run_log(text)
        self.assertEqual(summary["events"],100);self.assertEqual(summary["precision"],"MG5_4_SIGNIFICANT_DIGIT_DISPLAY_ONLY")
        self.assertEqual(v.half_print_unit(".001",significant_digits=4),Decimal(".0000005"))
        self.assertEqual(v.half_print_unit("1.234e-5",significant_digits=4),Decimal("5e-9"))
        self.assertEqual(v.half_print_unit("0",significant_digits=4),Decimal(0))
        for bad in (text+text,text.replace("zh100","other"),text.replace("100\n","99\n"),text.replace("1.234e-5","NaN")):
            with self.assertRaises(ValueError):v.parse_run_log(bad)

    def test_missing_artifact_and_unsafe_receipt_fail(self):
        with self.assertRaises(ValueError):v.bound_artifact({"path":"missing","sha256":"f"*64})
        with self.assertRaises(ValueError):v.bound_artifact({"path":"missing","sha256":True})

    def test_downstream_raw_weights_info_change_and_prefix_not_additional_source(self):
        checker=LHERecords();source=checker.check(fixture());rows=[]
        for event in source["source_events"][:10]:
            rows.append({"fixture_scope":"METHOD_ONLY","source_event_index":event["source_event_index"],"source_file_sha256":source["source_file_sha256"],
                "source_event_sha256":event["source_event_content_hash"],"source_total_events":100,
                "weight_names":["input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb","converter_weight_0_pb"],
                "weight_values":[".01","1",".0022965313147512443",".0022965313147512443"]})
        report=v.validate_downstream_binding(source,rows,expected_output_count=10,method_only=True)
        self.assertEqual(report["independent_additional_hard_events"],0)
        self.assertEqual(report["exclusive_physical_normalization"],"BLOCKED_BR_WEIGHT_CLOSURE")
        self.assertEqual(report["actual_ReaderAscii_physics_validation"],"SEPARATELY_REQUIRED_NOT_IMPLIED")
        for key,value in (("source_total_events",10),("source_event_index",11),("source_event_sha256","f"*64)):
            changed=copy.deepcopy(rows);changed[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.validate_downstream_binding(source,changed,expected_output_count=10,method_only=True)
        changed=copy.deepcopy(rows);changed[0]["weight_values"][3]="1"
        with self.assertRaises(ValueError):v.validate_downstream_binding(source,changed,expected_output_count=10,method_only=True)

    def test_frozen_historical_validator_bytes(self):
        for path in ("simulation/zh_pilot/scripts/validate_profiles.py","simulation/mg5/scripts/validate_lhe.py",
                     "simulation/pythia8/scripts/validate_hepmc3.py","simulation/delphes/src/analyze_delphes.cxx"):
            saved=subprocess.check_output(["git","-C",str(REPO),"show","05cff9a5d991ba6782b339bc41932ae4da296d8c:"+path],timeout=30)
            self.assertEqual(hashlib.sha256(saved).hexdigest(),v.file_sha(REPO/path))


if __name__=="__main__":unittest.main()

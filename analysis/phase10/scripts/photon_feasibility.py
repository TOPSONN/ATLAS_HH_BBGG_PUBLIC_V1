#!/usr/bin/env python3
"""Actual existing photon observability joined to Phase9; synthetic tests separate."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE = Path(__file__).resolve().parents[1] / "source"
sys.path.insert(0, str(SOURCE))
from sideband import synthetic_suite

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024), b""):h.update(block)
    return h.hexdigest()

def json_read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def exclusive(path, value):
    with Path(path).open("x",encoding="utf-8") as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write("\n")

def load_join(native_path, origins_path):
    native={}
    with Path(native_path).open(encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line)
            key=(row["dataset_id"],row["source_event_ordinal"],row["source_event_sha256"],row["hepmc_event_sha256"])
            if key in native:raise ValueError("duplicate source event key")
            native[key]=row
    pairs=[]
    seen=set()
    with Path(origins_path).open(encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line)
            key=(row["dataset_id"],row["source_event_index"],row["source_event_sha256"],row["hepmc_event_sha256"])
            if key in seen or key not in native:raise ValueError("unmatched/duplicate photon origin event")
            seen.add(key)
            if row["stages"] != native[key]["stages"]:raise ValueError("historical stage identity mismatch")
            pairs.append((native[key],row))
    if seen!=set(native):raise ValueError("incomplete source-event join")
    counts=Counter(k[0] for k in seen)
    if counts!={k:1000 for k in ("B01","B02","B03","B04","B05","B06")}:
        raise ValueError("full frozen 6000 backgrounds required")
    for dataset in counts:
        ordinals={k[1] for k in seen if k[0]==dataset}
        if ordinals!=set(range(1,1001)):raise ValueError("invalid frozen source ordinals")
    return pairs

def module_block(text, kind, name):
    # Cards have nested Tcl formula braces; bounded section ends at the next
    # module declaration rather than treating the first brace as the section end.
    match=re.search(r"(?m)^module\s+"+re.escape(kind)+r"\s+"+re.escape(name)+r"\s*\{", text)
    if not match:raise ValueError("required historical detector module missing")
    next_module=re.search(r"(?m)^module\s+",text[match.end():])
    return text[match.start():match.end()+next_module.start()] if next_module else text[match.start():]

def card_audit(manifest, home):
    rows=[]
    for d in manifest["datasets"]:
        if not d["dataset_id"].startswith("B"):continue
        path=Path(d["card_path"].replace("LOCAL_HOME",str(home)))
        if sha(path)!=d["card_sha256"]:raise ValueError("detector card identity mismatch")
        text=path.read_text()
        phot=module_block(text,"Isolation","PhotonIsolation")
        ele=module_block(text,"Isolation","ElectronIsolation")
        tree=module_block(text,"TreeWriter","TreeWriter")
        unique=module_block(text,"UniqueObjectFinder","UniqueObjectFinder")
        def settings(block):
            return {k:float(re.search(r"(?m)^\s*set\s+"+k+r"\s+([\d.]+)",block)[1])
                for k in ("DeltaRMax","PTMin","PTRatioMax")}
        expected={"DeltaRMax":.5,"PTMin":.5,"PTRatioMax":.12}
        if settings(phot)!=expected or settings(ele)!=expected:raise ValueError("historical isolation changed")
        if "PhotonIsolation/photons" not in unique:raise ValueError("photon prefilter unavailable")
        if "add Branch UniqueObjectFinder/photons Photon Photon" not in tree:raise ValueError("photon output changed")
        rows.append({"dataset_id":d["dataset_id"],"logical_path":d["card_path"],"sha256":d["card_sha256"],
            "photon_isolation_module":settings(phot),"electron_isolation_module":settings(ele),
            "persisted_photons":"UniqueObjectFinder/photons after PhotonIsolation",
            "preisolation_photon_candidate_branch_written":False,
            "tight_antitight_definition":None,"ATLAS_conversion_definition":None,
            "note":"Historical Delphes study isolation; not an ATLAS ID/isolation calibration"})
    return rows

def observability(repo, phase9, native_profile, home):
    profile=json_read(native_profile)
    if profile.get("evidence_class")!="ACTUAL_EXISTING_DATA_READBACK" or profile.get("actual_existing_background_events")!=6000:
        raise ValueError("missing actual native scalar profiling")
    manifest_path=repo/"analysis/phase8/config/datasets.json"
    manifest=json_read(manifest_path)
    expected={d["dataset_id"]:d for d in manifest["datasets"] if d["dataset_id"].startswith("B")}
    if {d["dataset_id"] for d in profile["datasets"]}!=set(expected):raise ValueError("native profile datasets changed")
    for d in profile["datasets"]:
        ref=expected[d["dataset_id"]]
        if d["root_sha256"]!=ref["root_sha256"] or d["card_sha256"]!=ref["card_sha256"] or d["events_read"]!=1000:
            raise ValueError("native profile source identity mismatch")
        if not d.get("source_hashes_unchanged_after_loop"):raise ValueError("source preservation unproven")
        for b in d["branches"].values():
            if not b["present"]:continue
            for f in b["numeric_members"]:
                if any(p["nonfinite"]!=0 for p in f["profiles"]):raise ValueError("nonfinite native observables")
    native=phase9/"native/phase9_native_events.jsonl"
    origins=phase9/"origins_03/phase9_origins_event_details.jsonl"
    pairs=load_join(native,origins)
    totals=Counter();by_dataset={}
    for n,o in pairs:
        dataset=n["dataset_id"];entry=by_dataset.setdefault(dataset,{"events":0,"cutflow":[0]*5,
            "selected_photon_origins":Counter(),"native_electrons":0,"native_photons":0,"unclassified_reason_counts":Counter()})
        entry["events"]+=1
        entry["cutflow"]=[a+int(b) for a,b in zip(entry["cutflow"],n["stages"])]
        entry["native_electrons"]+=len(n["electrons"]);entry["native_photons"]+=len(n["photons"])
        counts=o["photon_origin"]["selected_reco_photon_counts"]
        if sum(counts.values())!=n["selected_photon_multiplicity"]:raise ValueError("photon denominator mismatch")
        entry["selected_photon_origins"].update(counts);totals.update(counts)
        for p in o["photon_origin"]["reco_photons"]:
            if p["selected"] and p["origin"]=="UNCLASSIFIED":entry["unclassified_reason_counts"][p["reason"]]+=1
    if dict(totals)!={"ELECTRON_ASSOCIATED":3,"HADRON_DECAY":0,"PROMPT_HARD_PROCESS":6298,"SHOWER_RADIATION":24,"UNCLASSIFIED":674}:
        raise ValueError("frozen selected photon counts changed")
    for dataset,row in by_dataset.items():
        if row["cutflow"]!=expected[dataset]["expected_cutflow"]:raise ValueError("frozen historical cutflow changed")
    b06=by_dataset["B06"]
    if b06["cutflow"]!=[1000,2,2,2,0]:raise ValueError("B06 support changed")
    matrix=[
        {"observable":"tight / anti-tight ID","status":"ABSENT_VALIDATED_DEFINITION",
         "evidence":"Photon numeric-member inventory lacks shower-shape and tight-ID decisions; Status is simulation classification, not detector ID"},
        {"observable":"isolated / nonisolated photon controls","status":"CENSORED_NONISOLATED_DENOMINATOR",
         "evidence":"IsolationVar and sums are present, but TreeWriter saves photons after PhotonIsolation; upstream failing photon candidates are not a saved Photon branch"},
        {"observable":"conversion categories","status":"ABSENT",
         "evidence":"No ATLAS converted/unconverted ID/vertex category in Photon numeric fields"},
        {"observable":"electron control candidates","status":"PRESENT_UNCALIBRATED",
         "evidence":"Electron kinematics/charge/isolation/impact parameters exist after isolation and efficiency; no matching ATLAS tight-electron denominator or Z control calibration"},
        {"observable":"prompt leakage","status":"TRUTH_DIAGNOSTIC_ONLY",
         "evidence":"Phase9 selected origins retained; ancestry association is not measured control-region prompt subtraction"},
        {"observable":"background subtraction","status":"ABSENT_COMPATIBLE_CONTROL_DATA",
         "evidence":"No matched data controls, prompt leakage covariance, or subtraction source"},
        {"observable":"jet flavour composition","status":"PRESENT_DESCRIPTIVE",
         "evidence":"Jet Flavor/FlavorAlgo/FlavorPhys/BTag profile and Phase9 ancestry categories; no validated fake-control flavour transport"}
    ]
    catalog_path=repo/"analysis/phase10/config/photon_public_calibration.json"
    catalog=json_read(catalog_path)
    return {"schema_version":1,"evidence_class":"ACTUAL_EXISTING_DATA_READBACK",
        "status":"BLOCKED_MISSING_COMPATIBLE_OBSERVABLES","physical_fake_rate":"UNKNOWN",
        "actual_existing_events_joined":len(pairs),"native_scalar_profile":profile,
        "phase9_selected_photon_origin_objects":dict(totals),"unclassified_is_fake":False,
        "by_dataset":by_dataset,"B06_interpretation":"1000 source events, 2 two-photon events, 0 final; not a fake-rate denominator",
        "observability_matrix":matrix,"historical_detector_cards":card_audit(manifest,home),
        "public_calibration_audit":catalog,"compatible_public_calibration_imported":False,
        "calibrated_jet_to_photon_probability":None,
        "calibrated_electron_to_photon_transfer_factor":None,
        "synthetic_result_used_in_physical_output":False,
        "input_hashes":{"phase8_dataset_manifest":sha(manifest_path),"phase9_native_events":sha(native),
            "phase9_origin_details":sha(origins),"native_scalar_profile":sha(native_profile),"public_catalog":sha(catalog_path)},
        "new_ME_calls":0,"new_integrals":0,"new_hard_events":0,"new_Pythia_events":0,"new_Delphes_events":0}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True);parser.add_argument("--phase9",type=Path,required=True)
    parser.add_argument("--native-observability",type=Path,required=True);parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--home",type=Path,default=Path("/home/btu"))
    args=parser.parse_args()
    actual=observability(args.repo,args.phase9,args.native_observability,args.home)
    synthetic=synthetic_suite()
    if synthetic["status"]!="PASS_SYNTHETIC_METHOD_ONLY":raise ValueError("synthetic method tests failed")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name in ("phase10_photon_observability.json","phase10_synthetic_sideband_tests.json"):
        if (args.output_dir/name).exists():raise ValueError("refuse overwrite: "+name)
    exclusive(args.output_dir/"phase10_photon_observability.json",actual)
    exclusive(args.output_dir/"phase10_synthetic_sideband_tests.json",synthetic)
    print(json.dumps({"status":"PASS_PHASE10_PHOTON_FEASIBILITY_WITH_BLOCKERS","events":actual["actual_existing_events_joined"],
        "physical_fake_rate":"UNKNOWN","actual_transfer":"BLOCKED_MISSING_COMPATIBLE_OBSERVABLES",
        "synthetic":synthetic["status"]}))
if __name__=="__main__":main()

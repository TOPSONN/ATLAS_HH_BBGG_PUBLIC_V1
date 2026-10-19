#!/usr/bin/env python3
"""Bounded provenance/readiness contract; no physical total-background arithmetic."""
import argparse, itertools, json
from pathlib import Path

PROCESSES = {"B01":"pp -> b b~ gamma gamma", "B02":"pp -> c c~ gamma gamma", "B03":"pp -> light-j j gamma gamma", "B04":"ZH, Z -> b b~, H -> gamma gamma", "B05":"ttH, H -> gamma gamma", "B06":"pp -> b b~ gamma j (one Born photon)"}
CONTINUUM = {"B01", "B02", "B03"}

def build_background_contract(manifest):
    datasets = {row["dataset_id"]: row for row in manifest["datasets"]}
    if not set(PROCESSES).issubset(datasets):
        raise ValueError("background dataset missing from source contract")
    pairs = []
    for left, right in itertools.combinations(PROCESSES, 2):
        pair = {left, right}
        if pair <= CONTINUUM:
            status = "POTENTIAL_DOUBLE_COUNTING"
            mechanism = "Exclusive ME flavour labels do not define exclusive shower/reconstructed-heavy-flavour samples; shower g->bb/cc may populate the same selected final-state region."
            evidence = ["metadata/phase6e_source997_manifest.json", "metadata/phase6e_flavour_decomposition.csv", "reports/phase6e_background_overlap.md"]
        elif "B06" in pair:
            status = "NOT_COMPARABLE"
            mechanism = "One-Born-photon source cannot be compared as a calibrated two-photon fake prediction; prompt/shower/fake double-counting control and fake calibration are unavailable."
            evidence = ["metadata/phase6g_run_manifest.json", "reports/phase6g_background_cutflow.md"]
        else:
            status = "OVERLAP_UNKNOWN"
            mechanism = "Resonant and continuum source components are separately identified, but no complete common final-state overlap/interference, matching or calibrated normalization prescription has been validated."
            evidence = ["metadata/phase6g_run_manifest.json", "metadata/phase6g_weight_accounting.json"]
        pairs.append({"dataset_left": left, "dataset_right": right,
                      "process_definitions": [PROCESSES[left], PROCESSES[right]],
                      "ME_flavour_content": ["explicit bb" if v in ("B01", "B06") else "explicit cc" if v=="B02" else "light-parton source" if v=="B03" else "resonant source; decay scope retained" for v in (left,right)],
                      "shower_flavour_content": "Flavour-changing shower/decay content retained; process name is not reconstructed jet flavour.",
                      "possible_overlap_mechanism": mechanism, "existing_ancestry_evidence": evidence,
                      "matching_merging_information": "No validated common ME/PS exclusivity scheme for physical addition",
                      "status": status, "validated_exclusive": False, "safe_for_physical_addition": False,
                      "source_ROOT_sha256": [datasets[left]["root_sha256"], datasets[right]["root_sha256"]]})
    return {"schema_version":1, "evidence_class":"HISTORICAL_EVIDENCE_AUDIT", "status":"BLOCKED_OVERLAP_AND_CALIBRATION",
            "scope":"ATLAS_LIKE_EXPLORATORY_COMPONENTS_ONLY", "pairs":pairs,
            "processes": {key:{"process":value, "raw_source_weight_scope":datasets[key]["source_weight_scope"],
                "BR_scope":datasets[key]["branching_ratio_scope"], "source_ROOT_sha256":datasets[key]["root_sha256"],
                "scientific_limitations":datasets[key]["scientific_limitations"]} for key,value in PROCESSES.items()},
            "combined_physical_background":"BLOCKED", "physical_significance":"NOT_EVALUATED", "physical_CLs_limit":"NOT_EVALUATED",
            "sample_files_or_seed_differences_establish_physics_exclusivity":False,
            "new_generation_events":0}

def fake_photon_readiness():
    return {"schema_version":1, "dataset_id":"B06", "status":"BLOCKED_NO_CALIBRATED_FAKE_PHOTON_MODEL",
            "numerical_fake_rate":None, "zero_selected_events_implies_zero_background":False,
            "missing_inputs":["jet->photon fake probability", "photon identification definition", "fake-enriched control data", "isolation treatment", "pT/eta dependence", "process normalization", "uncertainties and correlations", "prompt/shower/fake double-counting control"],
            "scope":"The actual one-Born-photon source can be studied descriptively; no calibrated two-photon fake yield is defined."}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--manifest",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    outputs={"phase8_background_overlap_matrix.json":build_background_contract(json.loads(a.manifest.read_text())),"phase8_fake_photon_readiness.json":fake_photon_readiness()}
    if any((a.output/name).exists() for name in outputs):raise SystemExit("existing background-contract output overwrite refused")
    a.output.mkdir(parents=True,exist_ok=True)
    for name,value in outputs.items():
        with (a.output/name).open("x") as f:json.dump(value,f,indent=2);f.write("\n")
    print(json.dumps({"status":"BACKGROUND_BLOCKERS_RECORDED", "pairs":15,"new_generation_events":0}))

if __name__=="__main__":main()

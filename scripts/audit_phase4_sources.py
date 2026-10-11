#!/usr/bin/env python3
"""Join cached official source metadata without downloading event data.

This inventory classifies the *documented generator samples*, not reconstructed
events.  It never infers truth availability, a b-tag working point, or a valid
luminosity normalization from a filename or from the numerical metadata.
"""

import argparse
import collections
import csv
import hashlib
import json
import math
import re
from pathlib import Path


RECORD_URL = "https://opendata.cern.ch/record/93922"
METADATA_URL = (
    "https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2F"
    "physlitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0"
)
TARGET_LOW, TARGET_HIGH = 105.0, 160.0
DEFAULT_SELECTED = {343981, 346214, 423103}
NEW_BUDGET_BYTES = 128 * 1024 * 1024
NUMERIC_FIELDS = (
    "crossSection_pb", "genFiltEff", "kFactor", "nEvents",
    "sumOfWeights", "sumOfWeightsSquared",
)
FIELDS = (
    "dsid", "filename", "size_bytes", "checksum", "release_uri", "physics_short",
    "process", "generator", "e_tag", "crossSection_pb", "genFiltEff", "kFactor",
    "nEvents", "sumOfWeights", "sumOfWeightsSquared", "description", "keywords",
    "job_path", "physics_classification", "documented_phase_space",
    "generated_mass_low_GeV", "generated_mass_high_GeV", "target_mass_overlap",
    "intended_role", "selection_reason", "download_chosen", "download_status",
    "normalization_status", "exact_release_producer_status", "truth_schema_status",
    "record_url", "metadata_url", "record_snapshot_sha256", "metadata_snapshot_sha256",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(row):
    name = row["physics_short"]
    process = row["process"]
    description = row["description"]
    text = " ".join((name, process, description))
    # A literal HH inside a decay label such as tautauHH is not Higgs-pair evidence.
    if re.search(r"\b(?:ggFHH|VBFHH|di[- ]?Higgs|Higgs[- ]boson pair)\b", text, re.I):
        category = "EXPLICIT_HIGGS_PAIR_CANDIDATE"
        role = "HH candidate requiring independent decay/channel verification"
    elif process in {"QCD direct diphoton production", "Diphoton"}:
        category = "PROMPT_DIPHOTON_CONTINUUM"
        role = "prompt diphoton continuum candidate; not a complete background model"
    elif re.search(r"(?:gamgam|Hyy)", name, re.I) and re.search(r"H(?:125|gamgam|yy)|ggH|VBFH|ttH|tHjb|tWH", name):
        category = "SINGLE_HIGGS_DIPHOTON"
        role = "single-H resonance/reconstructed-kinematics check; not HH"
    elif process == "QCD direct photon production":
        category = "GAMMAJETS_FAKE_RELATED_CANDIDATE"
        role = "one generator photon-pT slice; not a calibrated jet-to-photon estimate"
    elif process == "QCD jets":
        category = "DIJET_FAKE_RELATED_CANDIDATE"
        role = "possible fake-related source; photon misidentification not validated"
    elif re.search(r"(?:gamma|photon|yyy)", text, re.I):
        category = "OTHER_PHOTON_BACKGROUND_CANDIDATE"
        role = "other photon-bearing process; selected-channel relevance unverified"
    elif re.search(r"Higgs|H125", text, re.I):
        category = "OTHER_SINGLE_HIGGS_CHANNEL"
        role = "other single-H decay/channel; target-window relevance unverified"
    elif re.search(r"top|ttbar|ttW|ttZ", text, re.I):
        category = "OTHER_TOP_BACKGROUND_CANDIDATE"
        role = "other top process; selected-channel relevance unverified"
    else:
        category = "OTHER_PROCESS_RELEVANCE_UNKNOWN"
        role = "inventory coverage only; no target-channel use established"

    mass = re.search(r"(?:Mass|myy)_(\d+)_(\d+|inf|E_CMS)\b", name, re.I)
    low, high = "", ""
    overlap = "UNKNOWN_NO_GENERATOR_MASS_WINDOW"
    phase_space = "No target-window generator phase space established; see description"
    if mass:
        low = float(mass.group(1))
        high = math.inf if mass.group(2).lower() in {"inf", "e_cms"} else float(mass.group(2))
        overlap = (
            "OVERLAPS_GENERATED_105_160"
            if max(low, TARGET_LOW) < min(high, TARGET_HIGH)
            else "NO_FINITE_GENERATED_105_160_OVERLAP"
        )
        phase_space = f"Generator diphoton mass slice {mass.group(1)} < Mgg < {mass.group(2)} GeV"
        low, high = mass.group(1), mass.group(2)
    elif category == "SINGLE_HIGGS_DIPHOTON":
        overlap = "H125_RESONANCE_NAME_NOT_CONTINUUM_WINDOW"
        phase_space = "Single H125 diphoton decay as identified by published sample name"
    elif category == "GAMMAJETS_FAKE_RELATED_CANDIDATE":
        photon_slice = re.search(r"_DP(\d+)_(\d+|inf)\b", name)
        if photon_slice:
            phase_space = (
                "Photon-filter pT slice " + photon_slice.group(1) + " < pT < "
                + photon_slice.group(2) + " GeV; not a diphoton mass slice; see description"
            )
    return category, role, phase_space, low, high, overlap


def build_manifest(record_path, metadata_path, selected):
    record = json.loads(record_path.read_text(encoding="utf-8"))
    release_files = record["metadata"]["files"]
    if len(release_files) != 373:
        raise ValueError(f"Release index has {len(release_files)} files; expected 373")
    metadata = {}
    with metadata_path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            dsid = int(row["dataset_number"])
            if dsid in metadata:
                raise ValueError(f"Duplicate metadata DSID {dsid}")
            metadata[dsid] = row
    record_hash, metadata_hash = sha256(record_path), sha256(metadata_path)
    rows, seen = [], set()
    for entry in release_files:
        filename = entry["key"]
        match = re.fullmatch(r"ODEO_FEB2025_v0_GamGam_mc_(\d{6})\.(.+)\.GamGam\.root", filename)
        if not match:
            raise ValueError(f"Unexpected release filename {filename}")
        dsid = int(match.group(1))
        if dsid in seen:
            raise ValueError(f"Duplicate release DSID {dsid}")
        seen.add(dsid)
        if dsid not in metadata:
            raise ValueError(f"Release DSID {dsid} missing from metadata")
        source = metadata[dsid]
        if match.group(2) != source["physics_short"]:
            raise ValueError(f"Filename / metadata physics_short mismatch for {dsid}")
        for field in NUMERIC_FIELDS:
            if not math.isfinite(float(source[field])):
                raise ValueError(f"Non-finite {field} for DSID {dsid}")
        size = entry["size"]
        if not isinstance(size, int) or size <= 0:
            raise ValueError(f"Invalid release size for DSID {dsid}")
        if not re.fullmatch(r"adler32:[0-9a-fA-F]{8}", entry["checksum"]):
            raise ValueError(f"Unexpected checksum for DSID {dsid}")
        if not entry["uri"].endswith("/" + filename):
            raise ValueError(f"URI / filename mismatch for DSID {dsid}")
        category, role, phase_space, low, high, overlap = classify(source)
        chosen = dsid in selected
        reason = "Not selected: scope-limited source inventory; no target use established"
        if chosen:
            reason = {
                343981: "Selected ggF single-H diphoton example; not HH; no luminosity normalization",
                346214: "Selected VBF single-H diphoton example; not HH; no luminosity normalization",
                423103: "Selected gammajet photon-pT 70-140 slice; does not cover all fake backgrounds",
            }.get(dsid, "Explicitly selected for bounded schema/kinematics inspection only")
        elif category == "PROMPT_DIPHOTON_CONTINUUM":
            if overlap == "NO_FINITE_GENERATED_105_160_OVERLAP":
                reason = "Excluded as generic 105-160 continuum: generator slice has no finite overlap; migration not assumed"
            elif size > NEW_BUDGET_BYTES:
                reason = "Relevant continuum but full file exceeds the entire 128 MiB new-file budget"
            else:
                reason = "Relevant continuum fits a fresh 128 MiB budget but not the remaining budget after committed transfer allocation"
        elif category == "SINGLE_HIGGS_DIPHOTON":
            reason = "Not selected: additional single-H production/decay or generator alternative; do not add overlapping rates"
        elif category in {"GAMMAJETS_FAKE_RELATED_CANDIDATE", "DIJET_FAKE_RELATED_CANDIDATE"}:
            reason = "Not selected: limited budget/coverage; fake-rate estimate and overlapping-sample combination unverified"
        rows.append({
            "dsid": dsid, "filename": filename, "size_bytes": size,
            "checksum": entry["checksum"], "release_uri": entry["uri"],
            **{field: source[field] for field in (
                "physics_short", "process", "generator", "crossSection_pb", "genFiltEff",
                "kFactor", "nEvents", "sumOfWeights", "sumOfWeightsSquared", "description",
                "keywords", "job_path",
            )},
            "e_tag": source["e-tag"], "physics_classification": category,
            "documented_phase_space": phase_space, "generated_mass_low_GeV": low,
            "generated_mass_high_GeV": high, "target_mass_overlap": overlap,
            "intended_role": role, "selection_reason": reason,
            "download_chosen": "YES" if chosen else "NO",
            "download_status": "SELECTED_SEE_TRANSFER_LEDGER" if chosen else "NOT_DOWNLOADED_BY_THIS_AUDIT",
            "normalization_status": "BLOCKED_EXACT_RELEASE_GENERATED_SUM_AND_DECAY_CONVENTION_UNVERIFIED",
            "exact_release_producer_status": "UNKNOWN_FEB2025_VS_LATER_V1_0_0",
            "truth_schema_status": "METADATA_ONLY_SEE_NATIVE_SCHEMA_AUDIT",
            "record_url": RECORD_URL, "metadata_url": METADATA_URL,
            "record_snapshot_sha256": record_hash, "metadata_snapshot_sha256": metadata_hash,
        })
    if not selected <= seen:
        raise ValueError(f"Selected DSIDs absent from release: {sorted(selected - seen)}")
    rows.sort(key=lambda row: row["dsid"])
    selected_bytes = sum(row["size_bytes"] for row in rows if row["download_chosen"] == "YES")
    if selected_bytes > NEW_BUDGET_BYTES:
        raise ValueError("Selected file sizes exceed 128 MiB before protocol/failure overhead")
    summary = {
        "metadata_join": "PASS", "release_files": len(rows), "unique_dsids": len(seen),
        "total_release_bytes": sum(row["size_bytes"] for row in rows),
        "selected_dsids": sorted(selected), "selected_payload_bytes": selected_bytes,
        "new_file_budget_bytes": NEW_BUDGET_BYTES,
        "transfer_budget_authority": "Parent transfer ledger; includes previously received/failed-transfer bytes",
        "physics_categories": dict(sorted(collections.Counter(row["physics_classification"] for row in rows).items())),
        "explicit_higgs_pair_candidates": [row["dsid"] for row in rows if row["physics_classification"] == "EXPLICIT_HIGGS_PAIR_CANDIDATE"],
        "record_snapshot_sha256": record_hash, "metadata_snapshot_sha256": metadata_hash,
        "source_status": "PUBLIC_METADATA_AUDIT_ONLY_NOT_NATIVE_SCHEMA_OR_NORMALIZATION_VALIDATION",
    }
    return rows, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=Path(".local/phase0_sources/opendata_93922_json.json"))
    parser.add_argument("--metadata", type=Path, default=Path(".local/phase0_sources/framework_extras_metadata.csv.txt"))
    parser.add_argument("--output", type=Path, default=Path("metadata/phase4_mc_sample_manifest.csv"))
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--selected", nargs="*", type=int, default=sorted(DEFAULT_SELECTED))
    args = parser.parse_args()
    rows, summary = build_manifest(args.record, args.metadata, set(args.selected))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary["manifest_sha256"] = sha256(args.output)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

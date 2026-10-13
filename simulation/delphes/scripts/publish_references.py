#!/usr/bin/env python3
"""Prepare only genuine validated100-entry detector references locally.

No Git/release calls, ROOT slicing/reserialization, event generation or overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

REPO = Path(__file__).resolve().parents[3]
CARD_SHA256 = "cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47"
PYTHIA_CARD_SHA256 = "53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389"
DELPHES_COMMIT = "28658365abeb71ee36dfc739f9670c1514c0cb10"
DELPHES_ARCHIVE_SHA256 = "b60d26d2ee2c84b58fbf2cf397fabd0ef3e89d3a0546d843c4ada82cc802d787"
DELPHES_SOURCE_URL = "https://codeload.github.com/delphes/delphes/tar.gz/refs/tags/3.5.1"
CAP = 10 * 1024**2
PROFILES = {
    "bbgg": ("pp_bbgg_atlas_like", "pp_bbgg_sm_lo_ps_13tev", "pp_bbgg_sm_lo_13tev", 610301, 610201),
    "ccgg": ("pp_ccgg_atlas_like", "pp_ccgg_sm_lo_ps_13tev", "pp_ccgg_sm_lo_13tev", 610302, 610202),
    "jjgg": ("pp_jjgg_light_atlas_like", "pp_jjgg_light_sm_lo_ps_13tev", "pp_jjgg_light_sm_lo_13tev", 610303, 610203),
}
PRIVATE = re.compile(rb"(?i)(?:/home/[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)")


def require(test, reason):
    if not test:
        raise ValueError(reason)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path):
    require(Path(path).stat().st_size <= 5 * 1024**2, "metadata exceeds bounded publication policy")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inspect_root(path, *, allow_oversize=False):
    """Portable ROOT signature/privacy guard; not native physical validation."""
    require(allow_oversize or path.stat().st_size <= CAP, "real100-entry ROOT reference exceeds10MiB; retain locally and prepare release proposal")
    with path.open("rb") as stream:
        require(stream.read(4) == b"root", "selected file lacks actual ROOT magic")
        stream.seek(0)
        tail = b""
        for chunk in iter(lambda: stream.read(1024**2), b""):
            data = tail + chunk
            require(PRIVATE.search(data) is None, "private path/credential visible in ROOT payload; original bytes preserved locally")
            tail = data[-2048:]


def prepare(profile, directory):
    directory = Path(directory).resolve()
    target_dir, hepmc_dir, mg5_dir, detector_seed, pythia_seed = PROFILES[profile]
    run = load(directory / "run_manifest.json")
    require(run["status"] == "PASS" and run["process"] == profile and run["events_requested"] == 100,
            "only a genuine independently validated100-input run may be selected")
    require(run["delphes_version"] == "3.5.1" and run["delphes_source_commit"] == DELPHES_COMMIT and
            run["root_version"] == "6.40.04", "detector software/source identity differs")
    require(run["installation"]["source_archive_sha256"] == DELPHES_ARCHIVE_SHA256,
            "verified official Delphes source archive identity differs")
    require(run["detector_canonical_card_sha256"] == CARD_SHA256 and
            sha(REPO / "simulation/delphes/cards/atlas_like_bbgg_baseline.tcl") == CARD_SHA256 and
            run["detector_seed"] == detector_seed and run["source_pythia_settings_sha256"] == PYTHIA_CARD_SHA256 and
            run["source_total_events"] == 1000, "detector/Pythia/card/normalization identity differs")
    for key in ("N_input", "N_read", "N_processed", "N_output"):
        require(run[key] == 100, "incomplete physical run counter: " + key)
    require(run["N_invalid"] == run["N_skipped"] == 0, "invalid/skipped detector inputs may not be hidden")
    prefix = f"reference_samples/delphes/{target_dir}"
    hepmc_relative = f"reference_samples/pythia8/{hepmc_dir}/shower_100.hepmc3.gz"
    mg5_relative = f"reference_samples/mg5/{mg5_dir}/reference_1000.lhe.gz"
    hepmc_manifest = load((REPO / hepmc_relative).parent / "sample_manifest.json")
    hepmc = next(item for item in hepmc_manifest["samples"] if item["sample_id"] == "shower_100")
    require(sha(REPO / hepmc_relative) == hepmc["compressed_file_sha256"] and
            run["selected_input_sha256"] == hepmc["decompressed_file_sha256"] and
            run["source_mg5_sha256"] == hepmc["source_file_sha256"] and
            run["source_pythia_run_id"] == hepmc["portable_validation"]["pythia_run_id"] and
            hepmc["pythia_seed"] == pythia_seed, "detector input is not the exact selected published shower100")
    require(sha(REPO / mg5_relative) == run["source_mg5_sha256"], "original MG5 source identity differs")
    mg5_manifest = load((REPO / mg5_relative).parent / "sample_manifest.json")
    mg5 = next(item for item in mg5_manifest["samples"] if item["sample_id"] == "reference_1000")
    require(mg5["actual_events"] == 1000 and math.isclose(run["input_cross_section_pb"], mg5["generator_cross_section_pb"], rel_tol=1e-12),
            "original per-process cross section/count differs")
    native_path = directory / "native_validation.json"
    native = load(native_path)
    require(native["validation_status"] == "PASS" and
            native["validator"] == "actual_ROOT_TClonesArray_Delphes_dictionary_and_source_adapter" and
            native["root_version"] == "6.40.04" and native["cpp_standard"] == 20 and native["process"] == profile,
            "actual compatible native ROOT readback proof missing")
    for key in ("N_input", "N_read", "N_processed", "N_output"):
        require(native[key] == 100, "incomplete native assessment: " + key)
    require(native["N_invalid"] == native["N_skipped"] == 0, "native failed/skipped events cannot become references")
    for key, name in (("root_file_sha256", "detector.root"), ("input_index_sha256", "input_event_index.dat"),
                      ("truth_index_sha256", "truth_analysis_index.dat"), ("detector_card_sha256", "detector_card.tcl")):
        require(native[key] == sha(directory / name) == run["files"][name]["sha256"], "native report inspected different bytes: " + name)
    root = directory / "detector.root"
    inspect_root(root, allow_oversize=True)
    runtime = (directory / "detector_card.tcl").read_bytes()
    canonical = (REPO / "simulation/delphes/cards/atlas_like_bbgg_baseline.tcl").read_bytes()
    require(runtime == canonical.replace(b"set RandomSeed 610301", f"set RandomSeed {detector_seed}".encode(), 1),
            "runtime card contains an unreviewed change")
    copies = {}
    names = {"detector.root": "detector_100.root", "detector_card.tcl": "detector_card.tcl",
             "source_event_ledger.jsonl": "source_event_ledger.jsonl", "input_event_index.dat": "input_event_index.dat",
             "input_event_index.jsonl": "input_event_index.jsonl", "truth_analysis_index.dat": "truth_analysis_index.dat",
             "native_validation.json": "native_validation.json", "reco_events.jsonl": "reco_events.jsonl",
             "cutflow.csv": "cutflow.csv", "efficiencies.csv": "efficiencies.csv"}
    for name, public_name in names.items():
        source = directory / name
        require(sha(source) == run["files"][name]["sha256"], "selected local snapshot changed: " + name)
        if name != "detector.root":
            cap = CAP if name == "input_event_index.dat" else 5 * 1024**2
            require(source.stat().st_size <= cap and PRIVATE.search(source.read_bytes()) is None,
                    "private/oversized selected source evidence: " + name)
        copies[prefix + "/" + public_name] = source
    require(native["scientific_content_sha256"] == sha(directory / "reco_events.jsonl"), "reco scientific-content hash differs")
    def object_for(filename):
        return {"path": prefix + "/" + names[filename], "sha256": sha(directory / filename)}
    manifest = {"schema_version": 1, "process": profile, "physics_label": "FAST_SIM_ATLAS_LIKE_NOT_OFFICIAL_ATLAS",
                "events": 100, "delphes_version": "3.5.1", "delphes_source_commit": DELPHES_COMMIT, "root_version": "6.40.04",
                "delphes_source_url": DELPHES_SOURCE_URL, "delphes_source_archive_sha256": DELPHES_ARCHIVE_SHA256,
                "root_file": {**object_for("detector.root"), "bytes": root.stat().st_size},
                "input_hepmc": {"path": hepmc_relative, "compressed_sha256": hepmc["compressed_file_sha256"],
                                "decompressed_sha256": hepmc["decompressed_file_sha256"], "events": 100},
                "source_ledger": object_for("source_event_ledger.jsonl"), "input_index": object_for("input_event_index.dat"),
                "truth_index": object_for("truth_analysis_index.dat"),
                "detector_card": {"path": prefix + "/detector_card.tcl", "canonical_sha256": CARD_SHA256,
                                  "runtime_sha256": sha(directory / "detector_card.tcl"), "seed": detector_seed},
                "source_mg5": {"path": mg5_relative, "sha256": run["source_mg5_sha256"]},
                "source_pythia": {"settings_sha256": PYTHIA_CARD_SHA256, "run_id": run["source_pythia_run_id"], "seed": pythia_seed},
                "native_validation": object_for("native_validation.json"), "normalization_denominator": 1000,
                "input_generator_cross_section_pb": mg5["generator_cross_section_pb"],
                "validation_status": "PASS", "publication": "LOCAL_PREPARED_NO_GIT_ACTION",
                "transformation": "NONE; original ROOT/card/index/ledger/analysis bytes copied unchanged",
                "statistics": "same original1000 hard-event source; these100 detector inputs are not independent extra hard statistics",
                "provenance_files": [object_for(name) for name in ("input_event_index.jsonl", "reco_events.jsonl", "cutflow.csv", "efficiencies.csv")]}
    return prefix + "/sample_manifest.json", manifest, copies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for profile in PROFILES:
        parser.add_argument("--" + profile + "-run", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        writes, copies, summary = {}, {}, {}
        for profile in PROFILES:
            name, manifest, plan = prepare(profile, getattr(args, profile + "_run"))
            require(not copies.keys() & plan.keys(), "overlapping publication paths")
            writes[name] = (json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
            copies.update(plan)
            summary[profile] = manifest["root_file"]
        if any(value["bytes"] > CAP for value in summary.values()):
            proposal = {"schema_version": 1, "status": "DRAFT_RELEASE_PROPOSAL_LOCAL_ONLY",
                        "repository": "TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1", "proposed_tag": "phase6c-delphes-detector100-v1", "draft": True,
                        "source_commit": "UNKNOWN_PENDING_REMOTE_SEAL", "actual_events_per_asset": 100,
                        "proposed_assets": [{"name": profile + "_detector_100.root", "sha256": value["sha256"], "bytes": value["bytes"],
                                             "github_individual_asset_size_preflight": "PASS" if value["bytes"] < 2 * 1024**3 else "FAIL_OVERSIZE"}
                                            for profile, value in summary.items()],
                        "reviewed_repository_root_asset_cap_bytes": CAP, "release_created": False, "assets_uploaded": False,
                        "git_lfs_enabled": False, "public_reference_files_written": False,
                        "next_action": "User review and explicit authorization required; no complete GitHub reference publication claimed"}
            target = REPO / "simulation/delphes/evidence/large_root_release_proposal.json"
            require(not target.exists(), "existing release proposal preserved; no overwrite")
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("x", encoding="utf-8") as output:
                    json.dump(proposal, output, indent=2, allow_nan=False)
                    output.write("\n")
            print(json.dumps({"status": "BLOCKED_REFERENCE_SIZE_CAP", "proposal": proposal, "dry_run": args.dry_run}, indent=2))
            return 2
        require(all(not (REPO / name).exists() for name in [*writes, *copies]), "existing publication artifacts preserved; no overwrite")
        if not args.dry_run:
            expected = {}
            for data in writes.values():
                manifest = json.loads(data)
                descriptors = [manifest[key] for key in ("root_file", "source_ledger", "input_index", "truth_index", "native_validation")]
                descriptors.extend(manifest["provenance_files"])
                expected.update({item["path"]: item["sha256"] for item in descriptors})
                expected[manifest["detector_card"]["path"]] = manifest["detector_card"]["runtime_sha256"]
            require(expected.keys() == copies.keys(), "copy plan lacks exact manifest hash binding")
            for name, original in copies.items():
                target = REPO / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with original.open("rb") as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output, length=1024**2)
                require(sha(target) == expected[name], "copied artifact changed after preflight; incomplete local preparation: " + name)
            for name, data in writes.items():
                with (REPO / name).open("xb") as output:
                    output.write(data)
        print(json.dumps({"status": "PREFLIGHT_PASS_NO_PUBLIC_WRITES" if args.dry_run else "PREPARED_LOCAL_ONLY",
                          "files": len(writes) + len(copies), "references": summary}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, StopIteration) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

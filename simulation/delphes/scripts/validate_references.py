#!/usr/bin/env python3
"""Portable reference integrity checks; does not open ROOT with its native API."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

from run_delphes import REPO, CARD, CARD_SHA256, SOURCE_COMMIT, SEEDS, hepmc, file_sha256, require, read_json, indexed_particles

DIRECTORIES = {"bbgg": "pp_bbgg_atlas_like", "ccgg": "pp_ccgg_atlas_like", "jjgg": "pp_jjgg_light_atlas_like"}
DELPHES_SOURCE_ARCHIVE_SHA256 = "b60d26d2ee2c84b58fbf2cf397fabd0ef3e89d3a0546d843c4ada82cc802d787"
DELPHES_SOURCE_ARCHIVE_URL = "https://codeload.github.com/delphes/delphes/tar.gz/refs/tags/3.5.1"


def relative_file(repo, value, cap=5 * 1024**2):
    require(isinstance(value, str) and not Path(value).is_absolute(), "publication path must be repository-relative")
    original = repo / value
    resolved = original.resolve()
    require(resolved.is_relative_to(repo) and original.is_file() and not original.is_symlink(), "missing/escaping/symlink publication artifact")
    require(original.stat().st_size <= cap, "publication artifact exceeds bounded policy")
    return original


def artifact(repo, descriptor, *, sha_key="sha256", cap=5 * 1024**2):
    path = relative_file(repo, descriptor["path"], cap)
    require(file_sha256(path) == descriptor[sha_key], "artifact SHA256 mismatch: " + descriptor["path"])
    if "bytes" in descriptor:
        require(path.stat().st_size == descriptor["bytes"], "artifact size mismatch")
    return path


def next_line(stream):
    raw = stream.readline(1024 * 1024 + 1)
    require(raw and len(raw) <= 1024 * 1024 and raw.endswith("\n"), "truncated/oversized index record")
    return raw.split()


def validate_input_index(index_path, hepmc_path, ledger_path, count):
    rows = hepmc.ledger_rows(ledger_path)
    header = None
    events = 0
    with index_path.open(encoding="utf-8") as index:
        require(index.readline() == "ATLAS_DELPHES_INPUT_V1\n", "unsupported native input index schema")
        for kind, raw in hepmc.iter_ascii(hepmc_path, max_decompressed_gb=1):
            if kind == "header":
                header = hepmc.parse_header(raw)
            elif kind == "event":
                events += 1
                event = hepmc.parse_event(raw, header)
                ledger = next(rows, None)
                require(ledger is not None, "input index lacks source ledger row")
                fields = next_line(index)
                require(len(fields) == 11 and fields[0] == "E", "invalid native E index")
                require(int(fields[1]) == events and int(fields[2]) == event["event_number"] and fields[3] == event["event_hash"],
                        "native index is not bound to the exact HepMC event")
                require(int(fields[4]) == ledger["source_event_index"] and fields[5] == ledger["source_event_content_hash"]
                        and int(fields[8]) == ledger["source_total_events"], "native index source ancestry/normalization mismatch")
                require(math.isclose(float(fields[6]), ledger["input_contribution_pb"], rel_tol=1e-12, abs_tol=1e-15)
                        and math.isclose(float(fields[7]), ledger["lhe_weight_pb"], rel_tol=1e-12, abs_tol=1e-15), "native index source weights mismatch")
                particles = list(indexed_particles(raw))
                require(int(fields[9]) == len(particles) and int(fields[10]) == len(event["weights"]), "native index particle/weight count mismatch")
                weights = next_line(index)
                require(weights[0] == "W" and len(weights) == len(event["weights"]) + 1
                        and all(float(a) == b for a, b in zip(weights[1:], event["weights"])), "native index weight vector mismatch")
                for particle in particles:
                    expected = ["P", *particle]
                    require(next_line(index) == expected, "native input Particle tuple differs from exact source record")
        require(events == count and not index.read().strip(), "native index count/trailing data mismatch")


def validate_truth_envelope(path, count, ledger_path, run_id, seed):
    rows = hepmc.ledger_rows(ledger_path)
    with path.open(encoding="utf-8") as stream:
        require(stream.readline() == "ATLAS_DELPHES_TRUTH_V1\n", "unsupported truth index schema")
        for ordinal in range(1, count + 1):
            row = next(rows, None)
            fields = next_line(stream)
            require(len(fields) == 12 and fields[0] == "E" and list(map(int, fields[1:4])) == [ordinal, ordinal, row["source_event_index"]],
                    "truth index event/source numbering mismatch")
            require(fields[4] == row["source_event_content_hash"] and fields[5] == run_id and int(fields[6]) == seed,
                    "truth index run/seed/source mismatch")
            counts = list(map(int, fields[7:]))
            require(counts[:4] == [2, 2, 2, 2] and 0 <= counts[4] <= 100000, "invalid baseline truth multiplicities")
            for marker, amount in zip(("L", "G", "Q", "R", "H"), counts):
                seen = set()
                for _ in range(amount):
                    entry = next_line(stream)
                    expected_len = 10 if marker == "H" else 8
                    require(entry[0] == marker and len(entry) == expected_len and int(entry[1]) > 0 and int(entry[1]) not in seen,
                            "invalid/duplicate truth particle record")
                    seen.add(int(entry[1]))
                    require(int(entry[2]) != 0, "invalid truth PID")
                    start = 5 if marker == "H" else 3
                    require(all(math.isfinite(float(value)) for value in entry[start:]), "non-finite truth record")
                    if marker == "H":
                        require(entry[3] in {"0", "1"} and entry[4] in {"0", "1"} and "1" in entry[3:5], "invalid inclusive heavy-flavour flags")
        require(not stream.read().strip(), "truth index trailing records")


def validate_repository(repo):
    repo = Path(repo).resolve()
    require(file_sha256(repo / CARD.relative_to(REPO)) == CARD_SHA256, "reviewed canonical detector card changed")
    results, index_total_bytes = [], 0
    for profile, name in DIRECTORIES.items():
        directory = repo / "reference_samples/delphes" / name
        manifest = read_json(directory / "sample_manifest.json")
        require(manifest["schema_version"] == 1 and manifest["process"] == profile and manifest["events"] == 100,
                "unsupported detector reference schema/process/count")
        require(manifest["physics_label"] == "FAST_SIM_ATLAS_LIKE_NOT_OFFICIAL_ATLAS", "missing study interpretation")
        require(manifest["delphes_version"] == "3.5.1" and manifest["delphes_source_commit"] == SOURCE_COMMIT and manifest["root_version"] == "6.40.04",
                "detector/ROOT source version identity mismatch")
        require(manifest["delphes_source_archive_sha256"] == DELPHES_SOURCE_ARCHIVE_SHA256 and manifest["delphes_source_url"] == DELPHES_SOURCE_ARCHIVE_URL,
                "official versioned source archive identity mismatch")
        require(manifest["normalization_denominator"] == 1000, "reference prefix must retain original MG5 denominator")
        root = artifact(repo, manifest["root_file"], cap=10 * 1024**2)
        require(root == directory / "detector_100.root", "unexpected detector reference filename")
        with root.open("rb") as stream:
            require(stream.read(4) == b"root", "ROOT file signature missing")
        source_path, source_hash, sigma = hepmc.SOURCE_SAMPLES[profile]
        source = artifact(repo, manifest["source_mg5"])
        require(source == repo / source_path and manifest["source_mg5"]["sha256"] == source_hash, "original MG5 source identity changed")
        require(math.isclose(manifest["input_generator_cross_section_pb"], sigma, rel_tol=1e-12), "original per-process cross section changed")
        input_desc = manifest["input_hepmc"]
        input_path = artifact(repo, input_desc, sha_key="compressed_sha256", cap=10 * 1024**2)
        expected_input = repo / hepmc.REFERENCE_DIRS[profile] / "shower_100.hepmc3.gz"
        require(input_path == expected_input and input_desc["events"] == 100, "reference requires the existing published100 HepMC input")
        phase6b = read_json(input_path.parent / "sample_manifest.json")
        reference = next(row for row in phase6b["samples"] if row["sample_id"] == "shower_100")
        require(input_desc["compressed_sha256"] == reference["compressed_file_sha256"] and
                input_desc["decompressed_sha256"] == reference["decompressed_file_sha256"], "Phase6B input checksum linkage mismatch")
        ledger = artifact(repo, manifest["source_ledger"])
        pythia = manifest["source_pythia"]
        require(pythia["settings_sha256"] == hepmc.BASELINE_SETTINGS_SHA256 and pythia["run_id"] == reference["portable_validation"]["pythia_run_id"]
                and pythia["seed"] == reference["pythia_seed"], "Pythia card/run/seed ancestry mismatch")
        checked = hepmc.validate_file(input_path, 100, ledger=ledger, source_file=source, source_sha256=source_hash,
                                      sample_id=profile, pythia_seed=pythia["seed"])
        require(checked["event_identity"] == "PASS" and checked["ledger_failed_inputs"] == 0, "input source mapping incomplete")
        index = artifact(repo, manifest["input_index"], cap=10 * 1024**2)
        require(index == directory / "input_event_index.dat", "expanded index cap applies only to the exact reviewed reference index")
        index_total_bytes += index.stat().st_size
        truth = artifact(repo, manifest["truth_index"])
        validate_input_index(index, input_path, ledger, 100)
        validate_truth_envelope(truth, 100, ledger, pythia["run_id"], pythia["seed"])
        card_desc = manifest["detector_card"]
        card = artifact(repo, card_desc, sha_key="runtime_sha256")
        require(card_desc["canonical_sha256"] == CARD_SHA256 and card_desc["seed"] == SEEDS[profile], "detector seed/canonical card mismatch")
        expected_card = (repo / CARD.relative_to(REPO)).read_bytes().replace(b"set RandomSeed 610301", f"set RandomSeed {SEEDS[profile]}".encode(), 1)
        require(card.read_bytes() == expected_card, "runtime card includes an unreviewed physics change")
        physical_path = artifact(repo, manifest["native_validation"])
        native = read_json(physical_path)
        require(native["validation_status"] == "PASS" and all(native[key] == 100 for key in ("N_input", "N_read", "N_processed", "N_output"))
                and native["N_invalid"] == native["N_skipped"] == 0, "actual native ROOT report has failed/lost events")
        for key, path in (("root_file_sha256", root), ("input_index_sha256", index), ("truth_index_sha256", truth), ("detector_card_sha256", card)):
            require(native[key] == file_sha256(path), "native physical report not bound to exact artifact: " + path.name)
        results.append({"process": profile, "events": 100, "root_sha256": manifest["root_file"]["sha256"], "root_bytes": root.stat().st_size,
                        "portable_integrity_status": "PASS", "native_ROOT_readback": "NOT_EXECUTED_BY_PORTABLE_CI",
                        "physical_validation_evidence": "HASH_BOUND_EXISTING_NATIVE_REPORT", "truth_ancestry_recomputation": "NOT_EXECUTED_BY_PORTABLE_CI"})
    require(index_total_bytes <= 30 * 1024**2, "combined reviewed reference input indices exceed 30 MiB")
    return {"validation_status": "PASS", "validator": "portable_files_source_cards_indices_and_native_report_binding", "samples": results,
            "reviewed_input_index_bytes": index_total_bytes, "reviewed_input_index_budget_bytes": 30 * 1024**2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = validate_repository(args.repo)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, StopIteration) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        raise SystemExit(1)

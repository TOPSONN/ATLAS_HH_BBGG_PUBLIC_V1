#!/usr/bin/env python3
"""Read-only binned raw-jet diagnostics from actual native Stage C records.

No detector execution, ROOT rewriting, calibration or physics acceptance claim.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import sys

from publish_references import CARD_SHA256, DELPHES_COMMIT, PROFILES, PYTHIA_CARD_SHA256, load, require, sha

PT_EDGES = (25.0, 50.0, 100.0, 200.0, None)
ETA_EDGES = (0.0, 0.8, 1.6, 2.5)
CATEGORIES = ("b", "c", "light", "UNKNOWN")


def flavor_category(value):
    return "b" if value == 5 else "c" if value == 4 else "light" if value in (0, 1, 2, 3, 21) else "UNKNOWN"


def probability(flavor, pt):
    if flavor == 5:
        return 0.80 * math.tanh(0.003 * pt) * (30 / (1 + 0.086 * pt))
    if flavor == 4:
        return 0.20 * math.tanh(0.02 * pt) / (1 + 0.0034 * pt)
    return 0.002 + 7.3e-6 * pt


def interval(tagged, count):
    if not count:
        return None
    z = 1.959963984540054
    p, denominator = tagged / count, 1 + z * z / count
    center = (p + z * z / (2 * count)) / denominator
    half = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / denominator
    return [0.0 if tagged == 0 else max(0.0, center - half), 1.0 if tagged == count else min(1.0, center + half)]


def new_group():
    return {"eligible_reco_jets": 0, "tagged_bit0": 0, "probabilities": []}


def add(group, tagged, predicted):
    group["eligible_reco_jets"] += 1
    group["tagged_bit0"] += int(tagged)
    group["probabilities"].append(predicted)


def finish(group, category):
    n, k = group["eligible_reco_jets"], group["tagged_bit0"]
    expected = math.fsum(group["probabilities"])
    variance = math.fsum(p * (1 - p) for p in group["probabilities"])
    sufficient = category != "UNKNOWN" and n >= 30 and expected >= 5 and n - expected >= 5
    return {"eligible_reco_jets": n, "tagged_bit0": k, "expected_tags": expected,
            "mean_card_probability": expected / n if n else None, "observed_fraction": k / n if n else None,
            "wilson95": interval(k, n), "conditional_card_tag_variance": variance,
            "model_standardized_residual": (k - expected) / math.sqrt(variance) if variance else None,
            "statistics_status": "DESCRIPTIVE_SUFFICIENT_COUNTS" if sufficient else "INSUFFICIENT_STATISTICS"}


def bin_number(value, edges):
    for index, (low, high) in enumerate(zip(edges, edges[1:])):
        if value >= low and (high is None or value < high):
            return index
    raise ValueError("eligible jet outside documented diagnostic bins")


def summarize(profile, directory):
    directory = Path(directory)
    manifest, native = load(directory / "run_manifest.json"), load(directory / "native_validation.json")
    require(manifest["status"] == native["validation_status"] == "PASS" and manifest["process"] == native["process"] == profile,
            "only actual validated Stage C runs may supply binned diagnostics")
    require(manifest["events_requested"] == 1000 and manifest["source_total_events"] == 1000 and
            manifest["detector_canonical_card_sha256"] == CARD_SHA256, "Stage C/card/original count identity differs")
    require(manifest["delphes_version"] == "3.5.1" and manifest["delphes_source_commit"] == DELPHES_COMMIT and
            manifest["root_version"] == native["root_version"] == "6.40.04" and native["cpp_standard"] == 20 and
            manifest["source_pythia_settings_sha256"] == PYTHIA_CARD_SHA256 and
            sha(directory / "detector_card.tcl") == manifest["detector_runtime_card_sha256"] == native["detector_card_sha256"],
            "actual native software/card/source identity differs")
    for key in ("N_input", "N_read", "N_processed", "N_output"):
        require(manifest[key] == native[key] == 1000, "incomplete native Stage C event counts")
    require(manifest["N_invalid"] == native["N_invalid"] == manifest["N_skipped"] == native["N_skipped"] == 0,
            "failed/skipped events cannot supply accepted binned statistics")
    records = directory / "reco_events.jsonl"
    require(records.stat().st_size <= 64 * 1024**2, "native diagnostic records exceed bounded64MiB policy")
    hashes = {name: sha(directory / name) for name in ("native_validation.json", "reco_events.jsonl", "efficiencies.csv", "detector.root")}
    require(all(hashes[name] == manifest["files"][name]["sha256"] for name in hashes) and
            hashes["detector.root"] == native["root_file_sha256"] and hashes["reco_events.jsonl"] == native["scientific_content_sha256"],
            "analysis/native/ROOT hash binding differs")
    aggregate = {category: new_group() for category in CATEGORIES}
    bins = {axis: {category: [new_group() for _ in edges[:-1]] for category in CATEGORIES}
            for axis, edges in (("pt_gev", PT_EDGES), ("abs_eta", ETA_EDGES))}
    indices = set()
    count = 0
    with records.open("rb") as stream:
        while raw := stream.readline(1024**2 + 1):
            require(raw.endswith(b"\n") and len(raw) <= 1024**2, "truncated/oversized native diagnostic row")
            row = json.loads(raw)
            count += 1
            require(row["ordinal"] == count and 1 <= row["source_event_index"] <= 1000 and
                    row["source_event_index"] not in indices, "duplicated/gapped source event diagnostic")
            indices.add(row["source_event_index"])
            eligible, tagged_in_event = 0, 0
            for jet in row["jets"]:
                pt, eta, flavor, bits = jet["pt"], jet["eta"], jet["flavor"], jet["btag"]
                require(math.isfinite(pt) and math.isfinite(eta) and isinstance(flavor, int) and isinstance(bits, int) and
                        flavor >= 0 and bits in (0, 1), "invalid native jet fields")
                if not (pt > 25 and abs(eta) < 2.5):
                    continue
                category, tagged = flavor_category(flavor), bool(bits & 1)
                predicted = probability(flavor, pt)
                require(math.isfinite(predicted) and 0 <= predicted <= 1, "card probability outside Bernoulli domain")
                eligible += 1
                tagged_in_event += tagged
                add(aggregate[category], tagged, predicted)
                for axis, value, edges in (("pt_gev", pt, PT_EDGES), ("abs_eta", abs(eta), ETA_EDGES)):
                    add(bins[axis][category][bin_number(value, edges)], tagged, predicted)
            require(eligible == row["N_jets"] and tagged_in_event == row["N_btags"], "independent eligible denominator differs from native record")
    require(count == 1000, "native record count differs from Stage C")
    result = {category: finish(group, category) for category, group in aggregate.items()}
    with (directory / "efficiencies.csv").open(newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    require(len(csv_rows) == 4 and {row["flavor"] for row in csv_rows} == set(CATEGORIES), "native aggregate flavor rows incomplete")
    for row in csv_rows:
        actual = result[row["flavor"]]
        require(row["process"] == profile and int(row["eligible_reco_jets"]) == actual["eligible_reco_jets"] and
                int(row["tagged_bit0"]) == actual["tagged_bit0"] and
                math.isclose(float(row["expected_tags"]), actual["expected_tags"], rel_tol=1e-12, abs_tol=1e-12) and
                row["statistics_status"] == actual["statistics_status"],
                "independent binned totals do not match actual native CSV")
        if actual["eligible_reco_jets"]:
            for field, value in (("estimate", actual["observed_fraction"]), ("wilson95_low", actual["wilson95"][0]),
                                 ("wilson95_high", actual["wilson95"][1])):
                require(math.isclose(float(row[field]), value, rel_tol=1e-12, abs_tol=1e-12), "independent descriptive interval differs from native CSV")
    return {"process": profile, "events": count, "source_mg5_sha256": manifest["source_mg5_sha256"],
            "source_pythia_run_id": manifest["source_pythia_run_id"], "detector_runtime_card_sha256": manifest["detector_runtime_card_sha256"],
            "source_native_hashes": hashes, "aggregate": result,
            "bins": {axis: {category: [finish(group, category) for group in groups] for category, groups in by_category.items()}
                     for axis, by_category in bins.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for profile in PROFILES:
        parser.add_argument("--" + profile + "-run", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    require(not args.report.exists(), "existing numerical evidence preserved; choose a new report filename")
    samples = [summarize(profile, getattr(args, profile + "_run")) for profile in PROFILES]
    report = {"schema_version": 1, "validation_status": "PASS_NUMERICAL_READBACK_OF_NATIVE_STAGE_C",
              "working_point": "UPSTREAM_ATLAS_CARD_BIT0_STUDY", "canonical_card_sha256": CARD_SHA256,
              "input_events_per_process": 1000, "stage_b_added_to_statistics": False,
              "denominator": "raw eligible reconstructed jets pT>25GeV |eta|<2.5 before event-level cuts; actual Flavor category",
              "pt_bin_edges_gev": PT_EDGES, "abs_eta_bin_edges": ETA_EDGES,
              "bin_convention": "lower inclusive, upper exclusive after strict eligible-jet selection; null final pT upper edge means infinity",
              "interval_scope": "descriptive per-jet Wilson95; event correlations/systematics unmodeled; not ATLAS calibration",
              "low_count_policy": "INSUFFICIENT_STATISTICS if n<30 or expected_tags<5 or n-expected_tags<5 or UNKNOWN category",
              "physics_acceptance": "no independent ROOT execution by this numerical summary; hashes bind actual preceding native readback",
              "samples": samples}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write("\n")
    print("PASS: Stage C numerical b-tag bins independently match native aggregate CSV; " + str(args.report))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        raise SystemExit(1)

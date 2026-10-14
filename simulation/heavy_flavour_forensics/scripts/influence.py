#!/usr/bin/env python3
"""Event influence and native-flavour tag combinations on the fixed Phase6D pilot.

All source events remain authoritative. Leave-one-out quantities are diagnostics,
not corrected predictions, extra samples, or a background-stitching prescription.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/rare_backgrounds/scripts"))
import conditional_tags as tags
import analyze_pilot as pilot

PAIR_TYPES = ("bb", "bc", "b-light", "cc", "c-light", "light-light")
EVENT_TYPES = ("at_least_two_native_b_tags", "one_native_b_tag_and_nonb_tags", "zero_native_b_tags_and_nonb_tags")
PROFILES = ("bbgg", "ccgg", "jjgg")
ZERO, ONE = Decimal(0), Decimal(1)
BASE = "7b1fccb41133f4f97a5277fa09efc90a1da41239"


def pair_type(first, second):
    a, b = tags.flavor_category(first), tags.flavor_category(second)
    if a == b:
        return {"b": "bb", "c": "cc", "light": "light-light"}[a]
    return "bc" if {a, b} == {"b", "c"} else "b-light" if "b" in (a, b) else "c-light"


def states(probabilities):
    p0, p1, tail = ONE, ZERO, ZERO
    for value in probabilities:
        p = tags.decimal_value(value)
        tags.require(0 <= p <= 1, "invalid tag probability")
        tail, p1, p0 = tail + p1 * p, p1 * (1 - p) + p0 * p, p0 * (1 - p)
    return p0, p1, tail


def event_decomposition(jets, eligible=True):
    """Two distinct exclusive partitions: leading pair and number of b tags."""
    jets = tags.sorted_objects(jets)
    pairs = {name: ZERO for name in PAIR_TYPES}
    events = {name: ZERO for name in EVENT_TYPES}
    if not eligible:
        return {"q": ZERO, "leading_pair_types": pairs, "event_tag_origin_types": events}
    with localcontext() as context:
        context.prec = 60
        probabilities = [tags.tag_probability(jet["flavor"], jet["pt"]) for jet in jets]
        q = tags.probability_at_least_two(probabilities)
        for a, b, chance in tags.leading_pair_probabilities(probabilities):
            pairs[pair_type(jets[a]["flavor"], jets[b]["flavor"])] += chance
        b_probs = [p for jet, p in zip(jets, probabilities) if jet["flavor"] == 5]
        nonb_probs = [p for jet, p in zip(jets, probabilities) if jet["flavor"] != 5]
        b0, b1, b2 = states(b_probs)
        n0, n1, n2 = states(nonb_probs)
        events[EVENT_TYPES[0]] = b2
        events[EVENT_TYPES[1]] = b1 * (n1 + n2)
        events[EVENT_TYPES[2]] = b0 * n2
        tags.require(abs(sum(pairs.values()) - q) <= Decimal("1e-44") and
                     abs(sum(events.values()) - q) <= Decimal("1e-44"), "exclusive native-flavour partitions do not normalize")
        return {"q": q, "leading_pair_types": pairs, "event_tag_origin_types": events}


def finite(value):
    number = float(value)
    tags.require(math.isfinite(number), "nonfinite influence statistic")
    return number


def stage_statistics(records, stage, target=997):
    tags.require(len(records) >= 2, "source variance requires at least two original events")
    identities = [row["source_event_index"] for row in records]
    tags.require(all(type(index) is int and index > 0 for index in identities) and
                 len(identities) == len(set(identities)), "duplicate/invalid source identities in stage statistics")
    with localcontext() as context:
        context.prec = 60
        n = Decimal(len(records))
        q = [tags.decimal_value(row[stage]["q"]) for row in records]
        tags.require(all(0 <= value <= 1 for value in q), "stage probability outside [0,1]")
        for row, value in zip(records, q):
            for field, categories in (("leading_pair_types", PAIR_TYPES), ("event_tag_origin_types", EVENT_TYPES)):
                tags.require(set(row[stage][field]) == set(categories), "incomplete/unknown native-flavour categories")
                values = [tags.decimal_value(row[stage][field][category]) for category in categories]
                tags.require(all(0 <= chance <= 1 for chance in values) and abs(sum(values) - value) <= Decimal("1e-44"),
                             "native-flavour category partition does not normalize")
        weights = [tags.decimal_value(row["source_contribution_pb"]) for row in records]
        total, square = sum(q), sum(value * value for value in q)
        mean = total / n
        integrands = [n * w * value for w, value in zip(weights, q)]
        cross_section = sum(w * value for w, value in zip(weights, q))
        pilot_var_count = n / (n - 1) * sum((value - mean)**2 for value in q)
        pilot_var_sigma = sum((value - cross_section)**2 for value in integrands) / (n * (n - 1))
        conditional_tag_var = sum(value * (1 - value) for value in q)
        tag_weight_var = sum(w * w * value * (1 - value) for w, value in zip(weights, q))
        order = sorted(range(len(records)), key=lambda i: (-q[i], records[i]["source_event_index"]))
        per_event = []
        for i, row in enumerate(records):
            values = {"q": str(q[i]), "source_weighted_expected_cross_section_pb": str(weights[i] * q[i]),
                      "conditional_tag_count_variance": str(q[i] * (1 - q[i])),
                      "conditional_tag_weighted_variance_pb2": str(weights[i]**2 * q[i] * (1 - q[i])),
                      "pilot_probability_mean_variance_contribution": str((q[i] - mean)**2 / (n * (n - 1))),
                      "pilot_expected_count_variance_contribution": str(n * (q[i] - mean)**2 / (n - 1)),
                      "pilot_cross_section_mean_variance_contribution_pb2": str((integrands[i] - cross_section)**2 / (n * (n - 1)))}
            per_event.append(values)
            row[stage].update(values)
        total_weights, square_weights = sum(weights), sum(w*w for w in weights)
        result = {
            "events_original_independent_sources": len(records), "expected_count": str(total),
            "expected_cross_section_pb": str(cross_section), "conditional_tag_count_variance": str(conditional_tag_var),
            "conditional_tag_weighted_variance_pb2": str(tag_weight_var),
            "pilot_expected_count_variance": str(pilot_var_count), "pilot_cross_section_mean_variance_pb2": str(pilot_var_sigma),
            "pilot_probability_mean_variance": str(pilot_var_count / n**2),
            "top5_sum_q": str(sum(q[i] for i in order[:5])), "top10_sum_q": str(sum(q[i] for i in order[:10])),
            "top5_fraction": finite(sum(q[i] for i in order[:5]) / total) if total else None,
            "top10_fraction": finite(sum(q[i] for i in order[:10]) / total) if total else None,
            "concentration_sum_q_squared": str(square),
            "concentration_ratio": finite(total**2 / square) if square else None,
            "concentration_scope": "(sum q)^2/sum(q^2) is a yield-concentration diagnostic, not a count of independent events",
            "weight_only_effective_sample_size": finite(total_weights**2 / square_weights) if square_weights else None,
            "weight_information_scope": "weight dispersion only, without rare acceptance; positive-equal original weights yield N=1000",
            "pilot_inverse_squared_relative_SE": finite(total**2 / pilot_var_count) if pilot_var_count else None,
            "conditional_tag_inverse_squared_relative_SD": finite(total**2 / conditional_tag_var) if conditional_tag_var else None,
            "pilot_weighted_inverse_squared_relative_SE": finite(cross_section**2 / pilot_var_sigma) if pilot_var_sigma else None,
            "conditional_weighted_inverse_squared_relative_SD": finite(cross_section**2 / tag_weight_var) if tag_weight_var else None,
            "precision_information_scope": "inverse estimated squared relative error; separate pilot/tag meanings; not extra events, calibrated significance or validated precision",
            "maximum_pilot_variance_fraction": finite(max((value - mean)**2 for value in q) /
                sum((value - mean)**2 for value in q)) if pilot_var_count else None,
            "top10_events": [{"source_event_index": records[i]["source_event_index"],
                              "source_event_hash": records[i]["source_event_hash"],
                              "q": str(q[i]), "fraction_of_expected_count": finite(q[i] / total) if total else None,
                              **per_event[i]} for i in order[:10]],
            "leading_pair_decomposition": {}, "event_tag_origin_decomposition": {}, "exclusive_category_correlations": {},
        }
        for field, categories in (("leading_pair_types", PAIR_TYPES), ("event_tag_origin_types", EVENT_TYPES)):
            output_key = "leading_pair_decomposition" if field == "leading_pair_types" else "event_tag_origin_decomposition"
            for category in categories:
                chances = [tags.decimal_value(row[stage][field][category]) for row in records]
                count = sum(chances)
                result[output_key][category] = {"expected_count": str(count),
                    "expected_cross_section_pb": str(sum(w * value for w, value in zip(weights, chances))),
                    "fraction_of_expected_count": finite(count / total) if total else None}
            by_category = {category: [tags.decimal_value(row[stage][field][category]) for row in records] for category in categories}
            means = {category: sum(chances) / n for category, chances in by_category.items()}
            matrices = {name: {} for name in ("conditional_count_covariance", "conditional_weighted_covariance_pb2",
                                             "pilot_probability_mean_covariance", "pilot_cross_section_mean_covariance_pb2")}
            for first in categories:
                for name in matrices:
                    matrices[name][first] = {}
                for second in categories:
                    a, b = by_category[first], by_category[second]
                    conditional = [x * (1 - x) if first == second else -x * y for x, y in zip(a, b)]
                    pilot_cov = sum((x - means[first]) * (y - means[second]) for x, y in zip(a, b)) / (n * (n - 1))
                    raw_a, raw_b = [n * w * x for w, x in zip(weights, a)], [n * w * y for w, y in zip(weights, b)]
                    sigma_a = sum(raw_a) / n
                    sigma_b = sum(raw_b) / n
                    weighted_pilot_cov = sum((x - sigma_a) * (y - sigma_b) for x, y in zip(raw_a, raw_b)) / (n * (n - 1))
                    for name, value in (("conditional_count_covariance", sum(conditional)),
                                        ("conditional_weighted_covariance_pb2", sum(w*w*v for w, v in zip(weights, conditional))),
                                        ("pilot_probability_mean_covariance", pilot_cov),
                                        ("pilot_cross_section_mean_covariance_pb2", weighted_pilot_cov)):
                        matrices[name][first][second] = str(value)
            tags.require(abs(sum(Decimal(value) for row in matrices["conditional_count_covariance"].values() for value in row.values()) - conditional_tag_var) <= Decimal("1e-44"),
                         "exclusive category covariance does not recover total tag variance")
            result["exclusive_category_correlations"][output_key] = {"matrices": matrices,
                "scope": "categories are mutually exclusive per original tag outcome; off-diagonal conditional covariance=-sum(r_a*r_b); sum all covariance entries for total variance, never sum diagonals alone"}
        matches = [i for i, row in enumerate(records) if row["source_event_index"] == target]
        if matches:
            i = matches[0]
            remaining_count = total - q[i]
            remaining_sigma = cross_section - weights[i] * q[i]
            result["leave_one_out_diagnostic"] = {
                "source_event_index": target, "individual_q": str(q[i]),
                "fraction_of_total_expected_count": finite(q[i] / total) if total else None,
                "remaining_event_count": len(records) - 1, "remaining_fixed_pilot_expected_count": str(remaining_count),
                "remaining_cross_section_original_N_denominator_pb": str(remaining_sigma),
                "remaining_mean_probability": str(remaining_count / (n - 1)),
                "remaining_raw_integrand_mean_pb": str(remaining_sigma * n / (n - 1)),
                "interpretation": "DIAGNOSTIC_ONLY: original all-event result remains authoritative; neither subtraction nor the rescaled remaining-event mean is a corrected physical prediction",
            }
        return result


def analyze_profile(rows, *, expected_events=1000):
    tags.require(len(rows) == expected_events, "complete original source pilot required")
    records, seen = [], set()
    with localcontext() as context:
        context.prec = 60
        for ordinal, row in enumerate(rows, 1):
            tags.require(row["source_event_index"] == row["ordinal"] == row["native_event_number"] == ordinal and
                         row["source_event_hash"] not in seen, "duplicate/missing original source identity")
            seen.add(row["source_event_hash"])
            frozen = tags.analyze_event(row, {"baseline": tags.SCENARIOS["baseline"]}, expected_events)
            jets = [jet for jet in tags.sorted_objects(row["jets"]) if tags.jet_eligible(jet)]
            parts = event_decomposition(jets, frozen["cut_jets"])
            tags.require(abs(parts["q"] - Decimal(frozen["scenarios"]["baseline"]["stage_two_tags_probability"])) <= Decimal("1e-44"),
                         "frozen probability differs from flavour decomposition")
            record = {key: frozen[key] for key in ("source_event_index", "source_event_hash", "input_hepmc_event_hash", "source_contribution_pb")}
            record.update(eligible_native_jet_flavours=[jet["flavor"] for jet in jets],
                          observed_two_tags=frozen["observed_two_tags"], observed_mgg=frozen["observed_mgg"])
            for stage, passed in (("two_tags", True), ("mgg", frozen["tag_independent_mgg"])):
                record[stage] = {"q": str(parts["q"] if passed else ZERO),
                    "leading_pair_types": {key: str(value if passed else ZERO) for key, value in parts["leading_pair_types"].items()},
                    "event_tag_origin_types": {key: str(value if passed else ZERO) for key, value in parts["event_tag_origin_types"].items()}}
            records.append(record)
        statistics = {stage: stage_statistics(records, stage) for stage in ("two_tags", "mgg")}
    return {"statistics": statistics, "records": records}


def analyze(pilot_dir, output):
    protected = [pilot_dir / name for name in ("extraction.json", *[p + s for p in PROFILES for s in (".jsonl", "_binding.json")])]
    protected += [pilot_dir.parent / "input_verification.json", REPO / "metadata/phase6c_detector_manifest.json",
                  REPO / "simulation/rare_backgrounds/evidence/results/analysis.json", Path(__file__), Path(tags.__file__), Path(pilot.__file__)]
    protected += [REPO / "reference_samples/mg5" / pilot.MG_PROCESSES[profile] / "sample_manifest.json" for profile in PROFILES]
    before = {path: tags.file_sha256(path) for path in protected}
    pilot.validate_inputs(pilot_dir)
    reference = pilot.load(REPO / "simulation/rare_backgrounds/evidence/results/analysis.json")
    tags.require(not output.exists(), "output exists; preserve previous evidence")
    output.mkdir(parents=True)
    result = {"schema_version": 1, "status": "PARTIAL", "base_head": BASE,
        "scope": "existing all1000 pilot per process; native flavour diagnostic, no physical recalibration or stitching",
        "new_independent_physics_events": 0, "normalization_denominator": 1000,
        "authoritative_events_removed_or_corrected": 0, "model": "frozen Phase6D conditional tag model and persisted selections",
        "input_sha256": {path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.name: digest
                         for path, digest in before.items() if path != Path(__file__)},
        "source_sha256": tags.file_sha256(__file__), "samples": {}}
    try:
        for profile in PROFILES:
            rows = [json.loads(raw, parse_float=Decimal, parse_constant=tags.reject_constant)
                    for raw in (pilot_dir / (profile + ".jsonl")).read_text(encoding="utf-8").splitlines()]
            analysis = analyze_profile(rows)
            for stage, summary in analysis["statistics"].items():
                previous = reference["samples"][profile]["scenarios"]["baseline"][stage]
                tags.require(math.isclose(float(summary["expected_count"]), previous["conditional_tag"]["expected_count"], rel_tol=2e-14) and
                             math.isclose(float(summary["expected_cross_section_pb"]), previous["conditional_tag"]["expected_weighted_cross_section_pb"], rel_tol=2e-14),
                             "authoritative Phase6D cross section/probability changed")
            records_path = output / (profile + "_event_influence.jsonl")
            records_path.write_text("".join(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n" for row in analysis["records"]), encoding="utf-8")
            result["samples"][profile] = {"statistics": analysis["statistics"], "all_event_contributions": {
                "file": records_path.name, "events": 1000, "sha256": tags.file_sha256(records_path),
                "publication": "LOCAL_FULL_TABLE; small public summaries/top10 and exact source997 contribution are selected"}}
        tags.require(all(tags.file_sha256(path) == digest for path, digest in before.items()), "input/source bytes changed during influence analysis")
        result["status"] = "PASS"
        (output / "influence.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        with (output / "flavour_decomposition.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(("process", "stage", "partition", "category", "expected_count", "expected_cross_section_pb", "fraction", "interpretation"))
            for profile, sample in result["samples"].items():
                for stage, summary in sample["statistics"].items():
                    for partition in ("leading_pair_decomposition", "event_tag_origin_decomposition"):
                        for category, value in summary[partition].items():
                            writer.writerow((profile, stage, partition, category, value["expected_count"], value["expected_cross_section_pb"], value["fraction_of_expected_count"], "DELPHES_ASSOCIATED_FLAVOUR_DIAGNOSTIC_ONLY"))
        return result
    except Exception as error:
        (output / "partial_status.json").write_text(json.dumps({"status": "PARTIAL", "error": str(error)}, indent=2) + "\n", encoding="utf-8")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, default=REPO / "simulation/rare_backgrounds/evidence/pilot")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.pilot_dir, args.output)
    print(json.dumps({"status": result["status"], "original_source_events": 3000, "new_physics_events": 0,
                      "output": str(args.output), "influence_sha256": tags.file_sha256(args.output / "influence.json")}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Reproduce a bounded numerical study of existing, verified full1000 inputs.

This command reads published ROOT-derived tables. It performs no simulation,
installation, calibration, ROOT writing, Git operation or sample production.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import importlib.util
import json
import math
from pathlib import Path
import sys

import conditional_tags as tags

MODULE_DIR = Path(__file__).resolve().parent
REPO = MODULE_DIR.parents[2]
spec = importlib.util.spec_from_file_location("phase6d_event_statistics", MODULE_DIR / "statistics.py")
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)
PROFILES = ("bbgg", "ccgg", "jjgg")
MG_PROCESSES = {"bbgg": "pp_bbgg_sm_lo_13tev", "ccgg": "pp_ccgg_sm_lo_13tev", "jjgg": "pp_jjgg_light_sm_lo_13tev"}


def sha(path):
    return tags.file_sha256(path)


def load(path, cap=5 * 1024**2):
    tags.require(path.is_file() and path.stat().st_size <= cap, "missing/oversized evidence: " + path.name)
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=tags.reject_constant)


def source_normalization(profile, binding):
    path = REPO / "reference_samples/mg5" / MG_PROCESSES[profile] / "sample_manifest.json"
    matches = [row for row in load(path)["samples"] if row["compressed_file_sha256"] == binding["source_mg5_sha256"]]
    tags.require(len(matches) == 1 and matches[0]["actual_events"] == 1000, "original MG5 full1000 receipt identity mismatch")
    source = matches[0]
    tags.require(source["generator_cross_section_pb"] == binding["input_generator_cross_section_pb"],
                 "original generator cross section mismatch")
    return {"printed_cross_section_pb": str(source["generator_cross_section_pb"]),
            "reported_integration_error_pb": str(source["cross_section_uncertainty_pb"]),
            "source_manifest": path.relative_to(REPO).as_posix(), "source_manifest_sha256": sha(path),
            "scope": "original MG5 run integration receipt; fixed source normalization, reported separately, no covariance evidence for quadrature combination"}


def concentration(events, key):
    """Contribution concentration is not an independent-event effective count."""
    with localcontext() as context:
        context.prec = 60
        values = [(Decimal(row["scenarios"]["baseline"][key]), row) for row in events]
        total = sum(value for value, _ in values)
        squares = sum(value * value for value, _ in values)
        top = sorted(values, key=lambda item: (-item[0], item[1]["source_event_index"]))[:10]
        return {
            "sum_q": float(total), "sum_q_squared": float(squares),
            "contribution_concentration_ratio": float(total * total / squares) if squares else None,
            "ratio_interpretation": "(sum q)^2/sum(q^2) describes yield concentration only; not new independent events or a confidence interval",
            "maximum_contribution_fraction": float(top[0][0] / total) if total else None,
            "top_contributing_source_events": [{
                "source_event_index": row["source_event_index"], "source_event_hash": row["source_event_hash"],
                "input_hepmc_event_hash": row["input_hepmc_event_hash"], "probability": str(value),
                "fraction_of_expected_count": float(value / total) if total else None,
            } for value, row in top if value],
            "limitation": "unseen rare kinematics and a single shower/reconstruction per source event remain unresolved",
        }


def probability_storage_bound(pilot):
    """Conservative rounding bound on baseline counts for retained Float_t pT.

    Every positive normal Float32 value has a pre-rounding interval within
    PT*(1 +/- 2^-23). Derivative bounds enclose the literal card probabilities.
    A coupling bounds the change of any event tag probability by sum |delta p|.
    This does not recover hidden actual pT or change eligible jet membership.
    """
    bounds = {"two_tags": 0.0, "mgg": 0.0}
    for row in pilot:
        if not row["cut_jets"]:
            continue
        error = 0.0
        for jet in row["jets"]:
            pt = float(jet["pt"])
            if not (pt > 25 and abs(float(jet["eta"])) < 2.5):
                continue
            delta = pt * 2**-23
            lo = pt - delta
            flavor = jet["flavor"]
            if flavor == 5:
                derivative_bound = 24 * (.003 / (1 + .086 * lo) + .086 / (1 + .086 * lo)**2)
            elif flavor == 4:
                derivative_bound = .2 * (.02 / (1 + .0034 * lo) + .0034 / (1 + .0034 * lo)**2)
            else:
                derivative_bound = 7.3e-6
            error += derivative_bound * delta
        bounds["two_tags"] += error
        if row["m_gamma_gamma"] is not None and 105 <= float(row["m_gamma_gamma"]) <= 160:
            bounds["mgg"] += error
    return {"baseline_expected_count_absolute_bounds": bounds,
            "method": "Float32 pre-rounding PT relative enclosure 2^-23; literal-card derivative envelope; Bernoulli coupling union bound",
            "scope": "probability evaluation only, with fixed persisted selection, native flavor and eligible jet membership",
            "hidden_full_precision_pt_recovered": False}


def validate_inputs(pilot_dir):
    extraction = load(pilot_dir / "extraction.json")
    verification_path = pilot_dir.parent / "input_verification.json"
    verification = load(verification_path)
    historical = load(REPO / "metadata/phase6c_detector_manifest.json")
    tags.require(extraction["status"] == verification["status"] == "PASS" and
                 extraction["actual_ROOT_entries_read"] == 3000 and
                 extraction["new_physics_events_generated"] == 0,
                 "actual complete existing ROOT extraction receipt required")
    tags.require(sha(verification_path) == extraction["verification_receipt_sha256"], "native verification receipt hash mismatch")
    pins = {row["process"]: row for row in historical["full1000_local_runs"]}
    extracted = {row["process"]: row for row in extraction["samples"]}
    verified = {row["process"]: row for row in verification["samples"]}
    tags.require(set(extracted) == set(verified) == set(PROFILES) and
                 len(extraction["samples"]) == len(verification["samples"]) == 3, "incomplete/duplicate process extraction")
    for profile in PROFILES:
        path, binding_path = pilot_dir / (profile + ".jsonl"), pilot_dir / (profile + "_binding.json")
        binding = load(binding_path)
        tags.validate_binding(binding, path)
        proof, pin = extracted[profile], pins[profile]
        tags.require(binding["process"] == profile and proof["events"] == 1000 and
                     proof["ROOT_physical_readback"] == "PASS" and
                     path.stat().st_size == proof["bytes"] <= 2 * 1024**2 and
                     sha(path) == proof["sha256"] and sha(binding_path) == proof["binding_sha256"],
                     "pilot extraction byte/process binding mismatch")
        for binding_key, pin_key in (("root_sha256", "root_sha256"),
                                     ("native_scientific_content_sha256", "scientific_content_sha256"),
                                     ("runtime_card_sha256", "runtime_card_sha256"),
                                     ("native_report_sha256", "native_report_sha256")):
            tags.require(binding[binding_key] == pin[pin_key], "historical full1000 input identity mismatch")
        proof = verified[profile]
        tags.require(proof["status"] == "PASS" and proof["events"] == proof["normalization_denominator"] == 1000 and
                     proof["new_physics_events_generated"] == 0 and not proof["root_binary_rewritten"],
                     "incomplete original ROOT readback scope")
        for key in ("root_sha256", "native_report_sha256", "native_scientific_content_sha256", "runtime_card_sha256", "source_mg5_sha256", "source_pythia_run_id"):
            tags.require(binding[key] == proof[key], "original ROOT/source receipt binding mismatch")
        source_normalization(profile, binding)
    return extraction, verification


def run(pilot_dir, output):
    protected_paths = [pilot_dir / name for name in ("extraction.json", *[profile + suffix for profile in PROFILES for suffix in (".jsonl", "_binding.json")])]
    protected_paths += [pilot_dir.parent / "input_verification.json", REPO / "metadata/phase6c_detector_manifest.json"]
    protected_paths += [REPO / "reference_samples/mg5" / MG_PROCESSES[profile] / "sample_manifest.json" for profile in PROFILES]
    protected_paths += [MODULE_DIR / name for name in ("analyze_pilot.py", "conditional_tags.py", "statistics.py")]
    before_hashes = {path: sha(path) for path in protected_paths}
    extraction, verification = validate_inputs(pilot_dir)
    tags.require(not output.exists(), "output must be a new directory; existing evidence is not overwritten")
    output.mkdir(parents=True)
    result = {
        "schema_version": 1, "status": "PARTIAL", "study": "PHASE6D_RARE_BACKGROUND_STATISTICS_AND_SYSTEMATICS_V1",
        "base_head": "5e7a9522e08e50d99b1a166789500a4039c3e9b1",
        "existing_input_only": True, "new_independent_physics_events": 0,
        "variation_label": "TOY_MODEL_SENSITIVITY_ONLY", "official_ATLAS_systematics": "NOT_EVALUATED",
        "input_verification_sha256": extraction["verification_receipt_sha256"],
        "extraction_receipt_sha256": sha(pilot_dir / "extraction.json"),
        "source_sha256": {name: sha(MODULE_DIR / name) for name in ("analyze_pilot.py", "conditional_tags.py", "statistics.py")},
        "selection": "existing native photon/jet selection, Flavor-based BTag bit0 >=2, closed105..160 GeV mgg; no mbb window",
        "normalization": "sum original signed source contribution_pb * event probability; original1000 denominator; no luminosity or new normalization",
        "samples": {},
    }
    try:
        for profile in PROFILES:
            source, binding = pilot_dir / (profile + ".jsonl"), pilot_dir / (profile + "_binding.json")
            summary = tags.analyze_file(source, binding, output / profile)
            rows = [json.loads(line) for line in (output / profile / "conditional_events.jsonl").read_text(encoding="utf-8").splitlines()]
            pilot = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
            weights = [row["source_contribution_pb"] for row in rows]
            analyses = {}
            for scenario in tags.SCENARIOS:
                stages = {name: stats.analyze_stage(rows, key, observed, scenario=scenario)
                          for name, key, observed in (("two_tags", "stage_two_tags_probability", "observed_two_tags"),
                                                      ("mgg", "stage_mgg_probability", "observed_mgg"))}
                stages["nested_stage_covariance"] = stats.nested_stage_covariance(
                    [row["scenarios"][scenario]["stage_two_tags_probability"] for row in rows],
                    [row["scenarios"][scenario]["stage_mgg_probability"] for row in rows], weights)
                for stage in ("two_tags", "mgg"):
                    stages[stage]["exact_observed_interval"]["data_scope"] = "unchanged nominal observed tag counts; not a confidence interval for altered toy-model acceptance"
                    stages[stage]["forecasts"]["conservative_observed_scope"] = "unchanged nominal CP lower bound; toy-model acceptance receives no observed confidence interval"
                    expected = float(summary["results"][scenario][stage]["expected_count"])
                    tags.require(math.isclose(expected, stages[stage]["conditional_tag"]["expected_count"], rel_tol=1e-14),
                                 "independent probability summations disagree")
                analyses[scenario] = stages
            baseline = analyses["baseline"]
            toys = {name: {stage: {
                "expected_count": values[stage]["conditional_tag"]["expected_count"],
                "fractional_change_from_baseline": values[stage]["conditional_tag"]["expected_count"] /
                    baseline[stage]["conditional_tag"]["expected_count"] - 1,
            } for stage in ("two_tags", "mgg")} for name, values in analyses.items() if name != "baseline"}
            result["samples"][profile] = {
                "counts": summary["counts"], "binding": summary["binding"],
                "original_nominal_weight_sum_pb": summary["weight_sum_pb"],
                "original_source_normalization": source_normalization(profile, summary["binding"]),
                "conditional_summary_sha256": sha(output / profile / "conditional_summary.json"),
                "conditional_events_sha256": summary["conditional_events_sha256"],
                "scenarios": analyses, "toy_sensitivity": toys,
                "concentration": {stage: concentration(rows, key) for stage, key in
                    (("two_tags", "stage_two_tags_probability"), ("mgg", "stage_mgg_probability"))},
                "persisted_pt_rounding": probability_storage_bound(pilot),
                "mass_pair_moments": "see conditional_summary: exact leading tagged-pair combination probabilities, not the observed pair; no optimized mass cut",
            }
        tags.require(all(sha(path) == digest for path, digest in before_hashes.items()),
                     "protected pilot/provenance/source bytes changed during numerical study")
        result["protected_input_source_bytes_unchanged"] = True
        result["status"] = "PASS"
        (output / "analysis.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return result
    except Exception as error:
        (output / "partial_status.json").write_text(json.dumps({"status": "PARTIAL", "error": str(error)}, indent=2) + "\n", encoding="utf-8")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new local numerical output directory")
    args = parser.parse_args()
    result = run(args.pilot_dir, args.output)
    print(json.dumps({"status": result["status"], "events": 3000, "new_physics_events": 0,
                      "analysis_sha256": sha(args.output / "analysis.json"), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        raise SystemExit(1)

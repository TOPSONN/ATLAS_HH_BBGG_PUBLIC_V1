#!/usr/bin/env python3
"""Conditional study of pinned Delphes bit-0 tags; no detector event generation.

Probabilities condition on the verified persisted reconstruction and assume
independent per-jet Bernoulli tagging. Toy multipliers are not calibration errors.
Decimal arithmetic retains signed original source contributions without renorm.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import re
import sys

PRECISION = 50
ZERO, ONE = Decimal(0), Decimal(1)
CARD_SHA256 = "cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47"
RUNTIME_CARD_SHA256 = {
    "bbgg": CARD_SHA256,
    "ccgg": "5507d5a49492512aa454193c3b1de007933050bf91d50c11caf751618b8a3522",
    "jjgg": "762d5ff5f44b3f41783b086636df53c3c563e9ad673afd867d64926ae0b6f134",
}
SCENARIOS = {
    "baseline": {"b": "1", "c": "1", "light": "1"},
    "b_down20": {"b": ".8", "c": "1", "light": "1"},
    "b_up20": {"b": "1.2", "c": "1", "light": "1"},
    "c_down20": {"b": "1", "c": ".8", "light": "1"},
    "c_up20": {"b": "1", "c": "1.2", "light": "1"},
    "light_down20": {"b": "1", "c": "1", "light": ".8"},
    "light_up20": {"b": "1", "c": "1", "light": "1.2"},
    "joint_down20": {"b": ".8", "c": ".8", "light": ".8"},
    "joint_up20": {"b": "1.2", "c": "1.2", "light": "1.2"},
}
HASH = re.compile(r"[0-9a-f]{64}\Z")
MAX_RECORD_BYTES = 2 * 1024**2


def require(ok, message):
    if not ok:
        raise ValueError(message)


def decimal_value(value):
    require(not isinstance(value, bool), "boolean is not a numerical value")
    result = value if isinstance(value, Decimal) else Decimal(str(value))
    require(result.is_finite(), "non-finite numerical value")
    return result


def finite_float(value):
    result = float(decimal_value(value))
    require(math.isfinite(result), "value outside binary64 range")
    return result


def flavor_category(flavor):
    require(isinstance(flavor, int) and not isinstance(flavor, bool), "Flavor must be a persisted integer")
    if flavor == 5:
        return "b"
    if flavor == 4:
        return "c"
    require(flavor in (0, 1, 2, 3, 21), "unsupported persisted Jet.Flavor")
    return "light"


def tag_probability_details(flavor, pt, multipliers=None):
    category = flavor_category(flavor)
    pt = finite_float(pt)
    require(pt >= 0, "negative jet PT")
    # Literal pinned card formulas, using persisted Float_t PT. The actual
    # Delphes draw used its preceding full-precision Momentum.Pt(); this is a
    # explicitly recorded small storage-rounding approximation, not recovery
    # of the exact hidden per-draw probability.
    if category == "b":
        raw = .80 * math.tanh(.003 * pt) * (30 / (1 + .086 * pt))
    elif category == "c":
        raw = .20 * math.tanh(.02 * pt) * (1 / (1 + .0034 * pt))
    else:
        raw = .002 + 7.3e-06 * pt
    factor = decimal_value((multipliers or SCENARIOS["baseline"])[category])
    require(factor >= 0, "negative toy probability multiplier")
    with localcontext() as context:
        context.prec = PRECISION
        scaled = Decimal(str(raw)) * factor
        probability = min(ONE, max(ZERO, scaled))
    return {"category": category, "baseline_raw": Decimal(str(raw)),
            "multiplier": factor, "scaled_raw": scaled, "probability": probability,
            "clipped": scaled != probability}


def tag_probability(flavor, pt, multipliers=None):
    return tag_probability_details(flavor, pt, multipliers)["probability"]


def probability_at_least_two(probabilities):
    """Direct three-state Poisson-binomial DP: 0, 1, and >=2 tags.

    The >=2 tail is accumulated through 1->2 transitions. It is never obtained
    through 1-P(0)-P(1), which loses small rare-background probabilities.
    """
    with localcontext() as context:
        context.prec = PRECISION
        p0, p1, tail = ONE, ZERO, ZERO
        for value in probabilities:
            p = decimal_value(value)
            require(ZERO <= p <= ONE, "Bernoulli probability outside [0,1]")
            tail, p1, p0 = tail + p1 * p, p1 * (ONE - p) + p0 * p, p0 * (ONE - p)
        return +tail


def leading_pair_probabilities(probabilities):
    """Exact probabilities for the two leading tagged indices, already PT sorted.

    For a<b: p[a]p[b] product(1-p[k], k<b except a). Tags after b are
    unrestricted. No division by (1-p) is used, so deterministic tags work.
    """
    p = [decimal_value(value) for value in probabilities]
    require(len(p) <= 512, "leading-pair study exceeds bounded eligible-jet limit512")
    require(all(ZERO <= value <= ONE for value in p), "Bernoulli probability outside [0,1]")
    with localcontext() as context:
        context.prec = PRECISION
        result, earlier_fail = [], ONE
        for a, value in enumerate(p):
            middle_fail = ONE
            for b in range(a + 1, len(p)):
                probability = value * p[b] * earlier_fail * middle_fail
                if probability:
                    result.append((a, b, +probability))
                middle_fail *= ONE - p[b]
            earlier_fail *= ONE - value
        return result


def p4(obj, photon=False):
    pt, eta, phi = (finite_float(obj[key]) for key in ("pt", "eta", "phi"))
    mass = 0.0 if photon else finite_float(obj["mass"])
    require(pt >= 0, "negative persisted PT")
    x, y, z = pt * math.cos(phi), pt * math.sin(phi), pt * math.sinh(eta)
    p2 = math.fsum((x*x, y*y, z*z))
    signed_m2 = mass * abs(mass)
    require(mass >= 0 or -signed_m2 <= 16 * sys.float_info.epsilon * p2,
            "signed native jet mass exceeds pinned double-cancellation bound")
    energy2 = p2 + signed_m2
    require(energy2 >= 0, "negative native E squared")
    return x, y, z, math.sqrt(energy2)


def combined_mass(vectors):
    x, y, z, energy = (math.fsum(v[k] for v in vectors) for k in range(4))
    momentum = math.hypot(x, y, z)
    m2 = (energy - momentum) * (energy + momentum)
    require(m2 >= -64 * sys.float_info.epsilon * max(energy * energy, 1),
            "unphysical combined Cartesian four-vector")
    return math.sqrt(max(m2, 0))


def photon_eligible(obj):
    pt, eta = finite_float(obj["pt"]), abs(finite_float(obj["eta"]))
    return pt > 25 and eta < 2.37 and not (1.37 < eta < 1.52)


def jet_eligible(obj):
    return finite_float(obj["pt"]) > 25 and abs(finite_float(obj["eta"])) < 2.5


def sorted_objects(objects):
    require(isinstance(objects, list) and len(objects) <= 4096, "invalid/oversized object list")
    indices = [obj["index"] for obj in objects]
    require(all(isinstance(index, int) and not isinstance(index, bool) and index >= 0 for index in indices)
            and len(indices) == len(set(indices)), "invalid/duplicate native object index")
    return sorted(objects, key=lambda obj: (-finite_float(obj["pt"]), obj["index"]))


def leading_pair_moments(jets, photons, probabilities):
    with localcontext() as context:
        context.prec = PRECISION
        totals = {"probability": ZERO, "mbb_first": ZERO, "mbb_second": ZERO,
                  "mbbgg_first": ZERO, "mbbgg_second": ZERO}
        jet_vectors = [p4(jet) for jet in jets]
        gamma_vectors = [p4(photon, True) for photon in photons[:2]]
        for a, b, probability in leading_pair_probabilities(probabilities):
            mbb = Decimal(str(combined_mass([jet_vectors[a], jet_vectors[b]])))
            totals["probability"] += probability
            totals["mbb_first"] += probability * mbb
            totals["mbb_second"] += probability * mbb * mbb
            if len(gamma_vectors) == 2:
                mbbgg = Decimal(str(combined_mass([jet_vectors[a], jet_vectors[b], *gamma_vectors])))
                totals["mbbgg_first"] += probability * mbbgg
                totals["mbbgg_second"] += probability * mbbgg * mbbgg
        tail = probability_at_least_two(probabilities)
        require(abs(totals["probability"] - tail) <= Decimal("1e-44"), "leading-pair probabilities do not normalize to >=2 tail")
        totals["conditional_mean_mbb"] = totals["mbb_first"] / tail if tail else None
        totals["conditional_mean_mbbgg"] = totals["mbbgg_first"] / tail if tail and len(gamma_vectors) == 2 else None
        return totals


def analyze_event(row, scenarios=None, source_count=1000):
    """Analyze one source-bound reconstruction; retain zero-probability events."""
    require(isinstance(source_count, int) and source_count > 0, "invalid original source count")
    scenarios = SCENARIOS if scenarios is None else scenarios
    weight = decimal_value(row["source_contribution_pb"])
    jets = [obj for obj in sorted_objects(row["jets"]) if jet_eligible(obj)]
    photons = [obj for obj in sorted_objects(row["photons"]) if photon_eligible(obj)]
    require(len(jets) <= 512, "too many eligible jets for bounded pair study")
    photon_cut = len(photons) >= 2 and finite_float(photons[0]["pt"]) > 35
    jet_cut = photon_cut and len(jets) >= 2
    for key, actual in (("cut_photons", photon_cut), ("cut_jets", jet_cut)):
        require(isinstance(row[key], bool) and row[key] == actual, "persisted cut differs from frozen selection: " + key)
    tagged = 0
    for obj in jets:
        flavor_category(obj["flavor"])
        require(isinstance(obj["btag"], int) and not isinstance(obj["btag"], bool)
                and obj["btag"] in (0, 1), "unexpected persisted tagging bits")
        tagged += bool(obj["btag"] & 1)
    if "N_jets" in row:
        require(row["N_jets"] == len(jets), "persisted eligible jet count mismatch")
    if "N_btags" in row:
        require(row["N_btags"] == tagged, "persisted tag count mismatch")
    mass = row["m_gamma_gamma"]
    if len(photons) >= 2:
        require(mass is not None, "missing source-bound diphoton mass")
        mass_cut = Decimal(105) <= decimal_value(mass) <= Decimal(160)
    else:
        require(mass is None, "diphoton mass present without two eligible photons")
        mass_cut = False
    observed = jet_cut and tagged >= 2
    require(isinstance(row["cut_two_btags"], bool) and row["cut_two_btags"] == observed,
            "persisted observed two-tag flag mismatch")
    require(isinstance(row["cut_mgg"], bool) and row["cut_mgg"] == (observed and mass_cut),
            "persisted tagged diphoton flag mismatch")
    result = {key: row[key] for key in ("ordinal", "native_event_number", "source_event_index",
                                       "source_event_hash", "input_hepmc_event_hash")}
    if "native_physics_branches_sha256" in row:
        result["native_physics_branches_sha256"] = row["native_physics_branches_sha256"]
    result.update(source_count=source_count, source_contribution_pb=str(weight),
                  cut_photons=photon_cut, cut_jets=jet_cut, tag_independent_mgg=mass_cut,
                  eligible_jets=len(jets), observed_eligible_tags=tagged,
                  observed_two_tags=observed, observed_mgg=observed and mass_cut, scenarios={})
    for name, multipliers in scenarios.items():
        details = [tag_probability_details(obj["flavor"], obj["pt"], multipliers) for obj in jets]
        probabilities = [value["probability"] for value in details]
        with localcontext() as context:
            context.prec = PRECISION
            q = probability_at_least_two(probabilities) if jet_cut else ZERO
            moments = leading_pair_moments(jets, photons, probabilities) if jet_cut else {
                "probability": ZERO, "mbb_first": ZERO, "mbb_second": ZERO,
                "mbbgg_first": ZERO, "mbbgg_second": ZERO,
                "conditional_mean_mbb": None, "conditional_mean_mbbgg": None}
        result["scenarios"][name] = {"stage_two_tags_probability": str(q),
                                      "stage_mgg_probability": str(q if mass_cut else ZERO),
                                      "clipped_eligible_jet_probabilities": sum(value["clipped"] for value in details),
                                      "leading_pair_moments": {key: str(value) if value is not None else None
                                                               for key, value in moments.items()}}
    return result


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reject_constant(value):
    raise ValueError("non-finite JSON constant: " + value)


def iter_analysis_events(path, scenarios=None, source_count=1000):
    seen_source_hashes, seen_hepmc_hashes = set(), set()
    with Path(path).open("rb") as stream:
        ordinal = 0
        while raw := stream.readline(MAX_RECORD_BYTES + 1):
            require(len(raw) <= MAX_RECORD_BYTES and raw.endswith(b"\n"), "oversized/truncated reconstruction record")
            row = json.loads(raw, parse_float=Decimal, parse_constant=reject_constant)
            ordinal += 1
            require(ordinal <= source_count and row["ordinal"] == row["native_event_number"] == row["source_event_index"] == ordinal,
                    "source ordinal/event-number mismatch; no missing/repeated rows are allowed")
            for key, seen in (("source_event_hash", seen_source_hashes), ("input_hepmc_event_hash", seen_hepmc_hashes)):
                require(isinstance(row[key], str) and HASH.fullmatch(row[key]) and row[key] not in seen,
                        "invalid/duplicate event identity: " + key)
                seen.add(row[key])
            yield analyze_event(row, scenarios, source_count)
        require(ordinal == source_count, "analysis must retain every original source event")


def validate_binding(binding, path):
    require(binding["schema_version"] == 1 and binding["process"] in RUNTIME_CARD_SHA256, "unsupported input binding schema/process")
    require(binding["events"] == binding["normalization_denominator"] == 1000, "this pilot requires the full original1000 denominator")
    require(binding["verification_status"] == "PASS" and
            binding["verification_scope"] == "actual_ROOT_native_source_card_full_file_hash", "missing physical ROOT/source verification")
    require(binding["canonical_card_sha256"] == CARD_SHA256 and
            binding["runtime_card_sha256"] == RUNTIME_CARD_SHA256[binding["process"]], "unreviewed detector card")
    for key in ("reco_sha256", "root_sha256", "native_report_sha256", "native_scientific_content_sha256", "source_mg5_sha256"):
        require(isinstance(binding[key], str) and HASH.fullmatch(binding[key]), "invalid provenance hash: " + key)
    require(isinstance(binding["source_pythia_run_id"], str) and binding["source_pythia_run_id"], "missing Pythia run identity")
    require(file_sha256(path) == binding["reco_sha256"], "reconstruction input SHA256 mismatch")


def serializable_record(event):
    # Event-wise q/weights remain at full Decimal precision. Mass moments are
    # aggregated separately to keep the portable1000-row evidence bounded.
    return {**event, "scenarios": {name: {key: value for key, value in values.items()
                                            if key != "leading_pair_moments"}
                                    for name, values in event["scenarios"].items()}}


def analyze_file(path, binding_path, output):
    path, binding_path, output = Path(path), Path(binding_path), Path(output)
    binding = json.loads(binding_path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    validate_binding(binding, path)
    binding_hash = file_sha256(binding_path)
    require(not output.exists(), "analysis output directory already exists")
    output.mkdir(parents=True)
    counts = {"events": 0, "after_photons": 0, "after_jets": 0, "observed_two_tags": 0, "observed_mgg": 0}
    totals = {name: {stage: {"expected_count": ZERO, "weighted_cross_section_pb": ZERO,
                             "mbb_first_weighted": ZERO, "mbb_second_weighted": ZERO,
                             "mbbgg_first_weighted": ZERO, "mbbgg_second_weighted": ZERO}
                     for stage in ("two_tags", "mgg")} for name in SCENARIOS}
    clipped = {name: 0 for name in SCENARIOS}
    weight_sum = abs_sum = weight_squared = ZERO
    negative = zero = 0
    try:
        with localcontext() as context, (output / "conditional_events.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
            context.prec = PRECISION
            for event in iter_analysis_events(path, source_count=binding["normalization_denominator"]):
                counts["events"] += 1
                counts["after_photons"] += event["cut_photons"]
                counts["after_jets"] += event["cut_jets"]
                counts["observed_two_tags"] += event["observed_two_tags"]
                counts["observed_mgg"] += event["observed_mgg"]
                weight = decimal_value(event["source_contribution_pb"])
                weight_sum += weight
                abs_sum += abs(weight)
                weight_squared += weight * weight
                negative += weight < 0
                zero += weight == 0
                for name, values in event["scenarios"].items():
                    clipped[name] += values["clipped_eligible_jet_probabilities"]
                    for stage, key in (("two_tags", "stage_two_tags_probability"), ("mgg", "stage_mgg_probability")):
                        q = decimal_value(values[key])
                        total = totals[name][stage]
                        total["expected_count"] += q
                        total["weighted_cross_section_pb"] += weight * q
                        if stage == "two_tags" or event["tag_independent_mgg"]:
                            for moment in ("mbb_first", "mbb_second", "mbbgg_first", "mbbgg_second"):
                                total[moment + "_weighted"] += weight * decimal_value(values["leading_pair_moments"][moment])
                stream.write(json.dumps(serializable_record(event), separators=(",", ":"), allow_nan=False) + "\n")
            require(file_sha256(path) == binding["reco_sha256"] and file_sha256(binding_path) == binding_hash,
                    "input/binding changed during analysis")
            for stages in totals.values():
                for total in stages.values():
                    denominator = total["weighted_cross_section_pb"]
                    for quantity in ("mbb", "mbbgg"):
                        total["signed_weight_conditional_mean_" + quantity] = (
                            total[quantity + "_first_weighted"] / denominator if denominator else None)
        summary = {"schema_version": 1, "status": "PASS", "process": binding["process"], "binding": binding,
                   "input_binding_sha256": binding_hash, "counts": counts,
                   "model": "conditional independent per-jet Bernoulli tags on fixed verified persisted reconstruction",
                   "decimal_precision": PRECISION, "probability_algorithm": "direct saturated0/1/>=2 Poisson-binomial DP; no subtraction",
                   "jet_eligibility": "persisted PT>25 GeV and abs(Eta)<2.5; bit0; actual native Flavor",
                   "probability_pt_assumption": "card evaluated at persisted Float_t Jet.PT; upstream tag draw used full-precision Momentum.Pt before tree storage; exact hidden per-draw probability is not recovered",
                   "scenarios": SCENARIOS, "variation_interpretation": "TOY_MODEL_SENSITIVITY_ONLY",
                   "clipped_eligible_jet_probabilities": clipped,
                   "optional_mbb_window": "NOT_EVALUATED; no new cut or small-sample optimization",
                   "mass_moment_definition": "exact leading-tagged-pair probability model; binary64 Cartesian masses with pinned signed native mass convention; signed source-weighted moments; no observed-pair substitution",
                   "weight_sum_pb": str(weight_sum), "weight_abs_sum_pb": str(abs_sum), "weight_sum_squared_pb2": str(weight_squared),
                   "negative_source_weights": negative, "zero_source_weights": zero,
                   "normalization": "sum original signed source contributions*q; denominator remains full original1000; no selected/passing-row renormalization",
                   "results": {name: {stage: {key: str(value) if value is not None else None for key, value in total.items()}
                                            for stage, total in stages.items()} for name, stages in totals.items()},
                   "uncertainty": "NOT_COMPUTED_BY_THIS_MODULE; independent statistics module required",
                   "conditional_events_sha256": file_sha256(output / "conditional_events.jsonl"),
                   "estimator_source_sha256": file_sha256(__file__)}
        (output / "conditional_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        (output / "input_binding.json").write_bytes(binding_path.read_bytes())
        return summary
    except Exception as error:
        (output / "partial_status.json").write_text(json.dumps({"status": "PARTIAL", "error": str(error), "counts": counts}, indent=2) + "\n", encoding="utf-8")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="verified full1000 native/compact reconstruction JSONL")
    parser.add_argument("--binding", type=Path, required=True, help="hash-bound actual ROOT/source/card verification receipt")
    parser.add_argument("--output", type=Path, required=True, help="new local numerical-analysis directory")
    args = parser.parse_args()
    summary = analyze_file(args.input, args.binding, args.output)
    print(json.dumps({"status": summary["status"], "process": summary["process"], "counts": summary["counts"],
                      "output": str(args.output), "conditional_events_sha256": summary["conditional_events_sha256"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, OverflowError, TypeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        raise SystemExit(1)

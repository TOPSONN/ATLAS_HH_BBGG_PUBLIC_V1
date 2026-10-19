#!/usr/bin/env python3
"""Independent event-unit HF moments; reuses persisted labels, no classifier import."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import zip_longest
from pathlib import Path

STAGES = ("00_INPUT", "01_TWO_PHOTONS", "02_TWO_JETS", "03_TWO_BTAGS", "04_MGG_105_160")
DATASETS = ("B01", "B02", "B03")
EXPECTED = {"B01": (1000, 446, 266, 91, 28), "B02": (1000, 378, 241, 7, 1),
            "B03": (1000, 445, 277, 0, 0)}
FLAGS = ("ME_BOTTOM", "ME_CHARM", "ME_LIGHT_OR_GLUON", "HAS_NATIVE_BOTTOM_JET",
         "HAS_NATIVE_CHARM_JET", "NATIVE_TAGS_0", "NATIVE_TAGS_1", "NATIVE_TAGS_GE2",
         "HAS_SHOWER_BOTTOM_BIRTH", "HAS_SHOWER_CHARM_BIRTH",
         "HAS_DIRECT_G_TO_HEAVY_PAIR", "HAS_HEAVY_HADRON_ELIGIBLE_JET")


def frac(value):
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_NOT_WEIGHT")
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError("NONFINITE_MOMENT")
    return Fraction(d)


def close(a, b, tolerance=Fraction(1, 10**10), absolute=Fraction(1, 10**24)):
    a, b = frac(a), frac(b)
    return abs(a-b) <= absolute + tolerance*max(abs(a), abs(b))


def covariance_from_moments(n, sum_a, sum_b, cross_sum):
    if n <= 1:
        raise ValueError("ORIGINAL_SOURCE_N_REQUIRED")
    return Fraction(n, n-1) * (frac(cross_sum) - frac(sum_a)*frac(sum_b)/n)


def ratio_variance(n, selected, selected_square, base, base_square):
    if frac(base) == 0:
        return None
    q = frac(selected)/frac(base)
    # Stage selection is a subset of the unchanged source-level base stratum.
    residual_square = frac(selected_square)*(1-2*q) + q*q*frac(base_square)
    return Fraction(n, n-1)*residual_square/frac(base)**2


def independent_masks(origin, native):
    """ME PDG and native bit0 are recalculated; shower/hadron labels stay persisted."""
    outgoing = {abs(int(x)) for x in origin["hard_outgoing_pdg_ids"]}
    me = "ME_BOTTOM" if 5 in outgoing else "ME_CHARM" if 4 in outgoing else "ME_LIGHT_OR_GLUON"
    h = origin["heavy_flavour"]
    jets = native["eligible_jets"]
    tags = sum(bool(int(j["native_btag_bits"]) & 1) for j in jets)
    return {
        "ME_BOTTOM": me == "ME_BOTTOM", "ME_CHARM": me == "ME_CHARM",
        "ME_LIGHT_OR_GLUON": me == "ME_LIGHT_OR_GLUON",
        "HAS_NATIVE_BOTTOM_JET": any(j["flavour"] == 5 for j in jets),
        "HAS_NATIVE_CHARM_JET": any(j["flavour"] == 4 for j in jets),
        "NATIVE_TAGS_0": tags == 0, "NATIVE_TAGS_1": tags == 1, "NATIVE_TAGS_GE2": tags >= 2,
        "HAS_SHOWER_BOTTOM_BIRTH": h["shower_bottom_births"] > 0,
        "HAS_SHOWER_CHARM_BIRTH": h["shower_charm_births"] > 0,
        "HAS_DIRECT_G_TO_HEAVY_PAIR": h["direct_gluon_splitting_count"] > 0,
        "HAS_HEAVY_HADRON_ELIGIBLE_JET": any(j["heavy_hadron_flavour"] in (4, 5) for j in h["jets"]),
    }


def identity_errors(origin, native):
    errors = []
    for a, b in (("dataset_id", "dataset_id"), ("source_event_index", "source_event_ordinal"),
                 ("source_event_sha256", "source_event_sha256"),
                 ("hepmc_event_sha256", "hepmc_event_sha256"), ("stages", "stages")):
        if origin[a] != native[b]:
            errors.append("IDENTITY_JOIN:" + a)
    if not close(origin["weight_pb"], native["source_weight_pb"], tolerance=Fraction(1, 10**14)):
        errors.append("WEIGHT_JOIN")
    for jet in native["eligible_jets"]:
        if bool(int(jet["native_btag_bits"]) & 1) != jet["tagged"]:
            errors.append("NATIVE_BIT0_DISAGREES")
    h = origin["heavy_flavour"]
    if h is not None:
        left = {j["index"]: j for j in native["eligible_jets"]}
        right = {j["index"]: j for j in h["jets"]}
        if set(left) != set(right):
            errors.append("ELIGIBLE_JET_INDEX_JOIN")
        for key in set(left) & set(right):
            if (left[key]["flavour"], left[key]["tagged"]) != (right[key]["native_flavour"], right[key]["tagged"]):
                errors.append("NATIVE_LABEL_JOIN")
            if right[key]["sole_hadron_endpoint"] != "UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED":
                errors.append("UNKNOWN_ANCESTRY_NOT_PRESERVED")
    return errors


def load_rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(origins, native, hf):
    errors, metrics = [], Counter()

    def check(ok, message):
        metrics["checks"] += 1
        if not ok:
            errors.append(message)

    cohorts = defaultdict(list)
    all_ordinals, all_hashes = defaultdict(list), defaultdict(set)
    with origins.open() as source, native.open() as detector:
        for i, pair in enumerate(zip_longest(source, detector)):
            x, y = pair
            if x is None or y is None:
                raise ValueError("UNEQUAL_SOURCE_COHORT_LENGTHS")
            origin, reco = json.loads(x, parse_float=Decimal), json.loads(y, parse_float=Decimal)
            problems = identity_errors(origin, reco)
            check(not problems, "EVENT_JOIN:" + str(i) + ":" + ",".join(problems))
            ds = origin["dataset_id"]
            all_ordinals[ds].append(origin["source_event_index"])
            all_hashes[ds].add(origin["source_event_sha256"])
            check(all(not origin["stages"][j+1] or origin["stages"][j] for j in range(4)),
                  "NESTED_STAGE_IDENTITY:" + str(i))
            metrics["existing_events_joined"] += 1
            if ds in DATASETS:
                masks = independent_masks(origin, reco)
                me = "ME_BOTTOM" if masks["ME_BOTTOM"] else "ME_CHARM" if masks["ME_CHARM"] else "ME_LIGHT_OR_GLUON"
                check(me == origin["heavy_flavour"]["hard_process_flavour"], "RAW_ME_VS_PERSISTED_ME")
                cohorts[ds].append((frac(reco["source_weight_pb"]), reco["stages"], masks))
                metrics["unknown_endpoint_jets_preserved"] += len(origin["heavy_flavour"]["jets"])
    check(metrics["existing_events_joined"] == 6000, "FULL_EXISTING_6000_JOIN")
    check(set(all_ordinals) == {f"B{i:02}" for i in range(1, 7)}, "SIX_DATASET_IDENTITIES")
    for ds in all_ordinals:
        check(all_ordinals[ds] == list(range(1, 1001)) and len(all_hashes[ds]) == 1000,
              ds + ":EXACT_UNIQUE_1000_SOURCE_COHORT")
    check(sum(map(len, cohorts.values())) == 3000, "HF_THREE_ORIGINAL_COHORTS")

    strata_rows = load_rows(hf/"phase10_hf_strata.csv")
    cov_rows = load_rows(hf/"phase10_hf_covariance.csv")
    summary = json.loads((hf/"phase10_hf_summary.json").read_text())
    strata = {(r["dataset_id"], r["stage"], r["category"]): r for r in strata_rows
              if r["row_type"] == "NONEXCLUSIVE_ORIGIN_FLAG"}
    cov = {(r["dataset_id"], r["stage"], r["flag_a"], r["flag_b"]): r for r in cov_rows}
    check(len(cov_rows) == len(cov) == 6000, "EXACT_6000_UNIQUE_COVARIANCE_ROWS")
    check(len(strata) == 300, "TWENTY_FLAGS_FIFTEEN_COHORT_STAGES")
    for key, row in cov.items():
        ds, stage, a, b = key
        other = cov[(ds, stage, b, a)]
        check(row["statistical_unit"] == "ORIGINAL_SOURCE_EVENT_ALL_JETS_CLUSTERED" and
              row["nonexclusive_flags"] == "True", "EVENT_CLUSTER_NONEXCLUSIVE_POLICY")
        check(int(row["overlap_events"]) == int(other["overlap_events"]) and
              close(row["fixed_N_covariance_pb2"], other["fixed_N_covariance_pb2"]), "COVARIANCE_SYMMETRY")
        ca, cb = int(strata[(ds, stage, a)]["events"]), int(strata[(ds, stage, b)]["events"])
        check(0 <= int(row["overlap_events"]) <= min(ca, cb), "COVARIANCE_OVERLAP_BOUND")
        if a == b:
            check(int(row["overlap_events"]) == ca and
                  close(row["fixed_N_covariance_pb2"], strata[(ds, stage, a)]["fixed_N_variance_pb2"]),
                  "ALL_TWENTY_FLAG_DIAGONALS")
        if row["correlation"]:
            check(abs(frac(row["correlation"])) <= 1 + Fraction(1, 10**10), "CORRELATION_BOUND")
        metrics["covariance_schema_symmetry_rows"] += 1

    for ds in DATASETS:
        records = cohorts[ds]
        n = len(records)
        weights = [e[0] for e in records]
        constant = len(set(weights)) == 1
        metrics["observed_constant_weight_cohorts"] += int(constant)
        base_bits = {name: sum(1 << i for i, e in enumerate(records) if e[2][name]) for name in FLAGS}

        def sums(mask):
            count = mask.bit_count()
            if constant:
                return count, count*weights[0], count*weights[0]**2
            selected = [weights[i] for i in range(n) if mask & (1 << i)]
            return count, sum(selected, Fraction()), sum((w*w for w in selected), Fraction())

        for si, stage in enumerate(STAGES):
            stage_bits = sum(1 << i for i, e in enumerate(records) if e[1][si])
            check(stage_bits.bit_count() == EXPECTED[ds][si], ds + ":HISTORICAL_STAGE_CUTFLOW")
            check(summary["datasets"][ds]["stages"][stage]["events"] == stage_bits.bit_count(),
                  ds + ":SUMMARY_STAGE_IDENTITY")
            selected_bits = {f: base_bits[f] & stage_bits for f in FLAGS}
            moments = {f: sums(selected_bits[f]) for f in FLAGS}
            for name in FLAGS:
                count, total, square = moments[name]
                row = strata[(ds, stage, name)]
                var = covariance_from_moments(n, total, total, square)
                check(int(row["original_N"]) == n and int(row["events"]) == count, "SELECTED_FLAG_EVENT_N")
                check(close(row["sumw_pb"], total) and close(row["sumw2_pb2"], square) and
                      close(row["fixed_N_variance_pb2"], var), "INDEPENDENT_FLAG_MOMENTS")
                base_count, base_total, base_square = sums(base_bits[name])
                check(int(row["stratum_denominator_events"]) == base_count and
                      close(row["stratum_denominator_sumw_pb"], base_total), "UNCHANGED_FLAG_BASE_DENOMINATOR")
                ratio = total/base_total if base_total else None
                variance = ratio_variance(n, total, square, base_total, base_square)
                if ratio is None:
                    check(row["stratum_weighted_acceptance"] == "" and
                          row["stratum_weighted_acceptance_variance"] == "", "EMPTY_STRATUM_UNDEFINED")
                else:
                    check(close(row["stratum_weighted_acceptance"], ratio) and
                          close(row["stratum_weighted_acceptance_variance"], variance, absolute=Fraction(1, 10**15)),
                          "SHARED_SOURCE_RATIO_DELTA_VARIANCE")
                if square:
                    check(close(row["ESS"], total*total/square), "FLAG_POSITIVE_WEIGHT_ESS")
                else:
                    check(row["ESS"] == "", "EMPTY_ESS_UNDEFINED")
                metrics["selected_flag_stratum_checks"] += 1
            for a in FLAGS:
                ca, sa, qa = moments[a]
                for b in FLAGS:
                    cb, sb, qb = moments[b]
                    overlap, _, cross = sums(selected_bits[a] & selected_bits[b])
                    value = covariance_from_moments(n, sa, sb, cross)
                    row = cov[(ds, stage, a, b)]
                    check(int(row["overlap_events"]) == overlap and
                          close(row["fixed_N_covariance_pb2"], value), "INDEPENDENT_EVENT_MASK_COVARIANCE")
                    va, vb = covariance_from_moments(n, sa, sa, qa), covariance_from_moments(n, sb, sb, qb)
                    if va > 0 and vb > 0:
                        with localcontext() as ctx:
                            ctx.prec = 80
                            v = Decimal(value.numerator)/Decimal(value.denominator)
                            product = va*vb
                            den = (Decimal(product.numerator)/Decimal(product.denominator)).sqrt()
                            correlation = v/den
                        check(row["correlation"] != "" and close(row["correlation"], correlation),
                              "INDEPENDENT_CORRELATION")
                    else:
                        check(row["correlation"] == "", "DEGENERATE_CORRELATION_UNDEFINED")
                    metrics["independent_covariance_entries"] += 1

    for name, digest in summary["input_hashes"].items():
        check(sha(Path(name)) == digest, "BOUND_SOURCE_HASH:" + name)
    check(summary["source_events_joined"] == 6000 and summary["source_events_stratified"] == 3000 and
          summary["new_physical_events"] == 0 and summary["heavy_flavour_generator_exclusivity"] == "UNVERIFIED" and
          summary["physical_total_background"] == "BLOCKED", "HF_SCIENTIFIC_GATES")
    files = [origins, native] + [hf/name for name in
             ("phase10_hf_strata.csv", "phase10_hf_covariance.csv", "phase10_hf_summary.json")]
    return {"schema_version": 1, "status": "PASS_INDEPENDENT_EVENT_UNIT_HF_STATISTICS_WITH_LIMITS" if not errors else
            "FAIL_INDEPENDENT_EVENT_UNIT_HF_STATISTICS", "evidence_class": "ACTUAL_EXISTING_DATA_READBACK",
            "independent_implementation": "Integer source-event bit masks, exact Fraction raw moments, Decimal80 correlations; no production-module imports",
            "metrics": dict(metrics), "error_count": len(errors), "errors": errors[:50],
            "selected_flags": list(FLAGS), "source_files": {str(p): {"bytes": p.stat().st_size, "sha256": sha(p)}
                                                         for p in files},
            "limits": ["No LHE/HepMC/ROOT raw truth graph reclassification; persisted shower/hadron labels are shared input evidence.",
                       "ME outgoing species and native bit0 are independently formed from persisted PDG/native fields.",
                       "All 6000 covariance rows receive schema/symmetry/bound checks; exact mask arithmetic covers selected 12x12 entries per dataset/stage.",
                       "Uses original-source-event statistical unit with all jets clustered; no independent per-jet sample count.",
                       "No claim of external human review, generator exclusivity or physical background normalization."],
            "new_physical_events": 0, "heavy_flavour_generator_exclusivity": "UNVERIFIED",
            "physical_total_background": "BLOCKED"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origins", type=Path, required=True)
    p.add_argument("--native", type=Path, required=True)
    p.add_argument("--hf", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("OUTPUT_MUST_BE_FRESH")
    result = audit(a.origins, a.native, a.hf)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "error_count": result["error_count"],
                      "metrics": result["metrics"]}, sort_keys=True))
    return 0 if not result["error_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

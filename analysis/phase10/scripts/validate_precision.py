#!/usr/bin/env python3
"""Independent Fraction/Decimal audit of existing summary plans; no planner import."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

TARGETS = (Fraction(1, 10), Fraction(1, 5), Fraction(3, 10), Fraction(1, 2))
STAGE = "04_MGG_105_160"


def rational(value):
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_IS_NOT_A_NUMBER")
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError("NONFINITE_NUMBER")
    return Fraction(d)


def ceiling(value):
    return max(2, -(-value.numerator // value.denominator))


def acceptance_requirement(p, r):
    p, r = rational(p), rational(r)
    if not 0 <= p <= 1 or not 0 < r < 1:
        raise ValueError("INVALID_PROBABILITY_OR_TARGET")
    return None if p == 0 else ceiling((1 - p) / p / r**2)


def rate_requirement(n, total, variance, r):
    s, v, r = rational(total), rational(variance), rational(r)
    if n <= 1 or v < 0 or not 0 < r < 1:
        raise ValueError("INVALID_RATE_PLAN_INPUT")
    return None if s == 0 or v == 0 else ceiling(n * v / s**2 / r**2)


def ess_requirement(n, ess, r):
    if ess is None or ess == "":
        return None
    e, r = rational(ess), rational(r)
    if not 0 < e <= n * Fraction(1000000000001, 1000000000000) or not 0 < r < 1:
        raise ValueError("INVALID_ESS_PLAN_INPUT")
    return ceiling(n / e / r**2)


def moment_variance(n, total, square_total):
    return Fraction(n, n - 1) * (rational(square_total) - rational(total)**2 / n)


def normalized_variance(n, bin_total, bin_square, total, square_total):
    if rational(total) == 0:
        return None
    b, q, s, z = map(rational, (bin_total, bin_square, total, square_total))
    f = b / s
    return Fraction(n, n - 1) * (q - 2 * f * q + f * f * z) / s**2


def close(a, b, rtol=Fraction(1, 10**10), atol=Fraction(1, 10**24)):
    a, b = rational(a), rational(b)
    return abs(a - b) <= atol + rtol * max(abs(a), abs(b))


def number_or_none(value):
    return None if value is None or value == "" else int(value)


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def read_json(path):
    return json.loads(path.read_text(), parse_float=Decimal)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(plans: Path, phase9: Path):
    errors = []
    metrics = Counter()

    def require(ok, label):
        metrics["checks"] += 1
        if not ok:
            errors.append(label)

    def plan_equal(row, field, expected, label):
        require(number_or_none(row.get(field)) == expected, label + ":" + field)

    summary = read_json(plans / "phase10_precision_summary.json")
    scenarios = read_csv(plans / "phase10_precision_scenarios.csv")
    bins = read_csv(plans / "phase10_bin_support_plan.csv")
    kappa = read_csv(plans / "phase10_kappa_support_plan.csv")
    importance = read_json(plans / "phase10_importance_sampling_contract.json")
    rare_path = phase9 / "statistics_02/phase9_rare_event_precision.csv"
    plot_path = phase9 / "statistics_02/phase9_plot_data.json"
    rare = {x["dataset_id"]: x for x in read_csv(rare_path) if x["stage"] == STAGE}
    plots = read_json(plot_path)
    require(len(scenarios) == 88 and len(bins) == 3648 and len(kappa) == 16, "EXPECTED_ROW_SCOPE")
    expected_counts = {"S01_B100": (100, 18), "S01_C1000": (1000, 143),
                       "B01": (1000, 28), "B02": (1000, 1), "B03": (1000, 0),
                       "B04": (1000, 75), "B05": (1000, 131), "B06": (1000, 0)}
    require(set(rare) == set(expected_counts), "EIGHT_SOURCE_IDENTITIES")
    for ds, source in rare.items():
        n, k = int(source["N"]), int(source["k"])
        require((n, k) == expected_counts[ds], ds + ":HISTORICAL_CUTFLOW")
        direct = moment_variance(n, source["source_sumw_pb"], source["source_sumw2_pb2"])
        require(close(direct, source["fixed_original_N_sampling_variance_pb2"]), ds + ":BESSEL_MOMENT")
        if k == 0:
            with localcontext() as context:
                context.prec = 80
                p95 = Decimal(1) - Decimal("0.05")**(Decimal(1) / n)
            require(close(p95, source["one_sided95_upper_if_zero"]), ds + ":ANALYTIC_ZERO_UPPER")
    seen = set()
    for row in scenarios:
        ds = row["dataset_id"]
        source = rare[ds]
        n, k = int(source["N"]), int(source["k"])
        r = rational(row["target_relative_SE"])
        quantity = row["precision_quantity"]
        key = (ds, quantity, r, row.get("scenario_definition", ""))
        require(key not in seen, "DUPLICATE_SCENARIO")
        seen.add(key)
        require(r in TARGETS, "UNKNOWN_TARGET")
        require((int(row["pilot_N_original"]), int(row["pilot_survivors"])) == (n, k),
                ds + ":SCENARIO_SOURCE_COUNTS")
        require(row["physical_normalization_uncertainty"] == "UNKNOWN_NOT_INCLUDED" and
                row["guaranteed_precision"] == "False" and row["new_generation_performed"] == "False" and
                row["same_proposal_required"] == "True", ds + ":PLANNING_GATES")
        if quantity == "ZERO_SURVIVOR_ACCEPTANCE_SCENARIO":
            divisor = int(row["scenario_definition"].split("/")[-1])
            p = rational(source["one_sided95_upper_if_zero"]) / divisor
            require(k == 0 and divisor in (1, 10, 100), ds + ":ZERO_SCENARIO_SCOPE")
            require(close(row["assumed_p"], p), ds + ":ASSUMED_P_SOURCE")
            plan_equal(row, "N_total_acceptance_point", acceptance_requirement(p, r), ds)
            require(row["status"] == "ASSUMED_P_SCENARIO_NOT_MEASURED_REQUIREMENT" and
                    row["evidence_class"] == "FUTURE_UNEXECUTED_PROPOSAL" and
                    row["N_total_CP95_lower_p_conservative"] == "", ds + ":ZERO_NO_GUARANTEE")
            metrics["zero_scenario_rows"] += 1
        else:
            require(quantity in ("ACCEPTANCE", "WEIGHTED_SELECTED_RAW_SOURCE_RATE"), "UNKNOWN_QUANTITY")
            plan_equal(row, "N_total_acceptance_point", acceptance_requirement(Fraction(k, n), r), ds)
            plan_equal(row, "N_total_CP95_upper_p_optimistic", acceptance_requirement(source["upper"], r), ds)
            plan_equal(row, "N_total_CP95_lower_p_conservative", acceptance_requirement(source["lower"], r), ds)
            require(close(row["pilot_acceptance"], Fraction(k, n)), ds + ":PILOT_ACCEPTANCE")
            expected_status = ("NO_FINITE_MEASURED_GUARANTEE_ZERO_SURVIVORS" if k == 0
                               else "CONDITIONAL_SAME_IID_PROPOSAL_PLANNING")
            require(row["status"] == expected_status, ds + ":MEASURED_PLAN_STATUS")
            require(row["pilot_interval_envelope"] ==
                    "CP95_ACCEPTANCE_UNCERTAINTY_ENVELOPE_NOT_FUTURE_PRECISION_COVERAGE",
                    ds + ":CP_INTERVAL_IS_NOT_PRECISION_COVERAGE")
            if quantity == "WEIGHTED_SELECTED_RAW_SOURCE_RATE":
                expected = rate_requirement(n, source["source_sumw_pb"],
                                            source["fixed_original_N_sampling_variance_pb2"], r)
                plan_equal(row, "N_total_weighted_moment_point", expected, ds)
                require(close(row["pilot_source_sumw_pb"], source["source_sumw_pb"]) and
                        close(row["pilot_source_variance_pb2"],
                              source["fixed_original_N_sampling_variance_pb2"]), ds + ":RATE_SOURCE_MOMENTS")
            else:
                plan_equal(row, "N_total_weighted_moment_point", None, ds)
        metrics["scenario_rows"] += 1

    histogram_bins = {}
    for h in plots["histograms"]:
        if h["stage"] != STAGE:
            continue
        allbins = [h["underflow"]] + h["bins"] + [h["overflow"]]
        for index, b in enumerate(allbins):
            histogram_bins[(h["dataset_id"], h["observable"], index)] = (h, b, len(allbins))
    require(len(histogram_bins) == 912, "EXACT_BIN_SOURCE_SCOPE")
    seen = set()
    for row in bins:
        key = (row["dataset_id"], row["observable"], int(row["bin"]))
        r = rational(row["target_relative_SE"])
        require((key, r) not in seen and r in TARGETS, "BIN_IDENTITY_OR_TARGET")
        seen.add((key, r))
        h, b, count = histogram_bins[key]
        n, k = int(h["N_original"]), int(b["N"])
        require(int(row["pilot_N_original"]) == n and int(row["bin_sources"]) == k,
                "BIN_ORIGINAL_DENOMINATOR")
        expected_flow = "UNDERFLOW" if key[-1] == 0 else "OVERFLOW" if key[-1] == count - 1 else "REGULAR"
        require(row["flow"] == expected_flow, "BIN_FLOW_IDENTITY")
        direct_raw = moment_variance(n, b["sumw"], b["sumw2"])
        require(close(direct_raw, b["source_variance"]), "BIN_BESSEL_VARIANCE_IDENTITY")
        direct_shape = normalized_variance(n, b["sumw"], b["sumw2"], h["sumw"], h["sumw2"])
        if direct_shape is not None:
            require(close(direct_shape, b["variance"], atol=Fraction(1, 10**15)),
                    "BIN_TOTAL_COVARIANCE_DELTA_IDENTITY")
            require(close(b["value"], rational(b["sumw"]) / rational(h["sumw"])),
                    "BIN_NORMALIZED_FRACTION_IDENTITY")
        plan_equal(row, "N_total_bin_acceptance_plugin", acceptance_requirement(Fraction(k, n), r), "BIN")
        plan_equal(row, "N_total_raw_bin_rate_moment",
                   rate_requirement(n, b["sumw"], b["source_variance"], r), "BIN")
        shape = (rate_requirement(n, b["value"], b["variance"], r)
                 if k >= 2 and b["value"] is not None and b["variance"] is not None else None)
        plan_equal(row, "N_total_normalized_bin_delta_point", shape, "BIN")
        plan_equal(row, "N_total_ESS_inverse_variance_proxy", ess_requirement(n, b["ESS"], r), "BIN")
        expected_status = ("NO_FINITE_MEASURED_PLAN_EMPTY_BIN" if k == 0 else
                           "UNSUPPORTED_SINGLETON_SHAPE" if k == 1 else
                           "DEGENERATE_OR_EMPTY_SHAPE_VARIANCE" if shape is None else
                           "CONDITIONAL_MOMENT_EXTRAPOLATION")
        require(row["status"] == expected_status and row["guaranteed_precision"] == "False" and
                row["physical_normalization_uncertainty"] == "UNKNOWN_NOT_INCLUDED", "BIN_SUPPORT_GUARD")
        if k < 2:
            require(row["N_total_normalized_bin_delta_point"] == "", "NO_EMPTY_SINGLETON_SHAPE_REQUIREMENT")
        metrics["bin_rows"] += 1
        metrics["bin_status_" + expected_status] += 1

    ksummary = {rational(x["kappa_lambda"]): x for x in plots["kappa_summary"]
                if rational(x["kappa_lambda"]) in (Fraction(5, 2), Fraction(5))}
    for kval, source in ksummary.items():
        concentration = [x for x in plots["kappa_weight_concentration"]
                         if rational(x["kappa_lambda"]) == kval]
        require(len(concentration) == 1000 and
                len({x["source_event_sha256"] for x in concentration}) == 1000, "KAPPA_UNIQUE_SOURCE_IDENTITIES")
        for stage, field in (("INPUT", "source_ESS"), ("FINAL_MGG", "final_ESS")):
            rows = concentration if stage == "INPUT" else [x for x in concentration if x["final_selected"]]
            fractions = [rational(x["abs_weight_fraction"]) for x in rows]
            total, squares = sum(fractions), sum(x*x for x in fractions)
            require(close(total**2/squares, source[field]), "KAPPA_INDEPENDENT_ESS")
            metrics["kappa_ESS_identity_checks"] += 1
    seen = set()
    for row in kappa:
        kval, r = rational(row["kappa_lambda"]), rational(row["target_relative_SE"])
        stage = row["stage"]
        require((kval, stage, r) not in seen and r in TARGETS, "KAPPA_ROW_IDENTITY")
        seen.add((kval, stage, r))
        require(stage in ("INPUT", "FINAL_MGG"), "KAPPA_STAGE_SCOPE")
        source = ksummary[kval]
        ess = rational(source["source_ESS" if stage == "INPUT" else "final_ESS"])
        n = int(row["pilot_original_N"])
        require(n == 1000 and close(ess, row["pilot_ESS"]), "KAPPA_ORIGINAL_N_AND_ESS")
        rv = (Fraction(n) / ess - 1) / (n - 1)
        with localcontext() as context:
            context.prec = 80
            se = (Decimal(rv.numerator) / Decimal(rv.denominator)).sqrt()
        require(close(se, row["pilot_relative_MC_SE"]), "KAPPA_RELATIVE_SE")
        plan_equal(row, "N_total_old_proposal_moment_point", ceiling(n * rv / r**2), "KAPPA")
        plan_equal(row, "N_total_ESS_proxy", ess_requirement(n, ess, r), "KAPPA")
        require(close(row["top1_input_abs_fraction"], source["top1_abs_fraction"]) and
                close(row["top1_final_abs_fraction"], source["final_top1_abs_fraction"]),
                "KAPPA_TAIL_CONCENTRATION")
        require(row["status"] == "INCONCLUSIVE_REWEIGHTING_CONDITIONAL_PLAN_ONLY",
                "KAPPA_NOT_A_VALIDATED_PRODUCTION_REQUIREMENT")
        metrics["kappa_rows"] += 1

    for name, identity in summary["source_inputs"].items():
        p = Path(name)
        require(p.is_file() and p.stat().st_size == identity["bytes"] and sha256(p) == identity["sha256"],
                "PRECISION_INPUT_HASH:" + name)
    for key in ("additional_independent_events", "new_ME_calls", "new_integrals", "new_hard_events"):
        require(summary[key] == 0, "NO_PHYSICAL_PRODUCTION:" + key)
    require(summary["physical_total_background"] == "BLOCKED" and
            summary["physical_significance"] == "NOT_EVALUATED", "PHYSICAL_GATES")
    require(summary["scenarios"] == 88 and summary["bin_support_rows"] == 3648 and
            summary["kappa_plan_rows"] == 16, "SUMMARY_ROW_COUNTS")
    require(importance["pilot_executed"] is False and importance["new_independent_sources"] == 0 and
            importance["physical_execution_authorized"] is False, "IMPORTANCE_NOT_EXECUTED")
    require(importance["proposal_densities_known"] is False and importance["support_validated"] is False and
            importance["normalizing_constants_known"] is False, "IMPORTANCE_MISSING_DENSITIES_PRESERVED")
    files = [plans / name for name in ("phase10_precision_summary.json", "phase10_precision_scenarios.csv",
             "phase10_bin_support_plan.csv", "phase10_kappa_support_plan.csv",
             "phase10_importance_sampling_contract.json")] + [rare_path, plot_path]
    return {"schema_version": 1, "status": "PASS_INDEPENDENT_PRECISION_ARITHMETIC_WITH_LIMITS" if not errors else
            "FAIL_INDEPENDENT_PRECISION_ARITHMETIC", "evidence_class": "HISTORICAL_SOURCE_AUDIT",
            "independent_implementation": "Fraction ceilings and Decimal80 zero-bound/sqrt; no production planner imports",
            "metrics": dict(metrics), "errors": errors[:50], "error_count": len(errors),
            "source_files": {str(p): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in files},
            "limits": ["Uses frozen Phase9 CP endpoints and histogram summaries; no new raw event readback.",
                       "Recomputes finite-pilot planning arithmetic, not future achieved-precision coverage.",
                       "Empty/singleton normalized shapes have no finite empirical variance plan.",
                       "ESS proxies are conditional diagnostics, not new independent hard counts.",
                       "No physical normalization, matching validation, new ME weights or new events."],
            "physical_total_background": "BLOCKED", "physical_significance": "NOT_EVALUATED",
            "new_independent_hard_events": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plans", type=Path, required=True)
    parser.add_argument("--phase9", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("OUTPUT_MUST_BE_FRESH")
    result = audit(args.plans, args.phase9)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "errors": result["error_count"],
                      "metrics": result["metrics"]}, sort_keys=True))
    return 0 if not result["error_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Event-level pilot uncertainty; no generator, detector, or calibration work.

Linear/quadratic moments use Decimal(60), serialized as finite binary64 values.
Conditional count distributions use a direct binary64 Poisson-binomial DP.
Exact binomial intervals invert binomial tails, without a SciPy dependency.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from functools import lru_cache
import math

Z95 = 1.959963984540054
PILOT_SCOPE = (
    "IID source-event pilot variation includes generation, shower and "
    "reconstruction; one realization per hard event cannot separate them"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decimal_value(value):
    require(not isinstance(value, bool), "boolean is not a numerical value")
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise ValueError("invalid decimal value") from error
    require(result.is_finite(), "non-finite decimal value")
    return result


def probability(value):
    result = decimal_value(value)
    require(0 <= result <= 1, "probability outside [0,1]")
    return result


def _finite(value):
    result = float(value)
    require(math.isfinite(result), "statistic exceeds finite binary64 range")
    return result


def sample_covariance(first, second):
    """Unbiased event sample covariance, denominator N-1."""
    require(len(first) == len(second) and len(first) >= 2, "covariance needs paired events")
    with localcontext() as context:
        context.prec = 60
        a, b = list(map(decimal_value, first)), list(map(decimal_value, second))
        n = Decimal(len(a))
        ma, mb = sum(a) / n, sum(b) / n
        return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (n - 1)


def _binomial_range(n, low, high, p):
    """Direct log-scaled binomial probability sum; no normal approximation."""
    if low > high:
        return 0.0
    if p == 0:
        return float(low <= 0 <= high)
    if p == 1:
        return float(low <= n <= high)
    logp, log1p = math.log(p), math.log1p(-p)
    term = (
        math.lgamma(n + 1) - math.lgamma(low + 1) - math.lgamma(n - low + 1)
        + low * logp + (n - low) * log1p
    )
    terms = [term]
    for k in range(low, high):
        term += math.log(n - k) - math.log(k + 1) + logp - log1p
        terms.append(term)
    scale = max(terms)
    return math.exp(scale) * math.fsum(math.exp(x - scale) for x in terms)


def _tail_root(n, low, high, target, increasing):
    lo, hi = 0.0, 1.0
    for _ in range(160):
        mid = (lo + hi) / 2
        if mid == lo or mid == hi:
            break
        value = _binomial_range(n, low, high, mid)
        if (value < target) == increasing:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@lru_cache(maxsize=256)
def clopper_pearson(k, n, confidence=0.95):
    """Equal-tailed frequentist CP interval and one-sided upper limit."""
    require(type(n) is int and type(k) is int and n > 0 and 0 <= k <= n,
            "invalid unweighted binomial counts")
    require(math.isfinite(confidence) and 0 < confidence < 1,
            "invalid confidence level")
    alpha = 1 - confidence
    lower = 0.0 if k == 0 else _tail_root(n, k, n, alpha / 2, True)
    if k == n:
        upper = one_upper = 1.0
    elif k == 0:
        upper = -math.expm1(math.log(alpha / 2) / n)
        one_upper = -math.expm1(math.log(alpha) / n)
    else:
        upper = _tail_root(n, 0, k, alpha / 2, False)
        one_upper = _tail_root(n, 0, k, alpha, False)
    return {
        "method": "Clopper-Pearson exact binomial tail inversion",
        "confidence": confidence, "successes": k, "trials": n,
        "estimate": k / n, "two_sided_equal_tail": [lower, upper],
        "one_sided_upper": one_upper,
        "interpretation": (
            "frequentist interval for unconditional IID event acceptance; "
            "not the fixed-pilot Poisson-binomial predictive interval"
        ),
    }


def poisson_binomial(probabilities, observed_count=None, confidence=0.95):
    """Distribution of independent event tag decisions given fixed kinematics."""
    q = [_finite(probability(x)) for x in probabilities]
    require(q and 0 < confidence < 1, "empty/invalid predictive request")
    require(observed_count is None or
            (type(observed_count) is int and 0 <= observed_count <= len(q)),
            "invalid observed count")
    pmf = [1.0]
    for value in q:
        if value == 0:
            pmf.append(0.0)
            continue
        pmf.append(0.0)
        for k in range(len(pmf) - 1, 0, -1):
            pmf[k] = pmf[k] * (1 - value) + pmf[k - 1] * value
        pmf[0] *= 1 - value
    mass = math.fsum(pmf)
    require(abs(mass - 1) <= 1e-11, "Poisson-binomial numerical mass error")
    cdf = []
    for value in pmf:
        cdf.append(math.fsum((cdf[-1] if cdf else 0.0, value)))
    def quantile(target):
        return next((k for k, value in enumerate(cdf) if value >= target), len(q))
    tail = (1 - confidence) / 2
    log_zero = -math.inf if any(x == 1 for x in q) else math.fsum(math.log1p(-x) for x in q)
    zero = math.exp(log_zero)
    return {
        "scope": "fixed verified kinematics; conditional event tag randomness only",
        "method": "direct Poisson-binomial recurrence; no normal count approximation",
        "events": len(q), "pmf": pmf, "pmf_mass_minus_one": mass - 1,
        "probability_zero": zero,
        "log_probability_zero": None if log_zero == -math.inf else log_zero,
        "predictive_interval": {
            "confidence": confidence,
            "equal_tail_discrete_bounds": [quantile(tail), quantile(1 - tail)],
            "actual_coverage": math.fsum(pmf[quantile(tail):quantile(1-tail) + 1]),
        },
        "observed_count": observed_count,
        "probability_observed_count": None if observed_count is None else pmf[observed_count],
        "probability_at_most_observed": None if observed_count is None else math.fsum(pmf[:observed_count + 1]),
        "probability_at_least_observed": None if observed_count is None else math.fsum(pmf[observed_count:]),
    }


def relative_precision_forecast(p, relative_precision, z=1.0):
    """Independent future Bernoulli count planning, not a realized guarantee."""
    p = _finite(probability(p))
    require(math.isfinite(relative_precision) and relative_precision > 0 and
            math.isfinite(z) and z > 0, "invalid planning precision")
    if p == 0:
        return {"status": "UNBOUNDED_INCONCLUSIVE", "events": None,
                "reason": "zero lower bound gives no positive rate for finite planning"}
    needed = z * z * (1 - p) / (p * relative_precision * relative_precision)
    require(math.isfinite(needed), "planning count exceeds finite numerical range")
    return {"status": "CONDITIONAL_PLANNING_ONLY", "events": max(1, math.ceil(needed)),
            "assumed_acceptance": p, "relative_precision": relative_precision, "z": z,
            "equation": "N >= z^2(1-p)/(p*r^2)",
            "scope": "future IID hard/shower/reco/tag event counts; no systematics"}


def analytic_mean_forecast(mean, pilot_event_variance, relative_precision, z=1.0):
    """Model-assisted planning for averaging q, not realized tag counts."""
    mean, variance = _finite(mean), _finite(pilot_event_variance)
    require(mean >= 0 and variance >= 0 and relative_precision > 0 and z > 0,
            "invalid analytic-mean planning parameters")
    if mean == 0:
        return {"status": "UNBOUNDED_INCONCLUSIVE", "events": None}
    needed = z * z * variance / (relative_precision * mean) ** 2
    require(math.isfinite(needed), "analytic planning count exceeds numerical range")
    return {
        "status": "MODEL_ASSISTED_PILOT_VARIANCE_ONLY",
        "events": max(1, math.ceil(needed)), "relative_precision": relative_precision,
        "z": z, "equation": "N >= z^2*s_q^2/(r^2*mean_q^2)",
        "scope": "new independent source+shower+reco events analyzed by averaging q; not tag-count precision",
        "limitation": "pilot variance may miss rare kinematics; zero sample variance is not proof of zero population variance",
    }


def zero_detection_planning(upper, lower=0.0, detection_probability=0.95):
    """An upper rate gives a best-case minimum, never guaranteed detection."""
    upper, lower = _finite(probability(upper)), _finite(probability(lower))
    require(lower <= upper and 0 < detection_probability < 1, "invalid detection bounds")
    def count(p):
        if p == 0:
            return None
        if p == 1:
            return 1
        return max(1, math.ceil(math.log1p(-detection_probability) / math.log1p(-p)))
    return {
        "target_detection_probability": detection_probability,
        "conditional_sufficient_events_at_lower_rate": count(lower),
        "lower_bound_status": "UNBOUNDED_INCONCLUSIVE" if lower == 0 else "CONDITIONAL_PLANNING_ONLY",
        "optimistic_minimum_at_upper_rate_events": count(upper),
        "upper_bound_interpretation": (
            "p<=upper implies detection probability <=1-(1-upper)^N; "
            "plugging upper gives an optimistic minimum, not a sufficient sample size"
        ),
        "frequentist_scope": "planning conditional on confidence-bound coverage, not posterior probability",
    }


def analyze_values(probabilities, weights_pb, observed_count=None, *, source_count=None):
    """Low-level numerical API; analytic fixtures are not physics references."""
    require(len(probabilities) == len(weights_pb) and len(probabilities) >= 2,
            "at least two paired source events required")
    n = len(probabilities)
    source_count = n if source_count is None else source_count
    require(type(source_count) is int and source_count == n,
            "pilot uncertainty requires all original source events, not an eligible subset")
    with localcontext() as context:
        context.prec = 60
        q, weights = list(map(probability, probabilities)), list(map(decimal_value, weights_pb))
        nd = Decimal(n)
        mean = sum(q) / nd
        tag_variance = sum(x * (1 - x) for x in q)
        pilot_variance = sample_covariance(q, q)
        empirical_variance = pilot_variance * (nd - 1) / nd
        raw_integrands = [nd * w * x for w, x in zip(weights, q)]
        integral_variance = sample_covariance(raw_integrands, raw_integrands)
        weighted_mean = sum(w * x for w, x in zip(weights, q))
        weighted_tag_variance = sum(w * w * x * (1 - x) for w, x in zip(weights, q))
        equal_positive = all(w > 0 and w == weights[0] for w in weights)
        cp = clopper_pearson(observed_count, n) if observed_count is not None and equal_positive else None
        pilot_se = math.sqrt(_finite(pilot_variance / nd))
        integral_se = math.sqrt(_finite(integral_variance / nd))
        empirical_total = empirical_variance + tag_variance / nd
        result = {
            "events_all_source": n, "eligible_subset_used_as_denominator": False,
            "numeric_moments": "Decimal60 accumulation; finite binary64 report serialization",
            "conditional_tag": {
                "expected_count": _finite(sum(q)),
                "count_variance": _finite(tag_variance),
                "count_standard_deviation": math.sqrt(_finite(tag_variance)),
                "expected_weighted_cross_section_pb": _finite(weighted_mean),
                "weighted_variance_pb2": _finite(weighted_tag_variance),
                "weighted_standard_deviation_pb": math.sqrt(_finite(weighted_tag_variance)),
                "scope": "tag randomization on exactly this fixed kinematic pilot",
            },
            "source_event_pilot": {
                "scope": PILOT_SCOPE, "probability_mean": _finite(mean),
                "unbiased_event_sample_variance_q": _finite(pilot_variance),
                "variance_of_probability_mean": _finite(pilot_variance / nd),
                "probability_mean_standard_error": pilot_se,
                "normal95_unclipped_mean_diagnostic": [
                    _finite(mean) - Z95 * pilot_se, _finite(mean) + Z95 * pilot_se],
                "raw_weight_times_q_sample_variance_pb2": _finite(integral_variance),
                "variance_of_cross_section_mean_pb2": _finite(integral_variance / nd),
                "cross_section_mean_standard_error_pb": integral_se,
                "normal_diagnostic_limit": "asymptotic, not exact coverage; rare pilot/systematics unresolved",
            },
            "law_total_variance": {
                "empirical_population_variance_q": _finite(empirical_variance),
                "mean_q_one_minus_q": _finite(tag_variance / nd),
                "sum_components": _finite(empirical_total),
                "marginal_bernoulli_mean_one_minus_mean": _finite(mean * (1 - mean)),
                "scope": "empirical event-population identity; N denominator, not unbiased N-1 estimator",
            },
            "observed_count": observed_count,
            "exact_observed_interval": {
                "status": "APPLICABLE" if cp else "NOT_APPLICABLE",
                "verified_positive_equal_source_weights": equal_positive,
                "interval": cp,
                "reason": None if cp else "requires observed integer count and verified positive equal weights",
            },
            "conditional_predictive": poisson_binomial(q, observed_count),
            "forecasts": {
                "conservative_observed_lower_bound": [
                    relative_precision_forecast(cp["two_sided_equal_tail"][0], r, z)
                    for r in (0.20, 0.10) for z in (1.0, Z95)
                ] if cp else None,
                "model_assisted_mean_rate": [
                    relative_precision_forecast(mean, r, z)
                    for r in (0.20, 0.10) for z in (1.0, Z95)
                ],
                "model_assisted_analytic_q_mean": [
                    analytic_mean_forecast(mean, pilot_variance, r, z)
                    for r in (0.20, 0.10) for z in (1.0, Z95)
                ],
                "interpretation": (
                    "z1 one-SD precision and z1.95996 approximate95% half-width are distinct; "
                    "model-assisted rates are conditional study-model planning, not official performance"
                ),
                "zero_detection": zero_detection_planning(cp["one_sided_upper"]) if cp and observed_count == 0 else None,
            },
        }
    return result


def analyze_stage(events, probability_key, observed_key, *, scenario="baseline",
                  expected_events=1000, source_count=1000):
    """Consume generator's schema without dropping any zero-probability event."""
    require(len(events) == expected_events == source_count, "complete source-pilot count required")
    indices, q, weights, observed = set(), [], [], 0
    for ordinal, row in enumerate(events, 1):
        require(row["ordinal"] == ordinal and row["source_count"] == source_count,
                "source ordinal/count mismatch")
        index = row["source_event_index"]
        require(type(index) is int and 1 <= index <= source_count and index not in indices,
                "duplicated/out-of-range source event")
        indices.add(index)
        value = probability(row["scenarios"][scenario][probability_key])
        decision = row[observed_key]
        require(type(decision) is bool, "observed event decision must be boolean")
        if not row["cut_jets"]:
            require(value == 0 and not decision, "ineligible source event omitted or nonzero")
        q.append(value)
        weights.append(row["source_contribution_pb"])
        observed += decision
    result = analyze_values(q, weights, observed, source_count=source_count)
    result.update({"scenario": scenario, "stage_probability_key": probability_key,
                   "observed_key": observed_key})
    return result


def nested_stage_covariance(first, second, weights_pb):
    """Same tag decisions: stage B is stage A plus tag-independent cuts."""
    require(len(first) == len(second) == len(weights_pb) and len(first) >= 2,
            "paired full event pilot required")
    with localcontext() as context:
        context.prec = 60
        a, b = list(map(probability, first)), list(map(probability, second))
        weights = list(map(decimal_value, weights_pb))
        require(all(y <= x for x, y in zip(a, b)), "nested stage probability ordering violated")
        n = Decimal(len(a))
        conditional = sum(y * (1 - x) for x, y in zip(a, b))
        covariance = sample_covariance(a, b)
        raw_a = [n * w * x for w, x in zip(weights, a)]
        raw_b = [n * w * y for w, y in zip(weights, b)]
        population = covariance * (n - 1) / n
        return {
            "conditional_count_covariance": _finite(conditional),
            "conditional_weighted_covariance_pb2": _finite(sum(
                w * w * y * (1 - x) for w, x, y in zip(weights, a, b))),
            "pilot_event_sample_covariance": _finite(covariance),
            "pilot_probability_mean_covariance": _finite(covariance / n),
            "pilot_cross_section_mean_covariance_pb2": _finite(sample_covariance(raw_a, raw_b) / n),
            "empirical_total_per_event_covariance": _finite(population + conditional / n),
            "marginal_nested_identity": _finite(sum(b) / n * (1 - sum(a) / n)),
            "scope": "same original events and same tag outcomes; do not treat cutflow stages independently",
        }

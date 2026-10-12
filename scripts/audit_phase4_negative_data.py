#!/usr/bin/env python3
"""Independently audit the 37 Phase 4 DATA negative-invariant cached pairs.

Usage: python scripts/audit_phase4_negative_data.py CACHE_DIRECTORY NEW_JSON

This scoped audit reads objects.csv and pairs.csv only. It never opens collision
ROOT files, changes the input tuples, or interprets a rounding-compatible input
as corrected. The backend is Python's standard-library Decimal (no mpmath or
third-party installation), with independent Taylor sin/cos and Decimal exp/sqrt.
Nine-significant-digit native Float32 CSV values are first round-tripped through
binary32 and then converted to exact rational values. Numerical signs are checked
at both 100 and 75 decimal digits. The checked direction domain is |phi| <= 4.

The recorded half-ULP envelope is conservative. A zero-crossing energy witness is
an existence diagnostic within an assumed round-to-nearest input interval, not
proof of the actual input's origin or permission to alter it. The physical cause
remains UNKNOWN. The output is created exclusively; existing evidence is refused.
"""

import argparse
import csv
import decimal
import hashlib
import json
import math
from pathlib import Path
import platform
import struct


def require(condition, message):
    if not condition:
        raise ValueError(message)


def trig(value, sine):
    """Independent Taylor series; termination is current-context convergence."""
    require(abs(value) <= 4, "Native phi outside the audited Taylor domain")
    term = value if sine else decimal.Decimal(1)
    result = term
    square = value * value
    for index in range(1, 1000):
        denominator = ((2 * index) * (2 * index + 1) if sine
                       else (2 * index - 1) * (2 * index))
        term = -term * square / denominator
        following = result + term
        if following == result:
            return result
        result = following
    raise ValueError("Independent Taylor series did not converge")


def sinh(value):
    return (value.exp() - (-value).exp()) / 2


def cosh(value):
    return (value.exp() + (-value).exp()) / 2


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def native(value):
    result = struct.unpack("<f", struct.pack("<f", float(value)))[0]
    require(math.isfinite(result), "Nonfinite native binary32 input")
    return result


def exact(value):
    numerator, denominator = value.as_integer_ratio()
    return decimal.Decimal(numerator) / denominator


def bits(value):
    return struct.unpack("<I", struct.pack("<f", value))[0]


def from_bits(value):
    return struct.unpack("<f", struct.pack("<I", value))[0]


def neighbors(value):
    if value == 0:
        return -from_bits(1), from_bits(1)
    integer = bits(value)
    result = ((from_bits(integer - 1), from_bits(integer + 1)) if value > 0
              else (from_bits(integer + 1), from_bits(integer - 1)))
    require(all(math.isfinite(item) for item in result),
            "Float32 neighbor outside the finite audited domain")
    return result


def half_ulp(value):
    lower, upper = neighbors(value)
    return max(exact(value) - exact(lower), exact(upper) - exact(value)) / 2


def render(value):
    return format(value, ".85g")


def event_key(row):
    return row["entry"], row["run"], row["event"]


def components(values):
    pt, eta, phi, energy = (exact(values[name])
                           for name in ("pt", "eta", "phi", "energy"))
    return [pt * trig(phi, False), pt * trig(phi, True), pt * sinh(eta), energy]


def mass_squared(values):
    return values[3] ** 2 - sum(item * item for item in values[:3])


def audit(base, expected_cases):
    negative = {}
    with (base / "pairs.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["group"] != "photon":
                continue
            has_negative = any(row[name] and decimal.Decimal(row[name]) < 0
                               for name in ("original_mass2", "corrected_mass2",
                                            "reference_mass2"))
            if has_negative:
                key = event_key(row)
                require(key not in negative, "Duplicate cached photon pair key")
                negative[key] = row
    require(len(negative) == expected_cases,
            f"Expected {expected_cases} negative pairs; found {len(negative)}")
    objects = {key: {} for key in negative}
    with (base / "objects.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            key = event_key(row)
            if key in negative and row["group"] == "photon":
                index = int(row["input_index"])
                require(index not in objects[key], "Duplicate cached photon object")
                objects[key][index] = row
    results = []
    for key, pair in negative.items():
        totals = [decimal.Decimal(0)] * 4
        delta = [decimal.Decimal(0)] * 4
        upper_energy_allowance = decimal.Decimal(0)
        records = []
        indices = [int(pair[name]) for name in
                   ("leading_input_index", "subleading_input_index")]
        require(indices[0] != indices[1], "Pair reused the same photon")
        for index in indices:
            require(index in objects[key], "Selected native photon missing from cache")
            row = objects[key][index]
            values = {name: native(row["raw_" + name])
                      for name in ("pt", "eta", "phi", "energy")}
            require(values["pt"] >= 0 and values["energy"] > 0,
                    "Input outside the audited photon domain")
            # Rebuild the binary rational first: the printed decimal is a
            # round-trip representation, not the exact underlying value.
            require(values["pt"] == float(row["scaled_pt"]) and
                    values["energy"] == float(row["scaled_energy"]),
                    "Scale-one native tuple round-trip mismatch")
            pt, eta, phi, energy = (exact(values[name]) for name in
                                   ("pt", "eta", "phi", "energy"))
            vector = components(values)
            hp, heta, hphi, he = (half_ulp(values[name]) for name in
                                  ("pt", "eta", "phi", "energy"))
            transverse = hp + (abs(pt) + hp) * hphi
            maximum_eta = abs(eta) + heta
            uncertainty = [transverse, transverse,
                           hp * sinh(maximum_eta) +
                           (abs(pt) + hp) * cosh(maximum_eta) * heta, he]
            for axis in range(4):
                totals[axis] += vector[axis]
                delta[axis] += uncertainty[axis]
            upper_energy_allowance += (exact(neighbors(values["energy"])[1]) -
                                       energy) / 2
            records.append({"input_index": index, "native_float32": {
                name: {"csv_roundtrip": row["raw_" + name],
                       "binary32_hex": f"{bits(value):08x}",
                       "exact_binary_value_hex": value.hex(),
                       "exact_rational": list(value.as_integer_ratio())}
                for name, value in values.items()}})
        square = mass_squared(totals)
        bound = sum(2 * abs(value) * uncertainty + uncertainty * uncertainty
                    for value, uncertainty in zip(totals, delta))
        with decimal.localcontext() as context:
            context.prec = 75
            second = [decimal.Decimal(0)] * 4
            for record in records:
                values = {name: from_bits(int(native_value["binary32_hex"], 16))
                          for name, native_value in record["native_float32"].items()}
                for axis, value in enumerate(components(values)):
                    second[axis] += value
            square75 = mass_squared(second)
        require(square < 0 and square75 < 0 and
                abs(square - square75) < decimal.Decimal("1e-60"),
                "Negative sign or precision-repeat agreement failed")
        require(all(pair[name] and decimal.Decimal(pair[name]) < 0 for name in
                    ("original_mass2", "corrected_mass2", "reference_mass2")),
                "Cached original/corrected/reference sign disagreement")
        require(pair["original_valid"] == "0" and pair["corrected_valid"] == "0",
                "Invalid supplied tuple was accepted")
        compatible = abs(square) <= bound
        require(compatible and pair["mass2_classification"] ==
                "NEGATIVE_SUPPLIED_FLOAT32_TUPLE_HALF_ULP_COMPATIBLE_ORIGIN_UNKNOWN",
                "Cached half-ULP classification disagrees with independent audit")
        energy_deficit = sum(value * value for value in totals[:3]).sqrt() - totals[3]
        results.append({
            "entry": int(key[0]), "run": int(key[1]), "event": int(key[2]),
            "objects": records,
            "mass2_100_decimal_digits": render(square),
            "mass2_75_decimal_digits": render(square75),
            "precision_repeat_difference": render(abs(square - square75)),
            "cached_reference_mass2": pair["reference_mass2"],
            "cached_corrected_mass2": pair["corrected_mass2"],
            "difference_from_cached_long_double": render(abs(
                square - decimal.Decimal(pair["reference_mass2"]))),
            "conservative_independent_half_ulp_bound": render(bound),
            "cached_half_ulp_bound": pair["half_ulp_mass2_bound"],
            "absolute_mass2_over_bound": render(abs(square) / bound),
            "inside_conservative_half_ulp_envelope": compatible,
            "energy_only_zero_crossing_deficit": render(energy_deficit),
            "upward_energy_half_ulp_allowance": render(upper_energy_allowance),
            "energy_only_half_ulp_zero_crossing_exists":
                energy_deficit <= upper_energy_allowance,
            "classification": "NEGATIVE_EXACT_SUPPLIED_BINARY32_TUPLE; INPUT_ORIGIN_UNKNOWN"})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache_directory", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--expected-cases", type=int, default=37)
    arguments = parser.parse_args()
    require(arguments.expected_cases > 0, "Expected case count must be positive")
    require(not arguments.output_json.exists(), "Refusing to overwrite audit evidence")
    decimal.getcontext().prec = 100
    results = audit(arguments.cache_directory, arguments.expected_cases)
    payload = {
        "schema": "independent-negative-data-v2", "status": "PASS",
        "scope": "Cached Phase 4 DATA photon negative-invariant sign audit",
        "method": "Exact rational binary32 input; 100 decimal digits repeated at 75 digits",
        "arithmetic_backend": "Decimal exp/sqrt; independent Taylor sin/cos",
        "python_version": platform.python_version(),
        "decimal_version": decimal.__version__,
        "libmpdec_version": decimal.__libmpdec_version__,
        "third_party_dependencies": [], "collision_root_reads": 0,
        "input_scale_to_gev": "1", "phi_domain_max_abs": "4",
        "cache_directory": str(arguments.cache_directory.resolve()),
        "cached_pairs_sha256": digest(arguments.cache_directory / "pairs.csv"),
        "cached_objects_sha256": digest(arguments.cache_directory / "objects.csv"),
        "cases": len(results), "negative_high_precision_cases": len(results),
        "sign_disagreements": 0,
        "inside_conservative_half_ulp_envelope": sum(
            row["inside_conservative_half_ulp_envelope"] for row in results),
        "energy_only_half_ulp_zero_crossing_exists": sum(
            row["energy_only_half_ulp_zero_crossing_exists"] for row in results),
        "minimum_negative_mass2": min((row["mass2_100_decimal_digits"] for row in results),
                                     key=decimal.Decimal),
        "maximum_negative_mass2": max((row["mass2_100_decimal_digits"] for row in results),
                                     key=decimal.Decimal),
        "maximum_difference_from_cached_long_double": max(
            (row["difference_from_cached_long_double"] for row in results),
            key=decimal.Decimal),
        "maximum_abs_mass2_over_half_ulp_bound": max(
            (row["absolute_mass2_over_bound"] for row in results), key=decimal.Decimal),
        "maximum_precision_repeat_difference": max(
            (row["precision_repeat_difference"] for row in results), key=decimal.Decimal),
        "interpretation": (
            "Negativity is in the exact supplied binary32 tuples and remains invalid. "
            "The conservative half-ULP envelope alone does not prove an attainable "
            "correlated perturbation. Energy-only zero-crossing witnesses, when "
            "present, establish existence within an assumed rounding interval, "
            "not the actual physical, calibration or rounding origin. Inputs and "
            "invalid classifications are unchanged; origin UNKNOWN."),
        "results": results}
    with arguments.output_json.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in payload.items() if key != "results"},
                     indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Audit preserved Phase 4 V2 weight/SF CSVs without ROOT or network access.

Creates only new Phase 5 evidence outputs. Bounded post-skim moments are
diagnostics, never generated denominators or authorization to apply weights.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

DSIDS = (343981, 346214, 423103)
SF_BRANCHES = (
    "ScaleFactor_BTAG", "ScaleFactor_FTAG", "ScaleFactor_PHOTON",
    "ScaleFactor_PILEUP", "ScaleFactor_JVT",
)
SCALARS = (
    ("sigma_pb", "xsec", "table_crossSection_pb"),
    ("generator_filter_efficiency", "filteff", "table_genFiltEff"),
    ("k_factor", "kfac", "table_kFactor"),
    ("generated_event_count", "num_events", "table_nEvents"),
    ("signed_pre_skim_sumW", "sum_of_weights", "table_signed_sumW"),
    ("pre_skim_sumW2", "sum_of_weights_squared", "table_sumW2"),
)
SOURCE_BASE = (
    "https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2F"
    "physlitetoopendata/repository/files/"
)
SOURCES = {
    "converter": SOURCE_BASE + "Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0",
    "skim": SOURCE_BASE + "scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0",
    "jet": SOURCE_BASE + "Root%2FJetInfo.cxx/raw?ref=v1.0.0",
    "photon": SOURCE_BASE + "Root%2FPhotonInfo.cxx/raw?ref=v1.0.0",
    "algorithm": SOURCE_BASE + "python%2FPhysLiteToOpenDataAlgorithms.py/raw?ref=v1.0.0",
}
SOURCE_HASHES = {
    "converter": "d17dd6e26f8217bfd967dd4007cbbe1df6e8f742a8a8ee0b3fec6dfd863d0093",
    "skim": "798cc579aaa303be420ca8621d7cb3e1b3ef2cee1f0ecb9d25469a1aba32f6b8",
    "jet": "01325c175a93676dea65f7946dba486bcc1e84c6f7168e694bc3362c05f3a5b5",
    "photon": "9a59853da9c04a428d1990320b680940480bdf723f8d299689ac3bc26e7a8569",
    "algorithm": "5a56eb88d9beb3c472f21defca8f250a7dd3ca63ef60fe08f56cc8183eaf56c3",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def identity(row):
    return tuple(int(row[name]) for name in ("dsid", "entry", "run", "event"))


def moments(values):
    require(all(math.isfinite(v) for v in values), "Non-finite generator value")
    sumw = math.fsum(values)
    sumw2 = math.fsum(v * v for v in values)
    sumabsw = math.fsum(abs(v) for v in values)
    signed_fraction = abs(sumw) / sumabsw if sumabsw else None
    return {
        "entries": len(values),
        "positive": sum(v > 0 for v in values),
        "negative": sum(v < 0 for v in values),
        "zero": sum(v == 0 for v in values),
        "sumW": sumw, "sumW2": sumw2, "sumAbsW": sumabsw,
        "effective_statistics_signed": sumw * sumw / sumw2 if sumw2 else None,
        "absolute_signed_sum_over_sumAbsW": signed_fraction,
        "cancellation_fraction": 1 - signed_fraction if signed_fraction is not None else None,
        "minimum": min(values), "maximum": max(values),
        "usage": "DIAGNOSTIC_ONLY_BOUNDED_POSTSKIM_NOT_NORMALIZATION_DENOMINATOR",
        "sumAbsW_usage": "CANCELLATION_METRIC_ONLY_NO_ABSOLUTE_WEIGHT_REPLACEMENT",
        "definitions": {
            "sumW": "math.fsum of signed preserved mc_weight values",
            "sumW2": "math.fsum of squared signed preserved values; no SF applied",
            "sumAbsW": "math.fsum(abs(weight)) only to quantify signed cancellation",
            "effective_statistics_signed": "sumW^2/sumW2; diagnostic, not generated N",
            "cancellation_fraction": "1-abs(sumW)/sumAbsW; undefined if sumAbsW=0",
        },
    }


def compare_moments(observed, prior):
    result = {"counts_exact": all(
        observed[new] == prior[old] for new, old in (
            ("entries", "entries"), ("positive", "positive"),
            ("negative", "negative"), ("zero", "zero")))}
    for new, old in (
        ("sumW", "sumw"), ("sumW2", "sumw2"),
    ):
        old_value = float(prior[old])
        delta = observed[new] - old_value
        result[new] = {
            "preserved_Phase4_value": old_value,
            "recomputed_fsum_value": observed[new],
            "delta_recomputed_minus_preserved": delta,
            "relative_delta": delta / old_value if old_value else None,
            "exact_equal": delta == 0,
            "interpretation": (
                "EXACT_MATCH" if delta == 0 else
                "DIFFERENCE_RECORDED_NOT_AUTOMATICALLY_ACCEPTED"
            ),
        }
    result["status"] = "PASS" if result["counts_exact"] and all(
        result[field]["exact_equal"] for field in ("sumW", "sumW2")
    ) else "FAIL"
    result["scope"] = "Preserved CSV/JSON evidence consistency; no physical convention validation"
    return result


def ranges(rows):
    values = [float(row["value"]) for row in rows]
    finite = [v for v in values if math.isfinite(v)]
    types = sorted({row["native_type"] for row in rows})
    require(len(types) == 1, "Mixed native types in diagnostic branch")
    require(all(row["usage"] == "NOT_APPLIED" for row in rows), "Applied SF diagnostic")
    return {
        "native_type": types[0], "count": len(values), "finite": len(finite),
        "nonfinite": len(values) - len(finite),
        "positive": sum(v > 0 for v in finite),
        "negative": sum(v < 0 for v in finite),
        "zero": sum(v == 0 for v in finite),
        "minimum": min(finite) if finite else None,
        "maximum": max(finite) if finite else None,
        "usage": "DIAGNOSTIC_ONLY_NOT_APPLIED",
    }


def compare_ranges(observed, prior):
    checks = {
        "native_type_exact": observed["native_type"] == prior["type"],
        "count_exact": observed["count"] == prior["count"],
        "finite_count_exact": observed["finite"] == prior["finite"],
        "negative_count_exact": observed["negative"] == prior["negative"],
        "minimum_exact": observed["minimum"] == prior["minimum"],
        "maximum_exact": observed["maximum"] == prior["maximum"],
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "zero_comparison": "NOT_AVAILABLE_IN_ORIGINAL_PHASE4_JSON_ZERO_COUNT_COMPUTED_FROM_FULL_V2_CSV"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-dir", type=Path, default=Path("outputs/phase4_numerical_v2_20261012"))
    parser.add_argument("--csv", type=Path, default=Path("metadata/phase5_weight_evidence.csv"))
    parser.add_argument("--json", type=Path, default=Path("metadata/phase5_weight_observations.json"))
    args = parser.parse_args()
    repo = args.repo.resolve()
    resolve = lambda path: path.resolve() if path.is_absolute() else repo / path
    run_dir, csv_out, json_out = map(resolve, (args.run_dir, args.csv, args.json))
    require(not csv_out.exists() and not json_out.exists(), "Refusing to overwrite an evidence output")
    original_path = repo / "metadata/phase4_weight_normalization_evidence.json"
    manifest_path = repo / "metadata/phase5_dsid_manifest.csv"
    original = json.loads(original_path.read_text(encoding="utf-8-sig"))
    manifest = {int(row["dsid"]): row for row in read_csv(manifest_path)}
    require(all(dsid in manifest for dsid in (*DSIDS, 302521)), "Incomplete manifest")
    source_inputs = {
        original_path.relative_to(repo).as_posix(): sha(original_path),
        manifest_path.relative_to(repo).as_posix(): sha(manifest_path),
    }
    samples, evidence_rows = {}, []
    columns = (
        "dsid", "ingredient", "evidence_status", "physical_applicability",
        "later_table_candidate", "native_observed_value", "native_type", "count",
        "positive", "negative", "zero", "minimum", "maximum", "sumW", "sumW2",
        "sumAbsW", "effective_statistics_signed", "cancellation_fraction",
        "entry_range", "source_url", "source_version", "source_snapshot_sha256",
        "definition_source_url", "definition_source_version", "definition_source_sha256",
        "input_ROOT_sha256", "local_evidence_path", "local_evidence_sha256",
        "usage", "limitation",
    )

    for dsid in (*DSIDS, 302521):
        metadata = manifest[dsid]
        sample = {
            "input_filename": metadata["filename"],
            "input_ROOT_sha256": metadata["local_ROOT_sha256"] or None,
            "published_checksum": metadata["published_checksum"],
            "record_url": metadata["record_url"],
            "record_response_sha256": metadata["record_response_sha256"],
            "release_filename_tag": metadata["release_filename_tag"],
            "table_generation_tag": metadata["table_e_tag"],
            "exact_release_applicability": "UNKNOWN",
            "absolute_normalization": "BLOCKED",
            "physical_input_status": metadata["physical_input_status"],
        }
        event_path = run_dir / str(dsid) / "reconstruction/events.csv"
        sf_path = run_dir / str(dsid) / "reconstruction/normalization_sf_diagnostics.csv"
        grouped = {}
        if dsid in DSIDS:
            events, diagnostics = read_csv(event_path), read_csv(sf_path)
            event_ids = [identity(row) for row in events]
            require(len(events) == 9900, f"Unexpected event count for {dsid}")
            require([key[1] for key in event_ids] == list(range(100, 10000)), "Non-contiguous entry range")
            require(all(key[0] == dsid for key in event_ids), "DSID mismatch")
            require(len(set(event_ids)) == len(events), "Duplicate event row identity")
            event_set = set(event_ids)
            for row in diagnostics:
                require(identity(row) in event_set, "SF row lacks matching event identity")
                grouped.setdefault(row["branch"], []).append(row)
            needed = {*SF_BRANCHES, *(scalar[1] for scalar in SCALARS)}
            require(needed <= grouped.keys(), f"Missing diagnostic branches: {needed - grouped.keys()}")
            for branch in needed:
                ids = [identity(row) for row in grouped[branch]]
                require(len(ids) == 9900 and len(set(ids)) == 9900 and set(ids) == event_set,
                        f"Incomplete/duplicated SF entry coverage: {dsid}/{branch}")
            sample["generator_observation"] = moments([float(row["mc_weight"]) for row in events])
            sample["original_generator_comparison"] = compare_moments(
                sample["generator_observation"], original[str(dsid)]["generator_diagnostic"])
            sample["scalar_observations"] = {branch: ranges(grouped[branch]) for branch in sorted(needed)}
            sample["original_scalar_comparisons"] = {
                branch: compare_ranges(observed, original[str(dsid)]["native_scalar_ranges"][branch])
                for branch, observed in sample["scalar_observations"].items()
            }
            sample["event_rows"] = len(events)
            sample["diagnostic_rows"] = len(diagnostics)
            sample["entry_range"] = [100, 10000]
            sample["csv_identity_join"] = "PASS_EXACT_DSID_ENTRY_RUN_EVENT"
            for path in (event_path, sf_path):
                source_inputs[path.relative_to(repo).as_posix()] = sha(path)
        else:
            sample.update({"generator_observation": None, "scalar_observations": None,
                           "entry_range": None, "csv_identity_join": "NOT_EVALUATED",
                           "native_observation_status": "NOT_EVALUATED_MISSING_PHYSICAL_INPUT"})

        def emit(ingredient, *, candidate="", observed=None, source="metadata",
                 applicability="UNKNOWN", limitation="", usage="NOT_APPLIED"):
            row = dict.fromkeys(columns, "")
            row.update(dsid=dsid, ingredient=ingredient, physical_applicability=applicability,
                       later_table_candidate=candidate, input_ROOT_sha256=metadata["local_ROOT_sha256"],
                       usage=usage, limitation=limitation)
            row.update(source_url=metadata["metadata_url"] if source == "metadata" else SOURCES[source],
                       source_version=metadata["metadata_version"],
                       source_snapshot_sha256=metadata["metadata_response_sha256"] if source == "metadata" else SOURCE_HASHES[source])
            if candidate:
                row.update(source_url=metadata["metadata_url"], source_snapshot_sha256=metadata["metadata_response_sha256"])
                if source != "metadata":
                    row.update(definition_source_url=SOURCES[source],
                               definition_source_version="v1.0.0_preserved_2026-10-09",
                               definition_source_sha256=SOURCE_HASHES[source])
            if observed is not None:
                row.update(evidence_status="PASS_PRESERVED_CSV_OBSERVATION_ONLY", entry_range="[100,10000)",
                           local_evidence_path=sf_path.relative_to(repo).as_posix(), local_evidence_sha256=source_inputs[sf_path.relative_to(repo).as_posix()])
                for key in ("native_type", "count", "positive", "negative", "zero", "minimum", "maximum"):
                    row[key] = observed[key]
                if observed["minimum"] == observed["maximum"]:
                    row["native_observed_value"] = observed["minimum"]
            else:
                row.update(evidence_status="NOT_EVALUATED_NATIVE" if dsid == 302521 else "UNKNOWN_PHYSICAL_CONVENTION",
                           local_evidence_path=manifest_path.relative_to(repo).as_posix(),
                           local_evidence_sha256=source_inputs[manifest_path.relative_to(repo).as_posix()])
            evidence_rows.append(row)
            return row

        for ingredient, branch, field in SCALARS:
            observed = sample["scalar_observations"][branch] if dsid in DSIDS else None
            row = emit(ingredient, candidate=metadata[field], observed=observed,
                       source="skim" if "skim" in ingredient or ingredient == "generated_event_count" else "converter",
                       limitation="Later table/native field does not verify exact FEB2025 convention, aggregation or completeness")
            if observed is not None:
                native_value = observed["minimum"] if observed["minimum"] == observed["maximum"] else None
                sample.setdefault("table_native_comparison", {})[ingredient] = {
                    "later_table_candidate": metadata[field], "native_constant": native_value,
                    "difference_native_minus_table": native_value - float(metadata[field]) if native_value is not None else None,
                    "relative_difference": (native_value - float(metadata[field])) / float(metadata[field]) if native_value is not None and float(metadata[field]) else None,
                    "exact_applicability": "UNKNOWN_NO_VALUE_REPLACEMENT",
                }
        emit("generator_event_weight_semantics", source="converter",
             limitation="Later converter copies generatorWeight_NOSYS; exact FEB2025 nominal index/meaning UNKNOWN")
        emit("nominal_generator_weight_index", source="converter",
             limitation="No exact FEB2025 nominal index verified; later name is not exact producer proof")
        emit("production_and_generation_tag", candidate=metadata["release_filename_tag"] + ";table:" + metadata["table_e_tag"],
             limitation="Filename release tag and later table e-tag are separate; complete production chain UNKNOWN")
        emit("decay_branching_ratio_convention", candidate=metadata["branching_ratio_convention"],
             limitation="Do not add a branching ratio until exact sigma/filter/forced-decay convention excludes double counting")
        emit("skim_and_processing_completeness", candidate=metadata["skim_completeness"], source="skim",
             limitation="Skim entry count and bounded event moments do not prove complete generated input/CutBookKeeper aggregation")

        for branch in SF_BRANCHES:
            observation = sample["scalar_observations"][branch] if dsid in DSIDS else None
            emit(branch, observed=observation,
                 source="photon" if branch == "ScaleFactor_PHOTON" else
                 "converter" if branch in ("ScaleFactor_FTAG", "ScaleFactor_PILEUP") else "jet",
                 applicability="BLOCKED",
                 limitation="Correction validity, exact producer/object/WP/calibration/sentinel applicability UNKNOWN; values never repaired or applied")
        generator_row = emit("bounded_postskim_generator_moments", source="converter",
                             limitation="9900 inspected entries only; not pre-skim sumW, generated N, full sample, selected-yield prediction or physical semantics validation",
                             usage="DIAGNOSTIC_ONLY_NOT_NORMALIZATION_DENOMINATOR")
        if dsid in DSIDS:
            observation = sample["generator_observation"]
            generator_row.update(evidence_status="PASS_PRESERVED_CSV_OBSERVATION_ONLY",
                                 entry_range="[100,10000)", count=observation["entries"],
                                 local_evidence_path=event_path.relative_to(repo).as_posix(),
                                 local_evidence_sha256=source_inputs[event_path.relative_to(repo).as_posix()])
            for field in ("positive", "negative", "zero", "minimum", "maximum", "sumW", "sumW2", "sumAbsW", "effective_statistics_signed", "cancellation_fraction"):
                generator_row[field] = observation[field]
        samples[str(dsid)] = sample

    integrity_pass = all(samples[str(dsid)]["original_generator_comparison"]["status"] == "PASS"
                         and all(check["status"] == "PASS" for check in samples[str(dsid)]["original_scalar_comparisons"].values())
                         for dsid in DSIDS)
    payload = {
        "project": "ATLAS_HH_BBGG_PUBLIC_V1", "task": "PHASE5_WEIGHT_EVIDENCE_AUDIT",
        "status": "PASS" if integrity_pass else "FAIL",
        "status_scope": "Preserved CSV/JSON consistency and observed diagnostic accounting only",
        "normalization": "BLOCKED", "generator_weight_physical_semantics": "UNKNOWN",
        "signed_preskim_denominator_applicability": "UNKNOWN", "scale_factor_application": "BLOCKED",
        "new_ROOT_entry_reads": 0, "new_network_requests": 0, "signed_values_modified": False,
        "bounded_event_rows": 29700, "source_inputs_sha256": source_inputs,
        "script_sha256": sha(Path(__file__).resolve()),
        "reproduction_command": "python scripts/audit_phase5_weights.py --csv outputs/phase5_weight_audit_reproduced.csv --json outputs/phase5_weight_audit_reproduced.json",
        "output_policy": "Outputs must be new paths; historical evidence is never overwritten",
        "official_sources": {
            key: {"url": value, "version": "v1.0.0_preserved_2026-10-09",
                  "local_snapshot_sha256": SOURCE_HASHES[key],
                  "hash_provenance": "Preserved source audit; not a fresh download or official strong digest"}
            for key, value in SOURCES.items()
        },
        "serialization_note": "CSV versus JSON textual formatting can differ; parsed moments and scalar extrema/types/counts are compared exactly, with all actual deltas recorded",
        "negative_SF_policy": "Negative BTAG scalars are separate from generator signs; no absolute/unity/zero replacement or correction application",
        "samples": samples,
    }
    for path in (csv_out, json_out):
        path.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(evidence_rows)
    with json_out.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": payload["status"], "csv_rows": len(evidence_rows),
                      "event_rows": 29700, "normalization": "BLOCKED"}))
    return 0 if integrity_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prepare bounded real shower references locally; never call Git or releases.

Select whole original HepMC3 ASCII event blocks from a fully validated1000 run.
No particle/event reserialization or physics edits are permitted. Only the gzip
container is changed and non-event evidence paths may use documented placeholders.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

from validate_hepmc3 import iter_ascii, validate_file

REPO = Path(__file__).resolve().parents[3]
MAX_ARCHIVE = 10 * 1024**2
MAX_FULL_TOTAL = 30 * 1024**2
BASELINE_SHA256 = "53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389"
PROFILES = {
    "bbgg": ("pp_bbgg_sm_lo_ps_13tev", "pp_bbgg_sm_lo_13tev", "bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343", 610201),
    "ccgg": ("pp_ccgg_sm_lo_ps_13tev", "pp_ccgg_sm_lo_13tev", "3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef", 610202),
    "jjgg": ("pp_jjgg_light_sm_lo_ps_13tev", "pp_jjgg_light_sm_lo_13tev", "606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030", 610203),
}
PRIVATE = re.compile(r"(?i)(?:/home/(?!\[)[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def check_public_text(data):
    require(PRIVATE.search(data.decode("utf-8")) is None, "private path/credential in selected public artifact")


def select_prefix(source, target, events=100):
    """Write original header, complete selected event blocks and original footer."""
    selected, full_count = [], 0
    full_digest, selected_digest = hashlib.sha256(), hashlib.sha256()
    footer_seen = False
    with Path(target).open("wb") as stream:
        for kind, block in iter_ascii(Path(source)):
            if kind == "header":
                check_public_text(block)
                stream.write(block)
            elif kind == "event":
                full_count += 1
                full_digest.update(block)
                if full_count <= events:
                    check_public_text(block)
                    event_number = int(block.splitlines()[0].split()[1])
                    require(event_number not in selected, "duplicate output event number")
                    selected.append(event_number)
                    selected_digest.update(block)
                    stream.write(block)
            elif kind == "footer":
                require(not footer_seen, "duplicate HepMC footer")
                stream.write(block)
                footer_seen = True
            else:
                raise ValueError("unknown ASCII block type")
    require(footer_seen and len(selected) == events and full_count == 1000,
            "published prefix must come from a complete original1000-event file")
    return {"event_numbers": selected, "actual_events": events, "full_run_events": full_count,
            "event_content_sha256": selected_digest.hexdigest(),
            "full_event_content_sha256": full_digest.hexdigest()}


def deterministic_gzip(source, target):
    with Path(source).open("rb") as src, Path(target).open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as stream:
            shutil.copyfileobj(src, stream, length=1024**2)


def verify_full_gzip(source, expected_sha256, expected_bytes):
    """Bind the retained/release gzip to the physically read-back ASCII file."""
    digest, size = hashlib.sha256(), 0
    with gzip.open(source, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            size += len(chunk)
            require(size <= expected_bytes, "local full gzip expands beyond the verified ASCII file")
            digest.update(chunk)
    require(size == expected_bytes and digest.hexdigest() == expected_sha256,
            "local full gzip differs from the physically validated ASCII file")


def select_ledger(source, target, event_numbers):
    required, rows = set(event_numbers), {}
    with Path(source).open("rb") as stream:
        for raw in stream:
            require(raw.endswith(b"\n"), "truncated event ledger line")
            row = json.loads(raw)
            number = row.get("output_event_index")
            if number in required:
                require(number not in rows, "duplicate output mapping in ledger")
                check_public_text(raw)
                rows[number] = raw
    require(set(rows) == required, "selected output event is missing its source ledger mapping")
    with Path(target).open("wb") as stream:
        for number in event_numbers:
            stream.write(rows[number])


def sanitize_evidence(data, run):
    text = data.decode("utf-8")
    substitutions = {str(run.resolve()): "[LOCAL_RUN_DIRECTORY]", str(REPO): "[REPOSITORY]",
                     str(Path.home()): "[LOCAL_USER_HOME]"}
    for original in sorted(substitutions, key=len, reverse=True):
        text = text.replace(original, substitutions[original])
    published = text.encode("utf-8")
    check_public_text(published)
    return published


def prepare_run(profile, run, stage, publish_full):
    """Create and validate local candidates, returning explicit artifact plans."""
    run, stage = Path(run).resolve(), Path(stage)
    public_dir, input_dir, source_hash, seed = PROFILES[profile]
    source_relative = f"reference_samples/mg5/{input_dir}/reference_1000.lhe.gz"
    source = REPO / source_relative
    require(file_hash(source) == source_hash, "original MG5 source identity mismatch")
    input_manifest = json.loads((source.parent / "sample_manifest.json").read_text())
    input_record = next(s for s in input_manifest["samples"] if s["sample_id"] == "reference_1000")
    local = json.loads((run / "run_manifest.json").read_text())
    require(local["status"] == "PASS", "full shower run is not independently validated PASS")
    require(local["source_sample_id"] == profile and local["source_file_sha256"] == source_hash,
            "run source identity differs from selected MG5 input")
    require(local["pythia_seed"] == seed and local["events_requested"] == 1000 and
            local["input_event_count"] == 1000, "selected full-run seed/count mismatch")
    summary = json.loads((run / "run_summary.json").read_text())
    for key in ("N_attempted", "N_shower_success", "N_written"):
        require(summary[key] == 1000, "incomplete full-run counter: " + key)
    require(summary["N_shower_failed"] == 0, "failed shower inputs may not be silently published as a complete run")
    full = run / "shower.hepmc3"
    ledger = run / "event_ledger.jsonl"
    validated = validate_file(full, 1000, ledger=ledger, source_file=source,
                              source_sha256=source_hash, sample_id=profile, pythia_seed=seed)
    full_hash = file_hash(full)
    verify_full_gzip(run / "shower.hepmc3.gz", full_hash, full.stat().st_size)
    relative = "reference_samples/pythia8/" + public_dir
    evidence_dir = "simulation/pythia8/evidence/" + profile
    prepared, records = {}, []
    stage.mkdir(parents=True)
    cpp_report = run / "physical_validation.json"
    report = json.loads(cpp_report.read_text())
    require(report["validation_status"] == "PASS" and report["N_readback"] == 1000 and report["N_failed_validation"] == 0,
            "actual full1000 HepMC3 ReaderAscii validation is missing or incomplete")
    report_hash = report.get("decompressed_file_sha256", report.get("file_sha256"))
    require(report_hash == full_hash, "ReaderAscii proof is not bound to this exact full ASCII file")
    require(report["validator"] == "actual_HepMC3_ReaderAscii_and_Pythia_ParticleData" and
            report["source_file_sha256"] == source_hash and report["source_sample_id"] == profile and
            report["pythia_seed"] == seed and
            report["pythia_run_id"] == validated["pythia_run_id"] == local["pythia_run_id"],
            "ReaderAscii identity proof does not match the selected real run")
    require(str(local["pythia_version"]) == report["pythia_version"] == "8.317", "Pythia source version differs")
    reported_hepmc_version = local["hepmc3_version"]
    require(tuple(int(component) for component in reported_hepmc_version.split(".")) == (3, 3, 1) and
            tuple(int(component) for component in report["hepmc3_version"].split(".")) == (3, 3, 1),
            "HepMC3 source version differs")
    public_report = sanitize_evidence(cpp_report.read_bytes(), run)
    cpp_path = evidence_dir + "/physical_validation.json"
    prepared[cpp_path] = {"data": public_report}
    settings = run / "settings.cmnd"
    settings_hash = file_hash(settings)
    require(settings_hash == local["settings_sha256"] == BASELINE_SHA256 and
            file_hash(REPO / "simulation/pythia8/config/baseline_shower.cmnd") == BASELINE_SHA256,
            "original settings card differs from the reviewed immutable baseline")
    check_public_text(settings.read_bytes())
    settings_path = evidence_dir + "/settings.cmnd"
    prepared[settings_path] = {"source": settings}
    require(ledger.stat().st_size <= 5 * 1024**2, "full-run source ledger exceeds bounded evidence policy")
    full_ledger_data = ledger.read_bytes()
    check_public_text(full_ledger_data)
    full_ledger_path = evidence_dir + "/event_ledger_1000.jsonl"
    full_ledger_hash = hashlib.sha256(full_ledger_data).hexdigest()
    prepared[full_ledger_path] = {"source": ledger}
    evidence_files = []
    for name in ("effective_settings.cmnd", "effective_particle_data.xml", "run_summary.json"):
        original = run / name
        raw = original.read_bytes()
        require(len(raw) <= 5 * 1024**2, "selected settings/summary evidence exceeds bounded source policy")
        published = sanitize_evidence(raw, run)
        path = evidence_dir + "/" + name
        prepared[path] = {"data": published}
        evidence_files.append({"path": path, "sha256": hashlib.sha256(published).hexdigest(),
                               "original_sha256": hashlib.sha256(raw).hexdigest(),
                               "transformation": "path placeholders only" if raw != published else "NONE"})
    for count in (100, 1000) if publish_full else (100,):
        raw_candidate = stage / f"shower_{count}.hepmc3"
        if count == 100:
            selection = select_prefix(full, raw_candidate, 100)
        else:
            shutil.copyfile(full, raw_candidate)
            numbers = [int(block.splitlines()[0].split()[1]) for kind, block in iter_ascii(full) if kind == "event"]
            selection = {"event_numbers": numbers, "actual_events": 1000, "full_run_events": 1000,
                         "event_content_sha256": validated["event_content_sha256"]}
        selected_ledger = stage / f"event_ledger_{count}.jsonl"
        select_ledger(ledger, selected_ledger, selection["event_numbers"])
        target = stage / f"shower_{count}.hepmc3.gz"
        deterministic_gzip(raw_candidate, target)
        require(target.stat().st_size <= MAX_ARCHIVE, "selected shower archive exceeds10 MiB")
        checked = validate_file(target, count, ledger=selected_ledger, source_file=source,
                               source_sha256=source_hash, sample_id=profile, pythia_seed=seed)
        require(checked["event_content_sha256"] == selection["event_content_sha256"], "selected raw event bytes changed")
        file_relative = relative + f"/shower_{count}.hepmc3.gz"
        ledger_relative = relative + f"/event_ledger_{count}.jsonl"
        prepared[file_relative] = {"source": target}
        prepared[ledger_relative] = {"source": selected_ledger}
        records.append({
            "sample_id": f"shower_{count}", "file": file_relative, "events": count,
            "source_sample_id": profile, "source_file": source_relative, "source_file_sha256": source_hash,
            "source_input_count": 1000, "input_count": 1000,
            "input_xsec_pb": input_record["generator_cross_section_pb"],
            "input_xsec_uncertainty_pb": input_record["cross_section_uncertainty_pb"],
            "pythia_version": local["pythia_version"], "hepmc3_version": "3.3.1",
            "hepmc3_reported_version": reported_hepmc_version,
            "pythia_seed": seed, "seed": seed, "settings_path": settings_path, "settings_sha256": settings_hash,
            "ledger_path": ledger_relative, "ledger_sha256": file_hash(selected_ledger),
            "full_run_ledger_path": full_ledger_path, "full_run_ledger_sha256": full_ledger_hash,
            "full_run_ledger_bytes": len(full_ledger_data), "full_run_ledger_transformation": "NONE; original raw JSONL lines",
            "cpp_report_path": cpp_path, "cpp_report_sha256": hashlib.sha256(public_report).hexdigest(),
            "cpp_report_original_sha256": file_hash(cpp_report), "full_run_events": 1000,
            "full_run_decompressed_file_sha256": full_hash, "full_run_event_content_sha256": validated["event_content_sha256"],
            "subset_of_full_run": {"events": 1000, "decompressed_file_sha256": full_hash,
                                   "event_content_sha256": validated["event_content_sha256"],
                                   "selected_event_numbers": selection["event_numbers"]},
            "compressed_file_sha256": file_hash(target), "decompressed_file_sha256": file_hash(raw_candidate),
            "event_content_sha256": checked["event_content_sha256"], "compressed_bytes": target.stat().st_size,
            "validation_status": "PASS", "portable_validation": checked,
            "physical_validation_scope": "actual full1000 ReaderAscii run; subset event blocks preserved byte-for-byte",
            "statistics": "subset of original1000 LHE hard events; no new independent hard statistics",
            "weight_interpretation": "first weight input_contribution_pb already equals signed LHE_XWGTUP/1000; remaining pb columns retain raw provenance; do not divide or multiply again",
            "publication_transformation": "NONE for event bytes; original ASCII blocks and event numbers; deterministic gzip metadata only",
            "provenance_files": evidence_files,
        })
    public_manifest = {"schema_version": 1, "samples": records,
                       "full_output_local": {"events": 1000, "decompressed_file_sha256": full_hash,
                                             "bytes": full.stat().st_size,
                                             "compressed_file_sha256": file_hash(run / "shower.hepmc3.gz"),
                                             "compressed_bytes": (run / "shower.hepmc3.gz").stat().st_size,
                                             "full_run_ledger_path": full_ledger_path,
                                             "full_run_ledger_sha256": full_ledger_hash,
                                             "full_run_ledger_bytes": len(full_ledger_data),
                                             "published_full": publish_full},
                       "source_sample_id": profile, "physical_validation_status": "PASS",
                       "large_release_status": "NOT_NEEDED" if publish_full else "DRAFT_RELEASE_PROPOSAL_LOCAL_ONLY; no release created"}
    prepared[relative + "/sample_manifest.json"] = {"data": json_bytes(public_manifest)}
    return public_manifest, prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for profile in PROFILES:
        parser.add_argument("--" + profile + "-run", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true", help="validate and prepare temporary candidates without changing public files")
    args = parser.parse_args()
    try:
        runs = {profile: getattr(args, profile + "_run").resolve() for profile in PROFILES}
        full_sizes = {profile: (run / "shower.hepmc3.gz").stat().st_size for profile, run in runs.items()}
        full_allowed = {profile: size <= MAX_ARCHIVE for profile, size in full_sizes.items()}
        if sum(size for profile, size in full_sizes.items() if full_allowed[profile]) > MAX_FULL_TOTAL:
            full_allowed = {profile: False for profile in runs}
        with tempfile.TemporaryDirectory(prefix="atlas-hh-shower-publication-") as temporary:
            manifests, writes = {}, {}
            for profile, run in runs.items():
                manifest, plan = prepare_run(profile, run, Path(temporary) / profile, full_allowed[profile])
                require(not writes.keys() & plan.keys(), "overlapping publication artifacts")
                manifests[profile] = manifest
                writes.update(plan)
            proposed_assets = []
            for profile, manifest in manifests.items():
                if not full_allowed[profile]:
                    output = manifest["full_output_local"]
                    proposed_assets.append({"name": profile + "_shower_1000.hepmc3.gz", "actual_events": 1000,
                                            "compressed_file_sha256": output["compressed_file_sha256"],
                                            "compressed_bytes": output["compressed_bytes"],
                                            "decompressed_file_sha256": output["decompressed_file_sha256"],
                                            "source_file_sha256": PROFILES[profile][2],
                                            "github_asset_size_preflight": "PASS" if output["compressed_bytes"] < 2 * 1024**3 else "FAIL_OVERSIZE"})
            if proposed_assets:
                proposal = {"schema_version": 1, "status": "DRAFT_RELEASE_PROPOSAL_LOCAL_ONLY",
                            "repository": "TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1",
                            "proposed_tag": "phase6b-pythia8-full-1k-v1", "draft": True,
                            "source_commit": "UNKNOWN_PENDING_REMOTE_SEAL", "proposed_assets": proposed_assets,
                            "event_scope": "actual validated1000-run outputs; prefixes share the same hard events",
                            "github_asset_limit_bytes_exclusive": 2 * 1024**3,
                            "github_size_policy_source": "https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases",
                            "release_created": False, "assets_uploaded": False, "git_lfs_enabled": False,
                            "next_action": "User review and explicit authorization required before creating or uploading any large release"}
                writes["simulation/pythia8/evidence/large_output_release_proposal.json"] = {"data": json_bytes(proposal)}
            require(all(not (REPO / path).exists() for path in writes), "existing publication artifacts preserved; no overwrite")
            if not args.dry_run:
                for relative, content in writes.items():
                    target = REPO / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        if "data" in content:
                            stream.write(content["data"])
                        else:
                            with content["source"].open("rb") as original:
                                shutil.copyfileobj(original, stream, length=1024**2)
            print(json.dumps({"status": "PREFLIGHT_PASS_NO_PUBLIC_WRITES" if args.dry_run else "PREPARED_LOCAL_ONLY",
                              "published_full": full_allowed, "artifacts": len(writes),
                              "samples": {profile: [{key: record[key] for key in ("sample_id", "events", "compressed_bytes", "compressed_file_sha256")} for record in manifest["samples"]]
                                          for profile, manifest in manifests.items()}}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, EOFError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

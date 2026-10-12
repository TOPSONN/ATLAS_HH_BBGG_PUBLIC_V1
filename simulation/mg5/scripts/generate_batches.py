#!/usr/bin/env python3
"""Sequential independent MG5 batches. No event concatenation or cross-section summation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from generate_sample import atomic_json, check_output, now, prepare_request, preflight
from installation import verify


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--action", choices=("plan", "run", "status", "stop", "resume", "validate"), default="plan")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--process", default="pp_bbgg")
    parser.add_argument("--events-per-batch", type=int, default=100000)
    parser.add_argument("--batches", type=int, default=10)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--energy", type=float, default=13000)
    parser.add_argument("--run-card", type=Path)
    parser.add_argument("--param-card", type=Path)
    parser.add_argument("--jobs", type=int, default=min(2, os.cpu_count() or 1))
    parser.add_argument("--max-hours", type=float, default=24, help="elapsed limit for each individual batch")
    parser.add_argument("--max-disk-gb", type=float, default=20, help="GiB budget for each individual batch")
    parser.add_argument("--dry-run", action="store_true", help="equivalent to --action plan; generates no events")
    return parser.parse_args()


def batch_snapshot(root, verify_samples=False):
    path = root / "batch_manifest.json"
    if not path.is_file():
        raise ValueError("batch directory has no batch_manifest.json")
    plan = json.loads(path.read_text())
    validate_plan(plan)
    rows, complete_count, event_hashes = [], 0, set()
    for batch in plan["batches"]:
        directory = root / batch["directory"]
        manifest_path = directory / "run_manifest.json"
        row = {"directory": batch["directory"], "seed": batch["seed"], "status": "NOT_STARTED", "actual_events": 0}
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("request") != batch["request"]:
                raise ValueError("batch run request differs from frozen plan")
            row["status"] = manifest.get("status", "INVALID_MANIFEST")
            if row["status"] == "PASS":
                if manifest.get("random_seed") != batch["seed"] or manifest.get("events_requested") != batch["events"]:
                    raise ValueError("batch manifest seed/count differs from frozen plan")
                if verify_samples:
                    from validate_sample import validate_run
                    validated = validate_run(directory)
                    row["actual_events"] = validated["actual_events"]
                    row["compressed_file_sha256"] = validated["compressed_file_sha256"]
                    row["cross_section_pb"] = validated["cross_section_pb"]
                    row["cross_section_uncertainty_pb"] = validated["cross_section_uncertainty_pb"]
                    event_hash = validated["event_content_sha256"]
                    if event_hash in event_hashes:
                        raise ValueError("duplicate event content across supposedly independent batches")
                    event_hashes.add(event_hash)
                    row["event_content_sha256"] = event_hash
                else:
                    row["actual_events"] = manifest.get("validation", {}).get("actual_events", 0)
                    row["cross_section_pb"] = manifest.get("validation", {}).get("cross_section_pb")
                complete_count += row["actual_events"]
        rows.append(row)
    return {"status": "PASS" if verify_samples and complete_count == plan["target_events"] and
            all(row["status"] == "PASS" for row in rows) else "INCOMPLETE" if verify_samples else "MANIFEST_SNAPSHOT",
            "target_events": plan["target_events"], "complete_events": complete_count,
            "counts_independently_validated": verify_samples,
            "reference_samples_included": False, "batches": rows,
            "cross_section_combination": "NOT_COMPUTED; repeated-process cross sections must never be summed",
            "event_concatenation": "NOT_PERFORMED; each batch is an independent complete LHE file"}


def plan_fingerprint(rows):
    values = [{key: value for key, value in row.items() if key != "command"} for row in rows]
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def validate_plan(plan):
    rows = plan.get("batches")
    if not isinstance(rows, list) or not rows or plan.get("batch_count") != len(rows):
        raise ValueError("invalid batch count in saved plan")
    seeds, total = set(), 0
    for index, row in enumerate(rows):
        if row.get("directory") != f"batch_{index + 1:02d}":
            raise ValueError("saved batch directory does not match its safe sequential name")
        seed, events, request = row.get("seed"), row.get("events"), row.get("request", {})
        if not isinstance(seed, int) or isinstance(seed, bool) or not 1 <= seed <= 30081 ** 2 or seed in seeds:
            raise ValueError("saved batch seeds must be distinct and in range")
        if not isinstance(events, int) or isinstance(events, bool) or events <= 0:
            raise ValueError("saved batch event count must be positive")
        if request.get("random_seed") != seed or request.get("events_requested") != events:
            raise ValueError("saved batch request seed/count mismatch")
        seeds.add(seed)
        total += events
    if plan.get("target_events") != total or plan.get("plan_sha256") != plan_fingerprint(rows):
        raise ValueError("saved batch target or plan SHA256 mismatch")


def make_plan(args, config):
    root = args.output.resolve()
    check_output(root, config)
    if args.batches <= 0 or args.batches > 10000:
        raise ValueError("batches must be in [1, 10000]")
    if args.events_per_batch <= 0 or not 1 <= args.seed <= args.seed + args.batches - 1 <= 30081 ** 2:
        raise ValueError("positive events and distinct in-range seeds are required for all batches")
    requests = []
    common = ["--installation", str(args.installation.resolve()), "--process", args.process,
              "--energy", str(args.energy), "--jobs", str(args.jobs),
              "--max-hours", str(args.max_hours), "--max-disk-gb", str(args.max_disk_gb)]
    for path, flag in ((args.run_card, "--run-card"), (args.param_card, "--param-card")):
        if path:
            common.extend([flag, str(path.resolve())])
    if args.process not in {"pp_bbgg", "pp_diphoton"}:
        common[common.index("--process") + 1] = str(Path(args.process).resolve())
    for index in range(args.batches):
        name = f"batch_{index + 1:02d}"
        sample_args = argparse.Namespace(**vars(args))
        sample_args.events = args.events_per_batch
        sample_args.seed = args.seed + index
        sample_args.output = root / name
        _, _, _, _, request, _ = prepare_request(sample_args, config)
        command = [sys.executable, str(Path(__file__).with_name("generate_sample.py")), *common,
                   "--events", str(args.events_per_batch), "--seed", str(sample_args.seed),
                   "--output", str(sample_args.output)]
        requests.append({"directory": name, "seed": sample_args.seed, "events": args.events_per_batch,
                         "request": request, "command": command})
    fingerprint = plan_fingerprint(requests)
    return {"schema_version": 1, "status": "PLANNED", "target_events": args.batches * args.events_per_batch,
            "batch_count": args.batches, "batches": requests, "plan_sha256": fingerprint,
            "resources": preflight(root, args), "jobs_are_per_batch": True,
            "execution_mode": "sequential independent complete samples", "publication": "LOCAL_ONLY",
            "reference_samples_included": False, "cross_sections": "stored per batch; never summed"}


def run_batches(root, plan, resume):
    previous_path = root / "batch_manifest.json"
    if root.exists():
        if not resume or not previous_path.is_file():
            raise ValueError("batch output exists; use --action resume with its identical frozen plan")
        previous = json.loads(previous_path.read_text())
        validate_plan(previous)
        if previous["plan_sha256"] != plan["plan_sha256"]:
            raise ValueError("resume plan differs; use the exact original batch options")
        if previous.get("status") == "RUNNING":
            pid = previous.get("controller_pid")
            if not isinstance(pid, int) or pid <= 0:
                raise ValueError("running batch manifest has no valid controller PID")
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise ValueError("another batch controller is running")
    elif resume:
        raise ValueError("resume requires an existing batch directory")
    root.mkdir(parents=True, exist_ok=True)
    if (root / "STOP").exists():
        (root / "STOP").rename(root / f"STOP_consumed_{time.time_ns()}")
    plan.update(status="RUNNING", controller_pid=os.getpid(), started_utc=now())
    atomic_json(previous_path, plan)
    stopping = False

    def stop_signal(signum, frame):
        nonlocal stopping
        stopping = True

    handlers = {s: signal.signal(s, stop_signal) for s in (signal.SIGINT, signal.SIGTERM)}
    child = None
    try:
        for batch in plan["batches"]:
            if stopping or (root / "STOP").exists():
                raise RuntimeError("batch stop requested; remaining batches were not started")
            directory = root / batch["directory"]
            command = list(batch["command"])
            if directory.exists():
                command.append("--resume")
            plan.update(current_batch=batch["directory"], updated_utc=now())
            atomic_json(previous_path, plan)
            child = subprocess.Popen(command)
            stop_sent = False
            while child.poll() is None:
                if (stopping or (root / "STOP").exists()) and not stop_sent:
                    # Never create a STOP-only directory before the child has
                    # initialized its manifest: that would block safe resume.
                    if (directory / "run_manifest.json").is_file():
                        (directory / "STOP").touch()
                    child.send_signal(signal.SIGTERM)
                    stop_sent = True
                time.sleep(0.25)
            if child.returncode:
                raise RuntimeError(f"batch {batch['directory']} stopped/failed with exit {child.returncode}; inspect its manifest")
            child = None
        snapshot = batch_snapshot(root, verify_samples=True)
        if snapshot["status"] != "PASS":
            raise RuntimeError("independent final batch validation did not reach the planned event count")
        plan.update(status="PASS", completed_utc=now(), validation=snapshot)
        atomic_json(previous_path, plan)
        print(json.dumps(snapshot, indent=2))
        return 0
    except BaseException as exc:
        if child and child.poll() is None:
            child.send_signal(signal.SIGTERM)
            child.wait()
        plan.update(status="PARTIAL_STOPPED" if stopping or (root / "STOP").exists() else "PARTIAL_FAILED",
                    failure=str(exc), updated_utc=now())
        atomic_json(previous_path, plan)
        raise
    finally:
        for s, handler in handlers.items():
            signal.signal(s, handler)


def main():
    args = parse_args()
    root = args.output.resolve()
    if args.action in {"status", "stop", "validate"} and not args.dry_run:
        config = json.loads(args.installation.read_text())
        check_output(root, config)
        if args.action == "stop":
            if not (root / "batch_manifest.json").is_file():
                raise ValueError("not a manifested batch directory")
            (root / "STOP").touch()
            print("Stop requested; controller will stop its active batch and preserve all attempts")
            return 0
        snapshot = batch_snapshot(root, verify_samples=args.action == "validate")
        print(json.dumps(snapshot, indent=2))
        return 0 if args.action == "status" or snapshot["status"] == "PASS" else 1
    config = json.loads(args.installation.read_text())
    verify(config)
    plan = make_plan(args, config)
    if args.action == "plan" or args.dry_run:
        print(json.dumps(plan, indent=2))
        return 0
    return run_batches(root, plan, args.action == "resume")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Streaming, user-initiated external-LHE shower with independent readback.

No hard-event generation, automatic publication, event replacement or repair.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

from validate_lhe_stream import file_sha256, iter_lhe_events, open_lhe

REPO = Path(__file__).resolve().parents[3]
SCRIPTS = Path(__file__).resolve().parent
BASELINE = SCRIPTS.parent / "config/baseline_shower.cmnd"
BASELINE_SHA256 = "53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389"
REFERENCE_INPUTS = {
    "bbgg": ("reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz",
             "bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343"),
    "ccgg": ("reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz",
             "3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef"),
    "jjgg": ("reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz",
             "606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030"),
}


def atomic_json(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def safe_output(output, config):
    require(not output.exists(), f"Output exists; choose a new directory: {output}")
    require(not any(c.isspace() for c in str(output)) and not any(c in str(output) for c in "\n\r\"';"),
            "output path contains unsupported whitespace/metacharacters")
    for root in (REPO, Path(config["pythia_prefix"]).resolve(), Path(config["hepmc3_prefix"]).resolve()):
        require(output != root and root not in output.parents and output not in root.parents,
                "output must be outside Git and installed tool directories")


def resources(output):
    ancestor = output
    while not ancestor.exists():
        ancestor = ancestor.parent
    disk = shutil.disk_usage(ancestor)
    require(disk.free >= 1024 ** 3, "less than 1 GiB free on output filesystem")
    memory = {}
    if Path("/proc/meminfo").is_file():
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            if key in ("MemAvailable", "MemTotal"):
                memory[key] = int(value.split()[0]) * 1024
    require(memory.get("MemAvailable", 1024 ** 3) >= 512 * 1024 ** 2, "less than 512 MiB available RAM")
    return {"jobs": 1, "available_logical_cpus": os.cpu_count(), "disk_free_bytes": disk.free,
            "ram_available_bytes": memory.get("MemAvailable", "UNKNOWN"),
            "ram_total_bytes": memory.get("MemTotal", "UNKNOWN"),
            "predicted_hepmc_bytes": "UNKNOWN", "predicted_runtime_seconds": "UNKNOWN",
            "prediction_basis": "No production throughput extrapolation; actual run metrics are recorded"}


def verify_installation(config):
    require(config["pythia_version"] == "8.317" and config["hepmc3_version"] == "3.3.1", "unverified library version")
    require(config["pythia_source_commit"] == "83a5c9986f30746cfb390435a9b10ac55a758fca" and
            config["hepmc3_source_commit"] == "beb66aa1a2ac263066becdee26d18ead83edec95", "source identity mismatch")
    for table in ("library_sha256", "header_sha256", "xml_sha256"):
        require(config.get(table), "installation lacks recorded " + table)
        for name, expected in config[table].items():
            require(file_sha256(name) == expected, "installed library/header changed: " + Path(name).name)
    runner, validator = Path(config["runner_path"]), Path(config["validator_path"])
    require(runner.is_file() and validator.is_file(), "build the real runner and independent ReaderAscii validator first")
    build = json.loads(subprocess.check_output([str(runner), "--build-info"], text=True))
    require(build["pythia_version_integer"] == 8317 and build["hepmc3_version"] == "3.03.01" and
            build["cxx_standard"] >= 202002, "runner binary version/ABI metadata mismatch")
    dependencies = {}
    for binary in (runner, validator):
        loaded = subprocess.check_output(["ldd", str(binary)], text=True)
        require("not found" not in loaded, "runner/validator runtime dependency missing")
        for line in loaded.splitlines():
            if "libpythia8.so" in line or "libHepMC3.so" in line:
                require("=>" in line, "unresolved scientific runtime library")
                path = Path(line.split("=>", 1)[1].split()[0]).resolve()
                permitted = {Path(name).resolve() for name in config["library_sha256"]}
                require(path in permitted, "binary loaded an unverified Pythia/HepMC library")
        dependencies[binary.name] = loaded
    return {"binary_build_info": build, "runner_sha256": file_sha256(runner),
            "reader_validator_sha256": file_sha256(validator), "runtime_dependencies": dependencies}


def input_preflight(path, profile, expected, timeout):
    code = ("import json,sys; from validate_lhe_stream import validate_lhe_stream; "
            "print(json.dumps(validate_lhe_stream(sys.argv[1],sys.argv[2],sys.argv[3] or None)))")
    result = subprocess.run([sys.executable, "-c", code, str(path), profile, expected or ""],
                            cwd=SCRIPTS, text=True, capture_output=True, timeout=timeout)
    require(result.returncode == 0, "original LHE validation failed: " + result.stderr[-3000:])
    return json.loads(result.stdout)


class StopRun(RuntimeError):
    pass


class Monitor:
    def __init__(self, output, args, manifest, started=None):
        self.output, self.args, self.manifest = output, args, manifest
        self.started = time.monotonic() if started is None else started
        self.last_disk = -10
        self.stopped = False
        self.handlers = {s: signal.signal(s, self.signal_handler) for s in (signal.SIGINT, signal.SIGTERM)}

    def signal_handler(self, signum, frame):
        self.stopped = True

    def restore(self):
        for s, previous in self.handlers.items():
            signal.signal(s, previous)

    def check(self, force=False):
        elapsed = time.monotonic() - self.started
        if self.stopped or (self.output / "STOP").exists():
            raise StopRun("PARTIAL_STOPPED: stop requested; real files retained")
        if elapsed > self.args.max_hours * 3600:
            raise StopRun("PARTIAL_TIMEOUT: elapsed limit reached; real files retained")
        if force or elapsed - self.last_disk >= 5:
            self.last_disk = elapsed
            size = 0
            for folder, _, names in os.walk(self.output, followlinks=False):
                for name in names:
                    path = Path(folder) / name
                    try:
                        if not path.is_symlink():
                            size += path.stat().st_size
                    except FileNotFoundError:
                        pass
            free = shutil.disk_usage(self.output).free
            self.manifest.update(elapsed_seconds=elapsed, output_bytes=size, available_disk_bytes=free)
            atomic_json(self.output / "run_manifest.json", self.manifest)
            if size > self.args.max_disk_gb * 1024 ** 3 or free < 256 * 1024 ** 2:
                raise StopRun("PARTIAL_DISK: output budget/free-disk reserve reached")

    def run(self, command, phase):
        self.manifest["phase"] = phase
        self.check(force=True)
        started = time.monotonic()
        with (self.output / (phase + ".log")).open("wb") as log:
            child = subprocess.Popen(command, cwd=self.output, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            self.manifest["process_group_id"] = child.pid
            atomic_json(self.output / "run_manifest.json", self.manifest)
            try:
                while child.poll() is None:
                    self.check()
                    time.sleep(0.25)
            except BaseException:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                raise
        self.manifest.pop("process_group_id", None)
        self.manifest["execution"][phase] = {"exit_code": child.returncode, "elapsed_seconds": time.monotonic() - started}
        self.check(force=True)
        return child.returncode


def prepare_source(original, output, validation, monitor):
    plain = output / "input.lhe"
    digest = hashlib.sha256()
    with open_lhe(original) as source, plain.open("wb") as target:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            target.write(chunk)
            digest.update(chunk)
            monitor.check()
    require(digest.hexdigest() == validation["decompressed_file_sha256"], "scratch LHE bytes differ from original validated source")
    with (output / "source_index.dat").open("w") as index, (output / "source_events.jsonl").open("w") as events:
        count = 0
        for source in iter_lhe_events(plain):
            rows = source["rows"]
            numbers = [str(rows[0][0]), str(rows[0][1])] + [format(float(value.replace("D", "e").replace("d", "e")), ".17g") for value in rows[0][2:]]
            index.write("E " + str(source["source_event_index"]) + " " + source["source_event_content_hash"] + " " + " ".join(numbers) + "\n")
            particles = []
            for row in rows[1:]:
                values = list(row[:6]) + [format(float(value.replace("D", "e").replace("d", "e")), ".17g") for value in row[6:]]
                index.write("P " + " ".join(values) + "\n")
                particles.append({"pdg_id": int(row[0]), "status": int(row[1]), "mothers": [int(row[2]), int(row[3])],
                                  "colors": [int(row[4]), int(row[5])],
                                  "p4_and_mass_gev": [float(value.replace("D", "e").replace("d", "e")) for value in row[6:11]]})
            events.write(json.dumps({key: source[key] for key in ("source_event_index", "source_event_content_hash", "nominal_generator_weight", "scale_gev")} |
                                    {"particles": particles}, sort_keys=True) + "\n")
            count += 1
            monitor.check()
    require(count == validation["actual_events"], "source index count differs from original source")
    require(file_sha256(original) == validation["compressed_file_sha256"], "original source changed while preparing the run")
    return plain


def gzip_output(source, target, monitor):
    with source.open("rb") as incoming, target.open("wb") as packed:
        with gzip.GzipFile(filename="", mode="wb", fileobj=packed, compresslevel=9, mtime=0) as compressed:
            for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
                compressed.write(chunk)
                monitor.check()


def record_physical_validation(manifest, report_path, exit_code):
    """Keep observed reader/event failure counts; never invent an event count.

    A nonzero validator exit alone proves a failed invocation, not how many
    event records failed. The real ReaderAscii report supplies those counts.
    """
    manifest["physical_validator_exit_code"] = exit_code
    if report_path.is_file():
        report = json.loads(report_path.read_text())
        manifest["physical_validation"] = report
        for key in ("N_readback", "N_passed_validation", "N_failed_validation", "N_not_assessed",
                    "mass_shell_failed_particle_count"):
            if key in report:
                manifest[key] = report[key]
        return report
    manifest.update(N_readback="UNKNOWN", N_failed_validation="UNKNOWN",
                    physical_validation={"validation_status": "FAIL", "diagnostic": "validator did not produce event-count evidence"})
    return None


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--process", choices=REFERENCE_INPUTS, required=True)
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--settings", type=Path, default=BASELINE)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--max-hours", type=float, default=1)
    parser.add_argument("--max-disk-gb", type=float, default=5, help="entire local run-directory budget in GiB")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    require(args.jobs == 1, "this deterministic runner supports --jobs 1 only; separate runs may be launched manually")
    require(args.events > 0 and 1 <= args.seed <= 900000000, "positive events and a fixed seed in [1,900000000] are required")
    require(all(math.isfinite(value) and value > 0 for value in (args.max_hours, args.max_disk_gb)), "finite positive resource limits required")
    require(args.input.is_file() and args.settings.is_file(), "input or settings file missing")
    require(file_sha256(BASELINE) == BASELINE_SHA256, "repository baseline card differs from the immutable reviewed version")
    require(file_sha256(args.settings) == BASELINE_SHA256, "only the immutable reviewed baseline settings card is supported in Phase 6B")
    config = json.loads(args.installation.read_text())
    output = (args.output or Path.home() / "simulations/pythia8_runs" / f"{args.process}_{args.events}_seed{args.seed}_{time.strftime('%Y%m%dT%H%M%S')}").resolve()
    safe_output(output, config)
    resource_info = resources(output)
    software = verify_installation(config)
    canonical, expected = REFERENCE_INPUTS[args.process]
    known_reference = args.input.resolve() == (REPO / canonical).resolve()
    remaining = args.max_hours * 3600 - (time.monotonic() - started)
    require(remaining > 0, "preflight exceeded max-hours; no events processed")
    validation = input_preflight(args.input.resolve(), args.process, expected if known_reference else None, remaining)
    require(args.events <= validation["actual_events"], "requested event limit exceeds verified LHE source count")
    resource_info["lhe_decompressed_bytes"] = validation["decompressed_bytes"]
    dry_command = [config["runner_path"], "--xml", config["xml_path"], "--settings", str(args.settings.resolve()), "--seed", str(args.seed), "--dry-run"]
    remaining = args.max_hours * 3600 - (time.monotonic() - started)
    require(remaining > 0, "preflight exceeded max-hours; no events processed")
    settings_check = subprocess.run(dry_command, text=True, capture_output=True, timeout=min(remaining, 60))
    require(settings_check.returncode == 0, "installed Pythia settings preflight failed: " + settings_check.stderr[-2000:])
    if args.dry_run:
        print(json.dumps({"status": "DRY_RUN", "events_processed": 0, "events_requested": args.events,
                          "input_event_count": validation["actual_events"], "input_sha256": validation["compressed_file_sha256"],
                          "settings_readback": json.loads(settings_check.stdout), "resources": resource_info,
                          "library_build_info": software["binary_build_info"]}, indent=2))
        return 0
    output.mkdir(parents=True)
    source_file = canonical if known_reference else str(args.input.resolve())
    run_identity = json.dumps({"input": validation["compressed_file_sha256"], "settings": file_sha256(args.settings),
                               "process": args.process, "seed": args.seed, "events": args.events,
                               "pythia": config["pythia_version"], "hepmc3": config["hepmc3_version"]}, sort_keys=True)
    manifest = {"schema_version": 1, "status": "RUNNING", "publication": "LOCAL_ONLY", "source_sample_id": args.process,
                "source_file": source_file, "source_file_sha256": validation["compressed_file_sha256"],
                "source_decompressed_sha256": validation["decompressed_file_sha256"], "input_event_count": validation["actual_events"],
                "events_requested": args.events, "pythia_seed": args.seed,
                "pythia_run_id": str(uuid.uuid5(uuid.NAMESPACE_URL, run_identity)), "execution_id": str(uuid.uuid4()),
                "pythia_version": config["pythia_version"], "hepmc3_version": config["hepmc3_version"],
                "input_cross_section_pb": validation["cross_section_pb"],
                "input_cross_section_uncertainty_pb": validation["cross_section_uncertainty_pb"],
                "settings_sha256": file_sha256(args.settings), "settings_file": "settings.cmnd",
                "resource_limits": {"jobs": 1, "max_hours": args.max_hours, "max_disk_gb": args.max_disk_gb},
                "resources_preflight": resource_info, "software": software, "source_identity": config,
                "execution": {}, "original_hard_sample_status": "EXISTING_MG5_INPUT_REUSED_WITHOUT_GENERATION",
                "normalization_denominator": "full original LHE event count, including for prefix runs"}
    atomic_json(output / "run_manifest.json", manifest)
    monitor = Monitor(output, args, manifest, started=started)
    try:
        shutil.copyfile(args.settings, output / "settings.cmnd")
        card_dir = output / "source_cards"
        card_dir.mkdir()
        for key, name in (("process_card", "proc_card_mg5.dat"), ("run_card", "run_card.dat"), ("param_card", "param_card.dat")):
            (card_dir / name).write_text(validation["cards"][key])
        original = args.input.resolve()
        plain = prepare_source(original, output, validation, monitor)
        command = [config["runner_path"], "--input", str(plain), "--source-index", str(output / "source_index.dat"),
                   "--events", str(args.events), "--source-total", str(validation["actual_events"]), "--seed", str(args.seed),
                   "--settings", str(output / "settings.cmnd"), "--xml", config["xml_path"], "--output", str(output),
                   "--source-sha256", manifest["source_file_sha256"], "--sample-id", args.process, "--run-id", manifest["pythia_run_id"],
                   "--source-sigma-pb", str(validation["cross_section_pb"]), "--source-error-pb", str(validation["cross_section_uncertainty_pb"]),
                   "--max-hours", str(args.max_hours), "--max-disk-gb", str(args.max_disk_gb)]
        atomic_json(output / "runner_command.json", command)
        exit_code = monitor.run(command, "shower")
        require((output / "run_summary.json").is_file(), f"runner failed without completed counters (exit {exit_code}); inspect shower.log")
        summary = json.loads((output / "run_summary.json").read_text())
        manifest["counters"] = summary
        written = summary["N_written"]
        require(written > 0, "no showered outputs; partial evidence retained")
        physical_command = [config["validator_path"], "--input", str(output / "shower.hepmc3"), "--events", str(written),
                            "--xml", config["xml_path"], "--report", str(output / "physical_validation.json"),
                            "--source-sha256", manifest["source_file_sha256"], "--sample-id", args.process, "--seed", str(args.seed)]
        physical_exit = monitor.run(physical_command, "physical_readback")
        physical = record_physical_validation(manifest, output / "physical_validation.json", physical_exit)
        require(physical_exit == 0 and physical is not None and physical["validation_status"] == "PASS",
                "independent HepMC3 ReaderAscii validation failed; exact failure counts/details retained; inspect physical_readback.log")
        gzip_output(output / "shower.hepmc3", output / "shower.hepmc3.gz", monitor)
        portable_command = [sys.executable, str(SCRIPTS / "validate_hepmc3.py"), "--file", str(output / "shower.hepmc3.gz"),
                            "--events", str(written), "--ledger", str(output / "event_ledger.jsonl"), "--source-file", str(original),
                            "--source-sha256", manifest["source_file_sha256"], "--sample-id", args.process, "--seed", str(args.seed),
                            "--max-decompressed-gb", str(args.max_disk_gb),
                            "--report", str(output / "portable_validation.json")]
        require(monitor.run(portable_command, "portable_readback") == 0, "independent source-ledger/ASCII validation failed; inspect portable_readback.log")
        portable = json.loads((output / "portable_validation.json").read_text())
        require(physical["decompressed_file_sha256"] == portable["decompressed_file_sha256"] == file_sha256(output / "shower.hepmc3"),
                "physical and portable validators did not inspect identical output bytes")
        require(file_sha256(original) == manifest["source_file_sha256"], "original MG5 input changed during showering")
        manifest.update(physical_validation=physical, portable_validation=portable,
                        N_readback=physical["N_readback"], N_failed_validation=physical["N_failed_validation"],
                        peak_rss_bytes=summary["peak_rss_bytes"], elapsed_seconds=time.monotonic() - monitor.started)
        complete = exit_code == 0 and summary["status"] == "PASS" and written == args.events and summary["N_input"] == args.events and summary["N_shower_failed"] == 0
        manifest["status"] = "PASS" if complete else "PARTIAL"
        manifest["files"] = {name: {"sha256": file_sha256(output / name), "bytes": (output / name).stat().st_size}
                             for name in ("shower.hepmc3", "shower.hepmc3.gz", "event_ledger.jsonl", "particle_diagnostics.jsonl", "source_events.jsonl",
                                          "settings.cmnd", "effective_settings.cmnd", "effective_particle_data.xml", "physical_validation.json", "portable_validation.json", "run_summary.json")}
        monitor.check(force=True)
        atomic_json(output / "run_manifest.json", manifest)
        print(f"{manifest['status']}: {written}/{args.events} verified showered {args.process} outputs; original source={validation['actual_events']} events")
        print(f"Local HepMC3: {output / 'shower.hepmc3.gz'}")
        print("SHA256: " + manifest["files"]["shower.hepmc3.gz"]["sha256"])
        return 0 if complete else 2
    except BaseException as error:
        manifest.update(status="PARTIAL" if isinstance(error, StopRun) or (output / "shower.hepmc3").exists() else "FAILED",
                        diagnostic=str(error), elapsed_seconds=time.monotonic() - monitor.started)
        if (output / "run_summary.json").is_file():
            manifest["counters"] = json.loads((output / "run_summary.json").read_text())
        atomic_json(output / "run_manifest.json", manifest)
        raise
    finally:
        monitor.restore()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        raise SystemExit(1)

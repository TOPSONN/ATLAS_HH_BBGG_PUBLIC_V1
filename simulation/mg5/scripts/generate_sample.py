#!/usr/bin/env python3
"""Generate one independently validated local sample using the installed MG5.

Resume preserves failed attempts and starts a new attempt. It does not claim to
resume an interrupted MG5 integration or merge partially generated event files.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

from installation import verify
from validate_lhe import canonical_card, integer, number, run_values

REPO = Path(__file__).resolve().parents[3]
DEFAULT_RUN_ROOT = Path.home() / "simulations/mg5_runs"
PROFILES = {
    "bbgg": ("generate p p > b b~ a a QCD=2 QED=2", [5, -5, 22, 22]),
    "diphoton": ("generate p p > a a QCD=0 QED=2", [22, 22]),
}
ALIASES = {"pp_bbgg": "bbgg.mg5", "pp_diphoton": "diphoton.mg5"}
BASE_SETTINGS = {
    "lpp1": 1, "lpp2": 1, "pdlabel": "cteq6l1", "lhaid": 10042,
    "fixed_ren_scale": True, "fixed_fac_scale": True, "scale": 125.0,
    "dsqrt_q2fact1": 125.0, "dsqrt_q2fact2": 125.0,
    "dynamical_scale_choice": -1, "scalefact": 1.0,
    "pta": 25.0, "ptb": 20.0, "etaa": 2.5, "etab": 5.0,
    "draa": 0.4, "drab": 0.4, "drbb": 0.4, "ptgmin": 0.0,
    "ickkw": 0, "use_syst": False, "systematics_program": "none",
    "event_norm": "average", "maxjetflavor": 4,
}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gzip_deterministic(data):
    """Compatibility helper for the deliberately small reference publisher."""
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0) as stream:
        stream.write(data)
    return buffer.getvalue()


def atomic_json(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def profile_from_card(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^# validation_profile: (\w+)$", text, re.M)
    if not match or match[1] not in PROFILES:
        raise ValueError("Unknown validation profile; follow USER_GUIDE_ZH_TW before adding a process")
    profile = match[1]
    commands = [line.split("#", 1)[0].strip() for line in text.splitlines()
                if line.split("#", 1)[0].strip()]
    expected = ["import model sm-no_b_mass", "define p = g u c d s b u~ c~ d~ s~ b~",
                PROFILES[profile][0]]
    if commands != expected:
        raise ValueError("Process card differs from an implemented, reviewed physics profile")
    return profile, commands


def validate_cuts(values, profile):
    keys = ["pta", "etaa", "draa"]
    if profile == "bbgg":
        keys += ["ptb", "etab", "drbb", "drab"]
        if number(values.get("maxjetflavor", "0")) != 4:
            raise ValueError("bbgg requires maxjetflavor=4 to apply the documented b-specific cuts")
    if any(number(values.get(key, "0")) <= 0 for key in keys):
        raise ValueError("profile requires finite positive pT/eta/DeltaR generation cuts")
    if number(values.get("ptgmin", "0")) != 0:
        raise ValueError("smooth-cone isolation requires a separately reviewed validation profile")
    if values.get("pdlabel", "").lower() != "cteq6l1" or integer(values.get("lhaid", "0")) != 10042:
        raise ValueError("this profile requires the installed built-in CTEQ6L1 (10042) PDF")
    if integer(values.get("lpp1", "0")) != 1 or integer(values.get("lpp2", "0")) != 1:
        raise ValueError("this profile requires proton/proton beams")
    if integer(values.get("ickkw", "0")) != 0:
        raise ValueError("matching/merging is outside the reviewed LO profile")


def validate_param_card(path):
    block, masses, yukawa = None, {}, {}
    for line in path.read_text().splitlines():
        row = line.split("#", 1)[0].split()
        if not row:
            continue
        if row[0].lower() == "block":
            if len(row) < 2:
                raise ValueError("malformed parameter block")
            block = row[1].lower()
        elif row[0].lower() == "decay":
            if len(row) < 3 or number(row[2]) < 0:
                raise ValueError("invalid decay width")
            block = "decay"
        elif block in {"mass", "sminputs", "yukawa"}:
            if len(row) != 2:
                raise ValueError("malformed parameter value")
            key, value = integer(row[0]), number(row[1])
            if block == "mass":
                if key in masses or value < 0:
                    raise ValueError("duplicate or negative mass parameter")
                masses[key] = value
            elif block == "yukawa":
                yukawa[key] = value
            elif value <= 0:
                raise ValueError("SMINPUTS must be finite and positive")
    # sm-no_b_mass removes the fixed-zero b Yukawa entry from the active card.
    if any(masses.get(pdg) != 0 for pdg in (1, 2, 3, 4, 5, 21, 22)) or yukawa.get(5, 0) != 0:
        raise ValueError("parameter card must retain massless five-flavour partons and zero b Yukawa")


def is_within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def check_output(output, config):
    if any(char.isspace() for char in str(output)) or any(c in str(output) for c in "\n\r;\"'"):
        raise ValueError("MG5 output path must not contain whitespace or shell metacharacters")
    protected = [REPO, Path(config["mg5_path"]).resolve(), Path(config["toolchain_prefix"]).resolve()]
    if any(is_within(output, root) or is_within(root, output) for root in protected):
        raise ValueError("sample output must be outside the Git repository and installed tool directories")


def existing_parent(path):
    parent = path
    while not parent.exists():
        if parent.parent == parent:
            raise ValueError("no existing output filesystem ancestor")
        parent = parent.parent
    if not parent.is_dir():
        raise ValueError("output ancestor is not a directory")
    return parent


def preflight(output, args):
    usage = shutil.disk_usage(existing_parent(output))
    memory = {}
    if Path("/proc/meminfo").is_file():
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            if key in ("MemTotal", "MemAvailable"):
                memory[key] = int(value.split()[0]) * 1024
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
    if not 1 <= args.jobs <= cpus:
        raise ValueError(f"jobs must be in [1, {cpus}] available logical CPUs")
    if usage.free < 1024 ** 3:
        raise ValueError("less than 1 GiB free on output filesystem; free disk space before generating")
    if memory.get("MemAvailable", 1024 ** 3) < 512 * 1024 ** 2:
        raise ValueError("less than 512 MiB RAM available; stop other workloads before generating")
    return {"available_logical_cpus": cpus, "jobs": args.jobs,
            "ram_total_bytes": memory.get("MemTotal", "UNKNOWN"),
            "ram_available_bytes": memory.get("MemAvailable", "UNKNOWN"),
            "disk_free_bytes": usage.free, "disk_total_bytes": usage.total,
            "output_size_estimate_bytes": "UNKNOWN", "runtime_estimate_seconds": "UNKNOWN",
            "estimate_basis": "No extrapolated production benchmark; limits are enforced during the run",
            "max_hours": args.max_hours, "max_disk_gb": args.max_disk_gb,
            "disk_budget_scope": "entire sample output directory; GiB (1024^3 bytes)",
            "free_disk_stop_bytes": 256 * 1024 ** 2}


def directory_bytes(root):
    size = 0
    for directory, _, filenames in os.walk(root, followlinks=False):
        for name in filenames:
            try:
                path = Path(directory) / name
                if not path.is_symlink():
                    size += path.stat().st_size
            except FileNotFoundError:
                pass  # MG5 may rename a temporary file while this snapshot is taken.
    return size


class RunInterrupted(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class Controller:
    def __init__(self, output, args, manifest):
        self.output, self.args, self.manifest = output, args, manifest
        self.started = time.monotonic()
        self.signal_requested = False
        self.last_measure = 0
        self.last_size = directory_bytes(output)
        self.previous_handlers = {}

    def signal_handler(self, signum, frame):
        self.signal_requested = True

    def install(self):
        for signum in (signal.SIGINT, signal.SIGTERM):
            self.previous_handlers[signum] = signal.signal(signum, self.signal_handler)

    def restore(self):
        for signum, handler in self.previous_handlers.items():
            signal.signal(signum, handler)

    def check(self, force=False):
        elapsed = time.monotonic() - self.started
        if self.signal_requested or (self.output / "STOP").exists():
            raise RunInterrupted("PARTIAL_STOPPED", "Stop requested; partial attempt preserved")
        if elapsed > self.args.max_hours * 3600:
            raise RunInterrupted("PARTIAL_TIMEOUT", "Maximum elapsed hours reached; partial attempt preserved")
        if force or elapsed - self.last_measure >= 5:
            self.last_measure = elapsed
            self.last_size = directory_bytes(self.output)
            free = shutil.disk_usage(self.output).free
            self.manifest.update(elapsed_seconds=elapsed, output_bytes=self.last_size,
                                 available_disk_bytes=free, updated_utc=now())
            atomic_json(self.output / "run_manifest.json", self.manifest)
            if self.last_size > self.args.max_disk_gb * 1024 ** 3:
                raise RunInterrupted("PARTIAL_DISK", "Sample output exceeds max-disk-gb; partial attempt preserved")
            if free < 256 * 1024 ** 2:
                raise RunInterrupted("PARTIAL_DISK", "Output filesystem has less than 256 MiB free")

    @staticmethod
    def stop_process(process):
        if process.poll() is not None:
            return
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()

    def run(self, command, cwd, log, phase):
        self.manifest["phase"] = phase
        self.manifest["current_log"] = str(log.relative_to(self.output))
        self.check(force=True)
        started = time.monotonic()
        with log.open("wb") as stream:
            process = subprocess.Popen(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            self.manifest["process_group_id"] = process.pid
            atomic_json(self.output / "run_manifest.json", self.manifest)
            try:
                while process.poll() is None:
                    self.check()
                    time.sleep(0.25)
            except BaseException:
                self.stop_process(process)
                raise
        self.manifest.pop("process_group_id", None)
        result = {"exit_code": process.returncode, "elapsed_seconds": time.monotonic() - started}
        self.manifest["execution"][phase] = result
        self.check(force=True)
        if process.returncode:
            raise RuntimeError(f"Generator exit {process.returncode}; see {log}")
        return result


def stream_export(original, output, controller):
    plain = output / "sample.lhe.tmp"
    compressed = output / "sample.lhe.gz.tmp"
    with gzip.open(original, "rb") as source, plain.open("wb") as raw, compressed.open("wb") as packed:
        with gzip.GzipFile(filename="", mode="wb", fileobj=packed, compresslevel=9, mtime=0) as target:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                raw.write(chunk)
                target.write(chunk)
                controller.check()
    controller.check(force=True)
    plain.replace(output / "sample.lhe")
    compressed.replace(output / "sample.lhe.gz")


def validator():
    # Separate standard-library implementation: no MG5 imports or event repair.
    from validate_sample import validate_file
    return validate_file


def guarded_validation(controller, attempt, path, args, phase, *, deterministic=True, manifest=None):
    result_path = attempt / (phase + ".json")
    command = [sys.executable, str(Path(__file__).with_name("validation_worker.py")),
               "--file", str(path), "--events", str(args.events), "--profile", controller.manifest["profile"],
               "--beam-energy", str(args.energy / 2), "--seed", str(args.seed),
               "--result", str(result_path)]
    if not deterministic:
        command.append("--generator-original")
    if manifest:
        command.extend(["--manifest", str(manifest)])
    controller.run(command, attempt, attempt / (phase + ".log"), phase)
    return json.loads(result_path.read_text())


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--installation", type=Path, required=True)
    result.add_argument("--process", default="pp_bbgg", help="pp_bbgg, pp_diphoton, or a validated process card")
    result.add_argument("--events", type=int, default=1000)
    result.add_argument("--seed", type=int, default=12345)
    result.add_argument("--energy", type=float, default=13000, help="total pp centre-of-mass energy in GeV")
    result.add_argument("--output", type=Path)
    result.add_argument("--run-card", type=Path)
    result.add_argument("--param-card", type=Path)
    result.add_argument("--jobs", type=int, default=min(2, os.cpu_count() or 1))
    result.add_argument("--max-hours", type=float, default=24)
    result.add_argument("--max-disk-gb", type=float, default=20, help="output directory budget in GiB")
    result.add_argument("--dry-run", action="store_true", help="verify installation/request/resources; generate zero events")
    result.add_argument("--resume", action="store_true", help="verify completed run, or restart partial run in a new attempt")
    return result


def prepare_request(args, config):
    for value, name in ((args.energy, "energy"), (args.max_hours, "max-hours"), (args.max_disk_gb, "max-disk-gb")):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if args.events <= 0 or not 1 <= args.seed <= 30081 ** 2:
        raise ValueError("events must be positive; seed must be in [1, 30081^2]")
    process = (REPO / "simulation/mg5/cards" / ALIASES[args.process]
               if args.process in ALIASES else Path(args.process).resolve())
    profile, commands = profile_from_card(process)
    for path in (args.run_card, args.param_card):
        if path and not path.is_file():
            raise ValueError(f"card does not exist: {path}")
    if args.run_card:
        validate_cuts(run_values(args.run_card.read_text()), profile)
    if args.param_card:
        validate_param_card(args.param_card)
    output = (args.output or DEFAULT_RUN_ROOT /
              f"{profile}_{args.events}_seed{args.seed}_{time.strftime('%Y%m%dT%H%M%S')}").resolve()
    check_output(output, config)
    request = {"profile": profile, "process": PROFILES[profile][0], "events_requested": args.events,
               "random_seed": args.seed, "sqrt_s_gev": args.energy, "jobs": args.jobs,
               "max_hours": args.max_hours, "max_disk_gb": args.max_disk_gb,
               "process_card_sha256": digest_file(process),
               "supplied_run_card_sha256": digest_file(args.run_card) if args.run_card else None,
               "supplied_param_card_sha256": digest_file(args.param_card) if args.param_card else None,
               "mg5_source_commit": config["source_commit"]}
    request_hash = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    return process, profile, commands, output, request, request_hash


def execute(args):
    config = json.loads(args.installation.read_text())
    mg5, source_identity = verify(config)
    process_card, profile, commands, output, request, request_hash = prepare_request(args, config)
    resources = preflight(output, args)
    previous = None
    if output.exists():
        if not args.resume:
            raise ValueError(f"Output exists; choose a new directory or explicitly use --resume: {output}")
        manifest_path = output / "run_manifest.json"
        if not manifest_path.is_file():
            raise ValueError("existing directory has no run manifest; refusing to overwrite it")
        previous = json.loads(manifest_path.read_text())
        saved_request = previous.get("request", {})
        saved_hash = hashlib.sha256(json.dumps(saved_request, sort_keys=True).encode()).hexdigest()
        if previous.get("request_sha256") != saved_hash or saved_request != request:
            raise ValueError("resume request differs from saved request; use identical options or a new output")
        if previous.get("status") == "RUNNING":
            pid = previous.get("process_group_id")
            if pid:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    pass
                else:
                    raise ValueError("previous MG5 process is still running; stop it before resuming")
        if previous.get("status") == "PASS":
            validator()(output / "sample.lhe.gz", args.events, profile=profile,
                        beam_energy=args.energy / 2, expected_seed=args.seed, manifest=manifest_path)
            print(f"PASS: existing complete sample independently revalidated: {output / 'sample.lhe.gz'}")
            return 0
    elif args.resume:
        raise ValueError("resume requires an existing manifested output directory")
    if args.dry_run:
        print(json.dumps({"status": "DRY_RUN", "events_generated": 0, "output": str(output),
                          "request": request, "resources": resources,
                          "source_files_verified": len(source_identity["retained_file_sha256"])}, indent=2))
        return 0
    output.mkdir(parents=True, exist_ok=True)
    # Restart is explicit. The stop marker remains in the old attempt history.
    if (output / "STOP").exists():
        (output / "STOP").rename(output / f"STOP_consumed_{time.time_ns()}")
    attempt_number = (previous or {}).get("attempt_number", 0) + 1
    attempt = output / "attempts" / f"attempt_{attempt_number:03d}"
    attempt.mkdir(parents=True)
    if previous:
        atomic_json(attempt / "previous_manifest.json", previous)
    manifest = {"schema_version": 2, "status": "RUNNING", "publication": "LOCAL_ONLY", **request,
                "request": request, "request_sha256": request_hash,
                "source_identity": config, "mg5_version": "3.5.16",
                "source_verified_file_count": len(source_identity["retained_file_sha256"]),
                "generator_script_sha256": digest_file(Path(__file__)),
                "preflight": resources, "attempt_number": attempt_number,
                "attempt_directory": str(attempt.relative_to(output)), "started_utc": now(),
                "execution": {}, "actual_events": 0,
                "resume_semantics": "New complete attempt; interrupted integration and partial events are retained, never merged"}
    atomic_json(output / "run_manifest.json", manifest)
    controller = Controller(output, args, manifest)
    controller.install()
    try:
        shutil.copyfile(process_card, attempt / "requested_process.mg5")
        for supplied, name in ((args.run_card, "requested_run_card.dat"), (args.param_card, "requested_param_card.dat")):
            if supplied:
                shutil.copyfile(supplied, attempt / name)
        command_card = attempt / "generate.mg5"
        command_card.write_text("\n".join([
            "set automatic_html_opening False", "set auto_update 0", f"set nb_core {args.jobs}",
            "set fortran_compiler x86_64-conda-linux-gnu-gfortran",
            "set cpp_compiler x86_64-conda-linux-gnu-g++", *commands, "output process -nojpeg", "quit", ""]))
        controller.run([sys.executable, str(mg5 / "bin/mg5_aMC"), str(command_card)], attempt,
                       attempt / "process_generation.log", "process_generation")
        cards = attempt / "process/Cards"
        if args.run_card:
            shutil.copyfile(args.run_card, cards / "run_card.dat")
        else:
            sys.path.insert(0, str(mg5))
            from madgraph.various.banner import RunCardLO
            card = RunCardLO(str(cards / "run_card.dat"))
            for key, value in BASE_SETTINGS.items():
                card.set(key, value, user=True)
            card.write(str(cards / "run_card.dat"), template=str(cards / "run_card.dat"), write_hidden=False)
        if args.param_card:
            shutil.copyfile(args.param_card, cards / "param_card.dat")
        validate_cuts(run_values((cards / "run_card.dat").read_text()), profile)
        launch = attempt / "launch.mg5"
        launch.write_text("\n".join([
            "launch process -m --name=sample", "shower=OFF", "detector=OFF", "analysis=OFF",
            "madspin=OFF", "reweight=OFF", "done", f"set nevents {args.events}",
            f"set iseed {args.seed}", f"set ebeam1 {args.energy / 2:.12g}",
            f"set ebeam2 {args.energy / 2:.12g}", "done", "quit", ""]))
        controller.run([sys.executable, str(mg5 / "bin/mg5_aMC"), str(launch)], attempt,
                       attempt / "event_generation.log", "event_generation")
        original = attempt / "process/Events/sample/unweighted_events.lhe.gz"
        if not original.is_file():
            raise RuntimeError("No actual LHE output; inspect event_generation.log")
        manifest["phase"] = "validation_original"
        controller.check(force=True)
        result = guarded_validation(controller, attempt, original, args, "validation_original", deterministic=False)
        actual = result.pop("cards")
        result.pop("run_values", None)
        saved_cards = output / "cards"
        saved_cards.mkdir(exist_ok=True)
        hashes = {}
        for key, filename in (("process_card", "proc_card_mg5.dat"), ("run_card", "run_card.dat"),
                              ("param_card", "param_card.dat")):
            source = cards / filename
            if key != "run_card" and canonical_card(source.read_text()) != canonical_card(actual[key]):
                raise ValueError("actual generator card differs from LHE banner: " + key)
            if key == "run_card":
                values = run_values(actual[key])
                if (integer(values["iseed"]) != args.seed or integer(values["nevents"]) != args.events or
                        number(values["ebeam1"]) != args.energy / 2 or number(values["ebeam2"]) != args.energy / 2):
                    raise ValueError("actual banner does not match requested seed/count/energy")
                shutil.copyfile(source, saved_cards / "post_run_run_card.dat")
            (saved_cards / filename).write_text(actual[key], encoding="utf-8")
            hashes[key + "_sha256"] = digest_file(saved_cards / filename)
        shutil.copyfile(cards / "me5_configuration.txt", saved_cards / "me5_configuration.txt")
        banners = list((attempt / "process/Events/sample").glob("*_banner.txt"))
        if len(banners) != 1:
            raise RuntimeError("expected one actual run banner")
        shutil.copyfile(banners[0], output / "generator_banner.txt")
        manifest["phase"] = "export"
        stream_export(original, output, controller)
        result = guarded_validation(controller, attempt, output / "sample.lhe.gz", args, "validation_export")
        result.pop("cards", None)
        result.pop("run_values", None)
        result["original_compressed_sha256"] = digest_file(original)
        manifest.update(validation=result, card_hashes=hashes, actual_events=args.events,
                        lhe="sample.lhe", lhe_gz="sample.lhe.gz",
                        actual_cards_authority="Exact LHE banner text; mutable post-run seed-reset card separately retained")
        for filename in ("generate.mg5", "launch.mg5", "process_generation.log", "event_generation.log", "requested_process.mg5"):
            shutil.copyfile(attempt / filename, output / filename)
        process_link = output / "process"
        if process_link.is_symlink():
            process_link.unlink()
        elif process_link.exists():
            raise ValueError("unexpected process path in sample output")
        process_link.symlink_to(attempt.relative_to(output) / "process", target_is_directory=True)
        controller.check(force=True)
        manifest.update(status="PASS", phase="complete", completed_utc=now(),
                        elapsed_seconds=time.monotonic() - controller.started)
        atomic_json(output / "run_manifest.json", manifest)
        guarded_validation(controller, attempt, output / "sample.lhe.gz", args, "validation_manifest",
                           manifest=output / "run_manifest.json")
        manifest.update(phase="complete", completed_utc=now(),
                        elapsed_seconds=time.monotonic() - controller.started)
        atomic_json(output / "run_manifest.json", manifest)
        print(f"PASS: {args.events} actual {profile} LO events; seed={args.seed}; sqrt(s)={args.energy:g} GeV")
        print(f"Cross section: {result['cross_section_pb']:.10g} +/- {result['cross_section_uncertainty_pb']:.5g} pb")
        print(f"Local sample: {output / 'sample.lhe.gz'}")
        print(f"SHA256: {result['compressed_file_sha256']}")
        return 0
    except BaseException as exc:
        manifest.update(status=getattr(exc, "status", "FAILED"), failure=str(exc), updated_utc=now(),
                        elapsed_seconds=time.monotonic() - controller.started, phase_at_failure=manifest.get("phase"))
        atomic_json(output / "run_manifest.json", manifest)
        raise
    finally:
        controller.restore()


def main():
    args = parser().parse_args()
    return execute(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

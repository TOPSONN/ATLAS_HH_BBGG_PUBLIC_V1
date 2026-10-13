#!/usr/bin/env python3
"""Bounded, source-bound real DelphesHepMC3 execution and native ROOT readback.

Existing MG5/Pythia events are reused. No event repair or automatic publication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

REPO = Path(__file__).resolve().parents[3]
PYTHIA_SCRIPTS = REPO / "simulation/pythia8/scripts"
sys.path.insert(0, str(PYTHIA_SCRIPTS))
import validate_hepmc3 as hepmc
from validate_lhe_stream import file_sha256 as ordinary_file_sha256

CARD = Path(__file__).resolve().parents[1] / "cards/atlas_like_bbgg_baseline.tcl"
CARD_SHA256 = "cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47"
SOURCE_COMMIT = "28658365abeb71ee36dfc739f9670c1514c0cb10"
SEEDS = {"bbgg": 610301, "ccgg": 610302, "jjgg": 610303}
DEADLINE = None


def file_sha256(path):
    """Streaming digest that also enforces the whole-command deadline."""
    if DEADLINE is None:
        return ordinary_file_sha256(path)
    sha = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            if time.monotonic() > DEADLINE:
                raise StopRun("PARTIAL_TIMEOUT: source/signature hashing reached elapsed cap")
            sha.update(chunk)
    return sha.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def atomic_json(path, data):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path, max_bytes=20 * 1024**2):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= max_bytes, "missing/oversized JSON evidence: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def bound_file(directory, relative):
    relative = Path(relative)
    require(not relative.is_absolute(), "run evidence must use relative paths")
    path = (directory / relative).resolve()
    require(path.is_relative_to(directory.resolve()) and path.is_file() and not path.is_symlink(), "evidence path escape/missing file")
    return path


def jsonl_rows(path, maximum=16 * 1024**2):
    """Bound individual provenance records, including raw Pythia diagnostics."""
    with Path(path).open("rb") as stream:
        while True:
            line = stream.readline(maximum + 1)
            if not line:
                return
            require(len(line) <= maximum and line.endswith(b"\n"), "oversized/truncated provenance JSONL record")
            yield json.loads(line)


def indexed_particles(raw):
    """Exact P-line values plus source-defined production position in mm.

    Official Delphes AnalyzeVertex initializes implicit vertices to zero;
    explicit V records supply x/y/z/ct and are applied before finalization.
    """
    lines = raw.decode().splitlines()
    vertices = {}
    for line in lines:
        if line.startswith("V "):
            vid = int(line.split()[1])
            require(vid not in vertices, "repeated explicit vertex position unsupported")
            coordinates = [float(value) for value in line.rsplit(" @ ", 1)[1].split()] if " @ " in line else [0.0] * 4
            require(len(coordinates) == 4 and all(math.isfinite(v) for v in coordinates), "invalid explicit vertex position")
            vertices[vid] = coordinates
    for line in lines:
        if line.startswith("P "):
            fields = line.split()
            parent = int(fields[2])
            require(parent >= 0 or parent in vertices, "source particle explicit vertex missing")
            coordinates = vertices.get(parent, [0.0] * 4)
            yield [fields[1], fields[3], fields[9], *fields[4:9], fields[2], *[format(value, ".17g") for value in coordinates]]


def runtime_environment(config):
    env = os.environ.copy()
    root = Path(config["root_prefix"]).resolve()
    delphes = Path(config["delphes_prefix"]).resolve()
    extra = config.get("runtime_library_dirs", [])
    require(isinstance(extra, list), "runtime_library_dirs must be a list")
    env["PATH"] = str(root / "bin") + os.pathsep + env.get("PATH", "")
    env["LD_LIBRARY_PATH"] = os.pathsep.join([str(delphes), str(delphes / "lib"), str(root / "lib"), *extra])
    env["ROOTSYS"] = str(root)
    env["OMP_NUM_THREADS"] = "1"
    return env


def pythia_environment(config, root_prefix):
    """Scope the verified input reader independently of an activated ROOT shell."""
    env = os.environ.copy()
    env["PYTHIA8DATA"] = config["xml_path"]
    env["LD_LIBRARY_PATH"] = os.pathsep.join([str(Path(config["pythia_prefix"]) / "lib"),
                                               str(Path(config["hepmc3_prefix"]) / "lib"),
                                               str(Path(root_prefix) / "lib")])
    return env


def verify_pythia_reader(config_path, root_prefix):
    config = read_json(config_path)
    env = pythia_environment(config, root_prefix)
    code = ("import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[2]); "
            "from shower_sample import verify_installation; "
            "print(json.dumps(verify_installation(json.loads(Path(sys.argv[1]).read_text()))))")
    verified = json.loads(subprocess.check_output([sys.executable, "-B", "-c", code, str(config_path), str(PYTHIA_SCRIPTS)],
                                                 env=env, text=True, timeout=30))
    return config, env, verified


def verify_installation(config):
    require(config.get("delphes_version") == "3.5.1" and config.get("delphes_source_commit") == SOURCE_COMMIT,
            "unverified Delphes version/source identity")
    require(config.get("root_version") == "6.40.04", "requires the verified ROOT 6.40.04 installation")
    for table in ("library_sha256", "dictionary_sha256", "header_sha256", "source_sha256"):
        require(config.get(table), "installation lacks " + table)
        for path, expected in config[table].items():
            require(file_sha256(path) == expected, "installed scientific source/ABI file changed: " + Path(path).name)
    env = runtime_environment(config)
    root_config = Path(config["root_prefix"]) / "bin/root-config"
    version = subprocess.check_output([str(root_config), "--version"], env=env, text=True, timeout=30).strip()
    require(version == "6.40.04", "actual root-config version mismatch")
    flags = subprocess.check_output([str(root_config), "--cflags"], env=env, text=True, timeout=30)
    require("-std=c++20" in flags, "actual ROOT toolchain lacks C++20")
    binaries = {"delphes": Path(config["delphes_binary"]), "analyzer": Path(config["analyzer_path"])}
    dependencies = {}
    for name, path in binaries.items():
        require(path.is_file(), "required native executable is absent: " + name)
        require(file_sha256(path) == config["binary_sha256"][str(path)], "native executable changed: " + name)
        loaded = subprocess.check_output(["ldd", str(path)], env=env, text=True, timeout=30)
        require("not found" not in loaded, "native executable has an unresolved shared library")
        for line in loaded.splitlines():
            if "=>" in line and any(lib in line for lib in ("libCore.so", "libRIO.so", "libTree.so", "libPhysics.so")):
                resolved = Path(line.split("=>", 1)[1].split()[0]).resolve()
                require(resolved.is_relative_to(Path(config["root_prefix"]).resolve()), "mixed ROOT runtime detected")
        dependencies[name] = loaded
    analyzer_build = json.loads(subprocess.check_output([str(binaries["analyzer"]), "--build-info"], env=env, text=True, timeout=30))
    require(analyzer_build["root_version"] == "6.40.04" and analyzer_build["cpp_standard"] == 20,
            "actual analyzer ROOT/C++ build identity mismatch")
    require(Path(analyzer_build["delphes_library"]).resolve().is_relative_to(Path(config["delphes_prefix"]).resolve()),
            "analyzer loaded a different Delphes dictionary library")
    pythia_config_path = Path(config.get("pythia_installation", REPO / ".local/pythia8_installation.json"))
    pythia_config, py_env, pythia_software = verify_pythia_reader(pythia_config_path, config["root_prefix"])
    return env, pythia_config, py_env, {"root_version": version, "root_cflags": flags.strip(),
                               "runtime_dependencies": dependencies, "analyzer_build_info": analyzer_build, "pythia_preflight": pythia_software,
                               "pythia_reader_environment": {key: py_env[key] for key in ("PYTHIA8DATA", "LD_LIBRARY_PATH")},
                               "binary_sha256": {name: file_sha256(path) for name, path in binaries.items()}}


def safe_output(output, config):
    require(not output.exists(), "output exists; choose a new directory: " + str(output))
    require(not any(c.isspace() or c in "\"';" for c in str(output)), "unsupported output whitespace/metacharacters")
    for protected in (REPO, Path(config["delphes_prefix"]).resolve(), Path(config["root_prefix"]).resolve()):
        require(output != protected and not output.is_relative_to(protected) and not protected.is_relative_to(output),
                "output must be outside Git and installed tool directories")


class StopRun(RuntimeError):
    pass


class Monitor:
    def __init__(self, directory, args, manifest, started=None):
        self.directory, self.args, self.manifest = directory, args, manifest
        self.started = time.monotonic() if started is None else started
        self.last_disk = -10
        self.stopped = False
        self.handlers = {s: signal.signal(s, self.signal_handler) for s in (signal.SIGINT, signal.SIGTERM)}

    def signal_handler(self, *_):
        self.stopped = True

    def restore(self):
        for key, previous in self.handlers.items():
            signal.signal(key, previous)

    def check(self, force=False):
        elapsed = time.monotonic() - self.started
        if self.stopped or (self.directory / "STOP").exists():
            raise StopRun("PARTIAL_STOPPED: stop requested; existing files retained")
        if elapsed > self.args.max_hours * 3600:
            raise StopRun("PARTIAL_TIMEOUT: elapsed cap reached; existing files retained")
        if force or elapsed - self.last_disk >= 5:
            self.last_disk = elapsed
            size = sum(path.stat().st_size for path in self.directory.rglob("*") if path.is_file() and not path.is_symlink())
            free = shutil.disk_usage(self.directory).free
            self.manifest.update(elapsed_seconds=elapsed, output_bytes=size, disk_free_bytes=free)
            atomic_json(self.directory / "run_manifest.json", self.manifest)
            if size > self.args.max_disk_gb * 1024**3 or free < 256 * 1024**2:
                raise StopRun("PARTIAL_DISK: budget/reserve reached; existing files retained")

    def run(self, command, phase, env=None):
        self.manifest["phase"] = phase
        self.check(force=True)
        began = time.monotonic()
        peak_observed = 0
        with (self.directory / (phase + ".log")).open("wb") as log:
            child = subprocess.Popen(command, cwd=self.directory, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            self.manifest["process_group_id"] = child.pid
            atomic_json(self.directory / "run_manifest.json", self.manifest)
            try:
                while child.poll() is None:
                    status = Path(f"/proc/{child.pid}/status")
                    try:
                        for line in status.read_text().splitlines():
                            if line.startswith("VmHWM:"):
                                peak_observed = max(peak_observed, int(line.split()[1]) * 1024)
                    except FileNotFoundError:
                        pass
                    self.check()
                    time.sleep(0.1)
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
        self.manifest["execution"][phase] = {"exit_code": child.returncode, "elapsed_seconds": time.monotonic() - began,
                                               "peak_observed_rss_bytes": peak_observed or "UNKNOWN",
                                               "rss_scope": "sampled /proc child VmHWM; no unsampled peak guarantee"}
        self.check(force=True)
        return child.returncode


def resource_preflight(output):
    ancestor = output
    while not ancestor.exists():
        ancestor = ancestor.parent
    free = shutil.disk_usage(ancestor).free
    require(free >= 1024**3, "less than 1 GiB free on output filesystem")
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key = line.split(":", 1)[0]
        if key in {"MemAvailable", "MemTotal"}:
            memory[key] = int(line.split()[1]) * 1024
    require(memory["MemAvailable"] >= 512 * 1024**2, "less than 512 MiB available RAM")
    return {"jobs": 1, "logical_cpus": os.cpu_count(), "disk_free_bytes": free, "ram_bytes": memory,
            "predicted_root_output_bytes": "UNKNOWN", "predicted_runtime_seconds": "UNKNOWN"}


def source_context(input_path, profile, config, supplied=None):
    if supplied is not None:
        manifest_path = supplied.resolve()
    elif (input_path.parent / "run_manifest.json").is_file():
        manifest_path = input_path.parent / "run_manifest.json"
    else:
        candidate = config.get("phase6b_runs", {}).get(profile)
        require(candidate, "source run manifest not discovered; supply --source-manifest for the original verified Pythia run")
        manifest_path = Path(candidate)
        if manifest_path.is_dir():
            manifest_path /= "run_manifest.json"
    manifest = read_json(manifest_path)
    directory = manifest_path.parent
    require(manifest.get("status") == "PASS" and manifest["source_sample_id"] == profile, "original Pythia run not PASS or process mismatch")
    require(manifest["pythia_version"] == "8.317" and manifest["hepmc3_version"] == "3.3.1", "unverified source generator versions")
    require(manifest["settings_sha256"] == hepmc.BASELINE_SETTINGS_SHA256, "source Pythia settings are not the reviewed v2 baseline")
    files = {}
    for name in ("event_ledger.jsonl", "particle_diagnostics.jsonl", "source_events.jsonl", "settings.cmnd", "physical_validation.json"):
        path = bound_file(directory, name)
        require(file_sha256(path) == manifest["files"][name]["sha256"], "source run snapshot hash mismatch: " + name)
        files[name] = path
    require(file_sha256(files["settings.cmnd"]) == manifest["settings_sha256"], "source settings card mismatch")
    cpp = read_json(files["physical_validation.json"])
    require(cpp["validation_status"] == "PASS" and cpp["N_failed_validation"] == 0 and cpp["N_not_assessed"] == 0,
            "original source did not pass actual HepMC3 ReaderAscii validation")
    source = Path(manifest["source_file"])
    if not source.is_absolute():
        source = REPO / source
    require(source.is_file() and file_sha256(source) == manifest["source_file_sha256"], "original MG5 ancestry source missing/changed")
    input_hash = file_sha256(input_path)
    full_hashes = {manifest["files"][name]["sha256"] for name in ("shower.hepmc3", "shower.hepmc3.gz") if name in manifest["files"]}
    publication = None
    if input_hash in full_hashes:
        expected = manifest["counters"]["N_written"]
    else:
        require((input_path.parent / "sample_manifest.json").is_file(), "input bytes are not the original full run or a manifest-bound published subset")
        published = read_json(input_path.parent / "sample_manifest.json")
        matches = [row for row in published["samples"] if row["compressed_file_sha256"] == input_hash]
        require(len(matches) == 1, "published subset checksum not identified")
        publication = matches[0]
        require(publication["source_sample_id"] == profile and publication["source_file_sha256"] == manifest["source_file_sha256"]
                and publication["settings_sha256"] == manifest["settings_sha256"]
                and publication["full_run_decompressed_file_sha256"] == cpp["decompressed_file_sha256"], "subset belongs to another source/settings/full run")
        expected = publication["events"]
    return {"manifest": manifest, "manifest_path": manifest_path, "files": files, "source": source,
            "input_sha256": input_hash, "expected_events": expected, "published_subset": publication}


def copy_ledger_prefix(context, directory, count, monitor):
    target = directory / "source_event_ledger.jsonl"
    with context["files"]["event_ledger.jsonl"].open("rb") as source, target.open("wb") as output:
        for index in range(1, count + 1):
            raw = source.readline(1024 * 1024 + 1)
            require(raw.endswith(b"\n") and len(raw) <= 1024 * 1024, "source ledger truncated/oversized")
            row = json.loads(raw)
            require(row["processing_status"] == "WRITTEN" and row["output_event_index"] == index, "source ledger prefix contains failed/gap records")
            output.write(raw)
            monitor.check()
    return target


def native_index_and_prefix(source_plain, directory, count, context, monitor):
    output = directory / "input.hepmc3"
    dat = directory / "input_event_index.dat"
    jsonl = directory / "input_event_index.jsonl"
    original_rows = jsonl_rows(context["files"]["event_ledger.jsonl"], 1024 * 1024)
    header = None
    ordinal = 0
    with output.open("wb") as selected, dat.open("w") as index, jsonl.open("w") as audit:
        index.write("ATLAS_DELPHES_INPUT_V1\n")
        for kind, raw in hepmc.iter_ascii(source_plain, max_decompressed_gb=monitor.args.max_disk_gb):
            if kind == "header":
                selected.write(raw)
                header = hepmc.parse_header(raw)
            elif kind == "event":
                ordinal += 1
                if ordinal > count:
                    continue
                record = hepmc.parse_event(raw, header)
                row = next(original_rows)
                require(record["event_hash"] == row["output_event_hash"] and record["identity"]["source_event_content_hash"] == row["source_event_content_hash"], "exact source-ledger event binding mismatch")
                selected.write(raw)
                particle_rows = list(indexed_particles(raw))
                values = [ordinal, record["event_number"], record["event_hash"], row["source_event_index"], row["source_event_content_hash"],
                          format(row["input_contribution_pb"], ".17g"), format(row["lhe_weight_pb"], ".17g"),
                          row["source_total_events"], len(particle_rows), len(record["weights"])]
                index.write("E " + " ".join(map(str, values)) + "\n")
                index.write("W " + " ".join(format(w, ".17g") for w in record["weights"]) + "\n")
                for fields in particle_rows:
                    index.write("P " + " ".join(fields) + "\n")
                audit.write(json.dumps({"input_ordinal": ordinal, "native_hepmc_event_number": record["event_number"],
                                        "input_event_sha256": record["event_hash"], "source_identity": record["identity"],
                                        "weights": record["weights"], "weight_names": header["weight_names"],
                                        "source_total_events": row["source_total_events"], "particle_count": len(particle_rows),
                                        "source_particle_position_units": "x,y,z,ct in mm; native GenParticle.T=float(ct_mm*1e-3/2.99792458e8) seconds"}, sort_keys=True) + "\n")
            elif kind == "footer":
                selected.write(raw)
            monitor.check()
    require(ordinal == context["expected_events"] and count <= ordinal, "prepared prefix/source count mismatch")
    return output


def truth_index(directory, count, context, monitor):
    hard_rows = jsonl_rows(context["files"]["source_events.jsonl"])
    py_rows = jsonl_rows(context["files"]["particle_diagnostics.jsonl"])
    with (directory / "truth_analysis_index.dat").open("w") as output:
        output.write("ATLAS_DELPHES_TRUTH_V1\n")
        for index in range(1, count + 1):
            original, py = next(hard_rows), next(py_rows)
            require(original["source_event_index"] == py["source_event_index"] == py["output_event_index"] == index,
                    "truth sidecar source cursor mismatch")
            hard = list(enumerate(original["particles"], 1))
            lhe_gamma = [(i, p) for i, p in hard if p["status"] == 1 and p["pdg_id"] == 22]
            lhe_parton = [(i, p) for i, p in hard if p["status"] == 1 and (abs(p["pdg_id"]) <= 6 or p["pdg_id"] == 21)]
            py_gamma = [p for p in py["particles"] if p["is_final"] and p["pdg_id"] == 22
                        and p.get("photon_origin_diagnostic") in {"HARD_PROCESS_PHOTON", "HARD_PHOTON_ANCESTOR"}
                        and not p.get("has_produced_hadron_ancestor", True) and p.get("hard_photon_ancestors")]
            py_parton = [p for p in py["particles"] if abs(p["status"]) == 23 and (abs(p["pdg_id"]) <= 6 or p["pdg_id"] == 21)]
            heavy = [p for p in py["particles"] if p["terminal_b_hadron"] or p["terminal_c_hadron"]]
            require(len(lhe_gamma) == len(lhe_parton) == len(py_gamma) == len(py_parton) == 2,
                    "baseline hard truth counts are not two photons/two outgoing partons")
            require(all(len(p["hard_photon_ancestors"]) == 1 for p in py_gamma)
                    and {p["hard_photon_ancestors"][0] for p in py_gamma} == set(py["hard_photon_roots"]),
                    "final hard-photon descendant matching is ambiguous; truth identity blocked")
            manifest = context["manifest"]
            output.write("E " + " ".join(map(str, [index, index, index, original["source_event_content_hash"], manifest["pythia_run_id"],
                                                     manifest["pythia_seed"], 2, 2, 2, 2, len(heavy)])) + "\n")
            for key, rows in (("L", lhe_gamma), ("G", py_gamma), ("Q", lhe_parton), ("R", py_parton)):
                for item in rows:
                    if key in {"L", "Q"}:
                        i, p = item
                        vector = p["p4_and_mass_gev"]
                    else:
                        p = item
                        i = p["pythia_index"]
                        vector = [*p["p4_gev"], p["mass_gev"]]
                    output.write(key + " " + " ".join(map(str, [i, p["pdg_id"], *[format(v, ".17g") for v in vector]])) + "\n")
            for p in heavy:
                output.write("H " + " ".join(map(str, [p["pythia_index"], p["pdg_id"], int(p["terminal_b_hadron"]), int(p["terminal_c_hadron"]),
                                                          *[format(v, ".17g") for v in [*p["p4_gev"], p["mass_gev"]]]])) + "\n")
            monitor.check()


def runtime_card(card, target, seed):
    raw = card.read_bytes()
    require(file_sha256(card) == CARD_SHA256 and file_sha256(CARD) == CARD_SHA256, "only the immutable reviewed detector card is supported")
    marker = b"set RandomSeed 610301"
    require(raw.count(marker) == 1, "reviewed card seed declaration missing/ambiguous")
    target.write_bytes(raw.replace(marker, f"set RandomSeed {seed}".encode(), 1))


def record_native_validation(manifest, path, exit_code):
    manifest["native_validator_exit_code"] = exit_code
    keys = ("N_input", "N_read", "N_processed", "N_output", "N_invalid", "N_skipped")
    if path.is_file():
        report = read_json(path)
        manifest["native_validation"] = report
        manifest.update({key: report.get(key, "UNKNOWN") for key in keys})
        return report
    manifest.update({key: "UNKNOWN" for key in keys})
    return None


def delphes_command(config, directory):
    # TFile persists its supplied name. Keep the actual output argument relative
    # to Monitor.run's verified cwd, so publication does not require rewriting.
    return [config["delphes_binary"], str(directory / "detector_card.tcl"), "detector.root", str(directory / "input.hepmc3")]


def main():
    global DEADLINE
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--process", choices=["bbgg", "ccgg", "jjgg", "jjgg_light"], required=True)
    parser.add_argument("--card", type=Path, default=CARD)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--events", type=int, help="exact unchanged input prefix; physical acceptance requires actual count/readback tests")
    parser.add_argument("--source-manifest", type=Path, help="original verified Pythia run_manifest.json, discovered automatically when possible")
    parser.add_argument("--max-hours", type=float, default=1)
    parser.add_argument("--max-disk-gb", type=float, default=5, help="entire local run-directory budget in GiB")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    profile = "jjgg" if args.process == "jjgg_light" else args.process
    require(args.events is None or args.events > 0, "event limit must be positive")
    require(all(math.isfinite(v) and v > 0 for v in (args.max_hours, args.max_disk_gb)), "finite positive caps required")
    DEADLINE = started + args.max_hours * 3600
    require(args.input.is_file() and args.card.is_file(), "input/card missing")
    require(file_sha256(args.card) == file_sha256(CARD) == CARD_SHA256, "detector card is not the immutable reviewed version")
    config = read_json(args.installation)
    output = (args.output or Path.home() / "simulations/delphes_runs" / f"{profile}_{time.strftime('%Y%m%dT%H%M%S')}").resolve()
    safe_output(output, config)
    resources = resource_preflight(output)
    env, pyconfig, py_env, software = verify_installation(config)
    context = source_context(args.input.resolve(), profile, config, args.source_manifest)
    count = args.events or context["expected_events"]
    require(count <= context["expected_events"], "event limit exceeds verified input count")
    manifest = {"schema_version": 1, "status": "PREPARING", "publication": "LOCAL_ONLY", "physics_label": "FAST_SIM_ATLAS_LIKE_NOT_OFFICIAL_ATLAS",
                "process": profile, "process_argument": args.process, "events_requested": count, "input_event_count": context["expected_events"],
                "input_hepmc_sha256": context["input_sha256"], "source_sample_id": profile, "source_mg5_sha256": context["manifest"]["source_file_sha256"],
                "source_pythia_run_id": context["manifest"]["pythia_run_id"], "source_pythia_settings_sha256": context["manifest"]["settings_sha256"],
                "source_run_manifest_sha256": file_sha256(context["manifest_path"]), "detector_canonical_card_sha256": CARD_SHA256,
                "detector_seed": SEEDS[profile], "delphes_version": "3.5.1", "delphes_source_commit": SOURCE_COMMIT, "root_version": "6.40.04",
                "execution_id": str(uuid.uuid4()), "software": software, "installation": config, "resources_preflight": resources,
                "resource_limits": {"jobs": 1, "max_hours": args.max_hours, "max_disk_gb": args.max_disk_gb}, "execution": {},
                "input_cross_section_pb": context["manifest"]["input_cross_section_pb"], "source_total_events": context["manifest"]["input_event_count"],
                "normalization": "original signed input_contribution_pb; original full MG5 denominator retained for all prefixes; no luminosity"}
    temporary = tempfile.TemporaryDirectory(prefix="atlas-delphes-preflight-") if args.dry_run else None
    directory = Path(temporary.name) if temporary else output
    directory.mkdir(parents=True, exist_ok=bool(temporary))
    monitor = Monitor(directory, args, manifest, started)
    try:
        actual_ledger = copy_ledger_prefix(context, directory, context["expected_events"], monitor)
        portable_report = directory / "input_portable_validation.json"
        portable_command = [sys.executable, "-B", str(PYTHIA_SCRIPTS / "validate_hepmc3.py"), "--file", str(args.input.resolve()),
                            "--events", str(context["expected_events"]), "--ledger", str(actual_ledger), "--source-file", str(context["source"]),
                            "--source-sha256", context["manifest"]["source_file_sha256"], "--sample-id", profile,
                            "--seed", str(context["manifest"]["pythia_seed"]), "--max-decompressed-gb", str(args.max_disk_gb),
                            "--report", str(portable_report)]
        require(monitor.run(portable_command, "input_portable_readback") == 0, "portable source-ledger input preflight failed")
        validation = read_json(portable_report)
        require(validation["event_identity"] == "PASS", "source event mapping not established")
        atomic_json(directory / "input_portable_validation.json", validation)
        source_plain = directory / "source_full.hepmc3"
        with source_plain.open("wb") as target:
            for _, raw in hepmc.iter_ascii(args.input, max_decompressed_gb=args.max_disk_gb):
                target.write(raw)
                monitor.check()
        require(file_sha256(source_plain) == validation["decompressed_file_sha256"], "scratch input bytes changed")
        cpp_report = directory / "input_native_validation.json"
        command = [pyconfig["validator_path"], "--input", str(source_plain), "--events", str(context["expected_events"]), "--xml", pyconfig["xml_path"],
                   "--report", str(cpp_report), "--source-sha256", context["manifest"]["source_file_sha256"], "--sample-id", profile,
                   "--seed", str(context["manifest"]["pythia_seed"])]
        require(monitor.run(command, "input_native_readback", py_env) == 0, "actual HepMC3 ReaderAscii input preflight failed")
        native_input = read_json(cpp_report)
        require(native_input["validation_status"] == "PASS" and native_input["decompressed_file_sha256"] == validation["decompressed_file_sha256"],
                "native reader inspected different input bytes")
        manifest["input_validation"] = {"portable": validation, "native": native_input}
        manifest["resources_preflight"]["verified_hepmc_decompressed_bytes"] = source_plain.stat().st_size
        runtime_card(args.card, directory / "detector_card.tcl", SEEDS[profile])
        manifest["detector_runtime_card_sha256"] = file_sha256(directory / "detector_card.tcl")
        if args.dry_run:
            print(json.dumps({"status": "DRY_RUN", "detector_events_processed": 0, "events_requested": count, "input_event_count": context["expected_events"],
                              "input_validation": manifest["input_validation"], "detector_canonical_card_sha256": CARD_SHA256,
                              "detector_runtime_card_sha256": manifest["detector_runtime_card_sha256"], "detector_seed": SEEDS[profile], "resources": resources}, indent=2))
            return 0
        native_index_and_prefix(source_plain, directory, count, context, monitor)
        copy_ledger_prefix(context, directory, count, monitor)
        truth_index(directory, count, context, monitor)
        manifest["selected_input_sha256"] = file_sha256(directory / "input.hepmc3")
        manifest["prepared_file_sha256"] = {name: file_sha256(directory / name) for name in
                                             ("input.hepmc3", "input_event_index.dat", "input_event_index.jsonl",
                                              "truth_analysis_index.dat", "source_event_ledger.jsonl", "detector_card.tcl")}
        manifest["source_sidecar_sha256"] = {name: file_sha256(path) for name, path in context["files"].items()}
        source_plain.unlink()
        command = delphes_command(config, directory)
        atomic_json(directory / "delphes_command.json", command)
        delphes_exit = monitor.run(command, "delphes", env)
        require((directory / "detector.root").is_file(), "Delphes did not produce a ROOT file; inspect delphes.log")
        native_command = [config["analyzer_path"], "--input", str(directory / "detector.root"), "--input-index", str(directory / "input_event_index.dat"),
                          "--truth-index", str(directory / "truth_analysis_index.dat"), "--events", str(count), "--process", profile,
                          "--card", str(directory / "detector_card.tcl"), "--summary", str(directory / "native_validation.json"),
                          "--events-jsonl", str(directory / "reco_events.jsonl"), "--cutflow", str(directory / "cutflow.csv"),
                          "--efficiencies", str(directory / "efficiencies.csv")]
        native_exit = monitor.run(native_command, "native_root_readback", env)
        report_path = directory / "native_validation.json"
        native = record_native_validation(manifest, report_path, native_exit)
        require(native is not None, "native ROOT validation produced no event-count evidence")
        require(delphes_exit == native_exit == 0 and native["validation_status"] == "PASS", "real Delphes/native ROOT validation failed; explicit counters retained")
        require(manifest["N_input"] == manifest["N_read"] == manifest["N_processed"] == manifest["N_output"] == count
                and manifest["N_invalid"] == manifest["N_skipped"] == 0, "lost/invalid events; partial counts retained")
        for key, filename in (("root_file_sha256", "detector.root"), ("input_index_sha256", "input_event_index.dat"),
                              ("truth_index_sha256", "truth_analysis_index.dat"), ("detector_card_sha256", "detector_card.tcl")):
            require(native[key] == file_sha256(directory / filename), "native ROOT report inspected different bytes: " + filename)
        require(file_sha256(args.input) == context["input_sha256"], "original HepMC input changed during reconstruction")
        require(file_sha256(context["source"]) == context["manifest"]["source_file_sha256"], "original MG5 source changed")
        require(file_sha256(context["manifest_path"]) == manifest["source_run_manifest_sha256"], "original Pythia run manifest changed")
        for name, expected in manifest["prepared_file_sha256"].items():
            require(file_sha256(directory / name) == expected, "prepared source/card/index file changed during reconstruction: " + name)
        for name, path in context["files"].items():
            require(file_sha256(path) == manifest["source_sidecar_sha256"][name], "original source sidecar changed")
        manifest["files"] = {path.name: {"sha256": file_sha256(path), "bytes": path.stat().st_size}
                             for path in directory.iterdir() if path.is_file() and path.name != "run_manifest.json" and not path.name.endswith(".tmp")}
        manifest.update(status="PASS", elapsed_seconds=time.monotonic() - started)
        monitor.check(force=True)
        atomic_json(directory / "run_manifest.json", manifest)
        print(f"PASS: {count}/{count} real {profile} ROOT entries validated; LOCAL_ONLY")
        print("ROOT: " + str(directory / "detector.root"))
        print("SHA256: " + manifest["files"]["detector.root"]["sha256"])
        return 0
    except BaseException as error:
        manifest.update(status="PARTIAL" if isinstance(error, StopRun) or (directory / "detector.root").exists() else "FAILED", diagnostic=str(error))
        root_file = directory / "detector.root"
        if root_file.is_file():
            try:
                manifest["partial_root_file"] = {"sha256": file_sha256(root_file), "bytes": root_file.stat().st_size}
            except StopRun:
                manifest["partial_root_file"] = {"sha256": "UNKNOWN", "bytes": root_file.stat().st_size, "diagnostic": "deadline exhausted during hashing"}
        atomic_json(directory / "run_manifest.json", manifest)
        raise
    finally:
        monitor.restore()
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, StopIteration) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        raise SystemExit(1)

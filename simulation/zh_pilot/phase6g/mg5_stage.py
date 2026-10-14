"""Frozen one-run MG5 driver preparation and guarded execution adapter.

Preparation writes text only.  This module has no subprocess runner or CLI.
The caller must supply the authorization/resource controller's ``run_command``
capability before export/integration can be invoked.  No retry or replacement
run is provided.  Tests using a recording callback are METHOD_ONLY.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Callable

REPO = Path(__file__).resolve().parents[3]
PROFILE = "ZH_ZBB_STABLE_H"
RUN_NAME = "zh100"
MG5_COMMIT = "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"
GENERATOR_CONTRACT_SHA256 = "a385af80aebb8462b73c6eb83de54a7f996d4f1e4d5e6aff840b5c83f44d2cf4"
PROCESS_COMMANDS = [
    "import model sm-no_b_mass",
    "define p = g u c d s b u~ c~ d~ s~ b~",
    "generate p p > z h QCD=0 QED=2, z > b b~",
]
NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?"
# This adapter executes only when passed to the outer guarded callback.  It
# changes runtime cache/installation-write flags, never installed source or the
# matrix element.  -O is required to prevent bin/mg5_aMC's shell self-relaunch.
READONLY_MG5_ADAPTER = '''import os
import runpy
import sys
from pathlib import Path
if len(sys.argv) != 4:
    raise RuntimeError("fixed MG5 root, driver and toolchain arguments required")
root = Path(sys.argv[1]).resolve()
driver = Path(sys.argv[2]).resolve()
toolchain = Path(sys.argv[3]).resolve()
protected = (root, toolchain)
def protected_path(value):
    if not isinstance(value, (str, bytes, os.PathLike)):
        return False
    path = Path(os.fsdecode(value)).resolve()
    return any(path == item or path.is_relative_to(item) for item in protected)
def reject_installation_write(event, args):
    targets = []
    if event == "open":
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or \
                  (isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
        if writing:
            targets = [path]
    elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.chown", "os.utime", "os.truncate"}:
        targets = args[:1]
    elif event == "os.rename":
        targets = args[:2]
    elif event in {"os.link", "os.symlink"}:
        targets = args[1:2]
    if any(protected_path(value) for value in targets):
        raise PermissionError("BLOCKED_INSTALLATION_WRITE: " + event)
# Defense in depth for unexpected Python-side mutation, including symlinked
# destinations.  Compiler outputs are confined separately by the controller.
sys.addaudithook(reject_installation_write)
make_opts = root / "Template/LO/Source/make_opts"
# madgraph.__init__ contains an ancient template repair before its public flag
# can be changed.  Fail closed if that repair would run.
if make_opts.exists() and make_opts.stat().st_mtime < 1480375724:
    raise RuntimeError("BLOCKED: MG5 ancient template repair would change installation")
sys.path.insert(0, str(root))
import madgraph
if Path(madgraph.MG5DIR).resolve() != root:
    raise RuntimeError("unexpected imported MG5 installation")
madgraph.ReadWrite = False
entrypoint = root / "bin/mg5_aMC"
sys.argv = [str(entrypoint), str(driver)]
runpy.run_path(str(entrypoint), run_name="__main__")
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact(path: Path) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing or symlinked MG5 artifact: " + str(path))
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return {"path": str(path), "sha256": digest.hexdigest(), "bytes": size}


def _checker(repo: Path):
    path = Path(repo) / "simulation/zh_pilot/scripts/check_generator.py"
    spec = importlib.util.spec_from_file_location("phase6g_frozen_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safe_argument_path(value, *, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    # MG5 interprets driver lines itself: reject whitespace and all shell/control
    # metacharacters even though the controller uses an argv subprocess API.
    if any(c.isspace() or c in "\"';`$|&<>\\" for c in path.as_posix()):
        raise ValueError("unsafe " + label + " path")
    return path


def _request(events, seed, energy_gev):
    if type(events) is not int or events != 100:
        raise ValueError("MG5 stage supports exactly one 100-event run")
    if type(seed) is not int or not 1 <= seed <= 900000000:
        raise ValueError("MG5 seed must be a literal integer in [1,900000000]")
    if type(energy_gev) not in (int, float) or energy_gev != 13000:
        raise ValueError("MG5 stage supports only 13000 GeV")


def _installation(config):
    if not isinstance(config, dict) or any(config.get(k) != v for k, v in {
        "source_commit": MG5_COMMIT, "source_tag": "v3.5.16",
        "source_url": "https://github.com/mg5amcnlo/mg5amcnlo.git",
    }.items()):
        raise ValueError("unreviewed MG5 installation identity")
    mg5 = _safe_argument_path(config["mg5_path"], label="MG5 installation")
    toolchain = _safe_argument_path(config["toolchain_prefix"], label="toolchain")
    return mg5, toolchain


def _drivers(config):
    mg5, toolchain = _installation(config)
    generation = [
        "set automatic_html_opening False", "set auto_update 0",
        "set nb_core 1", "set run_mode 0",
        "set fortran_compiler " + str(toolchain / "bin/x86_64-conda-linux-gnu-gfortran"),
        "set cpp_compiler " + str(toolchain / "bin/x86_64-conda-linux-gnu-g++"),
        *PROCESS_COMMANDS, "output process -nojpeg", "quit", "",
    ]
    launch = [
        "set automatic_html_opening False", "set auto_update 0",
        "set nb_core 1",
        "launch process -m --name=" + RUN_NAME,
        "shower=OFF", "detector=OFF", "analysis=OFF", "madspin=OFF",
        "reweight=OFF", "done", "done", "quit", "",
    ]
    return "\n".join(generation).encode(), "\n".join(launch).encode(), mg5, toolchain


def _run_card(raw: bytes, *, events: int, seed: int, energy_gev: float) -> bytes:
    text = raw.decode("utf-8")
    for key, value in {"nevents": str(events), "iseed": str(seed),
                       "ebeam1": str(int(energy_gev / 2)),
                       "ebeam2": str(int(energy_gev / 2))}.items():
        pattern = re.compile(r"^(\s*)[^\n=!]+(\s*=\s*" + key + r"\b[^\n]*)$", re.M)
        text, count = pattern.subn(lambda m: m[1] + value + m[2], text)
        if count != 1:
            raise ValueError("missing or duplicated run-card request field: " + key)
    return text.encode("utf-8")


def _frozen_inputs(repo: Path, *, events: int, seed: int, energy_gev: float) -> dict:
    contract_path = repo / "simulation/zh_pilot/config/generator_contract.json"
    raw_contract = contract_path.read_bytes()
    if sha256(raw_contract) != GENERATOR_CONTRACT_SHA256:
        raise ValueError("frozen Phase6F generator contract changed")
    checker = _checker(repo)
    contract = json.loads(raw_contract)
    checker.validate_bundle(contract, repo)
    selected = {item["id"]: repo / item["path"] for item in contract["cards"]}
    raw_run = selected["run"].read_bytes()
    prepared_run = _run_card(raw_run, events=events, seed=seed, energy_gev=energy_gev)
    before, after = checker.parse_run(raw_run.decode()), checker.parse_run(prepared_run.decode())
    changed = {k for k in before if before[k] != after[k]}
    if not changed <= {"nevents", "iseed", "ebeam1", "ebeam2"} or set(before) != set(after):
        raise ValueError("prepared run changed a frozen physics setting")
    return {"process.mg5": selected["process_zbb"].read_bytes(),
            "run_card.dat": prepared_run, "param_card.dat": selected["param"].read_bytes()}


def prepare_mg5_stage(output, *, repo=REPO, installation: dict, seed=20261104,
                       events=100, energy_gev=13000, python_executable=None) -> dict:
    """Create a fresh text-only workdir; never import/execute MG5 itself.

    The outer preflight verifies installed file identities, environment activation,
    path protection, resources, and all contracts.  The stage independently binds
    the reviewed generator configuration and the request-specific cards.
    """
    _request(events, seed, energy_gev)
    repo = Path(repo).resolve()
    work = _safe_argument_path(output, label="output")
    gen, launch, mg5, toolchain = _drivers(installation)
    python = _safe_argument_path(python_executable or toolchain / "bin/python", label="Python")
    if work.exists():
        raise ValueError("MG5 workdir already exists; preserve it and choose a fresh path")
    for protected in (repo, mg5, toolchain):
        if work == protected or work.is_relative_to(protected) or protected.is_relative_to(work):
            raise ValueError("MG5 workdir overlaps protected source or installation")
    inputs = _frozen_inputs(repo, events=events, seed=seed, energy_gev=energy_gev)
    work.mkdir(parents=True, exist_ok=False)
    (work / "inputs").mkdir()
    for name, raw in inputs.items():
        (work / "inputs" / name).write_bytes(raw)
    (work / "generate.mg5").write_bytes(gen)
    (work / "launch.mg5").write_bytes(launch)
    plan = {
        "schema_version": 1, "status": "PREPARED_TEXT_ONLY",
        "execution_authority": "NONE_REQUIRES_OUTER_AUTHORIZATION_AND_RESOURCE_CAPABILITY",
        "new_physics_events_generated": 0, "repo": str(repo), "workdir": str(work),
        "request": {"process": "zh", "profile": PROFILE, "events": events,
                    "seed": seed, "energy_gev": energy_gev, "workers": 1},
        "installation": dict(installation), "python_executable": str(python),
        "generator_contract_sha256": GENERATOR_CONTRACT_SHA256,
        "readonly_runtime_adapter_sha256": sha256(READONLY_MG5_ADAPTER.encode()),
        "installation_write_policy": "madgraph.ReadWrite=False before UFO/interface/export imports; -O -B; Python audit rejects installed-root/toolchain mutations",
        "run_name": RUN_NAME,
        "drivers": {"generate": artifact(work / "generate.mg5"),
                    "launch": artifact(work / "launch.mg5")},
        "cards": {key: artifact(work / "inputs" / name) for key, name in {
            "process_card": "process.mg5", "run_card": "run_card.dat",
            "param_card": "param_card.dat"}.items()},
        "future_outputs": {"process_dir": "process", "lhe": "process/Events/zh100/unweighted_events.lhe.gz",
                           "banner": "process/Events/zh100/*_banner.txt",
                           "process_log": "process_generation.log", "run_log": "event_generation.log"},
        "environment_requirement": "outer controller supplies the existing activated Phase6A toolchain environment",
        "retry_policy": "NONE_NO_SMOKE_MG5_EVENTS_NO_AUTOMATIC_RERUN_OR_REPLACEMENT",
    }
    (work / "prepared_stage.json").write_bytes((json.dumps(plan, indent=2) + "\n").encode())
    return plan


def _check_prepared(plan: dict):
    if (not isinstance(plan, dict) or type(plan.get("schema_version")) is not int or plan["schema_version"] != 1
            or plan.get("run_name") != RUN_NAME or plan.get("status") != "PREPARED_TEXT_ONLY"
            or plan.get("execution_authority") != "NONE_REQUIRES_OUTER_AUTHORIZATION_AND_RESOURCE_CAPABILITY"
            or type(plan.get("new_physics_events_generated")) is not int or plan["new_physics_events_generated"] != 0
            or plan.get("generator_contract_sha256") != GENERATOR_CONTRACT_SHA256
            or plan.get("readonly_runtime_adapter_sha256") != sha256(READONLY_MG5_ADAPTER.encode())):
        raise ValueError("invalid prepared MG5 stage")
    req = plan["request"]
    _request(req["events"], req["seed"], req["energy_gev"])
    if req.get("profile") != PROFILE or req.get("process") != "zh" or type(req.get("workers")) is not int or req["workers"] != 1:
        raise ValueError("unsupported prepared MG5 profile/workers")
    work = _safe_argument_path(plan["workdir"], label="output")
    if work.is_symlink() or not work.is_dir():
        raise ValueError("missing MG5 prepared directory")
    if json.loads((work / "prepared_stage.json").read_bytes()) != plan:
        raise ValueError("prepared MG5 plan changed")
    gen, launch, mg5, toolchain = _drivers(plan["installation"])
    python = _safe_argument_path(plan["python_executable"], label="Python")
    if python != (toolchain / "bin/python").resolve():
        raise ValueError("MG5 execution must reuse the reviewed toolchain Python")
    repo = Path(plan["repo"]).resolve()
    for protected in (repo, mg5, toolchain):
        if work == protected or work.is_relative_to(protected) or protected.is_relative_to(work):
            raise ValueError("MG5 workdir overlaps protected source or installation")
    inputs = _frozen_inputs(repo, events=req["events"], seed=req["seed"], energy_gev=req["energy_gev"])
    expected = {"generate.mg5": gen, "launch.mg5": launch,
                **{"inputs/" + name: raw for name, raw in inputs.items()}}
    for relative, raw in expected.items():
        path = work / relative
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError("prepared MG5 driver/card changed: " + relative)
    for key, name in {"process_card": "process.mg5", "run_card": "run_card.dat", "param_card": "param_card.dat"}.items():
        if plan["cards"][key] != artifact(work / "inputs" / name):
            raise ValueError("prepared card descriptor changed: " + key)
    for key, name in {"generate": "generate.mg5", "launch": "launch.mg5"}.items():
        if plan["drivers"][key] != artifact(work / name):
            raise ValueError("prepared driver descriptor changed: " + key)
    return work, mg5, python


def parse_generation_summary(text: str) -> dict:
    """Parse one actual MG5 final summary; values have display precision only."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", text)
    marker = re.compile(r"=== Results Summary for run:\s*" + RUN_NAME + r"\s+tag:\s*(\S+).*?===")
    blocks = list(marker.finditer(clean))
    if len(blocks) != 1:
        raise ValueError("expected one final zh100 MG5 result summary")
    body = clean[blocks[0].end():]
    crosses = re.findall(r"^\s*Cross-section\s*:\s*(" + NUM + r")\s*\+[-/]\s*(" + NUM + r")\s+pb\s*$", body, re.M)
    counts = re.findall(r"^\s*Nb of events\s*:\s*(\d+)\s*$", body, re.M)
    if len(crosses) != 1 or len(counts) != 1 or int(counts[0]) != 100:
        raise ValueError("missing/ambiguous cross section or actual event count other than 100")
    try:
        sigma, error = (Decimal(v.replace("d", "e").replace("D", "E")) for v in crosses[0])
    except InvalidOperation as exc:
        raise ValueError("invalid MG5 numerical summary") from exc
    if not sigma.is_finite() or not error.is_finite() or sigma <= 0 or error < 0:
        raise ValueError("nonfinite/invalid MG5 cross section or integration uncertainty")
    return {"events": 100, "cross_section_pb": str(sigma), "uncertainty_pb": str(error),
            "run_tag": blocks[0].group(1), "precision": "MG5_4_SIGNIFICANT_DIGIT_DISPLAY_ONLY",
            "authority": "independent actual MG5 log; full precision and agreement require LHE/banner validation"}


def execute_mg5_stage(prepared: dict, *, run_command: Callable) -> dict:
    """Invoke only the outer authorized resource controller, exactly once/stage.

    The controller callback signature is ``run_command(argv, cwd, stage)`` and
    returns a mapping with ``exit_code`` and preferably ``log_path``.  This
    adapter never grants authorization, launches an independent subprocess, or
    restarts any failed run.  Physical validation is the next independent gate.
    """
    if not callable(run_command):
        raise ValueError("outer authorization/resource run_command capability is required")
    work, mg5, python = _check_prepared(prepared)
    toolchain = _installation(prepared["installation"])[1]
    process = work / "process"
    if process.exists() or process.is_symlink():
        raise ValueError("MG5 process output exists; no rerun or overwrite is allowed")
    execution = {}
    for stage, driver, log in (("mg5_process_export", "generate.mg5", "process_generation.log"),
                               ("mg5_100_event_generation", "launch.mg5", "event_generation.log")):
        _check_prepared(prepared)
        if stage == "mg5_100_event_generation":
            cards = process / "Cards"
            if (process.is_symlink() or process.resolve().parent != work or cards.is_symlink()
                    or not cards.is_dir() or (process / "Events" / RUN_NAME).exists()):
                raise ValueError("missing/unsafe exported Cards directory or existing run")
            for name in ("run_card.dat", "param_card.dat"):
                destination = cards / name
                if destination.is_symlink():
                    raise ValueError("unsafe exported card destination")
                destination.write_bytes((work / "inputs" / name).read_bytes())
        result = run_command([str(python), "-O", "-B", "-c", READONLY_MG5_ADAPTER,
                              str(mg5), str(work / driver), str(toolchain)], work, stage)
        if not isinstance(result, dict) or type(result.get("exit_code")) is not int or result["exit_code"] != 0:
            raise ValueError("guarded MG5 command did not complete successfully: " + stage)
        execution[stage] = dict(result)
        actual_log = Path(result.get("log_path", work / log)).resolve()
        if actual_log.parent not in {work, work.parent / "logs"}:
            raise ValueError("MG5 log path is outside its workdir")
        execution[stage]["log"] = artifact(actual_log)
    run = process / "Events" / RUN_NAME
    if run.is_symlink() or not run.is_dir():
        raise ValueError("missing actual MG5 run directory")
    banners = list(run.glob("*_banner.txt"))
    if len(banners) != 1:
        raise ValueError("expected exactly one original MG5 run banner")
    summary = parse_generation_summary(Path(execution["mg5_100_event_generation"]["log"]["path"]).read_text(encoding="utf-8"))
    actual_cards = {key: artifact(process / "Cards" / name) for key, name in {
        "post_run_process": "proc_card_mg5.dat", "post_run_run": "run_card.dat",
        "post_run_param": "param_card.dat", "configuration": "me5_configuration.txt"}.items()}
    return {
        "schema_version": 1, "status": "MG5_OUTPUT_PRESENT_PENDING_INDEPENDENT_LHE_PHYSICS_VALIDATION",
        "profile": PROFILE, "request": dict(prepared["request"]),
        "lhe_path": str(run / "unweighted_events.lhe.gz"), "process_dir": str(process),
        "banner_path": str(banners[0]), "run_log": execution["mg5_100_event_generation"]["log"]["path"],
        "cards": actual_cards, "prepared_cards": dict(prepared["cards"]),
        "artifacts": {"lhe_gz": artifact(run / "unweighted_events.lhe.gz"),
                      "banner": artifact(banners[0]),
                      "run_log": execution["mg5_100_event_generation"]["log"],
                      "prepared_process": prepared["cards"]["process_card"],
                      "prepared_run": prepared["cards"]["run_card"],
                      "prepared_param": prepared["cards"]["param_card"]},
        "generation": summary, "execution": execution,
        "source_identity": {**dict(prepared["installation"]), "version": "3.5.16"},
        "source_cross_section_pb": summary["cross_section_pb"],
        "integration_uncertainty_pb": summary["uncertainty_pb"],
        "cross_section_scope": "LOG_DISPLAY_ONLY_NOT_A_REPLACEMENT_FOR_VALIDATED_LHE_INIT",
        "full_original_event_denominator": 100,
        "source_included_decay_ids": ["Z_to_b_bbar"],
        "missing_decay_ids_pending_weight_closure": ["H_to_gamma_gamma"],
        "retry_or_event_replacement_performed": False,
    }

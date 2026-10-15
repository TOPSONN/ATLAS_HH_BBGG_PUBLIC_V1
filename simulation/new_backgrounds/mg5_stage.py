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

REPO = Path(__file__).resolve().parents[2]
PROFILES = {"zh": "B04_ZH_BBGG", "tth": "B05_TTH_HGG", "bbgj": "B06_BBGJ"}
PROFILE = PROFILES["zh"]
RUN_NAME = "zh1000"
MG5_COMMIT = "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"
GENERATOR_CONTRACT_SHA256 = "a385af80aebb8462b73c6eb83de54a7f996d4f1e4d5e6aff840b5c83f44d2cf4"
MODEL = "import model sm-no_b_mass"
PROTON = "define p = g u c d s b u~ c~ d~ s~ b~"
PROCESS_COMMANDS = {
    "zh": [MODEL, PROTON, "generate p p > z h QCD=0 QED=2, z > b b~"],
    "tth": [MODEL, PROTON, "generate p p > t t~ h QCD=2 QED=1"],
    "bbgj": [MODEL, PROTON, "define j4 = g u c d s u~ c~ d~ s~", "generate p p > b b~ a j4 QCD=3 QED=1"],
}
RUN_OVERRIDES = {
    "zh": {},
    "tth": {"run_tag": "phase6g_tth_1k", "scale": 235.5, "dsqrt_q2fact1": 235.5, "dsqrt_q2fact2": 235.5},
    "bbgj": {"run_tag": "phase6g_bbgj_1k", "scale": 125.0, "dsqrt_q2fact1": 125.0, "dsqrt_q2fact2": 125.0,
             "maxjetflavor": 4, "ptb": 25.0, "ptj": 25.0, "pta": 25.0, "etab": 2.5, "etaj": 2.5, "etaa": 2.5,
             "drbb": 0.4, "drbj": 0.4, "drab": 0.4, "draj": 0.4, "drjj": 0.4},
}
PRODUCTION_ORDERS = {"zh": {"QCD":0,"QED":2}, "tth": {"QCD":2,"QED":1}, "bbgj": {"QCD":3,"QED":1}}
MODEL_PARAMETERS = {"mdl_MZ":91.188,"mdl_MH":125.0,"mdl_MT":173.0,"mdl_WZ":2.441404,"mdl_WH":0.00638233934,
                    "mdl_WT":1.4915,"mdl_WW":2.0476,"mdl_ymt":173.0,"aEWM1":132.507,"mdl_Gf":1.16639e-5,"aS":0.129783}
NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?"
# This adapter executes only when passed to the outer guarded callback.  It
# changes runtime cache/installation-write flags, never installed source or the
# matrix element.  -O is required to prevent bin/mg5_aMC's shell self-relaunch.
READONLY_MG5_ADAPTER = '''import os
import runpy
import json
import hashlib
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
from madgraph.interface.master_interface import MasterCmd
from madgraph.various.banner import RunCardLO
from models.check_param_card import ParamCard
from models.model_reader import ModelReader
original_output = MasterCmd.do_output
def amplitude_records(amplitude, model, scope="production"):
    if "amplitudes" in amplitude:
        return [row for item in amplitude.get("amplitudes") for row in amplitude_records(item, model, scope)] + [row for item in amplitude.get("decay_chains") for row in amplitude_records(item, model, "Z_decay")]
    process = amplitude.get("process")
    diagrams = amplitude.get("diagrams")
    orders = set()
    for diagram in diagrams:
        diagram.calculate_orders(model)
        orders.add(tuple(sorted((key, value) for key, value in diagram.get("orders").items() if key != "WEIGHTED")))
    return [{"scope": scope, "initial_pdgs": [leg.get("id") for leg in process.get("legs") if not leg.get("state")], "final_pdgs": [leg.get("id") for leg in process.get("legs") if leg.get("state")], "diagram_count": len(diagrams), "actual_amplitude_orders": [dict(row) for row in sorted(orders)]}]
def guarded_output(self, line, *args, **kwargs):
    expected = json.loads((driver.parent / "amplitude_contract.json").read_bytes())
    alias = expected["process"]
    if alias not in ("zh", "tth", "bbgj") or line.strip() != "process -nojpeg":
        raise RuntimeError("unexpected process export")
    records = [row for amp in self._curr_amps for row in amplitude_records(amp, self._curr_model)]
    if not records or sorted(self._multiparticles["p"]) != [-5,-4,-3,-2,-1,1,2,3,4,5,21]:
        raise RuntimeError("no retained Born diagrams or wrong five-flavour proton")
    for row in records:
        order = {"QCD":0, "QED":1} if row["scope"] == "Z_decay" else expected["production_orders"]
        if row["diagram_count"] <= 0 or row["actual_amplitude_orders"] != [order]:
            raise RuntimeError("actual Born coupling orders differ")
        initial, final = sorted(row["initial_pdgs"]), sorted(row["final_pdgs"])
        if row["scope"] == "Z_decay":
            valid = alias == "zh" and initial == [23] and final == [-5,5]
        elif alias == "zh":
            valid = initial in [[-i,i] for i in range(1,6)] and final == [23,25]
        elif alias == "tth":
            valid = initial in [[21,21]] + [[-i,i] for i in range(1,6)] and final == [-6,6,25]
        else:
            j4 = [-4,-3,-2,-1,1,2,3,4,21]
            valid = len(initial) == 2 and all(i in [-5,-4,-3,-2,-1,1,2,3,4,5,21] for i in initial) and len(final) == 4 and final.count(5) == final.count(-5) == final.count(22) == 1 and next(i for i in final if i not in (5,-5,22)) in j4
        if not valid:
            raise RuntimeError("actual Born production/decay topology differs")
    if (alias == "zh") != any(row["scope"] == "Z_decay" for row in records):
        raise RuntimeError("unexpected/missing source Z decay chain")
    if alias == "bbgj" and sorted(self._multiparticles["j4"]) != [-4,-3,-2,-1,1,2,3,4,21]:
        raise RuntimeError("actual j4 alias differs")
    run = RunCardLO(str(driver.parent / "inputs/run_card.dat"))
    if any(run[key] != value for key, value in expected["official_run_checks"].items()):
        raise RuntimeError("actual official RunCardLO readback differs")
    param = ParamCard(str(driver.parent / "inputs/param_card.dat"))
    reader = ModelReader(self._curr_model)
    reader.set_parameters_and_couplings(param_card=param)
    values = reader["parameter_dict"]
    actual = {key: float(complex(values[key]).real) for key in expected["model_parameters"]}
    if actual != expected["model_parameters"]:
        raise RuntimeError("actual restricted model mass/width/EW/Yukawa differs")
    symbols = {str(pdg): self._curr_model.get_particle(pdg)["mass"] for pdg in (4,5)}
    if any(value != "ZERO" for value in symbols.values()) or values["ZERO"] != 0:
        raise RuntimeError("restricted c/b are not massless")
    receipt = {"schema_version":1, "status":"PASS_ACTUAL_TREE_AMPLITUDES_AND_OFFICIAL_CARDS", "process":alias, "profile":expected["profile"], "amplitude_records":records, "actual_parameters":actual, "actual_restricted_mass_symbols":symbols, "official_run_readback":{key:run[key] for key in expected["official_run_checks"]}, "source_commit":"3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7", "event_generation_invocations":0, "cross_section_pb":"NOT_YET_INTEGRATED"}
    with (driver.parent / "amplitude_validation.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\\n")
    return original_output(self, line, *args, **kwargs)
MasterCmd.do_output = guarded_output
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


def _request(events, seed, energy_gev, process="zh"):
    if process not in PROFILES:
        raise ValueError("unsupported background process")
    if type(events) is not int or events != 1000:
        raise ValueError("MG5 stage supports exactly one 1000-event run per process")
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


def _drivers(config, process="zh"):
    mg5, toolchain = _installation(config)
    generation = [
        "set automatic_html_opening False --no_save", "set auto_update 0 --no_save",
        "set nb_core 1 --no_save", "set run_mode 0 --no_save",
        "set fortran_compiler x86_64-conda-linux-gnu-gfortran --no_save",
        "set cpp_compiler x86_64-conda-linux-gnu-g++ --no_save",
        *PROCESS_COMMANDS[process], "output process -nojpeg", "quit", "",
    ]
    launch = [
        "set automatic_html_opening False --no_save", "set auto_update 0 --no_save",
        "set nb_core 1 --no_save",
        "launch process -m --name=" + process + "1000",
        "shower=OFF", "detector=OFF", "analysis=OFF", "madspin=OFF",
        "reweight=OFF", "done", "done", "quit", "",
    ]
    return "\n".join(generation).encode(), "\n".join(launch).encode(), mg5, toolchain


def _run_card(raw: bytes, *, events: int, seed: int, energy_gev: float, process="zh") -> bytes:
    text = raw.decode("utf-8")
    for key, value in {"nevents": str(events), "iseed": str(seed),
                       "ebeam1": str(int(energy_gev / 2)),
                       "ebeam2": str(int(energy_gev / 2)), **RUN_OVERRIDES[process]}.items():
        pattern = re.compile(r"^(\s*)[^\n=!]+(\s*=\s*" + key + r"\b[^\n]*)$", re.M)
        text, count = pattern.subn(lambda m: m[1] + str(value) + m[2], text)
        if count != 1:
            raise ValueError("missing or duplicated run-card request field: " + key)
    return text.encode("utf-8")


def _frozen_inputs(repo: Path, *, events: int, seed: int, energy_gev: float, process="zh") -> dict:
    contract_path = repo / "simulation/zh_pilot/config/generator_contract.json"
    raw_contract = contract_path.read_bytes()
    if sha256(raw_contract) != GENERATOR_CONTRACT_SHA256:
        raise ValueError("frozen Phase6F generator contract changed")
    checker = _checker(repo)
    contract = json.loads(raw_contract)
    checker.validate_bundle(contract, repo)
    selected = {item["id"]: repo / item["path"] for item in contract["cards"]}
    raw_run = selected["run"].read_bytes()
    new_root = repo / "simulation/new_backgrounds"
    bundle = json.loads((new_root / "config/generator_contract.json").read_bytes())
    if bundle["source_identity"] != contract["source_identity"] or bundle["profiles"][process]["profile"] != PROFILES[process]:
        raise ValueError("new background source/profile identity differs")
    for row in bundle["cards"]:
        path = repo / row["path"]
        if path.is_symlink() or not path.resolve().is_relative_to(new_root.resolve()) or sha256(path.read_bytes()) != row["sha256"]:
            raise ValueError("new background frozen card changed: " + row["id"])
    if (new_root / "cards/run_card.dat").read_bytes() != raw_run or (new_root / "cards/param_card.dat").read_bytes() != selected["param"].read_bytes():
        raise ValueError("frozen common cards differ from exact Phase6F reviewed bytes")
    process_raw = (new_root / ("cards/" + process + ".mg5")).read_bytes()
    lines = [line.split("#", 1)[0].strip() for line in process_raw.decode().splitlines() if line.split("#", 1)[0].strip()]
    if lines != PROCESS_COMMANDS[process] or bundle["profiles"][process]["run_overrides"] != RUN_OVERRIDES[process]:
        raise ValueError("background process/coupling orders or cuts/scales changed")
    prepared_run = _run_card(raw_run, events=events, seed=seed, energy_gev=energy_gev, process=process)
    before, after = checker.parse_run(raw_run.decode()), checker.parse_run(prepared_run.decode())
    changed = {k for k in before if before[k] != after[k]}
    if not changed <= {"nevents", "iseed", "ebeam1", "ebeam2", *RUN_OVERRIDES[process]} or set(before) != set(after):
        raise ValueError("prepared run changed a frozen physics setting")
    return {"process.mg5": process_raw,
            "run_card.dat": prepared_run, "param_card.dat": selected["param"].read_bytes()}


def _amplitude_contract(repo, inputs, process):
    values = _checker(repo).parse_run(inputs["run_card.dat"].decode())
    keys = ("nevents", "iseed", "lpp1", "lpp2", "ebeam1", "ebeam2", "pdlabel", "lhaid", "fixed_ren_scale", "fixed_fac_scale",
            "scale", "dsqrt_q2fact1", "dsqrt_q2fact2", "dynamical_scale_choice", "scalefact", "bwcutoff", "cut_decays",
            "ptb", "ptj", "pta", "etab", "etaj", "etaa", "drbb", "drbj", "drab", "draj", "drjj", "maxjetflavor",
            "ptgmin", "ickkw", "use_syst", "event_norm", "lhe_version")
    return {"process":process, "profile":PROFILES[process], "production_orders":PRODUCTION_ORDERS[process],
            "official_run_checks":{key:values[key] for key in keys}, "model_parameters":MODEL_PARAMETERS}


def prepare_mg5_stage(output, *, repo=REPO, installation: dict, seed=20261104,
                       events=1000, energy_gev=13000, process="zh", python_executable=None) -> dict:
    """Create a fresh text-only workdir; never import/execute MG5 itself.

    The outer preflight verifies installed file identities, environment activation,
    path protection, resources, and all contracts.  The stage independently binds
    the reviewed generator configuration and the request-specific cards.
    """
    _request(events, seed, energy_gev, process)
    repo = Path(repo).resolve()
    work = _safe_argument_path(output, label="output")
    gen, launch, mg5, toolchain = _drivers(installation, process)
    python = _safe_argument_path(python_executable or toolchain / "bin/python", label="Python")
    if work.exists():
        raise ValueError("MG5 workdir already exists; preserve it and choose a fresh path")
    for protected in (repo, mg5, toolchain):
        if work == protected or work.is_relative_to(protected) or protected.is_relative_to(work):
            raise ValueError("MG5 workdir overlaps protected source or installation")
    inputs = _frozen_inputs(repo, events=events, seed=seed, energy_gev=energy_gev, process=process)
    work.mkdir(parents=True, exist_ok=False)
    (work / "inputs").mkdir()
    for name, raw in inputs.items():
        (work / "inputs" / name).write_bytes(raw)
    (work / "generate.mg5").write_bytes(gen)
    (work / "launch.mg5").write_bytes(launch)
    amplitude_contract = json.dumps(_amplitude_contract(repo, inputs, process), indent=2, allow_nan=False) + "\n"
    (work / "amplitude_contract.json").write_bytes(amplitude_contract.encode())
    plan = {
        "schema_version": 1, "status": "PREPARED_TEXT_ONLY",
        "execution_authority": "NONE_REQUIRES_OUTER_AUTHORIZATION_AND_RESOURCE_CAPABILITY",
        "new_physics_events_generated": 0, "repo": str(repo), "workdir": str(work),
        "request": {"process": process, "profile": PROFILES[process], "events": events,
                    "seed": seed, "energy_gev": energy_gev, "workers": 1},
        "installation": dict(installation), "python_executable": str(python),
        "generator_contract_sha256": GENERATOR_CONTRACT_SHA256,
        "background_generator_contract_sha256": artifact(repo / "simulation/new_backgrounds/config/generator_contract.json")["sha256"],
        "amplitude_contract": artifact(work / "amplitude_contract.json"),
        "readonly_runtime_adapter_sha256": sha256(READONLY_MG5_ADAPTER.encode()),
        "installation_write_policy": "madgraph.ReadWrite=False before UFO/interface/export imports; -O -B; Python audit rejects installed-root/toolchain mutations",
        "run_name": process + "1000",
        "drivers": {"generate": artifact(work / "generate.mg5"),
                    "launch": artifact(work / "launch.mg5")},
        "cards": {key: artifact(work / "inputs" / name) for key, name in {
            "process_card": "process.mg5", "run_card": "run_card.dat",
            "param_card": "param_card.dat"}.items()},
        "future_outputs": {"process_dir": "process", "lhe": "process/Events/" + process + "1000/unweighted_events.lhe.gz",
                           "banner": "process/Events/" + process + "1000/*_banner.txt",
                           "process_log": "process_generation.log", "run_log": "event_generation.log"},
        "environment_requirement": "outer controller supplies the existing activated Phase6A toolchain environment",
        "retry_policy": "NONE_NO_SMOKE_MG5_EVENTS_NO_AUTOMATIC_RERUN_OR_REPLACEMENT",
    }
    (work / "prepared_stage.json").write_bytes((json.dumps(plan, indent=2) + "\n").encode())
    return plan


def _check_prepared(plan: dict):
    if (not isinstance(plan, dict) or type(plan.get("schema_version")) is not int or plan["schema_version"] != 1
            or plan.get("status") != "PREPARED_TEXT_ONLY"
            or plan.get("execution_authority") != "NONE_REQUIRES_OUTER_AUTHORIZATION_AND_RESOURCE_CAPABILITY"
            or type(plan.get("new_physics_events_generated")) is not int or plan["new_physics_events_generated"] != 0
            or plan.get("generator_contract_sha256") != GENERATOR_CONTRACT_SHA256
            or plan.get("readonly_runtime_adapter_sha256") != sha256(READONLY_MG5_ADAPTER.encode())):
        raise ValueError("invalid prepared MG5 stage")
    req = plan["request"]
    _request(req["events"], req["seed"], req["energy_gev"], req["process"])
    if req.get("profile") != PROFILES[req["process"]] or plan["run_name"] != req["process"] + "1000" or type(req.get("workers")) is not int or req["workers"] != 1:
        raise ValueError("unsupported prepared MG5 profile/workers")
    work = _safe_argument_path(plan["workdir"], label="output")
    if work.is_symlink() or not work.is_dir():
        raise ValueError("missing MG5 prepared directory")
    if json.loads((work / "prepared_stage.json").read_bytes()) != plan:
        raise ValueError("prepared MG5 plan changed")
    gen, launch, mg5, toolchain = _drivers(plan["installation"], req["process"])
    python = _safe_argument_path(plan["python_executable"], label="Python")
    if python != (toolchain / "bin/python").resolve():
        raise ValueError("MG5 execution must reuse the reviewed toolchain Python")
    repo = Path(plan["repo"]).resolve()
    for protected in (repo, mg5, toolchain):
        if work == protected or work.is_relative_to(protected) or protected.is_relative_to(work):
            raise ValueError("MG5 workdir overlaps protected source or installation")
    inputs = _frozen_inputs(repo, events=req["events"], seed=req["seed"], energy_gev=req["energy_gev"], process=req["process"])
    expected = {"generate.mg5": gen, "launch.mg5": launch,
                "amplitude_contract.json": (json.dumps(_amplitude_contract(repo, inputs, req["process"]), indent=2, allow_nan=False) + "\n").encode(),
                **{"inputs/" + name: raw for name, raw in inputs.items()}}
    for relative, raw in expected.items():
        path = work / relative
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError("prepared MG5 driver/card changed: " + relative)
    if plan["amplitude_contract"] != artifact(work / "amplitude_contract.json") or plan["background_generator_contract_sha256"] != artifact(repo / "simulation/new_backgrounds/config/generator_contract.json")["sha256"]:
        raise ValueError("prepared background/amplitude contract changed")
    for key, name in {"process_card": "process.mg5", "run_card": "run_card.dat", "param_card": "param_card.dat"}.items():
        if plan["cards"][key] != artifact(work / "inputs" / name):
            raise ValueError("prepared card descriptor changed: " + key)
    for key, name in {"generate": "generate.mg5", "launch": "launch.mg5"}.items():
        if plan["drivers"][key] != artifact(work / name):
            raise ValueError("prepared driver descriptor changed: " + key)
    return work, mg5, python


def parse_generation_summary(text: str, process="zh") -> dict:
    """Parse one actual MG5 final summary; values have display precision only."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", text)
    marker = re.compile(r"=== Results Summary for run:\s*" + process + r"1000\s+tag:\s*(\S+).*?===")
    blocks = list(marker.finditer(clean))
    if len(blocks) != 1:
        raise ValueError("expected one final " + process + "1000 MG5 result summary")
    body = clean[blocks[0].end():]
    crosses = re.findall(r"^\s*Cross-section\s*:\s*(" + NUM + r")\s*\+[-/]\s*(" + NUM + r")\s+pb\s*$", body, re.M)
    counts = re.findall(r"^\s*Nb of events\s*:\s*(\d+)\s*$", body, re.M)
    if len(crosses) != 1 or len(counts) != 1 or int(counts[0]) != 1000:
        raise ValueError("missing/ambiguous cross section or actual event count other than 1000")
    try:
        sigma, error = (Decimal(v.replace("d", "e").replace("D", "E")) for v in crosses[0])
    except InvalidOperation as exc:
        raise ValueError("invalid MG5 numerical summary") from exc
    if not sigma.is_finite() or not error.is_finite() or sigma <= 0 or error < 0:
        raise ValueError("nonfinite/invalid MG5 cross section or integration uncertainty")
    return {"events": 1000, "cross_section_pb": str(sigma), "uncertainty_pb": str(error),
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
    run_name = prepared["run_name"]
    process_alias = prepared["request"]["process"]
    for stage, driver, log in (("mg5_process_export", "generate.mg5", "process_generation.log"),
                               ("mg5_1000_event_generation", "launch.mg5", "event_generation.log")):
        _check_prepared(prepared)
        if stage == "mg5_1000_event_generation":
            cards = process / "Cards"
            if (process.is_symlink() or process.resolve().parent != work or cards.is_symlink()
                    or not cards.is_dir() or (process / "Events" / run_name).exists()):
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
        if stage == "mg5_process_export":
            amplitude_path = work / "amplitude_validation.json"
            amplitude = json.loads(amplitude_path.read_bytes())
            if amplitude.get("status") != "PASS_ACTUAL_TREE_AMPLITUDES_AND_OFFICIAL_CARDS" or amplitude.get("profile") != PROFILES[process_alias] or amplitude.get("process") != process_alias or amplitude.get("event_generation_invocations") != 0:
                raise ValueError("actual source amplitude gate did not pass before integration")
    run = process / "Events" / run_name
    if run.is_symlink() or not run.is_dir():
        raise ValueError("missing actual MG5 run directory")
    banners = list(run.glob("*_banner.txt"))
    if len(banners) != 1:
        raise ValueError("expected exactly one original MG5 run banner")
    summary = parse_generation_summary(Path(execution["mg5_1000_event_generation"]["log"]["path"]).read_text(encoding="utf-8"), process_alias)
    actual_cards = {key: artifact(process / "Cards" / name) for key, name in {
        "post_run_process": "proc_card_mg5.dat", "post_run_run": "run_card.dat",
        "post_run_param": "param_card.dat", "configuration": "me5_configuration.txt"}.items()}
    return {
        "schema_version": 1, "status": "MG5_OUTPUT_PRESENT_PENDING_INDEPENDENT_LHE_PHYSICS_VALIDATION",
        "profile": PROFILES[process_alias], "request": dict(prepared["request"]),
        "lhe_path": str(run / "unweighted_events.lhe.gz"), "process_dir": str(process),
        "banner_path": str(banners[0]), "run_log": execution["mg5_1000_event_generation"]["log"]["path"],
        "cards": actual_cards, "prepared_cards": dict(prepared["cards"]),
        "artifacts": {"lhe_gz": artifact(run / "unweighted_events.lhe.gz"),
                      "banner": artifact(banners[0]),
                      "run_log": execution["mg5_1000_event_generation"]["log"],
                      "prepared_process": prepared["cards"]["process_card"],
                      "prepared_run": prepared["cards"]["run_card"],
                      "prepared_param": prepared["cards"]["param_card"]},
        "generation": summary, "execution": execution,
        "amplitude_validation": artifact(work / "amplitude_validation.json"),
        "amplitude_contract": prepared["amplitude_contract"],
        "background_generator_contract_sha256": prepared["background_generator_contract_sha256"],
        "source_identity": {**dict(prepared["installation"]), "version": "3.5.16"},
        "source_cross_section_pb": summary["cross_section_pb"],
        "integration_uncertainty_pb": summary["uncertainty_pb"],
        "cross_section_scope": "LOG_DISPLAY_ONLY_NOT_A_REPLACEMENT_FOR_VALIDATED_LHE_INIT",
        "full_original_event_denominator": 1000,
        "source_included_decay_ids": ["Z_to_b_bbar"] if process_alias == "zh" else [],
        "missing_decay_ids_pending_weight_closure": ["H_to_gamma_gamma"] if process_alias != "bbgj" else [],
        "retry_or_event_replacement_performed": False,
    }

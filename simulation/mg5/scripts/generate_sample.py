#!/usr/bin/env python3
"""Self-service MG5 generation. All output is local; existing runs are protected."""
from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from validate_lhe import canonical_card, sha256, validate_data, ValidationError
from installation import verify

REPO = Path(__file__).resolve().parents[3]
SOURCE_COMMIT = "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"
PROFILES = {
    "bbgg": ("generate p p > b b~ a a QCD=2 QED=2", [5, -5, 22, 22]),
    "diphoton": ("generate p p > a a QCD=0 QED=2", [22, 22]),
}
BASE_SETTINGS = {
    "lpp1": 1, "lpp2": 1, "pdlabel": "cteq6l1", "lhaid": 10042,
    "fixed_ren_scale": True, "fixed_fac_scale": True, "scale": 125.0,
    "dsqrt_q2fact1": 125.0, "dsqrt_q2fact2": 125.0,
    "dynamical_scale_choice": -1, "scalefact": 1.0,
    "pta": 25.0, "ptb": 20.0, "etaa": 2.5, "etab": 5.0,
    "draa": 0.4, "drab": 0.4, "drbb": 0.4, "ptgmin": 0.0,
    "ickkw": 0, "use_syst": False, "systematics_program": "none", "event_norm": "average",
    "maxjetflavor": 4,
}


def run(command, cwd, log):
    started = time.monotonic()
    with log.open("wb") as stream:
        result = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"Generator exit {result.returncode}; see {log}")
    return {"exit_code": result.returncode, "elapsed_seconds": time.monotonic() - started}


def gzip_deterministic(data):
    import io
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0) as stream:
        stream.write(data)
    return buffer.getvalue()


def profile_from_card(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^# validation_profile: (\w+)$", text, re.M)
    if not match or match[1] not in PROFILES:
        raise ValueError("Unknown process validation profile; follow USER_GUIDE_ZH_TW before adding a process")
    profile = match[1]
    commands = [line.split("#", 1)[0].strip() for line in text.splitlines() if line.split("#", 1)[0].strip()]
    expected = ["import model sm-no_b_mass", "define p = g u c d s b u~ c~ d~ s~ b~", PROFILES[profile][0]]
    if commands != expected:
        raise ValueError("Process card differs from an implemented, reviewed physics profile")
    return profile, commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--process", type=Path, default=REPO / "simulation/mg5/cards/bbgg.mg5")
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261013)
    parser.add_argument("--energy", type=float, default=13000, help="total pp centre-of-mass energy in GeV")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-card", type=Path)
    parser.add_argument("--param-card", type=Path)
    args = parser.parse_args()
    if args.events <= 0 or not 1 <= args.seed <= 30081 ** 2:
        parser.error("events must be positive; seed must be in [1, 30081^2]")
    import math
    if not math.isfinite(args.energy) or args.energy <= 0:
        parser.error("energy must be finite and positive (GeV)")
    # Prevent unnoticed generation with a different installation.
    config = json.loads(args.installation.read_text())
    mg5, source_identity = verify(config)
    head = source_identity["source_commit"]
    profile, commands = profile_from_card(args.process)
    output = (args.output or REPO / ".local/user-samples" /
              f"{profile}_{args.events}_seed{args.seed}_{time.strftime('%Y%m%dT%H%M%S')}").resolve()
    if output.exists():
        raise ValueError(f"Output already exists; choose a new directory: {output}")
    output.mkdir(parents=True)
    # Relative command paths keep machine-specific output paths out of proc cards.
    process_dir = output / "process"
    process_relative = "process"
    if any(c in str(output) for c in "\n\r;\"'") or " " in str(output):
        raise ValueError("MG5 process directory must not contain whitespace or shell metacharacters")
    shutil.copyfile(args.process, output / "requested_process.mg5")
    generation_commands = [
        "set automatic_html_opening False", "set auto_update 0", "set nb_core 2",
        "set fortran_compiler x86_64-conda-linux-gnu-gfortran",
        "set cpp_compiler x86_64-conda-linux-gnu-g++", *commands,
        f"output {process_relative} -nojpeg", "quit",
    ]
    command_card = output / "generate.mg5"
    command_card.write_text("\n".join(generation_commands) + "\n")
    execution = {"process_generation": run([sys.executable, str(mg5 / "bin/mg5_aMC"), str(command_card)],
                                            output, output / "process_generation.log")}
    cards = process_dir / "Cards"
    if args.run_card:
        shutil.copyfile(args.run_card, cards / "run_card.dat")
    else:
        # Use the real release's complete card, then explicitly set our study defaults.
        sys.path.insert(0, str(mg5))
        from madgraph.various.banner import RunCardLO
        card = RunCardLO(str(cards / "run_card.dat"))
        for key, value in BASE_SETTINGS.items():
            card.set(key, value, user=True)
        card.write(str(cards / "run_card.dat"), template=str(cards / "run_card.dat"), write_hidden=False)
    if args.param_card:
        shutil.copyfile(args.param_card, cards / "param_card.dat")
    from validate_lhe import run_values, number
    cut_values = run_values((cards / "run_card.dat").read_text())
    required_cuts = ["pta", "etaa", "draa"]
    if profile == "bbgg":
        required_cuts += ["ptb", "etab", "drbb", "drab"]
        if number(cut_values["maxjetflavor"]) != 4:
            raise ValueError("bbgg profile needs maxjetflavor=4 for the explicit b-specific cut convention")
    if any(number(cut_values[key]) <= 0 for key in required_cuts):
        raise ValueError("profile requires finite positive pT/eta/DeltaR generation cuts")
    if number(cut_values["ptgmin"]) != 0:
        raise ValueError("new smooth-cone isolation needs a separately reviewed validation profile")
    # Command-line events/seed/energy always override supplied run card fields.
    launch = output / "launch.mg5"
    launch.write_text("\n".join([
        "launch " + process_relative + " -m --name=sample", "shower=OFF", "detector=OFF",
        "analysis=OFF", "madspin=OFF", "reweight=OFF", "done",
        f"set nevents {args.events}", f"set iseed {args.seed}",
        f"set ebeam1 {args.energy / 2:.12g}", f"set ebeam2 {args.energy / 2:.12g}",
        "done", "quit", "",
    ]))
    execution["event_generation"] = run([sys.executable, str(mg5 / "bin/mg5_aMC"), str(launch)],
                                        output, output / "event_generation.log")
    lhe_path = process_dir / "Events/sample/unweighted_events.lhe.gz"
    if not lhe_path.is_file():
        raise RuntimeError(f"No actual LHE output; inspect {output / 'event_generation.log'}")
    # Reading to EOF independently verifies the generator's original gzip CRC.
    with gzip.open(lhe_path, "rb") as stream:
        data = stream.read()
    result = validate_data(data, args.events, profile=profile, beam_energy=args.energy / 2)
    actual = result.pop("cards")
    result.pop("run_values")
    saved_cards = output / "cards"
    saved_cards.mkdir()
    card_hashes = {}
    for key, filename in (("process_card", "proc_card_mg5.dat"), ("run_card", "run_card.dat"),
                          ("param_card", "param_card.dat")):
        source = cards / filename
        if key != "run_card" and canonical_card(source.read_text()) != canonical_card(actual[key]):
            raise ValidationError("actual generator card differs from LHE banner: " + key)
        # MG5 resets Cards/run_card.dat iseed to 0 AFTER generation. The LHE
        # banner, not this mutable post-run file, is the actual run authority.
        if key == "run_card":
            from validate_lhe import run_values, integer, number
            values = run_values(actual[key])
            if (integer(values["iseed"]) != args.seed or integer(values["nevents"]) != args.events or
                    number(values["ebeam1"]) != args.energy / 2 or number(values["ebeam2"]) != args.energy / 2):
                raise ValidationError("actual banner does not match requested seed/count/energy")
            shutil.copyfile(source, saved_cards / "post_run_run_card.dat")
        (saved_cards / filename).write_text(actual[key])
        card_hashes[key + "_sha256"] = sha256((saved_cards / filename).read_bytes())
    shutil.copyfile(cards / "me5_configuration.txt", saved_cards / "me5_configuration.txt")
    banners = list((process_dir / "Events/sample").glob("*_banner.txt"))
    if len(banners) != 1:
        raise RuntimeError("expected one actual run banner")
    shutil.copyfile(banners[0], output / "generator_banner.txt")
    (output / "sample.lhe").write_bytes(data)
    compressed = gzip_deterministic(data)
    (output / "sample.lhe.gz").write_bytes(compressed)
    result.update(compressed_file_sha256=sha256(compressed), compressed_bytes=len(compressed),
                  original_compressed_sha256=sha256(lhe_path.read_bytes()))
    manifest = {"schema_version": 1, "status": "PASS", "profile": profile,
                "process": PROFILES[profile][0], "events_requested": args.events,
                "random_seed": args.seed, "sqrt_s_gev": args.energy, "mg5_source_commit": head,
                "source_identity": config, "execution": execution, "card_hashes": card_hashes,
                "validation": result, "publication": "LOCAL_ONLY",
                "actual_cards_authority": "Exact LHE banner text; post-run card separately retained (MG5 resets iseed=0)",
                "lhe": "sample.lhe", "lhe_gz": "sample.lhe.gz"}
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"PASS: {args.events} actual {profile} LO events; seed={args.seed}; sqrt(s)={args.energy:g} GeV")
    print(f"Cross section: {result['cross_section_pb']:.10g} +/- {result['cross_section_uncertainty_pb']:.5g} pb")
    print(f"Local sample: {output / 'sample.lhe.gz'}")
    print(f"SHA256: {result['compressed_file_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

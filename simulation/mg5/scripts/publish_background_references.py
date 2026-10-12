#!/usr/bin/env python3
"""Prepare selected actual ccgg/light-jjgg 1000-event references; no Git calls.

Both runs must validate before any new publication file is written. Original LHE
bytes remain exact; only gzip metadata is made deterministic. The historical
bbgg directory is neither opened for writing nor included in output plans.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
import re
import sys

from generate_sample import gzip_deterministic
from validate_lhe import canonical_card, event_bytes, integer, number, sha256, validate_file

REPO = Path(__file__).resolve().parents[3]
SOURCE_COMMIT = "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"
SOURCE_URL = "https://github.com/mg5amcnlo/mg5amcnlo.git"
PROFILES = {
    "ccgg": {"directory": "pp_ccgg_sm_lo_13tev", "seed": 20261021,
             "process": "p p > c c~ a a QCD=2 QED=2", "final_ids": [-4, 4, 22, 22]},
    "jjgg": {"directory": "pp_jjgg_light_sm_lo_13tev", "seed": 20261022,
             "process": "p p > a a jl jl QCD=2 QED=2", "final_ids": [-3, -2, -1, 1, 2, 3, 21, 22]},
}
PRIVATE = re.compile(r"(?i)(?:/home/(?!\[)[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def param_blocks(text):
    blocks, current = {}, None
    for line in text.splitlines():
        row = line.split("#", 1)[0].split()
        if not row:
            continue
        if row[0].upper() == "BLOCK":
            current = row[1].upper()
            blocks[current] = {}
        elif row[0].upper() == "DECAY":
            current = None
        elif current and len(row) == 2:
            blocks[current][integer(row[0])] = number(row[1])
    return blocks


def make_sanitizer(config, run, repo):
    replacements = {
        config["mg5_path"]: "[LOCAL_MG5_INSTALLATION]",
        config["toolchain_prefix"]: "[LOCAL_TOOLCHAIN]",
        config["conda_sh"]: "[LOCAL_CONDA_SH]",
        str(repo.resolve()): "[REPOSITORY]", str(run.resolve()): "[LOCAL_RUN_DIRECTORY]",
        str(Path.home()): "[LOCAL_USER_HOME]",
    }

    def sanitize(text):
        for old in sorted(replacements, key=len, reverse=True):
            text = text.replace(old, replacements[old])
        require(PRIVATE.search(text) is None, "unsanitized private path/credential in selected provenance")
        return text

    return sanitize


def json_data(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def prepare_run(profile, run, repo=REPO):
    """Return complete validated write plan without mutating the repository."""
    definition = PROFILES[profile]
    run = Path(run).resolve()
    repo = Path(repo).resolve()
    local = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    require(local["status"] == "PASS" and local["profile"] == profile, "local run is not a completed selected profile")
    require(local["events_requested"] == 1000 and local["random_seed"] == definition["seed"], "selected count/seed mismatch")
    require(local["sqrt_s_gev"] == 13000, "selected reference must use sqrt(s)=13000 GeV")
    require(local["process"] == "generate " + definition["process"], "selected process differs from reviewed profile")
    config = local["source_identity"]
    require(config["source_commit"] == local["mg5_source_commit"] == SOURCE_COMMIT and
            config["source_tag"] == "v3.5.16" and config["source_url"] == SOURCE_URL,
            "run source identity does not match the fixed official source")
    validation = validate_file(run / "sample.lhe.gz", 1000, profile=profile, beam_energy=6500)
    for key in ("actual_events", "compressed_file_sha256", "decompressed_file_sha256", "event_content_sha256",
                "negative_weight_count", "zero_weight_count"):
        require(validation[key] == local["validation"][key], "local validation differs from actual file: " + key)
    for key in ("cross_section_pb", "cross_section_uncertainty_pb"):
        require(math.isclose(validation[key], local["validation"][key], rel_tol=1e-8, abs_tol=1e-12), "local cross section differs")
    rv = validation["run_values"]
    require(integer(rv["iseed"]) == definition["seed"] and integer(rv["nevents"]) == 1000, "actual banner count/seed mismatch")
    settings = {"pta": 25, "etaa": 2.5, "ptj": 20, "etaj": 5, "draa": 0.4, "draj": 0.4,
                "drjj": 0.4, "maxjetflavor": 4, "scale": 125, "dsqrt_q2fact1": 125,
                "dsqrt_q2fact2": 125, "ptgmin": 0, "ickkw": 0}
    require(all(number(rv[key]) == value for key, value in settings.items()), "selected generation settings differ")
    require(rv["pdlabel"] == "cteq6l1" and validation["pdf_ids"] == [10042, 10042], "selected PDF differs")
    require(rv["fixed_ren_scale"].lower() in {"true", ".true."} and
            rv["fixed_fac_scale"].lower() in {"true", ".true."}, "selected scales are not fixed")
    require(rv["event_norm"] == "average" and rv["systematics_program"] == "none", "selected run convention differs")
    original = run / "process/Events/sample/unweighted_events.lhe.gz"
    original_gzip = original.read_bytes()
    data = gzip.decompress(original_gzip)
    require(sha256(data) == validation["decompressed_file_sha256"], "export differs from original generator bytes")
    require(data == (run / "sample.lhe").read_bytes(), "plain LHE differs from original generator bytes")
    require(event_bytes(data) == event_bytes((run / "sample.lhe").read_bytes()), "original event content differs")
    published_gzip = gzip_deterministic(data)
    require(gzip.decompress(published_gzip) == data, "gzip publication changed original bytes")
    require(len(published_gzip) <= 5 * 1024 * 1024, "selected reference exceeds 5 MiB archive cap")
    relative_dir = "reference_samples/mg5/" + definition["directory"]
    sample_path = relative_dir + "/reference_1000.lhe.gz"
    label = profile + "_reference_1000"
    card_dir = "simulation/mg5/cards/" + label
    evidence_dir = "simulation/mg5/evidence/" + label
    writes = {sample_path: published_gzip}
    sanitize = make_sanitizer(config, run, repo)
    cards = {}
    for key, name in (("process_card", "proc_card_mg5.dat"), ("run_card", "run_card.dat"), ("param_card", "param_card.dat")):
        source = run / "cards" / name
        raw = source.read_bytes()
        require(sha256(raw) == local["card_hashes"][key + "_sha256"], "local exact-card hash mismatch")
        require(canonical_card(raw.decode("utf-8")) == canonical_card(validation["cards"][key]), "archived card differs from banner")
        require(sanitize(raw.decode("utf-8")) == raw.decode("utf-8"), "exact generator card requires private-path review")
        relative = card_dir + "/" + name
        writes[relative] = raw
        cards[key + "_path"] = relative
        cards[key + "_sha256"] = sha256(raw)
    provenance = []
    for source, relative in (
        (run / "generator_banner.txt", evidence_dir + "/generator_banner.txt"),
        (run / "process_generation.log", evidence_dir + "/process_generation.txt"),
        (run / "event_generation.log", evidence_dir + "/event_generation.txt"),
        (run / "cards/me5_configuration.txt", card_dir + "/me5_configuration.txt"),
        (run / "generate.mg5", evidence_dir + "/generate.mg5"),
        (run / "launch.mg5", evidence_dir + "/launch.mg5"),
    ):
        raw = source.read_bytes()
        published = sanitize(raw.decode("utf-8")).encode("utf-8")
        writes[relative] = published
        provenance.append({"path": relative, "sha256": sha256(published), "original_sha256": sha256(raw),
                           "transformation": "path placeholders only" if raw != published else "NONE"})
    blocks = param_blocks(validation["cards"]["param_card"])
    inputs, masses = blocks["SMINPUTS"], blocks["MASS"]
    require(len(validation["event_alpha_s_values"]) == len(validation["event_alpha_em_values"]) == 1,
            "selected fixed-coupling references must have one event coupling value")
    cuts = {"photon_pt_min_gev": number(rv["pta"]), "photon_abs_eta_max": number(rv["etaa"]),
            "jet_pt_min_gev": number(rv["ptj"]), "jet_abs_eta_max": number(rv["etaj"]),
            "delta_r_aa_min": number(rv["draa"]), "delta_r_aj_min": number(rv["draj"]),
            "delta_r_jj_min": number(rv["drjj"]), "maxjetflavor_for_cut_classification": integer(rv["maxjetflavor"]),
            "photon_isolation": "fixed parton-photon separation only; ptgmin=0 disables smooth-cone isolation"}
    sample = {
        "sample_id": "reference_1000", "physics_profile": profile, "file": sample_path,
        "physics_process": definition["process"],
        "physics_model": "sm-no_b_mass (bundled SM UFO, diagonal CKM, massless b and zero b Yukawa)",
        "perturbative_order": "LO", "sqrt_s_gev": number(rv["ebeam1"]) + number(rv["ebeam2"]),
        "beam_energies_gev": [number(rv["ebeam1"]), number(rv["ebeam2"])],
        "mg5_version": validation["mg5_version"],
        "mg5_source_identity": {"url": config["source_url"], "tag": config["source_tag"], "commit": config["source_commit"]},
        "pdf_name_and_id": {"name": "CTEQ6L1", "lhapdf_id": validation["pdf_ids"][0], "interface": "MG5 built-in Ctq6Pdf.f",
                            "data_source": "Template/LO/lib/Pdfdata/cteq6l1.tbl"},
        "flavour_scheme": "5F massless hard process; u,d,s,c,b and antiquarks in proton; no top PDF",
        "b_mass_treatment": f"MB={masses[5]:g} GeV; zero b Yukawa in sm-no_b_mass restriction",
        "charm_mass_treatment": (f"MC={masses[4]:g} GeV; charm treated as an ordinary jet for generation cuts" if profile == "ccgg"
                                 else f"MC={masses[4]:g} GeV; initial charm PDF is active; final jl excludes charm"),
        "final_state_definition": {"allowed_pdg_ids": definition["final_ids"],
                                   "light_jet_definition": "jl = g u d s u~ d~ s~; excludes charm and bottom" if profile == "jjgg" else "exact c and cbar plus two photons"},
        "alpha_s_settings": {"pdf_alpha_s_mz": 0.130, "running": "CTEQ6L1 LO one-loop",
                             "param_card_as": inputs[3], "event_aqcd": validation["event_alpha_s_values"][0],
                             "event_aqcd_values": validation["event_alpha_s_values"],
                             "note": "actual banner SMINPUTS(3) recorded; hadronic event running uses the built-in PDF"},
        "alpha_em_settings": {"aEWM1": inputs[1], "alpha_em": 1 / inputs[1], "GF_gev_minus2": inputs[2],
                              "MZ_gev": masses[23], "event_aqed_values": validation["event_alpha_em_values"],
                              "input_scheme": "aEWM1, GF, MZ; MW derived"},
        "renormalization_scale": {"type": "fixed", "gev": number(rv["scale"])},
        "factorization_scale": {"type": "fixed", "beam1_gev": number(rv["dsqrt_q2fact1"]), "beam2_gev": number(rv["dsqrt_q2fact2"])},
        "generation_cuts": cuts, "random_seed": integer(rv["iseed"]), "requested_events": 1000,
        "actual_events": validation["actual_events"], "generator_cross_section_pb": validation["cross_section_pb"],
        "cross_section_uncertainty_pb": validation["cross_section_uncertainty_pb"],
        "generator_weight_convention": {"idwtup": validation["idwtup"], "event_norm": rv["event_norm"],
                                        "description": "positive constant XWGTUP in pb equals integrated cross section; histogram normalization is XWGTUP/N"},
        "negative_weight_count": validation["negative_weight_count"], "zero_weight_count": validation["zero_weight_count"],
        "event_content_sha256": validation["event_content_sha256"], "compressed_file_sha256": sha256(published_gzip),
        "decompressed_file_sha256": sha256(data), "original_compressed_file_sha256": sha256(original_gzip),
        "original_decompressed_file_sha256": sha256(data),
        "lhe_publication_transformation": "NONE; decompressed bytes unchanged; deterministic gzip mtime=0, no filename",
        "compressed_bytes": len(published_gzip), "validation_status": "PASS", "provenance_files": provenance,
        "execution": local["execution"], **cards,
    }
    writes[relative_dir + "/sample_manifest.json"] = json_data({"schema_version": 1, "samples": [sample]})
    require(all(not (repo / path).exists() for path in writes), "preserve existing publication files; no overwrite is allowed")
    return sample, writes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ccgg-run", required=True, type=Path)
    parser.add_argument("--jjgg-run", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true", help="validate both selected runs without writing publication files")
    args = parser.parse_args()
    try:
        samples, writes = [], {}
        for profile, run in (("ccgg", args.ccgg_run), ("jjgg", args.jjgg_run)):
            sample, plan = prepare_run(profile, run)
            samples.append(sample)
            require(not writes.keys() & plan.keys(), "publication plans overlap")
            writes.update(plan)
        require(sum(s["compressed_bytes"] for s in samples) <= 10 * 1024 * 1024, "selected background archives exceed total cap")
        if not args.dry_run:
            for relative, data in writes.items():
                path = REPO / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(data)
        print(json.dumps({"status": "PREFLIGHT_PASS_NO_WRITES" if args.dry_run else "PREPARED_LOCAL_ONLY",
                          "samples": [{key: s[key] for key in ("physics_profile", "actual_events", "compressed_file_sha256",
                                                                 "generator_cross_section_pb", "cross_section_uncertainty_pb")} for s in samples],
                          "publication_files": len(writes)}, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

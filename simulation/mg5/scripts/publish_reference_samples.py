#!/usr/bin/env python3
"""Prepare the two selected validated references locally. Does not call Git.

LHE bytes and event blocks are preserved; only gzip container metadata changes.
Execution/settings evidence is separately path-redacted with original hashes.
"""
import argparse
import gzip
import json
from pathlib import Path
import shutil

from generate_sample import gzip_deterministic
from validate_lhe import SAMPLE_DIR, sha256, validate_file, event_bytes

REPO = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--smoke-run", type=Path, required=True)
parser.add_argument("--reference-run", type=Path, required=True)
args = parser.parse_args()
destination = REPO / SAMPLE_DIR
destination.mkdir(parents=True, exist_ok=True)
samples = []
for sid, run, count, seed in (("smoke_100", args.smoke_run, 100, 20261012),
                              ("reference_1000", args.reference_run, 1000, 20261013)):
    run = run.resolve()
    local_manifest = json.loads((run / "run_manifest.json").read_text())
    if local_manifest["status"] != "PASS" or local_manifest["random_seed"] != seed:
        raise SystemExit("local run is not the verified selected reference")
    validation = validate_file(run / "sample.lhe.gz", count, beam_energy=6500)
    original = run / "process/Events/sample/unweighted_events.lhe.gz"
    original_compressed = original.read_bytes()
    data = gzip.decompress(original_compressed)
    if sha256(data) != validation["decompressed_file_sha256"]:
        raise SystemExit("export differs from original generator LHE")
    target = destination / (sid + ".lhe.gz")
    if target.exists():
        raise SystemExit("preserve existing reference before preparing a new version")
    target.write_bytes(gzip_deterministic(data))
    if gzip.decompress(target.read_bytes()) != data or event_bytes(data) != event_bytes((run / "sample.lhe").read_bytes()):
        raise SystemExit("generator content changed")
    card_dir = REPO / "simulation/mg5/cards" / sid
    evidence_dir = REPO / "simulation/mg5/evidence" / sid
    card_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    cfg = local_manifest["source_identity"]
    replacements = {
        cfg["mg5_path"]: "[LOCAL_MG5_INSTALLATION]",
        cfg["toolchain_prefix"]: "[LOCAL_TOOLCHAIN]",
        cfg["conda_sh"]: "[LOCAL_CONDA_SH]",
        str(REPO): "[REPOSITORY]",
        str(run): "[LOCAL_RUN_DIRECTORY]",
        str(Path.home()): "[LOCAL_USER_HOME]",
    }
    def sanitize(text):
        for old in sorted(replacements, key=len, reverse=True):
            text = text.replace(old, replacements[old])
        return text
    cards = {}
    provenance = []
    for key, name in (("process_card", "proc_card_mg5.dat"), ("run_card", "run_card.dat"),
                      ("param_card", "param_card.dat")):
        source = run / "cards" / name
        path = card_dir / name
        # These exact production cards must not require any redaction.
        if sanitize(source.read_text()) != source.read_text():
            raise SystemExit("exact physics card needs explicit metadata sanitation review: " + name)
        shutil.copyfile(source, path)
        cards[key + "_path"] = path.relative_to(REPO).as_posix()
        cards[key + "_sha256"] = sha256(path.read_bytes())
    for source, target_path in (
        (run / "generator_banner.txt", evidence_dir / "generator_banner.txt"),
        (run / "process_generation.log", evidence_dir / "process_generation.txt"),
        (run / "event_generation.log", evidence_dir / "event_generation.txt"),
        (run / "cards/me5_configuration.txt", card_dir / "me5_configuration.txt"),
        (run / "generate.mg5", evidence_dir / "generate.mg5"),
        (run / "launch.mg5", evidence_dir / "launch.mg5"),
    ):
        raw = source.read_bytes()
        published = sanitize(raw.decode("utf-8")).encode("utf-8")
        target_path.write_bytes(published)
        provenance.append({"path": target_path.relative_to(REPO).as_posix(), "sha256": sha256(published),
                           "original_sha256": sha256(raw),
                           "transformation": "path placeholders only" if raw != published else "NONE"})
    samples.append({
        "sample_id": sid, "file": target.relative_to(REPO).as_posix(),
        "physics_process": "p p > b b~ a a QCD=2 QED=2",
        "physics_model": "sm-no_b_mass (bundled SM UFO, diagonal CKM, massless b and zero b Yukawa)",
        "perturbative_order": "LO", "sqrt_s_gev": 13000, "beam_energies_gev": [6500, 6500],
        "mg5_version": "3.5.16",
        "mg5_source_identity": {"url": cfg["source_url"], "tag": "v3.5.16", "commit": cfg["source_commit"]},
        "pdf_name_and_id": {"name": "CTEQ6L1", "lhapdf_id": 10042, "interface": "MG5 built-in Ctq6Pdf.f",
                            "data_source": "Template/LO/lib/Pdfdata/cteq6l1.tbl"},
        "flavour_scheme": "5F massless hard process; u,d,s,c,b and antiquarks in proton; no top PDF",
        "b_mass_treatment": "MB=0 GeV and ymb=0 in sm-no_b_mass",
        "alpha_s_settings": {"pdf_alpha_s_mz": 0.130, "running": "CTEQ6L1 LO one-loop",
                             "event_aqcd": 0.1238062, "param_card_as": 0.118,
                             "note": "Hadronic running alpha_s follows the built-in PDF, not the param-card default"},
        "alpha_em_settings": {"aEWM1": 132.507, "alpha_em": 1 / 132.507,
                              "input_scheme": "aEWM1, GF=1.16639e-5 GeV^-2, MZ=91.188 GeV; MW derived"},
        "renormalization_scale": {"type": "fixed", "gev": 125},
        "factorization_scale": {"type": "fixed", "beam1_gev": 125, "beam2_gev": 125},
        "generation_cuts": {"photon_pt_min_gev": 25, "photon_abs_eta_max": 2.5,
                            "b_pt_min_gev": 20, "b_abs_eta_max": 5,
                            "delta_r_aa_min": 0.4, "delta_r_ab_min": 0.4, "delta_r_bb_min": 0.4,
                            "maxjetflavor_for_cut_classification": 4,
                            "photon_isolation": "fixed parton-photon separation only; ptgmin=0 disables smooth-cone isolation"},
        "random_seed": seed, "requested_events": count, "actual_events": validation["actual_events"],
        "generator_cross_section_pb": validation["cross_section_pb"],
        "cross_section_uncertainty_pb": validation["cross_section_uncertainty_pb"],
        "generator_weight_convention": {"idwtup": validation["idwtup"], "event_norm": "average",
                                        "description": "positive constant XWGTUP in pb equals integrated cross section; histogram normalization is XWGTUP/N"},
        "negative_weight_count": validation["negative_weight_count"], "zero_weight_count": validation["zero_weight_count"],
        "event_content_sha256": validation["event_content_sha256"],
        "compressed_file_sha256": sha256(target.read_bytes()),
        "decompressed_file_sha256": validation["decompressed_file_sha256"],
        "original_compressed_file_sha256": sha256(original_compressed),
        "original_decompressed_file_sha256": sha256(data),
        "lhe_publication_transformation": "NONE; decompressed bytes unchanged; deterministic gzip mtime=0, no filename",
        "compressed_bytes": target.stat().st_size, "validation_status": "PASS",
        "provenance_files": provenance, "execution": local_manifest["execution"], **cards,
    })
(destination / "sample_manifest.json").write_text(json.dumps({"schema_version": 1, "samples": samples}, indent=2, sort_keys=True) + "\n")
print("Prepared actual references locally, with unchanged decompressed generator bytes")

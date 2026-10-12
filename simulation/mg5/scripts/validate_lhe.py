#!/usr/bin/env python3
"""Independent, standard-library validation of the Phase 6A MG5 samples.

No generator imports and no event repair/filtering. Every failure rejects the
whole file. Tolerances cover decimal LHE serialization, not physics accuracy.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

MAX_COMPRESSED = 5 * 1024 * 1024
MAX_TOTAL = 10 * 1024 * 1024
MAX_DECOMPRESSED = 40 * 1024 * 1024
CLOSURE_ATOL_GEV = 1e-6
CLOSURE_RTOL = 5e-9
SHELL_ATOL_GEV2 = 1e-6
SHELL_RTOL = 5e-9
SAMPLE_DIR = "reference_samples/mg5/pp_bbgg_sm_lo_13tev"
EXPECTED_SAMPLES = {"smoke_100": (100, 20261012), "reference_1000": (1000, 20261013)}
ALLOWED_INITIAL = {21, *range(1, 6), *range(-5, 0)}
EXPECTED_FINAL = Counter([5, -5, 22, 22])
CARD_TAGS = {"process_card": "MG5ProcCard", "run_card": "MGRunCard", "param_card": "slha"}
REQUIRED_FIELDS = {
    "sample_id", "physics_process", "physics_model", "perturbative_order",
    "sqrt_s_gev", "beam_energies_gev", "mg5_version", "mg5_source_identity",
    "pdf_name_and_id", "flavour_scheme", "b_mass_treatment", "alpha_s_settings",
    "alpha_em_settings", "renormalization_scale", "factorization_scale",
    "generation_cuts", "random_seed", "requested_events", "actual_events",
    "generator_cross_section_pb", "cross_section_uncertainty_pb",
    "generator_weight_convention", "negative_weight_count", "zero_weight_count",
    "event_content_sha256", "compressed_file_sha256", "decompressed_file_sha256",
    "process_card_sha256", "run_card_sha256", "param_card_sha256", "validation_status",
}


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def number(value: str) -> float:
    try:
        result = float(value.replace("D", "e").replace("d", "e"))
    except ValueError as exc:
        raise ValidationError(f"invalid real number: {value}") from exc
    require(math.isfinite(result), f"non-finite real number: {value}")
    return result


def integer(value: str) -> int:
    require(re.fullmatch(r"[+-]?\d+", value) is not None, f"invalid integer: {value}")
    return int(value)


def records(text: str):
    return [line.split("#", 1)[0].split() for line in text.splitlines()
            if line.split("#", 1)[0].strip()]


def run_values(text: str):
    values = {}
    for line in text.splitlines():
        line = line.split("!", 1)[0].split("#", 1)[0].strip()
        if "=" in line:
            value, key = line.split("=", 1)
            key = key.strip().lower()
            require(key not in values, f"duplicate run-card key: {key}")
            values[key] = value.strip().strip("'\"")
    return values


def canonical_card(text: str) -> str:
    # MG5 wraps cards with a newline in the XML banner.
    return text.replace("\r\n", "\n").strip()


def event_bytes(data: bytes) -> bytes:
    return b"".join(re.findall(rb"<event(?:\s[^>]*)?>.*?</event>", data, re.S))


def read_gzip(path: Path, *, require_deterministic=True):
    compressed = path.read_bytes()
    require(len(compressed) <= MAX_COMPRESSED, f"sample exceeds 5 MiB: {path.name}")
    require(compressed[:3] == b"\x1f\x8b\x08", "invalid gzip signature")
    require(len(compressed) >= 18, "truncated gzip")
    if require_deterministic:
        require(compressed[4:8] == b"\0\0\0\0" and not (compressed[3] & 8),
                "gzip must have mtime=0 and no original filename")
    try:
        with gzip.open(path, "rb") as stream:
            data = stream.read(MAX_DECOMPRESSED + 1)
    except (OSError, EOFError) as exc:
        raise ValidationError(f"gzip integrity failure: {exc}") from exc
    require(len(data) <= MAX_DECOMPRESSED, "decompressed size limit exceeded")
    return compressed, data


def validate_data(data: bytes, expected_events: int | None = None, *, profile="bbgg", beam_energy=None):
    require(profile in {"bbgg", "diphoton"}, "unknown physical validation profile")
    expected_final = EXPECTED_FINAL if profile == "bbgg" else Counter([22, 22])
    expected_nup = sum(expected_final.values()) + 2
    require(b"<!DOCTYPE" not in data.upper() and b"<!ENTITY" not in data.upper(),
            "DTD/entities are not supported")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValidationError(f"invalid or truncated LHE XML: {exc}") from exc
    require(root.tag == "LesHouchesEvents", "wrong LHE root")
    require(root.get("version") in {"1.0", "3.0"}, "unsupported LHE version")
    header = root.find("header")
    init = root.find("init")
    require(header is not None and init is not None, "header/init missing")
    require(len(root.findall("header")) == len(root.findall("init")) == 1, "duplicate header/init")
    version = header.findtext("MGVersion", "").strip()
    require(version == "3.5.16", "unexpected MG5 version")
    generator = init.find("generator")
    require(generator is not None and generator.get("name") == "MadGraph5_aMC@NLO" and
            generator.get("version") == version, "init generator identity mismatch")
    cards = {key: header.findtext(tag, "") for key, tag in CARD_TAGS.items()}
    require(all(text.strip() for text in cards.values()), "generator cards missing from header")
    require("MadGraph" in data[:data.index(b"<event>")].decode("utf-8"), "generator identity missing")
    rv = run_values(cards["run_card"])
    init_rows = records(init.text or "")
    require(init_rows and len(init_rows[0]) == 10, "invalid init beam record")
    beam = init_rows[0]
    require([integer(x) for x in beam[:2]] == [2212, 2212], "beams are not protons")
    if beam_energy is None:
        beam_energy = number(rv["ebeam1"])
    require([number(x) for x in beam[2:4]] == [beam_energy, beam_energy], "wrong beam energies")
    require(number(rv["ebeam1"]) == number(rv["ebeam2"]) == beam_energy, "card/init energy mismatch")
    pdf_groups = [integer(x) for x in beam[4:6]]
    pdf_ids = [integer(x) for x in beam[6:8]]
    idwtup, nprup = [integer(x) for x in beam[8:10]]
    require(idwtup == -4 and nprup > 0, "expected MG5 IDWTUP=-4 with event_norm=average")
    require(len(init_rows) == nprup + 1, "init process count mismatch")
    processes = {}
    for row in init_rows[1:]:
        require(len(row) == 4, "invalid init subprocess record")
        xsec, error, xmax = [number(x) for x in row[:3]]
        pid = integer(row[3])
        require(xsec > 0 and error >= 0 and xmax > 0, "invalid cross-section metadata")
        require(pid not in processes, "duplicate init process ID")
        processes[pid] = (xsec, error, xmax)
    events = root.findall("event")
    require(events, "LHE contains no events")
    if expected_events is not None:
        require(len(events) == expected_events, "actual LHE event count mismatch")
    require(len(events) == integer(rv["nevents"]), "event count differs from actual run card")
    max_closure = 0.0
    max_shell = 0.0
    signs = Counter()
    weight_values = set()
    event_scales, aqed_values, aqcd_values = set(), set(), set()
    initial_counts = Counter()
    minima = {"photon_pt": math.inf, "b_pt": math.inf, "draa": math.inf,
              "drab": math.inf, "drbb": math.inf}
    maxima = {"photon_abs_eta": 0.0, "b_abs_eta": 0.0}
    for event_index, event in enumerate(events, 1):
        rows = records(event.text or "")
        require(rows and len(rows[0]) == 6, f"event {event_index}: invalid event header")
        nup, pid = [integer(x) for x in rows[0][:2]]
        weight, scale, aqed, aqcd = [number(x) for x in rows[0][2:]]
        require(nup == expected_nup and len(rows) == nup + 1, f"event {event_index}: particle record count")
        require(pid in processes and scale > 0 and aqed > 0 and aqcd > 0, "invalid event metadata")
        signs["negative" if weight < 0 else "zero" if weight == 0 else "positive"] += 1
        weight_values.add(weight)
        event_scales.add(scale)
        aqed_values.add(aqed)
        aqcd_values.add(aqcd)
        incoming, outgoing = [], []
        for particle_index, row in enumerate(rows[1:], 1):
            require(len(row) == 13, f"event {event_index}: malformed particle record")
            pdg, status, mother1, mother2, color1, color2 = [integer(x) for x in row[:6]]
            px, py, pz, energy, mass, lifetime, spin = [number(x) for x in row[6:]]
            require(status in {-1, 1}, "unexpected particle status for direct LO bbgg")
            require(energy > 0 and mass >= 0 and lifetime >= 0, "invalid particle energy/mass/lifetime")
            require(0 <= mother1 <= nup and 0 <= mother2 <= nup and
                    particle_index not in {mother1, mother2}, "invalid mother indices")
            require(color1 >= 0 and color2 >= 0, "invalid color tags")
            require((mother1, mother2) == ((0, 0) if status == -1 else (1, 2)),
                    "unexpected direct-process mother assignment")
            if pdg == 22:
                require(color1 == color2 == 0, "photon carries color")
            require(mass == 0.0, "expected massless five-flavour hard particles")
            p2 = px * px + py * py + pz * pz
            shell = abs(energy * energy - p2 - mass * mass)
            require(shell <= SHELL_ATOL_GEV2 + SHELL_RTOL * max(energy * energy, p2, mass * mass, 1.0),
                    f"event {event_index}: mass-shell failure")
            max_shell = max(max_shell, shell)
            particle = (pdg, px, py, pz, energy)
            (incoming if status == -1 else outgoing).append(particle)
        require(len(incoming) == 2 and len(outgoing) == expected_nup - 2, "wrong incoming/outgoing multiplicity")
        require(all(p[0] in ALLOWED_INITIAL for p in incoming), "unexpected incoming PDG ID")
        require(Counter(p[0] for p in outgoing) == expected_final, "final state differs from declared process")
        initial_counts[",".join(str(p[0]) for p in incoming)] += 1
        require(all(p[1] == p[2] == 0 for p in incoming) and incoming[0][3] > 0 > incoming[1][3],
                "invalid collinear beam kinematics")
        require(all(p[4] <= beam_energy + CLOSURE_ATOL_GEV for p in incoming), "parton exceeds beam energy")
        total_energy = sum(p[4] for p in incoming)
        for component in range(1, 5):
            residual = abs(math.fsum(p[component] for p in incoming) -
                           math.fsum(p[component] for p in outgoing))
            require(residual <= CLOSURE_ATOL_GEV + CLOSURE_RTOL * total_energy,
                    f"event {event_index}: four-momentum closure failure")
            max_closure = max(max_closure, residual)
        charge = {21: 0, 1: -1, 2: 2, 3: -1, 4: 2, 5: -1}
        require(sum(charge[abs(p[0])] * (1 if p[0] > 0 else -1) for p in incoming) == 0,
                "incoming charge does not match neutral final state")
        objects = []
        for pdg, px, py, pz, energy in outgoing:
            pt = math.hypot(px, py)
            eta = math.asinh(pz / pt) if pt > 0 else math.inf
            photon = pdg == 22
            key = "photon" if photon else "b"
            cut_pt = number(rv["pta" if photon else "ptb"])
            cut_eta = number(rv["etaa" if photon else "etab"])
            require(pt >= cut_pt - 1e-6 and abs(eta) <= cut_eta + 1e-8, "generation pT/eta cut failure")
            minima[key + "_pt"] = min(minima[key + "_pt"], pt)
            maxima[key + "_abs_eta"] = max(maxima[key + "_abs_eta"], abs(eta))
            objects.append((photon, eta, math.atan2(py, px)))
        for index, (photon1, eta1, phi1) in enumerate(objects):
            for photon2, eta2, phi2 in objects[index + 1:]:
                key = "draa" if photon1 and photon2 else "drbb" if not photon1 and not photon2 else "drab"
                delta_phi = math.remainder(phi1 - phi2, 2 * math.pi)
                delta_r = math.hypot(eta1 - eta2, delta_phi)
                require(delta_r >= number(rv[key]) - 1e-8, "generation DeltaR cut failure")
                minima[key] = min(minima[key], delta_r)
        for optional in event.findall(".//wgt"):
            number(optional.text or "")
    require(signs["negative"] == signs["zero"] == 0, "non-positive nominal LO event weight")
    require(len(weight_values) == 1, "unweighted sample has unequal nominal event weights")
    total_xsec = math.fsum(p[0] for p in processes.values())
    require(math.isclose(next(iter(weight_values)), total_xsec, rel_tol=1e-7, abs_tol=1e-12),
            "MG5 nominal weight differs from init cross section")
    extrema = {key: value for key, value in {**minima, **maxima}.items() if math.isfinite(value)}
    return {
        "validation_status": "PASS", "lhe_version": root.get("version"),
        "mg5_version": version, "actual_events": len(events), "idwtup": idwtup,
        "pdf_groups": pdf_groups, "pdf_ids": pdf_ids,
        "cross_section_pb": total_xsec,
        "cross_section_uncertainty_pb": math.sqrt(sum(p[1] ** 2 for p in processes.values())),
        "negative_weight_count": signs["negative"], "zero_weight_count": signs["zero"],
        "positive_weight_count": signs["positive"], "nominal_event_weight": next(iter(weight_values)),
        "event_scale_values_gev": sorted(event_scales), "event_alpha_em_values": sorted(aqed_values),
        "event_alpha_s_values": sorted(aqcd_values),
        "max_four_momentum_residual_gev": max_closure,
        "max_mass_shell_residual_gev2": max_shell,
        "cut_extrema": extrema, "incoming_pdg_pair_counts": dict(initial_counts),
        "event_content_sha256": sha256(event_bytes(data)),
        "decompressed_file_sha256": sha256(data), "run_values": rv,
        "cards": cards,
        "tolerances": {"closure_atol_gev": CLOSURE_ATOL_GEV, "closure_rtol": CLOSURE_RTOL,
                       "shell_atol_gev2": SHELL_ATOL_GEV2, "shell_rtol": SHELL_RTOL},
    }


def validate_file(path: Path, expected_events=None, *, profile="bbgg", beam_energy=None, require_deterministic=True):
    compressed, data = read_gzip(path, require_deterministic=require_deterministic)
    result = validate_data(data, expected_events, profile=profile, beam_energy=beam_energy)
    result.update(compressed_file_sha256=sha256(compressed), compressed_bytes=len(compressed),
                  decompressed_bytes=len(data))
    return result


def safe_file(repo: Path, relative: str):
    path = (repo / relative).resolve()
    require(path.is_relative_to(repo.resolve()), "manifest path escapes repository")
    require(path.is_file() and not path.is_symlink(), f"required file missing: {relative}")
    return path


def validate_repository(repo: Path):
    sample_path = repo / SAMPLE_DIR
    manifest = json.loads((sample_path / "sample_manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("schema_version") == 1, "unsupported manifest schema")
    samples = manifest["samples"]
    require(len(samples) == 2 and {s["sample_id"] for s in samples} == set(EXPECTED_SAMPLES),
            "both exact reference samples required")
    require(sum(safe_file(repo, s["file"]).stat().st_size for s in samples) <= MAX_TOTAL, "total size cap")
    expected_files = {"smoke_100.lhe.gz", "reference_1000.lhe.gz", "sample_manifest.json", "README.md"}
    require({p.name for p in sample_path.iterdir()} == expected_files, "unexpected reference-directory output")
    reports = []
    for sample in samples:
        require(REQUIRED_FIELDS <= sample.keys(), "missing mandatory provenance fields")
        sid = sample["sample_id"]
        count, seed = EXPECTED_SAMPLES[sid]
        require(sample["file"] == f"{SAMPLE_DIR}/{sid}.lhe.gz", "unexpected sample path")
        result = validate_file(safe_file(repo, sample["file"]), count, beam_energy=6500)
        require(sample["requested_events"] == sample["actual_events"] == count, "manifest count")
        require(sample["random_seed"] == seed == integer(result["run_values"]["iseed"]), "actual seed mismatch")
        require(sample["validation_status"] == "PASS", "sample not independently validated")
        for key in ("compressed_file_sha256", "decompressed_file_sha256", "event_content_sha256",
                    "negative_weight_count", "zero_weight_count", "compressed_bytes"):
            require(sample[key] == result[key], f"manifest mismatch: {key}")
        for key, result_key in (("generator_cross_section_pb", "cross_section_pb"),
                                ("cross_section_uncertainty_pb", "cross_section_uncertainty_pb")):
            require(math.isclose(sample[key], result[result_key], rel_tol=1e-8, abs_tol=1e-12), key + " mismatch")
        for key in CARD_TAGS:
            path = safe_file(repo, sample[key + "_path"])
            require(sha256(path.read_bytes()) == sample[key + "_sha256"], "card hash mismatch: " + key)
            require(canonical_card(path.read_text(encoding="utf-8")) == canonical_card(result["cards"][key]),
                    "card differs from generator banner: " + key)
        for item in sample["provenance_files"]:
            require(sha256(safe_file(repo, item["path"]).read_bytes()) == item["sha256"], "provenance file hash")
        require(sample["mg5_version"] == result["mg5_version"], "generator version mismatch")
        require(sample["mg5_source_identity"]["commit"] == "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7",
                "source identity differs from pinned official tag")
        require(sample["perturbative_order"] == "LO" and sample["sqrt_s_gev"] == 13000 and
                sample["beam_energies_gev"] == [6500, 6500], "physics manifest mismatch")
        require(sample["physics_process"] == "p p > b b~ a a QCD=2 QED=2", "declared process mismatch")
        require(sample["pdf_name_and_id"]["name"] == "CTEQ6L1" and
                sample["pdf_name_and_id"]["lhapdf_id"] == 10042, "manifest PDF mismatch")
        require(sample["renormalization_scale"] == {"type": "fixed", "gev": 125} and
                sample["factorization_scale"] == {"type": "fixed", "beam1_gev": 125, "beam2_gev": 125},
                "manifest scale mismatch")
        require(sample["generator_weight_convention"]["idwtup"] == -4 and
                sample["generator_weight_convention"]["event_norm"] == "average", "manifest weight convention")
        require(sample["original_decompressed_file_sha256"] == sample["decompressed_file_sha256"],
                "published LHE differs from original decompressed identity")
        expected_cuts = {"photon_pt_min_gev": 25, "photon_abs_eta_max": 2.5, "b_pt_min_gev": 20,
                         "b_abs_eta_max": 5, "delta_r_aa_min": 0.4, "delta_r_ab_min": 0.4,
                         "delta_r_bb_min": 0.4, "maxjetflavor_for_cut_classification": 4}
        require(all(sample["generation_cuts"][key] == value for key, value in expected_cuts.items()),
                "manifest generation cuts mismatch")
        require(result["event_scale_values_gev"] == [125] and result["event_alpha_s_values"] == [0.1238062] and
                result["event_alpha_em_values"] == [0.007546771], "event scale/coupling evidence mismatch")
        rv = result["run_values"]
        expected_settings = {"pta": 25, "ptb": 20, "etaa": 2.5, "etab": 5,
                             "draa": 0.4, "drab": 0.4, "drbb": 0.4,
                             "ebeam1": 6500, "ebeam2": 6500, "ickkw": 0, "ptgmin": 0,
                             "maxjetflavor": 4, "scale": 125, "dsqrt_q2fact1": 125,
                             "dsqrt_q2fact2": 125}
        for key, value in expected_settings.items():
            require(number(rv[key]) == value, "unexpected actual setting: " + key)
        require(rv["pdlabel"] == "cteq6l1", "unexpected PDF")
        require(result["pdf_ids"] == [10042, 10042], "init PDF identity mismatch")
        require(rv["fixed_ren_scale"].lower() in {"true", ".true."} and
                rv["fixed_fac_scale"].lower() in {"true", ".true."}, "scales are not fixed")
        require(rv["systematics_program"] == "none" and rv["event_norm"] == "average", "run convention mismatch")
        process = result["cards"]["process_card"]
        require("import model sm-no_b_mass" in process and
                "generate p p > b b~ a a QCD=2 QED=2" in process and
                "define p = g u c d s b u~ c~ d~ s~ b~" in process,
                "process/model/orders/initial-state definition mismatch")
        result.pop("cards")
        result.pop("run_values")
        reports.append({"sample_id": sid, **result})
    return {"status": "PASS", "samples": reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--events", type=int)
    parser.add_argument("--profile", choices=["bbgg", "diphoton"], default="bbgg")
    parser.add_argument("--generator-original", action="store_true", help="permit original gzip timestamp/filename; all physical checks remain")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        require(bool(args.repository) != bool(args.file), "choose --repository or --file")
        result = validate_repository(args.repository) if args.repository else validate_file(args.file, args.events, profile=args.profile, require_deterministic=not args.generator_original)
        result.pop("cards", None)
        result.pop("run_values", None)
        output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.report:
            args.report.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0
    except (ValidationError, OSError, KeyError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

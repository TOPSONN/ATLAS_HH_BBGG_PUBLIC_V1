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
LIGHT_JETS = {21, 1, -1, 2, -2, 3, -3}
PROFILE_PROCESSES = {
    "bbgg": "p p > b b~ a a QCD=2 QED=2",
    "ccgg": "p p > c c~ a a QCD=2 QED=2",
    "jjgg": "p p > a a jl jl QCD=2 QED=2",
    "diphoton": "p p > a a QCD=0 QED=2",
}
BACKGROUND_DIRS = {"ccgg": "reference_samples/mg5/pp_ccgg_sm_lo_13tev",
                   "jjgg": "reference_samples/mg5/pp_jjgg_light_sm_lo_13tev"}
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


def validate_profile_cards(cards, rv, profile):
    commands = [line.split("#", 1)[0].strip() for line in cards["process_card"].splitlines()
                if line.split("#", 1)[0].strip()]
    require([line for line in commands if line.startswith("import model ")] == ["import model sm-no_b_mass"],
            "process/model profile mismatch")
    require([line for line in commands if line.startswith(("generate ", "add process "))] ==
            ["generate " + PROFILE_PROCESSES[profile]], "declared process/orders profile mismatch")
    proton = [line for line in commands if line.startswith("define p =")]
    require(proton and proton[-1] == "define p = g u c d s b u~ c~ d~ s~ b~",
            "five-flavour proton definition mismatch")
    if profile == "jjgg":
        light = [line for line in commands if line.startswith("define jl =")]
        require(light and light[-1] == "define jl = g u u~ d d~ s s~", "light-jet definition mismatch")
    require(rv.get("pdlabel") == "cteq6l1" and number(rv.get("lhaid", "0")) == 10042,
            "profile PDF mismatch")
    require(rv.get("event_norm") == "average" and number(rv.get("ickkw", "-1")) == 0,
            "profile weight/matching convention mismatch")
    require(number(rv.get("ptgmin", "-1")) == 0, "profile smooth-cone isolation mismatch")
    require(1 <= integer(rv.get("iseed", "0")) <= 30081 ** 2, "actual seed outside valid MG5 range")
    keys = ["pta", "etaa", "draa"]
    if profile == "bbgg":
        keys += ["ptb", "etab", "drab", "drbb"]
    elif profile in {"ccgg", "jjgg"}:
        keys += ["ptj", "etaj", "draj", "drjj"]
    require(all(number(rv.get(key, "0")) > 0 for key in keys), "invalid profile generation cuts")
    if profile != "diphoton":
        require(number(rv.get("maxjetflavor", "-1")) == 4, "profile requires maxjetflavor=4")
    block, masses, seen = None, {}, set()
    for row in records(cards["param_card"]):
        if row[0].lower() == "block":
            require(len(row) >= 2, "invalid parameter block")
            block = row[1].lower()
        elif row[0].lower() == "decay":
            require(len(row) >= 3 and number(row[2]) >= 0, "invalid decay width")
            block = "decay"
        elif block in {"mass", "yukawa", "sminputs"}:
            require(len(row) == 2, "invalid parameter value")
            key, value = integer(row[0]), number(row[1])
            require((block, key) not in seen, "duplicate parameter entry")
            seen.add((block, key))
            require(value >= 0 and (block != "sminputs" or value > 0), "invalid Standard Model parameter")
            if block == "mass":
                masses[key] = value
            elif block == "yukawa" and key in {1, 2, 3, 4, 5}:
                require(value == 0, "massless light-flavour Yukawa mismatch")
    require(all(masses.get(pdg) == 0 for pdg in (1, 2, 3, 4, 5, 21, 22)),
            "parameter card violates massless five-flavour model")


def validate_data(data: bytes, expected_events: int | None = None, *, profile="bbgg", beam_energy=None):
    require(profile in PROFILE_PROCESSES, "unknown physical validation profile")
    expected_final = {"bbgg": EXPECTED_FINAL, "ccgg": Counter([4, -4, 22, 22]),
                      "diphoton": Counter([22, 22])}.get(profile)
    expected_nup = 4 if profile == "diphoton" else 6
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
    require(all(len(header.findall(tag)) == 1 for tag in ("MGVersion", *CARD_TAGS.values())) and
            len(init.findall("generator")) == 1, "duplicate generator identity/card")
    require("MadGraph" in cards["process_card"], "generator identity missing")
    rv = run_values(cards["run_card"])
    validate_profile_cards(cards, rv, profile)
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
    require(pdf_ids == [10042, 10042], "init PDF differs from declared CTEQ6L1")
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
    final_counts = Counter()
    jet_profile = profile in {"ccgg", "jjgg"}
    object_name = "jet" if jet_profile else "b"
    cross_dr, pair_dr = ("draj", "drjj") if jet_profile else ("drab", "drbb")
    minima = {"photon_pt": math.inf, object_name + "_pt": math.inf, "draa": math.inf,
              cross_dr: math.inf, pair_dr: math.inf}
    maxima = {"photon_abs_eta": 0.0, object_name + "_abs_eta": 0.0}
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
        incoming, outgoing, color_balance = [], [], Counter()
        for particle_index, row in enumerate(rows[1:], 1):
            require(len(row) == 13, f"event {event_index}: malformed particle record")
            pdg, status, mother1, mother2, color1, color2 = [integer(x) for x in row[:6]]
            px, py, pz, energy, mass, lifetime, spin = [number(x) for x in row[6:]]
            require(status in {-1, 1}, "unexpected particle status for direct LO process")
            require(energy > 0 and mass >= 0 and lifetime >= 0, "invalid particle energy/mass/lifetime")
            require(0 <= mother1 <= nup and 0 <= mother2 <= nup and
                    particle_index not in {mother1, mother2}, "invalid mother indices")
            require(color1 >= 0 and color2 >= 0, "invalid color tags")
            require((mother1, mother2) == ((0, 0) if status == -1 else (1, 2)),
                    "unexpected direct-process mother assignment")
            if pdg == 22:
                require(color1 == color2 == 0, "photon carries color")
            elif 1 <= abs(pdg) <= 5:
                require((color1 > 0 and color2 == 0) if pdg > 0 else (color1 == 0 and color2 > 0),
                        "quark/antiquark color assignment mismatch")
            elif pdg == 21:
                require(color1 > 0 and color2 > 0 and color1 != color2, "invalid gluon color assignment")
            direction = -1 if status == -1 else 1
            if color1:
                color_balance[color1] += direction
            if color2:
                color_balance[color2] -= direction
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
        final_pdg = Counter(p[0] for p in outgoing)
        if profile == "jjgg":
            require(final_pdg[22] == 2 and sum(final_pdg[pdg] for pdg in LIGHT_JETS) == 2 and
                    set(final_pdg) <= LIGHT_JETS | {22}, "final state differs from declared light-jet process")
        else:
            require(final_pdg == expected_final, "final state differs from declared process")
        require(all(value == 0 for value in color_balance.values()), "color-flow conservation failure")
        final_counts.update(final_pdg)
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
        charge = {21: 0, 22: 0, 1: -1, 2: 2, 3: -1, 4: 2, 5: -1}
        electric_charge = lambda particles: sum(charge[abs(p[0])] * (1 if p[0] > 0 else -1) for p in particles)
        require(electric_charge(incoming) == electric_charge(outgoing), "electric-charge conservation failure")
        if profile in {"ccgg", "jjgg"}:
            # At QCD=2 QED=2 the continuum amplitudes contain two photon
            # vertices and conserve every quark flavour's net number.
            net_flavours = lambda particles: {
                flavour: sum((p[0] == flavour) - (p[0] == -flavour) for p in particles)
                for flavour in range(1, 6)
            }
            require(net_flavours(incoming) == net_flavours(outgoing),
                    "quark-flavour net-number conservation failure")
        objects = []
        for pdg, px, py, pz, energy in outgoing:
            pt = math.hypot(px, py)
            eta = math.asinh(pz / pt) if pt > 0 else math.inf
            photon = pdg == 22
            key = "photon" if photon else object_name
            cut_pt = number(rv["pta" if photon else "ptj" if jet_profile else "ptb"])
            cut_eta = number(rv["etaa" if photon else "etaj" if jet_profile else "etab"])
            require(pt >= cut_pt - 1e-6 and abs(eta) <= cut_eta + 1e-8, "generation pT/eta cut failure")
            minima[key + "_pt"] = min(minima[key + "_pt"], pt)
            maxima[key + "_abs_eta"] = max(maxima[key + "_abs_eta"], abs(eta))
            objects.append((photon, eta, math.atan2(py, px)))
        for index, (photon1, eta1, phi1) in enumerate(objects):
            for photon2, eta2, phi2 in objects[index + 1:]:
                key = "draa" if photon1 and photon2 else pair_dr if not photon1 and not photon2 else cross_dr
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
        "outgoing_pdg_counts": dict(sorted(final_counts.items())), "physics_profile": profile,
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
    require(isinstance(relative, str) and not Path(relative).is_absolute(), "manifest paths must be relative")
    path = repo / relative
    require(path.resolve().is_relative_to(repo.resolve()), "manifest path escapes repository")
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


def parameter_value(card, block_name, code):
    block = None
    for row in records(card):
        if row[0].lower() == "block":
            block = row[1].lower()
        elif row[0].lower() == "decay":
            block = "decay"
        elif block == block_name and integer(row[0]) == code:
            return number(row[1])
    raise ValidationError(f"parameter missing: {block_name}[{code}]")


def validate_background_manifest(repo: Path, profile: str):
    require(profile in BACKGROUND_DIRS, "unknown background-library profile")
    relative_dir = BACKGROUND_DIRS[profile]
    directory = repo / relative_dir
    manifest = json.loads((directory / "sample_manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("schema_version") == 1 and len(manifest.get("samples", [])) == 1,
            "new background manifest requires exactly one sample")
    require({path.name for path in directory.iterdir()} ==
            {"reference_1000.lhe.gz", "sample_manifest.json", "README.md"},
            "unexpected background-directory output")
    sample = manifest["samples"][0]
    require(REQUIRED_FIELDS | {"physics_profile"} <= sample.keys(), "missing mandatory background provenance")
    require(sample["sample_id"] == "reference_1000" and sample["physics_profile"] == profile,
            "background sample/profile identity mismatch")
    require(sample["file"] == relative_dir + "/reference_1000.lhe.gz", "background sample path mismatch")
    result = validate_file(safe_file(repo, sample["file"]), 1000, profile=profile, beam_energy=6500)
    rv, cards = result["run_values"], result["cards"]
    require(sample["requested_events"] == sample["actual_events"] == result["actual_events"] == 1000,
            "background count mismatch")
    require(sample["random_seed"] == integer(rv["iseed"]), "background actual seed mismatch")
    require(sample["validation_status"] == "PASS", "background not independently validated")
    for key in ("compressed_file_sha256", "decompressed_file_sha256", "event_content_sha256",
                "negative_weight_count", "zero_weight_count", "compressed_bytes"):
        require(sample[key] == result[key], "background manifest mismatch: " + key)
    for key, actual in (("generator_cross_section_pb", "cross_section_pb"),
                        ("cross_section_uncertainty_pb", "cross_section_uncertainty_pb")):
        require(math.isclose(number(str(sample[key])), result[actual], rel_tol=1e-8, abs_tol=1e-12),
                "background cross-section mismatch: " + key)
    for key in CARD_TAGS:
        path = safe_file(repo, sample[key + "_path"])
        require(sha256(path.read_bytes()) == sample[key + "_sha256"], "background card hash mismatch: " + key)
        require(canonical_card(path.read_text(encoding="utf-8")) == canonical_card(cards[key]),
                "background card differs from actual LHE banner: " + key)
    require(sample.get("provenance_files"), "background generation provenance missing")
    for item in sample["provenance_files"]:
        require(sha256(safe_file(repo, item["path"]).read_bytes()) == item["sha256"], "background provenance hash mismatch")
    source = sample["mg5_source_identity"]
    require(source == {"url": "https://github.com/mg5amcnlo/mg5amcnlo.git", "tag": "v3.5.16",
                       "commit": "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"},
            "background official generator source identity mismatch")
    require(sample["mg5_version"] == result["mg5_version"] == "3.5.16", "background generator version mismatch")
    require(sample["physics_process"] == PROFILE_PROCESSES[profile], "background declared process mismatch")
    require("sm-no_b_mass" in sample["physics_model"], "background declared model mismatch")
    require(sample["perturbative_order"] == "LO" and sample["sqrt_s_gev"] == 13000 and
            sample["beam_energies_gev"] == [6500, 6500], "background declared order/energy mismatch")
    require(sample["pdf_name_and_id"]["name"] == "CTEQ6L1" and
            sample["pdf_name_and_id"]["lhapdf_id"] == 10042, "background declared PDF mismatch")
    require(sample["renormalization_scale"] == {"type": "fixed", "gev": 125} and
            sample["factorization_scale"] == {"type": "fixed", "beam1_gev": 125, "beam2_gev": 125},
            "background scale metadata mismatch")
    require(sample["generator_weight_convention"]["idwtup"] == -4 and
            sample["generator_weight_convention"]["event_norm"] == "average", "background weight convention mismatch")
    require(sample["original_decompressed_file_sha256"] == sample["decompressed_file_sha256"],
            "background generator decompressed content changed")
    cuts = {"photon_pt_min_gev": 25, "photon_abs_eta_max": 2.5, "jet_pt_min_gev": 20,
            "jet_abs_eta_max": 5, "delta_r_aa_min": 0.4, "delta_r_aj_min": 0.4,
            "delta_r_jj_min": 0.4, "maxjetflavor_for_cut_classification": 4}
    require(all(sample["generation_cuts"].get(key) == value for key, value in cuts.items()),
            "background declared generation cuts mismatch")
    settings = {"pta": 25, "ptj": 20, "etaa": 2.5, "etaj": 5, "draa": 0.4, "draj": 0.4,
                "drjj": 0.4, "ebeam1": 6500, "ebeam2": 6500, "ickkw": 0, "ptgmin": 0,
                "maxjetflavor": 4, "scale": 125, "dsqrt_q2fact1": 125, "dsqrt_q2fact2": 125}
    require(all(number(rv[key]) == value for key, value in settings.items()), "background actual run setting mismatch")
    require(rv["fixed_ren_scale"].lower() in {"true", ".true."} and
            rv["fixed_fac_scale"].lower() in {"true", ".true."} and
            rv["systematics_program"] == "none", "background scale/systematics convention mismatch")
    require(result["event_scale_values_gev"] == [125] and result["event_alpha_s_values"] == [0.1238062] and
            result["event_alpha_em_values"] == [0.007546771], "background actual scale/coupling mismatch")
    aewm1 = parameter_value(cards["param_card"], "sminputs", 1)
    alpha_s = parameter_value(cards["param_card"], "sminputs", 3)
    require(math.isclose(sample["alpha_s_settings"]["param_card_as"], alpha_s, rel_tol=1e-8) and
            sample["alpha_s_settings"]["event_aqcd"] == result["event_alpha_s_values"][0],
            "background alpha_s metadata differs from actual card/event")
    require(math.isclose(sample["alpha_em_settings"]["aEWM1"], aewm1, rel_tol=1e-8) and
            math.isclose(sample["alpha_em_settings"]["alpha_em"], 1 / aewm1, rel_tol=1e-8),
            "background alpha_em metadata differs from actual parameter card")
    result.pop("cards")
    result.pop("run_values")
    return {"sample_id": sample["sample_id"], "file": sample["file"], **result}


def validate_background_library(repo: Path):
    legacy = validate_repository(repo)
    bbgg = next(sample for sample in legacy["samples"] if sample["sample_id"] == "reference_1000")
    reports = [{**bbgg, "file": SAMPLE_DIR + "/reference_1000.lhe.gz"}]
    reports.extend(validate_background_manifest(repo, profile) for profile in BACKGROUND_DIRS)
    require(sum(sample["actual_events"] for sample in reports) == 3000, "background library total must equal 3000")
    require(sum(safe_file(repo, sample["file"]).stat().st_size for sample in reports) <= MAX_TOTAL,
            "background library total compressed size cap")
    require(len({sample["event_content_sha256"] for sample in reports}) == 3, "background library duplicate event content")
    return {"status": "PASS", "actual_reference_events": 3000, "smoke_events_excluded": 100,
            "library_profiles": ["bbgg", "ccgg", "jjgg"], "samples": reports,
            "statistical_interpretation": "Three separate process samples; process cross sections are not summed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--background-library", type=Path, help="verify bbgg/ccgg/light-jjgg reference library; excludes smoke_100")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--events", type=int)
    parser.add_argument("--profile", choices=sorted(PROFILE_PROCESSES), default="bbgg")
    parser.add_argument("--generator-original", action="store_true", help="permit original gzip timestamp/filename; all physical checks remain")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        require(sum(bool(value) for value in (args.repository, args.file, args.background_library)) == 1,
                "choose --repository, --background-library, or --file")
        if args.background_library:
            result = validate_background_library(args.background_library)
        elif args.repository:
            result = validate_repository(args.repository)
        else:
            result = validate_file(args.file, args.events, profile=args.profile, require_deterministic=not args.generator_original)
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

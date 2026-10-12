#!/usr/bin/env python3
"""Stream every event in a local plain/gzip LHE and verify its run provenance.

Memory is bounded by the XML header and one event. Default input/decompressed
limits are 20/100 GiB, adjustable explicitly; reference publication uses its
separate, much smaller repository limits. No event is repaired or filtered.
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

from validate_lhe import (
    ALLOWED_INITIAL, CARD_TAGS, CLOSURE_ATOL_GEV, CLOSURE_RTOL,
    EXPECTED_FINAL, SHELL_ATOL_GEV2, SHELL_RTOL, ValidationError,
    canonical_card, integer, number, records, require, run_values, sha256,
)

SOURCE_COMMIT = "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"
SOURCE_URL = "https://github.com/mg5amcnlo/mg5amcnlo.git"
SOURCE_TAG = "v3.5.16"
MAX_XML_TOKEN = 16 * 1024 * 1024
CHUNK = 64 * 1024
PROCESS = {
    "bbgg": "generate p p > b b~ a a QCD=2 QED=2",
    "diphoton": "generate p p > a a QCD=0 QED=2",
}


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


class EventDigest:
    """Hash exact event element bytes, excluding inter-event whitespace.

    The tokenizer skips comments/CDATA/processing instructions so an apparent
    event tag inside a card comment cannot enter the event hash. ElementTree
    separately enforces well-formed XML. Retained token length is bounded.
    """
    def __init__(self):
        self.pending = b""
        self.inside = False
        self.count = 0
        self.event_bytes = 0
        self.digest = hashlib.sha256()

    def _consume(self, token):
        if token.startswith(b"<") and not token.startswith((b"<!--", b"<![", b"<?")):
            if re.match(rb"^<event(?:\s|>)", token):
                require(not self.inside and not token.endswith(b"/>"), "nested/empty event element")
                self.inside = True
                self.count += 1
                self.event_bytes = 0
            if token.startswith(b"</event"):
                require(re.fullmatch(rb"</event\s*>", token) and self.inside, "unmatched event closing tag")
                self.digest.update(token)
                require(self.event_bytes + len(token) <= MAX_XML_TOKEN, "event element exceeds 16 MiB")
                self.inside = False
                return
        if self.inside:
            self.event_bytes += len(token)
            require(self.event_bytes <= MAX_XML_TOKEN, "event element exceeds 16 MiB")
            self.digest.update(token)

    def feed(self, chunk):
        self.pending += chunk
        while self.pending:
            if not self.pending.startswith(b"<"):
                at = self.pending.find(b"<")
                if at == -1:
                    self._consume(self.pending)
                    self.pending = b""
                    break
                self._consume(self.pending[:at])
                self.pending = self.pending[at:]
            # A token prefix can straddle the input chunk boundary.
            if len(self.pending) < 9 and b">" not in self.pending:
                break
            ending = b"-->" if self.pending.startswith(b"<!--") else (
                b"]]>" if self.pending.startswith(b"<![CDATA[") else (
                    b"?>" if self.pending.startswith(b"<?") else b">"))
            if ending == b">":
                quote, at = None, -1
                for index, character in enumerate(self.pending):
                    if character in (34, 39):
                        quote = None if quote == character else character if quote is None else quote
                    elif character == 62 and quote is None:
                        at = index
                        break
            else:
                at = self.pending.find(ending)
            if at == -1:
                require(len(self.pending) <= MAX_XML_TOKEN, "XML token exceeds 16 MiB")
                break
            end = at + len(ending)
            self._consume(self.pending[:end])
            self.pending = self.pending[end:]

    def finish(self):
        require(not self.pending and not self.inside, "truncated event/XML token")


class CheckedReader:
    def __init__(self, stream, max_bytes):
        self.stream, self.max_bytes = stream, max_bytes
        self.total = 0
        self.digest = hashlib.sha256()
        self.events = EventDigest()
        self.tail = b""

    def read(self, size=-1):
        try:
            chunk = self.stream.read(min(size, CHUNK) if size >= 0 else CHUNK)
        except (OSError, EOFError) as exc:
            raise ValidationError(f"gzip integrity failure: {exc}") from exc
        self.total += len(chunk)
        require(self.total <= self.max_bytes, "decompressed size limit exceeded")
        scan = (self.tail + chunk).upper()
        require(b"<!DOCTYPE" not in scan and b"<!ENTITY" not in scan,
                "DTD/entities are not supported")
        self.tail = scan[-16:]
        self.digest.update(chunk)
        self.events.feed(chunk)
        require(self.events.count > 0 or self.total <= MAX_XML_TOKEN,
                "LHE header exceeds 16 MiB")
        return chunk


def validate_physics_cards(cards, rv, profile):
    commands = [line.split("#", 1)[0].strip() for line in cards["process_card"].splitlines()
                if line.split("#", 1)[0].strip()]
    required = ["import model sm-no_b_mass", "define p = g u c d s b u~ c~ d~ s~ b~", PROCESS[profile]]
    require(all(item in commands for item in required), "process/model/initial-state profile mismatch")
    require([line for line in commands if line.startswith("import model ")] == [required[0]] and
            [line for line in commands if line.startswith(("generate ", "add process "))] == [required[2]] and
            [line for line in commands if line.startswith("define p =")][-1] == required[1],
            "unreviewed process addition or model substitution")
    require(rv["pdlabel"].lower() == "cteq6l1" and number(rv["lhaid"]) == 10042,
            "profile requires the reviewed CTEQ6L1 PDF")
    require(rv["event_norm"] == "average" and number(rv["ickkw"]) == 0,
            "profile requires average unweighted LO events without matching")
    require(number(rv["ptgmin"]) == 0, "smooth-cone cuts need a separately implemented profile")
    required_cuts = ["pta", "etaa", "draa"]
    if profile == "bbgg":
        required_cuts += ["ptb", "etab", "drab", "drbb"]
        require(number(rv["maxjetflavor"]) == 4, "bbgg requires maxjetflavor=4 for b cuts")
    require(all(number(rv[key]) > 0 for key in required_cuts), "non-positive generation cut")
    block, masses, parameters = None, {}, set()
    for row in records(cards["param_card"]):
        if row[0].lower() == "block":
            require(len(row) >= 2, "invalid parameter block")
            block = row[1].lower()
        elif row[0].lower() == "decay":
            require(len(row) >= 3 and number(row[2]) >= 0, "invalid decay width")
            block = "decay"
        elif block in {"mass", "sminputs", "yukawa"}:
            require(len(row) == 2, "invalid parameter value")
            key, value = integer(row[0]), number(row[1])
            require((block, key) not in parameters, "duplicate parameter-card entry")
            parameters.add((block, key))
            if block == "mass":
                require(key not in masses and value >= 0, "duplicate/negative mass parameter")
                masses[key] = value
            if block == "yukawa" and key == 5:
                require(value == 0, "profile requires zero b Yukawa")
            require(value >= 0 and (block != "sminputs" or value > 0),
                    "non-positive Standard Model input or negative parameter")
    require(all(masses.get(pdg) == 0 for pdg in (1, 2, 3, 4, 5, 21, 22)),
            "parameter card violates massless five-flavour profile")


def _header(root, profile, beam_energy):
    header, init = root.find("header"), root.find("init")
    require(header is not None and init is not None, "header/init missing")
    require(all(len(header.findall(tag)) == 1 for tag in ("MGVersion", *CARD_TAGS.values())),
            "missing/duplicate generator identity or header card")
    version = header.findtext("MGVersion", "").strip()
    require(version == "3.5.16", "unexpected MG5 version")
    generator = init.find("generator")
    require(len(init.findall("generator")) == 1 and generator is not None and generator.get("name") == "MadGraph5_aMC@NLO" and
            generator.get("version") == version, "init generator identity mismatch")
    cards = {key: header.findtext(tag, "") for key, tag in CARD_TAGS.items()}
    require(all(text.strip() for text in cards.values()), "generator cards missing from header")
    rv = run_values(cards["run_card"])
    require(1 <= integer(rv["iseed"]) <= 30081 ** 2, "actual random seed outside supported range")
    validate_physics_cards(cards, rv, profile)
    init_rows = records(init.text or "")
    require(init_rows and len(init_rows[0]) == 10, "invalid init beam record")
    beam = init_rows[0]
    require([integer(x) for x in beam[:2]] == [2212, 2212], "beams are not protons")
    if beam_energy is None:
        beam_energy = number(rv["ebeam1"])
    require(math.isfinite(beam_energy) and beam_energy > 0, "invalid beam energy")
    require([number(x) for x in beam[2:4]] == [beam_energy, beam_energy], "wrong beam energies")
    require(number(rv["ebeam1"]) == number(rv["ebeam2"]) == beam_energy, "card/init energy mismatch")
    require(number(rv["lpp1"]) == number(rv["lpp2"]) == 1, "run-card beams are not protons")
    pdf_groups = [integer(x) for x in beam[4:6]]
    pdf_ids = [integer(x) for x in beam[6:8]]
    require(pdf_ids == [10042, 10042], "init PDF differs from reviewed CTEQ6L1")
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
    expected_final = EXPECTED_FINAL if profile == "bbgg" else Counter([22, 22])
    return {"cards": cards, "rv": rv, "version": version, "beam_energy": beam_energy,
            "pdf_groups": pdf_groups, "pdf_ids": pdf_ids, "idwtup": idwtup, "processes": processes,
            "expected_final": expected_final, "expected_nup": sum(expected_final.values()) + 2,
            "max_closure": 0.0, "max_shell": 0.0, "signs": Counter(), "weight_values": set(),
            "event_scales": set(), "aqed_values": set(), "aqcd_values": set(), "truncated_sets": set(),
            "initial_counts": Counter(), "minima": {"photon_pt": math.inf, "b_pt": math.inf,
            "draa": math.inf, "drab": math.inf, "drbb": math.inf},
            "maxima": {"photon_abs_eta": 0.0, "b_abs_eta": 0.0}}


def _bounded_add(context, key, value):
    values = context[key]
    if value in values or len(values) < 256:
        values.add(value)
    else:
        context["truncated_sets"].add(key)


def _event(event, event_index, context):
    rv, processes = context["rv"], context["processes"]
    expected_nup, expected_final = context["expected_nup"], context["expected_final"]
    beam_energy = context["beam_energy"]
    minima, maxima = context["minima"], context["maxima"]
    rows = records(event.text or "")
    require(rows and len(rows[0]) == 6, f"event {event_index}: invalid event header")
    nup, pid = [integer(x) for x in rows[0][:2]]
    weight, scale, aqed, aqcd = [number(x) for x in rows[0][2:]]
    require(nup == expected_nup and len(rows) == nup + 1, f"event {event_index}: particle record count")
    require(pid in processes and scale > 0 and aqed > 0 and aqcd > 0, "invalid event metadata")
    context["signs"]["negative" if weight < 0 else "zero" if weight == 0 else "positive"] += 1
    require(weight > 0, "non-positive nominal LO event weight")
    context["weight_values"].add(weight)
    require(len(context["weight_values"]) == 1, "unweighted sample has unequal nominal event weights")
    for key, value in (("event_scales", scale), ("aqed_values", aqed), ("aqcd_values", aqcd)):
        _bounded_add(context, key, value)
    if rv.get("fixed_ren_scale", "").lower() in {"true", ".true."}:
        require(math.isclose(scale, number(rv["scale"]), rel_tol=1e-7), "fixed renormalization scale mismatch")
    incoming, outgoing = [], []
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
        require(mass == 0.0, "expected massless five-flavour hard particles")
        p2 = px * px + py * py + pz * pz
        shell = abs(energy * energy - p2 - mass * mass)
        require(shell <= SHELL_ATOL_GEV2 + SHELL_RTOL * max(energy * energy, p2, mass * mass, 1.0),
                f"event {event_index}: mass-shell failure")
        context["max_shell"] = max(context["max_shell"], shell)
        particle = (pdg, px, py, pz, energy)
        (incoming if status == -1 else outgoing).append(particle)
    require(len(incoming) == 2 and len(outgoing) == expected_nup - 2, "wrong incoming/outgoing multiplicity")
    require(all(p[0] in ALLOWED_INITIAL for p in incoming), "unexpected incoming PDG ID")
    require(Counter(p[0] for p in outgoing) == expected_final, "final state differs from declared process")
    context["initial_counts"][",".join(str(p[0]) for p in incoming)] += 1
    require(all(p[1] == p[2] == 0 for p in incoming) and incoming[0][3] > 0 > incoming[1][3],
            "invalid collinear beam kinematics")
    require(all(p[4] <= beam_energy + CLOSURE_ATOL_GEV for p in incoming), "parton exceeds beam energy")
    total_energy = sum(p[4] for p in incoming)
    for component in range(1, 5):
        residual = abs(math.fsum(p[component] for p in incoming) - math.fsum(p[component] for p in outgoing))
        require(residual <= CLOSURE_ATOL_GEV + CLOSURE_RTOL * total_energy,
                f"event {event_index}: four-momentum closure failure")
        context["max_closure"] = max(context["max_closure"], residual)
    charge = {21: 0, 1: -1, 2: 2, 3: -1, 4: 2, 5: -1}
    require(sum(charge[abs(p[0])] * (1 if p[0] > 0 else -1) for p in incoming) == 0,
            "incoming charge does not match neutral final state")
    objects = []
    for pdg, px, py, pz, energy in outgoing:
        pt = math.hypot(px, py)
        eta = math.asinh(pz / pt) if pt > 0 else math.inf
        photon = pdg == 22
        key = "photon" if photon else "b"
        cut_pt, cut_eta = number(rv["pta" if photon else "ptb"]), number(rv["etaa" if photon else "etab"])
        require(pt >= cut_pt - 1e-6 and abs(eta) <= cut_eta + 1e-8, "generation pT/eta cut failure")
        minima[key + "_pt"] = min(minima[key + "_pt"], pt)
        maxima[key + "_abs_eta"] = max(maxima[key + "_abs_eta"], abs(eta))
        objects.append((photon, eta, math.atan2(py, px)))
    for index, (photon1, eta1, phi1) in enumerate(objects):
        for photon2, eta2, phi2 in objects[index + 1:]:
            key = "draa" if photon1 and photon2 else "drbb" if not photon1 and not photon2 else "drab"
            delta_r = math.hypot(eta1 - eta2, math.remainder(phi1 - phi2, 2 * math.pi))
            require(delta_r >= number(rv[key]) - 1e-8, "generation DeltaR cut failure")
            minima[key] = min(minima[key], delta_r)
    for optional in event.findall(".//wgt"):
        number(optional.text or "")


def _finish(context, count, expected_events, root, reader):
    rv = context["rv"]
    require(count > 0, "LHE contains no events")
    if expected_events is not None:
        require(count == expected_events, "actual LHE event count mismatch")
    require(count == integer(rv["nevents"]), "event count differs from actual run card")
    require(reader.events.count == count, "raw/XML event element counts disagree")
    reader.events.finish()
    total_xsec = math.fsum(p[0] for p in context["processes"].values())
    nominal = next(iter(context["weight_values"]))
    require(math.isclose(nominal, total_xsec, rel_tol=1e-7, abs_tol=1e-12),
            "MG5 nominal weight differs from init cross section")
    extrema = {key: value for key, value in {**context["minima"], **context["maxima"]}.items() if math.isfinite(value)}
    return {
        "validation_status": "PASS", "lhe_version": root.get("version"),
        "mg5_version": context["version"], "actual_events": count, "idwtup": context["idwtup"],
        "pdf_groups": context["pdf_groups"], "pdf_ids": context["pdf_ids"],
        "cross_section_pb": total_xsec,
        "cross_section_uncertainty_pb": math.sqrt(sum(p[1] ** 2 for p in context["processes"].values())),
        "negative_weight_count": context["signs"]["negative"], "zero_weight_count": context["signs"]["zero"],
        "positive_weight_count": context["signs"]["positive"], "nominal_event_weight": nominal,
        "event_scale_values_gev": sorted(context["event_scales"]),
        "event_alpha_em_values": sorted(context["aqed_values"]), "event_alpha_s_values": sorted(context["aqcd_values"]),
        "distinct_value_lists_truncated": sorted(context["truncated_sets"]),
        "max_four_momentum_residual_gev": context["max_closure"],
        "max_mass_shell_residual_gev2": context["max_shell"], "cut_extrema": extrema,
        "incoming_pdg_pair_counts": dict(context["initial_counts"]),
        "event_content_sha256": reader.events.digest.hexdigest(),
        "decompressed_file_sha256": reader.digest.hexdigest(), "decompressed_bytes": reader.total,
        "run_values": rv, "cards": context["cards"],
        "tolerances": {"closure_atol_gev": CLOSURE_ATOL_GEV, "closure_rtol": CLOSURE_RTOL,
                       "shell_atol_gev2": SHELL_ATOL_GEV2, "shell_rtol": SHELL_RTOL},
    }


def validate_file(path, expected_events=None, *, profile="bbgg", beam_energy=None,
                  expected_seed=None, require_deterministic=True, manifest=None,
                  max_file_gb=20, max_decompressed_gb=100):
    path = Path(path)
    require(profile in PROCESS, "unknown physical validation profile")
    require(path.is_file() and not path.is_symlink(), "sample file missing or symlink")
    require(all(math.isfinite(x) and x > 0 for x in (max_file_gb, max_decompressed_gb)), "invalid file limits")
    initial_stat = path.stat()
    size = initial_stat.st_size
    require(size <= max_file_gb * 1024 ** 3, "sample input size limit exceeded")
    with path.open("rb") as stream:
        signature = stream.read(18)
    is_gzip = signature.startswith(b"\x1f\x8b\x08")
    if path.suffix == ".gz":
        require(is_gzip and size >= 18, "invalid/truncated gzip signature")
    if is_gzip and require_deterministic:
        require(signature[4:8] == b"\0\0\0\0" and not (signature[3] & 8),
                "gzip must have mtime=0 and no original filename")
    raw = gzip.open(path, "rb") if is_gzip else path.open("rb")
    root, context, count = None, None, 0
    header_count = init_count = 0
    depth = 0
    try:
        with raw:
            reader = CheckedReader(raw, max_decompressed_gb * 1024 ** 3)
            for action, element in ET.iterparse(reader, events=("start", "end")):
                if action == "start":
                    depth += 1
                    require(depth <= 32, "XML nesting limit exceeded")
                    if root is None:
                        root = element
                        require(root.tag == "LesHouchesEvents", "wrong LHE root")
                        require(root.get("version") in {"1.0", "3.0"}, "unsupported LHE version")
                    elif depth == 2:
                        require(element.tag in {"header", "init", "event"},
                                "unexpected top-level LHE element: " + element.tag)
                    continue
                if depth == 2:
                    if element.tag == "header":
                        header_count += 1
                        require(header_count == 1 and count == 0, "duplicate/out-of-order header")
                    elif element.tag == "init":
                        init_count += 1
                        require(init_count == 1 and count == 0, "duplicate/out-of-order init")
                        context = _header(root, profile, beam_energy)
                    elif element.tag == "event":
                        require(context is not None and header_count == init_count == 1, "header/init missing")
                        count += 1
                        _event(element, count, context)
                        root.remove(element)
                        element.clear()
                    else:
                        raise ValidationError("unexpected top-level LHE element: " + element.tag)
                depth -= 1
                require(reader.total <= MAX_XML_TOKEN or context is not None, "LHE header exceeds 16 MiB")
            require(root is not None and context is not None and header_count == init_count == 1, "header/init missing")
            result = _finish(context, count, expected_events, root, reader)
    except ET.ParseError as exc:
        raise ValidationError(f"invalid or truncated LHE XML: {exc}") from exc
    result.update(compressed_file_sha256=file_hash(path), compressed_bytes=size,
                  file_format="gzip" if is_gzip else "lhe", validator="streaming_all_events")
    final_stat = path.stat()
    require((initial_stat.st_size, initial_stat.st_mtime_ns, initial_stat.st_ino) ==
            (final_stat.st_size, final_stat.st_mtime_ns, final_stat.st_ino),
            "sample changed during independent validation")
    if expected_seed is not None:
        require(integer(result["run_values"]["iseed"]) == expected_seed, "actual seed mismatch")
    if manifest is not None:
        validate_manifest(result, Path(manifest), path, profile)
    return result


def _run_file(directory, relative):
    require(isinstance(relative, str) and not Path(relative).is_absolute(), "run manifest paths must be relative")
    path = directory / relative
    require(path.resolve().is_relative_to(directory.resolve()), "run manifest path escapes run directory")
    require(path.is_file() and not path.is_symlink(), "run provenance file missing/symlink: " + relative)
    return path


def validate_manifest(result, manifest_path, sample_path, profile):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    directory = manifest_path.parent
    require(manifest.get("status") == "PASS", "run manifest is not complete PASS")
    require(manifest.get("schema_version") in {1, 2}, "unsupported run manifest schema")
    require(manifest["profile"] == profile, "run manifest validation profile mismatch")
    require(manifest["process"] == PROCESS[profile], "run manifest process mismatch")
    require(manifest["events_requested"] == result["actual_events"], "run manifest requested count mismatch")
    require(integer(result["run_values"]["iseed"]) == manifest["random_seed"], "run manifest seed mismatch")
    require(number(result["run_values"]["ebeam1"]) * 2 == manifest["sqrt_s_gev"], "run manifest energy mismatch")
    require(manifest["mg5_source_commit"] == SOURCE_COMMIT, "run source identity differs from pinned official tag")
    source = manifest.get("source_identity", {})
    require(source.get("source_commit") == SOURCE_COMMIT, "run source identity disagreement")
    require(source.get("source_url") == SOURCE_URL and source.get("source_tag") == SOURCE_TAG,
            "run source URL/tag differs from pinned official release")
    if manifest["schema_version"] == 2:
        request = manifest["request"]
        require(sha256(json.dumps(request, sort_keys=True).encode()) == manifest["request_sha256"],
                "run request hash mismatch")
        for key in ("profile", "process", "events_requested", "random_seed", "sqrt_s_gev", "mg5_source_commit"):
            require(request[key] == manifest[key], "saved request differs from run manifest: " + key)
        attempt = manifest["attempt_directory"]
        requested = {"process_card_sha256": "requested_process.mg5",
                     "supplied_run_card_sha256": "requested_run_card.dat",
                     "supplied_param_card_sha256": "requested_param_card.dat"}
        for key, filename in requested.items():
            if request.get(key) is not None:
                require(file_hash(_run_file(directory, attempt + "/" + filename)) == request[key],
                        "requested input card hash mismatch: " + key)
    validated = manifest["validation"]
    for key in ("compressed_file_sha256", "decompressed_file_sha256", "event_content_sha256",
                "actual_events", "compressed_bytes", "negative_weight_count", "zero_weight_count"):
        require(validated[key] == result[key], "run manifest mismatch: " + key)
    for key in ("cross_section_pb", "cross_section_uncertainty_pb"):
        require(math.isclose(validated[key], result[key], rel_tol=1e-8, abs_tol=1e-12), "run manifest mismatch: " + key)
    files = {"process_card": "cards/proc_card_mg5.dat", "run_card": "cards/run_card.dat", "param_card": "cards/param_card.dat"}
    for key, relative in files.items():
        path = _run_file(directory, relative)
        require(file_hash(path) == manifest["card_hashes"][key + "_sha256"], "run card hash mismatch: " + key)
        require(canonical_card(path.read_text(encoding="utf-8")) == canonical_card(result["cards"][key]),
                "run archived card differs from actual LHE banner: " + key)
    if "lhe_gz" in manifest:
        require(_run_file(directory, manifest["lhe_gz"]).resolve() == sample_path.resolve(), "run manifest sample path mismatch")
    result["run_manifest_validation"] = "PASS"
    result["mg5_source_commit"] = SOURCE_COMMIT


def validate_run(directory, *, max_file_gb=20, max_decompressed_gb=100):
    directory = Path(directory).resolve()
    manifest_path = _run_file(directory, "run_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample_path = _run_file(directory, manifest["lhe_gz"])
    return validate_file(sample_path, manifest["events_requested"], profile=manifest["profile"],
                         beam_energy=manifest["sqrt_s_gev"] / 2, expected_seed=manifest["random_seed"],
                         manifest=manifest_path, max_file_gb=max_file_gb, max_decompressed_gb=max_decompressed_gb)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, help="verify a completed local run, including manifest and exact cards")
    parser.add_argument("--file", type=Path, help="plain LHE or gzip LHE")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--events", type=int)
    parser.add_argument("--profile", choices=sorted(PROCESS), default="bbgg")
    parser.add_argument("--beam-energy", type=float, help="energy of each equal proton beam in GeV")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--generator-original", action="store_true", help="allow original gzip timestamps/filename")
    parser.add_argument("--max-file-gb", type=float, default=20)
    parser.add_argument("--max-decompressed-gb", type=float, default=100)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        require(bool(args.run) != bool(args.file), "choose --run or --file")
        require(args.events is None or args.events > 0, "events must be positive")
        limits = {"max_file_gb": args.max_file_gb, "max_decompressed_gb": args.max_decompressed_gb}
        if args.run:
            require(not args.manifest, "--run already identifies its manifest")
            result = validate_run(args.run, **limits)
        else:
            result = validate_file(args.file, args.events, profile=args.profile, beam_energy=args.beam_energy,
                                   expected_seed=args.seed, require_deterministic=not args.generator_original,
                                   manifest=args.manifest, **limits)
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

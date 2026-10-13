#!/usr/bin/env python3
"""Read-only streaming validation of the original Phase 6A hard events.

The per-event checks preserve Phase 6A's physics rules; the original XML cards
and event bytes are never rewritten. Memory holds the header and one event.
"""
from collections import Counter
import gzip
import hashlib
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/mg5/scripts"))
from validate_lhe import (ALLOWED_INITIAL, CARD_TAGS, CLOSURE_ATOL_GEV, CLOSURE_RTOL,
                         EXPECTED_FINAL, LIGHT_JETS, PROFILE_PROCESSES, SHELL_ATOL_GEV2,
                         SHELL_RTOL, ValidationError, integer, number, records, require,
                         run_values, validate_profile_cards)

CHUNK = 65536
MAX_ELEMENT_BYTES = 16 * 1024 * 1024
REFERENCE_HASHES = {
    "bbgg": "bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343",
    "ccgg": "3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef",
    "jjgg": "606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030",
}


class WeightStats:
    """Signed finite moments; Welford variance avoids cancellation."""
    def __init__(self):
        self.n = 0
        self.mean = self.m2 = self.sum = self.sum_abs = self.sum_squared = 0.0
        self.minimum, self.maximum = math.inf, -math.inf
        self.first, self.constant = None, True
    def add(self, weight):
        self.n += 1
        delta = weight - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (weight - self.mean)
        self.sum += weight
        self.sum_abs += abs(weight)
        self.sum_squared += weight * weight
        self.minimum, self.maximum = min(self.minimum, weight), max(self.maximum, weight)
        if self.first is None:
            self.first = weight
        self.constant = self.constant and weight == self.first
    def report(self):
        require(all(math.isfinite(value) for value in (self.mean, self.m2, self.sum, self.sum_abs, self.sum_squared)),
                "source weight moments overflow/non-finite")
        return {"sum": self.sum, "sum_abs": self.sum_abs, "sum_squared": self.sum_squared,
                "mean": self.mean, "min": self.minimum, "max": self.maximum,
                "standard_error": math.sqrt(max(0.0, self.m2) / (self.n - 1) / self.n) if self.n > 1 else 0.0,
                "constant": self.constant}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_lhe(path):
    return gzip.open(path, "rb") if Path(path).suffix == ".gz" else Path(path).open("rb")


def iter_lhe_events(path):
    """Yield exact raw event elements, with 1-based index and finite header.

    This byte iterator is used after validate_lhe_stream confirms complete XML.
    It deliberately uses the MG5's exact <event> marker and retains original
    spacing so hashes agree with the published Phase 6A event identities.
    """
    pending, index, saw_event = b"", 0, False
    try:
        with open_lhe(path) as stream:
            while True:
                chunk = stream.read(CHUNK)
                if not chunk:
                    break
                pending += chunk
                while True:
                    start = pending.find(b"<event>")
                    if start < 0:
                        require(len(pending) <= MAX_ELEMENT_BYTES, "LHE header/footer exceeds 16 MiB")
                        break
                    stop = pending.find(b"</event>", start)
                    if stop < 0:
                        pending = pending[start:]
                        require(len(pending) <= MAX_ELEMENT_BYTES, "LHE event exceeds 16 MiB")
                        break
                    stop += len(b"</event>")
                    raw = pending[start:stop]
                    pending = pending[stop:]
                    saw_event = True
                    index += 1
                    element = ET.fromstring(raw)
                    rows = records(element.text or "")
                    require(rows and len(rows[0]) == 6, "invalid source event header")
                    yield {"source_event_index": index, "source_event_content_hash": hashlib.sha256(raw).hexdigest(),
                           "raw": raw, "nominal_generator_weight": number(rows[0][2]),
                           "scale_gev": number(rows[0][3]), "rows": rows}
        require(saw_event and b"<event>" not in pending, "no events or truncated source event")
    except (OSError, EOFError, ET.ParseError) as error:
        raise ValidationError("LHE/gzip integrity failure: " + str(error)) from error


class CheckedReader:
    def __init__(self, stream, max_bytes):
        self.stream, self.max_bytes = stream, max_bytes
        self.total = 0
        self.digest = hashlib.sha256()
        self.tail = b""
        self.event_bytes = 0
        self.in_event = False
        self.element_start = 0
    def read(self, size=-1):
        try:
            chunk = self.stream.read(CHUNK if size < 0 else min(size, CHUNK))
        except (OSError, EOFError) as error:
            raise ValidationError("LHE/gzip integrity failure: " + str(error)) from error
        self.total += len(chunk)
        require(self.total <= self.max_bytes, "LHE decompressed size limit exceeded")
        require(self.total - self.element_start <= MAX_ELEMENT_BYTES + CHUNK,
                "source XML element exceeds bounded memory limit")
        scan = self.tail + chunk
        require(b"<!DOCTYPE" not in scan.upper() and b"<!ENTITY" not in scan.upper(), "DTD/entities unsupported")
        self.tail = scan[-16:]
        self.digest.update(chunk)
        return chunk


def _header(root, profile):
    header, init = root.find("header"), root.find("init")
    require(header is not None and init is not None, "LHE header/init missing")
    version = header.findtext("MGVersion", "").strip()
    require(version == "3.5.16", "unexpected MG5 version")
    generator = init.find("generator")
    require(generator is not None and generator.get("name") == "MadGraph5_aMC@NLO" and
            generator.get("version") == version, "init generator identity mismatch")
    cards = {key: header.findtext(tag, "") for key, tag in CARD_TAGS.items()}
    require(all(value.strip() for value in cards.values()), "generator cards missing")
    require(all(len(header.findall(tag)) == 1 for tag in ("MGVersion", *CARD_TAGS.values())) and
            len(init.findall("generator")) == 1, "duplicate source card/generator")
    rv = run_values(cards["run_card"])
    validate_profile_cards(cards, rv, profile)
    rows = records(init.text or "")
    require(rows and len(rows[0]) == 10, "invalid LHE init record")
    beam = rows[0]
    require([integer(x) for x in beam[:2]] == [2212, 2212], "source beams are not protons")
    beam_energy = number(rv["ebeam1"])
    require(number(rv["ebeam2"]) == beam_energy and beam_energy > 0 and
            [number(x) for x in beam[2:4]] == [beam_energy, beam_energy], "source beam energy mismatch")
    require(number(rv["lpp1"]) == number(rv["lpp2"]) == 1, "source proton beam card mismatch")
    require([integer(x) for x in beam[6:8]] == [10042, 10042], "source init PDF mismatch")
    require(integer(beam[8]) == -4 and integer(beam[9]) > 0 and len(rows) == integer(beam[9]) + 1,
            "source weight/subprocess convention mismatch")
    processes = {}
    for row in rows[1:]:
        require(len(row) == 4, "invalid init subprocess")
        xsec, error, xmax = [number(x) for x in row[:3]]
        pid = integer(row[3])
        require(xsec > 0 and error >= 0 and xmax > 0 and pid not in processes, "invalid source cross section")
        processes[pid] = (xsec, error, xmax)
    return cards, rv, beam_energy, processes


def _event(event, event_index, context):
    (profile, rv, beam_energy, processes, expected_final, expected_nup, signs, weight_values,
     event_scales, aqed_values, aqcd_values, initial_counts, final_counts, jet_profile,
     object_name, cross_dr, pair_dr, minima, maxima, weight_stats) = context
    max_closure = max_shell = 0.0
    rows = records(event.text or "")
    require(rows and len(rows[0]) == 6, f"event {event_index}: invalid event header")
    nup, pid = [integer(x) for x in rows[0][:2]]
    weight, scale, aqed, aqcd = [number(x) for x in rows[0][2:]]
    require(nup == expected_nup and len(rows) == nup + 1, f"event {event_index}: particle record count")
    require(pid in processes and scale > 0 and aqed > 0 and aqcd > 0, "invalid event metadata")
    signs["negative" if weight < 0 else "zero" if weight == 0 else "positive"] += 1
    if len(weight_values) < 256:
        weight_values.add(weight)
    weight_stats.add(weight)
    event_scales.add(scale) if len(event_scales) < 256 else None
    aqed_values.add(aqed) if len(aqed_values) < 256 else None
    aqcd_values.add(aqcd) if len(aqcd_values) < 256 else None
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
    return max_closure, max_shell


def validate_lhe_stream(path, profile, expected_hash=None, *, max_decompressed_gb=100):
    path = Path(path)
    require(profile in {"bbgg", "ccgg", "jjgg"}, "unsupported shower input profile")
    require(path.is_file() and not path.is_symlink(), "source LHE missing/symlink")
    require(math.isfinite(max_decompressed_gb) and max_decompressed_gb > 0, "invalid source size limit")
    compressed_hash = file_sha256(path)
    initial_stat = path.stat()
    if expected_hash is not None:
        require(compressed_hash == expected_hash, "original LHE file SHA256 mismatch")
    root = context = None
    header_count = init_count = count = depth = 0
    signs, weight_values = Counter(), set()
    weight_stats = WeightStats()
    scales, aqeds, aqcds, initials, finals = set(), set(), set(), Counter(), Counter()
    max_closure = max_shell = 0.0
    jet_profile = profile in {"ccgg", "jjgg"}
    object_name = "jet" if jet_profile else "b"
    cross_dr, pair_dr = ("draj", "drjj") if jet_profile else ("drab", "drbb")
    minima = {"photon_pt": math.inf, object_name + "_pt": math.inf,
              "draa": math.inf, cross_dr: math.inf, pair_dr: math.inf}
    maxima = {"photon_abs_eta": 0.0, object_name + "_abs_eta": 0.0}
    event_start_bytes = 0
    try:
        with open_lhe(path) as stream:
            reader = CheckedReader(stream, max_decompressed_gb * 1024**3)
            for action, element in ET.iterparse(reader, events=("start", "end")):
                if action == "start":
                    depth += 1
                    require(depth <= 32, "LHE XML nesting limit")
                    if root is None:
                        root = element
                        require(root.tag == "LesHouchesEvents" and root.get("version") in {"1.0", "3.0"}, "invalid LHE root")
                    elif depth == 2:
                        require(element.tag in {"header", "init", "event"}, "unexpected LHE top-level element")
                        event_start_bytes = reader.total
                        reader.element_start = max(0, reader.total - CHUNK)
                    continue
                if depth == 2:
                    require(reader.total - event_start_bytes <= MAX_ELEMENT_BYTES, "LHE element exceeds 16 MiB")
                    if element.tag == "header":
                        header_count += 1
                        require(header_count == 1 and not count, "duplicate/out-of-order source header")
                    elif element.tag == "init":
                        init_count += 1
                        require(init_count == 1 and not count, "duplicate/out-of-order source init")
                        cards, rv, beam_energy, processes = _header(root, profile)
                        expected_final = EXPECTED_FINAL if profile == "bbgg" else Counter([4, -4, 22, 22]) if profile == "ccgg" else None
                        context = (profile, rv, beam_energy, processes, expected_final, 6, signs, weight_values,
                                   scales, aqeds, aqcds, initials, finals, jet_profile, object_name,
                                   cross_dr, pair_dr, minima, maxima, weight_stats)
                    elif element.tag == "event":
                        require(context is not None and header_count == init_count == 1, "source header/init missing")
                        count += 1
                        closure, shell = _event(element, count, context)
                        max_closure, max_shell = max(max_closure, closure), max(max_shell, shell)
                        root.remove(element)
                        element.clear()
                depth -= 1
            require(context is not None and count > 0, "source contains no events")
            require(count == integer(rv["nevents"]), "source count differs from original run card")
            xsec = math.fsum(p[0] for p in processes.values())
            xsec_error = math.sqrt(sum(p[1]**2 for p in processes.values()))
            moments = weight_stats.report()
            printed_tolerance = 1e-7 * max(abs(xsec), abs(moments["mean"]), 1e-9) + 1e-12
            normalization_tolerance = 5 * math.hypot(xsec_error, moments["standard_error"]) + printed_tolerance
            require(abs(moments["mean"] - xsec) <= normalization_tolerance,
                    "source signed mean weight/init cross section inconsistency")
            known_reference = compressed_hash == REFERENCE_HASHES[profile]
            if known_reference:
                require(count == 1000 and signs["negative"] == signs["zero"] == 0 and weight_stats.constant and
                        math.isclose(weight_stats.first, xsec, rel_tol=1e-7, abs_tol=1e-12),
                        "fixed reference nominal positive LO weight convention")
    except ET.ParseError as error:
        raise ValidationError("invalid/truncated source LHE XML: " + str(error)) from error
    event_digest = hashlib.sha256()
    raw_count = 0
    for source in iter_lhe_events(path):
        raw_count += 1
        event_digest.update(source["raw"])
    require(raw_count == count, "source raw/XML event count mismatch")
    final_stat = path.stat()
    require((initial_stat.st_size, initial_stat.st_mtime_ns, initial_stat.st_ino) ==
            (final_stat.st_size, final_stat.st_mtime_ns, final_stat.st_ino), "source input changed during validation")
    return {"validation_status": "PASS", "actual_events": count, "N_input": count,
            "cross_section_pb": xsec, "cross_section_uncertainty_pb": xsec_error,
            "nominal_event_weight": weight_stats.first if weight_stats.constant else None,
            "weight_moments": moments, "weight_normalization_residual_pb": moments["mean"] - xsec,
            "weight_normalization_tolerance_pb": normalization_tolerance,
            "weight_normalization_test": "mean(XWGTUP) vs init: 5*hypot(integration_error,sample_mean_standard_error)+printed_precision",
            "known_positive_reference": known_reference, "signed_weights_preserved": True,
            "idwtup": -4, "physics_profile": profile,
            "compressed_file_sha256": compressed_hash, "decompressed_file_sha256": reader.digest.hexdigest(),
            "decompressed_bytes": reader.total, "event_content_sha256": event_digest.hexdigest(),
            "cards": cards, "run_values": rv, "mg5_version": "3.5.16", "beam_energy_gev": beam_energy,
            "cut_extrema": {k: val for k, val in {**minima, **maxima}.items() if math.isfinite(val)},
            "max_four_momentum_residual_gev": max_closure, "max_mass_shell_residual_gev2": max_shell,
            "negative_weight_count": signs["negative"], "zero_weight_count": signs["zero"],
            "positive_weight_count": signs["positive"], "source_event_hash_rule": "SHA256 exact <event> through </event> bytes"}

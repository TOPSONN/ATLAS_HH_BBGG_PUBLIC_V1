#!/usr/bin/env python3
"""Portable integrity validation of actual Pythia HepMC3 ASCII references.

This standard-library parser does not replace the separately executed C++
HepMC3 ReaderAscii/Pythia ParticleData validator. It streams one event at a
time, including gzip CRC, exact source/ledger hashes and the encoded graph.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from validate_lhe_stream import file_sha256, iter_lhe_events

REPO = Path(__file__).resolve().parents[3]
MAX_LINE = 1024 * 1024
MAX_EVENT = 64 * 1024 * 1024
START = b"HepMC::Asciiv3-START_EVENT_LISTING\n"
END = b"HepMC::Asciiv3-END_EVENT_LISTING\n"
CLOSURE_ATOL_GEV, CLOSURE_RTOL = 1e-5, 1e-9
SOURCE_SAMPLES = {
    "bbgg": ("reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz",
             "bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343", 0.06624666),
    "ccgg": ("reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz",
             "3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef", 0.6274417),
    "jjgg": ("reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz",
             "606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030", 9.436556),
}
REFERENCE_DIRS = {"bbgg": "reference_samples/pythia8/pp_bbgg_sm_lo_ps_13tev",
                  "ccgg": "reference_samples/pythia8/pp_ccgg_sm_lo_ps_13tev",
                  "jjgg": "reference_samples/pythia8/pp_jjgg_light_sm_lo_ps_13tev"}
IDENTITY_FIELDS = ("source_sample_id", "source_file_sha256", "source_event_index",
                   "source_event_content_hash", "pythia_run_id", "pythia_seed", "output_event_index")
WEIGHT_NAMES = ("input_contribution_pb", "LHE_XWGTUP_pb", "Pythia_Info_weight_pb")
BASELINE_SETTINGS_SHA256 = "53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389"


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def real(value):
    try:
        result = float(value)
    except (ValueError, TypeError) as error:
        raise ValidationError("invalid real: " + str(value)) from error
    require(math.isfinite(result), "non-finite value")
    return result


def integer(value):
    text = str(value)
    require(re.fullmatch(r"[+-]?\d+", text) is not None, "invalid integer: " + text)
    return int(text)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def valid_status(status):
    # Actual Pythia8.317 Particle::statusHepMC(): final=1, decay=2,
    # beam=4, otherwise valid negative generator status becomes 11..200.
    return status in {1, 2, 4} or 11 <= status <= 200


def unescape(value):
    require(re.search(r"\\(?![\\|])", value) is None, "unsupported HepMC string escape")
    return re.sub(r"\\([\\|])", lambda match: "\n" if match[1] == "|" else "\\", value)


def iter_ascii(path, *, max_decompressed_gb=100):
    """Yield (header/event/footer, exact bytes); never reserialize event data."""
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "HepMC input missing/symlink")
    require(math.isfinite(max_decompressed_gb) and max_decompressed_gb > 0, "invalid decompressed limit")
    total = 0
    header, event, footer = bytearray(), None, bytearray()
    started = ended = False
    stream = gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")
    try:
        with stream:
            while True:
                line = stream.readline(MAX_LINE + 1)
                if not line:
                    break
                total += len(line)
                require(total <= max_decompressed_gb * 1024**3, "HepMC decompressed size limit")
                require(len(line) <= MAX_LINE and line.endswith(b"\n"), "overlong/truncated ASCII line")
                require(b"\0" not in line and b"\r" not in line, "invalid ASCII control byte")
                if ended:
                    require(not line.strip(), "data after HepMC footer")
                    footer.extend(line)
                elif line == END:
                    require(started and event is not None, "no events or misplaced end marker")
                    yield "event", bytes(event)
                    event = None
                    footer.extend(line)
                    ended = True
                elif line.startswith(b"E "):
                    require(started, "event before start marker")
                    if event is None:
                        yield "header", bytes(header)
                    else:
                        yield "event", bytes(event)
                    event = bytearray(line)
                elif event is not None:
                    require(not line.startswith(b"HepMC"), "unexpected envelope inside event")
                    event.extend(line)
                    require(len(event) <= MAX_EVENT, "HepMC event exceeds 64 MiB")
                else:
                    if line == START:
                        require(not started and header.startswith(b"HepMC::Version "), "invalid start/version header")
                        started = True
                    elif line.startswith(b"HepMC"):
                        require(not header and re.fullmatch(rb"HepMC::Version 3\.\d+\.\d+\n", line), "invalid version header")
                    else:
                        require(started and line[:2] in {b"W ", b"T ", b"A "}, "unsupported run header record")
                    header.extend(line)
                    require(len(header) <= MAX_LINE, "HepMC run header exceeds 1 MiB")
            require(started and ended and event is None, "missing/truncated HepMC end marker")
            yield "footer", bytes(footer)
    except (OSError, EOFError) as error:
        raise ValidationError("gzip/file integrity failure: " + str(error)) from error


def parse_header(raw):
    lines = raw.decode("utf-8").splitlines()
    raw_version = lines[0].split()[1]
    version = ".".join(str(int(component)) for component in raw_version.split("."))
    weights, tools, attrs = None, [], {}
    for line in lines[2:]:
        if line.startswith("W "):
            require(weights is None, "duplicate run weight names")
            weights = unescape(line[2:]).splitlines()
            require(weights and len(set(weights)) == len(weights), "missing/duplicate weight names")
        elif line.startswith("T "):
            values = unescape(line[2:]).splitlines()
            require(len(values) >= 2 and values[0] and values[1], "invalid generator tool metadata")
            tools.append(values)
        elif line.startswith("A "):
            name, value = line[2:].split(" ", 1)
            require(name not in attrs, "duplicate run attribute")
            attrs[name] = unescape(value)
        else:
            raise ValidationError("invalid run metadata record")
    require(weights is not None and tuple(weights[:3]) == WEIGHT_NAMES, "nominal/raw/API weight-name contract mismatch")
    require(any(tool[0].lower().startswith("pythia") and tool[1] in {"8.317", "8.317000"} for tool in tools),
            "Pythia version/tool metadata missing")
    return {"hepmc3_version": version, "hepmc3_reported_version": raw_version,
            "weight_names": weights, "tools": tools, "attributes": attrs}


def parse_event(raw, header):
    lines = raw.decode("utf-8").splitlines()
    first = lines[0].split()
    require(len(first) in {4, 9} and first[0] == "E", "invalid E record")
    event_number, nvertices, nparticles = map(integer, first[1:4])
    require(event_number > 0 and nvertices > 0 and nparticles > 0, "invalid event numbers/counts")
    if len(first) == 9:
        require(first[4] == "@", "invalid event position")
        [real(value) for value in first[5:]]
    particles, explicit, attrs, weights, units = {}, {}, {}, None, None
    vertex_re = re.compile(r"V (-?\d+) ([+-]?\d+) \[([^]]*)\](?: @ (\S+) (\S+) (\S+) (\S+))?$")
    for line in lines[1:]:
        if line.startswith("U "):
            require(units is None and line == "U GEV MM", "missing/wrong/duplicate GeV/mm units")
            units = "GEV MM"
        elif line.startswith("W "):
            require(weights is None, "duplicate event weights")
            weights = [real(value) for value in line[2:].split()]
            require(len(weights) == len(header["weight_names"]), "weight-name/value count mismatch")
        elif line.startswith("A "):
            fields = line.split(" ", 3)
            require(len(fields) == 4, "invalid event attribute")
            owner = integer(fields[1])
            name, value = unescape(fields[2]), unescape(fields[3])
            require((owner, name) not in attrs, "duplicate event/particle/vertex attribute")
            attrs[owner, name] = value
        elif line.startswith("P "):
            row = line.split()
            require(len(row) == 10, "invalid particle record")
            pid, parent, pdg = map(integer, row[1:4])
            vector = [real(value) for value in row[4:9]]
            status = integer(row[9])
            require(pid > 0 and pid not in particles and pdg != 0 and abs(pdg) <= 2147483647 and
                    valid_status(status) and vector[3] >= 0, "invalid particle ID/PDG/status/energy")
            particles[pid] = {"parent": parent, "pdg": pdg, "p4": vector[:4], "mass": vector[4], "status": status}
        elif line.startswith("V "):
            match = vertex_re.fullmatch(line)
            require(match is not None, "invalid vertex record")
            vid, status = integer(match[1]), integer(match[2])
            incoming = [integer(value) for value in match[3].split(",")] if match[3] else []
            require(vid < 0 and vid not in explicit and incoming and len(set(incoming)) == len(incoming),
                    "invalid vertex ID/incoming links")
            if match[4] is not None:
                [real(value) for value in match.groups()[3:]]
            explicit[vid] = {"in": incoming, "out": [], "status": status}
        else:
            raise ValidationError("unsupported/empty event record")
    require(units is not None and weights is not None and len(particles) == nparticles, "incomplete event records/count")
    vertices = {("explicit", vid): vertex for vid, vertex in explicit.items()}
    for pid, particle in particles.items():
        parent = particle["parent"]
        if parent < 0:
            require(parent in explicit, "dangling explicit production vertex")
            vertices["explicit", parent]["out"].append(pid)
        elif parent > 0:
            require(parent in particles and parent != pid, "dangling/self implicit production parent")
            vertices.setdefault(("implicit", parent), {"in": [parent], "out": [], "status": 0})["out"].append(pid)
    require(len(vertices) == nvertices, "explicit/implicit vertex count mismatch")
    end = {}
    for key, vertex in vertices.items():
        require(vertex["out"], "dangling vertex with no descendants")
        for pid in vertex["in"]:
            require(pid in particles and pid not in end and pid not in vertex["out"], "dangling/duplicate/self end vertex")
            end[pid] = key
    for (owner, name), value in attrs.items():
        require(owner == 0 or owner in particles or owner in explicit, "attribute owner does not exist")
    beams, final = [], []
    for pid, particle in particles.items():
        if particle["status"] == 4:
            require(particle["pdg"] == 2212 and particle["parent"] == 0 and pid in end and
                    abs(particle["p4"][3] - 6500) <= 1e-6, "invalid proton beam record")
            beams.append(pid)
        else:
            require(particle["parent"] != 0, "orphan non-beam particle")
        if particle["status"] == 1:
            require(pid not in end, "stable final particle has an end vertex")
            final.append(pid)
        else:
            require(pid in end, "non-final particle has no end vertex")
    require(len(beams) == 2 and final, "missing full beams/stable final state")
    free_partons = sum(abs(particles[pid]["pdg"]) in {1, 2, 3, 4, 5, 6, 21} or
                       (1000 <= abs(particles[pid]["pdg"]) <= 9999 and abs(particles[pid]["pdg"]) // 10 % 10 == 0)
                       for pid in final)
    require(free_partons == 0, "incomplete baseline hadronization: stable free parton/diquark")
    incoming_p4 = [math.fsum(particles[pid]["p4"][component] for pid in beams) for component in range(4)]
    final_p4 = [math.fsum(particles[pid]["p4"][component] for pid in final) for component in range(4)]
    residual = max(abs(a - b) for a, b in zip(incoming_p4, final_p4))
    require(residual <= CLOSURE_ATOL_GEV + CLOSURE_RTOL * incoming_p4[3], "beam-to-stable four-momentum closure failure")
    remaining = {key: len(vertex["in"]) for key, vertex in vertices.items()}
    queue, visited = deque(beams), set()
    while queue:
        pid = queue.popleft()
        require(pid not in visited, "duplicate graph traversal")
        visited.add(pid)
        if pid in end:
            key = end[pid]
            remaining[key] -= 1
            if remaining[key] == 0:
                queue.extend(vertices[key]["out"])
    require(len(visited) == len(particles), "cycle/disconnected mother-descendant graph")
    identity = {name: attrs.get((0, name), "") for name in IDENTITY_FIELDS}
    require(all(identity.values()), "source identity attributes missing")
    for name in ("source_file_sha256", "source_event_content_hash"):
        require(re.fullmatch("[0-9a-f]{64}", identity[name]) is not None, "invalid source identity SHA256")
    require(integer(identity["source_event_index"]) > 0 and integer(identity["output_event_index"]) == event_number and
            1 <= integer(identity["pythia_seed"]) <= 900000000, "source/output index or seed mismatch")
    return {"event_number": event_number, "particles": len(particles), "vertices": len(vertices),
            "stable_particles": len(final), "stable_photons": sum(particles[pid]["pdg"] == 22 for pid in final),
            "weights": weights, "identity": identity, "beam_to_stable_residual_gev": residual,
            "source_total_events": integer(attrs.get((0, "source_total_events"), "0")),
            "stable_free_parton_count": free_partons,
            "event_hash": digest(raw), "particle_status_counts": Counter(p["status"] for p in particles.values())}


def ledger_rows(path):
    stream = gzip.open(path, "rt", encoding="utf-8") if Path(path).suffix == ".gz" else Path(path).open(encoding="utf-8")
    try:
        with stream:
            for line in stream:
                require(len(line) <= MAX_LINE and line.endswith("\n"), "overlong/truncated source ledger row")
                row = json.loads(line)
                require(isinstance(row, dict), "source ledger row is not an object")
                yield row
    except (OSError, EOFError, json.JSONDecodeError) as error:
        raise ValidationError("source ledger integrity failure: " + str(error)) from error


def ledger_weight_vector(row, expected_source_events=None):
    """Check actual runner columns, preserving their signed nominal values."""
    fields = {"nominal_generator_weight", "lhe_weight_pb", "pythia_weight_pb", "input_contribution_pb",
              "source_total_events", "converter_weights_pb"}
    require(fields <= row.keys(), "required actual-schema ledger weight fields missing")
    raw, lhe, py, contribution = (real(row[name]) for name in
                                  ("nominal_generator_weight", "lhe_weight_pb", "pythia_weight_pb", "input_contribution_pb"))
    denominator = integer(row["source_total_events"])
    require(denominator > 0 and (expected_source_events is None or denominator == expected_source_events),
            "full original source normalization denominator mismatch")
    converters = row["converter_weights_pb"]
    require(isinstance(converters, list) and 0 < len(converters) <= 256, "missing/unbounded converter weight vector")
    converters = [real(value) for value in converters]
    close = lambda a, b: math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)
    require(close(lhe, raw) and close(py, raw) and close(converters[0], raw),
            "original LHE/Pythia/converter nominal ledger weights disagree")
    require(close(contribution, raw / denominator), "per-input nominal contribution normalization mismatch")
    return [contribution, lhe, py, *converters]


def validate_file(path, expected_events=None, *, ledger=None, source_file=None, source_sha256=None,
                  sample_id=None, pythia_seed=None, require_deterministic=True, max_decompressed_gb=100):
    path = Path(path)
    size = path.stat().st_size
    if path.suffix == ".gz" and require_deterministic:
        with path.open("rb") as stream:
            signature = stream.read(18)
        require(signature[:3] == b"\x1f\x8b\x08" and signature[4:8] == b"\0" * 4 and not signature[3] & 8,
                "published gzip requires deterministic mtime=0/no filename")
    source_events = None
    if source_file is not None:
        actual_source_hash = file_sha256(source_file)
        require(source_sha256 is None or source_sha256 == actual_source_hash, "original MG5 source file hash mismatch")
        source_sha256 = actual_source_hash
        source_events = sum(1 for _ in iter_lhe_events(source_file))
    rows = iter(ledger_rows(ledger)) if ledger is not None else None
    sources = iter(iter_lhe_events(source_file)) if source_file is not None else None
    source_cache, last_source_index = None, 0
    processed_rows = written_rows = failures = 0
    header, count = None, 0
    decompressed, events = hashlib.sha256(), hashlib.sha256()
    weights_moments = []
    particles = vertices = stable = photons = 0
    max_residual, status_counts, photon_hist = 0.0, Counter(), Counter()
    common_run = common_source = common_sample = common_seed = None
    common_denominator = None
    event_hashes = hashlib.sha256()
    def next_written():
        nonlocal processed_rows, written_rows, failures, last_source_index, source_cache
        for row in rows:
            processed_rows += 1
            require(set(IDENTITY_FIELDS) | {"processing_status", "output_event_hash", "nominal_generator_weight", "weight_interpretation"} <= row.keys(),
                    "required source ledger fields missing")
            index = integer(row["source_event_index"])
            require(index == last_source_index + 1, "source ledger index duplicate/gap/out-of-order")
            last_source_index = index
            require(real(row["nominal_generator_weight"]) == real(row["nominal_generator_weight"]) and row["weight_interpretation"],
                    "invalid source ledger nominal weight/interpretation")
            if source_sha256 is not None:
                require(row["source_file_sha256"] == source_sha256, "ledger source file mismatch")
            if sample_id is not None:
                require(row["source_sample_id"] == sample_id, "ledger source sample mismatch")
            if sources is not None:
                source_cache = next(sources, None)
                require(source_cache is not None and source_cache["source_event_index"] == index and
                        source_cache["source_event_content_hash"] == row["source_event_content_hash"] and
                        math.isclose(source_cache["nominal_generator_weight"], real(row["nominal_generator_weight"]), rel_tol=1e-12),
                        "ledger does not match original indexed LHE event")
            if row["processing_status"] == "WRITTEN":
                written_rows += 1
                return row
            require(row["output_event_index"] is None and row["output_event_hash"] is None,
                    "failed source input unexpectedly linked to output")
            failures += 1
        return None
    for kind, raw in iter_ascii(path, max_decompressed_gb=max_decompressed_gb):
        decompressed.update(raw)
        if kind == "header":
            header = parse_header(raw)
            weights_moments = [[0.0, 0.0, 0.0, 0, 0, 0] for _ in header["weight_names"]]
        elif kind == "event":
            require(header is not None, "run header missing")
            count += 1
            record = parse_event(raw, header)
            require(record["event_number"] == count, "output event index duplicate/gap/out-of-order")
            identity = record["identity"]
            if common_run is None:
                common_run, common_source = identity["pythia_run_id"], identity["source_file_sha256"]
                common_sample, common_seed = identity["source_sample_id"], identity["pythia_seed"]
                common_denominator = record["source_total_events"]
            require(identity["pythia_run_id"] == common_run and identity["source_file_sha256"] == common_source and
                    identity["source_sample_id"] == common_sample and identity["pythia_seed"] == common_seed and
                    record["source_total_events"] == common_denominator,
                    "mixed run/source/sample/seed/denominator identities in one event stream")
            if source_sha256 is not None:
                require(identity["source_file_sha256"] == source_sha256, "event source file identity mismatch")
            if sample_id is not None:
                require(identity["source_sample_id"] == sample_id, "event source sample identity mismatch")
            if pythia_seed is not None:
                require(integer(identity["pythia_seed"]) == pythia_seed, "event random seed identity mismatch")
            if rows is not None:
                row = next_written()
                require(row is not None, "output event missing source ledger mapping")
                for key in IDENTITY_FIELDS:
                    require(str(row[key]) == identity[key], "output/ledger identity mismatch: " + key)
                require(row["output_event_hash"] == record["event_hash"], "exact output event hash mismatch")
                expected_weights = ledger_weight_vector(row, source_events)
                require(record["source_total_events"] == integer(row["source_total_events"]),
                        "HepMC/ledger full original source count mismatch")
                require(len(record["weights"]) == len(expected_weights) and
                        all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15) for a, b in zip(record["weights"], expected_weights)),
                        "HepMC/actual-schema ledger stored weight vector mismatch")
                if "hepmc_weights" in row:
                    require(len(row["hepmc_weights"]) == len(record["weights"]) and
                            all(math.isclose(real(a), b, rel_tol=1e-12, abs_tol=1e-15) for a, b in zip(row["hepmc_weights"], record["weights"])),
                            "HepMC/ledger stored weight vector mismatch")
            for value, moments in zip(record["weights"], weights_moments):
                moments[0] += value
                moments[1] += abs(value)
                moments[2] += value * value
                moments[3 if value > 0 else 4 if value < 0 else 5] += 1
                require(all(math.isfinite(moment) for moment in moments[:3]), "non-finite/overflowing stored weight moments")
            particles += record["particles"]
            vertices += record["vertices"]
            stable += record["stable_particles"]
            photons += record["stable_photons"]
            photon_hist[record["stable_photons"]] += 1
            status_counts.update(record["particle_status_counts"])
            max_residual = max(max_residual, record["beam_to_stable_residual_gev"])
            events.update(raw)
            event_hashes.update(bytes.fromhex(record["event_hash"]))
    require(count > 0 and (expected_events is None or count == expected_events), "actual HepMC event count mismatch")
    if rows is not None:
        require(next_written() is None, "source ledger contains unmapped written output")
        require(written_rows == count, "source ledger/output count mismatch")
    return {"validation_status": "PASS", "format_validation_status": "PASS", "validator": "portable_ASCII_graph_and_source_integrity",
            "physical_library_readback": "NOT_EVALUATED_BY_PYTHON", "actual_events": count, "N_readback": count,
            "hepmc3_version": header["hepmc3_version"], "weight_names": header["weight_names"],
            "weight_moments_by_name": {name: dict(zip(("sum", "sum_abs", "sum_squared", "positive", "negative", "zero"), moments))
                                       for name, moments in zip(header["weight_names"], weights_moments)},
            "compressed_file_sha256": file_sha256(path), "compressed_bytes": size,
            "decompressed_file_sha256": decompressed.hexdigest(), "event_content_sha256": events.hexdigest(),
            "ordered_event_hashes_sha256": event_hashes.hexdigest(), "total_particles": particles, "total_vertices": vertices,
            "mean_final_multiplicity": stable / count, "mean_final_photons": photons / count,
            "final_photon_multiplicity_histogram": dict(photon_hist), "particle_status_counts": dict(status_counts),
            "max_beam_to_stable_residual_gev": max_residual, "closure_atol_gev": CLOSURE_ATOL_GEV, "closure_rtol": CLOSURE_RTOL,
            "stable_free_parton_count": 0,
            "ledger_rows": processed_rows, "ledger_failed_inputs": failures,
            "source_total_events": common_denominator,
            "per_event_weight_accounting": "PASS" if rows is not None else "NOT_EVALUATED_NO_LEDGER",
            "event_identity": "PASS" if rows is not None and sources is not None else "ATTRIBUTES_ONLY",
            "source_file_sha256": common_source, "pythia_run_id": common_run}


def safe_file(repo, relative):
    require(isinstance(relative, str) and not Path(relative).is_absolute(), "manifest paths must be relative")
    path = repo / relative
    require(path.resolve().is_relative_to(repo.resolve()) and path.is_file() and not path.is_symlink(), "manifest file missing/escape/symlink")
    return path


def validate_full_ledger(path, source, source_hash, process, seed, run_id):
    """Published reference evidence is bounded to exactly 1000 original rows."""
    require(path.stat().st_size <= 5 * 1024**2, "full reference ledger exceeds bounded evidence policy")
    raw_lines = path.read_bytes().splitlines(keepends=True)
    require(len(raw_lines) == 1000 and all(line.endswith(b"\n") for line in raw_lines),
            "full reference ledger requires 1000 complete rows")
    source_rows = iter(iter_lhe_events(source))
    for index, raw in enumerate(raw_lines, 1):
        row = json.loads(raw)
        original = next(source_rows, None)
        require(original is not None and row["source_event_index"] == row["output_event_index"] == index and
                row["processing_status"] == "WRITTEN", "full reference ledger contains input gaps/failures")
        require(row["source_sample_id"] == process and row["source_file_sha256"] == source_hash and
                row["pythia_seed"] == seed and row["pythia_run_id"] == run_id and
                row["source_event_content_hash"] == original["source_event_content_hash"],
                "full ledger/source/run identity mismatch")
        require(re.fullmatch("[0-9a-f]{64}", row["output_event_hash"]) is not None, "full ledger output hash missing")
        raw_weight = real(row["nominal_generator_weight"])
        require(math.isclose(raw_weight, original["nominal_generator_weight"], rel_tol=1e-12),
                "full ledger original nominal weight mismatch")
        expected = ledger_weight_vector(row, 1000)
        if "hepmc_weights" in row:
            require(len(row["hepmc_weights"]) >= 4 and
                    all(math.isclose(real(a), b, rel_tol=1e-12, abs_tol=1e-15) for a, b in zip(row["hepmc_weights"], expected)),
                    "full ledger nominal/API weight normalization mismatch")
    require(next(source_rows, None) is None, "full source contains unaccounted events")
    return raw_lines


def validate_repository(repo):
    repo = Path(repo).resolve()
    results, full_total = [], 0
    canonical_settings = safe_file(repo, "simulation/pythia8/config/baseline_shower.cmnd")
    require(file_sha256(canonical_settings) == BASELINE_SETTINGS_SHA256, "reviewed canonical shower settings changed")
    for process, relative_dir in REFERENCE_DIRS.items():
        directory = repo / relative_dir
        manifest = json.loads((directory / "sample_manifest.json").read_text(encoding="utf-8"))
        require(manifest.get("schema_version") == 1 and isinstance(manifest.get("samples"), list), "unsupported shower manifest schema")
        samples = manifest["samples"]
        require(len(samples) in {1, 2} and {item["sample_id"] for item in samples} in
                ({"shower_100"}, {"shower_100", "shower_1000"}), "required real shower references missing")
        source_path, source_hash, source_xsec = SOURCE_SAMPLES[process]
        source = safe_file(repo, source_path)
        require(file_sha256(source) == source_hash, "original published MG5 source hash changed")
        for sample in samples:
            expected_count = 100 if sample["sample_id"] == "shower_100" else 1000
            require(sample["file"] == relative_dir + "/" + sample["sample_id"] + ".hepmc3.gz" and
                    sample["events"] == expected_count and sample["source_sample_id"] == process,
                    "reference path/count/process mismatch")
            require(sample["source_file"] == source_path and sample["source_file_sha256"] == source_hash and
                    sample["input_count"] == sample["full_run_events"] == 1000 and
                    math.isclose(real(sample["input_xsec_pb"]), source_xsec, rel_tol=1e-12), "reference source/normalization mismatch")
            require(sample["pythia_version"] == "8.317" and sample["hepmc3_version"] == "3.3.1", "reference generator versions mismatch")
            require(sample["validation_status"] == "PASS", "reference not independently validated")
            lhe_ledger = safe_file(repo, sample["ledger_path"])
            require(file_sha256(lhe_ledger) == sample["ledger_sha256"], "source ledger hash mismatch")
            settings = safe_file(repo, sample["settings_path"])
            require(file_sha256(settings) == sample["settings_sha256"] == BASELINE_SETTINGS_SHA256,
                    "reviewed shower settings hash mismatch")
            cpp_path = safe_file(repo, sample["cpp_report_path"])
            require(file_sha256(cpp_path) == sample["cpp_report_sha256"], "physical library report hash mismatch")
            cpp = json.loads(cpp_path.read_text(encoding="utf-8"))
            require(cpp["validation_status"] == "PASS" and
                    cpp["N_requested_validation"] == cpp["N_readback"] == cpp["N_passed_validation"] ==
                    cpp["N_events_with_complete_physics_assessment"] == 1000 and
                    cpp["N_failed_validation"] == cpp["N_not_assessed"] == 0 and
                    cpp["validator"] == "actual_HepMC3_ReaderAscii_and_Pythia_ParticleData", "actual full-run HepMC3 readback evidence missing")
            require(cpp["fatal_error"] is None and cpp["mass_shell_failed_particle_count"] == 0 and
                    cpp["failure_detail_count"] == 0 and not cpp["failures"] and
                    cpp["stable_colored_particle_count"] == cpp["stable_free_quark_count"] ==
                    cpp["stable_free_gluon_count"] == cpp["stable_free_diquark_count"] == 0,
                    "physical library report contains invalid or unassessed particles")
            require(math.isclose(real(cpp["mass_shell_atol_gev2"]), 1e-7, rel_tol=1e-12) and
                    math.isclose(real(cpp["mass_shell_rtol_energy_squared"]), 1e-9, rel_tol=1e-12) and
                    math.isclose(real(cpp["closure_atol_gev"]), CLOSURE_ATOL_GEV, rel_tol=1e-12) and
                    math.isclose(real(cpp["closure_rtol"]), CLOSURE_RTOL, rel_tol=1e-12) and
                    0 <= real(cpp["max_stable_mass_shell_residual_to_tolerance"]) <= 1 and
                    0 <= real(cpp["max_beam_to_stable_residual_gev"]) <= CLOSURE_ATOL_GEV + CLOSURE_RTOL * 13000,
                    "physical library report does not satisfy the unchanged strict numerical gates")
            require(".".join(str(int(component)) for component in cpp["hepmc3_version"].split(".")) == "3.3.1" and
                    cpp["pythia_version"] == "8.317" and cpp["source_file_sha256"] == source_hash and
                    cpp["source_sample_id"] == process and cpp["pythia_seed"] == sample["pythia_seed"],
                    "physical library report version/source/seed correspondence mismatch")
            path = safe_file(repo, sample["file"])
            require(path.stat().st_size <= 10 * 1024**2, "published HepMC reference exceeds 10 MiB")
            if expected_count == 1000:
                full_total += path.stat().st_size
            result = validate_file(path, expected_count, ledger=lhe_ledger, source_file=source, source_sha256=source_hash,
                                   sample_id=process, pythia_seed=sample["pythia_seed"])
            for key in ("compressed_file_sha256", "decompressed_file_sha256", "event_content_sha256"):
                require(sample[key] == result[key], "shower manifest hash mismatch: " + key)
            require(result["event_identity"] == "PASS" and result["ledger_failed_inputs"] == 0, "published source mapping incomplete")
            subset = sample["subset_of_full_run"]
            require(subset["events"] == 1000 and re.fullmatch(r"[0-9a-f]{64}", subset["decompressed_file_sha256"]), "full-run subset provenance missing")
            require(cpp["decompressed_file_sha256"] == subset["decompressed_file_sha256"] and
                    cpp["pythia_run_id"] == result["pythia_run_id"], "physical library report is for a different full output/run")
            full_ledger = safe_file(repo, sample["full_run_ledger_path"])
            require(full_ledger.stat().st_size == sample["full_run_ledger_bytes"] and
                    file_sha256(full_ledger) == sample["full_run_ledger_sha256"], "full reference ledger hash/size mismatch")
            full_lines = validate_full_ledger(full_ledger, source, source_hash, process, sample["pythia_seed"], result["pythia_run_id"])
            selected_lines = lhe_ledger.read_bytes().splitlines(keepends=True)
            numbers = subset["selected_event_numbers"]
            require(numbers == list(range(1, expected_count + 1)) and
                    selected_lines == [full_lines[number - 1] for number in numbers],
                    "selected source ledger is not an exact raw prefix of the validated full-run ledger")
            if expected_count == 1000:
                require(subset["decompressed_file_sha256"] == result["decompressed_file_sha256"], "full-run hash correspondence mismatch")
            nominal = result["weight_moments_by_name"]["input_contribution_pb"]["sum"]
            require(math.isclose(nominal, source_xsec * expected_count / 1000, rel_tol=1e-7, abs_tol=1e-12),
                    "per-input cross-section contribution counted incorrectly")
            results.append({"process": process, "sample_id": sample["sample_id"], **result})
    require(full_total <= 30 * 1024**2, "total full HepMC references exceed 30 MiB")
    return {"status": "PASS", "samples": results, "full_compressed_payload_bytes": full_total,
            "physical_validation_basis": "Separate committed actual C++ ReaderAscii reports; Python checks portable integrity"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--events", type=int)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--source-sha256")
    parser.add_argument("--sample-id")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--generator-original", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--max-decompressed-gb", type=float, default=100)
    args = parser.parse_args()
    try:
        require(bool(args.repository) != bool(args.file), "choose --repository or --file")
        result = validate_repository(args.repository) if args.repository else validate_file(
            args.file, args.events, ledger=args.ledger, source_file=args.source_file, source_sha256=args.source_sha256,
            sample_id=args.sample_id, pythia_seed=args.seed, require_deterministic=not args.generator_original,
            max_decompressed_gb=args.max_decompressed_gb)
        output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.report:
            args.report.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0
    except (ValidationError, OSError, KeyError, ValueError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

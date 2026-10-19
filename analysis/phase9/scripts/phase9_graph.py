#!/usr/bin/env python3
"""Read-only Phase9 graph adapters; reuse the validated historical byte parsers."""
from __future__ import annotations
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'simulation/pythia8/scripts'))
from validate_hepmc3 import iter_ascii
from validate_lhe_stream import iter_lhe_events
_spec = importlib.util.spec_from_file_location('phase9_historical_source997', REPO / 'simulation/heavy_flavour_forensics/scripts/source997.py')
historical = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(historical)
require = historical.require
ancestors = historical.ancestors
audit_graph = historical.audit_graph
eta_phi = historical.eta_phi
delta_r = historical.delta_r


def retain_native_particle_attributes(graph, raw):
    """Read explicitly serialized converter identities; never invent status flags."""
    retained = {}
    names = {'original_pythia_status', 'original_pythia_is_hadron', 'original_pythia_index'}
    for line in raw.decode('utf-8').splitlines():
        fields = line.split(' ', 3)
        if len(fields) != 4 or fields[0] != 'A' or fields[2] not in names:
            continue
        pid = int(fields[1])
        require(pid > 0 and pid in graph['particles'], 'dangling original particle identity attribute')
        name = fields[2]
        values = retained.setdefault(pid, {})
        require(name not in values, 'duplicate original particle identity attribute')
        values[name] = int(fields[3])
    if retained:
        require(set(retained) == set(graph['particles']), 'partial original particle identity attributes')
        require(all(set(v) == names for v in retained.values()), 'incomplete original particle identity tuple')
        indices = [v['original_pythia_index'] for v in retained.values()]
        require(all(i > 0 for i in indices) and len(set(indices)) == len(indices), 'duplicate original Pythia identities')
        for pid, values in retained.items():
            require(values['original_pythia_is_hadron'] in (0, 1), 'invalid original hadron flag')
            row = graph['particles'][pid]
            row['original_pythia_status'] = values['original_pythia_status']
            row['is_hadron'] = bool(values['original_pythia_is_hadron'])
            row['original_pythia_index'] = values['original_pythia_index']
        graph['original_pythia_attributes_status'] = 'COMPLETE_NATIVE_SERIALIZED_IDENTITY'
    else:
        graph['original_pythia_attributes_status'] = 'NOT_SERIALIZED'
    return graph


def iter_hepmc(path):
    """Exact event bytes and native graph IDs; no ordinal/barcode equivalence."""
    for kind, raw in iter_ascii(path, max_decompressed_gb=4):
        if kind != 'event':
            continue
        graph = retain_native_particle_attributes(historical.parse_hepmc(raw), raw)
        require(audit_graph(graph['particles'])['status'] == 'PASS', 'invalid HepMC ancestry graph')
        yield graph


def iter_lhe(path):
    for event in iter_lhe_events(path):
        rows = event['rows']
        n = int(rows[0][0])
        require(n > 0 and len(rows) >= n + 1, 'invalid LHE particle count')
        particles = []
        for index, row in enumerate(rows[1:n + 1], 1):
            require(len(row) == 13, 'invalid LHE particle row')
            p4 = [float(x.replace('D', 'E').replace('d', 'e')) for x in row[6:10]]
            mass = float(row[10].replace('D', 'E').replace('d', 'e'))
            require(all(math.isfinite(x) for x in (*p4, mass)), 'nonfinite LHE p4')
            particles.append(dict(index=index, pdg_id=int(row[0]), status=int(row[1]),
                                  mother1=int(row[2]), mother2=int(row[3]), p4_gev=p4, mass_gev=mass))
        yield dict(source_event_index=event['source_event_index'],
                   source_event_sha256=event['source_event_content_hash'],
                   raw_weight=str(event['nominal_generator_weight']), particles=particles)


def iter_jsonl(path):
    with Path(path).open('rb') as stream:
        for raw in stream:
            require(len(raw) <= 16 * 1024**2, 'oversized diagnostic JSON row')
            yield json.loads(raw)


def enrich_with_pythia(graph, diagnostic):
    """Recover original flags only through the historical exact tuple bijection."""
    pygraph = historical.pythia_graph(diagnostic['particles'])
    require(audit_graph(pygraph)['status'] == 'PASS', 'invalid original Pythia graph')
    mapping = historical.match_pythia_hepmc(pygraph, graph['particles'])
    require(not mapping['mother_edge_differences'], 'Pythia/HepMC mapped mother graph differs')
    unique = {pid: row['hepmc_ids'][0] for pid, row in mapping['particles'].items()
              if row['status'] == 'UNIQUE_TUPLE_MATCH'}
    require(len(set(unique.values())) == len(unique), 'noninjective exact tuple mapping')
    for pid, hid in unique.items():
        source = pygraph[pid]
        for name in ('is_hadron', 'terminal_b_hadron', 'terminal_c_hadron'):
            graph['particles'][hid][name] = source[name]
        graph['particles'][hid]['original_pythia_status'] = source['status']
    roots = diagnostic.get('hard_photon_roots', [])
    graph['hard_photon_roots'] = [unique[x] for x in roots if x in unique]
    graph['hard_photon_roots_unmapped'] = [x for x in roots if x not in unique]
    graph['pythia_mapping'] = dict(unique_matches=len(unique), total_pythia=len(pygraph),
                                  ambiguous_or_missing=mapping['ambiguous_or_missing'])
    return pygraph


def hard_match(lhe_particles, graph_particles):
    """Conservative diagnostic only; Pythia mass projection can change hard p4.

    A match requires signed PID and a unique binary64-close p4 tuple. Failure
    stays unavailable; this is never an assumed LHE/Pythia ordinal mapping.
    """
    result = {}
    for source in lhe_particles:
        candidates = [pid for pid, particle in graph_particles.items()
                      if particle['pdg_id'] == source['pdg_id'] and
                      abs(particle.get('original_pythia_status', particle['status'])) in (22, 23) and
                      all(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-7)
                          for a, b in zip(source['p4_gev'], particle['p4_gev']))]
        result[source['index']] = dict(status='UNIQUE_KINEMATIC_DIAGNOSTIC' if len(candidates) == 1
                                      else 'UNAVAILABLE_OR_AMBIGUOUS', graph_ids=candidates)
    return result
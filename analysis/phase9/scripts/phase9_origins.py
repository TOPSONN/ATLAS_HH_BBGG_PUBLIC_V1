#!/usr/bin/env python3
"""Stream existing source graphs once, join freshly read native objects exactly."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
from phase9_graph import (REPO, enrich_with_pythia, iter_hepmc, iter_jsonl, iter_lhe, require)
from phase9_heavy_flavour import (OVERLAP_STATUS, classify_heavy_flavour, event_flags as hf_flags, summarize_indicator)
from phase9_photon import classify_photons, event_flags as photon_flags, object_counts as photon_objects

STAGES = ('00_INPUT', '01_TWO_PHOTONS', '02_TWO_JETS', '03_TWO_BTAGS', '04_MGG_105_160')
HF_IDS = {'B01': 'bbgg', 'B02': 'ccgg', 'B03': 'jjgg'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_file(path, expected):
    require(Path(path).is_file() and not Path(path).is_symlink(), 'missing/symlink original input')
    require(sha(path) == expected, 'original file hash mismatch: ' + str(path))


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    require(rows and keys, 'no CSV evidence')
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ('' if v is None else v) for k, v in row.items()})


def continuum_streams(dataset):
    directory = Path('/home/btu/simulations/pythia8_runs') / (HF_IDS[dataset['dataset_id']] + '_1k')
    manifest = json.loads((directory / 'run_manifest.json').read_text())
    require(manifest['status'] == 'PASS' and manifest['events_requested'] == dataset['N_original'], 'unverified original shower run')
    require(manifest['source_file_sha256'] == dataset['lhe_sha256'], 'original shower wrong LHE source')
    paths = [directory / name for name in ('particle_diagnostics.jsonl', 'event_ledger.jsonl', 'source_events.jsonl')]
    for path in paths:
        verify_file(path, manifest['files'][path.name]['sha256'])
    return [iter_jsonl(path) for path in paths]


def prepare_decay_lineage(graph):
    raw = graph['attributes'].get('background_decay_lineage')
    if raw is None:
        return
    lineage = json.loads(raw)
    require('Native graph IDs' in lineage.get('mapping_scope', ''), 'lineage lacks native graph binding')
    ids = list(lineage.get('higgs_photon_birth_ids', []))
    born = lineage.get('Born_photon_root', 0)
    if born:
        ids.append(born)
    require(all(pid in graph['particles'] and graph['particles'][pid]['pdg_id'] == 22 for pid in ids), 'invalid decay-lineage photon IDs')
    graph['hard_photon_roots'] = sorted(set(ids))
    graph['hard_photon_roots_status'] = 'VERIFIED_SOURCE_LEDGER_OR_DECAY_LINEAGE'
    graph['background_decay_lineage'] = lineage


def classified_events(dataset, native_rows):
    extra = continuum_streams(dataset) if dataset['dataset_id'] in HF_IDS else None
    streams = [iter_lhe(dataset['lhe_path']), iter_hepmc(dataset['hepmc_path']), iter(native_rows)]
    if extra:
        streams.extend(extra)
    n = 0
    for combined in itertools.zip_longest(*streams):
        require(all(row is not None for row in combined), 'incomplete/misaligned full original cohort')
        lhe, graph, reco = combined[:3]
        n += 1
        require(lhe['source_event_index'] == n == reco['source_event_ordinal'], 'nonordinal or duplicate source join')
        require(reco['source_event_sha256'] == lhe['source_event_sha256'] == graph['attributes'].get('source_event_content_hash'), 'hard event identity mismatch')
        require(int(graph['attributes']['source_event_index']) == n and graph['event_number'] == reco['native_event_number'], 'HepMC/native event identity mismatch')
        require(graph['exact_event_sha256'] == reco['hepmc_event_sha256'], 'native input HepMC byte identity mismatch')
        require(int(graph['attributes']['source_total_events']) == dataset['N_original'] == reco['N_original'], 'wrong source denominator')
        expected_weight = Decimal(lhe['raw_weight']) / dataset['N_original']
        require(abs(Decimal(str(reco['source_weight_pb'])) - expected_weight) <= max(Decimal('1e-18'), abs(expected_weight)*Decimal('2e-15')), 'source weight applied incorrectly')
        pygraph = None
        if extra:
            diagnostic, ledger, source = combined[3:]
            require(diagnostic['source_event_index'] == diagnostic['output_event_index'] == ledger['source_event_index'] == source['source_event_index'] == n, 'original diagnostics ordinal mismatch')
            require(ledger['processing_status'] == 'WRITTEN' and ledger['source_event_content_hash'] == source['source_event_content_hash'] == lhe['source_event_sha256'], 'original diagnostics wrong hard identity')
            require(ledger['output_event_hash'] == graph['exact_event_sha256'], 'original shower ledger wrong HepMC event')
            require(ledger['source_total_events'] == dataset['N_original'], 'wrong ledger denominator')
            pygraph = enrich_with_pythia(graph, diagnostic)
            graph['hard_photon_roots_status'] = 'VERIFIED_SOURCE_LEDGER_OR_DECAY_LINEAGE'
            graph['hard_photon_roots_complete'] = not graph['hard_photon_roots_unmapped']
        else:
            prepare_decay_lineage(graph)
        hf = classify_heavy_flavour(graph, reco, lhe, pygraph) if pygraph is not None else None
        photons = classify_photons(graph, reco, lhe)
        yield dict(dataset_id=dataset['dataset_id'], source_event_index=n,
                   source_event_sha256=lhe['source_event_sha256'], hepmc_event_sha256=graph['exact_event_sha256'],
                   weight_pb=reco['source_weight_pb'], model_br_factor=dataset['model_br_factor'], stages=reco['stages'],
                   heavy_flavour=hf, photon_origin=photons, observables=reco['observables'],
                   pythia_mapping=graph.get('pythia_mapping'),
                   hard_outgoing_pdg_ids=[p['pdg_id'] for p in lhe['particles'] if p['status'] == 1])
    require(n == dataset['N_original'], 'full source cohort count mismatch')


def conditional_origin_fraction(events, values, stage_index):
    count = sum(e['stages'][stage_index] for e in events)
    selected = sum(values)
    denominator = math.fsum(e['weight_pb'] for e in events if e['stages'][stage_index])
    numerator = math.fsum(e['weight_pb'] for e,v in zip(events,values) if v)
    ratio = numerator/denominator if denominator else None
    variance = None
    if denominator:
        residuals = [e['weight_pb']*(int(v)-ratio*int(e['stages'][stage_index])) for e,v in zip(events,values)]
        mean = math.fsum(residuals)/len(events)
        variance = len(events)/(len(events)-1)*math.fsum((x-mean)**2 for x in residuals)/denominator**2
    z = 1.959963984540054
    if count:
        d = 1+z*z/count
        c = (selected/count+z*z/(2*count))/d
        h = z*math.sqrt((selected/count)*(1-selected/count)/count+z*z/(4*count*count))/d
    else:
        c=h=None
    return dict(stage_event_denominator=count, stage_weight_denominator_pb=denominator,
                within_stage_event_fraction=selected/count if count else None,
                within_stage_wilson95_low=c-h if count else None,
                within_stage_wilson95_high=c+h if count else None,
                weighted_within_stage_fraction=ratio,
                weighted_within_stage_fraction_event_cluster_se=math.sqrt(variance) if variance is not None else None,
                conditional_fraction_scope='SHARED_SOURCE_EVENT_NUMERATOR_DENOMINATOR_DESCRIPTIVE')


def aggregate(events, kind):
    rows = []
    indicators = [hf_flags(e['heavy_flavour']) if kind == 'heavy_flavour' else photon_flags(e['photon_origin']) for e in events]
    categories = sorted(set().union(*(set(flags) for flags in indicators)))
    for stage_index, stage in enumerate(STAGES):
        weights = [e['weight_pb'] for e in events]
        for category in categories:
            values = [e['stages'][stage_index] and flags.get(category, False) for e, flags in zip(events, indicators)]
            rows.append(dict(dataset_id=events[0]['dataset_id'], stage=stage, category=category,
                             evidence_class='ACTUAL_EXISTING_DATA_READBACK', weight_scope='RAW_SOURCE_PB_NO_NEW_NORMALIZATION',
                             classification_unit='SOURCE_EVENT_INDICATOR_NONEXCLUSIVE_ORIGIN_FLAGS',
                             **summarize_indicator(values, weights),
                             **conditional_origin_fraction(events,values,stage_index)))
    return rows


def aggregate_photon_objects(events):
    rows = []
    objects = [photon_objects(e['photon_origin']) for e in events]
    categories = sorted(set().union(*(set(x) for x in objects)))
    n = len(events)
    for stage_index, stage in enumerate(STAGES):
        for category in categories:
            counts = [obj[category] if e['stages'][stage_index] else 0 for obj,e in zip(objects,events)]
            stats = summarize_indicator([x > 0 for x in counts], [e['weight_pb'] for e in events])
            xs = [x*e['weight_pb'] for x,e in zip(counts,events)]
            total = math.fsum(xs); mean = total/n
            variance = n/(n-1)*math.fsum((x-mean)**2 for x in xs)
            rows.append(dict(dataset_id=events[0]['dataset_id'], stage=stage, category=category,
                             classification_unit='SOURCE_EVENT_HAS_MATCHING_PHOTON_ORIGIN_OBJECT',
                             evidence_class='ACTUAL_EXISTING_DATA_READBACK',
                             object_count=sum(counts), weighted_object_multiplicity_pb=total,
                             object_multiplicity_event_correlated_variance_pb2=variance,
                             fake_rate_interpretation='NOT_A_CALIBRATED_FAKE_RATE', **stats))
    return rows


def object_composition(events):
    rows = []
    for stage_index, stage in enumerate(STAGES):
        categories = sorted({f"HARD_{j['hard_cone_flavour']}_SHOWER_{j['shower_record_cone_flavour']}_HADRON_{j['heavy_hadron_flavour']}_NATIVE_{j['native_flavour']}_TAG_{int(j['tagged'])}"
                             for e in events for j in e['heavy_flavour']['jets']})
        for category in categories:
            counts = []
            for event in events:
                n = sum(f"HARD_{j['hard_cone_flavour']}_SHOWER_{j['shower_record_cone_flavour']}_HADRON_{j['heavy_hadron_flavour']}_NATIVE_{j['native_flavour']}_TAG_{int(j['tagged'])}" == category for j in event['heavy_flavour']['jets']) if event['stages'][stage_index] else 0
                counts.append(n)
            stats = summarize_indicator([n > 0 for n in counts], [e['weight_pb'] for e in events])
            xs = [n*e['weight_pb'] for n, e in zip(counts, events)]
            total = math.fsum(xs)
            mean = total/len(events)
            var = len(events)/(len(events)-1)*math.fsum((x-mean)**2 for x in xs)
            all_jet_counts = [len(e['heavy_flavour']['jets']) if e['stages'][stage_index] else 0 for e in events]
            denominator = math.fsum(n*e['weight_pb'] for n, e in zip(all_jet_counts, events))
            fraction = total/denominator if denominator else None
            if denominator:
                residuals = [e['weight_pb']*(a-fraction*b) for a,b,e in zip(counts,all_jet_counts,events)]
                centred = math.fsum(residuals)/len(events)
                ratio_var = len(events)/(len(events)-1)*math.fsum((x-centred)**2 for x in residuals)/denominator**2
            else:
                ratio_var = None
            rows.append(dict(dataset_id=events[0]['dataset_id'], stage=stage, category=category,
                             eligible_jet_denominator=sum(all_jet_counts), weighted_jet_denominator_pb=denominator,
                             jet_composition_fraction=fraction,
                             jet_composition_fraction_event_cluster_se=math.sqrt(ratio_var) if ratio_var is not None else None,
                             ratio_error_scope='EVENT_CLUSTER_DELTA_METHOD_SHARED_NUMERATOR_DENOMINATOR',
                             classification_unit='SOURCE_EVENT_HAS_MATCHING_ELIGIBLE_JET', evidence_class='ACTUAL_EXISTING_DATA_READBACK',
                             eligible_jet_count=sum(counts), weighted_jet_multiplicity_pb=total,
                             jet_multiplicity_event_correlated_variance_pb2=var,
                             **stats))
    return rows


def kinematic_summaries(events):
    out = {}
    for stage_index, stage in enumerate(STAGES):
        selected = [e for e in events if e['stages'][stage_index]]
        values = defaultdict(list)
        for event in selected:
            for name, value in event['observables'].items():
                if value is not None:
                    values[name].append(value)
        names = sorted(set().union(*(set(e['observables']) for e in events)))
        out[stage] = {name: dict(defined=len(values[name]), missing=len(selected)-len(values[name]),
                                minimum=min(values[name]) if values[name] else None,
                                maximum=max(values[name]) if values[name] else None,
                                mean=math.fsum(values[name])/len(values[name]) if values[name] else None)
                      for name in names}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--native-jsonl', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'output exists; preserve prior evidence')
    manifest = json.loads(args.manifest.read_text())
    native = defaultdict(list)
    for row in iter_jsonl(args.native_jsonl):
        require(row['dataset_id'] in ('B01', 'B02', 'B03', 'B04', 'B05', 'B06'), 'unexpected native source dataset')
        native[row['dataset_id']].append(row)
    datasets = [d for d in manifest['datasets'] if d['dataset_id'] in native]
    require({d['dataset_id'] for d in datasets} == {'B01', 'B02', 'B03', 'B04', 'B05', 'B06'}, 'missing background cohort')
    for dataset in datasets:
        for role in ('lhe', 'hepmc'):
            verify_file(dataset[role + '_path'], dataset[role + '_sha256'])
    args.output.mkdir(parents=True)
    hf_rows, photon_rows, summaries = [], [], {}
    with (args.output/'phase9_origins_event_details.jsonl').open('x') as stream:
        for dataset in datasets:
            events = list(classified_events(dataset, native[dataset['dataset_id']]))
            for event in events:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False, separators=(',', ':')) + '\n')
            photon_rows.extend(aggregate(events, 'photon_origin'))
            photon_rows.extend(aggregate_photon_objects(events))
            object_total = Counter()
            for event in events:
                object_total.update(photon_objects(event['photon_origin']))
            summaries[dataset['dataset_id']] = dict(original_N=len(events), photon_object_totals=dict(object_total),
                                                    kinematics=kinematic_summaries(events),
                                                    cutflow=[sum(e['stages'][i] for e in events) for i in range(5)])
            if dataset['dataset_id'] in HF_IDS:
                hf_rows.extend(aggregate(events, 'heavy_flavour'))
                hf_rows.extend(object_composition(events))
                summaries[dataset['dataset_id']]['native_flavour_mismatch_events'] = sum(not e['heavy_flavour']['native_reproduction_pass'] for e in events)
                summaries[dataset['dataset_id']]['heavy_quark_origin_counts'] = dict(sum((Counter(e['heavy_flavour']['heavy_quark_birth_counts']) for e in events), Counter()))
                summaries[dataset['dataset_id']]['pythia_mapping'] = dict(sum((Counter(e['pythia_mapping']) for e in events), Counter()))
    write_csv(args.output/'phase9_heavy_flavour_origins.csv', hf_rows)
    write_csv(args.output/'phase9_photon_origin_study.csv', photon_rows)
    summary = dict(status='PASS_EXISTING_EVENT_CLASSIFICATION_WITH_LIMITS', evidence_class='ACTUAL_EXISTING_DATA_READBACK',
                   new_ME_calls=0, new_integrals=0, new_events=0,
                   native_background_events=6000, classified_HF_events=3000,
                   overlap_status=OVERLAP_STATUS, exclusive_background_definition='NOT_VERIFIED',
                   photon_fake='BLOCKED_CALIBRATION_UNAVAILABLE', datasets=summaries,
                   input_manifest_sha256=sha(args.manifest), native_objects_sha256=sha(args.native_jsonl),
                   output_hashes={p.name: sha(p) for p in sorted(args.output.iterdir())})
    (args.output/'phase9_origins_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(dict(status=summary['status'], native_background_events=6000, classified_HF_events=3000)))

if __name__ == '__main__':
    main()
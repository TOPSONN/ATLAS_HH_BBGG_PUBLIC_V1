#!/usr/bin/env python3
"""Check cached physical geometry outputs; no ROOT input reads or origin claims."""
import csv, hashlib, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

root = Path(sys.argv[1])
destination = Path(sys.argv[2])
if destination.exists():
    raise FileExistsError('Refusing to overwrite matching audit evidence')
def rows(name):
    with (root/name).open(newline='',encoding='utf-8') as source:
        return list(csv.DictReader(source))
summary=json.loads((root/'summary.json').read_text())
events={int(row['entry']):row for row in rows('events.csv')}
assert len(events)==summary['entries_read']
assert set(events)==set(range(summary['start_entry'],summary['end_exclusive']))
objects=rows('truth_objects.csv')
truth_indices=defaultdict(set);eligible_truth_indices=defaultdict(set)
for row in objects:
    key=(int(row['entry']),row['object_group'])
    assert int(row['index']) not in truth_indices[key]
    truth_indices[key].add(int(row['index']))
    pt=float(row['raw_pt'])*summary['truth_scale_to_gev'];eta=float(row['raw_eta']);phi=float(row['raw_phi'])
    assert math.isfinite(pt) and pt>=0 and math.isfinite(eta) and math.isfinite(phi) and abs(phi)<=math.pi+1e-5
    if pt>25 and abs(eta)<(2.37 if row['object_group']=='photon' else 2.5):
        eligible_truth_indices[key].add(int(row['index']))
    event=events[key[0]]
    assert (row['dsid'],row['run'],row['event'])==(event['dsid'],event['run'],event['event'])
assignments=rows('matching_assignments.csv')
reco_used=defaultdict(set);truth_used=defaultdict(set);pairs=defaultdict(dict)
counts=Counter(); distances=[]
for row in assignments:
    entry=int(row['entry']);group=row['object_group'];threshold=float(row['threshold']);scope=row['scope']
    key=(entry,group,threshold,scope)
    event=events[entry]
    assert event['valid']=='1'
    assert (row['dsid'],row['run'],row['event'])==(event['dsid'],event['run'],event['event'])
    reco=int(row['reco_index']);truth=int(row['truth_index']);dr=float(row['delta_r'])
    assert reco not in reco_used[key] and truth not in truth_used[key]
    assert 0<=reco<int(event[group+'_n']) and truth in truth_indices[(entry,group)]
    assert truth in eligible_truth_indices[(entry,group)]
    assert math.isfinite(dr) and 0<=dr<threshold
    assert scope in {'ALL_VALID','C9'}
    if scope=='C9':assert event['C9_selected']=='1'
    reco_used[key].add(reco);truth_used[key].add(truth);pairs[key][(reco,truth)]=dr
    counts[(group,threshold,scope)]+=1;distances.append(dr)
for (entry,group,threshold,scope),value in pairs.items():
    if scope=='ALL_VALID':
        selected=events[entry]['C9_selected']=='1'
        assert pairs.get((entry,group,threshold,'C9'),{})==(value if selected else {})
    else:assert value==pairs[(entry,group,threshold,'ALL_VALID')]
threshold_summary=rows('matching_threshold_summary.csv')
assert len(threshold_summary)==12
seen=set()
for row in threshold_summary:
    key=(row['object_group'],float(row['threshold']),row['scope'])
    assert key not in seen;seen.add(key)
    matched=int(row['matched_pairs']);reco=int(row['eligible_reco']);truth=int(row['eligible_truth'])
    assert matched==counts[key]
    assert matched+int(row['unmatched_reco'])==reco
    assert matched+int(row['unmatched_truth'])==truth
    assert reco<=int(row['reco_provided']) and truth<=int(row['truth_provided'])
    population=[event for event in events.values() if event['valid']=='1' and
                (row['scope']=='ALL_VALID' or event['C9_selected']=='1')]
    assert int(row['events'])==len(population)
    assert int(row['truth_available_events'])+int(row['truth_missing_events'])==len(population)
    assert int(row['truth_missing_events'])==0
    assert int(row['reco_provided'])==sum(int(event[row['object_group']+'_n']) for event in population)
    assert int(row['truth_provided'])==sum(len(truth_indices[(int(event['entry']),row['object_group'])]) for event in population)
    assert truth==sum(len(eligible_truth_indices[(int(event['entry']),row['object_group'])]) for event in population)
    for field,denominator in [('geometric_reco_match_fraction',reco),('geometric_truth_match_fraction',truth)]:
        if denominator:assert math.isclose(float(row[field]),matched/denominator,rel_tol=1e-14,abs_tol=1e-15)
        else:assert row[field]==''
    assert row['classification']=='PROVISIONAL_GEOMETRIC_ONLY_NOT_ORIGIN_PURITY_OR_OFFICIAL_EFFICIENCY'
for group,thresholds in [('photon',summary['photon_matching_thresholds']),('jet',summary['jet_matching_thresholds'])]:
    for scope in ['ALL_VALID','C9']:
        assert all(counts[(group,a,scope)]<=counts[(group,b,scope)] for a,b in zip(thresholds,thresholds[1:]))
        for entry,event in events.items():
            if event['valid']!='1' or (scope=='C9' and event['C9_selected']!='1'):continue
            assert all(len(pairs.get((entry,group,a,scope),{}))<=len(pairs.get((entry,group,b,scope),{}))
                       for a,b in zip(thresholds,thresholds[1:]))
result={'dsid':summary['dsid'],'range':[summary['start_entry'],summary['end_exclusive']],
        'assignment_rows':len(assignments),'threshold_summary_rows':len(threshold_summary),
        'csv_identity_uniqueness_threshold_denominator_scope_checks':'PASS',
        'raw_truth_object_rows':len(objects),'reconstruction_mass_closure_status':summary['mass_closure_status'],
        'classification':'PROVISIONAL_GEOMETRIC_DIAGNOSTIC_ONLY',
        'input_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
          ['events.csv','truth_objects.csv','matching_assignments.csv','matching_threshold_summary.csv','summary.json']}}
destination.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

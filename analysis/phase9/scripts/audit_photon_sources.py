#!/usr/bin/env python3
"""HISTORICAL_EVIDENCE_AUDIT: frozen process-card photon definitions only."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re

KEYS = ('pta', 'etaa', 'draa', 'draj', 'ptgmin', 'r0gamma', 'xn', 'epsgamma', 'isoem', 'cut_decays', 'ickkw', 'xqcut')

def card_values(text):
    values = {}
    for line in text.splitlines():
        line = line.split('!', 1)[0].split('#', 1)[0].strip()
        m = re.fullmatch(r'(.+?)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)', line)
        if not m or m[2].lower() not in KEYS:
            continue
        key, value = m[2].lower(), m[1].strip()
        if key in values:
            raise ValueError('duplicate photon cut: ' + key)
        if value.lower() in ('true', 'false'):
            values[key] = value.lower() == 'true'
        else:
            values[key] = float(value.replace('d', 'e').replace('D', 'E'))
    values['frixione_active'] = values.get('ptgmin', 0) > 0
    return values

def audit(repo, home):
    source = repo / 'analysis/phase8/config/datasets.json'
    manifest = json.loads(source.read_text())
    rows = []
    for d in manifest['datasets']:
        if not d['dataset_id'].startswith('B'):
            continue
        row = {'dataset_id': d['dataset_id'], 'process': d['process'], 'test_scope': 'HISTORICAL_EVIDENCE_AUDIT', 'cards': []}
        for c in d['generator_cards']:
            if not any(k in c['role'] for k in ('run_card', 'proc_card', 'process_card', 'post_run_process')):
                continue
            p = pathlib.Path(c['path'].replace('LOCAL_HOME', str(home)).replace('REPOSITORY', str(repo)))
            raw = p.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            if sha != c['sha256']:
                raise ValueError('historical photon card SHA mismatch: ' + d['dataset_id'])
            entry = {'role': c['role'], 'logical_path': c['path'], 'sha256': sha}
            if 'run_card' in c['role']:
                entry['assignments'] = card_values(raw.decode())
            else:
                entry['process_commands'] = [x.strip() for x in raw.decode().splitlines() if x.strip().startswith(('import model ', 'define ', 'generate ', 'add process '))]
            row['cards'].append(entry)
        row['photon_definition_scope'] = ('TWO_DIRECT_TREE_ME_PHOTONS_WITH_PHASE_SPACE_CUTS' if d['dataset_id'] in ('B01','B02','B03') else 'SOURCE_HIGGS_STABLE_THEN_EXISTING_PYTHIA_HGG_DECAY' if d['dataset_id'] in ('B04','B05') else 'ONE_DIRECT_TREE_ME_PHOTON_NO_CALIBRATED_JET_FAKE_MODEL')
        row['official_ATLAS_prompt_ID_or_fake_calibration'] = False
        rows.append(row)
    return {'schema_version': 1, 'test_scope': 'HISTORICAL_EVIDENCE_AUDIT', 'phase8_manifest_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'datasets': rows,
            'interpretation': 'Born definitions and fixed cut parameters do not calibrate detector photon identification or fake rates; ptgmin=0 disables the run-card Frixione block.'}

def main():
    a=argparse.ArgumentParser();a.add_argument('--repo', type=pathlib.Path, required=True);a.add_argument('--home', type=pathlib.Path, required=True);a.add_argument('--output', type=pathlib.Path, required=True);args=a.parse_args()
    out=audit(args.repo,args.home)
    with args.output.open('x') as stream:json.dump(out,stream,indent=2);stream.write('\n')
    print(json.dumps({'status':'PASS_HISTORICAL_PHOTON_CARD_AUDIT','datasets':len(out['datasets']),'output':str(args.output)}))
if __name__=='__main__':main()
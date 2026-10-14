#!/usr/bin/env python3
"""Read-only Phase6D verification of existing full1000 inputs and native ROOT.

No Delphes/generator execution, ROOT rewrite, install, or historical-file edit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'simulation/delphes/scripts'))
import run_delphes as baseline


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def require(test, reason):
    if not test:
        raise ValueError(reason)


def load(path):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= 20*1024**2, 'missing/oversized metadata')
    return json.loads(path.read_text(encoding='utf-8'))


def verify(profile, directory, output, config, env):
    directory = directory.resolve()
    original_run_manifest_sha256 = sha(directory / 'run_manifest.json')
    manifest = load(directory / 'run_manifest.json')
    native = load(directory / 'native_validation.json')
    pinned = next(r for r in load(REPO / 'metadata/phase6c_detector_manifest.json')['full1000_local_runs'] if r['process'] == profile)
    require(manifest['status'] == native['validation_status'] == 'PASS' and manifest['process'] == native['process'] == profile,
            'existing detector run not PASS / process mismatch')
    require(manifest['events_requested'] == manifest['source_total_events'] == 1000 and
            manifest['detector_canonical_card_sha256'] == baseline.CARD_SHA256, 'not pinned full1000 study run')
    for key in ('N_input','N_read','N_processed','N_output'):
        require(manifest[key] == native[key] == 1000, 'incomplete original native counts')
    require(manifest['N_invalid'] == native['N_invalid'] == manifest['N_skipped'] == native['N_skipped'] == 0,
            'failed/skipped original inputs')
    files = {}
    for name, descriptor in manifest['files'].items():
        path = baseline.bound_file(directory, name)
        actual = sha(path)
        require(actual == descriptor['sha256'] and path.stat().st_size == descriptor['bytes'], 'original run bytes changed: '+name)
        files[name] = actual
    require(files['detector.root'] == pinned['root_sha256'] == native['root_file_sha256'] and
            files['reco_events.jsonl'] == pinned['scientific_content_sha256'] == native['scientific_content_sha256'],
            'full ROOT/reco differs from pinned Phase6C')
    require(files['detector_card.tcl'] == pinned['runtime_card_sha256'] == native['detector_card_sha256'] and
            files['input_event_index.dat'] == native['input_index_sha256'] and
            files['truth_analysis_index.dat'] == native['truth_index_sha256'], 'card/index binding mismatch')
    require(sha(directory / 'native_validation.json') == pinned['native_report_sha256'], 'original native report changed')
    source_input = Path(config['phase6b_runs'][profile]) / 'shower.hepmc3.gz'
    context = baseline.source_context(source_input, profile, config)
    require(context['input_sha256'] == manifest['input_hepmc_sha256'] and context['expected_events'] == 1000 and
            context['manifest']['source_file_sha256'] == manifest['source_mg5_sha256'] and
            sha(context['manifest_path']) == manifest['source_run_manifest_sha256'], 'existing full source ancestry mismatch')
    for name, expected in manifest['source_sidecar_sha256'].items():
        require(sha(context['files'][name]) == expected, 'source ledger/card/raw diagnostics changed')
    source_snapshots = {context['manifest_path']: manifest['source_run_manifest_sha256'],
                        source_input: manifest['input_hepmc_sha256']}
    source_snapshots.update({path: context['manifest']['files'][name]['sha256'] for name, path in context['files'].items()})
    source_lhe = context['source']
    source_snapshots[source_lhe] = manifest['source_mg5_sha256']
    target = output / profile
    target.mkdir()
    arguments = [config['analyzer_path'], '--input', str(directory/'detector.root'),
                 '--input-index',str(directory/'input_event_index.dat'),'--truth-index',str(directory/'truth_analysis_index.dat'),
                 '--events','1000','--process',profile,'--card',str(directory/'detector_card.tcl'),
                 '--summary',str(target/'native_validation.json'),'--events-jsonl',str(target/'reco_events.jsonl'),
                 '--cutflow',str(target/'cutflow.csv'),'--efficiencies',str(target/'efficiencies.csv')]
    with (target/'native_readback.log').open('wb') as log:
        subprocess.run(arguments,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    fresh = load(target/'native_validation.json')
    require(fresh['validation_status']=='PASS' and fresh['N_processed']==fresh['N_read']==fresh['N_output']==1000 and
            fresh['N_invalid']==fresh['N_skipped']==0, 'fresh compatible native ROOT readback failed')
    require(sha(target/'reco_events.jsonl') == files['reco_events.jsonl'], 'fresh native scientific content differs')
    for name, expected in files.items():
        require(sha(directory/name)==expected, 'input mutation during verification: '+name)
    require(sha(directory / 'run_manifest.json') == original_run_manifest_sha256, 'detector run manifest changed during native readback')
    for path, expected in source_snapshots.items():
        require(sha(path) == expected, 'source manifest/LHE/HepMC/sidecar changed during native readback: '+path.name)
    return {'process':profile,'status':'PASS','events':1000,'normalization_denominator':1000,
            'root_sha256':files['detector.root'],'root_bytes':(directory/'detector.root').stat().st_size,
            'native_report_sha256':sha(directory/'native_validation.json'),
            'fresh_native_report_sha256':sha(target/'native_validation.json'),
            'native_scientific_content_sha256':files['reco_events.jsonl'],
            'canonical_card_sha256':baseline.CARD_SHA256,'runtime_card_sha256':files['detector_card.tcl'],
            'source_mg5_sha256':manifest['source_mg5_sha256'],'source_pythia_run_id':manifest['source_pythia_run_id'],
            'source_pythia_manifest_sha256':sha(context['manifest_path']),
            'input_generator_cross_section_pb':manifest['input_cross_section_pb'],
            'source_files_sha256':files,'source_sidecar_sha256':manifest['source_sidecar_sha256'],
            'source_run_manifest_sha256':sha(directory/'run_manifest.json'),
            'counts':{key:fresh[key] for key in ('N_input','N_read','N_processed','N_output','N_invalid','N_skipped')},
            'native_particle_validation':fresh['native_particle_identity'],
            'verification_scope':'actual_ROOT_native_source_card_full_file_hash',
            'root_binary_rewritten':False,'new_physics_events_generated':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for profile in ('bbgg','ccgg','jjgg'):
        parser.add_argument('--'+profile+'-run',type=Path,default=Path.home()/('simulations/delphes_runs/stage_c_'+profile+'_1000'))
    parser.add_argument('--installation',type=Path,default=REPO/'.local/delphes_installation.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(), 'verification output exists; choose a new directory')
    config=load(args.installation)
    env, _, _, software=baseline.verify_installation(config)
    args.output.mkdir(parents=True)
    samples=[verify(p,getattr(args,p+'_run'),args.output,config,env) for p in ('bbgg','ccgg','jjgg')]
    receipt={'schema_version':1,'status':'PASS','baseline_head':'5e7a9522e08e50d99b1a166789500a4039c3e9b1',
             'verification_scope':'actual_ROOT_native_source_card_full_file_hash','root_version':'6.40.04','cpp_standard':20,
             'software_binary_sha256':software['binary_sha256'],'samples':samples,
             'new_events_generated':0,'software_installed_or_modified':False,'historical_inputs_modified':False}
    (args.output/'verification.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'PASS','actual_native_ROOT_events':3000,'output':str(args.output)},indent=2))


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        raise SystemExit(1)

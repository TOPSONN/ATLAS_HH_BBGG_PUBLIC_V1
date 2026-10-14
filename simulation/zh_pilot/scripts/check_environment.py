#!/usr/bin/env python3
"""Read-only verification of retained physics installations; no event calls."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_environment(repo=REPO):
    repo = Path(repo)
    mgcfg_path = repo / '.local/mg5_installation.json'
    delcfg_path = repo / '.local/delphes_installation.json'
    mgcfg = json.loads(mgcfg_path.read_text(encoding='utf-8'))
    delcfg = json.loads(delcfg_path.read_text(encoding='utf-8'))
    spec = importlib.util.spec_from_file_location('zh_mg_identity', repo/'simulation/mg5/scripts/installation.py')
    mgmodule = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mgmodule)
    mgpath, identity = mgmodule.verify(mgcfg)
    version_match = re.search(r'^version\s*=\s*(\S+)',(mgpath/'VERSION').read_text(),re.M)
    if not version_match or version_match[1] != '3.5.16' or mgcfg.get('source_tag') != 'v3.5.16':
        raise ValueError('actual MG5 VERSION/source tag mismatch')
    sys.path.insert(0, str(repo/'simulation/delphes/scripts'))
    import run_delphes
    _, pycfg, _, software = run_delphes.verify_installation(delcfg)
    result = {
        'schema_version': 1, 'status': 'PASS_INSTALLED_IDENTITY_ONLY',
        'scope': 'real hash/version/ABI/build-info checks; no integration, next, shower or detector execution',
        'versions': {'MG5': version_match[1], 'Pythia8': pycfg['pythia_version'],
                     'HepMC3': pycfg['hepmc3_version'], 'Delphes': delcfg['delphes_version'],
                     'ROOT': software['root_version'], 'CXX_standard': software['analyzer_build_info']['cpp_standard']},
        'mg5_source_commit': identity['source_commit'],
        'mg5_retained_source_files_verified': len(identity['retained_file_sha256']),
        'mg5_entrypoint_sha256': digest(mgpath/'bin/mg5_aMC'),
        'mg5_actual_version_file_sha256': digest(mgpath/'VERSION'),
        'delphes_source_commit': delcfg['delphes_source_commit'],
        'delphes_identity_file_counts': {key: len(delcfg[key]) for key in
            ('source_sha256','library_sha256','header_sha256','dictionary_sha256')},
        'native_binary_sha256': software['binary_sha256'],
        'pythia_runner_sha256': software['pythia_preflight']['runner_sha256'],
        'hepmc_reader_sha256': software['pythia_preflight']['reader_validator_sha256'],
        'local_installation_config_sha256': {'mg5': digest(mgcfg_path), 'delphes': digest(delcfg_path),
            'pythia': digest(repo/'.local/pythia8_installation.json')},
        'loaded_library_paths_match_pinned_installations': True,
        'software_installed_or_reinstalled': False, 'new_physics_events_generated': 0,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error('preserve existing receipt; choose a new output file')
    result = verify_environment()
    data = json.dumps(result, indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data.encode('utf-8'))
    else:
        print(data, end='')


if __name__ == '__main__':
    main()

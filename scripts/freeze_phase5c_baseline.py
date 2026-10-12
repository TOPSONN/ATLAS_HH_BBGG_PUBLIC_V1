#!/usr/bin/env python3
"""Freeze/verify unchanged Phase5B tracked payloads and prior local evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE = '1c7da77fe4c852c929be39b10544220033de9fec'
TEXT_SUFFIXES = {'.md', '.txt', '.csv', '.json', '.yml', '.yaml', '.ini', '.py', '.sh', '.cxx', '.cpp', '.h', '.hpp', '.cmake'}
TEXT_NAMES = {'CMakeLists.txt', '.gitignore', '.gitattributes'}
PRESERVED_DIRECTORIES = (
    '.local/phase0_sources', '.local/phase5_access_20261012',
    '.local/phase5_sources_20261012', '.local/phase5b_windows_network_20261012',
    '.local/phase5b_wsl_network_20261012', '.local/phase5b_windows_sources_20261012',
    '.local/phase5b_xrootd_metadata_20261012', '.local/phase5b_validation_20261012',
    '.local/phase5b_review_20261012', 'outputs/phase5b_v1',
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    tracked = []
    for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], text=True).splitlines():
        original = subprocess.check_output(['git', 'show', BASE + ':' + name])
        actual = Path(name).read_bytes()
        is_text = Path(name).suffix.lower() in TEXT_SUFFIXES or Path(name).name in TEXT_NAMES
        if is_text:
            original = original.replace(b'\r\n', b'\n')
            actual = actual.replace(b'\r\n', b'\n')
        check = 'unchanged_prefix' if name == 'CMakeLists.txt' else 'unchanged'
        if not (actual.startswith(original) if check == 'unchanged_prefix' else actual == original):
            raise ValueError('Historical tracked evidence changed: ' + name)
        tracked.append({'path': name, 'sha256_lf' if is_text else 'sha256': sha(original),
                        'hash_convention': 'LF_TEXT_ONLY' if is_text else 'RAW_BINARY_OR_UNCLASSIFIED', 'check': check})
    if args.verify:
        evidence = json.loads(args.manifest.read_text(encoding='utf-8'))
        if evidence['base_commit'] != BASE or evidence['tracked'] != tracked:
            raise ValueError('Baseline identity differs')
        for item in evidence['immutable_local']:
            path = Path(item['path'])
            if path.stat().st_size != item['bytes'] or sha(path.read_bytes()) != item['sha256']:
                raise ValueError('Historical local evidence changed: ' + str(path))
        print(f'PASS Phase5B baseline: {len(tracked)} tracked + {len(evidence["immutable_local"])} immutable local files')
        return
    previous = json.loads(Path('metadata/phase5b_baseline_manifest.json').read_text(encoding='utf-8'))
    paths = {item['path'] for item in previous['immutable_local']}
    for directory in PRESERVED_DIRECTORIES:
        if not Path(directory).is_dir():
            raise ValueError('Historical directory missing: ' + directory)
        paths.update(p.as_posix() for p in Path(directory).rglob('*') if p.is_file())
    for name in ('.local/phase5b_final_report.md',):
        paths.add(name)
    local = []
    for name in sorted(paths):
        path = Path(name)
        local.append({'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())})
    evidence = {'base_commit': BASE, 'tracked': tracked, 'immutable_local': local,
                'scope': 'All Phase5B tracked payloads (CMake append only), inherited original four ROOT inputs and prior scientific/draft evidence, original access/source receipts, Phase0 primary-source caches, all Phase5B DATA output versions and integrated validation evidence. Temporary synthetic build fixtures excluded.'}
    with args.manifest.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(evidence, indent=2) + '\n')
    print(f'PASS frozen Phase5B baseline: {len(tracked)} tracked + {len(local)} immutable local files')


if __name__ == '__main__':
    main()

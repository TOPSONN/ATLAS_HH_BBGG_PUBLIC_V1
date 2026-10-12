#!/usr/bin/env python3
"""Freeze or verify Phase5B's unchanged Phase5 tracked and local evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE = 'e131de92897b75185981ec2c5ce1c722e9ada6c3'
TEXT_SUFFIXES = {'.md', '.txt', '.csv', '.json', '.yml', '.yaml', '.ini', '.py', '.sh', '.cxx', '.cpp', '.h', '.hpp', '.cmake'}
TEXT_NAMES = {'CMakeLists.txt', '.gitignore', '.gitattributes'}


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
        text = Path(name).suffix.lower() in TEXT_SUFFIXES or Path(name).name in TEXT_NAMES
        if text:
            original = original.replace(b'\r\n', b'\n')
            actual = actual.replace(b'\r\n', b'\n')
        check = 'unchanged_prefix' if name == 'CMakeLists.txt' else 'unchanged'
        if not (actual.startswith(original) if check == 'unchanged_prefix' else actual == original):
            raise ValueError('Historical tracked evidence changed: ' + name)
        tracked.append({'path': name, 'sha256_lf' if text else 'sha256': sha(original),
                        'hash_convention': 'LF_TEXT_ONLY' if text else 'RAW_BINARY_OR_UNCLASSIFIED', 'check': check})
    if args.verify:
        evidence = json.loads(args.manifest.read_text(encoding='utf-8'))
        if evidence['base_commit'] != BASE or evidence['tracked'] != tracked:
            raise ValueError('Baseline identity differs')
        for item in evidence['immutable_local']:
            path = Path(item['path'])
            if path.stat().st_size != item['bytes'] or sha(path.read_bytes()) != item['sha256']:
                raise ValueError('Historical local evidence changed: ' + str(path))
        print(f'PASS Phase5 baseline: {len(tracked)} tracked + {len(evidence["immutable_local"])} immutable local files')
        return
    previous = json.loads(Path('metadata/phase5_baseline_preservation.json').read_text(encoding='utf-8'))
    paths = {item['path'] for item in previous['immutable_local']}
    for directory in ('.local/phase5_access_20261012', '.local/phase5_sources_20261012', 'outputs/phase5_v1'):
        paths.update(p.as_posix() for p in Path(directory).rglob('*') if p.is_file())
    local = []
    for name in sorted(paths):
        path = Path(name)
        local.append({'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())})
    evidence = {'base_commit': BASE, 'tracked': tracked, 'immutable_local': local,
                'scope': 'Phase5 tracked payloads (CMake append only), inherited original four ROOT inputs and prior local physics evidence, original Phase5 access/source receipts and Phase5 outputs. Temporary test fixtures excluded.'}
    with args.manifest.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(evidence, indent=2) + '\n')
    print(f'PASS frozen Phase5 baseline: {len(tracked)} tracked + {len(local)} immutable local files')


if __name__ == '__main__':
    main()

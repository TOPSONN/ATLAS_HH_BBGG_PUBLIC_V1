#!/usr/bin/env python3
"""Verify the unchanged Phase 4 head and immutable local evidence during Phase 5."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE = '704045c6c18c313114e3ab41019e46c70beb086b'


def digest(raw, lf=False):
    return hashlib.sha256(raw.replace(b'\r\n', b'\n') if lf else raw).hexdigest()


def main():
    if not __debug__:raise RuntimeError('Baseline validation requires Python assertion checks enabled')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    tracked = []
    for name in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE], text=True).splitlines():
        original = subprocess.check_output(['git','show',BASE+':'+name]).replace(b'\r\n',b'\n')
        actual = Path(name).read_bytes().replace(b'\r\n',b'\n')
        if name == 'CMakeLists.txt':
            assert actual.startswith(original), 'Historical CMake must be preserved verbatim; Phase 5 is an appended section'
        else:
            assert actual == original, name
        tracked.append({'path':name,'sha256_lf':digest(original),'check':'unchanged_prefix' if name=='CMakeLists.txt' else 'unchanged'})
    if args.verify:
        saved = json.loads(args.manifest.read_text())
        assert saved['base_commit'] == BASE and saved['tracked'] == tracked
        for entry in saved['immutable_local']:
            path = Path(entry['path'])
            assert path.stat().st_size == entry['bytes'] and digest(path.read_bytes()) == entry['sha256'], str(path)
        print(f'PASS Phase 4 baseline: {len(tracked)} tracked + {len(saved["immutable_local"])} immutable local files')
        return
    directories = ('outputs/phase2_20261010T092242Z','outputs/phase3_20261010T092242Z',
                   'outputs/phase4_v1','outputs/phase4_numerical_v2_20261012',
                   '.local/phase1_access_20261009','.local/phase4_access_20261011',
                   '.local/phase4_numerical_v2')
    local = []
    for directory in directories:
        for path in sorted(Path(directory).rglob('*')):
            if path.is_file():
                local.append({'path':path.as_posix(),'bytes':path.stat().st_size,'sha256':digest(path.read_bytes())})
    evidence = {'base_commit':BASE,'tracked':tracked,'immutable_local':local,
                'scope':'All baseline tracked payloads (CMake append only), historical local outputs, original four ROOT inputs and Phase 4 evidence. Temporary external CTest stress pointers are excluded because new test invocations update them by design.'}
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    with args.manifest.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(evidence,indent=2)+'\n')
    print(f'PASS frozen Phase 4 baseline: {len(tracked)} tracked + {len(local)} immutable local files')


if __name__ == '__main__':
    main()

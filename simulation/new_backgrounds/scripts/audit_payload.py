#!/usr/bin/env python3
"""Audit exact Git payloads, verified reference bytes and preserved history."""
import argparse
import importlib.util
from pathlib import Path
import re
import subprocess

REPO=Path(__file__).resolve().parents[3]
BASE='05cff9a5d991ba6782b339bc41932ae4da296d8c'
REFERENCE='reference_samples/new_backgrounds/'
WORKFLOW='.github/workflows/new_backgrounds_full_chain.yml'
FIGURES=('.pdf','.png','.svg','.jpg','.jpeg','.gif','.webp','.eps','.ps')
BINARY=('.root','.lhe','.hepmc','.hepmc3','.gz','.zip','.tar','.tgz','.xz','.bz2',
        '.exe','.dll','.so','.pcm','.rootmap','.pyc','.pkl','.npy','.npz')
PRIVATE=re.compile(rb'(?i)(?:/home/[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)')

def permitted(path):
    return path.startswith(('simulation/new_backgrounds/','reports/phase6g_','metadata/phase6g_',REFERENCE)) or path==WORKFLOW

def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])

def names(data):return [x for x in data.decode().split('\0') if x]

def inspect(path,data,physical):
    if not permitted(path):raise ValueError('historical/unrelated payload: '+path)
    if path.lower().endswith(FIGURES):raise ValueError('unapproved figure forbidden: '+path)
    if any(x.lower() in {'vendor','external','build','downloads','lib','lib64','__pycache__'} for x in path.split('/')):
        raise ValueError('install/vendor/build/cache forbidden: '+path)
    if path in physical:
        if len(data)>20*1024**2:raise ValueError('reference exceeds ordinary small-file policy: '+path)
        return
    if path.lower().endswith(BINARY) or (path.endswith('.jsonl') and not path.startswith(REFERENCE)):
        raise ValueError('unverified physical/binary/full-event-table payload: '+path)
    sidecar=path.startswith(REFERENCE) and path.endswith(('/pythia8/input_event_index.dat','/pythia8/background_truth_index.dat'))
    text_limit=20*1024**2 if sidecar else 2*1024**2
    if len(data)>text_limit:raise ValueError('bounded text/data per-file limit exceeded: '+path)
    data.decode('utf-8')
    if path.endswith('.md'):data=data.replace(b'/mnt/'+b'c/HH',b'[DOCUMENTED_REPOSITORY_PATH]')
    if PRIVATE.search(data):raise ValueError('private path/credential: '+path)

def validate_packet(files):
    refs={p:b for p,b in files.items() if p.startswith(REFERENCE)}
    if not refs:return set()
    script=REPO/'simulation/new_backgrounds/scripts/validate_references.py'
    spec=importlib.util.spec_from_file_location('background_reference_payload_validation',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    report=module.validate_files(refs)
    return {item['path'] for item in report['validated_physical_paths']}

def audit(files,baseline_reader):
    physical=validate_packet(files)
    for path,data in files.items():inspect(path,data,physical)
    text_size=sum(len(b) for p,b in files.items() if not p.startswith(REFERENCE))
    if text_size>6*1024**2:raise ValueError('source and bounded evidence exceed6MiB')
    if sum(len(b) for p,b in files.items() if p.startswith(REFERENCE))>180*1024**2:
        raise ValueError('selected reference packet exceeds180MiB')
    old=names(git('ls-tree','-r','--name-only','-z',BASE))
    for path in old:
        if baseline_reader(path)!=git('show',BASE+':'+path):raise ValueError('historical file changed/deleted: '+path)
    return {'entries':len(files),'verified_physical_assets':len(physical),'unchanged_baseline_blobs':len(old)}

def snapshot(tree,reader):
    return {p:reader(p) for p in tree if permitted(p)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tracked',action='store_true');parser.add_argument('--staged',action='store_true')
    parser.add_argument('--outgoing',metavar='BASE');args=parser.parse_args()
    if not(args.tracked or args.staged or args.outgoing):parser.error('choose a payload scope')
    results=[]
    try:
        if args.tracked:
            tree=names(git('ls-files','-z'));reader=lambda p:(REPO/p).read_bytes()
            results.append(('tracked',audit(snapshot(tree,reader),reader)))
        if args.staged:
            changed=names(git('diff','--cached','--name-only','--no-renames','-z'))
            if any(not permitted(p) for p in changed):raise ValueError('historical/unrelated staged change')
            tree=names(git('ls-files','-z'));reader=lambda p:git('show',':'+p)
            results.append(('staged',audit(snapshot(tree,reader),reader)))
        if args.outgoing:
            for commit in git('rev-list','--reverse',args.outgoing+'..HEAD').decode().splitlines():
                changed=names(git('diff-tree','--no-commit-id','--name-only','--no-renames','-r','-z',commit))
                if any(not permitted(p) for p in changed):raise ValueError('historical/unrelated outgoing change in '+commit)
                tree=names(git('ls-tree','-r','--name-only','-z',commit));reader=lambda p,c=commit:git('show',c+':'+p)
                results.append((commit,audit(snapshot(tree,reader),reader)))
        print('PASS exact payload audit: '+repr(results));return 0
    except (OSError,ValueError,KeyError,UnicodeError,subprocess.CalledProcessError) as error:
        print('FAIL: '+str(error));return 1

if __name__=='__main__':raise SystemExit(main())

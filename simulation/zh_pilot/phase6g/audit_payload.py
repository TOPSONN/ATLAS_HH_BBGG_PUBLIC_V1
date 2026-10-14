#!/usr/bin/env python3
"""Audit source-only Phase6G preparation, including every outgoing commit."""
import argparse
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parents[3]
WRAPPER = 'simulation/zh_pilot/scripts/generate_pilot.sh'
WORKFLOW = '.github/workflows/zh_physical_pilot_bridge.yml'
BLOCKED = ('.root','.lhe','.hepmc','.hepmc3','.gz','.zip','.tar','.tgz','.xz','.bz2',
           '.pdf','.png','.svg','.jpg','.jpeg','.gif','.webp','.eps','.ps','.exe',
           '.dll','.so','.pcm','.rootmap','.pyc','.pkl','.npy','.npz','.jsonl')
PRIVATE = re.compile(rb'(?i)(?:/home/[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)')


def permitted(path):
    return (path.startswith('simulation/zh_pilot/phase6g/') or
            path.startswith('reports/phase6g_') or path.startswith('metadata/phase6g_') or
            path in {WRAPPER, WORKFLOW})


def inspect(path, data):
    if not permitted(path):
        raise ValueError('historical/unrelated Phase6G payload: '+path)
    if path.lower().endswith(BLOCKED):
        raise ValueError('physical/binary/archive/figure/full-event payload forbidden before authorization: '+path)
    if any(part.lower() in {'vendor','external','build','downloads','lib','lib64','__pycache__'} for part in path.split('/')):
        raise ValueError('installed/vendored/cache payload forbidden: '+path)
    if len(data) > 2*1024**2:
        raise ValueError('bounded text exceeds2MiB: '+path)
    data.decode('utf-8')
    if path.lower().endswith('.md'):
        data=data.replace(b'/mnt/'+b'c/HH', b'[DOCUMENTED_REPOSITORY_PATH]')
    if PRIVATE.search(data):
        raise ValueError('private path/credential visible: '+path)


def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])


def names(data):
    return [p for p in data.decode('utf-8').split('\0') if p]


def audit(paths, reader):
    total=0
    for path in paths:
        data=reader(path);inspect(path,data);total+=len(data)
    if total > 6*1024**2:
        raise ValueError('complete source/evidence payload exceeds6MiB')
    return len(paths),total


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tracked',action='store_true')
    parser.add_argument('--working',action='store_true',help='include new source paths before staging')
    parser.add_argument('--staged',action='store_true')
    parser.add_argument('--outgoing',metavar='BASE')
    args=parser.parse_args()
    if not any((args.tracked,args.working,args.staged,args.outgoing)):
        parser.error('choose an audit scope')
    checked=0;bytes_=0;commits=0
    try:
        if args.tracked or args.working:
            paths=set(names(git('ls-files','-z')))
            if args.working:
                paths.update(names(git('ls-files','--others','--exclude-standard','-z')))
            paths=sorted(p for p in paths if permitted(p))
            n,b=audit(paths,lambda p:(REPO/p).read_bytes());checked+=n;bytes_+=b
        if args.staged:
            paths=names(git('diff','--cached','--name-only','--no-renames','-z'))
            index=set(names(git('ls-files','-z')))
            for p in paths:
                if not permitted(p) or p not in index:
                    raise ValueError('historical/unrelated modification or deletion staged: '+p)
            n,b=audit(paths,lambda p:git('show',':'+p));checked+=n;bytes_+=b
        if args.outgoing:
            for commit in git('rev-list','--reverse',args.outgoing+'..HEAD').decode().splitlines():
                commits+=1
                paths=names(git('diff-tree','--no-commit-id','--name-only','--no-renames','-r','-z',commit))
                tree=set(names(git('ls-tree','-r','--name-only','-z',commit)))
                for p in paths:
                    if not permitted(p) or p not in tree:
                        raise ValueError('historical/unrelated outgoing modification or deletion: '+p)
                n,b=audit(paths,lambda p:git('show',commit+':'+p));checked+=n;bytes_+=b
                audit(sorted(p for p in tree if permitted(p)),lambda p:git('show',commit+':'+p))
        print(f'PASS_SOURCE_ONLY_PAYLOAD: entries={checked}, inspected_bytes={bytes_}, outgoing_commits={commits}; physical gates NOT_EVALUATED')
        return 0
    except (OSError,ValueError,UnicodeError,subprocess.CalledProcessError) as error:
        print('FAIL_SOURCE_ONLY_PAYLOAD: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())

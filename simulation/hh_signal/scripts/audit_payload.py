#!/usr/bin/env python3
"""Audit every outgoing commit and index, preserving the exact PR18 baseline."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.hh_signal.contracts import BASE, REPO, require

ALLOWED=('simulation/hh_signal/','reports/phase7a_','metadata/phase7a_',
         '.github/workflows/hh_signal_readiness.yml')
FORBIDDEN={'.pdf','.png','.jpg','.jpeg','.lhe','.hepmc','.hepmc3','.root','.gz',
           '.zip','.tar','.a','.so','.dll','.exe','.o','.mod','.pyc','.pkl'}

def git(*args,repo=REPO):
    return subprocess.check_output(['git','-C',str(repo),*args])

def scan(path,data):
    require(path.startswith(ALLOWED), 'OUT_OF_SCOPE_PAYLOAD: '+path)
    require(Path(path).suffix.lower() not in FORBIDDEN, 'UNAPPROVED_FIGURE_OR_GENERATED_PAYLOAD')
    require(len(data)<=1024**2 and b'\x00' not in data, 'OVERSIZED_OR_BINARY_PAYLOAD')
    require(not {'vendor','__pycache__','.local','Events','Source','lib'} & set(Path(path).parts),
            'VENDOR_CACHE_INSTALL_OUTPUT_FORBIDDEN')
    text=data.decode('utf-8')
    require(re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-{5}BEGIN [A-Z ]*PRIVATE KEY)',text) is None,
            'SECRET_PATTERN')
    require(re.search(r'(?:/[h]ome/[A-Za-z0-9_.-]+/|/[m]nt/[a-z]/|[A-Z]:[\\/](?:Users|HH)[\\/])',text) is None,
            'PRIVATE_ABSOLUTE_PATH')
    require('<Les'+'HouchesEvents' not in text and 'HepMC::'+'Version' not in text,
            'PHYSICAL_OR_FAKE_SIGNAL_EVENT_PAYLOAD')

def blobs(revision):
    result={}
    for item in git('ls-tree','-r','-z',revision).split(b'\x00'):
        if item:
            meta,path=item.split(b'\t',1);mode,kind,oid=meta.split()
            require(mode!=b'120000','UNREVIEWED_SYMLINK_IN_TREE')
            result[path.decode()] = oid.decode()
    return result

def audit(include_index=True):
    baseline=blobs(BASE)
    revisions=git('rev-list','--reverse',BASE+'..HEAD').decode().splitlines()
    for rev in revisions+(['INDEX'] if include_index else []):
        if rev=='INDEX':
            tree={}
            for row in git('ls-files','--stage','-z').split(b'\0'):
                if row:
                    meta,path=row.split(b'\t',1);mode,oid,stage=meta.split()
                    require(stage==b'0' and mode!=b'120000','UNMERGED_OR_SYMLINK_INDEX')
                    tree[path.decode()]=oid.decode()
        else: tree=blobs(rev)
        for path,oid in baseline.items():
            require(tree.get(path)==oid,'HISTORICAL_BLOB_CHANGED: '+path)
        for path,oid in tree.items():
            if path not in baseline: scan(path,git('cat-file','blob',oid))
    # Working files from baseline must also remain byte-for-byte intact.
    # Hash through git's clean filter so retained CRLF worktrees stay valid.
    changed=git('diff','--name-only',BASE,'--').decode().splitlines()
    require(not any(p in baseline for p in changed),'HISTORICAL_WORKTREE_CHANGED')
    return {'status':'PASS_ALL_OUTGOING_SNAPSHOTS_AND_INDEX','baseline':BASE,
            'historical_blobs_preserved':len(baseline),'outgoing_commits_checked':len(revisions),
            'index_checked':include_index,'unapproved_figures':0}

if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tracked',action='store_true')
    parser.parse_args()
    print(json.dumps(audit(),indent=2))

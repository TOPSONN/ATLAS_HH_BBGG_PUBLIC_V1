#!/usr/bin/env python3
"""Verify bounded Phase9 source/evidence; no native data or generator dispatch."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
BASE='8ecd91106acb1dae065cde14f1d62867d10b073f'
ALLOWED_PREFIXES=('analysis/phase9/','metadata/phase9','reports/phase9')
ALLOWED_EXACT=('CMakeLists.txt','.github/workflows/phase9-review.yml')
FORBIDDEN_SUFFIXES=('.pdf','.png','.root','.so','.a','.o','.exe','.lhe','.lhe.gz','.hepmc','.hepmc.gz','.jsonl','.hepmc3','.hepmc3.gz')
def demand(ok,reason):
    if not ok:raise ValueError(reason)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()
def allowed(path):return path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)
def ensure_exact_bytes(actual,expected,name):
    demand(actual==expected,'GIT_INDEX_OR_REMOTE_BYTE_NORMALIZATION:'+name)

def validate_payload(name,payload,covered):
    demand(allowed(name) and name in covered,'UNLISTED_OR_DISALLOWED_PAYLOAD:'+name)
    demand(not name.lower().endswith(FORBIDDEN_SUFFIXES),'FORBIDDEN_PAYLOAD_TYPE:'+name)
    demand(name=='analysis/phase9/.gitattributes' or Path(name).suffix.lower() in ('.py','.cxx','.hxx','.md','.json','.csv','.yml','.txt'),'UNSUPPORTED_PAYLOAD_TYPE:'+name)
    demand(len(payload)<2*1024**2,'UNBOUNDED_PAYLOAD:'+name)
    demand(not payload.startswith((b'%PDF-',b'\x89PNG',b'root',b'\x7fELF',b'MZ')),'BINARY_OR_FIGURE_MAGIC:'+name)
    payload.decode('utf-8')

def validate(repo):
    repo=Path(repo).resolve();manifest=json.loads((repo/'metadata/phase9_source_manifest.json').read_text());gates=json.loads((repo/'metadata/phase9_quality_gates.json').read_text())
    demand(manifest['base_revision']==BASE,'EXACT_BASE_MISMATCH')
    demand(gates['physical_total_background']=='BLOCKED' and all(gates[k]=='NOT_EVALUATED' for k in ('physical_significance','physical_CLs','physical_kappa_interval')),'FALSE_PHYSICAL_INFERENCE')
    demand(all(gates[k]==0 for k in ('new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events')),'FORBIDDEN_PRODUCTION')
    demand(gates['figure_publication_authorized'] is False,'UNAPPROVED_FIGURES')
    seen=set();total=0
    for group in ('source_files','published_evidence'):
        demand(manifest[group],'MISSING_SOURCE_OR_EVIDENCE')
        for row in manifest[group]:
            name=row['path'];p=repo/name
            demand(name not in seen and allowed(name) and '..' not in Path(name).parts and not Path(name).is_absolute(),'UNSAFE_OR_DUPLICATE_PATH');seen.add(name)
            demand(not name.lower().endswith(FORBIDDEN_SUFFIXES),'FORBIDDEN_PUBLICATION_FILE')
            demand(p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'SOURCE_OR_EVIDENCE_BYTES_CHANGED:'+name)
            if group=='published_evidence':demand(row['bytes']<2*1024**2,'UNBOUNDED_SINGLE_EVIDENCE');total+=row['bytes']
    demand(total<10*1024**2,'UNBOUNDED_AGGREGATE_EVIDENCE')
    def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).splitlines()
    covered=seen|{'metadata/phase9_source_manifest.json'}
    tracked=set(git('ls-files'))
    for name in covered & tracked:
        indexed=subprocess.check_output(['git','-C',str(repo),'show',':'+name])
        ensure_exact_bytes(indexed,(repo/name).read_bytes(),name)
    changes=git('diff','--name-only',BASE)+git('diff','--cached','--name-only')+git('ls-files','--others','--exclude-standard')
    for name in set(changes):
        demand((repo/name).is_file() and not (repo/name).is_symlink(),'DELETED_OR_SYMLINK_PAYLOAD:'+name)
        validate_payload(name,(repo/name).read_bytes(),covered)
    commits=git('rev-list',BASE+'..HEAD');snapshots=0
    for commit in commits:
        for name in git('diff-tree','--no-commit-id','--name-only','-r',commit):
            payload=subprocess.check_output(['git','-C',str(repo),'show',commit+':'+name])
            validate_payload(name,payload,covered);snapshots+=1
    return {'status':'PASS_PHASE9_BOUNDED_SOURCE_EVIDENCE_AUDIT','evidence_class':'SOURCE_ONLY_AND_HISTORICAL_EVIDENCE_AUDIT','verified_files':len(seen),'published_evidence_bytes':total,'outgoing_commits':len(commits),'outgoing_commit_paths_checked':snapshots,'native_ROOT_reexecuted':False,'new_ME_calls':0,'new_integrals':0,'new_events':0}
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3]);a=p.parse_args();print(json.dumps(validate(a.repo)))
if __name__=='__main__':main()
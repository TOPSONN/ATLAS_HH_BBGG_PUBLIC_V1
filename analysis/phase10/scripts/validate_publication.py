#!/usr/bin/env python3
"""Exact Phase10 bounded source/evidence and every outgoing commit, no production."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path,PurePosixPath
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from physical_gates import validate as validate_gates,CLASSES
BASE='ebae34fdaf9ccb09c77bd47cb1c7827fa560de0a'
MANIFEST='metadata/phase10_source_manifest.json'
ALLOWED_EXACT={MANIFEST,'.github/workflows/phase10-feasibility.yml','analysis/phase10/.gitattributes'}
ALLOWED_PREFIXES=('analysis/phase10/','metadata/phase10','reports/phase10')
FORBIDDEN_SUFFIXES=('.pdf','.png','.root','.so','.a','.o','.exe','.lhe','.lhe.gz','.hepmc','.hepmc.gz','.jsonl','.hepmc3','.hepmc3.gz')

def demand(ok,reason):
 if not ok:raise ValueError(reason)

def allowed(name):
 p=PurePosixPath(name)
 return not p.is_absolute() and '..' not in p.parts and '\\' not in name and (name in ALLOWED_EXACT or name.startswith(ALLOWED_PREFIXES))

def ensure_exact_bytes(actual,expected,name):demand(actual==expected,'GIT_INDEX_OR_REMOTE_BYTE_NORMALIZATION:'+name)

def validate_payload(name,payload,covered):
 demand(allowed(name) and name in covered,'UNLISTED_OR_DISALLOWED_PAYLOAD:'+name)
 demand(not name.lower().endswith(FORBIDDEN_SUFFIXES),'FORBIDDEN_PAYLOAD_TYPE:'+name)
 demand(name=='analysis/phase10/.gitattributes' or PurePosixPath(name).suffix.lower() in ('.py','.cxx','.hxx','.md','.json','.csv','.yml','.txt'),'UNSUPPORTED_PAYLOAD_TYPE:'+name)
 demand(0<len(payload)<2*1024**2,'EMPTY_OR_UNBOUNDED_PAYLOAD:'+name)
 demand(not payload.startswith((b'%PDF-',b'\x89PNG',b'root',b'\x7fELF',b'MZ')),'BINARY_OR_FIGURE_MAGIC:'+name)
 payload.decode('utf-8')

def validate(repo):
 repo=Path(repo).resolve();manifest=json.loads((repo/MANIFEST).read_text())
 demand(manifest['base_revision']==BASE,'EXACT_BASE_MISMATCH')
 validate_gates(json.loads((repo/'metadata/phase10_quality_gates.json').read_text()))
 validate_gates(json.loads((repo/'analysis/phase10/evidence/phase10_physics_gate_matrix.json').read_text()))
 seen=set();total=0
 for group in ('source_files','published_evidence'):
  demand(manifest[group],'MISSING_SOURCE_OR_EVIDENCE')
  for row in manifest[group]:
   name=row['path'];p=repo/name;demand(name not in seen and allowed(name),'UNSAFE_OR_DUPLICATE_PATH');seen.add(name)
   demand(p.is_file() and not p.is_symlink(),'MISSING_OR_SYMLINK_PAYLOAD:'+name)
   raw=p.read_bytes();validate_payload(name,raw,{name})
   demand(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'SOURCE_OR_EVIDENCE_BYTES_CHANGED:'+name)
   if group=='published_evidence':
    demand(row.get('evidence_class') in CLASSES,'INVALID_EVIDENCE_CLASS:'+name);total+=len(raw)
 demand(total<10*1024**2,'UNBOUNDED_AGGREGATE_EVIDENCE')
 def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).splitlines()
 covered=seen|{MANIFEST};tracked=set(git('ls-files'))
 for name in covered & tracked:ensure_exact_bytes(subprocess.check_output(['git','-C',str(repo),'show',':'+name]),(repo/name).read_bytes(),name)
 changes=git('diff','--name-only',BASE)+git('diff','--cached','--name-only')+git('ls-files','--others','--exclude-standard')
 for name in set(changes):
  p=repo/name;demand(p.is_file() and not p.is_symlink(),'DELETED_OR_SYMLINK_PAYLOAD:'+name);validate_payload(name,p.read_bytes(),covered)
 source_revision=manifest.get('source_payload_commit')
 if source_revision:
  delivery={'metadata/phase10_quality_gates.json',MANIFEST,'reports/phase10_final_report.md'}
  for row in manifest['source_files']:
   name=row['path']
   if name in delivery:continue
   raw=subprocess.check_output(['git','-C',str(repo),'show',source_revision+':'+name]);ensure_exact_bytes(raw,(repo/name).read_bytes(),'SOURCE_COMMIT:'+name)
 commits=git('rev-list',BASE+'..HEAD');snapshots=0
 for commit in commits:
  for name in git('diff-tree','-m','--no-commit-id','--name-only','-r',commit):
   raw=subprocess.check_output(['git','-C',str(repo),'show',commit+':'+name]);validate_payload(name,raw,covered);snapshots+=1
 return {'status':'PASS_PHASE10_BOUNDED_SOURCE_EVIDENCE_AUDIT','evidence_class':'HISTORICAL_SOURCE_AUDIT','verified_files':len(seen)+1,'published_evidence_bytes':total,'outgoing_commits':len(commits),'outgoing_commit_paths_checked':snapshots,'new_ME_calls':0,'new_integrals':0,'new_events':0,'figure_publication':False,'ci_scope':'SOURCE_METHODS_AND_PUBLISHED_BOUNDED_EVIDENCE_NOT_FULL_NATIVE_ROOT'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3]);a=p.parse_args();print(json.dumps(validate(a.repo)))
if __name__=='__main__':main()

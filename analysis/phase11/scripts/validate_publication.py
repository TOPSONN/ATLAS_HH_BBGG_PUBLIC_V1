#!/usr/bin/env python3
"""Validate exact Phase11 source/evidence/index and every outgoing commit payload."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path,PurePosixPath
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from pilot_policy import validate_contract,validate_inactive_card,PHYSICAL_GATES,COUNTERS,demand
BASE='7b65428648bd3b1040721cf569604e6d8ad1625c'
MANIFEST='metadata/phase11_scientific_source_identity.json'
CLASSES={'ACTUAL_EXISTING_DATA_READBACK','HISTORICAL_SOURCE_AUDIT','PUBLIC_SOURCE_AUDIT','SYNTHETIC_METHOD_ONLY','FUTURE_UNEXECUTED_PROPOSAL'}
EXACT={MANIFEST,'.github/workflows/phase11-pilot-gate.yml','analysis/phase11/.gitattributes'}
PREFIXES=('analysis/phase11/','metadata/phase11','reports/phase11')
FORBIDDEN=('.pdf','.png','.root','.exe','.so','.o','.a','.lhe','.lhe.gz','.hepmc','.hepmc.gz','.hepmc3','.hepmc3.gz','.jsonl')

def allowed(name):
 p=PurePosixPath(name);return not p.is_absolute() and '..' not in p.parts and '\\' not in name and (name in EXACT or name.startswith(PREFIXES))

def exact_bytes(actual,expected,name):demand(actual==expected,'INDEX_OR_REMOTE_NORMALIZATION:'+name)

def payload(name,raw,covered):
 demand(allowed(name) and name in covered,'UNLISTED_OR_HISTORICAL_PAYLOAD:'+name)
 demand(not name.lower().endswith(FORBIDDEN),'FORBIDDEN_FIGURE_BINARY_EVENT:'+name)
 demand(name=='analysis/phase11/.gitattributes' or PurePosixPath(name).suffix.lower() in ('.py','.json','.md','.csv','.txt','.yml'),'UNSUPPORTED_PAYLOAD:'+name)
 demand(0<len(raw)<2*1024**2,'EMPTY_OR_UNBOUNDED_PAYLOAD:'+name)
 demand(not raw.startswith((b'%PDF-',b'\x89PNG',b'root',b'MZ',b'\x7fELF')),'BINARY_OR_FIGURE_MAGIC:'+name);raw.decode('utf-8')

def validate(repo):
 repo=Path(repo).resolve();identity=json.loads((repo/MANIFEST).read_text());g=json.loads((repo/'metadata/phase11_quality_gates.json').read_text())
 demand(identity['base_revision']==BASE,'EXACT_BASE')
 for key,value in PHYSICAL_GATES.items():demand(g.get(key)==value,'FALSE_PHYSICAL_PROMOTION:'+key)
 for key in COUNTERS:demand(type(g.get(key)) is int and g[key]==0,'PHYSICAL_PRODUCTION:'+key)
 demand(g.get('SELECTED_PILOT_COMPONENT')=='NONE_READY' and g.get('PILOT_APPROVAL')=='NOT_AUTHORIZED' and g.get('PILOT_EXECUTED') is False,'UNREVIEWED_PILOT')
 demand(g.get('figure_publication_authorized') is False,'UNAPPROVED_FIGURES')
 validate_contract(json.loads((repo/'analysis/phase11/config/bounded_pilot_contract.json').read_text()))
 for p in [*sorted((repo/'analysis/phase11/config/cards').glob('*.inactive.txt')),repo/'analysis/phase11/config/inactive_detector_diff.txt']:validate_inactive_card(p.read_text())
 seen=set();total=0
 for group in ('source_files','published_evidence'):
  demand(bool(identity[group]),'MISSING_SOURCE_OR_EVIDENCE')
  for row in identity[group]:
   name=row['path'];p=repo/name;demand(name not in seen and p.is_file() and not p.is_symlink(),'UNSAFE_OR_DUPLICATE_PAYLOAD');seen.add(name);raw=p.read_bytes();payload(name,raw,{name})
   demand(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'SOURCE_OR_EVIDENCE_CHANGED:'+name)
   if group=='published_evidence':demand(row['evidence_class'] in CLASSES,'INVALID_EVIDENCE_CLASS');total+=len(raw)
 demand(total<10*1024**2,'UNBOUNDED_AGGREGATE')
 def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).splitlines()
 covered=seen|{MANIFEST};tracked=set(git('ls-files'))
 for name in covered&tracked:exact_bytes(subprocess.check_output(['git','-C',str(repo),'show',':'+name]),(repo/name).read_bytes(),name)
 for name in set(git('diff','--name-only',BASE)+git('diff','--cached','--name-only')+git('ls-files','--others','--exclude-standard')):
  p=repo/name;demand(p.is_file() and not p.is_symlink(),'DELETION_OR_SYMLINK');payload(name,p.read_bytes(),covered)
 revision=identity.get('source_payload_commit');delivery={'metadata/phase11_quality_gates.json',MANIFEST,'reports/phase11_final_report.md'}
 if revision:
  for row in identity['source_files']:
   name=row['path']
   if name not in delivery:exact_bytes(subprocess.check_output(['git','-C',str(repo),'show',revision+':'+name]),(repo/name).read_bytes(),'SOURCE_COMMIT:'+name)
 commits=git('rev-list',BASE+'..HEAD');snapshots=0
 for commit in commits:
  for name in git('diff-tree','-m','--no-commit-id','--name-only','-r',commit):payload(name,subprocess.check_output(['git','-C',str(repo),'show',commit+':'+name]),covered);snapshots+=1
 return {'status':'PASS_PHASE11_BOUNDED_PUBLICATION_AUDIT','evidence_class':'HISTORICAL_SOURCE_AUDIT','verified_files':len(covered),'published_evidence_bytes':total,'outgoing_commits':len(commits),'outgoing_payload_snapshots':snapshots,'figure_publication':False,'new_physical_events':0,'CI_scope':'Source/method and bounded existing evidence; no generator/process parser or native full-data ROOT execution.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3]);a=p.parse_args();print(json.dumps(validate(a.repo)))
if __name__=='__main__':main()

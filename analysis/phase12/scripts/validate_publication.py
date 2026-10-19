#!/usr/bin/env python3
"""Exact Phase12 publication/index/outgoing-commit audit; no scientific dispatcher."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path,PurePosixPath
BASE='988c5a8b23f0ae3edf536bbabd17eef291717335'
MANIFEST='metadata/phase12_scientific_source_identity.json'
QUALITY='metadata/phase12_quality_gates.json'
WORKFLOW='.github/workflows/phase12-runtime-pdf.yml'
DELIVERY={QUALITY,MANIFEST,'reports/phase12_final_report.md'}
CLASSES={'ACTUAL_RAW_RUNTIME_OBSERVATION','PUBLIC_SOURCE_AUDIT','ACTUAL_ISOLATED_PDF_READBACK','LOCAL_PAYLOAD_METADATA_AUDIT','SYNTHETIC_METHOD_ONLY','INDEPENDENT_ALGEBRA_METHOD_TEST','HISTORICAL_SOURCE_AUDIT','FUTURE_UNEXECUTED_PROPOSAL'}
PHYSICS={'PHYSICAL_TOTAL_BACKGROUND':'BLOCKED','PHYSICAL_SIGNIFICANCE':'NOT_EVALUATED','PHYSICAL_CLs':'NOT_EVALUATED','PHYSICAL_KAPPA_INTERVAL':'NOT_EVALUATED','PHOTON_FAKE_RATE':'UNKNOWN','MATCHED_SIGNAL_NORMALIZATION':'BLOCKED_PHASE7I','HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY':'UNVERIFIED','SELECTED_PILOT_COMPONENT':'NONE_READY','PILOT_APPROVAL':'NOT_AUTHORIZED'}
FALSE_GATES=('BASELINE_APPROVED','OLD_PHASE11_RAW_GATE_RECLASSIFIED','MG5_PARSER_EXECUTED','MATCHING_VALIDATED','PILOT_EXECUTED','figure_publication_authorized')
COUNTERS=('NEW_ME_CALLS','NEW_INTEGRALS','NEW_HARD_EVENTS','NEW_PYTHIA_EVENTS','NEW_DELPHES_EVENTS')
FORBIDDEN=('.pdf','.png','.root','.exe','.dll','.so','.o','.a','.pyc','.dat','.info','.lhe','.lhe.gz','.hepmc','.hepmc.gz','.hepmc3','.hepmc3.gz','.jsonl','.tar','.tar.gz','.zip','.bin')
PRIVATE_RUNTIME_HASHES={'83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85','9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506','82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a','e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1'}
PRIVATE_KEYS={'raw_bytes','raw_hex','raw_base64','raw_config','raw_config_bytes','raw_configuration','raw_configuration_bytes','private_config_bytes','private_runtime_bytes','full_configuration_text','runtime_config_text','raw_contents','original_raw_bytes','configuration_raw_bytes','config_raw_bytes'}

def demand(ok,reason):
 if not ok:raise ValueError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def allowed(name):
 if not isinstance(name,str) or not re.fullmatch('[A-Za-z0-9_./-]+',name):return False
 p=PurePosixPath(name)
 return bool(p.parts) and name==p.as_posix() and not p.is_absolute() and '..' not in p.parts and (name in {MANIFEST,WORKFLOW,'analysis/phase12/.gitattributes'} or name.startswith('analysis/phase12/') or name.startswith('metadata/phase12_') or bool(re.fullmatch(r'reports/phase12[a-z]?_[A-Za-z0-9_.-]+\.md',name)))
def exact_bytes(actual,expected,name):demand(actual==expected,'INDEX_OR_REMOTE_NORMALIZATION:'+name)
def private_json_bytes(obj):
 if isinstance(obj,str):
  assignments=re.findall(r'(?m)^\s*(fortran_compiler|cpp_compiler|auto_update|mg5_path)\s*=',obj)
  return sha(obj.encode()) in PRIVATE_RUNTIME_HASHES or ('MG5 MAIN DIRECTORY' in obj and len(set(assignments))>=3) or obj.lstrip().startswith(('PdfType:','SetDesc:'))
 if isinstance(obj,dict):
  for key,value in obj.items():
   if str(key).lower() in PRIVATE_KEYS and isinstance(value,(str,list,dict)) and value and value not in ('REDACTED','NOT_PUBLISHED','NOT_PUBLISHED_PRIVATE_BYTES'):return True
   if private_json_bytes(value):return True
 elif isinstance(obj,list):return any(private_json_bytes(v) for v in obj)
 return False

def payload(name,raw,covered):
 demand(allowed(name) and name in covered,'UNLISTED_OR_HISTORICAL_PAYLOAD:'+name)
 lower=name.lower();demand(not lower.endswith(FORBIDDEN) and PurePosixPath(lower).name not in ('lhapdf.conf','mg5_configuration.txt'),'FORBIDDEN_FIGURE_GRID_BINARY_OR_PRIVATE_CONFIG:'+name)
 demand(name=='analysis/phase12/.gitattributes' or PurePosixPath(name).suffix.lower() in ('.py','.json','.md','.csv','.txt','.yml','.cxx','.cc','.c','.h','.hpp','.sh'),'UNSUPPORTED_PAYLOAD:'+name)
 demand(0<len(raw)<2*1024**2,'EMPTY_OR_UNBOUNDED_PAYLOAD:'+name)
 demand(not raw.startswith((b'%PDF-',b'\x89PNG',b'root',b'MZ',b'\x7fELF',b'\x1f\x8b',b'PK\x03\x04')),'BINARY_OR_FIGURE_MAGIC:'+name)
 demand(sha(raw) not in PRIVATE_RUNTIME_HASHES,'PRIVATE_RUNTIME_RAW_IDENTITY:'+name)
 text=raw.decode('utf-8');start=text.lstrip()
 demand(not start.startswith(('PdfType:','SetDesc:')),'RAW_LHAPDF_PAYLOAD_DISGUISED:'+name)
 assignments=re.findall(r'(?m)^\s*(fortran_compiler|cpp_compiler|auto_update|mg5_path)\s*=',text)
 demand(not ('MG5 MAIN DIRECTORY' in text and len(set(assignments))>=3),'RAW_PRIVATE_CONFIGURATION_DISGUISED:'+name)
 if lower.endswith('.json'):demand(not private_json_bytes(json.loads(text)),'PRIVATE_CONFIGURATION_BYTES_IN_JSON:'+name)

def validate_gates(g):
 for key,value in PHYSICS.items():demand(g.get(key)==value,'FALSE_PHYSICAL_PROMOTION:'+key)
 for key in COUNTERS:demand(type(g.get(key)) is int and g[key]==0,'PHYSICAL_PRODUCTION:'+key)
 for key in FALSE_GATES:demand(g.get(key) is False,'UNREVIEWED_APPROVAL_OR_EXECUTION:'+key)
 return True

def git_bytes(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],timeout=30)
def git_lines(repo,*args):return git_bytes(repo,*args).decode().splitlines()
def git_paths(repo,*args):return [p.decode() for p in git_bytes(repo,*args).split(b'\0') if p]
def git_blob(repo,ref,name):
 entry=git_bytes(repo,'ls-tree','-z',ref,'--',name).split(b'\0')[0]
 demand(bool(entry),'DELETION_OR_MISSING_COMMIT_PAYLOAD:'+name)
 mode,kind,unused=entry.split(b'\t',1)[0].split()
 demand(mode in (b'100644',b'100755') and kind==b'blob','GIT_SYMLINK_OR_NONREGULAR_PAYLOAD:'+name)
 return git_bytes(repo,'show',ref+':'+name)

def audit_git(repo,covered,base=BASE):
 repo=Path(repo);tracked=set(git_paths(repo,'ls-files','-z'));snapshots=[]
 for name in covered&tracked:
  rows=git_bytes(repo,'ls-files','-s','-z','--',name).split(b'\0');entries=[x for x in rows if x]
  demand(len(entries)==1 and entries[0].split(b'\t',1)[0].split()[0] in (b'100644',b'100755') and entries[0].split(b'\t',1)[0].split()[2]==b'0','INDEX_SYMLINK_OR_UNMERGED:'+name)
  exact_bytes(git_bytes(repo,'show',':'+name),(repo/name).read_bytes(),name)
 changed=set(git_paths(repo,'diff','--name-only','-z',base)+git_paths(repo,'diff','--cached','--name-only','-z')+git_paths(repo,'ls-files','--others','--exclude-standard','-z'))
 for name in changed:
  p=repo/name;demand(p.is_file() and not any(q.is_symlink() for q in [p,*p.parents]),'DELETION_OR_SYMLINK:'+name);payload(name,p.read_bytes(),covered)
 commits=git_lines(repo,'rev-list',base+'..HEAD')
 for commit in commits:
  for name in sorted(set(git_paths(repo,'diff-tree','-m','--root','--no-renames','--no-commit-id','--name-only','-r','-z',commit))):
   raw=git_blob(repo,commit,name);payload(name,raw,covered);snapshots.append({'commit':commit,'path':name,'bytes':len(raw),'sha256':sha(raw)})
 return {'outgoing_commits':len(commits),'outgoing_payload_snapshots':len(snapshots),'outgoing_raw_payload_identity':sha(json.dumps(snapshots,sort_keys=True,separators=(',',':')).encode()),'all_staged_and_intermediate_commit_payloads_inspected':True}

def validate(repo):
 repo=Path(repo).resolve();identity=json.loads((repo/MANIFEST).read_text());g=json.loads((repo/QUALITY).read_text())
 demand(identity['base_revision']==BASE,'EXACT_BASE');validate_gates(g)
 seen=set();total=0;evidence_total=0
 for group in ('source_files','published_evidence'):
  demand(isinstance(identity.get(group),list) and bool(identity[group]),'MISSING_SOURCE_OR_EVIDENCE')
  for row in identity[group]:
   name=row['path'];demand(allowed(name) and name not in seen,'UNSAFE_OR_DUPLICATE_PAYLOAD');p=repo/name
   demand(p.is_file() and not any(q.is_symlink() for q in [p,*p.parents]),'UNSAFE_OR_DUPLICATE_PAYLOAD');seen.add(name);raw=p.read_bytes();payload(name,raw,{name})
   demand(type(row['bytes']) is int and len(raw)==row['bytes'] and sha(raw)==row['sha256'],'SOURCE_OR_EVIDENCE_CHANGED:'+name);total+=len(raw)
   if group=='published_evidence':demand(row['evidence_class'] in CLASSES,'INVALID_EVIDENCE_CLASS');evidence_total+=len(raw)
 demand(total<10*1024**2,'UNBOUNDED_AGGREGATE')
 covered=seen|{MANIFEST};payload(MANIFEST,(repo/MANIFEST).read_bytes(),covered)
 revision=identity.get('source_payload_commit')
 if revision:
  demand(isinstance(revision,str) and re.fullmatch('[0-9a-f]{40}',revision),'SOURCE_COMMIT_IDENTITY')
  git_bytes(repo,'merge-base','--is-ancestor',revision,'HEAD')
  for name in covered-DELIVERY:exact_bytes(git_blob(repo,revision,name),(repo/name).read_bytes(),'SOURCE_COMMIT:'+name)
 git_result=audit_git(repo,covered)
 return {'status':'PASS_PHASE12_BOUNDED_PUBLICATION_AUDIT','evidence_class':'HISTORICAL_SOURCE_AUDIT','verified_files':len(covered),'published_evidence_bytes':evidence_total,'all_manifest_payload_bytes':total,**git_result,'figure_publication':False,'raw_runtime_or_downloaded_grid_publication':False,'new_physical_events':0,'CI_scope':'Phase12 source/method and Phase11 unit regression plus bounded publication evidence only. No network acquisition, native PDF probe, generator or full-data analysis.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3]);a=p.parse_args();print(json.dumps(validate(a.repo)))
if __name__=='__main__':main()

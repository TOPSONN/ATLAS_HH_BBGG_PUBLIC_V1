"""Additive Phase13F source/bounded-evidence gate; inspect every outgoing blob."""
import hashlib,importlib.util,json,re,subprocess
from pathlib import Path
REPO=Path(__file__).resolve().parents[3];BASE='aa6eb8c9abdcc4d177af2e84296180624faf835a'
MANIFEST='metadata/phase13f_source_manifest.json';QUALITY='metadata/phase13f_quality_gates.json'
WORKFLOW='.github/workflows/phase13f-resource-closure.yml';DELIVERY={MANIFEST,QUALITY,'reports/phase13f_final_report.md'}
spec=importlib.util.spec_from_file_location('phase13_preserved_payload_policy',REPO/'analysis/phase13/source/publication.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
GLOBAL_CURRENT_RAW_SHA='5e8460eee42abcf08840b5a9d7666c1d9ae6abf92c4692abbee6428f7945b08e'
CLASSES=set(old.CLASSES)
def demand(ok,reason):
 if not ok:raise ValueError(reason)
def allowed(name):
 return isinstance(name,str) and re.fullmatch('[A-Za-z0-9_./-]+',name) is not None and '..' not in Path(name).parts and not Path(name).is_absolute() and (name.startswith('analysis/phase13f/') or name.startswith('metadata/phase13f_') or bool(re.fullmatch(r'reports/phase13f_[A-Za-z0-9_.-]+\.md',name)) or name==WORKFLOW)
def payload(name,raw,covered):
 demand(allowed(name) and name in covered,'UNLISTED_OR_HISTORICAL_PAYLOAD:'+name)
 demand(hashlib.sha256(raw).hexdigest()!=GLOBAL_CURRENT_RAW_SHA,'CURRENT_PRIVATE_GLOBAL_CONFIG_RAW_BYTES')
 # Reuse the unmodified Phase13 binary/grid/private-data scanner through a
 # namespaced virtual path after checking the real Phase13F path above.
 virtual='analysis/phase13/phase13f_payload/'+name
 old.payload(virtual,raw,{virtual})
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],timeout=30)
def gitpaths(repo,*args):return [s.decode() for s in git(repo,*args).split(b'\0') if s]
def audit_git(repo,covered,base=BASE):
 git(repo,'merge-base','--is-ancestor',base,'HEAD');commits=git(repo,'rev-list','--reverse',base+'..HEAD').decode().splitlines();snapshots=[];staged=[]
 tracked=set(gitpaths(repo,'ls-files','-z'))
 for name in sorted(covered&tracked):demand(old.index_blob(repo,name)==(Path(repo)/name).read_bytes(),'INDEX_NORMALIZATION:'+name)
 for name in gitpaths(repo,'diff','--cached','--name-only','-z'):
  raw=old.index_blob(repo,name);payload(name,raw,covered);staged.append(name)
 changed=set(gitpaths(repo,'diff','--name-only','-z',base)+gitpaths(repo,'ls-files','--others','--exclude-standard','-z'))
 for name in sorted(changed):
  p=Path(repo)/name;demand(p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),'DELETE_OR_SYMLINK:'+name);payload(name,p.read_bytes(),covered)
 for commit in commits:
  demand(len(git(repo,'rev-list','--parents','-n','1',commit).split())==2,'OUTGOING_MERGE_FORBIDDEN')
  for name in gitpaths(repo,'diff-tree','--root','--no-renames','--no-commit-id','--name-only','-r','-z',commit):
   raw=old.git_blob(repo,commit,name);payload(name,raw,covered);snapshots.append({'commit':commit,'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
 return {'outgoing_commits':len(commits),'outgoing_payload_snapshots':len(snapshots),'staged_payloads':len(staged),'index_exact_paths':len(covered&tracked),'every_staged_and_intermediate_commit_payload_inspected':True,'payload_snapshot_identity':hashlib.sha256(json.dumps(snapshots,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
def validate(repo):
 repo=Path(repo);m=json.loads((repo/MANIFEST).read_text());g=json.loads((repo/QUALITY).read_text());demand(m['base_revision']==BASE,'EXACT_BASE')
 for k in ('MG5_invocations','NEW_ME_CALLS','NEW_INTEGRALS','NEW_HARD_EVENTS','NEW_PYTHIA_EVENTS','NEW_DELPHES_EVENTS'):demand(type(g[k]) is int and g[k]==0,'PHYSICS_COUNTER:'+k)
 for k in ('PARSER_EXECUTED','PARSER_APPROVED','HUMAN_AUTHORIZATION_CREATED','figure_publication_authorized'):demand(g[k] is False,'UNAUTHORIZED_ACTION:'+k)
 covered={MANIFEST};total=0;evbytes=0
 for group in ('source_files','published_evidence'):
  demand(m[group],'EMPTY_MANIFEST_GROUP')
  for row in m[group]:
   name=row['path'];demand(name not in covered,'DUPLICATE_PATH');p=repo/name;demand(p.is_file() and not any(q.is_symlink() for q in (p,*p.parents)),'UNSAFE_PATH');raw=p.read_bytes();payload(name,raw,{name});demand(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'RAW_IDENTITY_MISMATCH:'+name);covered.add(name);total+=len(raw)
   if group=='published_evidence':demand(row['evidence_class'] in CLASSES,'EVIDENCE_CLASS');evbytes+=len(raw)
 demand(total<10*1024**2,'AGGREGATE_PUBLICATION_BOUND')
 payload(MANIFEST,(repo/MANIFEST).read_bytes(),covered)
 if m.get('source_payload_commit'):
  rev=m['source_payload_commit'];demand(re.fullmatch('[0-9a-f]{40}',rev),'EXACT_SOURCE_COMMIT');git(repo,'merge-base','--is-ancestor',rev,'HEAD')
  for name in covered-DELIVERY:demand(old.git_blob(repo,rev,name)==(repo/name).read_bytes(),'REVIEWED_SOURCE_DRIFT:'+name)
 audit=audit_git(repo,covered)
 return {'evidence_class':'PUBLIC_SOURCE_AUDIT','status':'PASS_PHASE13F_BOUNDED_PUBLICATION','files':len(covered),'evidence_bytes':evbytes,'payload_bytes_excluding_manifest':total,**audit,'figures_or_binaries_or_grid_or_private_config_published':False,'MG5_invocations':0}

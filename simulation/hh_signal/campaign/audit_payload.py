"""Audit source/evidence/reference allowlist in every outgoing snapshot."""
import subprocess,hashlib,re,json,os
from pathlib import Path
from .common import REPO,BASE,PHASE7A,require

ALLOWED=('simulation/hh_signal/','reports/phase7a_','reports/phase7b','reports/phase7c','reports/phase7d',
         'metadata/phase7a_','metadata/phase7_signal_','metadata/phase7b_','metadata/phase7c_','metadata/phase7d_',
         'metadata/phase7_quality_','reference_samples/hh_signal/S01_ggf_hh_sm/',
         '.github/workflows/hh_signal_readiness.yml','.github/workflows/hh_signal_campaign.yml',
         'reports/phase7e_','metadata/phase7e_','.github/workflows/hh_signal_integration_audit.yml',
         'reports/phase7f_','metadata/phase7f_','.github/workflows/hh_signal_config_lock.yml',
         'reports/phase7g_','metadata/phase7g_','.github/workflows/hh_signal_matched_integration.yml',
         'reports/phase7h_','reports/phase7i_','reports/phase7j_','reports/phase7k_','reports/phase7l_',
         'reports/phase7_final_','metadata/phase7_final_','.github/workflows/hh_signal_final_closure.yml',
         'metadata/phase7i_git_precheck_recovery.json')

def git(*args):
    # Read-only audits must not refresh/write the shared Windows/WSL index.
    return subprocess.check_output(['git','-C',str(REPO),*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})

def tree(rev):
    out={}
    for row in git('ls-tree','-r','-z',rev).split(b'\0'):
        if not row:continue
        m,p=row.split(b'\t',1);mode,kind,oid=m.split();require(mode!=b'120000','OUTGOING_SYMLINK');out[p.decode()]=oid.decode()
    return out

def scan(path,data):
    require(path.startswith(ALLOWED),'OUT_OF_SCOPE_PAYLOAD:'+path)
    suffix=Path(path).suffix.lower()
    require(suffix not in ['.pdf','.png','.jpg','.jpeg','.gif','.svg','.exe','.dll','.so','.a','.o','.mod','.pyc','.pkl'], 'UNAPPROVED_FIGURE_OR_BINARY:'+path)
    require(not {'.local','__pycache__','vendor','Events'}&set(Path(path).parts),'CACHE_OR_GENERATOR_SOURCE_PAYLOAD')
    physical=path.startswith('reference_samples/hh_signal/') and suffix in ['.gz','.root','.hepmc3']
    text_cap=12 if path.startswith('reference_samples/hh_signal/') and suffix=='.dat' else 8 if suffix=='.csv' else 2
    require(len(data)<40*1024**2 if physical else len(data)<text_cap*1024**2,'OVERSIZED_PAYLOAD:'+path)
    require(physical or b'\0' not in data,'UNREVIEWED_BINARY:'+path)
    if not physical:
        t=data.decode('utf-8');require(re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-{5}BEGIN [A-Z ]*PRIVATE KEY)',t) is None,'SECRET_PATTERN')
        require(re.search(r'(?:/[h]ome/[A-Za-z0-9_.-]+/|/[m]nt/[a-z]/|[A-Z]:[\\/](?:Users|HH)[\\/])',t) is None,'PRIVATE_ABSOLUTE_PATH:'+path)

def reference_manifests(snapshot):
    """Latest tree/index must include even deliberately ignored physics files."""
    checked=0
    for path,oid in snapshot.items():
        if not path.startswith('reference_samples/hh_signal/S01_ggf_hh_sm/') or not path.endswith('/manifest.json'):continue
        manifest=json.loads(git('cat-file','blob',oid));parent=Path(path).parent
        for row in manifest['files']:
            relative=Path(row['path']);require(not relative.is_absolute() and '..' not in relative.parts,'UNSAFE_REFERENCE_MANIFEST_PATH')
            target=(parent/relative).as_posix();require(target in snapshot,'REFERENCE_MANIFEST_ASSET_NOT_STAGED:'+target)
            data=git('cat-file','blob',snapshot[target])
            require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'REFERENCE_MANIFEST_BLOB_MISMATCH:'+target)
            checked+=1
    return checked

def audit():
    base=tree(BASE);a=tree(PHASE7A);revs=git('rev-list','--reverse',BASE+'..HEAD').decode().splitlines()
    index={}
    for row in git('ls-files','--stage','-z').split(b'\0'):
        if row:
            m,p=row.split(b'\t',1);mode,oid,stage=m.split();require(stage==b'0' and mode!=b'120000','UNSAFE_INDEX');index[p.decode()]=oid.decode()
    new_blobs=set();total=0;head=git('rev-parse','HEAD').decode().strip();manifest_assets=0
    for rev,t in [(r,tree(r)) for r in revs]+[('INDEX',index)]:
        for p,oid in base.items():require(t.get(p)==oid,'HISTORICAL_BASE_CHANGED:'+p)
        # Phase7A numerical evidence/cards/reports remain exactly immutable.
        descendant=rev=='INDEX' or subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',PHASE7A,rev],capture_output=True).returncode==0
        if descendant:
            for p,oid in a.items():
                if p not in base and p!='.github/workflows/hh_signal_readiness.yml':
                    require(t.get(p)==oid,'PHASE7A_ARTIFACT_CHANGED:'+p)
        for p,oid in t.items():
            if p in base:continue
            if (p,oid) not in new_blobs:scan(p,git('cat-file','blob',oid));new_blobs.add((p,oid))
        # Older development commits are still scanned for forbidden payloads;
        # completeness is enforced on the actual latest HEAD and staged index.
        if rev in [head,'INDEX']:manifest_assets=reference_manifests(t)
        total+=1
    require(not any(p in base for p in git('diff','--name-only',BASE).decode().splitlines()),'HISTORICAL_WORKTREE_CHANGED')
    return {'status':'PASS_EVERY_OUTGOING_SNAPSHOT_AND_INDEX','baseline':BASE,'phase7a_snapshot':PHASE7A,
       'snapshots_including_index':total,'distinct_blobs_scanned':len(new_blobs),'historical_blobs_preserved':len(base),
       'latest_reference_manifest_assets_verified':manifest_assets,'unapproved_PDF_PNG':0}

if __name__=='__main__':print(json.dumps(audit(),indent=2))

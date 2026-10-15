"""Freeze PR22, audit all intermediate outgoing payloads and explicit CI edits."""
import hashlib,json
from pathlib import Path
from .contracts import BASE,REPO,require
from simulation.hh_signal.campaign.audit_payload import git,tree,scan,reference_manifests
from simulation.hh_signal.integration_audit.audit_payload import evidence_manifests
from simulation.hh_signal.config_lock.audit_payload import manifest_assets as historical_manifest

PREFIXES=('simulation/hh_signal/matched_integration/','reports/phase7g_','metadata/phase7g_',
    '.github/workflows/hh_signal_matched_integration.yml')
PATCHES={
 'simulation/hh_signal/campaign/audit_payload.py':(
  "         'reports/phase7f_','metadata/phase7f_','.github/workflows/hh_signal_config_lock.yml')\n",
  "         'reports/phase7f_','metadata/phase7f_','.github/workflows/hh_signal_config_lock.yml',\n         'reports/phase7g_','metadata/phase7g_','.github/workflows/hh_signal_matched_integration.yml')\n"),
 '.github/workflows/hh_signal_readiness.yml':(
  "github.head_ref == 'codex/phase7f-hh-effective-config-lock')",
  "github.head_ref == 'codex/phase7f-hh-effective-config-lock' || github.head_ref == 'codex/phase7g-hh-matched-integration')"),
 '.github/workflows/hh_signal_config_lock.yml':(
  '          fetch-depth: 0\n',
  "          fetch-depth: 0\n          # The Phase7G job audits its actual head; retain this historical gate\n          # against the exact immutable Phase7F source/evidence snapshot.\n          ref: ${{ github.head_ref == 'codex/phase7g-hh-matched-integration' && '081d29a8499a714faeb9e1296d41ac93d48c82d2' || github.sha }}\n")}

def compatibility(path,before,after):
    require(path in PATCHES,'HISTORICAL_BLOB_CHANGED:'+path)
    old,new=[t.encode() for t in PATCHES[path]]
    require(before.count(old)==1 and after==before.replace(old,new),'ONLY_DECLARED_CI_COMPATIBILITY_PATCH:'+path)

def manifest_assets(t):
    parent='simulation/hh_signal/matched_integration/evidence/';path=parent+'manifest.json'
    if path not in t:return
    manifest=json.loads(git('cat-file','blob',t[path]));declared=set()
    for row in manifest['files']:
        target=parent+row['path'];require(target in t,'MISSING_MATCHED_EVIDENCE:'+target)
        data=git('cat-file','blob',t[target]);declared.add(target)
        require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'MATCHED_EVIDENCE_HASH:'+target)
    require({p for p in t if p.startswith(parent) and p!=path}==declared,'MATCHED_EVIDENCE_FILE_SET')

def audit():
    base=tree(BASE);revs=git('rev-list','--reverse',BASE+'..HEAD').decode().splitlines();index={};seen=set()
    for row in git('ls-files','--stage','-z').split(b'\0'):
        if row:
            meta,path=row.split(b'\t',1);mode,oid,stage=meta.split();require(mode!=b'120000' and stage==b'0','UNSAFE_INDEX')
            index[path.decode()]=oid.decode()
    for rev,t in [(r,tree(r)) for r in revs]+[('INDEX',index)]:
        for path,oid in base.items():
            require(path in t,'HISTORICAL_FILE_DELETED:'+path)
            if t[path]!=oid:compatibility(path,git('cat-file','blob',oid),git('cat-file','blob',t[path]))
        for path,oid in t.items():
            if path in base or (path,oid) in seen:continue
            require(path.startswith(PREFIXES),'OUTSIDE_PHASE7G_SCOPE:'+path)
            require(Path(path).suffix.lower() not in ['.lhe','.root','.hepmc','.hepmc3','.gz','.zip','.tar'],
                'PHYSICAL_SAMPLE_OR_ARCHIVE_FORBIDDEN:'+path)
            scan(path,git('cat-file','blob',oid));seen.add((path,oid))
        reference_manifests(t);evidence_manifests(t);historical_manifest(t);manifest_assets(t)
    for path in git('diff','--name-only',BASE).decode().splitlines():
        if path in base:compatibility(path,git('cat-file','blob',base[path]),(REPO/path).read_bytes())
    return {'status':'PASS_EVERY_OUTGOING_COMMIT_AND_INDEX','base_head':BASE,'snapshots':len(revs)+1,
        'baseline_blobs':len(base),'new_blobs_scanned':len(seen),'historical_physics_files_changed':0,
        'exact_CI_compatibility_edits':list(PATCHES),'unapproved_PDF_PNG':0}

if __name__=='__main__':print(json.dumps(audit(),indent=2))

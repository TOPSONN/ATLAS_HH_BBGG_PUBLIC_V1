"""Freeze PR21 science; permit only explicit fail-closed legacy hook edits."""
import hashlib,json
from pathlib import Path
from .contract import BASE,REPO,require
from simulation.hh_signal.campaign.audit_payload import git,tree,scan,reference_manifests
from simulation.hh_signal.integration_audit.audit_payload import evidence_manifests

PREFIXES=('simulation/hh_signal/config_lock/','reports/phase7f_','metadata/phase7f_','.github/workflows/hh_signal_config_lock.yml')
PATCHES={
 'simulation/hh_signal/campaign/production.py':(
  'def generate_source(output,phase,seed,build,monitor,reservation):\n',
  "def generate_source(output,phase,seed,build,monitor,reservation):\n    from simulation.hh_signal.config_lock.contract import deny_execution\n    deny_execution('new HH hard-event source')\n"),
 'simulation/hh_signal/campaign/launch_adapter.py':(
  'def main():\n',"def main():\n    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))\n    from simulation.hh_signal.config_lock.contract import deny_execution\n    deny_execution('legacy MG5 hard-event launch')\n"),
 'simulation/hh_signal/campaign/controller.py':(
  '        STATE.mkdir(parents=True,exist_ok=True)\n',
  "        from simulation.hh_signal.config_lock.contract import deny_execution\n        deny_execution('legacy HH campaign; effective runtime evidence is required')\n        STATE.mkdir(parents=True,exist_ok=True)\n"),
 'simulation/hh_signal/campaign/audit_payload.py':(
  "         'reports/phase7e_','metadata/phase7e_','.github/workflows/hh_signal_integration_audit.yml')\n",
  "         'reports/phase7e_','metadata/phase7e_','.github/workflows/hh_signal_integration_audit.yml',\n         'reports/phase7f_','metadata/phase7f_','.github/workflows/hh_signal_config_lock.yml')\n"),
 '.github/workflows/hh_signal_readiness.yml':(
  "github.head_ref == 'codex/phase7e-hh-integration-convergence')",
  "github.head_ref == 'codex/phase7e-hh-integration-convergence' || github.head_ref == 'codex/phase7f-hh-effective-config-lock')")}

def compatibility(path,before,after):
    require(path in PATCHES,'HISTORICAL_SOURCE_OR_DATA_CHANGED:'+path)
    old,new=PATCHES[path];old=old.encode();new=new.encode()
    require(before.count(old)==1 and after==before.replace(old,new),'ONLY_DECLARED_FAIL_CLOSED_HOOK_PERMITTED:'+path)

def manifest_assets(t):
    parent='simulation/hh_signal/config_lock/evidence/';path=parent+'manifest.json'
    if path not in t:return
    manifest=json.loads(git('cat-file','blob',t[path]));declared=set()
    for row in manifest['files']:
        target=parent+row['path'];require(target in t,'EVIDENCE_ASSET_NOT_STAGED:'+target)
        data=git('cat-file','blob',t[target]);declared.add(target)
        require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'EVIDENCE_BLOB_HASH:'+target)
    require({p for p in t if p.startswith(parent) and p!=path}==declared,'EVIDENCE_MANIFEST_FILE_SET')

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
            require(path.startswith(PREFIXES),'OUTSIDE_PHASE7F_SCOPE:'+path)
            require(Path(path).suffix.lower() not in ['.lhe','.root','.hepmc','.hepmc3','.gz','.zip','.tar'],
                'NEW_PHYSICAL_SAMPLE_OR_ARCHIVE_FORBIDDEN:'+path)
            scan(path,git('cat-file','blob',oid));seen.add((path,oid))
        reference_manifests(t);evidence_manifests(t);manifest_assets(t)
    for path in git('diff','--name-only',BASE).decode().splitlines():
        if path in base:compatibility(path,git('cat-file','blob',base[path]),(REPO/path).read_bytes())
    return {'status':'PASS_EVERY_OUTGOING_COMMIT_AND_INDEX','base_head':BASE,'snapshots':len(revs)+1,
        'baseline_blobs':len(base),'new_blobs_scanned':len(seen),'historical_physics_events_cards_weights_logs_reports_changed':0,
        'legacy_changes_only':list(PATCHES),'unapproved_PDF_PNG':0}

if __name__=='__main__':print(json.dumps(audit(),indent=2))

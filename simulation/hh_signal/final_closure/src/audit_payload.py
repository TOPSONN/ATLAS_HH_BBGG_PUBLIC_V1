"""Freeze PR23 scientific blobs and inspect every outgoing commit and index."""
import hashlib,json
from pathlib import Path
from .contracts import BASE,REPO,require
from simulation.hh_signal.campaign.audit_payload import git,tree,scan,reference_manifests
from simulation.hh_signal.integration_audit.audit_payload import evidence_manifests
from simulation.hh_signal.config_lock.audit_payload import manifest_assets as f_manifest
from simulation.hh_signal.matched_integration.audit_payload import manifest_assets as g_manifest
PREFIXES=('simulation/hh_signal/final_closure/','simulation/hh_signal/semantics_recovery/',
    'reports/phase7h_','reports/phase7i_','reports/phase7j_','reports/phase7k_','reports/phase7l_',
    'reports/phase7_final_','metadata/phase7_final_','.github/workflows/hh_signal_final_closure.yml',
    'metadata/phase7i_git_precheck_recovery.json',
    'metadata/phase7i_stop92_diagnostic_status.json',
    'metadata/phase7i_guard_correction_status.json',
    'metadata/phase7i_builder_review_contract.json')
PATCHES={
 'simulation/hh_signal/campaign/audit_payload.py':(
  "         'reports/phase7g_','metadata/phase7g_','.github/workflows/hh_signal_matched_integration.yml')\n",
  "         'reports/phase7g_','metadata/phase7g_','.github/workflows/hh_signal_matched_integration.yml',\n         'reports/phase7h_','reports/phase7i_','reports/phase7j_','reports/phase7k_','reports/phase7l_',\n         'reports/phase7_final_','metadata/phase7_final_','.github/workflows/hh_signal_final_closure.yml')\n"),
 '.github/workflows/hh_signal_readiness.yml':(
  "github.head_ref == 'codex/phase7g-hh-matched-integration')",
  "github.head_ref == 'codex/phase7g-hh-matched-integration' || github.head_ref == 'codex/phase7-final-closure')"),
 '.github/workflows/hh_signal_config_lock.yml':(
  "github.head_ref == 'codex/phase7g-hh-matched-integration' &&",
  "(github.head_ref == 'codex/phase7g-hh-matched-integration' || github.head_ref == 'codex/phase7-final-closure') &&"),
 '.github/workflows/hh_signal_matched_integration.yml':(
  '          fetch-depth: 0\n',
  "          fetch-depth: 0\n          ref: ${{ github.head_ref == 'codex/phase7-final-closure' && 'a5582e508e452a515670d1edc1d39041e88a8638' || github.sha }}\n")}

def compatibility(path,before,after):
    require(path in PATCHES,'HISTORICAL_BLOB_CHANGED:'+path);old,new=[s.encode() for s in PATCHES[path]]
    expected=before.replace(old,new)
    variants=[expected]
    if path=='simulation/hh_signal/campaign/audit_payload.py':
        tail=b"         'reports/phase7_final_','metadata/phase7_final_','.github/workflows/hh_signal_final_closure.yml')\n"
        added=b"         'reports/phase7_final_','metadata/phase7_final_','.github/workflows/hh_signal_final_closure.yml',\n         'metadata/phase7i_git_precheck_recovery.json')\n"
        require(expected.count(tail)==1,'RECOVERY_SCOPE_PATCH_BASE')
        variants.append(expected.replace(tail,added))
        diagnostic=added.replace(b"'metadata/phase7i_git_precheck_recovery.json')",b"'metadata/phase7i_git_precheck_recovery.json',\n         'metadata/phase7i_stop92_diagnostic_status.json')")
        variants.append(expected.replace(tail,diagnostic))
        scientific=diagnostic.replace(b"'metadata/phase7i_stop92_diagnostic_status.json')",b"'metadata/phase7i_stop92_diagnostic_status.json',\n         'metadata/phase7i_guard_correction_status.json',\n         'metadata/phase7i_builder_review_contract.json')")
        variants.append(expected.replace(tail,scientific))
    require(before.count(old)==1 and after in variants,'ONLY_DECLARED_CI_COMPATIBILITY_EDIT:'+path)

def manifest_assets(t):
    parent='simulation/hh_signal/final_closure/evidence/';name=parent+'manifest.json'
    if name not in t:return
    m=json.loads(git('cat-file','blob',t[name]));declared=set()
    for row in m['files']:
        path=parent+row['path'];require(path in t,'UNSTAGED_CLOSURE_EVIDENCE:'+path)
        data=git('cat-file','blob',t[path]);declared.add(path)
        require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'CLOSURE_EVIDENCE_BLOB_DRIFT:'+path)
    require({p for p in t if p.startswith(parent) and p!=name}==declared,'CLOSURE_EVIDENCE_FILE_SET')

def worktree_compatibility(path,oid):
    before=git('cat-file','blob',oid);current=(REPO/path).read_bytes()
    if current==before:return
    # With diff.autoRefreshIndex=false Git can list a stat-only mismatch.
    # Compare canonical Git content without -w, index refresh or object writes.
    if git('hash-object','--path='+path,path).decode().strip()==oid:return
    compatibility(path,before,current)

def audit():
    base=tree(BASE);revs=git('rev-list','--reverse',BASE+'..HEAD').decode().splitlines();index={};seen=set()
    for row in git('ls-files','--stage','-z').split(b'\0'):
        if row:
            meta,path=row.split(b'\t',1);mode,oid,stage=meta.split();require(mode!=b'120000' and stage==b'0','UNSAFE_INDEX')
            index[path.decode()]=oid.decode()
    for rev,t in [(r,tree(r)) for r in revs]+[('INDEX',index)]:
        for path,oid in base.items():
            require(path in t,'HISTORICAL_BLOB_DELETED:'+path)
            if t[path]!=oid:compatibility(path,git('cat-file','blob',oid),git('cat-file','blob',t[path]))
        for path,oid in t.items():
            if path in base or (path,oid) in seen:continue
            require(path.startswith(PREFIXES),'OUTSIDE_CLOSURE_SCOPE:'+path)
            require(Path(path).suffix.lower() not in ['.lhe','.root','.hepmc','.hepmc3','.gz','.zip','.tar'],'NEW_SAMPLE_ARCHIVE_FORBIDDEN:'+path)
            scan(path,git('cat-file','blob',oid));seen.add((path,oid))
        reference_manifests(t);evidence_manifests(t);f_manifest(t);g_manifest(t);manifest_assets(t)
    for path in git('diff','--name-only',BASE).decode().splitlines():
        if path in base:worktree_compatibility(path,base[path])
    return {'status':'PASS_EVERY_OUTGOING_COMMIT_AND_INDEX','base_head':BASE,'snapshots':len(revs)+1,
        'baseline_blobs':len(base),'new_blobs_scanned':len(seen),'historical_scientific_blobs_changed':0,
        'exact_CI_compatibility_edits':list(PATCHES),'new_PDF_PNG_physical_samples':0}
if __name__=='__main__':print(json.dumps(audit(),indent=2))

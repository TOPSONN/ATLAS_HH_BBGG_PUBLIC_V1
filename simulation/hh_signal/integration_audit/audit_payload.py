"""Freeze PR20 and inspect every outgoing commit and staged snapshot."""
import ast
import hashlib
import json
import re
from .audit import BASE,REPO,require
from simulation.hh_signal.campaign.audit_payload import git,tree,scan,reference_manifests

COMPAT='simulation/hh_signal/campaign/audit_payload.py'
WORKFLOW='.github/workflows/hh_signal_readiness.yml'
NEW_PREFIXES=('reports/phase7e_','metadata/phase7e_','.github/workflows/hh_signal_integration_audit.yml')
SCOPE=('simulation/hh_signal/integration_audit/',*NEW_PREFIXES)

def evidence_manifests(snapshot):
    root='simulation/hh_signal/integration_audit/evidence/'
    for path in [root+'manifest.json',root+'prepared_plan/manifest.json']:
        if path not in snapshot:continue
        manifest=json.loads(git('cat-file','blob',snapshot[path]));parent=path.rsplit('/',1)[0]+'/'
        declared=set()
        for row in manifest['files']:
            target=parent+row['path'];require(target in snapshot,'AUDIT_EVIDENCE_NOT_STAGED:'+target)
            data=git('cat-file','blob',snapshot[target]);declared.add(target)
            require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'AUDIT_EVIDENCE_BLOB_MISMATCH:'+target)
        actual={p for p in snapshot if p.startswith(parent) and p!=path}
        require(actual==declared,'AUDIT_EVIDENCE_MANIFEST_FILE_SET')

def compatibility(path,before,after):
    if path==COMPAT:
        def strip(data):
            text=data.decode();nodes=[n for n in ast.parse(text).body if isinstance(n,ast.Assign) and
                any(isinstance(t,ast.Name) and t.id=='ALLOWED' for t in n.targets)]
            require(len(nodes)==1,'COMPAT_ASSIGNMENT_COUNT');n=nodes[0];lines=text.splitlines(keepends=True)
            return ''.join(lines[:n.lineno-1]+lines[n.end_lineno:]),ast.literal_eval(n.value)
        a,old=strip(before);b,new=strip(after)
        require(a==b and new==old+NEW_PREFIXES,'ONLY_ADDITIVE_COMPAT_ALLOWLIST_PERMITTED')
    elif path==WORKFLOW:
        old=b"github.head_ref == 'codex/phase7b7c7d-ggf-hh-signal'"
        new=b"(github.head_ref == 'codex/phase7b7c7d-ggf-hh-signal' || github.head_ref == 'codex/phase7e-hh-integration-convergence')"
        require(before.count(old)==1 and after==before.replace(old,new),'ONLY_PINNED_LEGACY_CI_BRANCH_COMPAT_PERMITTED')
    else:raise ValueError('HISTORICAL_BASE_CHANGED:'+path)

def audit():
    base=tree(BASE);revs=git('rev-list','--reverse',BASE+'..HEAD').decode().splitlines();index={}
    for row in git('ls-files','--stage','-z').split(b'\0'):
        if row:
            m,p=row.split(b'\t',1);mode,oid,stage=m.split()
            require(mode!=b'120000' and stage==b'0','UNSAFE_INDEX');index[p.decode()]=oid.decode()
    seen=set();snapshots=[(r,tree(r)) for r in revs]+[('INDEX',index)]
    for rev,t in snapshots:
        for path,oid in base.items():
            require(path in t,'HISTORICAL_BASE_DELETED:'+path)
            if t[path]!=oid:compatibility(path,git('cat-file','blob',oid),git('cat-file','blob',t[path]))
        for path,oid in t.items():
            if path in base or (path,oid) in seen:continue
            require(path.startswith(SCOPE),'OUTSIDE_PHASE7E_SCOPE:'+path)
            data=git('cat-file','blob',oid);scan(path,data);seen.add((path,oid))
        reference_manifests(t)
        evidence_manifests(t)
    for path in git('diff','--name-only',BASE).decode().splitlines():
        if path in base:compatibility(path,git('cat-file','blob',base[path]),(REPO/path).read_bytes())
    return {'status':'PASS_ALL_OUTGOING_COMMITS_AND_INDEX','baseline':BASE,'snapshots':len(snapshots),
        'new_blobs_scanned':len(seen),'baseline_blobs':len(base),'historical_scientific_blobs_changed':0,
        'permitted_compatibility_only':[COMPAT,WORKFLOW],'unapproved_figures':0}

if __name__=='__main__':
    import json
    print(json.dumps(audit(),indent=2))

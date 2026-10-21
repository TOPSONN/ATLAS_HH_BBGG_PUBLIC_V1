"""Immutable input identities and fail-closed closure commands."""
import csv,json,hashlib
from pathlib import Path
from simulation.hh_signal.contracts import require,sha,read_json
HERE=Path(__file__).resolve().parents[1]
REPO=HERE.parents[2]
BASE='a5582e508e452a515670d1edc1d39041e88a8638'
BRANCH='codex/phase7-final-closure'
MODES=('audit','validate','report','prepare-integration','prepare-corrected-signal','integration','corrected-signal')

def identity(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def source_identity():
    rows=[]
    for folder in [HERE,REPO/'simulation/hh_signal/semantics_recovery']:
        rows += [{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted(folder.rglob('*'))
            if p.is_file() and 'evidence' not in p.parts and p.suffix in ['.py','.f','.f90','.c','.cxx','.sh','.json','.csv']]
    return rows

def core_evidence_identity():
    names=['native_method_result.json','root_object_readback.json','object_pt_features.csv','native_dependency_source_identity.json']
    return [{'path':name,'sha256':sha(HERE/'evidence'/name)} for name in names]

def input_identity():
    rows=read_json(HERE/'config/source_inputs.json')['files']
    require(rows and len({r['path'] for r in rows})==len(rows),'MISSING_SOURCE_IDENTITIES')
    observed=[]
    for r in rows:
        p=Path(r['path']);require(not p.is_absolute() and '..' not in p.parts,'UNSAFE_FROZEN_INPUT_PATH')
        data=(REPO/p).read_bytes()
        if r.get('text_git_normalization'):data=data.replace(b'\r\n',b'\n')
        if hashlib.sha256(data).hexdigest()!=r['sha256']:
            require(r['path']=='.github/workflows/hh_signal_campaign.yml','FROZEN_INPUT_DRIFT:'+r['path'])
            from ..master.history import reviewed_workflow_delta
            delta=reviewed_workflow_delta(r['path'],data,r['sha256'])
            observed.append({**r,**delta,'frozen_git_blob':r.get('git_blob'),
                'git_blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
        else:observed.append(r)
    return observed

def safe_output(value):
    p=Path(value).expanduser();allowed=Path.home()/'simulations/hh_final_closure'
    require(p.is_absolute() and '..' not in p.parts and p.resolve().is_relative_to(allowed.resolve()) and p.resolve()!=allowed.resolve()
        and not any(x.is_symlink() for x in [p,*p.parents]),'UNSAFE_CLOSURE_OUTPUT')
    return p

def assert_closed(mode):
    require(mode not in ['integration','corrected-signal'],'NOT_AUTHORIZED_SEPARATE_HUMAN_APPROVAL_AND_NATIVE_REVIEW_REQUIRED')

def inventory(root,rows):
    root=Path(root);require(root.is_dir(),'LOCAL_PROTECTED_INPUTS_UNAVAILABLE')
    for r in rows:
        p=Path(r['path']);require(not p.is_absolute() and '..' not in p.parts,'UNSAFE_PROTECTED_PATH')
        require((root/p).is_file() and sha(root/p)==r['sha256'] and (root/p).stat().st_size==int(r['bytes']),'HISTORICAL_INPUT_MODIFIED:'+r['path'])
    require({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}=={r['path'] for r in rows},'HISTORICAL_FILE_SET_CHANGED')
    return {'status':'PASS_FULL_LOCAL_SHA256_INVENTORY','files':len(rows),'logical_bytes':sum(int(r['bytes']) for r in rows)}

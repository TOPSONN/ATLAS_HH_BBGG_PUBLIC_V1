"""Portable verification of bounded native review receipts; never runs ME."""
from .contract import *

def validate():
    e=HERE/'evidence';m=read_json(e/'manifest.json')
    require({p.relative_to(e).as_posix() for p in e.rglob('*') if p.is_file()}==
        {r['path'] for r in m['files']}|{'manifest.json'},'REVIEW_EVIDENCE_FILE_SET')
    for row in m['files']:require(sha(e/row['path'])==row['sha256'],'REVIEW_EVIDENCE_DRIFT')
    r=read_json(e/'executable_review.json')
    require(r['source_identity']==sources() and r['physics_contract_sha256']==PHYSICS_SHA,'REVIEW_SOURCE_OR_CONTRACT_DRIFT')
    require(r['status']=='NEW_EXECUTABLE_REVISION_REQUIRES_EXPLICIT_APPROVAL' and r['new_genuine_ME_calls']==r['new_integrals']==0,'UNAPPROVED_PHYSICS_OVERCLAIM')
    b=r['public_native_build'];require([x['seed'] for x in b['replicas']]==list(SEEDS),'REVIEW_SEEDS_DRIFT')
    for replica in b['replicas']:
        require(replica['unsupervised_exit']==80 and replica['new_ME_calls']==replica['new_integrals']==0,'NATIVE_ENTRY_GUARD_DRIFT')
        require(len(replica['preflights'])==2,'MISSING_NATIVE_ENDPOINT_PREFLIGHT')
        for p in replica['preflights']:
            require(p['exit']==0 and any(s=='HI_PREFLIGHT_ZERO_ME' for s in p['records']) and
                not any(s.startswith(('HI_COUNTS','HI_ME_ENTRY')) for s in p['records']),'PREFLIGHT_OVERCLAIM')
    n=read_json(e/'native_method_review.json')
    require(n['source_identity']==sources() and len(n['computational_source_projection'])==6 and n['no_ME_or_sampler_symbols'],
        'NATIVE_SOURCE_OR_METHOD_REVIEW_DRIFT')
    require([s['exit'] for s in n['synthetic_point_cases']]==[0,92,92,92,92,90],'NATIVE_POINT_NEGATIVE_FAILURE')
    return {'status':'PASS_REVIEW_EVIDENCE_ONLY','new_genuine_ME_calls':0,'new_integrals':0,
        'execution_status':'NEW_REVISION_APPROVAL_REQUIRED','genuine_native_runtime':'NOT_EXECUTED'}

if __name__=='__main__':print(json.dumps(validate(),indent=2))

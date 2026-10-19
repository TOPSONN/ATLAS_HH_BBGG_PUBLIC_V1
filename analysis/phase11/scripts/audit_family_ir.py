#!/usr/bin/env python3
"""Read-only static audit plus fresh local JSON receipt; no generator parser."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
    p.add_argument('--mg5-root',type=Path,default=Path('/home/btu/opt/mg5amcnlo'))
    p.add_argument('--pythia-root',type=Path,default=Path('/home/btu/opt/pythia8'))
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise SystemExit('FRESH_OUTPUT_REQUIRED')
    src=a.repo/'analysis/phase11/source/family_ir.py'
    spec=importlib.util.spec_from_file_location('phase11_family_ir',src)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    paths=[a.repo/'analysis/phase11/config/candidate_b.json',a.repo/'analysis/phase11/config/photon_ir.json',a.repo/'analysis/phase11/config/cards/candidate_b.inactive.txt',src,Path(__file__).resolve()]
    before={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
    b=json.loads(paths[0].read_text());ir=json.loads(paths[1].read_text())
    errors=m.validate_candidate_b(b)+m.validate_photon_ir(ir)+m.inactive_card_errors(paths[2].read_text())
    if errors:raise SystemExit(json.dumps({'status':'FAIL_STATIC_CONFIG','errors':errors}))
    result=m.audit_sources(a.mg5_root,a.pythia_root)
    result.update({'status':'PASS_STATIC_SOURCE_REVIEW_WITH_BLOCKERS','candidate_b':b,'photon_ir':ir,'configuration_and_executed_source_sha256':before,'external_independent_human_approval':None,'parser_validation_status':'NOT_AUTHORIZED_NOT_EXECUTED','physics_validation_status':'NOT_EXECUTED','unresolved_count':len(b['unresolved_fields'])+len(ir['unresolved_fields'])})
    after={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
    if before!=after:raise SystemExit('SOURCE_CHANGED_DURING_AUDIT')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'status':result['status'],'source_files':len(result['files']),'witness_groups':len(result['source_witnesses']),'unresolved':result['unresolved_count'],'output':str(a.output)}))
if __name__=='__main__':main()

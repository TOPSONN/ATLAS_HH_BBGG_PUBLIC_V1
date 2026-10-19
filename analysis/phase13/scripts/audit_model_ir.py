#!/usr/bin/env python3
"""Read exact MG5 text sources without importing or executing MG5."""
import argparse
import datetime
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
import model_ir

def identity(p):
    p=Path(p)
    model_ir.require(p.is_file() and not p.is_symlink() and p.resolve()==p,'REGULAR_RESOLVED_AUDIT_INPUT_REQUIRED')
    return {'path':str(p),**model_ir.raw_identity(p.read_bytes())}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mg5-root',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--process-text',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    cpath=args.config.absolute();tpath=args.process_text.absolute();out=args.output.absolute()
    allowed=Path('/home/btu/simulations/hh_phase13/run_01')
    model_ir.require(allowed==out.parent or allowed in out.parent.parents,'AUDIT_OUTPUT_MUST_BE_TASK_LOCAL')
    model_ir.require(out.suffix=='.json' and out.parent.is_dir() and out.parent.resolve()==out.parent and not out.exists() and not out.is_symlink(),'FRESH_REGULAR_AUDIT_OUTPUT_REQUIRED')
    inputs=[Path(__file__).resolve(),Path(model_ir.__file__).resolve(),cpath,tpath]
    before=[identity(p) for p in inputs]
    result=model_ir.audit_model_ir(args.mg5_root,json.loads(cpath.read_text()),tpath.read_text())
    after=[identity(p) for p in inputs]
    model_ir.require(before==after,'AUDIT_IMPLEMENTATION_OR_PLAN_CHANGED')
    result['audit_inputs_before']=before;result['audit_inputs_after']=after
    result['observed_UTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'audited_source_files':len(result['source_identities_before']),'source_witnesses':len(result['source_witnesses']),'MG5_parser_executed':False,'new_ME_calls':0,'output':str(out)}))

if __name__=='__main__':main()
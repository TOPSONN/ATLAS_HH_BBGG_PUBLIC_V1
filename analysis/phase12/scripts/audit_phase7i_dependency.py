#!/usr/bin/env python3
"""Static Route-A dependency impact: no import/call of historical runtime modules."""
import argparse,hashlib,importlib.util,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--phase7i-checkout',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 if a.output.exists():raise SystemExit('FRESH_OUTPUT_REQUIRED')
 source=Path(__file__).resolve().parents[1]/'source/phase7i_dependency.py'
 before=hashlib.sha256(source.read_bytes()).hexdigest()
 spec=importlib.util.spec_from_file_location('phase12_static_dependency',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 result=m.audit(a.phase7i_checkout)
 if hashlib.sha256(source.read_bytes()).hexdigest()!=before:raise SystemExit('AUDITOR_SOURCE_CHANGED')
 result['auditor_source_sha256']=before
 result['auditor_cli_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
 print(json.dumps({'status':result['status'],'source_revision':result['phase7i_source_revision'],'inventories':len(result['inventory_scopes']),'output':str(a.output)}))
if __name__=='__main__':main()

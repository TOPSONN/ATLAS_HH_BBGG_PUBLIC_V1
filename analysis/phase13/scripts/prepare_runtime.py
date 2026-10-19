#!/usr/bin/env python3
"""Prepare a private exact source copy; no MG5 or physical command is executed."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
from runtime_layout import prepare
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--output-dir",type=Path,required=True)
 parser.add_argument("--policy",type=Path,default=Path(__file__).resolve().parents[1]/"config/runtime_layout.json")
 args=parser.parse_args();policy=json.loads(args.policy.read_text());result=prepare(Path(policy["source_root"]),args.output_dir,policy)
 print(json.dumps({"status":result["status"],"regular_files":result["regular_files"],"regular_bytes":result["regular_bytes"],
                   "source_manifest_sha256":result["source_manifest_sha256"],"new_MG5_processes":0,"new_ME_calls":0,
                   "parser_execution_authorized":False,"new_baseline_approved":False}))
if __name__=="__main__":main()

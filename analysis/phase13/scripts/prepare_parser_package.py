#!/usr/bin/env python3
"""Assemble an UNAUTHORIZED proposal; never invokes MG5."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
from parser_contract import prepare
p=argparse.ArgumentParser(description=__doc__)
for key in ("repo","runtime-receipt","resource-receipt","output","future-output"):p.add_argument("--"+key,type=Path,required=True)
p.add_argument("--reviewed-revision",required=True)
a=p.parse_args()
try:
 result=prepare(a.repo,a.runtime_receipt,a.resource_receipt,a.output,a.reviewed_revision,a.future_output)
 print(json.dumps({"status":"PREPARED_UNAUTHORIZED_UNEXECUTED_PACKAGE","source_revision":result["source_revision"],"parser_executed":False}))
except (ValueError,OSError,KeyError) as error:
 print(json.dumps({"status":"BLOCKED_PHASE13_PARSER_CONTRACT","reason":str(error),"parser_executed":False}));sys.exit(2)

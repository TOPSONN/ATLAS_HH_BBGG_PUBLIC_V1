#!/usr/bin/env python3
"""Three sequential read-only Python snapshots. No generator dispatch or MG5 imports."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
from runtime_provenance import (COUNTERS,demand,identity,private_write,propose_baseline,
 safe_output,semantic_settings,serializer_source_identity,snapshot,summarize_snapshots,
 task_record_summary,validate_policy,write_json,exact_diff_and_reproduction)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--output-dir",type=Path,required=True)
 parser.add_argument("--policy",type=Path,default=Path(__file__).resolve().parents[1]/"config/runtime_proposal.json")
 parser.add_argument("--serializer-source",type=Path,default=Path("/home/btu/opt/mg5amcnlo/madgraph/interface/extended_cmd.py"))
 parser.add_argument("--execution-record",action="append",type=Path,default=[])
 parser.add_argument("--worker-index",type=int,choices=(1,2,3))
 args=parser.parse_args();policy=json.loads(args.policy.read_text());validate_policy(policy)
 demand(str(args.serializer_source)==policy["serializer_source"],"UNREVIEWED_SERIALIZER_SOURCE_PATH")
 output=safe_output(args.output_dir,policy["allowed_output_root"],policy["forbidden_write_roots"])
 if args.worker_index is not None:
  demand(output.is_dir(),"CONTROLLER_WORKSPACE_REQUIRED")
  private=output/"private"/("snapshot_"+str(args.worker_index))
  result=snapshot(policy["target"],policy["expected_resolved"],private,policy["max_config_bytes"])
  print(json.dumps({"status":result["status"],"pid":result["pid"],"bytes":result["raw_identity"]["bytes"],"sha256":result["raw_identity"]["sha256"]}))
  return
 output.mkdir(mode=0o700);(output/"private").mkdir(mode=0o700)
 rows=[]
 for index in (1,2,3):
  command=[sys.executable,"-B",str(Path(__file__).resolve()),"--output-dir",str(output),
           "--policy",str(args.policy.resolve()),"--worker-index",str(index)]
  child=subprocess.run(command,capture_output=True,text=True,timeout=policy["worker_timeout_seconds"],check=False)
  demand(child.returncode==0,"SNAPSHOT_WORKER_FAILED:"+str(index))
  rows.append(json.loads((output/"private"/("snapshot_"+str(index))/"snapshot_metadata.json").read_text()))
 summary=summarize_snapshots(rows)
 write_json(output/"runtime_raw_snapshots.json",summary)
 raw=Path(rows[-1]["private_raw_copy"]).read_bytes();demand(identity(raw)==summary["current_raw_identity"],"PRIVATE_SNAPSHOT_HASH_CHANGED")
 source=serializer_source_identity(args.serializer_source)
 exact=exact_diff_and_reproduction(raw,source,output/"private")
 demand(serializer_source_identity(args.serializer_source)["sha256"]==source["sha256"],"SERIALIZER_SOURCE_CHANGED_DURING_REVIEW")
 write_json(output/"runtime_exact_diff.json",exact)
 record_root=Path("/home/btu/simulations/hh_phase11/run_01").resolve()
 allowed_extra={Path("/home/btu/simulations/hh_phase11/run_01/final_02/runtime_configuration_drift.json").resolve()}
 records=args.execution_record or sorted(record_root.glob("*_execution.json"))
 demand(len(records)<=32,"TASK_RECORD_COUNT_LIMIT")
 for path in records:
  resolved=path.resolve()
  demand((resolved.parent==record_root and resolved.name.endswith("_execution.json")) or resolved in allowed_extra,
         "UNAUTHORIZED_TASK_RECORD_SOURCE")
 record_summary=task_record_summary(records)
 writer={"schema_version":1,"evidence_class":"HISTORICAL_SOURCE_AUDIT","actual_writer":"UNKNOWN",
         "actual_writer_identified":False,"serializer_behavior":exact["serializer_behavior"],
         "serializer_source_identity":source,"authorized_task_records":record_summary,
         "records_are_direct_writer_proof":False,
         "reason":"Source transformation matching and task execution receipts do not identify the historical process that wrote the file.",
         "private_histories_credentials_unrelated_processes_read":False,"invasive_tracing_performed":False,**COUNTERS}
 write_json(output/"runtime_writer_attribution.json",writer)
 proposed_copy=None
 if summary["raw_bytes_stable"] and summary["file_identity_stable"]:
  proposed_copy=output/"private"/(policy["proposal_version"]+".raw.txt")
  private_write(proposed_copy,raw)
 proposal=propose_baseline(summary,policy,proposed_copy)
 write_json(output/"runtime_baseline_proposal.json",proposal)
 write_json(output/"runtime_policy_identity.json",{"path":str(args.policy.resolve()),**identity(args.policy.read_bytes())})
 print(json.dumps({"status":summary["status"],"current_raw_identity":summary["current_raw_identity"],
                   "snapshot_pids":summary["distinct_snapshot_pids"],"writer":"UNKNOWN",
                   "serializer_behavior":exact["serializer_behavior"],"new_baseline_approved":False,
                   "old_phase11_raw_gate":"BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT",**COUNTERS}))
if __name__=="__main__":
 try:main()
 except (ValueError,OSError,subprocess.TimeoutExpired) as error:
  print(json.dumps({"status":"BLOCKED_PHASE12_RUNTIME_DRIFT","reason":str(error),"new_ME_calls":0,"new_integrals":0}),file=sys.stderr)
  raise SystemExit(2)

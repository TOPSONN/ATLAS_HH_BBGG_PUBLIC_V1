#!/usr/bin/env python3
"""Execute only enumerated harmless kernel/resource fixtures; never MG5."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
import native_guard as g
from runtime_layout import ensure_fresh_output,write_json,digest

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--runtime-receipt",type=Path,required=True)
 parser.add_argument("--output-dir",type=Path,required=True)
 args=parser.parse_args()
 allowed=Path("/home/btu/simulations/hh_phase13/run_01").resolve()
 receipt_path=args.runtime_receipt.resolve(strict=True)
 if not receipt_path.is_relative_to(allowed):raise ValueError("UNREVIEWED_RUNTIME_RECEIPT_ROOT")
 receipt=json.loads(receipt_path.read_text())
 if receipt.get("status")!="EXACT_COPY_PREPARED_NOT_EXECUTED" or receipt.get("parser_execution_authorized") is not False:
  raise ValueError("UNREVIEWED_RUNTIME_RECEIPT")
 runtime=Path(receipt["isolated_runtime_root"]).resolve(strict=True)
 if not runtime.is_relative_to(allowed):raise ValueError("UNREVIEWED_PRIVATE_RUNTIME_ROOT")
 runtime_config=runtime/"input/mg5_configuration.txt"
 installed=Path("/home/btu/opt/mg5amcnlo/input/mg5_configuration.txt").resolve(strict=True)
 expected={"bytes":9302,"sha256":"e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1"}
 def identity(path):
  raw=path.read_bytes();return {"bytes":len(raw),"sha256":digest(raw)}
 before={"runtime_config":identity(runtime_config),"installed_config":identity(installed)}
 if any(value!=expected for value in before.values()):raise ValueError("STALE_RAW_CONFIGURATION_BEFORE_FIXTURES")
 output=ensure_fresh_output(args.output_dir,allowed);output.mkdir(mode=0o700)
 escape=output/"escape_symlink";escape.symlink_to(installed)
 targets={"runtime_config":str(runtime_config),"installed_config":str(installed),"escape_symlink":str(escape)}
 roots=[runtime,output]
 results=[]
 for name in g.FIXTURES:
  result=g.execute_fixture(name,output/name,roots,targets);results.append(result)
  write_json(output/(name+".json"),result)
  if result["status"]!="PASS_EXPECTED_CONTAINMENT":break
 after={"runtime_config":identity(runtime_config),"installed_config":identity(installed)}
 preservation=before==after
 passed=len(results)==len(g.FIXTURES) and all(r["status"]=="PASS_EXPECTED_CONTAINMENT" for r in results) and preservation
 summary={"schema_version":1,"evidence_class":"SYNTHETIC_METHOD_ONLY",
          "status":"PASS_NATIVE_RESOURCE_FIXTURES" if passed else "BLOCKED_NATIVE_RESOURCE_FIXTURES",
          "enforcement_verified":passed,"fixture_count":len(results),"required_fixture_count":len(g.FIXTURES),
          "runtime_receipt":{"path":str(receipt_path),"sha256":digest(receipt_path.read_bytes())},
          "raw_config_before":before,"raw_config_after":after,"raw_preservation_verified":preservation,
          "resource_profile":dict(g.LIMITS),"fixture_names":[r["fixture"] for r in results],
          "results":[{"fixture":r["fixture"],"status":r["status"],"signal":r["signal"],
                      "CPU_seconds":r["CPU_seconds"],"wall_seconds":r["wall_seconds"]} for r in results],
          "future_parser_or_MG5_success":"UNVERIFIED_NOT_EXECUTED","parser_execution_authorized":False,
          "new_baseline_approved":False,**g.COUNTERS}
 write_json(output/"resource_fixture_summary.json",summary)
 print(json.dumps({"status":summary["status"],"enforcement_verified":passed,"fixture_count":len(results),**g.COUNTERS}))
 return 0 if passed else 2
if __name__=="__main__":raise SystemExit(main())

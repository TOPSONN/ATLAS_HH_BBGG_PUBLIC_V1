#!/usr/bin/env python3
"""Only reads text/configuration/grid files; never executes a generator."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
from model_pdf import audit

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mg5", type=Path, default=Path("/home/btu/opt/mg5amcnlo"))
    parser.add_argument("--pythia", type=Path, default=Path("/home/btu/opt/pythia8"))
    parser.add_argument("--env-prefix", type=Path, default=Path("/home/btu/miniforge3/envs/atlas-hh-root"))
    parser.add_argument("--candidate", type=Path, default=Path(__file__).resolve().parents[1] / "config/candidate_a.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("fresh output file required; historical receipt must remain unchanged")
    result = audit(args.mg5, args.pythia, args.env_prefix, json.loads(args.candidate.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "source_files": len(result["source_identity"]),
                      "new_ME_calls": 0, "new_integrals": 0, "output": str(args.output)}))
if __name__ == "__main__":
    main()

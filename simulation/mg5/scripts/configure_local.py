#!/usr/bin/env python3
"""Register an existing pinned MG5 + isolated conda toolchain; installs nothing."""
import argparse
import json
from pathlib import Path
import subprocess
from installation import verify, COMMIT

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--mg5", type=Path, required=True)
parser.add_argument("--toolchain", type=Path, required=True)
parser.add_argument("--conda-sh", type=Path, required=True)
parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[3] / ".local/mg5_installation.json")
args = parser.parse_args()
commit = COMMIT
verify({"mg5_path": str(args.mg5), "source_commit": commit})
for path in (args.mg5 / "bin/mg5_aMC", args.toolchain / "bin/python", args.conda_sh):
    if not path.is_file():
        parser.error("missing installed tool: " + str(path))
if args.output.exists():
    parser.error("configuration already exists; preserve it or choose a new --output")
args.output.parent.mkdir(parents=True, exist_ok=True)
config = {"mg5_path": str(args.mg5.resolve()), "toolchain_prefix": str(args.toolchain.resolve()),
          "conda_sh": str(args.conda_sh.resolve()), "source_commit": commit,
          "source_url": "https://github.com/mg5amcnlo/mg5amcnlo.git", "source_tag": "v3.5.16"}
args.output.write_text(json.dumps(config, indent=2) + "\n")
print("Registered existing MG5; no packages installed:", args.output)

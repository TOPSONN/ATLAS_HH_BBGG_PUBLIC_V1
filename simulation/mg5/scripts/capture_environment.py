#!/usr/bin/env python3
"""Capture local MG5 identity and runtime evidence without changing any tool."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
from installation import verify

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--installation", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
cfg = json.loads(args.installation.read_text())
mg5, source_identity = verify(cfg)


def command(argv):
    result = subprocess.run(argv, text=True, capture_output=True)
    return {"argv": argv, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


files = ["VERSION", "LICENSE", "INSTALL", "models/sm/restrict_no_b_mass.dat",
         "models/sm/parameters.py", "madgraph/various/banner.py", "Template/LO/SubProcesses/cuts.f",
         "Template/Common/Source/PDF/Ctq6Pdf.f", "Template/LO/lib/Pdfdata/cteq6l1.tbl"]
identities = {}
for name in files:
    path = mg5 / name
    if not path.is_file():
        raise SystemExit("required generator source missing: " + name)
    identities[name] = {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
memory = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
          for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith(("MemTotal:", "MemAvailable:"))}
report = {"source": cfg, "source_archive_sha256": source_identity["source_archive_sha256"],
          "packaging": {key: value for key, value in source_identity.items() if key != "retained_file_sha256"},
          "retained_source_files_verified": len(source_identity["retained_file_sha256"]), "source_files": identities,
          "platform": platform.platform(), "python": platform.python_version(),
          "six": __import__("six").__version__, "memory": memory,
          "cpus": command(["nproc"]), "disk": dict(zip(["total", "used", "free"], shutil.disk_usage(mg5))),
          "gcc": command(["x86_64-conda-linux-gnu-gcc", "--version"]),
          "gxx": command(["x86_64-conda-linux-gnu-g++", "--version"]),
          "gfortran": command(["x86_64-conda-linux-gnu-gfortran", "--version"]),
          "make": command(["make", "--version"]),
          "source_commit": source_identity["source_commit"]}
args.output.write_text(json.dumps(report, indent=2) + "\n")
print("Captured", len(identities), "source identities and full pinned source archive hash")

#!/usr/bin/env python3
"""Check selected Phase 6A assets and every staged/outgoing change before push."""
import argparse
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parents[3]
ALLOWED = {
    "reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz",
    "reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz",
    "reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz",
    "reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz",
}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--tracked", action="store_true")
parser.add_argument("--staged", action="store_true")
parser.add_argument("--outgoing", metavar="BASE")
args = parser.parse_args()


def git(*argv):
    return subprocess.check_output(["git", "-C", str(REPO), *argv])


def inspect(path, data, changed):
    lower = path.lower()
    if changed and lower.endswith((".png", ".pdf", ".root")):
        raise SystemExit("unapproved figure/data in payload: " + path)
    if lower.endswith((".lhe", ".gz", ".zip", ".tar", ".hepmc")) and path not in ALLOWED:
        raise SystemExit("unselected generated/archive payload: " + path)
    if len(data) > 5 * 1024 * 1024:
        raise SystemExit("unexpected large output: " + path)
    if path.startswith(("simulation/mg5/", "reference_samples/mg5/")):
        if any(part in {"SubProcesses", "Source", "Events", "lib", "vendor", "MG5_aMC"} for part in path.split("/")):
            raise SystemExit("generator source/build output in payload: " + path)
    if path not in ALLOWED and changed:
        text = data.decode("utf-8", errors="strict")
        private = r"(?i)(?:/home/(?!\[)[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)"
        if re.search(private, text):
            raise SystemExit("machine-specific path or credential pattern: " + path)


checks = 0
if args.tracked:
    for path in git("ls-files", "-z", "simulation/mg5", "reference_samples/mg5").decode().split("\0"):
        if path:
            inspect(path, (REPO / path).read_bytes(), True)
            checks += 1
    if not all(path in git("ls-files").decode().splitlines() for path in ALLOWED):
        raise SystemExit("all four selected actual sample archives must be tracked")
if args.staged:
    for path in git("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z").decode().split("\0"):
        if path:
            inspect(path, git("show", ":" + path), True)
            checks += 1
if args.outgoing:
    for commit in git("rev-list", "--reverse", args.outgoing + "..HEAD").decode().splitlines():
        for path in git("diff-tree", "--no-commit-id", "--name-only", "-r", "--diff-filter=ACMRT", "-z", commit).decode().split("\0"):
            if path:
                inspect(path, git("show", commit + ":" + path), True)
                checks += 1
if not (args.tracked or args.staged or args.outgoing):
    parser.error("choose an audit scope")
print("PASS:", checks, "payload entries inspected; no unapproved figures or unselected outputs")

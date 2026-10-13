#!/usr/bin/env python3
"""Audit selected Phase 6B source/reference payloads and outgoing commits.

This enforces the publication allowlist and figure approval gate. It is not a
HepMC3 parser or a substitute for physical ReaderAscii and event validation.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parents[3]
DIRECTORIES = ("pp_bbgg_sm_lo_ps_13tev", "pp_ccgg_sm_lo_ps_13tev", "pp_jjgg_light_sm_lo_ps_13tev")
SHOWER_ARCHIVES = {f"reference_samples/pythia8/{directory}/shower_{count}.hepmc3.gz"
                  for directory in DIRECTORIES for count in (100, 1000)}
MINIMUM_ARCHIVES = {path for path in SHOWER_ARCHIVES if path.endswith("/shower_100.hepmc3.gz")}
MG5_ARCHIVES = {
    "reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz",
    "reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz",
    "reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz",
    "reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz",
}
MAX_SAMPLE_BYTES = 10 * 1024**2
MAX_FULL_TOTAL_BYTES = 30 * 1024**2
MAX_PREFIX_TOTAL_BYTES = 30 * 1024**2
PRIVATE = re.compile(r"(?i)(?:/home/(?!\[)[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)")
USER_DOCUMENTED_PATHS = ("/home/btu/opt/pythia8", "/home/btu/simulations/pythia8_runs", "/mnt/c/HH")


def git(*arguments):
    return subprocess.check_output(["git", "-C", str(REPO), *arguments])


def inspect(path, data):
    lower = path.lower()
    if lower.endswith((".png", ".pdf", ".root")):
        raise ValueError("unapproved figure/data in changed payload: " + path)
    if lower.endswith((".hepmc", ".hepmc3", ".lhe", ".gz", ".zip", ".tar", ".tgz", ".xz", ".bz2")):
        if path not in SHOWER_ARCHIVES | MG5_ARCHIVES:
            raise ValueError("unselected generated/archive payload: " + path)
    limit = MAX_SAMPLE_BYTES if path in SHOWER_ARCHIVES else 5 * 1024**2
    if len(data) > limit:
        raise ValueError("payload file exceeds reviewed size limit: " + path)
    if path.startswith(("simulation/pythia8/", "reference_samples/pythia8/")):
        forbidden = {"build", "lib", "lib64", "vendor", "pythia8317", "HepMC3", "downloads", "process"}
        if any(part in forbidden for part in path.split("/")):
            raise ValueError("third-party source/build/run tree in payload: " + path)
    if path not in SHOWER_ARCHIVES | MG5_ARCHIVES:
        text = data.decode("utf-8", errors="strict")
        for documented in USER_DOCUMENTED_PATHS:
            text = text.replace(documented, "[DOCUMENTED_USER_PATH]")
        if PRIVATE.search(text):
            raise ValueError("private path/credential in payload: " + path)


def inspect_archive_totals(paths, reader):
    selected = [path for path in paths if path in SHOWER_ARCHIVES]
    full = sum(len(reader(path)) for path in selected if path.endswith("/shower_1000.hepmc3.gz"))
    prefixes = sum(len(reader(path)) for path in selected if path.endswith("/shower_100.hepmc3.gz"))
    if full > MAX_FULL_TOTAL_BYTES or prefixes > MAX_PREFIX_TOTAL_BYTES:
        raise ValueError("total selected shower archive payload exceeds reviewed limit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracked", action="store_true")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--outgoing", metavar="BASE")
    args = parser.parse_args()
    if not (args.tracked or args.staged or args.outgoing):
        parser.error("choose an audit scope")
    checks = 0
    try:
        if args.tracked:
            paths = [p for p in git("ls-files", "-z", "simulation/pythia8", "reference_samples/pythia8",
                                    ".github/workflows/pythia8_reference_samples.yml", "reports/phase6b*", "metadata/phase6b*").decode().split("\0") if p]
            tracked = set(git("ls-files", "-z").decode().split("\0"))
            if not MINIMUM_ARCHIVES <= tracked:
                raise ValueError("three actual shower_100 reference archives must be tracked")
            for path in paths:
                inspect(path, (REPO / path).read_bytes())
                checks += 1
            inspect_archive_totals(paths, lambda path: (REPO / path).read_bytes())
        if args.staged:
            paths = [p for p in git("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z").decode().split("\0") if p]
            for path in paths:
                inspect(path, git("show", ":" + path))
                checks += 1
            index_paths = [p for p in git("ls-files", "-z").decode().split("\0") if p]
            inspect_archive_totals(index_paths, lambda path: git("show", ":" + path))
        if args.outgoing:
            for commit in git("rev-list", "--reverse", args.outgoing + "..HEAD").decode().splitlines():
                paths = [p for p in git("diff-tree", "--no-commit-id", "--name-only", "-r", "--diff-filter=ACMRT", "-z", commit).decode().split("\0") if p]
                for path in paths:
                    inspect(path, git("show", commit + ":" + path))
                    checks += 1
                tree_paths = [p for p in git("ls-tree", "-r", "--name-only", "-z", commit).decode().split("\0") if p]
                inspect_archive_totals(tree_paths, lambda path: git("show", commit + ":" + path))
        print(f"PASS: {checks} payload entries inspected; selected archives bounded, no unapproved figures")
        return 0
    except (ValueError, OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        print("FAIL: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

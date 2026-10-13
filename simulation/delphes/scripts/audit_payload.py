#!/usr/bin/env python3
"""Audit exact selected detector assets, changed payloads and outgoing commits.

No native ROOT/physics acceptance is inferred from this payload audit.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parents[3]
ROOT_REFERENCES = {f"reference_samples/delphes/{name}/detector_100.root" for name in
                   ("pp_bbgg_atlas_like", "pp_ccgg_atlas_like", "pp_jjgg_light_atlas_like")}
INPUT_INDICES = {f"reference_samples/delphes/{name}/input_event_index.dat" for name in
                 ("pp_bbgg_atlas_like", "pp_ccgg_atlas_like", "pp_jjgg_light_atlas_like")}
OLDER_ARCHIVES = {
    "reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz", "reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz",
    "reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz", "reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz",
    "reference_samples/pythia8/pp_bbgg_sm_lo_ps_13tev/shower_100.hepmc3.gz", "reference_samples/pythia8/pp_ccgg_sm_lo_ps_13tev/shower_100.hepmc3.gz",
    "reference_samples/pythia8/pp_jjgg_light_sm_lo_ps_13tev/shower_100.hepmc3.gz",
}
PRIVATE = re.compile(rb"(?i)(?:/home/[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)")
USER_HOME = b"/" + b"home" + b"/btu/"
DOCUMENTED_PATHS = (USER_HOME + b"opt/delphes", USER_HOME + b"simulations/", USER_HOME + b"miniforge3/", b"/mnt/" + b"c/HH")


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def inspect(path, raw):
    lower = path.lower()
    if lower.endswith((".pdf", ".png")):
        raise ValueError("unapproved figure in changed payload: " + path)
    if lower.endswith((".root", ".gz", ".hepmc3", ".hepmc", ".lhe", ".zip", ".tgz", ".tar", ".xz", ".bz2")) and path not in ROOT_REFERENCES | OLDER_ARCHIVES:
        raise ValueError("unselected generated/archive asset: " + path)
    limit = 10 * 1024**2 if path in ROOT_REFERENCES | INPUT_INDICES | OLDER_ARCHIVES else 5 * 1024**2
    if len(raw) > limit:
        raise ValueError("payload file exceeds selected size cap: " + path)
    if path in ROOT_REFERENCES:
        if not raw.startswith(b"root"):
            raise ValueError("selected ROOT asset lacks ROOT magic: " + path)
    elif path not in OLDER_ARCHIVES:
        raw.decode("utf-8")
    if path.startswith("simulation/delphes/"):
        forbidden = {"build", "lib", "lib64", "vendor", "external", "downloads", "delphes-3.5.1"}
        if any(part in forbidden for part in path.split("/")):
            raise ValueError("vendored source/build/install tree: " + path)
    if path not in OLDER_ARCHIVES:
        if lower.endswith(".md"):
            for documented in DOCUMENTED_PATHS:
                raw = raw.replace(documented, b"[DOCUMENTED_USER_PATH]")
        if PRIVATE.search(raw):
            raise ValueError("private data visible in payload: " + path)


def totals(paths, reader):
    amount = sum(len(reader(path)) for path in paths if path in ROOT_REFERENCES)
    if amount > 30 * 1024**2:
        raise ValueError("three selected ROOT assets exceed their combined30MiB maximum")
    index_amount = sum(len(reader(path)) for path in paths if path in INPUT_INDICES)
    if index_amount > 30 * 1024**2:
        raise ValueError("three selected original input indices exceed their separate combined30MiB maximum")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracked", action="store_true")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--outgoing", metavar="BASE")
    args = parser.parse_args()
    if not (args.tracked or args.staged or args.outgoing):
        parser.error("choose an audit scope")
    checked = 0
    try:
        if args.tracked:
            paths = [p for p in git("ls-files", "-z", "simulation/delphes", "reference_samples/delphes", "reports/phase6c*", "metadata/phase6c*",
                                    ".github/workflows/delphes_reference_samples.yml").decode().split("\0") if p]
            all_tracked = set(git("ls-files", "-z").decode().split("\0"))
            if not ROOT_REFERENCES <= all_tracked:
                raise ValueError("three actual selected ROOT references must be tracked")
            for path in paths:
                inspect(path, (REPO/path).read_bytes()); checked += 1
            totals(paths, lambda path:(REPO/path).read_bytes())
        if args.staged:
            paths = [p for p in git("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z").decode().split("\0") if p]
            for path in paths:
                inspect(path, git("show", ":"+path)); checked += 1
            index = [p for p in git("ls-files", "-z").decode().split("\0") if p]
            totals(index, lambda path:git("show", ":"+path))
        if args.outgoing:
            for commit in git("rev-list", "--reverse", args.outgoing+"..HEAD").decode().splitlines():
                paths = [p for p in git("diff-tree", "--no-commit-id", "--name-only", "-r", "--diff-filter=ACMRT", "-z", commit).decode().split("\0") if p]
                for path in paths:
                    inspect(path, git("show", commit+":"+path)); checked += 1
                tree = [p for p in git("ls-tree", "-r", "--name-only", "-z", commit).decode().split("\0") if p]
                totals(tree, lambda path:git("show", commit+":"+path))
        print(f"PASS: {checked} exact payload entries inspected; no unselected data/figures")
        return 0
    except (OSError, ValueError, UnicodeError, subprocess.CalledProcessError) as error:
        print("FAIL: "+str(error)); return 1


if __name__ == "__main__":
    raise SystemExit(main())

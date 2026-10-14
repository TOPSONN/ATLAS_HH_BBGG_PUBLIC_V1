#!/usr/bin/env python3
"""Bound Phase6D numerical publication; never infer physics from payload checks."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parents[3]
PILOT = {f"simulation/rare_backgrounds/evidence/pilot/{profile}.jsonl" for profile in ("bbgg", "ccgg", "jjgg")}
WORKFLOW = ".github/workflows/rare_backgrounds_statistics.yml"
PRIVATE = re.compile(rb"(?i)(?:/home/[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)")
BLOCKED_SUFFIXES = (".root", ".lhe", ".hepmc", ".hepmc3", ".gz", ".zip", ".tar", ".tgz", ".xz", ".bz2",
                    ".pdf", ".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp", ".eps", ".ps",
                    ".exe", ".dll", ".so", ".pcm", ".rootmap", ".pyc", ".pkl", ".npy", ".npz")


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def permitted(path):
    return (path.startswith("simulation/rare_backgrounds/") or path.startswith("reports/phase6d_") or
            path.startswith("metadata/phase6d_") or path == WORKFLOW)


def inspect(path, data):
    if not permitted(path):
        raise ValueError("historical/unrelated path changed by Phase6D: " + path)
    if path.lower().endswith(BLOCKED_SUFFIXES):
        raise ValueError("new physics/archive/binary/figure payload forbidden: " + path)
    if path.lower().endswith(".jsonl") and path not in PILOT:
        raise ValueError("only exact three compact pilot tables may be public JSONL: " + path)
    if len(data) > (2 if path in PILOT else 5) * 1024**2:
        raise ValueError("numerical publication file exceeds reviewed size cap: " + path)
    data.decode("utf-8")
    if "__pycache__" in path.split("/") or any(part in {"vendor", "external", "build", "downloads", "lib", "lib64"} for part in path.split("/")):
        raise ValueError("vendored source/install/cache path: " + path)
    if path.lower().endswith(".md"):
        data = data.replace(b"/mnt/" + b"c/HH", b"[DOCUMENTED_REPOSITORY_PATH]")
    if PRIVATE.search(data):
        raise ValueError("private path/credential visible in numerical publication: " + path)


def total(paths, reader):
    size = sum(len(reader(path)) for path in paths if path in PILOT)
    if size > 6 * 1024**2:
        raise ValueError("three pilot tables exceed separate6MiB combined cap")


def names(data):
    return [path for path in data.decode().split("\0") if path]


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
            paths = names(git("ls-files", "-z", "simulation/rare_backgrounds", "reports/phase6d_*", "metadata/phase6d_*", WORKFLOW))
            if not PILOT <= set(paths):
                raise ValueError("all three verified compact pilot tables must be tracked")
            for path in paths:
                inspect(path, (REPO/path).read_bytes()); checked += 1
            total(paths, lambda path: (REPO/path).read_bytes())
        if args.staged:
            changed = names(git("diff", "--cached", "--name-only", "--no-renames", "-z"))
            index = set(names(git("ls-files", "-z")))
            for path in changed:
                if not permitted(path):
                    raise ValueError("historical/unrelated staged modification/deletion: " + path)
                if path in index:
                    inspect(path, git("show", ":"+path)); checked += 1
            total(index, lambda path: git("show", ":"+path))
        if args.outgoing:
            for commit in git("rev-list", "--reverse", args.outgoing+"..HEAD").decode().splitlines():
                changed = names(git("diff-tree", "--no-commit-id", "--name-only", "--no-renames", "-r", "-z", commit))
                tree = set(names(git("ls-tree", "-r", "--name-only", "-z", commit)))
                for path in changed:
                    if not permitted(path):
                        raise ValueError("historical/unrelated outgoing modification/deletion: " + path)
                    if path in tree:
                        inspect(path, git("show", commit+":"+path)); checked += 1
                total(tree, lambda path: git("show", commit+":"+path))
        print(f"PASS: {checked} bounded numerical payload entries inspected; no physical/CI acceptance inferred")
        return 0
    except (OSError, ValueError, UnicodeError, subprocess.CalledProcessError) as error:
        print("FAIL: "+str(error)); return 1


if __name__ == "__main__":
    raise SystemExit(main())

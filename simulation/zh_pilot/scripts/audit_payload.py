#!/usr/bin/env python3
"""Audit Phase6F source/small derived evidence; no physical readiness inference."""
import argparse
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parents[3]
CARDS = set()
WORKFLOW = ".github/workflows/zh_pilot_readiness.yml"
BLOCKED = (".root", ".lhe", ".hepmc", ".hepmc3", ".gz", ".zip", ".tar", ".tgz", ".xz", ".bz2",
           ".pdf", ".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp", ".eps", ".ps",
           ".exe", ".dll", ".so", ".pcm", ".rootmap", ".pyc", ".pkl", ".npy", ".npz", ".jsonl")
PRIVATE = re.compile(rb"(?i)(?:/home/[a-z0-9_-]+|/mnt/[a-z]/[a-z0-9_.-]+|C:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|BEGIN [A-Z ]*PRIVATE KEY)")


def permitted(path):
    return (path.startswith("simulation/zh_pilot/") or path.startswith("reports/phase6f_")
            or path.startswith("metadata/phase6f_") or path in CARDS or path == WORKFLOW)


def inspect(path, data):
    if not permitted(path):
        raise ValueError("historical/unrelated Phase6F payload: " + path)
    if path.lower().endswith(BLOCKED):
        raise ValueError("physical/binary/archive/figure/full-event-table payload forbidden: " + path)
    if any(part.lower() in {"vendor", "external", "build", "downloads", "lib", "lib64", "__pycache__"} for part in path.split("/")):
        raise ValueError("vendored source/install/cache forbidden: " + path)
    if len(data) > 2 * 1024**2:
        raise ValueError("small derived text evidence exceeds 2MiB per-file cap: " + path)
    data.decode("utf-8")
    if path.lower().endswith(".md"):
        data = data.replace(b"/mnt/" + b"c/HH", b"[DOCUMENTED_REPOSITORY_PATH]")
    if PRIVATE.search(data):
        raise ValueError("private path/credential visible: " + path)


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def names(data):
    return [item for item in data.decode("utf-8").split("\0") if item]


def total(paths, reader):
    size = sum(len(reader(path)) for path in paths if permitted(path))
    if size > 6 * 1024**2:
        raise ValueError("complete Phase6F text/derived-evidence payload exceeds 6MiB cap")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracked", action="store_true")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--outgoing", metavar="BASE")
    args = parser.parse_args()
    if not (args.tracked or args.staged or args.outgoing):
        parser.error("choose a payload audit scope")
    checked = 0
    try:
        if args.tracked:
            paths = [path for path in names(git("ls-files", "-z")) if permitted(path)]
            if not CARDS <= set(paths):
                raise ValueError("all three new process proposals must be tracked")
            for path in paths:
                inspect(path, (REPO / path).read_bytes()); checked += 1
            total(paths, lambda path: (REPO / path).read_bytes())
        if args.staged:
            changed = names(git("diff", "--cached", "--name-only", "--no-renames", "-z"))
            index = set(names(git("ls-files", "-z")))
            for path in changed:
                if not permitted(path):
                    raise ValueError("historical/unrelated staged modification/deletion: " + path)
                if path in index:
                    inspect(path, git("show", ":" + path)); checked += 1
            total(index, lambda path: git("show", ":" + path))
        if args.outgoing:
            for commit in git("rev-list", "--reverse", args.outgoing + "..HEAD").decode().splitlines():
                changed = names(git("diff-tree", "--no-commit-id", "--name-only", "--no-renames", "-r", "-z", commit))
                tree = set(names(git("ls-tree", "-r", "--name-only", "-z", commit)))
                for path in changed:
                    if not permitted(path):
                        raise ValueError("historical/unrelated outgoing modification/deletion: " + path)
                    if path in tree:
                        inspect(path, git("show", commit + ":" + path)); checked += 1
                total(tree, lambda path: git("show", commit + ":" + path))
        print(f"PASS: {checked} small text payload entries inspected; no physical calibration/production inferred")
        return 0
    except (OSError, ValueError, UnicodeError, subprocess.CalledProcessError) as error:
        print("FAIL: " + str(error)); return 1


if __name__ == "__main__":
    raise SystemExit(main())

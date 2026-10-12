#!/usr/bin/env python3
"""Materialize official pinned source with upstream release-directory packaging.

Implements only bin/create_release.py's directory packaging (lines 249-267),
without its upstream maintainer tag/push operations. Never changes physics code.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

COMMIT = "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--checkout", type=Path, required=True)
parser.add_argument("--destination", type=Path, required=True)
args = parser.parse_args()
source = args.checkout.resolve()
destination = args.destination.resolve()
head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
if head != COMMIT or destination.exists():
    parser.error("requires pinned official checkout and a new destination")
archive = subprocess.check_output(["git", "-C", str(source), "archive", "--format=tar", "HEAD"])
destination.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
    stream.extractall(destination, filter="data")
removed = []
renamed = {}
for path in (destination / "bin").iterdir():
    if not str(path).endswith(("mg5", "mg5_aMC")):
        if "compile.py" not in path.name:
            if not path.is_file():
                raise SystemExit("unexpected non-file upstream bin member")
            removed.append(str(path.relative_to(destination)))
            path.unlink()
        else:
            target = path.with_name(path.name.replace("compile.py", ".compile.py"))
            renamed[str(path.relative_to(destination))] = str(target.relative_to(destination))
            path.rename(target)
(destination / "README.developer").unlink()
removed.append("README.developer")
(destination / "README.release").rename(destination / "README")
renamed["README.release"] = "README"
retained = {}
for path in sorted(destination.rglob("*")):
    if path.is_file():
        relative = str(path.relative_to(destination))
        retained[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
recipe = source / "bin/create_release.py"
identity = {"schema_version": 1, "source_commit": head, "source_tag": "v3.5.16",
            "source_url": "https://github.com/mg5amcnlo/mg5amcnlo.git",
            "source_archive_sha256": hashlib.sha256(archive).hexdigest(),
            "upstream_packaging_recipe_sha256": hashlib.sha256(recipe.read_bytes()).hexdigest(),
            "packaging": "upstream bin/create_release.py directory transformations only",
            "removed_developer_utilities": sorted(removed), "renamed": renamed,
            "retained_file_sha256": retained,
            "physics_source_changes": []}
(destination / ".phase6a_source_identity.json").write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
print("Packaged", len(retained), "unchanged upstream files; removed only upstream developer utilities")
print("Source archive SHA256:", identity["source_archive_sha256"])

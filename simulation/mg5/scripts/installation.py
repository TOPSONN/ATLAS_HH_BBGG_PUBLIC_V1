"""Verify the pinned release-mode MG5 installation against its source snapshot."""
import hashlib
import json
from pathlib import Path

COMMIT = "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"


def verify(config):
    mg5 = Path(config["mg5_path"]).resolve()
    identity_path = mg5 / ".phase6a_source_identity.json"
    identity = json.loads(identity_path.read_text())
    if identity["source_commit"] != COMMIT or config["source_commit"] != COMMIT:
        raise ValueError("MG5 differs from the pinned official source")
    if (mg5 / "bin/create_release.py").exists():
        raise ValueError("use the documented upstream release-directory packaging")
    for name, expected in identity["retained_file_sha256"].items():
        path = mg5 / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("installed MG5 source changed: " + name)
    return mg5, identity

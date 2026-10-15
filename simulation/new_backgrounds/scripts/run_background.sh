#!/usr/bin/env bash
# Explicit command requests one bounded fresh source; personal outputs stay local.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$script_dir/../controller.py" "$@"

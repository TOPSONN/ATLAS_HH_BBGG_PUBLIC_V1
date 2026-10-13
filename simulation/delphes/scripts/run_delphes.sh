#!/usr/bin/env bash
# Reuse the verified local installation; personal runs remain outside Git.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/../../.." && pwd)"
config="${DELPHES_LOCAL_CONFIG:-$repo_dir/.local/delphes_installation.json}"
[[ -f "$config" ]] || { echo "Missing verified Delphes installation contract: $config" >&2; exit 2; }
exec python3 -B "$script_dir/run_delphes.py" --installation "$config" "$@"

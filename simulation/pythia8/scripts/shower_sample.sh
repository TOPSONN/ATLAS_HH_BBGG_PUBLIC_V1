#!/usr/bin/env bash
# Reuses the verified isolated install. Personal output stays local.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/../../.." && pwd)"
config="${PYTHIA8_LOCAL_CONFIG:-$repo_dir/.local/pythia8_installation.json}"
[[ -f "$config" ]] || { echo "Missing isolated Pythia/HepMC installation config: $config" >&2; exit 2; }
exec python3 "$script_dir/shower_sample.py" --installation "$config" "$@"

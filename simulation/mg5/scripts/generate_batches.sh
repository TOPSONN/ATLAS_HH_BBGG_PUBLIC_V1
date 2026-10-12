#!/usr/bin/env bash
# User initiated sequential samples; publication is a separate explicit action.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/../../.." && pwd)"
config="${MG5_LOCAL_CONFIG:-$repo_dir/.local/mg5_installation.json}"
[[ -f "$config" ]] || { echo "Missing local installation config: $config" >&2; exit 2; }
toolchain="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["toolchain_prefix"])' "$config")"
conda_sh="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["conda_sh"])' "$config")"
source "$conda_sh"
conda activate "$toolchain"
exec python "$script_dir/generate_batches.py" --installation "$config" "$@"

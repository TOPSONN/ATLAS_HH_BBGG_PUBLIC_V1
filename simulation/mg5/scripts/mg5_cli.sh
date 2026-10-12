#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/../../.." && pwd)"
config="${MG5_LOCAL_CONFIG:-$repo_dir/.local/mg5_installation.json}"
[[ -f "$config" ]] || { echo "Missing local installation config: $config" >&2; exit 2; }
mapfile -t paths < <(python3 -c 'import json,sys; c=json.load(open(sys.argv[1])); print(c["conda_sh"]); print(c["toolchain_prefix"]); print(c["mg5_path"])' "$config")
source "${paths[0]}"
conda activate "${paths[1]}"
exec python "${paths[2]}/bin/mg5_aMC" "$@"

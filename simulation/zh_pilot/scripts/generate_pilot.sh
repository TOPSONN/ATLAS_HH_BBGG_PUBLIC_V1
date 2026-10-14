#!/usr/bin/env bash
# Phase6F prepares local text only. No production path is enabled.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$script_dir/prepare_pilot.py" "$@"

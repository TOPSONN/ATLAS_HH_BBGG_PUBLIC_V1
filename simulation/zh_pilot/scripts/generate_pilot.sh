#!/usr/bin/env bash
# Phase6G retains text-only dry-run and requires a separate one-use human ticket.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$script_dir/../phase6g/controller.py" "$@"

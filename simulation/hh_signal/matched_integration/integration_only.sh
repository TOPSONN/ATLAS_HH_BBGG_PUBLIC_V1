#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$here/../../.."
exec python3 -B -m simulation.hh_signal.matched_integration.controller "$@"

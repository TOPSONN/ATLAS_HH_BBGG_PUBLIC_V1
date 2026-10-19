#!/usr/bin/env python3
"""Inspect JSON/comment-only proposals; contains no generator execution path."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis/phase10/source"))
from generator_schemes import validate_pilot_contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path,
                        default=ROOT / "analysis/phase10/config/generator_pilot_contract.json")
    parser.add_argument("--scheme-review", type=Path,
                        default=ROOT / "metadata/phase10_generator_scheme_review.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    review = json.loads(args.scheme_review.read_text())
    result = validate_pilot_contract(contract, review, ROOT)
    if args.output:
        artifact = dict(contract)
        artifact["offline_validation"] = result
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid_inactive_contract"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

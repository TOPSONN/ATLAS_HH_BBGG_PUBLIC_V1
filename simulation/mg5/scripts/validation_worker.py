#!/usr/bin/env python3
"""Internal worker lets the generation controller enforce limits during validation."""
import argparse
import json
from pathlib import Path

from validate_sample import validate_file

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--file", type=Path, required=True)
parser.add_argument("--events", type=int, required=True)
parser.add_argument("--profile", required=True)
parser.add_argument("--beam-energy", type=float, required=True)
parser.add_argument("--seed", type=int, required=True)
parser.add_argument("--result", type=Path, required=True)
parser.add_argument("--manifest", type=Path)
parser.add_argument("--generator-original", action="store_true")
args = parser.parse_args()
result = validate_file(args.file, args.events, profile=args.profile, beam_energy=args.beam_energy,
                       expected_seed=args.seed, manifest=args.manifest,
                       require_deterministic=not args.generator_original)
args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

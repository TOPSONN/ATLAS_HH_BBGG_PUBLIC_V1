#!/usr/bin/env python3
"""Portable frozen source/method evidence validation; no generator invocation."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.hh_signal.contracts import verify_bundle

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
    args=parser.parse_args()
    manifest=verify_bundle(args.repo)
    print('PASS_FROZEN_SIGNAL_READINESS_BUNDLE',len(manifest['project_bindings']),
          'bindings; physical events=0; real closure NOT_EVALUATED')
if __name__=='__main__': main()

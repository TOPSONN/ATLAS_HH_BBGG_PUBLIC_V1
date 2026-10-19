#!/usr/bin/env python3
"""Download one reviewed official PDF member into the fixed fresh isolated folder."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from pdf_acquisition import acquire
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);a=p.parse_args();r=acquire(json.loads(a.contract.read_text()));print(json.dumps({k:r[k] for k in ('status','aggregate_body_bytes','candidate','member')}))

#!/usr/bin/env python3
"""Only fixed inert controller-loss proof. Does not invoke a parser."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from envelope import run_case,new_json
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
value=run_case('controller_loss',a.output,lose_controller=True)
new_json(a.output/'controller_return.json',value)
os._exit(0)

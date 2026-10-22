"""Versioned pure G2 DAG using the preserved Master lock/child/ledger engine."""
import argparse,json,sys
from pathlib import Path
from unittest.mock import patch
from . import readiness_runner as engine,ledger
from .contract import REPO,canonical,git,load,need,no_links,sha

BASE='6126b315834715983481802f35630742accf1d88'
PROGRESS=REPO/'.local/g2_progress_v1'
STAGES=('R0_EXACT_BASE_AND_EVIDENCE','R1_G1_FINAL_EVIDENCE_RECONCILIATION','R2_CPU_CAPABILITY_AND_ACCOUNTING',
 'R3_MEMORY_SWAP_CAPABILITY','R4_WALL_AND_LIFECYCLE_MODEL','R5_ARCHITECTURE_A_FEASIBILITY','R6_B_V2_CLAUSE_AND_COST_REVIEW',
 'R7_FINAL_OBSERVER_AND_G3_SOURCE_GAPS','R8_G4_G7_DEPLOYMENT_FEASIBILITY','R9_SCIENTIFIC_RESTART_PREFLIGHT',
 'R10_INDEPENDENT_VERIFICATION','R11_CI_AND_PUBLICATION')
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv.pop(1));from simulation.hh_signal.final_closure.master.g2_worker import main;raise SystemExit(main())'
EXTERNAL={'host':'8e16a1e0d90b62b63c91ca0852aff19e848752440f047246a966ad65d21c06b5',
 'guest':'c575418ca9c4a63c8ea6e53404652b4b190b03e2e5c65ada4321880c2cb87cbc'}
MASTER_CHECK=engine.check

def binding(capture,running=None,guest=None):
 need(running is None,'NO_NEW_RUNNING_OR_GUEST_QUERY');need(not git('status','--porcelain','--untracked-files=no'),'TRACKED_SOURCE_DIRTY')
 need(git('merge-base',BASE,'HEAD').decode().strip()==BASE,'EXACT_PR42_ANCESTRY')
 old=load(REPO/'reports/g1_guest_v2_counter_repair/SOURCE_MANIFEST.json')
 frozen={r['path']:r['sha256'] for r in old['files']}
 names=set(frozen)|{p.relative_to(REPO).as_posix() for p in (REPO/'simulation/hh_signal/final_closure/master').glob('g2_*') if p.suffix=='.py'}|{'.github/workflows/g2_actual_capability.yml'}
 source=[engine.source_row(n,frozen) for n in sorted(names)]
 from ..src.contracts import input_identity
 inputs=[{'path':r['path'],'sha256':r['sha256']} for r in input_identity()]
 external={}
 for name,path in (('host',capture),('guest',guest)):
  need(path is not None,'IMMUTABLE_EXISTING_INPUT_REQUIRED');p=no_links(Path(path))
  need(p.is_file() and p.stat().st_size<=262144,'EXTERNAL_BOUND')
  digest=sha(p.read_bytes());need(digest==EXTERNAL[name],'NEW_INPUT_REQUIRES_NEW_REVIEWED_PROFILE')
  external[name]={'path':str(p),'sha256':digest}
 external['running']=None
 v={'schema':'HH_G2_SAFE_CONTEXT_V1','revision':git('rev-parse','HEAD').decode().strip(),'base':BASE,
  'source_rows':source,'source_sha256':sha(canonical(source)),'inputs_sha256':sha(canonical(inputs)),
  'frozen_inputs':inputs,'host_capture':external['host'],'external':external,'scope':'G2_ENGINEERING_EXISTING_INPUTS_NO_LIVE_DISPATCH'}
 v['scope_identity']=sha(canonical(v));return v

def check(run):
 c=MASTER_CHECK(run)
 for event in ledger.events(run):
  need(event.get('external_input_sha256')=={n:c['external'][n]['sha256'] for n in ('host','guest')} and event.get('scope_identity')==c['scope_identity'],'G2_LEDGER_EXTERNAL_OR_SCOPE_DRIFT')
 return c

def invoke(mode,*,capture=None,guest=None,run_id=None):
 with patch.multiple(engine,BASE=BASE,PROGRESS=PROGRESS,STAGES=STAGES,BOOTSTRAP=BOOTSTRAP,binding=binding,check=check):
  if mode=='run-safe':return engine.execute(engine.new_run(capture,None,guest))
  run=engine.run_path(run_id)
  if mode=='resume-safe':return engine.execute(run)
  if mode=='status':return engine.status(run)
  if mode=='verify':engine.check(run);return ledger.verify(run)
  raise ValueError('NO_LIVE_OR_APPROVAL_MODE')

def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);s=p.add_subparsers(dest='mode',required=True)
 s.add_parser('plan',allow_abbrev=False)
 a=s.add_parser('run-safe',allow_abbrev=False);a.add_argument('--host-capture',type=Path,required=True);a.add_argument('--guest-capture',type=Path,required=True)
 for name in ('resume-safe','status','verify'):s.add_parser(name,allow_abbrev=False).add_argument('--run-id',required=True)
 a=p.parse_args(argv)
 try:
  if a.mode=='plan':v={'stages':STAGES,'live_dispatcher':False,'execution_authorized':False,'reuses_master_child_lock_ledger':True}
  else:v=invoke(a.mode,capture=getattr(a,'host_capture',None),guest=getattr(a,'guest_capture',None),run_id=getattr(a,'run_id',None))
  print(json.dumps(v,indent=2));return 2 if v.get('status') in ('UNKNOWN','FAIL') else 0
 except (ValueError,OSError,KeyError,TypeError):print(json.dumps({'status':'FAIL','reason':'G2_SAFE_PROFILE_VALIDATION','execution_authorized':False}));return 2

if __name__=='__main__':raise SystemExit(main())

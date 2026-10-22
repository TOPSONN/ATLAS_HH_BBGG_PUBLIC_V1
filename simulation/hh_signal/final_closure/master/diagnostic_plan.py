"""New immutable engineering profile; never dispatches the actual adapter."""
from pathlib import Path
from unittest.mock import patch
from . import g2_runner as prior,readiness_runner as engine
from .contract import REPO,canonical,sha,git,load,need
BASE='d66585fdb29c6d9262f9059ac27aaca45ed84704'
PRIOR_BINDING=prior.binding
PROGRESS=REPO/'.local/diagnostic_preparation_v1'
STAGES=('D0_SOURCE_AND_EVIDENCE_IDENTITY','D1_TOOL_BINARY_BINDING','D2_SYSTEMD_MANAGER_QUERY_REVIEW',
 'D3_DELEGATION_QUERY_REVIEW','D4_BOUNDED_DIAGNOSTIC_IMPLEMENTATION','D5_INDEPENDENT_RECEIPT_VALIDATION',
 'D6_G2_A_B_CAPABILITY_AND_COST_REVIEW','D7_GUEST_ASYNC_KERNEL_COST_REVIEW','D8_G3_DEPLOYMENT_GAP_REVIEW',
 'D9_G4_G7_MINIMUM_CAPABILITY_PATH','D10_SCIENTIFIC_CONTINUATION_FEASIBILITY','D11_REGRESSION_AND_PUBLICATION')
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv.pop(1));from simulation.hh_signal.final_closure.master.diagnostic_worker import main;raise SystemExit(main())'
def binding(capture,running=None,guest=None):
 c=PRIOR_BINDING(capture,running,guest);need(git('merge-base',BASE,'HEAD').decode().strip()==BASE,'EXACT_PR43_ANCESTRY')
 baseline=load(REPO/'reports/phase7i_g2_actual_capability/SOURCE_MANIFEST.json')['files']
 names={r['path'] for r in baseline}|{p.relative_to(REPO).as_posix() for p in (REPO/'simulation/hh_signal/final_closure/master').glob('diagnostic_*.py')}|{'.github/workflows/g2_effective_diagnostic.yml'}
 old={r['path']:r['sha256'] for r in baseline}
 c['source_rows']=[engine.source_row(n,old) for n in sorted(names)];c['source_sha256']=sha(canonical(c['source_rows']))
 c['base']=BASE;c['scope']='G2_EFFECTIVE_DIAGNOSTIC_PREPARATION_NO_ACQUISITION';c.pop('scope_identity')
 c['scope_identity']=sha(canonical(c));return c
def main(argv=None):
 with patch.multiple(prior,BASE=BASE,PROGRESS=PROGRESS,STAGES=STAGES,BOOTSTRAP=BOOTSTRAP,binding=binding):
  return prior.main(argv)
if __name__=='__main__':raise SystemExit(main())

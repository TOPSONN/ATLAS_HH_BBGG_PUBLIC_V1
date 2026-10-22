"""Preserved child audit, new fixed preparation stages only."""
from unittest.mock import patch
from . import readiness_worker as worker,readiness_stages,diagnostic_plan,diagnostic_stages
def main():
 with patch.multiple(worker,STAGES=diagnostic_plan.STAGES,PROGRESS=diagnostic_plan.PROGRESS),patch.object(readiness_stages,'TASKS',diagnostic_stages.TASKS):return worker.main()
if __name__=='__main__':raise SystemExit(main())

"""Fixed pure/read-existing G2 child; uses the old worker audit policy."""
from unittest.mock import patch
from . import readiness_worker as worker,g2_runner,g2_stages
def main():
 # Existing worker dynamically imports readiness_stages after enabling its audit.
 # Replace only the fixed stage table; no looser I/O policy or new dispatcher.
 from . import readiness_stages
 with patch.multiple(worker,STAGES=g2_runner.STAGES,PROGRESS=g2_runner.PROGRESS),patch.object(readiness_stages,'TASKS',g2_stages.TASKS):
  return worker.main()
if __name__=='__main__':raise SystemExit(main())

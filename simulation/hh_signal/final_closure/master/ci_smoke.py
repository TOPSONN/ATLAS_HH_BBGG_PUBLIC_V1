"""Actual safe CLI smoke after run-safe; never launches a live stage."""
import contextlib,io,json,sys
from .contract import need
from . import ledger,runner
def main():
 run_id=sys.argv[1];run=runner.run_path(run_id);before=ledger.events(run)
 for mode in ('resume-safe','status','verify','export-review'):
  stream=io.StringIO()
  with contextlib.redirect_stdout(stream):code=runner.main([mode,'--run-id',run_id])
  need(code==0,'SAFE_CLI_SMOKE_FAILURE:'+mode)
  need(ledger.events(run)==before,'RESUME_REEXECUTED_OR_REWROTE_LEDGER')
  print(json.dumps({'mode':mode,'exit_status':code,'ledger_events_unchanged':True}))
 need(not any(r['status']=='FAIL' for r in before),'SAFE_TASK_FAILURE')
 print(json.dumps({'status':'PASS_SOURCE_ONLY','actual_safe_subprocesses':sum(r['real_subprocess_exit_status'] is not None for r in before),'live_dispatches':0}));return 0
if __name__=='__main__':raise SystemExit(main())

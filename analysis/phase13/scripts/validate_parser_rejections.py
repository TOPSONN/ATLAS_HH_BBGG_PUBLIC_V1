#!/usr/bin/env python3
"""Real CLI negative tests only; no MG5 import, subprocess build or physics."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists() or not a.output.parent.is_dir() or a.output.is_symlink():raise ValueError('FRESH_REJECTION_RECEIPT_REQUIRED')
scripts=Path(__file__).resolve().parent
cases=[('launcher_missing_new_approval',[sys.executable,'-B',str(scripts/'run_parser_review.py'),'--package','/nonexistent/phase13_proposal'],'MISSING_NEW_EXPLICIT_USER_APPROVAL'),('direct_child_resource_hard_block',[sys.executable,'-B',str(scripts/'parser_child.py')],'FULL_LAUNCH_ENVELOPE_NOT_IMPLEMENTED; CHILD_DISPATCH_FORBIDDEN')]
results=[]
for name,command,reason in cases:
 done=subprocess.run(command,capture_output=True,text=True,timeout=5)
 if done.returncode!=2 or reason not in done.stdout+done.stderr:raise ValueError('NEGATIVE_ENTRYPOINT_FAILED:'+name)
 results.append({'case':name,'exit_code':done.returncode,'expected_reason_found':True,'stdout':done.stdout,'stderr':done.stderr,'command':command})
value={'schema_version':1,'evidence_class':'SYNTHETIC_METHOD_ONLY','status':'PASS_ACTUAL_NEGATIVE_CLI_REJECTIONS','tests':results,'positive_MG5_or_parser_dispatch_tested':False,'new_MG5_processes':0,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_pythia_events':0,'new_delphes_events':0}
with a.output.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
print(json.dumps({'status':value['status'],'tests':len(results),'MG5_dispatched':False}))

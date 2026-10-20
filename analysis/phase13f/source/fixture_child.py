"""Fixed inert child. No MG5/model import or executable arguments accepted."""
import argparse,sys,json,hashlib,os,errno
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workflow import action,RUNTIME
from envelope import REPO
p=argparse.ArgumentParser();p.add_argument('--mode',choices=('normal','cpu','ram','wall','disk','abnormal'),required=True);a=p.parse_args()
if a.mode!='normal':
 # Adversarial inert stand-in isolates the outer aggregate envelope. This is
 # not a production parser switch and does not disable any legacy source gate.
 try:action(a.mode)
 except OSError as e:
  print(json.dumps({'kind':'INERT_RESOURCE_STOP','errno':e.errno,'tmpfs_used_bytes':(os.statvfs('.').f_blocks-os.statvfs('.').f_bfree)*os.statvfs('.').f_frsize}),flush=True);sys.exit(73 if e.errno==errno.ENOSPC else 78)
 sys.exit(79)
sys.path.insert(0,str(REPO/'analysis/phase13/source'))
from native_guard import install,LIMITS
install([RUNTIME,Path.cwd()],LIMITS)
raw=(RUNTIME/'input/mg5_configuration.txt').read_bytes()
print(json.dumps({'kind':'INERT_CHILD','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'original_child_limits':LIMITS,'MG5_invocations':0}),flush=True)

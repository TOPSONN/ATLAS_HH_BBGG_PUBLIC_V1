#!/usr/bin/env python3
"""Future supervisor-only bootstrap. Never invoked during Phase13 validation."""
import argparse,ctypes,json,os,runpy,stat,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from parser_contract import COMMANDS,LIMITS,identity,read_json,require,FULL_LAUNCH_ENVELOPE_IMPLEMENTED
from native_guard import install

def main():
 require(FULL_LAUNCH_ENVELOPE_IMPLEMENTED,"FULL_LAUNCH_ENVELOPE_NOT_IMPLEMENTED; CHILD_DISPATCH_FORBIDDEN")
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--package',type=Path,required=True);p.add_argument('--command-file',type=Path,required=True);p.add_argument('--token-fd',type=int,required=True);p.add_argument('--supervisor',type=int,required=True)
 a=p.parse_args()
 require(a.supervisor==os.getppid() and stat.S_ISFIFO(os.fstat(a.token_fd).st_mode),'AUTHORIZED_SUPERVISOR_PIPE_REQUIRED')
 token=json.loads(os.read(a.token_fd,4096));os.close(a.token_fd)
 package=read_json(a.package)
 require(token=={'package_sha256':identity(a.package)['sha256'],'output':package['future_output'],'supervisor':a.supervisor},'SUPERVISOR_TOKEN_MISMATCH')
 require(a.command_file.read_text()=='\n'.join(COMMANDS)+'\n','EXACT_COMMAND_FILE_REQUIRED')
 require(a.command_file.resolve().parent==Path(package['future_output']),'COMMAND_FILE_OUTSIDE_APPROVED_OUTPUT')
 require(identity(Path(package['runtime_root'])/'input/mg5_configuration.txt')==package['configuration_proposal_identity'],'ACTIVATED_PRIVATE_CONFIG_REQUIRED')
 libc=ctypes.CDLL(None,use_errno=True)
 require(libc.prctl(1,9,0,0,0)==0 and os.getppid()==a.supervisor,'PARENT_DEATH_GUARD_FAILED')
 roots=[package['runtime_root'],str(Path(__file__).resolve().parents[1]),package['future_output'],*package['fresh_environment'].values()]
 roots=[str(Path(value)) for value in roots if str(value).startswith('/') and Path(value).exists()]
 for path in ('/usr','/lib','/lib64','/bin','/etc','/dev/null'):
  if Path(path).exists():roots.append(path)
 install(roots,LIMITS)
 # Guard is installed BEFORE importing MG5. No exec, children, network or write-open is permitted.
 mg5=Path(package['runtime_root'])/'bin/mg5_aMC'
 sys.path.insert(0,package['runtime_root']);sys.argv=[str(mg5),str(a.command_file)]
 runpy.run_path(str(mg5),run_name='__main__')
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError) as error:
  print('PARSER_BOOTSTRAP_REJECTED:'+str(error),file=sys.stderr);sys.exit(2)

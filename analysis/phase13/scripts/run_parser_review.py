#!/usr/bin/env python3
"""NOT AUTHORIZED IN PHASE13. Only a future new exact-scope human approval can dispatch."""
from __future__ import annotations
import argparse,fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
from parser_contract import (authorization,canonical,fresh_output,identity,no_symlink,read_json,require,runtime_check,verify_checkout,COMMANDS,LIMITS)
def members(pgid):
 result=[]
 for path in Path('/proc').iterdir():
  if not path.name.isdigit():continue
  try:
   raw=(path/'stat').read_text();fields=raw[raw.rfind(')')+2:].split()
   if int(fields[2])==pgid and fields[0] not in ('Z','X'):result.append(int(path.name))
  except (OSError,ValueError,IndexError):pass
 return result
def cleanup(proc):
 for sig in (signal.SIGTERM,signal.SIGKILL):
  if members(proc.pid):
   try:os.killpg(proc.pid,sig)
   except ProcessLookupError:pass
  stop=time.monotonic()+.5
  while members(proc.pid) and time.monotonic()<stop:time.sleep(.01)
  if not members(proc.pid):
   if proc.poll() is None:proc.wait(timeout=1)
   return
 raise RuntimeError('OWN_PROCESS_GROUP_TERMINATION_FAILED')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--approval',type=Path)
 a=p.parse_args();package,_=authorization(a.package,a.approval)
 repo=no_symlink(package['source_repository']);verify_checkout(repo,package['source_revision'],package['source_inputs'])
 before=runtime_check(package)
 require(identity(package['python']['path'])=={k:package['python'][k] for k in ('bytes','sha256')},'PYTHON_EXECUTABLE_DRIFT')
 for key in ('runtime_receipt','resource_receipt'):
  row=package[key];require(identity(row['path'])=={k:row[k] for k in ('bytes','sha256')},'REVIEW_RECEIPT_DRIFT')
 runtime=Path(package['runtime_root']);base=Path(package['runtime_receipt']['path']).resolve().parents[1]
 output=fresh_output(package['future_output'],base)
 # Current Phase13 never reaches here: a new user's approval plus terminal confirmation is required.
 with (base/'.future_parser_single_job.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  output.mkdir(mode=0o700)
  def write(name,value):
   with (output/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
  write('human_scope_confirmation.json',{'authorization_type':'NEW_USER_FILE_PLUS_EXACT_TTY_CHALLENGE','approval_sha256':identity(a.approval)['sha256'],'package_sha256':identity(a.package)['sha256'],'source_revision':package['source_revision'],'consumed_for_this_one_output':True,'automated_identity_authentication_of_human':False})
  config=runtime/'input/mg5_configuration.txt';proposal=Path(package['configuration_proposal_path'])
  raw=config.read_bytes();candidate=proposal.read_bytes()
  with (output/'private_original_copied_configuration.bin').open('xb') as stream:stream.write(raw)
  # Exact one approved config edit, only in the independent copy, never the installed runtime.
  require(config.stat().st_nlink==1 and not config.is_symlink(),'CONFIG_NOT_INDEPENDENT_REGULAR_FILE')
  with config.open('r+b') as stream:stream.write(candidate);stream.truncate()
  require(identity(config)==package['configuration_proposal_identity'],'ACTIVATION_IDENTITY_MISMATCH')
  commands=output/'reviewed_commands.txt'
  with commands.open('x') as stream:stream.write('\n'.join(COMMANDS)+'\n')
  write('attempt_started.json',{'parser_dispatch_permitted_after_new_human_confirmation':True,'source_revision':package['source_revision'],'commands':COMMANDS,'limits':LIMITS})
  outpath,errpath=output/'stdout.log',output/'stderr.log'
  env={'HOME':package['fresh_environment']['HOME'],'TMPDIR':package['fresh_environment']['TMPDIR'],'TMP':package['fresh_environment']['TMP'],'TEMP':package['fresh_environment']['TEMP'],'XDG_CONFIG_HOME':package['fresh_environment']['XDG_CONFIG_HOME'],'XDG_CACHE_HOME':package['fresh_environment']['XDG_CACHE_HOME'],'XDG_STATE_HOME':package['fresh_environment']['XDG_STATE_HOME'],'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','LANG':'C.UTF-8','PATH':'/usr/bin:/bin'}
  rfd,wfd=os.pipe();start=time.monotonic();proc=None;reason=None
  try:
   with outpath.open('xb') as out,errpath.open('xb') as err:
    proc=subprocess.Popen([package['python']['path'],'-B','-s',str(repo/'analysis/phase13/scripts/parser_child.py'),'--package',str(a.package.resolve()),'--command-file',str(commands),'--token-fd',str(rfd),'--supervisor',str(os.getpid())],stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,cwd=output,start_new_session=True,pass_fds=(rfd,))
    os.close(rfd);rfd=-1;os.write(wfd,json.dumps({'package_sha256':identity(a.package)['sha256'],'output':str(output),'supervisor':os.getpid()}).encode());os.close(wfd);wfd=-1
    while proc.poll() is None:
     if time.monotonic()-start>LIMITS['wall_seconds']:reason='WALL_LIMIT';cleanup(proc);break
     time.sleep(.01)
    if members(proc.pid):reason='UNEXPECTED_DESCENDANT';cleanup(proc)
    proc.wait(timeout=1)
    if proc.returncode and reason is None:reason='NATIVE_CHILD_NONZERO_OR_GUARD_STOP'
  finally:
   for fd in (rfd,wfd):
    if fd>=0:os.close(fd)
   if proc is not None and members(proc.pid):cleanup(proc)
   after_package=dict(package);after_package['raw_configuration_identity']=package['configuration_proposal_identity']
   from runtime_layout import inspect_tree
   after=inspect_tree(runtime,{'max_single_file_bytes':64*1024**2,'max_entries':10000,'max_total_regular_bytes':512*1024**2})
   b={row['relative_path']:row for row in before['entries']};c={row['relative_path']:row for row in after['entries']}
   differences=[name for name in sorted(set(b)|set(c)) if b.get(name)!=c.get(name)]
   closed=(differences==['input/mg5_configuration.txt'] and identity(config)==package['configuration_proposal_identity'])
   if not closed:reason='UNEXPECTED_RUNTIME_SOURCE_WRITE'
   write('parser_execution_receipt.json',{'schema_version':1,'evidence_class':'FUTURE_ACTUAL_SYMBOLIC_PARSER_ATTEMPT','source_revision':package['source_revision'],'package_sha256':identity(a.package)['sha256'],'approval_sha256':identity(a.approval)['sha256'],'runtime_before':before['content_manifest_sha256'],'runtime_after':after['content_manifest_sha256'],'only_preapproved_private_config_activation_changed':closed,'exit_code':None if proc is None else proc.poll(),'resource_stop':reason,'wall_seconds':time.monotonic()-start,'stdout_sha256':identity(outpath)['sha256'] if outpath.exists() else None,'stderr_sha256':identity(errpath)['sha256'] if errpath.exists() else None,'parser_completed':bool(proc and proc.returncode==0 and reason is None),'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_pythia_events':0,'new_delphes_events':0,'counter_basis':'exact symbolic-only command scope; not a numerical-ME instrumentation proof','numerical_MG5_PDF_binding':'UNVERIFIED','physical_pilot_authorized':False})
  require(proc is not None and proc.returncode==0 and reason is None,'PARSER_ATTEMPT_STOPPED:'+str(reason))
  print(json.dumps({'status':'COMPLETED_SYMBOLIC_PARSER_ONLY','output':str(output),'physical_pilot_authorized':False}))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError,RuntimeError,subprocess.SubprocessError) as error:
  print(json.dumps({'status':'BLOCKED_PHASE13_PARSER_CONTRACT','reason':str(error),'no_further_production_authorized':True}));sys.exit(2)

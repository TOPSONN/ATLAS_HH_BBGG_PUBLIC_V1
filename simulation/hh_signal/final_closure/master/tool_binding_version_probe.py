"""Separately approved version-only candidate; no manager/bus/cgroup query."""
import os,re,sys,time
from pathlib import Path
from . import diagnostic_contract as c,diagnostic_capture as original,diagnostic_tools as tools
from . import tool_binding_review as review,tool_binding_elf as elf
EXTRA=('tool_binding_version_probe.py','tool_binding_review.py','tool_binding_elf.py')
VERSION_OUTPUT='/home/btu/simulations/hh_final_closure/g2_tool_version_probe_01'
def pending(revision,extra_hashes):
 return {'schema':'HH_G2_VERSION_ONLY_SCOPE_V1','source_revision':revision,'source_sha256':dict(review.SOURCES,**extra_hashes),
  'tool_sha256':dict(review.TOOLS),'uid':1000,'gid':1000,'argv':['/usr/bin/systemctl','--version'],'environment':c.environment(1000),
  'output':VERSION_OUTPUT,'authorization_reference':None,'execution_authorized':False,'limits':dict(review.LIMITS)}
def check(scope):
 c.need(type(scope) is dict,'VERSION_SCOPE')
 c.need(scope.get('schema')=='HH_G2_VERSION_ONLY_SCOPE_V1','VERSION_SCOPE')
 c.need(type(scope['source_revision']) is str and re.fullmatch('[0-9a-f]{40}',scope['source_revision']) is not None,'VERSION_REVISION')
 c.need(scope['tool_sha256']==review.TOOLS and scope['uid']==scope['gid']==1000 and type(scope['uid']) is int and type(scope['gid']) is int,'VERSION_TOOL_UID_BINDING')
 c.need(scope['argv']==['/usr/bin/systemctl','--version'] and scope['environment']==c.environment(1000),'VERSION_FIXED_COMMAND')
 c.need(scope['limits']==review.LIMITS and scope['output']==VERSION_OUTPUT,'VERSION_LIMITS_OUTPUT')
 for value in scope['limits'].values():c.u64(value)
 c.need(set(scope['source_sha256'])==set(review.SOURCES)|set(EXTRA),'VERSION_SOURCE_SET')
 for h in scope['source_sha256'].values():c.need(type(h) is str and re.fullmatch('[0-9a-f]{64}',h) is not None,'VERSION_SOURCE_SHA256')
 for name,h in review.SOURCES.items():c.need(scope['source_sha256'][name]==h,'ORIGINAL_SOURCE_DRIFT')
 c.need(scope.get('authorization_reference') is not None,'BLOCKED_AUTHORIZATION')
 # The reference is supplied by an external human review. This code creates none.
 c.need(type(scope['authorization_reference']) is str and len(scope['authorization_reference'])==64 and all(ch in '0123456789abcdef' for ch in scope['authorization_reference']),'AUTHORIZATION_REFERENCE')
 c.need(scope['execution_authorized'] is False,'FLAG_CANNOT_GRANT_EXECUTION')
def run(scope):
 check(scope)
 c.need(sys.platform=='linux' and tuple(sys.version_info[:3])==(3,12,3),'OBSERVED_PYTHON3123_LINUX')
 c.need(os.getuid()==os.geteuid()==1000 and os.getgid()==os.getegid()==1000,'NONROOT_IDENTITY')
 for name,h in scope['source_sha256'].items():c.need(c.sha(original.bounded_bytes(Path(__file__).parent/name))==h,'SOURCE_HASH')
 for path,h in review.TOOLS.items():c.need(tools.identity(path)['sha256']==h,'TOOL_CHANGED')
 actual=os.stat('/proc/self/exe');expected=os.stat('/usr/bin/python3');c.need((actual.st_dev,actual.st_ino)==(expected.st_dev,expected.st_ino),'RUNNING_PYTHON_IDENTITY')
 # Reuse the same exclusive private writer; only this separate reviewed directory.
 folder=original.private_output({'output':VERSION_OUTPUT,'uid':1000});began=time.monotonic_ns()
 original.write_private(folder,'attempt.json',c.canonical({'scope_sha256':c.sha(c.canonical(scope)),'single_use_consumed':True})+b'\n')
 fd=None
 try:
  fd=os.open('/usr/bin/systemctl',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);info=os.fstat(fd)
  c.need(info.st_uid==0 and not info.st_mode&0o6022 and info.st_size<=tools.MAX_BINARY,'PINNED_ELF_PERMISSIONS')
  data=bytearray()
  while True:
   b=os.read(fd,1024*1024)
   if not b:break
   data.extend(b);c.need(len(data)<=tools.MAX_BINARY,'ELF_BOUND')
  c.need(c.sha(data)==review.TOOLS['/usr/bin/systemctl'],'PINNED_TOOL_DRIFT')
  static=elf.inspect(bytes(data));row=original.child(scope['argv'],fd,scope['environment'])
  result=review.version_result(row)
  receipt={'schema':'HH_G2_VERSION_ONLY_RECEIPT_V1','source_revision':scope['source_revision'],'scope_sha256':c.sha(c.canonical(scope)),
   'tool_sha256':dict(review.TOOLS),'source_sha256':scope['source_sha256'],'uid':1000,'gid':1000,'python_version':list(sys.version_info[:3]),
   'start_ns':began,'end_ns':time.monotonic_ns(),'query':row,'version_review':result,'systemctl_static_ELF':static,
   'bus_queries':0,'complete_diagnostic_executed':False,'dependency_closure_verified':False,'authorization_reference':scope['authorization_reference']}
  c.need(receipt['end_ns']-began<=30_000_000_000,'VERSION_ADAPTER_SOFT_TIME')
  raw=c.canonical(receipt)+b'\n';original.write_private(folder,'receipt.json',raw);original.write_private(folder,'receipt.sha256',(c.sha(raw)+'\n').encode())
  return {'status':result['status'],'receipt_sha256':c.sha(raw),'automatic_retry':False,'dependency_closure_verified':False}
 finally:
  if fd is not None:os.close(fd)
  os.close(folder)
def main(argv=None):
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--scope',required=True,type=Path);a=p.parse_args(argv)
 try:v=run(c.load(original.bounded_bytes(a.scope)));print(c.canonical(v).decode());return 0 if v['status']=='OBSERVED_CLIENT_V255_NOT_MANAGER_ATTESTATION' else 2
 except (OSError,ValueError,KeyError,TypeError):print('{"status":"BLOCKED_VERSION_SCOPE_OR_RUNTIME","automatic_retry":false}');return 2
if __name__=='__main__':raise SystemExit(main())

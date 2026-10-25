"""Versioned entry over the preserved adapter. No ordinary-path scope import."""
import os,sys
from . import manager_scope_contract as c,manager_scope_fs as fs,manager_scope_loader as loader
from . import diagnostic_capture as old,diagnostic_contract as original
def file_proof(pin):return {'name':pin.name,'sha256':c.sha(pin.raw),'identity':fs.ident(os.fstat(pin.fd))}
def initial_matches(pin,identity):
 now=os.fstat(pin.fd);c.need(all(getattr(now,k)==v for k,v in identity.items()),'BOOTSTRAP_TO_SECURE_FD_INSTANCE')
def run(manifest_raw,scope_raw,approval_raw,manifest_sha,scope_sha,approval_sha,initial_ids,source_ids):
 scope=c.load(scope_raw);record,m=c.approval(scope,scope_raw,scope_sha,approval_raw,approval_sha,manifest_raw)
 original.checked_scope(scope)
 c.need(sys.platform=='linux' and tuple(sys.version_info[:3])==(3,12,3) and sys.flags.isolated and sys.flags.no_site,'PYTHON3123_ISOLATED_NO_SITE')
 c.need(os.getuid()==os.geteuid()==os.getgid()==os.getegid()==1000,'EXACT_NONROOT_IDENTITY')
 stores=[];pins=[];output=None;old_output=old.private_output
 try:
  for key in ('scope_store','source_store','output_parent_store'):
   spec=m[key];stores.append(fs.Store(spec['path'],spec['policy'],private=key!='output_parent_store'))
  scope_store,source_store,parent=stores
  inputs={'runtime_manifest.json':(manifest_raw,manifest_sha),'scope.json':(scope_raw,scope_sha),'approval.json':(approval_raw,approval_sha)}
  for name,(raw,digest) in inputs.items():
   pin=scope_store.pin(name,digest);pins.append(pin);c.need(pin.raw==raw,'ORIGINAL_INPUT_INSTANCE_BYTES');initial_matches(pin,initial_ids[name])
  source_pins,raws=loader.pin_sources(source_store,m['source_closure_sha256']);pins.extend(source_pins)
  for pin in source_pins:initial_matches(pin,source_ids[pin.name])
  dependencies=loader.dependency_check(m)
  # Fixed file hashes do not verify the child's dynamic resolution / plugins.
  # This revision deliberately cannot turn an allowlist assertion into closure.
  c.need(dependencies['transitive_mapping_attested'] is True,'BLOCKED_DEPENDENCY_CLOSURE_DYNAMIC_RESOLUTION_NOT_VERIFIED')
  for pin in pins:pin.verify()
  before={'scope_store':scope_store.proof(),'source_store':source_store.proof(),'inputs':[file_proof(p) for p in pins[:3]],'source_files':[file_proof(p) for p in source_pins]}
  output=fs.create_private(parent,'g2_effective_diagnostic_01');stores.append(output)
  pre=output.write_new('security_attempt.json',c.canonical({'scope_raw_sha256':scope_sha,'approval_record_sha256':approval_sha,'runtime_manifest_sha256':manifest_sha,'single_use_consumed':True})+b'\n');pre.close()
  def guarded_output(s):
   c.need(s['output']==scope['output'],'FIXED_OUTPUT');output.verify();return os.dup(output.fd)
  old.private_output=guarded_output
  result=old.capture(scope)
  # Captured output is untrusted until the independent validator checks original bytes.
  receipt_pin=output.pin('receipt.json',result['sha256']);pins.append(receipt_pin)
  for pin in pins:pin.verify()
  after={'scope_store':scope_store.proof(),'source_store':source_store.proof(),'inputs':[file_proof(p) for p in pins[:3]],'source_files':[file_proof(p) for p in source_pins]}
  envelope={'schema':'HH_G2_MANAGER_SECURITY_RECEIPT_V1','source_revision':scope['source_revision'],'source_closure_sha256':m['source_closure_sha256'],'scope_raw_sha256':scope_sha,'approval_record_sha256':approval_sha,'runtime_manifest_sha256':manifest_sha,'original_manager_receipt_sha256':result['sha256'],'before_launch':before,'after_capture':after,'dependencies':dependencies,'host_attestation':False,'actual_job_enforcement':False,'automatic_retry':False}
  raw=c.canonical(envelope)+b'\n';security=output.write_new('security_receipt.json',raw);security.close()
  checksum=output.write_new('security_receipt.sha256',(c.sha(raw)+'\n').encode());checksum.close()
  return {'status':'CAPTURED_UNATTESTED_READ_ONLY_SECURITY_BOUND' if result['status']=='CAPTURED_UNATTESTED_READ_ONLY' else 'PARTIAL_CAPTURE_STOPPED','receipt_sha256':result['sha256'],'security_receipt_sha256':c.sha(raw),'automatic_retry':False,'actual_job_enforcement':False}
 finally:
  old.private_output=old_output
  for p in pins:p.close()
  for store in reversed(stores):store.close()

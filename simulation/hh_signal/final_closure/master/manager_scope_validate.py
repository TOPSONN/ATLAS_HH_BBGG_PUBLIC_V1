"""Independent original bytes and storage provenance; never calls acquisition."""
import base64,re,stat
from . import manager_scope_contract as c,diagnostic_validate as original
def storage(proof,manifest,scope_sha,approval_sha,manifest_sha):
 c.need(type(proof) is dict and set(proof)=={'scope_store','source_store','inputs','source_files'},'MISSING_STORAGE_PROOF')
 for key in ('scope_store','source_store'):
  row=proof[key];expected=manifest[key]['policy'];c.need(row['filesystem']==expected['filesystem'] and row['filesystem']['classification']=='LINUX_NATIVE_FILESYSTEM_CONFIRMED','STORAGE_FILESYSTEM_PROVENANCE')
  c.need(row['directory_identity']==expected['directory_identity'] and row['mode']==0o700 and row['posix_acl']=='ABSENT_CONFIRMED_BY_FD_XATTR' and row['ancestors_bound']>0 and row['host_admin_excluded'] is False,'PRIVATE_STORAGE_PROVENANCE')
 wanted={'scope.json':scope_sha,'approval.json':approval_sha,'runtime_manifest.json':manifest_sha}
 def rows(values,hashes,mode):
  c.need(len(values)==len(hashes) and {x['name'] for x in values}==set(hashes),'FILE_PROOF_SET')
  for row in values:
   s=row['identity'];c.need(all(type(v) is int and 0<=v<=2**64-1 for v in s.values()),'FILE_STORAGE_NUMERIC_IDENTITY');c.need(row['sha256']==hashes[row['name']] and s['st_uid']==1000 and s['st_nlink']==1 and stat.S_ISREG(s['st_mode']) and stat.S_IMODE(s['st_mode'])==mode and 0<s['st_size']<=c.CAP,'FILE_STORAGE_IDENTITY')
 rows(proof['inputs'],wanted,0o600);rows(proof['source_files'],manifest['source_closure_sha256'],0o400)
def review(receipt_raw,receipt_sha,scope_raw,scope_sha,record_raw,record_sha,manifest_raw,security_raw,security_sha,seen=()):
 try:
  c.need(type(receipt_raw) is bytes and len(receipt_raw)<=c.CAP and type(security_raw) is bytes and len(security_raw)<=c.CAP,'INPUT_BOUND')
  c.need(c.sha(receipt_raw)==receipt_sha and c.sha(security_raw)==security_sha,'RECEIPT_ORIGINAL_BYTES')
  c.need(receipt_sha not in seen and security_sha not in seen,'RECEIPT_REPLAY')
  scope=c.load(scope_raw);record,m=c.approval(scope,scope_raw,scope_sha,record_raw,record_sha,manifest_raw)
  security=c.load(security_raw);c.need(security['schema']=='HH_G2_MANAGER_SECURITY_RECEIPT_V1','SECURITY_RECEIPT_SCHEMA')
  expected={'source_revision':scope['source_revision'],'source_closure_sha256':m['source_closure_sha256'],'scope_raw_sha256':scope_sha,'approval_record_sha256':record_sha,'runtime_manifest_sha256':c.sha(manifest_raw),'original_manager_receipt_sha256':receipt_sha}
  for key,value in expected.items():c.need(security[key]==value,'SECURITY_RECEIPT_BINDING')
  c.need(security['host_attestation'] is False and security['actual_job_enforcement'] is False and security['automatic_retry'] is False,'SECURITY_CLAIM_ESCALATION')
  storage(security['before_launch'],m,scope_sha,record_sha,c.sha(manifest_raw));storage(security['after_capture'],m,scope_sha,record_sha,c.sha(manifest_raw))
  c.need(security['before_launch']==security['after_capture'],'STORAGE_REPLACEMENT_OR_MUTATION')
  c.need(security['dependencies']=={'status':'FIXED_EXTERNAL_ALLOWLIST_MATCHED_WITH_LIMITS','file_count':len(m['dependencies']['files']),'host_attestation':False,'automatic_dependency_discovery':False,'transitive_mapping_attested':False},'DEPENDENCY_PROVENANCE_REQUIRED')
  value=c.load(receipt_raw);base=original.review(receipt_raw,receipt_sha,scope_raw,scope_sha,record_sha)
  # Validate service state independently: an inactive service is not a usable manager/delegation observation.
  queries=value.get('queries',[]);service=None
  if len(queries)>2 and 'skipped' not in queries[2] and queries[2].get('exit_code')==0:
   row=queries[2];props=original.properties(base64.b64decode(row['stdout_b64'],validate=True),original.c.PROPS);service=props
   if 'ActiveState' in props:
    c.need(props['ActiveState'] in ('active','reloading','inactive','failed','activating','deactivating','maintenance'),'INVALID_SERVICE_ACTIVE_STATE')
    c.need('SubState' in props and re.fullmatch('[a-z][a-z0-9-]{0,63}',props['SubState']) is not None,'INVALID_SERVICE_SUBSTATE')
   if props.get('ActiveState') in ('active','reloading'):
    c.need(re.fullmatch('[0-9a-f]{32}',props.get('InvocationID','')) is not None and original.decimal(props.get('MainPID','0'))>0,'ACTIVE_SERVICE_IDENTITY')
  if base['status'] in ('FAIL_SOURCE_OR_RECEIPT_MISMATCH','BLOCKED_TOOL_IDENTITY','BLOCKED_AUTHORIZATION'):
   # Only the known inactive identity representation is a partial observation, never other invalid identity data.
   if not(service and service.get('ActiveState') in ('inactive','failed','activating','deactivating') and base.get('reason') in ('INVOCATION_ID','UNIT_CGROUP')):return dict(base,scope_security='PASS_OBSERVED_STORAGE_WITH_LIMITS',actual_job_enforcement=False)
  absent_user=len(queries)<2 or 'skipped' in queries[1]
  if absent_user or service and service.get('ActiveState') not in ('active','reloading'):status='UNKNOWN_USER_MANAGER'
  elif base.get('all_query_records_complete'):status='PASS_EFFECTIVE_READ_ONLY_OBSERVATION'
  else:status='UNKNOWN_MANAGER_STATE'
  return {'status':status,'scope_security':'PASS_OBSERVED_STORAGE_WITH_LIMITS','original_validator_status':base['status'],'future_delegation':'UNKNOWN_FUTURE_DELEGATION','actual_job_enforcement':False,'host_attestation':False,'manager_state':base.get('system_manager'),'user_manager_state':base.get('user_manager'),'partial_query_indexes':base.get('partial_query_indexes',[])}
 except (ValueError,KeyError,TypeError,UnicodeError,OverflowError) as e:
  reason=str(e)[:120]
  status='BLOCKED_AUTHORIZATION' if any(x in reason for x in ('APPROVAL','AUTHORIZATION')) else 'BLOCKED_DEPENDENCY_CLOSURE' if 'DEPENDENCY' in reason else 'FAIL_SCOPE_SECURITY'
  return {'status':status,'reason':reason,'actual_job_enforcement':False,'host_attestation':False,'future_delegation':'UNKNOWN_FUTURE_DELEGATION'}

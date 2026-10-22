"""Pure versioned binding of user observations, never host attestation/authority."""
import copy,re
from . import diagnostic_contract as c
BASE='a0176ad0c684ea3f8a2d879090a1649485f225a4'
PRIOR_SOURCE='d1a92efdace4c8e0ab480db6c5ab5dd9b7d11121'
TOOLS={'/usr/bin/systemctl':'37ec607113f55f1b385b4fa75588a43402aec0de57927500763b267713f10f63',
 '/usr/bin/python3':'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f',
 '/usr/bin/timeout':'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'}
SOURCES={'diagnostic_capture.py':'2deda99bb913e6a8ee37993778c6db4201d3ff3f1cdd048f290440e26b2f28a4',
 'diagnostic_contract.py':'bdca317b0ef0fecc7c5b141171cd2915e2be46938402ae223fbefa1955b704b5',
 'diagnostic_tools.py':'6ffd7db2f116fb509e44584651feb5bb4595ab33dcc3f034d89c25fe50509582',
 'diagnostic_validate.py':'fcd9e45af9bbadcf5db53bb3f00ca68296aa2c1582c044e300f9de6c8acc8c87'}
OUTPUT='/home/btu/simulations/hh_final_closure/g2_effective_diagnostic_01'
LIMITS={'child_seconds':5,'cleanup_seconds':1,'adapter_soft_seconds':30,'per_child_bytes':8192,'aggregate_bytes':32768,'receipt_bytes':131072,'max_levels':8}
def observation():
 return {'schema':'HH_G2_USER_REPORTED_TOOL_OBSERVATION_V1','status':'HASH_ONLY_OBSERVED_NOT_ATTESTED','provenance':'DIRECT_USER_REPORT_NOT_ORIGINAL_PROBE_BYTES',
  'uid':1000,'gid':1000,'python_version':[3,12,3],'tool_sha256':dict(TOOLS),
  'python_resolved':'/usr/bin/python3.12','targets_root_owned':True,'elf_class':64,'elf_machine':'x86_64','python_symlink_root_owned':True,
  'bus_queries':0,'other_tools_executed':0,'original_probe_raw_sha256':None,'installed_systemd_version':None,
  'tool_identity_attested':False,'execution_authorized':False}
def check_observation(raw,expected_sha):
 c.need(c.sha(raw)==expected_sha,'OBSERVATION_BYTE_BINDING');v=c.load(raw)
 c.need(v==observation() and type(v['uid']) is int and type(v['gid']) is int,'EXACT_USER_REPORTED_OBSERVATION')
 for k in ('targets_root_owned','python_symlink_root_owned'):c.need(v[k] is True,'BOOLEAN_IDENTITY')
 c.need(v['tool_identity_attested'] is False and v['execution_authorized'] is False,'NO_ATTESTATION_OR_AUTHORITY')
 for key in ('bus_queries','other_tools_executed','elf_class'):c.u64(v[key])
 for value in v['python_version']:c.u64(value)
 return v
def pending_scope(revision):
 c.need(type(revision) is str and re.fullmatch('[0-9a-f]{40}',revision) is not None,'SOURCE_REVISION')
 return {'schema':'HH_G2_DIAGNOSTIC_SCOPE_V1','source_revision':revision,'source_sha256':dict(SOURCES),'tool_sha256':dict(TOOLS),
  'uid':1000,'gid':1000,'argvs':c.argvs(1000),'environment':c.environment(1000),'output':OUTPUT,
  'authorization_reference':None,'execution_authorized':False,'limits':dict(LIMITS),
  'systemd_source_family_review':'255_DIRECT_PRIVATE_NO_AUTOSTART_WITH_POISONED_FALLBACK'}
def scope_review(scope):
 c.need(type(scope) is dict,'SCOPE_SCHEMA')
 expected=pending_scope(scope.get('source_revision'))
 c.need(scope==expected,'PENDING_SCOPE_DRIFT')
 for field in ('uid','gid'):c.u64(scope[field])
 for value in scope['limits'].values():c.u64(value)
 c.need(scope['execution_authorized'] is False and scope['authorization_reference'] is None,'CANNOT_CREATE_HUMAN_AUTHORIZATION')
 try:c.checked_scope(scope)
 except ValueError as e:c.need(str(e)=='BLOCKED_AUTHORIZATION','ORIGINAL_CONTRACT_MISMATCH')
 else:raise ValueError('PENDING_SCOPE_MUST_NOT_EXECUTE')
 return {'status':'PASS_PENDING_SCOPE_SOURCE_BINDING','tool_values_bound':True,'original_fixed_argv_preserved':True,
  'execution_authorized':False,'authorization_reference':None,'full_diagnostic_ready':False,
  'remaining_blockers':['USER_REPORTED_NOT_INDEPENDENTLY_REHASHED','INSTALLED_SYSTEMD_VERSION_UNKNOWN','DEPENDENCY_CLOSURE_UNKNOWN','EXISTING_BUS_SOCKET_CONDITIONS_UNKNOWN','PRIVATE_PARENT_UNKNOWN','SEPARATE_HUMAN_APPROVAL_REQUIRED']}
def binding_report(raw,expected_sha,revision,seen=()):
 check_observation(raw,expected_sha);c.need(expected_sha not in seen,'OBSERVATION_REPLAY_NEW_RUN_REQUIRED')
 return {'schema':'HH_G2_ACTUAL_TOOL_BINDING_REVIEW_V1','source_revision':revision,'prior_source_revision':PRIOR_SOURCE,
  'observation_sha256':expected_sha,'observation_origin':'USER_REPORTED_NORMALIZED_STATEMENT_NOT_RAW_CAPTURE','tool_sha256':dict(TOOLS),'source_sha256':dict(SOURCES),
  'uid':1000,'gid':1000,'python_version':[3,12,3],'python_resolved':'/usr/bin/python3.12',
  'TOOL_IDENTITY_OBSERVED':True,'TOOL_IDENTITY_VERIFIED':False,'INSTALLED_SYSTEMD_VERSION_VERIFIED':False,
  'independent_binary_read_performed':False,'runtime_rehash_required':True,'dependency_closure':'UNKNOWN','execution_authorized':False}
def version_result(row):
 c.need(row['argv']==['/usr/bin/systemctl','--version'],'FIXED_VERSION_ARGV')
 c.need(row['environment_sha256']==c.sha(c.canonical(c.environment(1000))),'VERSION_ENVIRONMENT')
 import base64
 out=base64.b64decode(row['stdout_b64'],validate=True);err=base64.b64decode(row['stderr_b64'],validate=True)
 c.need(type(row['stdout_bytes']) is int and type(row['stderr_bytes']) is int and row['stdout_bytes']==len(out) and row['stderr_bytes']==len(err) and len(out)+len(err)<=8192,'VERSION_OUTPUT_BOUND')
 for k in ('start_ns','end_ns','pid','start_ticks'):c.u64(row[k])
 c.need(row['start_ns']<=row['end_ns'],'VERSION_CLOCK')
 c.need(row['pid']>0 and row['start_ticks']>0 and row['cleanup'] in ('VERIFIED_GROUP_ABSENT','UNKNOWN'),'VERSION_CHILD_IDENTITY')
 if row['exit_code'] is not None:c.u64(row['exit_code'])
 if row['exit_signal'] is not None:c.u64(row['exit_signal'])
 c.need(not(row['exit_code'] is not None and row['exit_signal'] is not None),'VERSION_EXIT_CONTRADICTION')
 if row['cleanup']!='VERIFIED_GROUP_ABSENT' or row['stop_reason'] is not None or row['exit_code']!=0 or row['exit_signal'] is not None or err or row['end_ns']-row['start_ns']>6_000_000_000:
  return {'status':'UNKNOWN_INSTALLED_VERSION','verified':False,'family':None}
 first=out.decode('ascii').splitlines()[0] if out else ''
 match=re.fullmatch(r'systemd ([1-9][0-9]{1,3})(?: \([ -~]{1,256}\))?',first)
 c.need(match is not None,'VERSION_SYNTAX')
 family=int(match[1]);return {'status':'OBSERVED_CLIENT_V255_NOT_MANAGER_ATTESTATION' if family==255 else 'BLOCKED_VERSION_FAMILY_MISMATCH','verified':family==255,'family':family,'manager_version_verified':False,'dependency_closure_verified':False}
def review_version_receipt(raw,expected_sha,scope_raw,expected_scope_sha,authorization_reference,seen=()):
 """Independent original-byte binding; no producer import until pure scope check."""
 c.need(type(raw) is bytes and type(scope_raw) is bytes and len(raw)<=131072 and len(scope_raw)<=131072,'VERSION_RECEIPT_BOUND')
 c.need(c.sha(raw)==expected_sha and c.sha(scope_raw)==expected_scope_sha,'VERSION_ORIGINAL_BYTES')
 c.need(expected_sha not in seen,'VERSION_RECEIPT_REPLAY')
 scope=c.load(scope_raw);value=c.load(raw);c.need(type(scope) is dict and type(value) is dict,'VERSION_RECEIPT_SCHEMA')
 from .tool_binding_version_probe import check
 check(scope)
 c.need(value['schema']=='HH_G2_VERSION_ONLY_RECEIPT_V1' and value['scope_sha256']==c.sha(c.canonical(scope)),'VERSION_SCOPE_BINDING')
 c.need(value['source_revision']==scope['source_revision'] and value['source_sha256']==scope['source_sha256'] and value['tool_sha256']==TOOLS,'VERSION_SOURCE_TOOL_BINDING')
 c.need(value['authorization_reference']==scope['authorization_reference']==authorization_reference,'EXTERNAL_AUTHORIZATION_BINDING')
 c.need(type(value['uid']) is int and type(value['gid']) is int and value['uid']==value['gid']==1000 and value['python_version']==[3,12,3],'VERSION_RUNTIME_IDENTITY')
 c.need(type(value['bus_queries']) is int and value['bus_queries']==0 and value['complete_diagnostic_executed'] is False and value['dependency_closure_verified'] is False,'VERSION_SCOPE_ESCALATION')
 for key in ('start_ns','end_ns'):c.u64(value[key])
 row=value['query'];c.need(value['start_ns']<=row['start_ns']<=row['end_ns']<=value['end_ns'],'VERSION_OBSERVATION_ORDER')
 result=version_result(row)
 if value['end_ns']-value['start_ns']>30_000_000_000:result={'status':'UNKNOWN_INSTALLED_VERSION','verified':False,'family':None}
 return dict(result,original_bytes_bound=True,TOOL_IDENTITY_VERIFIED=False,host_attestation=False,G2_MANAGER_STATE_VERIFIED=False,G2_CGROUP_DELEGATION_VERIFIED=False)

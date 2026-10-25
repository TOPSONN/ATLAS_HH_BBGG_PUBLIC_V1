"""Independent structural/identity validation. Never collects or imports a target."""
import stat
from . import manager_dependency_contract as c,manager_elf as elf,manager_dependency_provider as provider
def identity(s,owner=0,regular=True):
 required={'st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'};c.need(required<=set(s),'MISSING_FILE_IDENTITY')
 for v in s.values():c.u64(v)
 c.need(s['st_uid']==owner and not s['st_mode']&0o6022,'UNSAFE_FILE_OWNER_OR_MODE')
 if regular:c.need(stat.S_ISREG(s['st_mode']) and s['st_nlink']==1 and 0<s['st_size']<=c.FILE_CAP,'REGULAR_SINGLE_LINK_FILE')
def file_proof(row,allow):
 c.need(row['requested']==allow['path'],'FILE_ALLOWLIST_BINDING');c.path(row['physical']);c.digest(row['sha256']);identity(row['identity']);c.need(row['acl']=='ABSENT_BY_SAME_FD' and row['bytes_equality_rechecked'] is True,'FILE_FD_ACCESS_PROOF')
 if allow['sha256'] is not None:c.need(row['sha256']==allow['sha256'],'EXPECTED_TOOL_HASH')
 current=row['requested'];seen=set()
 for hop in row['aliases']:
  p=hop['path'];c.need(p not in seen and allow['aliases'].get(p)==hop['target'],'ALIAS_CHAIN_DRIFT');seen.add(p);s=hop['identity'];c.need(stat.S_ISLNK(s['st_mode']) and s['st_uid']==0,'ALIAS_OWNER_TYPE')
  c.need(current==p or current.startswith(p+'/'),'ALIAS_PATH_TRANSITION');current=c.alias_target(p,hop['target'])+current[len(p):]
 c.need(current==row['physical'] and len(seen)<=c.MAX_ALIASES,'ALIAS_FINAL_PHYSICAL_PATH')
 for node in row['ancestor_instances']:
  s=node['identity'];c.need(s['st_uid']==0,'ANCESTOR_ROOT_OWNER')
  if node['type']!='SYMLINK':c.need(not s['st_mode']&0o6022,'ANCESTOR_WRITABLE_OR_SPECIAL')
 c.need(row['ancestor_instances'] and row['mount_namespace_inode']>0,'FILE_PROVENANCE_REQUIRED')
def review(raw,expected_sha,scope_raw,scope_sha,record_raw,record_sha,source_hashes,seen=(),allow_fixture=False,now=None):
 try:
  from . import manager_native_contract as nc
  scope,record=nc.approval(scope_raw,record_raw,scope_sha,record_sha,allow_fixture=allow_fixture,now=now)
  c.digest(expected_sha);c.need(c.sha(raw)==expected_sha and expected_sha not in seen,'EVIDENCE_HASH_OR_REPLAY');v=c.load(raw)
  c.need(v['schema']==c.SCHEMA and v['scope_sha256']==scope_sha and v['source_revision']==scope['source_revision'] and v['source_closure_sha256']==source_hashes,'EVIDENCE_SCOPE_SOURCE_CHAIN')
  fixture=v['evidence_origin']=='SYNTHETIC_TEST_FIXTURE';c.need(v['evidence_origin']=='LOCAL_APPROVED_FILE_INSPECTION_UNATTESTED' or allow_fixture and fixture,'EVIDENCE_PROVENANCE');c.need(v['approval_record_sha256']==record_sha and scope['source_closure_sha256']==source_hashes,'APPROVAL_SOURCE_BINDING')
  c.need(v['uid']==v['gid']==1000 and type(v['uid']) is int and type(v['gid']) is int,'EVIDENCE_UID_GID');c.need(v['automatic_retry'] is False and v['manager_queries']==v['other_children']==0 and v['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED'] is False,'EVIDENCE_CLAIM_ESCALATION')
  c.need(type(v['started_monotonic_ns']) is int and type(v['finished_monotonic_ns']) is int and 0<=v['started_monotonic_ns']<=v['finished_monotonic_ns'] and v['finished_monotonic_ns']-v['started_monotonic_ns']<=scope['limits']['soft_seconds']*10**9,'EVIDENCE_SOFT_TIME_WINDOW')
  allowed={x['path']:x for x in scope['files']};rows=v['files'];c.need(len(rows)<=c.MAX_FILES and len(rows)==len({r['requested'] for r in rows}),'DUPLICATE_FILE_EVIDENCE')
  ancestors=v['ancestor_table'];c.need(type(ancestors) is dict and len(ancestors)<=256,'ANCESTOR_TABLE_BOUND')
  for key,node in ancestors.items():c.need(c.sha(c.canonical(node))==key,'ANCESTOR_TABLE_HASH')
  for row in rows:
   c.need(row['requested'] in allowed,'UNAPPROVED_FILE');refs=row['ancestor_instance_refs'];c.need(0<len(refs)<=64 and all(key in ancestors for key in refs),'ANCESTOR_REFERENCE_SET');file_proof(dict(row,ancestor_instances=[ancestors[k] for k in refs]),allowed[row['requested']])
  reported={r['requested'] for r in rows};missing={r['path'] for r in v['unavailable_files']};c.need(len(missing)==len(v['unavailable_files']) and not reported&missing and reported|missing==set(allowed),'INCOMPLETE_FILE_COVERAGE')
  c.need(all(row['reason'] in ('MISSING','UNREVIEWED_ALIAS','SECURITY_REJECTED') for row in v['unavailable_files']),'UNKNOWN_FILE_FAILURE_REASON')
  c.need(v['native_parent']['host_attestation'] is False and v['native_parent']['actual_private_source_staged'] is False and v['native_parent']['actual_private_scope_staged'] is False,'OBSERVATION_NOT_DEPLOYMENT')
  for proof in (v['native_parent']['proof'],v['output_store']):
   fs=proof['filesystem'];c.need(fs['classification']=='LINUX_NATIVE_FILESYSTEM_CONFIRMED' and fs['fs_type']=='ext4' and fs['fs_magic']==0xef53 and proof['posix_acl']=='ABSENT_CONFIRMED_BY_FD_XATTR' and proof['host_admin_excluded'] is False,'NATIVE_STORAGE_PROOF')
   for key in ('mount_id','device','mount_namespace_inode'):c.need(type(fs[key]) is int and fs[key]>0,'NATIVE_FILESYSTEM_IDENTITY')
  c.need(v['output_store']['mode']==0o700 and v['output_store']['directory_identity']['st_uid']==1000,'PRIVATE_RECEIPT_STORE')
  # Reparse recorded raw bounded ELF bytes independently when separately provided.
  graph=v['static_graph'];c.need(graph['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED'] is False and graph['status']=='OBSERVED_BOUNDED_ELF_NODES_NOT_LOADER_RESOLUTION' and graph['edges_reviewed'] is False,'STATIC_NOT_RUNTIME')
  bypath={r['physical']:r for r in rows}
  for p,node in graph['parsed_nodes'].items():c.need(p in bypath and node['sha256']==bypath[p]['sha256'] and node['bytes']==bypath[p]['identity']['st_size'] and node['format']=='ELF64_LE_X86_64' and len(node['needed'])<=128,'ELF_NODE_ORIGINAL_FILE_BINDING')
  python=v['python'];c.need(python['schema']=='PYTHON_RUNTIME_IMPORT_EVIDENCE_V1' and python['version']==[3,12,3] and python['isolated'] is True and python['no_site'] is True and python['no_bytecode_write'] is True,'PYTHON_OBSERVATION_VERSION')
  modules=python['modules'];c.need(len(modules)<=c.MAX_MODULES and len(modules)==len({r['name'] for r in modules}) and python['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED'] is False,'PYTHON_MODULE_EVIDENCE')
  for row in modules:
   if row['sha256'] is not None:c.need(row['origin'] in bypath and row['sha256']==bypath[row['origin']]['sha256'] and row['file_identity']==bypath[row['origin']]['identity'],'PYTHON_MODULE_FILE_BINDING')
  c.need(all(type(p) is str and p.startswith('/usr/') for p in python['sys_path']),'UNEXPECTED_PYTHON_SEARCH_PATH')
  c.need(v['session']['created_session'] is False and v['session']['mount_namespace_inode']==v['output_store']['filesystem']['mount_namespace_inode'],'SESSION_NAMESPACE_BINDING')
  c.need(len(v['bus_metadata'])==2 and {r['path'] for r in v['bus_metadata']}==set(scope['socket_metadata_only']) and all(r['connected'] is False for r in v['bus_metadata']),'BUS_METADATA_ONLY')
  for row in v['bus_metadata']:
   c.need(row['status'] in ('OBSERVED_METADATA_ONLY','UNKNOWN_MISSING_SOCKET','UNKNOWN_SOCKET_SECURITY'),'BUS_OBSERVATION_STATUS')
   if row['status']=='OBSERVED_METADATA_ONLY':c.need(stat.S_ISSOCK(row['identity']['st_mode']) and row['identity']['st_uid']==(1000 if '/user/' in row['path'] else 0),'SOCKET_OBSERVED_OWNER_TYPE')
  c.need(v['mapping']['lifetime_coverage'] is False and v['mapping']['future_child_identity_bound'] is False,'SNAPSHOT_NOT_LIFETIME')
  return {'status':'PASS_TEST_FIXTURE_ONLY' if fixture else 'PASS_READ_ONLY_OBSERVED_WITH_LIMITS','file_count':len(rows),'unavailable_count':len(missing),'static_graph_status':v['static_graph']['status'],'runtime_mapping_status':v['mapping']['status'],'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False,'MANAGER_DIAGNOSTIC_EXECUTED':False,'host_attestation':False}
 except (ValueError,KeyError,TypeError,UnicodeError,OverflowError):return {'status':'FAIL_NATIVE_EVIDENCE_BINDING','COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False,'MANAGER_DIAGNOSTIC_EXECUTED':False}
def static_recompute(blobs,expected,roots,resolutions,aliases):
 actual=provider.graph(blobs,roots,resolutions,aliases);c.need(actual==expected,'STATIC_GRAPH_RECOMPUTATION_MISMATCH');return actual
def stage_review(raw,expected_sha,scope_raw,scope_sha,record_raw,record_sha,allow_fixture=False,now=None):
 from . import manager_native_contract as nc
 scope,record=nc.approval(scope_raw,record_raw,scope_sha,record_sha,allow_fixture=allow_fixture,now=now);c.need(scope['operation']=='NATIVE_STAGE_ONCE','SEPARATE_STAGE_APPROVAL');c.need(c.sha(raw)==expected_sha,'STAGE_ORIGINAL_RECEIPT_BYTES');v=c.load(raw)
 c.need(v['schema']=='HH_G2_NATIVE_FINITE_STAGE_RECEIPT_V1' and v['source_revision']==scope['source_revision'] and v['source_closure_sha256']==scope['source_closure_sha256'] and v['scope_sha256']==scope_sha and v['approval_record_sha256']==record_sha,'STAGE_IDENTITY_CHAIN')
 fixture=v['evidence_origin']=='SYNTHETIC_TEST_FIXTURE';c.need(v['evidence_origin']=='LOCAL_APPROVED_FILE_CREATION_UNATTESTED' or allow_fixture and fixture,'STAGE_EVIDENCE_ORIGIN')
 c.need(v['source_files']==len(c.CLOSURE) and v['source_mode']==0o400 and v['scope_mode']==0o600 and v['manager_queries']==0 and v['automatic_retry'] is False and v['host_attestation'] is False,'STAGE_OPERATION_LIMITS')
 c.need(v['store']['filesystem']['classification']=='LINUX_NATIVE_FILESYSTEM_CONFIRMED' and v['store']['mode']==0o700 and v['store']['posix_acl']=='ABSENT_CONFIRMED_BY_FD_XATTR' and v['store']['directory_identity']['st_uid']==1000,'STAGE_NATIVE_PRIVATE_STORE')
 rows=v['source_instances'];c.need(len(rows)==len(c.CLOSURE) and {r['name'] for r in rows}==c.CLOSURE,'STAGE_SOURCE_INSTANCE_SET')
 total=0
 for row in rows:
  identity(row['identity'],owner=1000);c.need(stat.S_IMODE(row['identity']['st_mode'])==0o400 and row['sha256']==scope['source_closure_sha256'][row['name']],'STAGED_SOURCE_HASH_MODE');total+=row['identity']['st_size']
 c.need(total==v['source_bytes'] and total<=1048576 and v['pending_scope_A_sha256']==c.sha(c.canonical(nc.pending(scope['source_revision'],scope['source_closure_sha256'],'NATIVE_READ_ONLY_ONCE'))),'STAGE_AGGREGATE_AND_PENDING_SCOPE')
 return {'status':'PASS_TEST_FIXTURE_ONLY' if fixture else 'PASS_ACTUAL_PRIVATE_SOURCE_AND_PENDING_SCOPE_STAGED_WITH_LIMITS','host_attestation':False,'manager_authorized':False}

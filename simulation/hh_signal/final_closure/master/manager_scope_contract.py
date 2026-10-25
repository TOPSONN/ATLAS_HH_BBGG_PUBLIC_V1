"""New manager approval, not the consumed version authorization. Pure validation."""
import hashlib,json,re
BASE='0edd24ed6cfba314e8f3632a0e61bd6265b7dbfa'
PREVIOUS='55777dd8a21964dd87c7294550bd51cef73e5fa8'
CONSUMED={'0e76645d07be2eb646f2cc44163b8a34db3f3ad38cfe07c42105845df37e2e02','09c7e3b9b4380d0dd40fdea6a618f997180925ae0b1ab7b3f0d7b0cc0902ca62'}
CAP=131072;PROFILE='HH_G2_MANAGER_NATIVE_SECURITY_V1'
ORIGINAL=('diagnostic_capture.py','diagnostic_contract.py','diagnostic_tools.py','diagnostic_validate.py')
ADDED=('manager_scope_fs.py','manager_scope_contract.py','manager_scope_loader.py','manager_scope_capture.py','manager_scope_validate.py','manager_scope_bootstrap.py')
CLOSURE=set(ORIGINAL+ADDED)
ORIGINAL_SHA={'diagnostic_capture.py':'2deda99bb913e6a8ee37993778c6db4201d3ff3f1cdd048f290440e26b2f28a4','diagnostic_contract.py':'bdca317b0ef0fecc7c5b141171cd2915e2be46938402ae223fbefa1955b704b5','diagnostic_tools.py':'6ffd7db2f116fb509e44584651feb5bb4595ab33dcc3f034d89c25fe50509582','diagnostic_validate.py':'fcd9e45af9bbadcf5db53bb3f00ca68296aa2c1582c044e300f9de6c8acc8c87'}
TOOLS={'/usr/bin/systemctl':'37ec607113f55f1b385b4fa75588a43402aec0de57927500763b267713f10f63','/usr/bin/python3':'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f','/usr/bin/timeout':'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'}
LIMITS={'child_seconds':5,'cleanup_seconds':1,'adapter_soft_seconds':30,'per_child_bytes':8192,'aggregate_bytes':32768,'receipt_bytes':131072,'max_levels':8}
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def load(raw):
 need(type(raw) is bytes and len(raw)<=CAP,'INPUT_BOUND')
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
  return out
 def bad(_):raise ValueError('NONCANONICAL_NUMBER')
 def integer(s):
  need(re.fullmatch('0|[1-9][0-9]*',s) is not None and int(s)<=2**64-1,'CANONICAL_U64');return int(s)
 return json.loads(raw,object_pairs_hook=pairs,parse_int=integer,parse_float=bad,parse_constant=bad)
def digest(value):need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'SHA256_REQUIRED')
def fixed_argvs():
 common=['/usr/bin/systemctl','--no-pager','--no-ask-password'];manager=['show','--property=Version','--property=SystemState']
 props=('ControlGroup','Delegate','CPUAccounting','MemoryAccounting','MemoryMax','MemorySwapMax','CPUQuotaPerSecUSec','TasksMax','ActiveState','SubState','InvocationID','MainPID','User')
 return [common+['--system']+manager,common+['--user']+manager,common+['--system','show','user@1000.service']+['--property='+p for p in props]]
def fixed_env():return {'PATH':'/usr/bin','LANG':'C','LC_ALL':'C','SYSTEMD_COLORS':'0','SYSTEMD_PAGER':'','XDG_RUNTIME_DIR':'/run/user/1000','DBUS_SYSTEM_BUS_ADDRESS':'unix:path=/run/dbus/system_bus_socket','DBUS_SESSION_BUS_ADDRESS':'unix:path=/proc/self/fd/-1'}
def pending(original_scope,closure,manifest_sha256):
 need(set(closure)==CLOSURE,'MINIMUM_SOURCE_CLOSURE');digest(manifest_sha256)
 for value in closure.values():digest(value)
 s=json.loads(canonical(original_scope));need(s['authorization_reference'] is None and s['execution_authorized'] is False,'PENDING_ONLY')
 s['security']={'profile':PROFILE,'runtime_manifest_sha256':manifest_sha256,'source_closure_sha256':closure,'storage_required':'LINUX_NATIVE_FILESYSTEM_CONFIRMED','dependency_closure_required':True}
 return s
def check_manifest(m,scope):
 need(m['schema']=='HH_G2_NATIVE_RUNTIME_MANIFEST_V1' and m['uid']==m['gid']==1000 and type(m['uid']) is int and type(m['gid']) is int,'RUNTIME_MANIFEST_IDENTITY')
 need(m['python_version']==[3,12,3] and m['source_revision']==scope['source_revision'],'INTERPRETER_SOURCE_BINDING')
 need(m['source_closure_sha256']==scope['security']['source_closure_sha256'] and set(m['source_closure_sha256'])==CLOSURE,'SOURCE_CLOSURE_BINDING')
 for value in m['source_closure_sha256'].values():digest(value)
 for key in ('scope_store','source_store','output_parent_store'):
  store=m[key];need(store['policy']['uid']==1000 and store['policy']['filesystem']['classification']=='LINUX_NATIVE_FILESYSTEM_CONFIRMED','UNKNOWN_APPROVED_NATIVE_STORE')
  need(type(store['path']) is str and (store['path']=='/home/btu/simulations/hh_final_closure' if key=='output_parent_store' else store['path'].startswith('/home/btu/simulations/hh_final_closure/')),'STORE_LOCATION')
  need(type(store['policy']['directory_identity']) is dict and set(store['policy']['directory_identity'])=={'st_dev','st_ino','st_uid'},'DIRECTORY_IDENTITY_REQUIRED')
 need(m['output_parent_store']['path']=='/home/btu/simulations/hh_final_closure','FIXED_OUTPUT_PARENT')
 deps=m['dependencies'];need(deps['status']=='EXTERNALLY_REVIEWED_FIXED_CLOSURE' and 0<len(deps['files'])<=128,'BLOCKED_DEPENDENCY_CLOSURE')
 need(deps['filesystem_scan'] is False and deps['host_attestation'] is False,'DEPENDENCY_SCOPE')
 names=[]
 for row in deps['files']:
  need(set(row)=={'path','sha256','kind'} and row['kind'] in ('ELF','PYTHON_SOURCE','PYTHON_EXTENSION'),'DEPENDENCY_ENTRY')
  need(type(row['path']) is str and row['path'].startswith(('/usr/','/lib/','/lib64/')) and '..' not in row['path'].split('/'),'DEPENDENCY_PATH');digest(row['sha256']);names.append(row['path'])
 need(len(set(names))==len(names),'DUPLICATE_DEPENDENCY')
 need(type(deps['required_import_origins']) is dict and deps['required_import_origins'],'IMPORT_ORIGINS_REQUIRED')
 need(m['no_wsl_startup'] is True and m['no_root_fallback'] is True,'NO_PRIVILEGE_FALLBACK')
def approval(scope,scope_raw,scope_sha,record_raw,record_sha,manifest_raw,seen=()):
 digest(scope_sha);digest(record_sha);need(record_sha not in CONSUMED and record_sha not in seen,'CONSUMED_OR_REPLAYED_APPROVAL')
 need(sha(scope_raw)==scope_sha and sha(record_raw)==record_sha,'ORIGINAL_BYTES_BINDING')
 need(scope==load(scope_raw) and scope['authorization_reference']==record_sha and scope['execution_authorized'] is False,'EXTERNAL_AUTHORIZATION_REFERENCE')
 need(scope['schema']=='HH_G2_DIAGNOSTIC_SCOPE_V1','ORIGINAL_MANAGER_SCOPE_SCHEMA')
 need(scope['source_revision']!=PREVIOUS and re.fullmatch('[0-9a-f]{40}',scope['source_revision']) is not None,'NEW_EXACT_SOURCE_REQUIRED')
 need(scope['security']['profile']==PROFILE and scope['security']['dependency_closure_required'] is True and scope['security']['storage_required']=='LINUX_NATIVE_FILESYSTEM_CONFIRMED','SECURITY_PROFILE')
 need(scope['tool_sha256']==TOOLS and scope['uid']==scope['gid']==1000 and type(scope['uid']) is int and type(scope['gid']) is int and scope['limits']==LIMITS,'ORIGINAL_TOOLS_UID_LIMITS')
 need(scope['argvs']==fixed_argvs() and scope['environment']==fixed_env() and scope['output']=='/home/btu/simulations/hh_final_closure/g2_effective_diagnostic_01','FIXED_MANAGER_COMMAND_ENV_OUTPUT')
 need(scope['source_sha256']==ORIGINAL_SHA and all(scope['security']['source_closure_sha256'].get(n)==h for n,h in ORIGINAL_SHA.items()),'ORIGINAL_FOUR_SOURCE_IDENTITY')
 for x in scope['limits'].values():need(type(x) is int,'LIMIT_INTEGER')
 record=load(record_raw);need(record['provenance']=='USER_PROVIDED_VERBATIM_APPROVAL_REPORTED' and record['identity_attestation'] is False,'APPROVAL_PROVENANCE')
 need(record['operation']=='G2_MANAGER_DIAGNOSTIC_ONCE' and record['maximum_attempts']==1 and type(record['maximum_attempts']) is int,'MANAGER_ONLY_APPROVAL')
 need(type(record['approval_text']) is str and 0<len(record['approval_text'].encode())<=16384,'APPROVAL_TEXT_REQUIRED')
 need(sha((record['approval_text'].rstrip()+'\n').encode()) not in CONSUMED,'CONSUMED_VERSION_TEXT_REUSE')
 empty=json.loads(canonical(scope));empty['authorization_reference']=None
 need(record['pending_scope_canonical_sha256']==sha(canonical(empty)) and record['runtime_manifest_sha256']==sha(manifest_raw),'APPROVAL_SCOPE_MANIFEST_CHAIN')
 need(record['source_revision']==scope['source_revision'] and record['excluded_architecture_acceptance'] is True,'SCOPE_NOT_ARCHITECTURE_ACCEPTANCE')
 need(sha(manifest_raw)==scope['security']['runtime_manifest_sha256'],'RUNTIME_MANIFEST_BYTES')
 manifest=load(manifest_raw);check_manifest(manifest,scope);return record,manifest

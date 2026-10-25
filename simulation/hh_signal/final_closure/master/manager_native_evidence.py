"""Future approved collector/stager. No child, network, service or target ELF call."""
import base64,os,signal,stat,sys,time
from . import manager_dependency_contract as c,manager_native_contract as nc,manager_scope_fs as fs,manager_dependency_io as dio,manager_elf as elf,manager_dependency_provider as provider
def observed_store(path,private):
 c.path(path);fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:s=os.fstat(fd);identity=fs.fs_identity(fd)
 finally:os.close(fd)
 policy={'uid':1000,'filesystem':identity,'directory_identity':{k:getattr(s,k) for k in ('st_dev','st_ino','st_uid')}}
 return fs.Store(path,policy,private=private)
def interpreter():
 c.need(sys.platform=='linux' and os.getuid()==os.geteuid()==os.getgid()==os.getegid()==1000,'REQUIRED_EXISTING_NONROOT_UBUNTU_SESSION');c.need(tuple(sys.version_info[:3])==(3,12,3) and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'REVIEWED_PYTHON3123_ISOLATED')
 with_file=dio.AliasPin('/usr/bin/python3.12',{},nc.PYTHON)
 try:
  a=os.stat('/proc/self/exe');b=os.fstat(with_file.fd);c.need((a.st_dev,a.st_ino)==(b.st_dev,b.st_ino),'ACTUAL_PYTHON_EXECUTABLE_INSTANCE')
 finally:with_file.close()
def import_observation(files):
 rows=[];unknown=[];modules=list(sys.modules.items());c.need(len(modules)<=c.MAX_MODULES+len(c.CLOSURE)+1,'MODULE_SNAPSHOT_BOUND')
 for name,module in sorted(modules):
  if name=='_hh_g2_native_v2' or name.startswith('_hh_g2_native_v2.'):continue
  spec=getattr(module,'__spec__',None);origin=getattr(spec,'origin',None);kind='BUILTIN' if origin=='built-in' else 'FROZEN' if origin=='frozen' else 'BYTECODE' if isinstance(origin,str) and origin.endswith('.pyc') else 'EXTENSION' if isinstance(origin,str) and origin.endswith('.so') else 'SOURCE' if isinstance(origin,str) and origin.endswith('.py') else 'UNKNOWN'
  file=files.get(origin);rows.append({'name':name,'origin_class':kind,'origin':origin,'sha256':None if file is None else file['sha256'],'file_identity':None if file is None else file['identity'],'cached_path':getattr(module,'__cached__',None),'execution_bytes_attested':False})
  if kind=='UNKNOWN' or kind in ('SOURCE','BYTECODE','EXTENSION') and file is None:unknown.append(name)
 c.need(len(rows)<=c.MAX_MODULES,'MODULE_EVIDENCE_BOUND')
 return {'schema':'PYTHON_RUNTIME_IMPORT_EVIDENCE_V1','version':list(sys.version_info[:3]),'actual_executable':'/usr/bin/python3.12','isolated':bool(sys.flags.isolated),'no_site':bool(sys.flags.no_site),'no_bytecode_write':sys.dont_write_bytecode,'sys_path':list(sys.path),'meta_path':[getattr(x,'__module__',type(x).__module__)+'.'+getattr(x,'__qualname__',type(x).__qualname__) for x in sys.meta_path],'modules':rows,'unbound_modules':unknown,'mapped_extensions':[],'extension_mapping_status':'UNKNOWN_UNTIL_VALIDATED_MAPPING_SNAPSHOT','COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
def socket_metadata(path):
 c.path(path);parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds=[parent]
 try:
  root=os.fstat(parent);c.need(root.st_uid==0 and not root.st_mode&0o022,'SOCKET_ROOT_ANCESTOR');fs.no_acl(parent,True)
  for part in path.split('/')[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);fds.append(fd);s=os.fstat(fd);c.need(s.st_uid in (0,1000) and not s.st_mode&0o022,'SOCKET_ANCESTOR');fs.no_acl(fd,True);parent=fd
  s=os.stat(path.split('/')[-1],dir_fd=parent,follow_symlinks=False);c.need(stat.S_ISSOCK(s.st_mode) and s.st_uid==(1000 if '/user/' in path else 0),'SOCKET_TYPE_OWNER');return {'path':path,'status':'OBSERVED_METADATA_ONLY','identity':fs.ident(s),'connected':False,'manager_or_bus_semantics':'UNKNOWN'}
 except FileNotFoundError:return {'path':path,'status':'UNKNOWN_MISSING_SOCKET','connected':False}
 except (ValueError,PermissionError):return {'path':path,'status':'UNKNOWN_SOCKET_SECURITY','connected':False}
 finally:
  for fd in reversed(fds):os.close(fd)
def static_observation(blobs):
 parsed={};unknown=[]
 for path,raw in blobs.items():
  try:parsed[path]=elf.parse(raw)
  except (ValueError,UnicodeError):unknown.append(path)
 return {'status':'OBSERVED_BOUNDED_ELF_NODES_NOT_LOADER_RESOLUTION','parsed_nodes':parsed,'unsupported_nodes':unknown,'edges_reviewed':False,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
def collect(scope_raw,record_raw,scope_sha,record_sha,source_raws):
 # Approval is validated before any actual guest/runtime metadata read.
 scope,record=nc.approval(scope_raw,record_raw,scope_sha,record_sha);c.need(scope['operation']=='NATIVE_READ_ONLY_ONCE','OBSERVATION_SCOPE_A_REQUIRED');interpreter();started=time.monotonic_ns();pins=[];total=0
 def deadline():c.need(time.monotonic_ns()-started<scope['limits']['soft_seconds']*10**9,'COLLECTOR_SOFT_DEADLINE')
 store=observed_store(nc.DEST,True);attempt_created=False
 try:
  c.need(set(source_raws)==c.CLOSURE,'EXACT_COLLECTOR_SOURCE_CLOSURE')
  for name,raw in source_raws.items():c.need(c.sha(raw)==scope['source_closure_sha256'][name],'CAPSULE_SOURCE_DRIFT')
  attempt=store.write_new('observe_attempt.json',c.canonical({'scope_sha256':scope_sha,'approval_record_sha256':record_sha,'consumed':True}));attempt.close();attempt_created=True
  files=[];unavailable=[];blobs={};ancestor_table={}
  for row in scope['files']:
   deadline()
   try:pin=dio.AliasPin(row['path'],row['aliases'],row['sha256'])
   except TimeoutError:raise
   except FileNotFoundError:unavailable.append({'path':row['path'],'reason':'MISSING'});continue
   except ValueError as exc:
    item={'path':row['path'],'reason':'UNREVIEWED_ALIAS' if str(exc)=='UNREVIEWED_SYMLINK' else 'SECURITY_REJECTED'}
    if item['reason']=='UNREVIEWED_ALIAS':
     try:item['alias_metadata']=dio.alias_observation(row['path'])
     except TimeoutError:raise
     except (OSError,ValueError):pass
    unavailable.append(item);continue
   except (PermissionError,OSError):unavailable.append({'path':row['path'],'reason':'SECURITY_REJECTED'});continue
   pins.append(pin);total+=len(pin.raw);c.need(total<=c.TOTAL_FILE_CAP,'AGGREGATE_BINARY_READ_BOUND');proof=pin.proof();refs=[]
   for node in proof.pop('ancestor_instances')[:-1]:
    key=c.sha(c.canonical(node));ancestor_table[key]=node;refs.append(key)
   proof['ancestor_instance_refs']=refs;files.append(proof)
   if row['kind'] in ('ELF','PYTHON_EXTENSION'):blobs[pin.physical]=pin.raw
  aliases=[]
  for path in scope['alias_metadata_only']:
   deadline()
   try:aliases.append(dio.alias_observation(path))
   except TimeoutError:raise
   except (ValueError,OSError):aliases.append({'path':path,'status':'UNKNOWN_ALIAS_METADATA','target_followed':False})
  bypath={r['physical']:r for r in files};python=import_observation(bypath);maps=fs.read_proc('/proc/self/maps',65536)
  try:mapping=provider.mapping(maps,bypath)
  except ValueError:mapping={'status':'UNKNOWN_UNLISTED_OR_UNBOUND_CURRENT_MAPPING','lifetime_coverage':False,'future_child_identity_bound':False,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
  mapping['original_snapshot_sha256']=c.sha(maps)
  if mapping['status']=='PASS_ACTUAL_RUNTIME_MAPPING_EVIDENCE_WITH_LIMITS':python['mapped_extensions']=[p for p in mapping['mapped_paths'] if p.endswith('.so')];python['extension_mapping_status']='OBSERVED_IN_SAME_PROCESS_SNAPSHOT_ONLY'
  with_parent=observed_store(nc.PARENT,False)
  try:parent_proof=with_parent.proof()
  finally:with_parent.close()
  session={'sessionid':fs.read_proc('/proc/self/sessionid',128).decode('ascii').strip(),'loginuid':fs.read_proc('/proc/self/loginuid',128).decode('ascii').strip(),'mount_namespace_inode':os.stat('/proc/self/ns/mnt').st_ino,'user_namespace_inode':os.stat('/proc/self/ns/user').st_ino,'created_session':False}
  for pin in pins:deadline();pin.verify()
  sockets=[socket_metadata(path) for path in scope['socket_metadata_only']];deadline()
  value={'schema':c.SCHEMA,'source_revision':scope['source_revision'],'source_closure_sha256':scope['source_closure_sha256'],'scope_sha256':scope_sha,'approval_record_sha256':record_sha,'uid':1000,'gid':1000,'started_monotonic_ns':started,'finished_monotonic_ns':time.monotonic_ns(),'timing_scope':'OBSERVATION_BEFORE_SERIALIZATION_AND_RECEIPT_WRITE; OWN_REAL_TIMER_ALSO_COVERS_WRITING','files':files,'ancestor_table':ancestor_table,'unavailable_files':unavailable,'alias_metadata':aliases,'native_parent':{'proof':parent_proof,'host_attestation':False,'actual_private_source_staged':False,'actual_private_scope_staged':False},'output_store':store.proof(),'python':python,'static_graph':static_observation(blobs),'mapping':mapping,'session':session,'bus_metadata':sockets,'manager_queries':0,'other_children':0,'automatic_retry':False,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
  value['evidence_origin']='LOCAL_APPROVED_FILE_INSPECTION_UNATTESTED'
  from . import manager_dependency_validate as validator
  raw=c.canonical(value)+b'\n';c.need(len(raw)<=c.CAP,'EVIDENCE_RECEIPT_BYTE_BOUND');deadline();receipt=store.write_new('native_evidence.json',raw)
  try:checked=validator.review(receipt.raw,c.sha(raw),scope_raw,scope_sha,record_raw,record_sha,scope['source_closure_sha256']);c.need(checked['status']=='PASS_READ_ONLY_OBSERVED_WITH_LIMITS','INDEPENDENT_EVIDENCE_VALIDATION_FAILED');receipt.verify()
  finally:receipt.close()
  check=store.write_new('native_evidence.sha256',(c.sha(raw)+'\n').encode());check.close();deadline()
  return {'status':'CAPTURED_READ_ONLY_OBSERVED_NOT_ATTESTED','sha256':c.sha(raw),'local_receipt':nc.DEST+'/native_evidence.json','manager_queries':0,'automatic_retry':False,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
 except BaseException as exc:
  if attempt_created:
   try:
    failure=store.write_new('observe_failure.json',c.canonical({'status':'ABORTED_PRIVATE_EVIDENCE_PRESERVED','exception_class':type(exc).__name__,'scope_sha256':scope_sha,'approval_record_sha256':record_sha,'automatic_retry':False}));failure.close()
   except (OSError,ValueError):pass
  raise
 finally:
  for pin in pins:pin.close()
  store.close()
def stage(scope_raw,record_raw,scope_sha,record_sha,raws):
 scope,record=nc.approval(scope_raw,record_raw,scope_sha,record_sha);c.need(scope['operation']=='NATIVE_STAGE_ONCE','SEPARATE_SCOPE_B_REQUIRED');interpreter();started=time.monotonic_ns();c.need(set(raws)==c.CLOSURE and sum(map(len,raws.values()))<=1048576,'MINIMAL_SOURCE_PAYLOAD')
 for name,b in raws.items():c.need(c.sha(b)==scope['source_closure_sha256'][name],'STAGE_SOURCE_HASH')
 parent=observed_store(nc.PARENT,False);store=None;attempt_created=False;staged_pins=[]
 try:
  store=fs.create_private(parent,nc.NAME);attempt=store.write_new('stage_attempt.json',c.canonical({'scope_sha256':scope_sha,'approval_record_sha256':record_sha,'single_use_consumed':True}));attempt.close();attempt_created=True
  for name,b in sorted(raws.items()):
   c.need(time.monotonic_ns()-started<30*10**9,'STAGE_SOFT_DEADLINE');pin=store.write_new(name,b,0o400);staged_pins.append(pin)
  pending=nc.pending(scope['source_revision'],scope['source_closure_sha256'],'NATIVE_READ_ONLY_ONCE');pin=store.write_new('pending_scope_A.json',c.canonical(pending));pin.close()
  result={'schema':'HH_G2_NATIVE_FINITE_STAGE_RECEIPT_V1','source_revision':scope['source_revision'],'source_closure_sha256':scope['source_closure_sha256'],'scope_sha256':scope_sha,'approval_record_sha256':record_sha,'store':store.proof(),'parent':parent.proof(),'source_files':len(raws),'source_bytes':sum(map(len,raws.values())),'source_mode':0o400,'scope_mode':0o600,'actual_private_source_staged':True,'actual_private_scope_staged':'PENDING_SCOPE_A_ONLY_NOT_MANAGER','host_attestation':False,'instance_qualification':'OBSERVED_AT_CREATION_NOT_PRE_ATTESTED','manager_queries':0,'automatic_retry':False}
  for pin in staged_pins:pin.verify()
  result['evidence_origin']='LOCAL_APPROVED_FILE_CREATION_UNATTESTED';result['source_instances']=[{'name':p.name,'sha256':c.sha(p.raw),'identity':fs.ident(os.fstat(p.fd))} for p in staged_pins];result['pending_scope_A_sha256']=c.sha(c.canonical(pending))
  receipt_raw=c.canonical(result);pin=store.write_new('stage_receipt.json',receipt_raw);pin.close();pin=store.write_new('stage_receipt.sha256',(c.sha(receipt_raw)+'\n').encode());pin.close();return {'status':'STAGED_NATIVE_SOURCE_AND_PENDING_SCOPE_NOT_ATTESTED','local_receipt':nc.DEST+'/stage_receipt.json','sha256':c.sha(receipt_raw),'manager_queries':0,'automatic_retry':False}
 except BaseException as exc:
  if attempt_created:
   try:
    failure=store.write_new('stage_failure.json',c.canonical({'status':'ABORTED_PRIVATE_STAGE_PRESERVED','exception_class':type(exc).__name__,'scope_sha256':scope_sha,'automatic_retry':False}));failure.close()
   except (OSError,ValueError):pass
  raise
 finally:
  for pin in staged_pins:pin.close()
  if store:store.close()
  parent.close()
def execute(scope_raw,record_raw,scope_sha,record_sha,raws):
 # The real timer is a soft watchdog, not a kernel hard CPU/RAM/wall envelope.
 scope,_=nc.approval(scope_raw,record_raw,scope_sha,record_sha)
 c.need(hasattr(signal,'setitimer') and signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0),'UNKNOWN_OR_EXISTING_SOFT_TIMER')
 old=signal.getsignal(signal.SIGALRM)
 def expired(signum,frame):raise TimeoutError('NATIVE_EVIDENCE_SOFT_WATCHDOG')
 signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,30)
 try:
  action=stage if scope['operation']=='NATIVE_STAGE_ONCE' else collect
  return action(scope_raw,record_raw,scope_sha,record_sha,raws)
 finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)

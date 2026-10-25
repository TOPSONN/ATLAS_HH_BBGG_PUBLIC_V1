"""Separate A observation and B finite creation. Neither authorizes Manager C."""
import datetime,re
from . import manager_dependency_contract as c
PARENT='/home/btu/simulations/hh_final_closure';NAME='g2_native_dependency_private_01';DEST=PARENT+'/'+NAME
LIMITS={'soft_seconds':30,'file_bytes':c.FILE_CAP,'aggregate_read_bytes':c.TOTAL_FILE_CAP,'files':c.MAX_FILES,'receipt_bytes':c.CAP,'max_modules':c.MAX_MODULES,'max_alias_hops':c.MAX_ALIASES,'automatic_retries':0}
SYSTEMCTL='37ec607113f55f1b385b4fa75588a43402aec0de57927500763b267713f10f63';PYTHON='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
LIBS=('ld-linux-x86-64.so.2','libc.so.6','libm.so.6','libcap.so.2','libseccomp.so.2','libcrypto.so.3','libssl.so.3','liblz4.so.1','liblzma.so.5','libzstd.so.1','libgcrypt.so.20','libgpg-error.so.0','libmount.so.1','libblkid.so.1','libpcre2-8.so.0','libselinux.so.1','libffi.so.8','libexpat.so.1','libz.so.1','libuuid.so.1')
STDLIB=('os.py','json/__init__.py','json/decoder.py','json/encoder.py','json/scanner.py','hashlib.py','re/__init__.py','struct.py','stat.py','ctypes/__init__.py','ctypes/_endian.py','importlib/__init__.py','importlib/abc.py','importlib/util.py','types.py','datetime.py','base64.py','enum.py','functools.py','collections/__init__.py','abc.py','contextlib.py','warnings.py','weakref.py','signal.py')
EXTENSIONS=('_ctypes','_struct','_hashlib','_json','_datetime','_sha2','_socket','select')
def pending(revision,hashes,operation):
 c.need(operation in ('NATIVE_READ_ONLY_ONCE','NATIVE_STAGE_ONCE'),'OPERATION');c.need(re.fullmatch('[0-9a-f]{40}',revision) is not None and set(hashes)==c.CLOSURE,'EXACT_V2_SOURCE_CLOSURE')
 for h in hashes.values():c.digest(h)
 files=[{'path':'/usr/bin/systemctl','sha256':SYSTEMCTL,'kind':'ELF','aliases':{}},{'path':'/usr/bin/python3.12','sha256':PYTHON,'kind':'ELF','aliases':{}}]
 files += [{'path':'/usr/lib/x86_64-linux-gnu/'+n,'sha256':None,'kind':'ELF','aliases':{}} for n in LIBS]
 files += [{'path':'/usr/lib/x86_64-linux-gnu/systemd/libsystemd-shared-255.so','sha256':None,'kind':'ELF','aliases':{}}]
 files += [{'path':'/usr/lib/python3.12/'+n,'sha256':None,'kind':'PYTHON_SOURCE','aliases':{}} for n in STDLIB]
 files += [{'path':'/usr/lib/python3.12/lib-dynload/'+n+'.cpython-312-x86_64-linux-gnu.so','sha256':None,'kind':'PYTHON_EXTENSION','aliases':{}} for n in EXTENSIONS]
 c.need(len(files)<=c.MAX_FILES,'FIXED_FILE_SET_BOUND')
 value={'schema':'HH_G2_NATIVE_PENDING_SCOPE_V1','source_revision':revision,'source_capsule_schema':c.CAPSULE_SCHEMA,'source_closure_sha256':hashes,'operation':operation,'uid':1000,'gid':1000,'python_version':[3,12,3],'authorization_reference':None,'execution_authorized':False,'limits':LIMITS,'parent':PARENT,'destination':DEST,'files':files,'alias_metadata_only':['/usr/bin/python3','/lib','/lib64','/usr/lib64/ld-linux-x86-64.so.2'],'proc_interfaces':['/proc/self/exe','/proc/self/maps','/proc/self/sessionid','/proc/self/loginuid','/proc/self/ns/mnt','/proc/self/ns/user','/proc/self/fdinfo/<OWNED_FD>','/proc/self/mountinfo'],'socket_metadata_only':['/run/dbus/system_bus_socket','/run/user/1000/systemd/private'],'new_directory_count':1 if operation=='NATIVE_STAGE_ONCE' else 0,'maximum_created_files':len(hashes)+5 if operation=='NATIVE_STAGE_ONCE' else 4,'maximum_created_bytes':2097152 if operation=='NATIVE_STAGE_ONCE' else c.CAP+12288,'stage_modes':{'directory':0o700,'source':0o400,'scope_and_receipt':0o600},'read_only_exception':'EXPLICIT_EXCLUSIVE_PRIVATE_ATTEMPT_RECEIPT_AND_CHECKSUM_ONLY; STAGING_REQUIRES_SEPARATE_B','systemctl_children':0,'target_ELF_execution':False,'no_WSL_startup':True,'no_network':True,'manager_authorized':False,'B_V2_accepted':False,'scope_B_parent_instance':'OBSERVED_AT_CREATION_NOT_PRE_ATTESTED; LATER_INDEPENDENT_REVIEW_REQUIRED'}
 value['source_input_root']=('/mnt/c/HH/.local/phase7i_g2_native_dependency_v1/source/simulation/hh_signal/final_closure/master' if operation=='NATIVE_STAGE_ONCE' else DEST)
 value['soft_watchdog']='OWN_POSIX_REAL_TIMER_30S; NO_UNINTERRUPTIBLE_IO_OR_KERNEL_HARD_ENVELOPE_CLAIM'
 value['file_allowlist_scope']='EXPLICIT_COLLECTOR_TARGET_READS; PYTHON_STARTUP_IMPORTS_NOT_FULLY_ATTESTED'
 if operation=='NATIVE_STAGE_ONCE':
  value['files']=[files[1]];value['alias_metadata_only']=[];value['socket_metadata_only']=[];value['proc_interfaces']=['/proc/self/exe','/proc/self/ns/mnt','/proc/self/fdinfo/<OWNED_FD>','/proc/self/mountinfo']
 return value

def check(scope):
 c.need(scope==pending(scope['source_revision'],scope['source_closure_sha256'],scope['operation']) if scope['authorization_reference'] is None else dict(scope,authorization_reference=None)==pending(scope['source_revision'],scope['source_closure_sha256'],scope['operation']),'FIXED_NATIVE_SCOPE_ONLY')
def approval(scope_raw,record_raw,scope_sha,record_sha,now=None,seen=(),allow_fixture=False):
 c.digest(scope_sha);c.digest(record_sha);c.need(record_sha not in c.CONSUMED and record_sha not in seen,'CONSUMED_OR_REPLAYED_APPROVAL');c.need(c.sha(scope_raw)==scope_sha and c.sha(record_raw)==record_sha,'APPROVAL_ORIGINAL_BYTES')
 scope=c.load(scope_raw);check(scope);c.need(scope['authorization_reference']==record_sha and scope['execution_authorized'] is False,'EXTERNAL_REFERENCE_NO_FLAG_GRANT');record=c.load(record_raw)
 provenance=record['provenance'];c.need(provenance=='USER_PROVIDED_VERBATIM_APPROVAL_REPORTED' or allow_fixture and provenance=='SYNTHETIC_TEST_FIXTURE','HUMAN_PROVENANCE_REQUIRED')
 c.need(record['operation']==scope['operation'] and record['source_revision']==scope['source_revision'] and record['maximum_attempts']==1 and type(record['maximum_attempts']) is int and record['manager_authorized'] is False,'EXACT_SINGLE_OPERATION')
 c.need(record['pending_scope_sha256']==c.sha(c.canonical(dict(scope,authorization_reference=None))) and record['identity_attestation'] is False,'APPROVAL_SCOPE_CHAIN')
 text=record['approval_text'];c.need(type(text) is str and 0<len(text.encode())<=16384 and c.sha((text.rstrip()+'\n').encode()) not in c.CONSUMED,'VERSION_APPROVAL_REUSE')
 expires=datetime.datetime.fromisoformat(record['expires_utc'].replace('Z','+00:00'));now=now or datetime.datetime.now(datetime.timezone.utc);c.need(expires.tzinfo is not None and now<expires<=now+datetime.timedelta(hours=24),'EXPIRED_OR_UNBOUNDED_APPROVAL')
 return scope,record

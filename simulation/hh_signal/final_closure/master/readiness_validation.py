"""Independent pure G1/G3/G5/G6/G7 readers. No device or privileged executor."""
import hashlib,json,re,uuid
from .contract import need,canonical,sha

def uint(v):return type(v) is int and 0<=v<2**63
def decimal(value):
 need(type(value) is str and re.fullmatch(r'0|[1-9][0-9]{0,18}',value) is not None,'COUNTER_SYNTAX')
 return int(value)
def pairs(text):
 result={}
 for line in text.splitlines():
  row=line.split();need(len(row)==2 and row[0] not in result,'DUPLICATE_OR_BAD_COUNTER');result[row[0]]=decimal(row[1])
 return result

# The V2 collector's exact limit fields, not a memory.* wildcard. Keep the
# historical decimal()/pairs() readers for geometry/other consumers unchanged.
CGROUP_MAX_FIELDS=frozenset(('memory.max','memory.swap.max','pids.max','cpu.max:quota'))
def cgroup_number(text):
 need(type(text) is str and re.fullmatch(r'0|[1-9][0-9]{0,19}',text) is not None,'COUNTER_SYNTAX')
 value=int(text);need(value<=2**64-1,'COUNTER_RANGE');return value

def cgroup_limit(name,text):
 need(name in CGROUP_MAX_FIELDS,'UNREVIEWED_LIMIT_FIELD')
 return 'UNLIMITED' if text=='max' else cgroup_number(text)

def cgroup_pairs(text):
 result={}
 for line in text.splitlines():
  row=line.split();need(len(row)==2 and row[0] not in result,'DUPLICATE_OR_BAD_COUNTER')
  result[row[0]]=cgroup_number(row[1])
 return result

def guest_review(value,expected_source,expected_legacy,*,now_monotonic_ns=None):
 need(type(value) is dict and value.get('schema')=='HH_G1_GUEST_READONLY_V2','GUEST_SCHEMA')
 need(len(canonical(value))<=262144 and value.get('source_sha256')==expected_source,'GUEST_BOUND_OR_SOURCE')
 need(value.get('legacy_source_sha256')==expected_legacy,'LEGACY_COLLECTOR_SOURCE')
 need(value.get('trust')=='REPORTED_UNATTESTED' and value.get('host_mapping_complete') is False,'UNSUPPORTED_ATTESTATION')
 start=value.get('started_monotonic_ns');end=value.get('ended_monotonic_ns')
 need(uint(start) and uint(end) and start<=end,'CLOCK_ORDER')
 if now_monotonic_ns is not None:need(uint(now_monotonic_ns) and 0<=now_monotonic_ns-end<=60_000_000_000,'STALE_CAPTURE_SAME_BOOT_CLOCK_REQUIRED')
 before=value['anchor_before'];after=value['anchor_after']
 for k in ('boot_id','cgroup','mount_namespace','pid','uid','gid'):need(canonical(before[k])==canonical(after[k]),'BOOT_NAMESPACE_OR_SESSION_CHANGED')
 need(all(uint(before.get(k)) for k in ('pid','uid','gid','monotonic_ns')) and before['pid']>0 and uint(after.get('monotonic_ns')),'ANCHOR_IDENTITY')
 need(start<=before['monotonic_ns']<=after['monotonic_ns']<=end,'ANCHOR_CLOCK')
 need(type(before['boot_id']) is str and str(uuid.UUID(before['boot_id'].strip()))==before['boot_id'].strip(),'BOOT_ID')
 need(set(before['mount_namespace'])=={'dev','inode'} and all(uint(x) and x>0 for x in before['mount_namespace'].values()),'NAMESPACE')
 records=value['records'];need(type(records) is list and len(records)<=768,'RECORD_BOUND')
 table={};used=0;seen={}
 for r in records:
  need(type(r) is dict and r.get('status') in ('UNKNOWN','REPORTED_UNATTESTED') and type(r.get('path')) is str,'RECORD_SCHEMA')
  path=r['path'];seen[path]=seen.get(path,0)+1
  if seen[path]>1:
   # acquire() reads exactly these anchors before and after. Other repeated
   # paths (including UNKNOWN/reported conflicts) are not merged silently.
   need(path in ('/proc/sys/kernel/random/boot_id','/proc/self/cgroup') and seen[path]<=2,'DUPLICATE_RECORD')
  if r['status']=='UNKNOWN':continue
  need(type(r.get('text')) is str and sha(r['text'].encode())==r.get('sha256'),'READBACK_DIGEST')
  owner=before['uid'] if r['path'].startswith('/proc/self/') else 0
  need(all(uint(r.get(k)) for k in ('uid','mode','dev','inode','bytes')) and r['uid']==owner,'READBACK_OWNERSHIP')
  need(r['bytes']==len(r['text'].encode())<=32768,'READBACK_BOUND');used+=r['bytes']
  if r['path'] in table:need(table[r['path']]['text']==r['text'],'REPEATED_READ_CHANGED')
  table[r['path']]=r
 need(used==value.get('retained_payload_bytes') and used<=196608,'PAYLOAD_COUNT')
 for path,key in (('/proc/sys/kernel/random/boot_id','boot_id'),('/proc/self/cgroup','cgroup')):
  need(path in table and table[path]['text']==before[key],'ANCHOR_READBACK_CONTRADICTION')
 need(type(before['cgroup']) is str and len([x for x in before['cgroup'].splitlines() if x.startswith('0::')])==1,'CGROUP_V2_IDENTITY')
 rel=next(x[3:] for x in before['cgroup'].splitlines() if x.startswith('0::'))
 need(rel.startswith('/') and all(x not in ('.','..','') for x in rel[1:].split('/')) if rel!='/' else True,'CGROUP_PATH')
 parts=[] if rel=='/' else rel[1:].split('/');need(len(parts)<=16,'LINEAGE_DEPTH')
 expected=['/sys/fs/cgroup'+('/'+'/'.join(parts[:n]) if n else '') for n in range(len(parts),-1,-1)]
 need(value.get('cgroup_lineage')==expected,'LINEAGE_COVERAGE')
 missing=[];limits=[];unlimited=[];missing_by_level=[];nonroot_missing=[]
 for level,path in enumerate(expected):
  item={};missing_start=len(missing)
  for name in ('cpu.stat','cpu.max','memory.max','memory.current','memory.peak','memory.events','memory.swap.max','memory.swap.current','cgroup.events','cgroup.controllers','cgroup.subtree_control','cgroup.type','pids.max','cgroup.procs'):
   if path+'/'+name not in table:missing.append(name);continue
   text=table[path+'/'+name]['text'].strip()
   if name in ('cpu.stat','memory.events','cgroup.events'):
    item[name]=cgroup_pairs(text)
    required={'cpu.stat':{'usage_usec','user_usec','system_usec'},'memory.events':{'oom','oom_kill'},'cgroup.events':{'populated','frozen'}}[name]
    missing.extend(name+':'+k for k in sorted(required-set(item[name])))
    if name=='cgroup.events':need(all(item[name].get(k,0) in (0,1) for k in ('populated','frozen')),'CGROUP_EVENT_CONTRADICTION')
   elif name in ('memory.max','memory.swap.max','pids.max'):item[name]=cgroup_limit(name,text)
   elif name in ('memory.current','memory.peak','memory.swap.current'):item[name]=cgroup_number(text)
   elif name=='cpu.max':
    fields=text.split();need(len(fields)==2,'CPU_RATE')
    quota=cgroup_limit('cpu.max:quota',fields[0]);period=cgroup_number(fields[1])
    need((quota=='UNLIMITED' or quota>0) and period>0,'CPU_RATE')
    item[name]={'quota_usec':quota,'period_usec':period,'kind':'BANDWIDTH_ONLY_NOT_CUMULATIVE_CPU'}
  selected={k:item[k] for k in ('memory.max','memory.swap.max','pids.max','cpu.max') if k in item}
  limits.append({'lineage_index':level,'limits':selected})
  unlimited.extend({'lineage_index':level,'field':k,'meaning':'UNLIMITED'} for k,v in selected.items() if v=='UNLIMITED')
  if item.get('cpu.max',{}).get('quota_usec')=='UNLIMITED':unlimited.append({'lineage_index':level,'field':'cpu.max:quota','meaning':'UNLIMITED'})
  absent=missing[missing_start:]
  if absent:missing_by_level.append({'lineage_index':level,'root_cgroup':path=='/sys/fs/cgroup','fields':sorted(set(absent))})
  if path!='/sys/fs/cgroup':nonroot_missing.extend(absent)
 # Separate file reads are not an atomic snapshot: current may exceed a newly
 # reduced max; a later current can exceed an earlier peak. Do not invent
 # cross-file conservation or derive swap-disabled/enforcement from usage=0.
 need(all(type(x) is dict and x.get('relation_complete') is True for x in value['block_graph']),'INCOMPLETE_BLOCK_RELATIONS')
 return {'status':'PASS_READ_ONLY_OBSERVED','trust':'REPORTED_UNATTESTED','lineage_count':len(expected),
  'missing_counter_names':sorted(set(missing)),'effective_manager_state':'UNKNOWN_NOT_BUS_ATTESTED',
  'missing_by_lineage':missing_by_level,'nonroot_missing_counter_names':sorted(set(nonroot_missing)),
  'counter_coverage':'INCOMPLETE_OBSERVED' if missing else 'COMPLETE_FOR_COLLECTED_FIELDS',
  'limit_observations':limits,'unlimited_limits':unlimited,
  'boot_consistent_within_capture':True,'mount_namespace_consistent_within_capture':True,
  'cgroup_membership_consistent_within_capture':True,'swap_disabled_verified':False,
  'freshness':'CHECKED_SAME_BOOT_CLOCK' if now_monotonic_ns is not None else 'UNKNOWN_NO_CURRENT_SAME_BOOT_CLOCK',
  'host_mapping_complete':False,'complete_attestation':False,'runtime_enforcement':False,'kernel_acceptance':None}

def device_adapter(host,guest=None):
 from ..resource_closure.g1_acquisition import validate_host
 validate_host(host)
 need(guest is None or guest.get('trust')=='REPORTED_UNATTESTED','GUEST_ORIGIN')
 # No host/guest map or all-mount-namespace inventory is available from either
 # collector. Never manufacture device_policy's complete=true from JSON shape.
 return {'status':'REJECTED_INCOMPLETE_ACQUISITION','host_sha256':sha(canonical(host)),
  'guest_available':guest is not None,'complete':False,'host_mapping_complete':False,
  'all_mount_namespaces_complete':False,'nodes':[],
  'supported_future_candidate':'INDEPENDENT_DISPOSABLE_WHOLE_DISK_ONLY',
  'rejected_topologies':['part','sibling','dm','loop','thin','sparse','snapshot','growable','unknown_alias','protected_backing'],
  'operation_authorized':False}

def review_same_instance(records,plan):
 need(type(records) is list and len(records)==4 and type(plan) is dict,'TRANSACTION_SHAPE')
 need(plan.get('consumer')=='SAME_FD_IN_PROCESS_REVIEWED_HELPER','PATH_REOPENING_CONSUMER')
 need(all(type(x) is dict and canonical(x.get('identity'))==canonical(plan.get('expected_identity')) for x in records),'FD_HELPER_OR_LEASE_SUBSTITUTION')
 from ..resource_closure.instance_binding import review_transaction
 r=review_transaction(records,plan)
 need(plan.get('all_host_writers_excluded_required') is True,'WRITER_BOUNDARY')
 return dict(r,consumer='NO_PRIVILEGED_FD_CONSUMER_IMPLEMENTED',runtime_closed=False)

def geometry(readback,profile):
 need(type(readback) is dict and type(profile) is dict,'GEOMETRY_OBJECT')
 fields=('device_bytes','block_size','block_count','inode_count','inode_size','journal_blocks','free_blocks','free_inodes')
 need(all(uint(readback.get(k)) for k in fields),'MISSING_GEOMETRY')
 need(readback.get('raw_sha256') and re.fullmatch('[0-9a-f]{64}',readback['raw_sha256']),'RAW_BINDING')
 need(readback.get('filesystem')=='ext4' and readback.get('internal_journal') is True and 'has_journal' in readback.get('features',[]),'JOURNAL_REQUIRED')
 need(readback.get('source_instance_sha256')==profile['source_instance_sha256'],'SOURCE_INSTANCE')
 need(type(profile.get('source_instance_sha256')) is str and re.fullmatch('[a-f0-9]{64}',profile['source_instance_sha256']),'UNBOUND_DEVICE_INSTANCE')
 need(readback.get('uuid')==profile.get('expected_uuid') and str(uuid.UUID(readback['uuid']))==readback['uuid'] and readback['uuid'] not in profile.get('protected_uuids',[]),'FILESYSTEM_UUID')
 need(readback.get('label')==profile.get('expected_label') and readback.get('external_journal') is False,'LABEL_OR_EXTERNAL_JOURNAL')
 need(type(profile.get('expected_label')) is str and 0<len(profile['expected_label'].encode('utf-8'))<=16,'LABEL_BOUND')
 for k in ('device_bytes','block_size','block_count','inode_count','inode_size','journal_blocks'):need(readback[k]==profile[k],'EXACT_REVIEWED_GEOMETRY')
 need(readback['block_size']*readback['block_count']<=readback['device_bytes'],'DEVICE_CAPACITY')
 need(1024<=readback['journal_blocks']<=readback['block_count']//2,'JOURNAL_GEOMETRY')
 need(readback['free_blocks']<=readback['block_count'] and readback['free_inodes']<=readback['inode_count'],'FREE_COUNTS')
 need(readback['free_blocks']*readback['block_size']>=32768 and readback['free_inodes']>=8,'EVIDENCE_RESERVE')
 return {'status':'PASS_GEOMETRY_INPUT_CONSISTENCY_ONLY','allocated_capacity_bytes':readback['block_size']*readback['block_count'],
  'inode_ceiling':readback['inode_count'],'journal_included_in_fixed_volume':True,'power_loss_verified':False,
  'live_readback_authenticated':False,'format_or_mount_authorized':False}

def parse_geometry_header(raw,device_bytes,instance_sha256):
 """Strict reviewed dumpe2fs-header subset; unknown versions stay rejected.

 No command is executed. Native command/source/device provenance must be
 acquired separately; a digest plus parse is input consistency, not attestation.
 """
 need(type(raw) is bytes and len(raw)<=16384,'GEOMETRY_HEADER_BOUND')
 text=raw.decode('utf-8');need(len(text.splitlines())<=256,'GEOMETRY_HEADER_ROWS')
 data={}
 for line in text.splitlines():
  if ':' not in line:continue
  key,value=line.split(':',1);key=key.strip();need(key not in data,'DUPLICATE_GEOMETRY_HEADER');data[key]=value.strip()
 mapping={'Block size':'block_size','Block count':'block_count','Inode count':'inode_count','Inode size':'inode_size',
  'Total journal blocks':'journal_blocks','Free blocks':'free_blocks','Free inodes':'free_inodes'}
 need(all(k in data for k in (*mapping,'Filesystem features','Filesystem UUID','Filesystem volume name','Journal inode')),'GEOMETRY_HEADER_FIELDS')
 need(decimal(data['Journal inode'])>0,'JOURNAL_INODE')
 result={v:decimal(data[k]) for k,v in mapping.items()}
 result.update(device_bytes=device_bytes,source_instance_sha256=instance_sha256,raw_sha256=sha(raw),
  filesystem='ext4',uuid=data['Filesystem UUID'],label=data['Filesystem volume name'],features=data['Filesystem features'].split(),
  internal_journal=True,external_journal='Journal device' in data)
 return result

def postmount(readback,contract):
 from ..resource_closure.mount_attestation import parse_mountinfo
 need(type(readback) is dict and type(contract) is dict,'MOUNT_READBACK_OBJECT')
 need(readback.get('namespace_before')==contract.get('namespace')==readback.get('namespace_after') and contract.get('namespace') is not None,'MOUNT_NAMESPACE')
 target=contract.get('mountpoint');need(type(target) is str and target.startswith('/srv/atlas-hh/'),'MOUNT_TARGET')
 rows=parse_mountinfo(readback['mountinfo'].encode());selected=[x for x in rows if x['path']==target]
 need(len(selected)==1 and not any(x['path'].startswith(target+'/') for x in rows),'MOUNT_SUBSTITUTION_OR_NESTED')
 row=selected[0];need(row['dev']==contract['major_minor'] and row['filesystem_type']=='ext4' and row['root']=='/','MOUNT_DEVICE_OR_BIND')
 need({'rw','nodev','nosuid','noexec'}<=set(row['mount_options']),'MOUNT_OPTIONS')
 need(readback.get('filesystem_uuid')==contract.get('filesystem_uuid') and type(contract.get('filesystem_uuid')) is str,'FILESYSTEM_UUID')
 need(type(readback.get('mount_root_uid')) is int and readback['mount_root_uid']==contract.get('mount_root_uid') and type(readback.get('mount_root_mode')) is int and readback['mount_root_mode']==0o700,'POST_MOUNT_ROOT_OWNERSHIP')
 need(readback.get('worker_raw_device_access') is False and readback.get('unexpected_writable_sources')==[],'WORKER_WRITE_BOUNDARY')
 need(readback.get('independent_findmnt')=={'target':target,'major_minor':contract['major_minor'],'uuid':contract['filesystem_uuid']},'INDEPENDENT_MOUNT_READBACK')
 return {'status':'PASS_POSTMOUNT_INPUT_CONSISTENCY_ONLY','mount_executed':False,'runtime_acceptance':False}

def resource_trace(records,limit):
 need(type(records) is list and 2<=len(records)<=64,'TRACE_COUNT')
 identity=None;last=None;dead=False;invocation=None
 for row in records:
  need(all(uint(row.get(k)) for k in ('monotonic_ns','CPU_usec','memory_peak_bytes','swap_bytes','cgroup_inode')),'MISSING_KERNEL_COUNTER')
  need(row.get('InvocationID') and re.fullmatch('[a-f0-9]{32}',row['InvocationID']),'INVOCATION_ID')
  need(row.get('worker_state') in ('NOT_STARTED','RUNNING','DEAD_OBSERVED'),'UNKNOWN_WORKER_STATE')
  raw=row.get('cpu_stat');need(type(raw) is dict and {'usage_usec','user_usec','system_usec'}<=set(raw),'RAW_CPU_STAT_REQUIRED')
  need(all(uint(raw[k]) for k in ('usage_usec','user_usec','system_usec')) and raw['usage_usec']==row['CPU_usec'] and abs(raw['usage_usec']-raw['user_usec']-raw['system_usec'])<=2,'RAW_CPU_COUNTER_CONTRADICTION')
  memory=row.get('memory_events');need(type(memory) is dict and all(uint(memory.get(k)) for k in ('oom','oom_kill')),'RAW_MEMORY_EVENTS_REQUIRED')
  need(memory['oom']==0 and memory['oom_kill']==0,'RAW_OOM_FAILURE')
  key=(row.get('boot_id'),row.get('cgroup_dev'),row['cgroup_inode'],row.get('collector_identity'))
  need(all(x is not None for x in key),'COLLECTOR_IDENTITY')
  need(type(key[0]) is str and str(uuid.UUID(key[0]))==key[0] and uint(key[1]) and key[2]>0 and type(key[3]) is str and 0<len(key[3])<=256,'TRACE_KERNEL_IDENTITY')
  if identity is None:identity=key;invocation=row['InvocationID']
  need(key==identity and invocation==row['InvocationID'],'IDENTITY_REPLAY_OR_SUBSTITUTION')
  if last:need(row['monotonic_ns']>last['monotonic_ns'] and row['CPU_usec']>=last['CPU_usec'] and row['memory_peak_bytes']>=last['memory_peak_bytes'],'CLOCK_OR_COUNTER_RESET')
  need(not dead or row.get('worker_state')!='RUNNING','WORKER_RESURRECTION')
  dead|=row.get('worker_state')=='DEAD_OBSERVED';last=row
 first=records[0];end=records[-1]
 need(first.get('phase')=='admission' and end.get('phase')=='collector_finalized','FULL_WALL_ENDPOINTS')
 need(first['CPU_usec']==0 and end['worker_state']=='DEAD_OBSERVED','FRESH_CGROUP_AND_TERMINAL_STATE')
 need(end.get('cgroup_empty') is True and end.get('owned_descendants')==[] and end.get('postmortem_raw_sha256') and re.fullmatch('[a-f0-9]{64}',end['postmortem_raw_sha256']),'MISSING_CLEANUP_OR_POSTMORTEM')
 need(type(end.get('final_observer_identity')) is str and end['final_observer_identity'] and end['final_observer_identity']!=end['collector_identity'],'COLLECTOR_CANNOT_ATTEST_OWN_POST_EXIT_EMPTY_GROUP')
 need(type(end.get('cgroup_events')) is dict and type(end['cgroup_events'].get('populated')) is int and end['cgroup_events']['populated']==0,'RAW_CGROUP_EMPTY_REQUIRED')
 cpu=end['CPU_usec']-first['CPU_usec'];wall=end['monotonic_ns']-first['monotonic_ns']
 need(cpu<=limit['CPU_seconds']*1000000 and wall<=limit['wall_seconds']*1000000000,'ACTUAL_CPU_OR_WALL_OVERRUN')
 need(end['memory_peak_bytes']<=limit['RAM_bytes'] and all(r['swap_bytes']==0 for r in records),'RAM_OR_SWAP_FAILURE')
 need(all(r.get('cause') not in ('OOM','timeout','controller_loss','collector_crash','ENOSPC','missing_postmortem') for r in records),'FAILURE_EVENT_NOT_SUCCESS')
 return {'status':'PASS_REPORTED_TRACE_CONSISTENCY_ONLY','CPU_usec':cpu,'wall_ns':wall,
  'authenticated_kernel_receipt':False,'actual_enforcement_proven':False,'runtime_acceptance':False}

def live_operation(*args,**kwargs):raise PermissionError('NO_PRIVILEGED_OR_KERNEL_DISPATCHER; SEPARATE_EXACT_SCOPE_REQUIRED')

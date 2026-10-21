"""V2 compact local CIM edge contract. Reported topology is never attestation."""
import re

KEYS=('disk_partition_links','partition_volume_links')
CONTRACT='LOCAL_CIM_COMPACT_EDGES_V1'

def require(ok,reason):
 if not ok:raise ValueError('ASSOCIATION_'+reason)

def identity(value):
 require(type(value) is str and 0<len(value)<=1024 and re.fullmatch(r'[\x20-\x7e]+',value) is not None,'DEVICE_ID')
 return value.lower()

def endpoint(value,expected):
 require(type(value) is dict and set(value)=={'class','namespace','server','device_id'},'ENDPOINT_SHAPE')
 require(value['class']==expected and value['namespace']=='root/cimv2' and value['server']=='LOCAL_CHECKED','ENDPOINT_CLASS_OR_ORIGIN')
 return identity(value['device_id'])

def integer(value):return type(value) is int and 0<=value<=4294967295

def validate(rows):
 """Reject partial graphs, extra fields, unknown origins, duplicate or conflicting keys.

 Provider end-of-enumeration is a reported property, not independently measurable
 from JSON. Fixed disk coverage and referential checks detect internal omissions.
 """
 def inventory(key):
  row=rows[key];require(row['status']=='REPORTED_UNATTESTED','PREREQUISITE_INCOMPLETE')
  result={}
  for item in row['data']:
   require(type(item) is dict,'INVENTORY_SHAPE');key_id=identity(item.get('DeviceID'))
   require(key_id not in result,'INVENTORY_DUPLICATE');result[key_id]=item
  return result
 for key in KEYS:
  row=rows[key]
  if row['status']!='REPORTED_UNATTESTED':
   require('data' not in row and row.get('provider_enumeration_complete') is not True,'FAILED_PARTIAL_DATA')
   continue
  require(row.get('association_encoding')==CONTRACT and row.get('provider_enumeration_complete') is True,'ENUMERATION_INCOMPLETE')
  require(type(row.get('enumerated_edge_count')) is int and row['enumerated_edge_count']==len(row['data']),'EDGE_COUNT')
  disk=key==KEYS[0]
  left=inventory('disk_drives' if disk else 'partitions');right=inventory('partitions' if disk else 'logical_disks')
  if not disk:require(rows[KEYS[0]]['status']=='REPORTED_UNATTESTED','PREREQUISITE_INCOMPLETE')
  seen=set();parents=set();covered=set()
  for edge in row['data']:
   fields={'association_class','antecedent','dependent'}| (set() if disk else {'starting_address','ending_address'})
   require(type(edge) is dict and set(edge)==fields,'EDGE_SHAPE')
   require(edge['association_class']==('Win32_DiskDriveToDiskPartition' if disk else 'Win32_LogicalDiskToPartition'),'CLASS')
   a=endpoint(edge['antecedent'],'Win32_DiskDrive' if disk else 'Win32_DiskPartition')
   b=endpoint(edge['dependent'],'Win32_DiskPartition' if disk else 'Win32_LogicalDisk')
   require(a in left and b in right,'DANGLING_ENDPOINT')
   require((a,b) not in seen,'DUPLICATE_OR_CONFLICT');seen.add((a,b));covered.add(b)
   if disk:
    x=left[a].get('Index');y=right[b].get('DiskIndex')
    require(integer(x) and integer(y) and x==y and b not in parents,'DISK_PARENT_CONTRADICTION');parents.add(b)
   else:
    values=[edge[n] for n in ('starting_address','ending_address')]
    require(all(type(x) is str and re.fullmatch(r'0|[1-9][0-9]{0,19}',x) for x in values),'EXTENT_REQUIRED')
    start,end=map(int,values);require(0<=start<=end<=18446744073709551615,'EXTENT_ORDER')
  if disk:require(parents==set(right),'PARTITION_COVERAGE_INCOMPLETE')
  else:
   require(all(integer(x.get('DriveType')) for x in right.values()),'DRIVE_TYPE')
   require({k for k,v in right.items() if v['DriveType']==3}<=covered,'FIXED_VOLUME_COVERAGE_INCOMPLETE')
 return {'contract':CONTRACT,'status':'COMPACT_EDGES_REPORTED_UNATTESTED',
         'coverage_is_host_attestation':False,'guest_validated':False,'G2_authorized':False}

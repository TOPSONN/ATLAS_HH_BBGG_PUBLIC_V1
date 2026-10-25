"""Static closure and observed origins. Does not attest another process lifetime."""
import re,stat
from . import manager_dependency_contract as c,manager_elf as elf
def graph(blobs,roots,resolutions,aliases):
 c.need(type(blobs) is dict and 0<len(blobs)<=c.MAX_FILES and sum(map(len,blobs.values()))<=c.TOTAL_FILE_CAP,'GRAPH_INPUT_BOUND')
 nodes={c.path(p):elf.parse(b) for p,b in blobs.items()};c.need(type(roots) is list and roots and len(roots)==len(set(roots)) and set(roots)<=set(nodes),'GRAPH_ROOTS')
 c.need(type(resolutions) is list and len(resolutions)<=c.MAX_EDGES,'GRAPH_EDGE_BOUND');edge_map={}
 for row in resolutions:
  c.need(set(row)=={'from','needed','to','provenance'} and row['from'] in nodes and row['to'] in nodes,'GRAPH_EDGE_SCHEMA')
  c.need(row['provenance'] in ('REVIEWED_EXACT_FILE_SET','REVIEWED_RPATH','REVIEWED_RUNPATH'),'RESOLUTION_PROVENANCE');key=(row['from'],row['needed']);c.need(key not in edge_map,'DUPLICATE_RESOLUTION');edge_map[key]=row
 sonames={}
 for p,n in nodes.items():
  if n['soname']:c.need(n['soname'] not in sonames,'DUPLICATE_SONAME');sonames[n['soname']]=p
 edges=[];used=set();seen=set();active=set();cycles=[]
 def walk(p):
  if p in active:cycles.append(p);return
  if p in seen:return
  seen.add(p);active.add(p);n=nodes[p]
  if n['interpreter']:
   requested=n['interpreter'];target=aliases.get(requested,requested);c.need(target in nodes,'MISSING_ELF_INTERPRETER');edges.append({'from':p,'needed':'PT_INTERP','to':target,'provenance':'REVIEWED_INTERPRETER_ALIAS'});walk(target)
  for needed in n['needed']:
   key=(p,needed);c.need(key in edge_map,'MISSING_TRANSITIVE_DEPENDENCY');row=edge_map[key];target=row['to'];c.need(nodes[target]['soname']==needed,'SONAME_EDGE_MISMATCH')
   dirs=n['runpath'] or n['rpath']
   if dirs:
    expanded=[c.path(directory.replace('$ORIGIN',p.rsplit('/',1)[0])) for directory in dirs.split(':')]
    c.need(row['provenance']==('REVIEWED_RUNPATH' if n['runpath'] else 'REVIEWED_RPATH') and target.rsplit('/',1)[0] in expanded,'SEARCH_PATH_RESOLUTION_NOT_REVIEWED')
   used.add(key);edges.append(row);walk(target)
  active.remove(p)
 for root in roots:walk(root)
 c.need(used==set(edge_map) and seen==set(nodes),'UNUSED_OR_UNREACHABLE_GRAPH_INPUT')
 return {'status':'PASS_STATIC_ELF_GRAPH','nodes':nodes,'edges':edges,'cycle_nodes':sorted(set(cycles)),'resolution_scope':'EXACT_REVIEWED_EDGES_NOT_LDSO_SEARCH_ATTESTATION','COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
def python_imports(value,files,expected):
 c.need(value['schema']=='PYTHON_RUNTIME_IMPORT_EVIDENCE_V1' and value['version']==[3,12,3] and value['isolated'] is True and value['no_site'] is True and value['no_bytecode_write'] is True,'PYTHON_INTERPRETER_OR_FLAGS')
 c.need(value['sys_path']==expected['sys_path'] and value['meta_path']==expected['meta_path'],'PYTHON_IMPORT_MACHINERY_OR_PATH')
 rows=value['modules'];c.need(0<len(rows)<=c.MAX_MODULES and {r['name'] for r in rows}==set(expected['modules']) and len(rows)==len(expected['modules']),'PYTHON_MODULE_SET')
 unknown=[]
 for row in rows:
  name=row['name'];c.need(re.fullmatch('[A-Za-z_][A-Za-z_0-9.]*',name) is not None,'PYTHON_MODULE_NAME');want=expected['modules'][name];kind=row['origin_class'];c.need(row['origin']==want['origin'] and kind==want['origin_class'],'PYTHON_ORIGIN_DRIFT')
  if kind in ('BUILTIN','FROZEN'):c.need(row['origin']==('built-in' if kind=='BUILTIN' else 'frozen') and row['sha256'] is None and row['file_identity'] is None,'PYTHON_INTERNAL_ORIGIN')
  elif kind in ('SOURCE','BYTECODE','EXTENSION'):
   p=c.path(row['origin']);c.need(p in files and row['sha256']==files[p]['sha256'] and row['file_identity']==files[p]['identity'],'PYTHON_FILE_INSTANCE')
   if kind=='BYTECODE':c.need(want.get('bytecode_reviewed') is True and p.endswith('.pyc'),'UNREVIEWED_PYC')
   elif kind=='SOURCE':c.need(p.endswith('.py'),'PYTHON_SOURCE_SUFFIX');unknown.append(name+':EXECUTED_CACHE_OR_BYTES_NOT_PROVEN_BY_SOURCE_ORIGIN')
   else:c.need(p.endswith('.so') and p in value['mapped_extensions'],'PYTHON_EXTENSION_MAPPING')
  else:raise ValueError('UNKNOWN_PYTHON_ORIGIN')
 c.need(value['actual_executable']==expected['actual_executable'] and value['actual_executable'] in files,'PYTHON_EXECUTABLE_INSTANCE')
 return {'status':'PASS_PYTHON_OBSERVED_ORIGIN_CONTRACT','module_count':len(rows),'execution_bytes_unproven':unknown,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
def mapping(raw,files):
 c.need(type(raw) is bytes and len(raw)<=65536,'MAPPING_SNAPSHOT_BOUND');paths=set();lines=raw.decode('ascii').splitlines();c.need(len(lines)<=512,'MAPPING_LINE_BOUND')
 for line in lines:
  fields=line.split(maxsplit=5);c.need(len(fields)>=5 and re.fullmatch('[0-9a-f]+-[0-9a-f]+',fields[0]) is not None,'MAPPING_SYNTAX')
  if len(fields)==6 and fields[5].startswith('/'):
   p=c.path(fields[5]);c.need(p in files,'UNLISTED_RUNTIME_MAPPING');major,minor=fields[3].split(':');ident=files[p]['identity'];c.need(int(fields[4])==ident['st_ino'] and int(major,16)==ident['device_major'] and int(minor,16)==ident['device_minor'],'MAPPING_DEVICE_INODE');paths.add(p)
 return {'status':'PASS_ACTUAL_RUNTIME_MAPPING_EVIDENCE_WITH_LIMITS','mapped_paths':sorted(paths),'lifetime_coverage':False,'future_child_identity_bound':False,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
def manager_gate(evidence):
 c.need(evidence.get('static_graph',{}).get('status')=='PASS_STATIC_ELF_GRAPH','BLOCKED_STATIC_DEPENDENCY_GRAPH')
 c.need(evidence.get('python_imports',{}).get('status')=='PASS_PYTHON_OBSERVED_ORIGIN_CONTRACT','BLOCKED_PYTHON_IMPORT_EVIDENCE')
 # No current collector observes complete dlopen/NSS/plugin resolution for the future child.
 c.need(not evidence.get('COMPLETE_DYNAMIC_RESOLUTION_ATTESTED',False),'UNSUPPORTED_ATTESTATION_CLAIM')
 raise ValueError('BLOCKED_EXECUTION_LIFECYCLE_RESOLUTION_EVIDENCE_NOT_IMPLEMENTED')

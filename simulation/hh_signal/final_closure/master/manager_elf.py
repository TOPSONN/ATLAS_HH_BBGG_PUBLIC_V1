"""Bounded ELF64 little-endian x86-64 parser. Never executes target bytes."""
import struct
from . import manager_dependency_contract as c
U64=2**64-1
def span(raw,off,size):
 c.need(type(off) is int and type(size) is int and 0<=off<=U64 and 0<=size<=U64-off and off+size<=len(raw),'ELF_RANGE_OR_OVERFLOW');return raw[off:off+size]
def text(raw,off):
 c.need(0<=off<len(raw),'ELF_STRING_OFFSET');end=raw.find(b'\0',off);c.need(off<=end and end-off<=512,'ELF_STRING_TERMINATOR')
 s=raw[off:end].decode('ascii');c.need(s and all(32<=ord(ch)<127 for ch in s),'ELF_STRING_CHARACTERS');return s
def parse(raw):
 c.need(type(raw) is bytes and 64<=len(raw)<=c.FILE_CAP,'ELF_FILE_BOUND');c.need(raw[:4]==b'\x7fELF','ELF_MAGIC')
 c.need(raw[4] in (1,2),'ELF_CLASS');c.need(raw[4]==2,'UNSUPPORTED_ELF32');c.need(raw[5]==1,'UNSUPPORTED_ELF_ENDIANNESS');c.need(raw[6]==1 and raw[7] in (0,3),'ELF_IDENT_VERSION_ABI')
 kind,machine,version,entry,phoff,shoff,flags,ehsize,phsize,phnum,shsize,shnum,shstr=struct.unpack_from('<HHIQQQIHHHHHH',raw,16)
 c.need(kind in (2,3) and machine==62 and version==1 and ehsize==64,'ELF_MACHINE_TYPE_ABI');c.need(phsize==56 and 0<phnum<=128,'ELF_PHDR_COUNT_SIZE');span(raw,phoff,phnum*56)
 c.need((shoff==0 and shnum==0 and shstr==0) or (shoff>=64 and shsize==64 and 0<shnum<=4096 and shstr<shnum),'ELF_SECTION_TABLE')
 if shoff:
  span(raw,shoff,shnum*64)
  for i in range(shnum):
   name,typ,sflags,addr,off,size,link,info,align,entsize=struct.unpack_from('<IIQQQQIIQQ',raw,shoff+i*64)
   c.need(align==0 or align&(align-1)==0,'ELF_SECTION_ALIGNMENT');c.need(link<shnum,'ELF_SECTION_LINK')
   if typ!=8:span(raw,off,size)
 loads=[];dynamic=[];interp=[]
 for i in range(phnum):
  typ,pflags,off,vaddr,paddr,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',raw,phoff+i*56)
  span(raw,off,filesz);c.need(vaddr<=U64-memsz and filesz<=memsz,'ELF_SEGMENT_OVERFLOW_OR_SIZE');c.need(align in (0,1) or align&(align-1)==0,'ELF_SEGMENT_ALIGNMENT')
  if typ==1:
   c.need(align in (0,1) or off%align==vaddr%align,'ELF_LOAD_ALIGNMENT');loads.append((off,vaddr,filesz))
  elif typ==2:dynamic.append((off,filesz))
  elif typ==3:
   b=span(raw,off,filesz);c.need(1<filesz<=512 and b.endswith(b'\0') and b.count(b'\0')==1,'ELF_INTERP_STRING');interp.append(c.path(b[:-1].decode('ascii')))
 c.need(loads and len(dynamic)<=1 and len(interp)<=1,'ELF_AMBIGUOUS_SEGMENTS');tags={};needed=[]
 if dynamic:
  off,size=dynamic[0];c.need(0<size<=65536 and size%16==0,'ELF_DYNAMIC_BOUND');terminated=False
  c.need(any(a<=off and size<=n-(off-a) for a,_,n in loads if a<=off<=a+n),'ELF_DYNAMIC_LOAD_MAPPING')
  for i in range(size//16):
   tag,value=struct.unpack_from('<qQ',raw,off+i*16)
   if terminated:c.need(tag==value==0,'ELF_DATA_AFTER_DT_NULL');continue
   if tag==0:terminated=True;continue
   c.need(tag not in (0x6ffffefa,0x6ffffefb,0x6ffffefc,0x7ffffffd,0x7fffffff),'UNSUPPORTED_ELF_DYNAMIC_AUDIT_FILTER')
   if tag==1:needed.append(value);c.need(len(needed)<=128,'ELF_NEEDED_BOUND')
   elif tag in (5,10,14,15,29):c.need(tag not in tags,'ELF_DUPLICATE_DYNAMIC_TAG');tags[tag]=value
  c.need(terminated,'ELF_MISSING_DT_NULL')
 strings=b''
 if needed or any(k in tags for k in (14,15,29)):
  c.need(5 in tags and 10 in tags and 0<tags[10]<=1048576,'ELF_MISSING_STRTAB');locations=[]
  for off,vaddr,size in loads:
   if vaddr<=tags[5] and tags[5]-vaddr<=size and tags[10]<=size-(tags[5]-vaddr):locations.append(off+tags[5]-vaddr)
  c.need(len(locations)==1,'ELF_STRTAB_LOAD_MAPPING');strings=span(raw,locations[0],tags[10]);c.need(strings[0]==0,'ELF_STRTAB_START')
 result={'format':'ELF64_LE_X86_64','sha256':c.sha(raw),'bytes':len(raw),'type':kind,'interpreter':interp[0] if interp else None,'needed':[text(strings,x) for x in needed],'soname':text(strings,tags[14]) if 14 in tags else None,'rpath':text(strings,tags[15]) if 15 in tags else None,'runpath':text(strings,tags[29]) if 29 in tags else None}
 c.need(len(result['needed'])==len(set(result['needed'])),'ELF_DUPLICATE_NEEDED')
 for name in result['needed']:c.need('/' not in name and name not in ('.','..'),'ELF_NEEDED_PATH_NOT_SUPPORTED')
 for key in ('rpath','runpath'):
  if result[key]:
   for directory in result[key].split(':'):
    if directory=='$ORIGIN':continue
    if directory.startswith('$ORIGIN/'):c.path(directory.replace('$ORIGIN','/REVIEWED_ORIGIN',1));c.need('$' not in directory[7:],'ELF_DYNAMIC_TOKEN_NOT_REVIEWED')
    else:c.path(directory);c.need('$' not in directory,'ELF_DYNAMIC_TOKEN_NOT_REVIEWED')
 return result

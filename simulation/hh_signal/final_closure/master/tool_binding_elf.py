"""Bounded static ELF64 header facts; never executes a loader or resolves libraries."""
import struct
from .diagnostic_contract import need
def inspect(raw):
 need(type(raw) is bytes and 64<=len(raw)<=64*1024**2,'ELF_BYTE_BOUND')
 need(raw[:7]==b'\x7fELF\x02\x01\x01','ELF64_LITTLE_ENDIAN')
 header=struct.unpack_from('<HHIQQQIHHHHHH',raw,16)
 need(header[1]==62 and header[7]==64 and header[8]==56 and 0<header[9]<=64,'ELF_HEADER')
 offset=header[4];count=header[9];need(offset>=64 and offset+count*56<=len(raw),'PROGRAM_HEADER_BOUND')
 interps=[];dynamic=False;loads=0
 for i in range(count):
  kind,flags,where,virtual,physical,size,memsz,align=struct.unpack_from('<IIQQQQQQ',raw,offset+i*56)
  need(where<=len(raw) and size<=len(raw)-where,'SEGMENT_BOUND')
  if kind==1:loads+=1
  if kind==2:dynamic=True
  if kind==3:
   need(1<size<=512,'INTERPRETER_BOUND');value=raw[where:where+size];need(value[-1:]==b'\0' and b'\0' not in value[:-1],'INTERPRETER_NUL')
   text=value[:-1].decode('ascii');need(text.startswith(('/lib/','/lib64/','/usr/lib/')) and '..' not in text.split('/'),'INTERPRETER_PATH');interps.append(text)
 need(len(interps)<=1 and loads>0,'ELF_INTERPRETER_OR_LOADS')
 return {'format':'ELF64_LE_X86_64','interpreter':interps[0] if interps else None,'PT_DYNAMIC_present':dynamic,'interpreter_binary_sha256':None,
  'DT_NEEDED_resolution':'UNKNOWN_NOT_PERFORMED','transitive_dynamic_closure_verified':False,'ldd_executed':False}

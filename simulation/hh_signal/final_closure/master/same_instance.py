"""Inert same-FD reader implementation; no block-device/privileged consumer.

The real administrator helper is intentionally absent. Ordinary-file fixtures
exercise FD identity, no path reopening during consume, and one-shot leases.
They do not establish host writer/hotplug exclusion or a format/mount ability.
"""
import os,stat,threading
from pathlib import Path
from .contract import need,no_links,sha

class InertFDLease:
 _active=set();_mutex=threading.Lock()
 def __init__(self,path,expected_sha256,*,offline_fixture_only=False):
  need(offline_fixture_only is True,'REAL_DEVICE_HELPER_NOT_DEPLOYED')
  path=no_links(Path(path));need(path.is_file() and path.stat().st_size<=65536,'INERT_REGULAR_FILE_REQUIRED')
  self.fd=None;self.key=None;self.used=False
  fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0))
  try:
   s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=65536,'NONREGULAR_OR_SHARED_FD')
   key=(s.st_dev,s.st_ino)
   with self._mutex:
    need(key not in self._active,'CONFLICTING_INERT_LEASE');self._active.add(key)
   self.key=key;self.fd=fd;self.identity=(s.st_dev,s.st_ino,s.st_size);self.expected=expected_sha256
   need(sha(self.consume())==expected_sha256,'INERT_INPUT_HASH')
   self.used=False;os.lseek(fd,0,os.SEEK_SET)
  except BaseException:
   if self.key is not None:
    with self._mutex:self._active.discard(self.key)
   os.close(fd);self.fd=None;raise
 def consume(self):
  need(self.fd is not None and not self.used,'CLOSED_OR_ALREADY_CONSUMED_FD')
  s=os.fstat(self.fd);need((s.st_dev,s.st_ino,s.st_size)==self.identity,'PINNED_INSTANCE_CHANGED')
  raw=os.read(self.fd,65537);need(len(raw)==s.st_size and sha(raw)==self.expected,'FD_CONTENT_CHANGED')
  self.used=True;return raw
 def close(self):
  if self.fd is not None:
   os.close(self.fd);self.fd=None
   with self._mutex:self._active.discard(self.key)
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
def privileged_operation(*args,**kwargs):
 raise PermissionError('NO_PRIVILEGED_ADAPTER_NO_AUTHORIZATION; SAME_FD_INERT_READER_ONLY')

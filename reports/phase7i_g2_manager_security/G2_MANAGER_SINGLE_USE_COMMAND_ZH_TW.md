# 單次命令候選：BLOCKED，現在不可執行

Exact source `c80244e69b840eb3984ba9bda1b2f64546556124`，bootstrap SHA `1e7e52cea1aa2096fb9ffb0dd98086032b703d07cecf0fa88f77bd2e4901a57e`。以下僅說明最終cold-start contract；真正scope/manifest/approval digest均未產生，原樣先STOP，不讀native檔案。native檔案位置只是規劃，尚未建立；不能用Windows checkout代替。

```bash
/usr/bin/python3 -I -S -B - <<'PY'
import hashlib,os,stat,sys
MANIFEST_SHA256 = None
SCOPE_SHA256 = None
APPROVAL_RECORD_SHA256 = None
if any(v is None for v in (MANIFEST_SHA256,SCOPE_SHA256,APPROVAL_RECORD_SHA256)):
    raise SystemExit("BLOCKED_PENDING_NATIVE_STORAGE_DEPENDENCIES_AND_APPROVAL")
bootstrap = '/home/btu/simulations/hh_final_closure/g2_manager_source_private_01/manager_scope_bootstrap.py'
expected = '1e7e52cea1aa2096fb9ffb0dd98086032b703d07cecf0fa88f77bd2e4901a57e'
fd=os.open(bootstrap,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
try:
    before=os.fstat(fd)
    if not stat.S_ISREG(before.st_mode) or before.st_uid!=1000 or before.st_nlink!=1 or stat.S_IMODE(before.st_mode)!=0o400 or not 0<before.st_size<=131072:
        raise SystemExit('BLOCKED_BOOTSTRAP_INSTANCE')
    raw=bytearray()
    while True:
        block=os.read(fd,min(65536,131073-len(raw)))
        if not block:break
        raw.extend(block)
        if len(raw)>131072:raise SystemExit('BLOCKED_BOOTSTRAP_BOUND')
    after=os.fstat(fd)
    if any(getattr(before,k)!=getattr(after,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')) or hashlib.sha256(raw).hexdigest()!=expected:
        raise SystemExit('BLOCKED_BOOTSTRAP_SHA_OR_DRIFT')
    root='/home/btu/simulations/hh_final_closure/g2_manager_scope_private_01/'
    sys.argv=['manager_scope_bootstrap.py','--manifest',root+'runtime_manifest.json','--scope',root+'scope.json','--approval',root+'approval.json','--manifest-sha256',MANIFEST_SHA256,'--scope-sha256',SCOPE_SHA256,'--approval-sha256',APPROVAL_RECORD_SHA256]
    exec(compile(bytes(raw),bootstrap,'exec',dont_inherit=True),{'__name__':'__main__','__file__':bootstrap,'EXTERNAL_BOOTSTRAP_SHA256':expected})
finally:
    os.close(fd)
PY
```

獨立審核完成後，完整人工命令須以/usr/bin/python3 -I -S -B啟動外部已審inline loader；它用O_NOFOLLOW與fstat驗已審native bootstrap，bounded same-FD hash等於上述值，將EXTERNAL_BOOTSTRAP_SHA256放入同次compile namespace，exec同一份bytes。再傳--manifest/--scope/--approval與三個original-byte SHA；沒有裸path import或sys.path插入。bootstrap固定10-file closure並在任何manager dispatch之前再次驗native Store與same-instance證據。

本修訂的動態解析provider尚未實作，因此即使補三個hash也仍BLOCKED_DEPENDENCY_CLOSURE。不能以本文件作execution-ready命令或新human authorization；不得執行舊PR45 command，亦不得重跑version-only。後續provider改動要另審新exact revision。

"""Bounded review artifacts. Source-only labels never assert a deployed filesystem."""
from . import manager_scope_contract as c
STORAGE={'schema':'HH_G2_SCOPE_STORAGE_POLICY_REVIEW_V1','source_status':'PASS_SCOPE_STORAGE_SOURCE_ONLY','actual_storage_identity':None,'actual_scope_created':False,'required_classification':'LINUX_NATIVE_FILESYSTEM_CONFIRMED','accepted_fs_type':'ext4','expected_fs_identity':None,'expected_mount_identity':None,'expected_directory_identity':None,'scope_mode':0o600,'directory_mode':0o700,'source_mode':0o400,'owner_uid':1000,'scope_bytes':131072,'no_symlink_ancestors':True,'no_writable_ancestors':True,'posix_access_or_default_acl':'REJECT_NONEMPTY; UNKNOWN_ON_UNSUPPORTED','scope_nlink':1,'original_byte_hash':True,'same_fd_read':True,'pre_post_identity':True,'directory_fd_pinning':True,'source_code_from_verified_memory':True,'exclusive_create':True,'automatic_retry':False,'host_admin_excluded':False,'WORM_storage_claimed':False}
DEPENDENCIES={'schema':'HH_G2_DEPENDENCY_SOURCE_REVIEW_V1','status':'BLOCKED_DEPENDENCY_CLOSURE','actual_current_tools':None,'historical_tool_sha256':c.TOOLS,'historical_client_release':'255.4-1ubuntu8.18','observed_PT_INTERP':'/lib64/ld-linux-x86-64.so.2','actual_interpreter_hash':None,'actual_DT_NEEDED':None,'actual_transitive_libraries':None,'actual_stdlib_and_extension_hashes':None,'required_APIs':['pidfd_open','dir_fd','O_NOFOLLOW','fstat','fstatfs','getxattr','procfs','cgroup_v2','existing_manager_buses'],'current_machine_API_qualification':None,'fixed_allowlist_max_entries':128,'fixed_file_read_max_bytes':67108864,'filesystem_scan':False,'ldd_executed':False,'library_installation':False,'dynamic_resolution_or_plugin_mapping_attested':False,'dispatch_gate':'FAIL_CLOSED_EVEN_AFTER_ALLOWLIST_MATCH; A_REVIEWED_RESOLUTION_PROVIDER_IS_NOT_IMPLEMENTED_IN_THIS_REVISION','next_evidence_needed':'SEPARATELY_REVIEWED_FIXED_ELF_LOADER_DEPENDENCY_AND_IMPORT_ORIGIN_CAPTURE; NO_LIVE_CAPTURE_THIS_TASK'}
DOCS={
'G2_ORIGINAL_SCOPE_ACL_FINDING.md':'''# 原Scope與Source ACL根因

CURRENT_WINDOWS_SCOPE_ACL=FAIL；HISTORICAL_SCOPE_ACL_AT_EXECUTION_TIME=UNKNOWN。原SHA仍與正式wrapper receipt相符，VERSION_ONLY_RECEIPT_INTEGRITY_REVIEW=PASS_WITH_PROVENANCE_LIMITS。原source同樣要以本輪唯讀DACL觀測分類，不能從Git clean推為他人不可寫。

原因是原Windows資料目錄繼承廣泛DACL，Users可讀、Authenticated Users可Modify；名為private的資料夾、SHA正確及/mnt/c路徑不會自動建立0700/0600 Linux權限。先hash再讓普通Python loader按路徑重讀，仍可能讀到不同bytes。原history只記錄writer檢查及hash，不補造執行前ACL證據。

本修訂保留原scope、receipt、authorization、checkpoint與PR45不變。新Windows工程輸出目錄只保護自己的DACL，不更改舊目錄；這仍不是Linux-native staging驗收。未來scope/source採獨立原生儲存、原始檔FD與記憶體code binding，不把Windows工程checkout直接當正式import根。
''',
'G2_NATIVE_PRIVATE_SCOPE_IMPLEMENTATION.md':'''# Native scope實作與驗證界線

manager_scope_fs.py用完整ancestor dirfd鏈、O_DIRECTORY/O_NOFOLLOW與lstat/fstat身分核對，拒絕其他使用者可寫祖先。final私有dir需owner UID1000、0700；scope0600、source0400、regular file、nlink1。以fstatfs magic、proc fdinfo mount_id、精確mountinfo/device/fsid與mount namespace identity核對外部已審filesystem contract；只接受ext4。9p/DrvFS與unknown類型不會因path/chmod變成PASS。

getxattr在同FD讀access/default POSIX ACL；非空拒絕，unsupported/permission錯誤保持UNKNOWN。openat以固定單一basename開scope，bounded read在同FD計SHA；比對pre/post dev/inode/owner/mode/nlink/size/mtime/ctime及dirfd lookup，dispatch前再驗bytes。exclusive-create不覆寫；建立失敗保留檔案，不自行修chmod或重試。ordinary fsync不是WORM或power-loss證明。[open/openat](https://man7.org/linux/man-pages/man2/open.2.html)、[POSIX ACL](https://man7.org/linux/man-pages/man5/acl.5.html)。

本機沒有建立候選ext4 scope/source目錄，也沒有取得實際fsid/mount/namespace/dir inode；所有實測值null。Native CI只能證明它自己的普通fixture檔案行為，不是WSL部署。root、Windows host administrator、WSL控制面與同UID高權限侵入並未被排除。固定依賴／dynamic resolution仍BLOCKED，即使檔案allowlist相符也不能dispatch manager。
''',
'G2_SOURCE_IMPORT_TRUST_REVIEW.md':'''# Python import信任與修復

原Windows-backed checkout的DACL與hash-then-import間隙分開記錄；不移動或修改PR45。新版本只規劃10份最小source closure，原四份diagnostic檔逐SHA不改；新增guard、capsule bootstrap與獨立security validator。staging writer只向已驗native Store exclusive-create 0400檔案，不搬整個專案。

正式冷啟動必須先由外部已審的inline command在同FD讀bootstrap bytes、核exact SHA，再compile相同bytes；缺EXTERNAL_BOOTSTRAP_SHA256就在native讀取前BLOCKED。bootstrap固定closure名稱、逐FD hash並保留FD到結束，建立封閉private package；只exec已compile的approved bytes，不插checkout sys.path、不讀它的__init__或pyc，也不對missing capsule module退回一般PathFinder。原始與secure Store兩組FD還須是同一檔案實例。

python -I忽略PYTHON環境、user site及不安全的起始搜尋路徑；不會凍結檔案。-B只禁止寫pyc，不能阻止讀取既有stdlib cache。新-I -S -B提案另禁site；這是新source契約，不能繼承已消耗version批准。Python/root stdlib、extension、loader、libpython與動態插件仍是外部信任邊界；檔名來源或.py hash不等於已驗執行中的cache/DSO閉合。[Python3.12 options](https://docs.python.org/3.12/using/cmdline.html)。

目前native staging與runtime dependency proof均未取得。固定allowlist比對已實作，但child的完整動態解析provider尚未實作；capture額外fail-closed gate保持BLOCKED，不讓一個JSON status取代閉合。
''',
'G2_MANAGER_FIXED_QUERY_REVIEW.md':'''# 原三條Manager查詢

manager_scope_contract.fixed_argvs()/fixed_env()逐項回歸等於PR45 contract；無新增properties，固定user@1000.service，無remote bus、pager/password agent/root fallback，timeout只hash不執行。client255僅歷史self-report，system/user manager及effective service properties都尚未觀察。show的manager/既存unit property意圖保留，但不稱零control-plane成本。[systemctl v255](https://www.freedesktop.org/software/systemd/man/255/systemctl.html)。

原5s child、1s cleanup、30s adapter soft、8192-byte合併child output、32768 aggregate、131072 receipt、8層lineage、0700/0600、retry0不變。新增security envelope也受131072-byte bound；額外輸入證據是固定有界資料，並不是完整kernel CPU/RAM/wall envelope。原capture/validator不作正式entry，只有新冷啟動guard路徑可候選。

完整diagnostic含原before/after proc/namespace/cgroup snapshot，固定每層九介面各256 bytes，mountinfo65536 bytes；不掃描全機。root預期缺欄位、缺bus、partial、inactive user service都保留UNKNOWN。先確認source/tool/UID/GID、scope/approval bytes鏈與native FS，再談實機批准；現在沒有final launch manifest或human reference。
''',
'G2_BUS_AND_SESSION_REQUIREMENTS.md':'''# Bus與Session條件

既存system socket預期root owner，user systemd/private預期UID1000；需safe ancestors、型別、owner與前後一致性。不存在時UNKNOWN_USER_MANAGER_BUS，不能start/enable/linger或daemon-reload。原WSL user-session warning沒有被client version成功清除。

所審v255 user-private連線失敗可能轉default user bus；封閉DBUS_SESSION_BUS_ADDRESS指向無效FD路徑的既有規則保留。這是source-family推論，不是對Ubuntu binary patch/library的attestation。[bus-util v255](https://raw.githubusercontent.com/systemd/systemd/v255/src/shared/bus-util.c)。

本輪沒有讀live sockets、bus、proc或cgroup。將來只可使用使用者既有非root session；不能用wsl --exec建立新attachment替代未驗證的原session。無合法直接session能力時交付人工命令，仍需scope/source/dependencies先通過。不是在本輪啟動WSL、登入或修復服務。
''',
'G2_MANAGER_AUTHORIZATION_REQUEST_ZH_TW.md':'''# 下一次Manager獨立批准：目前BLOCKED草案

Version-only批准已消耗；禁止重用其reference或retrospective record。新的批准必須在新exact source、原三argv/env、10-file closure、native scope/source storage與runtime manifest完整核對後，綁新的pending canonical scope SHA。record provenance只可USER_PROVIDED_VERBATIM_APPROVAL_REPORTED；沒有原message ID/簽章就不捏造身分認證。

目前沒有scope/source實際FS identity，也沒有child動態解析closure provider，不能直接批准後執行。下一步應先另審最小native資料staging/identity與runtime closure採集範圍；本任務不授權建立Linux目錄或採集。若provider需要新source，必須再次exact-source review，不能用外部JSON旗標繞過現有BLOCKED。

未來單次診斷提案只含固定manager三查詢與原snapshot、必要private attempt/receipt；5s/1s/30s soft及所有bytes/lineage上限不變。不接受B-V2、不准service/cgroup/device寫入、quota、mount/format、install、WSL啟動/重啟、sudo、kernel stress、S4、BUILD或physics。失敗保留證據，不換output/retry。
'''}
def command(revision,bootstrap_sha):
 return '''# 單次命令候選：BLOCKED，現在不可執行

Exact source `'''+revision+'''`，bootstrap SHA `'''+bootstrap_sha+'''`。以下僅說明最終cold-start contract；真正scope/manifest/approval digest均未產生，原樣先STOP，不讀native檔案。native檔案位置只是規劃，尚未建立；不能用Windows checkout代替。

```bash
/usr/bin/python3 -I -S -B - <<'PY'
import hashlib,os,stat,sys
MANIFEST_SHA256 = None
SCOPE_SHA256 = None
APPROVAL_RECORD_SHA256 = None
if any(v is None for v in (MANIFEST_SHA256,SCOPE_SHA256,APPROVAL_RECORD_SHA256)):
    raise SystemExit("BLOCKED_PENDING_NATIVE_STORAGE_DEPENDENCIES_AND_APPROVAL")
bootstrap = '/home/btu/simulations/hh_final_closure/g2_manager_source_private_01/manager_scope_bootstrap.py'
expected = '''+repr(bootstrap_sha)+'''
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
'''

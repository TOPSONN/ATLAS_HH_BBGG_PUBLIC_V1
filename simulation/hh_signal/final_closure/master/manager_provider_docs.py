"""Review artifacts: source, CI and user-guest evidence have different levels."""
from . import manager_dependency_contract as c,manager_native_contract as nc
DOCS={
'G2_ELF_DEPENDENCY_PROVIDER_REPORT.md':'''# ELF provider source review

manager_elf.py parses original bounded bytes without executing them: ELF32 is recognized and explicitly unsupported; ELF64 LE x86-64 supports bounded program/section tables, PT_INTERP, PT_DYNAMIC, LOAD string-table address translation, DT_NEEDED/SONAME/RPATH/RUNPATH, null termination, alignment, overflow and corrupt/truncated input rejection. $ORIGIN is limited to an exact reviewed physical parent plus safe suffix; $LIB/$PLATFORM and parent escapes are rejected. Dynamic audit/filter/config tags are rejected rather than silently omitted. Unknown target formats remain UNKNOWN, not a successful closure.

manager_dependency_provider.graph builds a deterministic graph from an exact supplied file set and explicit reviewed edges. No filesystem search, ld.so.cache emulation or ldd execution. SONAME conflicts, duplicate/missing edges, unreferenced input and incorrect interpreter mapping fail. Cycles preserve edges and terminate. This is PASS_STATIC_ELF_GRAPH, not actual loader selection. The independent validator reparses the same original ELF blobs and compares the complete graph; genuine guest blobs were not acquired here. [ELF gABI dynamic linking](https://gabi.xinuos.com/elf/08-dynamic.html).
''',
'G2_DYNAMIC_RESOLUTION_LIMITATIONS.md':'''# Dynamic resolution limitations

COMPLETE_DYNAMIC_RESOLUTION_ATTESTED=false. Static DT_NEEDED edges and one process mapping snapshot cannot establish another future child's whole-lifetime resolution. dlopen, NSS/PAM/plugins, ld.so.cache, environment, hwcaps and conditional loading remain separate risks. The provider labels observed origins and mapping/device/inode checks independently. It never derives lifecycle attestation from a status string or turns the PR46 boolean true. [Linux loader search semantics](https://man7.org/linux/man-pages/man8/ld.so.8.html).

No process-lifecycle observer with adequate scope/permissions has been approved or implemented. Scope A observes the collector itself only. The V2 Manager gate validates available raw native evidence chains and still refuses execution. A future lifecycle mechanism and exact source revision require separate review and authorization; there is no current execution-ready Manager command. A and B do not grant C, B-V2, G3–G7, S4 or physics.
''',
'G2_NATIVE_EXT4_POSITIVE_VALIDATION.md':'''# Native ext4 positive validation levels

PR46's four skipped positive fixtures remain historical SKIP. New CI fixtures qualify only three fixed candidate parents (runner home, RUNNER_TEMP, /mnt), using the unchanged no-ACL/no-writable-ancestor policy before creating an owned temporary directory. No chmod/setfacl/sudo/mount/install. If all parents fail, the result remains BLOCKED_NO_QUALIFIED_CI_EXT4_PARENT. A missing capability is not converted into PASS. Pure tests cover partial/zero/interrupted writes, replacement, mount identity, ACL and source races; they do not prove ext4.

Only a real successful CI ext4 Store creation can earn PASS_CI_NATIVE_POSITIVE / PASS_ACTUAL_NATIVE_STORAGE_FIXTURE. CI also reads the existing root-owned /usr/bin/true ELF and reviewed /bin alias without executing that target; those are CI ELF/alias evidence, not user WSL storage. Final CI logs determine actual results, separately from this local stage.

User WSL identity/source/scope staging remains null. A future separately approved Scope B qualifies the fixed ext4 parent and exclusively creates a new 0700 directory, 0400 reviewed sources and 0600 pending scope/receipts. Its creation-time instance is an observation requiring independent review before Manager scope; it is not pre-attestation of an inode currently unknown. No user acceptance test is run here. Same UID, root/Windows administrator and WSL control-plane compromise remain outside the proven trust boundary.
''',
'G2_SOURCE_CAPSULE_V2_REVIEW.md':'''# Source capsule V2

Schema HH_G2_SOURCE_CAPSULE_V2 has exactly 13 files: the original four diagnostic sources plus nine native/provider modules. V1's 10-file contract and historical manifests/checkpoints are not edited or rebound. All 13 original-byte SHA values are bound to a fresh revision and pending A/B scopes. The original diagnostic four remain byte-identical.

The reviewed external inline entry reads/hash-checks its bootstrap from one FD, compiles those bytes, then pins and hashes every closure source once. Only those compiled bytes enter a private package. No project __init__, pyc, checkout sys.path insertion or missing-module fallback. Source can initially be read from the exact Windows-backed engineering path for separately approved B, but it is trusted as reviewed bytes, not native ACL attestation; A uses the newly staged native path. Missing approval/hash/revision stops first. No guest source staging occurs in this task.

-I -S -B restrict startup/search/site and pyc writing, not existing caches or DSO execution. Required Python startup imports are not claimed to be a complete IO sandbox. [Python options](https://docs.python.org/3.12/using/cmdline.html), [importlib](https://docs.python.org/3.12/library/importlib.html).
''',
'G2_NATIVE_READ_ONLY_COLLECTOR_REVIEW.md':'''# Collector and finite staging review

Scope A: exact enumerated targets only, no recursive scanning or target ELF invocation, no systemctl/ldd/timeout child, no network/service/cgroup/config writes. Hash and same-FD root ownership/mode/ACL/instance checks precede retaining file evidence. Aliases are pinned explicit hops; metadata-only unknown aliases are not followed. Missing/unbound paths and Python origins remain UNKNOWN. Socket lstat and safe ancestor checks do not connect or verify manager/bus semantics. The candidate receipt is exclusively preserved, then its pinned original bytes/SHA independently validated before checksum/success; invalid/partial evidence and failure markers stay private.

Limits: 64 target files, 16MiB/file, 64MiB aggregate inspected bytes, 128 non-capsule modules, 8 alias hops, 131072-byte receipt, 30s owned POSIX real-timer soft watchdog including writes. At most four A files / 143360 bytes are created (attempt, receipt, checksum, optional failure). The timer cannot promise interruption of uninterruptible kernel IO and is not a hard CPU/RAM/wall/disk envelope. Parent qualification, close/fsync failures and partial files are preserved; no retry/cleanup deletion or reuse of consumed approval. Source-only CI is not a whole-job resource qualification.

Scope B: separate bounded creation in the fixed destination, at most 18 files / 2MiB, source bytes at most 1MiB. It reads only the fixed Python executable for identity plus native-parent/proc metadata and reviewed source input bytes; it does not inspect A's whole file list. Own partial files remain on failure; operator review required. B's outputs are not Manager approval.
''',
'G2_COLLECTOR_STOP_RULES.md':'''# STOP rules

Stop before new guest metadata on missing/consumed/expired/wrong-operation approval, wrong source revision or input SHA, unsupported interpreter/UID, source closure drift, no external bootstrap hash, or source-root substitution. Reject unsafe/native-unknown storage, ACL support unknown/nonempty ACL, symlink/hardlink/instance changes, existing output, write with no progress, byte/module/time bound and independent validator failure. No retries, replacement output, chmod, elevation or root fallback. Preserve attempt/failure/partial evidence.

Unresolved optional fixed files or origins can be retained as explicitly UNKNOWN partial observations; they do not qualify Manager execution. Fixed required Python hash/interpreter or private output failure stops. A failed required systemctl SHA is an explicit unavailable/security-rejected observation and never a verified tool identity. A and B require separate new approvals; prior Version-only is consumed. Do not start WSL or create a session to run these commands.
''',
'G2_MANAGER_DISPATCH_GATE_AUDIT.md':'''# Manager gate audit

V1 loader/capture/contract/validator and original diagnostic four are preserved. V2 is a separate proposed schema. It checks original exact three argv/env, a new reference, raw independently reviewed B staging and A observation chains and provider contracts. A status=PASS flag cannot grant execution: complete dynamic-resolution lifecycle evidence is not implemented, so the final provider gate always fails closed. No live Manager launcher is introduced in this PR. Full future Manager approval-record semantics and a lifecycle-capable dispatch integration must be reviewed at another exact revision before C is executable.

Manager limits remain 5s child/1s cleanup/30s adapter soft; 8192 child/32768 aggregate/131072 receipt bytes, lineage8, retry0. A collector's own 30s timer is a different scope. System/user manager and future delegation are UNKNOWN. Architecture A remains A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST; B-V2 unaccepted, guest async filesystem/journal CPU not zero. FULL_LAUNCH_ENVELOPE_VERIFIED=false; no S4/build/physics.
''',
'G2_NEXT_USER_APPROVAL_REQUEST_ZH_TW.md':'''# 下一個獨立批准：B先建立必要私人輸出，再另審A

本文件是待核准提案，不是批准。所有human reference、最終scope SHA與approval SHA均null；不要重用Version-only。Source hash、來源revision、完整檔案清單及兩份pending scope見本交付。未另收到人類批准，任何使用者WSL操作都STOP。

Scope B（有限檔案建立，非純唯讀）：只在既有非root Ubuntu/Python3.12.3終端，資格核對/home/btu/simulations/hh_final_closure為安全ext4 parent後，新建g2_native_dependency_private_01（0700），寫入13個精確hash來源（0400）、pending_scope_A.json及stage attempt/receipt/checksum/必要failure（0600）；上限18檔/2MiB、source最多1MiB，exclusive-create、不得覆寫。讀取固定Python binary核SHA與自己的proc/mount資料；不執行target ELF、systemctl、sudo、服務或磁碟設定。Parent instance是當次觀測，並非已在本輪取得事前attestation。若不符合原policy，不建立目錄、不換路徑重試。若部分失敗，保留檔案交由使用者另審清理。

Scope A（唯讀觀察，另有明列的私人收據建立例外）：B完成並獨立驗證後，另批准固定56個target檔案、四個alias metadata介面、自己的proc/mapping/session與兩個既有socket metadata；無Manager query。最多64檔、每檔16MiB、aggregate64MiB inspected bytes、128 modules、8 hops；receipt131072 bytes，最多4新檔/143360 bytes、30s soft timer、retry0。不要求所有未知file先猜hash；已知Python/systemctl SHA必須匹配。新library/Python origin身分只是觀察，不是完整runtime attestation。Python啟動及stdlib/extension載入是明示的外部信任邊界，沒有宣稱全面檔案或network kernel sandbox。

Scope C（未來Manager）：只有所需A/B證據、固定runtime manifest與足夠lifecycle機制都經過新exact-source審查後，才另行提出。A/B均不批准C、B-V2條款、G3–G7、裝置、quota/format/mount、S4、BUILD_ONLY或任何HH物理運算。目前C仍不可執行。此輪保存checkpoint並停止，沒有自行製造批准文字或收據。
'''}
def command(revision,hashes):
 text='# 單次候選命令：待獨立批准，原樣必定STOP\n\nExact source `'+revision+'`；V2 closure13檔。先B有限建立，實際收據獨立審查後再另批A。兩者不含Manager。以下最終scope/approval hash留null，沒有自動生成或接受批准。\n\n'
 for suffix,operation in (('B','NATIVE_STAGE_ONCE'),('A','NATIVE_READ_ONLY_ONCE')):
  root='/mnt/c/HH/.local/phase7i_g2_native_dependency_v1/source/simulation/hh_signal/final_closure/master' if suffix=='B' else nc.DEST
  text+='## Scope '+suffix+' — '+operation+'\n\n```bash\n/usr/bin/python3 -I -S -B - <<\'PY\'\nimport hashlib,json,os,stat\nSCOPE_SHA256 = None\nAPPROVAL_RECORD_SHA256 = None\nif SCOPE_SHA256 is None or APPROVAL_RECORD_SHA256 is None:\n    raise SystemExit("STOP_PENDING_NEW_INDEPENDENT_APPROVAL")\nROOT = '+repr(root)+'\nENTRY_SHA256 = '+repr(hashes['manager_capsule_v2.py'])+'\nREVISION = '+repr(revision)+'\nheld=[]\ndef read_exact(path,expected):\n    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC); held.append(fd)\n    a=os.fstat(fd)\n    if not stat.S_ISREG(a.st_mode) or a.st_nlink!=1 or not 0<a.st_size<=131072:raise ValueError("INPUT_INSTANCE")\n    raw=bytearray()\n    while True:\n        b=os.read(fd,min(65536,131073-len(raw)))\n        if not b:break\n        raw.extend(b)\n        if len(raw)>131072:raise ValueError("INPUT_BOUND")\n    z=os.fstat(fd)\n    if any(getattr(a,k)!=getattr(z,k) for k in ("st_dev","st_ino","st_size","st_mtime_ns","st_ctime_ns","st_mode","st_nlink")) or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("INPUT_SHA_OR_INSTANCE_DRIFT")\n    return bytes(raw)\ntry:\n    entry=read_exact(ROOT+"/manager_capsule_v2.py",ENTRY_SHA256)\n    scope=read_exact("/mnt/c/HH/.local/phase7i_g2_native_dependency_v1/private/final_scope_'+suffix+'.json",SCOPE_SHA256)\n    approval=read_exact("/mnt/c/HH/.local/phase7i_g2_native_dependency_v1/private/approval_'+suffix+'.json",APPROVAL_RECORD_SHA256)\n    space={"__name__":"reviewed_native_entry","EXTERNAL_ENTRY_SHA256":ENTRY_SHA256,"EXTERNAL_SOURCE_REVISION":REVISION}\n    exec(compile(entry,ROOT+"/manager_capsule_v2.py","exec",dont_inherit=True),space)\n    print(json.dumps(space["launch"](ROOT,scope,approval,SCOPE_SHA256,APPROVAL_RECORD_SHA256)))\nexcept (OSError,ValueError,KeyError,TypeError):\n    raise SystemExit("BLOCKED_NATIVE_EVIDENCE; PRESERVE_PRIVATE_ATTEMPT; NO_RETRY")\nfinally:\n    for fd in held:os.close(fd)\nPY\n```\n\n'
 return text+'不是目前可執行的授權命令；必須另核對具新reference的final scope原bytes/SHA與批准紀錄，不能手補旗標當批准。不得啟動WSL替代既有終端；B partial留存、A bounded failures留存，不自動清理或重跑。所有soft watchdog與外部信任界線見collector review。\n'
def artifacts(stage,context,hashes):
 rev=context['revision'];i=int(stage[1:3]);out={}
 if i==2:out['G2_NATIVE_STORAGE_ATTESTATION_PLAN.json']={'source_status':'PASS_SOURCE_ONLY','actual_user_ext4_identity':None,'actual_source_staged':None,'actual_scope_staged':None,'no_ACL_policy_change':True,'write_progress_guard':True,'fd_lookup_mount_comparison':True,'statfs_ABI':'LINUX_X86_64_LP64_SIZE120; CI_CPP_OFFSETS_REVIEW','host_trust_boundary':'UNKNOWN_HOST_TRUST_BOUNDARY'}
 if i==3:out['G2_NATIVE_EXT4_POSITIVE_VALIDATION.md']=DOCS['G2_NATIVE_EXT4_POSITIVE_VALIDATION.md']
 if i==4:out['G2_ELF_DEPENDENCY_PROVIDER_REPORT.md']=DOCS['G2_ELF_DEPENDENCY_PROVIDER_REPORT.md']
 if i==6:out['G2_ELF_TRANSITIVE_GRAPH_CONTRACT.json']={'source_revision':rev,'schema':'G2_REVIEWED_STATIC_GRAPH_CONTRACT_V1','maximum_nodes':c.MAX_FILES,'maximum_edges':c.MAX_EDGES,'original_ELF_bytes_required_for_recompute':True,'resolution':'EXACT_REVIEWED_EDGES; NO_CACHE_SEARCH_OR_TARGET_EXECUTION','cycles':'PRESERVE_EDGES_AND_BOUND_VISITED_SET','actual_guest_graph':None,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
 if i==7:out['G2_PYTHON_RUNTIME_IMPORT_CONTRACT.json']={'schema':'PYTHON_RUNTIME_IMPORT_CONTRACT_REVIEW_V1','evidence_schema':'PYTHON_RUNTIME_IMPORT_EVIDENCE_V1','target_version':[3,12,3],'classes':['BUILTIN','FROZEN','SOURCE','BYTECODE','EXTENSION','UNKNOWN'],'required_fields':['name','origin_class','origin','sha256','file_identity','cached_path','execution_bytes_attested'],'maximum_modules':128,'source_hash_implies_executed_cache_identity':False,'actual_user_imports':None}
 if i==8:out['G2_DYNAMIC_RESOLUTION_LIMITATIONS.md']=DOCS['G2_DYNAMIC_RESOLUTION_LIMITATIONS.md']
 if i==9:
  out['G2_NATIVE_READ_ONLY_COLLECTOR_REVIEW.md']=DOCS['G2_NATIVE_READ_ONLY_COLLECTOR_REVIEW.md'];out['G2_RUNTIME_DEPENDENCY_EVIDENCE_SCOPE.json']={'status':'PENDING_MINIMAL_NATIVE_READ_ONLY_SCOPE_AND_SEPARATE_FINITE_STAGE','exact_source':rev,'scope_A':nc.pending(rev,hashes,'NATIVE_READ_ONLY_ONCE'),'scope_B':nc.pending(rev,hashes,'NATIVE_STAGE_ONCE'),'pending_manager_runtime_manifest':c.pending_runtime_manifest(rev,hashes),'scope_C_authorized':False,'actual_guest_data':None}
 if i==10:out['G2_SOURCE_CAPSULE_V2_REVIEW.md']=DOCS['G2_SOURCE_CAPSULE_V2_REVIEW.md']
 if i==11:out['G2_INDEPENDENT_EVIDENCE_VALIDATOR_RESULTS.json']={'status':'PASS_VALIDATOR_SYNTHETIC_SOURCE_FIXTURES_ONLY','actual_guest_receipt':None,'fixture_verdict':'PASS_TEST_FIXTURE_ONLY','fixture_cannot_pass_actual_mode':True,'independent':'SEPARATE_PARSER_AND_RAW_HASH_CHAIN; SAME_AGENT_NOT_SECOND_HUMAN','COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
 if i==13:out['G2_MANAGER_DISPATCH_GATE_AUDIT.md']=DOCS['G2_MANAGER_DISPATCH_GATE_AUDIT.md']
 if i==14:
  out['G2_COLLECTOR_SINGLE_USE_COMMAND_ZH_TW.md']=command(rev,hashes)
  for name in ('G2_COLLECTOR_STOP_RULES.md','G2_NEXT_USER_APPROVAL_REQUEST_ZH_TW.md'):out[name]=DOCS[name]
 return out

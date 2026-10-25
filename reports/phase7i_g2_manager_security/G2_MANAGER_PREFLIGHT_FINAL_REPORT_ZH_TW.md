# G2 Manager Scope安全修補與部署前審查

**本輪結論：PASS_SCOPE_STORAGE_SOURCE_ONLY；BLOCKED_DEPENDENCY_CLOSURE_AND_NATIVE_DEPLOYMENT。** 本輪沒有重跑已消耗的version-only，沒有manager查詢、WSL啟動／attachment、sudo、service/cgroup/device變更、kernel stress、S4、BUILD或物理計算。真正manager批准套件尚未就緒，不應直接請使用者批准後執行。

## 歷史正式收據與ACL

原正式receipt SHA256 `a5a114a7099b0ddf9c8a0c9735501986e1e77b250d615705ac0211b830e090cc`、原scope SHA256 `41723b055e30886c3b32ead6d838c4ecae7b4ea1a2aafba4ca747f1192ca3a6f`在新worker中以原bytes重新獨立驗證。實際歷史child為1、exit0、stdout330/stderr0、retry0、cleanup VERIFIED_GROUP_ABSENT；client self-report是255.4-1ubuntu8.18，沒有system/user manager狀態。原批准reference `0e76645d07be2eb646f2cc44163b8a34db3f3ad38cfe07c42105845df37e2e02`與retrospective record SHA256 `09c7e3b9b4380d0dd40fdea6a618f997180925ae0b1ab7b3f0d7b0cc0902ca62`不同；保留真實歷史，不重綁或覆寫。批准來源仍是USER_PROVIDED_VERBATIM_APPROVAL_REPORTED，不是身分密碼學認證。

原scope與source目前的Windows DACL都含廣泛繼承存取，scope為FAIL；執行當下ACL為UNKNOWN。Git clean或SHA相符不能證明當時存取控制。新工程目錄只保護新檔的DACL；不修寫舊scope、PR45 checkout或歷史ACL，也不將新Windows目錄稱為native ext4 staging。

## 實質Source修補

新增Linux-native Store：完整ancestor dirfd、O_NOFOLLOW/openat、fstatfs與fdinfo/mountinfo身分、同FD POSIX ACL、owner/mode/nlink及pre/post instance/bytes驗證；exclusive-create、bounded read、fsync、拒絕replace/hardlink/DrvFS/unknown或不安全ACL。scope0600、dir0700、source0400。非空ACL一律拒絕是保守政策，不對unknown作PASS。這些檢查尚未在使用者WSL native目錄實測；實際mount/fsid/inode均null。root／Windows administrator／WSL控制面與同UID入侵仍在外部信任邊界。

新增外部same-FD bootstrap與10-file frozen-memory capsule，compile並import相同已審bytes，不透過checkout sys.path重讀；缺外部bootstrap SHA先停止。原diagnostic四份bytes不改，未來只有新guard entry可候選。-I/-S/-B限制搜尋與site/pyc寫入，並不凍結stdlib cache或DSO。完整API與信任限制見SOURCE_IMPORT_TRUST及DEPENDENCY報告。

固定allowlist核對不等於child動態解析閉合。目前沒有loader、direct/transitive libraries、stdlib/native extensions與實際解析的受審實機身分；dynamic-resolution provider也尚未實作。capture明確要求該條件並fail-closed：即使補上allowlist與批准，這個revision仍不能dispatch。不得透過JSON status/flag或synthetic fixture繞過。下一個provider實作必須另做exact-source review。

原三條systemctl argv/env、user@1000.service properties與5s child／1s cleanup／30s adapter soft watchdog、8192 child／32768 aggregate／131072 receipt bytes、8層lineage及retry0不變。closed bus fallback保留；本輪未讀live bus/session，也未清除歷史user-session warning。這些不是完整kernel hard resource envelope。

## 真正執行的測試及失敗保存

本機首個candidate：239項，232 PASS、7 POSIX skip。最後source新增CI祖先ACL分類正反案例後，focused28項為23 PASS、5 POSIX skip。Linux CI重跑612/612 offline與81/81 safe legacy；affected240為235 PASS、5 SKIP，其中4項native正向檔案案例因真實runner祖先ACL被拒絕而SKIP，另1項為Windows-only。新增真實ancestor rejection案例PASS只證明拒絕，不能當正向native storage證據。Windows CI179為171 PASS、8 SKIP。集合重疊，不相加。C++20固定inert arithmetic 5例通過，不是HH build。

首次Linux CI原239測試有4個ACL setup error；原失敗logs與run完整保留。修正僅將已核實的環境阻擋標成SKIP，增加明確拒絕測試，不更改runtime ACL政策、不改ACL、不將SKIP當PASS。初次safe CLI因缺少預備progress目錄在run建立前exit1也保存；只建立新Windows工程checkpoint目錄後，以新exact source開始fresh run，沒有重試已啟動child。

新source/input run實際完成13個source-only child、26個append-only ledger events。status、verify、resume-safe實際exit0，resume前後26→26，重複child0。ledger僅ordinary files/fsync，沒有kernel容量或power-loss保證。舊completed run不重綁。獨立驗證指獨立receipt parser及同agent分開AST/semantic worker/process，不冒稱第二位人類或host attestation。

## 尚未解除的關卡與下一步

| 類別 | 目前結果 | 必要下一步 |
|---|---|---|
| PASS | scope/source FD、frozen import、negative/replay/partial validators與safe checkpoint的source工程 | 審查PR46與exact source |
| FAIL | 原Windows scope/source目前DACL；首次CI native setup失敗 | 保留歷史，不能retrofit成PASS |
| BLOCKED | 使用者native scope/source實例與正向native fixture | 另審最小native identity/staging範圍，未批准前不建立或採集 |
| BLOCKED | 動態解析provider未實作；loader/libraries/stdlib/extensions未驗 | 先準備固定有界證據採集方案與provider source，另審exact revision |
| BLOCKED | 新Manager批准不存在 | 前述通過後才發出新的單次scope/source/hash批准請求 |
| UNKNOWN | system/user manager、bus/session、未來delegation與job enforcement | 需要日後明確核准的真實OS收據 |

目前command文件是有確切source/bootstrap SHA、但三個必要digest為null而先STOP的cold-start候選，**不是可執行命令**。不要手補值、不執行舊PR45 command、不重跑version。B-V2三份條款未接受；Architecture A仍A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST，guest async journal/filesystem CPU不默認0，G3–G7/S4/build/physical gates均未解除。

附件B1–B8字串只有57hex，不能作SHA256；實際既存64hex檔身分保留，見PRESERVATION。1019 frozen inputs中1018 scientific bytes完全相同；唯一frozen例外為精確CI routing，非物理source變更。原四份diagnostic、physics contract、guard與歷史資料均逐SHA核對。PR45保持原HEAD及Draft，PR46 stacked Draft，不merge/rebase/force-push。公開輸出不含raw receipt/scope/approval、私人ACL帳號、boot/topology、binary/events或PDF/PNG。

下面DELIVERY_REVISION使用containing-commit語義，避免commit自含SHA的循環；最終exact delivery SHA與其CI在PR HEAD及本機final_delivery.json另外記錄。公開報告內CI為source commit的已完成快照，不冒稱尚未建立的report commit CI。

## 必填驗收欄位

- **PROJECT**: ATLAS_HH_BBGG_PUBLIC_V1

- **TASK**: PHASE7I_G2_MANAGER_SCOPE_SECURITY_AND_DEPLOYMENT_PREFLIGHT_V1

- **BASE_PR**: 45

- **BASE_HEAD**: 0edd24ed6cfba314e8f3632a0e61bd6265b7dbfa

- **EXECUTED_SOURCE_REVISION**: c80244e69b840eb3984ba9bda1b2f64546556124

- **HISTORICAL_VERSION_EXECUTABLE_SOURCE**: 55777dd8a21964dd87c7294550bd51cef73e5fa8

- **DELIVERY_REVISION**: CONTAINING_REPORT_COMMIT; exact SHA is external PR HEAD/local final delivery receipt to avoid a self-referential commit hash

- **PULL_REQUEST_URL**: https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/46

- **VERSION_ONLY_ACTUAL_RECEIPT_VERIFIED**: true

- **VERSION_APPROVAL_CONSUMED**: true

- **ORIGINAL_SCOPE_CURRENT_ACL**: FAIL

- **ORIGINAL_SCOPE_EXECUTION_TIME_ACL**: UNKNOWN

- **NEW_SCOPE_STORAGE_SECURITY**: PASS_SCOPE_STORAGE_SOURCE_ONLY; ACTUAL_NATIVE_DEPLOYMENT_BLOCKED

- **NEW_SCOPE_ACTUALLY_CREATED**: false

- **NEW_SOURCE_STAGING_SECURITY**: SOURCE_ONLY_PINNED_BYTES_CAPSULE; ACTUAL_STAGING_NOT_CREATED

- **DEPENDENCY_CLOSURE_STATUS**: BLOCKED_DEPENDENCY_CLOSURE; DYNAMIC_RESOLUTION_PROVIDER_NOT_IMPLEMENTED

- **SYSTEMD_CLIENT_VERSION**: HISTORICAL_CLIENT_SELF_REPORT_255.4-1ubuntu8.18; REAL_RECEIPT_REVALIDATED

- **SYSTEM_MANAGER_STATE**: null

- **USER_MANAGER_STATE**: null

- **CGROUP_DELEGATION**: UNKNOWN_FUTURE_DELEGATION

- **MANAGER_DIAGNOSTIC_AUTHORIZED**: false

- **MANAGER_DIAGNOSTIC_EXECUTED**: false

- **G2_ARCHITECTURE_A**: A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST

- **G2_ARCHITECTURE_B_V2_ACCEPTED**: false

- **G3_COLLECTOR_DEPLOYED**: false

- **G4_DEVICE_READY**: false

- **G5_FORMAT_EXECUTED**: false

- **G6_READBACK**: null

- **G7_MOUNT_EXECUTED**: false

- **S4_EXECUTED**: false

- **FULL_LAUNCH_ENVELOPE_VERIFIED**: false

- **FORMAL_BUILD_ONLY_AUTHORIZED**: false

- **PHYSICAL_RESTART_AUTHORIZED**: false

- **NEW_ME_CALLS**: 0

- **NEW_INTEGRALS**: 0

- **NEW_EVENTS**: 0

- **ACTUAL_NEW_NATIVE_STORAGE_IDENTITY**: null

- **ACTUAL_NEW_NATIVE_SOURCE_INSTANCE**: null

- **ACTUAL_CURRENT_TOOL_HASHES**: null

- **ACTUAL_DYNAMIC_DEPENDENCY_IDENTITY**: null

- **ACTUAL_MANAGER_RECEIPT**: null

- **ACTUAL_JOB_CPU_RAM_WALL_DISK**: null

- **TEST_RESULTS**: {"local_candidate_affected":"239 RUN / 232 PASS / 7 SKIP","final_local_focused":"28 RUN / 23 PASS / 5 POSIX SKIP","Linux_CI":"612/612 offline, 81/81 safe legacy, 240 affected / 235 PASS / 5 SKIP","Windows_CI":"179 affected / 171 PASS / 8 SKIP","CXX20_inert_arithmetic":"5 CI CASES PASS; NO_PHYSICS_BUILD","safe_DAG":"13 SOURCE_ONLY CHILDREN; 26 APPEND_ONLY EVENTS; RESUME NO_CHILD_REPEAT","native_positive_fixture":"4 BLOCKED_CI_ANCESTOR_ACL SKIPS, not PASS"}

- **CI_RESULTS**: {"source":"c80244e69b840eb3984ba9bda1b2f64546556124","status":"SUCCESS_WITH_NATIVE_POSITIVE_FIXTURE_LIMITS","run":40177965897,"url":"https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/40177965897","jobs":[{"job":121122664892,"platform":"ubuntu-24.04","status":"success","offline":612,"offline_skipped":0,"safe_legacy":81,"legacy_skipped":0,"affected":240,"affected_pass":235,"affected_skipped":5,"actual_ancestor_acl_rejection":"PASS_NEGATIVE_ONLY","native_positive_fixture":"BLOCKED_CI_ANCESTOR_ACL; FOUR_SKIPS","cpp_inert_arithmetic_cases":5},{"job":121122665105,"platform":"windows-2025","status":"success","affected":179,"affected_pass":171,"affected_skipped":8}],"independent_user_WSL_OS_acceptance":null,"suites_overlap_not_additive":true,"original_failed_run":40177600277,"original_failed_source":"dac78384fa09ea294ec526e7193224ba9bb60929","original_failure_preserved":true,"decoded_log_sha256":{"121122664892":"2481a9db5737566da78976368b8396cc6966a54f7a3e136de367ba729c29ff75","121122665105":"7ab2461b48fad1cf59aece10b6dbe6528c3eeba43193574ddeed1fc1080e88b7"}}

- **HISTORICAL_PRESERVATION**: PASS_BYTE_IDENTITY; HISTORICAL_ACL_FAIL_AND_FAILURES_PRESERVED

- **PUBLICATION_AUDIT**: ALL_INTERMEDIATE_COMMITS_AND_FULL_CHANGED_INDEX_CHECKED_BEFORE_EACH_REF_UPDATE; FINAL_SNAPSHOT_EXTERNAL

- **NEXT_USER_ACTION**: Review source-only PR46 and BLOCKED runtime prerequisites; do not run pending command or repeat version query

- **NEXT_EXACT_APPROVAL_REQUIRED**: First separately review minimal native-storage identity/staging and fixed runtime dependency evidence scope. Implement and review any dynamic-resolution provider revision before seeking manager execution approval. No currently executable approval packet.

- **GATES_PASS**: ["EXACT_PR45_ANCESTRY","ORIGINAL_VERSION_RECEIPT_REVALIDATED_NO_REEXECUTION","ORIGINAL_FOUR_DIAGNOSTIC_HASHES_UNCHANGED","PINNED_SCOPE_SOURCE_AND_EXCLUSIVE_CREATE_SOURCE","COLD_START_VERIFIED_BYTES_CAPSULE","FIXED_THREE_ARGV_ENV_AND_SOFT_LIMITS_UNCHANGED","INDEPENDENT_RECEIPT_SOURCE_FIXTURES","SOURCE_CI_WITH_EXPLICIT_NATIVE_LIMITS","FRESH_EXACT_SOURCE_INPUT_DAG_AND_NO_REPEAT_RESUME","HISTORICAL_AND_PUBLICATION_GUARDS"]

- **GATES_FAIL**: ["CURRENT_HISTORICAL_WINDOWS_SCOPE_AND_SOURCE_DACL_FAIL","INITIAL_LINUX_NATIVE_FIXTURE_SETUP_FAILED_ACL_POLICY_AS_RECORDED"]

- **GATES_BLOCKED**: ["ACTUAL_NATIVE_FS_MOUNT_ACL_PARENT_IDENTITIES_NOT_ACQUIRED","FOUR_NATIVE_POSITIVE_FIXTURES_BLOCKED_BY_CI_ANCESTOR_ACL","DYNAMIC_RESOLUTION_PROVIDER_NOT_IMPLEMENTED","CURRENT_LOADER_LIBRARIES_STDLIB_EXTENSIONS_UNKNOWN","NEW_MANAGER_SCOPE_APPROVAL_ABSENT"]

- **GATES_UNKNOWN**: ["HISTORICAL_EXECUTION_TIME_ACL","CURRENT_SYSTEM_USER_MANAGER_AND_BUS_SESSION","FUTURE_DELEGATION","WHOLE_JOB_KERNEL_ENFORCEMENT_AND_PERSISTENT_CAPACITY"]

- **FINAL_VERDICT**: PASS_SCOPE_STORAGE_SOURCE_ONLY; BLOCKED_DEPENDENCY_CLOSURE_AND_NATIVE_DEPLOYMENT

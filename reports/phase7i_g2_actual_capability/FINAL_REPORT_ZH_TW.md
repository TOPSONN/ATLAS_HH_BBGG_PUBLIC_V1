# G2 真實能力與執行架構工程交付

完成的是有實質source修補的安全工程與決策套件；**沒有完成實機資源封裝或物理restart**。Base PR42 `6126b315834715983481802f35630742accf1d88`；exact executed source `f2be12fd487c66d877e0362d6a5922cafc8ac369`；新[Draft PR43](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/43)。Fresh safe run `d39682c2-2f08-4ac6-a162-d8bb44d5cb65`。Delivery commit尚未建立時不可能自引用其SHA，本報告保留publication前快照；完整交付SHA及最終CI由PR metadata、交付訊息與本機DELIVERY_REPORT_ZH_TW.md補上。

## 實質成果

1. 既有raw hash與13/13 host coverage保留，不重採。2層Guest lineage的10個root缺介面由Linux6.6 non-root flags/API解釋，不當作deployment failure。shell UNLIMITED不等於新job不能設定限制。
2. 新版g2_protocol實作一個parent總CPU/RAM/wall的pure驗證、PID/start/UID/source/config/slot綁定、collector退出後獨立observer、no-internal-process hierarchy及resident allocation arithmetic。修正舊raw reader空direct PID但children活著的語義缺口；舊runtime及收據不改，新協定仍需真正protected acquirer/manager。
3. stop state machine先TERM/KILL worker/controller域，collector仍在同pool作限時postmortem後退出，最後外部observer確認。沒有source函數可啟動service或發出signal；全部只是經測試的請求與一致性檢查。
4. BUILD tmpfs full ceilings2.25GiB已比RAM多256MiB，未計runtime；明確拒絕全滿載宣稱。S4 ext4 4MiB/1KiB/128inode/1MiB journal核心幾何與e2fsprogs1.47.0 source相容，未mkfs，配置/features/free-space/durability仍未驗證。
5. A缺joint host/guest/VMM成本與強停止證據。B-V2＋VM＋observer僅建議逐條審查，8組具名阻擋與額外guest async kernel CPU歸屬缺口均明列，不將external成本記0或偷偷加排除角色。三份條款全不改、全未接受。

## 真實執行與驗證範圍

12個安全child實際exit0，24筆append-only ledger；status/verify/resume-safe實際exit0，resume沒有重跑child。新G2 profile重用Master的lock/child/bounds；只為G2 schema增加host＋guest external hash及scope identity，legacy ledger的byte projection一致。每child仍120s soft timeout與65536-byte retained-log界線，這不是OS CPU/RAM/disk硬封裝。

本機final affected164/164；新trace具名45個synthetic負例與套件重疊，不加總成獨立測試數。C++20沿用原checked arithmetic程式，8個實際正反案例，只是inert integer computation，binary留local。Source Ubuntu CI每輪612/612 offline、81/81 safe legacy、affected163通過1Windows-only skip；Windows103/103含26個in-memory CIM案例。actual decoded job logs已讀，沒有physics imports、kernel service、human approval construction。report-only delivery CI須待其commit建立後另查，不借用舊source checks。

獨立驗證為同agent的另一stage process＋不同整數/observer oracle subset、AST及diff審查，沒有虛構第二位人類或完整第二kernel實作。初版mock fixture漏external path導致3個source-test errors，已補inert metadata並保留原candidate及failure history；沒有真實kernel失敗或自動重試live操作。

## 科學與資料保存

1711個base檔1706逐byte不變；existing改動僅3個CI branch routing、精確history exception與G2 ledger metadata。physics contract `a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`、corrected guard `404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123`、cards/weights/events/ROOT provenance全保留；1019 frozen inputs中1018原科學/data exact，唯一差異是既有精確CI例外。原run84個檔的aggregate SHA `37eab3240a1ba8551f971e56031e852bf22fd6737c5790df370aec067924d241` 不變，沒有重綁。

source preflight沒有發現新physics-card/guard錯誤；確認目前active builder/reader source已接入Route-A corrected guard，不沿用較早metadata的NOT_MIGRATED斷言。B100與C1000實際PDF/running分開，C/D不重標成CTEQ6L1；STOP92歷史失敗predicate仍UNKNOWN。沒有啟動ROOT、MG5、ME、integration、Pythia或Delphes，沒有新截面推論。真正corrected binary/dependencies、native PDF/alpha/seed/grid/error/tail/writer及zero-retention還是未來物理關卡。

## 最小決策與下一步

先讀G2_B1_TO_B8_DECISIONS_ZH_TW.md、G2_MINIMUM_DECISION_REQUIRED.md及G2_PATH_A_VS_B_COMPARISON.md。若維持A，須先提供能證成原保證的平台；若考慮B，逐條審其較弱語義與未閉合成本。附件terms literal只有57字元，完整原件SHA為`c01968bda61e705c25cca774372572ad8b5efb221451db21ba33c21b77682193`，不可用短literal作批准binding。

下一個候選scope可以是單次唯讀effective manager/delegation/tool身份診斷，僅補決策資訊，不先要求接受B；未經另審不執行，binary identity尚缺時不稱execution-ready。之後device/provision/format/mount、kernel正常故障、S4、BUILD_ONLY、binary review與physical restart各自獨立授權。本任務沒有sudo、WSL/UNC啟動存取、cgroup/quota修改、服務操作、磁碟操作或kernel stress。

發布只含16個source/CI檔與42份有界sanitized文件，raw、boot IDs、serial/WWN、private host paths、events、binary、PDF/PNG排除。每個intermediate commit及完整index均須實際audit後才能push；舊PR維持Draft，不merge/rebase/force-push。所有實機kernel measurement=null，所有release旗標false。

## 必要最終欄位（publication前快照）

- **PROJECT**: ATLAS_HH_BBGG_PUBLIC_V1
- **TASK**: PHASE7I_G2_ACTUAL_CAPABILITY_AND_EXECUTION_ARCHITECTURE_V1
- **BASE_PR**: 42
- **BASE_REVISION**: 6126b315834715983481802f35630742accf1d88
- **EXECUTED_SOURCE_REVISION**: f2be12fd487c66d877e0362d6a5922cafc8ac369
- **DELIVERY_COMMIT**: PENDING_CONTAINING_REPORT_COMMIT_CREATION
- **PULL_REQUEST_URL**: https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/43
- **G1_HOST_COVERAGE**: 13/13 REPORTED_UNATTESTED; 4 disk-partition, 1 partition-logical edges
- **G1_GUEST_VALIDATION**: PASS_READ_ONLY_OBSERVED_REUSED_IMMUTABLE_EVIDENCE
- **G1_COUNTER_COVERAGE**: 2 lineages; nonroot missing0; root10 expected upstream nonroot-only interfaces
- **G1_CURRENT_FRESHNESS**: UNKNOWN
- **G1_MANAGER_STATE**: UNKNOWN
- **G2_A_FEASIBILITY**: A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST
- **G2_B_V2_RECOMMENDATION**: REVIEW_CONDITIONALLY; ASYNC_GUEST_KERNEL_COST_OWNERSHIP_STILL_UNRESOLVED
- **G2_B1_TO_B8_DECISIONS**: {"B1_BOUNDARY":"NOT_ACCEPTED","B2_CPU":"NOT_ACCEPTED","B3_WALL":"NOT_ACCEPTED","B4_RAM":"NOT_ACCEPTED","B5_DISK":"NOT_ACCEPTED","B6_EVIDENCE":"NOT_ACCEPTED","B7_CLEANUP":"NOT_ACCEPTED","B8_RELEASE":"NOT_ACCEPTED"}
- **G2_VM_COST_ASSIGNMENT**: {"sha256":"eedc17a761f2aaefde628d858a70bf9d4518d271df8bedcaf54f34d96cf6237d","status":"PROPOSED_NOT_ACCEPTED"}
- **G2_POST_EXIT_OBSERVER**: {"sha256":"fcbfba8c4dececd545b4f75a852a7ec4b123d67078a038d03d85772c5076364b","status":"PROPOSED_NOT_ACCEPTED"}
- **G2_USER_ACCEPTED**: false
- **G2_CPU_CONTROL_CAPABILITY**: DOCUMENTED_RATE_AND_ACCOUNTING; SOURCE_CUMULATIVE_PROTOCOL_TESTED; NEW_JOB_EFFECTIVE_ENFORCEMENT_UNKNOWN
- **G2_MEMORY_CONTROL_CAPABILITY**: DOCUMENTED_HIERARCHICAL_MEMORY_MAX; NO_ZERO_TRANSIENT_OVERSHOOT_GUARANTEE; NOT_DEPLOYED
- **G2_SWAP_ZERO_CAPABILITY**: DOCUMENTED_MEMORY_SWAP_MAX_0; CURRENT_SHELL_UNLIMITED; NEW_JOB_EFFECTIVE_CONFIG_UNKNOWN
- **G2_WALL_CONTROL_CAPABILITY**: SOURCE_LIFECYCLE_STOP_PROTOCOL_TESTED; NO_REALTIME_BOUND_OR_ACTUAL_JOB_VERIFICATION
- **G2_HOST_GUEST_COST_ACCOUNTING**: NO_JOINT_A_ENFORCER; B_EXTERNAL_COSTS_NONZERO_UNKNOWN; ASYNC_KERNEL_COST_GAP
- **G2_RECOMMENDED_PATH**: B_V2_VM_OBSERVER_CANDIDATE_REVIEW_ONLY
- **G3_SOURCE_CHANGES**: ["VERSIONED_IDENTITY_BOUND_TRACE_AND_FINAL_OBSERVER","HIERARCHICAL_PARENT_DIRECT_PID_FIX","CHECKED_CPU_RAM_WALL_AND_RESIDENT_MODEL","WORKER_DOMAIN_STOP_COLLECTOR_DRAIN_OBSERVER_STATE_MACHINE","REUSED_MASTER_ENGINE_WITH_NEW_EXTERNAL_SCOPE_LEDGER_METADATA"]
- **G3_REAL_ENFORCEMENT_DEPLOYED**: false
- **G3_NEGATIVE_TESTS**: 45 named SYNTHETIC cases plus aggregate unit tests; overlapping coverage
- **G3_OBSERVER_SOURCE_READY**: PURE_PROTOCOL_READY; PROTECTED_NATIVE_ACQUIRER_NOT_IMPLEMENTED
- **G3_OBSERVER_ACTUALLY_DEPLOYED**: false
- **G4_DISPOSABLE_DEVICE_AVAILABLE**: UNKNOWN_NO_QUALIFIED_CANDIDATE
- **G4_PROVISIONING_EXECUTED**: false
- **G5_FORMAT_EXECUTED**: false
- **G6_REAL_FILESYSTEM_READBACK**: false
- **G7_MOUNT_EXECUTED**: false
- **G7_COLLECTOR_DEPLOYED**: false
- **G7_READY_FOR_S4**: false
- **SCIENTIFIC_PREFLIGHT**: PASS_FROZEN_SOURCE_ONLY; NO_NEW_CARD_OR_GUARD_SOURCE_PROBLEM_IDENTIFIED; NATIVE_RUNTIME_UNVERIFIED
- **FROZEN_INPUT_SHA256_STATUS**: 1019 checked; 1018 scientific/data exact, one exact CI-routing compatibility exception
- **OFFLINE_TEST_RESULTS**: Local affected164 PASS; Ubuntu612/612 offline,81/81 safe legacy; affected163PASS1Windows-onlySKIP
- **WINDOWS_TEST_RESULTS**: CI affected subset103/103 including26 in-memory CIM cases; no host recapture
- **GITHUB_CI**: {"source":"SUCCESS_DECODED_LOGS_REVIEWED","source_runs":[39717712217,39717767921],"delivery":"PENDING_UNTIL_COMMIT_EXISTS"}
- **PUBLICATION_AUDIT**: SOURCE16_PAYLOAD_PASS; FINAL_REPORT_INDEX_AND_INTERMEDIATES_REQUIRED_BEFORE_PUSH
- **S4_EXECUTED**: false
- **FULL_LAUNCH_ENVELOPE_VERIFIED**: false
- **FORMAL_BUILD_ONLY_AUTHORIZED**: false
- **PHYSICAL_RESTART_AUTHORIZED**: false
- **NEW_ME_CALLS**: 0
- **NEW_INTEGRALS**: 0
- **NEW_EVENTS**: 0
- **ACTUAL_KERNEL_CPU**: null
- **ACTUAL_KERNEL_RAM**: null
- **ACTUAL_KERNEL_WALL**: null
- **ACTUAL_KERNEL_DISK**: null
- **GATES_PASS**: ["EXACT_BASE_AND_IMMUTABLE_INPUTS","G2_G3_SOURCE_PROTOCOL_AND_NEGATIVES","12_REAL_SAFE_CHILDREN_EXIT0","24_APPEND_ONLY_EVENTS_NO_RESUME_RERUN","INDEPENDENT_INTEGER_ORACLE_SUBSET_AND_AST_PROCESS","INERT_CPP20_ARITHMETIC8","SCIENTIFIC_FROZEN_SOURCE_PREFLIGHT","SOURCE_CI"]
- **GATES_FAIL**: ["BUILD_TMPFS_FULL_2_25GiB_CANNOT_FIT_2GiB_PLUS_RUNTIME","ATTACHMENT_TERMS_SHA_LITERAL_HAS57_CHARACTERS"]
- **GATES_BLOCKED**: ["EXACT_ARCHITECTURE_TERMS_ACCEPTANCE","EFFECTIVE_MANAGER_AND_DELEGATION","INDEPENDENT_FIXED_DEVICE_PROVISION","HOST_GUEST_SAME_INSTANCE_EXCLUSIVITY","PROTECTED_COLLECTOR_AND_FINAL_OBSERVER","WHOLE_JOB_NORMAL_AND_FAILURE_KERNEL_TESTS","BOUNDED_CONTROL_PLANE_AND_LOG_COSTS","GUEST_ASYNC_KERNEL_COST_OWNERSHIP"]
- **GATES_UNKNOWN**: ["CURRENT_GUEST_FRESHNESS","EFFECTIVE_MANAGER_AND_USER_SESSION_WARNING","NEW_JOB_DELEGATION","QUALIFIED_DEVICE_AND_ALL_HOST_WRITERS","INSTALLED_MKE2FS_CONFIG_FEATURES","BUILD_RUNTIME_RESIDENT_ALLOCATION","POWER_LOSS_DURABILITY","ASYNC_KERNEL_COST_CHARGING"]
- **MINIMUM_USER_DECISION**: Review exact B1-B8/VM/observer meanings and unresolved async-kernel cost; no acceptance inferred. A separately gated single-use read-only diagnostic can collect missing decision facts.
- **NEXT_AUTHORIZED_ACTION**: Read decision package; verify existing safe checkpoint only. No new OS/device/kernel/physics action authorized.
- **NEXT_SAFE_RESUMABLE_ACTION**: At exact source f2be12fd487c66d877e0362d6a5922cafc8ac369, status/verify/resume-safe --run-id d39682c2-2f08-4ac6-a162-d8bb44d5cb65; new input/source requires fresh run.
- **FINAL_VERDICT**: PASS_SAFE_G2_G3_ENGINEERING_AND_DECISION_PACKAGE; BLOCKED_ACTUAL_OS_DEPLOYMENT

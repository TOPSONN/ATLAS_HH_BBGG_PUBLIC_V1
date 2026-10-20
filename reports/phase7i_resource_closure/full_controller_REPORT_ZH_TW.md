# Phase7I 完整 controller 與儲存限制執行驗收

**FINAL_VERDICT：BLOCKED_FULL_CONTROLLER_KERNEL_AND_STORAGE_ENFORCEMENT**

本輪有實際工程與一次核心執行，沒有通過完整資源驗收。新增單一 service controller 與 51 個離線測試；Main 內已實作八階段流程，但實際服務在 Pre 停止，Main 沒有執行。沒有把 flags 改成 true，沒有放寬設定或補跑替代案。

| 必要欄位 | 結果 |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE7I_FULL_CONTROLLER_AND_STORAGE_ENFORCEMENT_V1 |
| BASE_REVISION | PR32：66663557984fcc069de600e2af07e778a4ac30ff；GitHub 已即時確認 |
| NEW_SOURCE_REVISION | 實際執行來源：3c89de1e67def831e5aa69ce56bab427bfc28cbf |
| CONTROLLER_IMPLEMENTATION_STATUS | PARTIAL_IMPLEMENTED；八階段 Main 已實作，僅 mock 流程通過，實際 Main 未進入 |
| KERNEL_EFFECTIVE_LIMITS | UNKNOWN：沒有完整即時 attestation；不可引用 unit 卸載後的預設值 |
| AGGREGATE_CPU_SECONDS | null／UNKNOWN |
| AGGREGATE_WALL_SECONDS | null／UNKNOWN；journal 起始至失敗訊息跨度 0.179121s，範圍不足以作完整 wall 證明 |
| PEAK_RAM_BYTES | null／UNKNOWN |
| SWAP_BYTES | null／UNKNOWN；設定值為 0，未取得可獨立驗證的即時讀值 |
| ALLOCATED_DISK_BOUND | BLOCKED：persistent allocated block／inode hard boundary 未實作、未驗證 |
| RESOURCE_TESTS_EXECUTED | 1 次固定無壓力 service；0 次 stress、0/47 matrix、0 次替代重跑 |
| OFFLINE_REGRESSION | 最終 207/207 offline + 81/81 safe legacy；0 failure/error/skip |
| HISTORICAL_PRESERVATION | 前後兩次 SHA256 保存檢查 PASS；50,169 內容觀測、3,588,706,711 bytes、122 links；0 變更／錯誤／race |
| REAL_ME_CALLS | 0 |
| REAL_INTEGRALS | 0 |
| NEW_EVENTS | 0 |
| FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED | false |
| FULL_LAUNCH_ENVELOPE_VERIFIED | false |
| COMMIT_HASH | executable source 為 3c89de1…；交付 report commit 另見 PR head／本機 DELIVERY |
| PULL_REQUEST_URL | https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/33 （Draft，stacked on PR32） |

## 實際工程範圍

新增 `simulation/hh_signal/final_closure/resource_closure/full_controller.py`，SHA256：
`d32b570213873a8ed5a3765babc2d6b64c6fd6bb3fb50e83ed0e6066cfa9ab2f`。

Main 包含 pre-provisioning、完整 tracked source/Git preflight、Python／Git／已映射 shared objects hashing、inert child 建立與監控、無編譯準備、private tmpfs 收據、postflight、固定檔名 failure cleanup。child 必須在同一 aggregate cgroup 與 mount namespace。host 入口只 exec 固定 systemd activation；沒有 host business hashing／observer／結果計算。

Pre／StopPost 只作有界核心讀回，不共用 tmpfs；它們各自建立 namespace。StopPost 的控制程序可在同 service aggregate 下的 control subgroup。新診斷沒有 OpenFile，僅能測試其缺席；不能拿來驗證一般 OpenFile handoff。固定 unit 名只防同時存在，不是 persistent single-use 授權。

所有正式入口保持 fail-closed：舊 backend／worker／integration_runtime 與歷史 source 未更動；新 full-campaign 也無條件拒絕。沒有建立、輸入或重用人類授權。舊 47 案規格及 assessor bytes 完整保留。

## 唯一一次實測與停止原因

在獨立來源審查、207 offline、81 safe legacy 通過且 source 乾淨後，執行固定無壓力 diagnostic：

- `ExecStartPre` 輸出 `BLOCKED / UNACCOUNTED_WRITABLE_MOUNT`，程序 exit 2；activation exit 1。
- Main 未進入，inert child 未建立；完整八階段只在 mock 正反測試中驗證。
- `ExecStopPost` 有嘗試，但在 Python 啟動前以 `226/NAMESPACE` 失敗。journal 顯示 `/dev/mqueue: Operation not permitted`，並記錄 PrivateNetwork 設定未套用、PrivateIPC 設定失敗被忽略。
- 這些是同一 invocation 的失敗，沒有第二次 probe。已立即停止相依 stress／47 案，沒有改 flags、換 user、提高 CPU/RAM/disk 或 sudo／remount／安裝。
- Pre 在完整 attestation 輸出前拋錯，原始可寫 mount 清單沒有留下。因此清單為 UNKNOWN，不自行補造。前置 limit guards 在控制流程上應已走過，僅為來源推論，不能升格為獨立核心數據。
- 後續唯讀查詢確認 exact unit inactive/dead、MainPID=0、ControlPID=0；journal 指出的 exact cgroup 路徑已移除。這支持本次失敗服務的清理，沒有測得 controller-loss／orphan 壓力清理。
- unload 後讀到的 infinity／default／空 ControlGroup／unset MemoryPeak 都不是執行期間限制值，沒有用來判斷 WSL 全面不支援。

原始 stdout／stderr／journal／manager query 保存在本機；public execution JSON 提供原檔 SHA256 與移除 machine/host identifiers 的投影。原始失敗不改寫為 PASS。

## 儲存與時間界線

核准參數保持 CPU4s、wall13s、RAM512MiB、swap0、work8MiB、private1MiB、disk16MiB。未來正式提案 CPU/wall14400s、RAM2GiB、swap0、1 job/worker、5GiB、retained LHE0 均沒有擴大，也沒有正式執行授權。

新 service 的保守 timer 分配合計 11.5s，30% quota 加 period carry 的計算為 3.453 CPU s。這是設計界線，沒有等同完成 OS 實測；systemd timer 不提供 realtime 排程保證。RuntimeMax 不涵蓋所有 Pre／Stop 階段，per-process CPU 也不是 aggregate CPU。

獨立唯讀儲存檢查：共享 `/dev/sdd` ext4 mount flags 未顯示 user/group/project quota；實際 quota 啟用狀態仍 UNKNOWN。btu 無有效 capabilities，無可用 setquota／repquota／xfs_quota。FUSE device、fusermount 與部分 libraries 存在，但未找到已安裝可用的 fuse2fs／guestmount。不能宣稱 unprivileged bounded FS 絕對不可能；目前沒有實作、審查及驗證的 capacity backend。

FSIZE、固定 FDs、allocation filter、事後 st_blocks 或 IO rate 都未被當成 persistent allocated-capacity 的證明。sealed memfd 可作有限 volatile transport，仍不能替代持久 sink quota。systemd/journal 與本機 raw evidence 保存屬診斷控制面，沒有被算成已驗證的 16MiB persistent hard bound。

## 驗證分類

**PASS**：新 controller source 工程、獨立 source／storage review、最終 207 offline、81 safe legacy、來源 hash、前後歷史保存、guard `404dfd1f…4fba123`、physics contract `a8a093e2…1c937cb`、停止失敗測試並保留原始證據。Safe legacy audit：551 Git、5 fixed Python、1 fixed sleep，0 forbidden imports／HumanReview attempts；獨立結果審查另外實際完成 92 項收據／投影比對，全部通過。

**FAIL**：唯一 positive kernel diagnostic；Pre 可寫 mount guard；StopPost namespace setup。

**BLOCKED**：persistent capacity、完整 controller kernel 驗收、47 stress matrix、正式 BUILD_ONLY、zero-ME configuration、binary review、physical restart。

**UNKNOWN**：active 完整 kernel readback、CPU／wall／MemoryPeak／swap、Pre 實際可寫 mount inventory、完整 full-lifecycle 負面測試、under-load cleanup；STOP92 原因仍未完全確立。

離線 wrapper 曾有一次執行前的 SyntaxError，原始錯誤另存本機；只修正 wrapper，沒有測試或 service 在該錯誤中啟動。最後同一來源的 207/81 測試重跑均通過。

本輪沒有新 σ 或積分誤差。歷史 B/C/D、Stage A、binary、events、cards 與收據未變。

## 證據與 publication

- `full_controller_execution_01.json`：真實失敗與原檔 SHA256。
- `full_controller_source_review_final_02.json`：exact source 獨立來源審查。
- `full_controller_storage_review_01.json`：只讀 capability／capacity review。
- `full_controller_offline_final_02.json`、`full_controller_legacy_final_02.json`：最終 207／81 回歸。
- `full_controller_historical_after_01.json`：執行後歷史 SHA256。
- `full_controller_independent_result_final_03.json`：獨立結果解讀。

新的 full_publication 固定以 PR32 SHA 為 base，檢查 staged index 與每個 outgoing intermediate payload，保留原 131072 bytes/blob、2MiB aggregate cap。僅推 source、tests、bounded JSON/Markdown；未推 PDF／PNG、raw events、ROOT/LHE/HepMC、binary、cache 或 private configuration。PR24、PR32 的原 HEAD 與 Draft 狀態保留，沒有 merge／force push。

GitHub CI 已核對 source/evidence head d313f1d42a44dbd8841d8d01fa09935a14f93ccf：PR resource job 39386496525／118507475129 SUCCESS，push resource job 39386440153 SUCCESS；三個歷史 PR jobs 明確 SKIPPED。Job log 實際包含 207 offline、81 safe legacy 與 publication PASS；完整 receipt 見 full_controller_github_ci_01.json。最後 report-only head 的狀態另見 PR／本機 DELIVERY。新分支只執行固定安全 offline／legacy／publication；三個歷史 workflow 對 PR 與 manual dispatch 都排除此新分支，避免未授權 native／正向授權測試。CI 成功不能當 kernel 或物理驗收。

## NEXT_RECOMMENDED_STEP

先審查本次 namespace／writable-mount 失敗與診斷缺測，提出能保留失敗前 readback 的 exact source 修補；再審查可實際提供 persistent allocated blocks／inodes 上限的 dedicated quota 或固定容量檔案系統方案。任何新增 driver／mount／主機設定或替代 kernel attempt 均先提出精確範圍，不在本次失敗後自動重試。

在完整正例與固定負面矩陣真正通過前，下一關不是物理執行。之後仍須另審 exact source／scope／RAM／CPU／wall／disk／fresh output，才可申請四個 fresh native builds、八個 zero-ME preflights、四個 unsupervised-entry refusal tests；BINARY_REVIEW 與 PHYSICAL_RESTART 仍各須獨立授權。

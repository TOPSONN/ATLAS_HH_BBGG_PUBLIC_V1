# G1/G2 實際能力與執行路徑

結論：`G1_G2_PARTIAL_WITH_SPECIFIC_EXTERNAL_BLOCKERS`。

本輪已實跑非管理員 Windows acquisition，保留兩次原始收據與一次來源修正；最終 13 類觀測取得 2 類 `REPORTED_UNATTESTED`，11 類 `UNKNOWN`。沒有取得可選用的安全磁碟，也沒有確認 Ubuntu 是否正在執行。實際拒絕不能解讀成 WSL 已停止、硬體不存在，或必然需要管理員權限。

Architecture A 判定為 `A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST`。建議使用者審查 B-V2 的八項明示修約，並優先在一般使用者可存取的主機環境完成同一支唯讀 acquisition。B-V2 尚未接受；本輪沒有下達 distro/service 啟動或重啟命令，也沒有執行 S4、stress、build 或物理運算。

## 來源與實際觀測

基底為 PR37 `80f78fafa5fb835a35d9a58537360c1726cf2eea`，其既有 tested source 為 `e8709b27103dd0aa1fad1c7d06192ab1cf1d8d6e`。本輪確切來源及各檔 SHA256 記於 `source_manifest.json`；交付 commit 與 CI 結果以新 Draft PR 的實際 HEAD/checks 為準。

acquisition 由目前非管理員 PowerShell 實跑。原始資料只放本機受保護目錄，公開 `host_projection.json` 為 allowlist 投影。原始位元組 SHA256 與 canonical JSON SHA256 分別記錄，兩者不可互換。來源 hash 相符可以驗證所宣告的程式版本，不能獨自認證執行來源、主機身分或完整性。

| 資訊 | 實際介面／範圍 | 本輪結果／信任 |
|---|---|---|
| Windows／PowerShell runtime | 目前程序 API | REPORTED_UNATTESTED |
| 已安裝 WSL 版本 | 固定 System32 wsl.exe，簽章及 SHA 綁定，`--version` exit0 | REPORTED_UNATTESTED；不是目前 guest kernel |
| Running distributions | 同一 executable，`--list --running --quiet` | UNKNOWN；非零退出、E_ACCESSDENIED |
| OS memory | 固定 Win32_OperatingSystem CIM | UNKNOWN |
| Hypervisor | 固定 Win32_ComputerSystem CIM | UNKNOWN |
| Windows optional features | 固定 Win32_OptionalFeature CIM | UNKNOWN |
| Disk drives／partitions／logical disks | 三項固定 CIM 查詢 | UNKNOWN |
| Disk-partition／partition-volume links | 兩項固定 CIM association 類別 | UNKNOWN |
| Storage disks | 固定 MSFT_Disk CIM | UNKNOWN |
| 已註冊 distro backing | 目前使用者 Lxss registry | UNKNOWN／ACCESS_DENIED |

九項 CIM 均失敗；獨立審查只從私有收據確認「client 無法存取 CIM resource」，未找出拒絕位於工具安全邊界、broker、provider 或主機政策的哪一層。因此先請同一使用者在一般終端執行同一支受審 adapter，不能直接要求全面管理員權限或變更 DCOM/WMI ACL。

| Guest／儲存／控制項 | SOURCE_SUPPORTED | OS_AVAILABLE | DEPLOYED | KERNEL_VERIFIED |
|---|---|---|---|---|
| Guest acquisition adapter | 是；AST/compile 與來源審查 | UNKNOWN | 本輪未執行 | 否 |
| PID1、user manager、D-Bus、session | 有讀取計畫；bus 連線尚不包含於 adapter | UNKNOWN | UNKNOWN | 否 |
| cgroup delegation、cpu.stat、effective memory/swap | 有 bounded 檔案讀取計畫 | UNKNOWN | UNKNOWN | 否 |
| Guest kernel／mount namespace／findmnt | adapter 可記錄部分檔案；獨立 findmnt 未執行 | UNKNOWN | UNKNOWN | 否 |
| Host/guest 同時間裝置對應及 protected storage graph | 既有 policy 拒絕不完整資料 | UNKNOWN | 無安全 candidate | 否 |
| 真正 quota／capacity-backed store | 既有檢核來源保留 | UNKNOWN | UNKNOWN | 否 |
| 32KiB fixed evidence slots | 舊協定保留，未重設計 | UNKNOWN | UNKNOWN | 否 |
| Worker 無法修改 evidence／collector 跨 controller 死亡 | 既有要求保留；需實際 UID/FD/control 配置 | UNKNOWN | UNKNOWN | 否 |

本輪三個既有 device、mount、transaction 入口均在**不完整資訊**下拒絕，沒有補造磁碟節點使其通過。這是 fail-closed 解讀檢查，不是完成真實 topology attestation。沒有任何觀測升格為 `OBSERVED_TRUSTED_SOURCE`。

## G2 的實質選擇

A 要把 Windows/WSL launcher、VM/hypervisor、manager/log、backing、guest controller、worker、collector 全部納入一個可強制的總額。目前沒有證據證明本機具備這個共同執行邊界。額外新增 Python watchdog 或縮小 guest cgroup 都不能補足 host 成本和排程延遲。

| 角色／成本 | A 要求 | B-V2 待批准提案 | 本機證據 |
|---|---|---|---|
| Worker、compiler、helper descendants | 共用 aggregate CPU/RAM/wall/disk | 維持共用，1 scientific worker | effective controls UNKNOWN |
| Trusted controller | 須計入至 cleanup 完成 | 計入同一 parent；不能另開未計帳 supervisor | UNKNOWN |
| Protected collector | 須計入，獨立保存死亡證據 | 計入同一 parent、不同 worker/controller death domain | UID/FD isolation 未部署 |
| Launcher | 納入總額 | 三個具名 external roles 之一；成本非零 | 未共同計帳 |
| Host manager／journals | 納入總額 | external infrastructure；仍揭露容量／故障風險 | 路徑、轉送及限制 UNKNOWN |
| Host backing management | 納入總額 | 三個具名 external roles 之一，不能聲稱零成本 | backing／thin／snapshot UNKNOWN |
| VM／hypervisor 的 CPU/RAM runtime overhead | 納入總額 | 尚未明確分配至既有三角色；BLOCKED，不自動排除、不新增第四角色 | overhead 與歸屬 UNKNOWN |
| Postmortem 與 cleanup | 納入完整 CPU、activation-to-cleanup wall | 保留總額驗收；缺失或超額拒絕 | 尚無 kernel 證據 |

CPUQuota／cpu.max 限制頻寬，並非累積 lifetime CPU hard cap。Windows Job 的累積時間欄位是定期檢查的 user-mode 時間；不能據此宣稱 Windows+guest user/kernel 全部受到同一總額限制。Linux memory.max 允許部分暫時超額；一般 systemd timer 不提供零延遲硬即時停止。因此 A 的零瞬時超調／無限精度停止保證在此平台**不可證明**。這是目前可證性結論，不是所有獨立主機都不可能。

參考：[Linux cgroup v2](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd resource control](https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html)、[Windows Job time limit](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information)。

`.wslconfig` 是 WSL VM 的整體設定，不能提供本研究工作的完整 host+guest 專屬總額。更動會影響其他 WSL 使用者／distributions，這裡沒有執行。參考：[Microsoft WSL configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)。

| 保留的 nominal budget | S4 | 未來 BUILD |
|---|---:|---:|
| 累積 CPU | 4 s | 14400 s |
| 完整 wall | 13 s | 14400 s |
| RAM | 512 MiB | 2 GiB |
| Swap | 0 | 0 |
| 所有新工作 disk | 16 MiB | 5 GiB |
| Jobs／scientific workers | 1／1 | 1／1 |

B-V2 除了外部角色範圍，還必須**分別**取得 CPU 監測及驗收、wall 非即時語意、RAM 標準 kernel 語意的同意。數字相同不代表保證相同。完整逐條提案見 `B_V2_AMENDMENT_ZH_TW.md`，八條全為 NOT_ACCEPTED。即使未來獲准，B 的結果也不能改名成原 A 的 FULL PASS。

B1 目前還缺 VM／hypervisor runtime overhead 的明確角色歸屬；不能將 host_backing management 自動解讀成所有 VM CPU/RAM。接受前必須補定義及新 exact clause hash、獨立審查，再由人類決策。此缺口不影響 R1 唯讀取得能力，但會阻擋 B 的部署與最終接受。

## Durable evidence 與實體容量

沒有找到已驗證的專用 capacity-backed protected store。本機 acquisition 的檔案 ACL、Flush/fsync/reopen 只能證明當次可讀回；它不是硬容量限制、worker 身分隔離、filesystem crash consistency 或 power-loss survival 的證明。

舊 32KiB slots 不變；未來需在工作前配置 blocks/inodes、同步並讀回，保護 worker 無法 unlink/truncate/punch-hole/rename，collector 必須在 unit/cgroup 卸載前保存 raw CPU/memory/events/membership 與 unit/InvocationID、PID/starttime、boot/cgroup 身分。Collector 自己或 host 消失時，只能保留之前已 commit 的 checkpoint，其後狀態 UNKNOWN；不得合成成功或終止證據。

現有 S4 work8MiB+private1MiB+persistent 候選4MiB=13MiB，剩餘3MiB只是算術。BUILD tmpfs maxima2.25GiB+persistent 候選2GiB=4.25GiB，剩餘768MiB也不是 metadata/journal/failure reserve 的強制證據。2.25GiB tmpfs maxima 不能宣稱在 RAM2GiB、swap0 加上 controller/collector 下可同時用滿。

Persistent 方案仍須符合舊 P1：真正獨立可拋棄 whole-device、完整 host/guest mapping、與 root／歷史 backing 不重疊。不能改用 C: 小 VHD、loop、shared-root partition 或 ordinary tempfile 當作通過。尚無安全實際 device identity，所以沒有可負責任執行的格式化／mount 命令。具體外部資源與檢驗要求見 `ADMIN_REQUESTS_ZH_TW.md`。

systemd user service 的 LogNamespace 支援有限；journal rotation/rate/size 設定也不等於所有 forwarded syslog、active files、manager 與 filesystem allocated blocks/inodes 的總硬限制。參考：[systemd.exec](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)、[journald.conf](https://www.freedesktop.org/software/systemd/man/255/journald.conf.html)。

## 真正剩餘關卡

| 狀態 | 精確 blocker | 責任／下一動作 |
|---|---|---|
| PASS | 固定來源、bounded 原始資料、去識別投影、缺資訊拒絕、獨立解讀 | 收據與 hash 已保存 |
| UNKNOWN | WSL running/session、CIM/storage/backing 的讀取權限來源 | 同一使用者一般終端執行受審唯讀命令；不提升 |
| BLOCKED | Guest controls／user-manager health、同 epoch/namespace 裝置對應 | 確認已啟動後才進既有 guest shell；否則獨立診斷啟動批准 |
| BLOCKED | 原 A 完整共同 hard aggregate | 選擇不同可控制平台，或逐條審核 B-V2；不再以 source gate 宣稱可部署 |
| BLOCKED | P1-safe 獨立實體容量與 collector 隔離 | 提供真實 disposable whole-device 及可用控制／隔離權限，後續 exact-target provisioning 另批 |
| BLOCKED | B-V2 未接受 | 使用者逐條決策；同意修約也不等於執行授權 |
| BLOCKED | 正反 kernel evidence、完整 CPU/wall/cleanup、持久 failure reserve | 先完成上面條件，再審 exact source/config 與單次無害測試 |

最小下一步是 `EXECUTION_PATH_ZH_TW.md` 的一般使用者 Windows 唯讀 acquisition。未取得權限前不啟動 guest，也不改 WMI/DCOM、systemd、quota 或磁碟。報告不要求立即執行 S4 或任何物理程式。

本輪來源改動限新 acquisition/parser/publication/提案及四份 CI routing；舊 device_policy、instance_binding、evidence_slots、612 runner、81 runner、physics contract 與歷史資料不變。來源與歷史 SHA 保存證據見 `preservation.json`；實際測試及修正歷程見 `validation.json`、`failure_history.json`、`independent_review.json`。

`FULL_LAUNCH_ENVELOPE_VERIFIED=false`、`FORMAL_BUILD_ONLY_AUTHORIZED=false`、`S4_EXECUTION_AUTHORIZED=false`、`PHYSICS_EXECUTION_AUTHORIZED=false`。

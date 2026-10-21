# 最小下一個可執行範圍

先在**一般權限** PowerShell 查清相同使用者是否能讀 WSL/CIM。不要使用 Run as Administrator、ExecutionPolicy Bypass、額外 credentials，也不要啟動 distro。以下命令是下一個外部使用者唯讀步驟的精確套件；本輪已在工具程序執行過此來源，沒有自動再於另一安全 context 執行。

現有受保護輸出目錄由目前 Windows 使用者擁有、DACL 只有該使用者一條 FullControl 繼承規則；程式會重新驗證，不符合就拒絕。不應為了通過自行放寬 ACL。輸出為每次新 UUID 檔案，不覆寫舊失敗。這是本機證據檔案寫入，沒有修改 WSL／CIM／磁碟設定。

```powershell
pwsh -NoProfile -File 'C:\HH\.local\phase7i_g1_g2_feasibility_v1\source\simulation\hh_signal\final_closure\resource_closure\g1_windows_inventory.ps1' `
  -OutputDirectory 'C:\HH\.local\phase7i_g1_g2_feasibility_v1\private' `
  -ExpectedScriptSha256 '7be2def2a3e605914826195f5f330e913ac05d641999db59d8e1893ca51d1411' `
  -ExpectedWslExeSha256 'fcd08205b608b5c4831e0dcb1801dd274436cd2c8420815f18ae58a085891a18'
```

程式只允許簽章及固定 hash 的 System32 wsl.exe 兩個 argv：`--version` 和 `--list --running --quiet`。已安裝版本或 executable hash 變更即停止，不自動接受新 hash。每個 native stream 保留上限32768 bytes，query timeout4s，45s為查詢間 soft deadline，capture262144 bytes。CIM provider 的 allocation/return latency 並非 kernel 強制上限；這不是 FULL resource envelope。若 cleanup 無法確認，停止其後查詢並保留 UNKNOWN。

成功條件是 queries 真正 exit0、原始 bytes 完整、來源與時間可核對；仍為 REPORTED_UNATTESTED，不是 host attestation。若繼續 denied，不需要重跑，保留新 receipt 路徑／hash，由主機管理員辨識拒絕的安全層。**不要**貼原始 JSON、磁碟序號、拓撲、帳號識別或終端歷史到公開 PR。

去識別投影使用同一 checkout 的 CLI，`--capture` 換成程式實際輸出的新完整路徑，`--output` 必須是不存在的本機檔案：

```powershell
Set-Location 'C:\HH\.local\phase7i_g1_g2_feasibility_v1\source'
python -B -m simulation.hh_signal.final_closure.resource_closure.g1_acquisition --capture '<實際新收據完整路徑>' --output '..\host_projection_external_01.json'
```

這一行包含必須由真實收據填入的參數，不是可以原樣貼入的示範路徑；沒有替使用者猜測 UUID 或改寫舊 hash。Projection 也只表示來源自述一致，公開前仍須 publication gate 審核。

## 已在執行中的 guest

目前 running state UNKNOWN，因此本輪完全沒有進入 guest。若外部唯讀結果及同一 instance 的 terminal 證據確認 Ubuntu **已在執行**，下一個診斷可以在該現有 Linux shell 內進行；不從 Windows 呼叫 `wsl -d`、不經 UNC 試啟動，也不重建 session。

受審 guest adapter hash 為 `dc9240024052d2d1ab8fa76689e8bcce3281078026826271da7469f2fb6b881f`。它只讀固定 proc/sysfs/config／path metadata，不執行子程序、quota syscall、device-content read 或 IPC bus connect。它尚未實跑，也不取代獨立 findmnt、user-manager health、實際 quota enforcement 的檢查。

在已確認 instance 內，先提供同 source hash 的 guest 檔案路徑，及已存在、目前 UID 擁有的0700私有目錄。程式介面如下；兩個參數不得猜測或沿用另一 instance：

```bash
python3 -B /verified/path/g1_guest_inventory.py --output-directory /verified/private/directory --expected-script-sha256 dc9240024052d2d1ab8fa76689e8bcce3281078026826271da7469f2fb6b881f
```

這是待 real path/permission 綁定的介面，不是已批准／已實跑命令；若 distro 停止或狀態仍未知，先提出單獨 bounded diagnostic startup 範圍，不得自動啟動。完整 `findmnt`／manager／quota 讀取的最小請求見 ADMIN_REQUESTS；不以本 adapter 的 partial snapshot 宣告 G1 完成。

## 之後的部署順序

1. 同一時間與 namespace 完成 host/guest device graph、protected root/history mapping、manager/cgroup/log 能力；缺少即停。
2. 使用者選不同平台的 A，或逐條審核 B-V2。修約不是執行批准。
3. 管理員提供真實、獨立 disposable whole-device 及 collector/control 能力；舊 P1 policy 確認安全後，才產生 exact-target provisioning 命令和 rollback，另批執行。
4. 必要 source 實作：同一 parent CPU/wall collector/enforcer、獨立 manager fallback、UID/FD/storage isolation、卸載前 raw capture。保留舊 policy/slots；修改的 executable revision 需獨立審核。
5. 另行批准無害 normal／CPU／wall／OOM／controller-loss／block/inode ENOSPC／capture-retention kernel 正反測試。通過 B 也不等於原 A FULL。
6. 最後才準備 exact BUILD_ONLY 範圍、來源、資源、evidence 和人類單次授權；ME/integration/events 仍另審。

每個步驟都有具體能力或人類決策的停止點；不靠增加 source-only gate 推遲架構選擇。

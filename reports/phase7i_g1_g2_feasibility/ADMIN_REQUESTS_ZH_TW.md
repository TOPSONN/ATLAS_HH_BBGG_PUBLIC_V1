# 外部權限與管理員最小請求矩陣

目前沒有證據證明需要 administrator 才能讀上述資料；實際只證明目前工具程序被拒絕。先執行 EXECUTION_PATH 中**不提升**的相同 adapter，若仍拒絕才由主機擁有者辨識 broker/provider/安全政策。沒有授權 sudo、管理員 shell、修改 ACL、啟動 WSL 或任何 provisioning。

| 請求 | 誰／精確資源 | 成功檢查 | 失敗／rollback | A/B |
|---|---|---|---|---|
| R1 一般使用者 host acquisition | 目前帳號，一次固定來源 PS adapter；兩個 WSL state/version argv、九項 CIM、唯讀 Lxss | bounded bytes、exit、時間與 source hash；完整度獨立判讀 | denied/truncated/cleanup UNKNOWN即停；無系統設定可回復，保留收據 | 共用 |
| R2 狹義 host topology read | 僅 R1 仍 denied 時由管理員提供 named interface 的可核實 readback，原始敏感資料限本機 | Stable host IDs、root/history、完整 sibling/partition/backing/reference graph、觀測來源 | 不直接變更 WMI/DCOM ACL 或給 generic admin；缺值維持 UNKNOWN | 共用 |
| R3 既有 guest 診斷 | 已正面確認 running 的同一 Ubuntu instance、目前 UID、bounded protected output | PID1、boot/mount namespace、session/bus、delegation/effective files、storage/log 同一 snapshot | guest stopped/unknown 須獨立 diagnostic startup批准；不 restart、linger、daemon-reload | 共用 |
| R4 合約選擇 | 使用者逐條 B1–B8；或改用能證明 A 的其他平台；B1先補 VM/hypervisor runtime 成本歸屬 | 新定義需 exact clause hash 及獨立審查；不得把未分配成本自動排除，再記逐條接受／拒絕 | 拒絕保留 A 與歷史，沒有執行／設定要 rollback | G2 |
| R5 Provisioning 能力 | 管理員提供真正獨立 disposable fixed whole-device、protected collector 身分及同一 parent controls | 舊 P1-safe graph、精確 device/diskseq/mount 身分、allocated blocks/inodes/journal/reserve、worker 不可寫 evidence | 尚無真實 target，所以 format/mount/chown/unit 命令未準備，禁止猜 target | 接受後的 A 或 B |
| R6 Kernel 正反測試 | 另行 exact-source/config 單次授權；一個無害 child，完整 lifecycle及fault範圍 | raw kernel evidence、CPU/wall從 activation至cleanup、OOM/timeout/controller-loss、容量與證據保存 | 無自動 retry；任何 missing/超限/殘留即 FAIL或UNKNOWN，保留新 instance收據 | 部署後 |

R2 固定查詢已實作於 adapter：Win32_OperatingSystem、Win32_ComputerSystem、Win32_OptionalFeature、Win32_DiskDrive、Win32_DiskPartition、Win32_LogicalDisk、Win32_DiskDriveToDiskPartition、Win32_LogicalDiskToPartition、MSFT_Disk。每項固定 property、operation timeout 與保留筆數上限；受審 source 是精確命令定義，不允許替換為無界 Get-* dump。

若需虛擬 backing，管理員須先提供**已核實路徑**及已存在 Get-VHD 的唯讀 VhdType/Size/FileSize/BlockSize/DiskIdentifier/Attached/ParentPath readback，並說明 thin/sparse、snapshot chain、可增長性及 active references。不可安裝 module、猜 VHD 路徑、attach/detach，或把 logical size 當 outer allocated bytes。Serial/完整拓撲不能公開。

R3 還需一次有界、私有保存的下列獨立 readback：`systemctl --no-pager show --property=Version --property=SystemState` 與 `systemctl --user --no-pager show --property=Version --property=SystemState`；同一 namespace 的 findmnt/mountinfo、lsblk/by-id/diskseq、cgroup lineage/controllers/subtree_control/cpu.max/cpu.stat/memory.max/memory.peak/swap/events/pids；journald/rsyslog effective config 和實際 storage path。這些目前不是一套已執行或完成封裝的 adapter，執行前仍須固定argv、byte/time bounds與輸出權限；不允許直接無界輸出或 log bodies／environment。Quota state僅能另審非寫入 GETFMT/GETINFO；本輪沒有任何 quota syscall，更沒有啟用或配置 quota。

R5 的實體 store 必須明確標示 partition table、filesystem metadata、journal、allocated data、inodes、preallocated failure slots、outer backing 與 host logs 各在誰的計帳範圍。S4 3MiB／BUILD768MiB 的算術餘額不能冒充測得 reserve。若最低 filesystem overhead 不能容納 nominal budget，該方案應 BLOCKED；不能調高數字或只限制檔案長度。

成功測試至少包含：normal寫入與reopen、blocks耗盡、inodes耗盡、metadata/commit failure、worker/controller消失、collector消失後最後checkpoint、unit卸載前raw capture、owned descendants清空。Power-loss若未實測就標UNKNOWN。這些是**未授權的未來測試條件**，本輪沒有執行。

Provisioning rollback 只能作用於未來批准、已驗身分的新工作資源：先停止核實的新 writers、保存 checkpoints/raw receipts，再依獨立批准撤回該新配置。不能 lazy unmount、root remount、清除全域 journal、刪歷史、移除未知 device 或重置已停止的舊 attempt。

最小立即請求是 R1，不是 R5/R6。接受 R4 也不會自動授權 R5、R6、S4、BUILD_ONLY 或 physics。

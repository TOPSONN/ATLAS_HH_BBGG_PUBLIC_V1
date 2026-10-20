# RAM 明確審核補件

本文件接續 b45f0c31 的原報告；原始失敗、收據與歷史 source 不改寫。

使用者已在本次聊天明確核准：無害測試整組 RAM 512 MiB、swap 0；未來正式 BUILD_ONLY 提案整組 RAM 2 GiB、swap 0。此項只核准參數，沒有建立 HumanReview、正式 build、zero-ME、ME、integration 或 event 授權。原本 CPU／wall 各 14,400 秒、1 job／1 worker、額外磁碟 5 GiB 的正式上限不變。

兩份 profile 與 backend 固定常數只更新 RAM 審核來源／範圍；原數值和控制流程不變。完整 controller 尚未封裝，正式入口仍在 TTY／output／確認之前無條件拒絕。FULL_LAUNCH_ENVELOPE_VERIFIED=false。

## 單次非壓力環境探測

新增 service_probe.py 僅執行 /usr/bin/true。使用 fixture 的 CPU、RAM、swap、wall、tmpfs、唯讀和 namespace 設定；沒有 archive／mutex／TTY OpenFile，stdout／stderr 指向 null。沒有 worker／model／物理 imports、filter install 或壓力。其目的只確認這組 exact user-service 設定能否建立及執行 true，不是完整限額的實證。

來源先經獨立審查與離線負面測試，再 commit 成乾淨 exact revision。output 使用全新 namespace；只執行一次。任何失敗保留 unit 結果與工作目錄，停止相依測試；不降低隔離旗標、不換 user、不重跑替代案。診斷工具本身不宣稱完整 host controller 封裝。10 項 mock-only 探測測試包含失敗 kill 仍 stop、missing PID、空 cgroup 讀回不能當作已清空。

探測執行前的狀態是 PLANNED_NOT_EXECUTED。實際結果將另存有 source revision 與 SHA256 的 append-only numerical evidence；不能把本規劃文件當作成功收據。

## 仍然阻擋的設計關卡

完整 controller 的 provisioning、preflight/hash、observer、receipt/postflight 必須在同一 aggregate cgroup／namespace 內；不能用排除 controller CPU／RAM 的方式宣稱完整驗收。服務啟動控制面只應接受固定操作；未知／被殺的收據保留 UNKNOWN，不能由外部補成 PASS。

當前共享 ext4／4096-byte granule 沒有為此 job 建立且驗證 allocated block／inode 的硬 quota。RLIMIT_FSIZE、固定FD、seccomp與事後 st_blocks 是防護及方法證據，不是已證明 allocated disk 從未超限。cgroup IO rate 不是容量 quota。可靠選項須審查 job quota 或固定容量專用 filesystem，以及 tmpfs／來源副本／metadata 的總額；未授權 sudo、remount、安裝工具或修改原環境。

即使 true 探測成功，47 案仍未執行，完整 controller 與實際 RAM／CPU／disk 強制限制仍未驗證。之後仍須新的 source 修補、完整正反測試、exact revision 審查，才可另外提出 BUILD_ONLY。正式 binary review、PHYSICAL_RESTART、Phase7J/K/L 仍各有獨立物理關卡。

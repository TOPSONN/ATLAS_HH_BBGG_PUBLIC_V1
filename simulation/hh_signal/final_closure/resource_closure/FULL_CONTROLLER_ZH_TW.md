# Phase7I 完整 controller 工程補件

本版新增 `full_controller.py`：單一 outer user service 的 Main 執行暫存工作區配置、完整 tracked Git preflight、工具與已映射依賴 SHA256、inert child 的建立／監控、無編譯準備、暫存收據、postflight 與固定檔名清理。自訂 business 工作不在 host observer 中執行。

`ExecStartPre` 與 `ExecStopPost` 只進行有界的即時核心／namespace 讀回；它們各自有獨立 mount namespace，不能共用 Main 的 tmpfs 檔案，也不依賴 OpenFile 傳遞。StopPost 的 control subgroup 必須位於相同 aggregate service cgroup 下。Main 與 child 必須位於相同 aggregate cgroup、相同 mount namespace。這是新架構，沒有修改舊 PR32 worker 或 47 個 fixture 的語意。

CPU quota 是速率限制。設定一次 Pre 與 Main activation 各 1s、Main runtime 8s、三段保守 stop／post／kill 各 0.5s，timer 預算 11.5s；30% quota 加一個 period 的保守 carry 為 3.453 CPU s，小於 4s。systemd 不是 realtime 系統，排程延遲仍須由實測揭露，不能只憑此計算宣稱完整 wall cap。每程序 hard CPU 2s 也不等於整組累計上限。

RAM512MiB、swap0、work tmpfs8MiB／1024 inodes、private tmpfs1MiB／256 inodes 均由 service 設定並在存活時讀回。缺少 memory.peak 保留 null／UNKNOWN。服務只有兩個可寫 tmpfs；沒有 host 輸出路徑或 OpenFile。固定 host activation 只 exec systemd-run，沒有 preflight、hash、observer、結果計算或工作目錄配置。

**持久輸出仍 BLOCKED。** 診斷 JSON 經固定 stdout transport 輸出，journal／host 保存是另外的診斷證據保存，沒有被當成 16MiB aggregate persistent disk 的強制證明。tmpfs 容量與 inode 限制不能證明 ext4 的持久 metadata／block 容量。原 FSIZE、固定 FDs、allocation guard 與 st_blocks 檢查均保留，但不升格為 allocated-disk hard quota。

`full-campaign` 與 `BUILD_ONLY` 無條件拒絕，任何 receipt、環境變數或旗標都不能解除。原有正式入口不變。只有經來源審查、離線測試與 exact revision 凍結後，才可在既有授權範圍執行一次 `launch-live-diagnostic`；此命令不是正式 build，失敗後不得自動重跑或改限額。

固定 unit 名稱只防止同時存在的相同 unit，不是持久 single-use 授權機制。本版不建立、讀取或重用 HumanReview。

成功的 diagnostic 只能支持實際觀察到的 volatile lifecycle 與限制；完整 47-case／負面資源矩陣、persistent capacity、unexpected termination／orphan 與 inode exhaustion 未全部實測前，`FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED`、`FULL_LAUNCH_ENVELOPE_VERIFIED` 均為 false。

安全離線回歸使用既有七個 resource test modules、新增兩個 full-controller/publication test modules，以及固定 81-case `legacy_regression`。禁止 discover 舊 integration_runtime／guard_correction 全目錄。新的 publication guard 固定 base 為 PR32 `66663557984fcc069de600e2af07e778a4ac30ff`，只允許本補件 source／tests／reports／四個 CI 設定；逐一檢查 staged index 與每個 outgoing commit 的 intermediate payload，禁止圖、binary、event、private config。

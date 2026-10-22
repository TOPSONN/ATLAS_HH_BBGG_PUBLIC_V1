# G2 能力分析：既有 capture 的範圍

本次 exact reader source `d05acf64521775f1df5fb2dcb917981f107c672c`。輸入 raw SHA256 `c575418ca9c4a63c8ea6e53404652b4b190b03e2e5c65ada4321880c2cb87cbc`。只重驗既有 bytes；沒有重新採集、啟動 WSL、查詢 manager bus、配置 service 或執行 kernel 測試。G1 的 PASS_READ_ONLY_OBSERVED 不授權 G2、S4、BUILD_ONLY 或物理計算。

| 能力 | 本次證據 | 狀態與下一個所需證據 |
|---|---|---|
| cgroup v2 lineage 與 anchors | 2 層；capture 內 boot、mount namespace、membership 前後一致 | PASS_READ_ONLY_OBSERVED；沒有驗證現在的 boot／freshness |
| CPU | 第 0 層 quota=UNLIMITED、period=100000 µs；數值 cpu.stat 可解析 | BLOCKED 全作業累積 CPU stop；需覆蓋 controller／worker／collector 的共同 cgroup 與獨立停止、收尾量測 |
| RAM／swap | 第 0 層 memory.max 與 memory.swap.max 均 UNLIMITED | BLOCKED 指定 RAM ceiling／swap0；usage=0 或 parser PASS 不能證明 swap 禁用 |
| wall | 只有唯讀 collector 的 monotonic anchors | UNKNOWN activation-to-final-cleanup；不是實際作業或 deadline receipt |
| root 介面 | 10 個 UNKNOWN/FileNotFoundError；非 root 指定欄位無缺值 | 保留缺值。多數 limit/usage 介面由規格限定 non-root，不能補成 0 或 max；不是整個 guest 已完成 attestation |
| manager／user session | 本次沒有 bus/effective unit query | UNKNOWN；先前 WSL user-session warning 不能由此解析成功宣告解除 |
| persistent capacity | 沒有取得已核實專用固定裝置／quota／allocated-block與inode上限的新增證據 | BLOCKED；host↔guest 映射、root-device排除、same-FD identity、exclusivity 仍需獨立審查 |
| journald／rsyslog／control plane | 靜態資料不能自證實際 routing、容量與durability | UNKNOWN；需有界持久 failure slots、受保護 collector 與獨立 capture 的部署證據 |
| OOM／timeout／controller loss與cleanup | 沒有實際正常／故障 job | BLOCKED；需原始 kernel counters、InvocationID、終態空 cgroup 與 collector 退出後獨立 observer |
| host VM／launcher／manager成本 | 既有 B-V2 三份條款仍 user_accepted=false | BLOCKED 架構接受；不得把未量測 overhead 記為0或自行排除 |

`cpu.max` 是期間內 bandwidth quota，不能單靠它保證整個生命週期累積 CPU 秒數。`RuntimeMaxSec` 約束 active runtime，還需 activation、stop 與最終觀察的整段證據。Linux memory.max 可短暫超額，memory.swap.max 降低後 usage 可能暫高於新限制；因此本修復不把分開讀取的 usage>limit 或較晚 current>較早 peak 當成必然矛盾。[Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)、[systemd resource control](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html)、[systemd service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)。這是正式 API 語義；沒有藉此斷言本機安裝版本或部署能力。

下一步為 G2 **能力與邊界決策審查**：先決定保留原 A 全 host+guest／零瞬時超額契約，或逐條審查既有 B-V2、VM cost assignment 與 post-exit observer supplement 的較弱語義；三份原件 byte 不變，本次不設定 accepted。若堅持 A，目前 WSL 觀察仍不足以建立完整能力，不宣稱所有平台技術上不可能。接受 B 也不代表立即可執行，仍須可核實固定裝置、manager/log bounds、collector 隔離、精確 source review，以及另行授權的部署／正常與失敗 kernel 測試。

本報告不提供執行 service、mount、format、sudo 或 stress 的命令。`FULL_LAUNCH_ENVELOPE_VERIFIED=false`；`FORMAL_BUILD_ONLY_AUTHORIZED=false`。

# G1 association output-bound 修復審查

結論：SOURCE_REPAIR_VALIDATED_FRESH_CAPTURE_PENDING。Exact source `61bda291c2bc6a04607cb8ea889e520a4ceb260b`，stacked base PR39 `b2bd49b68c3a439eeef24b7b2e134f1746bf5fb9`。原失敗收據只讀取、雜湊核對，沒有修改或公開 raw 資料。

## 觀察與推論

原收據 6,065 bytes，11 reported-unattested、2 UNKNOWN。兩個 association 的私有受控錯誤均為 byte-bound 分支，而不是先執行的 row-bound 分支。使用原 Depth8、Compress 設定重新序列化既有成功 rows，合計 2,400 bytes；兩次失敗前 aggregate 都尚餘 194,208 bytes，故各查詢必定超出 65,536 bytes。失敗 payload 未留存，確切大小與 edge 數量 UNKNOWN。

使用者回報兩次 depth8 warning；原收據未保存 warning stream，不能將其當成獨立量測。來源確實序列化完整巢狀 CimInstance；它是合理的膨脹原因推論，仍需新實際擷取才能確認實際 compact 大小及 coverage。

## 實質修改

PowerShell 驗證 association/endpoint CIM 類型、root/cimv2 namespace、本機 server、Reference key 與 DeviceID key，輸出 scalar class/DeviceID identity。disk inventory 加入原本缺少的 DeviceID 供 referential integrity 使用。兩類 edge 全量讀到結束或第129筆 sentinel；129筆即整項 UNKNOWN，不接受前128筆作完整結果。完整集合還需通過已知 inventories 的唯一性、dangling、partition coverage、DiskIndex、固定磁碟 volume coverage 檢查。Volume 保留完整 UInt64 起訖位址為十進位字串，接受不同 partition 指向相同 volume，不任選一條 edge。

缺值、錯類別／namespace／remote identity、未支援 reference 表示法、重複 edge（包括不同 extent 的 conflicting duplicate）、不完整 prerequisite、矛盾 parent 或 extent 都拒絕。缺失的 provider edge 若不造成內部矛盾或 coverage 缺口，單次 JSON 無法獨立證明；provider end-of-enumeration 仍屬 reported-unattested，不是假裝 host attestation。無額外硬體查詢或 parser/physics 呼叫。

所有 payload ConvertTo-Json 加 WarningAction Stop；警告整項失敗，最終 capture 警告則不寫入檔案。row/query-byte/aggregate-byte 分開原因；bound diagnostics 只留數值下限，不保留被拒絕的部分拓撲。所有容量保持原值。原 nonadmin、私有 ACL、signed/hash-pinned wsl.exe、allowlist argv、owned PID cleanup、CreateNew、flush/readback 原碼逐段核對不變。Provider allocation 與45秒 between-query deadline仍非完整硬性 resource envelope。

V2 Python 驗證與 PowerShell 分開實作，同樣檢查 graph/extent/closure；原 V1 只保留歷史解讀，不能以新 collector SHA 重新解釋為本次有效 capture。sanitized projection 不含 endpoint IDs、序號、原始 rows、paths 或錯誤文字。

## 實際驗證與界線

本機84項 affected tests 全過；另外實跑 PowerShell 的26個 in-memory CIM 正反案例，沒有執行 inventory top level、Get-CimInstance、WSL、systemd 或任何物理工具。128 disk edges 編碼 35987 bytes，128 volume edges 編碼 41363 bytes。這些是 fixtures，不是真實主機數字。另測100條較長 identity 之完整合法集合超過byte cap時整項拒絕，沒有截斷。

Linux-only 612/81 完整 runners 在本機 Windows 分別因 fcntl/resource 不可用而未啟動；保留為 BLOCKED_LOCAL_PLATFORM，由新 PR 的 Ubuntu CI 實跑。CI Windows job 另實跑合成 CIM。舊三份 physics/readiness workflow 與舊 resource job 對此分支停用，轉入本次固定 source-only CI；historical frozen-input 只容許固定 branch 排除字串，其他1018份 input exact，原 manifest 不改。

來源審查由本 agent 完成；不同語言的 producer/reader 互驗是獨立實作驗證，不能稱為另有人類審批。已逐byte核對1614/1621份基底檔未變，其餘7份為限定 source/CI 修改。原始收據及歷史報告/物理資料保存。

## 如果真實完整 edges 仍超限

保持 UNKNOWN，不增大現行上限。新錯誤會區分 row/query-byte/aggregate，記錄可觀察 exact serialized bytes 或129-row lower bound。最小未授權 V3 設計是分頁的 bounded edge-only capture：每頁仍最多128 edges／65,536 bytes，manifest 要有相同 capture/session/source identity、總數、每頁ordinal與SHA、endpoint inventory SHA、全域duplicate/conflict檢查及確定的終止標記；先後 snapshot 需一致性核對。每頁不得任意裁切一條 edge；若單頁單edge已超限或無法保證穩定snapshot，需保持 BLOCKED。總頁數、aggregate disk/bytes 與最小所需容量必須依新真實下限重新提案核准；本 PR 未實作或授權 V3，不能預先宣稱盤點完成。

## 狀態

PASS：byte-bound 原因證據、compact source/graph validator、正反測試、私有輸出安全規則保存、原收據 SHA 保存、現有 WSL binary hash 一致。

FAIL：原 capture 的兩類查詢歷史失敗保留；無本次未解決的 affected-test failure。

BLOCKED：本機 Linux-only runners；後續 kernel/capacity/G2 等既有外部關卡未被本修復解除。

UNKNOWN/PENDING：新真實 capture、實際 edge counts/bytes、13/13 coverage、host attestation、guest identity；CI 在本檔生成時 PENDING，以 PR checks 最新結果為準。

`FULL_LAUNCH_ENVELOPE_VERIFIED=false`、`FORMAL_BUILD_ONLY_AUTHORIZED=false`。S4、sudo、裝置修改、WSL啟動、MG5/build/ME/integration/events 均未執行。下一步只有 USER_COMMAND_ZH_TW.md 的一般權限 PowerShell7 單次新擷取，之後驗證 SHA 並產生新的 sanitized projection。

Microsoft class contracts：[DiskDriveToDiskPartition](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-diskdrivetodiskpartition)、[LogicalDiskToPartition](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-logicaldisktopartition)。前者 endpoints 為磁碟與partition，後者為partition與logicaldisk並具有extent起訖；本修復依此保留關聯。

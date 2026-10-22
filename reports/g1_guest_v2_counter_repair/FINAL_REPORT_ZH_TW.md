# Guest V2 cgroup counter parser 修復報告

完成範圍：既有收據的獨立唯讀驗證。最終驗證標籤 **PASS_READ_ONLY_OBSERVED**；資源硬限制、G2、S4、正式 build 仍未驗收／未授權。

Base：Draft PR41 `1ee91a8b4aa974a80c0b5a73c35e2c0e34204fee`。修復 exact source：`d05acf64521775f1df5fb2dcb917981f107c672c`。Draft PR：[PR42](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/42)，stacked on `codex/phase7i-g1-g7-engineering`。報告 commit 為獨立的 report-only delivery；其最終 SHA 以 PR HEAD 及交付訊息記錄，不更動此 exact executable source。

## 根因與修復

指定 raw SHA256 `c575418ca9c4a63c8ea6e53404652b4b190b03e2e5c65ada4321880c2cb87cbc` 已核對。以舊 `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d` 的實際 reader 重現 COUNTER_SYNTAX；Python exception trace 精確定位第 0 層 `memory.swap.max`、token `max`。不是只依錯誤名稱猜測。詳見 OLD_FAILURE_DIAGNOSTIC.json。

原分支僅特判 memory.max／pids.max，memory.swap.max 落入 memory.* decimal 分支。新 parser 只對 memory.max、memory.swap.max、pids.max 與 cpu.max quota 接受 `max`，統一輸出 `UNLIMITED`；不轉0、不輸出swap-disabled。cpu.max period、memory.current／peak／swap.current、cpu.stat／memory.events／cgroup.events 仍嚴格解析 canonical 非負整數，拒絕非法字串、負號、缺失 scalar、重複鍵與超出 unsigned64 上限。原 geometry decimal／pairs 保持原碼；cgroup 專用 numeric parser 明確支援完整 u64，未放寬全域 parser。

同一路徑重複 record 拒絕，只有 collector 固定的兩次 boot／membership anchors 例外且須內容一致。flat counters 與 raw JSON 重複鍵拒絕。populated／frozen 超出0/1為矛盾；不同時間讀取的 current／peak／limit 不強行建立不存在的原子一致性。缺少介面／key 保留 missing 與 coverage，不補0或UNLIMITED。[正式 Linux 語義](https://docs.kernel.org/admin-guide/cgroup-v2.html)。

## Sanitized 真實驗證

| 項目 | 結果 |
|---|---|
| status／trust | PASS_READ_ONLY_OBSERVED／REPORTED_UNATTESTED |
| lineage | 2 層；第0層非root，第1層root |
| 第0層 limit | memory.max=UNLIMITED；memory.swap.max=UNLIMITED；cpu.max quota=UNLIMITED、period=100000 µs；pids.max=9201 |
| non-root missing | 0 |
| root missing | 10 個介面，原始狀態均 UNKNOWN/FileNotFoundError；詳細欄位見下 |
| boot／mount namespace／membership | capture 內 before/after 一致；只輸出布林值，不公開原始 identities |
| coverage | INCOMPLETE_OBSERVED；不將root缺值補成數字 |
| freshness／manager | UNKNOWN_NO_CURRENT_SAME_BOOT_CLOCK／UNKNOWN_NOT_BUS_ATTESTED |
| host mapping／attestation／runtime enforcement | false／false／false |

root 未回報清單：cgroup.events、cgroup.type、cpu.max、memory.current、memory.events、memory.max、memory.peak、memory.swap.current、memory.swap.max、pids.max。non-root限定介面在root缺少可符合kernel語義，但仍如實列出。`swap_disabled_verified=false`。完整有界輸出為 G1_GUEST_VALIDATION.json；不含原始 topology、boot ID、namespace inode 或 cgroup 路徑。

## 實際測試與保存

- PASS：本機142 affected tests，0 failure／0 error／0 skip。新21個counter測試方法與5個publication方法，含大量參數化正反案例；與既有套件有重疊，不相加成獨立覆蓋數。
- PASS：exact source 的 offline CLI 實際 exit0；兩個 CLI 負例實際 exit2（既有output不覆寫、錯raw digest拒絕），raw及既有sanitized output hash不變。
- PASS：Ubuntu source push／PR CI 各612/612 offline、81/81 safe legacy；affected142中141通過、1個Windows-only skip。Windows各81/81 affected subset，包含26個in-memory PowerShell CIM案例。decoded logs已讀；forbidden attempts、physics imports、human authorization construction均0。
- PASS：同agent在獨立 Python process以不同的逐字元／整數演算法核對真實raw，UNLIMITED及anchors結果相符；另做AST與diff審查。沒有虛構第二位人類審查或kernel驗收。
- PASS：394份source/dependency SHA256清單。1698個base檔中1693逐byte不變；只改reader、history精確CI相容例外及3條branch exclusions，另新增5個source/CI檔。1019 frozen inputs中1018原科學輸入exact，唯一例外是已審查的campaign CI routing。
- PASS：原guest collector與legacy、Windows collector、核心guards、歷史科學報告／圖像／事件原件均不改；舊83d1 checkout保持clean，84個checkpoint檔之aggregate SHA256 `37eab3240a1ba8551f971e56031e852bf22fd6737c5790df370aec067924d241` 前後一致。原run不重綁；本次為獨立離線review。
- FAIL（歷史、保留）：舊reader對合法swap max拒絕；修復前candidate收據保留，不覆寫。沒有未解決的新測試failure。
- BLOCKED：資源enforcement、G2架構接受、persistent capacity、cleanup正反實測、S4及正式build。
- UNKNOWN：當前guest session／freshness、有效manager／logging與跨host mapping。沒有重跑capture來補證據。

Source CI：[push](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/39713098495)、[PR](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/39713143442)。TEST_RESULTS.json記錄source revision已完成的CI；本report-only commit尚不存在時，其delivery CI標記PENDING，最後以PR checks與交付訊息補充，不能將舊CI冒充新HEAD。

## 操作與下一關卡

重驗只讀取已存在的本機raw，不需要WSL。以下Windows PowerShell命令會建立全新sanitized檔案，已存在則拒絕；它不建立Master run、不重新採集、不啟動任何service：

```powershell
Set-Location 'C:\HH\.local\g1_guest_v2_counter_repair_v1\source'
& 'C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe' -B -X utf8 -m simulation.hh_signal.final_closure.master.guest_counter_review --input 'C:\HH\.local\g1_guest_v2_counter_repair_v1\private\existing_guest.json' --expected-raw-sha256 c575418ca9c4a63c8ea6e53404652b4b190b03e2e5c65ada4321880c2cb87cbc --output 'C:\HH\.local\g1_guest_v2_counter_repair_v1\sanitized_user_review_01.json'
```

公開前固定PR41 gate檢查完整index及每個intermediate commit，逐份source hash、UTF-8、大小、private schema／nested identity、binary／event／figure排除。只提交10個source/CI檔與8份有界sanitized報告；raw guest JSON及本機完整logs不提交。沒有PDF／PNG產生或推送。

下一步是 G2 能力與條款審查，詳見 G2_CAPABILITY_ANALYSIS_ZH_TW.md。原A、B-V2條款／VM成本assignment／observer supplement全保留；不自行設定接受、不產生授權。沒有sudo、WSL啟動／重啟、format、mount、服務修改、stress、MG5/build/ME/integration/events。`FULL_LAUNCH_ENVELOPE_VERIFIED=false`；`FORMAL_BUILD_ONLY_AUTHORIZED=false`。PR保持Draft，不merge或force-push。

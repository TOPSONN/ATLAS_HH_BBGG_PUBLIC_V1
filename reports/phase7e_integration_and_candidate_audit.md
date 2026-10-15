# Phase7E：積分、候選事件與截斷

結論：B/C 的 10.3786% 相對差含有**已證實的不同 PDF 與 αs running**。用兩者所報誤差算出的 8.18128 單位只是數值比值，不能當同一 integrand 的 seed tension 或 8.18σ 物理顯著性。尚未量化 PDF、running、積分收斂各自貢獻。

以下讀取真實原生日誌；[數值投影與原檔 SHA](../simulation/hh_signal/integration_audit/evidence/source_audit.json) 保留逐 iteration 證據，不把投影誤稱完整 log。

| 原生工作 | iteration mean pb（error） | 最後彙總 std pb | 最後 χ欄位 | Found → Wrote | overweight |
|---|---|---|---|---|---|
| B survey G1 | .01839(.0008844), .01678(.0003224), .01733(.0001432) | .0001295 | 2.0402 | 406 → 403 | 0 |
| C survey G1 | .01847(.0009136), .01858(.0003223), .01910(.0001468) | .0001322 | 1.2676 | 398 → 394 | 0 |
| C refine G1_1 | .01907(.0001174)，**僅一次** | .0001174 | 0 | 2703 → 2203 | 416 |

B `results.dat` 保存更高印出精度的 iteration means .018386/.016783/.017334；最後 σ=.017276±.00018503。B survey 的 input_app 為 1000、max/min iterations=5/3、accuracy=.02、grid adjustment=2、exact helicity nhel=0；403 候選已足夠取得 100，原 `refine 100` 沒有排新積分工作。

C survey 實際跑三次並累積 .019003795176943006 pb，前端所報 .019004±.00014885。C refine 的 input_app 是 2925、max/min=1/1、accuracy=.02、grid adjustment=−2、nhel=0；結果 .019069±.00011745。保留的 C G1/input_app 與 results.dat 已被後續工作覆寫為 refine 控制／合併結果，不能誤當最初 survey 設定。初期 survey 的原 input card 已無獨立快照；三次實際迭代由 log 證實。

MG `dsample.f` 使用最後最多三次 iteration、以相對變異決定權重，並在內部 χ欄位大於 1 時將誤差乘 sqrt(χ)。例如 B 的 .0001295×sqrt(2.0402)≈.000185；C survey 的 .0001322×sqrt(1.2676)≈.00014885。數字有日誌印出捨入。這不是以多個獨立 seed 校準的 coverage；C refine 只有一次，χ=0 不證明收斂，也不代表誤差為零。自適應、尾部抽樣、loop 穩定性與權重相關的低估可能性仍需匹配設定的獨立重複量測。

候選池不可直接當作有效未加權產生效率。B log 的 0.52%、C survey 的 0.49%、C refine 的 0.33% 是原生表的 primary efficiency 欄；Found/Wrote 是緩衝池與部分 unweight 後數量，Wrote/Found 並非完整 ME-call 效率。B 保存的 run_statistics 為 28100 次評估、平均 .0625797962 秒、累積 1758.90595 秒；7016 等其他原生欄位不是同一分母。

C refine 的 `% Cross section > 1:` 兩欄為 `0.051445615000118433`（內部權重超額）及 **1.0021788225048662%**（100*xover/xtot）。不可把第一欄說成丟掉 5.14% pb 或截面。`unwgt.f` 對 overweight 保留 max(abs(weight),target)，416 不是「遺失 416 事件」。原生緩衝上限 200000，最大可見 Found=2703，沒有觀察到此上限被打滿。

最終 combine/unweight 使用 trunc_error=.01、event_target=100/1000。積分報值早於最後 target thinning，故將 2203 候選取成 1000 不會算術上改寫先前所報 integral；它仍可能影響保留事件的納入機率及尾部代表性。最終逐候選權重／接受歷史已清理，**無法精確重建實際截斷份額與所有候選納入機率**；不能宣稱完全排除截斷影響，也不能把 .01 設定值當作觀測到的損失。

Grid 歷史是 **PARTIAL**：B G1/ftn26 留存；C G1/ftn26 與 G1_1/ftn25 hash 相同，支持 refine 由 survey grid 起始；G1_1/ftn26 是後續不同快照。精確 bytes/hash 在 source_audit 的 retained_grid_inventory。不是每次 iteration 的完整 grid 軌跡，亦不構成獨立 seed 驗證。原始資料共 8420 檔（752305317 logical bytes）均未改動。

本次可確認配置失配，不能將殘餘差異唯一歸因於 seed、截斷或誤差低估。需先通過 compiled/runtime PDF、running、seed 一致性，再在不同新 seed、獨立 grid、受控預算下測量；目前未授權，沒有新積分。

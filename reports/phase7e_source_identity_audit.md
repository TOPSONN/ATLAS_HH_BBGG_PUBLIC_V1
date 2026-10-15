# Phase7E：來源身分稽核與補充更正

基線為 PR20 的 `a0e1539e56c122deb6b36a708a121d2098ad3220`。這次只讀既有輸入；新增物理事件與積分均為 0。

**更正：C1000 的有效 PDF／αs running 並非原契約宣告的 CTEQ6L1／一圈。** 原卡片、LHE header 與舊驗證報告不足以證明實際 PDF 身分。本次交叉檢查編譯 include、原生日誌及全部既有事件的 ALPS，確認 C 使用 `nn23lo1` 與兩圈 running。因此 C 及以 C 為來源的 D 不可視為已驗證的原 CTEQ6L1 目標。歷史檔案保留；本報告及 [機器可讀更正](../metadata/phase7e_audit.json) 補充限制舊結論。

| 項目 | B100 | C1000 |
|---|---|---|
| 真實保留來源事件 | 100 | 1000 |
| 原生截面 pb | 0.017276 ± 0.00018503 | 0.019069 ± 0.00011745 |
| reviewed／embedded card PDF | cteq6l1 | cteq6l1 |
| `Source/run_card.inc` 全域 PDLABEL | cteq6l1 | **nn23lo1** |
| 兩個 PDSUBLABEL | cteq6l1 | cteq6l1 |
| G1／G1_1 實際初始化 | CTEQ6L1 | **NNPDF23_lo_as_0130_qed_mem0.grid** |
| 原生 αs(MZ) | 0.13 | 0.13 |
| 實際 running | 1 loop | **2 loops** |
| LHE PDFSUP | 10042/10042 | 10042/10042，與執行衝突 |
| requested seed → effective | 20261121 → **21** | 20261122 → 20261122 |

原始來源 SHA256：

* B：`29f025bd9b08a494b744b1d1927ab6e787b8af9c239656fa740885a1d373d16b`
* C：`b13e5010f80b734495598492c97f5a7f73da72568c296134b2fb15b302a69eac`

相同的物理部分：`g g > h h [noborn=QCD]`、`loop_sm`、有限 MT/MB、13 TeV、MH=125、MT=173、MB=4.7 GeV、κλ=κt=1、inclusive on-shell HH、μR=μF=mHH/2。原嵌入 param card 完全相同，SHA256=`7202496aa723bbaba468993245343e82819c233a1c69f9bf684bdce7aa5c08e0`。原生 param card 的 SMINPUTS[3]=0.129783 是初始化前輸入；不得把它誤稱為積分實際使用的 αs(MZ)。

[物理來源比對](../simulation/hh_signal/integration_audit/evidence/physics_source_identity.json) 確認 84 個原生 MODEL、DHELAS 與 loop subprocess Fortran/include 檔完全相同，process commands 相同。[完整卡片稽核](../simulation/hh_signal/integration_audit/evidence/source_audit.json) 顯示 embedded run cards 只有 nevents、iseed 不同；編譯 include 除 nevents 外，多出關鍵的 PDLABEL 差異。MadLoop card SHA 相同；不是改成 HEFT、換質量或額外套 K factor。

`pdf.f` 依全域 PDLABEL 分派密度；PDSUBLABEL 保持 cteq6l1 不能推翻全域 nn23lo1。`pdfwrap.f` 預設 nloop=2，CTEQ6L1 分支改為 1，NNPDF 分支沒有此改寫。原生程式來源及行號見 [native_semantics.json](../simulation/hh_signal/integration_audit/evidence/native_semantics.json)，MG5 commit 固定 `3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`。

已實際編譯並執行純原生 `ALPHAS(Q)` 探針，只代入既有 1100 個尺度，不呼叫 PDF、矩陣元素、不採樣相空間。B 全部吻合一圈（最大相對差 4.756e−7），C 全部吻合兩圈（4.870e−7）；獨立 Python RGE 解亦吻合，差異在原生七位有效數字容許內。[實測證據](../simulation/hh_signal/integration_audit/evidence/alpha_running_audit.json) 保留來源及探針 hash。

卡片轉譯實驗另重現一種一致的失敗模式：重複使用 working-card 的 RunCardLO writer，後續 write 可能讀取鄰近 default card，造成全域 nn23lo1、beam sublabels 仍 cteq6l1。這是實際重現的機制，**不是完整重建已遺失的歷史 Python 記憶體狀態**。新準備命令每次從精確文字新建 writer，重做三次 include 並檢查三個 PDF 欄位。

B 的 seed 偏移獨立於 PDF 問題：第一次編譯前失敗時 working iseed 已被 MG 清為 0；舊 continuation 未恢復 reviewed seed，後續原生 banner／survey 使用 21。最終 randinit 的 r=27 是後續工作狀態，不是初始 seed；C 為 r=20261128。保留 working iseed=0 亦不能解讀為實際生成 seed=0。詳見 [seed_audit.json](../simulation/hh_signal/integration_audit/evidence/seed_audit.json)。本次沒有改 seed 或重製 B。

保留的 D event-wise ME 比率及原 ALPS 綁定仍可做「實際 C proposal 上」的方法與統計稽核；不能以此宣稱原 CTEQ6L1 物理率、獨立 κ 產生驗證或官方 ATLAS 結果。原 BR 因子只套一次、原 selection／weights 均未改動。

# Phase7G native writer suppression 科學語義稽核

結論：**BLOCKED_INTEGRATION_SEMANTICS**。目前沒有新積分，沒有新截面，沒有證明完整 native survey 等價。
實測與來源推論分開記錄於 [semantics.json](../simulation/hh_signal/matched_integration/evidence/semantics.json)。
所有稽核 native 檔案先與 PR22 的 frozen source SHA256 核對；摘錄包含來源相對路徑與原行號。

| 問題 | 證據與限定 |
|---|---|
| RNG | `Source/ranmar.f` 的 RANMAR common state、`Source/dsample.f:2546` 的 ran1 SAVE state、`Source/ran1.f` 的 xran1 SAVE state互相分開。原生 RNG-only executable 實際測試兩模式：各 16 次 RANMAR，模式1穿插32次 ran1、16次 xran1。RANMAR trace 精確一致；下一個輔助輸出不同。這不是實際 native writer 的 point trace。 |
| point sampling | `dsample.f:1104,1202,1206` 與 `auto_dsig*.f` 使用 RANMAR；writer topology/addmothers 使用 ran1、unweight/store 使用 xran1。實際 `MAPCONFIG(0)=1`，多 channel 的 ran1 選擇路徑不啟用。不能推廣至其他 process。完整新 survey 的 ME/point trace 尚未執行。 |
| 候選狀態 | 原 `unwgt.f:817–820` 更新 nw/swgt 並序列化 scratch candidate。F suppression 移除整段 write_leshouche，另將 th_nunwgt/th_maxwgt/neventswritten 歸零。suppressed-call counter 是呼叫次數，不能冒稱原本保留候選數。 |
| stopping | `dsample.f:2183–2221` 負 accuracy 的 luminosity/event stopping 讀 neventswritten，與 suppression 不等價。預定只允許 accuracy=0、固定 min=max iterations；native failure/resource cutoff 仍可能提前終止，必須 PARTIAL。 |
| adaptation | `sample_put_point` 累加 abs(wgt)、wgt²、grid 及 grid2。若輸入完全相同，這些更新相同；原程式另明確設 zooming=false。相同完整 weight stream 是尚未驗證的前提。 |
| integral/error | 原權重經 DSIG 計算後才呼叫 UNWGT；固定 synthetic list 的兩份算式和=41、平方和=289 已實測。這只檢查算式，沒有執行 native estimator、grid、ME 或誤差估計；不構成 integral/error 等價證明。 |
| 尾端統計 | suppression 清除原候選統計，所以原 th_maxwgt/th_nunwgt 不能直接用來判斷 tails/overweight。需要與積分權重相連的原生計數及有界 diagnostics；目前 UNKNOWN。 |
| transient outputs | RNG-only 工作目錄最後沒有事件檔。無真正 survey，未聲稱完整 transient coverage；未來輪詢亦需揭露間隔、建立即刪除的盲區與其他可寫位置。 |

沒有執行原始實體 serializer 來做對照，避免為測試建立任何實體物理事件。
原生 initialization/writer 邊界證據保留自 F，並重新驗證其 bytes；G 只新增 RNG-only/固定 synthetic weights 原生測試。
Stage A 真實 ME/config/counters/seed/grid/zero-retention 測試及 Stage B 全部 NOT_EVALUATED。
方法測試的人工 receipt 不當作真實執行 receipt。

下一個技術步驟是先審查狹窄的 paired no-output native instrumentation：分離 candidate 的計數/RNG 語義與實體序列化，
在無物理事件輸出的條件下記錄每輪原始權重、ME 呼叫、網格增量、停止決策與估計量；
需要明確定義 rounding、store/clear 邊界與尾端統計的替代語義。
僅當來源證據與真正執行證據足夠，才可把語義閘門改為 VALIDATED。
在此之前保留 STOP80；另行人類授權也不會自動解決這個科學阻擋。

統計方法預先實作：四個完整、matched、獨立 grid 端點之平均、sample SD、SD/2、t(3) 的95%區間；
native internal errors 與由其傳播的 mean error 另列，不與 between-run error 盲目相加。
小樣本 t 區間依賴獨立性及近似常態，heavy tails 時覆蓋率尚未保證；四個完成 job 本身不證明收斂。
需要不同預算端點的穩定性、iteration/grid/tail diagnostics，不能把同一 grid 的 successive refine 當獨立測量。

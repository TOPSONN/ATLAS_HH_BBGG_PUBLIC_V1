# Phase7D：逐來源訊號／背景比較

κλ=2.5與5明確為 `INCONCLUSIVE_REWEIGHTING`：來源ESS分別36.6943、19.5442，最大單點份額超過10%；最終選擇ESS為16.0736、7.65012。它們只有實測權重與診斷分布，不能稱已驗證的精密相對形狀或物理率。其他benchmark也須逐bin檢查低ESS及尾部支援，不能用全局ESS保證每bin精度。

| 來源 | 固定cutflow | 最終模型權重 pb | 100 fb⁻¹探索產量 | 解讀範圍 |
|---|---|---|---|---|
| S01 | 1000 / 484 / 403 / 143 / 143 | 7.23559408e-06 | 0.72355941 | MODEL_BR_ONLY_REWEIGHTED_INCONCLUSIVE_ABSOLUTE_RATE |
| B01 | 1000 / 446 / 266 / 91 / 28 | 0.00185490654 | 185.49065 | RAW_SOURCE_EXPLORATORY_UNCALIBRATED_OVERLAP_UNKNOWN |
| B02 | 1000 / 378 / 241 / 7 / 1 | 0.0006274417 | 62.74417 | RAW_SOURCE_EXPLORATORY_UNCALIBRATED_OVERLAP_UNKNOWN |
| B03 | 1000 / 445 / 277 / 0 / 0 | 0 | 0 | RAW_SOURCE_EXPLORATORY_UNCALIBRATED_OVERLAP_UNKNOWN |
| B04 | 1000 / 370 / 220 / 77 / 75 | 1.54220116e-05 | 1.5422012 | MODEL_BR_ONLY_EXPLORATORY |
| B05 | 1000 / 327 / 322 / 131 / 131 | 0.000120145251 | 12.014525 | MODEL_BR_ONLY_EXPLORATORY_TTH_SPIN_UNVALIDATED |
| B06 | 1000 / 2 / 2 / 2 / 0 | 0 | 0 | ONE_BORN_PHOTON_NO_CALIBRATED_FAKE_MODEL |


固定Phase6C選擇：至少兩光子、leading pT>35與subleading>25、|η|<2.37、排除1.37<|η|<1.52；至少兩個pT>25、|η|<2.5的jet；至少兩個native bit0 tag；105≤mγγ≤160 GeV。沒有mbb最佳化cut。mbb及相關變數使用實際leading tagged pair，沒有把條件式tag期望當成質量分布。

13個共同observable、input與final階段、六κ與六條背景分開保存在 `metadata/phase7d_weighted_histograms.csv` 與選定數值ROOT。單位面積模式含flows且防護零總和／符號抵消；100fb⁻¹模式為pb×100×1000，只是共同探索參數。背景truth HH變數標為不適用，缺配對不是0質量。

B01–B03的ME/PS overlap未解；B04/B05為MODEL_BR_ONLY；B05 spin未驗證；B06只有一個Born photon且沒有校準fake模型。合併物理產量=`BLOCKED_OVERLAP_AND_CALIBRATION`。沒有官方總背景、S/√B、發現或排除宣稱。

絕對率維持 INCONCLUSIVE_ABSOLUTE_NORMALIZATION_CROSS_RUN_TENSION：B/C實際卡一致，但截面差為所報積分誤差quadrature的8.18128倍；這不是已校準Gaussian顯著性。未執行獨立κ benchmark積分，不重縮放來源，不採用NLO K factor。

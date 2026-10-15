# Phase7B/C/D：最終物理與方法判決

κλ=2.5與5明確為 `INCONCLUSIVE_REWEIGHTING`：來源ESS分別36.6943、19.5442，最大單點份額超過10%；最終選擇ESS為16.0736、7.65012。它們只有實測權重與診斷分布，不能稱已驗證的精密相對形狀或物理率。其他benchmark也須逐bin檢查低ESS及尾部支援，不能用全局ESS保證每bin精度。

FINAL_VERDICT: PASS_7B_7C_WITH_7D_INCONCLUSIVE

7B100與7C新1000實際full-mass SM來源、物理對稱逐Higgs混合衰變、Pythia、獨立HepMC ReaderAscii、Delphes與ROOT全鏈通過。總獨立來源1100，D新增0；10/100前綴從不增加統計。B有效seed21對請求20261121的歷史偏差明確保留；未補生事件。C有效seed20261122與請求完全一致，已在續跑前修正卡恢復並通過負向回歸。

7D1000×6原生ME、獨立15點fresh-process對照、Decimal數值回歸、7100筆native ROOT讀回、逐來源比較與統計評估實際完成。數學/相對形狀可在有限pilot支援範圍使用，絕對物理率仍INCONCLUSIVE。模型BRbb0.5774528919828654、BRγγ0.00229754317933142、2BRbbBRγγ=0.0026534459067208711，只乘一次；外部reference/adopted physical BR均未採用。

| κλ | 生產估計 pb | 輸入MC標準誤 pb | 輸入ESS | 最大ratio | 最終MODEL_BR_ONLY pb | 最終ESS |
|---|---|---|---|---|---|---|
| -1 | 0.0774790357 | 0.00441673 | 235.495 | 188.9326 | 3.20259311e-05 | 43.7733 |
| 0 | 0.0417814248 | 0.00131228 | 503.655 | 54.19853 | 1.66726454e-05 | 78.3097 |
| 1 | 0.019069 | 0 | 1000 | 1 | 7.23559408e-06 | 143 |
| 2 | 0.00934176118 | 0.000582774 | 204.589 | 29.33706 | 3.71477711e-06 | 71.9809 |
| 2.5 | 0.00934758653 | 0.0015153 | 36.6943 | 74.08143 | 4.17295652e-06 | 16.0736 |
| 5 | 0.0580711608 | 0.0130132 | 19.5442 | 603.5617 | 2.86497324e-05 | 7.65012 |


絕對率維持 INCONCLUSIVE_ABSOLUTE_NORMALIZATION_CROSS_RUN_TENSION：B/C實際卡一致，但截面差為所報積分誤差quadrature的8.18128倍；這不是已校準Gaussian顯著性。未執行獨立κ benchmark積分，不重縮放來源，不採用NLO K factor。

Q/R/S/T維持BLOCKED。無未核准PDF/PNG、無自動大生產、無合併背景敏感度宣稱；原625個基線blob及Phase7A科學來源/報告/數值證據維持不變。選定真實來源與100事件HepMC/ROOT前綴發布於同一stacked Draft PR20，完整C1000下游樣本留本機。

資源收據：受監控的來源/重加權及已記錄準備時間合計8495.927秒；抽樣process-tree峰值RSS=1759412224 bytes；當時campaign+隔離cache邏輯大小=1132101557 bytes。這些是實際輪詢/檔案快照，瞬時未取樣峰值及未單獨量測準備CPU仍UNKNOWN。

Source regression 469項（461通過、8項native安裝相依skip）；新增方法及實際物理回歸分別記錄。最終publication gate需由實際remote byte readback與exact-head CI收據補齊，不能引用未來CI。CI不重新生成物理事件。

PR_URL: https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/20

NEXT_RECOMMENDED_STEP: 另行核准零保留事件的獨立積分／收斂與候選截斷稽核，解決B/C絕對正規化張力後再規劃新統計。


自助命令最後實際測試13個案例（help/dry-run、B/C frozen-resume、D/all complete-resume，以及events/energy/seed/process/hours/disk/kappa的拒絕路徑），全部通過；原始LHE、完整ROOT、重加權表及campaign registry SHA均未改變。新增方法測試13項通過。完整CLI收據在 `simulation/hh_signal/evidence/campaign/final_cli_validation.json`。

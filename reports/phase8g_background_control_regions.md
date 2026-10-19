# Phase8G 背景來源、Control/Sideband Regions 與物理解讀界限

## 目標與實際輸入

六個背景各自分析，不建立未驗證的物理總背景。來源身分來自 `metadata/phase8_dataset_manifest.json`：B01 bbγγ、B02 ccγγ、B03 light jjγγ、B04 ZH、B05 ttH、B06 bbγj。113檔實際來源hash audit已通過；新的完整ROOT event-loop已實讀六背景各1000筆，並與historical cutflow全stage閉合；region細分由另外的既有事件後處理產生，不能用本readiness契約代替數值。

## 方法與固定分區

Region basis維持photon+eligible-jet選擇，於≥2 tags前，把每個事件依observed native bit0分為 `TAG_0`、`TAG_1`、`TAG_GE2`；mγγ分為 `[105,120)`、`[120,130]`、`(130,160]`，另保留outside分類。所有邊界明確且互斥，105–160 baseline沒有改變。事件key包含dataset，不以不同sample相同event number進行合併。0/1tag沒有兩個tagged jets，m_bb與m_HH須保持null。

三個tag groups與三個broad-mgg cells應逐事件exactly-one assignment；加outside後必須恢復整個photon/jet-eligible denominator及sumw/sumw2。使用原始1000筆source denominator，未選取事件保留zero contributions。實際region counts、加權和、ESS及missing candidate統計待原生loop產生，再由獨立數值程式驗證。


## 本次實際Full ROOT Cutflow

| Dataset | Input | Photons | Jets | Two bit0 tags | mγγ105–160 |
|---|---:|---:|---:|---:|---:|
| B01 | 1000 | 446 | 266 | 91 | 28 |
| B02 | 1000 | 378 | 241 | 7 | 1 |
| B03 | 1000 | 445 | 277 | 0 | 0 |
| B04 | 1000 | 370 | 220 | 77 | 75 |
| B05 | 1000 | 327 | 322 | 131 | 131 |
| B06 | 1000 | 2 | 2 | 2 | 0 |

以上為 `ACTUAL_FULL_DATA_READBACK`，六組皆difference=0、無invalid/skipped/duplicate events。B03與B06的final0保留proposal interval解讀，不能推成物理rate為0。

## 背景物理來源與Overlap契約

`analysis/phase8/scripts/background_contract.py` 產生15個pair的machine-readable evidence matrix。B01/B02/B03的ME flavour互異，並不表示reconstructed heavy-flavour exclusivity：parton shower的g→bb/cc能讓不同來源進入相同重建tagged區域。既有 `metadata/phase6e_source997_manifest.json` 與 flavour decomposition作為歷史ancestry證據；不能只看process名稱替所有jets決定flavour，也不能因不同檔名或seed就宣稱物理互斥。這三組標記 `POTENTIAL_DOUBLE_COUNTING`，physical addition保持blocked。

ZH與ttH以各自的H→γγ model BR恰好一次處理；ZH的Z→bb已包含在source，不能重乘。不同初始化模型的Hγγ BR數值不強制統一。B05保留production/decay spin-correlation未完整驗證限制。對resonant/continuum的共同final-state overlap/interference、matching與calibrated normalization未做完整驗證，因此標記 `OVERLAP_UNKNOWN`，不能只憑resonance名稱解除physical-addition gate。

## B06 Fake-photon Readiness

B06只有一個Born photon。既有二photon候選與final zero僅是這份sample的觀察，不能導出jet→photon fake rate，不能證明背景cross section為0。需要fake-enriched control data、明確ID/isolation定義、pT/η依賴、normalization、相關不確定度與prompt/shower/fake double-counting control。這些未提供時 `numerical_fake_rate=null`，不得用0替代UNKNOWN。含B06的pair標記 `NOT_COMPARABLE`，解讀範圍僅現有source component。

## 數值結果與驗證範圍

目前background readiness契約的15pair均沒有驗證過可物理相加。這是 `HISTORICAL_EVIDENCE_AUDIT`，不是新MC結果。真正region數值應以 `phase8_control_regions.csv`、`phase8_region_summary.json`、`phase8_background_overlap_matrix.json` 與 `phase8_fake_photon_readiness.json` 對應nativeROOT輸出。Synthetic negative tests須確認physicalsum不能因component plots或單個來源通過就解除，也不能以zero survivor解除fake gate。

## 下一步

完成各組fullROOT與region closure，逐來源比較形狀與統計支持。未來若要物理總背景或likelihood，需另有validated overlap/exclusivity、photon fake與detector calibration輸入；本Phase8不生成新事件、不補造這些條件。Physical significance、CLs與κλ interval保持 `NOT_EVALUATED`。

# Phase9A：Phase8 獨立科學審查

審查結論為 `PASS_INDEPENDENT_SCIENCE_REVIEW_WITH_PHYSICAL_BLOCKERS`。這是對既有 source、來源身分及數值方法的獨立審查，不是 physical likelihood 的核准。

審查對象固定為 Phase8 published revision `8ecd91106acb1dae065cde14f1d62867d10b073f`；實際執行的核心分析 source revision 為 `19faeaf487fb1f9b49ff00f5cf85eeeb1c949930`。逐檔比對 Git blobs，確認本次讀取的 Phase8 source 與 published revision 一致，且核心 include/src/apps/config 與 executed revision 的 bytes 相同。後來 publication commits 的內容不被倒推為當時已執行的分析程式。

獨立 reviewer：Phase9 science-review agent。簽核意義是下列檢查確實讀檔並重新計算；沒有以 Phase8 的 PASS 標籤取代檢查。可執行入口為 [review_phase8.py](../analysis/phase9/scripts/review_phase8.py)，機器可讀簽核矩陣為 `phase9a_independent_review.json`。每一列均附 evidence logical locator、實際 SHA256、檔案大小及證據範圍。

## 證據範圍

| 證據 | 本次可支持的結論 | 不能支持的結論 |
|---|---|---|
| 已雜湊且與原紀錄相符的完整 ROOT、LHE、index、truth、cards | 實際檔案可用，來源 bytes 未改變 | 單憑檔案 hash 不能宣稱重新讀過 TTree |
| Phase8 原生 ROOT readback receipts 與 canonical digest | 歷史上實際完成完整 native readback | 不是 Phase9 的新 ROOT dispatch |
| 本次獨立讀取 7,100 行 full-cohort event summaries，並直接對 InputIndex | 完整來源身分、cutflow、bit0、權重與數值關係再次計算 | persisted summary 不能取代新的 detector branch readback |
| GitHub Phase8 source/method CI 與 frozen numerical summaries | 指定 head 的 source/method/evidence regression 成功 | GitHub Actions 未重新跑完本機全部 ROOT inputs |
| Phase9 新的 targeted native extraction／ROOT histogram validation | 另由主執行器的實際收據判定 | 不得將 reference prefix 或重讀次數加進獨立來源數 |

本審查 helper 的 `fresh_native_ROOT_dispatches=0`；其獨立歷史審查收據保留模組內的 `PENDING_ROOT_ORCHESTRATOR` 標籤，沒有事後改寫。主執行器後來另外實際完成新 native readback：B01–B06 共 **6,000** entries，ROOT 6.40.04／C++20，六組 root／card／index hashes與cutflows一致，status為 `PASS_FULL_EXISTING_BACKGROUND_NATIVE_READBACK`。Signal B100/C1000的1,100來源沿用Phase8 evidence，沒有重跑signal完整event loop；因此仍是7,100個獨立來源，不是13,100。

此外，本次實際重新開啟既有Phase8 histogram ROOT，檢查 **4,052 TH1D＋616 TH2D**，canonical digest再次為 `4a8899dfde5b484d49e30438b704f81e77b648cb07d643e7360b0c181a2a9ed2`，原生命令exit0。這些新收據與13列歷史審查矩陣分開保存在execution manifest；新ROOT核對沒有新增任何物理事件。

## 完整 cohort 與 selection closure

| Dataset | 原始 N | Photons | Jets | ≥2 native tags | Final mγγ |
|---|---:|---:|---:|---:|---:|
| S01_B100 | 100 | 45 | 38 | 18 | 18 |
| S01_C1000 | 1000 | 484 | 403 | 143 | 143 |
| B01 | 1000 | 446 | 266 | 91 | 28 |
| B02 | 1000 | 378 | 241 | 7 | 1 |
| B03 | 1000 | 445 | 277 | 0 | 0 |
| B04 | 1000 | 370 | 220 | 77 | 75 |
| B05 | 1000 | 327 | 322 | 131 | 131 |
| B06 | 1000 | 2 | 2 | 2 | 0 |

獨立來源合計 **7,100**；另有 800 筆 overlapping reference-prefix readbacks，其獨立來源增量為 **0**。40 個 cutflow counts 均與凍結定義完全一致。

Baseline 維持原有嚴格 pT／η cuts、開區間 photon crack、leading photon >35 GeV、native bit0 與 inclusive 105–160 GeV diphoton window；沒有新增 baseline m_bb cut。每一個 eligible native jet 都檢查 `(BTag & 1) != 0`，合計 **19,483 jets**；沒有以 native flavour、BTagAlgo 或任意非零 tag bit 代替。

## 獨立簽核矩陣

| 檢查 | 實際方法與結果 | 狀態 |
|---|---|---|
| EXACT_PHASE8_SOURCE | published Git blobs 與讀取 source 一致，核心 source 與 executed commit 一致 | PASS |
| FULL_COHORTS | 全部 summary 行重計 7,100 originals 與 40 cutflow counts | PASS |
| SOURCE_EVENT_IDENTITY | dataset + source ordinal + native event number + hard-event SHA；另比對 HepMC SHA、InputIndex ordinal、original N；沒有 duplicate／missing joins | PASS |
| SOURCE_WEIGHTS_AND_FIXED_N_VARIANCE | 每筆 raw XWGTUP / original N；完整 N 保留 failed-cut zeros，獨立 Decimal70 centered moments | PASS |
| MODEL_BR_ONCE | 40 個 stage-accounting rows，HH／ZH／ttH 各自 model factor 一次，其他背景無 Higgs factor | PASS |
| NATIVE_BIT0 | 19,483 eligible jets 的 bit0、tag multiplicity、jet/tag-stage 邏輯 | PASS |
| SIGNAL_PDF_ALPHA_IDENTITY | B100 CTEQ6L1 one-loop、effective seed21；C1000 NNPDF23 LO two-loop、seed20261122 | PASS；不可 homogeneous pooling |
| CONTROL_REGION_PARTITION | 120 分區 summaries，由 1,769 eligible events 重建；count 與 source sumw 閉合，0／1-tag 不造 bb candidate | PASS |
| HISTOGRAM_HASH_BINDING | 4,668 objects 的歷史 canonical digest／readback receipt，ROOT bytes 與凍結 hashes 相同；每項 source N、root SHA、BR scaling 另查 | PASS_HISTORICAL_EVIDENCE；新 native 另列 |
| KAPPA_COMMON_SOURCE_COVARIANCE_AND_ESS | 6,000 ratios 對原始 1,000 hard-event identities；6 個 ESS 與 180 covariance entries 獨立重算 | PASS；2.5／5 不解鎖 |
| EMPTY_LOW_ESS_GUARDS | 空 bin ESS 仍 undefined、低 ESS flags 保留 | PASS |
| NO_PHYSICAL_SUM_AND_INFERENCE_BLOCKERS | background sum blocked、fake rate null、physical inference not evaluated、22 類 nuisance 不填零 | PASS |
| EVIDENCE_SCOPE_SEPARATION | 本機 native、歷史證據、published summaries、GitHub CI 分開標示 | PASS |

Source sampling variance 使用完整原始 cohort：

\[
\widehat{\mathrm{Var}}\!\left(\sum_i x_i\right)
=\frac{N}{N-1}\sum_i(x_i-\bar x)^2.
\]

這與單純 `sumw2` 不同。這個 variance 是既有 source proposal、shower／detector realization 下的 sample estimator；integration normalization error、conditional tag variance 與未知 official systematics 沒有未經論證就相加。固定等權 INPUT estimator 為零 sampling variance，也不代表 generator cross section 已沒有 integration uncertainty。

## 有限支持的具體結果

| κλ | Source ESS | Final ESS | 可支持的用途 |
|---:|---:|---:|---|
| −1 | 235.494846 | 43.773331 | Descriptive |
| 0 | 503.655334 | 78.309716 | Descriptive |
| 1 | 1000 | 143 | Descriptive |
| 2 | 204.589405 | 71.980943 | Descriptive |
| 2.5 | 36.694300 | 16.073571 | INCONCLUSIVE_REWEIGHTING |
| 5 | 19.544223 | 7.650124 | INCONCLUSIVE_REWEIGHTING |

26-observable source bin-quality ledger 有 7,868 個 EMPTY_BIN、3,191 個 LOW_ESS_LT10、1,202 個 LOW_ESS_LT20、2,099 個 VALID_DESCRIPTIVE_ONLY；κ ledger 有 4,086 EMPTY_BIN、3,531 LOW_ESS_LT10、1,310 LOW_ESS_LT20、240 HIGH_SINGLE_EVENT_DOMINANCE、1,603 VALID_DESCRIPTIVE_ONLY。這些 rows 跨越 stages／observables，不是獨立樣本數。沒有因 test PASS 就將低支持 bins 當作精密物理模板。

零 survivors 的 proposal acceptance 必須保留 interval；對 0/1000，單側95%上界約 0.00299125。這不是 fake-rate 或 weighted physical-background upper bound。

## 可追溯 evidence hashes

| Evidence | SHA256 |
|---|---|
| metadata/phase7e_audit.json | `facb9646c4afae0f1e3558b00cf1bbc317964c9e144430e0d9ea42502af88f75` |
| phase8_weight_accounting.csv | `4b6508f2e68a4b55c52c498a5c45c1a31bd9e04b4dd074b1717a5f3fd6535de2` |
| phase8_control_regions.csv | `471cc1efe06e0c360b7000c1e42df8f6d04e21e7a728105612ddd602b0c22b6a` |
| phase8_kappa_covariance.csv | `02ba74806fc8672bf1e44459351d5c148bd6bbe4fa1de7d24470fc3c01b9adda` |
| Phase9 native/phase9_native_readback.json | `6d46d1b76519b59c64aabb8bf7632871997f37b5f38e4a5d7e91bd71a9c979ad` |
| Histogram canonical numerical content | `4a8899dfde5b484d49e30438b704f81e77b648cb07d643e7360b0c181a2a9ed2` |

完整矩陣的每個 logical evidence locator 都帶 SHA；canonical histogram hash 包含 edges、contents、sumw2、flows、unit 與 dataset/mode 等語意，與 ROOT 檔案原始 bytes hash 分開。ROOT UUID 不是數值再現性標準。

## 未解決與下一步

B01/B02/B03 尚無經驗證的 exclusive／matching definition；B06 沒有相容且經 closure 的 fake model；官方 detector calibration 與 nuisance values/correlations 缺少；single-Higgs modeling 假設及 κ tails 仍有限。Historical C1000 不可宣稱為未來修正後的 CTEQ6L1 one-loop source。

Phase9 的新 ancestry／photon／native readback 證據可增進來源解釋，但不能自動解除上述 physical gates。任何 future matched integration 或 corrected full chain 都須另行授權並保留新 source identity；本次沒有執行。
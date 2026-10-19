# Phase9G：Physical likelihood readiness

目前結論為 `BLOCKED_PHYSICAL_INFERENCE_REQUIRED_INPUTS_MISSING`。本次沿用已驗證的 Phase8 RooFit／RooStats framework；沒有重寫 synthetic framework，沒有建立 physical signal-plus-background fit。

| 輸出 | 狀態 |
|---|---|
| PHYSICAL_TOTAL_BACKGROUND | **BLOCKED** |
| PHYSICAL_SIGNIFICANCE | **NOT_EVALUATED** |
| PHYSICAL_CLs | **NOT_EVALUATED** |
| PHYSICAL_KAPPA_INTERVAL | **NOT_EVALUATED** |
| Method-only fits | **SYNTHETIC_METHOD_ONLY** |

## 輸入與方法

依據 exact Phase8 revision `8ecd91106acb1dae065cde14f1d62867d10b073f` 的 likelihood code、Phase7E effective-configuration audit、8組 cohort/accounting、overlap／fake contracts、bin quality、κ common-source covariance 及22項 systematics readiness。Phase9A 獨立審查必須先 PASS；新 helper [readiness.py](../analysis/phase9/scripts/readiness.py) 只建立 readiness ledger，不會呼叫 physical fit。

[Phase8Likelihood.cxx](../analysis/phase8/src/Phase8Likelihood.cxx) 與其 header 為既有實作。原有 synthetic checks 支持 Gaussian／lognormal／MC-stat constraints、template validation、profile／Asimov 方法與 fail-closed policy；toy input 的存在不能供應真實 calibration、background composition 或 uncertainty。

Missing numerical input 保持 `null`。沒有因某 gate 缺少就假設值為0，也沒有因暫未提供 correlation 就設定各 nuisance 相互獨立。

## 九項必要 gates

| Gate | 狀態 | 目前證據與限制 | 解除所需條件 |
|---|---|---|---|
| Signal matched normalization | BLOCKED | B100 CTEQ6L1 one-loop／effective seed21；C1000 NNPDF23 LO two-loop／seed20261122。歷史C並非未來宣告的CTEQ6L1 one-loop target；B/C cross-run差異不是同integrand seed pull | 另行授權的 matched integration、獨立 cross-section／error 驗證、corrected full chain 與新 retained source identities |
| Heavy-flavour exclusivity | BLOCKED | B01/B02/B03 的 reconstructed phase-space sharing 或 ancestry 分類，不能證明 perturbatively consistent exclusivity | Matched/merged generation 或 validated generator-level exclusive definition 與 uncertainty／closure |
| Fake-photon estimation | BLOCKED | B06 one Born photon，final0/1000；沒有相容且經closure的 jet→photon transfer model | 對應period、energy、object/isolation、region的公開或資料導向fake calibration；含組成、prompt contamination、uncertainty與correlations |
| Single-Higgs modeling | BLOCKED | ZH／ttH 已使用各自 MODEL_BR_ONLY factor 一次；這只驗證weight convention。ttH top-decay／spin及physical normalization等假設未完整校驗 | Review production/decay/BR、topology/spin、generator/PS及normalization uncertainties |
| Detector calibration | BLOCKED | Native bit0、Delphes kinematics與readback closure是目前fast-sim實作的證據 | 相容且可追溯的 photon／trigger／jet／b-tag／pileup等 detector calibration與selection適用性 |
| Systematic nuisance values | UNKNOWN | 22類 physical value／constraint仍缺少；toy widths未填入physical ledger | 有來源、單位、rate/shape定義與validation的physical inputs |
| Nuisance correlations | UNKNOWN | 沒有process/object/bin/period間已驗證的physical correlation model | Reviewed correlation model、constraints、PSD／likelihood closure；κ statistical covariance不能替代 |
| MC bin statistical support | BLOCKED | B02 final1/1000、B03/B06 final0/1000；空及低ESS bins；κ2.5/5尾端支持不足 | 預宣告足夠支持分箱、獨立來源／rare-event interval評估及validated finite-MC likelihood |
| Signed expectation model if applicable | PASS_CURRENT_INPUTS_ONLY | 現有raw cohorts沒有negative source weights；Phase8拒絕未支援signed physical template | 若未來出現signed inputs，先驗證正確expectation model與nonnegative total rates；不得clip負bin |

八項 gates 為 BLOCKED／UNKNOWN。第九項只對目前正權重資料條件成立，不代表可接受未來 signed samples，也不解除任何其他 gate。即使未來某 gate 有進展，仍須整體 source/configuration 與 likelihood review；本次任務沒有授權 physical inference。

## 為何既有正確結果還不夠做物理 fit

1. **Normalization與selection是不同問題。** 7,100個既有來源、bit0與歷史cutflow閉合，不會讓effective PDF/αs不相同的B/C成為同一proposal。也不能從一次integration error直接保證同設定convergence。
2. **Origin分類與exclusive normalization是不同問題。** B01/B02/B03可各自畫圖與描述；尚無經驗證的exclusive prescription時，不能直接相加成total background。
3. **零存活不代表零成分。** B03/B06 final0/1000有有限proposal upper interval；B06還缺少fake transfer model。其final hist為空不能當成可忽略的physical background。
4. **統計covariance與systematic correlations是不同問題。** 六個κ vectors共用1,000來源的statistical covariance已知；它沒有定義luminosity、objects、generator或fake nuisance間的physical correlation。
5. **Toy closure只驗證方法。** Phase8的26項RooFit/RooStats checks使用synthetic inputs；不能轉換成實際HH資料的significance、CLs或κ interval。

## Validation 與 guard

獨立 test module 為 [test_phase9_science_review.py](../analysis/phase9/tests/test_phase9_science_review.py)。其中 synthetic failure-path tests 刻意檢查：missing gate、fake數值0、toy nuisance代入、擅自填correlation、signal PDF重新標籤、signed inputs、未通過review與遺漏nuisance category均被拒絕；即使目前全部權重為正，physical inference仍維持blocked。

這些是 `SYNTHETIC_METHOD_TEST`，不是新的ROOT readback。Actual source/event preservation 與 fresh native extraction 收據另列於Phase9 execution manifest。Readiness JSON逐gate附真實來源SHA256與future requirement；程式沒有呼叫MG5／Pythia／Delphes，也沒有產生任何新integral或hard events。

## Phase7I dependency 與下一步

Phase7I interface只追蹤依賴，不改程式、不build、不restart。需要的後續證據包括：corrected CTEQ6L1 one-loop matched SM integration、獨立核准的cross section與uncertainty、corrected full event chain，以及retained new event/source identities。歷史C1000保留原本配置與物理限制，不以新normalization或source silently overwrite。

可先進行的工作是審查本次truth-origin/photon/region/precision證據與公開calibration可適用性；未取得上述physical inputs前，報告只能維持exploratory與method scope。
# Phase8F 來源權重、模型 branching ratio 與 MC 統計

## 目標與實際輸入

以本次 native ROOT readback 的完整原始事件為分母，逐一分析八個資料來源。S01_B100 是不同有效設定的獨立100-event pilot；S01_C1000 是 NNPDF23 LO、two-loop alpha_s、seed20261122 的歷史1000-event source。兩者不合併。六個背景各維持自己的1000-event cohort，沒有產生新物理事件。

## 權重與選擇方法

native source index 綁定的 source_weight_pb 已為 XWGTUP_pb / N_original；不再乘 sigma/N。模型 BR 僅由原始 source contribution 套用一次。Signal 使用2 BR(H→bb) BR(H→gamma gamma)；ZH 已含 Z→bb，只乘自己的 H→gamma gamma；ttH 使用自己的 H→gamma gamma，沒有 HH factor2。identity multiplier1不宣稱物理BR=1。

| Dataset | N_original | 模型 factor | factor applications |
|---|---:|---:|---:|
| S01_B100 | 100 | 0.00265344590672 | 1 |
| S01_C1000 | 1000 | 0.00265344590672 | 1 |
| B01 | 1000 | 1 | 0 |
| B02 | 1000 | 1 | 0 |
| B03 | 1000 | 1 | 0 |
| B04 | 1000 | 0.00229653131475 | 1 |
| B05 | 1000 | 0.00229754678431 | 1 |
| B06 | 1000 | 1 | 0 |

## 實際最終選擇數值

weighted sum 為各別來源的探索性 pb estimator；不得相加為 calibrated ATLAS total background。

| Dataset | N_pass | sumw [pb] | fixed-N source SE [pb] | ESS | conditional expected count | conditional tag variance |
|---|---:|---:|---:|---:|---:|---:|
| S01_B100 | 18 | 8.25136766721e-06 | 1.7700234305e-06 | 18 | 16.2603679831 | 7.6886064375 |
| S01_C1000 | 143 | 7.23559407932e-06 | 5.60420280088e-07 | 143 | 148.876131473 | 74.7849402602 |
| B01 | 28 | 0.001854906536 | 0.000345774852069 | 28 | 30.2713031522 | 15.4660569066 |
| B02 | 1 | 0.0006274417 | 0.0006274417 | 1 | 1.31214349915 | 1.24796081949 |
| B03 | 0 | 0 | 0 | 未定義 | 0.501324516614 | 0.257369102087 |
| B04 | 75 | 1.54220115645e-05 | 1.7135568405e-06 | 75 | 76.2002634056 | 40.4724343165 |
| B05 | 131 | 0.000120145250979 | 9.79034746113e-06 | 131 | 119.824370064 | 56.4989413787 |
| B06 | 0 | 0 | 0 | 未定義 | 0 | 0 |

## 寬 mgg cut 前的雙 tag 對照

| Dataset | observed native double tags | conditional expected | conditional SD |
|---|---:|---:|---:|
| S01_B100 | 18 | 16.2603679831 | 2.77283364764 |
| S01_C1000 | 143 | 148.876131473 | 8.64782864424 |
| B01 | 91 | 99.3063072879 | 7.12105888076 |
| B02 | 7 | 4.07895913435 | 1.94447802473 |
| B03 | 0 | 0.57937150728 | 0.577235776038 |
| B04 | 77 | 77.2427612227 | 6.40132919851 |
| B05 | 131 | 122.114301754 | 7.57672580153 |
| B06 | 2 | 0.751777748745 | 0.684965738027 |

## 統計限制

x_i 已含來源1/N，未通過事件保留零貢獻。Var(S)=N/(N-1) sum_i(x_i-mean)^2，以 translated centered long-double accumulation 計算。sumw2是不同 histogram moment；不等同 fixed-N source variance。ESS=(sumw)^2/sumw2；零 second moment為null，signed weights保留符號，另列sum_absw與cancellation ratio。

observed event-sampling variance已含歷史 shower/detector/tag realization，不能隔離純generator variance。conditional estimator只對固定 reconstructed jets使用實際卡的獨立Bernoulli模型；persisted Float_t pT有storage-rounding approximation。三狀態DP直接累積P>=2，避免稀有tail由1-P0-P1相減消失。

conditional sum(w_i^2 q_i(1-q_i)) 與 analytic-mean source variance分開列出；不加回已含realized tag randomness的observed-outcome variance。conditional tag-count expectation不是conditional m_bb/m_HH分布；沒有用一個observed tagged pair代表所有可能tag組合。

N=1000零survivor的one-sided95% proposal acceptance upper約0.0029912495451。這只限制未加權Bernoulli proposal count，不是weighted cross-section或photon-fake rate上限。100fb^-1欄只按pb*1000*fb^-1換算，標記ILLUSTRATIVE_MODEL_YIELD。integration、PDF/scale、BR、full detector與overlap uncertainties沒有混成total band。

## 驗證、未解問題與下一步

獨立 Decimal70 重算所有stage/observable/bin、ESS與missing，conditional tags以完整Poisson-binomial PMF獨立驗證。共378351項比較，狀態`PASS_INDEPENDENT_DECIMAL70_STATISTICS`，證據ACTUAL_FULL_DATA_READBACK；收據SHA256 `3e20fecd989cfbe23b07f43345dff8511c7d8ef284454d0f288fe49824550016`。

B01–B03 ME/PS overlap、B04/B05 MODEL_BR_ONLY、ttH spin、B06 photon fake、signal PDF/alpha_s與detector calibration限制仍保留。未來需要獨立來源、matching及校準輸入；本次不執行新production。

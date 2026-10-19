# Phase 10F：統計精度與未來獨立來源 campaign 規劃

證據類別：`HISTORICAL_SOURCE_AUDIT`；zero-support 情境與新 proposal contract 為 `FUTURE_UNEXECUTED_PROPOSAL`。本節讀取已保留的 Phase9 數值摘要與本輪 `precision_01/`，沒有重跑 Phase8／9 全 pipeline、沒有重新讀取完整 raw events、沒有新 ME／積分／Pythia／Delphes 事件。總共仍是 7,100 個歷史 independent original sources；resampling 或同源 κ reweighting 不增加這個數字。

本輪實際產物是 **88 個 precision scenario rows、3,648 個 bin-support rows、16 個 κ support rows**。這些是固定既有 proposal 和 selection 下的條件規劃，並未建立物理總背景或 production requirement。`MATCHED_SIGNAL_NORMALIZATION=BLOCKED_PHASE7I`、`PHYSICAL_TOTAL_BACKGROUND=BLOCKED`；physical significance／CLs／κ interval 均 NOT_EVALUATED。

## 1. 需要分開的五種不確定性

| 層級 | 本輪可做的計算 | 不能從本輪推出的結論 |
|---|---|---|
| Acceptance | 固定 proposal 下 Bernoulli k/N 及 pilot CP95 interval 的 sample-size 轉換 | 改了 matching、PDF、生成 cut 後仍有相同 p；未來 achieved precision 的保證 |
| Weighted selected raw source rate | 固定 original N 的 source variance 與 selected-rate moment extrapolation | 已含 integration／BR／luminosity／matched-signal 物理 normalization 的 total error |
| Histogram-bin support | raw bin rate、含 bin-total covariance 的 normalized fraction/bin、ESS 與 tail concentration | empty/singleton 的 empirical zero variance 等於 shape 已精確測量 |
| Source proposal uncertainty | 指出 acceptance/weight moments 是否只適用歷史 proposal；設計另行 pilot/known-density contract | 由現有 histogram 倒推真實 proposal density，或保證未見尾部不重要 |
| Physical normalization | 保留 UNKNOWN／BLOCKED；不當成零 | 可相加的 physical total background、物理顯著度或 κ 信賴區間 |

增加 N 只在已知且可控制的 sampling model 下縮小 MC sampling error；不會消除 perturbative overlap、photon-fake 輸入缺失或 Phase7I normalization blocker。S01_B100 與 S01_C1000 的 PDF／alpha_s identities 不同，仍分開列示，沒有將 100＋1000 直接當作同一 proposal 的 1100 個事件。

## 2. Acceptance 與 weighted-rate 的定義

若 `N0` 個 original independent sources 中有 k 個通過固定 selection，使用 `p_hat=k/N0` 的 asymptotic Bernoulli plug-in：

```text
N_acceptance(r) = ceil[(1-p_hat)/(p_hat*r^2)].
```

這是 **total independent source N**，不是 additional N；例如 S01_C1000 的 10% 點估計為 600，不能解讀成還需新增 600。公式最低保留 N=2 以避免 sample-variance 定義退化。當 k=0，主 measured plan 為 undefined，而非 N=0 或任意有限保證。

將 Phase9 的 CP95 pilot endpoints p_low、p_high 轉為 `[N(p_high),N(p_low)]`，只是反映 pilot acceptance 不確定性的規劃 envelope，**不是**「將來達到 r 的 95% coverage guarantee」。此處重用 Phase9 已驗證 interval endpoints；獨立覆核重新計算它們到 sample-size 的非線性轉換。

對 weighted selected raw source rate，令 c_i 是已包含原 original-N denominator 的各 trial contribution，包含失敗 selection 的零貢獻，`R_hat=sum c_i`。固定 original N 的 Bessel variance 為：

```text
V0 = N0/(N0-1) * [sum(c_i^2) - R_hat^2/N0]
N_rate(r) = ceil[N0*V0/(R_hat^2*r^2)].
```

這保留原 source denominator，不能改用 final survivors 當 N0。需要新的 independent trials、相同 normalized proposal、相同 selection、finite variance 和足夠穩定的 weight-tail moments。若 R_hat=0 或 empirical V0=0，程式不回報有限 measured requirement。這也避免把「沒有觀察到變化」解讀成真實誤差為零。固定的本來源 BR factor 在 relative SE 中相消，並不表示該 BR 或 normalization 已被物理驗證。

## 3. 實際 final-selection 規劃值

以下每格為 `acceptance total N / weighted raw-source-rate total N`；所有數字均是本輪 CSV 的條件點估計，未包括物理 normalization error。

| 來源與現有 final support | r=10% | r=20% | r=30% | r=50% |
|---|---:|---:|---:|---:|
| S01_C1000：143/1000 | 600 / 600 | 150 / 150 | 67 / 67 | 24 / 24 |
| B01：28/1000 | 3,472 / 3,475 | 868 / 869 | 386 / 387 | 139 / 139 |
| B02：1/1000 | 99,900 / 100,000 | 24,975 / 25,000 | 11,100 / 11,112 | 3,996 / 4,000 |
| B03：0/1000 | undefined | undefined | undefined | undefined |
| B06：0/1000 | undefined | undefined | undefined | undefined |

八個來源均在完整 88-row CSV 中：另有 S01_B100 18/100、B04 75/1000、B05 131/1000。20% acceptance 點估計分別為 114、309、166；weighted-rate 分別為 116、309、167。它們仍然是各自來源的 sampling statements，不是可相加的 physical event yields。

B02 的歷史 20% acceptance 估計 **24,975** 被原樣保留，10% 為 **99,900**。Bessel 版本因 `N0/(N0-1)` 校正變成 25,000／100,000；這個差異不是新的物理需求或更精確測量。只有 1 個 final source，p 與 tail variance 本身非常不確定。

實際 CP95 pilot envelope 在 20% 時：

| 來源 | acceptance N_point | 由 p_high 至 p_low 的規劃 envelope |
|---|---:|---:|
| S01_C1000 | 150 | 126–181 |
| B01 | 868 | 597–1,313 |
| B02 | 24,975 | **4,473–987,435** |

B02 envelope 的跨度說明 25k 不能作保證的 production requirement。這個數字也不能直接搬到改成 4F／merged generation、改 photon cuts 或改 source proposal 的 campaign。

## 4. B03／B06 的 zero-support 情境

主 measured acceptance 和 weighted-rate plan 均保持 undefined，且 `guaranteed_precision=false`。對 N0=1000、k=0，單側 95% exact upper 為：

```text
p95 = 1 - 0.05^(1/1000) = 0.002991249545095296（保留的 Phase9 數值）
```

本輪另列三個 **假設 p**：p95、p95/10、p95/100。它們是可行性情境，不是測得的 fake rate、acceptance 或 production requirement；B03、B06 各有 12 列，共 24 列。

| 假設 | r=10% | r=20% | r=30% | r=50% |
|---|---:|---:|---:|---:|
| p=p95 | 33,331 | 8,333 | 3,704 | 1,334 |
| p=p95/10 | 334,209 | 83,553 | 37,135 | 13,369 |
| p=p95/100 | 3,342,985 | 835,747 | 371,443 | 133,720 |

兩個 zero-support 來源得到相同情境表，只因使用相同 N0 和相同假設；不表示它們的真實 p 相同。若真實 p 更小，需求可再上升；p=0 時 relative rate precision 本身無定義，因此沒有有限 guaranteed requirement。

CSV 的主 CP95 envelope 使用**雙側** pilot endpoints，其上端給出 20% optimistic N=6,765；上表則使用**單側** p95，給出 8,333。兩者 confidence construction 不同，不混成同一個 bound，也不把 optimistic endpoint 當保證。

## 5. Histogram-bin precision 與 normalized covariance

本輪 final stage 有 8 datasets × 9 observables，共 72 histograms；含 underflow／overflow 合計 912 個 bin positions，乘四個 r 目標為 3,648 rows。Flows 按 Phase9 定義仍包含於 normalization denominator；normalized value 是 fraction/bin，並未另除 bin width。

對 bin B，令 `S_B=sum c_i I_B`、`Q_B=sum c_i^2 I_B`、total T 與 Q_T 包含同一 normalization 範圍。raw-bin variance 用與 rate 相同的 original-N Bessel formula。normalized fraction `f_B=S_B/T` 的 delta variance 包含 shared-event bin-total covariance：

```text
Var_delta(f_B) = N0/(N0-1) * [Q_B - 2*f_B*Q_B + f_B^2*Q_T] / T^2.
N_shape(r) = ceil[N0*Var_delta(f_B)/(f_B^2*r^2)].
```

獨立計算器從 Phase9 bin sumw/sumw2 和 total moments 重新形成這個 identity，不只讀取 planner 已寫入的 N。當 empty、singleton、T=0 或 empirical shape variance 退化時，不輸出 finite normalized-shape plan。Singleton 的 raw rate moment 外推可以有數字，但仍是極弱的條件外推，不能當作已知 shape variance。

每個 target 下均有 **603 empty、51 singleton、258 conditional moment** bin positions；即 2,412／204／1,032 個四目標 rows。20% target 的分布如下：

| 來源 | empty bins | singleton bins | conditional moment bins |
|---|---:|---:|---:|
| S01_B100 | 69 | 18 | 27 |
| S01_C1000 | 48 | 3 | 63 |
| B01 | 55 | 10 | 49 |
| B02 | 105 | 9 | 0 |
| B03 | 114 | 0 | 0 |
| B04 | 58 | 4 | 52 |
| B05 | 40 | 7 | 67 |
| B06 | 114 | 0 | 0 |

B02 每個 observable 最多只由同一個 final source 填入一個 bin，因此九個 singleton 不是九個 independent events。B03／B06 全部 bins empty，不能藉由 normalized histogram 的 empirical zero variance 計算有限保證。

表內另保留正權重 `ESS=(sum w)^2/sum w^2`、largest fraction 與原 quality flags。ESS-based `N0/(r^2*ESS)` 僅是 inverse-variance proxy；它與完整 moment／normalized-shape 公式不同，也不是新的 independent hard count、信賴區間或尾部穩定性證明。即使 quality 是 VALID_DESCRIPTIVE_ONLY，也不解除 physical blockers。

## 6. 未來 κ_lambda=2.5、5 的支援規劃

本輪只重讀既有 κ weight summaries 和 source concentration，沒有計算新的 ME weights。兩個 κ 點共享同一批 1000 original C1000 sources；source-event identity 和跨 κ covariance 必須保留。

| κ | Input ESS | Final ESS | Input top1 abs-weight fraction | Final top1 abs-weight fraction |
|---|---:|---:|---:|---:|
| 2.5 | 36.6943 | 16.0736 | 0.151126 | 0.193904 |
| 5 | 19.5442 | 7.65012 | 0.198193 | 0.267854 |

這些 concentration 使未觀察尾部成為重要限制；ESS 不等於另外產生了 16 或 8 個 hard events。κ=5 的 final 最大單源約占 26.8%，因此少數源主導的 empirical moments 不足以提供 production 保證。

用正權重 empirical ESS 重建 fixed-original-N relative rate variance：

```text
Var(R_hat)/R_hat^2 = (N0/ESS - 1)/(N0-1).
```

保留 old-proposal moments 的條件外推如下，均為 total N：

| κ／stage | r=10% | r=20% | r=30% | r=50% |
|---|---:|---:|---:|---:|
| 2.5 Input | 2,628 | 657 | 292 | 106 |
| 2.5 Final | 6,128 | 1,532 | 681 | 246 |
| 5 Input | 5,022 | 1,256 | 558 | 201 |
| 5 Final | 12,985 | 3,247 | 1,443 | 520 |

所有 16 列維持 **INCONCLUSIVE_REWEIGHTING_CONDITIONAL_PLAN_ONLY**。例如 κ=5 Final 的 20% 3,247 只代表「若未知真實尾部可用目前 old-proposal moment 描述」時的外推；它不是可信的 production requirement，更不是 physical κ interval。

未來可另行審查 κ=2.5／5 的獨立 dedicated sources，或來自多個已知 proposal 的 balance-mixture 方法；必須先有 exact-source approval、matching/normalization readiness、有限 resource envelope、新 output directory 和 independent closure。不能先生成新 weights/events 再補授權。

## 7. Known-density importance sampling 的可行條件

保留一個目前不可執行的 `phase10_importance_sampling_contract.json`：proposal densities、normalizing constants、support 皆未驗證；physical_execution_authorized=false，new independent sources=0。

若將來共同 phase space 上的各 normalized proposal g_k 都可評估，取固定 independent allocation N_k、N=sum N_k、a_k=N_k/N，定義：

```text
q_mix(x) = sum_k a_k*g_k(x)
R_hat = (1/N) sum_k sum_i f(x_ki)/q_mix(x_ki)
Var_fixed = sum_k a_k^2 * Var_gk[f/q_mix]/N_k.
```

其 unbiasedness 需要 q_mix 在 f 非零處有 support，且 proposal normalization、filters、decays 和 target f 的 perturbative definition 一致。把各 proposal 的期望按 a_k 相加，才可還原 integral f；若密度或 normalization 未知，這個推導不能直接用。Fixed-allocation variance 要保留 proposal strata；同一 source 的多個 κ 權重則另外保留 cross-κ covariance。

這個 contract 沒有由 observed histogram frequencies 推斷 proposal density，也沒有把 B100/C1000 或非互斥 B01/B02/B03 任意 pooling。對 B03／B06 而言，仍須先建立相容 physics target 和可觀測 photon/control 定義，不能用 importance sampling 解決 fake-input 不存在的問題。Resampling、重複 shower 或同源 reweighting 不能計為新的 independent hard statistics。

## 8. 獨立 source review、算術覆核與執行界線

Planner 為 `source/precision.py`＋`scripts/precision_plan.py`；本次新增的 `scripts/validate_precision.py` **不 import 這兩個 production modules**，改用獨立 Fraction ceilings 與 Decimal80 arithmetic。小型 fixtures 已驗證 B02 plug-in／Bessel 差異、zero/degenerate guards、raw moment、normalized bin covariance、ESS、negative-weight rate 與 nonfinite rejection。

獨立 review 逐項檢查：

- 八個歷史 source identities／final counts 與 original-N denominator。
- 全 88 scenario rows 的點估計、CP endpoint 轉換、24 個 zero-p 假設和 missing physical-normalization guards。
- 全 3,648 bin rows 的 acceptance／raw-rate／normalized-shape／ESS-proxy N，含 raw Bessel 與 bin-total covariance identity。
- 全 16 κ plan rows，另由保留的 concentration summaries 重算 Input／Final 共四個 ESS identities。
- Phase9 source-file bytes/SHA-256、沒有新增 production、physical gates 及 unknown proposal densities。

主代理已在 sequential resource ledger 實際完成 independent audit，結果為 **PASS_INDEPENDENT_PRECISION_ARITHMETIC_WITH_LIMITS**：42,078 checks、0 errors；完整覆核 88 scenarios（含 24 zero-p 情境）、3,648 bins、16 κ rows 和四個 ESS identities。實際 receipt 為 `/home/btu/simulations/hh_phase10/run_01/phase10_precision_independent_review.json`，SHA-256：`930a49363b3bb24cfa69cca2f368ea84e661babb83845b6b657ace107097303d`。以下為其 source-only CLI；重跑須使用新的 output filename：

```text
python3 analysis/phase10/scripts/validate_precision.py --plans /home/btu/simulations/hh_phase10/run_01/precision_01 --phase9 /home/btu/simulations/hh_phase9/run_01 --output FRESH_JSON
```

本次 review 沒有把同一個 report 看兩次算成 independence，也沒有宣稱外部獨立人員簽核。這個算術 audit 只證明既有 moments 到條件規劃的轉換；不能驗證 future proposal tails、matching、fake rate 或物理 normalization。

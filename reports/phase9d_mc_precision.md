# Phase9D：有限 Monte Carlo 支持與未來樣本規劃

目前資料足以量化既有 proposal 的選取與有限樣本限制；不足以把稀有背景視為精密 physical template。特別是 B02 final 僅1個來源，B03／B06 final沒有存活事件，不能宣稱背景為零。

## 輸入、範圍與實際執行

固定 Phase8 published revision `8ecd91106acb1dae065cde14f1d62867d10b073f` 的完整 persisted-event summaries、source weights、original-N與frozen edges；共7,100個獨立來源。新 native background readback另外實際驗證6,000個B01–B06 entries；signal1,100來源沿用Phase8。沒有新ME、integral、hard events或shower/detector production。

程式為 [phase9_statistics.py](../analysis/phase9/scripts/phase9_statistics.py) 與 [phase9_regions.py](../analysis/phase9/scripts/phase9_regions.py)。本報告採主執行器實際完成的 **statistics_02** 結果。初次statistics與receipts保留；僅修正Wilson的數學0/1端點，以及使用Decimal ceiling避免B02 30%規劃因floating-point向上誤差多算1個事件（11101→11100）。歷史Phase8資料與報告未變。

## 方法與誤差意義

每一階段先用真正的unit-event counts計算proposal acceptance \(\hat p=k/N\)、Wilson95與central Clopper–Pearson95 intervals。Clopper–Pearson透過獨立incomplete-beta continued fraction＋bisection求值；沒有將ESS當成binomial N。

Source contribution \(x_i=\mathrm{XWGTUP}_i/N_{original}\) 已包含一次original-N normalization；失敗cut的事件仍在cohort內，以0 contribution進入：

\[
\widehat{\operatorname{Var}}(S)=\frac{N}{N-1}\sum_i(x_i-\bar x)^2,
\quad S=\sum_i x_i.
\]

MODEL_BR_ONLY數值再乘該process自己的BR factor一次，variance乘factor平方。Integration cross-section error、conditional tag variance及未知systematics沒有加進本表。這是既有來源proposal與已實現shower/detector下的sampling診斷，無法由單次detector realization獨立拆出純generator及detector variance。

Observed0的empirical variance estimator可等於0；其coverage不能由這個數值推論。對0/1000，central95% CP interval為 \([0,0.00368208390]\)，單側95%上界為 **0.00299124955**。這是proposal acceptance bound，不是physical cross-section或jet→photon fake-rate bound。

## Final selection 的實際支持

| Dataset | k/N | Wilson95 | Central CP95 | MODEL_BR_ONLY或raw source sumw ± sampling SE（pb） | Relative sampling SE | ESS／最大來源占比 |
|---|---|---|---|---|---|---|
| S01_B100 | 18/100 | [0.117002,0.266674] | [0.110311,0.269477] | 8.25137e−6 ±1.77002e−6 | 21.45% | 18／5.56% |
| S01_C1000 | 143/1000 | [0.122667,0.166065] | [0.121879,0.166247] | 7.23559e−6 ±5.60420e−7 | 7.75% | 143／0.70% |
| B01 | 28/1000 | [0.0194423,0.0401702] | [0.0186847,0.0402149] | 1.85491e−3 ±3.45775e−4 | 18.64% | 28／3.57% |
| B02 | 1/1000 | [0.000176546,0.00564256] | [0.0000253175,0.00555892] | 6.27442e−4 ±6.27442e−4 | **100%** | **1／100%** |
| B03 | 0/1000 | [0,0.00382676] | [0,0.00368208] | 觀測estimator=0；不能推論背景為零 | undefined | undefined |
| B04 ZH | 75/1000 | [0.0602518,0.0930009] | [0.0594461,0.0931084] | 1.54220e−5 ±1.71356e−6 | 11.11% | 75／1.33% |
| B05 ttH | 131/1000 | [0.111493,0.153332] | [0.110698,0.153501] | 1.20145e−4 ±9.79035e−6 | 8.15% | 131／0.76% |
| B06 | 0/1000 | [0,0.00382676] | [0,0.00368208] | 觀測estimator=0；fake model缺少 | undefined | undefined |

上表各process分開列示；沒有physical B01+B02+B03 sum。ZH的Z→bb已在source，ZH／ttH使用各自H→γγ model factor；HH使用自己的2BRbbBRγγ。這些仍是MODEL_BR_ONLY／exploratory conventions。

## Stage／bin與tail診斷

五階段、九個requested observables共有 **4,560 bin-quality rows**：2,379 EMPTY_BIN、1,039 LOW_ESS_LT10、447 LOW_ESS_LT20、695 VALID_DESCRIPTIVE_ONLY。Rows跨stage／observable，不能當成新的獨立來源數。每一列保留N、sumw、sumw2、fixed-N variance、ESS、最大來源占比及normalized-bin variance。

40個source-tail summaries另列top1／5／10 absolute-weight fractions及dominant source ordinals/SHA。當前未重加權cohorts在各process內等權；B02 final的一個事件支配100% sumw。跨process raw cross-section差異不能直接解讀為可物理相加的組成。

κ reweighting只重用C1000的1,000個hard sources：

| κλ | Source ESS | Final ESS | Source top1／top5 | Final top1 | 判斷 |
|---:|---:|---:|---|---:|---|
| −1 | 235.495 | 43.7733 | 4.65%／9.45% | 9.24% | Descriptive |
| 0 | 503.655 | 78.3097 | 2.47%／5.38% | 5.67% | Descriptive |
| 1 | 1000 | 143 | 0.10%／0.50% | 0.70% | Descriptive |
| 2 | 204.589 | 71.9809 | 5.99%／9.28% | 7.44% | Descriptive |
| 2.5 | 36.6943 | 16.0736 | 15.11%／25.13% | 19.39% | **INCONCLUSIVE_REWEIGHTING** |
| 5 | 19.5442 | 7.65012 | 19.82%／35.68% | 26.79% | **INCONCLUSIVE_REWEIGHTING** |

6,000 reweight rows不是6,000獨立事件。排序cumulative concentration保留source identity；不以更細分箱或平滑掩蓋dominant tails。未產生新ME。

## 明示假設的未來樣本規劃

以下只是**相同IID source proposal、相同selection、unweighted Bernoulli acceptance**下，達到acceptance估計之目標relative SE \(r\) 的asymptotic規劃：

\[
N_{plan}=\left\lceil\frac{1-p}{p r^2}\right\rceil.
\]

這是全新獨立campaign所需的總N估計，不是本次啟動生產的指令，也不是保證值。若未來使用matched configuration／不同proposal、fake transfer weights或shape-bin精度目標，必須重新規劃。CP95 acceptance上下限映射出的range只描述pilot p的不確定性，不代表未來precision有95%保證。小N／低expected-success情境尤其不能把此asymptotic式當成coverage證明。

| Dataset | 目標20%：point N [CP-envelope範圍] | 目標30% | 目標50% |
|---|---:|---:|---:|
| S01_C1000 | 150 [126,181] | 67 [56,81] | 24 [21,29] |
| B01 | 868 [597,1313] | 386 [266,584] | 139 [96,211] |
| B02 | **24,975 [4,473,987,435]** | **11,100 [1,988,438,860]** | **3,996 [716,157,990]** |
| B04 | 309 [244,396] | 138 [109,176] | 50 [39,64] |
| B05 | 166 [138,201] | 74 [62,90] | 27 [23,33] |
| B03／B06 | point／conservative上限均未定義 | 同左 | 同左 |

B03／B06的p=0估計無法提供finite measured planning guarantee。若**另外假設**真實p恰為單側95%上界、其1/10、其1/100，20% relative-SE式分別給8,333、83,553、835,747 events；這三個p是假說，不是量得的值，亦不校準B06 fake背景。完整42筆planning rows保留這種區別。

## Validation與evidence

25項synthetic numerical／failure-path tests通過，包括CP edge／symmetry、zero-survivor guards、fixed-N zeros、bin-total covariance、BR shape cancellation、null candidate與signed/cancellation policy。ROOT 6.40.04另以TEfficiency Clopper–Pearson對 **33 cases／66 endpoints**獨立核對，largest absolute difference **1.19904e−14**，status `PASS_INDEPENDENT_ROOT_BINOMIAL_REFERENCE`。這是實際acceptance counts的數值方法cross-check，不是新事件production。

| statistics_02 evidence | SHA256 |
|---|---|
| phase9_rare_event_precision.csv | `16dab8fd42b0ab9f70eaeae877a94be09a0a41f4368a0dff4614dc17d2372c87` |
| phase9_mc_planning.csv | `f0490d48cd487c767360a3aaf8a3b20cee5bd731dbbf65c702c5a4294d732da5` |
| phase9_binomial_reference.json | `63e1f0b305fa72babd36d82ede489ad0c20de0459710777a736d232c62cde443` |
| phase9_statistics_manifest.json | `02880b79b21e3e0455c2463c76ef8a1e4a6792f1689184e726a9bb46ff92fb06` |

下一步是先審查proposal／exclusivity／fake與matched signal dependencies，再設定未來獨立樣本與合適分箱的precision目標。本任務沒有啟動任何新MC production，也沒有計算physical significance、CLs或κ interval。
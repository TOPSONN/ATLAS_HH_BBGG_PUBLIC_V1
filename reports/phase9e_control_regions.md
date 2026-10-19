# Phase9E：Control regions、獨立背景與shape comparisons

實際120個互斥regions的event counts與source sumw全部閉合；不存在把0／1-tag區域補成零質量bb pair的情況。Shape comparisons只能描述現有各process的有限樣本；沒有physical total background、同資料最佳化的獨立驗證，或physical significance。

## 輸入與不變的baseline

使用Phase8完整7,100來源summaries、原始weights、original-N、`selection_v1.json`、`regions_v1.json`與frozen histogram edges。九個observables為 mγγ、m_bb、m_HH、ΔR_bb、ΔR_γγ、pT_γγ、pT_bb、reconstructed jet multiplicity及native bit0 tag multiplicity。

`02_TWO_JETS`是既有photon＋jet selection後的eligible denominator；不先要求雙tag。以native bit0 tag數分成TAG_0／TAG_1／TAG_GE2，再按mγγ分為：[105,120) LOW、[120,130] HIGGS、(130,160] HIGH、OUTSIDE_MGG，以及顯式保留的UNDEFINED_MGG。最後一類目前count皆0，但不是省略null狀態的理由。原baseline的105–160 GeV final window、物件cuts與無m_bb cut保持不變。

## 實際event-count與weighted closure

| Dataset | Eligible | TAG_0／TAG_1／TAG_GE2 | LOW／HIGGS／HIGH／OUTSIDE | Partition source sumw（pb） |
|---|---:|---|---|---:|
| S01_B100 | 38 | 5／15／18 | 0／38／0／0 | 0.00656488 |
| S01_C1000 | 403 | 62／198／143 | 2／401／0／0 | 0.007684807 |
| B01 | 266 | 45／130／91 | 21／18／37／190 | 0.017621612092 |
| B02 | 241 | 194／40／7 | 29／12／35／165 | 0.1512134497 |
| B03 | 277 | 271／6／0 | 29／11／30／207 | 2.6139260397 |
| B04 | 220 | 35／108／77 | 0／216／0／4 | 0.01969836 |
| B05 | 322 | 50／141／131 | 2／312／2／6 | 0.128536604 |
| B06 | 2 | 0／0／2 | 0／0／0／2 | 0.131766172 |

合計1,769個eligible events。每一事件恰屬一個tag×mass partition；120 rows涵蓋每dataset的3×5組合，包括empty regions。各dataset的partition count及source sumw均與其自身eligible cohort一致，MODEL_BR_ONLY sumw亦僅乘自己的constant factor一次。沒有跨dataset的physical sum。

## Candidate null與region means

0／1 native tags時，m_bb、m_HH、ΔR_bb與pT_bb等雙tag候選量保持undefined。以C1000為例，TAG_0 Higgs-like有62事件、TAG_1 Higgs-like有196事件；兩者m_bb的N_defined皆0、missing分別62與196。程式沒有填m_bb=0或另挑untagged jets製造bb candidate。TAG_1另有2個LOW-sideband事件；全TAG_1計198個，並不與Higgs-like的196混用。

1080筆region-observable summaries記錄defined／missing／invalid、weighted mean與fixed-original-N delta SE，另列unweighted median與範圍。實際defined mean有316筆，其餘明確undefined；invalid counts皆0。

以下只比較 **TAG_GE2＋HIGGS-like** region，所有質量單位均為GeV；誤差為source sampling的delta-method SE，不是mass resolution或detector calibration uncertainty。

| Dataset | N／ESS | mean mγγ ±SE | mean m_bb ±SE | mean m_HH ±SE |
|---|---:|---:|---:|---:|
| S01_C1000 | 143 | 124.8668 ±0.1018 | 106.5729 ±2.7921 | 439.2307 ±12.1049 |
| B01 | 4 | 122.7663 ±0.9136 | 259.1019 ±76.5235 | 444.9943 ±68.0040 |
| B04 ZH | 75 | 125.0170 ±0.1362 | 77.0356 ±2.9059 | 357.7834 ±15.8221 |
| B05 ttH | 129 | 124.9092 ±0.1043 | 186.6524 ±11.7521 | 448.8955 ±16.4476 |

B01此區域只有4來源，單一來源占25%，均值與誤差不能支持精細shape校準。ttH此區域129事件，與較寬105–160 GeV final的131事件是不同denominator。ZH／ttH的Higgs-like diphoton形狀與signal接近，符合這些source包含H→γγ的定義；這個descriptive觀察不構成physical總背景模型。

Signal standalone distributions採INPUT階段的「候選量可定義」集合：C1000 mγγ為484、m_bb為305、m_HH為143。Pair comparisons採FINAL_MGG。這些階段及candidate定義不同，不把INPUT m_bb均值112.091GeV與TAG_GE2／HIGGS均值106.573GeV當成矛盾。

## Normalized-bin uncertainty

令 \(B_b=\sum_i w_i I_{ib}\)、\(T=\sum_i w_i\)、\(f_b=B_b/T\)。Denominator包含所有defined events及underflow／overflow；missing candidates不當作zero mass填入。Normalized-bin variance使用：

\[
\widehat{\operatorname{Var}}(f_b)=
\frac{1}{T^2}\widehat{\operatorname{Var}}\left[\sum_iw_i(I_{ib}-f_b)\right],
\]

右側variance採完整original-N centered estimator，failed selection與missing candidates的contribution為0。此式包含bin-total covariance；不是把原始TH1 Sumw2單純除以T²。Weighted mean對應influence為 \(w_i(x_i-\bar x_w)\)，同樣保留original cohort。

Unit-area值是**每bin的fraction**，並非每GeV密度；nonuniform edges下若繪density，value與SE都必須再除bin width。Flow fractions保留而不隱藏。若signed denominator空或cancellation不適定，value／variance保持null；負內容不被clip為0。

Empirical empty-bin source variance可能為0；這不保證該bin真實rate為0。B03／B06 final整個shape沒有defined denominator，因此全部normalized values與errors為null。B02 final只有一個來源，normalized ratio的empirical variance也可能出現0；它仍有ESS=1／100% dominance標記，不能把這種點看成精確shape。

## Descriptive shape結果

共864筆signal-vs-one-background comparisons，包含54個final pairs，以及相同tag×mass region內的comparisons；其中128筆defined、736筆因empty／null／cancellation而undefined。每筆保留兩邊N、ESS、最大來源占比。沒有B01+B02+B03 summed curve。

以下為FINAL_MGG，frozen bins與flows共同計算的Jensen–Shannon divergence（natural log）／binned CDF sup distance：

| Background | mγγ JS／CDF distance | m_bb JS／CDF distance | m_HH JS／CDF distance |
|---|---|---|---|
| B01 | 0.554365／0.571429 | 0.382720／0.595405 | 0.103672／0.166084 |
| B02 | 0.693147／1.000000 | 0.656247／0.972028 | 0.378991／0.489510 |
| B03 | undefined | undefined | undefined |
| B04 | 0.002874／0.045781 | 0.240539／0.618648 | 0.135247／0.369417 |
| B05 | 0.006075／0.018096 | 0.171983／0.453638 | 0.048458／0.145092 |
| B06 | undefined | undefined | undefined |

JS／CDF distance只描述這些binned empirical distributions，不是KS p-value、獨立nonparametric confidence interval、分類performance或physical sensitivity。B02最大JS與CDF distance來自單一事件的極端支持不足，不能當成完美區分。

逐bin signal/background shape ratio只在background denominator正且定義時給值。不同dataset source cohorts視為獨立proposal時，ratio variance採delta propagation；零background bin留null，沒有補epsilon。相同事件的tag／mass partitions與跨κ hypotheses不藉此宣稱相互獨立。

## Validation、可追溯輸出與限制

25項synthetic methods／negative guards通過：nonuniform/flow normalization、bin-total covariance、constant BR cancellation、null pair、exact mass boundaries、signed denominator／negative probability shape、empty bins與zero ratios等。主執行器已實際完成144份histograms對既有ROOT數值CSV的 **5,472項** sumw／sumw2／normalized fraction核對（含flows），exit0；源ROOT另外已完成native canonical readback。Plot-provenance收據綁定plot-data SHA `4ec74e50dcd66c94f7a314ec82316b51cf47a08208ecc68fa966f9439f093bd5` 與Phase8 ROOT histogram CSV SHA `2ac15f0de59cf0cf0c97e52119b63f2e28eda48c78c5f93f0768d5d107ba9511`。這份核對確認數值來源；其後獨立Decimal70 validator已實際PASS：144 histograms、1,824 flow-inclusive bins、40 stage rows及120 regions，共12,904項比較；同時驗證normalized variance與raw／BR-weighted closure，沒有匯入production statistics helpers。其收據為`independent_statistics_validation.json`（SHA256 `b25128faad66cae339134fbc375b2ab123d350279a68117d948abcb69eece19d`）。本Python module與validator都沒有dispatch新ROOT loop。

| statistics_02 evidence | SHA256 |
|---|---|
| phase9_region_diagnostics.csv | `e52ac09f437519ecd3cf3b276599ed96cfac01183149380fb5ffb3244000da02` |
| phase9_region_observables.csv | `13b562f7ab47a88cdc3f9191aac6159dc4d2fc22541a861e2070f0874b1da5d4` |
| phase9_shape_metrics.csv | `24a1ec5ae7e2f090311517e07b33633e67c23050d32845761898e4ba131e0aa8` |

完整local `phase9_plot_data.json`供ROOT plots，保留144個INPUT／FINAL histograms、flow／missing／ESS／error semantics；不將完整local event dumps推上GitHub。Bounded CSV／source依本次publication manifest選取。所有PDF／PNG仍需另外的exact-version使用者publication approval。

下一步是先完成heavy-flavour exclusivity、photon fake estimation、single-Higgs modeling與detector/systematic calibration的科學驗證，再設計獨立precision campaign／fit bins。不能利用同一小樣本挑cut後，把改善當成獨立驗證的sensitivity。
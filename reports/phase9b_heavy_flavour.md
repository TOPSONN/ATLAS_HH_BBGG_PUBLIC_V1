# Phase9B：重味背景來源鑑識與可相加性限制

本次從既有 B01、B02、B03 各 1000 個獨立 source events，實際連結原始 LHE、完整 Pythia diagnostics、HepMC graph 與新一次 native ROOT object readback。結果確認：light-jjγγ 的 Born outgoing jets 沒有 b/c，仍可經 shower 產生重味、重味 hadrons 與 native Flavor=5 jets；因此樣本名稱不能當成重建 flavour 的互斥分類。本結果沒有建立可物理相加的 B01+B02+B03 模型。

`ME_PS_OVERLAP = OVERLAP_UNRESOLVED_REQUIRES_MATCHED_GENERATION_OR_VALIDATED_EXCLUSIVE_DEFINITION`。

## 輸入、實際執行與來源身分

基底為 Phase8 `8ecd91106acb1dae065cde14f1d62867d10b073f`。分析沿用 Phase8 已驗證 reader、weights 與 baseline cuts。最終數字取自 `origins_03`，其執行前後 classifier、graph、driver source hashes 相同。前兩次 existing-data 診斷輸出留存，沒有覆寫。第一次診斷發現 incoming-HF 與 outgoing-HF 的同 PID 母子不能被當成 shower copy 而刪除；修正後明確區分 status21 incoming ME record、status23 outgoing ME record，以及真正 shower heavy-line births。最終 classifier SHA256：

`d489574df298c1dee54cbf3eed3f40d6cb97382e05e33e57a750c33c7148363e`。

每一事件以 dataset、one-based source ordinal、原始 LHE event SHA256、HepMC event SHA256 及 native event number 交叉綁定。Pythia ordinal 不被當成 HepMC barcode；原始 Pythia 與 HepMC 以 signed PID、converted status、完整 binary64 p4/generated-mass tuple 及可核對母節點連結建立關係。

| Dataset | Process | 獨立來源數 | 完整 Pythia records | Unique exact tuple mapping | Ambiguous/unmapped records |
|---|---|---:|---:|---:|---:|
| B01 | bbγγ | 1000 | 426370 | 426370 | 0 |
| B02 | ccγγ | 1000 | 468551 | 468547 | 4 |
| B03 | light jjγγ | 1000 | 470232 | 470230 | 2 |

6 個 ambiguous records 沒有強配。Heavy-flavour ancestry 使用具有實際 mothers/daughters 的原始 Pythia graph；photon roots 與 native HepMC 的映射只使用已證實的 tuple matches。全部 3000 事件 native eligible-jet flavour reproduction 無不一致、無 radius-boundary ambiguity；這不等同所有 hadron 的唯一 perturbative endpoint 都可知道。

## 明確的分類定義

- **ME outgoing flavour**：原始 LHE status1 outgoing quarks/gluons。B01 每事件有 b/bbar，B02 每事件有 c/cbar，B03 outgoing jets 均為 light/gluon。這個說法不排除初態 PDF 含 charm。
- **ME incoming/outgoing records**：原始 Pythia abs(status)=21/23，各自記錄，不稱為新增重味粒子 births，也不因相同 PID 的母節點而刪掉 outgoing hard record。
- **Shower heavy-line birth**：原始 abs(status)41–59 的 b/c record，且沒有直接同 signed-PID 母節點。後續 shifted copies 不重複計為 births；這是可驗證的 record 定義，並非所有可能 ISR heavy-flavour 機制的完整計數。
- **直接 gluon splitting 證據**：共同 gluon 母節點與正、反重味直接 daughters 均滿足明確 shower-status 條件。此保守定義沒有把所有 common ancestors 都叫作 splitting，也不把結果當作 merging prescription。
- **Hadron flavour**：原始 Pythia ParticleData 的 terminal b/c-hadron flags。每個 terminal hadron 只給最近 eligible jet，strict ΔR<0.4，等距保留 ambiguous；b priority over c，B_c flags 保留 inclusive。Terminal charm 可來自 bottom-hadron decay cascade，不是獨立 prompt-cc rate。
- **Hard/shower cone labels**：hard outgoing partons／abs(status)41–59 shower parton records 的 ΔR≤0.4 any-cone labels；gluon priority 最低，最高 quark |PID| 優先。它們是不同層級的診斷，不取代 native flavour。
- **Native flavour/tag**：實讀 `Jet.Flavor` 與 `(BTag & 1)!=0`。Native association 使用原始 Delphes parton-array acceptance/max-PDG 定義，保存 Float_t jet axis 的 2×10⁻⁶ angular envelope。沒有改 flavour、重抽 tags 或乘第二次 tagging probability。

Hard0 表示沒有符合該 cone 的原始 hard parton；hadron0 表示沒有被分配的 terminal heavy hadron，不能把兩者當作「沒有任何物理來源」。多母節點 string ancestry 不能證實唯一 bottom endpoint；每個 jet 的 `sole_hadron_endpoint` 保持 `UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED`。

## 每個 process 的實測來源組成

下表的單位是 **含至少一個指定證據的原始事件數／1000**。不同 origin flags 可以同時成立，不能把欄列相加成互斥機率。

| Evidence | B01 | B02 | B03 |
|---|---:|---:|---:|
| 原始 outgoing ME bottom/charm/light 分類 | bottom:1000 | charm:1000 | light/gluon:1000 |
| 有 incoming-HF ME record | 58 | 69 | 6 |
| 有 shower bottom-line birth | 53 | 36 | 49 |
| 有 shower charm-line birth | 170 | 211 | 183 |
| 有直接 g→heavy-pair 證據 | 211 | 240 | 220 |
| 有 terminal bottom hadron | 1000 | 36 | 49 |
| 有 terminal charm hadron | 1000 | 1000 | 221 |
| 有 native bottom eligible jet | 860 | 13 | 18 |
| 有 native charm eligible jet | 38 | 902 | 62 |
| 有未分類 heavy-quark birth | 0 | 0 | 0 |
| Terminal-hadron nearest-jet assignment ambiguity | 0 | 0 | 0 |

ME outgoing heavy records 合計為 B01:2000、B02:2000、B03:0；incoming heavy records 合計為 116、138、12；shower heavy-line births 合計為 559、628、501。Record 總數與含該類型的事件數是不同量。

以 shower bottom flag 為例，各來源的實測概率與 95% Wilson interval、raw source-weighted contribution 如下。Intervals 是 proposal-level event probability，SE 是完整 original-N source sampling SE；均不含 generator integration error 或官方 detector/model systematics。

| Dataset | k/N | Wilson95 probability | Raw contribution ± MC SE [pb] |
|---|---:|---|---|
| B01 | 53/1000 | [0.0407465,0.0686746] | 0.003511073086 ± 0.000469563337 |
| B02 | 36/1000 | [0.0261156,0.0494357] | 0.0225879012 ± 0.003698114912 |
| B03 | 49/1000 | [0.0372610,0.0641907] | 0.4623912489 ± 0.064449429961 |

B03 的 4.9% 是這個既有 proposal/shower contract 的診斷頻率；不能轉稱「jjγγ 對真實 ATLAS 的 b-background contamination」。

## 相同選擇下的重建相空間

Baseline 未改：leading/subleading photons 的 pT>35/25 GeV、|η|<2.37、排除開 crack；eligible jets pT>25 GeV、|η|<2.5；native bit0；final 105≤mγγ≤160 GeV；沒有 baseline mbb cut。

| Dataset | INPUT | TWO_PHOTONS | TWO_JETS | TWO_BTAGS | FINAL_MGG |
|---|---:|---:|---:|---:|---:|
| B01 | 1000 | 446 | 266 | 91 | 28 |
| B02 | 1000 | 378 | 241 | 7 | 1 |
| B03 | 1000 | 445 | 277 | 0 | 0 |

在 `02_TWO_JETS` cohort：

| Dataset | Eligible events | Eligible jets | 0/1/≥2 native-tag events | Native-b events | Native-c events | Shower-bottom events |
|---|---:|---:|---|---:|---:|---:|
| B01 | 266 | 657 | 45 / 130 / 91 | 263 | 10 | 20 |
| B02 | 241 | 580 | 194 / 40 / 7 | 5 | 236 | 12 |
| B03 | 277 | 691 | 271 / 6 / 0 | 3 | 28 | 11 |

Native-b event fractions within this stage 為 98.8722%、2.07469%、1.08303%。這些數字直接顯示不同 Born processes 可進入同一 photon/jet selection 並呈現 native heavy flavour。Stage-denominator fractions 與 original-N acceptances 分列保存，沒有混用。

對同批 eligible jets，比較不同 flavour 層級的 object counts（這不是獨立 jets 的 binomial measurement）：

| Dataset | Hard cone b/c/other | Shower-record cone b/c/other | Heavy-hadron b/c/no-heavy | Native b/c/other |
|---|---|---|---|---|
| B01 | 410 / 0 / 247 | 474 / 11 / 172 | 464 / 15 / 178 | 484 / 10 / 163 |
| B02 | 0 / 339 / 241 | 6 / 428 / 146 | 6 / 418 / 156 | 6 / 435 / 139 |
| B03 | 0 / 0 / 691 | 4 / 31 / 656 | 2 / 33 / 656 | 4 / 31 / 656 |

Hard other 包含 no-cone-match；native other 包含 Flavor0。B01 native Flavor0 有2 jets、B03有1 jet，未假裝全部都有已分類 parton candidate。完整 cross-class composition、weighted jet multiplicities、event-clustered ratio SE 皆在 CSV。各 jet 共享 source event，沒有把同事件 jets 當成額外獨立來源。

Photon/jet kinematics 也在相同 stage 實讀：

| Dataset | Mean leading γ pT | Mean subleading γ pT | Mean mγγ | Mean scalar HT | Mean native stored-jet multiplicity |
|---|---:|---:|---:|---:|---:|
| B01 | 101.6995 | 48.9964 | 142.6474 | 339.2158 | 2.7180 |
| B02 | 81.4046 | 44.6993 | 120.4084 | 296.7324 | 2.7178 |
| B03 | 107.9420 | 51.5376 | 149.6397 | 360.4575 | 2.8231 |

動量、質量單位為 GeV；最後一欄為既有 Phase8 observable 的 native stored-jet count，與上表有 acceptance cuts 的 eligible-jet count 不同。這些是有限樣本 descriptive means，不是獨立優化 cuts。B03 在此 cohort 的 ΔRbb defined0、missing277，mean/min/max 保持 null。

## 可追蹤的稀有事件

B03 在 TWO_JETS cohort 的三個 native-bottom events 為 170、971、997，各只有一個 observed native bit0 tag：

| Source index | Source SHA256 | Native-b 與 terminal-hadron cone 診斷 |
|---:|---|---|
| 170 | `22cca6b9baee9deb3307fd3eeb6a81fc254ab0a1b9ec70d0b717ebfa82be9bc1` | 一個 native5 jet；最近 terminal heavy-hadron label4 |
| 971 | `60f4b0bb85a70b18eb727a8213aa56eb4d3feb9c691e3cec6aa56a1b1a0fa5f5` | 一個 native5 jet；沒有 strictR0.4 terminal heavy-hadron assignment |
| 997 | `322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8` | 兩個 native5/hadron5 jets；observed tags1/0；直接 g17→bb |

Source997 的 hard/shower/hadron/native labels 分別維持 `[21,2,0,0,0]`、`[5,2,21,21,5]`、`[5,0,0,0,5]`、`[5,2,21,21,5]`，與既有 Phase6E 鑑識獨立 regression 一致。這些 witness 沒有被改寫或補抽 tag。

B02 的 source82 出現兩個 native5/hadron5 tagged jets、直接 g24→bb，通過 TWO_BTAGS 但未通過 final mγγ。唯一 final survivor 是 source481，hard ccγγ，兩個 tagged eligible jets 均 native4/hadron4；其 source SHA256 為 `2f304841fd3f7c2b6dae65c9a4d3f55cc2cc42cd0a4ed421a3875aeeee7aec1b`。不能因過去一個 source82 具有 shower bottom，就把所有 ccγγ tags 稱為 bottom。

## 權重、誤差與 bounded evidence 字典

所有此報告的 contributions 採原始 `XWGTUP_pb/N_original` 一次，三個 continuum samples 沒有 Higgs BR factor；沒有追加 σ/N、tag efficiency 或 luminosity。B01/B02/B03 原始 contribution 分別為每事件 0.000066246662、0.0006274417、0.0094365561 pb。三者保留各自 source normalization，未相加成 total background。

CSV 的 `events`、`original_N`、`event_fraction` 以完整 original cohort 為 denominator；`within_stage_*` 以該 stage cohort 為 denominator。`sumw_pb`、`sumw2_pb2`、`source_sampling_variance_pb2`、`source_sampling_se_pb` 使用 event units，包含未通過者的零 contribution。Variance 為 `N/(N-1)*(Σxi²-(Σxi)²/N)`，原生計算使用 centered accumulation；獨立驗算使用 Decimal70。`ESS=(Σxi)²/Σxi²`，空類別 ESS=null，不能當成有無窮精度的零。

Cross-class object rows 的 `weight_scope` cell 是空白，但其 `classification_unit=SOURCE_EVENT_HAS_MATCHING_ELIGIBLE_JET`、全部 `_pb/_pb2` 欄及這份明確字典共同定義 **RAW_SOURCE_PB_NO_NEW_NORMALIZATION**。`weighted_jet_multiplicity_pb` 是 weighted object multiplicity，與 event `sumw_pb` 不同；`jet_multiplicity_event_correlated_variance_pb2`、`jet_composition_fraction_event_cluster_se` 保留同一原始事件與 ratio numerator/denominator 的 correlations，不等於 independent-jet error。這個空 metadata cell 不被補成物理 normalization。

[完整 bounded HF CSV](../analysis/phase9/evidence/phase9_heavy_flavour_origins.csv) SHA256：`efc780381f213616d93a492e707c24e66a178d3c53cc12f9694847dfa0b965ab`。逐 source graph 詳情只保留在本機；公開 summary 不含完整 raw event dump。數值來源為 [origins summary](../analysis/phase9/evidence/phase9_origins_summary.json)。

## 驗證、限制與後續必要工作

22 項 HF synthetic-method controls 驗證 ME21/23 同-PID、fresh shower birth、共同 gluon 母節點、multi-mother graph、nearest-hadron ties、native label 保留、exact tuple identity、negative weights／variance 與零 survivor 解讀；source997 fixture 是獨立的 `HISTORICAL_EVIDENCE_AUDIT`，不冒充 full ROOT readback。另以獨立 Decimal70 validator 對完整 3000-event HF cohorts、所有 CSV rows、15 個 jet-composition count/weighted partitions 與 native observed fields 逐筆核對；該項是 `ACTUAL_EXISTING_DATA_READBACK` 的數值／identity 核對，不冒稱第二套完整 graph classifier。

Final B03 的 0/1000 仍只能給 proposal-level interval；例如 one-sided95% upper `1-0.05^(1/1000)=0.0029912495451`，不是物理 cross-section、detector fake rate 或真實背景為零的證明。Generator integration error、實現的 source sampling variance、條件 tag randomness 與 detector/model uncertainties 不混成一個誤差。

Shared reconstructed phase space 與這些 ancestry witnesses 說明 **重建 flavour 不互斥**；它們本身不能證明哪個 phase-space point 在 ME/PS 展開中被精確重複計算，也不能提供合法 subtraction/stitching weights。原始 run 設定的 ME/PS matching/merging 為關閉狀態，尚無可驗證的 generator-level exclusivity contract。

因此 physical B01+B02+B03 sum 維持 blocked。下一步應先制定並獨立審查 heavy-flavour scheme、ME multiplicities、matching/merging 或 exclusive phase-space/veto 定義，檢查 shower survival 與 normalization closure，才規劃另一個授權任務的 independent samples。本次新 ME calls、積分、新 hard/shower/detector events 全為0。
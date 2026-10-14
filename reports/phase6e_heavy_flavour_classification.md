# Phase 6E：分開記錄 hard、shower、hadron 與 native flavour

Source997 的 native Flavor=5 jets 是 light-jjgg hard process shower 後產生的 heavy-flavour jets。將整個來源樣本稱為純 light-mistag 背景會掩蓋這個既有事件。不同層級的 flavour 定義各自回答不同問題；本次保留原生 Jet.Flavor/BTag，alternative labels 僅用於診斷。

| 定義 | 本次明確規則 | Source997 eligible jets 0..4 |
|---|---|---|
| `HARD_PROCESS_FLAVOUR` | 原始 LHE outgoing quarks/gluons、jet-axis ΔR<=0.4 cone、最大 quark-PDG priority；gluon lowest；無候選0 | `[21,2,0,0,0]` |
| `SHOWER_PARTON_FLAVOUR` | 真實 Pythia quark/gluon records、absolute status41..59、ΔR<=0.4 cone、相同 flavour priority；包含 shifted records，並非獨立 birth 數量 | `[5,2,21,21,5]` |
| `HEAVY_HADRON_FLAVOUR` | distinct terminal b/c hadrons 各自只分配給最近 eligible jet，strict ΔR<0.4；ties UNKNOWN；b priority over c，inclusive B_c flags | `[5,0,0,0,5]` |
| `DELPHES_ASSOCIATED_FLAVOUR` | 實際 HepMC→Delphes parton array 與原始配置，所有允許 cone candidates 的最高 quark-PDG priority | `[5,2,21,21,5]` |

Alternative any-cone labels 與額外的 global one-to-one geometric cross-check 分開記錄。後者先最大化匹配數，再最小化 summed DeltaR；strict R0.4，object/jet identity 只能使用一次，exact equal optimums 回傳 UNKNOWN，不任意選一個。Source997 的四組 one-to-one checks 都有 unique optimum：原始 hard g/u→jets0/1；fresh b19/anti-b20→jets0/4；terminal B276/B488→jets0/4；terminal charm 526/555→jets0/4。Charm436 未在這個 one-to-one subset 中獲選，但仍留在 jet0 的完整 hadron association，沒有刪除真實 object。多個 hadrons 可共存於一個 physical jet。

原生 semantics 依據已驗證的 [Delphes 3.5.1 JetFlavorAssociation](https://github.com/delphes/delphes/blob/3.5.1/modules/JetFlavorAssociation.cc) 與 [HepMC3 reader](https://github.com/delphes/delphes/blob/3.5.1/classes/DelphesHepMC3Reader.cc)：reader 將已知 PDG 的非-stable quarks/gluons/tau 放入 `Delphes/partons`；本 card 的 PartonClassifier 再保留 absPID1..5 或21、PT>1 GeV、absEta<=2.5，排除 status=-1。它不把輸入限縮成原始 LHE hard partons，也不僅選 status2/3；status44/51/62/71 的合格 parton records 可參與原生 flavour cone。

原始 card 是 `JetFlavorAssociation DeltaR=0.4`、`PartonPTMin=1.0`、`PartonEtaMax=2.5`，輸入 `JetEnergyScale/jets`；BTagging 的 BitNumber=0。native cone 使用 `DeltaR<=0.4`，gluon 的 priority 設為0；最大 quark absolute PDG 為 jet flavour，只有 gluon 時還原成21，沒有候選時0。因此一個 cone 內的 soft-but-accepted b parton 也可壓過較高能量的 light parton；這個規則不是 calibrated heavy-hadron truth definition。

原生 association 時用的是當時完整精度 jet momentum；ROOT 只保留 Float_t PT/Eta/Phi/Mass。本次沿用 Phase6C 原有 angular quantization envelope `2e-6`，回報全部 source-derived attainable labels，不更改 radius/selection。Source997 的五個 label set 都是 singleton `[5] / [2] / [21] / [21] / [5]`，沒有 boundary ambiguity。完整 candidates、PDG/status/p4、parent/daughter、vertex keys、DeltaR 已保留在 [derived evidence](../simulation/heavy_flavour_forensics/evidence/source997.json)。

[原始 BTagging module](https://github.com/delphes/delphes/blob/3.5.1/modules/BTagging.cc) 對 `jet->Flavor` 查找 formula，沒有專屬 entry 時使用 default0；取 native momentum PT/Eta/Phi/E，並以 `gRandom->Uniform()<=formula` 設置 bit0。原始三個 probability functions 為：

| Native category | 原始 function |
|---|---|
| b / Flavor5 | `0.80*tanh(0.003*pt)*(30/(1+0.086*pt))` |
| c / Flavor4 | `0.20*tanh(0.02*pt)*(1/(1+0.0034*pt))` |
| default / light | `0.002+7.3e-06*pt` |

本次 native labels、seed610303 及 observed bit0 `[1,0,0,0,0]` 都直接讀取原始 ROOT。沒有重演或重新設定 random draws，也沒有強迫第二個 b jet 通過 tag。Conditional probabilities 使用 **persisted Float_t PT** 的原始 formula，保留先前已公開的微小儲存 rounding approximation；不聲稱回復 hidden full-precision pre-tree PT 或確切 per-draw probability。未知 flavour 在 frozen numerical module 中仍會拒絕，並未默默新增未驗證 category。

The two-tag event probability 包含全部 eligible jets 的 independent Bernoulli outcomes。Leading-tagged-pair `(a,b)` 的 probability 是 `p_a*p_b*product(1-p_k, k<b except a)`，`b` 後面的 tags 不受限制；所有 pair weights 加總回直接 DP tail。這與直接給 observed pair 乘一個 event-q 不同。Root influence module 另外按 native labels 分成 bb、bc、b-light、cc、c-light、light-light；分類基準是當下原生 flavour，而非 MG5 process name。各類 covariance 與不同 event-level decomposition 由 [influence evidence](../simulation/heavy_flavour_forensics/evidence/influence.json) 分開呈現。

對 source997，兩個 fresh perturbative bottom records19/20 的共同 mother17 是 FSR gluon；hard g7→shifted g13→g17 的精確 graph 與 HepMC mapping 相符。terminal B hadrons 的幾何近鄰與 ancestor sets 支持共同 shower production chain，但 string fragmentation 有多母粒子；sole parton endpoint attribution 保持 UNKNOWN。Hadron-level label、shower parton label 與 native label 的一致，不構成 btag calibration 或 event-level subtraction/stitching 許可。

本報告只有這個事件的實體鑑識與清楚定義的診斷標籤。三個既有 samples 的 shower 後重建 flavour mixtures、rare-event influence 與 overlap 風險需與各自原始 source cross section、ME/PS 定義及缺少 matching/merging 一起討論；不能把三者相加成官方背景，也不能因原始名稱不同就推定 reconstructed final-state exclusivity。

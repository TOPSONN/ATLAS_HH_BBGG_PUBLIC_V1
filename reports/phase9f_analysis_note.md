# Phase9 physics note：既有 HH→bbγγ 樣本與背景模型審查

本註記是 **existing-data、ATLAS-like fast-simulation exploratory analysis**。它整合實際來源／native ROOT readback、heavy-flavour與photon ancestry、有限MC統計、regions及ROOT diagnostic figures。Physical total background維持BLOCKED；physical significance、CLs及κλ interval均未計算。

固定基底 `8ecd91106acb1dae065cde14f1d62867d10b073f`；Phase8 executed core為 `19faeaf487fb1f9b49ff00f5cf85eeeb1c949930`。本次最終ancestry數字來自 **origins_03**、統計與shape來自 **statistics_02**。先前診斷、receipts與全部歷史source/events/cards/weights保留。數值權威由immutable來源、實際readback、具SHA的event/aggregate evidence到報告與figure依序建立；GitHub source/method CI不等於重跑全部本機ROOT inputs。

## 1. 物理動機與證據邊界

bbγγ final state同時提供diphoton與hadronic候選，可研究continuum γγ+jets、single-Higgs H→γγ及photon-fake成分。正式ATLAS HH搜尋亦使用此final state，但其detector calibration、data/control constraints及physical likelihood不能由本地Delphes自動繼承。[ATLAS公開HH→bbγγ論文，arXiv:2112.11876v2](https://arxiv.org/abs/2112.11876v2)

目前可回答：哪些既有source通過固定selection？Born、shower、hadron、native flavour與tag有何差別？光子lineage能證明到哪層？rare survivors與κ weights獲多少獨立來源支持？不能只靠origin labels建立perturbatively consistent exclusivity，也不能由幾何matching量到fake rate，或從同一小樣本挑cut後宣稱獨立sensitivity。

## 2. Simulation、samples與normalization

沿用既有MadGraph5_aMC@NLO3.5.16、Pythia8.317、Delphes3.5.1。分析為ROOT **6.40.04 EXACT／C++20**；沒有新ME、integration、hard/shower/detector events，沒有reinstall或Phase7I build/restart。

| Dataset | 已核對process | 原始N | 原始σ尺度（pb） | 自己的model BR factor |
|---|---|---:|---:|---:|
| S01_B100 | historical full-loop ggF HH pilot | 100 | 0.017276 | 0.002653445906720871 |
| S01_C1000 | historical full-loop ggF HH | 1000 | 0.019069 | 0.002653445906720871 |
| B01 | bb̄γγ | 1000 | ≈0.06624666 | 1，無Higgs BR |
| B02 | cc̄γγ | 1000 | ≈0.6274417 | 1，無Higgs BR |
| B03 | light jjγγ | 1000 | ≈9.436556 | 1，無Higgs BR |
| **B04** | **ZH，Z→bb̄、H→γγ** | 1000 | 0.089538 | 0.0022965313147512443 |
| **B05** | **ttH，H→γγ** | 1000 | 0.399182 | 0.002297546784308979 |
| B06 | bb̄γj，一個Born photon | 1000 | ≈65.88309 | 1，無Higgs BR |

Process IDs依dataset manifest核對，B04是ZH、B05是ttH。σ欄部分經manifest rounding，只顯示source尺度；真正normalization以frozen XWGTUP與original N為準。每事件contribution為XWGTUP/original N，只除一次，不再乘σ/N。HH乘自己的2BRbbBRγγ一次；ZH source已含Z→bb，只再乘自己的H→γγ；ttH乘自己的H→γγ，不能錯用factor2。這些仍是 **MODEL_BR_ONLY**，不是calibrated yields。

B100實際CTEQ6L1、one-loop αs、effective seed21；C1000實際NNPDF23 LO `NNPDF23_lo_as_0130_qed_mem0`、two-loop αs、seed20261122，兩者αs(MZ)=0.130。這些runtime事實依Phase7E additive audit，而非較早宣告cards。**不可pool成同配置1100-event SM；B/C差異不是同integrand seed pull。**

獨立來源7100；800筆舊reference-prefix與full inputs重疊，增量0。新native readback重讀6000背景entries，signal1100沿用Phase8 evidence；重讀不增加獨立樣本。

## 3. Object definitions與不變的selection

- Native photons先依pT排序、同值依原collection index，再套pT>25GeV、|η|<2.37，排除開區間1.37<|η|<1.52。至少兩個accepted photons，leading pT>35GeV。
- Eligible jets要求pT>25GeV、|η|<2.5。Native tag只用 `(BTag & 1)!=0`；不以Flavor、BTagAlgo／Phys或任意非零bit替代，也不重抽tag。
- TWO_JETS要求photon selection及至少兩個eligible jets；TWO_BTAGS再要求至少兩個native tagged eligible jets；FINAL_MGG要求inclusive **105≤mγγ≤160GeV**。Baseline沒有m_bb cut。
- Histogram的reconstructed_jet_multiplicity沿用native stored Jet collection count；selection的eligible-jet count有上述acceptance，不能混用。Tag multiplicity只數eligible jets的bit0。

B01–B03的Born photon pT／η／ΔR cuts與detector tight-ID/isolation不同。Source audit確認`ptgmin=0`關閉run-card Frixione block，不能因其他Frixione欄位存在就聲稱使用了Frixione isolation。詳細assignments與cards見[Phase9C](phase9c_photon_fake.md)。

## 4. Reconstruction與null候選

Hγγ由leading two accepted photons相加；Hbb由leading two **observed native tagged eligible jets**相加；兩者皆defined才有HH。沿用原P4/signed-mass/finite guards，不以abs或clip掩蓋非法mass²。這不是保證選到了truth Higgs的兩個b。

Candidate-defined collection與final selection不同。INPUT若有兩個accepted photons即可定義mγγ；有兩個eligible tags即可定義m_bb。Missing保持null，不填0GeV；0／1-tag regions沒有bb pair及HH mass。

| C1000 INPUT candidate | Defined／missing | Median（GeV） | Mean（GeV） | Sample std（GeV） |
|---|---|---:|---:|---:|
| mγγ | 484／516 | 124.9280 | 124.9308 | 1.38084 |
| m_bb | 305／695 | 107.2442 | 112.0914 | 59.0057 |
| m_HH | 143／857 | 397.5214 | 439.2307 | 145.1894 |

這些是finite fast-sim cohort分布；sample std不是official detector resolution或其uncertainty。歷史signal geometric0/1/2 matches：Hγγ為60/299/641，Hbb為43/402/555。Truth ID由source graph/index取得，native Particle order不作barcode；geometric matching不等於calibrated efficiency。

## 5. Cutflow、event yields與regions

| Dataset | INPUT | TWO_PHOTONS | TWO_JETS | TWO_BTAGS | FINAL_MGG |
|---|---:|---:|---:|---:|---:|
| S01_B100 | 100 | 45 | 38 | 18 | 18 |
| S01_C1000 | 1000 | 484 | 403 | 143 | 143 |
| B01 | 1000 | 446 | 266 | 91 | 28 |
| B02 | 1000 | 378 | 241 | 7 | 1 |
| B03 | 1000 | 445 | 277 | 0 | 0 |
| B04 | 1000 | 370 | 220 | 77 | 75 |
| B05 | 1000 | 327 | 322 | 131 | 131 |
| B06 | 1000 | 2 | 2 | 2 | 0 |

40個counts皆與原baseline閉合。各process保留自己的source denominator與weight，不將跨process counts變成一個physical yield。

TWO_JETS後按0／1／≥2 tags，以及LOW[105,120)、HIGGS[120,130]、HIGH(130,160]、OUTSIDE與UNDEFINED分區。120 partitions涵蓋1769 eligible events，逐dataset count、source sumw及MODEL_BR_ONLY sumw閉合。

| Dataset | TAG_0／TAG_1／TAG_GE2 | LOW／HIGGS／HIGH／OUTSIDE |
|---|---|---|
| C1000 | 62／198／143 | 2／401／0／0 |
| B01 | 45／130／91 | 21／18／37／190 |
| B02 | 194／40／7 | 29／12／35／165 |
| B03 | 271／6／0 | 29／11／30／207 |
| B04 | 35／108／77 | 0／216／0／4 |
| B05 | 50／141／131 | 2／312／2／6 |
| B06 | 0／0／2 | 0／0／0／2 |

UNDEFINED mγγ目前皆0，仍保留state。C1000 TAG_0／TAG_1 Higgs-like分別62／196 events，其m_bb皆undefined；TAG_1另2個LOW events，不能混用region與stage denominator。

## 6. Signal與per-background shapes

Unit-area只比較各process自己的distribution；constant modelBR相消，無luminosity scaling。Frozen edges非等寬，fraction是每bin而非每GeV density。Flows包含在denominator，display range不會改normalization。

TAG_GE2＋HIGGS-like region的weighted means與source delta SE如下，質量單位GeV；SE不是mass resolution或detector systematic。

| Dataset | N／ESS | mγγ | m_bb | m_HH |
|---|---:|---:|---:|---:|
| C1000 | 143 | 124.8668±0.1018 | 106.5729±2.7921 | 439.2307±12.1049 |
| B01 | 4 | 122.7663±0.9136 | 259.1019±76.5235 | 444.9943±68.0040 |
| B04 | 75 | 125.0170±0.1362 | 77.0356±2.9059 | 357.7834±15.8221 |
| B05 | 129 | 124.9092±0.1043 | 186.6524±11.7521 | 448.8955±16.4476 |

ZH／ttH包含H→γγ，diphoton候選亦集中於Higgs mass附近；m_bb與topology提供不同descriptive資訊。B01此區只有4來源，不能支持精細continuum shape校準。N129的ttH窄region與final N131是不同denominator。

Final105–160GeV下，C1000對每個背景的frozen-bin JS divergence（natural log）為：

| Background | mγγ JS | m_bb JS | m_HH JS |
|---|---:|---:|---:|
| B01 | 0.554365 | 0.382720 | 0.103672 |
| B02 | 0.693147 | 0.656247 | 0.378991 |
| B03 | undefined | undefined | undefined |
| B04 | 0.002874 | 0.240539 | 0.135247 |
| B05 | 0.006075 | 0.171983 | 0.048458 |
| B06 | undefined | undefined | undefined |

B02 singleton的極端distance不是完美discrimination；B03/B06 empty denominator為null。864 comparisons中128 defined、736 undefined。JS/CDF distance不是p-value、independent nonparametric CI或physical sensitivity。

Normalized fraction f_b=B_b/T的variance由完整original-N的influence w_i(I_ib−f_b)/T計算，包含bin–total covariance，不是單純TH1 Sumw2/T²。Weighted mean同理由w_i(x_i−mean_w)/T求delta SE。Empty bin／singleton empirical variance可為0，但真實rate／shape未知。Ratio遇zero background bin保持undefined，不補epsilon；不將correlated regions／κ hypotheses當獨立來源。

## 7. MC statistical support與sample planning

Fixed-original-N source variance保留cut failures的0 contributions：N/(N−1)×Σ(x_i−mean)²。Integration normalization error、conditional tag variance與未知systematics不直接加進同一誤差。單次shower/detector realization無法獨立識別純generator與純detector variance。

| Dataset | Final k/N | Central CP95 | Relative source sampling SE | ESS／最大來源 |
|---|---|---|---|---|
| C1000 | 143/1000 | [0.121879,0.166247] | 7.75% | 143／0.70% |
| B01 | 28/1000 | [0.0186847,0.0402149] | 18.64% | 28／3.57% |
| B02 | 1/1000 | [0.0000253175,0.00555892] | 100% | 1／100% |
| B03 | 0/1000 | [0,0.00368208] | undefined | undefined |
| B04 | 75/1000 | [0.0594461,0.0931084] | 11.11% | 75／1.33% |
| B05 | 131/1000 | [0.110698,0.153501] | 8.15% | 131／0.76% |
| B06 | 0/1000 | [0,0.00368208] | undefined | undefined |

0/1000的單側95%proposal-acceptance upper為0.00299124955；不是physical cross-section或fake-rate上界。4560 stage/bin rows有2379 EMPTY_BIN、1039 LOW_ESS_LT10與447 LOW_ESS_LT20。Global acceptance有意義不保證每bin有支持。

若未來proposal／selection完全相同且IID，unweighted acceptance的asymptotic relative SE目標r給N_plan≈ceil[(1−p)/(pr²)]。這是規劃，不是測量／保證，也不啟動production。

| Dataset | 20%目標point N [pilot CP envelope] | 30%point N | 50%point N |
|---|---:|---:|---:|
| 同C1000 proposal | 150 [126,181] | 67 | 24 |
| B01 | 868 [597,1313] | 386 | 139 |
| B02 | 24975 [4473,987435] | 11100 | 3996 |
| B04 | 309 [244,396] | 138 | 50 |
| B05 | 166 [138,201] | 74 | 27 |
| B03/B06 | 無finite measured guarantee | 同左 | 同左 |

此N是全新independent campaign總數估計；若改matched configuration、proposal、fake-transfer weights或bin precision目標須重規劃。若另假設B03/B06真p為單側upper、upper/10、upper/100，20%式給8333、83553、835747；這些p是假說，非測得值。CP envelope不代表未來precision有95%保證。

## 8. Heavy-flavour origins與overlap

B01–B03共3000 source events使用原LHE、完整Pythia diagnostics、HepMC graph與native objects。Exact tuple mapping unique數為B01 426370/426370、B02 468547/468551、B03 470230/470232；6個ambiguous records不強配。

ME incoming abs(status21)、outgoing abs(status23)分開；相同PID的incoming→outgoing不是可刪掉的shower copy。Shower heavy-line birth定義為abs(status41–59)且沒有直接同signed-PID母節點；direct g→QQ還要求共同gluon母及正／反heavy direct daughters。Terminal hadron、parton cones、nativeFlavor、native bit0各自保留；multi-mother string不能強配唯一perturbative endpoint。

| Full-cohort event flags／1000 | B01 | B02 | B03 |
|---|---:|---:|---:|
| Outgoing ME flavour | b:1000 | c:1000 | light/gluon:1000 |
| Incoming HF ME record | 58 | 69 | 6 |
| Shower bottom-line birth | 53 | 36 | 49 |
| Shower charm-line birth | 170 | 211 | 183 |
| Direct g→heavy-pair proof | 211 | 240 | 220 |
| Terminal bottom hadron | 1000 | 36 | 49 |
| Native eligible bottom jet | 860 | 13 | 18 |

Flags可重疊，不能相加成partition；terminal charm可能來自bottom decay。B03的4.9% shower-bottom頻率是本proposal/shower診斷，不是ATLAS contamination。

TWO_JETS中native-bottom events為263/266、5/241、3/277，直接顯示Born processes可進入共同photon/jet與heavy-flavour重建相空間。B03 source997有直接g→bb、兩個native5/hadron5 jets但observed tags1/0；source170／971也顯示native flavour與terminal-hadron cone不必一致。B02唯一final source481是hard ccγγ、兩個native4/hadron4 tagged jets，不能把所有ccγγ tags叫作shower bottom。

這證明reconstructed flavour不是Born-process exclusivity；不證明每個perturbative contribution被精確double counted，也不提供合法stitching／subtraction。原matching/merging關閉，沒有validated exclusive contract：

`OVERLAP_UNRESOLVED_REQUIRES_MATCHED_GENERATION_OR_VALIDATED_EXCLUSIVE_DEFINITION`。

因此不建立physical B01+B02+B03 sum。下一步先審查HF scheme、ME multiplicities、matching/merging或generator-level exclusive/veto定義及normalization closure，再另案授權新independent generation。

## 9. Photon origins與fake feasibility

只沿PDG22 copy chain到first non-photon parents，避免beam proton使所有pp photons被誤判hadron decay。Prompt roots須綁定hard source或H→γγ lineage；radiation須原Pythia status41–59與emitter。Native association為strict ΔR<0.2內唯一stable photon、truth不共享且無electron contender；多contenders／衝突保持unknown。這是geometric diagnosis，沒有fake-response校準含義。

| Accepted native photon objects | Prompt | Radiation | Hadron decay | Electron-associated | Unknown |
|---|---:|---:|---:|---:|---:|
| B01 | 1287 | 3 | 0 | 0 | 98 |
| B02 | 1155 | 7 | 0 | 0 | 138 |
| B03 | 1238 | 0 | 0 | 0 | 115 |
| B04 | 1092 | 4 | 0 | 0 | 93 |
| B05 | 965 | 8 | 0 | 3 | 176 |
| B06 | 561 | 2 | 0 | 0 | 54 |

8079 native reco objects中6999符合acceptance；這是物件數，仍只6000背景來源事件。674 unknown objects不是674個已證明fakes。同acceptance有676 stable truth hadron-decay photons，未必重建或unique-match；reco hadron-decay observed0不表示nonprompt成分不存在。

B06 cutflow1000/2/2/2/0：source69兩objects因多stable-photon contenders保持unknown、mγγ72.4906GeV；source245為Born-lineage photon加有原status−51證據的radiation photon、mγγ43.0919GeV。第二物件可以是QED radiation，**不是量到jet fake**；兩者皆不過final mass cut。

[Phase9C公開calibration audit](phase9c_photon_fake.md)查閱正式ATLAS HH方法及photon-efficiency資料。Prompt ID scale factor、electron→photon transfer、指定preselection composition各有不同分母，不能當本地Delphes per-jet fake probability；未知values/covariances維持null，未匯入restricted material。這是本次未建立compatibility，不宣稱全世界無公開輸入。

`PHOTON_FAKE=BLOCKED_CALIBRATION_UNAVAILABLE`。

未來須凍結tight/anti-tight、isolation、conversion與electron denominators，以相容data/control估prompt leakage、ID–isolation及雙物件correlations，再在tag/mγγ sidebands驗證transport。Electron→photon與jet→photon需分開。未啟動新generation。

## 10. κλ reweighting與未來proposal

六hypotheses共用C1000的1000 hard-event identities；6000 rows不是獨立6000事件。Source contribution乘frozen ratio與自己的modelBR一次；180個common-source covariance entries已獨立重算，不把hypotheses視為獨立MC。

| κλ | Source ESS | Final ESS | Source top1／top5 | Final top1 |
|---:|---:|---:|---|---:|
| −1 | 235.495 | 43.7733 | 4.65%／9.45% | 9.24% |
| 0 | 503.655 | 78.3097 | 2.47%／5.38% | 5.67% |
| 1 | 1000 | 143 | 0.10%／0.50% | 0.70% |
| 2 | 204.589 | 71.9809 | 5.99%／9.28% | 7.44% |
| 2.5 | 36.6943 | 16.0736 | 15.11%／25.13% | 19.39% |
| 5 | 19.5442 | 7.65012 | 19.82%／35.68% | 26.79% |

κ2.5／5仍為 **INCONCLUSIVE_REWEIGHTING**；分bin支持可能更差。不能用重複來源、更多bootstrap rows、截大weights或平滑圖形補獨立phase-space support。

未來可審查benchmarks附近independent generation或多κ proposals的mixture；需已知proposal densities/normalizations、明確balance/multiple-importance weights、獨立與shared source IDs/covariance、closure及tail/bin precision gates。先滿足matched PDF/αs signal contract；本次只提出策略，無新ME/integral/events。

## 11. Systematics與physical likelihood

22類readiness為luminosity；photon ID/trigger/energy scale/resolution；JES/JER；b-tag/light/charm mistag；pileup；PDF/μR/μF；generator/parton shower；Higgs BR；background normalization/HF overlap/photon fake；finite-MC及κ support。未有physical values、constraints、correlations者保持null；toy widths不是official ATLAS systematics。

| Gate | 狀態 |
|---|---|
| Matched signal normalization | BLOCKED |
| HF exclusivity | BLOCKED |
| Photon-fake estimation | BLOCKED |
| Single-Higgs modeling | BLOCKED |
| Detector calibration | BLOCKED |
| Nuisance values | UNKNOWN |
| Nuisance correlations | UNKNOWN |
| MC bin statistics／κ support | BLOCKED |
| Signed expectation model | 僅當前無負source weight條件成立；不支援未驗證未來signed inputs |

沿用Phase8 RooFit/RooStats及26項synthetic methods checks，不重寫或啟動physical fit。Toy Gaussian/lognormal/MC-stat/shape constraints只驗證方法，不能供應缺少calibration。未來signed model需合法expectations及非負總rates，不能clip負bins。

`PHYSICAL_TOTAL_BACKGROUND=BLOCKED`；`PHYSICAL_SIGNIFICANCE=NOT_EVALUATED`；`PHYSICAL_CLs=NOT_EVALUATED`；`PHYSICAL_KAPPA_INTERVAL=NOT_EVALUATED`。

## 12. 結論、驗證與後續需求

已確認：Born labels不給reconstructed flavour exclusivity；shower重味確實進入共同selection；one-Born-photon source的第二物件可能是radiation或ambiguous；zero/single survivors不足以定義穩定rare template；κ2.5/5由少數來源支配。

實證包括exact-source review、6000-background native ROOT readback、既有4668 histograms的fresh canonical validation、7100 persisted sources數值重算、120region閉合、ROOT33-case/66-endpoint binomial cross-check。另有獨立Decimal70：144hist／1824 flow-inclusive bins／40stage／120regions，共 **12904比較PASS**，未匯入production statistics helpers。Photon final750 aggregate rows亦經6300獨立數值比較；各證據類別不互相冒充。

後續先審查HF exclusive/matching、建立compatible fake calibration、核對single-Higgs modeling，再補detector/physical nuisance values與correlations，按proposal與bin support規劃獨立MC。本任務沒有啟動production。

Phase7I僅追蹤未來corrected CTEQ6L1 one-loop matched integration、獨立cross section/error、corrected event chain及新source IDs。**沒有改Phase7I、build/restart或以新normalization默換C1000。**

## 附錄A：12張ROOT local figures與caption guide

由 [prepare_plots.py](../analysis/phase9/scripts/prepare_plots.py) 建立規格、[phase9_plots.cxx](../analysis/phase9/apps/phase9_plots.cxx) 以CERN ROOT繪圖。144 histograms／5472個source sumw、sumw2與fraction comparisons含flows已核對。Local規格 `phase9_plot_spec_final.json` SHA：

`bf11aeef3a22f101eccde4d21a060d949dabc33d2bc575bc4c79fa99e091cabf`。

Local `figures_final_v2/phase9_plot_manifest.json`逐圖列最終PDF/PNG paths、SHA256及完整specification。十二張最終ROOT PDF均已實際用Poppler轉成preview，由主執行器檢視全套contact sheet與full-size panels，visual QA為 **QA_PASSED**；publication仍 **AWAITING_USER_APPROVAL**、`publication_authorized=false`。Visual QA不等於使用者核准，沒有任何PDF/PNG獲准推GitHub。下列中文caption guide不替代immutable plotted-caption spec。

最終PDF只用pypdf修改page boxes、去掉周圍空白；raster僅用於判定邊界，沒有以raster取代ROOT vector drawing。已逐一檢查12/12份manifest的decoded ROOT vector-stream SHA256在trim前後完全一致，`data_or_drawing_changed=false`。原ROOT PDF與最終PDF的整檔SHA不同並各自保存；approval必須針對最後paths/hashes及其caption/provenance，不能沿用較早版本。

共通：無luminosity scaling／official calibration／physical summed background。Shape為raw-source unit-area fraction/bin，flows在denominator，constant modelBR相消。1SE表示fixed-original-N delta含bin-total covariance，finite sparse-bin限制保留。

1. **phase9_01_signal_mgg：** C1000 originalN1000、INPUT defined484/missing516；mγγ GeV，fraction/bin，1SE normalized-bin delta。Display105–160只改可見範圍，不改完整denominator；不是官方mass-resolution測量。
2. **phase9_02_signal_mbb：** C1000 N1000、INPUT defined305/missing695；leading two observed native tagged eligible jets，GeV／fraction per bin／1SE。Overflow0.00327869仍在denominator，0–500GeV只是display；不是truth-pair效率。
3. **phase9_03_signal_mhh：** C1000 N1000、INPUT defined143/missing857；GeV、fraction/bin與1SE。Display200–1200，frozen bins/flows完整保留；finite tails不構成precision physical template。
4. **phase9_04_signal_b01_mgg：** C1000/B01各N1000，FINAL_MGG defined143/28，各自normalized、GeV/fraction per bin、1SE；不相加。Finite continuum support、HF/fake/detector blockers保留。
5. **phase9_05_signal_b04_b05_mgg：** C1000/ZH/ttH各N1000，FINAL_MGG defined143/75/131；三條各自normalized curves，GeV/fraction per bin、1SE；不是single-Higgs sum，BR cancellation不驗證physical rate。
6. **phase9_06_signal_backgrounds_mbb：** C1000對B01–B06、各sourceN1000、FINAL_MGG，六獨立panels。Observed tagged-pair mass，GeV/fraction per bin/1SE；B03/B06 empty明示undefined，B02 n1 unsupported，不補shape/error band。
7. **phase9_07_signal_backgrounds_mhh：** 同source/stage，六獨立panels；兩H candidates皆defined才有HH。GeV/fraction per bin/1SE；empty/singleton/tail限制保持，無total background。
8. **phase9_08_heavy_flavour_tags：** B01–B03各originalN1000、TWO_JETS。Native-b/c、direct g→QQ為可重疊event indicators；0/1/≥2 tags為partition。縱軸fraction/**original N**，非eligible denominator或獨立jet頻率；pointwise Wilson95，無HF process sum。
9. **phase9_09_cutflow_efficiency：** B100 N100，其餘各1000；五固定stages的unweighted cumulative acceptance，Wilson95 pointwise intervals。Stages correlated，不pool B/C，不宣稱official detector efficiency。
10. **phase9_10_kappa_weight_concentration：** C1000共用N1000與frozen六假說CSV，INPUT依各hypothesis |w|排序、顯示前10%；denominator全部1000 |w|。無誤差棒：deterministic support diagnostic，hypotheses correlated，不是confidence band。
11. **phase9_11_kappa_final_ess：** C1000 N1000、FINAL_MGG、frozen ratios；ESS=(sumw)²/sumw2、constantBR相消。無誤差棒，非confidence interval；κ2.5/5明示INCONCLUSIVE_REWEIGHTING，沒有κ limit。
12. **phase9_12_background_regions：** B01–B06各originalN1000、TWO_JETS後tags×mγγ bands，六separate process panels的raw event counts。Errors為Wilson95 acceptance×originalN，zero有非零upper；partitions correlated，undefined mγγ目前0另記，無luminosity/process sum。

## 附錄B：Evidence與閱讀順序

[Phase9A](phase9a_phase8_review.md)列source/weights/BR/bit0/hash/κ covariance；[Phase9B](phase9b_heavy_flavour.md)列graph定義與witnesses；[Phase9C](phase9c_photon_fake.md)列photon/fake/public applicability；[Phase9D](phase9d_mc_precision.md)及[Phase9E](phase9e_control_regions.md)列interval/planning/null/flow/shape；[Phase9G](phase9g_likelihood_readiness.md)列physical gates。

公開bounded evidence位於 `analysis/phase9/evidence/`；完整ROOT/LHE/HepMC、native event details、plot_data與未核准figures只留本機。

| Evidence | SHA256 |
|---|---|
| Native readback | `6d46d1b76519b59c64aabb8bf7632871997f37b5f38e4a5d7e91bd71a9c979ad` |
| HF CSV | `efc780381f213616d93a492e707c24e66a178d3c53cc12f9694847dfa0b965ab` |
| Photon CSV | `aca72e8876bbf9f87fb61c2b8a1f915b4586c2132a65c26d18070143c81c9497` |
| Origins summary | `86db961fb6c51fe545f1bc4670edc08bc4dbb49340e47952452e0f1c65a97ab5` |
| Rare precision | `16dab8fd42b0ab9f70eaeae877a94be09a0a41f4368a0dff4614dc17d2372c87` |
| Region diagnostics | `e52ac09f437519ecd3cf3b276599ed96cfac01183149380fb5ffb3244000da02` |
| Shape metrics | `24a1ec5ae7e2f090311517e07b33633e67c23050d32845761898e4ba131e0aa8` |
| Plot data | `4ec74e50dcd66c94f7a314ec82316b51cf47a08208ecc68fa966f9439f093bd5` |

Final source revision、remote bytes、CI與resource/preservation以Phase9 final report及execution/publication manifests為準。Source/method PASS不替代缺少的physical模型資料。
# Phase10G 科學分析註記：HH→bbγγ 背景生成與校準的可行性

本研究是既有樣本上的 ATLAS-like fast-simulation 探索分析。Phase10 的進展是釐清重味來源、重建相空間、光子控制可觀測性、生成處方與統計需求的關係；目前仍未建立可相加的物理背景模型。**PHYSICAL_TOTAL_BACKGROUND=BLOCKED；PHYSICAL_SIGNIFICANCE、PHYSICAL_CLs、PHYSICAL_KAPPA_INTERVAL 均為 NOT_EVALUATED。**

基準為 Phase9 PR26 head `ebae34fdaf9ccb09c77bd47cb1c7827fa560de0a`；Phase8 head 為 `8ecd91106acb1dae065cde14f1d62867d10b073f`；Phase9 實際執行來源為 `2584e342b80b20c314392d20d77d92a6ccb850c4`。使用既有 ROOT 6.40.04／C++20、MG5_aMC 3.5.16、Pythia 8.317、Delphes 3.5.1。沒有新 ME、積分、獨立 hard events、Pythia 或 Delphes events，沒有執行未來 pilot、重啟 Phase7I 或重畫圖。

證據分為 ACTUAL_EXISTING_DATA_READBACK、HISTORICAL_SOURCE_AUDIT、PUBLIC_SOURCE_AUDIT、SYNTHETIC_METHOD_ONLY、FUTURE_UNEXECUTED_PROPOSAL。這些類別回答不同問題；來源程式通過測試、物件值可讀與物理校準成立不是同一件事。本文的舊 shape／origin 數字來自 Phase9 最終 origins_03／statistics_02 及 versioned evidence；新 scalar observability 來自 Phase10 原生讀回與 photon01 hash/stage join；新重味分層來自 run_01/hf_02；新 precision planning 來自 run_01/precision_01。各數值並非重新生成的事件。

## 1. 物理動機（Physics motivation）

HH→bbγγ 同時提供 diphoton 與 hadronic Higgs 候選。H→γγ 的狹窄質量結構有助於區分 continuum γγ+jets；bb system 與 HH topology 另提供描述性資訊。單 Higgs 的 ZH、ttH 也可能含真正 H→γγ，因此不能僅憑 mγγ 峰值將它們和 HH 區分。

[ATLAS 公開 HH→bbγγ 論文](https://arxiv.org/abs/2112.11876v2) 是物件、資料控制與分析範圍的參考。正式結果的 tight ID、conversion、trigger、jet calibration、背景約束與 likelihood 不能由本地 Delphes 自動繼承。本研究的問題是：現有 source 的 hard flavour 如何經 shower／hadronization 進入相同重建選擇；缺少哪些資料才能建立可物理解讀的背景與校準策略。

## 2. 當前來源樣本（Current source samples）

獨立來源總數為 7100：signal B100 100、C1000 1000，加六個背景各 1000。歷史 reference-prefix 與完整來源重疊，不能增加獨立樣本數。Phase9 讀回 6000 個背景；Phase10 為檢查正規化 reader 未保存的 photon/electron/jet 欄位，再讀同一批 6000 個背景。重讀增量為零，不把 7100 加成 13100 或 19100。

| Dataset | 來源定義 | 原始 N | source σ 尺度 [pb] | 自己的 MODEL_BR factor |
|---|---|---:|---:|---:|
| S01_B100 | historical full-loop ggF HH pilot | 100 | 0.017276 | 0.002653445906720871 |
| S01_C1000 | historical full-loop ggF HH | 1000 | 0.019069 | 0.002653445906720871 |
| B01 | bb̄γγ | 1000 | 約 0.06624666 | 1 |
| B02 | cc̄γγ | 1000 | 約 0.6274417 | 1 |
| B03 | light jjγγ | 1000 | 約 9.436556 | 1 |
| B04 | ZH，Z→bb̄、H→γγ | 1000 | 0.08953800 | 0.0022965313147512443 |
| B05 | ttH，H→γγ | 1000 | 0.3991820 | 0.002297546784308979 |
| B06 | bb̄γj，一個 Born photon | 1000 | 65.88309 | 1 |

σ 尺度不是 calibrated yield；精確權重以原始 XWGTUP 和 frozen source denominator 為準。每事件 raw contribution 為 XWGTUP/N_original，只除一次，不能再乘 σ/N。HH 的 2BRbbBRγγ、ZH 與 ttH 各自 H→γγ factor 各施加一次；ZH source 已包含 Z→bb。不能將 HH factor2 套到 single-Higgs。跨 process 的數值不相加為物理總背景。

B100 實際 CTEQ6L1／one-loop αs／seed21；C1000 實際 NNPDF23_lo_as_0130_qed_mem0／two-loop αs／seed20261122。兩者 αs(MZ)=0.130，但 PDF／running 不同，不能 pool 成同配置的 1100-event SM，也不能把截面差異當純 seed fluctuation。[Phase9 analysis note](phase9f_analysis_note.md) 與 Phase7E additive audit 保留其來源限制。

## 3. Higgs 重建（Higgs reconstruction）

凍結的 selection_id 為 HISTORICAL_PHASE6C_7D_NATIVE_BIT0_V1。Photons 先按 native pT 遞減、同值依原 index 排序，再要求 pT>25 GeV、|η|<2.37，排除開區間 1.37<|η|<1.52；至少兩個合格 photon，leading pT>35 GeV。Eligible jets 要求 pT>25 GeV、|η|<2.5；native b tag 只讀 (BTag & 1)!=0，不以 flavour 替代、不重抽標記。TWO_JETS 要求至少兩個 eligible jets；TWO_BTAGS 至少兩個 tagged eligible jets；FINAL_MGG 為 inclusive 105≤mγγ≤160 GeV。Baseline 沒有 mbb cut。

Hγγ 是 leading two accepted photons 的四向量和；Hbb 是 leading two **observed native tagged eligible jets** 的和。兩者存在才定義 HH。這個選擇不保證選到 truth Higgs 的兩個 b。程式保留 finite／signed-mass guards，缺候選用 null；沒有把 missing mass 填成 0 GeV。0／1-tag region 缺少 Hbb 與 HH 候選。

INPUT candidate-defined denominator 與最終選擇不同：可有 mγγ 而沒有 Hbb，或有 Hbb 而沒有兩個 photons。stored-jet multiplicity 數全部 native Jet；selection eligible-jet multiplicity 才含 pT/η cuts，兩者不能混用。

## 4. 訊號分布（Signal distributions）

Phase9 frozen histogram 對 C1000 INPUT 的描述如下。Sample std 描述此有限 fast-sim cohort，不能稱為官方 detector resolution 或其校準誤差。

| Candidate | Defined / missing | Median [GeV] | Mean [GeV] | Sample std [GeV] |
|---|---|---:|---:|---:|
| mγγ | 484 / 516 | 124.9280 | 124.9308 | 1.38084 |
| mbb | 305 / 695 | 107.2442 | 112.0914 | 59.0057 |
| mHH | 143 / 857 | 397.5214 | 439.2307 | 145.1894 |

Hγγ 集中於 Higgs 質量附近；Hbb 的尾部與偏移同時受 native tag／候選選擇、jets response 和組合影響。尚未做可將這些效應分離的物理校準，不能單靠此分布指定因果比例。

既有 signal truth geometric 0／1／2 matches：Hγγ 為 60／299／641；Hbb 為 43／402／555。這是歷史來源 matching 診斷，並非 tight photon efficiency 或 calibrated b-tag efficiency。Truth ID 來自 source graph/index，不以 native Particle 順序作 barcode。

各 shape 自己做 unit area，常數 MODEL_BR 因子相消，沒有 luminosity scaling。Frozen bins 非等寬，縱軸是 fraction per bin，不能讀成 density per GeV；flows 保留於 normalization denominator。Normalized-bin delta error 包含 bin–total covariance，而非單純 Sumw2/T²。

## 5. 連續背景與單 Higgs（Continuum backgrounds）

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

B01 的 continuum final sample 只有 28 個來源；B02 只有 1 個，B03／B06 為零。空樣本沒有可定義的 normalized final shape；B02 singleton 的極端形狀距離也不是完美 discrimination。B04／B05 含 H→γγ，和 HH 的 diphoton shape 接近不能當作建模錯誤，也不能代表相同 topology。

Phase9 final frozen-bin natural-log JS divergence 的例子：C1000 對 B01 的 mγγ／mbb／mHH 為 0.554365／0.382720／0.103672；對 B04 為 0.002874／0.240539／0.135247；對 B05 為 0.006075／0.171983／0.048458。這些是 descriptive binned metrics，沒有 p-value 或 physical sensitivity 含義。稀疏、零 denominator、shared-event covariance 與未校準 normalization 限制均保留。

## 6. 重味來源（Heavy-flavour origin study）

Phase9 對 B01–B03 各 1000 個來源，用 LHE、完整 Pythia records、HepMC graph 與 native jets 分別描述 ME outgoing、ME incoming、shower births、direct g→QQ、terminal heavy hadrons、native flavour 和 observed bit0。這些是不同層級，不強制合成一個「真正 flavour」。

ME incoming/outgoing 用原始 Pythia abs(status)=21/23 分開；shower heavy-line birth 要求 abs(status)41–59 且沒有直接同 signed-PID 母節點；direct g→QQ 要求共同 gluon mother 及正反 heavy direct daughters。Terminal hadrons 以最近 eligible jet 的 strict ΔR<0.4 分配，ambiguous 保留；b priority 不刪除 charm cascade 證據。多母 string 的 sole perturbative endpoint 保持 UNKNOWN。

| 含至少一項證據的事件 /1000 | B01 | B02 | B03 |
|---|---:|---:|---:|
| Hard outgoing ME flavour | b:1000 | c:1000 | light/gluon:1000 |
| Incoming HF ME record | 58 | 69 | 6 |
| Shower bottom-line birth | 53 | 36 | 49 |
| Shower charm-line birth | 170 | 211 | 183 |
| Proven direct heavy-pair gluon splitting | 211 | 240 | 220 |
| Terminal bottom hadron | 1000 | 36 | 49 |
| Terminal charm hadron | 1000 | 1000 | 221 |
| Native eligible bottom jet | 860 | 13 | 18 |

Phase10 HF02 已實際完成 6000 筆來源連接，其中 B01–B03 共3000來源分層；輸出2220 strata rows、6000 covariance rows及60個process-overlap diagnostics。它重用凍結的Phase9 annotations、獨立ME flags／event join與統計計算，沒有新ROOT event loop或重新產生ancestry。status=VALIDATED_WITH_LIMITS，統計單位為完整原始source event，所有jets先在event內聚合。

各 origin flags 可重疊；shower-bottom 與 shower-charm、hadron 與 ME 類別不能相加成 partition。Terminal charm 可由 bottom decay 產生。Pythia/HepMC exact-tuple mapping 的 ambiguous records 為 B02 4、B03 2，沒有強配；未分類 ancestry 不改成 light 或 fake。

例如 shower-bottom raw source contributions／sampling SE [pb]：B01 0.003511073086±0.000469563337、B02 0.0225879012±0.003698114912、B03 0.4623912489±0.064449429961。其分母是每個來源自己的 original N；未含 integration error 或物理 systematics。B03 的 49/1000 不能讀成 ATLAS b-background contamination。

## 7. 重建 flavour 重疊（Reconstructed flavour overlap）

在相同 TWO_JETS 選擇中：

| Dataset | Eligible events | Eligible jets | 0 /1 /≥2 observed tags | Native-b events | Native-c events | Shower-bottom events |
|---|---:|---:|---|---:|---:|---:|
| B01 | 266 | 657 | 45 /130 /91 | 263 | 10 | 20 |
| B02 | 241 | 580 | 194 /40 /7 | 5 | 236 | 12 |
| B03 | 277 | 691 | 271 /6 /0 | 3 | 28 | 11 |

B01/B02/B03 可出現在共同 photon／jet phase space，也都可有 native heavy flavour。Native-b fractions 263/266、5/241、3/277 是 **stage-conditional** fractions；與 input acceptances 263/1000、5/1000、3/1000 不是同一量。

B02 唯一 final source481 具有 hard ccγγ、兩個 native4／hadron4 且 observed tags 的 jets，不能把所有 ccγγ tag 都叫作 shower-bottom。B03 source997 有直接 g→bb 與兩個 native5／hadron5 jets，但 tags 為 1／0；flavour 不保證 tag。不同 jets 共享 source event，其不確定度須以 event cluster 傳播。

這證明重建 flavour 不是 Born 樣本的互斥分割，**不證明某個 perturbative term 被重複計算，也不給出 subtraction／stitching 大小**。以 reco 或 bit0 veto 直接扣除來源無法代替 generator-level 處方。因此 HEAVY_FLAVOUR_ORIGIN=VALIDATED_WITH_LIMITS，HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY=UNVERIFIED。

## 8. Matching／merging 策略（Matching/merging strategy）

完整來源、軟體版本、官方一手文件與比較表見 [Phase10C](phase10c_generator_strategy.md) 及 metadata/phase10_generator_scheme_review.json。結論為 **NO_VALIDATED_MATCHING_PRESCRIPTION_YET**，不是預設 generic matching flag 可以解決本題。

| 方向 | 科學 verdict | 尚需解決 |
|---|---|---|
| A：massive-bottom 4F bbγγ 成分 | METHOD_ONLY | 相容 4F PDF／αs／ME／PS、photon IR 目標、互補樣本與 normalization |
| A：massive-charm 3F 成分 | UNVERIFIED | 3F PDF／閾值／PS／fragmentation 相容性 |
| B：共同 5F aa+0,1,2 QCD-parton MLM | UNVERIFIED | Exact process/history、nQmatch、Nmax、veto／DJR／scale scan |
| B：共同 family CKKW-L | UNVERIFIED | History／cut coverage／TMS／event×merging-weight closure |
| B：colourless aa Born core FxFx | UNVERIFIED | 本題 NLO amplitudes、IR isolation、HF coverage、負權重 |
| B：bbγγ 最低 core FxFx | INAPPLICABLE（所審官方處方） | 官方 lowest-core jets/b 限制 |
| C：完整共同測度的 exclusive flavour partition | METHOD_ONLY | IR-safe flavour-jet、coverage／orthogonality／subtraction |
| C：重建 flavour/tag veto shortcut | INAPPLICABLE | 不是 perturbative subtraction |

歷史 sm-no_b_mass 採 massless c/b，incoming 包含 c/b；B03 final light jets 不代表初態無 heavy flavour。4F／5F 的 collinear logarithms、mass 與 PDF 展開不同，不能直接相加兩套完整預測。一般 soft-heavy「任何 cone 有 b」flavour 定義在 massless limit 可能欠 IR safety；需明確 flavour-aware truth-jet 測度與 detector migration。

本機 3.5.16 templates 與 Pythia8.317 sources 證實 generic LO MLM／CKKW-L 與 NLO matching interfaces 存在，僅是軟體能力證據。nQmatch=4 對 b 的處理不能當作全部 HF double counting 已解。QCD merging 亦不補足 photon collinear／fragmentation 或 detector fake 成分。歷史 ptgmin=0 使 Frixione block 關閉；不能由其他欄位存在宣稱用了 smooth-cone isolation。

[Phase10D](phase10d_pilot_contract.md) 的 process proposals、matching-scale scan、truth／weight／resource契約均 **PREPARED_INACTIVE_BLOCKED**。所有 xqcut/qCut/TMS/qCutME 未選值；沒有執行 syntax parser 或任何 generated card。未來另需 exact source/card/hash approval、有限資源與新 output directory，cap 到達只能 inconclusive。

## 9. 光子 fake 可行性（Photon fake feasibility）

完整方法與來源見 [Phase10E](phase10e_photon_fake_feasibility.md)。Phase9 selected photon objects 為 prompt-hard 6298、radiation24、electron-associated3、unclassified674、hadron-decay0，共6999。Unclassified 保持未知；來源 ancestry/geometric match 沒有 detector fake calibration 含義。

Phase10 scalar readback 實際有 8079 原生 Photon、132 Electron（全在 B05）、19568 Jet。Photon IsolationVar 非零1941個，最大0.1199259683；Photon Status、EhadOverEem、SumPtChargedPU 全零。Jet Flavor、BTag 有非平凡值，FlavorAlgo／FlavorPhys 全零。Dictionary 有欄位不代表該樣本有資訊；Status 不能拿來分類真實 fake。

歷史 card 先以 ΔR=0.5、track/object pT threshold0.5 GeV、PTRatioMax0.12 隔離，再把 UniqueObjectFinder photons 寫成 Photon branch。失敗的 pre-isolation photon collection 未保存；現有隔離分布不能還原 nonisolated denominator。也沒有相容 tight/anti-tight shower shapes、conversion categories、tight-electron controls、prompt leakage 或 subtraction covariance。

B06 1000→2→2→2→0 不是 fake-rate measurement；第二物件可能是放射或無法唯一 matching。物理 fake rate=UNKNOWN，實際 transfer measurement=BLOCKED_MISSING_COMPATIBLE_OBSERVABLES。公開 ATLAS prompt-ID efficiency、electron-to-photon transfer 與分析 composition fractions 各有不同分母，catalog 審查只給 METHOD_ONLY，沒有匯入為 local jet fake probability。

## 10. 控制區定義（Control-region definitions）

TWO_JETS 後以 TAG_0／TAG_1／TAG_GE2，交叉 LOW=[105,120)、HIGGS_LIKE=[120,130]、HIGH=(130,160]、OUTSIDE_MGG、UNDEFINED_MGG。邊界120、130分配唯一；未定義候選仍有明確 state。這是預先聲明的描述性 region，未做資料驅動優化，亦不是已驗證的 control-to-target calibration。

Phase9 120 partitions 在各 dataset event count、raw sumW 與 MODEL_BR_ONLY sumW 閉合，TWO_JETS 總支持1769 events（包含兩個 signal cohorts）。例如 C1000 tag0/1/≥2=62/198/143；B01=45/130/91；B03=271/6/0；B06=0/0/2，且 B06 兩個皆在 OUTSIDE_MGG。沒有把不同來源的 counts 合成一個物理 control yield。

Synthetic photon ID×isolation 的 A/B/C/D 是另一套方法控制區，與上述 tag×mass partition 分開。A=tight isolated、B=tight nonisolated、C=anti-tight isolated、D=anti-tight nonisolated。令 F=N−P、κ_ID,iso=F_A F_D/(F_B F_C)，預測 A=κ F_B F_C/F_D。此 κ 與 κ_lambda 無關；完整9維 joint covariance 保留 prompt subtraction／shared-event／κ cross terms。Synthetic closure及20個 focused tests通過不解除物理阻擋。D≤0、zero C/B、負 subtraction 或 ill conditioning 會拒絕有效 rate claim；可選 signed diagnostic 仍 valid=false。

## 11. 統計支持（Statistical support）

| 來源 final | k/N | Central CP95 acceptance interval | Relative source sampling SE | Final ESS |
|---|---|---|---:|---:|
| C1000 | 143/1000 | [0.121879,0.166247] | 7.75% | 143 |
| B01 | 28/1000 | [0.0186847,0.0402149] | 18.64% | 28 |
| B02 | 1/1000 | [0.0000253175,0.00555892] | 100% | 1 |
| B03 | 0/1000 | [0,0.00368208] | undefined | undefined |
| B04 | 75/1000 | [0.0594461,0.0931084] | 11.11% | 75 |
| B05 | 131/1000 | [0.110698,0.153501] | 8.15% | 131 |
| B06 | 0/1000 | [0,0.00368208] | undefined | undefined |

CP intervals 是固定來源 proposal 的 event acceptance，不是物理 cross-section 或 fake-rate interval。0/1000 的單側95% upper為0.00299124955；不支持物理背景為零。Central two-sided upper0.00368208與one-sided upper不同，不混用。

完整 original N 來源 variance 包含失敗事件的零 contribution，以 N/(N−1) Σ(x_i−x̄)² 求 total variance；不把 Σw² 當成所有 normalization uncertainty。同事件 jets、regions、同來源 κ hypotheses 需 covariance。Finite MC sampling、integration error、proposal uncertainty、detector／model uncertainty 分開；一次 shower/detector realization 不能分離純 generator 與純 detector variance。

Phase9 4560 stage/bin quality rows 有2379 EMPTY_BIN、1039 LOW_ESS_LT10、447 LOW_ESS_LT20。Global acceptance有支持不代表每個bin有支持；singleton的empirical variance可能為零而真實shape仍未知。Zero denominator不補epsilon。對 future signed NLO weights 必須保留符號並另驗證合法 expectation model，不能 clip negative bins。

## 12. 未來樣本數（Future sample-size estimates）

Phase10 precision_01 實際產出88scenarios、3648bin-support rows、16個κ planning rows。32項 acceptance planning 的 Decimal80／exact rational cross-check通過，另核對兩個 frozen κ ESS。這是可重算的規劃數學，不是新 MC 或已達成精度。

對不變 selection、同一 IID proposal 的 Bernoulli acceptance，N_total≈ceil[(1−p)/(p r²)]；r 為目標相對SE。下表是**總N估計**，不是額外必須生成的N，不自動扣除舊樣本或授權production。

| 同 proposal | 10% | 20% | 30% | 50% | 20%的pilot CP95 envelope |
|---|---:|---:|---:|---:|---|
| C1000 | 600 | 150 | 67 | 24 | [126,181] |
| B01 | 3472 | 868 | 386 | 139 | [597,1313] |
| B02 | 99900 | 24975 | 11100 | 3996 | [4473,987435] |
| B04 | 1234 | 309 | 138 | 50 | [244,396] |
| B05 | 664 | 166 | 74 | 27 | [138,201] |
| B03/B06 | 無finite guarantee | 同左 | 同左 | 同左 | p lower=0，無有限保守上界 |

B02 的24975是歷史 p_hat=0.001 下 acceptance plugin；weighted selected raw rate 的 Bessel moment版本20%為25000。差異來自 finite-pilot N/(N−1)，均不是生產需求保證。CP envelope反映pilot p的不確定範圍，沒有保證未來精度以95%達成。B03/B06若改用假設p或pilot upper，可列scenario，但必須明示假設；p_hat=0本身沒有有限相對精度需求。

Weighted selected-rate planning 用 N0 Var_pilot(R)/(R²r²)，另記finite higher-moment／tail穩定假設。Bin raw rate、normalized fraction、acceptance是不同quantity；normalized-bin variance含bin-total covariance。Physical normalization uncertainty仍UNKNOWN/BLOCKED，不揉進這個MC precision。

κ_lambda=2.5/5 共用舊1000來源；其 source ESS36.6943/19.5442、final ESS16.0736/7.65012、final top1 fractions19.39%/26.79%。兩者均INCONCLUSIVE_REWEIGHTING。舊proposal final moment extrapolation的10/20/30/50%總N分別為2.5：6128/1532/681/246；5：12985/3247/1443/520。這些conditional numbers可能漏tail，不能當未來production requirement。

未來獨立benchmark或multiple-proposal importance sampling須有共同phase space、可求值且已正規化的proposal densities、已知normalizing constants、target support、unbiased weights與獨立source IDs，並保留cross-κ covariance。Observed histogram頻率不能替代proposal density；resampling、bootstrap或更多reweight rows不增加hard statistics。目前上述proposal feasibility尚未驗證，也沒有新ME weights。

## 13. 系統誤差準備度（Systematic readiness）

22類歷史readiness包括luminosity、photon ID/trigger/energy scale/resolution、JES/JER、b/light/charm tagging、pileup、PDF/μR/μF、generator/PS、Higgs BR、background normalization/HF overlap/fake、finite MC與κ support。缺少物理值、constraints或correlations者維持null，不能填0、toy width或任意全相關矩陣。

共用來源的κ statistical covariance雖可計算，並不給出luminosity、object、generator或fake nuisance的物理相關。Unknown nuisance policy必須fail closed；missing gate與null calibration不可當零背景，synthetic fit也不能unlock physical inference。Single-Higgs的own BR accounting通過，不代表top decay/spin、normalization及modeling系統誤差已驗證。

下游若將來使用likelihood，須同時有source-compatible signal/background rates、全部nuisance與correlation provenance、合法nonnegative expectation和足夠template support，才可評審physical fit。現有RooFit/RooStats方法測試僅SYNTHETIC_METHOD_ONLY；本文沒有執行physical significance／CLs／coupling interval。

## 14. 訊號正規化依賴（Signal normalization dependency）

MATCHED_SIGNAL_NORMALIZATION保持 **BLOCKED_PHASE7I**。C1000的實際PDF／two-loop running不等於歷史宣告的CTEQ6L1 one-loop matched target，不能用重新標籤或新的overall factor讓舊事件變成新配置。B100/C1000也不能當同integrand的1100個獨立同配置來源。

Phase7I依賴僅追蹤未來corrected matched integration、獨立截面與uncertainty、corrected full event chain及新的immutable source IDs。這些需要另行exact-source與bounded-resource批准。本文不改Phase7I、不build/restart、不默換歷史normalization，也不以background方法進展跳過signal blocker。

## 15. 結論、阻擋與既有圖件（Conclusions and blockers）

本研究已把「來源可追溯、重建可讀」與「背景處方已成立」分開。舊事件確實顯示ME flavour、shower births、hadrons、native flavour和bit0有migration；光子欄位確有隔離資訊，但被保存的collection缺少nonisolated denominator及validated ID／conversion。因此下一步科學工作是審查單一generator target／matching與photon IR處方、取得相容control data，並以明確proposal和bin support規劃獨立統計；這不是自動進入physical production的授權。

| Scientific gate | Phase10 required status | 解除條件 |
|---|---|---|
| HEAVY_FLAVOUR_ORIGIN | VALIDATED_WITH_LIMITS | 已有來源診斷；保留ambiguity與非互斥flags |
| HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY | UNVERIFIED | Generator-level common-measure／matching／coverage／normalization驗證 |
| PHOTON_FAKE_RATE | UNKNOWN | 相容control denominators、calibration、prompt subtraction與target closure |
| MATCHED_SIGNAL_NORMALIZATION | BLOCKED_PHASE7I | Corrected matched integration與完整新來源鏈 |
| PHYSICAL_TOTAL_BACKGROUND | BLOCKED | 上述以及single-Higgs／detector／nuisance／statistics共同滿足 |
| PHYSICAL_SIGNIFICANCE / CLs / KAPPA_INTERVAL | NOT_EVALUATED | 物理inputs全部ready後另行review與授權 |

獨立審查是另一份[Phase10A](phase10a_independent_review.md)的程式／算術／checklist證據，不虛構external human approval。Phase10B的HF02實際status=VALIDATED_WITH_LIMITS（6000 joined、3000 stratified），Phase10E photon01已實際完成6000來源的hash/stage一對一join與frozen selected-origin totals核對；兩者均保留各物理blockers。本文中的Phase9來源表與新檢查範圍分列，不稱新annotation或新獨立事件。獨立Phase10A的最終review_05 receipt實際為PASS_INDEPENDENT_PHASE9_REVIEW_WITH_LIMITS：9項checklist通過、完整6000 source joins、1200項HF Decimal70、510項stage/region Decimal70、108個background histograms／3862項histogram comparisons。另讀3個selected raw-Pythia graph witnesses；這不是獨立重分所有event ancestry。4668 ROOT objects（4052 TH1D、616 TH2D）以frozen canonical digest與histogram manifest綁定，4800 logical descriptors含132個undefined shapes；不是新ROOT histogram loop。來源、publication bytes與CRLF CSV identities亦核對，沒有fresh remote download或external human signoff。CI/source tests不等於重跑全部本機ROOT檔案。

既有4668 Phase8 ROOT objects與12組Phase9 figures保留。本文只讀原manifest與captions，沒有重畫或重新宣稱visual acceptance。12組目前為 **QA_PASSED／AWAITING_USER_APPROVAL**，publication_authorized=false。QA、CTest、歷史發表均不等於使用者對此版本的批准；exact path、SHA-256、caption/provenance須一併核准才能commit/push。本文不嵌入或發布PDF/PNG。

| Figure ID | 原caption的科學用途與分母 | 解讀限制 |
|---|---|---|
| phase9_01_signal_mgg | C1000 INPUT，484 defined；unit area | Candidate denominator非全部1000；finite cohort |
| phase9_02_signal_mbb | C1000 INPUT，305 defined；flow含分母 | m_bb overflow fraction0.00327869；非detector calibration |
| phase9_03_signal_mhh | C1000 INPUT，143 defined | 有兩個candidate才定義HH |
| phase9_04_signal_b01_mgg | FINAL，signal143 vs B01 28，分開unit area | 無luminosity、無physical背景sum |
| phase9_05_signal_b04_b05_mgg | FINAL，signal143、ZH75、ttH131 | Genuine H→γγ可有相似diphoton shape |
| phase9_06_signal_backgrounds_mbb | FINAL，每個背景各自panel | B02 singleton；B03/B06 empty=undefined |
| phase9_07_signal_backgrounds_mhh | FINAL，每個背景各自panel | 同上；未宣稱sensitivity |
| phase9_08_heavy_flavour_tags | TWO_JETS，B01–B03 event indicators | Origin flags重疊；pointwise Wilson95 |
| phase9_09_cutflow_efficiency | 8個歷史cohorts，各自N | Cumulative stages相關；不pool |
| phase9_10_kappa_weight_concentration | 同1000 sources，按各κ的abs weights排序 | Deterministic support；假說高度相關 |
| phase9_11_kappa_final_ess | Final143 source events，6個κ hypotheses | ESS非CI；2.5/5仍inconclusive |
| phase9_12_background_regions | TWO_JETS，tag×mass每個背景各panel | Raw counts、pointwise Wilson；非物理control normalization |

權威manifest為 analysis/phase9/evidence/phase9_plot_manifest.json；local full manifest SHA-256=772867efd37756d533d8dbe9df3b42674bf09a7fbff6a0a80000ce78fd9b47a9，final plot spec SHA-256=bf11aeef3a22f101eccde4d21a060d949dabc33d2bc575bc4c79fa99e091cabf。每組exact PDF/PNG hashes與captions仍由該manifest逐一追蹤。本文的表是圖件閱讀索引，沒有改寫科學caption或重新批准provenance。

可重查的來源入口：[Phase10C](phase10c_generator_strategy.md)、[Phase10D](phase10d_pilot_contract.md)、[Phase10E](phase10e_photon_fake_feasibility.md)，以及 analysis/phase8/config/datasets.json、selection_v1.json、regions_v1.json，Phase9 evidence中的 origins／rare-event／kappa／shape／region JSON/CSV，和本機phase10/run_01/precision_01/phase10_precision_summary.json。原始來源、歷史報告和既有圖件均不因本文而取代。

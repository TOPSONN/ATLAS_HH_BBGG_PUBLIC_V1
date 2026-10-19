# Phase 10C：diphoton＋jets 重味生成策略可行性

證據類別：`PUBLIC_SOURCE_AUDIT`、`HISTORICAL_SOURCE_AUDIT`。基準：`ebae34fdaf9ccb09c77bd47cb1c7827fa560de0a`。本節只讀來源、模型限制卡與公開一手文件；未啟動 MG5、未解析新 process、未計算 ME／積分、未產生任何 Pythia／Delphes 事件。外部獨立人員簽核：未觀察到。

結論為 **NO_VALIDATED_MATCHING_PRESCRIPTION_YET**。目前不能推薦一個已驗證的 inclusive diphoton＋heavy-flavour matching 處方。值得分開評審的方向是 massive-bottom 4F 成分、共同 5F diphoton QCD multiplicity family，以及具有完整測度定義的 exclusive-flavour partition；三者都不能直接把現有 B01、B02、B03 變成物理總背景。

## 1. 本機版本與歷史定義

`/home/btu/opt/mg5amcnlo` 實際指向保留的 `mg5-release-v3.5.16`；VERSION 是 3.5.16、日期 2026-06-03。Pythia 的本機 `Version.xml` 是 8.317、日期 20260120。本次以這兩個版本的模板、UFO、JetMatching header、aMCatNLO hooks 和隨附 manual 為準。完整路徑、位元組數與 SHA-256 見 `metadata/phase10_generator_scheme_review.json:local_source_audit`；網站 latest 文件只作補充，不能取代本機版本。

歷史 `simulation/mg5/cards/{bbgg,ccgg,jjgg_light}.mg5` 均採 `sm-no_b_mass`，incoming proton 包含 c、b。B01 指定 bbγγ，B02 指定 ccγγ；B03 的 final `jl` 只有 g/u/d/s，但 incoming 仍包含 c/b。這是 **massless 5F 的分開來源定義**，不是三個已證明互斥的 shower 後重味類別。Phase9 的來源／重建交叉表可指出需要處理的區域，不能反推已經存在某項 perturbative double counting，亦不能給出合法 subtraction 大小。

需特別保留模型限制語意：UFO `parameters.py` 的 MC=1.27 不能直接當作 `import model sm` 的有效 charm mass。實際 `restrict_default.dat` 設 MC=0、MB=4.7 GeV；`restrict_no_b_mass.dat` 設 MC=MB=0；`restrict_c_mass.dat` 則設 MC=1.55、MB=4.7 GeV。這些是來源觀察，沒有因為讀到數值便採用新的物理設定。

## 2. 必須一起定義的物理問題

**4F／5F 與 charm。** 對 bottom 而言，4F 的 incoming active flavours 不含 b，hard final b 可保留質量；5F 在 PDF 中處理 incoming b 並通常在 ME 採 massless b。兩種展開的 collinear logarithms 與有限階近似不同，不能把兩套完整預測直接相加。只把 proton alias 刪掉 b、卻仍用不相容 PDF／alpha_s，不足以建立 4F 處方。Charm 在常用 bottom 4F 定義中仍可為 active massless flavour；若想明確 massive-c，必須再評審 3F PDF、閾值、ME 和 shower。公開 Z/H＋b 的 4F／5F 比較可提供方法背景，但其過程與數值不能移植成 γγ＋HF 的處方。[Napoletano 等，arXiv:1706.10072](https://arxiv.org/abs/1706.10072)

**ME／shower／hadron／reco。** Incoming heavy flavour、hard final pair、shower heavy-line births、證明成立的 g→QQ、heavy hadron、Delphes flavour 與 bit0 是不同層級。Massive ME 不會自動關掉 shower g→bb/cc；把任何 heavy shower 出生都 veto 掉也不是一項已證明的 subtraction。有限 shower cutoff、重建閾值及 hadronization 會影響 ancestry-based 類別。普通「jet 含任一 soft heavy quark」的 flavour 定義在 massless limit 可能欠缺 IR safety；應明確指定 flavour-aware truth jet 測度，再研究與 detector flavour 的 migration。[Banfi、Salam、Zanderighi，hep-ph/0601139](https://arxiv.org/abs/hep-ph/0601139)

**Photons。** QCD jet merging 並不處理所有 quark→photon collinear 或 photon soft singularities，也不能補出 detector fakes。Direct-photon observable 可採有明確適用範圍的 smooth-cone isolation；fixed-cone 目標通常需要另處理 fragmentation，兩者不能直接宣稱相同。MG5 3.5.16 模板存在 `ptgmin/R0gamma/xn/epsgamma/isoEM`；模板明示 `ptgmin>0` 時有不同於 pta/draj 的使用語意，但本次不選數值。各 multiplicity 必須有共同 photon 目標、足夠 generation-cut coverage，並另做 cut-loosening 和 reconstructed-isolation mapping。[Frixione，hep-ph/9801442](https://arxiv.org/abs/hep-ph/9801442)

**Scales、PDF、alpha_s。** 需共同凍結 flavour-number／threshold、PDF set/member/file hash、ME alpha_s 演化及 shower tune 的 ISR/FSR coupling。ME 和 shower 的 alpha_s 不一定必須數值相同，但任何差異都要明列理由和變化試驗。歷史 CTEQ6L1／fixed125 GeV 是既有來源設定，沒有因此成為新匹配生成的 validated default。匹配方法也可能重新指定 clustering scales，不能同時盲目固定 hard scales。

**Weights。** 新來源必須讀取 IDWTUP、event_norm、XWGTUP、signed sumW、sumW2、integration uncertainty、veto acceptance 與 multiplicity normalization。歷史 `event_norm=average` 的 sigma/N 語意不得套用兩次。CKKW-L 的本機文件把 event weight 與 merging weight 分開，並要求依 accepted cross section 處理不同 multiplicity；HepMC writer 究竟保留哪個量仍需獨立 closure。FxFx 則須保留負權重及 cancellations，不能只用 accepted count 當 normalization。[Pythia CKKW-L 文件](https://pythia.org/latest-manual/CKKWLMerging.html)

## 3. 候選比較矩陣

以下是審查摘要；JSON 的每一列另明列 flavour/PDF/alpha_s、photon IR、shower gsplit、weight、Njets 與 flavour-jet 定義。所有列 `exact_process_validated=false`。SUPPORTED_CANDIDATE 是可用 verdict，但此次沒有一列達到足夠支持來採用它。

| scheme | physics definition | software support | source evidence | expected advantages | known weaknesses | required validation | unresolved assumptions | scientific verdict |
|---|---|---|---|---|---|---|---|---|
| A_4F_BB_LOPS | massive b、4F incoming 的 bbγγ 成分 | SM mass source 存在；新 syntax 未執行 | 本機 SM、4F/5F paper | 明確 resolved bb、保留 mass | 初態 logarithms、與其他 HF 來源互斥未證 | 4F PDF／ME／PS／photon／權重 closure | 新 PDF、scale、互補樣本 | METHOD_ONLY |
| A_3F_CC_LOPS | massive c、無 incoming c/b | sm-c_mass 存在；3F interface 未定 | 本機 restriction | 可明確研究 charm mass | 3F PDF／PS 相容性未知 | 三味閾值、fragmentation、互斥 | 精確 PDF 與 normalization | UNVERIFIED |
| B_5F_MLM | 同一 aa＋0,1,2 QCD-parton family | generic LO MLM 存在 | MG LO、Pythia 8.317 | 避免手工另加 HF 完整樣本 | nQmatch=4 不匹配 b；QED/缺少 orders | exact histories、Nmax、DJR、veto、scale scan | xqcut/qCut、jet coverage | UNVERIFIED |
| B_5F_CKKWL | 同一 5F family 的另一種 merging | Process/TMS/hooks 存在 | MG LO、Pythia 8.317 | 可追蹤 no-emission/PDF weights | Process token 存在非 physical proof | histories、cut coverage、weight×merging closure | TMS、hard scales、Nmax | UNVERIFIED |
| B_FXFX_AA_CORE | colourless aa Born core 的 NLO family | generic NLO FxFx 存在 | 官方 FxFx、原始論文 | 潛在 NLO multijet accuracy | NLO loops／isolation／negative weights | NLO model、IR、production scales、normalization | 精確 diphoton NLO 支援及成本 | UNVERIFIED |
| B_FXFX_BB_CORE | bbγγ 當最低 multiplicity core | 違反官方 core 限制 | 官方 FxFx limitations | 僅可作為未來專門方法研究問題 | lowest core 含 b | 需另一個明確支援的擴充方法 | 本次未找到該擴充 | INAPPLICABLE |
| C_EXCLUSIVE_FLAVOUR | 同一 target measure 的完整 flavour partition | 沒有已驗證單一開關 | flavour-IR paper、本機 matching | 成分可能透明可追蹤 | ancestry veto 可有 gap／cutoff bias | common measure、coverage、orthogonality、IR | partition／subtraction 未建立 | METHOD_ONLY |
| C_RECO_VETO_SHORTCUT | 用 reco/bit0 重疊扣除現有來源 | 只有診斷 labels | 歷史 cards、flavour-IR paper | 描述性比較 | 非 perturbative subtraction | 必須更換為 generator 處方 | 物理共同測度缺失 | INAPPLICABLE |

MG5 官方 LO 文件確認 v2.5.0 起有 Pythia8 MLM／CKKW-L 介面；本機 3.5.16 模板也有對應欄位，這是介面存在的證據。[官方 LO 介面](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/LOPY8Merging) 本機 Pythia 8.317 JetMatching 文件明示 nQmatch=4 時 bottom 被獨立處理且未匹配，因此不可宣稱「4F MLM 自動排除全部 HF overlap」。[Jet Matching 文件](https://pythia.org/latest-manual/JetMatching.html)

FxFx 是 NLO matched multiplicity 的 merging 方法，歷史 LO LHE 不能以切換旗標轉換。官方操作頁限制最低 core 不得含 jets 或 b；因此 bbγγ core 方案在該處方下是 INAPPLICABLE。Colourless aa core 沒有這項明確 core 違規，但仍缺本題 NLO amplitudes、IR-isolation、HF multiplicities 和權重驗證，故仍為 UNVERIFIED。[官方 FxFx 要求與限制](https://amcatnlo.web.cern.ch/FxFx_merging.htm)、[Frederix、Frixione，arXiv:1209.6215](https://arxiv.org/abs/1209.6215)

## 4. 未來驗證順序與停止條件

1. 先選定唯一目標：限定 massive 4F bb 成分，或同一 5F aa＋QCD-jets family；不得把兩者完整預測直接相加。完整 diphoton 範圍須明列 tree、loop-induced、QED radiation/fragmentation 和 detector-fake 的邊界。
2. 在 source review 先凍結 exact model/restriction、PDF/alpha_s、hard scale、photon IR 目標、flavour-jet 測度、multiplicity family 和 ME/PS interface。
3. xqcut、qCut、TMS、FxFx qCutME 均保留 null。未來由 hard scale／ME cut／shower history 推導有限 grid，再獲 exact-source/card/hash 和有限資源上限核准後才允許任何生成。模板中的自動 sentinel/default 不是物理驗證值。
4. 在核准的小樣本中，檢查 jet differential rates、matching/veto efficiency、highest multiplicity、inclusive／HF-resolved cross sections、photon generation-cut loosening、signed weights 與 per-multiplicity normalization。Scale 變化的統計相關需保留；不能把視覺平滑當充分條件。
5. 遇到 gap、重複覆蓋、IR 不穩定、weight closure 失敗或 tail 統計不足即停止；資源 cap 到達只可得 inconclusive，不自動延長、不聲稱完成處方驗證。

本階段的數值重味診斷保留 `HEAVY_FLAVOUR_ORIGIN=VALIDATED_WITH_LIMITS`；`HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY=UNVERIFIED`、`PHYSICAL_TOTAL_BACKGROUND=BLOCKED`。未進行 physical significance、CLs 或 kappa interval。

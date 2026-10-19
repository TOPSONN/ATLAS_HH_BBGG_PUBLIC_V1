# Phase8E：真實數值 ROOT distributions 與 normalization

目標是對每組 source 分開建立完整 kinematics，並保留空 bin、flows、缺失值與權重語意。輸入為本次 full readback 的 7,100 筆事件；不以 synthetic arrays 或 published 100-event prefixes 代替完整分析。

## Observables、stage 與 binning

共 26 個一維 observables：m_gamma_gamma、m_bb、m_HH；兩個 selected photons 的 pT/eta；diphoton_pT；兩個 tagged eligible jets 的 pT/eta；dijet_pT；HH_pT/eta；DeltaR_gamma_gamma、DeltaR_bb、DeltaPhi_gamma_gamma、DeltaPhi_bb、DeltaR_Hgg_Hbb、DeltaPhi_Hgg_Hbb、DeltaEta_Hgg_Hbb；selected-photon/eligible-jet minimum DeltaR；全部 reconstructed Jet multiplicity、eligible native bit0 tag multiplicity、native ScalarHT。

ScalarHT 直接取已驗證的原生 ScalarHT.HT，沒有自行以不同 jet definition 重算。MissingET branch 有做 schema/readback checks，但本版本沒有增加未規劃的 MET histogram。

每個 observable 在 INPUT、PHOTONS、JETS、TWO_BTAGS、FINAL_MGG 填入。四組二維 correlations 為 mgg–mbb、mgg–mHH、mbb–mHH、pT_Hgg–pT_Hbb；兩軸都真正 defined 才填入。bin edges 版本化於 `analysis/phase8/config/histogram_edges_v1.json`；mgg、mbb、reco mHH、diphoton/dijet pT、DeltaR、jet/tag multiplicity 對應量重用歷史 Phase7D common bins，新增量另記 rationale。

## 四種 normalization

- RAW_EVENT_COUNTS：每個真正 defined 的事件貢獻 1。
- SOURCE_WEIGHTED：使用 source XWGTUP/N_original，不再次乘 cross section 或 BR。
- UNIT_AREA_SHAPE：source weights 連同 underflow/overflow 一起求和、一起 normalization；signed weights 保留。
- EXPLORATORY_LUMINOSITY_YIELD：source contribution 僅乘一次該 process 已驗證 model BR factor，再乘 1000×100 fb^-1。標籤固定為 ILLUSTRATIVE_MODEL_YIELD_100_FB_INVERSE，不能當作 calibrated ATLAS expected yield。

若 sumw=0 或 |sumw|<=64×double epsilon×sum_absw，UNIT_AREA_SHAPE 為 `UNDEFINED_ILL_CONDITIONED_OR_EMPTY_SHAPE`，不製造假 normalization。undefined mass 不填 0；histogram manifest 保留 missing_count、invalid_count、source N、normalization mode、weight scope、sumw/sumw2/sum_absw 與 flow policy。sumw2 的 template content 不與 full-N event-sampling variance 混為一談。特別是 UNIT_AREA_SHAPE 的 ROOT Sumw2 只保存標準 TH1 對 fill weights 的代數縮放，即原 sumw2 乘 normalization scale²；它沒有自動包含 normalization denominator 與各 bin 的共同事件相關性，因此不是 normalized-shape MC covariance。完整 normalized-shape uncertainty 必須另用 full-N delta method 保留 bin–total covariance，並在後續 shape comparison 數值驗證中獨立檢查。

## 實際 numerical outputs

八組×五 stages×(26 TH1D+4 TH2D)×四 modes 共 4,800 個規劃 histogram slots。實際寫出並重新打開驗證：

| 類型 | 已定義、寫出且回讀 |
|---|---:|
| TH1D | 4,052 |
| TH2D | 616 |
| 合計 | 4,668 |
| 未正規化的空/不適定 shape slots | 132 |

132 個沒有建立 UNIT_AREA_SHAPE template 的 slots 來自 B03 的 102 與 B06 的 30。其對應 raw/source/yield histograms 仍保留真實零內容與 missing counts。沒有以空檔案或人造峰填補低統計來源。

Canonical numerical histogram digest：

`4a8899dfde5b484d49e30438b704f81e77b648cb07d643e7360b0c181a2a9ed2`

Canonical content 逐一包含 dataset、stage、observable、normalization mode、unit、axis edges、每個 bin contents 與 sumw2，包含全部 flow cells。ROOT UUID/timestamps 可變，因此 raw ROOT binary hash 與此 scientific-content digest 分開處理。`phase8_validate` 實際重新打開所有已寫出的 TH1D/TH2D 並逐一重建 digest，結果為 `PASS_ACTUAL_NUMERICAL_ROOT_READBACK`。後續 repeat/independent tests 的最終結果由 Phase8L 統整。

## 實際 shape 描述與統計限制

INPUT candidate cohort 中，C1000 mgg median=124.9280 GeV；B04=124.9548、B05=125.0030 GeV，符合三者都有 H→γγ source 的 descriptive expectation，但不代表 calibrated response。B01/B02/B03 的 mgg medians 分別 100.7328/95.8686/104.1102 GeV，分布廣且 cohort 定義只要求 pair 存在；不能把這些全 input medians 直接解讀成 final-selected composition。

C1000 diphoton/dijet pT medians 為 152.0368/134.6329 GeV，HH-like pT median=56.0122 GeV；這些來源的 defined counts 不同，完整 denominator/missingness 已保留。B02 只有一個 FINAL_MGG event；B03/B06 FINAL_MGG 為零，因此不能靠平滑 histogram 外觀聲稱有精確尾端模型。後續每-bin ESS、support flags、common-source kappa covariance 由 Phase8F/H 提供。

## 物理解釋界線與後續

各 background 分開保存，沒有建立 B01+B02+B03 的物理 total background。B06 缺少 validated photon-fake model；B04/B05 BR 僅 MODEL_BR_ONLY，B05 spin effects 未完成驗證。C1000 仍有有效 PDF/alpha_s 與 future target 不匹配的 rate limitation。shape histogram 不能解鎖 physical S/B、significance、CLs 或 kappa inference。

本次沒有產生 PDF/PNG figures。未來若需要繪圖，先由同一 versioned numeric histograms 建立 local drafts，另經 exact path/hash/caption approval 才可 push。下一步是以固定、事先文件化的 variants 研究每個 source 的可支撐 shape，並保留 in-sample/exploratory labels。

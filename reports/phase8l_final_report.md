# Phase8L 完整既有資料分析驗收報告

**PASS_PHASE8_EXPLORATORY_ANALYSIS_WITH_LIMITS**。八組實際完整ROOT資料、重建、histograms、region partition、weights、shared-source κλ diagnostics 與synthetic likelihood方法均已執行。物理combined fit、significance、CLs與κλ limit維持blocked／not evaluated。

## 來源與工作樹

Base為 `b80e16775bf141e45f4048c7197a8a99befaed51`；新Linux ext4 checkout、ordinary .git、無alternates或gitlinks，在建分支前已驗證tracked source乾淨。Source content與compiled executables/dependencies精確SHA列於bounded evidence execution manifest。沒有修改PR24、舊Phase7I checkout、歷史資料或科學選擇。

ROOT 6.40.04 EXACT、C++20、existing conda GCC15.3.0；Delphes3.5.1採既有installed library，未重裝。新source使用現有strict DelphesAdapter/InputIndex/Physics helper，沒有MG5/ME/integration/shower/detector production dispatch。

## 實際資料與cutflow

| Dataset | 完整來源事件 | INPUT / PHOTONS / JETS / TWO_BTAGS / FINAL_MGG | Closure |
|---|---:|---|---|
| S01_B100 | 100 | 100 / 45 / 38 / 18 / 18 | 5/5 exact |
| S01_C1000 | 1000 | 1000 / 484 / 403 / 143 / 143 | 5/5 exact |
| B01 | 1000 | 1000 / 446 / 266 / 91 / 28 | 5/5 exact |
| B02 | 1000 | 1000 / 378 / 241 / 7 / 1 | 5/5 exact |
| B03 | 1000 | 1000 / 445 / 277 / 0 / 0 | 5/5 exact |
| B04 | 1000 | 1000 / 370 / 220 / 77 / 75 | 5/5 exact |
| B05 | 1000 | 1000 / 327 / 322 / 131 / 131 | 5/5 exact |
| B06 | 1000 | 1000 / 2 / 2 / 2 / 0 | 5/5 exact |

八組共7,100個獨立原始事件。另800個公開100-event prefix entries實際重讀，來源hash、ordinal、weights、stages、所有event-summary fields與full對應事件完全一致；新增獨立來源0。113個綁定input檔、共1,658,781,807 bytes在前後核對均相同。舊Phase7I HEAD與index SHA維持相同。

## 重建與histograms

| S01_C1000 observable | Defined / Missing / Invalid | Median (GeV) | Mean (GeV) | Sample std (GeV) |
|---|---|---:|---:|---:|
| mγγ | 484 / 516 / 0 | 124.928034519 | 124.930833573 | 1.38083747386 |
| mbb | 305 / 695 / 0 | 107.244163666 | 112.091352772 | 59.0057257437 |
| mHH | 143 / 857 / 0 | 397.521386774 | 439.230744189 | 145.189448351 |

實際ROOT含4,052個TH1D與616個TH2D，共4,668個有定義histograms；132個unit-area shapes因empty／ill-conditioned denominator明確保持undefined，不寫虛構template。26個observables、5個stages、4種normalization及4組TH2 correlations的所有計畫entries均有manifest狀態。

Canonical numerical content SHA256：`4a8899dfde5b484d49e30438b704f81e77b648cb07d643e7360b0c181a2a9ed2`。獨立Python重算180,989個CSV cells的content與Sumw2，並強制完整cell coverage、唯一性及所有flows；ROOT自身readback也核對每個canonical digest。另一次完整native分析的事件摘要、cutflow、reconstruction、histogram CSV及truth JSON逐byte相同，canonical digest相同；不以ROOT UUID要求binary byte identity。

## 權重、統計與κλ

XWGTUP_pb／original N只套用一次；source normalization與own model BR一次分開。S01_B100與C1000的PDF、alpha_s running和seed差異保留，不合併為1100個同設定SM事件。8組full cohorts的stage/bin fixed-N moments、ESS與conditional P0/P1/P≥2由Decimal70及獨立Poisson-binomial PMF驗證，合計378,351項數值比較通過。Observed MC sampling variance、conditional tag variance、generator integration errors與systematics不混加。

| κλ | Input ESS | Final ESS | Status |
|---:|---:|---:|---|
| -1.0 | 235.494846185 | 43.7733314173 | VALID_DESCRIPTIVE_ONLY |
| 0.0 | 503.655334264 | 78.309715798 | VALID_DESCRIPTIVE_ONLY |
| 1.0 | 1000 | 143 | VALID_DESCRIPTIVE_ONLY |
| 2.0 | 204.589404636 | 71.9809431525 | VALID_DESCRIPTIVE_ONLY |
| 2.5 | 36.6942995242 | 16.0735705156 | INCONCLUSIVE_REWEIGHTING |
| 5.0 | 19.5442226883 | 7.65012406875 | INCONCLUSIVE_REWEIGHTING |

6000行κ權重只來自1000個共同source events。五階段6×6 covariance的180個entries逐一獨立核對，symmetry/finite/PSD以明確roundoff tolerance通過，沒有eigenvalue clipping。逐observable/bin ESS、dominant fractions及source counts保留；2.5／5不被當成足夠支持的physical benchmarks。

## Regions、shape與physical gates

每個dataset有3種互斥tag類別×5種mass狀態，共15個partition、全體120筆region summaries。包含低sideband、Higgs window、高sideband、outside與undefined，計數與sumw均閉合至原photon+jet eligible denominator。0/1tag沒有杜撰mbb/mHH pair。

B01/B02/B03 ME/PS heavy-flavour overlap未解決；六個背景分別分析，沒有相加的physical background。ZH與ttH只屬MODEL_BR_ONLY，ttH另有spin modelling限制。B06缺乏校準fake-photon模型。B03與B06的0/1000 final count，其proposal success probability單邊95%上界為0.0029912495451；不是weighted cross-section或fake-rate上界，也不表示零物理背景。

Shape比較是固定分箱descriptive metrics，normalized-bin variance保留bin-total covariance。100≤mbb≤150、diphoton pT、ΔRbb、mHH分類只屬預宣告in-sample變體，沒有最佳化顯著度。22種systematics的physical unknown values、constraints與correlations保持null。

## 方法與regression

- Native CTest 9/9 PASS，包括3項既有ROOT step1 regression。
- Python unittest 92/92 PASS，包含truncated/duplicate/missing-cell/source/hash、zero/signed weights、prefix完整度、resource timeout與orphan process-group negative tests。
- Actual RooFit/RooStats synthetic methods 26/26 PASS；Asimov μ=0.999999806946、EDM=1.723×10⁻¹²。
- 五個既有signal/new-background/MG5-LHE/Pythia-HepMC/Delphes frozen-reference validators全部PASS。
- 獨立完整native/historical event-level regression、Decimal70 moments/covariance、prefix readback與repeatability全部PASS。

曾出現的compile errors與兩項toy closure failures均保存在本機execution receipts；修正後對最終source重新建置並完成全套測試。Hessian covariance與bounded parameter error之差、以及tightened Minuit convergence的因果說明見Phase8J。

## 資源與輸出

Main contained build/analysis/regression commands在final assembly前的測得CPU 284.271481 s、command wall 303.389013 s；peak observed RSS 863653888 bytes。輕量source檢視與報告編輯的CPU未列入這個計時範圍；這不是human conversation elapsed time。原始attempts也保留於資源記錄。

Aggregate ceiling為4h CPU／4h command wall、1job／1worker、2GiB額外analysis output；實際測量與各command exits見execution manifest。Wrapper實際負測試證明timeout及leader退出後殘留child都會清除process group並fail，沒有自動重試或擴大budget。

所有新genuine ME、integrals、independent events、Pythia events、Delphes events皆為0；未執行RouteA build/restart。完整ROOT、所有histogram CSV、event summaries、templates與SHA256 manifest保留本機。GitHub只選29個bounded numeric/source identity artifacts，總量小於0.5MiB（每件精確bytes與SHA見payload manifest），沒有PDF/PNG、raw ROOT/event files或native binaries。

## GitHub與證據範圍

本報告在publication之前由實際local receipts產生。GitHub source-only workflow驗證Python方法/config與frozen public references，不宣稱cloud CI重跑private full ROOT。最後PR head、remote changed-blob byte/SHA核對、全部final-head CI conclusions與完整FINAL_REPORT由publication receipt記錄；PR上的Checks與最終交付報告為其完成狀態。只建立一個stacked Draft PR，不merge、不force push。

## 未解決項目與下一步

技術gate已通過；physical overlap、fake calibration、official detector/systematic calibration與κλ=2.5／5支持仍blocked，相關uncertainties未知而非0。下一步是審查本次source與數值證據，取得獨立校準資料及source-definition方案；任何新physical production都需另外授權。本次不以完成analysis宣稱ATLAS physics precision、發現、顯著度或limit。

Native implementation與方法source commit：`19faeaf487fb1f9b49ff00f5cf85eeeb1c949930`。該commit的所有C++／Python／config bytes均與execution manifest source hashes相符；後續publication commits加入metadata、數值證據、報告、CSV byte-preservation設定與其SHA regression；不改變該次native分析或科學計算。

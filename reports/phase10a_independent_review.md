# Phase10A：Phase9 精確來源、既有資料與選定算式的獨立檢閱

日期：2026-10-19。結論：`PASS_INDEPENDENT_PHASE9_REVIEW_WITH_LIMITS`。

「獨立」指另行實作的來源身份連結、選取及數值核對，不是把同一份 Phase9 報告讀兩次，也不是外部獨立研究者或人類審查人的正式簽署。`external_independent_human_approval=false`。本檢閱沒有批准圖表發布或物理推論。

## 精確來源與發布層次

- Phase9 最終交付／PR26 base：`ebae34fdaf9ccb09c77bd47cb1c7827fa560de0a`。
- Phase9 執行來源 capture：`2584e342b80b20c314392d20d77d92a6ccb850c4`。
- 以精確 Git object 核對 44 筆固定於執行版本的來源清單條目；它們不與最終交付文件混稱為同一 commit 的 bytes。
- 從執行 capture 到交付 base 的實際差異嚴格等於三條已聲明路徑：`metadata/phase9_quality_gates.json`、`metadata/phase9_source_manifest.json`、`reports/phase9_final_report.md`。來源清單中的 gates 與 final report 兩筆採精確 BASE blob；任何額外 science-source 差異或 allowlist 擴張均拒絕。
- 另行來源稽核 `origins_03` 的 7 個 runtime module hashes 與 `statistics_02` 的 2 個 runtime module hashes：各自 before=after，且 9 個 hashes 均等於執行 capture 的 Git blobs。

舊 Phase9 checkout `/home/btu/projects/atlas_hh_phase9_v1` 保持 clean，HEAD=上述 BASE，Git index SHA-256=`16bafc85092721f3dd5c70764c4c9516049be363fb7211c8d8564fa4ced7f3cb`，與 Phase10 initial audit 相同。新 Phase10 工作目錄的開發狀態不能用來推斷歷史 checkout 被修改；最終 A05 中被檢閱的既有發布路徑也沒有新的 worktree divergence。後續 Phase10 build 採獨立 CMake 工程，root CMake 保持 BASE。

發布身份核對使用精確 BASE Git blobs、Phase9 當時實際下載保存在 `remote_final_head/` 的 88 個 response body bytes、原始下載 receipt 的 SHA-256／bytes，以及舊 Phase9 checkout。四者逐檔相同。本項屬 `HISTORICAL_SOURCE_AUDIT`，沒有把舊的遠端下載 receipt 冒稱為本次新的 HTTP 遠端驗證；Phase10 新 head 的遠端驗證由交付流程另行執行。

## 實際既有資料與全 6000 個來源連結

本次 `ACTUAL_EXISTING_DATA_READBACK` 逐一讀取 B01–B06 各 1000 個原始事件的現存 LHE 與原始 HepMC event bytes，連結 Delphes input index event header、Phase9 native persisted row 與 ancestry details。核對 source ordinal、LHE source-content SHA、原始 HepMC event SHA、native event number、original N、raw XWGTUP、XWGTUP／N，以及 hard outgoing PID。6 個 ordered-source identity digests 均等於 Phase9 原始 native readback receipt。

實際核對 30 個來源檔案的存在、非 symlink、完整 SHA-256 與 manifest bytes：每個樣本各有 detector ROOT、input index、LHE、HepMC、detector card。ROOT 檔在此做 byte hash 與歷史 receipt 綁定；本檢閱的新增 native ROOT loops=0。不能因為讀過 persisted JSONL，就宣稱再獨立逐 entry 讀了一次 ROOT TTree、particle tuple 或全部 native flavour algorithm。

Phase8 的 7100 個原始獨立來源包括兩個歷史 signal cohort 共 1100 個事件與上述 6000 個背景。本 A05 新的逐事件來源連結範圍只有 6000 背景；signal cohort 與 κλ common-source reweight 的既有來源證據屬歷史稽核／後續 precision 工作，不虛增為本檢閱的新獨立 hard statistics。

## 選取、原生欄位與分母

獨立選取實作不 import Phase9 classifier、production statistics、event reconstruction 或 review 程式。只重用已驗證的 LHE／HepMC byte streaming parsers；輸入索引只解析必要的 event header，沒有重寫完整 reader。

photon pT>25、|η|<2.37，排除開區間 1.37<|η|<1.52；leading photon pT>35。jet pT>25、|η|<2.5。依 native pT／index 排序，bit0 使用 `(native_btag_bits & 1) != 0`，不以 flavour 或「bits 非零」替代。mγγ 另以質量為零的雙 photon 解析式 `sqrt(2 pT1 pT2 [cosh(Δη)−cos(Δφ)])` 重新計算，最終 broad window 包含 105 與 160。

| 樣本 | INPUT | TWO_PHOTONS | TWO_JETS | TWO_BTAGS | MGG 105–160 |
|---|---:|---:|---:|---:|---:|
| B01 | 1000 | 446 | 266 | 91 | 28 |
| B02 | 1000 | 378 | 241 | 7 | 1 |
| B03 | 1000 | 445 | 277 | 0 | 0 |
| B04 | 1000 | 370 | 220 | 77 | 75 |
| B05 | 1000 | 327 | 322 | 131 | 131 |
| B06 | 1000 | 2 | 2 | 2 | 0 |

全部 6000 個 event stage flags、eligible object index 與 bit0 多重數重算後保持歷史 cutflow；共核對 16569 個 eligible native jet 的 bit0。native／ancestry jet 欄位按原始 jet index 逐事件連結，flavour 與 tag 分別保持。這是 persisted native 欄位身份與選定圖見證核對，不是新的全樣本 Delphes native-flavour 重建。

## 重味與 photon 起源的選定獨立檢查

原始 Pythia diagnostic 檔先與生成 run manifest SHA 綁定，再對下列三個事件自行處理 status/mothers、同 flavour copy 抑制、直接 gluon 的 signed 重味子對，以及 terminal hadron 的最近 jet 幾何指派。沒有 import Phase9 `births()` 或 `classify_heavy_flavour()`。

| 樣本：source index | ME outgoing 重味 records | shower bottom/charm births | 直接 g→重味對母粒子 | terminal b/c hadrons | hadron-cone labels（依 eligible jet index） |
|---|---:|---:|---|---:|---|
| B01:1 | 2 | 0/0 | [] | 2/4 | {"0": 5, "1": 5, "3": 0} |
| B02:1 | 2 | 0/0 | [] | 0/2 | {"0": 0, "1": 4, "2": 4, "3": 0} |
| B03:997 | 0 | 2/0 | [17] | 2/3 | {"0": 5, "1": 0, "2": 0, "3": 0, "4": 5} |

B03 source997 的 source-event SHA 是 `322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8`；直接 splitting mother=17。此見證保留 hard-light 與 shower/hadron/native-heavy 的層級差異，不能藉此認定 B01/B02/B03 的生成器定義互斥。

這三個見證是選定原始圖交叉檢查，不是把 3000 個重味 event graphs 全部以另一個算法重分。全事件的 origin flags 由獨立程式根據凍結註記重建，與已發布 HF 事件旗標 CSV 比較 1200 個 Decimal70 數值欄位。多母字串的 sole-hadron endpoint 保持 `UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED`；B02 的 4 筆與 B03 的 2 筆非唯一／缺失 Pythia tuple binding 亦保留，未強制建立粒子身份。

photon 逐事件重新數出 selected origin composition，檢查配對 truth-ID 互斥、prompt 註記的 copy chain 與已驗證 hard root 有交集、radiation 註記包含原始 shower status。實際 selected objects 為 prompt-hard 6298、radiation 24、electron-associated 3、unclassified 674；全部 native photon objects 中 unclassified 為 756。這些是起源註記與來源證據的一致性檢查，沒有宣稱全面重新追蹤所有 photon graphs。未分類保持未知，不改稱 fake；calibrated fake probability 仍為 null。

## 權重、稀有事件與 MC covariance

權重直接由原始 LHE raw XWGTUP／固定 original N 重算；selection failure 保持原始 cohort 中的零貢獻。各樣本 own MODEL_BR_ONLY factor 比對 manifest 並只乘一次，沒有把物理 integration uncertainty 或 detector systematic 混入 source sampling SE。

以另一套 Decimal70 和矩公式重算 stage／region sumw、sumw2、固定 N variance、ESS 與 own BR factor，共 510 個已計數比較。固定 N variance 是 `N/(N−1)×[Σx²−(Σx)²/N]`，不是把選中事件數當作新的分母，也不是單用 Σw² 的 Poisson 假設。稀有邊界的 exact binomial 區間使用獨立 Python binomial CDF inversion；Wilson 端點 k=0、k=N 明確保留 0、1。

B02 final=1/1000，exact 95% `[2.531748749e-05,0.005558924280]`；B03/B06 final=0/1000，單側 95% 上限 `0.002991249545`。零經驗貢獻與零經驗 variance 不證明物理背景為零。這些區間只描述目前 IID source proposal 接受機率，不是 cross-section 或 photon fake probability。B06 two-photon stage 僅 2/1000、final 0，不能用作 fake-rate 測量。

另由 persisted event observables，獨立重算 108 個背景 normalized shape histogram 的分箱事件數、raw source moments 與 bin-total shared-event covariance，計數 3862 個數值比較。underflow/overflow 保持在各自定義值的分母；缺失 m_bb/m_HH 不被補成零。m_bb/m_HH 的重建數值本身沿用已驗證 persisted observables，這項 histogram 算術核對不是新的全部四向量重建。重味非互斥 origin 的完整固定 N covariance 另見 Phase10B。

## 區域互斥與 histogram 原始身份

由 `02_TWO_JETS` 中的 native tag 0、1、≥2，與 mγγ 的 LOW `[105,120)`、HIGGS `[120,130]`、HIGH `(130,160]`、OUTSIDE、UNDEFINED 分區。count、source sumw、variance 與 own BR-only contribution 均重算；tag<2 的 m_bb/m_HH null contract 保持。不同區域是一個來源事件的互斥分類；不同 origin flags 則刻意非互斥。

Phase8 historical histogram manifest 具有 4800 個 logical descriptors，其中 132 個為明確的 undefined empty/ill-conditioned unit-area shapes，沒有 dimension 與 numerical hash，也沒有寫成 ROOT object。實際 ROOT object 是 TH1D 4052 + TH2D 616 = 4668。此區分避免把未定義 shape 當作可用物理模板。

canonical numerical-content SHA-256 在 manifest 與歷史實際 native ROOT validation receipt 完全相同：`4a8899dfde5b484d49e30438b704f81e77b648cb07d643e7360b0c181a2a9ed2`。這一項為 `HISTORICAL_SOURCE_AUDIT`，本 A05 沒有重新讀取 4668 個 ROOT objects；不能將 receipt 綁定升格為新的 native content loop。

## CRLF 與 publication bytes

以下 11 個 CSV 的 BASE Git blob、當時保存的實際遠端 bytes 與舊 checkout 完全相同；沒有先換行正規化再比較。CRLF 數亦等於 LF 數。

| 發布 CSV | CRLF 結尾數（含 header） | Git blob／保存遠端 bytes |
|---|---:|---|
| phase9_bin_quality.csv | 4561 | 完全相同 |
| phase9_heavy_flavour_origins.csv | 981 | 完全相同 |
| phase9_kappa_support.csv | 7 | 完全相同 |
| phase9_mc_planning.csv | 43 | 完全相同 |
| phase9_photon_origin_study.csv | 751 | 完全相同 |
| phase9_rare_event_precision.csv | 41 | 完全相同 |
| phase9_region_diagnostics.csv | 121 | 完全相同 |
| phase9_region_observables.csv | 1081 | 完全相同 |
| phase9_shape_metrics.csv | 865 | 完全相同 |
| phase9_shape_ratios.csv | 1605 | 完全相同 |
| phase9_source_tail_support.csv | 41 | 完全相同 |

12 組 Phase9 local figures 維持既有 `QA_PASSED`／`AWAITING_USER_APPROVAL`，沒有重生成。任何成功測試、數值核對或本次檢閱，都不構成精確 figure path/hash/caption/provenance 的發布批准；本次 figure publication=NO。

## Reviewer checklist 與限制

| 稽核項目 | 結果 | 證據類型 |
|---|---|---|
| EXACT_PHASE9_SOURCE_AND_PUBLICATION_BYTES | PASS | HISTORICAL_SOURCE_AUDIT |
| FULL_6000_RAW_LHE_HEPMC_INDEX_NATIVE_PERSISTED_JOINS | PASS | ACTUAL_EXISTING_DATA_READBACK |
| INDEPENDENT_SELECTION_BIT0_WEIGHTS_REGIONS | PASS | ACTUAL_EXISTING_DATA_READBACK |
| SELECTED_RAW_PYTHIA_GRAPH_WITNESSES | PASS | ACTUAL_EXISTING_DATA_READBACK |
| INDEPENDENT_RARE_INTERVALS_AND_FIXED_N_STATISTICS | PASS | ACTUAL_EXISTING_DATA_READBACK |
| PHOTON_UNKNOWN_AND_MULTI_MOTHER_UNKNOWN_PRESERVED | PASS | ACTUAL_EXISTING_DATA_READBACK |
| HISTORICAL_4668_ROOT_CANONICAL_BINDING | PASS | HISTORICAL_SOURCE_AUDIT |
| EXACT_CRLF_CSV_GIT_BLOB_IDENTITY | PASS | HISTORICAL_SOURCE_AUDIT |
| SCIENTIFIC_PHYSICAL_BLOCKERS_PRESERVED | PASS | HISTORICAL_SOURCE_AUDIT |

這些 PASS 表示欄列所定義的 source／既有資料核對已實際完成，不能延伸為物理總背景、匹配處方或 detector calibration 的批准。重建 phase-space sharing 不能直接證明 perturbative double counting，也不能證明無 double counting。heavy-flavour generator exclusivity 仍 UNVERIFIED；physical fake rate 仍 UNKNOWN；matched signal normalization 仍 BLOCKED_PHASE7I。single-Higgs normalization、fast-simulation calibration、physical nuisances/correlations 與有限 MC bin support 的限制仍保留。

## 執行修正與可重現性

保留 `independent_phase9_review_01` 至 `_04` 四個失敗 attempt 的 log、execution receipt 與當時 source-hash 記錄；它們不是最終 PASS，也沒有被覆寫。四項失敗皆為 checker 的操作／schema 契約修正：Wilson 浮點零端點；執行版本與已聲明 final-delivery 文件的版本區別；新 Phase10 工作目錄與歷史 Phase9 checkout 的來源區別；4800 logical descriptors 與 4668 native objects 的計數區別。原始科學 cutflow、來源 bytes 與數值結果沒有因此被更動，亦沒有把這些 checker failures 捏造成新科學偏差。

最終使用重新凍結的 reviewer 與其 HF helper 來源執行 A05，before/after source hashes 相同，實際 PASS receipt 為 `/home/btu/simulations/hh_phase10/run_01/review_05/phase10a_review_receipt.json`。A+B bounded fixtures 共 34 項通過，涵蓋 zero statistics、固定 N covariance、ME/shower 分離、bit0、UNKNOWN、shape flow/empty guards、delivery allowlist、saved remote/base tamper 與 histogram schema。整體 Phase10 CI／regression／最終 head 綁定由交付報告另列，不能以此 34 項代替所有專案檢查。

實作為 `analysis/phase10/scripts/review_phase9.py`、`analysis/phase10/source/hf_stratification.py`；只使用原始資料的來源讀取與算術，不產生新 ME、積分、hard events、Pythia 或 Delphes events。物理總背景保持 BLOCKED；significance、CLs 與 κλ 物理區間均 NOT_EVALUATED。

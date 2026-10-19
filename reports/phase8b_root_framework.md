# Phase8B：原生 ROOT/C++20 分析框架

本階段的目標是在保持歷史物理定義與資料不變的條件下，對八組既有 Delphes ROOT 樣本實際執行 native readback、事件重建與數值直方圖填入。證據類型為 `ACTUAL_FULL_DATA_READBACK`；程式已讀取 7,100 筆原始事件記錄，沒有產生新的 ME、integration、LHE、Pythia 或 Delphes events。

## 實際輸入與環境

`S01_B100` 有 100 筆；`S01_C1000` 與 B01–B06 各有 1,000 筆。完整來源與 SHA256 見 [Phase8A](phase8a_data_provenance.md) 及 `metadata/phase8_dataset_manifest.json`。B100 與 C1000 的有效 PDF/alpha_s 設定不同，分析分開保存兩者，不合併成 1,100 筆同質 SM sample。

| 已使用工具 | 實際身分 |
|---|---|
| ROOT | 6.40.04，ROOT 本身 C++20 |
| C++ compiler | conda-forge GCC 15.3.0-7；`x86_64-conda-linux-gnu-c++` |
| Compiler SHA256 | `e802ef021bccd09d2ae1dae3f9400e53ab2c2c7bc2b4e47dc29a81c7ec3bcd31` |
| CMake / Ninja | 4.4.4 / 1.13.2 |
| Delphes | 既有 3.5.1 installed library |
| Installed libDelphes SHA256 | `e4fcd4d433bdfc231672f75b70ee08e830bd6169570d1e6611583fb2dd02fef8` |
| C++ dialect | C++20；extensions OFF |

分析使用原本 `atlas-hh-root` 環境，沒有重新安裝工具。編譯輸出位於 source checkout 外。Top-level `ATLAS_BUILD_PHASE8` 預設 OFF；實際 Step1 與 CI 結果由 Phase8L 最終驗證報告分別列出。

## 架構與演算法

直接重用 `simulation/delphes/include/DelphesAdapter.hxx` 中的 `Adapter`、`InputIndex`、native particle tuple，以及 `Physics.hxx` 的 P4、signed-mass policy、matching。沒有複製整套 ROOT reader，也沒有把歷史 `.cxx` 與其 `main()` 包進新 executable。

新的 `Phase8Reader` 組合這些已審查元件；其差異在於同時支援 signal、continuum、new-background 三種既有 truth-index profile，對每組資料在同一 native event loop 完成 source correspondence、selection、reconstruction、truth matching、26 個 observables、五個 stage 的直方圖與 bounded event-level summary。所有 selection-failed events 仍保留 original ordinal、source weight 與五個 stage bits，後續統計可以完整使用 original N 與零貢獻。

ROOT 物件保留真正的 `TClonesArray`，不假設為 ATLAS Open Data RVec。required branches 為 Event/HepMCEvent、Weight/Weight、Particle/GenParticle、Photon/Photon、Jet/Jet、GenJet/Jet、MissingET/MissingET、ScalarHT/ScalarHT。實際八組也都有 Track、Tower、Electron、Muon、EFlowTrack、EFlowPhoton、EFlowNeutralHadron、GenMissingET optional branches；這些分別依實際 native class 記錄。

讀取拒絕 zombie、recovered、writable input、external friend、錯誤 clone class、未載入 dictionary、streamer version/checksum 不符與 array-size 不一致。每個事件驗證 Event.Number、完整 Weight vector、native particle 的 PID/status/float32 p4/mass/position multiset、ancestry index 範圍及有限數值。source key 為 dataset_id + 1-based source_event_ordinal + native_event_number，不跨 dataset 用 event number 合併。

## 數值結果

| Dataset | 原生讀取且驗證的事件 | 對照 native Particle tuples | 合法微小 signed jet mass 數量 |
|---|---:|---:|---:|
| S01_B100 | 100 | 51606 | 12 |
| S01_C1000 | 1000 | 539836 | 62 |
| B01 | 1000 | 426370 | 64 |
| B02 | 1000 | 468551 | 83 |
| B03 | 1000 | 470232 | 80 |
| B04 | 1000 | 353821 | 107 |
| B05 | 1000 | 644591 | 96 |
| B06 | 1000 | 547708 | 54 |

共比較 3,502,715 個 native Particle tuples；558 個微小負 signed jet masses 依歷史 double-cancellation bound 保留原始四向量。invalid、skipped 與 duplicate event key 計數均為 0。這項 signed-mass 記錄不是把負質量強制改為正值。

CLI 提供 `audit`、`analyze`、`validate`、`summarize`、`methods-test`；完整 RooFit/RooStats synthetic methods 由 `phase8_methods` 執行。分析 executable 沒有 simulation-generation mode。錯誤 dataset、hash、樣本 N/version、object class、binning、mode，以及既有輸出覆寫均被拒絕。實際可重現命令見 `analysis/phase8/README_ZH_TW.md`。

## 驗證、限制與後續

實際完成 schema audit、7,100-event native loops、八組歷史 cutflow closure，以及輸出 ROOT 的 TH1D/TH2D numerical readback。原生回讀以 source tuple/multiplicity 驗證 correspondence，不把 native Particle array 排序當成 HepMC barcode。reference-prefix、獨立回歸與 canonical repeat 的最終執行狀態由 Phase8L 彙整；不以 method test 取代 full-data readback。

目前 detector 是 ATLAS-like Delphes model，沒有官方 photon ID、trigger、GN2、JES/JER 或 calibrated scale factors。框架的成功執行不解除 background overlap、fake photon、signal PDF/alpha_s 與低 ESS 限制。下一個科學步驟是先完成這些獨立 normalization/calibration gates，再透過相同 Dataset interface 匯入另行授權且驗證的新來源。

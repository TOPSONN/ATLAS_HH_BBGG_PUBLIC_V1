# Phase8D：Higgs candidates、HH-like 四物件重建與 truth diagnostic

本報告使用本次實際 full ROOT readback 的 reconstructed photons 與 jets。目標是建立真實、可缺失的候選變數與 source-corresponded truth checks；不把 continuum background 人為指定成 truth HH。

## 重建定義

Hgg 使用 leading two selected photons，P4 取 native PT/Eta/Phi 與零 photon mass；Hbb 使用 leading two native bit0-tagged eligible jets，保留 native signed-mass policy。HH-like candidate 為兩候選四向量相加。只有對應 pair 存在才定義 mass/pT/eta/phi；沒有兩個 tagged jets 時 m_bb、相關 m_HH 與角度為 null，不補入 untagged jets。P4 pT=0 時沒有定義的 eta/phi 亦保留 null。

候選定義與 cutflow stage 分開。mgg 只要有兩個 fiducial PT>25 photons 即可存在；leading>35 是另一個 cut。因此 continuum 的 mgg defined count 可以大於 PHOTONS count。mbb 可在 photon selection 前已存在；mHH 需要兩個 pair。對 background 的 mHH 名稱只表示四物件 invariant mass，不代表宣稱有兩個 truth Higgs。

重用已審查的 long-double Cartesian P4。native negative Mass 只接受 |M²|<=16×double epsilon×|p|² 的歷史 cancellation envelope，並保留 E²=p²-|M²| 的 signed native convention。summed-vector m² 只容許 64×long-double epsilon×max(E²,1) 的 roundoff，超過則失敗；不以任意截斷修補物理向量。

## 實際重建結果

下面是所有 input events 中真正有候選者的無權重描述統計，未先限定 FINAL_MGG。單位皆為 GeV；missing 保持分母。

| Dataset | mgg defined | mgg median | mbb defined | mbb median | mHH defined | mHH median |
|---|---:|---:|---:|---:|---:|---:|
| S01_B100 | 45 | 124.865029 | 31 | 107.324392 | 18 | 407.081903 |
| S01_C1000 | 484 | 124.928035 | 305 | 107.244164 | 143 | 397.521387 |
| B01 | 484 | 100.732757 | 215 | 135.299688 | 98 | 349.170138 |
| B02 | 417 | 95.8686271 | 13 | 145.860715 | 7 | 395.125648 |
| B03 | 473 | 104.110227 | 4 | 105.692766 | 0 | null |
| B04 | 371 | 124.95478 | 182 | 82.2914505 | 77 | 312.940183 |
| B05 | 328 | 125.002988 | 386 | 153.966465 | 131 | 410.555323 |
| B06 | 2 | 57.7912337 | 335 | 102.45362 | 2 | 230.47229 |

C1000 重新計算得到 mgg median=124.92803451905755、mbb median=107.24416366634247、mHH median=397.5213867738351 GeV；defined counts 分別 484/305/143，missing 分別 516/695/857，invalid 均為 0，符合歷史 descriptive regression。完整 min/median/mean/sample_std/max 與 defined/missing/finite counts 保存在 `phase8_reconstruction_statistics.csv` 和 JSON summary；不是把 median 當 calibration target。

B03 雖在全 input 中有四個 tagged-dijet candidates，但沒有同時可定義的 diphoton+dijet 四物件 candidate；其 mHH 全部為 null，而不是 1000 個零質量。B06 兩個 diphoton masses 為 43.0918556 與 72.4906118 GeV，均未通過 baseline mass window；這不提供 jet→photon fake probability。

## Truth matching 與歧義

Signal 由獨立 upstream InputIndex particle IDs 及 `signal_truth.dat` 取得 Higgs/daughter lineage，先與 native retained particle tuple multiset 對應。native Particle 順序不被當成唯一 barcode。Hgg photons 對全部 reconstructed photons 使用 R<0.2；Hbb birth bottoms 對 eligible jets 使用 R<0.4。重用 maximum-cardinality、minimum-total-distance matching，明列 ambiguous graph degrees。

| Signal | Hgg 0/1/2 matches | Hbb 0/1/2 matches | Hbb ambiguous truth / reco | Missing ancestry |
|---|---|---|---|---:|
| S01_B100 | 9 / 30 / 61 | 1 / 38 / 61 | 2 / 0 | 0 |
| S01_C1000 | 60 / 299 / 641 | 43 / 402 / 555 | 24 / 3 | 0 |

C1000 的 Hgg 60/299/641 與 Hbb 43/402/555 由實際本次資料重現。兩組 signal Hgg ambiguous truth/reco 都是 0；Hbb 的 ambiguity retained，沒有靜默移除。matching ΔR 保存在 bounded local JSON。這些是 geometric matching diagnostic，不是 calibrated detector efficiency；同一事件的物件也不是獨立 binomial trials。

B01–B06 的完整 HH truth comparison 為 `NOT_APPLICABLE_NO_TRUTH_HH`。B04/B05 可用的單一 H-origin photon lineage 在 event summary 另有獨立紀錄，沒有被當作 signal 的雙 Higgs truth。原生碼對其他背景不創造 truth HH。

## 驗證、限制與後續

native source、完整 Weight vector 與 tuple comparisons 通過；26 observables 的 finite/missing 分開追蹤。獨立比較需要考慮歷史 signal pT_gamma_gamma/pT_bb 使用 std::to_string 的 6-decimal serialization；新結果保存 17-digit precision，不能把此差異視為 physics selection migration。

目前候選質量與分布只描述既有 Delphes model 與 selection。不能由 mbb 的 median 回寫任意 detector correction，也不能以 pair reconstruction 等同 truth origin 純度。下一步是利用 actual matching ambiguity、region 與 bin-level MC support，建立有 source identity 的 shape diagnostic；物理 calibration 與新的 matched signal source 仍需獨立驗證。

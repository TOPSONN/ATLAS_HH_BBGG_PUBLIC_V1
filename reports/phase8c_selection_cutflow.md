# Phase8C：歷史 baseline selection 與 cutflow closure

目標是以真實 full ROOT event readback 重現已審查的 Phase6C/7D cuts，而非調整 cuts 使數字接近參考。下列 7,100 筆事件均使用本次原生 ROOT 分析讀取，證據類型為 `ACTUAL_FULL_DATA_READBACK`。

## 選擇與分母

Photons 先依 native PT 遞減排序，相同 PT 以原始 index 決定。篩選 PT>25 GeV、|eta|<2.37，排除 1.37<|eta|<1.52；至少兩個 selected photons，leading selected photon 另外要求 PT>35 GeV。閾值直接比較 native Float_t 的持存數值，不以重新計算的 P4 pT 替代。crack 的端點在數學定義上為開區間；native Float_t serialization 的相鄰可表達數值另有 boundary regression。

Jets 依 native PT 遞減排序並以原始 index 解 tie，要求 PT>25 GeV、|eta|<2.5。至少兩個 eligible jets，並至少兩個 `(Jet.BTag & 1) != 0` 的 jets；其他 tag bits 保留，不用 BTagAlgo 或 BTagPhys 替代。這不是官方 calibrated ATLAS GN2 working point。最後要求 105<=m_gamma_gamma<=160 GeV。baseline 沒有 m_bb cut，也沒有新加 isolation、trigger 或 identification。

五階段固定為 INPUT、PHOTONS、JETS、TWO_BTAGS、FINAL_MGG。每組原始 input N 為唯一分母；不以 survived events 重新正規化。

## 實際 full-run 結果

| Dataset | INPUT | PHOTONS | JETS | TWO_BTAGS | FINAL_MGG | Final / original N |
|---|---:|---:|---:|---:|---:|---:|
| S01_B100 | 100 | 45 | 38 | 18 | 18 | 18.0000% |
| S01_C1000 | 1000 | 484 | 403 | 143 | 143 | 14.3000% |
| B01 | 1000 | 446 | 266 | 91 | 28 | 2.8000% |
| B02 | 1000 | 378 | 241 | 7 | 1 | 0.1000% |
| B03 | 1000 | 445 | 277 | 0 | 0 | 0.0000% |
| B04 | 1000 | 370 | 220 | 77 | 75 | 7.5000% |
| B05 | 1000 | 327 | 322 | 131 | 131 | 13.1000% |
| B06 | 1000 | 2 | 2 | 2 | 0 | 0.0000% |

八組五階段共 40 個 actual/expected counts 的差值全為 0，均為 `FULL_CUTFLOW_PASS`。selection config SHA256 為 `4273803c4061302d0aa8f93201a05877bc926a92afbcea1439407a12a3f3c022`。這些數字由本次 event loop 累積，並非直接填入歷史參考值。

## 權重與統計

`phase8_cutflow_raw.csv` 保存 raw counts 與相對原始/前階段效率；`phase8_cutflow_weighted.csv` 分開保存 source sumw、sumw2、sum_absw、正/負/零權重事件數與 fixed-N source sampling variance。使用 upstream source_contribution=XWGTUP/N_original，不再次乘 generator cross section，cutflow 本身不重複乘 BR。

source-event variance 使用獨立 statistics module 的 shifted/centered accumulator，對每階段保留完整 original-N 貢獻向量，未通過者為零。它對應 N/(N-1)×[sum(x_i²)-sum(x_i)²/N]，但實作避免接近常數權重時直接相減造成 cancellation。sumw2 及此 fixed-N variance 分開報告；不把已包含 native tag draw 的 sampling variance 再加同一 conditional tag variance。

B03 與 B06 最後觀察到 0 筆，不代表物理 background 為零。N=1000、0 successes 的單邊 95% proposal-count upper bound 為 1-0.05^(1/1000)=0.00299124954509533；它不是沒有 weight bound 時的 weighted cross-section bound，也不是 photon fake rate。

## 驗證與解釋界線

本次對 full ROOT 實際數量、source ordinals、native event/weights/particle tuples 與 card hash 同時通過才報 closure。100-event published reference prefix 的測試另以 `REFERENCE_PREFIX_TEST` 標示，不拿它比對 1000-event full cutflow。獨立回歸與最終 CI 狀態集中於 Phase8L。

B100 仍為獨立 CTEQ6L1/one-loop pilot；C1000 為有效 NNPDF23 LO/two-loop exploratory signal，不合併成同質 source。B01/B02/B03 unresolved ME/PS heavy-flavour overlap、B06 缺少 validated photon-fake model，因此本報告不相加物理 background、不計算 physical significance 或 limit。下一步是分別研究已定義 regions 與 support，並補足各自的物理 gate。

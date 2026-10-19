# Phase10B：既有事件的重味分層與重建來源交叉診斷

日期：2026-10-19。`HEAVY_FLAVOUR_ORIGIN=VALIDATED_WITH_LIMITS`；`HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY=UNVERIFIED`；`PHYSICAL_TOTAL_BACKGROUND=BLOCKED`。

## 證據與統計單位

本次 `ACTUAL_EXISTING_DATA_READBACK` 使用 Phase9 已有的 native JSONL 與 ancestry event details。實際連結 6000 個 B01–B06 來源事件，分層對象為 B01、B02、B03 各 1000 個原始獨立 hard-source 事件。重用已凍結的 Phase9 ancestry 註記，另行實作 ME outgoing flavour、事件旗標、交叉分層與統計算式；本程式沒有新增 native ROOT event loop，也沒有把此項讀回宣稱為完整獨立圖重新分類。選定原始圖的獨立核對範圍見 Phase10A。

全部 jets 屬於同一個來源事件群集。不能把兩個 jet、兩個重強子、同一事件多個 origin flags 或不同階段當成額外獨立事件。本次輸出 2220 列分層（300 列非互斥旗標、1920 列已觀察交叉格）、6000 列旗標共同事件協方差、60 列跨樣本比較（15 列特徵格、45 列質量形狀）。每個樣本、每個階段的互斥交叉格事件數相加，均回到該階段實際來源事件數。

`ME flavour × shower flags × eligible-jet hadron flavour set × eligible native flavour set × native bit0 tag category` 是事件層級交叉格。flavour set 只記錄該事件中出現的標籤集合，不保留 jet 排序或每種 flavour 的 jet 多重數；tag 分為 0、1、≥2。`ME flavour` 由 LHE outgoing PID 分類；shower line birth 與 incoming heavy record 是原始 Pythia status/mother 的不同概念；hadron 幾何指派、Delphes native flavour 與 bit0 都保留各自定義。不能要求五個層級一致。

## 實際來源旗標

下表是事件數，不是重味粒子數；旗標可在同一個事件重疊。例如 terminal charm hadron 可來自 bottom hadron 衰變，不能因為 B01 具有 charm hadron 就改稱 ME charm。

| 事件旗標 | B01 input | B02 input | B03 input | B01 final | B02 final | B03 final |
|---|---:|---:|---:|---:|---:|---:|
| 硬製程 bottom | 1000 | 0 | 0 | 28 | 0 | 0 |
| 硬製程 charm | 0 | 1000 | 0 | 0 | 1 | 0 |
| 硬製程 light/gluon | 0 | 0 | 1000 | 0 | 0 | 0 |
| ME incoming heavy record | 58 | 69 | 6 | 2 | 0 | 0 |
| shower bottom-line birth | 53 | 36 | 49 | 3 | 0 | 0 |
| shower charm-line birth | 170 | 211 | 183 | 5 | 0 | 0 |
| 已證明直接 g→重味對 | 211 | 240 | 220 | 8 | 0 | 0 |
| 存在 terminal b hadron | 1000 | 36 | 49 | 28 | 0 | 0 |
| 存在 terminal c hadron | 1000 | 1000 | 221 | 28 | 1 | 0 |
| eligible native bottom jet | 860 | 13 | 18 | 28 | 0 | 0 |
| eligible native charm jet | 38 | 902 | 62 | 0 | 1 | 0 |
| eligible jet 有重強子 | 856 | 890 | 82 | 28 | 1 | 0 |
| 硬 light／native heavy | 0 | 0 | 79 | 0 | 0 | 0 |
| 原生 bit0：0 tags | 331 | 813 | 971 | 0 | 0 | 0 |
| 原生 bit0：1 tag | 454 | 174 | 25 | 0 | 0 | 0 |
| 原生 bit0：≥2 tags | 215 | 13 | 4 | 28 | 1 | 0 |

`HAS_ME_INITIAL_HEAVY_FLAVOUR_RECORD` 依據原始 |Pythia status|=21 的重味 ME record，與 |status|=23 的 outgoing record 分列。它不被當作 shower birth；這個計數本身尚未建立四味／五味生成器處方。shower birth 先排除同 signed-PID 母粒子的延續 copy，使用 |status|=41–59。直接 g→重味對則要求 shower gluon 的直接子粒子中同時存在同一重味的 q 與 anti-q；不能以任何重味祖先代替此證明。

## 各階段 source 權重與支援

每事件 raw source contribution 為實際 LHE XWGTUP／原始 N：B01 `6.6246662e-05 pb`，B02 `0.0006274417 pb`，B03 `0.0094365561 pb`。三個 cohort 目前各自為等權重；每一旗標的完整 sumw、sumw2、variance、ESS、原始 N 接受率及條件於該 input stratum 的接受率均保留於 CSV。這些單樣本 raw source 數值不構成可相加的物理總背景。

| 樣本 | 階段 | 事件數／1000 | raw source sumw [pb] | 固定 N sampling SE [pb] | ESS |
|---|---|---:|---:|---:|---:|
| B01 | 00_INPUT | 1000 | 0.06624666 | 0 | 1000 |
| B01 | 01_TWO_PHOTONS | 446 | 0.02954601 | 0.001041846 | 446 |
| B01 | 02_TWO_JETS | 266 | 0.01762161 | 0.0009261261 | 266 |
| B01 | 03_TWO_BTAGS | 91 | 0.006028446 | 0.0006028148 | 91 |
| B01 | 04_MGG_105_160 | 28 | 0.001854907 | 0.0003457749 | 28 |
| B02 | 00_INPUT | 1000 | 0.6274417 | 0 | 1000 |
| B02 | 01_TWO_PHOTONS | 378 | 0.237173 | 0.009625687 | 378 |
| B02 | 02_TWO_JETS | 241 | 0.1512134 | 0.008490242 | 241 |
| B02 | 03_TWO_BTAGS | 7 | 0.004392092 | 0.001655062 | 7 |
| B02 | 04_MGG_105_160 | 1 | 0.0006274417 | 0.0006274417 | 1 |
| B03 | 00_INPUT | 1000 | 9.436556 | 0 | 1000 |
| B03 | 01_TWO_PHOTONS | 445 | 4.199267 | 0.1483738 | 445 |
| B03 | 02_TWO_JETS | 277 | 2.613926 | 0.1336103 | 277 |
| B03 | 03_TWO_BTAGS | 0 | 0 | 0 | 未定義 |
| B03 | 04_MGG_105_160 | 0 | 0 | 0 | 未定義 |

INPUT 固定 N sampling SE=0 反映目前等權且全事件通過的條件抽樣算式；生成積分誤差、proposal 不確定度、物理正規化與 detector systematics 均未因此變成零，也沒有被合併到此 SE。

B02 final 的接受率為 1/1000，ESS=1，相對 raw-source sampling SE=100%。雙側 95% Clopper–Pearson 區間為 `[2.531748749e-05, 0.005558924280]`；不能以單一事件支援可靠的細分物理模板。B03 final 為 0/1000，雙側 95% exact 上限 `0.003682083897`，單側 95% 上限 `0.002991249545`；零經驗 sumw、variance 不代表物理背景為零，也不能由 p_hat=0 得到有限且保證的相對精度需求。Wilson 與稀有邊界 exact 區間只描述目前 IID proposal 的事件接受機率，不是物理 cross-section 或 fake-rate 信賴區間。

## 交叉格實例

下表每個樣本列出 `02_TWO_JETS` 事件最多的三格；完整交叉格及未留下事件的階段零列均保留。各層級差異是待建模的事實，沒有被強制改成同一 flavour。

| 樣本／02_TWO_JETS | ME | shower B/C/gpair | hadron flavour set | native flavour set | tags | 事件數 | raw source [pb] |
|---|---|---|---|---|---|---:|---:|
| B01 | ME_BOTTOM | B0_C0_GPAIR0 | 5 | 5 | TAG_1 | 47 | 0.003113593 |
| B01 | ME_BOTTOM | B0_C0_GPAIR0 | 5 | 5 | TAG_GE2 | 38 | 0.002517373 |
| B01 | ME_BOTTOM | B0_C0_GPAIR0 | 0+5 | 5+21 | TAG_1 | 26 | 0.001722413 |
| B02 | ME_CHARM | B0_C0_GPAIR0 | 4 | 4 | TAG_0 | 63 | 0.03952883 |
| B02 | ME_CHARM | B0_C0_GPAIR0 | 0+4 | 4+21 | TAG_0 | 47 | 0.02948976 |
| B02 | ME_CHARM | B0_C1_GPAIR1 | 4 | 4 | TAG_0 | 25 | 0.01568604 |
| B03 | ME_LIGHT_OR_GLUON | B0_C0_GPAIR0 | 0 | 2+21 | TAG_0 | 90 | 0.84929 |
| B03 | ME_LIGHT_OR_GLUON | B0_C0_GPAIR0 | 0 | 2 | TAG_0 | 36 | 0.339716 |
| B03 | ME_LIGHT_OR_GLUON | B0_C0_GPAIR0 | 0 | 1+2 | TAG_0 | 24 | 0.2264773 |

## 非互斥旗標的完整共同事件協方差

令 x_ia = w_i × I(stage_i) × I(flag_a,i)，未通過的原始來源事件貢獻為零。使用固定原始 N 的估計式：

`C_ab = N/(N−1) × [Σ_i x_ia x_ib − (Σ_i x_ia)(Σ_i x_ib)/N]`。

所有 20 個旗標的 20×20 對稱矩陣，依 3 個樣本與 5 個階段完整輸出；包含非互斥 origin 的共享事件項。ESS=(Σx)²/Σx²。條件接受率使用相同來源事件的 numerator/denominator residual 與共同分母協方差，沒有假設獨立 jets。

| 樣本 | 階段 | 旗標 a / b | 同時存在事件 | 固定 N covariance [pb²] | correlation |
|---|---|---|---:|---:|---:|
| B01 | 00_INPUT | shower bottom / native bottom | 48 | 1.063109e-08 | 0.03113072 |
| B01 | 02_TWO_JETS | shower bottom / native bottom | 20 | 6.475302e-08 | 0.2391431 |
| B02 | 00_INPUT | shower bottom / native bottom | 13 | 4.938575e-06 | 0.5938823 |
| B02 | 02_TWO_JETS | shower bottom / native bottom | 5 | 1.946741e-06 | 0.6432226 |
| B03 | 00_INPUT | shower bottom / native bottom | 18 | 0.00152586 | 0.5964482 |
| B03 | 02_TWO_JETS | shower bottom / native bottom | 3 | 0.0002644716 | 0.5201335 |

這些 covariance 描述單一來源 cohort 的抽樣關聯，不能充作不同物理過程間的 nuisance correlation，亦不能消除 ME/PS 生成器重疊問題。

## 歧義與 UNKNOWN 保留

| 樣本 | eligible jet 的 UNKNOWN endpoint 註記列 | 非唯一／缺失 Pythia tuple entries | hadron 幾何指派平手事件 | native flavour 邊界歧義事件 |
|---|---:|---:|---:|---:|
| B01 | 2097 | 0 | 0 | 0 |
| B02 | 2322 | 4 | 0 | 0 |
| B03 | 2218 | 2 | 0 | 0 |

UNKNOWN endpoint 數字是 Phase9 在 eligible jet 註記列所保留的 sentinel 數，包含沒有被指派重強子的 jet；不是「每列都已證明存在多母重強子」的計數。具有重強子的字串／多母粒子祖先仍未被指定到唯一 perturbative endpoint。B02 的 4 筆與 B03 的 2 筆非唯一／缺失 tuple binding 保持原樣；不能把它們與 native cone 邊界歧義事件數混為一談。本 cohort 的 native flavour mismatch 與未分類 heavy-quark birth 旗標為零，只限目前可檢查的定義，不代表所有 ancestry 都已唯一解決。

## 分開的跨樣本特徵與形狀比較

特徵格比較刻意拿掉 ME 標籤後，比較相同 shower／hadron／native／tag 事件特徵是否在兩個獨立樣本中出現。此步驟是有限樣本的觀察支援診斷，不是生成器 subtraction 或物理 process union。

質量形狀使用凍結 Phase8 的 mγγ、mbb、mHH edges，保留 underflow/overflow，並以每個樣本自己的 defined-event raw source sumw 正規化。下表的 mγγ defined N 分別為 B01 266、B02 241、B03 277，沒有遺漏值；JS 使用自然對數，CDF 指標為分箱 CDF 的最大差。

| 樣本對／02_TWO_JETS | 共用特徵格 | 樣本 a 位於共用格／總數 | 樣本 b 位於共用格／總數 | mγγ JS（自然對數） | mγγ CDF 最大差 |
|---|---:|---:|---:|---:|---:|
| B01/B02 | 3 | 8/266 | 3/241 | 0.02110975 | 0.09356378 |
| B01/B03 | 2 | 3/266 | 95/277 | 0.01412692 | 0.03785185 |
| B02/B03 | 6 | 19/241 | 113/277 | 0.02044398 | 0.1101757 |

在同一個兩 photon／兩 jet 階段，B01/B02 的 mbb defined support 僅為 91/7，B03 為 0；B03 相應 mbb、mHH 形狀比較保持 `UNDEFINED_EMPTY_OR_ZERO_WEIGHT_SUPPORT`。B02 final 只有一個事件，final 形狀指標至多是該單事件的描述，不能形成可靠的物理形狀結論。

重建區域共有特徵或相似 mγγ 形狀，並不證明 perturbative ME/PS double counting；觀察到很少共有格亦不證明生成器互斥。需要將 flavour scheme、ME/PS interface、matching/merging、jet multiplicity、photon isolation 與 source-level closure 一起驗證；本次仍不形成 B01+B02+B03 的物理總和。

## 精確來源與可重現產物

- native Phase9 JSONL SHA-256：`6535b5722c930898c3b7313af88ab62f492602be41eb6684c422ed90c19708eb`。
- ancestry event details SHA-256：`33e735989b03b98b49b98ad6eadbcc1681fb188d0e1380e0921dad98d639f45c`。
- 這兩個 hash 另與 Phase9 `independent_hf_validation.json` 原始輸入 receipt 相同；不是以新 report 互相引用取代資料身份驗證。
- frozen histogram edges SHA-256：`f3e0d1bda28f8b2415660a567c1aaa2d5dfea745d120d603fbae16b370d274c9`。
- 實際數值目錄：`/home/btu/simulations/hh_phase10/run_01/hf_02/`。
- 產物：`phase10_hf_strata.csv`、`phase10_hf_covariance.csv`、`phase10_process_overlap_diagnostics.csv`、`phase10_hf_summary.json`。
- 實作：`analysis/phase10/source/hf_stratification.py`、`analysis/phase10/scripts/stratify_existing.py`。

本分層沒有新 ME、積分、hard event、Pythia 或 Delphes production。物理背景總和仍為 BLOCKED；significance、CLs 與 κλ 物理區間均未評估。沒有建立或發布 PDF/PNG 圖。

## 執行狀態與 checker 修正範圍

B 分層以凍結來源的 `hf_02` 實際執行通過；沒有因 A 的 checker 修正重算或改寫 Phase9 origin 註記。A 的四個失敗 attempt 保留原始 log／execution receipt，分別修正 Wilson endpoint、執行與交付版本、工作目錄與歷史 checkout、logical descriptor 與 native object 的 checker 契約，並非本 B 結果的科學失敗。最終 A05 PASS 及其獨立範圍限制見 `phase10a_independent_review.md`。B 不宣稱外部人類簽署或全面獨立 graph reclassification。

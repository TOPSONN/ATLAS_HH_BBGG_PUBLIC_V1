# Phase9C：光子來源與 fake model 可行性

## 目的與證據層級

目標是釐清 B01–B06 的既有光子來源、重建物件的幾何關聯，以及目前能否定義可校準的 fake background。光子來源分類屬 `ACTUAL_EXISTING_DATA_READBACK`；process/run cards 屬 `HISTORICAL_EVIDENCE_AUDIT`；方法負例屬 `SYNTHETIC_METHOD_TEST`；官方文獻可用性屬 `PUBLIC_CALIBRATION_SOURCE_AUDIT`。四者不能互相替代。

**PHOTON_FAKE = BLOCKED_CALIBRATION_UNAVAILABLE。** 未匯入任何 restricted ATLAS calibration、內部材料或未驗證的 rate。

## 輸入與 frozen process 定義

使用既有完整 LHE、HepMC3、可用的原始 Pythia diagnostic ledger、native Delphes photon collection，以及 Phase8 selection。來源關係綁定 source-event SHA256、HepMC event SHA256、dataset 與 ordinal；HepMC ID、Pythia index、ROOT collection index 分開處理。

| Dataset | Frozen process 的光子範圍 | 校準限制 |
|---|---|---|
| B01 bbγγ | 兩個 direct tree-level ME photons | 不含完整物理背景組合或官方 ID 校準 |
| B02 ccγγ | 兩個 direct tree-level ME photons | 同上 |
| B03 jjγγ | 兩個 direct tree-level ME photons | 同上；light Born jets 不排除 shower heavy flavour |
| B04 ZH | hard H 保持穩定，由既有 Pythia H→γγ decay 提供光子 | H-decay lineage 明確；不是 continuum photon-fake sample |
| B05 ttH | hard H 保持穩定，由既有 Pythia H→γγ decay 提供光子 | 保留原 top／spin／MODEL_BR 限制 |
| B06 bbγj | 一個 direct tree-level ME photon | 沒有 validated jet→photon response |

B01–B03 的 frozen Born cuts 為 photon pT 25 GeV、|η| 2.5、ΔRγγ 與 ΔRγj 0.4。`ptgmin=0` 關閉 run-card Frixione block，因此不可僅因 card 存在 R0γ／εγ／n 欄位就聲稱使用了 Frixione isolation。這些 parton-level cuts 也不是 ATLAS tight ID／isolation。小型 source-card audit 逐一核對原有 SHA；實際 assignments 與 card locators 寫入 photon-card evidence。

## 分類方法與 selection

`phase9_photon.py` 對所有 stable truth photons 與所有 native reconstructed photons作診斷；另分開紀錄 selected photons。native selected flag 使用 frozen Phase8 acceptance，baseline cutflow 不變。

只沿同 PDG=22 的 photon-copy chain 追溯到 first non-photon parents。不能沿整個碰撞祖先圖尋找任何 hadron，否則幾乎所有 pp 光子都會被 beam proton 誤判成 hadron decay。

- `PROMPT_HARD_PROCESS`：copy chain 包含由原始 ledger／decay lineage 綁定、且經 HepMC identity mapping 驗證的 hard photon root；也涵蓋明確 H→γγ 來源。
- `SHOWER_RADIATION`：birth node 的**原始 Pythia status** 為 ISR／FSR 範圍 41–59，且有對應 emitter parent。不可用轉換後 HepMC status 猜測原始 Pythia status。
- `HADRON_DECAY`：first non-photon parent 有 hadron 證據；優先使用原始 `is_hadron` flag，缺少時使用明列的標準 meson／baryon PDG-digit 判別。
- `ELECTRON_ASSOCIATED`：明確 electron parent，或沒有 photon contender 時的唯一 stable-electron cone association；不等於量測到 electron fake probability。
- `UNCLASSIFIED`：證據缺少、互相衝突或 association ambiguous，保持明確 unknown。

LHE／HepMC p4 接近只作 serialization diagnostic，不把它當成 source identity 或 prompt origin 的替代證據。

Native association 使用嚴格 ΔR<0.2，要求 cone 中唯一 stable photon、該 truth photon 未被另一重建物件共用，且沒有 stable-electron contender。多光子、shared truth 或 electron conflict 均保留 unclassified。這是偏保守、明確可重現的 **geometric association**；沒有 detector shower-shape 或 fake response 的校準含義。

## 實際數值結果

最終 `origins_03` 已實際讀取並分類 B01–B06 各1000個原始事件，共6000個；其執行期間 source hashes 前後一致。數值權威為 `phase9_photon_origin_study.csv` 與 `phase9_origins_summary.json`；CSV包含150個 event-indicator rows及600個 object-multiplicity rows，兩種單位明確分開。

以下 **selected reco object counts** 涵蓋整個各1000-event cohort 中符合 photon acceptance 的物件，沒有要求該事件已通過兩光子、雙tag或final mass cuts。

| Dataset | Prompt hard | Shower／radiation | Hadron decay | Electron associated | Unclassified | Selected reco objects |
|---|---:|---:|---:|---:|---:|---:|
| B01 | 1287 | 3 | 0 | 0 | 98 | 1388 |
| B02 | 1155 | 7 | 0 | 0 | 138 | 1300 |
| B03 | 1238 | 0 | 0 | 0 | 115 | 1353 |
| B04 | 1092 | 4 | 0 | 0 | 93 | 1189 |
| B05 | 965 | 8 | 0 | 3 | 176 | 1152 |
| B06 | 561 | 2 | 0 | 0 | 54 | 617 |

合計8079個 native reco objects，其中6999個符合 selected acceptance；這些是物件數，不能當成6999個獨立事件。全部 selected classes 逐物件互斥且閉合。

相同 truth kinematic acceptance 下，既有 stable truth photons 的 hadron-decay counts 為 B01 56、B02 59、B03 105、B04 39、B05 324、B06 93。它們不一定被重建為 photon object，也不一定通過 exclusive cone association。重建類別中的 hadron-decay observed zero 不代表不存在 nonprompt photons，更不能定義官方 hadron→photon fake probability。674個 selected objects 保持 unclassified；它們不是已證明的 fake objects。

Final-stage event indicators 如下；檢查所有accepted photon objects，並非僅限用來重建mγγ的leading pair。同事件可同時含prompt、radiation或unclassified objects，因此列內類別不能相加成互斥 background partition。

| Dataset | Final surviving events | ≥1 prompt object | ≥1 radiation object | ≥1 electron-associated object | ≥1 unclassified object |
|---|---:|---:|---:|---:|---:|
| B01 | 28 | 28 | 0 | 0 | 4 |
| B02 | 1 | 1 | 0 | 0 | 0 |
| B03 | 0 | 0 | 0 | 0 | 0 |
| B04 | 75 | 75 | 0 | 0 | 12 |
| B05 | 131 | 128 | 1 | 1 | 32 |
| B06 | 0 | 0 | 0 | 0 | 0 |

上述CSV weighted quantities皆為原始 source contribution pb；沒有重新乘sigma/N或另加BR。Object multiplicity variance先在原始事件內加總所有物件，再計算完整N的事件 sampling variance，沒有將同一事件的光子當成獨立抽樣。

最終 photon CSV SHA256：`aca72e8876bbf9f87fb61c2b8a1f915b4586c2132a65c26d18070143c81c9497`；origins summary SHA256：`86db961fb6c51fe545f1bc4670edc08bc4dbb49340e47952452e0f1c65a97ab5`。

## B06 與 observed zero

B06 frozen LHE 每事件一個 Born photon；本次實際重現 cutflow **1000／2／2／2／0**。通過 two-photon selection 的兩個來源事件為：

| Source event | Reco photon labels | mγγ（GeV） | Final mass cut |
|---|---|---:|---|
| 69 | 兩者unclassified；各cone均有多個stable-photon contenders | 72.490612 | FAIL |
| 245 | 一個已綁定Born lineage的prompt photon＋一個有原始Pythia status −51證據的radiation photon | 43.091856 | FAIL |

事件245的radiation photon與native object距離ΔR=0.00117129；Born-lineage photon距離ΔR=0.00871333。這證明該模型中第二個重建物件可以由實際QED radiation提供；不是量測到jet fake。事件69的歧義保持unknown，沒有依最近距離強迫選一個truth photon。Source hashes與完整matched IDs保留在local event details。

一個 Born photon 的 bbγj source，加上不含正式假光子 transfer model 的 Delphes response，不能定義最終物理 fake background。0／1000 只表示此 proposal、此模型與此 finite sample 下沒有 final survivor；不是零物理背景。對未加權 Bernoulli acceptance，單側95% upper bound 為 `1-0.05**(1/1000)`；不是 weighted fake cross-section 的信賴上界。

## 公開 calibration source audit

已實際閱讀兩份官方 ATLAS 論文的公開版本；metadata `photon_calibration_audit.json` 記錄 official source／version、period、energy、object definition、transfer semantics、applicability、uncertainties 與 license。

[ATLAS HH→bbγγ 論文，arXiv:2112.11876v2／PRD 106 (2022) 052001](https://arxiv.org/abs/2112.11876v2) 描述 Run-2 2015–2018、13 TeV 的 tight photon ID／isolation 資料 sideband 方法。文中的 composition fraction 是指定 analysis preselection 的條件組成，不是 local Delphes 的 per-jet fake probability；continuum shape 另受 data-sideband normalization 與 bias tests 約束。公開全文採 CC BY 4.0。這是方法參考，沒有把其 fraction 乘進本地 MC。

[ATLAS photon efficiency 論文，arXiv:1810.05087v2／EPJC 79 (2019) 205](https://arxiv.org/abs/1810.05087v2) 使用2015–2016、13 TeV 資料，提供 prompt-photon ID data/MC ratio，並另量測 electron→photon transfer。其 electron transfer 的分母是 matching electron control selection；它既不是 jet fake probability，也不是本次幾何關聯率。Converted／unconverted、tight ID、tracking 與 isolation definitions 尚未與本地 Delphes 建立相容性，因此不匯入任何數值。公開全文採 CC BY 4.0；其 auxiliary portal 擷取失敗保留 `ACCESS_UNVERIFIED`，沒有推論 auxiliary 資料不存在。

結論是：**本次查閱的公開資料未提供已通過本地物件／分母／control-to-target compatibility 的 calibration input**。這不宣稱全世界不存在適用的公開輸入。未知的 transfer values／uncertainty covariance 維持 null。

## 驗證與負例

方法測試涵蓋 hard-root proof gate、只追 photon copies、beam-proton 誤分類防護、hadron／electron／radiation、缺少原始 status、p4近似不可提升 identity、dangling／cycle、unique cone、多重 association、phi wrapping、strict radius、source-hash mismatch、nonfinite 與 missing-calibration guards。公開 efficiency／purity payload 不能通過 `VALIDATED_COMPATIBLE_DATA_CALIBRATION` gate。本模組獨立執行44／44項 synthetic source／classification／evidence negative tests 通過。 其後對final `origins_03` 執行獨立Decimal70驗證：6000個事件、750個aggregate rows（150 event indicators＋600 object multiplicities）、6300項數值比較、120項object aggregate checks全部PASS。驗證沒有匯入production classifier／statistics模組，另外重建event indicators、完整N source variance、事件內object multiplicity variance與conditional fraction numerator–denominator covariance。第一次舊150-row verifier因新增600個object rows而fail的收據保留；修正後以嚴格750-row contract與12項新增negative fixtures驗證，沒有只放寬row-count門檻。公開收據：[independent_photon_validation_final.json](../analysis/phase9/evidence/independent_photon_validation_final.json)。所有 object counts 與 event indicators 保持不同分母；class object-count closure 必須等於相應 collection 大小。Event indicators 可同時在一個事件出現多種類別，因此跨類別的 event sums 不能當成互斥 partition 相加；逐物件 origin labels 則互斥且完整。

## 未解問題與未來策略

1. 先凍結目標 tight／anti-tight、isolated／nonisolated、conversion 與 electron-denominator definitions，依 pT、η、b-tag／flavour 環境明列適用範圍。
2. 在另行授權且物件相容的資料中建立 ID–isolation control regions，估計 prompt leakage、ID/isolation correlation、雙物件 correlation 與 trigger／subtraction effects。
3. Electron→photon 使用獨立 Z→ee／eγ control transfer，不能與 jet→photon 合併；處理不同物種、分母與 shared-event covariance。
4. 在0／1／≥2-tag 與 diphoton-mass sidebands驗證 transport closure，保留 extrapolation、finite-control-data 與 composition uncertainty。
5. 另行授權的 matched／merged prompt photon+jets 與完整 decay／radiation MC 可測 composition 和模型依賴；detector fake response 仍需資料驗證。
6. 公開 source／version／license、object compatibility、bin support、transfer semantics、correlations 與 control-to-target closure 全部通過後，才可建立 physical fake yield。本任務沒有啟動新 generation。
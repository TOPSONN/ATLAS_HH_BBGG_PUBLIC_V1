# Phase11C：direct-photon IR 定義與真實 MG5 3.5.16 LO 語意

結論：smooth-cone direct-photon observable 的方法與本機 LO 實作可追蹤；**物理數值、massive-bottom 的隔離涵蓋，以及 detector mapping 尚未封閉**。本階段沒有產生 cross section、沒有新 cut-independence 證據；`photon_ir.json` 的所有 production threshold 都是 null/BLOCKED。

## 定義目標與理論邊界

[Frixione 原始文獻](https://arxiv.org/abs/hep-ph/9801442) 定義 smooth-cone 隔離：對每顆 photon、對 R0 內所有子錐 r，要求 hadronic transverse energy 滿足

`Σ pT_i(r_i≤r) ≤ ε pTγ [(1−cos r)/(1−cos R0)]^n`。

當 n>0，r→0 的允許 hadronic energy 趨近零，保留 soft 輻射同時排除 photon–massless-parton 的 collinear fragmentation 區域。這是所定義 direct isolated-photon cross section 的性質；不是所有 detector isolated photons 的完整包含式預測。單純 fixed cone 允許極靠近 photon 的有限 hadronic energy，不能自動免除 fragmentation 問題。QED shower 輻射也不是已校準 fragmentation-function contribution。

正的 photon pT 下限處理 soft-photon 區域；smooth cone 本身不規範額外 QCD partons 的 soft/collinear singularity。B family 必須另外有一致的 jet-resolution/merging 與 multiplicity prescription。A 的 massive b 可使特定 collinear limit 有質量正規化，卻不會將不同隔離 observable 變成相同。

## 本機 LO 實作的具體結果

以下指向 `/home/btu/opt/mg5amcnlo` 實際 3.5.16；整檔 SHA256 和 anchor 行存入新的 family/IR source-audit receipt。不是依 NLO template 推論 LO。

| 欄位/行為 | 真實來源 | 解釋與限制 |
|---|---|---|
| `ptgmin` | LO `cuts.f:1090` | 不等於零即進隔離段；物理候選須要求正值，不能利用負值取得不一致行為 |
| `r0gamma`, `epsgamma`, `xn` | `cuts.f:1341–1352` | 實作 exponent 是 abs(xn)；xn=0 退化為 constant bound，沒有 r→0 的 smooth suppression |
| QCD energy sum | `cuts.f:1092–1105,1149–1165` | 只加 `is_a_j` 的 pT，按 photon distance 排序逐累積檢查；不包含 `is_a_b` |
| flavour 分類 | LO `setcuts.f:216–224` | abs(PDG)≤maxjetflavor 分到 is_a_j，較重但≤5 分到 is_a_b；gluon 強制 is_a_j |
| maxjetflavor=4 的 b | 同上 | b 被排除於 smooth-cone QCD sum，這是 A 的具體未解 observable 問題 |
| maxjetflavor=5 的 b/c | 同上 | 本 B 的 massless b/c 都可進入 smooth-cone QCD sum；這只是來源涵蓋條件 |
| `isoEM` | `cuts.f:1119–1134,1169–1194` | true 時另作其他 photons 與 charged leptons 的 isolation sum，排除被檢查的 photon 自身；不等於 detector EM shower-shape ID |
| `pta`, `draj` override | `banner.py:4244–4251` | ptgmin>0 時將正的 pta 與 draj 設成 0；不是兩套 independent photon cut 同時生效 |
| `drab` | `setcuts.f:356–357` | 是 photon–is_a_b separation，未被上述 override 關閉；不可錯認跟 draj 一樣失效 |
| photon pT mapping | `setcuts.f:298–304` | generic etmin=max(pta,ptgmin)，其餘 etaa、etaamin、ptamax 等需逐項凍結 |
| diphoton minimum mass | `setcuts.f:393` | 真正 run-card 名稱是 `mmaa`，映射 pair mass²；不是杜撰 `mmgg` 欄位 |
| acceptance ordering | LO `cuts.f:314–326,411–481,1083–1206` | generic pT、eta、DeltaR、pair-mass 等先行，smooth isolation 在後，任一失敗就 return |
| isolation 幾何與 frame | `cuts.f:1084–1086,1287–1295` | parton CM momenta，DeltaR 使用 pseudorapidity difference；對 massless particles/pT 的 longitudinal boost 性質不等於完整 detector 定義 |

MG5 banner 的來源預設值（例如某些 hidden isolation 欄位）只能作程式行為證據，**不構成這次選定的物理配置**。本次沒有把它們填到 future selected card。

## A 的 bottom coverage 不能略過

4F incoming 定義並不唯一決定 `maxjetflavor` 的 cut 分類。若 A 採 maxjetflavor=4，LO smooth cone 不計 b，獨立 drab 仍可能切掉 b–γ 區域。若改 maxjetflavor=5，會連動 b 的 generic jet cuts、分類、merging cut 等，也不能只改一個名稱便宣稱已封閉。需要先選擇明確 target：接受原始 massive-b 限制 observable，或審核能處理所有所需 QCD constituents 的隔離實作。當前不選擇、不改 generator source，A_bottom_coverage 仍為 null/BLOCKED。

## 數值與 acceptance closure

`ptgmin/r0gamma/xn/epsgamma/isoEM/etaa/mmaa/draa/draj/drab` 和相應 jet/bottom cut 都沒有 production 數值。若未來提出值，須逐項寫明 target acceptance、文獻或歷史源的理由，標記 `PROPOSED_NOT_PHYSICALLY_VALIDATED`，再以另行授權的敏感度檢查建立 closure。本次不把歷史 histogram window 或 Delphes cone 直接抄成 generation default。

現有 Delphes PhotonIsolation 是固定 detector cone、相對 isolation 加上持久化前篩選，與 parton smooth cone 的材料、動量、pileup/overlap 及解析度不同。即使兩者使用相近 radius，也需要新 shower/particle/detector migration 比較，不能宣稱等價，也不能由現有被截斷的非隔離分母測得 photon fake rate。

## 可執行的方法測試與未執行的物理檢查

`test_family_ir.py` 以 synthetic algebra 檢查 smooth-cone 零半徑極限、外錐界、單調性、abs(xn)、xn=0 反例；另一個 synthetic 近 photon 的 parton 可以通過 fixed cone 卻不通過 smooth cone，具體證明不能互換定義。測試也檢查 null 與 0/false 的區分、drab 不被自動關閉、maxjetflavor 的 bottom 分類、unreviewed threshold 拒絕。所有數字都是方法 fixture，不輸入實體 cross section。

本次未執行：精確 process parser、ME/integration、不同 photon/jet thresholds 的物理 scan、fragmentation matching、Pythia、Delphes。最小後續證據為：先凍結所選 component 的 IR target 與每個 cut，處理 A 的 bottom coverage 或 B 的 massless flavours/matching，再提出獨立審核的 parser/有限物理驗證範圍。

## 最終實跑收據與驗收範圍

最終純靜態命令收據為 `phase11_family_ir_audit_03.json`：35,341 bytes，SHA256 `8e8f12ec5b30766c78c37be02d0e05fd3018602e8c92ba2e99d540d9daa7da8a`。實際狀態為 `PASS_STATIC_SOURCE_REVIEW_WITH_BLOCKERS`，20 組逐行來源 witnesses，保留 B 的 8 個與 IR 的 5 個未解領域。root 的 Phase11 方法 suite 已執行本模組 44 項正負向測試並通過。這些證據支持來源解讀與 inactive schema；不是 generator parser、physical pilot、cut-independence 或 merging closure。B01 的 witness 轉義字串失敗記錄與後續 B02 收據均保留，最終證據綁定 B03 的凍結來源。

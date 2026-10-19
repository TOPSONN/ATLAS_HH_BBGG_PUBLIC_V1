# Phase11B：共同 5F aa＋0/1/2 QCD parton 候選族群

結論：`SOURCE_CONDITIONAL_NOT_READY`。安裝中的 MG5 3.5.16 與 Pythia 8.317 有相關 LO 介面；這不能取代精確 process parser、shower histories、matching 效率或權重驗證。本階段沒有呼叫 MG5 parser、生成 process、計算矩陣元素、積分或產生事件。`PARSER_NOT_VALIDATED`、`PHYSICAL_PILOT_NOT_EXECUTED`、`MATCHING_NOT_VALIDATED` 均保持。

## 來源與範圍

起點是 PR27、base `7b65428648bd3b1040721cf569604e6d8ad1625c` 中 Phase10 的兩份全註解 inactive card。新卡 `analysis/phase11/config/cards/candidate_b.inactive.txt` 仍然每行都是註解；`family_ir.py` 只做標準函式庫文字、雜湊及代數檢查，沒有任何 generator dispatcher。完整檔案 SHA256 與逐行 witnesses 由新 `audit_family_ir.py` 收據綁定，涵蓋本機實際 VERSION、model restriction、MG5 process parser 原始碼、LO cuts 與 Pythia matching 原始碼/同版手冊。receipt 的 PASS 只代表靜態來源檢查。

[MG5 官方 LO 介面說明](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/LOPY8Merging) 證實 LO MLM/CKKW-L 介面存在；此舊版短說明不提供本 aa＋HF 設定的物理驗證。精確語意採本機 3.5.16/8.317 而非線上 latest 預設值。

## Process 與 coupling orders

共同 multiparticle 定義 `p5` 與 `j5` 都是 g、u/d/s/c/b 及其反粒子；incoming c/b 與 final c/b 都在候選範圍。`sm-no_b_mass` 實際 restriction 的 MC、MB 都是 0 GeV；這是 ME model 身分，不代表 shower/hadron 的重味質量也是零。

| 額外 QCD parton | Phase10 文字 | 本階段嚴格等階語法提案 | 範圍 |
|---|---|---|---|
| 0 | `p5 p5 > a a QCD=0 QED=2` | `p5 p5 > a a QCD==0 QED==2` | tree amplitude e²，cross section α_em² |
| 1 | `p5 p5 > a a j5 QCD=1 QED=2` | `p5 p5 > a a j5 QCD==1 QED==2` | tree amplitude g_s e²，cross section α_s α_em² |
| 2 | `p5 p5 > a a j5 j5 QCD=2 QED=2` | `p5 p5 > a a j5 j5 QCD==2 QED==2` | tree amplitude g_s² e²，cross section α_s² α_em² |

`madgraph_interface.py:603–604,4847–4857` 明定單一 `=` 視為 `<=`；`==` 建立 constrained amplitude order，並設相應平方階數。`QCD^2==2` 是平方矩陣元素階數，不等於 amplitude `QCD==2`。因此不把 Phase10 的 `=` 誤稱為精確階數；也不宣稱本次改寫已使實際振幅數目不同，因為 exact process 尚未執行。第 2 個 multiplicity 的純 electroweak 較高 QED 階數、其他 mixed-coupling 系列不在這個嚴格 e² amplitude 定義內。

這個 tree-only family 沒有自動包含 loop-induced `gg→aa`。0-jet QCD=0 的來源是可存在的 tree quark/antiquark annihilation，而非把 gluon 入射 multiparticle label 誤讀成 loop 來源已計算。高 multiplicity gluon 入射 tree 子過程與 0-jet loop-induced channel 也不可混淆。0/1/2 是提案涵蓋的有限 multiplicities，尚未證明足夠近似 inclusive target；另外加上歷史 B01/B02/B03 會失去共同族群的物理分割，未授權任何相加。

## 逐項介面判定

| 問題 | 精確來源證據 | 判定 | 必要的未解證據 |
|---|---|---|---|
| 5F massless ME flavours | `restrict_no_b_mass.dat`、`candidate_b.json` | SOURCE_SUPPORTED（模型與字串層級） | 尚未執行精確 process |
| 5F PDF/α_s | 本機 payload 與 PDF/α_s 另見 Phase11A | BLOCKED | 新 family 的 PDF set/member/LHAID/hash、ME/ISR/FSR α_s 與 thresholds 必須共同凍結 |
| MLM 啟動路徑 | MG5 LO Pythia template:35–49 | generic SOURCE_SUPPORTED | ickkw/xqcut、jet coverage、matching scale 均不得採負 sentinel 當已驗證值 |
| MLM header 優先權 | `JetMatching.h:1053–1074` | SOURCE_SUPPORTED | `setMad` 會以 LHE header 覆寫 effective merge/qCut/nQmatch/clFact；必須保存 effective 設定 |
| b/c matching | `JetMatching.h:1385–1447` 與同版 manual:366–374 | 結構條件 nQmatch=5 | nQmatch=4 將 b 分為 heavy unmatched，不能覆蓋這個 j5 family |
| multiplicity 分工 | `JetMatching.h:1442–1447` | generic SOURCE_SUPPORTED | highest multiplicity inclusive、其他 exclusive 的 exact 0/1/2 行為與接受率仍未實跑 |
| CKKW-L photon core | 同版 `CKKWLMerging.html:601–641` 及 `aMCatNLOHooks.h:73–123` | photon token / guess 結構 SOURCE_SUPPORTED | `pp>aa` 只是字串提案；不等於 exact aa＋HF history 完整可重建 |
| CKKW-L flavours | 同版 manual:1183–1201 | 結構條件 nQuarksMerge=5 | 若 LHE 額外 flavours 超過 merging 範圍會有 double-counting 風險；massive history 設定尚未定案 |
| matching scale | xqcut/qCut/TMS 尚無 closure | BLOCKED | 選擇方法後先審核有限 scale scan；不得補 default 或自動猜值 |
| QCD/QED shower | 同版 Timelike/SpacelikeShowers | generic SOURCE_SUPPORTED | ISR/FSR photons、g→bb/cc、PDF/α_s 與 ME photon partition 要明定，不能將 QED shower 當 fragmentation completeness |
| photon IR | LO `cuts.f`、`setcuts.f`、`banner.py` | 定義 SOURCE_SUPPORTED、數值 BLOCKED | 見 Phase11C；B 要 maxjetflavor=5 才把 b/c 放入 smooth-cone QCD sum |
| fragmentation | 本 tree family 無 fragmentation functions | NOT_INCLUDED | direct-only target 或獨立合法的 fragmentation-inclusive prescription |
| 合併後 weights | 同版 CKKW-L manual:647–689 | 介面身分 SOURCE_SUPPORTED | source weight×mergingWeight、每 multiplicity accepted σ、sumW/sumW² 與 writer closure 未完成 |
| FxFx 對歷史 LO | 同版 JetMatching manual:399–411 | INAPPLICABLE | 必須是專為 NLO FxFx 準備的 source，不能翻旗標轉換 LO |

`aMCatNLOHooks.h` 的 guess 將非 coloured particles 等納入 core，再依 nQuarksMerge 計算額外 coloured partons；這能說明 photon core 的一般可表示性，不能證明每個 radiation/flavour history 可用。未來必須檢查缺失/被拒 history、flavour 別 differential jet rates、highest multiplicity、generator cut holes、scale stability、各 multiplicity/總接受率與獨立 seed 重現。只看 histogram 光滑不足。

[官方 FxFx prescription](https://amcatnlo.web.cern.ch/FxFx_merging.htm) 是 NLO 合併，並限制最低 Born core 不可含 jets 或 b。本 B 的 colourless aa core 雖不立即違反該 core 條件，仍未驗證 NLO model/loops/IR；因此不選 FxFx，更不套到歷史 LO 樣本。

## 權重與下一個可審核步驟

CKKW-L `Info::mergingWeight()` 不包含 phase-space `Info::weight()`，兩者都要保存。不同 multiplicity 還需 accepted cross section 正規化；接受率/Sudakov 的影響不可再重複乘。具體 HepMC writer 到 analysis 的 identity 尚未建立，所以 config 的 weight-writer closure 保持 false。signed/zero weight 的代數測試會保留負號與零值；這只是 readiness method test，沒有製造新實體權重。

B 的八個未解領域在 `candidate_b.json` 各有 null、BLOCKED、reason、evidence_required：PDF、α_s、matching prescription、scale、photon parameters、QCD/QED shower、normalization、Nmax coverage。**沒有一個 numerical scale 被採用**。若要最小下一步，應先審 exact-order process/parser 的窄範圍請求，並完成 PDF/α_s/IR/weight-source 封閉；本次不執行它。選一個可描述的 LO component 與證明完整背景模型是不同門檻。

## 最終實跑收據與驗收範圍

最終純靜態命令收據為 `phase11_family_ir_audit_03.json`：35,341 bytes，SHA256 `8e8f12ec5b30766c78c37be02d0e05fd3018602e8c92ba2e99d540d9daa7da8a`。實際狀態為 `PASS_STATIC_SOURCE_REVIEW_WITH_BLOCKERS`，20 組逐行來源 witnesses，保留 B 的 8 個與 IR 的 5 個未解領域。root 的 Phase11 方法 suite 已執行本模組 44 項正負向測試並通過。這些證據支持來源解讀與 inactive schema；不是 generator parser、physical pilot、cut-independence 或 merging closure。B01 的 witness 轉義字串失敗記錄與後續 B02 收據均保留，最終證據綁定 B03 的凍結來源。

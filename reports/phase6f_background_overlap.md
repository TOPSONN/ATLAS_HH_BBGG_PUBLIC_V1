# Phase6F ZH 與既有背景的分類及 overlap 限制

**READINESS_ONLY；沒有新 ZH 事件、沒有 stitching 或背景加總。**
`SINGLE_HIGGS_ZH_BBGG` 是含單一 Higgs resonance 的候選背景；它不會因為
重建到相同 bbγγ objects 就變成 continuum，亦不是 HH signal。

| 類別 | Hard 定義及來源 | 必須保留的區別 |
|---|---|---|
| CONTINUUM_BBGG | 既有 tree bbγγ，QCD2/QED2 | photons 是 continuum hard objects；不是已驗證的 H decay sample |
| CONTINUUM_CCGG | 既有 tree ccγγ | shower/association 可以出現 b；不是純 c-mistag 定義 |
| CONTINUUM_LIGHT_JJGG | final jl 不含 c/b，initial p 為5F | shower g→bb/cc 可改變重建 flavour；source997 是實際既有反例 |
| SINGLE_HIGGS_ZH_BBGG | 本次準備的 qqbar tree ZH；MG Z→bb chain、stable H | source Z decay 已包含，後續 H→γγ 與權重仍待實體 closure；ggZH 未包含 |
| SINGLE_HIGGS_TTH_BBGG | 前階段只 parse 的 ttH proposal | top/W decay、BR、spin/width 及真實 sample 未驗證；不得加入目前數值背景 |
| REDUCIBLE_BBGJ | 前階段一個 Born photon 的 bbγj proposal | jet→photon fake transfer/校準未知；不能當兩個真實 prompt photons |

既有來源的 Born final states 不同，但重建分類不必互斥。QCD shower 可產生
heavy flavours，QED radiation、fragmentation 與 hadron decays 可增加 photons。
原始 process name、seed 或 event hash 只能證明來源/事件身分，不能建立
reconstructed phase-space partition。既有 unmatched LO+Pythia 模型沒有提供
一致的多 multiplicity ME/PS matching、merging 或重 flavour subtraction scheme。

ZH 的 resonant H→γγ 與 continuum γγ 在相同 mγγ 區間可以共存；bb 可來自
Z、hard/shower bottom、或 native cone association。必須明確記錄 resonance
definition、finite-width window、generation cuts、decay scope 與 overlap policy。
獨立生成的 resonance component 不可重新命名為 continuum 再計一次；同時，
本次沒有計算 continuum/resonance interference，因此不能聲稱兩者在 amplitude
層級精確互斥或簡單加總已構成完整物理預測。

Preferred route 是 `ZH_ZBB_STABLE_H`：MG5 resonant Zbb chain 保留該 approximation
中的 production/decay correlations；source rate 若未來實際 integration，已具有
Zbb decay 與固定 ΓZ、Breit-Wigner window 的條件。不能再乘一次 `Z_to_b_bbar`
BR，也不能把 finite-width/cut-dependent chain rate 當精確
`σ(ZH)×BR(Z→bb)`。`H_to_gamma_gamma` 的外部 forced decay、原始 inclusive table、
partial/total width、adopted BR、Info/converter weights 與 original100 denominator
必須另行實體驗證。Stable Z/H alternative 的外部 Z spin limitation亦保持明示。

新 input profile 將 H-photon **birth** ancestry、Z-bottom **birth** ancestry
分開驗證；不要求每個 photon 是 continuum Born photon。Photon conversion/loss
與重建 acceptance 可使 final/reco photons 少於兩個，不能刪掉來源事件或改用
selected-output count normalize。重建使用原本 native jets、BTag bit0、Cartesian
`m_gamma_gamma / m_bb / m_bb_gamma_gamma` method；沒有新增 mbb cut、重抽 tag 或
official ATLAS efficiency claim。母女 DAG、相同 resonance copy、缺失/多重 ancestry
及兩個獨立 decay IDs 由新 module 的 METHOD_ONLY controls 檢查。

本次只發布 source/cards/configuration/tests 與 bounded text evidence。Synthetic
parser/graph/weight PASS 僅為 METHOD_ONLY，不能當成實體 ZH decay、Higgs BR、
HepMC3 library readback 或 native ROOT acceptance。Gate L 是 NOT_AUTHORIZED。
沒有 subtraction、negative stitching weights、source997 removal、背景 purity
修正、calibrated fake rate 或新的 HH sensitivity 結果。

# Phase7L 最終物理摘要

## 1. 物理範圍

LO finite-mass ggF HH research；官方ATLAS校準／全背景matching／發現敏感度不在範圍。

## 2. full-mass model

loop_sm finite mt/mb；保留A實際bounded模型驗證與source hashes，無HEFT。

## 3. generator來源

MG5 3.5.16 pinned source；原始G基準及新的isolated overlay可追溯。

## 4. 實際PDF/αs

B=CTEQ6L1/一圈；C/D=NNPDF23LO/兩圈。新target只完成初始化，無新physical source。

## 5. seed

B actual21而非requested20261121；C20261122；四個新integral seeds未真正使用於積分。

## 6. 積分方法

原生candidate/readback/RNG/grid/error保留；固定250初始點，4/3輪、accuracy0。

## 7. native語義

7組非物理native配對精確一致；inode-reuse失敗與lease修正保留；真實HH runtime未評估。

## 8. 截面收斂

未授權新matched integral，mean/SE/CI皆null；不將四個建置binary當四個積分。

## 9. Higgs decay角色

原兩個lineage與對稱獨立分配保留，不依pT排序改角色。

## 10. BR/權重

MODEL_BR_ONLY missing 2BRbbBRγγ一次，原N與signed weights保留，無sigma/N二次乘。

## 11. signal全鏈

原genuineB100/C1000 proofs重驗；corrected1000未授權，所有新chain counts null。

## 12. detector重建

既有ROOT 6.40.04/C++20唯讀7000entries；舊6C cuts與study card不改。

## 13. final cutflow

原C1000/484/403/143/143；corrected=null。

## 14. κλ結果

六benchmarks依actual C proposal分列；corrected CTEQ namespace為null。

## 15. κ統計限制

κ2.5/5 inconclusive；逐bin ESS、dominant fractions、shared covariance保留。

## 16. 背景比較

六個process各自UNIT_AREA_SHAPE及MODEL_WEIGHTED；不合併物理yield。

## 17. 科學阻擋

matched runtime/integration/convergence與corrected normalization缺少個別授權。

## 18. 可重現

五個已實作CLI模式、兩個明確拒絕future modes、safe resume與tamper checks已實測。

## 19. 歷史保存

8420個原始campaign檔案逐一SHA256相同；舊卡片、weights、6000ME rows與errata不覆寫。

## 20. 驗收

PHASE7_BLOCKED_AUTHORIZATION；完成目前允許的engineering/existing-input freeze，不冒稱LO物理閉合。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

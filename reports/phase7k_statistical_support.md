# Phase7K 支持度與 covariance

κ2.5/5維持INCONCLUSIVE_REWEIGHTING；bootstrap、重複shower或複製事件不能增加獨立硬點支持。
其餘benchmark只為bounded diagnostic，不能用global ESS保證每bin精度。完整低ESS/empty-bin flags、Wilson proposal intervals與zero-count upper列在CSV。
36格input RAW與36格selected MODEL_BR_ONLY covariance用相同event IDs重新center計算；不能當相互獨立，不能把兩種weight convention混加。selected MC sampling含已實現detector/tag波動，不能再重複加一個獨立tag variance。
zero proposal count的單側95%上限為固定source-proposal probability；沒有target weight bound時，不能推成物理率上限。
若將來要精密κ2.5/5，另案提出有界獨立direct-target或已正規化multi-proposal pilot、獨立seeds與完整covariance。不得自動放大本任務MC production。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

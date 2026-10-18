# Phase7K κλ 最終表

所有值源自同一組原C1000、實際NNPDF23 LO／兩圈及6000筆原生ME rows；κt=1。沒有新ME或獨立target integral。
完整表含歷史raw估計、absolute/shape status、N與sumw/sumw2/sign counts、ESS、最大份額、低ESS bins與numerical flags，見 evidence/analysis/kappa_benchmarks.csv。

| κλ | input ESS | final ESS | input最大份額 | final最大份額 | shape範圍 |
|---|---|---|---|---|---|
| -1.0 | 235.49 | 43.773 | 4.65% | 9.241% | BOUNDED_DIAGNOSTIC_REQUIRES_PER_BIN_SUPPORT |
| 0.0 | 503.66 | 78.31 | 2.474% | 5.668% | BOUNDED_DIAGNOSTIC_REQUIRES_PER_BIN_SUPPORT |
| 1.0 | 1000 | 143 | 0.1% | 0.6993% | BOUNDED_DIAGNOSTIC_REQUIRES_PER_BIN_SUPPORT |
| 2.0 | 204.59 | 71.981 | 5.988% | 7.437% | BOUNDED_DIAGNOSTIC_REQUIRES_PER_BIN_SUPPORT |
| 2.5 | 36.694 | 16.074 | 15.11% | 19.39% | INCONCLUSIVE_REWEIGHTING |
| 5.0 | 19.544 | 7.6501 | 19.82% | 26.79% | INCONCLUSIVE_REWEIGHTING |

所有absolute rates仍INCONCLUSIVE；修正CTEQ結果為null。SM closure、quadratic dependence、box/triangle interference及cancellation flags使用原實際ME資料與獨立Decimal/Lagrange回歸，不將重用事件當6000個獨立點。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

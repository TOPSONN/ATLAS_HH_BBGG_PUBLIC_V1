# Phase7I 收斂與誤差

CONVERGENCE=NOT_EVALUATED，mean／between-replica SE／native errors 都是 null。
預定 adaptation250初始點／4固定輪；measurement250／3固定輪；accuracy=0、min=max。native 每輪加倍非零 target，零權重點會增加嘗試數。
方法測試驗證 doubling、accuracy 分支、none-pass、capacity、own-grid讀回；不保證真實 HH 收斂、numerical rescue 或 coverage。
四個完成 matched endpoint 才能算 mean、sample SD、SE=SD/2 與 t(3)95%區間；其獨立性／近似常態假設須明示，heavy tails 不保證覆蓋率。
within-run native errors 與 between-run dispersion 分列，不盲加。資源提前結束為 PARTIAL，四個job完成也不是自動收斂PASS。
B .017276pb 與 C .019069pb 使用不同實際 PDF/running，不能當同 integrand 的 Gaussian pull；B 也有不同 seed與積分歷史，僅限定歷史比較。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

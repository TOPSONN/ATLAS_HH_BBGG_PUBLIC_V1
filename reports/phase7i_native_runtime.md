# Phase7I 原生 runtime

四份真正 native executable 已在隔離來源/library copies 建置；保留原始 dsample/unwgt/read/write computational bodies，只改 reviewed I/O boundaries，加 pre-ME configuration gate 與 STOP80。
執行範圍僅 pre-ME exit 與實際 exit80 拒絕。REAL_SURVEY_EXECUTED=NO，REAL_ME_CALLS=0，retained independent events=0。
真實 survey 的 zero-retention、loop stability、ME counters、tail/grid 行為與完整 transient coverage=NOT_EVALUATED。
現有 F resource watchdog 保留；未來新 route 啟用前須審查其 exact revision、process-group termination、scratch containment、immutable envelope 與實際 Stage A 行為，不能把初始化成功視為完整 runtime PASS。
Stage A 若失敗立即停止，不啟動其他 replica，不換 integrator 或隱藏失敗。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

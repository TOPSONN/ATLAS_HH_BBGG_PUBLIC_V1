# Phase7I 四個獨立積分結果

**NOT_AUTHORIZED / NOT_EXECUTED**。四 seed910001、910019、910037、910061 的 sigma/internal error/ME calls/grid results 全為 null。
只有獨立準備目錄及 preflight binaries，沒有四個完成 integral。Stage A adaptation 不當 final measurement。
未來每個 replica 必須獨立 fresh grid，measurement 只用自己 hash-bound adaptation grid；不得匯入 B/C 或用 successive refine 當獨立 replica。
每個失敗 seed 保留歷史，不自動替換。上限4 replicas、1job/1worker、CPU及wall合計各4h、額外5GiB，不自動擴充。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

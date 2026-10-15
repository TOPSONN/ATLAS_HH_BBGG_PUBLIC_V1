# Phase7H 候選與 RNG 稽核

原始 nw/swgt、th_nunwgt/th_maxwgt、neventswritten、sort、clear/store 及所有三個 RNG 呼叫保留，沒有為了禁止輸出將它們歸零。
原始 RANMAR、ran1、xran1 的 state 分離；HH configs=1 的限制保留，不將有限測試泛化到多 channel。
write_leshouche 的 topology、ptclus、boost/addmothers side effects、原生格式化權重 rounding 均留在 native 路徑。
METHOD_ONLY 的完整候選 buffers 只留本機 trace，不當獨立物理 LHE source；公開是 hashes、摘要與首差。
scratch 是可讀寫、rewind 的 unlink regular file，會用到檔案系統/page cache；不是純記憶體或沒有 transient records。
每次 native write_event 前檢查核准 unit、descriptor、regular file、nlink=0 及 inode identity。descriptor lease 防止關閉後 inode 立即重用，最多保留各核准 unit 一份，下一次核准 open 或 process exit 釋放。
舊 Phase7F STOP80/STOP86 完全不變；新隔離 I/O 路徑以87拒絕未核准 writer。未宣稱完整真實 survey 的未知外部 writer 已被觀察。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

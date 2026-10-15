# Phase7J 既有全鏈驗證

原B100與C1000 genuine source/derived decay/shower/HepMC/Delphes/ROOT證據及CRC/hash/count/lineage/weights重驗通過；完整歷史資料8420檔保留。
新唯讀ROOT程序重新檢查C1000與六背景各1000筆：source index/SHA、Event weight、所有named weights、eligible photon/jet與bit0 tag選擇相符，沒有新detector events。
既有C cutflow=1000/484/403/143/143，不能稱修正CTEQ baseline cutflow；corrected cutflow=null。
凍結6C選擇：leading photon>35、subleading>25、|η|<2.37，排除1.37<|η|<1.52；jet pT>25、|η|<2.5；至少2個bit0 tags；105≤mγγ≤160。沒有新增mbb優化cut。
缺物件的masses與pT維持null，沒有補0；tagged-pair masses使用原實際tag realization，沒有拿期望tag數代替mass分布。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

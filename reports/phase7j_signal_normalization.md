# Phase7J 訊號權重與 BR

原 B100：CTEQ6L1／一圈／seed21；原 C1000/D：NNPDF23 LO／兩圈／seed20261122。原 LHE XWGTUP、signed weights、original N、cross sections及integration errors原樣保留。
production-only HH 缺少的 mixed-decay factor 只乘 `2*BRbb*BRγγ` 一次；本模型 factor=0.0026534459067208711。2個 original Higgs lineages、獨立50/50角色分配與mother/daughter closure 使用原 genuine validation，不能再乘一次 sigma/N 或 assignment 反機率。
MODEL_BR_ONLY，不自動採用Pythia初始化值為已校準物理BR；external/adopted physical BR=null。單H背景不能套HH factor2。
重驗原source→HepMC/ROOT命名權重與source denominator；新ROOT reader逐一核對7000個既有 Event及全部 named Weight 值。
絕對 target normalization 仍 INCONCLUSIVE，沒有全域 rescale 舊樣本。integration／MC sampling／tagging／BR／PDF-scale／detector不合成一個假總誤差帶。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

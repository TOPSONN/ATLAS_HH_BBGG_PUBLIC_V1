# Phase7K 六背景逐一比較

S01與B01–B06分開比較，沒有合併物理背景。process_cutflow.csv保留每stage N_original/N_selected、efficiency、sumw/sumw2/sumabs與sign counts；process_shapes.csv包含原13個observable，另有4個由實際ROOT重新讀出的leading/subleading photon/jet pT。
兩種明示輸出：UNIT_AREA_SHAPE、PER_PROCESS_MODEL_WEIGHTED。flows、missing-pair counts/weights、低ESS與proposal intervals保留；未定義的unit-area形狀不當物理零。
S01歷史C=1000/484/403/143/143；B01=1000/446/266/91/28；B02=1000/378/241/7/1；B03=1000/445/277/0/0；B04=1000/370/220/77/75；B05=1000/327/322/131/131；B06=1000/2/2/2/0。
B03/B06 final觀察0的source-proposal binomial單側95%上限約0.00299125，依賴固定proposal/iid假設，不是零物理率或校準target-rate上限。
B01–B03 heavy-flavour overlap未解；B04/B05 MODEL_BR_ONLY，ttH spin未驗證；B06只有一個Born photon且無校準fake rate。
無官方總背景、發現significance、exclusion、ATLAS sensitivity或校準S/B。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

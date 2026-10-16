# Phase7J 修正 SM1000 準備

CORRECTED_SM_SOURCE=NOT_AUTHORIZED_NOT_EXECUTED；actual LHE/HepMC/ROOT counts、PDF/running/seed、sigma/error全為null。
已實際執行 prepare-corrected-signal：固定1000、proposed seed20261123，fresh RunCardLO preview與model/writer source hashes檢查通過；精確卡片公開供審查。
這是新 namespace，不能把C1000改名、串入CTEQ yield或套常數cross-section ratio當跨PDF shape reweight。
先須Phase7I科學gates PASS，再另行 AUTHORIZE_PHASE7_FINAL_SM_1000，綁定code/config/seed/retention；上限1source、最多2worker、12h wall、額外20GiB。名稱出現在文件不構成授權。
之後須真正1000 LHE／1000 HepMC3／1000 ROOT，前10/100只為prefix。此次沒有生產或新物理 shower/Delphes。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

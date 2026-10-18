# Phase7I 設定與 seed

凍結 target：MG5 3.5.16 loop_sm，g g > h h [noborn=QCD]，finite mt/mb，13TeV，MH125／MT173／MB4.7，κλ=κt=1，CTEQ6L1，αs(MZ)=.130、一圈，μR=μF=mHH/2，無HEFT／K factor／NLO+PS。
physics contract SHA256：`a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`。
四個 request/compiled/native-initialization seed910001/910019/910037/910061 與 global/beam PDF、PDFSUP10042、running/masses/scale flags 已實際 preflight 檢查。
這不是 actual integral seed/phase-point 證明；真正 ME 呼叫後仍需逐 integral 重查。原 B actual21、C actual20261122 不更改。
Source/pdf.f、Source/pdfwrap.f 的實際位置是 Source/PDF/ 子目錄；原始SHA留在 evidence，不靠檔名推測 PDF。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

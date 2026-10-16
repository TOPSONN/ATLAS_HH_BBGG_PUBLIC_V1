# Phase7H 實際方法測試

7組 native paired cases 全部精確一致：adaptation、measurement、negative/positive accuracy、none-pass、forced secondary store、candidate capacity。
6個 computational mutations 均拒絕並保留 FIRST_DIVERGENCE_LOCATION／EXPECTED_VALUE／OBSERVED_VALUE／CAUSAL_NATIVE_SOURCE_LINE／SCIENTIFIC_IMPACT。
4個實際 native I/O negatives 均 exit87；獨立 C API 測試另拒絕100次 unlink rebind。
bitwise paired tolerance=0；獨立 Decimal 回歸的預宣告 tolerance 為 relative1e-12、absolute1e-14，沒有觀察失敗後調寬。
第一輪實際嘗試270個固定非物理 weights，得到250個非零點；native mean=3.68518518518519、error=0.146549300498381，均為 METHOD_ONLY，不是 pb 或物理截面。
曾發生真實 I/O negative 失敗：關閉後 inode 重用令新 scratch 誤通過舊檢查。原失敗 receipt 保留；只做 descriptor lease 這一個有界修正，再執行獨立 regression，未修改預期拒絕碼或 tolerance。
完整 trace 在本機；公開 native_method_result.json 綁定 trace hashes、程式來源、compiled source、library 與 executable hashes。兩個相同 NaN 或空 trace 不算 PASS。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

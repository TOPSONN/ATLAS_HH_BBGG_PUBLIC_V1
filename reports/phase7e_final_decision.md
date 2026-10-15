# Phase7E 最終稽核決策

本次稽核辨識出可驗證的有效設定失配；原先將 B/C 當同一 integrand 的跨 seed 比較不成立。沒有聲稱已定量分解全部截面差，亦沒有執行任何新 integral／物理事件。

| 必要欄位 | 結果 |
|---|---|
| B_C_SOURCE_IDENTITY | B100/C1000 原 gzip 與全部歷史檔保留；84 個 frozen physics-source files 相同。實際 PDF/running 不同，不能認定完整 integrand 相同。 |
| B_C_INTEGRATION_CONFIG_DIFF | cards/scales/param/MadLoop 相同（事件數、seed 除外）；B compiled cteq6l1／1-loop，C compiled nn23lo1／2-loop。C 多一次 refine，只有一個 measurement iteration。 |
| B_C_SEED_AUDIT | B requested20261121、effective21；C requested/effective20261122。保留原樣，不重貼 seed。 |
| SURVEY_REFINE_DIAGNOSTICS | B3 survey、無新 refine 工作；C3 survey+1 refine iteration；完整逐步 grid history 僅 PARTIAL。 |
| WEIGHTED_CANDIDATE_AUDIT | B406→403；C survey398→394、refine2703→2203；refine416 overweight，權重超額保留；原生 buffer200000 未見觸頂。 |
| TRUNCATION_AUDIT | raw tail excess .051445615 不是截面百分比；第二欄1.00217882%才是原生比值。最終 target unweight 的實際截斷／納入歷史 UNKNOWN，不能排除選樣影響。 |
| INTEGRATION_ERROR_RELIABILITY | native χ inflation 已還原；內部誤差沒有跨 seed coverage 校準，C 單次 refine χ=0 不證明收斂。 |
| CROSS_RUN_TENSION_EXPLANATION | .017276±.00018503 vs .019069±.00011745 pb；比值8.18128所報誤差單位不能解釋為同 integrand tension。配置失配已證實，差異各來源比例未分離。 |
| INDEPENDENT_INTEGRATION_STATUS | **NOT_AUTHORIZED** |
| KAPPA_2_5_SUPPORT | INCONCLUSIVE；input/final ESS36.6943/16.0736；最大單點15.1126%。 |
| KAPPA_5_SUPPORT | INCONCLUSIVE；input/final ESS19.5442/7.65012；最大單點19.8193%。 |
| FUTURE_PROPOSAL_STRATEGY | 先修復並驗證有效設定，再另行授權 direct-target pilots 或 normalized positive multi-proposal mixture；保留 strata variance、跨κ covariance、tail gates。 |
| EXISTING_REGRESSION | 11新+13既有方法測試、B/C/D hash/count/weight/Decimal regression、1100尺度原生與獨立RGE驗證通過；未重跑 ROOT detector。 |
| GITHUB_CI | 使用新 PR 精確 head 的實際 checks；提交本檔時不預先宣稱成功。legacy readiness job 固定原Phase7A source，其餘 jobs 驗證目前audit/campaign。 |
| GATES_PASS | 原資料保存、實際配置稽核、候選／誤差來源分析、獨立ESS、準備與拒絕命令實測、source/evidence bounded scope。 |
| GATES_FAIL | C宣告/有效PDF與running一致性；B requested seed遵循；κ2.5/5精密支持。這些是科學驗收失敗，偵測它們的軟體測試可PASS。 |
| GATES_BLOCKED | 新積分未授權；零retained-LHE原生runtime驗證；匹配設定coverage/收斂校準；已清理candidate的完整截斷追蹤。 |
| COMMIT_HASH | 以包含本檔的新 Draft PR head SHA 為準，避免自引用hash。 |
| PR_URL | 新stacked Draft PR，以 PR20 branch為base；實際URL在交付訊息。 |
| FINAL_VERDICT | **AUDIT_COMPLETE_WITH_SCIENTIFIC_FAILURES_IDENTIFIED; CONVERGENCE_NOT_YET_MEASURED** |
| NEXT_RECOMMENDED_STEP | 審核更正與有效PDF/αs/seed guard，完成零LHE writer guard設計；之後另行明確核准有界matched-config integration-only量測。 |

細節：[來源與更正](phase7e_source_identity_audit.md)、[積分與候選](phase7e_integration_and_candidate_audit.md)、[未執行的積分計畫](phase7e_integration_only_plan.md)、[κ支持與proposal](phase7e_kappa_support_strategy.md)、[機器可讀gate](../metadata/phase7e_audit.json)。所有舊數值、events、cards、weights、reports、Git歷史保留；無新PDF/PNG、無重裝、無merge或force-push。

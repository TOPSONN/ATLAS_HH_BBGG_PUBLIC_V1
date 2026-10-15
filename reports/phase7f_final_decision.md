# Phase7F 驗收報告

PROJECT：ATLAS_HH_BBGG_PUBLIC_V1。TASK：PHASE7F_HH_EFFECTIVE_CONFIG_LOCK_AND_INTEGRATION_ONLY_RUNTIME_GUARD_V1。

| 驗收欄位 | 結果 |
|---|---|
| EFFECTIVE_PDF_GUARD | PASS：compiled global/beam labels、實際 native PDF/table、HEPRUP PDFSUP=10042，四個 driver 初始化出口一致。 |
| ALPHA_S_RUNNING_GUARD | PASS：αs(MZ)=.130、一圈 running，五尺度原生與獨立公式驗證。 |
| SEED_GUARD | PASS：四 seed 的 request/launch/prepared Banner/include/native初始化/run identity一致；seed0/21 reset與continuation mismatch拒絕。 |
| RUNCARD_WRITER_GUARD | PASS：實際重現鄰近 default drift；fresh IO writer三次輸出一致，模板/來源前後hash保持。 |
| ZERO_LHE_WRITER_DESIGN | 已實作 isolated candidate/store suppression、fatal permanent writer、輸出/immutable workspace envelope與publication guard。 |
| ZERO_LHE_RUNTIME_VALIDATION | **NOT_EVALUATED_FOR_REAL_SURVEY**。初始化與synthetic邊界已實測；不冒稱完整survey零保留PASS。 |
| INTEGRATION_ONLY_COMMAND | `bash simulation/hh_signal/config_lock/integration_only.sh --output "$HOME/simulations/hh_config_lock/my_plan_01"`；只準備/建置/初始化。`--validate`驗證；`--execute`拒絕。 |
| INTEGRATION_EXECUTED | **NO**；無新ME evaluation、無新硬事件。 |
| HISTORICAL_SIGNAL_PRESERVATION | 原8420檔、B100/C1000 LHE/HepMC/ROOT、D6000 ME rows與所有舊數值/報告/卡片/日誌保留。 |
| REGRESSION_TESTS | 19新+11 Phase7E+13 campaign，共43項通過；B/C/D reference與獨立Decimal數值回歸通過。ROOT detector未重跑。 |
| GITHUB_CI | 提交時不預先宣稱；以新Draft PR精確head的實際checks與遠端blob讀回結果為準。 |
| GATES_PASS | effective-config/native初始化、seed、writer、source identity、拒絕路徑、原始資料保存與既有回歸。 |
| GATES_FAIL | 無新增保護測試失敗；歷史C target失配與B requested seed失敗保留，不重貼PASS。 |
| GATES_BLOCKED | 新積分未授權；新硬事件禁止；native dispatch保持STOP80。 |
| GATES_UNKNOWN | 真實survey零retention與transient寫入、writer suppression對狀態/RNG/stopping/reporting的影響、完整stage轉換、收斂/coverage與絕對截面。 |
| COMMIT_HASH | 包含本檔的新stacked Draft PR head SHA；實際值見交付訊息。 |
| PR_URL | 新Draft PR以PR21 branch為base；實際URL見交付訊息。 |
| FINAL_VERDICT | **PROTECTION_READY_FOR_REVIEW；NATIVE_RUNTIME_GATE=NOT_EVALUATED**。 |
| NEXT_RECOMMENDED_STEP | 審查lock/bridge/資源與stage endpoints，之後另行明確授權matched-config integration-only runtime驗證。 |

四份真正native driver已編譯；只有初始化專用出口與拒絕分支被執行。任何非初始化分支先遇native STOP80，Python CLI/runtime dispatch亦在I/O前拒絕。這是防護工具驗證，不是積分收斂或物理率驗證。

保留 Phase7E erratum：B=CTEQ6L1/一圈、actual seed21；C/D=NNPDF23 LO/兩圈，不能稱為CTEQ6L1樣本；absolute cross sections=INCONCLUSIVE；κλ2.5/5=INCONCLUSIVE_REWEIGHTING。沒有改舊weights或補造新樣本。

詳見[設定鎖](phase7f_effective_configuration_lock.md)、[零保留設計](phase7f_zero_retention_and_runtime_guard.md)、[下一階段契約](phase7f_future_integration_authorization.md)、[繁體中文指南](../simulation/hh_signal/config_lock/USER_GUIDE_ZH_TW.md)、[機器可讀狀態](../metadata/phase7f_guard_status.json)。無新PDF/PNG、無merge、無force-push。

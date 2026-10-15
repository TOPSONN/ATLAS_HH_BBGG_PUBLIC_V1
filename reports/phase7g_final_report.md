# Phase7G 驗收報告

**目前未授權任何新積分；完整 writer 語義等價性亦未證實。Stage A/B 均未執行。**

此提交僅準備計畫、實際執行不含 ME 的 RNG/固定權重測試、CLI 拒絕測試及既有輸入回歸。
沒有新增物理事件、積分截面、shower 或 detector 執行；保留原 STOP80/STOP86。

| 驗收欄位 | 結果 |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE7G_HH_MATCHED_INTEGRATION_ONLY_V1 |
| AUTHORIZATION_STATUS | NOT_GRANTED |
| BASE_HEAD | 081d29a8499a714faeb9e1296d41ac93d48c82d2 |
| EFFECTIVE_PDF | CTEQ6L1 locked; preserved F native initialization proof revalidated; future survey gate NOT_EVALUATED |
| ALPHA_S_RUNNING | alpha_s(MZ)=0.130, one loop; preserved five-scale native initialization evidence revalidated |
| SEED_IDENTITY | {"planned":[910001,910019,910037,910061],"adaptation_moffset":0,"measurement_moffset":1,"actual_new_integral_seeds":[]} |
| MODEL_IDENTITY | MG5 3.5.16 loop_sm finite mt/mb; MH125 MT173 MB4.7, kappa_lambda=kappa_top=1, sqrt(s)13000, muR=muF=mHH/2; pinned F source inventory |
| NATIVE_SURVEY_EXECUTED | false |
| ZERO_RETAINED_LHE | PASS_FOR_NONINTEGRATING_PREPARATION_ONLY; genuine survey runtime NOT_EVALUATED |
| WRITER_SEMANTICS_VALIDATED | false |
| REPLICA_1 | {"seed":910001,"status":"NOT_EXECUTED","sigma_pb":null,"internal_error_pb":null,"ME_calls":null} |
| REPLICA_2 | {"seed":910019,"status":"NOT_EXECUTED","sigma_pb":null,"internal_error_pb":null,"ME_calls":null} |
| REPLICA_3 | {"seed":910037,"status":"NOT_EXECUTED","sigma_pb":null,"internal_error_pb":null,"ME_calls":null} |
| REPLICA_4 | {"seed":910061,"status":"NOT_EXECUTED","sigma_pb":null,"internal_error_pb":null,"ME_calls":null} |
| INTEGRATION_MEAN_PB | null |
| BETWEEN_REPLICA_SE | null |
| INTERNAL_ERRORS | null |
| CONVERGENCE_ASSESSMENT | NOT_EVALUATED |
| GRID_STABILITY | NOT_EVALUATED; independent empty preparation directories only |
| TAIL_DIAGNOSTICS | UNKNOWN; suppressed original candidate statistics cannot be interpreted as native tails |
| NEW_PHYSICAL_EVENTS | 0 |
| NEW_PHYSICAL_ME_CALLS | 0 |
| NEW_INTEGRALS | 0 |
| CPU_USAGE | {"native_survey":"NOT_EXECUTED","RNG_compile_and_probe_child_seconds":0.23024299999999998,"preparation_regression_child_seconds":23.532982,"coverage":"separate bounded runs; excludes shell/agent, prior failed diagnostics and initial scout"} |
| WALLTIME | {"native_survey":"NOT_EXECUTED","RNG_compile_and_probe_seconds":0.5298140940003577,"preparation_regression_seconds":150.17379439599972} |
| PEAK_MEMORY | {"RNG_child_high_water_KiB":33536,"regression_child_high_water_KiB":179040,"scope":"RUSAGE_CHILDREN process-lifetime maximum; not concurrent aggregate RAM and not survey RAM"} |
| DISK_USAGE | {"logical_bytes_snapshot_before_report":{"local_diagnostics_and_original_Phase7A_snapshot":107900964,"prepared_workspaces_and_native_RNG_probes":262469,"new_source_and_public_evidence":350771},"scope":"local source/evidence, probes, plans and immutable old A snapshot; not survey disk; later Git objects excluded"} |
| REGRESSION | {"method_tests_passed":415,"reference_validators_passed":5,"historical_files_unchanged":8420,"Phase7A_snapshot":"d9fe33f97773367a41b8877568401af594eeb2a6","current_head_Phase7A_hash_rejection":"EXPECTED_AND_PRESERVED; not suppressed or rewritten"} |
| GITHUB_CI | Final exact-head check results in delivery message; never inferred from local tests |
| GATES_PASS | ["frozen preparation/card/endpoint/seed-offset validation","actual CLI denials before I/O","native RNG-only noninterference test","independent fixed-weight/replica statistical methods","415 regression tests plus five reference validators","8420 original campaign files byte-identical"] |
| GATES_FAIL | ["historical C target-PDF mismatch preserved; no new target integrals evaluated"] |
| GATES_BLOCKED | ["NOT_AUTHORIZED","BLOCKED_INTEGRATION_SEMANTICS"] |
| GATES_UNKNOWN | ["actual ME and full native integration counters","native grid and stopping behavior under proposed endpoints","full writer suppression scientific equivalence","native loop/tail diagnostics","genuine-survey zero retention and complete transient coverage","convergence"] |
| COMMIT_HASH | Containing Draft PR final head; exact SHA in delivery message |
| PR_URL | New Draft PR stacked on PR22 actual branch; exact URL in delivery message |
| FINAL_VERDICT | NOT_AUTHORIZED |
| SCIENTIFIC_VERDICT | BLOCKED_INTEGRATION_SEMANTICS |
| NEXT_RECOMMENDED_STEP | Review paired no-output native semantics and instrumentation; only after resolving semantics obtain separate explicit scope-bound human authorization before Stage A |

PR22 exact head 已重新 fetch/核對。需求中的 branch alias 與實際 branch 不同；本 PR 以原存在的 `codex/phase7f-hh-effective-config-lock` 為 base，沒有改名或修改 PR22。

415 = 54（G/F/E/campaign）+42（原始 A 快照）+134（新背景）+78（ZH）+56（重味稽核）+51（rare-background）。
原 Phase7A 在目前 head 的凍結 hash 拒絕紀錄亦保留；沒有將這個拒絕改稱成功。CI 分別驗證原 A/F 快照，G job 檢查實際 G head 及全部 outgoing payload。

RNG-only 原生實測：兩模式各16個 RANMAR 值精確一致，輔助 RNG 消耗不同。固定人工權重和41、平方和289不是截面。
負 accuracy 停止邏輯與候選統計確實改變；完整 native point/weight/grid/error 等價仍 UNKNOWN，所以不可啟用 survey。

資源記錄僅描述有界準備/回歸與 RNG 編譯，並非新積分成本。沒有全 task CPU 計量；初始 scout、失敗診斷、shell/agent 不在所列子程序資源範圍。
RUSAGE_CHILDREN 峰值是各子程序最高水位，非同時總 RAM。磁碟數字是報告產生前快照，含原 A 的本地獨立 checkout；沒有將已有歷史資料計為新物理產生。

B 0.017276 pb（CTEQ6L1／一圈，seed21）與 C 0.019069 pb（NNPDF23 LO／兩圈，seed20261122）原樣保留，不能將 C 當 matched integrand。
absolute cross sections 與 κλ2.5/5 的既有 INCONCLUSIVE 限定不變。

相關檔案：[語義稽核](phase7g_writer_semantics.md)、[繁體中文操作指南](../simulation/hh_signal/matched_integration/USER_GUIDE_ZH_TW.md)、[實測證據](../simulation/hh_signal/matched_integration/evidence/manifest.json)、[機器可讀報告](../metadata/phase7g_matched_integration_status.json)。
無新 PDF/PNG、實體事件或執行檔公開；沒有 merge 或 force-push。

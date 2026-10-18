# Phase7 最終驗收

**最終判定：PHASE7_BLOCKED_AUTHORIZATION。目前授權的工程、方法與既有輸入收尾已完成；整個Phase7 LO物理campaign尚未閉合。**

| 欄位 | 實際結果 |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE7_FINAL_CLOSURE_CAMPAIGN_V1 |
| BASE_PR | 23 |
| BASE_HEAD | a5582e508e452a515670d1edc1d39041e88a8638 |
| PHASE7H_STATUS | READY_FOR_AUTHORIZED_NATIVE_VALIDATION |
| NATIVE_SEMANTICS | PASS_METHOD_LEVEL_SEMANTICS_WITH_LIMITS |
| CANDIDATE_BOOKKEEPING | native nw/swgt/store/clear/theoretical counters retained; exact paired traces |
| RNG_EQUIVALENCE | all consumed RANMAR/ran1/xran1 values match in deterministic native method cases |
| GRID_EQUIVALENCE | four-dimensional increments/geometry and own-grid transitions match in method cases |
| STOPPING_EQUIVALENCE | fixed, positive/negative accuracy, zero-pass and capacity cases match; not genuine-survey proof |
| INTEGRAL_ARITHMETIC | native fixed-stream sums/squares/chi/error match; independent double/Decimal regression PASS |
| TRANSIENT_OUTPUT_SCOPE | anonymous regular formatted scratch, native readback/rounding preserved; descriptor lease fix; no no-transient-write claim |
| PHASE7I_STATUS | NOT_AUTHORIZED_NOT_EXECUTED |
| AUTHORIZATION | NOT_GRANTED |
| REAL_INTEGRALS_EXECUTED | 0 |
| REAL_ME_CALLS | 0 |
| ZERO_RETAINED_EVENTS | 0 new retained independent events; real-survey zero-retention NOT_EVALUATED |
| REPLICA_910001 | NOT_EXECUTED |
| REPLICA_910019 | NOT_EXECUTED |
| REPLICA_910037 | NOT_EXECUTED |
| REPLICA_910061 | NOT_EXECUTED |
| MEAN_CROSS_SECTION_PB | null |
| BETWEEN_REPLICA_ERROR | null |
| INTERNAL_ERRORS | null |
| CONVERGENCE_VERDICT | NOT_EVALUATED |
| PHASE7J_STATUS | HISTORICAL_WEIGHT_CHAIN_REGRESSION_PASS; CORRECTED_NOT_EXECUTED |
| CORRECTED_SM_SOURCE_STATUS | NOT_AUTHORIZED_NOT_EXECUTED |
| CORRECTED_SM_LHE_EVENTS | null |
| CORRECTED_SM_HEPMC_EVENTS | null |
| CORRECTED_SM_ROOT_EVENTS | null |
| ACTUAL_EFFECTIVE_PDF | {"B":"CTEQ6L1","C_D":"NNPDF23_LO","corrected_source":null,"new_native_preflight_target":"CTEQ6L1"} |
| ALPHA_S_RUNNING | {"B":1,"C_D":2,"corrected_source":null,"new_native_preflight_target":1} |
| EFFECTIVE_SEED | {"B":21,"C":20261122,"corrected_source":null} |
| CROSS_SECTION_PB | {"historical_B":0.017276,"historical_C":0.019069,"corrected_target":null} |
| INTEGRATION_UNCERTAINTY | {"historical_B":0.00018503,"historical_C":0.00011745,"corrected_target":null} |
| BR_CONVENTION | MODEL_BR_ONLY: missing 2*BR(Hbb)*BR(Hgammagamma) once; no extra factor for assignment probability |
| BR_WEIGHT_CLOSURE | PASS_HISTORICAL_MODEL_SCOPE_ONLY |
| FINAL_CUTFLOW | {"historical_C":[1000,484,403,143,143],"corrected_target":null} |
| PHASE7K_STATUS | LIMITED_EXISTING_NNPDF_SOURCE_ANALYSIS |
| KAPPA_BENCHMARKS | [-1,0,1,2,2.5,5] |
| REWEIGHT_VALIDATION | PASS_6000_EXISTING_ACTUAL_ME_ROW_REGRESSION_NO_NEW_ME |
| KAPPA_2_5 | INCONCLUSIVE_REWEIGHTING |
| KAPPA_5 | INCONCLUSIVE_REWEIGHTING |
| CROSS_KAPPA_COVARIANCE | 36 centered input RAW +36 selected MODEL_BR_ONLY entries, same source events |
| LOW_ESS_FLAGS | explicit per-bin flags and proposal intervals; not physical rate intervals |
| ABSOLUTE_RATE_SCOPE | INCONCLUSIVE; historical actual C proposal only; no corrected CTEQ predictions |
| PHASE7L_STATUS | AUTHORIZED_ENGINEERING_AND_EXISTING_INPUT_SCOPE_FROZEN; PHYSICS_CLOSURE_BLOCKED |
| SIGNAL_BACKGROUND_COMPARISON | S01 vs B01-B06 independently, UNIT_AREA_SHAPE and PER_PROCESS_MODEL_WEIGHTED; no total physical background |
| FULL_PHYSICS_SUMMARY | twenty sections in phase7l_final_physics_summary.md |
| REPRODUCIBILITY | actual implemented CLI plus code/config/input/output identities and bounded native receipts |
| PHASE8_HANDOFF | ["matching/overlap","photon fakes","official calibration/systematics","combined likelihood"] |
| HISTORICAL_FILES_PRESERVED | 8420 |
| NEW_INDEPENDENT_EVENTS | 0 |
| NEW_INTEGRALS | 0 |
| TOTAL_RESOURCE_USAGE | {"scope":"audited per-run measurements and disk snapshot; no invented complete task CPU total","complete_task_CPU_seconds":null,"complete_task_wall_seconds":null,"unmeasured":"initial scout, failed compiler/link diagnostics, agent/shell and other preparatory work","final_native_method":{"wall_seconds":12.446943311000002,"child_CPU_seconds":7.380903,"child_peak_RSS_KiB_process_lifetime_high_water":97576,"logical_disk_bytes":92882790},"native_preparation_per_seed":[{"wall_seconds":2.3823164279999958,"child_CPU_seconds":1.62964,"child_peak_RSS_KiB_process_lifetime_high_water":49116,"logical_disk_bytes":60175667},{"wall_seconds":2.002400109000007,"child_CPU_seconds":1.6281259999999997,"child_peak_RSS_KiB_process_lifetime_high_water":49244,"logical_disk_bytes":60175667},{"wall_seconds":2.364358089999996,"child_CPU_seconds":1.6063269999999998,"child_peak_RSS_KiB_process_lifetime_high_water":49244,"logical_disk_bytes":60175667},{"wall_seconds":1.9369685750000087,"child_CPU_seconds":1.5939869999999998,"child_peak_RSS_KiB_process_lifetime_high_water":49252,"logical_disk_bytes":60175667}],"existing_ROOT_readback_wall_seconds":23.456969247000018,"regression_and_CLI":{"scope":"this regression and CLI script only; excludes prior build/readback/method attempts and agent/shell CPU","wall_seconds":261.56577425,"child_CPU_seconds":47.94982699999999,"child_peak_RSS_KiB_process_lifetime_high_water":179192,"new_real_ME_calls":0,"new_integrals":0,"new_independent_events":0},"disk_logical_snapshot_bytes":{"native_method_workspaces":606239168,"closure_workspaces":494985851,"closure_source_and_evidence":5994570,"local_closure_diagnostics":46998},"Git_objects_excluded":true,"new_physical_workload":{"ME_calls":0,"integrals":0,"independent_events":0}} |
| NEW_TESTS | 18 |
| NATIVE_TESTS | 7 exact paired cases,6 mutations,4 native I/O denials,100 independent unlinked rebinds;4 real guarded driver preflights |
| EXISTING_REGRESSION | 415 existing +18 new =433 tests; five reference validators; A tested at original frozen snapshot |
| GITHUB_CI | VERIFY_AT_DELIVERY_HEAD: exact-head check results recorded in final delivery; local tests do not establish CI status |
| REMOTE_BLOB_VERIFICATION | VERIFY_AT_DELIVERY_HEAD: actual changed blob bytes and remote ref results recorded in final delivery |
| GATES_PASS | ["A","B","E","J","K","L","M","O","P","Q"] |
| GATES_FAIL | ["historical C effective configuration mismatch","historical B requested/effective seed mismatch","development inode-reuse failure retained, fixed by descriptor lease"] |
| GATES_BLOCKED | ["F/G real integration authorization","corrected SM1000 production authorization and Phase7I prerequisites"] |
| GATES_UNKNOWN | ["real HH runtime equivalence","matched sigma/convergence","new corrected full chain","calibrated uncertainty coverage"] |
| FINAL_COMMIT_HASH | containing final Draft PR head; exact SHA in delivery |
| DRAFT_PR_URL | one Draft PR stacked on PR23; exact URL in delivery |
| FINAL_VERDICT | PHASE7_BLOCKED_AUTHORIZATION |
| NEXT_RECOMMENDED_STEP | review exact final code/config/seed/resource/scratch contract, then separately authorize bounded Stage A; corrected SM1000 requires another approval after Phase7I PASS |

## Quality gates

| Gate | Status | Reason |
|---|---|---|
| A | PASS | verified Git/base and frozen source identities |
| B | PASS_WITH_BOUNDED_SCOPE | preserved finite-mass model and numerical regressions |
| C | PARTIAL | target native initialization PASS; corrected physical source not executed; historical C mismatch preserved |
| D | PARTIAL | four native initialization seeds PASS; actual new integration seeds not evaluated; B seed deviation retained |
| E | PASS_METHOD_LEVEL_WITH_LIMITS | seven paired native nonphysical cases; genuine survey equivalence NOT_EVALUATED |
| F | BLOCKED_AUTHORIZATION | real-survey zero-retention not evaluated |
| G | BLOCKED_AUTHORIZATION | four matched real integrals not executed |
| H | NOT_EVALUATED | convergence/coverage not measured |
| I | INCONCLUSIVE | historical sigma provenance known; target absolute normalization unresolved |
| J | PASS_HISTORICAL_MODEL_SCOPE | two original Higgs lineages, missing BR applied exactly once; corrected source absent |
| K | PASS_HISTORICAL_CHAIN_ONLY | preserved genuine chains and new read-only ROOT weights/object regression; corrected chain absent |
| L | PASS_EXISTING_INPUT_SCOPE | frozen cuts, null handling, weighted cutflow and numerical methods |
| M | PASS_EXISTING_ME_ROW_METHOD | 6000 genuine old ME rows; quadratic/interference/SM closure regression; no new ME |
| N | LIMITED | per-bin support flags; kappa2.5/5 INCONCLUSIVE_REWEIGHTING |
| O | PASS_MODEL_DIAGNOSTIC_ONLY | six backgrounds independently compared; no combined physical yield |
| P | PASS | all 8420 protected campaign files and historical references preserved |
| Q | PASS | five implemented modes, two denied future modes, actual CLI/resume/tamper tests |
| R | VERIFY_AT_DELIVERY_HEAD | final CI, outgoing payloads and actual remote blobs checked after publication |
| S | OUTSIDE_PHASE7_BLOCKED | background matching/heavy-flavour overlap |
| T | OUTSIDE_PHASE7_BLOCKED | photon-fake calibration |
| U | OUTSIDE_PHASE7_BLOCKED | official detector/systematics |
| V | OUTSIDE_PHASE7_BLOCKED | combined physical likelihood/sensitivity |

未進行新genuine ME、survey、獨立hard events、LHE sample或物理Pythia/Delphes。暫存method candidates不算新physical source。
資源為有界實測子集合與磁碟快照，不編造全task CPU/wall總和。完整integration/corrected-source numerical結果以null標示未執行原因。
下一步只需審查本次單一review surface的exact code/config/seed/retention與上限，再另行明確授權Stage A；修正SM1000需要另一項授權及Phase7I先決條件。


本報告為新增收尾紀錄，未覆寫歷史科學報告。原始 source/card/weight/6000 ME rows 及 F/G failures 保留。
證據：[manifest](../simulation/hh_signal/final_closure/evidence/manifest.json)、[操作指南](../simulation/hh_signal/final_closure/USER_GUIDE_ZH_TW.md)、[最終驗收](phase7_final_acceptance.md)。

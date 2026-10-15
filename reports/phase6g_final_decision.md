# Phase6G 最終 acceptance decision

| Requested field | Actual result |
| --- | --- |
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE6G_THREE_NEW_BACKGROUNDS_FULL_CHAIN_1K_V1 |
| STATUS | PASS_TASK_ACCEPTANCE_WITH_INTERPRETATION_LIMITS |
| MG5_VERSION | 3.5.16 |
| PYTHIA_VERSION | 8.317 |
| HEPMC_VERSION | 3.3.1 |
| DELPHES_VERSION | 3.5.1 |
| ROOT_VERSION | 6.40.04 |
| B04_PROCESS | generate p p > z h QCD=0 QED=2, z > b b~ |
| B04_MG5_EVENTS | 1000 |
| B04_CROSS_SECTION_PB | 0.08953800 |
| B04_INTEGRATION_UNCERTAINTY | 0.0003975100 |
| B04_HEPMC_EVENTS | 1000 |
| B04_DELPHES_ENTRIES | 1000 |
| B04_FINAL_CUTFLOW | 1000/370/220/77/75 |
| B04_HIGGS_DECAY_VALIDATION | Hgg birth events=1000 |
| B04_BR_WEIGHT_CLOSURE | PASS / MODEL_BR_ONLY |
| B05_PROCESS | generate p p > t t~ h QCD=2 QED=1 |
| B05_MG5_EVENTS | 1000 |
| B05_CROSS_SECTION_PB | 0.3991820 |
| B05_INTEGRATION_UNCERTAINTY | 0.001975393 |
| B05_HEPMC_EVENTS | 1000 |
| B05_DELPHES_ENTRIES | 1000 |
| B05_FINAL_CUTFLOW | 1000/327/322/131/131 |
| B05_HIGGS_DECAY_VALIDATION | Hgg birth events=1000 |
| B05_BR_WEIGHT_CLOSURE | PASS / MODEL_BR_ONLY |
| B05_TOP_W_DECAY_SCOPE | PYTHIA_INCLUSIVE_SUPPORTED_MODEL; production-decay spin correlations NOT_VALIDATED |
| B06_PROCESS | generate p p > b b~ a j4 QCD=3 QED=1 |
| B06_MG5_EVENTS | 1000 |
| B06_CROSS_SECTION_PB | 65.88309 |
| B06_INTEGRATION_UNCERTAINTY | 0.3918004 |
| B06_HEPMC_EVENTS | 1000 |
| B06_DELPHES_ENTRIES | 1000 |
| B06_FINAL_CUTFLOW | 1000/2/2/2/0 |
| B06_PROMPT_PHOTON_VALIDATION | One-Born-photon identity events=1000 |
| B06_PHOTON_FAKE_STATUS | BLOCKED_UNCALIBRATED |
| TOTAL_MG5_EVENTS | 3000 |
| TOTAL_HEPMC_VALIDATED | 3000 |
| TOTAL_DELPHES_ENTRIES | 3000 |
| RAW_WEIGHT_ACCOUNTING | Original XWGTUP/full original1000; source/Info/converter closure; per-process separate |
| MODEL_BR_WEIGHT_ACCOUNTING | Actually initialized missing Hgg factor once on original raw source contribution; MODEL_BR_ONLY; no Z factor or HH2 |
| BACKGROUND_OVERLAP_STATUS | UNKNOWN_AND_BLOCKED_FOR_COMBINED_YIELDS |
| TOTAL_RUNTIME | 1139.76578759 seconds (controller/build/production; independent QA excluded) |
| PEAK_MEMORY | 731365376 bytes sampled process-tree RSS; instantaneous peak UNKNOWN |
| TOTAL_DISK_USAGE | 1696655731 bytes observed physical run trees |
| REGRESSION_TESTS | PASS 16 retained suites /42 C++ tests /existing3000 native ROOT; new tests and actual independent QA receipts separately retained |
| GITHUB_CI | PASS_2_OF_2_RUNS_AT_VERIFIED_SOURCE_EVIDENCE_HEAD |
| GITHUB_REFERENCE_SAMPLES | LOCAL_PREPARED_AND_VALIDATED_90_FILES_47102739_BYTES; REMOTE=PASS_90_ACTUAL_GITHUB_BLOBS_47102739_BYTES |
| GATES_PASS | A,B,C,D,E,F,G,H,I,J,K,L,M,N |
| GATES_FAIL | NONE |
| GATES_BLOCKED | O,Q |
| GATES_UNKNOWN | P |
| COMMIT_HASH | 1c4e4add9de4e13c5c4e6d255723665379a39847 |
| PR_URL | https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/18 |
| FINAL_VERDICT | PASS_THREE_FULL_CHAINS_WITH_SCOPE_LIMITS |
| NEXT_RECOMMENDED_STEP | Review frozen source/evidence and selected references; establish photon-fake, overlap and precision calibration models before physical combined-yield interpretation. No additional production is authorized. |

完整資料鏈 verdict 只採 actual original source、full1000 HMC、full1000 ROOT/native numerical receipts。O/P/Q保持獨立interpretation limits；metadata status不構成official ATLAS或完整physical background normalization。GitHub欄位是所附actual receipt snapshot；exact final-head CI需在PR核對。

[Full run manifest](../metadata/phase6g_run_manifest.json)；[quality gates](../metadata/phase6g_quality_gates.json)；[Traditional Chinese executable guide](../simulation/new_backgrounds/USER_GUIDE_ZH_TW.md)。

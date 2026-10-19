# Phase10 完整驗收報告

**PASS_PHASE10_FEASIBILITY_WITH_LIMITS**：來源工程、既有資料診斷與方法驗證通過；物理總背景仍 BLOCKED。沒有啟動新物理生成。

## 實際成果與限制

獨立 A05 審查實際核對6000筆來源 joins、16569個 eligible native jet bit0、1200個 HF Decimal70比較、510個stage／region比較及108個背景 histogram（3862個數值比較）。歷史4668個ROOT物件以原始manifest／canonical digest綁定：4800個邏輯描述包含4052TH1D＋616TH2D及132個未定義shape描述；不宣稱新ROOT histogram重讀。只有3個選定原始Pythia圖見證被獨立重判，並未獨立重分類全部graph。

B01／B02／B03原始N各1000，五階段保留1000/446/266/91/28、1000/378/241/7/1、1000/445/277/0/0。2220列strata、6000列event-unit covariance及60列overlap診斷，不產生物理加總。另一實作核對2160個選定covariance、180個strata與全部6000列schema／symmetry，共40296checks、0errors；共享persisted shower／hadron標籤的限制明列。

新native scalar profiling讀取六背景6000筆、8079個photon、132個electron、19568個jet；Photon isolation有1941個非零值，但已保存photons都受既有0.12篩選。沒有相容tight／anti-tight／conversion及nonisolated controls，無法量測真實fake transfer。6298 prompt／24 radiation／3electron-associated／674unknown維持原義，unknown不叫fake。12個synthetic sideband檢查不進入物理結果。

Generator比較涵蓋8種方案，檢查既有MG5 3.5.16／Pythia8.317來源、4F／5F、mass、PDF／alpha_s、photon IR及matching介面。未找到精確過程已驗證方案，因此不推薦套用預設MLM／CKKW-L／FxFx。Future pilot保持inactive、noninstantiable、null merging scales及另行授權要求。

精度規劃覆核全部88／3648／16列，共42078個獨立算術checks、0errors。B02在原proposal下20% acceptance plug-in N=24975、固定原始N Bessel rate版本25000，CP-p情境4473–987435；均非保證。B03／B06各0/1000仍有95%上限，不推得有限保證N。κ2.5／5支持不足，沒有新ME weights；重抽樣不增加hard statistics。

## 測試、保存與交付範圍

143項Phase10、165項Phase9、92項Phase8 Python測試、9項不同ROOT/C++ CTest及5個歷史參考驗證皆實際通過。Phase10 Python另由CTest包裝再次通過，不能重算成新的143項獨立測試。新standalone CMake重用未變的Phase8 adapter，舊root CMake與工作流程原樣保留。

前四次A checker失敗皆保存：Wilson端點、executed-source／delivery邊界、舊BASE與新worktree比較、邏輯descriptor／ROOT物件口徑。修正均有負向測試，最終A05才列PASS；這些不是新的物理replica，也不代表獨立人類簽核。

970個受監測歷史檔案共2437833683bytes前後SHA256一致，包括全部Phase9本地圖件版本／收據；舊PR24/25/26仍open Draft且head未變。Phase7I stopped checkout核對head／index並未派送寫入；不宣稱遞迴雜湊所有停止工作區。12組既有圖維持AWAITING_USER_APPROVAL；本次未重畫、未提交PDF/PNG。

GitHub只驗證來源／方法及有界已發布證據。完整本機ROOT／LHE／HepMC檢查由獨立local receipts界定；不把CI綠燈叫作完整資料重跑。最終HEAD的CI及遠端逐檔bytes收據，在不可自我引用的本機FINAL_REPORT.json記錄。

## 要求欄位

**PROJECT:**

ATLAS_HH_BBGG_PUBLIC_V1

**TASK:**

PHASE10_BACKGROUND_MODEL_FEASIBILITY_V1

**BASE_REVISION:**

ebae34fdaf9ccb09c77bd47cb1c7827fa560de0a

**NEW_SOURCE_REVISION:**

reviewed worktree; source commit recorded by delivery commit

**DRAFT_PR_URL:**

new stacked Draft PR created after reviewed source payload push

**PHASE9_INDEPENDENT_REVIEW:**

PASS_INDEPENDENT_PHASE9_REVIEW_WITH_LIMITS; final A05 only; no external human approval

**ACTUAL_EXISTING_EVENTS_USED:**

```json
{
  "raw_joins_background": 6000,
  "new_ROOT_scalar_profile_background": 6000,
  "HF_original_sources": 3000,
  "historical_all_sources": 7100,
  "independent_new_hard_sources": 0
}
```

**HF_SOURCE_STRATIFICATION:**

2220 strata /6000 covariance /60 overlap rows; full original N=1000 per cohort; no physical sum

**HF_GENERATOR_SCHEME_COMPARISON:**

8 source-audited schemes; source support != exact-process validation

**RECOMMENDED_MATCHING_CANDIDATE:**

NO_VALIDATED_MATCHING_PRESCRIPTION_YET

**SCHEME_VALIDATION_STATUS:**

UNVERIFIED_EXACT_PROCESS; FxFx HF-core restriction INAPPLICABLE where documented

**FUTURE_GENERATOR_PILOT:**

PREPARED_INACTIVE_BLOCKED; noninstantiable; null unvalidated settings

**SOURCE_AND_CARD_REVIEW:**

24 installed/historical source hashes; exact syntax proposals comment-only; no MG5 parser/run

**PHYSICAL_PILOT_EXECUTED:**

NO

**PHOTON_FAKE_OBSERVABILITY:**

BLOCKED_MISSING_COMPATIBLE_OBSERVABLES; no validated tight/anti-tight/conversion; nonisolated controls censored

**COMPATIBLE_PUBLIC_CALIBRATION:**

NONE_VALIDATED_FOR_LOCAL_OBJECTS; no efficiency imported as fake probability

**SYNTHETIC_SIDEBAND_CLOSURE:**

PASS_SYNTHETIC_METHOD_ONLY;12 checks;20 photon fixtures

**PHYSICAL_FAKE_RATE:**

UNKNOWN

**RARE_BACKGROUND_PRECISION:**

10/20/30/50% scenarios;88 rows /3648 bin rows /16 kappa rows; conditional fixed-proposal estimates only

**B02_SAMPLE_REQUIREMENTS:**

```json
{
  "20percent_acceptance_total_N": 24975,
  "20percent_weighted_source_rate_total_N": 25000,
  "20percent_CP_p_envelope_total_N": [
    4473,
    987435
  ],
  "guaranteed_production_requirement": false
}
```

**B03_B06_ZERO_SUPPORT:**

0/1000; one-sided95 p_upper=.002991249545095296; no finite guaranteed precision N

**KAPPA_SUPPORT_PLAN:**

2.5/5 final ESS16.073571/7.650124; frozen proposal and dominant events; no new ME weights/events; known-density MIS future proposal only

**ANALYSIS_NOTE:**

reports/phase10g_analysis_note.md;15 Traditional Chinese sections

**LOCAL_FIGURE_REVIEW:**

12 historical local sets; source-manifest/caption/SHA review; priorQA retained; no new visualQA/regeneration

**FIGURE_PUBLICATION:**

NO

**PHYSICAL_TOTAL_BACKGROUND:**

BLOCKED

**PHYSICAL_SIGNIFICANCE:**

NOT_EVALUATED

**PHYSICAL_CLs:**

NOT_EVALUATED

**PHYSICAL_KAPPA_INTERVAL:**

NOT_EVALUATED

**ROOT_VERSION:**

6.40.04 / C++20

**TESTS:**

```json
{
  "Phase10_Python": 143,
  "independent_precision_checks": 42078,
  "independent_HF_checks": 40296,
  "independent_HF_covariance_entries": 2160,
  "independent_background_histograms": 108,
  "independent_histogram_numeric_comparisons": 3862
}
```

**EXISTING_REGRESSIONS:**

```json
{
  "Phase9_Python": 165,
  "Phase8_Python": 92,
  "distinct_CPP_ROOT_CTest": 9,
  "Phase10_Python_CTest_wrapper": 1,
  "historical_reference_validators": 5,
  "status": "ALL_PASS"
}
```

**SOURCE_HASH_CLOSURE:**

Per-module execution before/after SHA256 and final source manifest; report-only delivery distinction explicit

**HISTORICAL_PRESERVATION:**

```json
{
  "files": 970,
  "bytes": 2437833683,
  "status": "PASS_EXACT_BYTES",
  "old_PRs": "24/25/26 open Draft exact original heads; no mutation",
  "stopped_workspace_scope": "exact old source head/index checked; no write dispatched; no claim of recursive audit of every stopped file"
}
```

**GITHUB_FINAL_HEAD_CI:**

Verified externally after exact final delivery HEAD in local FINAL_REPORT.json

**REMOTE_BLOB_VERIFICATION:**

Verified externally after exact final delivery HEAD in local FINAL_REPORT.json

**NEW_ME_CALLS:**

0

**NEW_INTEGRALS:**

0

**NEW_HARD_EVENTS:**

0

**NEW_PYTHIA_EVENTS:**

0

**NEW_DELPHES_EVENTS:**

0

**GATES_PASS:**

```json
[
  "INDEPENDENT_A05_6000_SOURCE_JOINS",
  "HF_3000_ORIGINAL_EVENT_STRATIFICATION",
  "INDEPENDENT_HF_EVENT_UNIT_COVARIANCE",
  "ACTUAL_6000_ROOT_PHOTON_SCALARS",
  "INDEPENDENT_PRECISION_ARITHMETIC",
  "143_PHASE10_TESTS",
  "165_PHASE9_TESTS",
  "92_PHASE8_TESTS",
  "9_CPP_ROOT_TESTS",
  "5_HISTORICAL_REFERENCE_VALIDATORS",
  "970_HISTORICAL_FILE_HASHES",
  "INACTIVE_PILOT_AND_NO_PHYSICAL_PRODUCTION",
  "RESOURCE_CONTAINMENT"
]
```

**GATES_FAIL:**

```json
[]
```

**GATES_BLOCKED:**

```json
[
  "PHYSICAL_TOTAL_BACKGROUND",
  "MATCHED_SIGNAL_NORMALIZATION_PHASE7I",
  "HF_GENERATOR_EXCLUSIVITY",
  "ACTUAL_FAKE_TRANSFER_MEASUREMENT",
  "UNVALIDATED_NUISANCE_MODEL",
  "PHYSICAL_PILOT_PENDING_SEPARATE_APPROVAL",
  "PDF_PNG_PUBLICATION_PENDING_USER_APPROVAL"
]
```

**GATES_UNKNOWN:**

```json
[
  "PHOTON_FAKE_RATE",
  "UNVALIDATED_NUISANCE_VALUES_AND_CORRELATIONS",
  "EXACT_MATCHING_PRESCRIPTION",
  "FUTURE_PHYSICAL_NORMALIZATION"
]
```

**FINAL_VERDICT:**

PASS_PHASE10_FEASIBILITY_WITH_LIMITS

**NEXT_RECOMMENDED_STEP:**

Review inactive exact-process flavour/PDF/alpha_s/photon-IR and calibration contracts. Physical generation requires new exact-source approval, finite resource envelope and new output directory; do not auto-start.

## 證據入口

- [A 獨立覆核](phase10a_independent_review.md)／[B 重味分層](phase10b_hf_stratification.md)
- [C Generator 策略](phase10c_generator_strategy.md)／[D 未啟用 pilot](phase10d_pilot_contract.md)
- [E Photon feasibility](phase10e_photon_fake_feasibility.md)／[F 精度規劃](phase10f_precision_plan.md)
- [G 完整科學筆記](phase10g_analysis_note.md)／[操作說明](../analysis/phase10/README_ZH_TW.md)

已知物理blockers保留；下一步僅為review，任何新pilot都需要另外明確授權。

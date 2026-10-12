# Phase 5 study regions and synthetic transfer-factor feasibility

**Verdict: PARTIAL.** The reusable region partition and synthetic covariance-aware transfer-factor framework pass their focused C++20 tests. **Physical transfer-factor application and physical CR/VR closure remain BLOCKED.** A synthetic PASS establishes the equations, event partition and input guards only; it supplies no measured background composition, continuum prediction or HH sensitivity.

## Preserved inputs and proposed region definition

The classifier reuses `atlas::selection` and the unchanged [Phase 3 configuration](../metadata/phase3_selection_config.ini), SHA-256 `77d57cd6fa204aad5a24031ac925c4e20e121b8aee35148cc29b522b39cf5751`. Its input is the valid pre-mass-cut **C5** population, followed by the separate existing jet multiplicity, pT and acceptance predicates from C7–C9. It deliberately evaluates these jet predicates without requiring C6 first. Events with mγγ below105 or above160 remain observable as `OUTSIDE_STUDY_DOMAIN`; they cannot be recovered by inspecting only C9. Invalid native tuples remain invalid. No kinematic reconstruction, units, event weights or historical cutflow is changed. Unit provenance remains **PROVISIONAL**, as recorded by the [Phase 4 numerical-recovery decision](phase4_numerical_recovery_decision.md).

The declared domain is105≤mγγ≤160 GeV. The candidate window is120≤mγγ<130 GeV. Define A by |ηγ1−ηγ2|<1 and B by |ηγ1−ηγ2|≥1, using the same leading photons as the existing selection. These thresholds are explicit study choices, not optimized or adopted from an official ATLAS HH analysis.

| Region | Photon partition | Mass requirement | Role |
|---|---|---|---|
| CR | A | [105,120)∪[130,160] | Candidate sideband calibration |
| VR | B | [105,120)∪[130,160] | Separate candidate sideband validation population |
| Prospective SR | A | [120,130) | Candidate central-window study |
| Reserved window partition | B | [120,130) | Unassigned; excluded from calibration/validation |
| Outside study domain | Either | mγγ<105 or mγγ>160 | Descriptive pre-mass coverage only |

All three named regions have disjoint event membership. This does **not** establish statistical independence of mass and |Δηγγ|, nor independence of their nuisance parameters or transfer factors. The shape correlation must be measured with compatible physical input before using VR to constrain an SR extrapolation. The reserved population makes the incomplete coverage explicit instead of silently allocating the same central-window events to validation.

The photon baseline remains pT1>35 GeV, pT2>25 GeV, |η|<2.37 with only the open crack interval1.37<|η|<1.52 excluded. Both leading inclusive jets must have pT>25 GeV and |η|<2.5. Existing optional tight-ID/isolation diagnostics remain optional. **Inclusive jets are not identified b jets**, so these are diphoton-plus-jets study regions. Background dominance, prompt/fake composition and signal contamination are **UNKNOWN**. The data mass histograms have already been inspected; this proposal makes no retrospective blinding claim.

The machine contract is [phase5_region_config.json](../metadata/phase5_region_config.json). The implementation is [AtlasControlRegions.h](../include/AtlasControlRegions.h) and [ControlRegions.cxx](../src/ControlRegions.cxx). `classify` returns one named region or an explicit invalid, selection-failure, reserved or outside-domain state. Boundary variations are permitted only through a separate explicit configuration; they leave the underlying Phase 3 thresholds unchanged.

## Synthetic statistical contract

The module reuses `atlas::normalization::SignedSums`, its signed-denominator conditioning and the explicit pairwise sample-disjointness contract. Every synthetic yield supplies a complete event-identity ledger with canonical sample namespace, run and event. A new cut label or reweighting does not create a new identity. Repeated identities within a yield or across calibration populations are rejected. `require_held_out_validation` checks the MC calibration ledger when given a transfer result; when given a prediction it additionally excludes DATA_CR and contamination input identities from held-out validation. The prediction's sample contract must cover the union of calibration and residual namespaces, with verified disjoint disposition for every pair, including main-MC versus contaminant-MC. Disjoint event IDs alone do not resolve overlapping generator populations. Missing, duplicate, overlapping or unknown mixed-sample evidence is rejected even for fixtures; synthetic evidence labels attest only the toy generators, never a real MC mixture.

For S=MC_SR and C=MC_CR, the synthetic ratio and its first-order uncertainty are

```text
T = S/C
J_T = (1/C, -S/C²)
Var(T) = J_T Cov(S,C) J_Tᵀ
       = Var(S)/C² + S² Var(C)/C⁴ - 2 S Cov(S,C)/C³.
```

The denominator must satisfy the explicit numerical condition |sumw|/sumabs>10⁻¹² by default. Zero or near-cancelling signed denominators are rejected. Negative signed weights, signed sums and negative numeric toy predictions are preserved; they are not repaired with absolute values, zeros or clipping, and are not interpreted as physical negative rates. This is a numerical conditioning criterion, not a statistical-significance test. First-order ratio propagation is not an exact small-count interval and is not reliable merely because a denominator passes the numerical check; a physical low-count/cancellation model would require a separately validated statistical treatment.

For an explicitly modelled multi-background toy, X=D_CR−ΣB_other,CR uses the **full** supplied covariance with derivative a=(1,−1,…). The prediction is

```text
B_pred,SR = T X
Var(X) = a Cov(D_CR, B_other,CR, ...) aᵀ
Var(B_pred,SR) = X² Var(T) + T² Var(X) + 2 T X Cov(T,X).
```

The covariance must be finite, symmetric, dimensionally consistent and positive semidefinite. A pure counting covariance has diagonal sumw2. An explicit synthetic nuisance model may increase the diagonal and supply correlations; no nuisance parameter is estimated or constrained by this module. Cross covariance is checked against its positive-semidefinite bound. Negative propagated variance is rejected. Covariance validation uses a named long-double arithmetic residual bound only; the reconstruction mass tolerance is untouched. The module implements neither an exact product-distribution interval nor second-order propagation, template fitting, likelihood profiling or a physical multi-background model.

Both transfer and prediction APIs explicitly reject `Scope::Physical`; normalization evidence or a nominal sample label cannot enable them. The default-constructed or subsequently modified transfer result is also rejected. Physical use therefore cannot be activated by merely counting these regions or passing the existing numerical tests.

## Executed focused evidence

The focused test compiled in the existing ROOT6.40.04/C++20 conda environment with `-Wall -Wextra -Wpedantic -Werror` and executed successfully:

```text
PASS control-region contract: 1887 assertions,
1782 independent partition fixtures, 51 rejection cases; SYNTHETIC ONLY
```

The independent partition oracle covers27 explicit window/split configurations,11 mass values and6 photon separations; exact outer/window/split boundaries and `nextafter` neighbours are also checked. It checks unchanged strict photon/jet thresholds, crack acceptance, optional ID/isolation behaviour, invalid kinematics and an outside-C6 event that passes C5.

Independent hand-derived fixtures establish T=40/100=0.4 with Var(T)=0.0056; subtraction of two contaminants gives X=200−30−20=150, Var(X)=250, B=60 and Var(B)=166. Separate fixtures test correlated yields, a common nuisance outer-product covariance, nonzero Cov(T,X), signed numerators/denominators, singular positive-semidefinite covariance and zero numerator. A held-out toy uses disjoint calibration and validation identities, T=160/400=0.4, validation-CR=250 and an engineered observed-VR=100; prediction100 with propagated variance127.5 reproduces this toy by construction. **This is synthetic closure only.** It asserts no physical VR/CR ratio equality, signal-free region or validated continuum shape.

The51 rejection cases include zero/near-zero signed denominators, malformed thresholds, incomplete/repeated event ledgers, reused MC/DATA_CR/contamination calibration events, unverified/overlapping sample combinations, missing calibration or main-MC/contaminant pair evidence, wrong covariance dimensions/diagonals, asymmetry, nonfinite/indefinite covariance, invalid cross covariance, forged/modified transfer results and physical application. The implementation does not run a physical fit or read physical ROOT events in this focused test. Full integrated CTest evidence is recorded separately by the Phase 5 orchestration; a focused PASS is not reported here as an integrated-suite PASS.

After CMake integration, reproduce with the existing Phase2–5 options and run:

```bash
ctest --test-dir <phase5-build-directory> -R control_region_contract --output-on-failure
```

The test executable accepts the existing `metadata/phase3_selection_config.ini` path and verifies all its current threshold values before exercising the proposed partition.

## Bounded descriptive cache inventory

[phase5_region_inventory.cxx](../apps/phase5_region_inventory.cxx) reads only the exact historical DATA28-column Phase2 or MC24-column Phase4 derived event-cache schema. It requires the complete explicitly requested contiguous range (at most64,000 entries), finite recorded values when objects are present, consistent missing fields when objects are absent/invalid, strict booleans/native count ranges, unique sample/run/event identities, unchanged MC C9 agreement, and no valid MC row with an unresolved recorded mass-closure failure. It rejects a mismatched schema, DSID, row width, order, numerical field, unit status or existing output path. It neither reopens ROOT nor duplicates four-vector reconstruction. A derived-cache PASS is not an independent verification of the original ROOT provenance; the orchestration separately pins cache/input checksums.

```bash
phase5_region_inventory events.csv metadata/phase3_selection_config.ini \
  NEW_output DATA 100 63195 PROVISIONAL
phase5_region_inventory events.csv metadata/phase3_selection_config.ini \
  ANOTHER_NEW_output 343981 100 10000 PROVISIONAL
```

Each fresh output directory contains `event_regions.csv`, `region_counts.csv` and `summary.json`. The ledger preserves identities, cache validity, C5, C5-plus-jets, C9, exact region membership and the supplied raw weight. Eight region rows partition the input; separately marked diagnostic population rows overlap cumulatively and must not be summed together. Counts and signed sumW/sumW2/sumabs/effective-entries are descriptive. MC weight semantics remain **UNKNOWN**, so these raw moments are not promoted to a generator-weighted physical shape or normalization. DATA raw weights are one. No SF, luminosity normalization, physical TF, ratio fit or figure is generated.

The new deterministic Python driver suite passes **10/10 tests**. Fixtures verify outside-domain C5 events, exact boundary ownership, reserved-window C9 conservation, missing objects/invalid rows, signed moments independently checked with Decimal, schema/identity/MC C9/closure guards, bounded parsing, unchanged input hashes, preservation of an existing output directory, and reproducible ledger/counts with LF versus CRLF. Any physical occupancy produced by the orchestration is a descriptive inventory only; it cannot unblock physical CR closure.

## Physical feasibility and blockers

| Requirement | Current scope/status |
|---|---|
| Deterministic, mutually exclusive region partition | PASS, code and synthetic oracle |
| Signed TF/subtraction/covariance arithmetic | PASS, synthetic equations and guards |
| Held-out event-ledger separation | PASS, synthetic rejection contract; physical identities still require audit |
| Independence of \|Δηγγ\| and mass/background shape | UNKNOWN |
| Compatible DATA/MC trigger, selection and photon composition | UNKNOWN; no new efficiency correction is applied |
| Continuum generated/reconstructed phase-space support at all proposed edges | BLOCKED pending physical input and coverage audit |
| Region-specific sample mixture and signal contamination | UNKNOWN |
| Applicable luminosity, signed pre-skim generator denominator, SF conventions | BLOCKED for absolute physical prediction |
| Physical CR/VR closure or physical SR background prediction | BLOCKED |

The baseline numerical-recovery PASS establishes pair arithmetic, not any of these missing physics inputs. Official public-input provenance must be taken from the Phase5 source, weight and luminosity audits for [GamGam DATA record93915](https://opendata.cern.ch/record/93915) and [MC record93922](https://opendata.cern.ch/record/93922). Different DSIDs, generator mass boxes or region labels alone do not prove that generated samples are exclusive. A generated-mass filter is not a reconstructed-mass support guarantee: migration and acceptance at both edges must be examined without extrapolating unsupported populations. No physical yield ratio is computed in this report.

The orchestration subsequently executed the descriptive C5-plus-jets inventory using the fresh integrated binary: DATA C9=1689, and MC343981/346214/423103 C9=1125/1419/588, exactly matching historical cutflows. Outside-domain counts are7348/2/21/1627 respectively. These are complete bounded-cache partitions with no physical ROOT reread, SF, normalization or TF. Actual region counts and identity hashes are recorded in [phase5_decision.md](phase5_decision.md), [phase5_region_occupancy.csv](../metadata/phase5_region_occupancy.csv) and the quality-gate evidence. The integrated suite executed **23/23 CTest PASS**, including this contract and the10 driver tests; it does not establish physical closure.

Next, establish continuum access and generator/SF conventions, validate selection/trigger compatibility and signal-contamination assumptions, and design a held-out model that tests the relevant mass/split correlation. Real closure, nuisance constraints and any background-prediction approval require that evidence. No figure is generated by this module, and no official ATLAS HH reproduction, b tagging, signal extraction or sensitivity claim is made.

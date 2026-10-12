# Phase 5 generator normalization contract

Date: **2026-10-12**. Engineering scope: **synthetic signed-weight regression PASS**. Physical application: **disabled by default and not executed**. Absolute reconstructed DATA/MC normalization and SF application remain **BLOCKED**. This additive module does not change Phase 3 selection, the shared Phase 4 Cartesian reconstruction, historical weights, histograms, cutflows or the preserved negative-M²/failure evidence.

The implementation is [AtlasNormalization.h](../include/AtlasNormalization.h) and [Normalization.cxx](../src/Normalization.cxx), namespace `atlas::normalization`. It uses the existing ROOT **6.40.04**, C++20, conda GNU **15.3.0-7** toolchain. Fresh `root-config --version` and compiler output are recorded with actual commands, completed compilation exits and SHA-256 values in local `.local/build_phase5_normalization_agent/execution_reviewed.json`. This module itself opens no ROOT input, applies no reconstruction or selection, and generates no figure.

## Conditional generator-level formula

Only after the declared ingredients are verified, the generator-level scale is

\[
 a={L\,[\mathrm{pb}^{-1}]\,\sigma\,[\mathrm{pb}]\,\epsilon_{\rm filter}\,k\over
         S_{\rm generated}},\qquad w_i^{\rm scaled}=a\,g_i,
 \qquad S_{\rm generated}=\sum_{\text{full pre-skim generation}}g_i.
\]

The algebra is the conditional formula requested for Phase 5, **before any reconstruction SF**. No extra branching-ratio multiplier is implemented: the verified cross-section/filter/decay convention must already establish what is included. `num_events`, inspected/selected event counts, absolute weights, sumW2, and selected-bin sums are not substitutes for the signed pre-skim denominator. The preserved [Phase 4 weight readiness assessment](phase4_weight_readiness_update.md) documents the unresolved exact FEB2025 producer, metadata/skim conventions, signed sums, filter efficiency mismatch, decay convention, luminosity and correction applicability. The official [ATLAS educational metadata guidance](https://opendata.atlas.cern/docs/data/for_education/13TeV25_metadata) is a provenance reference for that audit; this engineering implementation does not resolve those inputs.

`GeneratorNormalizationContract` defaults to `Scope::Physical`, `enable_physical=false`, and UNKNOWN evidence. It requires explicit sample and production identities, positive generated count, finite numerical inputs, and **Verified evidence with nonempty reference and description** for each of:

| Declaration | Required scope |
|---|---|
| Sample provenance | Exact released sample and production identity |
| Nominal generator-weight semantics | Correct signed nominal event-weight convention |
| Pre-skim denominator | Full signed generated sum, not a skim/subset sum |
| Cross-section convention | Units and exact process/production convention |
| Filter efficiency | Applicable filter and factors already included |
| k-factor | Applicable production convention |
| Branching-ratio convention | Explicit exclusion of double counting |
| Processing completeness | Full generated/input aggregation accounted for once |
| Luminosity applicability | Exposure appropriate to the actual target sample |

Enabling the physical flag alone does not bypass missing declarations. The code checks the declaration's completeness and numerical consistency; it cannot authenticate a scientific source merely from a caller-supplied `Verified` field. A provenance reviewer must establish each actual ingredient before making that declaration. Synthetic fixtures declare their own analytical definitions and return `Scope::Synthetic`; they are not evidence for real samples.

The returned `GeneratorScale` is explicitly labelled **`GENERATOR_LEVEL_ONLY; RECONSTRUCTED_SF_APPLICABILITY_NOT_VALIDATED`**. `apply_scale_factors=true` throws. Unknown/negative BTAG, FTAG, PHOTON, PILEUP or JVT semantics are not silently approved by a generator-only scale. No SF value is read, multiplied, replaced by unity/zero/absolute value, or inferred from a generator-weight sign. The module does not support a corrected reconstructed yield prediction. Default/unvalidated or subsequently modified scale objects are refused by `scaled_generator_weight`.

## Signed accumulation and cancellation policy

`SignedSums::add` retains each finite signed weight. Compensated extended-precision sums record

\[
 S=\sum_i w_i,\qquad Q=\sum_i w_i^2,\qquad A=\sum_i|w_i|,
 \qquad N_{\rm eff}=S^2/Q\quad(Q>0).
\]

Positive, negative and zero entry counts are distinct. `sumabs` is a cancellation diagnostic, **never** the normalization denominator. `effective_entries()` is a weight-moment diagnostic, can be fractional or below one, and is not a reconstructed event count, efficiency, luminosity or confidence interval. It returns zero for all-zero weights. `from_aggregates` explicitly marks sign counts UNKNOWN when only aggregate totals are supplied; they are not invented from the total's sign. `merge` retains signed moments across partitions.

The numerical conditioning policy rejects **`S == 0`** or

\[
 |S|/A\;\le\;10^{-12}.
\]

It rejects an empty/all-zero sum and requires a finite configured threshold strictly between zero and one. This explicit new policy guards arithmetic cancellation; it does not change any historical reconstruction tolerance or impose a statistical-significance requirement. Stable negative denominators remain signed and are allowed; normalizing by a negative total does not authorize an absolute-value replacement. The available actual pre-skim `sumabs` is required to assess this policy. If that diagnostic is unknown, it must not be supplied as an assumed unsigned denominator or silently reconstructed from event-count fractions.

Necessary aggregate moment checks enforce `|S| <= A`, `sqrt(Q) <= A`, and, where count is provided, `A/sqrt(Q) <= sqrt(N)` with explicitly bounded arithmetic roundoff. These checks cannot prove complete generation bookkeeping or recover the individual events from aggregates. NaN/infinity, negative Q/A, inconsistent zero Q, squared-weight overflow/underflow, positive scale underflow and nonzero scaled-event underflow throw. Internal moment comparisons use a relative `64*long_double_epsilon` bound; count Cauchy comparisons use `64*double_epsilon`. The separate ROOT-bin/event-ledger serialization bound belongs to the shape module and does not repair either source.

## Sample combination guard

Source samples remain separate by default. `validate_sample_combination` rejects missing/duplicate IDs, known/UNKNOWN overlaps, duplicate pair evidence, and incomplete pairwise disjoint evidence. Every unordered pair of a requested multi-sample mixture needs an explicit **Disjoint** disposition plus Verified evidence. A label such as diphoton or gammajet, a different DSID, or a generated mass box does not establish that physical samples may be added without double counting. A one-sample contract is not a mixture. Physical combination is disabled by default; the control-region module additionally retains its synthetic-only transfer-factor restriction. No real samples are combined here.

## Executed analytical evidence

[test_normalization.cxx](../tests/test_normalization.cxx) executed **70 deterministic assertions, PASS**, including:

- Signed fixture `[3,-1,2,0]`: S=4, Q=14, A=6, two positive/one negative/one zero, and Neff=16/14; partition merge agrees.
- Compensated `[1e20,1,-1e20]` retains S=1 but normalization rejects its extreme relative cancellation; exact zero and near-zero signed sums are rejected.
- Stable `[-4,1]` keeps denominator -3 and Neff=9/17.
- Analytical synthetic `L=100`, sigma=4, efficiency=0.5, k=2, generated S=4 produces scale 100; generator weight -1 remains scaled -100.
- Each of nine UNKNOWN/unreferenced provenance declarations is individually rejected; physical-default, SF request, missing generated count, invalid filter/luminosity and unvalidated/tampered/relabelled scale are rejected.
- Nonfinite/overflow/underflow and impossible aggregate moments are rejected. Known, unknown, duplicate and incomplete sample-overlap contracts are independently exercised.

The synthetic result verifies code behavior and the stated formulas. It does **not** make generator-weight semantics, signed generated denominators, branching ratios, exposure, SFs, processing completeness or sample overlap PASS for the actual MC files.

Reproduce through the parent Phase 5 CMake targets `test_normalization` and `test_shape_comparison` linked to `atlas_normalization` (`ROOT::Core`, `ROOT::Hist`). The focused executed standalone command used the explicit compiler, C++20 and `-Wall -Wextra -Wpedantic`, with the environment's headers/libraries and rpath; no compiler warning was emitted. The final executable was `.local/build_phase5_normalization_agent/test_normalization_reviewed`; retained earlier focused binaries were not overwritten. The shape report records the subsequent local-scale ledger-serialization guard and its additional tiny-weight checks; no historical tolerance was changed.

| Executed source / binary | SHA-256 |
|---|---|
| `include/AtlasNormalization.h` | `d08999881dd8bb29226a378b318b1f22a6944b2b9a9aa7e575bc2335f91f4485` |
| `src/Normalization.cxx` | `19a7a516d2d402fc83b6e422b511f4e69f5ebc13586f1950737c761dd0446e02` |
| `tests/test_normalization.cxx` | `efda50bdea4cec93057b3434a3bcc1cbbd1fbae8cbad3a15999c35b021540200` |
| Focused reviewed normalization executable | `7c67e187fee1db260641cbcb7780522c860cddb38371a445ed725bcda04a2dc8` |

Integrated regression results belong to the Phase 5 quality-gate evidence and decision report; they are not inferred from this focused execution. No physical normalized output, MC mixture, corrected yield, fit, limit or HH sensitivity is established by this contract.

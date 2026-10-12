# Phase 4 numerical recovery V2: physical DATA/MC regression

**PASS_NUMERICAL_RECOVERY for the executed bounded inputs.** This additive report records new runs from historical Phase 4 commit `d823593b42889592897263819138170470f4dc47`. The original `PARTIAL_WITH_FAILED_NUMERICAL_GATE` verdict and its physical Gate C FAIL remain unchanged in the original reports. This V2 result repairs pair arithmetic; it does not validate HH reconstruction, absolute MC/DATA rates, calibration, b tagging, prompt purity, significance, limits or ATLAS-publication reproduction. The [weight readiness update](phase4_weight_readiness_update.md) keeps those independent blockers visible.

## Exact failure and shared correction

The retained original executable reproduced DSID 343981 source entry 5888, run 284500, event 4385033 from the checksum-pinned native file. A is the old ROOT PtEtaPhiE sum; B calls the corrected shared DATA/MC `leading_pair`; C begins with original native Float32 values and computes Cartesian long-double components independently. Per-object interpretation, supplied energies, sorting, angular definitions, units and C0-C9 thresholds are unchanged.

| Exact photon-pair quantity | Actual value |
| --- | ---: |
| A original mass [GeV] | 123.949014957901354705 |
| B corrected returned mass [GeV] | 123.949015149146717363 |
| C independent native-input reference [GeV] | 123.949015149146711076 |
| A absolute residual [GeV] | 1.9124535637071726768e-07 |
| B absolute residual [GeV] | 6.28663787693994891015e-15 |
| Unchanged mass tolerance [GeV] | 1.12394901514914671104e-07 |

The corrected sum retains `ROOT::Math::PxPyPzE4D<long double>` coordinates through component evaluation, addition, M² and square root. Its public mass return remains double. All negative/nonfinite pair M² is still rejected; no clamp, offset, energy correction or MC-only path was introduced. The [Cartesian stability review](phase4_cartesian_stability_review.md) preserves the failed first double-Cartesian candidate (406 strict mass failures and 52 sign mismatches) and all 15,361 final deterministic stress cases, including Float32 phi normalization and extreme conditioning. No failed case or mass tolerance was removed.

## Inputs, ranges and execution

| Pinned sample | Bytes | Exact main range | SHA-256 |
| --- | ---: | --- | --- |
| DATA93915 | 17541818 | [100,63195) | `01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7` |
| 343981 | 32086416 | [100,10000) | `002e890c517e03ba59c49bc0852d0fdcd200e0d48add7ca189228a6f82965c56` |
| 346214 | 14414350 | [100,10000) | `8f32169da2dfa378e4b4d34573bf12a0475934b10cc4ad00e51da89c34bdb908` |
| 423103 | 10489108 | [100,10000) | `c65f7103c8e75c6a0d2faf5488752c2efc08376780c0f04fbe52052ac978da1e` |

DATA has 63,095 unique inspected entries. MC has 9,900 per DSID, 29,700 unique inspected entries; samples remain separate. Both the A/B/C harness and the existing production diagnostic drivers independently traversed these same ranges, so their repeated reads do not add new unique events. One separately logged source-entry read reproduced the historical failure. Nine physical pipeline processes actually completed with exit 0. No new ROOT dataset was downloaded. Input hashes were checked before and after execution.

| Sample | Entries | Nonnegative photon mass comparisons | Nonnegative jet mass comparisons | Corrected observable failures | C9 |
| --- | ---: | ---: | ---: | ---: | ---: |
| DATA93915 | 63095 | 63058 | 17212 | 0 | 1689 |
| 343981 | 9900 | 9900 | 2104 | 0 | 1125 |
| 346214 | 9900 | 9900 | 2297 | 0 | 1419 |
| 423103 | 9900 | 9900 | 3320 | 0 | 588 |

The existing MC driver's strict closure tests also passed independently: 12,004 / 12,197 / 13,220 pairs, **37,421 total**, zero failures. DATA's pair-level comparison population includes valid jets even in the 37 invalid diphoton events; its raw whole-event-valid histograms do not fill those events. Consequently the DATA harness compares 17,212 valid dijet pairs, while the existing whole-event diagnostic histogram/cache has 17,191 dijet fills. These are different explicitly preserved populations, not a lost-event correction.

Mass acceptance remains `abs(error) <= 1e-7 + 1e-10*abs(reference_mass)` GeV. Physical secondary diagnostics use component bound `1e-9+1e-12*abs(reference_component)`, M² bound `1e-9+64*double_epsilon*(E²+px²+py²+pz²)` and angle bound `1e-12` with wrapped deltaPhi residual. These separately declared arithmetic checks never replace mass closure or detector/systematic uncertainties. Relative maxima use nonzero references only.

| Physical observable | B/C comparisons | A maximum absolute residual | B maximum absolute residual | B maximum relative residual | A / B diagnostic failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| px | 117728 | 2.2082335959794364e-13 | 0 | 0 | 0 / 0 |
| py | 117728 | 2.5901503164504902e-13 | 0 | 0 | 0 / 0 |
| pz | 117728 | 4.7515921947072215e-08 | 0 | 0 | 23 / 0 |
| energy | 117728 | 0 | 0 | 0 | 0 / 0 |
| mass2 | 117728 | 4.7409346478843872e-05 | 0 | 0 | 2605 / 0 |
| mass | 117691 | 1.9124535637071727e-07 | 1.4899192990469601e-13 | 1.1047875499344762e-16 | 1 / 0 |
| delta_eta | 117691 | 0 | 0 | 0 | 0 / 0 |
| delta_phi | 117691 | 2.45029690981724e-16 | 2.45029690981724e-16 | 7.6812693130245247e-15 | 0 / 0 |
| delta_r | 117691 | 6.3707719655248241e-16 | 6.3707719655248241e-16 | 5.2451981476372587e-15 | 0 / 0 |

The machine-readable [gate results](../metadata/phase4_numerical_gate_results.json) retain per-sample/per-group counts, maxima, tolerance definitions and all exact paths/hashes. The old implementation's secondary M² or pz diagnostic failures do not independently identify a physically invalid event; strict mass closure and signed reference classification are separately reported.

## Complete event reconciliation

The requested [numerical event diff](../metadata/phase4_numerical_diff.csv) contains **92,795 rows**, one for every processed DATA/MC event, including invalid events. It records identifiers, both masses and their deltas, all angular deltas, validity/issues, both C0-C9 masks, histogram-change flags and pair classifications. It is intentionally committed derived numerical evidence, not a ROOT dataset. Full native objects, A/B/C Cartesian components, individual tolerance/residual tests and per-event histogram placements remain in the new local `outputs/phase4_numerical_v2_20261012/<sample>/regression/` directories; every file is hashed in the gate manifest. Their SHA-256 identities permit exact reconstruction without committing input data or native ROOT outputs.

| Sample | Diphoton returned-mass changes | Dijet returned-mass changes | Event validity changes | C0-C9 membership changes | Histogram event changes |
| --- | ---: | ---: | ---: | ---: | ---: |
| DATA93915 | 44474 | 12604 | 0 | 0 | 0 |
| 343981 | 6985 | 1572 | 0 | 0 | 0 |
| 346214 | 7504 | 1611 | 0 | 0 | 0 |
| 423103 | 7300 | 2413 | 0 | 0 | 0 |

These many small mass-value changes are the expected arithmetic correction, not a claim that previous decimal values were identical. All event identities, supplied object tuples, object order, geometry, raw photon flags and selection definitions are preserved. A/B use the same constructed collections; read-only source review confirms `construct` and input interpretation were not edited. Historical caches persist only their listed leading-object/observable fields, so the independent cache comparison does not claim that an absent old all-object dump was compared. It checks the actual persisted historical fields exactly as parsed binary64 numbers and strings, and the same checks against the fresh production DATA cache.

| Sample | Original = corrected C0-C9 counts, in order |
| --- | --- |
| DATA93915 | 63095, 63058, 63058, 53978, 53978, 51136, 12564, 2842, 1689, 1689 |
| 343981 | 9900, 9900, 9900, 9794, 9794, 9734, 9718, 2073, 1125, 1125 |
| 346214 | 9900, 9900, 9900, 9866, 9866, 9816, 9663, 2251, 1419, 1419 |
| 423103 | 9900, 9900, 9900, 9898, 9898, 9805, 3660, 965, 588, 588 |

There are no selection-category or histogram-bin migrations to explain in these bounded runs. Counts were measured, not forced to their historical values. The [updated per-DSID cutflow](../metadata/phase4_updated_mc_cutflow.csv) records all 30 MC cuts and deltas. Independent Python DATA predicates reproduce all ten cumulative stages and optional-flag diagnostics: 175 C9 events with both tight-ID flags and 48 with both tight ID and tight isolation; those flags remain diagnostics rather than added selection cuts.

The independent DATA cache audit performs **1,766,660 exact field checks per version** over all 63,095 entries. It verifies seven actual native Phase2 TH1 objects against both harness versions: **464 bin positions including flow per version**, plus errors, axes and entry counts. Historical Phase3 did not store a native ROOT histogram file; its preserved actual histogram inventory and independent selected-event bin reconstruction are checked explicitly, rather than inventing a missing native-file check. Four selected histograms are also reconciled with the harness. The independent MC histogram audit compares ten actual TH1 objects per DSID against both A/B harness versions: **4,140 versioned flow-inclusive bin positions**, plus errors, axes and entries. Every old/new bin content, underflow and overflow is identical.

## The 37 negative DATA diphoton combinations

Every historical negative pair is identified in the gate JSON with entry/run/event, original/corrected/reference signed M², exact diagnostic decimal values and its conservative half-ULP bound. All **37 remain negative under the original supplied tuples**, in A, B and native C; all remain invalid under the unchanged strict pair policy. None is repaired by dropping a row, changing energy or clamping M². There are **zero coordinate-conversion sign artifacts among these 37**.

An independent standard-library Decimal review reconstructs exact binary32 input values, computes trig/components and M² at 100 digits, and repeats at 75 digits. It confirms all 37 negative signs with no ROOT event reads or environment changes. All lie within the recorded conservative independent Float32 half-ULP perturbation bounds. A separate energy-only check also finds a pair-M² zero crossing within the assumed upward half-ULP energy allowances for all 37. This is a mathematical existence diagnostic under an assumed rounding interval; it does not identify rounding as the actual cause or establish detector/calibration validity. **Origin remains UNKNOWN**. These are invalid supplied reconstructed combinations under the numerical contract; no claim about the underlying physical event's true invariant is made.

## Matching, signed weights and immutable diagnostics

All **252,915** matching assignment rows and all 36 threshold-summary rows are byte-identical to the originals. The independent recovery audit rechecks same-event identity, unique reco/truth assignments, eligible-object denominators and every recorded deltaR from exact native Float32 directions. The largest distance residual is `1.3877787807814457e-17`; all **178,200** event/group/threshold graphs pass an independent cardinality-first minimum-cost DP oracle, with **zero skipped graphs**. C9 associations exactly equal their selected ALL_VALID same-event subset. Nominal thresholds remain photon deltaR < 0.2 and jet deltaR < 0.3, with existing threshold scans unchanged. Classification remains **PROVISIONAL_GEOMETRIC_MATCHING**, never origin purity, official efficiency or flavour validation.

Per-DSID native bindings, truth-object dumps, signed generator weights, normalization/SF diagnostic CSV/JSON and all cutflows are byte-identical before/after. Generator negative counts remain **14 / 15 / 0**; negative BTAG scalars remain **18 / 75 / 103** and are not applied. The two sign diagnostics remain distinct. Historical MC drivers did not persist event-level raw photon-flag values; that historical comparison is explicitly unavailable. Native flag bindings and new A/B optional-flag counts are preserved and independently checked. No truth origin/PDG ID/b-hadron information was invented, and no samples were combined into a background prediction.

## Toolchain, tests and reproduction

Actual ROOT is **6.40.04**, C++ **20**; compiler `/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`, version **15.3.0** (x86_64-conda-linux-gnu-c++ (conda-forge gcc 15.3.0-7) 15.3.0); CMake **4.4.4**. Compile commands for every target use the conda compiler and `-std=c++20`; inspected ROOT/libstdc++/libgcc linkage resolves inside the existing conda prefix. The long-double significand is 64 bits on this verified Linux build; no equivalence on double-only long-double platforms is assumed.

Fresh CTest is **18/18 PASS**. This includes Step1 3/3 and Phase1's historical combined baseline 5/5, 22 schema cases, 8 bounded transfer cases, native MC reader cases, selection/matching contracts, ten Phase4 driver cases and the new 15,361-case Cartesian suite. The existing synthetic RooFit/RooStats smoke test runs as a regression; no scientific DATA/MC fit is performed. Physical Gate C is additionally established by the actual source entry, never inferred from synthetic tests.

```bash
source /home/btu/miniforge3/etc/profile.d/conda.sh
conda activate atlas-hh-root
cd /mnt/c/HH
# Choose new build/output/evidence paths for a separate reproduction.
bash scripts/validate_phase4.sh /home/btu/build/atlas_phase4_recovery_repeat
python scripts/freeze_phase4_history.py .local/phase4_history_repeat.json
python scripts/run_phase4_numerical_recovery.py \
  --build-dir /home/btu/build/atlas_phase4_recovery_repeat \
  --output-dir outputs/phase4_recovery_repeat \
  --history .local/phase4_history_repeat.json
python scripts/audit_phase4_recovery_data.py \
  outputs/phase4_recovery_repeat/DATA93915 \
  outputs/phase4_recovery_repeat/independent_data.json
python scripts/audit_phase4_negative_data.py \
  outputs/phase4_recovery_repeat/DATA93915/regression \
  outputs/phase4_recovery_repeat/independent_negative.json
python scripts/audit_phase4_mc_histograms.py \
  outputs/phase4_recovery_repeat \
  outputs/phase4_recovery_repeat/independent_mc_histograms.json
```

The matching audit can be reproduced for all three DSIDs with separate new destinations:

```bash
for dsid in 343981 346214 423103; do
  python scripts/audit_phase4_recovery_matching.py \
    "outputs/phase4_v1/$dsid/reconstruction" \
    "outputs/phase4_recovery_repeat/$dsid/reconstruction" \
    "outputs/phase4_recovery_repeat/matching/$dsid" \
    --regression "outputs/phase4_recovery_repeat/$dsid/regression"
  python scripts/audit_phase4_recovery_matching.py \
    "outputs/phase4_v1/$dsid/reconstruction" \
    "outputs/phase4_recovery_repeat/$dsid/reconstruction" \
    "outputs/phase4_recovery_repeat/geometry/$dsid" \
    --regression "outputs/phase4_recovery_repeat/$dsid/regression" \
    --geometry-only
done
```

All nine exact executed physical pipeline commands and input/output/source/binary hashes are recorded in the gate JSON. The independent audit commands above reproduce the separately hashed audit evidence. Reproduction utilities refuse to overwrite outputs. Summarization likewise refuses to overwrite the committed V2 metadata; a separate verification checkout or separately named revision is required for new summary evidence.

## Preservation and figure policy

All **55 historical tracked scientific files**, **78 historical local output files** and **4 pinned inputs** (137 files) verify against the initial freeze. No previous verdict, cut definition, DATA result or original Phase4 evidence was replaced. Work remains on the existing Phase4 branch based on Phase3 and independent of plotting PR #6; no PR is merged or history rewritten.

Legacy DATA drivers generated eleven local PNG drafts for this rerun. Their status is **LOCAL_DRAFT**; they remain in the ignored new output directories for comparison. Numerical/CTest PASS is not visual QA or user figure approval. No new PDF/PNG/ROOT figure or data artifact is staged or pushed. Only explicit source, tests, reports and the requested numerical metadata are in the recovery payload. PR #7 remains Draft for independent approval.

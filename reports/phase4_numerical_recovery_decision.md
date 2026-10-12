# Phase 4 V2 numerical recovery decision

**FINAL_VERDICT = PASS_NUMERICAL_RECOVERY.** Gates A-J passed on the explicitly bounded pinned DATA/MC inputs. The original Phase4 verdict **PARTIAL_WITH_FAILED_NUMERICAL_GATE** and original physical Gate C **FAIL** remain preserved at commit `d823593b42889592897263819138170470f4dc47` and in their unchanged historical reports. V2 is a separately executed recovery verdict; it never changes that failed execution to PASS.

| Gate | Actual V2 result | Evidence scope |
| --- | --- | --- |
| A | PASS | Historical exact numerical failure reproduced from pinned source |
| B | PASS | Shared ROOT Cartesian implementation, independent physical diagnostics and stress checks |
| C | PASS | Exact entry5888 passes unchanged native-reference mass tolerance |
| D | PASS | All three physical MC strict closure tests execute successfully |
| E | PASS | Complete DATA cache/selection/bin/sign reconciliation with independent negative-tuple review |
| F | PASS | Complete MC event/cutflow/weights/native-histogram reconciliation |
| G | PASS | Same-event unique matching, independently computed denominators/geometry/optimality |
| H | PASS | Unchanged mass criterion, full event rows, no new suppression/correction |
| I | PASS | Historical files/input hashes and ancestry preserved |
| J | PASS | All existing and new CTest/physical independent regressions execute successfully |

The [physical regression report](phase4_data_mc_regression.md), [Cartesian review](phase4_cartesian_stability_review.md), [complete 92,795-row event diff](../metadata/phase4_numerical_diff.csv), [actual per-DSID cutflows](../metadata/phase4_updated_mc_cutflow.csv) and [gate/hash manifest](../metadata/phase4_numerical_gate_results.json) establish this decision. Source entry5888 now returns `123.949015149146717363` GeV versus independent native reference `123.949015149146711076` GeV, residual `6.28663787693994891015e-15` GeV at unchanged tolerance `1.12394901514914671104e-07` GeV.

The correction changes pair arithmetic in the shared DATA/MC kernel. All supplied inputs, per-object interpretation, energy, unit scale, directions, object ordering, selections, signed weights and statistical definitions remain preserved. No clamping, tolerance relaxation, offset, event suppression or MC-specific workaround was used. The failed double-Cartesian candidate remains recorded; final extended-precision ROOT Cartesian arithmetic passes 15,361 deterministic cases and the actual physical samples.

DATA63,095 and MC29,700 unique entries are accounted for. DATA's 37 negative supplied tuples remain invalid and are independently confirmed negative at high precision; their origin is UNKNOWN. Returned masses change at many low-order digits, recorded per event, but **zero event-validity, C0-C9 membership, histogram-bin or matching-assignment changes** occur in these runs. There is no material selection/bin migration requiring an additional scientific-category decision. Independent agent review and executed audit scripts establish numerical reconciliation; they do not constitute the human PR or final-figure approval.

**Separate scientific blockers remain:** applicable bounded-subset DATA luminosity; exact FEB2025 producer/skim/calibration; cross-section/filter/BR conventions; signed generated denominator/completeness; negative BTAG and other correction semantics; target-window prompt continuum and complete fake/background coverage; validated HH input, b tagging, acceptance/systematics and a statistical model. See the [documentation-first weight/background update](phase4_weight_readiness_update.md). Absolute MC/DATA normalization, correction application and complete background prediction remain **BLOCKED**. Matching remains **PROVISIONAL_GEOMETRIC_MATCHING**, and kinematic units retain **PROVISIONAL** provenance. A numerical PASS establishes neither HH sensitivity nor an official truth efficiency/purity.

The original 137-file preservation snapshot re-verifies. The fresh Linux toolchain is ROOT6.40.04 / C++20 / conda GNU15.3.0, CMake4.4.4; CTest18/18 PASS. Every numerical gate is PASS, none FAIL/BLOCKED/UNKNOWN in the executed scope. Generalization to other files, untested extreme conditioning or platforms with double-precision long double is not asserted.

Validated source/tests/reports and requested text metadata are prepared as additive commits on `codex/phase4-mc-truth-validation`. The branch retains Phase3 ancestry and stays independent of plotting PR #6. Every staged path and every outgoing commit version must pass the no-unapproved-PDF/PNG payload inspection before push. Eleven generated local PNGs remain **LOCAL_DRAFT**, with no approval or upload. PR #7 stays **OPEN / DRAFT** for independent numerical/scientific approval; no PR #4/#5/#6/#7 is merged.

The next recommended step is independent review of PR #7 and the recorded numerical evidence, followed by provenance and normalization-readiness resolution or separately bounded appropriate continuum-input feasibility. No physics fit, new normalized prediction or publication figure is authorized by this numerical decision.

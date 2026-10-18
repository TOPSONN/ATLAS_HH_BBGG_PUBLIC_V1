# Phase7I actual nonphysical numerical validation

The original, diagnostic-only and corrected guard were compiled and actually executed at both-O0 and-O2 using the existing compiler. Forty-seven deterministic cases per optimization cover thirteen corrected-success cases and all five fatal branch IDs. Each binary links only exact guard/statistics/include/scalar-math/RNG projections; symbol scans found no HH SMATRIX, MadLoop, genuine sampler, integrand, unweighter or writer entry points. The four RNG projections are real frozen RANMAR/rmarin/ran1/xran1 implementations, not fabricated random streams. [O0 evidence](phase7i_guard_correction_evidence/method_O0.json), [O2 evidence](phase7i_guard_correction_evidence/method_O2.json), [fixture identities](../simulation/hh_signal/final_closure/guard_correction/fixtures/manifest.json).

## Three-version matrix

| Cases | Covered behavior | Corrected outcome |
| --- | --- | --- |
|0,46|Valid native/model-equal q250/q125|Success|
|4,14,28,32-34|Model reference91.188 at q125/250/173/1000/6500, or another positive artificial reference|Success; original/diagnostic reject model/q inequality|
|5,23,27,40|Wrong/zero native scale; multiple finite failures; mismatch beyond tolerance|Renormalization STOP92; old guard ignored native scale|
|6,7,21,44|Wrong beam1/beam2 QF², negative finite QF², beyond-tolerance residual|Factorization STOP92|
|10-12,18-20,24|Both QF entries: NaN/+Inf/-Inf; nonfinite QF plus finite scale mismatch|NONFINITE STOP90 before scale ratios|
|13|Both PDFs exactly zero|Success|
|1-3,22|Zero invariant or negative PDFs, including multiple finite failures|Q_OR_PDF STOP92|
|15-17,25,29-31,37,41-42|Nonfinite incoming momentum/native scale/model reference/PDF/G|NONFINITE STOP90; original NaN masking and ignored native-scale cases reproduced|
|8,9|Zero derived alpha, wrong running alpha|Original alpha STOP92 identifiers|
|26,38|Nonpositive model reduction reference, also with a zero PDF|Renormalization STOP92; scalar diagnostic distinguishes reference from physical ratio|
|35|Most asymmetric13TeV-domain beam pair in this fixture at target q125|Success|
|36|Extreme outside-beam-domain boost with 1e12 GeV input energy|Fail closed at Q_OR_PDF; computed binary64 invariant collapses to zero|
|39,43,45|Within-tolerance native/QF residuals; negative G with unchanged positive G²|Original successful behavior retained|

Case35 computes q=124.99999999999255 GeV for the nominal125 target, a relative difference about5.96e-14; native-scale and guard arithmetic agree. This roundoff-level undershoot is not a new subthreshold physical process. Case36 is outside the frozen beam-energy domain and cannot be used to claim robust arbitrary-boost precision. No tolerance or invariant convention was changed to make it pass.

Each evidence row retains exact scalar representations, original/diagnostic/corrected exits, first diagnostics and input fixture ID. No physical momentum array or event record is exported. The maximum measured failure record was 291 bytes, below the768-byte strict parser cap and existing supervisor cap. Seven corrected native fixture failures per optimization were exercised through the unchanged Landlock/process-group supervisor; five IDs and STOP90 were preserved in partial receipts, with empty output files/scratch and discarded raw streams. Direct tests verify STOP92 separately from the possible supervisor-kill exit race.

## Noninterference and independent arithmetic

For every corrected-success case, the guard and no-guard control produce bitwise-identical outputs. The comparison includes actual RANMAR common-block state immediately across the call, the next64 RANMAR/ran1/xran1 draws after7 initial draws per routine, unchanged G/model/native-scale/QF/PDF/input arrays and observer state. Originally successful cases also match all three implementations. Artificial64-step candidate/weight/squared-weight/grid/mean/variance bookkeeping matches the control and independent 70-digit Decimal arithmetic. These are explicitly method fixtures, not a native integrator's measured cross section/error.

Real candidate selection, grid update, stopping and estimator structure are protected by exact frozen Source/dsample, unwgt, library and existing overlay hashes: the only proposed scientific arithmetic change is the guard predicate/finite coverage. The builder diff leaves the integrator and its estimator code unchanged. Actual complete native-integrator equivalence remains **NOT_EVALUATED_UNTIL_AUTHORIZED**.

The exact native ALPHAS source was tested at 17 scales, including125,173,250,1000,6500 and both sides of1.42/4.7/173. Independent reciprocal-alpha matching agrees within6.55e-15 relative; the physical-range fixed-nf5 residual is below 1.34e-15. Below4.7, the native helper changes nf; fixed nf5 is not asserted there. The441 earlier deterministic scale-expression probes were rerun as part of both method passes. A separate artificial Laurent-coefficient identity checks zero-pole reference cancellation and detects a nonzero-pole counterexample; it evaluates no actual loop amplitude or integral.

The [regression receipt](phase7i_guard_correction_evidence/regression.json) records the completed broader nonphysical suite and seven read-only existing validator commands. Those portable validators preserve their historical interpretation; no fresh ROOT, shower, detector or corrected-SM1000 production is implied. Hosted final-head CI and remote-byte readback are post-publication observations reported on PR24 and in the local final delivery receipt.

The completed local suite passed 155 tests, including the 12 new correction tests. Full [historical preservation](phase7i_guard_correction_evidence/preservation.json) uses strict inventory hashes for stopped/campaign data and preserves existing public CSV CRLF bytes while separately verifying their exact LF-only Git projection; historical files were not normalized or rewritten.

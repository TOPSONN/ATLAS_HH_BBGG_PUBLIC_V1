# Phase 5 shape comparison infrastructure

Date: **2026-10-12**. **SYNTHETIC_ENGINEERING_PASS; physical DATA/MC shape comparison NOT EXECUTED.** Neither a native collision tree nor a physical histogram was read by these tests. Historical/baseline source code, ROOT input bytes, Phase 3 cuts, Phase 4 reconstruction, historical histograms and scientific evidence are preserved; this task adds the gated normalization module and its tests. No PDF/PNG, fit or absolute prediction was generated.

The ROOT/C++20 module is [AtlasNormalization.h](../include/AtlasNormalization.h) / [Normalization.cxx](../src/Normalization.cxx); its conditional generator-level contract is documented in [phase5_normalization_contract.md](phase5_normalization_contract.md). It uses the existing ROOT **6.40.04** and conda GNU **15.3.0**. No additional package was installed.

## Explicit modes and preconditions

`ShapeContract` defaults to physical scope with physical application **disabled**. A synthetic fixture explicitly selects `Scope::Synthetic`, which stays in the output. The two modes are:

| Mode | Permitted interpretation / preconditions |
|---|---|
| `RawUnweightedDiagnostic` | Technical unit-area count comparison only. Selected bins must be finite nonnegative integer counts with variance equal to those counts. This cannot establish physical background agreement. |
| `GeneratorWeightedShape` | Signed selected-bin shape, conditional on explicitly Verified nominal generator-weight semantics. Requires ROOT Sumw2 and a complete per-bin signed event ledger, including flow slots. No SF is applied. |

Both modes require explicit selection, variable and unit IDs, Verified histogram semantics, and an explicit independent selected-bin statistical model. Metadata declarations do not authenticate a real sample: actual provenance and compatibility must be reviewed first. UNKNOWN weight semantics, missing Sumw2/ledger, disagreement between stored bin moments and ledger, unspecified bin covariance model or disabled physical application throw. `require_compatible_shapes` checks matching technical selection/variable/unit identities, selected edges, widths, flow policy, scope and mode. Passing those structural checks does not establish compatible generator filters, trigger/calibration conditions or physical background coverage.

Each nominal histogram is normalized **separately**. Combining source samples needs the separate explicit pairwise disjointness contract; shapes are not added by process labels or assumed mass-slice compatibility. No mixture is performed here.

## Signed area, variance and effective statistics

For selected bin yields x_i and stored Q_i=sum(w²), the signed denominator is

\[
 S=\sum_{i\in\mathrm{selected}}x_i,\qquad f_i=x_i/S.
\]

Negative bin contents remain negative before normalization; no clipping or absolute value is used. If S is negative, algebraically all ratios use that same signed denominator. This signed unit-area object is not generally a nonnegative probability density. Within-bin positive/negative cancellation remains visible in the event ledger's A=sum|w|; `abs(bin content)` is not substituted for A. The numerical conditioning guard rejects zero S or |S|/A <= 1e-12. This guard is not a guarantee of adequate effective statistics or a statistically reliable ratio approximation.

The result records stored source x_i/Q_i, selected bin indices and edges, per-bin widths, the actual stored-histogram denominator, selected event-ledger S/Q/A and entry-sign counts where known, Neff=S²/Q, normalized values, errors and the full covariance. The ledger's compensated sum and stored ROOT sum can differ by serialization arithmetic roundoff; each is explicitly retained. The implementation uses the stored histogram denominator for its stored-bin shape and does not repair either source. Their comparison bound is `64*double_epsilon*max(|stored|,|ledger|,relevant_absolute_or_squared_sum)` with exact equality when that local scale is zero. There is no unit-scale absolute floor that could admit contradictory tiny-weight moments. Each original moment source is checked separately; conditioning the stored denominator against the independently retained event-ledger A does not construct a fictitious mixed-origin S/Q/A aggregate. This is a new serialization check, not a change to the historical pair-mass tolerance.

For variable-width regular bins of width Δ_i, unit-area density is d_i=f_i/Δ_i. Its area is sum(d_i Δ_i)=1, not sum(d_i)=1. Bin widths must be finite and positive. Explicit first/last regular-bin selection controls the denominator and covariance. `FlowPolicy::Exclude` omits flows from normalization; `Include` includes the original underflow and overflow as discrete categories along with the selected regular bins. Flow contents/errors are never modified. **Density with included unbounded flows is rejected** because no finite physical flow width is defined. These choices are returned explicitly, so a consumer cannot mistake a regular-bin area for a flow-inclusive area.

## Normalization covariance

Conditional on fixed nominal weights and independent selected-bin yields with covariance diag(Q), the first-order Jacobian and full covariance are

\[
 J_{ik}={\delta_{ik}-x_i/S\over S},\qquad
 C_{ij}=\sum_k J_{ik}Q_kJ_{jk}.
\]

The same expression can independently be expanded as

\[
 C_{ij}={\delta_{ij}Q_i\over S^2}
       -{x_iQ_j+x_jQ_i\over S^3}
       +{x_ix_j\sum_kQ_k\over S^4}.
\]

Per-bin errors are sqrt(C_ii); signed x_i do not produce negative diagonal variance. Density rescales C_ij by 1/(Δ_i Δ_j). Fraction covariance rows sum to zero; density covariance has the bin-width vector as its null direction. Thus errors are correlated after normalization and must not be treated as independent ROOT errors divided by S. PSD follows analytically from J diag(Q>=0) J^T; executed tests additionally inspect independent deterministic quadratic forms.

These are **first-order statistical** uncertainties conditional on fixed weights and a valid independent-bin model, not finite-sample exact intervals. They omit generator/cross-section/luminosity/SF/selection/systematic nuisances and cross-histogram dependence. ROOT Sumw2 alone does not supply covariance for multiple correlated objects from the same event, repeated or shared events, nuisance-weight variations, or source-sample overlap. Such a source must not declare the required independent-bin model without evidence; this implementation does not infer or invent its covariance. Small Neff or substantial denominator fluctuations require further statistical review even when the arithmetic guard passes. No DATA/MC chi-square or ratio significance is computed.

## Executed independent synthetic checks

[test_shape_comparison.cxx](../tests/test_shape_comparison.cxx) executed **81,973 assertions across 519 analytical fixtures, with 33,216 deterministic PSD directions: PASS**. Seed **20261012**. The test compares the implementation's Jacobian loops with the independently expanded formula, checks symmetry, area, covariance null directions and errors, and compares each input histogram's bins, errors, edges, entries, moments and flows before/after.

| Fixture | Independently known result |
|---|---|
| Counts (2,6) | S=8, Neff=8; fractions (0.25,0.75); variances 0.0234375 and covariance -0.0234375 |
| Same counts with widths (1,2) | Densities (0.25,0.375); area=1; covariance -0.01171875 |
| Signed bin weights (3,-1), (-1), (3) | x=(2,-1,3), Q=(10,1,9), S=4, A=8, Neff=0.8; negative fraction -0.25 preserved; first variance 0.3125 and first/second covariance -0.03125 |
| Selected bins 2–3 | Signed denominator 2 and Q=10; excluded bin not included in normalization |
| Selected bins plus flow weights 2 and -0.5 | Signed denominator 3.5 and Q=14.25; indices (0,2,3,4) preserved; included-flow density rejected |
| Tiny weights 1e-100 and 2e-100, represented as the actual double weights supplied to ROOT | Valid fractions 1/3 and 2/3 with finite covariance; contradictory signed and squared-weight ledgers are independently rejected |
| 512 deterministic signed variable-width fixtures | Positive and negative signed totals, within-bin cancellation, expanded covariance, null directions, PSD and input identity all checked |

Rejection cases cover exact/near-zero signed denominators, missing event ledger/Sumw2, UNKNOWN nominal or covariance semantics, inconsistent stored/ledger Q, negative/weighted bins falsely requested as raw counts, default physical mode, incompatible selections/variables/scopes and shifted equal-width bin edges. Negative bins are never removed to pass a test. PSD directional tolerances are documented arithmetic checks (`128*long_double_epsilon*max(sum_abs_quadratic_terms,1)`), and independent analytical comparisons use a named `2e-14` relative/absolute fixture bound. They do not alter any physics/reconstruction threshold or validate a future unrelated covariance.

The final standalone compiler commands, completed exits, test outputs, ROOT/compiler versions and hashes are in `.local/build_phase5_normalization_agent/execution_reviewed.json`. The final focused executable is `.local/build_phase5_normalization_agent/test_shape_comparison_reviewed`. An intermediate guard run failed on an unnecessarily mixed ROOT-double/event-ledger moment check; its original output is preserved in `execution_guarded_failed.json`. The final implementation conditions the stored denominator separately after validating the ledger, and the valid tiny-weight fixture passes without relaxing the local comparison guard or changing either source. Earlier focused binaries and `execution.json` are retained. Integrated CTest results must be recorded separately in the Phase 5 quality gates; this report does not assume them.

| Executed source / binary | SHA-256 |
|---|---|
| `tests/test_shape_comparison.cxx` | `1d04982198b79fd08883b3d22a36dc9b2423eb80bfe048f5332504140bfb69fb` |
| Focused reviewed shape executable | `b8886ac0fea76fa2bd85237bc8b3cbe8b646600a940060e69f42c7094135ab8f` |

## Current physical limitations

The preserved [Phase 4 readiness assessment](phase4_weight_readiness_update.md), the separate Phase 5 source/luminosity audits and the Phase 5 decision must establish actual physical feasibility. Relevant outstanding issues include the generated continuum mass-filter coverage and reconstructed migration near edges; different/unresolved DATA/MC trigger and release/skim conditions; unknown nominal-weight and correction applicability; incomplete continuum/fake/single-H/background mixture and overlap disposition; bounded selected event populations and effective statistics. A generated 100–160 GeV filter cannot be assumed to describe a full reconstructed continuum outside that generated support or extrapolated across its edges.

The historical DATA subset [100,63195) is not automatically luminosity complete. No period exposure or event-count fraction is used here. The existing Phase 3 cuts are preserved, including their 105–160 GeV mass window and optional ID/iso diagnostics; this new code does not reinterpret them as an official ATLAS event selection. Engineering compatibility or synthetic covariance PASS does not make a physical background comparison, absolute prediction, CR closure, official HH result or signal sensitivity PASS. Current deliverable: reusable gated code and synthetic evidence only.

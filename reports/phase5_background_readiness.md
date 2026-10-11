# Phase 5 background readiness

**INCLUSIVE_DIPHOTON_JETS_METHOD_STUDY = BLOCKED_PENDING_NUMERICAL_RECOVERY;
CALIBRATED_BACKGROUND_PREDICTION = BLOCKED;
HH_LIKE_ANALYSIS = BLOCKED.** Phase 5 development is not started by this report.

Actual Phase 4 main runs processed 9,900 entries per sample, **29,700 total**,
in [100,10000). The ggF sample 343981 fails one of 12,004 original Cartesian
pair-mass closure comparisons at entry 5888: **1.9124535637071727e-7 GeV** exceeds
the unchanged pair tolerance **1.1239490151491467e-7 GeV**. That event has no
selected C9 category; excluding it from C9 does not clear the all-valid-pair
gate. VBF 346214 passes 12,197 comparisons and gammajet 423103 passes 13,220,
but overall numerical validation remains **FAIL**. Fresh CTest **17/17 PASS**
is distinct regression evidence. See [MC reconstruction](phase4_mc_reconstruction.md),
[numerical failure diagnosis](phase4_numerical_failure.md), and the
[quality gates](../metadata/phase4_quality_gates.json). Any numerical change
requires a separate shared-module task and fresh verification; no tolerance,
event or historical result is altered here.

The bounded Phase 4 source work selects single-H ggF/VBF diphoton examples and
one gamma+jet photon-pT slice. That could support conditional method/closure
exercises after numerical recovery
within the actual inspected entries and documented study selections. It does
not supply a complete continuum/fake model, luminosity-scaled prediction or HH
signal model. Refer to the reproducible
[373-DSID manifest](../metadata/phase4_mc_sample_manifest.csv) and
[source audit](phase4_mc_source_audit.md); the authoritative public release is
[CERN record 93922](https://opendata.cern.ch/record/93922).

## Readiness by component

| Component | Status | Requirement / scope |
| --- | --- | --- |
| Inclusive diphoton + leading-jet reconstructed observables | BLOCKED_PENDING_NUMERICAL_RECOVERY | Original 343981 pair-mass gate FAIL; preserve Phase 2/3 PROVISIONAL units, raw photon flags and inclusive m_jj semantics |
| Prompt continuum around 105–160 GeV | PARTIAL_SOURCE_COVERAGE | Official 302521 generated 100–160 and 364352 generated 90–175 are relevant; neither is in the selected inspected batch. 302521 fits a fresh 128 MiB budget but not this remaining allocation; 364352 exceeds the full ceiling |
| Single-H resonance examples | AVAILABLE_FOR_BOUNDED_STUDY | 343981 ggF and 346214 VBF are single H→γγ, not HH, and are not a full single-H prediction |
| Gamma+jet / jetjet fake contribution | BLOCKED_AS_PREDICTION | 423103 samples a generator photon 70–140 GeV slice; it supplies neither all slices nor a validated jet-to-photon misidentification transfer factor |
| Photon origin / prompt purity | BLOCKED | Supplied truth directions allow scoped geometrical association; promptness/ancestry construction is unverified |
| b tagging / flavour-dependent background | BLOCKED | Exact tagger/WP/calibration/truth flavour unresolved; see [b-tag audit](phase4_btag_feasibility.md) |
| Absolute MC normalization / data-MC comparison | BLOCKED | Exact signed generated denominator, decay/filter convention, selection-correction applicability and data/MC compatibility unverified |
| Background functional fit, selection and bias closure | NOT_STARTED | Requires approved blinded regions, candidate models, validation protocol and appropriate samples/statistics |
| HH signal efficiency or HH category | BLOCKED_INPUT | No suitable explicitly verified HH→bbγγ signal sample in the scoped release audit |
| Likelihood, significance, limit or coupling result | BLOCKED | No validated signal/background model, calibrated uncertainty model or suitable statistical inputs |

## Sidebands and model validation requirements

An inclusive data study could separately propose a blinded signal-region and
sideband definition inside the physically validated mass range; no blind window
or fit is chosen or executed here. Before observing a candidate signal region,
the protocol must freeze the region boundaries, event/object selection and the
admissible background families. It must define closure and bias tests on
independent control/validation inputs, fit-range sensitivity, sufficient
statistics and the treatment of single-H contamination. A smooth-looking
histogram alone cannot establish a background family or its uncertainty.

For a claimed fake prediction, ID/isolation control-region transfer factors need
verified flag semantics, contamination handling and independent closure. The
provided skim and one generator photon slice do not establish these controls.
For luminosity-scaled data/MC comparisons, use a verified signed pre-skim sum,
cross-section/filter/k-factor and decay convention; retain negative weights and
do not sum alternative generators or overlapping samples as distinct processes.
No MCweight, scale factor or luminosity is automatically applied in this phase.

The first-100 native probes already show a 423103 filteff difference
(0.000039 in the file versus 0.0000393 in the later table), rounded H generated
sum fields, a −1 `ScaleFactor_BTAG` value in gammajet and zero pileup SFs in the
H probes. Exact conventions/validity remain unresolved. These observations
strengthen the absolute-normalization/correction blocker; they cannot be
repaired by convenience or interpreted as generator-weight sign behavior.
Truth-jet mass has small negative native values with UNKNOWN semantics, while
direction-only geometrical checks can proceed separately under PROVISIONAL units.
The [source audit](phase4_mc_source_audit.md) preserves the values and bounded
scope. The actual larger [100,10000) summaries preserve negative truth masses
1397/2511/731 and negative BTAG SF scalars 18/75/103 for 343981/346214/423103.
Generator-weight negatives are separately 14/15/0. Their partial raw weight sums
are diagnostic only; no weight/SF is applied or converted into a full generated
denominator. Those larger-stage observations remain distinct from the first-100
probes and cannot establish complete-release provenance or clear the failed
numerical gate. Direction-only association checks passing within PROVISIONAL
geometry do not establish prompt purity, b flavour or official efficiency.

The official
[educational metadata guidance](https://opendata.atlas.cern/docs/data/for_education/13TeV25_metadata)
requires normalization to the full unskimmed sample. The official
[research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp)
also constrain object reconstruction and availability of signal/systematic
inputs. Source snapshots and the exact later-producer discrepancies are
preserved in the preceding audit; documentation access failures do not prove
that a public resource is absent.

The next step is a separately approved shared-module numerical recovery proposal
that preserves the original failed evidence and validates the same raw inputs
with fresh DATA/MC regressions. A bounded target-window continuum inspection or
richer research-input adapter/provenance study and inclusive sideband/control-
region proposal remain later conditional work. Passing C++ tests or changing
plotting style cannot resolve any of
these physical-input or calibration blockers. No HH fit, discovery, significance,
cross-section limit, coupling constraint or exact publication reproduction is
authorized or supported by this readiness assessment.

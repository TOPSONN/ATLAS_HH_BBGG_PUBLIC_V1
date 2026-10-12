# Phase 5B DATA-only sideband diagnostics

**DATA_SIDEBAND_DIAGNOSTIC_VALIDITY = PASS for this bounded descriptive
cache study. A/B mass independence is not established. Physical transfer-factor
prediction, background dominance, single-H contamination and physical closure
remain UNKNOWN or BLOCKED.** No native DATA ROOT file was reopened, no MC
distribution was invented, and no fit, correction weight, normalization or
figure was produced. The historical DATA and central mass window have already
been viewed; this is not a blinded analysis.

This additive study follows Phase 5 commit
`e131de92897b75185981ec2c5ce1c722e9ada6c3`. It preserves the Phase 4 numerical
recovery cache and the exact `study-preselection-v1` selection. ROOT 6.40.04 /
C++20 provides the existing selection and histogram implementation. The
source, tests and aggregate CSV are new; per-event diagnostics remain under
ignored local outputs.

## Input, selection and actual execution

The input is the preserved DATA Phase 2 cache from record 93915:

```text
outputs/phase4_numerical_v2_20261012/DATA93915/phase2/events.csv
SHA-256 c242e256d76d6832031b2e4b2dfeeb342b5b05885c2a6bdf53d2d5eab71201c7
exact range [100,63195), 63095 entries
metadata/phase3_selection_config.ini
SHA-256 77d57cd6fa204aad5a24031ac925c4e20e121b8aee35148cc29b522b39cf5751
```

These are hashes of the derived cache and selection bytes, not a fresh native
ROOT-file identity check. Native provenance and numerical recovery remain in
the preserved [Phase 4 recovery report](phase4_data_mc_regression.md).
Units retain **PROVISIONAL** status. Cache validity flags, leading-object
ordering and masses are consumed without reconstruction or reinterpretation.

The parser requires the exact DATA28 header, complete contiguous entry range,
unique run/event identities, strict booleans/native count limits, finite
present scalars and the published validity/multiplicity missing-field rules.
It rejects mismatched cached photon deltaEta and eta differences. Input and
selection hashes must remain identical before and after parsing. Invalid
input is rejected before output-directory creation; existing outputs are
never replaced.

The study invokes the existing `selection::evaluate` and
`regions::classify`. It first uses C5, then the individual unchanged jet
predicates, so the population before the C6 mass cut is available. It does not
try to recover outside-window events from an already C9-filtered input.
There are no new ID/isolation, trigger or b-tag requirements; jets remain
inclusive jets. The current study-defined photon/jet cuts are documented in
the [Phase 5 region assessment](phase5_control_region_feasibility.md).

The actual app exited **0** on 2026-10-12:

| Diagnostic population | Raw events |
| --- | ---: |
| Complete cache | 63,095 |
| Cache valid | 63,058 |
| C5 | 51,136 |
| C5 plus individual jet predicates | 9,037 |
| C9, unchanged baseline | **1,689** |
| C5 plus jets outside [105,160] | 7,348 |
| Sidebands with C5 plus jets | **1,374** |

The 37 invalid cache events remain excluded by the existing validity flag;
this study does not repair or relabel them. C9 is checked as a historical
regression total. The real central-window population is not used to compute
correlations, boundary sensitivity, pseudo-window counts or holdout occupancy.

## Sideband distributions, balance and counting precision

Sidebands are **[105,120) union [130,160]** in supplied reconstructed m_gg.
The A split is **abs(deltaEta_gg)<1**; B is **>=1**. This partitions the
same sideband events exactly once.

| Partition | Lower sideband, 15 GeV | Upper sideband, 30 GeV | Total | Lower counts/GeV | Upper counts/GeV |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 217 | 226 | **443** | 14.47 | 7.53 |
| B | 390 | 541 | **931** | 26.00 | 18.03 |
| A+B | 607 | 767 | **1,374** | 40.47 | 25.57 |

Different sideband widths make equal raw counts an inappropriate expectation.
The upper/lower density ratios are 0.52074 for A and 0.69359 for B. They
describe this selected sample; neither ratio is a physical transfer factor,
acceptance correction or fitted continuum slope. Selection, triggers,
composition and detector response have not been separated.

The sideband A fraction is 443/1374 = **32.24%**, with a **95% Wilson
binomial counting interval [29.82%,34.76%]**. Intervals quantify counting
precision conditional on the selected events; they omit selection, trigger,
calibration, composition and model uncertainties. The A fraction is 35.75%
in the lower sideband and 29.47% in the upper sideband. This observed variation
is not an independence or significance test.

Fixed 5 GeV bins expose the actual statistical support:

| Supplied m_gg interval, GeV | A | B | A fraction | 95% Wilson interval |
| --- | ---: | ---: | ---: | --- |
| [105,110) | 74 | 121 | 37.95% | 31.43%-44.93% |
| [110,115) | 78 | 146 | 34.82% | 28.89%-41.27% |
| [115,120) | 65 | 123 | 34.57% | 28.15%-41.62% |
| [130,135) | 45 | 105 | 30.00% | 23.24%-37.76% |
| [135,140) | 49 | 120 | 28.99% | 22.68%-36.24% |
| [140,145) | 32 | 87 | 26.89% | 19.74%-35.49% |
| [145,150) | 42 | 75 | 35.90% | 27.78%-44.91% |
| [150,155) | 32 | 83 | 27.83% | 20.45%-36.63% |
| [155,160] | 26 | 71 | 26.80% | 19.00%-36.38% |

The A cells contain 26-78 events; further splitting reduces that support.
These coarse-bin counts do not guarantee adequate precision for a fitted
transfer model. The central [120,130) bins are intentionally excluded and
their empty sideband-histogram bins must not be read as zero observed DATA.
ROOT's histogram upper edge is exclusive: an exact160 event would enter
overflow, while the semantic final diagnostic interval includes160. Both
flows are exported explicitly; the actual sample has no such endpoint event.

## Mass versus deltaEta

Pearson correlation uses centered long-double accumulation; Spearman uses
average ranks for exact ties. Both are descriptive coefficients, without
p-values, an independence test or a claim about a physical background.
The disconnected lower/upper support can affect a pooled coefficient, so
each sideband and each A/B partition is also reported separately.

| Population | N | Pearson m_gg vs signed deltaEta | Pearson m_gg vs abs(deltaEta) | Spearman m_gg vs abs(deltaEta) |
| --- | ---: | ---: | ---: | ---: |
| All sidebands | 1,374 | -0.01349 | **0.19574** | **0.18901** |
| Lower sideband | 607 | 0.04088 | 0.08678 | 0.08463 |
| Upper sideband | 767 | -0.03699 | 0.10784 | 0.10763 |
| A, both sidebands | 443 | -0.00826 | 0.04831 | 0.06066 |
| B, both sidebands | 931 | -0.01233 | **0.30425** | **0.28616** |

A small signed-deltaEta coefficient does not establish independence for the
**absolute**-deltaEta split. The observed absolute-deltaEta association and
mass-dependent A fractions prevent treating B as a validated mass-independent
proxy for A. Truncation into A/B also changes each conditional distribution;
the smaller A coefficient is not proof that an A transfer model closes.
All 36 signed/absolute Pearson/Spearman cell results, including individual
A/B lower/upper sidebands, are retained in the aggregate CSV.

## Fixed boundary sensitivity

The app specifies the following alternatives in source before reading the
physical cache. It does not optimize a cut, score a central-window signal, or
select a preferred boundary from these results.

| abs(deltaEta) split | Sideband A | Sideband B |
| --- | ---: | ---: |
| <0.8 / >=0.8 | 336 | 1,038 |
| **<1.0 / >=1.0 baseline** | **443** | **931** |
| <1.2 / >=1.2 | 530 | 844 |

At the unchanged split1, fixed outer-support trims leave A fractions of
31.30% for [110,160], 32.65% for [105,155], and 31.70% for [110,155], always
excluding [120,130). These trim intervals have inclusive outer endpoints.
The aggregate CSV contains all12 combinations of the three eta thresholds
and four fixed supports. They are overlapping sensitivity probes and must
not be combined as independent measurements. The central boundaries remain
120 and130 throughout.

## Holdout and pseudo-window assessment

A/B disjointness alone does not test transfer into A when mass and the split
variable are associated. A more relevant future test would withhold a fixed
mass subwindow **inside A**, freeze its prediction rule using distinct
calibration events, and test the withheld A population. This requires an
explicitly specified model, contamination treatment and covariance. No such
physical prediction or closure is executed or authorized here.

Two fixed half-open sideband pseudo-windows have these occupancies:

| Candidate pseudo-window | A | B |
| --- | ---: | ---: |
| [110,115) | 78 | 146 |
| [140,145) | 32 | 87 |

These are design-support counts, not successful closure tests. The upper
candidate offers fewer A events, and holding out additional identities will
further reduce counting precision. Neither pseudo-window certifies transfer
through the real central mass window, different background composition or
the near160 generation boundary of a separate MC sample.

A fixed prospective identity partition uses the low bit of FNV1a64 over
ASCII `DATA:run:event`. Fold0/fold1 occupancy is:

| Cell | Fold0 | Fold1 |
| --- | ---: | ---: |
| Lower A | 108 | 109 |
| Upper A | 123 | 103 |
| Lower B | 196 | 194 |
| Upper B | 267 | 274 |

This rule provides disjoint identities and reproducible occupancy; it is not
a randomized-design or independence proof. Run/event numbering may encode
conditions or correlations. A future validation protocol must freeze a split
and model before fitting, audit run/trigger conditions and exclude all held-out
identities from calibration. Since the historical DATA have already been
examined, these candidate folds remain retrospective design diagnostics and
cannot establish blinding or an untouched validation sample.

Single-H contamination and other physical composition remain **UNKNOWN**.
The DATA cache does not label origins, inclusive jets are not established
b-jets, and the unvalidated MC normalization/SF/exposure ingredients cannot
quantify leakage or a background-dominated sideband. No sideband count here
repairs those missing ingredients.

## Executed checks and reproducible artifacts

Focused ROOT/C++20 compilation with `-Wall -Wextra -Wpedantic -Werror` and
**14/14 Python tests PASS** preceded the final physical cache run. The suite executed
**53 synthetic cache invocations:21 accepted and32 rejected**. Coverage
includes exact mass/eta endpoints, independent Decimal Pearson and tied-rank
Spearman, independent Wilson intervals, empty/constant undefined values,
unchanged C9 and individual jet predicates, central-population modifications
that cannot alter diagnostic results, raw ROOT histogram flows/Sumw2,
deterministic folds, unequal sideband widths, SHA-256 across block sizes and
CRLF, strict malformed inputs/ranges, a sparse config exceeding the64MiB
hash-allocation bound, and existing-output preservation.

A separate Python cache check independently applied the published selection,
joined all1,374 sideband identities and raw values, reproduced C9=1,689,
verified histogram totals/flows and all36 correlation coefficients with
70-digit Decimal arithmetic. The maximum residual at serialized double
precision was **0**; this is numerical agreement, not physical closure.
The fresh integrated regression suite is a separate parent-agent gate; this
report does not substitute focused tests for it.

Run after activating the existing environment:

```bash
phase5b_data_sidebands \
  outputs/phase4_numerical_v2_20261012/DATA93915/phase2/events.csv \
  metadata/phase3_selection_config.ini outputs/NEW_DATA_SIDEBANDS \
  100 63195 PROVISIONAL
```

The executable must be built from the new target on the Phase5 development
branch. The original cache and local receipts are required for reproduction.
Use a new output directory each time. Actual local outputs are
`outputs/phase5b_v1/data_sidebands_final/`; the first local run under
`outputs/phase5b_v1/data_sidebands/` remains preserved. All four output files
are SHA-256-identical after the independently reviewed hash-allocation guard
was added and the final cache run executed. The published aggregate
[phase5b_region_diagnostics.csv](../metadata/phase5b_region_diagnostics.csv)
is an exact byte copy of the executed113-row diagnostic CSV, with no event
identities. Its fields record raw counts, denominators, values, Wilson bounds,
undefined states, fixed boundaries and the descriptive-only scope.

| Executed artifact | SHA-256 |
| --- | --- |
| Aggregate diagnostic CSV | `b9f9f9ad6a50f4a773fe42dcea984bf323e73e0e18b8ffcc97a4425234ec4eb7` |
| Local sideband event ledger | `1a37cdc169d74710fe10c6d03c4269ae9058230ca7eaf2444628eae2d45b6b4f` |
| Local ROOT histogram CSV | `30eb5954516f738e16f535d398e62a03bb832b41ae8b0a2d1e0c0880450cb485` |
| Local summary JSON | `4b12e7f040fa1621b81c639663329f1e0944cc09bd504b7003d16aa53b03555a` |
| Focused executed binary | `a094e6a53580a985ecc795be103faee0cb18c1de411a50629dfefaed57dee297` |
| Actual run log | `3f54a6a2599193e2faeec015f5e113298719424085bc4f26874ac6e3ce7d31af` |
| Final independent audit JSON | `83c39f33a534a676292267d6ca9f7c78811b10b7f5c80622d56325b0c430e5bf` |

The run log, focused log and independent audit reside in
`.local/build_phase5b_sidebands_agent/` (final run log:
`actual_final_run.log`; audit: `actual_final_independent_audit.json`). Only source/tests/report/aggregate
evidence are prepared for the parent workflow; no Git operation was performed
by this subtask. There are **no new PDF/PNG figures** requiring approval.
The honest next scientific step is a frozen sideband validation design and
independently established physical inputs, not a current physical TF or HH fit.

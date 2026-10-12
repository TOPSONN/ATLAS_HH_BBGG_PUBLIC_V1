# Phase 5C: fixed-protocol DATA sideband dependence

**The bounded DATA diagnostic and separated-fold procedure executed successfully.
A stable physical A/B mass-shape transfer is not validated.** This is a
retrospective description of the existing selected sample; the entire DATA
sample had already been viewed in earlier phases. Neither fold is an untouched
or blinded validation sample. No central-window fit, physical transfer factor,
background prediction, HH inference, normalization, scale factor or new native
ROOT event read was performed.

## Protocol and input preservation

The [literal protocol](../metadata/phase5c_sideband_protocol.json) was frozen at
**2026-10-12T07:05:36Z**, before the first Phase 5C cache read at
2026-10-12T07:17:43Z. Its 3,056 raw bytes have SHA-256
`e9916da8772902c5464ea141397340a5230cb1733bb05e7c86800d9681295f66`.
The protocol was reviewed before implementation. The application refuses
changed protocol bytes, changed Phase 3 selection bytes and, in its DATA mode,
any different cache checksum or range. The final execution after clarifying
fixed-trim labels ran from **2026-10-12T07:23:12Z to 07:23:18Z**, exit 0.
The first outputs remain separately preserved.

The only physical-derived input read was
`outputs/phase4_numerical_v2_20261012/DATA93915/phase2/events.csv`,
SHA-256 `c242e256d76d6832031b2e4b2dfeeb342b5b05885c2a6bdf53d2d5eab71201c7`.
It contains the same 28-column derived cache and exact entry range
**[100,63195), 63,095 rows**. The unchanged selection is
`metadata/phase3_selection_config.ini`, SHA-256
`77d57cd6fa204aad5a24031ac925c4e20e121b8aee35148cc29b522b39cf5751`.
The application verifies input hashes before and after reading, the exact
header, contiguous entry ordering, full-cache unique run/event identities,
native integer ranges, object-count/validity/scalar contracts and cached
photon eta-difference consistency. These checks attest the derived cache and
its documented contract; they do not independently revalidate its original
ROOT file, detector calibration or provenance.

The population is unchanged cumulative C5 plus the individual Phase 3 jet
multiplicity, pT and eta predicates. Photon pT cuts remain strictly above
35/25 supplied GeV, |eta|<2.37 with the original open crack exclusion, and
inclusive jets have pT>25 and |eta|<2.5. Tight ID/isolation flags are optional
diagnostics and do not become selection cuts. No trigger or b-tag requirement
is added. Units remain **PROVISIONAL**. These are study-defined cuts and
inclusive jets, with no official ATLAS or b-jet equivalence.

| Preserved population accounting | Actual count |
| --- | ---: |
| Cache rows / valid rows | 63,095 / 63,058 |
| C5 / C5 plus individual jet predicates | 51,136 / 9,037 |
| Outside the [105,160] study mass domain | 7,348 |
| Unchanged C9 | 1,689 |
| Central [120,130) excluded from all diagnostic statistics | 315 |
| Sidebands [105,120) union [130,160] | 1,374 |
| Baseline A / B | 443 / 931 |

Central rows contribute only to preservation/accounting checks. Their masses,
eta values and identities do not enter sideband statistics, boundary
diagnostics or shape comparisons. The synthetic central-perturbation test
requires identical sideband event, audit and ROOT-count CSV bytes.

## Fixed identity split and statistical contract

The canonical identity is ASCII
`ATLAS_HH_BBGG_PUBLIC_V1|DATA93915|run=<UInt decimal>|event=<ULong64 decimal>`.
Unsigned values are normalized to decimal before SHA-256. The first digest
byte's low bit assigns **fold 0 calibration** and **fold 1 validation**. The
hash rule does not use mass, eta, entry position or selected counts. All
63,095 input identities are unique; the two sideband folds have zero identity
intersection and their union is exactly all 1,374 sideband events.

Calibration here means computing the frozen descriptive statistics. No
parameter is fitted and no region is chosen on that fold. Validation means
applying the same fixed procedure to the other fold and comparing their
empirical shapes. Disjoint identities prevent event reuse; they do not prove
random sampling, IID observations, independence from run conditions or an
unseen validation population. Historical viewing is recorded explicitly.

Nine fixed 5-GeV categories cover the disconnected sideband support:
105–110, 110–115, 115–120, 130–135, 135–140, 140–145, 145–150,
150–155 and 155–160. Low edges are inclusive and high edges exclusive except
exact 160 belongs to the final semantic category. Native ROOT's 11-bin
105–160 histogram instead assigns exact 160 to overflow; both policies are
saved explicitly and tested. There are no exact-160 events in this actual
sideband sample. The empty 120–130 gap is never interpolated or treated as an
observed density. Lower and upper sideband widths are 15 and 30 supplied GeV;
their raw totals are not equal-exposure comparisons.

The unbinned KS output is only the empirical maximum CDF difference D, with
ties handled at their full shared jump. No continuous-null KS pvalue is used
on the disconnected support. Cramer's V describes the 2-by-9 A/B contingency
table. Only zero-total columns are omitted from its statistic; all nine
categories remain in the inventory. Zero row totals or fewer than two
populated columns yield **UNDEFINED**, not zero evidence of dependence.
No chi-square pvalue or independence claim is reported.

Conditional normalized shapes are raw fractions p_i=n_i/N within each
partition/fold, with all nine categories retained. The full counting-model
covariance is `(delta_ij*p_i-p_i*p_j)/N`, conditional on the fixed total N.
Negative off-diagonal entries preserve the normalization constraint. These
fractions are not luminosity-normalized yields or a DATA background model.
Wilson 95% intervals describe conditional A occupancies under a working
binomial counting model. Raw sqrt(n) values are descriptive plug-in count
standard deviations, not exact Poisson confidence intervals. For n=0,
sqrt(n)=0 does not establish zero uncertainty or a zero upper bound. Empty
conditional totals yield undefined fractions/covariance. None of these
approximations includes trigger, selection, calibration, systematic effects,
unknown signal contamination or a proof of their sampling assumptions.

## Executed dependence and fold comparisons

| Population | A / B | Pearson(mass,absDeltaEta) | Spearman | A/B empirical KS D | Cramer's V |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pooled sidebands | 443 / 931 | 0.195745 | 0.189009 | 0.082132 | 0.084597 |
| Fold 0 calibration | 240 / 484 | 0.165732 | 0.160426 | 0.060262 | 0.106824 |
| Fold 1 validation | 203 / 447 | 0.229448 | 0.221226 | 0.138912 | 0.134543 |

The pooled lower-only and upper-only Pearson values are 0.086775 and
0.107836; pooled A-only and B-only values are 0.048313 and 0.304253.
This distinguishes within-sideband and partition-specific behavior from
the combined disconnected mass support. A small signed-eta or linear
correlation would not establish full independence. The different unbinned
and binned statistics provide complementary descriptions, not multiple
independent tests or physics validation.

Within fixed A, the fold-0/fold-1 mass KS D is **0.088157**; within B it is
**0.083306**; pooled it is **0.051347**. No pvalue, fitted transfer function,
acceptance threshold, closure residual or physical yield is derived from
these numbers. The validation fold's A/B D differs from calibration's D;
finite counting variation and selection effects remain unresolved. The
available descriptions do not justify treating A/B mass shapes as a
universally stable physical transfer. They also do not establish a formal
rejection of equal underlying shapes without an applicable inferential
model.

| Fixed mass category | Pooled A / B | A fraction | Wilson 95% counting interval |
| --- | ---: | ---: | --- |
| [105,110) | 74 / 121 | 0.3795 | [0.3143,0.4493] |
| [110,115) | 78 / 146 | 0.3482 | [0.2889,0.4127] |
| [115,120) | 65 / 123 | 0.3457 | [0.2815,0.4162] |
| [130,135) | 45 / 105 | 0.3000 | [0.2324,0.3776] |
| [135,140) | 49 / 120 | 0.2899 | [0.2268,0.3624] |
| [140,145) | 32 / 87 | 0.2689 | [0.1974,0.3549] |
| [145,150) | 42 / 75 | 0.3590 | [0.2778,0.4491] |
| [150,155) | 32 / 83 | 0.2783 | [0.2045,0.3663] |
| [155,160] | 26 / 71 | 0.2680 | [0.1900,0.3638] |

All 18 baseline contingency cells are populated and contain at least 5 events
in the pooled sample and in each fold. This is a recorded occupancy fact,
not authorization to apply an asymptotic test. Fold-1 A has only 9 events in
the final category and 11 in [140,145), so its shape remains count limited.
The lower/upper A counts are 217/226 pooled, 111/129 in fold 0 and 106/97 in
fold 1; B has 390/541 pooled, 210/274 in fold 0 and 180/267 in fold 1.
The unequal widths and changing conditional A fractions must accompany any
shape interpretation. Counts do not identify which events are background,
single-Higgs or other processes.

## Prespecified sensitivity inventory

| Fixed absDeltaEta boundary | Pooled A / B | A/B mass KS D |
| --- | ---: | ---: |
| 0.8 | 336 / 1,038 | 0.088374 |
| 1.0, unchanged baseline | 443 / 931 | 0.082132 |
| 1.2 | 530 / 844 | 0.092547 |

The fixed outer trims [110,160], [105,155] and [110,155], always excluding
the central window, have baseline A/B counts 369/810, 417/860 and 343/739.
Their Cramer's V values are 0.074527, 0.080937 and 0.071410. Exact trim
endpoints are included in every CSV population label, so per-category rows
remain unambiguous. These probes overlap and are not independent. No
boundary was optimized or selected from their results; the Phase 3 selection
and baseline A/B threshold remain unchanged.

## Regressions, evidence and reproducibility

Focused strict-warning ROOT 6.40.04 / C++20 compilation passed. The final
synthetic-cache suite passed **20/20 tests**, with **67 app invocations:
29 accepted and 38 rejected**. It includes independent rational tied-KS
and Cramer's V references, 70-digit Decimal Pearson/tied ranks, full 9-by-9
covariance and PSD directions, sparse/empty/constant states, original cut
boundaries, exact 160 semantics, central perturbation, whole-cache duplicate
rejection, frozen protocol/config, SHA-256 block boundaries, input bounds and
exclusive output preservation. These are engineering/statistical-method
regressions, not physical closure. The complete integrated CTest result is
recorded separately in the root-led Phase 5C quality-gate report.

An explicit independent Python audit joins all 63,095 raw cache identities
and re-evaluates the selection with the unchanged configuration. It verifies
all 1,374 sideband rows and fold identities, 54 correlation cells, 18
Cramer's V statistics, 27 KS statistics, 81 conditional shape fractions,
729 covariance cells, 150 defined Wilson intervals and native ROOT count
inventory. Maximum absolute numerical residual is 1.8042e-16 for
correlations, 1.3878e-17 for V, zero for KS/fractions, 1.0843e-19 for
covariance and 1.1103e-16 for Wilson intervals. The independent numerical
reviewer also audited the first-run derived outputs without rereading the
physical cache; that narrower scope is kept distinct.

The [publication-safe audit CSV](../metadata/phase5c_sideband_audit.csv) is an
exact byte copy of the final 1,962-row aggregate audit. Per-event identities
stay only in the ignored output directory. Final evidence is preserved at
`outputs/phase5c_v1/data_sidebands_final/`, with independent audit
`outputs/phase5c_v1/independent_audit_final.json`. Their raw SHA-256 hashes:

| Artifact | SHA-256 |
| --- | --- |
| summary.json | `5ea4338ec5224b494cf3ebd5751752bd929ad7b6572d9198f23f670da3d1acef` |
| sideband_events.csv | `441822328bdfbfb5b25108a93ea78745ee8475af69e93a028f48aea7aea9ebfa` |
| sideband_audit.csv / metadata copy | `5df09c40c8fbaaec7b6074105bc8743f24be5cbb4bfcf2c1dfbfdfe4e4c5d587` |
| root_mass_counts.csv | `5e695321bb8b714a033b3f3a977ba8fd6688a7fd54cd30bb84eaeab6b34d4408` |
| independent_audit_final.json | `d5b21183967a44f96e9e1f46cf98d6e2a022d29d88c62ede3695185f7823c0e4` |

The focused executable hash is
`c5fd458482180cf6dfa26c784ca9bf9155c109351b389b9a3a525cac7807cea7`;
its final source hash is
`e8089225533276a395f4db51c44475325b692cf3554adce4e731a6cea012d15e`.
The source, protocol and native binary identities are distinct. A final
integrated binary/build snapshot may differ from this focused build and must
be recorded by the root-led validator rather than inferred from this hash.

From the existing activated environment, the synthetic and explicit cached
DATA commands are:

```bash
python -B tests/test_phase5c_sidebands.py \
  <build>/phase5c_data_sidebands metadata/phase3_selection_config.ini \
  metadata/phase5c_sideband_protocol.json

<build>/phase5c_data_sidebands \
  outputs/phase4_numerical_v2_20261012/DATA93915/phase2/events.csv \
  metadata/phase3_selection_config.ini metadata/phase5c_sideband_protocol.json \
  outputs/phase5c_v1/NEW_REPRODUCTION 100 63195 PROVISIONAL DATA93915

python -B tests/audit_phase5c_sidebands.py "$PWD" \
  outputs/phase5c_v1/NEW_REPRODUCTION outputs/phase5c_v1/NEW_AUDIT.json
```

Both reproduction destinations must be new. Prior outputs, Phase 5B's FNV
fold evidence and all selection definitions are retained; the SHA split is
an additive Phase 5C protocol. Arithmetic APIs are validated here within the
64,000-row bounded diagnostic contract, not promised overflow-safe for
unbounded external populations. No physical-study figure was generated.

**Scoped disposition:** dependence assessed and fold separation executed;
physical background closure **NOT_EVALUATED**, physical transfer and
background prediction **not authorized**, contamination/exposure/calibration
**UNKNOWN**. Further raw-methods studies can proceed under the preserved
gates; calibrated background or HH claims require suitable physical inputs
and a separately justified statistical model.

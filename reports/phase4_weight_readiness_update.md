# Phase 4 V2 weight and background readiness update

**ABSOLUTE_MC_NORMALIZATION = BLOCKED; SCALE_FACTOR_APPLICATION = BLOCKED;
COMPLETE_BACKGROUND_PREDICTION = BLOCKED.** This documentation audit applies to
the three already acquired GamGam MC files. It implements no event weights,
scale factors, luminosity scaling, additional ROOT transfer, fit, or HH result.
**V2 numerical status is recorded in the
[numerical recovery decision](phase4_numerical_recovery_decision.md) and
[machine-readable gate results](../metadata/phase4_numerical_gate_results.json);
normalization and calibration remain BLOCKED.** The separate
[DATA/MC regression report](phase4_data_mc_regression.md) records the actual
executions and their bounded scope. A successful numerical gate does not
verify any of the normalization or calibration ingredients below.

This is an additive assessment dated **2026-10-12**. The original Phase 4
commit `d823593b42889592897263819138170470f4dc47`, its failed ggF pair-mass
closure result, raw diagnostics, and original readiness reports remain
historical evidence. This report does not replace them. The observed weight
numbers below come from the preserved original native diagnostics in
[phase4_weight_normalization_evidence.json](../metadata/phase4_weight_normalization_evidence.json),
not a new reading of the ROOT files during this documentation audit.
The independent V2 DATA cache/histogram audit also checked all 63,095 historical
entries and the 37 original invalid photon pairs. Its C0-C9 counts, raw optional
flags, and full native histogram bins/flows are unchanged; sub-bin pair-mass
values can change under the shared numerical fix. Those checks preserve the
raw-data interpretation and do not supply a luminosity or MC correction.

## Source identity and access

The live browser check read [CERN record 93922](https://opendata.cern.ch/record/93922)
and [Zenodo version record 15791092](https://zenodo.org/records/15791092).
The former identifies the 2015+2016 13 TeV educational beta GamGam MC release,
373 files and 12,120,657 events. Its stated skim requires two photons each with
at least 25 GeV pT. The latter identifies PhysLiteToOpenData **v1.0.0**, published
2025-07-02. This release date follows the selected files' `ODEO_FEB2025_v0`
name tag; it does not establish their exact converter commit or configuration.

Detailed inspection uses the preserved, version-tagged official source
snapshots recorded in [sources.md](../metadata/sources.md). The later
[v1.0.0 skim script](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
uses photon pT > 20 GeV for its GamGam skim. This differs from the record's
25 GeV description. The exact FEB2025 selection, producer, generator metadata
route, and calibration payload are therefore **UNKNOWN_EXACT_RELEASE**, even
where the later implementation explains the observed branch names.

The SHA-256 values below identify the preserved local response bytes; they are
locally computed evidence hashes, not official published strong digests or a
claim that fresh access retrieved identical content.

| Preserved official snapshot, acquired 2026-10-09 | SHA-256 |
| --- | --- |
| `extras/metadata.csv`, v1.0.0 | `7cbf4522af6fb108c82be36d72a5d36a38dd126e609c71899b1c2f729d681225` |
| `scripts/skimOpenDataNtuples.py`, v1.0.0 | `798cc579aaa303be420ca8621d7cb3e1b3ef2cee1f0ecb9d25469a1aba32f6b8` |
| `Root/JetInfo.cxx`, v1.0.0 | `01325c175a93676dea65f7946dba486bcc1e84c6f7168e694bc3362c05f3a5b5` |
| `Root/PhotonInfo.cxx`, v1.0.0 | `9a59853da9c04a428d1990320b680940480bdf723f8d299689ac3bc26e7a8569` |
| `python/PhysLiteToOpenDataAlgorithms.py`, v1.0.0 | `5a56eb88d9beb3c472f21defca8f250a7dd3ca63ef60fe08f56cc8183eaf56c3` |

Fresh browser access to the detailed ATLAS documentation returned access
errors; versioned GitLab pages were inaccessible through that tool. Six
separately bounded HTTPS text requests, with TLS verification and a 256 KiB
body cap each, all timed out during TLS negotiation and consumed **0 response
body bytes**. Their explicit 64 KiB request reserve per attempt charges
**393,216 bytes** to the additive V2 ledger. Evidence stays at
`.local/phase4_v2_weight_sources_20261012/access.json`; this accounting is
application-consumed bodies plus reserve, **not measured wire traffic**.
Browser transport bytes are unavailable and are not presented as measured.
No source snapshot was replaced, no TLS verification was disabled, and no
ROOT dataset was fetched. These access failures do not prove public absence.

## Normalization fields and their unresolved conventions

The preserved official [educational metadata guidance](https://opendata.atlas.cern/docs/data/for_education/13TeV25_metadata)
requires a skimmed sample to use the full unskimmed generated normalization.
It identifies cross sections in pb and distinguishes cross section, filter
efficiency and k-factor. The versioned
[metadata table](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0)
provides the following candidate values; their exact FEB2025 applicability
has not been established.

| DSID / generation tag | Cross section [pb] | Filter efficiency | k-factor | Table nEvents | Table signed sumW | Table sumW2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 343981 / e5607 | 28.3 | 0.00227 | 1.717 | 200,000 | 5,660,114.774513245 | 162,287,375.54376578 |
| 346214 / e6970 | 3.782 | 0.00227 | 1 | 80,000 | 299,915.6851153374 | 1,142,827.2423424923 |
| 423103 / e3791 | 106,210,000 | 0.0000393 | 1 | 1,989,000 | 1,989,000 | 1,989,000 |

Native xsec, kfac and num_events match these table values in the inspected
entries. The native H-sample generated sums instead read
`5660115 / 162287376` and `299915.6875 / 1142827.25`; their differences are
consistent with Float32 rounding of the later table values. The native branch
types are double, so this observation alone does not identify where rounding
occurred or prove the converter route. For 423103, the native `filteff` is
**0.000039**, versus **0.0000393** in the later table, a relative difference of
approximately **-0.76336%**. Both values remain preserved; neither is silently
chosen or corrected for normalization.

The cached [variable dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
describes the two sum fields using square-root wording. In contrast, the
versioned skim script adds CutBookKeeper histogram bins 2 and 3 directly and
writes them as `sum_of_weights` and `sum_of_weights_squared`, without a square
root. The native magnitudes are consistent with direct sums, rather than the
square roots of the later table sums. This resolves what the **later code**
does; it does not verify the FEB2025 CutBookKeeper aggregation or remove the
public documentation discrepancy. Neither squaring a field nor taking its
square root is an authorized repair.

If all conventions were verified, a luminosity weight could use a signed
generator event weight with the verified product of luminosity [pb^-1], cross
section [pb], applicable filter efficiency and k-factor, divided by the
verified signed pre-skim generated sumW. This is an ingredient description,
not an implemented or approved normalization. `num_events`, the flat-tree
entry count, the 9,900-entry diagnostic sum, the selected-C9 sum, absolute
weights and sumW2 are not interchangeable denominators.

The selected H samples are decay-constrained single-H gamma-gamma samples,
and their table filter efficiencies are already 0.00227. Before any extra
Higgs branching-ratio factor, the exact generation job, decay enforcement,
cross-section convention, and existing efficiency factors must establish
whether that factor is already included. Adding a second factor by name or
numerical resemblance risks double counting. The metadata links generation
jobs on the mutable `master` branch; matching these links to the e5607/e6970
productions has not been verified. The separate later
[applyskim_addweights recipe](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2Fapplyskim_addweights.py/raw?ref=v1.0.0)
contains explicit gamma-gamma branching-factor adjustments for other DSIDs
(345965, 345961 and 345834), not 343981 or 346214. That recipe is not evidence
that a correction should be imported into the selected files.

The native trees have 94,082, 38,403 and 26,366 skimmed entries, respectively.
These counts differ from the generated totals above as expected for a skim,
but a count/size comparison cannot prove that all contributing generation
jobs, signed CutBookKeepers and retained events were combined once and
completely. Later source aggregation sums across contributing input files and
can skip an input without its expected histogram. Production provenance and
complete input accounting must establish the actual denominator. The bounded
[100,10000) interval is not a complete-sample rate estimator.

## Signed generator weights and negative correction scalars

The preserved native diagnostics cover **9,900 entries per DSID**, not the
whole release. Raw histogram/cutflow counts remain unweighted and samples
remain separate.

| DSID | Positive / negative / zero mcWeight | Diagnostic sum(mcWeight) | Diagnostic sum(mcWeight^2) | Negative ScaleFactor_BTAG / minimum |
| --- | --- | ---: | ---: | --- |
| 343981 | 9886 / 14 / 0 | 281211.1376647949 | 8033225.089416509 | 18 / -1.2101823091506958 |
| 346214 | 9885 / 15 / 0 | 37087.79810833931 | 140118.1906686802 | 75 / -1.2288618087768555 |
| 423103 | 9900 / 0 / 0 | 9900 | 9900 | 103 / -1.2561054229736328 |

Negative generator weights and negative BTAG correction scalars are separate
observations. The former are preserved signed values; their occurrence in the
selected Powheg samples does not verify the exact weight-index convention.
The latter have **UNKNOWN** validity/producer semantics and cannot be justified
as ordinary signed generator weights. Taking absolute values, dropping negative
events, replacing invalid scalars with unity, multiplying both BTAG and FTAG,
or applying either scalar is not supported by this audit.

In later [JetInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0),
the BTAG event scalar is the product of per-jet
`ftag_effSF_DL1dv01_Continuous_NOSYS`. Its multiplication does not have the
explicit -1 exclusion used for the neighboring JVT product. Sentinel
propagation is therefore a possible explanation, **not a demonstrated cause**
for the old files. The v1.0.0
[algorithm configuration](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/python%2FPhysLiteToOpenDataAlgorithms.py/raw?ref=v1.0.0)
names DL1dv01/Continuous and
`xAODBTaggingEfficiency/13TeV/2023-22-13TeV-MC20-CDI-2023-09-13_v1.root`.
This identifies a later configuration, not the exact calibration of the
FEB2025 files, a GN2 equivalence, a validated quantile-to-working-point mapping,
or a usable b-tag efficiency correction for this study.

Later [PhotonInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0)
multiplies loose photon-ID and loose-isolation factors across retained photons.
This does not establish applicability to retained photon objects, any future
tight-flag selection, pairing or event-level trigger. Tight-ID/isolation flags
remain optional diagnostics in the existing Phase 3/C9 selection. Zero pileup
scalars also appear in the native
ranges. Each applied correction would need its own producer, object scope,
working point, calibration, validity/sentinel policy and uncertainty model.

Negative native truth-jet masses (1397 / 2511 / 731 in the original main runs)
are preserved with **UNKNOWN_NEGATIVE_VALUES** mass-quality classification.
No energy is inferred from them. The separate pT/eta/phi association study is
geometric and **PROVISIONAL**; it establishes neither prompt-photon purity nor
truth flavour, b-tag efficiency or normalization.

## Background coverage and bounded next inputs

The physical source classification comes from the official versioned metadata
joined to [the 373-DSID manifest](../metadata/phase4_mc_sample_manifest.csv),
with exact release membership supplied by record 93922. None of these roles
is promoted into a combined or calibrated background yield.

| Input | Role / limitation | Current inspection status |
| --- | --- | --- |
| 343981 ggF H125 gamma-gamma; 346214 VBF H125 gamma-gamma | Single-H resonance examples, **not HH**; not a complete single-H prediction | Three-file batch includes both; bounded raw reconstruction only |
| 423103 gammajet DP70_140 | At least one hard-process or parton-shower photon with 70 < pT < 140 GeV; a **photon-pT slice**, not an m_gamma-gamma interval or complete jet-to-photon fake model | Included; no complete slicing/overlap/fake transfer model |
| 302521 diphoton Mass_100_160 | Generated two-photon pT > 20 GeV and 100 < m_gamma-gamma < 160 GeV; relevant continuum overlap with 105-160 | Public 110,755,804-byte file; not selected within this remaining allocation |
| 364352 diphoton myy_90_175 | Relevant target-window continuum alternative | 590,212,105 bytes exceeds the entire 128 MiB new-file ceiling |
| 302520 diphoton Mass_55_100 | No finite generated 105-160 GeV overlap; any detector migration would need measurement | Cannot substitute as generic target-window continuum |
| Other gammajet/dijet slices and photon/top processes | Require slice completeness, overlap control, verified weights and independent fake/control-region closure | Source inventory only; no full prediction |
| HH -> bb gamma-gamma | Suitable explicitly verified HH sample remains absent from the scoped inspected release inventory | **BLOCKED_INPUT**, not a claim of global public absence |

302521 fits a **fresh** 128 MiB allocation by itself, but does not fit after
the charged earlier batch and current access reserve. Its status is an
allocation/coverage limitation, not unavailable public physics. A separately
approved bounded transfer or a verified controlled-range transport could be
considered later; no transport implementation or new allocation is assumed
here. Smaller files from disjoint generated mass slices cannot repair the
target-window coverage.

## Required evidence before any weighted prediction

| Ingredient | Status / required evidence |
| --- | --- |
| Exact FEB2025 producer and skim | **UNKNOWN**; reproducible converter commit/configuration and generated-to-flat input mapping |
| Cross section, filter efficiency, k-factor and decay convention | **PARTIAL** later table/native agreement; resolve 423103 mismatch and verify generation-tag-specific semantics without branching-factor duplication |
| Signed generated denominator and sumW2 | **PARTIAL** native fields/later source; prove exact pre-skim aggregation, weight-index/sign convention, precision and completeness; resolve dictionary discrepancy |
| Luminosity for actual DATA subset | **UNKNOWN**; period/run/GRL/trigger-prescale-specific exposure, including the historical exclusion of entries [0,100); do not assign a full-release luminosity to this bounded subset |
| DATA/MC reconstruction compatibility | **UNKNOWN**; matching periods/campaign, calibrations, trigger and event/object selections |
| Photon/JVT/pileup/flavour/trigger corrections | **BLOCKED**; exact applicability, sentinel handling and uncertainty model, with BTAG/FTAG relationship resolved |
| Continuum/fakes/other backgrounds | **PARTIAL_SOURCE_COVERAGE**; relevant target-window continuum plus validated slices/control regions and overlap treatment |
| HH signal and statistical model | **BLOCKED**; verified signal, acceptance/efficiency, background and systematic model, and suitable statistical inputs |

The supported next work is documentation/provenance resolution and a separately
budgeted relevant-continuum or richer-input feasibility check. A numerical
recovery may reopen bounded reconstruction/method studies, but does not grant
absolute DATA/MC rate comparison, calibrated b-tagging, prompt-purity claims,
fits, likelihoods, limits, coupling constraints, discovery, or exact ATLAS
publication reproduction. The original Phase 4 scientific blockers remain
preserved independently of the V2 numerical result.

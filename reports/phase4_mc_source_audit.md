# Phase 4 MC source audit

Audit date: 2026-10-11. **SOURCE_METADATA_JOIN = PASS; SAMPLE_COVERAGE = PARTIAL;
EXACT_RELEASE_PRODUCER = UNKNOWN; ABSOLUTE_NORMALIZATION = BLOCKED;
PHYSICAL_RECONSTRUCTION_GATE = FAIL.**

This is a bounded public-source and sample-selection audit. It does not upgrade
Phase 0 PARTIAL or earlier PROVISIONAL object/unit interpretations, establish an
HH signal model, or validate luminosity-scaled data/MC predictions. Native ROOT
schema, staged entries, truth-unit probes and event tests are separate evidence.

## Release and reproducible inventory

[CERN record 93922](https://opendata.cern.ch/record/93922), DOI
[10.7483/OPENDATA.ATLAS.IMZO.7U52](https://doi.org/10.7483/OPENDATA.ATLAS.IMZO.7U52),
identifies the 2015+2016, 13 TeV GamGam educational MC beta release. Its live page
was readable on the audit date: 373 files and 12,120,657 events. The page describes
Athena Release 22 reprocessing, conversion from public DAOD_PHYSLITE, and a skim
with at least two photons of at least 25 GeV each. This release-level description
does not supply exact per-file producer/configuration provenance.

[The manifest](../metadata/phase4_mc_sample_manifest.csv) contains **373 rows for
373 unique DSIDs**, joined one-to-one to the cached official
[v1.0.0 metadata.csv](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0).
It preserves every filename, size, published Adler-32, URI, physics name/process,
generator, e-tag, description, job-option link and raw normalization fields.
Filename/metadata physics-name agreement, finite numeric fields, positive file
sizes, checksum syntax and URI/filename agreement were checked; this is metadata
integrity, not validation of generated-event sums or a normalization recipe.
The indexed payload totals **4,895,835,241 bytes**.

Run from the repository root with Python 3; this script has no network operation
and never opens a ROOT event file:

```bash
python scripts/audit_phase4_sources.py \
  --record .local/phase0_sources/opendata_93922_json.json \
  --metadata .local/phase0_sources/framework_extras_metadata.csv.txt \
  --selected 343981 346214 423103 \
  --output metadata/phase4_mc_sample_manifest.csv \
  --summary .local/phase4_source_inventory.json
```

| Input snapshot | SHA-256 |
| --- | --- |
| Record 93922 API JSON, preserved Phase 0 snapshot | `750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c` |
| Versioned metadata.csv, acquired 2026-10-09 | `7cbf4522af6fb108c82be36d72a5d36a38dd126e609c71899b1c2f729d681225` |
| Generated Phase 4 manifest | `dd4e7f4438a861705c5906368ad9eda91bce25f5cf08364cf2bc78bbbd5d2fc4` |

The script assigns documentary source categories: 20 diphoton continuum, 19
single-H diphoton, 14 gamma+jet, 13 dijet fake-related candidates, 62 other
photon-background candidates, 121 other single-H channels, 42 other top candidates,
and 82 other processes of unestablished target relevance. These categories are
triage labels; they do not determine an event's promptness, reconstructed origin,
fake rate, or flavour. All rows remain in the manifest, including unselected and
out-of-window samples. No explicitly identified Higgs-pair candidate was found
in this scoped 373-DSID join. Inspection of the preserved public research Higgs
[nominal index 80012](https://opendata.cern.ch/record/80012) and
[variation index 80013](https://opendata.cern.ch/record/80013), covering 94 and
55 cached index names respectively, also did not establish a suitable HH→bbγγ
sample. This is not a search of all public ATLAS collections.

## Selection and physical scope

Sample descriptions and the following phase spaces come from the versioned
official metadata above. Direct PMG job-option links are preserved per row.
The live GitLab blob/raw/API attempts were inaccessible through the browser
tool on this date, so these descriptions are cached official metadata evidence,
not a newly executed or independently validated generator configuration.

| DSID | Documented physics / phase space | Bytes | Published Adler-32 | Decision |
| --- | --- | ---: | --- | --- |
| 343981 | Powheg+Pythia8 ggF H125→γγ, single H | 32,086,416 | `3e3f0a3b` | Selected bounded reconstruction/schema example; not HH |
| 346214 | Powheg+Pythia8 VBF H125→γγ, single H | 14,414,350 | `52f61c51` | Selected complementary single-H example; not HH |
| 423103 | Pythia8 gamma+jet / jetjet with a hard-process or shower photon, 70 < photon pT < 140 GeV | 10,489,108 | `5bf96f22` | Selected one photon-pT slice; not full fake-background coverage |
| 302521 | Pythia8 direct diphoton, photon pT > 20 GeV, 100 < generated Mγγ < 160 GeV | 110,755,804 | `b43248ea` | Relevant continuum; not selected after earlier transfer allocation |
| 364352 | Sherpa diphoton, 90 < generated Mγγ < 175 GeV | 590,212,105 | `19c3d623` | Relevant continuum; full file exceeds the entire new-file budget |
| 302520 | Pythia8 direct diphoton, 55 < generated Mγγ < 100 GeV | 322,658,547 | `5c7f0ecf` | Excluded as generic 105–160 GeV continuum |

The selected payload is **56,989,874 bytes**, below the 128 MiB new-file ceiling.
The actual transfer ledger is authoritative: it also charges earlier received
bytes and failed/duplicate transfer traffic and preserves the cumulative 256 MiB
historical ceiling. Manifest `download_chosen=YES` means selection; its
`download_status` points to that ledger and does not itself certify a completed
download or checksum. Neither this script nor this source-audit subtask downloads
datasets.

The actual transfer uses certificate/hostname-validated HTTPS for public record
metadata and CERN certificate retrieval, then explicitly allowed CERN storage
redirects with **HTTP** for ROOT payloads. It is not an end-to-end TLS transfer.
Official file size and published Adler-32 are checked before event inspection;
the computed SHA-256 is a **local artifact identity**, not a strong digest
published by the source. Request locations/capability queries are redacted from
saved logs. Budget accounting is consumed HTTP-response payload plus a reserved
64 KiB per request, including failed requests/redirects; it is not a measurement
of total network-wire bytes or closed/unread error-response bodies.

302521 fits a fresh 128 MiB budget by itself, so **the public catalogue does have
a compatible target-window continuum candidate**. Its nonselection here is a
remaining-budget/allocation limit, not evidence of scientific unavailability.
Small Sherpa files below 50 GeV or above 2 TeV are not substitutes. A generated
slice beginning at 160 GeV has no finite overlap with 105–160 GeV; possible
detector migration must be measured and cannot justify treating it as complete
continuum coverage. The gamma+jet DP labels are photon-filter pT slices, not
diphoton-mass slices. One such slice cannot support a calibrated jet-to-photon
fake estimate or summation of all backgrounds.

## Exact production, truth, units and weights

The framework
[release record](https://zenodo.org/api/records/15791091) identifies v1.0.0 dated
2025-07-02, later than `ODEO_FEB2025_v0` in the files. Its archived API response
resolves to version record 15791092. The v1.0.0
[skim source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
uses photon_pt > 20 for its GamGam selection, whereas the release page states
25 GeV. This discrepancy reinforces **UNKNOWN exact producer equivalence**;
the later source is explanatory evidence only.

The later
[event source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0)
retrieves TruthPhotons and AntiKt4TruthDressedWZJets in the same MC event. Newly
retrieved official
[TruthInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FTruthInfo.cxx/raw?ref=v1.0.0)
(5,745 bytes, SHA-256
`792543c179d42efa2c10588b5175bd7150c1b9e30cfa2fd7e6e7358d7dd89317`)
stores photons with pT ≥ 10 GeV and jets with pT ≥ 20 GeV, multiplying truth pT
and jet mass by 0.001. No photon origin/ancestry/status or jet-flavour label is
exported by that source. Those definitions are not proof of the exact FEB2025
truth-collection construction.

Actual ROOT inventories in the selected three files establish the presence of
`truth_photon_n/pt/eta/phi` and `truth_jet_n/pt/eta/phi/m`, with native
`ROOT::VecOps::RVec<float>` vectors. Truth branches are therefore **present**;
absence cannot be used as a blocker. Matching can be scoped to same-row supplied
collections after separate physical structure/unit checks. A study-defined
geometrical association fraction is not prompt-photon purity, Higgs-daughter
purity, truth-b-jet efficiency, or a validated ATLAS detector performance result.
The matching validation report records its exact eligibility, acceptances,
thresholds, denominators and actual execution results.

First-100-entry physical probes, staged as disjoint [0,10) and [10,100), pass
the checked truth pT/eta/phi numeric consistency and same-entry DSID checks in
all three samples. GeV/radian interpretation remains **PROVISIONAL**, supported
by the numerical ranges and later source rather than exact producer provenance.
There are **15 / 22 / 8 negative native truth-jet mass values** for
343981 / 346214 / 423103, with minima −0.0663375631 / −0.1140715778 /
−0.0506430604 in the provisional GeV interpretation. Preserve these signed
values; their precise production/rounding semantics are UNKNOWN. Direction-only
geometrical association uses pT/eta/phi and does not need truth-jet mass, so it
can proceed within its explicit scope without declaring truth-mass quality PASS.
The native probe status is **truth_mass_quality = UNKNOWN_NEGATIVE_VALUES**.
No mass is clamped, made absolute or used to infer a truth-jet energy. Bounded
probe artifacts are retained under ignored
`outputs/phase4_v1/<DSID>/physical_probe.json`; the final Phase 4 validation
summaries record their identities and larger-stage results separately.

Raw normalization metadata for selected DSIDs are preserved without modification:

| DSID | σ [pb] | genFiltEff | kFactor | metadata nEvents | metadata signed sumW | metadata sumW² |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 343981 | 28.3 | 0.00227 | 1.717 | 200000 | 5660114.774513245 | 162287375.54376578 |
| 346214 | 3.782 | 0.00227 | 1 | 80000 | 299915.6851153374 | 1142827.2423424923 |
| 423103 | 106210000 | 3.93e-05 | 1 | 1989000 | 1989000 | 1989000 |

The first-100 native probes give **xsec, kfac and num_events numerically equal
to those table fields in all three samples**. The H samples also agree in
filteff. Two differences must remain visible:

| DSID / field | Native repeated value in first 100 | Later metadata value | Interpretation |
| --- | ---: | ---: | --- |
| 343981 sum_of_weights | 5660115 | 5660114.774513245 | Close to direct sum; consistent with single-precision rounding |
| 343981 sum_of_weights_squared | 162287376 | 162287375.54376578 | Same limited numerical consistency |
| 346214 sum_of_weights | 299915.6875 | 299915.6851153374 | Same limited numerical consistency |
| 346214 sum_of_weights_squared | 1142827.25 | 1142827.2423424923 | Same limited numerical consistency |
| 423103 filteff | 0.000039 | 0.0000393 | Native value is 0.7633588% lower; exact reason UNKNOWN |

These are numerical comparisons of bounded repeated scalars, not a proof that
the entire produced sample matches v1.0.0 or that the denominator is the correct
complete pre-skim signed sum. The H sums look like rounded direct sums rather
than the square-root dictionary description; no value is squared, rounded back,
replaced or repaired. Gammajet filteff is preserved separately from its later
table value and is not silently corrected. In these first 100 rows, mcWeight
is constant and positive: 28.48573112487793 / 3.7499001026153564 / 1 for
343981 / 346214 / 423103. That bounded observation does not establish the sign
distribution of every event in the release.

423103 also has a native `ScaleFactor_BTAG` minimum of −1, while its
`ScaleFactor_FTAG` range in the same probe is positive. The −1 value is a separate
unresolved SF/sentinel anomaly; it is not evidence of a negative generator
mcWeight. Zero pileup SFs occur in the first-100 H probes. Their exact validity
is unverified. Do not take absolute values, substitute one, multiply both tagging
fields, or apply any of these corrections automatically. See the
[b-tag feasibility report](phase4_btag_feasibility.md).

These later-table numbers are not automatically the exact processed-file
denominators. The
[educational dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
describes square roots for `sum_of_weights` and `sum_of_weights_squared`; the
versioned skim source instead sums CutBookKeeper bins and writes direct sums.
The exact FEB2025 mapping remains unresolved. Native values, sign counts and
partial selected sums are recorded separately, without resolving this conflict
by numerical convenience. Preserve negative event weights and both sums; do not
replace the signed pre-skim generated sum with an entry count or selected sum.

Only after verification could a normalization use
`L × σ × genFiltEff × kFactor / signed_generated_sumW`, multiplied by the actual
event generator weight and applicable object/event corrections. The metadata
filter efficiencies for the decay-restricted H→γγ examples are 0.00227, which is
consistent with a decay-related factor but does not establish the exact
convention. An additional branching ratio cannot be multiplied without verifying
whether it is already incorporated in σ, genFiltEff or another published factor.
The later PhotonInfo source builds its
photon SF from loose-ID/isolation ingredients, so a tight study selection does
not establish SF applicability. No luminosity, branching ratio, SF or MCweight
is applied here and no selected sample rates are combined.

## Public research alternative

The live official
[PHYSLITE variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html)
documents TruthPhotons, reconstructed photon truth links/origin/type and jet
hadron-cone truth-flavour labels. This is a possible route to richer same-event
truth provenance, not proof that an arbitrary file has readable/usable fields.
The preserved record 80012 index contains these first listed representatives:

| Public research sample | First listed file | Bytes | Adler-32 |
| --- | --- | ---: | --- |
| ggF H125→γγ | `DAOD_PHYSLITE.38191914._000036.pool.root.1` | 1,929,286,284 | `4444ddc1` |
| VBF H125→γγ | `DAOD_PHYSLITE.38191539._000052.pool.root.1` | 785,967,187 | `70fd7bae` |

Both exceed 128 MiB. No such ROOT file was downloaded. The native flat `analysis`
RVec reader is not an xAOD/ElementLink adapter; an alternative requires a bounded
transport plan, explicit xAOD reading/environment support, native schema/unit
checks and same-event closure before use. It is **BLOCKED_BUDGET / ADAPTER_NOT_VALIDATED**
for this run, while the existing flat truth collections permit a narrower
conditional geometrical study. Official
[research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp)
also restrict custom object reconstruction and completeness of inputs/systematic
samples. The Phase 0 snapshots preserve those limitations; live access to the
documentation/GitLab pages was not uniformly available today.

## Completed larger-stage evidence and disposition

The three actual main reconstructions each processed **[100,10000): 9,900
entries per sample, 29,700 total**. They preserve the first-100 evidence above
as a separate disjoint probe population. Across all three staged [0,10000)
populations the audit contains 30,000 unique entries; one explicitly recorded
repeat read of the failed event is a diagnostic read, not an added unique event.
See [MC reconstruction](phase4_mc_reconstruction.md), the machine-readable
[quality gates](../metadata/phase4_quality_gates.json), and the retained
[numerical failure diagnosis](phase4_numerical_failure.md).

| DSID | Valid pair masses checked | Failed mass comparisons | Maximum absolute discrepancy [GeV] | Raw C9 diagnostic events | Negative truth-jet masses | Negative BTAG SF scalars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 343981 | 12004 | 1 | 1.9124535637071727e-7 | 1125 | 1397 | 18 |
| 346214 | 12197 | 0 | 6.3440339023723702e-9 | 1419 | 2511 | 75 |
| 423103 | 13220 | 0 | 3.3821119627130969e-8 | 588 | 731 | 103 |

**The overall original numerical gate remains FAIL.** The 343981 failure is
the leading diphoton pair at source entry 5888 (C9_selected = false). Its
1.9124535637071727e-7 GeV discrepancy exceeds that pair's unchanged tolerance
1.1239490151491467e-7 GeV, from
`1e-7 + 1e-10*abs(long_double_reference_mass)`. A sample-wide maximum tolerance
is not the failed pair's tolerance. Other sample passes and fresh CTest **17/17
PASS** are separate regression evidence and do not clear this physical gate.
No event, value, old artifact or tolerance is changed to manufacture a pass.

Direction-only same-event association CSV checks pass within their explicit
**PROVISIONAL geometrical** scope; they are independent of truth-jet mass and
do not repair the reconstruction failure or establish physical origin/flavour.
The main negative truth-mass minima are −0.1931658387 / −0.1945634931 /
−0.4330529273 under the provisional unit interpretation. Signed mass remains
unused by geometry and no truth energy is inferred. The negative BTAG SF minima
are −1.2101823092 / −1.2288618088 / −1.2561054230; their convention/applicability
remains UNKNOWN. These are separate from signed generator weights.

The retained `reconstruction/weight_diagnostics.json` files contain:

| DSID | Positive / negative / zero mcWeight entries | Bounded raw sumW | Bounded raw sumW² |
| --- | --- | ---: | ---: |
| 343981 | 9886 / 14 / 0 | 281211.1376647949 | 8033225.089416509 |
| 346214 | 9885 / 15 / 0 | 37087.79810833931 | 140118.1906686802 |
| 423103 | 9900 / 0 / 0 | 9900 | 9900 |

The larger H samples thus contain negative generator weights that the first-100
probe did not encounter. Signs are retained; these partial-range diagnostic sums
are not full generated denominators, selection efficiencies or normalization
inputs. Histograms/cutflows remain RAW_UNWEIGHTED, with normalization and SFs
not applied. Phase 5 scientific development is blocked pending separately
reviewed numerical recovery plus the unresolved physical/provenance conditions.

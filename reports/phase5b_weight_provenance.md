# Phase 5B exact-production weight provenance review

**NOMINAL_GENERATOR_WEIGHT_SEMANTICS = UNKNOWN;
SIGNED_PRE_SKIM_DENOMINATOR_APPLICABILITY = UNKNOWN;
PHYSICAL_NORMALIZATION = BLOCKED; SCALE_FACTOR_APPLICATION = BLOCKED.**
This additive 2026-10-12 review uses preserved official source snapshots,
the current Phase 5 manifests, previously executed bounded diagnostics and
the newly root-ledger-acquired job response described below. This reviewer
makes no network request, ROOT event read, event-weight application,
figure or fit. No earlier blocker is relabelled PASS.

## Exact sample and candidate metadata

The current source identity is the DSID 302521 member of
[CERN record 93922](https://opendata.cern.ch/record/93922), with the pinned
110,755,804-byte filename and published `adler32:b43248ea` recorded in the
[filter review](phase5b_generator_filter_review.md). The preserved fresh
record response SHA-256 is
`750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c`.
No 302521 native scalar, sign count, tree entry count, unit or branch type is
inferred from this identity or the other MC samples.

The later official
[v1.0.0 metadata table](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0)
supplies the following **candidates**, separately from their physical applicability:

| Ingredient | Documented 302521 value | Exact FEB2025 applicability |
| --- | ---: | --- |
| Sigma | 18.282 pb | **UNKNOWN** exact sigma/process/filter convention |
| Generator filter efficiency | 0.44191 | **UNKNOWN** exact e4045 filter and production accounting |
| k-factor | 1 | **UNKNOWN** exact applicable convention |
| Generated N | 642,000 | **UNKNOWN** complete generated-input aggregation |
| Signed generated sumW | 642,000 | **UNKNOWN** nominal index, pre-skim scope and complete aggregation |
| Generated sumW2 | 642,000 | **UNKNOWN** matching index, definition and aggregation |
| Generation tag | e4045 | **UNKNOWN** mapping to immutable job/production chain |
| Filename release tag | ODEO_FEB2025_v0 | Identified name; exact converter/configuration not recovered |
| Branching/decay convention | Not independently established | **UNKNOWN**; no extra factor applied |
| Skim/processing completeness | Not established | **UNKNOWN** |

Equality of the candidate N/sumW/sumW2 values does not identify the released
event-weight branch, nominal index or full production provenance. It is not
a replacement for inspecting the physical file and generated-input records.
The direct-diphoton classification also does not authorize importing an extra
Higgs branching factor from unrelated single-H samples. Exact sigma/filter/
decay conventions must prevent any factor from being double counted.

## What later code establishes about event weights

The preserved
[v1.0.0 converter](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0)
copies the float decoration `generatorWeight_NOSYS` to `mcWeight`. Its xsec,
filter efficiency and k-factor come from `PMGCrossSectionTool`, initialized
through a resolved `PhysLiteToOpenData/PMGxsecDB_mc16.txt` payload. This is a
later implementation fact; the exact database payload/version used in FEB2025
and exact production applicability have not been recovered.

The preserved
[algorithm configuration](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/python%2FPhysLiteToOpenDataAlgorithms.py/raw?ref=v1.0.0)
adds `GeneratorLevelAnalysis` for MC. It does not explicitly assign a nominal
weight index in the inspected configuration. Naming a decoration NOSYS does
not prove which generator weight is nominal or whether the FEB2025 producer
used the same library/configuration. No index, rescaling, absolute value,
sign correction or unity substitution is invented.

The [v1.0.0 release](https://zenodo.org/records/15791092) dates from 2025-07-02,
later than the FEB2025 file tag. The public record's 25 GeV skim differs from
the later 20 GeV skim. Exact producer equivalence remains UNKNOWN even if
later code explains familiar branch names.

## Signed pre-skim aggregation and completeness

The later
[skim source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
searches matching CutBookKeeper histogram names and adds bins 1/2/3 as
generated count, sumW and sumW2 before applying its reconstructed skim. It
copies those direct sums into the flat columns, without a square root.
The preserved public
[dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
instead uses square-root wording for the two sum fields. The contradiction
remains explicit; neither squaring a field nor taking a square root is used
as a repair.

The code skips a ntuple without its expected histogram partner, can add only
inputs for which a matching histogram is obtained, and logs duplicate input
observations. The source is not an executed proof that all FEB2025 jobs were
included once, that all expected histograms were present, or that the chosen
histogram corresponds to the required nominal weight convention. There is no
recovered complete input DID/job manifest, generation log, exact CutBookKeeper
index/definition and aggregate report mapped to this release file.

A verified ROOT size/Adler-32/SHA-256 would establish acquired-byte identity;
it would not establish complete generated-input aggregation or nominal signed
denominator applicability. A native scalar constant matching the table would
likewise be consistency evidence, not independent production completeness.
Generated N, flat-tree entries, inspected or selected counts, partial sumW,
sumAbsW and sumW2 are not interchangeable denominator choices.

## Existing signed observations remain bounded diagnostics

The [Phase 5 weight observations](../metadata/phase5_weight_observations.json)
and [ingredient CSV](../metadata/phase5_weight_evidence.csv) were generated
from preserved Phase 4 V2 CSVs, 9,900 entries per existing DSID, [100,10000).
Exact identity joins and native types/counts/extrema were checked against the
original Phase 4 evidence. These facts remain diagnostic only:

| DSID | Positive / negative / zero generator weights | Bounded signed sumW | Bounded sumW2 | Negative BTAG scalars | Zero PILEUP scalars |
| --- | --- | ---: | ---: | ---: | ---: |
| 343981 | 9886 / 14 / 0 | 281211.1376647949 | 8033225.089416509 | 18 | 89 |
| 346214 | 9885 / 15 / 0 | 37087.79810833931 | 140118.1906686802 | 75 | 93 |
| 423103 | 9900 / 0 / 0 | 9900 | 9900 | 103 | 98 |

Signed counts and moments match the original evidence exactly at parsed
binary values. The observed negative generator weights are preserved and are
distinct from unexplained negative correction scalars. The existing 423103
native filter efficiency 0.000039 differs from the table's 0.0000393; both
remain preserved. H-sample generated sums have rounding-scale differences
from the later table, without proof of the exact producer precision/route.
None of these facts supplies missing 302521 native observations.

The observed SumAbsW, signed effective statistics and cancellation fraction
only characterize these bounded post-skim rows. They do not validate nominal
semantics, generated denominators, acceptance, luminosity, or a physical
generator-weighted comparison. The signs are not discarded and no diagnostic
sum is used to force a normalization.

## Five correction scalars require separate evidence

| Branch | Later source route | Unresolved physical requirements |
| --- | --- | --- |
| `ScaleFactor_BTAG` | Product of retained jets' DL1dv01 Continuous per-jet factors | Exact producer/tagger/CDI/object scope, sentinel validity and uncertainty; negative values are not signed generator weights |
| `ScaleFactor_FTAG` | EventInfo DL1dv01 Continuous event factor | Exact event/object scope and relation to BTAG; do not multiply both without a proven contract |
| `ScaleFactor_PHOTON` | Product of loose ID and loose isolation factors over retained photons | Applicability to this study's retained/leading pair and any future ID/isolation or trigger selection |
| `ScaleFactor_PILEUP` | EventInfo pileup decoration | Exact campaign/configuration/luminosity profile and zero-value validity |
| `ScaleFactor_JVT` | Product over retained jets, excluding -1 in later code | Exact jet/JVT working point, sentinel convention, object/event applicability and uncertainty |

In later
[JetInfo](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0),
the neighboring JVT product excludes a per-jet -1 value, but the BTAG product
has no corresponding exclusion. Sentinel propagation is a plausible source
question, not a demonstrated explanation for the existing negative BTAG
values. The later converter obtains FTAG directly from EventInfo; its relation
to the per-retained-jet BTAG product must be resolved before applying either.

Later
[PhotonInfo](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0)
selects objects through overlap-removal and kinematic decorations before
building its photon product. The Phase 3 study selects its pT-ranked pair;
raw tight-ID/isolation flags remain optional diagnostics. No loose-product
or photon-trigger equivalence is assumed.

The later algorithm config names DL1dv01/Continuous and a 2023 MC20 CDI file.
For DSID 302521 its `getGenerator` mapping passes the string `Powheg+Pythia8`
to `Jets.FlavourTaggingEventSF`, despite the process table naming Pythia8 plus
EvtGen. This is a tool-configuration category in later code, **not evidence
that 302521 was generated with Powheg**, nor proof of calibration applicability
to the FEB2025 file. No GN2 equivalence or official b-tag efficiency is inferred.

All five branches remain **BLOCKED_FOR_APPLICATION**. Negative/zero/unexplained
values are preserved; no absolute, zero or unity replacement is made. Even
positive, finite scalar values do not independently prove validity for the
requested sample, working point, selection or exposure.

## Source versions and required evidence to advance

Preserved local source hashes were rechecked. They identify the inspected
bytes, not official published strong digests or new downloads in this task.

| Preserved official source | Version / local SHA-256 |
| --- | --- |
| `extras/metadata.csv` | v1.0.0; `7cbf4522af6fb108c82be36d72a5d36a38dd126e609c71899b1c2f729d681225` |
| `Root/PhysLiteToOpenData.cxx` | v1.0.0; `d17dd6e26f8217bfd967dd4007cbbe1df6e8f742a8a8ee0b3fec6dfd863d0093` |
| `python/PhysLiteToOpenDataAlgorithms.py` | v1.0.0; `5a56eb88d9beb3c472f21defca8f250a7dd3ca63ef60fe08f56cc8183eaf56c3` |
| `scripts/skimOpenDataNtuples.py` | v1.0.0; `798cc579aaa303be420ca8621d7cb3e1b3ef2cee1f0ecb9d25469a1aba32f6b8` |
| `Root/JetInfo.cxx` | v1.0.0; `01325c175a93676dea65f7946dba486bcc1e84c6f7168e694bc3362c05f3a5b5` |
| `Root/PhotonInfo.cxx` | v1.0.0; `9a59853da9c04a428d1990320b680940480bdf723f8d299689ac3bc26e7a8569` |

The frozen generator job and dependencies must be tied to e4045 and the
release's complete generation/simulation/reconstruction/skim input mapping.
Recover exact nominal weight index/decoration semantics; applicable PMG
metadata version and sigma/filter/decay convention; complete signed nominal
pre-skim N/sumW/sumW2 accounting; exact converter/selection/calibration and
sentinel definitions; and exposure/trigger compatibility with the actual DATA
population. The [luminosity audit](phase5_luminosity_audit.md) remains UNKNOWN
for all five applicable exposure scopes. Current table values and a newly
acquired file cannot replace these independent ingredients.

The existing [normalization contract](phase5_normalization_contract.md) stays
disabled for physical application. Source review, bounded raw reconstruction,
synthetic engineering and DATA-only descriptive diagnostics may proceed under
their own gates. Generator-weighted physical shapes, absolute background
predictions, combined samples and real transfer-factor closure remain blocked
until their corresponding evidence is established. No extra filter/decay
factor, selected-event denominator, SF repair, HH fit or background-readiness
claim is introduced.

## Additive witnessed job and remaining normalization provenance

The root agent subsequently retrieved the exact job file API JSON under its
bounded Windows source ledger. Local decoding independently verifies a
1,422-byte source with SHA-256
`781c937e48b0c4a345952fa0ee856e8b59206d44aed3bb2954c226d39eb6b145`,
matching the API's `content_sha256`. The 2,401-byte API response has SHA-256
`f675347ddc6bd4dd17c5cfa51353af036c9ee29c5b0e8dd0cec1debbe7ae6060`.
The new decoded source stays at
`.local/phase5b_windows_sources_20261012/job302521_at_2ae5d187.py.txt`;
historical snapshots and reports remain unchanged.

The response's repository commit is
`2ae5d187a6036647276a28f7e62b9779edea76dc`, last file-changing commit
`586c7ddeb4f4e6856888ecea663187a9fdaf35e0`, and blob
`9cae92a8f15d26aab84cd11003de15030fb0f56e`. The
[frozen job reference](https://gitlab.cern.ch/atlas-physics/pmg/infrastructure/mc15joboptions/-/blob/2ae5d187a6036647276a28f7e62b9779edea76dc/share/DSID302xxx/MC15.302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.py)
is witnessed current-master content, **not verified e4045 production provenance**.
Its comment/description and configured direct-diphoton processes corroborate
the intended source classification, but no exact generation-to-release
mapping or complete input list was recovered by this response.

The file configures the direct diphoton subprocesses and PhaseSpace mHat
100/160 settings, plus DirectPhotonFilter Ptcut=20000, Etacut=2.7 and NPhotons=2.
It includes the A14/NNPDF23LO/EvtGen common configuration, which requires its
own frozen dependency provenance. It contains no explicit nominal-weight
index, signed aggregate sumW/sumW2, sigma, filter-efficiency value, k-factor,
complete generated event count, reconstructed skim configuration or applicable
SF validity declaration. `minevents=500` in a generation job is a configured
job property; it is not evidence for the release's total generated count or
processing completeness. It does not replace the table's candidate 642,000.

The [filter review](phase5b_generator_filter_review.md) distinguishes generator
mHat settings from a defined saved-truth photon pair. Likewise, seeing two
configured subprocess names does not establish nominal weight semantics or
authorize a signed normalization. The exact e4045 generator release/common
configuration, nominal weight definition/index, PMG metadata applicability,
filter implementation/efficiency and complete pre-skim accounting remain
UNKNOWN. The generated-denominator and calibration guards stay closed.

No extra branching/filter factor, event-weight replacement or source-derived
normalization is applied. All source-request accounting belongs to the root
agent's ledger; this review decodes and checks already acquired bytes only.

## Current physical observation gate

The separately executed bounded access diagnostics finish with
**CONTINUUM_ACCESS = BLOCKED_NETWORK**. The root-owned metadata-only XRootD
probe times out after 15 seconds. Its final receipt at
`.local/phase5b_xrootd_metadata_20261012/audit.json` retains zero ROOT payload
bytes and all previous charges: Phase 5 charged bytes **5,302,259**;
cumulative charged bytes **83,436,281**. Reserved metadata-operation accounting
is not a measurement of XRootD/control wire traffic; the public `root://`
operation makes no TLS assertion.

No physical 302521 `mcWeight`, nominal index, N/sumW/sumW2 scalar, SF value,
entry count or denominator-completeness evidence has been acquired. These
native observations are **NOT_EVALUATED**. The later table candidates and
witnessed job properties retain their documented scope; exact-production
weight/denominator applicability remains UNKNOWN and physical normalization
and all five SF applications remain BLOCKED. No new physical normalization
can be derived from the access failure or the existing other-sample moments.

# Phase 5C MC provenance update

**PROVENANCE_ASSESSMENT = PASS_DOCUMENTATION_REVIEW;
EXACT_FEB2025_PRODUCTION = UNKNOWN;
NOMINAL_GENERATOR_WEIGHT = UNKNOWN;
SIGNED_PRE_SKIM_SUMW_APPLICABILITY = UNKNOWN;
PHYSICAL_NORMALIZATION = DISABLED;
SCALE_FACTOR_APPLICATION = BLOCKED.** Assessment completion means that the
available evidence and remaining gaps have been identified. It does not
mean that a physical normalization ingredient has passed validation.

This additive 2026-10-12 review starts from
`1c7da77fe4c852c929be39b10544220033de9fec`. Historical reports, source snapshots,
selection definitions, event weights and results are preserved. This reviewer
made **zero network requests, Git operations and ROOT event reads**. Evidence
comes from previously acquired official bytes, the frozen Phase 5B generator
job, and existing bounded diagnostic manifests. The separate Phase 5C
documentation-access receipt records six blocked requests with zero received
HTTP body bytes; it supplies no new successful production document.

## Exact input identity and evidence levels

The preserved [CERN record 93922 API](https://opendata.cern.ch/api/records/93922)
identifies this release member:

```text
ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
size: 110755804 bytes
published checksum: adler32:b43248ea
```

The record's `online` annotation identifies a catalog claim, not independently
verified present-day storage reachability. The filename's FEB2025 tag does
not supply a processing date, generator release, input DID list or immutable
producer configuration. No actual 302521 ROOT file, local ROOT SHA-256,
native schema, event count, truth branch or weight observation is available
at this review. Physical input access and native inspection remain **BLOCKED /
NOT_EVALUATED**, respectively. The observed schemas of other DSIDs cannot be
substituted for this file.

The [v1.0.0 metadata table](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0)
documents candidate 302521 values, separated below from their applicability.

| Ingredient | Documented candidate | Exact released-file applicability |
| --- | --- | --- |
| Production / generation labels | ODEO_FEB2025_v0 / e4045 | UNKNOWN complete production mapping |
| Process / generator | QCD direct diphoton; Pythia8 v8.186 plus EvtGen v1.2.0 | Documented classification; exact configuration UNKNOWN |
| Cross section | 18.282 pb | UNKNOWN sigma/filter/decay convention |
| Generator filter efficiency | 0.44191 | UNKNOWN exact filter population and accounting |
| k-factor | 1 | UNKNOWN applicable metadata convention |
| Generated count | 642000 | UNKNOWN complete generated-input coverage |
| Signed generated sumW / sumW2 | 642000 / 642000 | UNKNOWN nominal index, definition, pre-skim scope and completeness |
| Nominal generator weight index | Not established | UNKNOWN |
| Branching-ratio treatment | Not established | UNKNOWN; no added branching factor |
| Object corrections / scale factors | Later code descriptions exist | BLOCKED for physical application |
| Pairwise sample overlap | Not established | UNKNOWN; samples remain separate |

Equality of candidate count, sumW and sumW2 does not prove that the actual
file has unit weights, that a branch is the nominal generator weight, or
that its denominator covers every generated input once. Candidate values
are not silently promoted to a physical normalization contract.

## Frozen job source is identified; production applicability is not

Phase 5B retrieved the job API through mutable `master`; the returned
repository commit freezes the inspected content at
`2ae5d187a6036647276a28f7e62b9779edea76dc`. The last file-changing commit is
`586c7ddeb4f4e6856888ecea663187a9fdaf35e0`, and blob is
`9cae92a8f15d26aab84cd11003de15030fb0f56e`. The
[immutable job reference](https://gitlab.cern.ch/atlas-physics/pmg/infrastructure/mc15joboptions/-/blob/2ae5d187a6036647276a28f7e62b9779edea76dc/share/DSID302xxx/MC15.302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.py)
is witnessed source content, **not verified e4045 production provenance**.
Local base64 decoding independently matches the response's `content_sha256`
and the preserved decoded file.

The job enables `PromptPhoton:ffbar2gammagamma` and
`PromptPhoton:gg2gammagamma`, sets `PhaseSpace:pTHatMin = 18`,
`PhaseSpace:mHatMin = 100.` and `PhaseSpace:mHatMax = 160.`, and configures
`DirectPhotonFilter.Ptcut = 20000.`, `Etacut = 2.7`, `NPhotons = 2`.
It includes `MC15JobOptions/Pythia8_A14_NNPDF23LO_EvtGen_Common.py`.
The exact included configuration, GeneratorFilters implementation, production
release and mapping to the released file have not been established.
`minevents = 500` is a configured job property, not the sample's generated
count or a completeness proof.

The mass-related commands are generator **mHat phase-space settings**. The
inspected file contains no explicit `DirectPhotonFilter` photon-pair mass
predicate. Its textual 100<Mgg<160 description therefore does not identify
the mass of the two highest-pT saved truth photons, a geometrically matched
pair, or the reconstructed leading pair. Exact photon status/origin/barcode
eligibility, count comparison, extra-photon treatment, pair definition,
property units, ordering and boundary comparisons require the applicable
implementation. They remain **UNKNOWN**. No apparent saved-pair mass is
classified as a filter failure from this description alone.

## Nominal weight and signed generated denominator

The [later converter](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0)
copies a float EventInfo decoration `generatorWeight_NOSYS` into `mcWeight`.
The [later algorithm configuration](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/python%2FPhysLiteToOpenDataAlgorithms.py/raw?ref=v1.0.0)
adds `GeneratorLevelAnalysis` for MC, but the inspected configuration does not
explicitly assign a nominal generator weight index. NOSYS names a systematic
decoration context; the name alone does not prove the generator weight choice
or exact FEB2025 implementation. No index, absolute value, sign repair,
rescaling or unity replacement is inferred.

The [v1.0.0 framework release](https://zenodo.org/records/15791092) is dated
2025-07-02, later than the filename's FEB2025 tag. The record describes a skim
requiring at least two photons with pT>=25 GeV; the preserved later skim code
uses `photon_pt >20` and at least two such photons. These definitions are not
declared equivalent. Exact converter/configuration applicability remains
UNKNOWN despite familiar branch names.

The [later skim source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
searches `CutBookkeeper_<DSID>_<six digits>_NOSYS` histograms and directly adds
bins 1/2/3 as count, sumW and sumW2 before its reconstructed skim. It skips a
ntuple with no expected histogram partner and logs duplicate observations.
This is a source-code route, not an executed proof of complete unique input
coverage or of a matching nominal index. The public
[flat-ntuple dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
uses square-root wording for the sum fields, unlike those direct additions.
The discrepancy remains recorded; squaring or taking a square root is not
used to repair a scalar.

Advancement requires the exact producer/release and weight definition, the
complete generated and processed DID/job ledger, applicable CutBookKeeper
names/index/cycle semantics, and an aggregation result proving all required
inputs were included once. File size, Adler-32 and a locally computed SHA-256
would validate acquired bytes, but would not independently establish those
production facts. A constant native scalar agreeing with the table would be
consistency evidence, not completeness proof.

Generated N, flat-tree entry counts, sampled or selected counts, post-skim
sumW, sumAbsW, sumW2 and signed effective statistics are distinct quantities.
None replaces a verified signed nominal pre-skim denominator. Existing
physical generator-weighted shape mode remains blocked until nominal
semantics are verified even if no luminosity scale is applied.

## Sigma, decay, filters and reconstructed support

The later converter initializes `PMGCrossSectionTool` using a resolved
`PhysLiteToOpenData/PMGxsecDB_mc16.txt` and obtains AMI xsec, filter efficiency
and k-factor. The exact FEB2025 database payload/version, sigma convention,
filter population and decay treatment are not established by the later
table. No extra branching ratio is multiplied into a candidate sigma/filter
product without evidence that it is absent from the existing convention.
Direct diphoton production does not authorize importing a Higgs branching
factor; single-H samples likewise need their own decay/filter contracts.

Generation, public-release skim and the unchanged study reconstruction are
different selections. The documented 100-160 GeV generation interval overlaps
the study's inclusive 105<=m_gg<=160 GeV domain, but generator mHat, retained
truth-pair mass and reconstructed mass are different quantities. Detector
response, retained objects and pair changes can cause migration. No source
description measures that migration or proves complete reconstructed support,
particularly at the strict documented generation edge versus inclusive
reconstructed 160 GeV endpoint. No edge correction, outside-window
extrapolation or unfiltered continuum acceptance is introduced.

The [later TruthInfo](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FTruthInfo.cxx/raw?ref=v1.0.0)
retains `TruthPhotons` with pT>=10 GeV and writes n/pT/eta/phi. It provides no
photon status, origin, barcode, mother, energy, filter decision or filter-pair
identifier in that source. `AntiKt4TruthDressedWZJets` are retained at pT>=20
GeV with signed stored mass. Actual 302521 branch availability is unobserved.
Even if its schema eventually matches other samples, a highest-pT saved
truth-pair comparison would be a study-defined diagnostic, not verification
of the generator-filter pair, prompt purity or complete efficiency.

## Corrections and preserved signed observations

| Scalar | Later source meaning | Unresolved application requirements |
| --- | --- | --- |
| BTAG | Product of retained jets' DL1dv01 Continuous per-jet factors | Producer, CDI, object scope, WP and invalid/sentinel behavior |
| FTAG | EventInfo DL1dv01 Continuous event factor | Event/object population and relation to BTAG; possible double counting |
| PHOTON | Retained-photon loose ID and loose isolation product | Study leading-pair/ID/isolation/trigger compatibility |
| PILEUP | EventInfo `PileupWeight_NOSYS` | Campaign, luminosity profile, configuration and validity of zero values |
| JVT | Retained-jet product excluding per-jet -1 in later code | Jet/JVT WP, exact sentinel convention, population and uncertainty |

The [JetInfo source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0)
excludes -1 from JVT multiplication but does not perform the same exclusion
in BTAG. Sentinel propagation is a question for production provenance, not
a proven physical explanation for observed negative BTAG scalars. The
[PhotonInfo source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0)
forms products after overlap-removal and kinematic selections. It does not
establish equivalence to this study's pT-ranked pair or optional tight flags.
Later `getGenerator(302521)` maps to a `Powheg+Pythia8` tool category; that
category is not evidence that this Pythia8/EvtGen sample was generated with
Powheg or that the calibration is applicable to the released file.

The existing [Phase 5 observation manifest](../metadata/phase5_weight_observations.json)
and [ingredient evidence](../metadata/phase5_weight_evidence.csv) preserve
9,900 post-skim entries per existing MC DSID, [100,10000). Their negative
generator counts are 14/15/0 for 343981/346214/423103, negative BTAG counts
18/75/103 and zero PILEUP counts 89/93/98. These are different diagnostics;
unexplained negative correction scalars are not nominal signed generator
weights. Raw signs and values remain unchanged. No sampled sum becomes a
generated denominator and no negative, zero or positive scalar is applied
without its validity contract. No 302521 observation is inferred.

## Overlap and missing components

The same later table describes 423103 DP70_140 as jetjet/gamma+jet with at
least one hard-process **or parton-shower** photon in 70<pT<140 GeV. This is a
photon-pT slice, not a 100-160 GeV mass slice, a complete fake-background model
or a proven disjoint complement to direct diphoton production. Process labels
alone do not demonstrate pairwise physical disjointness.

302520's documented 55-100 GeV generation interval is not a generic replacement
for the target reconstructed window; migration would require measurement.
364352 is a different continuum-generator alternative, not an extra component
to add to 302521 without combination/overlap evidence. A generated mass box
alone cannot prove detector-level migration coverage or resolve alternative
generator overlap. Samples remain separate by default. Prompt/fake origin
partition, complete continuum support, single-H contamination normalization
and the HH signal route are not established by these educational inputs.

Pairwise combination requires the applicable process/filter definitions and
an explicit evidence-backed overlap disposition for every pair, including
continuum, gammajet and any subtracted contaminant. Distinct DSIDs and event
IDs alone are not physical overlap evidence. A synthetic disjoint-sample test
cannot validate those physical dispositions.

## Preserved primary bytes and reproducibility

All hashes below are SHA-256 of the **raw preserved bytes**, with no newline
conversion. They identify inspected evidence, not officially published strong
digests or successful new Phase 5C downloads. Ten prior expected source hashes
and the job API's decoded-content hash were independently rechecked in
`.local/phase5c_review/provenance_sources.json`. Two additional cached primary
snapshots are identified below.

| Preserved source | Raw SHA-256 |
| --- | --- |
| Record 93922 API, 337923 bytes | `750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c` |
| v1.0.0 metadata table | `7cbf4522af6fb108c82be36d72a5d36a38dd126e609c71899b1c2f729d681225` |
| v1.0.0 PhysLiteToOpenData.cxx | `d17dd6e26f8217bfd967dd4007cbbe1df6e8f742a8a8ee0b3fec6dfd863d0093` |
| v1.0.0 algorithm configuration | `5a56eb88d9beb3c472f21defca8f250a7dd3ca63ef60fe08f56cc8183eaf56c3` |
| v1.0.0 skim source | `798cc579aaa303be420ca8621d7cb3e1b3ef2cee1f0ecb9d25469a1aba32f6b8` |
| v1.0.0 JetInfo.cxx | `01325c175a93676dea65f7946dba486bcc1e84c6f7168e694bc3362c05f3a5b5` |
| v1.0.0 PhotonInfo.cxx | `9a59853da9c04a428d1990320b680940480bdf723f8d299689ac3bc26e7a8569` |
| v1.0.0 TruthInfo.cxx | `792543c179d42efa2c10588b5175bd7150c1b9e30cfa2fd7e6e7358d7dd89317` |
| Phase 5B job API JSON, 2401 bytes | `f675347ddc6bd4dd17c5cfa51353af036c9ee29c5b0e8dd0cec1debbe7ae6060` |
| Decoded job source, 1422 bytes | `781c937e48b0c4a345952fa0ee856e8b59206d44aed3bb2954c226d39eb6b145` |
| Preserved flat-ntuple dictionary text | `09997d17b69c871fe46b79faca3c76d5827b99e2df907b403db2b1a7372d0096` |
| Preserved Zenodo v1.0.0 API JSON | `1502296af6f0ea4b214ee3fb5f5eb13f0e35d4708b864e300b0790c473e210bd` |

The original Phase 5 failed access receipt remains historical evidence; its
raw SHA-256 is
`be764a03f335e9cf238b9e8f1f67a8fd82bfa07aeb2ae145f490e8d6547ab134`.
The historical manifests and reports, including
[Phase 5B weight provenance](phase5b_weight_provenance.md) and
[filter review](phase5b_generator_filter_review.md), remain unchanged. Current
network accounting belongs to the root-owned Phase 5C ledger and does not
alter any earlier receipt or retroactively validate its transport.

## Decision and evidence needed next

**MC provenance is assessed with substantial UNKNOWN applicability; physical
normalization stays disabled.** The support request should seek the exact
FEB2025/e4045 production mapping, immutable generator/common/filter sources,
nominal weight definition/index, complete signed pre-skim CutBookKeeper
aggregation, applicable PMG sigma/filter/decay convention, SF calibration and
sentinel contracts, and pairwise overlap rules. Existing precise primary
references above identify the sample and witnessed source; current `master`
code cannot replace exact-production evidence. No broad or unmetered source
retrieval is introduced.

Acquiring and checksum-validating the authorized file would allow staged
native schema and bounded raw-event checks under their own gates; it would
not by itself clear these provenance gaps. DATA-only sideband dependence and
the fixed retrospective folds can continue independently. Neither a small
correlation, a shape comparison, a held-out diagnostic nor a passing
engineering regression supplies MC completeness, physical transfer-factor
closure, a background yield prediction or HH sensitivity. The
[normalization contract](phase5_normalization_contract.md) and
[luminosity audit](phase5_luminosity_audit.md) retain their existing guards.

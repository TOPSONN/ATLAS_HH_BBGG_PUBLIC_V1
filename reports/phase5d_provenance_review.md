# Phase 5D exact-production provenance review

**FEB2025 production applicability = UNKNOWN; nominal generator weight =
UNKNOWN; complete signed pre-skim sumW = UNKNOWN; physical normalization =
DISABLED.** Public documentation identifies the intended sample and later
software behavior. It does not yet establish the complete production contract
of the released 302521 file. This review changes no weights, selections,
historical results or input files.

The preserved baseline is
`ba2ba7d8fbfdf8d54c5f6156a673ee4ac1fb30af`. The independent reviewer rehashed
the previously acquired official bytes on 2026-10-12 UTC. Ten source digests
matched their prior expected values. The local receipt is
`.local/phase5d_provenance_review.json`. This reviewer made zero network
requests, Git operations and ROOT event reads. New Phase 5D bounded metadata
requests and their applicability are recorded separately by the task's
network-accounting owner; they must not be inferred from the older snapshots.

## Evidence classifications

VERIFIED means the stated, narrowly defined fact is witnessed in identified
official source bytes. PARTIAL means some required ingredients are witnessed
but the full physical contract is incomplete. UNKNOWN means an ingredient or
its exact released-file applicability has not been established.
ACCESS_UNVERIFIED means a current source/object could not be successfully
inspected; it does not assert that the source/object is absent or unavailable
to everyone. A source-code fact and its production applicability are reported
separately throughout this review.

## Exact member and release mapping

The preserved [official record 93922 API](https://opendata.cern.ch/api/records/93922)
contains exactly this target member:

```text
ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root
published size: 110755804 bytes
published checksum: adler32:b43248ea
```

Its catalog identity is **VERIFIED** in the previously retrieved metadata,
whose raw SHA-256 is
`750cefd4163a6b62bfa11c5898bd568342180d756fb2f377328065ff8fa69a2c`.
An `online` annotation, HEAD response, file name or checksum header does not
verify present storage readability. The actual file remains NOT_ACQUIRED;
local Adler-32/SHA-256, native schema and 302521 event observations remain
NOT_VERIFIED/NOT_EVALUATED. Other DSIDs' schemas do not establish this schema.

The [v1.0.0 metadata table](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0)
lists the generation tag `e4045`, Pythia8(v8.186)+EvtGen(v1.2.0), 18.282 pb,
filter efficiency 0.44191, k-factor 1, and 642000 for each of generated count,
sumOfWeights and sumOfWeightsSquared. These are **VERIFIED table contents**,
not verified normalization ingredients. The table does not supply an exact
FEB2025 converter commit/configuration, complete input DID/job list, generator
weight index or signed-denominator aggregation record. A generation tag alone
does not identify the complete simulation/reconstruction/derivation campaign
or prove the relation of every input to this release member.

The [Zenodo v1.0.0 framework record](https://zenodo.org/records/15791092) states
publication date 2025-07-02. Its preserved record identifies software version
v1.0.0 and Software Heritage directory
`swh:1:dir:fbb846702bea3cf437704cd6b567822c3b2e1826`. This identifies a later
software archive; neither the date nor a matching branch name establishes
that its source generated the FEB2025-labeled file. Exact producer commit,
release, algorithm options, conditions payloads, skimming/merging scripts and
command lines remain **UNKNOWN**.

### New bounded version-identification evidence

The task's once-only metadata pass successfully acquired the
[official v1.0.0 tag API](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/tags/v1.0.0)
on 2026-10-12 UTC with verified TLS. This newly witnessed tag resolves to
commit `985686c4c272eff6a224b9aea8787513576d9695`, whose `committed_date` is
2025-06-17T12:54:18+00:00. The tag's own `created_at` is null, so its creation
date remains UNKNOWN. This commit date is distinct from the Zenodo
2025-07-02 publication date. Neither establishes the FEB2025 producer.

The bounded [official history query ending 2025-03-01](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/commits?until=2025-03-01T00%3A00%3A00Z&per_page=5)
returned five commits. Its first returned entry is
`0cfc9416d6146ebdb31234f1e486f77abe28aa83`, with `committed_date`
2025-02-15T00:59:01+00:00. This is an immutable **POSSIBLE comparison
candidate** from date-bounded repository history, not the actual production
commit. The query is not a complete campaign history or complete ancestry
audit. Its commit title mentions truth/systematic handling changes; a title
does not substitute for source inspection or production logs.

The independently rehashed raw responses are 994 bytes / SHA-256
`7a0515700e007a11fcd41a6cd77ffa394e21f420e655e16ec5aec9e74f0e76f3`
for the tag and 4143 bytes / SHA-256
`26473d4837ffc102539b08c2ba7466b9f65887591d11d245343178033e46eb92`
for history. Their metered access is recorded in
`.local/phase5d_sources_20261012/audit.json`; no ROOT request or payload is
involved. This improves version identification while leaving exact FEB2025
applicability UNKNOWN.

### Targeted immutable February source comparison

The task acquired all three following source paths once with verified TLS,
each pinned to `0cfc9416d6146ebdb31234f1e486f77abe28aa83`. The reviewer
independently rehashed the received bytes and compared them to the preserved
v1.0.0 sources. No source was edited, imported or executed. The ignored local
comparison and hash receipts are
`.local/phase5d_provenance_candidate_diff.txt` and
`.local/phase5d_provenance_candidate_hashes.json`.

| Pinned official source | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| [Root/PhysLiteToOpenData.cxx](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=0cfc9416d6146ebdb31234f1e486f77abe28aa83) | 16441 | `29d56a2ffe708b3b2578b88ba265763791bf3ab418c46c2c4a3e81c4449797d9` |
| [python/PhysLiteToOpenDataAlgorithms.py](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/python%2FPhysLiteToOpenDataAlgorithms.py/raw?ref=0cfc9416d6146ebdb31234f1e486f77abe28aa83) | 19673 | `ecbc8c3a1ee3fc560c2f92dc9fb08ca201d85aff414c546525199f9dcab79274` |
| [scripts/skimOpenDataNtuples.py](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=0cfc9416d6146ebdb31234f1e486f77abe28aa83) | 28066 | `5cc1084166f3019594697a119b7814679c060ba4727d0c4416e6146a677e50e5` |

The following narrow facts are **VERIFIED source comparisons**, with actual
released-file applicability still UNKNOWN:

| Ingredient | February candidate versus preserved v1.0.0 |
| --- | --- |
| Nominal weight | Both copy `generatorWeight_NOSYS` to mcWeight and add GeneratorLevelAnalysis; neither inspected configuration explicitly supplies a nominal index. |
| PMG scalar route | Both load the named PMGxsecDB_mc16 payload and obtain AMI xsec, filter efficiency and k-factor. Exact applicable payload bytes remain unverified. |
| FTAG/CDI | Both copy event-level DL1dv01 Continuous FTAG and configure the same Continuous WP/CDI path. February has a metadata-driven Sherpa version override; the later source adds the DSID-specific getGenerator mapping. |
| DATA cleaning | February explicitly assigns `.userGRLFiles=GRLs`; that assignment is commented in the later source, which also adds removal of 2016 triggers for a 2015-only run range. Neither establishes the actual released GRL/exposure. |
| GamGam skim | Both count photons satisfying `photon_pt >20` and require at least two; both configure retained photonMinPt=25 GeV. They do not resolve the exact producer's threshold/boundaries or record-description mapping. |
| Cross-section branch | February creates `corrected_xsec`, using `my_total` if present, otherwise xsec times filter efficiency times k-factor. The later source instead writes/redefines separate xsec/kfac/filteff scalars. These are different metadata conventions, so an additional multiplication could duplicate factors. |
| Pre-skim sums | Both add matching histogram bins 1/2/3 before applySkim, skip missing histogram partners and report duplicates after the addition. Neither provides the actual complete unique-input ledger. |
| Input-tag selection | February calls getDSwithProperTags without assigning its returned list; the later source assigns the return and changes priority-tag discovery. Actual input completeness cannot be established from the later code alone. |

The untouched February skim also contains `required = ["directory"` at line
413 with no closing bracket. A narrowly scoped **AST-only** check with local
Python 3.14.2 rejects it with `SyntaxError: '[' was never closed`; the inspected
v1.0.0 skim parses successfully. This is an upstream candidate-source
limitation, not a project CTest result or failed repository regression. No
producer runtime was recreated, and no upstream code was repaired. The local
receipt is `.local/phase5d_candidate_static_review.json`. The actual production
script, revision or local patch is therefore essential evidence; the
date-bounded snapshot is not identified as an executable producer merely from
its date or other matching lines.

These three files do not include the applicable GeneratorFilters
implementation, GeneratorLevelAnalysis weight-selection implementation,
JetInfo/PhotonInfo candidate versions or calibration payload contents.
Consequently their comparison cannot establish the filter implementation,
nominal index, per-jet JVT/BTAG sentinel handling or retained-photon efficiency
contract for the February candidate. Later JetInfo/PhotonInfo behavior below
remains explicitly later-source evidence. No further broad retrieval or
synthetic framework is introduced.

## Generator and filter source

The [302521 job at commit 2ae5d187a6036647276a28f7e62b9779edea76dc](https://gitlab.cern.ch/atlas-physics/pmg/infrastructure/mc15joboptions/-/blob/2ae5d187a6036647276a28f7e62b9779edea76dc/share/DSID302xxx/MC15.302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.py)
is preserved in
`metadata/phase5b_source_evidence/job302521_at_2ae5d187.py.txt`. Its decoded
raw SHA-256 is
`781c937e48b0c4a345952fa0ee856e8b59206d44aed3bb2954c226d39eb6b145`;
the API response's decoded-content digest matches it. This is **VERIFIED
inspected source**, with exact e4045 production applicability **UNKNOWN**.

That source enables `PromptPhoton:ffbar2gammagamma` and
`PromptPhoton:gg2gammagamma`, sets `pTHatMin=18`, `mHatMin=100` and
`mHatMax=160`, includes
`MC15JobOptions/Pythia8_A14_NNPDF23LO_EvtGen_Common.py`, and configures
`DirectPhotonFilter` with Ptcut=20000, Etacut=2.7 and NPhotons=2.
The exact included files, GeneratorFilters implementation, generator release,
HepMC interpretation and production job configuration are not identified by
this one file.

The mHat commands constrain a generator phase-space quantity. The inspected
source does not implement a saved truth-photon pair mass predicate. Its
description cannot establish status/origin/barcode eligibility, strict versus
inclusive comparisons, filter-photon ordering, handling of extra photons or
the relation between filter photons, retained TruthPhotons and the
reconstructed pair. These details require the applicable implementation and
production mapping. The configured `minevents=500` does not mean the sample
has 500 events and does not establish complete input accounting.

The [later skim source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
counts photons with `photon_pt > 20`, whereas record 93922 describes a skim
requiring at least two photons with pT>=25 GeV. The later object configuration
itself sets photonMinPt to 25 GeV. Their interplay is not assumed to prove
the exact released selection or boundary convention. This discrepancy and
all prior selection definitions are preserved rather than resolved by a new
cut. Generator acceptance, public skim and study selection remain distinct.

## Nominal index and signed pre-skim aggregation

The [later converter](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0)
copies float `generatorWeight_NOSYS` from EventInfo into `mcWeight`. The
[later algorithm configuration](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/python%2FPhysLiteToOpenDataAlgorithms.py/raw?ref=v1.0.0)
adds GeneratorLevelAnalysis without an explicit nominal weight index in the
inspected configuration. These are **VERIFIED source facts**. NOSYS identifies
a systematic decoration context; it cannot prove the generator weight index,
weight-name mapping, normalization or applicability to this released file.
Index zero, an absolute value, a unit replacement and a sign correction are
not inferred.

The later skim finds `CutBookkeeper_<DSID>_<six digits>_NOSYS` histograms and
adds bins 1/2/3 directly as count/sumW/sumW2 before its reconstructed skim.
It skips ntuples without a matching histogram partner. Duplicate reporting
occurs after the observed histogram contribution is added. Thus source
presence is not proof that the actual production had complete unique inputs,
the correct bookkeeper cycle/population or a matching nominal index. The
public [flat-ntuple dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
uses square-root wording for its sum fields, which differs from these direct
source additions. That unresolved documentation discrepancy is not repaired
by squaring or taking a square root of a scalar.

The necessary evidence is a production ledger identifying every generated and
processed DID/job, the selected nominal weight name/index, bookkeeper names
and cycle rules, pre-skim population, duplicate/missing-input dispositions,
and a reproducible aggregation with signed sumW and sumW2. All must refer to
the exact file's production. Native branch values agreeing with 642000 would
be consistency evidence, not a proof of completeness. Generated count,
flat-tree entries, sampled/selected entries, post-skim sumW, sumAbsW and sumW2
cannot substitute for signed nominal generated pre-skim sumW.

## Sigma, decay and object corrections

| Requirement | Witnessed evidence | Exact production status |
| --- | --- | --- |
| Converter/configuration | v1.0.0 source and later archived release | UNKNOWN applicability |
| Generation/campaign | e4045 and generator versions in table | PARTIAL; complete input/campaign mapping UNKNOWN |
| Nominal generator index | EventInfo decoration copied to mcWeight | UNKNOWN index and mapping |
| Signed pre-skim sumW | Candidate 642000; later histogram aggregation route | UNKNOWN definition and complete aggregation |
| Generator filter | Frozen job properties and generator mHat settings | PARTIAL; implementation and applicability UNKNOWN |
| Cross section | Candidate 18.282 pb; later PMGCrossSectionTool route | UNKNOWN applicable convention/database payload |
| Filter efficiency | Candidate 0.44191 | UNKNOWN applicable filter population/accounting |
| Branching ratios | No released-file convention established | UNKNOWN; no additional factor applied |
| Photon corrections | Later loose ID/loose isolation retained-photon product | UNKNOWN applicability/object population |
| JVT corrections | Later retained-jet product excludes per-jet -1 | UNKNOWN applicable WP/sentinel/validity contract |
| BTAG/FTAG corrections | Later continuous per-jet product and event factor | UNKNOWN applicability/overlap/double-counting contract |

The converter uses PMGCrossSectionTool with a resolved
`PhysLiteToOpenData/PMGxsecDB_mc16.txt`. Its exact FEB2025 database bytes,
cross-section/filter/decay convention and source population are unresolved.
No sigma times filter-efficiency product is applied. No extra branching ratio
is multiplied without proving it is absent from the applicable convention;
a direct diphoton sample does not authorize a Higgs branching factor.

The later algorithm explicitly configures DL1dv01 Continuous with CDI
`xAODBTaggingEfficiency/13TeV/2023-22-13TeV-MC20-CDI-2023-09-13_v1.root`.
[JetInfo](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0)
multiplies retained jets' DL1dv01 factors into BTAG and excludes -1 only from
the JVT product. The converter independently copies event-level FTAG.
Multiplying BTAG and FTAG together could double count; no such multiplication
is authorized. The correction's generator category `Powheg+Pythia8` for
302521 is a tool configuration category and does not establish that the
physical sample was generated with Powheg.

[PhotonInfo](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0)
forms loose ID and loose isolation products for photons passing retained
object and overlap-removal selections. They do not establish a correction
for the study's two leading photons, a tight working point or diphoton
trigger. Missing/invalid/sentinel behavior, negative BTAG observations and
zero PILEUP values require exact-production validity contracts. Raw signs
and values are preserved. None is treated as a nominal generator-weight sign.

The [later TruthInfo](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FTruthInfo.cxx/raw?ref=v1.0.0)
stores selected photon n/pT/eta/phi, without status, origin, barcode, parent
or filter-pair identification in that source. A highest-pT retained truth-pair
diagnostic would not independently establish prompt purity or filter closure.
Actual 302521 truth branches have not been observed. Disjoint prompt/fake
components, continuum coverage and sample overlap remain separate missing
contracts; 423103, 302520 and 364352 are not automatically interchangeable or
additive to 302521.

## Rehashed primary sources

Raw SHA-256 identifies the exact inspected local bytes, including their
original line endings. These are local strong digests, not new official
checksums or proof that a tagged source produced the target file. Versioned
source URLs above are accompanied by these preserved-byte identities.

| Source | Raw SHA-256 |
| --- | --- |
| v1.0.0 metadata.csv | `7cbf4522af6fb108c82be36d72a5d36a38dd126e609c71899b1c2f729d681225` |
| v1.0.0 PhysLiteToOpenData.cxx | `d17dd6e26f8217bfd967dd4007cbbe1df6e8f742a8a8ee0b3fec6dfd863d0093` |
| v1.0.0 PhysLiteToOpenDataAlgorithms.py | `5a56eb88d9beb3c472f21defca8f250a7dd3ca63ef60fe08f56cc8183eaf56c3` |
| v1.0.0 OpenDataNtupler.py | `a9db065388e2ab43d8a3fb68cc3c258265f2e716e12a8b193bb29e08cc468c9e` |
| v1.0.0 skimOpenDataNtuples.py | `798cc579aaa303be420ca8621d7cb3e1b3ef2cee1f0ecb9d25469a1aba32f6b8` |
| v1.0.0 JetInfo.cxx | `01325c175a93676dea65f7946dba486bcc1e84c6f7168e694bc3362c05f3a5b5` |
| v1.0.0 PhotonInfo.cxx | `9a59853da9c04a428d1990320b680940480bdf723f8d299689ac3bc26e7a8569` |
| v1.0.0 TruthInfo.cxx | `792543c179d42efa2c10588b5175bd7150c1b9e30cfa2fd7e6e7358d7dd89317` |
| Zenodo 15791092 API record | `1502296af6f0ea4b214ee3fb5f5eb13f0e35d4708b864e300b0790c473e210bd` |
| Flat-ntuple dictionary text | `09997d17b69c871fe46b79faca3c76d5827b99e2df907b403db2b1a7372d0096` |

The earlier [Phase 5C provenance review](phase5c_mc_provenance_update.md),
[normalization contract](phase5_normalization_contract.md), physical filter
review, luminosity audit and weight observations remain unchanged.

## Decision and next evidence

**GO:** complete the [English support draft](phase5d_cern_support_email.md)
with the exact object and production questions, preserving it UNSENT. Sending
requires separate user authorization. The historical network observations
support a transport-support request and do not identify the failure's cause.

**CONDITIONAL:** a supported official access procedure could enable the
previously authorized member's gated checksum/native-schema/raw-event
inspection with all historical budget charges carried forward. This is not
permission to retry failed routes or to acquire a research sample. Native
intake alone would not establish complete production provenance.

**STOP:** absolute MC normalization, generator-weighted physical shape claims,
efficiency corrections, physical background closure/prediction and HH fits
until their matching physical inputs and contracts are verified. The next
provenance milestone is an official exact-production mapping plus a complete
nominal signed pre-skim aggregation, rather than additional synthetic tests.

This is a documentation assessment. It claims no new CTest execution, physical
schema result, unchanged-format production equivalence or calibrated HH
readiness. Research-format alternatives require their own explicit candidate,
toolchain, provenance and download-authorization gates.

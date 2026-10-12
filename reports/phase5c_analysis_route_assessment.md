# Phase 5C analysis-route assessment

Project: ATLAS_HH_BBGG_PUBLIC_V1. Assessment date: 2026-10-12.

**Recommendation: GO for the existing bounded, raw GamGam methods study;
CONDITIONAL for a separately scoped public PHYSLITE pilot; STOP for an
official HH result, calibrated background model or HH sensitivity claim
with the presently verified inputs.** The richer research format provides
documented routes to several missing fields. It does not establish that an
appropriate HH signal, exact calibrations, usable exposure or full statistical
model is public and applicable to this project.

This is a source-and-evidence assessment. No dataset, container, package or
calibration was downloaded or installed; no ROOT event, fit, new selection,
normalization or reconstruction was executed. Existing ROOT 6.40.04 / C++20,
data, selection definitions and historical results remain unchanged.

## Evidence date and status

The research conclusions below use official raw responses preserved during
Phase 0 on **2026-10-09**, rehashed locally for this review. They are historical
documentation and index evidence, not a successful current storage test or
a physical research-file inventory. Root-led Phase 5C refresh made six
one-time, capped requests to the exact official documentation endpoints.
All returned `URLError` before an HTTP body; no failure cause or HTTP status
is inferred. **CURRENT_DOCUMENT_ACCESS = UNVERIFIED**. These failures do not
prove that the documents or research files are unavailable.

The new receipt is `.local/phase5c_sources_20261012/audit.json`, raw SHA-256
`06ca8e5342a242fffc30141a1b218dc5a3a937b4dd26fda2a26833a6c43d64ba`.
It records zero new body bytes, 393,216 reserved-operation charged bytes,
5,695,475 Phase 5 charged bytes and 83,829,497 cumulative charged bytes,
with prior receipts retained. These are conservative application accounting,
not measured wire traffic. No retries or research ROOT requests were made.
This reviewer makes no network requests.

`GO` means the stated, limited use is supported by the present evidence.
`CONDITIONAL` means a plausible route has specific unclosed gates. `STOP`
means the proposed claim or operation would cross those gates with the
currently verified inputs. None means official ATLAS physics approval.

The [Phase 0 verdict](../note/phase0_feasibility.md) remains PARTIAL. Later
physical GamGam schema/reconstruction evidence refines that historical audit
without rewriting it: [DATA schema](phase1_schema_validation.md),
[bounded weight observations](../metadata/phase5_weight_observations.json),
[luminosity audit](phase5_luminosity_audit.md), and
[Phase 5B continuum gate](phase5b_continuum_schema.md). In particular,
302521 is still BLOCKED_NETWORK with native observations NOT_EVALUATED;
metadata identity is not an acquired input.

## Format and coverage comparison

The public [GamGam DATA record 93915](https://opendata.cern.ch/record/93915)
and [MC record 93922](https://opendata.cern.ch/record/93922) describe
2015-2016, 13 TeV educational flat ntuples with a two-photon skim. The
existing DATA input is one period-D file, not all data in the release.
Actual native readers support its RVec collection types; the scalar/vector
schema checks do not attest exact FEB2025 producer or detector calibration.

The preserved [research umbrella record 80020](https://opendata.cern.ch/record/atlas-80020)
describes 2015-2016, 13 TeV DAOD_PHYSLITE collision and MC collections,
Athena Release 22 reprocessing and MC20a simulation. Its usage guidance
explicitly allows direct ROOT/uproot use for simple studies and secondary
ntuples with systematic uncertainties through ATLAS AnalysisBase. The
[format overview](https://opendata.atlas.cern/docs/documentation/data_format/physlite/)
describes calibrated objects and lower-threshold information. These are
documented capabilities, not executed compatibility or calibration checks.

Neither specified release supplies the journal's full 2015-2018 Run 2 and
2022-2024 Run 3 data combination. The public 2015/2016 coverage descriptions
give approximately 3.2/33 fb^-1 at release level; neither quantity is the
effective exposure of the project's period-D bounded rows. A format change
cannot extend the release to the journal's 308 fb^-1 population.
[Research coverage](https://opendata.atlas.cern/docs/data/for_research/pp_data),
[journal reference](https://doi.org/10.1016/j.physletb.2026.140280).

## Capability matrix

The research entries in this table are **catalogue-level evidence**. Native
branches, units, decorations, links and tool compatibility must be checked
in each acquired DATA/MC production. Source snapshots and hashes are below.

| Requirement | Existing educational GamGam route | Public research PHYSLITE route | Gate consequence |
| --- | --- | --- | --- |
| Photon ID and isolation | Native loose/tight flag and kinematic fields are retained. Tight flags remain optional diagnostics in the unchanged study. The later converter's loose-ID/isolation product is not a validated correction for a leading pair or a future tight selection. | `AnalysisPhotons` catalogue includes `DFCommonPhotonsIsEMLoose`, `DFCommonPhotonsIsEMTight`, cut bits, cleaning and isolation variables. Exact object/ID/isolation tools and uncertainties must match production and the proposed study. | Raw diagnostics GO; calibrated tight-photon efficiency CONDITIONAL in research, blocked in current physical model. |
| Photon calibration | Numerical unit consistency and mass closure do not validate detector response, scale or resolution corrections. Exact FEB2025 producer equivalence remains UNKNOWN. | Format documents calibrated objects, but recalibration/uncertainty support must be established with the applicable public CP tools and configuration. Stored objects do not permit arbitrary new photon reconstruction. | Separate schema/units and calibration gates; no calibration PASS from a format label. |
| Jets | Existing jet four-vectors support inclusive leading-jet kinematics. No validated b-jet identity is assigned by the current selection. Reduced object acceptance/skim cannot recover discarded objects. | `AnalysisJets` catalogue includes kinematics, cleaning/JVT-related information and `btaggingLink`. Applicable collection definition, calibration, overlap removal and uncertainty route still need a physical/tool audit. | Inclusive kinematics GO within existing scope; calibrated jet study CONDITIONAL. |
| B-tagging working point and flavour | `jet_btag_quantile` exists natively, but exact production, thresholds/WP, CDI and negative BTAG scalar validity are unresolved. Supplied truth-jet directions do not establish b flavour. | Catalogue contains `BTagging_AntiKt4EMPFlow` DL1dv01 pb/pc/pu scores, jet flavour labels and links. These offer a possible documented-WP/flavour route, not a validated efficiency or the journal's GN2 selection. | Official WP/efficiency STOP now; research WP study CONDITIONAL on exact tool/CDI/sample evidence. |
| Photon truth and ancestry | Inspected MC files provide truth photon count and pT/eta/phi. Existing associations are study-defined geometry; prompt/Higgs origin and a generator-filter pair are not inferred. 302521 truth is NOT_EVALUATED. | Catalogue documents reconstructed photon `truthOrigin`, `truthType`, `TruthLink` and `truthParticleLink`; `TruthPhotons` includes barcode, PDG/status, classifier fields and parent/child or vertex links. Availability and link validity are per-MC-file questions; MCTC code definitions and an explicit eligibility rule are required. | Potentially addresses origin questions; no prompt/HH purity PASS before native truth and semantics checks. |
| Truth jets | Direction-only association preserves signed truth mass without inventing energy or flavour. | Catalogue lists `AntiKt4TruthDressedWZJets` labels, ghost b/c-hadron counts and parton/flavour information. This is not an automatic b-jet matching definition. | Conditional study definition and native inventory; truth labels are not a tagger efficiency measurement. |
| Trigger | Flat `trigP` is a later-source single-photon summary, not a diphoton pass/prescale/efficiency contract. | Catalogue includes `AnalysisTrigMatch_HLT_g35_loose_g25_loose` and other photon match collections. A match alone is not a pass decision or trigger exposure; menu, decisions, prescales, matching and corrections remain separate requirements. | Diphoton-calibrated comparison STOP now; research route CONDITIONAL. |
| GRL and luminosity | Native period-D inventory lacks an established LB/GRL/prescale/livetime recipe. All five exposure scopes in the luminosity audit remain UNKNOWN. Event-count fractions are not luminosity fractions. | `EventInfo` catalogue supplies run/lumiBlock and data-quality information, making GRL matching a plausible route. The official limitations require a GRL. Exact accepted runs/LBs, released-file completeness and trigger-effective exposure still need external metadata and validation. | Research may close some exposure gaps; it does not supply a numerical luminosity from event counts alone. |
| Generator weights and normalization | Three preserved 9,900-row samples have signed diagnostic moments; negative generator weights and negative BTAG factors remain separate. Exact nominal semantics and complete pre-skim signed sums are unresolved. No 302521 native observations exist. | Catalogue has `mcEventWeights` nominal/variations; public metadata documents sigma/filter/k and generated sums. Exact index/names, production tags, complete input aggregation, decay convention and overlap disposition must still match the selected sample. | Normalization remains BLOCKED until all ingredients close; richer weight vectors are not an approved denominator. |
| Detector/theory systematics | Limited exported branches and nominal scalar products do not provide the complete nuisance model for a new tight-photon/b-tag/trigger analysis. | Umbrella lists nominal and variation collections; AnalysisBase is documented for systematic secondary ntuples. Official limitations warn that some necessary variations/signals are unreleased. | Broad research workflow CONDITIONAL; complete HH systematics UNKNOWN. |
| HH signal MC | Current ggF/VBF single-H samples are not HH. No explicit matching HH->bbgg process was identified in the previously inspected complete GamGam names/metadata. | No explicit HH name was found in the preserved Higgs nominal/variation index names. That is a scoped index observation; availability of an applicable HH signal, couplings and variations is not established globally. | HH efficiency, sensitivity or limits STOP with present verified inputs. |
| Statistical model | Raw selected counts and distributions do not constitute a physical HH likelihood. | A research event format does not provide the journal's categories, trained classifiers, correlated nuisance model or workspace. HEPData/model attachment access remains independently unverified. | Official HH reproduction STOP; do not equate event-format richness with complete statistical inputs. |

These conclusions use the
[PHYSLITE catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html),
[research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp),
[MC metadata guidance](https://opendata.atlas.cern/docs/data/for_research/metadata),
[sample-combination guidance](https://opendata.atlas.cern/docs/data/for_research/evgen_collections),
and the [exact-production weight review](phase5b_weight_provenance.md).
An absent field in the inspected flat schema is not a claim about all ATLAS
formats; a documented research field is not a claim of native presence.

## Software, storage and compute implications

The present flat-ntuple study uses the existing conda ROOT 6.40.04 / C++20
environment and native readers. Keep it intact. The research umbrella allows
simple ROOT/uproot reads, so an inventory or primitive kinematic pilot does
not automatically require a full calibrated analysis stack. Resolving xAOD
ElementLinks, using the object model, CP calibration/efficiency tools and
systematic processing requires a demonstrated compatible tool environment.
The current conda ROOT build alone is not evidence for that compatibility.

The preserved public
[PhysLiteToOpenData v1.0.0 README](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/README.md/raw?ref=v1.0.0)
provides an AnalysisBase 25.2.40 setup example and Docker/Podman alternatives.
This is evidence that such workflows are documented, **not** a verified
current research-release choice or a requirement to replace ROOT 6.40.04.
A future calibrated pilot should pin an applicable AnalysisBase release,
source commit, image digest or CVMFS setup and its own bundled compiler/ROOT.
Use a separate environment/process; do not mix its dictionaries/libraries
into the existing conda runtime. No container/tool installation is authorized
or performed by this route assessment.

The format's published targets of roughly 10 kB/data event and 12 kB/MC event
are design figures, not measured local disk usage or a download estimate.
The preserved umbrella index aggregates **71,749,688,366,060 bytes** across
all collision and MC collections; that is neither a minimum pilot size nor
collision-only storage. Cache space, exact selected file bytes, container
layers, calibration payloads, outputs and logs must be budgeted separately.
No measured CPU-time, memory requirement or container size is available here.

Two scientifically relevant **single-H** entries in the preserved
[Higgs nominal record 80012](https://opendata.cern.ch/record/80012) illustrate
the scale of real research inputs. They are not an approved download list
and are not HH signals:

| Cached process index | Published member filename | Cached member bytes / Adler-32 |
| --- | --- | --- |
| `PowhegPythia8EvtGen_NNLOPS_nnlo_30_ggH125_gamgam` | `mc20_13TeV:DAOD_PHYSLITE.38191914._000036.pool.root.1` | 1,929,286,284 / `4444ddc1` |
| `PowhegPy8EG_NNPDF30_AZNLOCTEQ6L1_VBFH125_gamgam` | `mc20_13TeV:DAOD_PHYSLITE.38191539._000052.pool.root.1` | 785,967,187 / `70fd7bae` |

Each exceeds the existing 128 MiB Phase 5 cap and 256 MiB cumulative cap even
before prior charges. The cached index alone does not bind every physical
production tag, nominal weight convention or calibration. A smaller
`gamstargam`, WW or unrelated process is not a substitute for the desired
gamgam study. The compatible prompt-continuum research file/production and
its size have not been established in this assessment. Fresh metadata must
select the correct process/campaign before acquisition is considered.

## Route decisions

| Route and exact use | Decision | Reason and required next gate |
| --- | --- | --- |
| Existing GamGam DATA-only counts, bounded raw shapes and numerical/schema regressions | **GO** | Preserve the current selection and diagnostic scope. Do not assign a physical luminosity, flavour tag or official photon efficiency. |
| Recover the already approved GamGam 302521 member for raw continuum/schema/filter questions | **CONDITIONAL** | Network/access gate remains blocked. Require an approved metered acquisition, published integrity checks and new native evidence. Access success would not close exact-production normalization. |
| Existing GamGam absolute DATA-MC model, official b-tag efficiencies or HH interpretation | **STOP** | Exact calibration/WP, exposure, weight/denominator applicability, coverage and HH signal are not established. Synthetic or numerical PASS does not close them. |
| Metadata-only public research suitability audit | **GO** | Inspect bounded official indices/docs, record exact versions/hashes and select physically relevant candidate roles. No research ROOT download is part of this assessment. |
| One DATA plus one physically compatible research-MC schema/truth pilot | **CONDITIONAL** | Fresh identities and exact bytes, separate user-approved acquisition/storage budget, compatible tools and safe native schema/links/units checks are required. It is a pilot, not a complete physics model. |
| Separately defined calibrated public-research bbgg-like methods study | **CONDITIONAL** | Close photon/jet/WP/trigger/GRL, weights, overlap, uncertainty and sample-coverage gates under a pinned public workflow. State deviations from the publication. |
| Reproduce the journal's official HH result, full likelihood or coupling limits | **STOP** | Full data population, appropriate HH signal/coupling samples, analysis corrections/categories and complete statistical inputs are unverified or outside these specified releases. |

The recommended migration is therefore **documentation first, then a bounded
native pilot under a separate approval**, while retaining the existing flat
results for comparison. Migration is useful only if it demonstrably closes
specific missing ingredients. A failed storage route can also affect research
files on the same public infrastructure; a new format does not prove access
will work.

The scoped HH index assessment interprets process names, rather than using
a substring count as a physics classifier. The 94 nominal and 55 variation
index names include `PhH7` generator abbreviations and a `tautauhh` decay
label; case-insensitive `HH` matches in those strings are not evidence of
Higgs-pair production. No explicitly matching HH->bbgg input is identified
by this review. Requesting or locating an applicable public HH sample remains
a separate evidence task, not a global absence claim.

## Bounded migration gates

1. Define an independent study goal and exact missing ingredient, such as
   prompt-origin diagnostics or a documented DL1d working point. Preserve
   the existing inclusive-jet/raw-photon study as a distinct result.
2. Refresh bounded official research metadata. Record DSID/process, complete
   production/campaign tags, nominal/alternative role, generator filters,
   published member path/bytes/checksum and metadata provenance. Identify a
   physically appropriate continuum and single-H candidate separately;
   verify an HH signal only if an HH objective is proposed.
3. Obtain explicit approval for the exact research file(s), storage/tool
   footprint and new transfer budget. Carry historical charges forward.
   No remote ROOT reads, partial byte transport or sample substitution are
   introduced as an unmetered workaround.
4. In a separate compatible environment, inventory native metadata first:
   trees/aux stores, types, decorations, link targets, input checksums and
   file references. Then inspect small explicitly recorded entry ranges
   for identity, collection lengths, finite kinematics, units and link
   validity. Do not assume flat names, GeV conversion or MCTC categories.
5. Validate one intended public tool/selection contract at a time: photon
   ID/isolation/uncertainties; jet calibration/JVT/overlap removal; b-tag
   scores/WP/CDI/flavour; trigger decisions/menu/matching/corrections; GRL
   and accepted-run/LB exposure. Preserve raw observations and invalid or
   sentinel values; do not repair them with absolute values or unity.
6. Establish exact nominal generator weight, complete signed pre-skim sums,
   sigma/filter/k/decay conventions, production completeness and explicit
   sample overlap. Only then assess a physical normalization or uncertainty
   model. Selected/post-skim moments and event fractions remain diagnostics.
7. Stop a physics claim at any unclosed gate. Request specific missing public
   sample/provenance information through official channels if needed; this
   assessment does not send a request or propose local production of a
   guessed ATLAS-compatible signal.

The official limitations explicitly exclude complete tracks, clusters and
particle-flow inputs and restrict nonstandard object reconstruction, new
jet collections/grooming and custom heavy-flavour/photon reconstruction.
They also warn of unreleased signal/systematic samples and fast-simulation
electron/photon calibration limitations. Respect those boundaries rather
than treat PHYSLITE as raw detector data. A documented MC truth or flavour
label cannot independently validate reconstruction efficiency or the
publication's GN2 selection.
[Official limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp).

## Preserved primary-source registry

These **raw-byte SHA-256 hashes were rechecked locally**. HTML `.txt`
derivatives were used for convenient reading; the hashes below identify
the retained raw responses. They are local provenance hashes, not official
published strong digests. The mutable pages were acquired 2026-10-09;
unchanged bytes do not establish current content or native data availability.

| Official source | Preserved raw path | Local raw SHA-256 |
| --- | --- | --- |
| [Research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp) | `.local/phase0_sources/research_limitations_pp.response` | `8d888a6b77ac318b7ba2224b136d85d26e849a9fa250137c3b6d3c1f1670ab68` |
| [PHYSLITE format](https://opendata.atlas.cern/docs/documentation/data_format/physlite/) | `.local/phase0_sources/physlite_details.html` | `366783dfaa1a3951ea7b291c201c9bfaba440009d49312117aca26e21bfa15a5` |
| [pp variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html) | `.local/phase0_sources/physlite_pp_variables.html` | `4dfb10d27f5132f1dec370f3b9df4d0231af800b67a1a9a8227b86b7c3d42abb` |
| [Research coverage](https://opendata.atlas.cern/docs/data/for_research/pp_data) | `.local/phase0_sources/research_pp.html` | `c5abce7331a9e58dcabd09a6b99b1cc9d106a7ca4bfc1fcef7f0476d5cb1eaff` |
| [MC metadata](https://opendata.atlas.cern/docs/data/for_research/metadata) | `.local/phase0_sources/research_mc_metadata.html` | `b24cebfeb808e8764df4fbfbc4864cc33ed8a3070f57a7317831505cfdb0c9cd` |
| [Sample combination](https://opendata.atlas.cern/docs/data/for_research/evgen_collections) | `.local/phase0_sources/research_sample_combination.response` | `6af64a96ebf7e0e8ddec915d50967b9f85361b502d3531f647c5e6a1d3fdeefd` |
| [Research umbrella API](https://opendata.cern.ch/api/records/atlas-80020) | `.local/phase0_sources/opendata_80020_json.json` | `42127360b8271f7f6ed26ab78b92eea8011b2229f6695f5f912bd643a7220912` |
| [Higgs nominal API](https://opendata.cern.ch/api/records/80012) | `.local/phase0_sources/opendata_80012.json` | `d9338d0fed6eb83feb29735855531390657caec73ee6f2ba4b7df8e693515fff` |
| [Higgs variations API](https://opendata.cern.ch/api/records/80013) | `.local/phase0_sources/opendata_80013.json` | `94f5b798fc36f6edff7cdf05186cf96dbbd196fc16db52e92b3fc5399eb7bb94` |
| [Converter README v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/README.md/raw?ref=v1.0.0) | `.local/phase0_sources/framework_README.md.txt` | `49cb0542fd554aaa1c2afa3b070204faa11aa881d33526aa304065107f9c7c6c` |

The current report is a conditional route decision using those witnessed
sources. No research acquisition, applicable HH package, GRL/luminosity,
calibration, uncertainty or normalization gate is upgraded by this review.

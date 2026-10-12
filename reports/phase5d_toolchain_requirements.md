# Phase 5D ROOT and research-toolchain requirements

Project: ATLAS_HH_BBGG_PUBLIC_V1. Assessment date: 2026-10-12.

**The existing ROOT 6.40.04 / C++20 environment can retain the educational
native readers and can support a conditional research metadata/primitive
kinematics pilot. It is not a verified ATLAS xAOD or CP-tool installation.**
No research ROOT file, AnalysisBase release, container or calibration package
was downloaded, installed or executed for this assessment. No existing
environment or build configuration was changed.

Evidence classifications concern the exact assertion: **VERIFIED** means
directly supported within the stated scope; **PARTIAL** means documented
components exist but applicability has not been demonstrated; **UNKNOWN**
means the needed fact is not established; **ACCESS_UNVERIFIED** means current
retrieval was unsuccessful or not performed. A verified documentation statement
does not establish native presence or working tools for a candidate file.

## Operations and their separate requirements

| Operation | Existing ROOT 6.40.04 / C++20 route | When an ATLAS software stack is needed | Current disposition |
| --- | --- | --- | --- |
| A. Metadata/schema inventory | Local READ-mode key/tree/branch/type inspection; bounded metadata only; retain class names and unresolved dictionaries. Existing native GamGam RVec readers are physically verified for their audited inputs. | Listing stored names does not require constructing all xAOD objects. Instantiating an object with an unresolved class, external store or unsupported streamer must stop; do not treat missing dictionaries as an empty collection. | GamGam inventory VERIFIED; research inventory PARTIAL until a separately approved physical file is checked. |
| B. Primitive kinematics | Read independently supported numeric split aux branches, check native type and lengths, units, finite values and energy/mass convention, then construct numerical four-vectors. The umbrella explicitly permits direct ROOT/uproot simple studies. | xAOD tools are not automatically required for a plain numeric branch. They become necessary if the intended inputs can only be obtained through xAOD interfaces or transformations. | Conditional research pilot; stored calibrated-object labels do not validate an arbitrary new selection or calibration. |
| C. ElementLinks and decorations | Primitive decoration arrays can sometimes be read directly if their stored type is supported. An ElementLink representation is not an object association until its target and index are resolved and validated. | Compatible xAOD dictionaries, aux-store interfaces, object containers and event-store context are required for xAOD-native link/decorated-object access. Use an applicable AnalysisBase stack for this planned route; another independently verified implementation would need its own evidence. | xAOD-native research access UNKNOWN in the current conda runtime. Never load an arbitrary release's libraries into it. |
| D. Calibration and efficiency | Stored nominal kinematics can be described numerically. ROOT alone does not supply ATLAS calibration/efficiency tools, configuration, payloads or corrections appropriate to the selected campaign. | Applicable AnalysisBase CP tools and exact public photon, jet/JVT, flavour-tagging, pileup, event-cleaning/GRL and trigger configuration/payloads are required for the calibrated route. | PARTIAL documentation; exact release, corrections and candidate applicability remain unverified. |
| E. Systematic processing | Numeric variation branches can be inventoried if present. A nominal scalar or raw branch collection does not specify a nuisance model. | Applicable CP algorithms/systematics service, versioned payloads and the required nominal/variation samples. Record supported variations and missing sources; process object/event correlations consistently. | Research umbrella documents AnalysisBase secondary ntuples with systematics; complete bbgg/HH coverage UNKNOWN. |

The [research umbrella](https://opendata.cern.ch/record/atlas-80020) explicitly
distinguishes simple direct ROOT/uproot studies from secondary ntuples using
AnalysisBase with systematics. The [PHYSLITE variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html)
documents `ElementLink<DataVector<...>>` fields and nested trigger-match links.
These observations justify the separation above; they do not establish a
successful native research read in this workspace.

The freshly retrieved official [PHYSLITE tutorial](https://opendata.atlas.cern/docs/tutresearch/physlitetut)
documents direct uproot/awkward inspection, records, basic selection and overlap
removal, using a top-quark example. It explicitly directs the CP-algorithm/
NTuple route to AnalysisBase. This strengthens the workflow separation; it
does not validate the project's native C++ reader, a photon calibration tool
or an HH configuration. No tutorial notebook was executed.

## Public research release example and unresolved applicability

**DOCUMENTED_RESEARCH_ANALYSISBASE_EXAMPLE = 25.2.2; EXACT_CANDIDATE_TOOLCHAIN
APPLICABILITY = UNKNOWN.** Fresh official research
[container guidance](https://opendata.atlas.cern/docs/tutresearch/containers)
explicitly demonstrates `gitlab-registry.cern.ch/atlas/athena/analysisbase:25.2.2`
through the public minimal `setupATLAS` script. This is a research-specific
documented starting point, rather than borrowing a later educational converter
release. It is not an executed or production-specific compatibility guarantee:
image digest, actual platform/compiler/ROOT and applicable payloads remain
unverified. No script or image was downloaded or run.

The preserved research umbrella
identifies Athena Release 22 reprocessing and MC20a; that is production history,
not a directive to run an arbitrary AnalysisBase 22 release. The preserved
public research pages link the ATLAS analysis software tutorial, but the
applicable, tested release for this exact open-data production has not been
established by those snapshots.

The versioned [PhysLiteToOpenData v1.0.0 README](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/blob/v1.0.0/README.md)
shows **AnalysisBase 25.2.40** and a test production
`mc20_13TeV.700322.Sh_2211_Zee_maxHTpTV2_CVetoBVeto.deriv.DAOD_PHYSLITE.e8351_s3681_r13167_p5855`.
This is VERIFIED as a later educational-converter example. It is **not adopted
as a supported research release** and does not attest FEB2025 converter
provenance, the candidate files or an HH analysis configuration.

Before installation approval, obtain a public recommendation or an official
tested example binding a release to the chosen research production and physics
tools. Pin the release plus source configuration commit, platform/compiler/ROOT
identities, immutable image digest if applicable, payload versions and exact
input tags. A mutable container `master` tag is not a reproducible runtime.
If this cannot be established, stop the calibrated pilot at this gate while
retaining the primitive-schema option.

The newly retrieved [CP algorithm introduction](https://atlas-software.docs.cern.ch/analysis/analysis_tutorial/AnalysisSWTutorial/cpalg_intro/)
documents the current recommended CP-block configuration, YAML and `CPRun.py`
steering in EventLoop/AnalysisBase or Athena. These are current tutorial
mechanisms; **their presence in the example 25.2.2 image is not assumed**.
Select configuration interfaces supported by the eventually pinned release.
Its links to protected CP recommendations do not establish that all required
photon/b-tag/trigger recommendations and payloads are publicly usable.

Fresh official [uncertainty guidance](https://opendata.atlas.cern/docs/documentation/systematics)
documents tool-driven calibration/efficiency uncertainties, alternative
generators and internal weight variations. It also emphasizes retaining
correlations for statistical interpretation. Its broad availability language
does not override the more specific release limitations on missing signal/
variation samples or establish per-candidate public CP payload applicability.
The conclusion remains PARTIAL documentation / UNKNOWN complete HH coverage.

## Libraries and tools to establish in that isolated release

The following are functional requirements, not a tested installation recipe.
The exact package names, versions and public calibration payloads must be
resolved in the chosen supported release before claiming tool readiness.

| Required function | Specific witnessed public evidence | Missing applicability evidence |
| --- | --- | --- |
| xAOD I/O and EDM dictionaries | Later public converter calls `ROOT.xAOD.Init()`, uses `CollectionTree`, SampleHandler and EventLoop, and configures AnaAlgorithm. Catalogue names photon/jet/EventInfo/truth/b-tag/link types. | Release-provided xAODRootAccess and relevant xAOD EDM dictionaries plus valid aux stores and link target context for each selected physical file. These library requirements are inferred from the intended xAOD API, not observed locally. |
| Photon tools | Converter v1.0.0 uses `EgammaAnalysisAlgorithms` photon configuration through CP configuration blocks with ID/isolation working points. | Applicable photon energy scale/resolution, ID/isolation efficiencies and uncertainties for MC20a/data15-16, full/fast simulation and actual object definition; public payload identities and supported trigger corrections. |
| Jet and JVT tools | Converter uses `JetAnalysisAlgorithms`, `AntiKt4EMPFlowJets` and an NNJvt update configuration. | Correct research jet collection, calibration/uncertainty/JVT prescriptions and payloads; overlap removal; whether stored nominal objects are to be reused or rerun, avoiding double calibration. |
| Flavour tagging | Converter uses `FTagAnalysisAlgorithms`, DL1dv01 Continuous and `xAODBTaggingEfficiency/13TeV/2023-22-13TeV-MC20-CDI-2023-09-13_v1.root`. | Candidate's tagger, fixed WP/continuous semantics, generator-dependent CDI applicability and efficiency/inefficiency convention. The witnessed path is not approved for an arbitrary pilot and is not GN2. |
| Event quality, pileup and exposure | Converter uses event cleaning and generator analysis; catalogue has run/LB, quality bits, pileup weights and generator weights. Official research limitations require a GRL. | Exact GRL, accepted runs/LBs, pileup profile, luminosity and trigger-effective exposure of the acquired file set. A commented GRL setting in a later converter does not attest the exact producer. |
| Trigger tools | Catalogue documents diphoton trigger-match links; later converter configures trigger algorithms. | Decision/configuration metadata and applicable matching/efficiency/prescale treatment for the intended 2015/2016 photon triggers; no single-photon summary substitution. |
| Systematics | Umbrella documents AnalysisBase systematic secondary ntuples; converter has CP configuration/common services and nominal `NOSYS` accesses. | Applicable systematic algorithm/service configuration, exact supported variations, payloads and complete sample list; full/fast-simulation restrictions. Nominal export alone is not systematic coverage. |

The converter [configuration source](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/blob/v1.0.0/python/PhysLiteToOpenDataAlgorithms.py)
and [runner](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/blob/v1.0.0/share/OpenDataNtupler.py)
are versioned examples of the mechanisms above. Their mapping to the exact
FEB2025 production remains UNKNOWN; [Phase 5D provenance review](phase5d_provenance_review.md)
owns that distinction. The [official limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp)
also restrict nonstandard object reconstruction and warn of missing samples
and fast-simulation photon/electron calibration limitations.

## Runtime isolation and verification contract

Preserve `/home/btu/miniforge3/envs/atlas-hh-root` and its ROOT 6.40.04,
C++20, GNU 15.3.0 compiler contract. A prospective AnalysisBase process must
start in a separately provisioned environment with its own supported OS,
compiler, ROOT, Python and libraries. Do not source it into an activated conda
shell, inject its `LD_LIBRARY_PATH` into a conda ROOT process, or link its xAOD
dictionaries with the present compiler merely because both are C++ libraries.
This separation is an engineering requirement inferred from the need to
respect each toolchain's ABI and runtime contract.

Record release/platform/compiler paths and versions, ROOT C++ standard,
effective library resolution and dictionary identities. Compile only with
that release's supported C++ standard/toolchain; the existing project remains
C++20. Validate bounded local schema, decoration/link access and one intended
CP tool before processing larger entry ranges. Native compatibility and actual
memory/time measurements remain **NOT_EVALUATED** here. Container/CVMFS/WSL
support and space must be confirmed before any installation request.

## Storage and compute scope

No defensible numerical total installation, RAM or CPU estimate is established
by the present evidence. **AnalysisBase image/layers, CVMFS cache, calibration
payloads, build/output volume, peak resident memory and per-event CPU are
UNKNOWN**. They are not zero and are not inferred from educational tests.

The format overview gives design targets of roughly 10 kB/DATA event and
12 kB/MC event and reports preliminary CPU reduction. These are not a local
benchmark, exact file sizes or a resource guarantee. Use the exact candidate
manifest for physical file bytes. For a prospective pilot, budget at least:

`selected input bytes + immutable installation/cache bytes + payload bytes +
build/log/output bytes + explicitly approved reserve`.

If staged partial files, checksum copies or separate runtime copies are kept,
count those copies separately. The download request must include actual
published file bytes plus metadata and bounded per-request reserve, with
historical transfer charges carried forward. Required local storage and
network charge are distinct quantities.

Two witnessed single-Higgs files illustrate the lower bound for those exact
inputs; they are not a minimal DATA/continuum pilot or HH signal:

| Member and role | Published bytes | Consequence |
| --- | ---: | --- |
| Record 80012 ggH 343981: `mc20_13TeV:DAOD_PHYSLITE.38191914._000036.pool.root.1` | 1,929,286,284 | About 1.80 GiB input alone; exceeds existing Phase 5 128 MiB cap. |
| Record 80012 VBF 346214: `mc20_13TeV:DAOD_PHYSLITE.38191539._000052.pool.root.1` | 785,967,187 | About 0.73 GiB input alone; also exceeds that cap. |

Both together are **2,715,253,471 bytes** before any installation, DATA,
continuum, copies or outputs. Exact DATA and continuum proposals and any
remaining candidate-access limitations belong to the
[candidate audit](phase5d_research_dataset_candidates.md). The umbrella's
71,749,688,366,060-byte total aggregates collision and MC collections and is
irrelevant as a minimum pilot requirement. No large-file acquisition or
partial remote ROOT event read is used as a workaround in Phase 5D.

Fresh official record 80014 metadata also establishes these exact, differently
scoped file inputs. Their checksums and process joins are recorded in the
candidate manifest; no native file was acquired:

| Role and exact member | Published bytes | Scope of a possible pilot |
| --- | ---: | --- |
| Prompt diphoton 364352: `mc20_13TeV:DAOD_PHYSLITE.38191666._000047.pool.root.1` | 1,807,847,758 | Relevant continuum kinematics/origin candidate; about 1.68 GiB input alone. This is a Sherpa sample, not the approved Pythia 302521 file. |
| Gamma+jets 364543: `mc20_13TeV:DAOD_PHYSLITE.37322584._000156.pool.root.1` | 476,512,859 | SinglePhoton pT slice 70-140; separate background role and overlap/filter requirements. |
| Gamma+jets 364542: `mc20_13TeV:DAOD_PHYSLITE.37322576._000009.pool.root.1` | 87,201,141 | SinglePhoton pT slice 35-70; possible small object/truth/flavour/schema pilot. It is not prompt-diphoton closure or an HH signal substitute. |

The bounded first page of the official record 80000 index now establishes
DATA run 266919 member
`data15_13TeV:DAOD_PHYSLITE.37001628._000001.pool.root.1`, **7,394,251 bytes**,
Adler-32 `1e0e3038`. It is the smallest member on the inspected page, not an
established global minimum. Native content, photon multiplicity/trigger
support, GRL membership and useful exposure remain unverified; it is a schema
candidate rather than a photon-physics sample demonstrated suitable by this
review.

That exact DATA member plus the 364542 gamma+jets member requires
**94,595,392 bytes** (about 90.21 MiB) of input storage. With the relevant
364352 prompt-diphoton member instead, the input-only sum is
**1,815,242,009 bytes** (about 1.69 GiB). Neither sum includes tools,
calibrations, outputs, metadata, transfer reserve or retained copies.

Fitting a byte cap does not authorize a new sample. Both DATA and MC need
separate exact-file approval. One MC file is not a complete slice or generator
normalization denominator; a schema-sized DATA file does not establish
adequate photon statistics or trigger-effective luminosity.

After a separately approved pilot is executable, measure peak RSS and elapsed
CPU/wall time at fixed small entry ranges, record decompression/I/O and enabled
tool/systematic configuration, then make a scoped cost estimate. A primitive
schema read cannot estimate a full calibrated systematic job.

## Source identity and assessment limits

The official historical snapshots below were acquired 2026-10-09 and rehashed
locally for this review. Hashes identify retained raw bytes, not official
strong checksums or current page content. Text derivatives assist reading.
Phase 5C documentation GET failures did not establish a cause or file absence;
new Phase 5D retrieval evidence, if any, is recorded separately by the root-led
access audit and does not upgrade unexecuted native/tool checks.

| Preserved raw source | SHA-256 |
| --- | --- |
| `.local/phase0_sources/opendata_80020_json.json` | `42127360b8271f7f6ed26ab78b92eea8011b2229f6695f5f912bd643a7220912` |
| `.local/phase0_sources/physlite_details.html` | `366783dfaa1a3951ea7b291c201c9bfaba440009d49312117aca26e21bfa15a5` |
| `.local/phase0_sources/physlite_pp_variables.html` | `4dfb10d27f5132f1dec370f3b9df4d0231af800b67a1a9a8227b86b7c3d42abb` |
| `.local/phase0_sources/research_limitations_pp.response` | `8d888a6b77ac318b7ba2224b136d85d26e849a9fa250137c3b6d3c1f1670ab68` |
| `.local/phase0_sources/framework_README.md.txt` | `49cb0542fd554aaa1c2afa3b070204faa11aa881d33526aa304065107f9c7c6c` |
| `.local/phase0_sources/framework_config.txt` | `a9db065388e2ab43d8a3fb68cc3c258265f2e716e12a8b193bb29e08cc468c9e` |
| `.local/phase0_sources/framework_algorithms.txt` | `5a56eb88d9beb3c472f21defca8f250a7dd3ca63ef60fe08f56cc8183eaf56c3` |

Fresh official tutorial raw response (2026-10-12):
`.local/phase5d_sources_20261012/physlite_tutorial.html`, 35,357 bytes,
SHA-256 `74fe10fe7f3574a202ef66688e0e8aa0f3aa5d316c47e3cd14486516ac6640b2`.
The attempted software `setup_software/` path returned HTTP 404. The
`cpalg_ntuple/` response reported HTTP 200 and Content-Length 242,489,
exceeding its 131,072-byte cap before body ingestion. Neither was retried;
their release/configuration content remains ACCESS_UNVERIFIED. These are
specific access results, not evidence of a general ATLAS server outage.

Additional fresh official responses, both 2026-10-12 and locally rehashed:

| Source | Retained path / bytes | Raw SHA-256 |
| --- | --- | --- |
| [Research containers](https://opendata.atlas.cern/docs/tutresearch/containers) | `.local/phase5d_sources_additional_20261012/research_containers.html` / 27,441 | `8f66488d093fb5da1717ca4679e8ebfd284e5c765b21b9fa8799d815d5e5906a` |
| [CP algorithms introduction](https://atlas-software.docs.cern.ch/analysis/analysis_tutorial/AnalysisSWTutorial/cpalg_intro/) | `.local/phase5d_sources_additional_20261012/cpalg_intro.html` / 243,417 | `1196bfedf00f176763b2005001a25b8f13d890f4d12525c5574e6a798672e1f7` |
| [QCD nominal metadata](https://opendata.cern.ch/api/records/80014) | `.local/phase5d_sources_20261012/record80014.json` / 1,057,821 | `6a44431db897b5dff2cb872c5ae6c1e65e5ad76c654d436cfe4e634af521b1e0` |
| [DATA 2015 first index page](https://opendata.cern.ch/record/80000/filepage/1?group=1) | `.local/phase5d_candidate_sources_20261012/data2015_index_page.json` / 150,761 | `078a36a5212d88b2b16ad705e7dd0a0ee48a8b2a5e13c6fb325188ea403dfb2b` |
| [Uncertainty guidance](https://opendata.atlas.cern/docs/documentation/systematics) | `.local/phase5d_candidate_sources_20261012/research_systematics.html` / 42,187 | `15ae14edcfa5ce2efe44b547cc551b01ca776cea25b4e80e8ca095e34d440b7c` |

**Disposition:** ROOT-only inventory/primitive pilot CONDITIONAL; applicable
AnalysisBase calibrated compatibility/execution UNKNOWN despite the verified
research example 25.2.2; storage/compute total UNKNOWN. Installation and
research acquisition require separate exact
scope authorization. This report supplies a requirements decision, not a
tested candidate-specific AnalysisBase release recommendation.

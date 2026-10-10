# Phase 0: public-source feasibility audit

Project: ATLAS_HH_BBGG_PUBLIC_V1. Step: STEP_2_PHASE_0_SOURCE_FEASIBILITY.
Checked: 2026-10-09 UTC. Overall status: **PARTIAL**.

The documented public objects support a candidate bbgg-like methods study. The audited inputs do **not establish reproducibility of the official ATLAS HH result**. HEPData numerical payloads and resource attachments could not be accessed, no named HH signal was identified in the inspected MC indices, and the physical ROOT schemas have not been tested. The recommendation is a later, bounded schema check of GamGam collision record 93915; no event analysis was performed here.

## Evidence rules and scope

`VERIFIED` means the cited public document, index, or code explicitly supports the field. It does not mean a ROOT file was opened or its calibration validated. `NOT_AVAILABLE` is used only for an explicitly scoped absence in a complete inspected schema/index. `UNKNOWN` means the evidence is insufficient or inconsistent. `ACCESS_UNVERIFIED` means the resource could not be retrieved; it never establishes that a resource does not exist. The field-level evidence is in [dataset_manifest.csv](../metadata/dataset_manifest.csv); URLs, versions, checksums, and access attempts are in [sources.md](../metadata/sources.md).

Only official documentation, public record JSON, source code, and DOI metadata were retrieved. Individual metadata responses were bounded at 4 MiB. No collision/MC ROOT file, large dataset, likelihood workspace, event loop, fit, BDT, or ATLAS internal software was downloaded or executed. ROOT I/O in the Step 1 preflight used synthetic infrastructure fixtures only.

## Reference publication and version distinction

The reference is the **journal version**, Phys. Lett. B 876 (2026) 140280, [DOI 10.1016/j.physletb.2026.140280](https://doi.org/10.1016/j.physletb.2026.140280), read through the [publisher PDF](https://pure-oai.bham.ac.uk/ws/portalfiles/portal/301457864/1-s2.0-S0370269326001346-main.pdf). The [ATLAS auxiliary page](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/) supplies figures and six PDF/PNG auxiliary tables. The first preprint is [arXiv v1, 4 July 2025](https://arxiv.org/abs/2507.03495v1); [v2, 22 April 2026](https://arxiv.org/abs/2507.03495v2) matches the journal headline results. The publisher PDF states online publication on 23 February 2026; the bibliographic issue date is May 2026 ([Crossref](https://api.crossref.org/works/10.1016/j.physletb.2026.140280)). These are different dates, not conflicting dataset years.

| Quantity | Journal version, abstract and Sections 3, 7 | arXiv v1 / HEPData v1 DOI abstract |
| --- | --- | --- |
| Combined luminosity | 308 fb^-1 (rounded) | 308 fb^-1 |
| Run 2 | 140.1 +/- 1.2 fb^-1, 13 TeV, 2015-2018 | headline 140 fb^-1 |
| Run 3 | 168.0 +/- 6.7 fb^-1, 13.6 TeV, 2022-2024 | headline 168 fb^-1 |
| Best-fit mu_HH | 0.9 +1.4/-1.1 | same headline |
| 95% observed mu_HH upper limit | 3.7 | 3.8 |
| 95% expected upper limit, background-only | 2.6 | numerical table values not retrieved |
| 95% observed kappa_lambda interval | [-1.6, 6.6] | [-1.7, 6.6] |

The older numbers are independently present in the [HEPData v1 DOI metadata](https://api.datacite.org/dois/10.17182/hepdata.160696.v1), whose registration is 20 October 2025. Its metadata was subsequently updated in 2026; an update timestamp alone does not prove that its table values were revised. Until payloads are read, **HEPData/journal numerical agreement is UNKNOWN**. Do not combine their numbers silently.

## Candidate datasets

| Candidate | Provenance and format | Coverage and published size | Selection / intended role |
| --- | --- | --- | --- |
| [93915 collision GamGam](https://opendata.cern.ch/record/93915) | ATLAS; 2025 beta ROOT ntuples; filenames `ODEO_FEB2025_v0`; Athena release 22 derivation from public PHYSLITE; 2020 reprocessing | 2015-2016 pp, 13 TeV; 36,564,144 events, 16 files, 9,861,498,743 bytes | At least two photons with pT at least 25 GeV. Simplest first schema/methods candidate. |
| [93922 MC GamGam](https://opendata.cern.ch/record/93922) | Same educational release/skim; 373 distinct DSIDs in the file index | 2015-2016 modelling, 13 TeV; 12,120,657 events, 373 files, 4,895,835,241 bytes | Mixed processes, not an HH-only or pure diphoton sample. Normalisation and overlap must be resolved per DSID. |
| [80020 PHYSLITE umbrella](https://opendata.cern.ch/record/atlas-80020) | 2024 research release; calibrated ROOT/xAOD DAOD_PHYSLITE, Athena 22; MC20a | 2015-2016 pp, 13 TeV; aggregate 9,058,437,931 events, 70,611 files, 71,749,688,366,060 bytes | Eleven child collections, including collision and MC. These totals are **not collision-only** and are not luminosity. |

Exact counts come from the records' `metadata.distribution`, not from a local event count. All three records state CC0 licensing; cite and acknowledge ATLAS as requested in their usage guidance. Their public record/API access is VERIFIED; ROOT transfer and content remain UNKNOWN.

The [educational release documentation](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details) states **36 fb^-1**. The [research coverage documentation](https://opendata.atlas.cern/docs/data/for_research/pp_data) gives approximately 3.2 fb^-1 for 2015 and 33 fb^-1 for 2016. These are release-level/rounded quantities; the exact GRL and usable luminosity of any selected GamGam subsample are UNKNOWN. Never scale a single period-D file to the full release luminosity without matching period coverage.

The PHYSLITE umbrella links data records 80000/80001; electroweak 80010; exotic 80011; Higgs nominal/variation 80012/80013; QCD nominal/variation 80014/80015; SUSY 80016; top nominal/variation 80017/80018. The two collision child JSON responses exceeded this audit's size bound, so their full file inventories were not retained. Higgs child indices 80012 and 80013 were inspected. No explicit HH/bbgg name was found in those indices; this is an index observation, not a claim about every possible public ATLAS release.

## Documented object availability and important inconsistencies

For flat ntuples, the [published variable dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details) documents the following. Types and names are documentation-level evidence; runtime existence is UNKNOWN.

| Purpose | Exact documented fields | Limitation |
| --- | --- | --- |
| Photon four-vectors | `photon_n`; `photon_pt`, `photon_eta`, `photon_phi`, `photon_e` | pT/energy use GeV in the inspected producer code; correspondence to FEB2025 v0 needs a file check. |
| Photon ID and isolation | `photon_isLooseID`, `photon_isTightID`, `photon_isLooseIso`, `photon_isTightIso`; `photon_ptcone20`, `photon_topoetcone40` | Decisions permit a candidate selection; equality to the journal working points/calibrations is not established. |
| Small-R jets | `jet_n`; `jet_pt`, `jet_eta`, `jet_phi`, `jet_e`, `jet_jvt` | Documentation: anti-kt R=0.4, pT>20 GeV, abs(eta)<2.5. Forward jets removed by this acceptance cannot be recovered. |
| Flavour tagging | `jet_btag_quantile`, `ScaleFactor_BTAG` | Continuous DL1d quantiles and nominal SF are documented. Numeric quantile-to-WP mapping is UNKNOWN. They do not establish the journal GN2 selection or its nuisance model. |
| Photon efficiency SF | `ScaleFactor_PHOTON` | Exists, but v1.0.0 producer multiplies **loose** ID and isolation SF over selected photons. Applying it unchanged to a tight-ID selection is unjustified. |
| Event identity | `runNumber`, `eventNumber`, `channelNumber` | Not a full GRL/lumiblock/prescale recipe. |
| Trigger summary | `trigP` | Single-photon summary, not a diphoton-trigger decision. A dedicated diphoton bit and photon-trigger SF are NOT_AVAILABLE **in this inspected flat dictionary**. |
| MC weights | `mcWeight`, `xsec`, `filteff`, `kfac`, `num_events`, `sum_of_weights`, `sum_of_weights_squared`; `ScaleFactor_PILEUP`, `ScaleFactor_JVT` | Per-DSID definitions and matching generated sums are essential; see below. |
| Limited variations | `jet_pt_jer1`, `jet_pt_jer2` | Two JER variations do not supply the complete detector/theory systematics. |

Versioned public producer evidence: [PhysLiteToOpenData v1.0.0](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/tree/v1.0.0), [Zenodo release](https://doi.org/10.5281/zenodo.15791091), published 2 July 2025. `Root/PhotonInfo.cxx` and `Root/JetInfo.cxx` multiply MeV values by 0.001; `Root/JetInfo.cxx` reads `ftag_quantile_DL1dv01_Continuous` and `ftag_effSF_DL1dv01_Continuous_NOSYS`. The dictionary uses both DL1dv01 and DL1dv0 descriptions and describes `jet_jvt` as float; the code declares `vector<bool>`. Therefore neither exact file type nor naming/version correspondence is assumed. The producer is later than the filename's FEB2025 tag; it is supporting evidence, not an attestation of identical production.

For research PHYSLITE, the [public pp variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html) documents `AnalysisPhotons` kinematics, `DFCommonPhotonsIsEMLoose`, `DFCommonPhotonsIsEMTight`, isolation and cleaning variables; `AnalysisJets` kinematics, `DFCommonJets_fJvt`, and `btaggingLink`; b-tag containers with `DL1dv01_pb/pc/pu`; `EventInfo` with `runNumber`, `lumiBlock`, `mcChannelNumber`, `mcEventWeights`; and photon trigger-match collections. Trigger matching is not by itself a trigger pass decision or efficiency/prescale correction. Actual split-branch names and event-level decisions must be checked per physical file; flat-ntuple names must not be assumed for xAOD.

The [official research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp) explicitly exclude complete tracks, clusters, and particle-flow inputs, limiting reconstruction changes. They also warn that some signal/systematic samples are unreleased and some fast-simulation samples have photon/electron calibration limitations. Research format and available tools improve possibilities; they do not prove the inputs needed for this particular HH analysis are complete.

## MC composition and normalisation

The complete 93922 file index has 373 files and 373 unique DSIDs. All 373 DSIDs match rows in [the versioned public `extras/metadata.csv`](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/blob/v1.0.0/extras/metadata.csv). The [official educational metadata table](https://opendata.atlas.cern/docs/data/for_education/13TeV25_metadata) also supplies cross-section (pb), filter efficiency, k-factor, generated event count, sum of weights and sum of squared weights, process and generator labels.

Examples identified by index and metadata, **not locally processed samples**:

| DSID | Process metadata | Intended evidence |
| --- | --- | --- |
| 343981 | ggF single H -> gamma gamma | Resonant single-H input exists; it is not HH signal. |
| 346214 | VBF single H -> gamma gamma | Separate production mode, not an HH benchmark. |
| 302520 | QCD direct diphoton, generated 55<mgg<100 GeV | A mass-filtered sample; cannot stand for the complete continuum in the analysis window. |
| 423099-423112 | gamma+jet filename series | Candidate fake-photon background modelling; not a validated data-driven fake estimate. |

No explicitly named Higgs-pair process was found when inspecting filenames plus mapped process/keyword/description fields. **A usable ggF/VBF HH->bbgg signal and coupling-variation set is UNKNOWN/not established for this project**. Some tiny MC files may contain almost no selected events; file size is not signal statistics. No selected yield, efficiency, significance or upper limit was computed.

There is a documented ambiguity: the flat dictionary describes square roots for `sum_of_weights` and `sum_of_weights_squared`, whereas [v1.0.0 `skimOpenDataNtuples.py`](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/blob/v1.0.0/scripts/skimOpenDataNtuples.py) sums CutBookKeeper histogram bins directly and writes those sums without a square root. That code constructs the `analysis` tree and a GamGam multiplicity filter; the older `applyskim_addweights.py` has different skim/weight code. **Follow the record's published skim and retain the version discrepancy; do not infer a different 93915/93922 threshold from an unrelated script.**

A future nominal yield weight would require a matched pre-skim signed generated sum W, cross-section sigma in pb, generator filter efficiency f, k-factor k, and luminosity L in pb^-1: `w = L * sigma * f * k / W * mcWeight * applicable_corrections`. This is a conditional recipe, not a validated weight for these files. Cross-section/filter conventions may already encode decays; do not multiply a branching ratio twice. The total selected count and the post-skim weight sum are not substitutes for W. Relevant guidance: [research MC metadata](https://opendata.atlas.cern/docs/data/for_research/metadata) and [sample combination/overlap](https://opendata.atlas.cern/docs/data/for_research/evgen_collections). Match DSID, production tags, processed-file completeness, pileup period and SF working point first. Alternative generators/variations must not be added as independent nominal backgrounds.

## Comparison with the official analysis

The journal Sections 4-7 specify a 35/25 GeV diphoton trigger; tight photons with pT/mgg>0.35/0.25, central acceptance and crack exclusion; mgg=105-160 GeV; two b-tagged jets using GN2 at 85%; and b-jet corrections/kinematic fitting. Seven categories per run (14 total) use a 350 GeV corrected-mass split and BDTs. A simultaneous unbinned mgg fit uses signal/single-H shapes, data-driven continuum modelling, constrained nuisance parameters and asymptotic CLs. Detector/theory and spurious-signal uncertainties contribute. [Journal Sections 4-7](https://doi.org/10.1016/j.physletb.2026.140280).

Audit consequences (inferences from the comparisons above):

- The 2015-2016 release cannot supply the journal's full Run 2 or any Run 3 sample; multiplying its yields by 308/36 does not recreate those data.
- The GamGam skim plus released object acceptance define a conditional sample. Efficiency relative to all collisions or inclusive HH requires pre-skim information and an appropriate signal sample.
- Combining different skims can double-count events. Within data use run/event identity; within MC use DSID plus event identity and explicit sample-overlap rules. Do not assume index files are independent processes merely because they have different names.
- DL1d quantiles and loose photon SF are insufficient to replicate GN2/tight-photon efficiencies, corrections and nuisance correlations. Two JER branches do not close that gap.
- Published yields, weighted plots and profiled scans do not reconstruct category event data, shape parameters, constraints or their correlations. Workspace/resource availability remains ACCESS_UNVERIFIED, rather than proven absent.

## Capability matrix

These are feasibility assessments inferred from the cited availability; they are not executed analysis results.

| Capability | GamGam 93915/93922 | Research PHYSLITE | HEPData / auxiliary | Decision |
| --- | --- | --- | --- | --- |
| Inspect photon/jet schema | Documented candidate; actual file UNKNOWN | Documented richer candidate; actual file UNKNOWN | Not event objects | GO for later bounded check |
| Construct mgg and simple bbgg-like selections | Kinematics/ID/quantiles documented | Objects/ID/tagger outputs documented | Reference distributions | CONDITIONAL on physical schema/units/WP |
| Calibrated tight-photon/diphoton-trigger efficiency | Incomplete for that selection | Requires public tools, menu and calibration validation | No verified correction input package | Not established |
| Normalised background comparison | MC metadata exists; match sums and remove overlap | Metadata and tools needed | Yield references registered | CONDITIONAL, not validated |
| HH signal efficiency/coupling scan | No named matching signal established | No named matching signal in inspected Higgs indices | Profiled scan tables registered | Not established from current event inputs |
| Independent simplified likelihood | Requires explicit assumptions/new validation | Same | Some summary inputs described, payloads inaccessible | CLASS C only, future work |
| Replot published numerical curves | No role | No role | 30 table descriptions VERIFIED; exports ACCESS_UNVERIFIED | CLASS A candidate, not yet executed |
| Reproduce official ATLAS likelihood/limit | Missing full data coverage and validated inputs | Same coverage/input gaps | No verified complete likelihood/resources | CLASS B not established; CLASS D for current input set |

The full statistical input inventory and A/B/C/D definitions are in [public_input_inventory.md](../metadata/public_input_inventory.md). The decision, gate statuses and bounded next action are in [phase0_decision.md](phase0_decision.md).

## Questions that remain open

1. Can the HEPData table payloads/resources be retrieved, and do their values correspond to journal 3.7 or preprint 3.8? Are covariance/correlation, workspace or JSON likelihood attachments supplied?
2. What exact production commit, branch types, generated weight sums, GRL and usable luminosity correspond to FEB2025 v0? Do physical files agree with the dictionary or the later producer?
3. What are the exact quantile boundaries and efficiency SF semantics for a chosen b-tag/photon selection? Where are the matching photon-trigger decision, prescales and corrections?
4. Is an appropriate public ggF/VBF HH->bbgg signal (and required coupling/systematic samples) available outside the inspected collections, with sufficient selected statistics?
5. Can public calibration tools and documented corrections support a separately defined study with quantified uncertainties? This is not yet an approved event-analysis implementation.

# Phase 4 readiness assessment

Checked: 2026-10-10 UTC. Scope: documentation only after the bounded Phase 3 study.
**Overall: CONDITIONAL for further inclusive-object method studies; not ready for
an HH-like search, signal efficiency, calibrated prediction or likelihood.**

VERIFIED denotes a checked property within the stated scope; CONDITIONAL needs
specified closure/provenance work; UNKNOWN means not established;
ACCESS_UNVERIFIED records an unsuccessful access attempt; NOT_AVAILABLE is used
only for a precisely bounded input or field inventory. Neither an inaccessible
page nor absence in one inventory establishes global nonexistence.

## Component assessment

| Component | Classification | Evidence and requirement before use |
| --- | --- | --- |
| Existing data schema and exploratory reconstruction | VERIFIED implementation; CONDITIONAL physical interpretation | [Phase 1 manifest](../metadata/root_schema_manifest.csv), [Phase 2](phase2_kinematic_validation.md) and [Phase 3](phase3_validation.md). Native RVec readers and numerical tests pass. Exact FEB2025 production association is UNKNOWN; GeV/radian interpretation is PROVISIONAL. |
| Suitable HH signal MC | UNKNOWN | Phase 0 matched all 373 GamGam MC file DSIDs and inspected research Higgs child index names without establishing an explicit suitable HH process. This is a scoped inventory result, not a claim about all public ATLAS collections. Need documented HH production/decay, mass/couplings, generator, simulation, period, weights and schema compatibility. No signal was generated or fabricated. |
| Continuum/background MC release | VERIFIED record/index; CONDITIONAL suitability | [CERN record 93922](https://opendata.cern.ch/record/93922) describes the 2015+2016, 13 TeV GamGam beta MC release with 373 files and a two-photon >=25 GeV skim. The record page was readable again on this check date. No physical MC file was opened. Need process/DSID, overlap and phase-space coverage, including prompt/fake components, before selecting a prediction model. |
| Exact data/MC compatibility | UNKNOWN | [Record 93915](https://opendata.cern.ch/record/93915) and 93922 establish release-level identities, not exact calibrated equivalence of the processed periodD file and a chosen MC sample. Need production tags, schema/units, object definitions, GRL, pileup and simulation conditions matched explicitly. |
| MC normalization ingredients | CONDITIONAL | [Educational metadata](https://opendata.atlas.cern/docs/data/for_education/13TeV25_metadata), [research guidance](https://opendata.atlas.cern/docs/data/for_research/metadata), and versioned [metadata.csv](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0) list cross sections, filter efficiencies, k factors and generated sums. Mapping to an exact processed v0 sample and signed pre-skim sum is UNKNOWN. Post-skim counts are not that denominator. No weights were applied. |
| Photon flags and efficiencies | VERIFIED physical booleans; CONDITIONAL raw-flag diagnostic; UNKNOWN correction validity | Native RVec<bool> flags are present in the audited file. The [dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details) and [PhotonInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0) describe loose/tight ID/isolation decisions. The later producer does not prove exact FEB2025 configurations. `ScaleFactor_PHOTON` presence does not establish tight-selection applicability, efficiency or uncertainty. |
| Jet calibration and overlap/JVT recipe | UNKNOWN exact configuration; CONDITIONAL inclusive diagnostics | [PHYSLITE format](https://opendata.atlas.cern/docs/documentation/data_format/physlite/) and [variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html) document calibrated research objects. They do not establish the full exact flat-v0 calibration/overlap/JVT recipe or nuisance response. Current jets are leading inclusive jets with study cuts. |
| B-tag working point | UNKNOWN; analysis BLOCKED | Integer `jet_btag_quantile` exists. The dictionary and [JetInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0) have version-sensitive DL1d descriptions; no exact-v0 mapping and matching calibration are established. Do not equate DL1d with GN2, infer a WP, or call m_jj m_bb. |
| Official diphoton trigger decision/correction | UNKNOWN; dedicated decision NOT_AVAILABLE in audited flat field inventory | `trigP` is physically present. The later [producer](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0) combines single-photon trigger decisions; it is not proof of the journal 35/25 diphoton menu. Neither thresholds in a study cut nor trigger matching alone establishes decision, prescales, efficiency or correction. No trigger cut is applied. |
| PeriodD luminosity and data quality | UNKNOWN | Nominal full public 2015-2016 coverage is not the effective luminosity of this one periodD file and bounded range. [Research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp) require a GRL. Need matching GRL/run/lumiblock coverage and trigger/live-time information before a luminosity-normalized measurement. |
| Full journal collision sample | NOT_AVAILABLE in the specified 2015-2016 inputs | The [publication](https://doi.org/10.1016/j.physletb.2026.140280) uses combined 308 fb^-1. These public inputs do not supply that coverage. Do not rescale the partial skim to emulate it. |
| Detector/theory systematics | UNKNOWN complete validated set | Nominal fields and some documented variations do not prove complete photon/jet/b-tag/trigger/pileup/theory variations, correlations or calibrations for the selected v0 data/MC. [Research limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp) also document unreleased variations and simulation caveats. No arbitrary nuisance values are introduced. |
| Published statistical references | VERIFIED identity/descriptions; ACCESS_UNVERIFIED numeric payloads | [HEPData 160696 v1 DOI metadata](https://api.datacite.org/dois/10.17182/hepdata.160696.v1) identified 30 tables in Phase 0. Numerical exports/resource listings returned 403 then; they have not been recovered. Journal/older DOI headline differences must be resolved before numerical comparison. |
| Public complete likelihood/workspace | ACCESS_UNVERIFIED | [Inventory](../metadata/public_input_inventory.md) records inaccessible attachment listings. No complete workspace/model was downloaded or validated; do not label it globally absent. Published scans/curves do not themselves specify observations, constraints, nuisances and correlations of the generating model. |
| Statistical modeling readiness | CONDITIONAL requirements; currently blocked by missing validated inputs | Need suitable signal/background, calibrated selection, normalization, categories, resolution/shape closure, sideband strategy, nuisance model/correlations and coverage tests. Any new simplified model must be explicitly identified and independently validated. No fit or HH search was started. |

For future normalized MC, a possible structure is
`L[pb^-1] * sigma[pb] * filter_efficiency * k_factor / sum_signed_generated_weights`
times the signed event generator weight and only validated correction factors.
This is a requirement sketch, not an implemented prescription: metadata conventions
must establish which factors are already included, sample overlap, the exact
pre-skim denominator and effective luminosity. Negative generator weights cannot
be replaced with unweighted event counts. The current cutflow uses data raw counts.

## Source versions and access limits

The [Phase 0 register](../metadata/sources.md) provides URLs, acquisition dates,
SHA-256 hashes and access classifications. Its preserved snapshots were acquired
2026-10-09; they are source inspection evidence, not new event or MC execution.
The educational dictionary is a mutable webpage. Producer v1.0.0 is a later
July 2025 release and cannot alone establish the FEB2025 file's provenance.

This task rechecked the stored PhotonInfo and JetInfo bytes against the register:
`9a59853da9c04a428d1990320b680940480bdf723f8d299689ac3bc26e7a8569`
and `01325c175a93676dea65f7946dba486bcc1e84c6f7168e694bc3362c05f3a5b5`.
The preserved research MC metadata and limitations sources are registered with
hashes `b24cebfeb808e8764df4fbfbc4864cc33ed8a3070f57a7317831505cfdb0c9cd`
and `8d888a6b77ac318b7ba2224b136d85d26e849a9fa250137c3b6d3c1f1670ab68`.
The latter two pages returned 403 through the web client on 2026-10-10, so fresh
retrieval is ACCESS_UNVERIFIED; their retained source evidence remains dated.
Record 93922's readable page is a metadata check only. No new MC or collision
dataset bytes were downloaded. Historical PARTIAL verdicts remain unchanged.

## Safest next scope

Review and, with separate authorization, integrate the Phase 2 PR followed by the
stacked Phase 3 PR; rerun integrated regressions. Then close exact production,
unit/calibration, trigger/GRL and data/MC provenance gaps with a bounded metadata
and schema investigation. If compatible background MC is established, a narrowly
defined inclusive diphoton-plus-jets method/closure study is the safest scope.
Keep b-tagging blocked until a version-matched WP/calibration is verified.
Do not move to HH signal efficiencies, coupling/sensitivity claims, a full
308 fb^-1 comparison, cross sections or a likelihood until their inputs pass
separate scientific gates. PC2/PC3 remain PENDING.

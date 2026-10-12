# Phase 5D physics capability and prospective closure decision

Project: ATLAS_HH_BBGG_PUBLIC_V1. Assessment date: 2026-10-12.

**Rank 1: retain the GamGam raw methods study (GO) while resolving specific
physical-input gaps. Rank 2: a separately authorized PHYSLITE schema/truth
pilot (CONDITIONAL). Calibrated HH extraction or an absolute background
prediction remains STOP.** Richer fields are useful only when an exact
physical sample and its tools/provenance establish the required capability.

No new physics event read, boundary optimization, normalization, DATA transfer
fit, background prediction, closure test, HH fit or figure was performed in
this review. No research dataset or analysis container was downloaded.
Phase 5C results and their retrospective status are preserved.

## Evidence-specific capability comparison

`VERIFIED` below is restricted to existing witnessed schema/results or literal
public documentation. `PARTIAL` denotes a possible documented mechanism with
unclosed physical applicability. `UNKNOWN` denotes an unestablished fact.
Current endpoint access is distinct from these classifications and is captured
by the root-led metadata receipt. No PHYSLITE candidate was opened natively.
The machine-readable [capability matrix](../metadata/phase5d_capability_matrix.csv)
records the same scopes and next gates.

| Requirement | Route A: educational GamGam | Route B: research PHYSLITE | Consequence |
| --- | --- | --- | --- |
| Reconstructed photons | Audited DATA has native RVec kinematics and four ID/isolation bool arrays. Existing selection keeps those flags as diagnostics; exact FEB2025 producer/semantics remain unresolved. | Catalogue documents `AnalysisPhotons` kinematics, loose/tight cut decisions, cleaning and isolation. Per-file types, units and availability are NOT_EVALUATED. | Primitive study possible after native validation; an ID name does not prove journal object equivalence. |
| Photon calibration/efficiency | Numerical mass/unit consistency is not detector calibration. Exported correction semantics/applicability remain UNKNOWN for the intended leading-pair selection. | Format documents calibrated objects; applicable CP tool, full/fast-simulation handling, ID/isolation and trigger efficiency payloads still require matching production. | Calibrated photon model CONDITIONAL in B, STOP for current physical claims. |
| Jet calibration/selection | Existing leading jets are inclusive, with audited kinematics and bool JVT; no calibrated b-jet assertion. Reduced skim cannot restore removed objects. | `AnalysisJets` and standard calibrated collection information are documented; exact native collection, JVT, overlap-removal and uncertainties need tools/file verification. | New jet collections or grooming requiring missing constituents are outside documented PHYSLITE support. |
| b-tag WP/efficiency | Native integer `jet_btag_quantile` is readable; exact thresholds, CDI applicability and negative exported BTAG semantics are unclosed. | Documented DL1dv01 pb/pc/pu and `btaggingLink` allow a potential DL1d study with applicable WP/CDI. | No GN2 equivalence, efficiency or b-jet purity claim from scores/quantiles alone. |
| Truth flavour/photon origin | Existing three MC samples contain truth kinematics; geometric matching does not establish photon origin or jet b flavour. 302521 has no native observations. | Catalogue documents photon truth type/origin/links, TruthPhotons ancestry, jet `HadronConeExclTruthLabelID` and truth-jet labels. | B could close specific origin/flavour gaps only after native link/label semantics and sample support pass. |
| Reco-Gen matching | Preserved study-defined geometric matches are numerical diagnostics. They are not an official unique association, purity or efficiency denominator. | xAOD truth associations and eligibility information are documented. | Freeze matching/eligible-truth/ambiguity rules; validate target links before physical interpretation. |
| Trigger decision/exposure | `trigP` is an audited bool, later-source single-photon summary; not diphoton decision/prescale/efficiency. | Catalogue documents diphoton trigger-match ElementLinks. Matching is distinct from decision/menu/prescale/efficiency. | Native trigger/config and supported photon corrections remain unclosed; do not infer exposure from matching. |
| GRL/luminosity | Period-D bounded rows lack an established selected-file GRL/LB/prescale/livetime exposure. Event fractions are not luminosity fractions. | Run/LB and quality fields plus official GRL requirement provide a possible exposure route. Approximate release-level 3.2/33 fb^-1 is not the bounded selected-file exposure. | Calibrated DATA-MC rates require exact accepted runs/LBs, file completeness, luminosity and trigger convention. |
| Generator normalization | Signed diagnostic weights are preserved; exact nominal index, complete signed pre-skim denominator and sigma/filter/k/BR applicability remain unclosed. | Catalogue documents nominal/variation `mcEventWeights`; public metadata includes normalization ingredients. | A metadata table row or weight vector alone does not prove an applicable denominator for an incomplete file pilot. |
| Detector/theory systematics | Flat nominal branches do not supply a complete correlated model. | AnalysisBase processing and variation sample collections are documented, with explicit official limitations on unreleased samples. | Per-tool variations and required process samples must be enumerated; full HH coverage UNKNOWN. |
| HH signal | Witnessed ggH/VBF single-H inputs are not Higgs pairs. | No explicit matching HH signal is established by the inspected Higgs index scope. | STOP HH efficiency/sensitivity/limits; single-H and unrelated final states are not substitutes. |
| Background modelling | Raw sideband counts and shape diagnostics do not identify continuum/fake composition or provide physical closure. 302521 access remains blocked. | Prompt continuum, gamma+jets/fakes, single-H and relevant backgrounds require exact sample identities, filters/overlap and corrections. | Prompt MC alone does not model jets misidentified as photons or validate a complete bbgg background. |
| Reproducibility/cost | Preserved checksums, selection/cache ranges and native conda toolchain support bounded numerical reproducibility. | Requires exact physical tags/bytes, pinned tools/payloads/runtime and provenance. | Dataset identity, software identity and scientific applicability are separate gates; memory/CPU/install cost remains unmeasured. |

Primary evidence: [GamGam DATA](https://opendata.cern.ch/record/93915),
[GamGam MC](https://opendata.cern.ch/record/93922),
[research umbrella](https://opendata.cern.ch/record/atlas-80020),
[variable catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html),
[research coverage](https://opendata.atlas.cern/docs/data/for_research/pp_data),
[limitations](https://opendata.atlas.cern/docs/data/for_research/limitations_pp),
[MC metadata](https://opendata.atlas.cern/docs/data/for_research/metadata)
and [sample-combination guidance](https://opendata.atlas.cern/docs/data/for_research/evgen_collections).
The latter explains sliced/overlapping samples and distinguishes Baseline,
Alternative, Systematic and Specialized roles. It does not supply an approved
diphoton-plus-fake composition for this project.

Fresh [official uncertainty guidance](https://opendata.atlas.cern/docs/documentation/systematics)
documents many available tool/weight variations and correlation-aware
interpretation. That broad capability statement does not prove complete
candidate-specific or HH systematic coverage; the release's documented missing
sample and fast-simulation limitations still apply. It gives 2015/2016
release-level luminosities **3.24 +/- 0.04 / 33.40 +/- 0.30 fb^-1**. These are
documentation values, not this project's run-266919 or bounded period-D
trigger-effective exposure, and no luminosity normalization is applied.

The [native DATA schema](phase1_schema_validation.md),
[existing geometric matching review](phase4_genmatching_validation.md),
[additive numerical recovery decision](phase4_numerical_recovery_decision.md),
[luminosity audit](phase5_luminosity_audit.md),
[Phase 5D provenance](phase5d_provenance_review.md) and
[exact candidate audit](phase5d_research_dataset_candidates.md)
identify project-specific evidence and gaps. Both releases' 2015/2016 coverage
is separate from the journal's broader population; neither route alone proves
official analysis/category/likelihood equivalence.

## Scientific review of preserved Phase 5C results

The [Phase 5C report](phase5c_sideband_dependence.md) retains 63,095 historical
cache rows, C9=1,689, and 1,374 sideband events: A=443/B=931. All DATA had
already been examined. Its fixed SHA identity split has fold 0=724 and fold
1=650, zero intersection and full sideband union. These are **retrospective
diagnostic folds**, not prospective, untouched or blinded validation.

| Preserved statistic | Pooled | Fold 0 | Fold 1 |
| --- | ---: | ---: | ---: |
| Pearson(mass, absDeltaEta) | 0.195745 | 0.165732 | 0.229448 |
| Spearman | 0.189009 | 0.160426 | 0.221226 |
| A/B empirical mass KS D | 0.082132 | 0.060262 | 0.138912 |
| Cramer's V, fixed 2-by-9 table | 0.084597 | 0.106824 | 0.134543 |

Within A, fold-0/fold-1 KS D=0.088157; within B it is 0.083306.
These describe the observed shapes. They do not validate physical transfer
stability or establish formal rejection of equal shapes without an applicable
inferential model. Correlations can miss nonlinear/conditional dependence;
KS D and Cramer's V summarize complementary features of the same observations
and are not independent validation datasets. The disconnected sideband mass
support and unequal lower/upper widths remain part of every interpretation.

All baseline contingency cells are populated in each fold, but fold-1 A has
9 events in the final bin and 11 in [140,145). Occupancy alone is not a
justification for asymptotic pvalues. The fixed 0.8/1.0/1.2 boundaries and
outer-trim inventory overlap; none is chosen as a new optimum. No extra
boundary is proposed from these DATA.

The stored normalized-shape covariance is
`Cov(p_i,p_j)=(delta_ij*p_i-p_i*p_j)/N`, conditional on a fixed unweighted
total under a multinomial counting model. Negative off-diagonals implement
the normalization constraint, so bins are not independent. Sparse plug-in
zero variance does not give a zero confidence upper bound. The estimator
does not include run correlations, detector/trigger/systematic effects,
composition changes or signal contamination. Wilson occupancy intervals have
the same limited counting-model scope. Future weighted MC with signed weights
requires its own weight-squared/correlation treatment; these unweighted
probability/covariance formulas must not be silently reused. Effective sample
size, where meaningful, is a diagnostic, not proof of independence or a
physical normalization.

The protocol raw SHA-256 remains
`e9916da8772902c5464ea141397340a5230cb1733bb05e7c86800d9681295f66`;
the aggregate audit CSV remains
`5df09c40c8fbaaec7b6074105bc8743f24be5cbb4bfcf2c1dfbfdfe4e4c5d587`.
Both were rehashed for this review. No Phase 5C report, statistics, cache,
fold assignment or selection was rewritten or rerun by this reviewer.
The quoted rounded correlations, KS D and Cramer's V were checked directly
against the preserved aggregate CSV; this was artifact inspection, not a
fresh physical-cache processing run or a recomputed physics result.

## Prospective physical closure protocol: prepared, not executed

This is a future protocol outline requiring suitable authorized inputs and
an independently approved statistical specification. It creates no new
analysis framework and no present closure claim.

1. **Define the question before input inspection.** State whether the target
   is raw prompt-origin/schema compatibility, calibrated selection response,
   or a physical background transfer. A schema pilot cannot pass the latter.
   Identify prompt continuum, relevant gamma+jets/fake components, single-H
   contamination and any required heavy-flavour composition; record explicit
   sample/filter/overlap roles. No single-H substitution for an HH efficiency
   study and no incomplete prompt sample promoted to total background.
2. **Close input and correction gates first.** Require exact file identities,
   native schema, truth/eligibility semantics, applicable photon/jet/b-tag
   tools, trigger/GRL/exposure and complete nominal signed-weight denominator
   with sigma/filter/k/BR conventions. A small-file pilot can assess fields
   without being a complete rate model. Document residual missing variations
   and stop physical closure where those omissions invalidate the question.
3. **Freeze the full protocol before viewing new results.** Pin source and
   configuration hashes, unchanged historical selection as a reference,
   prospective selection/regions/binning, calibration and validation data
   identities, weighting, nuisance treatment and all pass/fail criteria.
   Define the minimum statistical precision/power and relevant effect-size
   tolerance from the stated physics goal before inspecting outcomes; this
   review supplies no threshold optimized on historical DATA.
4. **Enforce independent usage, not merely separate hashes.** New MC/DATA
   must have recorded unseen status if that is claimed. Split whole unique
   identities before selecting/processing the new sample; check duplicates
   across files, generator reuse and calibration/validation intersections.
   Account for run/campaign or generator correlations where relevant.
   Deterministic disjoint identities alone do not guarantee IID sampling.
   Existing Phase 5C folds retain their retrospective role and never become
   the new prospective validation set by relabelling.
5. **Evaluate the prespecified model on suitable held-out physical inputs.**
   Keep component and calibration/validation roles separate; include finite
   MC statistics, signed-weight cancellations, shared-normalization
   covariances and agreed systematic correlations. Compare observed versus
   expected quantities with the frozen closure residual/effect-size and
   interval/coverage procedure. Record undefined/sparse/invalid states
   honestly; do not drop inconvenient bins or retune boundaries after seeing
   validation. A changed protocol starts a new documented validation task.
6. **Keep current DATA inference closed.** This phase performs no real-DATA
   transfer fit or central-window prediction. Any future DATA fit/unblinding
   or HH interpretation needs its own explicit scope authorization and the
   required physical model. Record failure, partial coverage and contamination
   separately from an engineering pass. Successful physical closure for a
   limited component is not official ATLAS HH analysis validation.

## Ranked next actions and authorization boundaries

| Rank and scoped route | Decision | Missing evidence and next authorization |
| --- | --- | --- |
| 1. Preserve and communicate existing GamGam raw numerical/method results | **GO** | Keep exact selection, checksums, provisional units and diagnostic limitations. Source/text documentation is already authorized; generated figure publication requires exact version/caption approval. |
| 2. Resolve official production/access answers for the already authorized 302521 file | **CONDITIONAL** | Final unsent support package asks for supported transport and production/weight/filter/correction provenance. Sending requires explicit user authorization. Repeated failed transports remain stopped; any acquisition must obey the existing exact-file/budget approval and new official evidence. |
| 3. Bounded research DATA plus relevant MC schema/truth pilot | **CONDITIONAL** | Select exact files/tags/checksums/bytes in the candidate manifest; establish primitive or xAOD runtime requirements and available storage. New dataset transfer and any separate tool installation require explicit exact scope/budget authorization. |
| 4. Calibrated independent public bbgg-like methods study | **CONDITIONAL** | Applicable AnalysisBase release/tool/payload evidence, photon/jet/WP/trigger/GRL, complete weights, samples/overlap, uncertainties and prospective closure specification. Separate calibrated-analysis authorization follows those reviewable gates. |
| 5. Absolute background model or official HH extraction/sensitivity/limits now | **STOP** | Current physical closure NOT_EVALUATED; exact normalization, exposure, calibration and matching HH inputs/statistical model are unclosed. No framework tests or richer format name supplies those inputs. |

The defensible migration priority is **an exact physical input and provenance
milestone**, followed by a small native capability check under separate
approval. Repeating synthetic frameworks or tuning the already viewed DATA
would not resolve the present physics-input blockers. The
[toolchain requirements](phase5d_toolchain_requirements.md) preserve the
existing conda environment. Fresh official research container guidance
establishes a public AnalysisBase **25.2.2 example**, while its exact candidate
and tool/payload applicability, image digest and unmeasured installation/RAM/
CPU costs remain UNKNOWN. The later converter's 25.2.40 is not borrowed as
a research recommendation.

The newly identified 87,201,141-byte gamma+jets 364542 member offers a
smaller possible schema/origin/flavour capability milestone than the
1,807,847,758-byte prompt-diphoton 364352 member. Its purpose must be explicitly
limited and approved: it cannot substitute for prompt diphoton continuum,
complete fake/background modelling, normalization completeness or physical
closure. The relevant continuum candidate remains a separate, substantially
larger input whose required transfer/storage approval has not been granted.

The exact 7,394,251-byte run-266919 DATA member identified on the bounded
record-80000 first page makes the small DATA-plus-gamma+jets input-only sum
94,595,392 bytes. With prompt diphoton 364352 it is 1,815,242,009 bytes.
These are reviewable resource lower bounds, not approved downloads or
adequate-physics-statistics claims. The DATA member's photon content, GRL
membership and exposure are unverified. Establish them before promoting the
native schema pilot to a calibrated photon/background study.

Primary-source hashes and historical snapshot dates are listed in that
toolchain report and in the preserved [Phase 5C source registry](phase5c_analysis_route_assessment.md).
They attest witnessed documentation scope only. The final decision must also
include the root-led fresh access/candidate evidence and every unclosed gate.

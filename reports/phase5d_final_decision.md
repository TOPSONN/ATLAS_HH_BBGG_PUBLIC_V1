# Phase 5D physical-input and provenance decision

**STATUS: PARTIAL_INPUT_PROVENANCE_AND_TOOLCHAIN_BLOCKED.** The requested
documentary assessment is complete. No calibrated HH readiness, physical
background closure, absolute normalization or new event-level result has
passed. The recommended immediate action is the finalized, still UNSENT CERN
support package. A separately approved small research tool pilot is the next
conditional development route.

Project: ATLAS_HH_BBGG_PUBLIC_V1. Task:
PHASE5D_RESEARCH_PHYSLITE_AND_PROVENANCE_DECISION. Reviewed 2026-10-12 UTC.
Baseline: `ba2ba7d8fbfdf8d54c5f6156a673ee4ac1fb30af`, re-fetched before work.
PR [#8](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/8) continues
on `codex/phase5-background-normalization`, OPEN / DRAFT, with base
`codex/phase4-mc-truth-validation`. No main integration or merge is authorized.

## Ranked routes and exact next authorization

| Rank | Route | Decision | Missing evidence and next authorization |
| --- | --- | --- | --- |
| 1 | Preserve educational native ROOT methods and existing numerical/sideband diagnostics; seek official access/provenance clarification | **GO** for the already bounded methods scope | No new physics result is inferred. The final support email is prepared; explicit user sending authorization is required. Do not repeat failed 302521 storage routes pending a supported procedure. Any resumed transport must retain prior accounting and verified TLS where applicable. |
| 2 | Small research DATA + gamma+jets schema/object/truth/flavour and tool pilot | **CONDITIONAL** | Separately approve the two exact members and a metered acquisition plan, then establish native checksums/types/units/links. Calibrated CP operations additionally need an applicable pinned AnalysisBase runtime, public tool configuration/payloads and separate installation approval. Photon yield and DATA exposure are unknown. This is not prompt-diphoton closure. |
| 3 | Research prompt diphoton physical-input pilot | **CONDITIONAL** | Separately approve the exact 1,807,847,758-byte MC member, appropriate storage/transfer escalation and DATA selection; establish release/production applicability, truth/filter definitions, input completeness, nominal weights and corrections. A single member is a pilot, not a complete normalization population or background model. |
| 4 | Independent calibrated public bbgg-like methods study | **CONDITIONAL** | Candidate-matched photon/jet/working-point, trigger, GRL/exposure, sample overlap, normalization and uncertainty evidence must pass before a separately authorized calibrated workflow and prospective closure validation. Stored PHYSLITE does not establish compatibility with the ATLAS publication. |
| 5 | Official HH reproduction, signal extraction, physical TF fit, sensitivity or absolute MC prediction now | **STOP** | No matching exact HH signal input has been established, provenance/denominators/tools remain incomplete, and no physical closure has passed. Single-Higgs samples cannot replace HH. A new scoped task and matching physical evidence are required before any such analysis. |

The complete capability-by-capability comparison and prospective protocol are
in [route comparison](phase5d_analysis_route_comparison.md) and the
[capability matrix](../metadata/phase5d_capability_matrix.csv). GO applies to
methods already justified by the preserved inputs; it does not authorize a
new download, tool installation, email dispatch or physical normalization.

## Exact candidate inputs and storage bounds

Published identities are VERIFIED **metadata facts**. All new candidate files
remain NOT_ACQUIRED and their native capabilities NOT_EVALUATED. DSIDs below
are unique exact physics-short joins to the official research metadata, not
native DSID measurements or DAOD-number guesses. Production e/s/r/p tags are
not supplied in these member objects (`tags={}`).

| Role / record | Exact member | Published bytes / Adler-32 |
| --- | --- | --- |
| DATA 2015 run 266919 / 80000 | `data15_13TeV:DAOD_PHYSLITE.37001628._000001.pool.root.1` | 7,394,251 / `1e0e3038` |
| Gamma+jets DSID 364542, Sherpa SinglePhoton pT 35-70 / 80014 | `mc20_13TeV:DAOD_PHYSLITE.37322576._000009.pool.root.1` | 87,201,141 / `346325ac` |
| Prompt diphoton DSID 364352, Sherpa 2.2.4 myy 90-175 / 80014 | `mc20_13TeV:DAOD_PHYSLITE.38191666._000047.pool.root.1` | 1,807,847,758 / `58533a66` |
| Gamma+jets DSID 364543, Sherpa SinglePhoton pT 70-140 / 80014 | `mc20_13TeV:DAOD_PHYSLITE.37322584._000156.pool.root.1` | 476,512,859 / `fca46c9e` |

The DATA choice is the smallest on the **inspected first page: 5 of 131 run
indices**, not a demonstrated global minimum or a photon-rich dataset.
The MC choices are the smallest in their respective inspected process
indices (65, 19 and 146 members), useful only for prospective pilot scoping.
The official [DATA paginated metadata](https://opendata.cern.ch/record/80000/filepage/1?group=1)
and [QCD record API](https://opendata.cern.ch/api/records/80014) establish
these tuples. Raw response hashes and limitations accompany each manifest row.

DATA + gamma+jets 364542 has **94,595,392 input bytes**. DATA + prompt
diphoton 364352 has **1,815,242,009 input bytes**. These are exact input-only
lower bounds, excluding installations, caches, calibrations, retained copies,
outputs, metadata and transfer reserve. No numerical full installation/RAM/CPU
estimate is justified; those quantities remain UNKNOWN, not zero.
Fitting the current 128 MiB Phase 5 charged transfer budget does not approve a
new member; metadata and per-operation reserves consume that same budget.

The [candidate audit](phase5d_research_dataset_candidates.md) and
[dataset manifest](../metadata/phase5d_dataset_manifest.csv) cover ten exact
physical candidates: one DATA, four photon-background MC and five single-Higgs
MC, plus explicit unresolved DATA2016 and HH roles. The scoped search of 94
nominal Higgs, 55 Higgs-variation and 14 exotic process-index names identified
no matching HH->bbgg candidate. Global HH availability remains UNKNOWN; no
universal absence claim follows from these inspected collections.

## Production and tool blockers

The exact approved educational DSID 302521 member remains NOT_ACQUIRED:
`ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root`,
110,755,804 bytes, published Adler-32 `b43248ea`, [record 93922](https://opendata.cern.ch/record/93922).
Its catalog identity does not prove storage readability or native contents.

The later v1.0.0 tag points to a 2025-06-17 commit; its archive was published
2025-07-02. The date-bounded 2025-02-15 commit is an immutable comparison
candidate, not an established FEB2025 producer. The inspected February skim
has an unclosed bracket at line 413 in untouched official source; independent
AST-only checks witness an upstream candidate limitation, **not a project
regression failure**. None of these sources has been repaired or substituted
for actual production logs.

Both inspected versions copy `generatorWeight_NOSYS`; neither proves the
nominal vector index of the released file. Candidate 642000 sums lack a complete
unique-input signed pre-skim ledger. The February `corrected_xsec` can already
contain sigma, filter efficiency and k-factor, whereas later code exports
separate factors. An additional multiplication could therefore duplicate
factors. Exact e4045/filter, branching-ratio, correction-object populations,
sentinel and BTAG/FTAG overlap applicability remain unresolved. No candidate
factor was applied. See [exact provenance review](phase5d_provenance_review.md).

Existing ROOT 6.40.04 / C++20 can conditionally inventory supported native
numeric research branches and compute primitive quantities after file/type/unit
checks. xAOD ElementLinks, aux stores and decorated-object APIs require a
compatible verified implementation. ATLAS calibration/efficiency/systematics
require applicable CP tools/configuration/payloads, beyond ROOT alone.
The public [research container guidance](https://opendata.atlas.cern/docs/tutresearch/containers)
shows AnalysisBase **25.2.2 as an example**. Its precise candidate/tool/platform
compatibility is UNKNOWN; a later educational 25.2.40 example is not substituted.
Modern CP tutorial interfaces are not assumed to exist in that older release.
Any prospective ATLAS runtime must remain isolated from the conda compiler,
ROOT and library paths. No environment was changed or installed.

Truth links/flavour fields, DL1dv01 b-tagging information and trigger matching
are documented research capabilities, not successful native observations.
DL1dv01 is not evidence for GN2; matching is not trigger decision/prescale/SF;
release-level luminosity is not the exposure of a selected member. Exact
candidate calibration/systematic support remains unverified. The
[toolchain assessment](phase5d_toolchain_requirements.md) records these gates.

## Preserved sideband evidence and prospective closure

Historical DATA has 63,095 cached rows; C9=1,689, with 1,374 sideband events and
315 central events excluded from sideband statistics. Existing selections,
provisional units, no ID/b-tag/trigger selections, frozen protocol and outputs
are preserved. The pooled Pearson/Spearman coefficients remain
0.195744506755729 / 0.189009069888946; A/B mass KS D remains
0.082132128127478 and Cramer's V 0.084597473384167. These are dependent
descriptive diagnostics, not calibrated p-values or a physical closure PASS.

Fixed identity-SHA folds remain 724 calibration / 650 validation sideband
events with no identity overlap. The whole historical sample had already been
observed; both folds remain **retrospective**. In particular fold-1 A has
203 events, and the fixed nine-bin sparse-shape diagnostics and full multinomial
covariance do not establish robustness under calibration/trigger/systematics.
Negative MC weights must not be treated as ordinary multinomial counts.

The prospective protocol requires eligible future physical inputs, verified
truth/filter/weights/tools and sample overlap first; freeze selection, regions,
binning, tolerances, nuisance model and input identities before examining new
validation outcomes. Use new independent input and account for finite MC,
signed-weight covariance and applicable systematics. Do not retune boundaries
on the existing DATA or relabel its folds as untouched. No real-data TF fit,
background prediction, extrapolation into the central region or HH fit was run.
Detailed sequencing is recorded in the route-comparison report.

## Review gates, execution evidence and publication scope

| Gate | State | Meaning |
| --- | --- | --- |
| A | PASS | Every baseline tracked file and retained historical local evidence checked and unchanged. |
| B | PASS | Exact target, sanitized transport evidence and provenance questions finalized; email UNSENT. |
| C | UNKNOWN | Exact FEB2025 producer, nominal weight and complete signed sumW cannot be established. |
| D | PASS | Specific published candidates and scoped unresolved roles identified; no acquisition or suitability PASS implied. |
| E | PASS | Documentary truth/flavour assessment complete; exact candidate native capability remains unverified. |
| F | PASS | Documentary calibration/trigger/exposure assessment complete; no calibration/trigger readiness PASS implied. |
| G | UNKNOWN | Required functions/isolation documented, but supported candidate-matched runtime/platform/payloads unestablished. |
| H | UNKNOWN | Exact input-only bounds known; installation/RAM/CPU/full compute scope unmeasured. |
| I | PASS | Ranked recommendation and prospective physical gates justified. |
| J | PASS | Existing source/build files unchanged and retained actual regression evidence checked. |

Seven documentary/preservation gates PASS; three UNKNOWN. Physical
normalization, calibrated research execution and closure remain BLOCKED by
the stated missing evidence. Gate completion must never be read as physical
analysis acceptance. There is no FAIL manufactured from missing evidence and
no new synthetic framework.

The Phase 5C local audit was executed in Phase 5D; **916 checks PASS**.
Its actual final **CTest 28/28 PASS, zero skipped/failed** is retained historical
evidence. Phase 5D changes only reports/metadata, so CTest was not freshly
rerun, consistent with the task's source/build-change trigger. The retained
compiler is GNU 15.3.0 at
`/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`,
CMake 4.4.4, ROOT 6.40.04, project C++20. ROOT identity was queried anew;
compiler/build/linkage evidence was preserved and checked rather than rerun.
GitHub NO_CHECKS is not CI PASS.

Six final reports (including the UNSENT email), two CSVs, gate JSON and small
evidence projections/preservation manifest are additive text artifacts. Full
metadata bodies and private reviewer receipts stay ignored locally. Phase 5D
made 16 bounded source/metadata HTTP requests, consumed 1,678,884 body bytes
and charged 1,048,576 reserve bytes: increment **2,727,460 bytes**. Current
Phase 5 / cumulative application-accounting totals are **8,422,935 /
86,556,957 bytes**, under their 134,217,728 / 268,435,456 limits. This is not a
measured wire cap; provider-mediated discovery/Git/wire/control traffic is
outside the metered payload evidence. Zero ROOT requests/payload/acquisitions,
container/calibration installs and email dispatches occurred in Phase 5D.

[Quality gates](../metadata/phase5d_quality_gates.json),
[source access](../metadata/phase5d_source_access.json) and
[baseline preservation](../metadata/phase5d_baseline_preservation.json) seal
the evidence and scope. Before push, staged and every outgoing intermediate
commit payload must pass explicit-path, hash, size/binary, known-secret-pattern
and figure checks. No new PDF/PNG/ROOT may be committed; historical local
figure drafts remain AWAITING_USER_APPROVAL. PR #8 remains OPEN / DRAFT.

**Next scientific milestone:** receive official transport/production and
research-tool applicability clarification, then obtain separate exact-member
and isolated-runtime authorization for a bounded native/tool pilot. Physical
closure requires later suitable independent inputs and the frozen prospective
protocol; it has not been started or approved by this documentary audit.

# Phase 0 decision and quality gates

Project: ATLAS_HH_BBGG_PUBLIC_V1. Step: STEP_2_PHASE_0_SOURCE_FEASIBILITY.
Checked: 2026-10-09 UTC. **STATUS: PARTIAL**.

**Decision: conditional GO for a small schema/methods validation; NO-GO for claiming reproduction of the official ATLAS HH measurement with the currently verified inputs.** This is an audit conclusion, not an executed physics result. The evidence and references are in [phase0_feasibility.md](phase0_feasibility.md), [sources.md](../metadata/sources.md), and the [input inventory](../metadata/public_input_inventory.md).

Route classification: **PARTIAL_FEASIBILITY** overall; **GO_METHOD_ONLY** as the proposed next route after a separately approved first-file check. **GO_EVENT_LEVEL** and **GO_STATISTICAL_PUBLIC_INPUTS** have not passed their input-validation gates. Official-result reproduction is NO-GO with the currently verified inputs.

## Repository and Step 1 preflight

PR [#1](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/1) already reported **MERGED** when this task inspected GitHub, at `2026-10-09T07:51:05Z`. No merge was performed by this task, so no new merge-confirmation action was necessary. Its base is `main`; its expected feature head is `be3e3d0c647b4a7c825b20abcc24db5d1aeb4edc`; its main merge is `41d1a63daac0bc789a03c77daf091c9424b712cb`.

All ten changed files and the complete diff were inspected. They contain ROOT/C++20/CMake environment, setup documentation, smoke tests and environment lock infrastructure. No physics event-analysis code, private data, credentials or unintended files were identified. The 186 explicit conda package URLs are anonymous conda-forge URLs with SHA256 checksums. The merged infrastructure equals the feature-head contents.

At inspection, main protection required zero approving reviews and no CI checks; admin enforcement and conversation resolution were enabled, and force-push/deletion were prohibited. Reviews and check rollup were empty. **CI status: NO_CHECKS, not CI PASS.** No protection setting, history or branch deletion was changed.

The existing `atlas-hh-root` environment was activated and the unchanged validator actually executed:

```bash
cd /mnt/c/HH
source /home/btu/miniforge3/etc/profile.d/conda.sh
conda activate atlas-hh-root
bash scripts/validate_step1.sh "$HOME/build/atlas_hh_bbgg_public_v1_merge_review_20261009T075741Z"
```

| Check | Actual result |
| --- | --- |
| ROOT | 6.40.04 |
| C++ standard | 20, required, extensions off |
| CMake compiler | GNU 15.3.0; `/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++` |
| ROOT/compiler compatibility | ROOT reports C++20; CMake uses the conda compiler; ROOT/libstdc++/libgcc runtime linkage resolves in the same environment |
| CMake / Ninja | 4.4.4 / 1.13.2 |
| Fresh build / smoke | PASS / PASS |
| ROOT I/O / RDataFrame / RooFit-RooStats | PASS / PASS / PASS |
| CTest | 3/3 passed, zero failed, 2.69 seconds |

The first rerun using an existing cache stopped at a validator guard: it recognized only `FILEPATH`/`STRING`, while the otherwise correct compiler cache entry had type `UNINITIALIZED`. That run **failed**. Its files and diagnostics were preserved. The documented optional build-directory argument above provided a fresh directory; that full rerun **passed**. No Step 1 source was modified to hide this limitation. RooFit/RooStats tests instantiate infrastructure objects; they do not validate a scientific fit or an ATLAS workspace.

Local ignored transcript: `.local/step1_revalidation_for_phase0.log`. Detailed WSL evidence: `/home/btu/build/atlas_hh_bbgg_public_v1_merge_review_20261009T075741Z/step1_validation_20261009T075742Z.UX7RoI`. Logs remain local and are not part of this audit commit.

After validation, the requested clean-tree/fetch/switch-main/pull-ff-only checks succeeded. Local `main` and `origin/main` both pointed to `41d1a63daac0bc789a03c77daf091c9424b712cb`, with Step 1 infrastructure tracked and a clean working tree. The already existing `feature/phase0-source-feasibility` branch at that same commit was reused. No drafts or Git history were discarded. PC2 and PC3 remain PENDING.

## Phase 0 quality gates

Passing the documentation checks below does not convert missing scientific evidence into a PASS.

| Gate | Status | Evidence / unresolved condition |
| --- | --- | --- |
| A: official publication provenance/version | PASS | Journal DOI, publisher PDF, ATLAS auxiliary page, INSPIRE/Crossref and arXiv versions cross-checked; journal/preprint differences retained. |
| B: candidate identities/provenance | PASS | Public records/DOIs identify GamGam collision, GamGam MC and PHYSLITE umbrella with years, energy, licensing and release tags. |
| C: formats and skims | PASS at documentation level | Flat ROOT GamGam threshold/multiplicity and research xAOD format verified from records. Physical file validation is explicitly deferred. |
| D: object, trigger and normalisation sufficiency | PARTIAL | Documented objects and per-DSID metadata exist; actual schemas, v0/v1 mapping, tight-photon SF, diphoton trigger and matched generated sums are unresolved. |
| E: HEPData numerical/resource inventory | PARTIAL | 30 table DOI descriptions verified. HTML/JSON/YAML/CSV/ROOT exports returned HTTP 403; numerical contents, covariance and workspace attachments are ACCESS_UNVERIFIED. |
| F: official-analysis limitations | PASS | Coverage, selection, calibration, tagging, fit/model and public research-format limitations are stated with references. |
| G: decision and bounded next action | PASS | Conditional first-file schema check chosen; no official-reproduction claim or event-analysis implementation. |
| H: reviewable, reproducible documentation | PASS for audit packaging | Five UTF-8 deliverables, field-level status/evidence, source versions/access dates/checksums and complete diff reviewed. Scientific completeness remains PARTIAL. |

**Overall Phase 0: PARTIAL**, because D and E retain essential unanswered questions. This branch records a completed bounded audit with its access/knowledge limits; it does not approve a full HH analysis, assign fabricated systematic uncertainties, or declare official likelihood reproduction possible.

## Selected candidate and proposed first small-ROOT validation

Choose **collision record 93915** first. Its published GamGam objects are the easiest match to the existing C++20/ROOT infrastructure; MC normalisation can be postponed until a physical schema is known. This choice is an inference from the [record](https://opendata.cern.ch/record/93915) and [variable dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details).

The smallest file in the inspected 16-file record index is:

```text
ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root
size: 17541818 bytes
published checksum: adler32:037f48e7
URI: root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root
```

This file was **not downloaded or opened**. These are published-index properties, not locally verified bytes. It represents a subset of 2015, not the complete 36 fb^-1 release.

Proposed subsequent step, to be approved separately:

1. Re-fetch record metadata; pin filename, size, checksum and source date before any transfer. Fetch only this file with a bounded download and verify the checksum.
2. List ROOT keys/tree names and branch names/types/metadata without an event loop. Check whether the producer's expected `analysis` tree and documented photon/jet/ID/weight names are present. Do not assert that name before inspecting keys.
3. Compare actual types and units against the dictionary and versioned source; resolve `jet_jvt` type, photon SF working point, and any schema difference. Write an evidence report before selecting events.
4. Only after a further analysis gate, consider a small event-read validation with explicit photon/tagging definitions and unit checks. That implementation, plots, selections, MC weights and statistics are outside this Phase 0 commit.

Close the HEPData access/version question and the HH signal-input question before proposing official-result comparisons or a physics likelihood. Stop after the Phase 0 PR is created; do not merge it automatically.

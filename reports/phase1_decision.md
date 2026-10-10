# Phase 1 decision and gates

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1

STEP: STEP_2_PHASE_1_BOUNDED_SCHEMA_VALIDATION

STATUS: **PARTIAL_SCHEMA_VALIDATED**

Physical access, runtime types and a bounded structural sample are verified for one
93915 collision file. The ROOT/C++20 implementation supports its actual native RVec
types. Documentation differs in container types and in the `jet_jvt` element type;
units and working-point semantics remain UNKNOWN. See the [schema report](phase1_schema_validation.md),
[field manifest](../metadata/root_schema_manifest.csv) and [access audit](../metadata/root_access_audit.md).

## Repository prerequisites and preservation

The working tree was clean on `feature/phase0-source-feasibility` before implementation.
GitHub authentication as TOPSONN was confirmed. Default branch `main` contained merged
[PR #1](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/1), expected feature head
`be3e3d0c647b4a7c825b20abcc24db5d1aeb4edc`, main merge
`41d1a63daac0bc789a03c77daf091c9424b712cb`. Local main and origin/main matched.
The Step 1 infrastructure matched its validated feature-head contents, and the
unchanged validator was executed successfully before creating this branch.

The Phase 0 baseline is commit `48c4ff80e61f1b060d8e059c9e9107df327e9e96` on
`feature/phase0-source-feasibility`; [PR #2](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/2)
was still OPEN. This branch, **`codex/phase1-bounded-root-schema`**, starts at that
baseline and its PR targets the Phase 0 branch so that its diff contains Phase 1 only.
Neither existing PR nor this PR is automatically merged. Main, the six original
Step 1 drafts, Phase 0 evidence, diagnostics and Git history were preserved.
PC2 and PC3 remain PENDING.

## Gate results

| Gate | Status | Evidence and exact scope |
| --- | --- | --- |
| A: Git prerequisites | PASS | Clean start, merged PR1/default-main ancestry, Step 1 contents and executed preflight, dedicated branch after checks |
| B: official provenance | PASS | Official 93915/DOI/index; smallest file identity recorded before access; indexed size and Adler-32 match |
| C: bounded physical access | PASS | Exact one-byte HTTP 206 probe; 17.5 MB sample; cumulative ledger below 256 MiB; zero remote ROOT operations; transport/accounting limitations disclosed |
| D: runtime schema/types | PASS | 119 branch metadata rows, 25 requested fields; actual RVec/bool discrepancies explicit and native readers tested |
| E: structural sample | PASS | Exactly ten entries; count/length/type/finite checks passed; file hash unchanged; no physics selection |
| F: unsupported capabilities recorded | PASS | GN2/diphoton trigger/corrections/HH MC/systematics/likelihood gaps and UNKNOWN units/WPs retained |
| G: regression preservation | PASS | Existing three tests preserved; fresh unchanged Step 1 preflight 3/3; combined CTest 5/5 |
| H: reproducible audit artifacts | PASS | Pinned file hash, sanitized access ledger, native generated CSV/summary, environment facts, synthetic tests and reproduction commands |

**Gates FAIL: none.** The PASS gates certify this bounded schema audit, not physics
completeness. Scientific readiness remains partial. GitHub CI has no checks where
reported; absence of checks is **NO_CHECKS**, never CI PASS.

## Stop and next decision

Commit this Phase 1 result and create the separate review PR, then stop.
Do not run reconstruction or statistical analysis. A separately reviewed next phase
may propose a limited reconstruction study only after validating kinematic units and
defining defensible object/tagging semantics. The present result does not authorize
official ATLAS HH reproduction, yields, efficiencies, cross sections, signal strength,
significance, confidence limits or coupling scans.

Unresolved: exact FEB2025 production commit and v0/v1 mapping; RVec documentation
correspondence; JVT threshold; b-tag quantile boundaries/working points; kinematic
units; tight-photon and diphoton-trigger corrections; HH signal MC and normalisation;
systematic and statistical inputs; unverified HEPData/workspace payloads. Only one
file and ten entries have been checked. The EOS body used HTTP, published Adler-32
is non-cryptographic, and packet-level wire traffic was not measured. These limitations
are preserved explicitly rather than converted into successful analysis claims.

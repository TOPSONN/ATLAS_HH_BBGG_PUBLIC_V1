# Phase 5C decision

**FINAL_VERDICT = PARTIAL_STORAGE_BLOCKED.** The support package, DATA-only
method diagnostics, provenance-gap review and route assessment are complete.
The exact continuum input remains unacquired; physical normalization,
background closure, mass-shape transfer and HH interpretation are not validated.
Keep PR #8 OPEN/DRAFT on `codex/phase5-background-normalization`.

## Evidence and gate disposition

The baseline `1c7da77fe4c852c929be39b10544220033de9fec` is preserved.
The [machine gate report](../metadata/phase5c_quality_gates.json) seals source,
reports, aggregate diagnostics and actual local execution evidence by SHA-256.
All 190 prior tracked payloads and 407 retained local evidence files were
checked independently. CMake retains its prior prefix and adds an opt-in
Phase 5C target/tests. Original ROOT files, selection, figures, source snapshots,
receipts, results and Git history are unchanged.

| Gate | State | Meaning and remaining limit |
| --- | --- | --- |
| A: Historical baseline | PASS | Tracked and ignored local hashes preserved; CMake append only. |
| B: CERN support package | PASS | Exact-member request and sanitized evidence prepared; **UNSENT**. |
| C: New input access | BLOCKED | No 302521 ROOT payload or completed storage verification. |
| D: Local checksum/schema | BLOCKED | No acquired file; native checksum/schema and 10/100/10000 stages not executed. |
| E: MC generator provenance | UNKNOWN | Documentation assessment complete; exact e4045/FEB2025 applicability and normalization ingredients unresolved. |
| F: DATA dependence | PASS | Frozen-protocol descriptive diagnostics executed; no independence/physical-transfer approval. |
| G: Held-out methodology | PASS | Canonical SHA identities, disjoint fixed folds and central exclusion; retrospective, previously viewed DATA. |
| H: Research route | PASS | Scoped documentary GO/CONDITIONAL/STOP assessment; no research acquisition/tool/calibration PASS. |
| I: Unsupported prediction | PASS | No physical TF, background prediction, normalization, fit, signal extraction or sensitivity claim. |
| J: Regression/reproducibility | PASS | Final CTest **28/28**, compiler/linkage and exact integrated-output identity verified. |

No gate FAIL is recorded. Gates C/D remain BLOCKED and E UNKNOWN; passing
engineering gates cannot override them. The physical closure status is
**NOT_EVALUATED**. Historical Phase 0 PARTIAL and Phase 5B storage-blocked
verdicts remain unchanged.

## Actual DATA result

[Sideband evidence](phase5c_sideband_dependence.md) uses the exact prior
63,095-row DATA cache and unchanged PROVISIONAL selection. C9 remains 1,689;
315 central-window rows are excluded from all diagnostic statistics.
Sidebands contain 1,374 events, A/B=443/931. SHA folds contain 724/650
events with zero identity intersection and full sideband union.

Pooled mass-versus-absDeltaEta Pearson/Spearman are 0.195745/0.189009.
Baseline pooled A/B empirical KS D is 0.082132 and 2-by-9 Cramer's V is
0.084597. Calibration and validation A/B D are 0.060262 and 0.138912;
their V values are 0.106824 and 0.134543. Fixed boundaries 0.8/1.0/1.2
and fixed outer trims are descriptive sensitivity probes, with no chosen
best boundary. Full conditional multinomial covariance, counting intervals,
sparsity and disconnected-support limits accompany the raw shape fractions.

The finite-sample descriptions neither validate a universal physical A/B
transfer nor formally reject equal underlying shapes. No inferential pvalue,
fit or acceptance threshold is introduced. The entire cache was historically
viewed, so these are **retrospective held-out diagnostics**, not a blinded or
untouched validation. Disjoint identities do not prove IID sampling.

The final synthetic suite passed 20 methods /67 app invocations
(29 accepted,38 rejected); the documentation transport suite passed 23
offline mocked methods. Independent Python checked all raw cache identities
and selection, sideband join, correlations, KS/V, covariance and 150 defined
Wilson intervals. The final integrated ROOT/C++ output matches all four
focused final output files byte for byte. Per-event output stays ignored;
only the aggregate 1962-row audit is a committed publication input.

## Input, provenance and route decision

The [storage decision](phase5c_storage_decision.md) and
[CERN support draft](phase5c_cern_support_request.md) stop repeated failed
transport paths. Phase 5C's six once-only documentation failures added
393216 reserved charges and zero response-body/ROOT bytes. Totals are
5695475/134217728 Phase 5 and 83829497/268435456 cumulative. These are
application-model charges, not measured wire traffic. No new dataset or
transfer budget is approved. Future supported transport must carry every
receipt forward; earlier downloader totals are stale.

[MC provenance](phase5c_mc_provenance_update.md) preserves signed generator
weights and separates candidate metadata from exact-production applicability.
The frozen generator job does not establish the released e4045 dependency
stack or FEB2025 producer. Exact nominal-weight index/convention, complete
signed pre-skim sumW, completeness, filter population/efficiency, sigma/decay
conventions, invalid SF handling and overlap remain unresolved. Physical
normalization and correction/SF application stay disabled. Selected/sampled
weights are not a generated denominator.

[Route assessment](phase5c_analysis_route_assessment.md):

- **Educational GamGam GO** for preserved bounded raw counts, numerical
  checks and method diagnostics; **CONDITIONAL** for the already approved
  302521 intake; **STOP** for calibrated yields, official WP efficiencies
  or an HH result with currently verified inputs.
- **Research PHYSLITE CONDITIONAL** for a separately authorized, bounded
  native schema/truth/tool pilot. Richer documented fields do not verify
  physical links, calibration, GRL/exposure, nominal weights, appropriate
  continuum/HH signal or full systematics/likelihood. Previously inspected
  relevant single-H members exceed present budgets and are not HH samples.
- **Recommended route:** keep the existing raw study as a preserved result;
  obtain support evidence and exact-provenance information, then decide on
  a documentation-first research pilot with explicit input/tool/storage
  authorization. Do not add unsupported physics features to the flat route.

The official source snapshots used here were rehashed locally and retain
their historical acquisition dates. Fresh documentation access is UNVERIFIED;
six `URLError` results supply no cause or global availability conclusion.
No research ROOT file, tool container or calibration package was downloaded.

## Environment, reproduction and publication

Actual ROOT is **6.40.04**, project and ROOT standard **C++20**, GNU compiler
**15.3.0** at
`/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`,
CMake **4.4.4**. All 38 actual compile commands use that compiler and
`-std=c++20`; ROOT and libstdc++ runtime paths point into the same conda
environment. Host libc/loader are normal system dependencies. No environment
or unrelated toolchain was changed.

From the existing activated environment:

```bash
bash scripts/validate_phase5c.sh /home/btu/build/NEW_PHASE5C_BUILD
python -B scripts/freeze_phase5c_baseline.py metadata/phase5c_baseline_manifest.json --verify
python -B scripts/audit_phase5c_evidence.py --local
```

The validation wrapper is offline and requires an external compatible build
directory. `--local` additionally needs the preserved ignored evidence; the
offline published-artifact audit works without that flag. The separate
explicit DATA-cache reproduction/audit commands are in the sideband report.
Initial output and first validation evidence are retained separately from
the final label-clarified execution. No previous evidence was rewritten to
manufacture PASS. GitHub **NO_CHECKS** is distinct from the local CTest result.

No physical-study PDF/PNG was generated for Phase 5C. Historical local
drafts remain **AWAITING_USER_APPROVAL**; no new figure version is approved
or pushed. Older synthetic regressions create disposable mock PNG fixtures;
those are not study figures and are excluded from publication. Stage explicit
source/report/metadata paths and inspect the index and every outgoing commit
payload before pushing. Keep PR #8 draft, preserve its Phase 4 base and stop
after source/text delivery. Do not merge a PR or begin HH signal extraction.

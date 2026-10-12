# Phase 5B decision

**FINAL_VERDICT = BLOCKED_STORAGE_ACCESS.** Engineering regression and bounded
DATA-only descriptive diagnostics pass; the authorized302521 continuum file
is still inaccessible and physical model readiness is not established.

| Gate | Actual disposition | Scope and blocker |
| --- | --- | --- |
|A Historical preservation|PASS|164 tracked and269 local historical files verified; CMake append only; binaries compared raw|
|B CERN source identity|PASS|Fresh exact record/path/size/published checksum and current job response identified; no acquired ROOT checksum claim|
|C Bounded transport integrity|BLOCKED|Metadata accounting/caps pass; exact XRootD stat timed out and no proven usable metered bulk route|
|D Physical ROOT schema|BLOCKED|No acquired302521 file; actual tree/branches/types/DSID are NOT_EVALUATED|
|E Shared reconstruction closure|BLOCKED|Synthetic Cartesian/regression checks pass;302521 reconstruction/edge migration has no physical run|
|F Generator-filter applicability|UNKNOWN|Witnessed current job uses partonic mHat settings; exact e4045/FEB2025/filter pair not mapped|
|G Nominal generator weights|UNKNOWN|Nominal index and complete signed pre-skim denominator applicability are unverified|
|H Dataset/selection compatibility|UNKNOWN|Inclusive jets, trigger/ID/calibration and exact producer/skim equivalence not established|
|I DATA-only diagnostics|PASS|Preserved63095-entry cache; C9=1689;1374sideband events; descriptive only|
|J Regression/scientific integrity|PASS|Fresh ROOT6.40.04/C++20 build,26/26 CTest; physical guards and historical evidence preserved|

There are **no final FAIL gates**. BLOCKED and UNKNOWN are not PASS and not
failed executed physics tests. Physical schema, entry stages10/100/10000,
reconstruction, native weight observations and cutflow for302521 have
**0 entries processed / NOT_EVALUATED**. A metadata preflight's34 synthetic
checks do not certify DSID values or physical event integrity. Its conditional
plan explicitly stops at the missing raw native-first10 wrapper after any
future acquisition; StageB cannot start until StageA is actually executed.

## What advanced

Windows-vs-WSL DNS/TCP/TLS/proxy diagnosis and one exact official metadata-only
XRootD probe replace blind failed-route retries. The new transfer ledger
preserves the original failed receipt and all historical charges. Phase5
total is5,302,259 bytes; cumulative is83,436,281; new ROOT payload is0.
The scoped CERN CA trust was validated, certificate/hostname verification
stayed enabled, and no unmetered copying or remote ROOT streaming occurred.

The current official job source was acquired, response/content hashed and
bound to its API-reported commit. It configures `PhaseSpace:mHatMin/Max`, not
an explicitly witnessed mass cut on the two highest-pT saved truth photons.
This does not recover exact e4045 applicability or generated acceptance at
the reconstructed160GeV boundary. Candidate18.282pb,0.44191,k=1 and642000
aggregate fields remain candidates; nominal semantics, processing completeness,
BR/filter conventions, exposure and SF validity remain UNKNOWN/BLOCKED.
No selected-event sum is substituted for a normalization denominator.

The new DATA app reuses unchanged Phase3 cuts and the preserved Phase4 cache,
without reopening native ROOT data. Exact A/B and sideband endpoints remain
unchanged. The actual integrated binary reproduced all four independently
checked DATA outputs byte for byte in a new local directory:
`outputs/phase5b_v1/data_sidebands_integrated/`.
The [aggregate CSV](../metadata/phase5b_region_diagnostics.csv) publishes
descriptive values without event identities; detailed local versions remain
preserved. The DATA study generated no PDF/PNG. Historical regression drivers
did create temporary synthetic PNG fixtures during CTest; these are
unapproved `LOCAL_DRAFT` test artifacts excluded from staging/push. They are
not new physical-study or publication figures, and successful CTest does not
approve them. Temporary cleanup follows the unchanged old test suites.

## What the DATA observations permit

A has443 sideband events (217lower,226upper); B has931 (390lower,541upper).
The sideband widths are15 and30GeV, so equal raw occupancies are not expected.
Pooled Pearson(m_gg,absDeltaEta)=0.19574 and Spearman=0.18901; A fractions
are35.75% lower versus29.47% upper. These descriptions do not establish
independence, significance, prompt purity, continuum dominance or closure.
The small signed-deltaEta correlation is not a test of the absolute split.

Fixed boundaries, outer trims, counting intervals, pseudowindow occupancies
and deterministic identity folds are reported as retrospective design
diagnostics. A future frozen, contamination-aware prediction into a withheld
mass interval inside A is more relevant than assuming B is mass-independent.
No such prediction or independent holdout validation has been executed;
historical DATA were already viewed, so no blinding claim is made. Neither
the real central-window population nor these counts tunes a TF or HH fit.
Single-H contamination remains UNKNOWN.

## Validation and delivery

The existing atlas-hh-root environment remained ROOT6.40.04/C++20, GNU15.3.0,
CMake4.4.4. Actual compiler is
`/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`;
ROOT and compiler runtimes resolve inside that same prefix, with normal host
libc/loader. The fresh external CMake build compiled36 translation units.
CTest passed26/26, including Step1 3/3 and all prior Phase1-5 regressions.
New tests executed34 metadata checks/19 rejections,40 mock networking tests
and14 sideband tests. Tests are synthetic; the separate actual cache run is
bounded DATA descriptive validation. The quality JSON binds run/source/log
and output identities. GitHub CI remains NO_CHECKS.

Reproduce offline after activating the existing environment:

```bash
bash scripts/validate_phase5b.sh /home/btu/build/NEW_PHASE5B_BUILD
python -B scripts/freeze_phase5b_baseline.py metadata/phase5b_baseline_manifest.json --verify
```

The freezer needs the preserved local evidence; the synthetic build requires
no remote service or input data. The source-only validator wrapper has a
shell syntax check; the actual fresh integrated run used an equivalent
logged wrapper with the same targets/options/compiler. No successful
regression or visual QA constitutes final figure approval.

Delivery stays on `codex/phase5-background-normalization`, adds scoped
source/tests/reports/metadata to existing draft PR#8 and preserves its
Phase4 base/history. All outgoing intermediate commit payloads must be
inspected for unapproved PDF/PNG and unintended ROOT/binary/secrets before
push. No PR merge, branch deletion or force push is authorized or performed.
Existing local figures retain their prior approval status; no new figure
approval or publication is implied by this task.

The next step is official storage support plus exact e4045/producer/nominal
aggregation evidence. Then perform a newly metered acquisition and explicit
physical StageA/B/C gates. Continue a frozen sideband validation design only
after its inputs and independent closure protocol are established. Physical
normalization, combined samples, TF prediction and HH fitting remain blocked.

Detailed evidence: [storage](phase5b_storage_access_review.md),
[schema](phase5b_continuum_schema.md), [filter](phase5b_generator_filter_review.md),
[weights](phase5b_weight_provenance.md), [DATA](phase5b_data_sideband_diagnostics.md),
[gates](../metadata/phase5b_quality_gates.json).

# Phase 4 local MC validation (ROOT 6.40.04 / C++20)

The current physical result is **PARTIAL with Gate C FAIL**, despite17/17 passing
software regression tests. Read [the reconstruction report](../reports/phase4_mc_reconstruction.md)
before using any output. No normalized prediction, calibrated b-tag label or
official matching efficiency is supplied.

## Build and regression

Use the existing dedicated environment. Choose a build directory that does not
already exist; the validator refuses reuse to avoid stale build evidence.

```bash
cd /mnt/c/HH
source /home/btu/miniforge3/etc/profile.d/conda.sh
conda activate atlas-hh-root
bash scripts/validate_phase4.sh /home/btu/build/atlas_phase4_reproduce_01
```

This explicitly enables Phase1-4, enforces C++20 and the ROOT-matched conda
compiler, checks compile commands and library linkage, and runs all17 tests.
The verified build for the recorded run is
`/home/btu/build/atlas_phase4_mc_truth_v1`; its final test log is
`.local/phase4_final_regressions_v2.log`. The final reader safety-guard build is
`/home/btu/build/atlas_phase4_final_review_v1`, tested in
`.local/phase4_final_regressions_v3.log`. The existing Step1 and Phase3 validators
were also run separately. Passing software tests cannot override physical gates.

## Bounded inputs

Original files are under `.local/phase4_access_20261011/` (Windows `C:\HH\.local\phase4_access_20261011`).
ROOT files are ignored and must not be staged. Metadata and summaries are under
`metadata/phase4_*`; local per-event diagnostics are under `outputs/phase4_v1/`.
Never overwrite these retained versions.

`python scripts/fetch_phase4_samples.py --help` documents the downloader. It uses
the official index, pins exact file identities, verifies checksums, supports
charged resume, and limits new/cumulative transfer to128/256 MiB. Reuse the
verified existing cache whenever possible; a new audit must preserve prior
charges and budget all retries/metadata requests. It explicitly allows the
official public HTTP storage redirect with checksum checks; it does not promise
end-to-end TLS. No remote ROOT event operations are used.

## Physical stages and reproduction

Recorded stages were native schema [0,10), reco-unit [10,100), and separate truth/
scalar [0,10) then [10,100) probes, followed by reconstruction [100,10000).
The original prefix truth helper is preserved locally as
`.local/phase4_probe_truth.py`; its cached physical_probe.json and raw CSV evidence
are hashed in the checksum manifest. It also updated transfer accounting and
must not be blindly rerun against that ledger. The following portable C++ tools
can reproduce the native checks and raw truth/scalar diagnostics into **new**
directories without editing the original ledger or evidence:

```bash
build=/home/btu/build/atlas_phase4_reproduce_01
cache=.local/phase4_access_20261011
sample=ODEO_FEB2025_v0_GamGam_mc_343981.PowhegPythia8EvtGen_NNLOPS_nnlo_30_ggH125_gamgam.GamGam.root
mkdir -p outputs/phase4_reproduce_01/343981
out=outputs/phase4_reproduce_01/343981
"$build/inspect_root_schema" --input "$cache/$sample" --tree analysis \
  --manifest "$out/branches.csv" --summary "$out/schema.txt" \
  --evidence PHYSICAL_MC_343981_REPRODUCTION --max-entries 10
"$build/probe_kinematic_units" "$cache/$sample" "$out/units_raw.csv" 10 100
python scripts/audit_phase4_units.py "$out/units_raw.csv" 343981 "$out/reco_units_v2.json"
# Separate prefix diagnostics, after successful schema/reco-unit checks.
"$build/phase4_mc_reconstruction" "$cache/$sample" "$out/prefix10" \
  343981 0 10 1 PROVISIONAL metadata/phase3_selection_config.ini
"$build/phase4_mc_reconstruction" "$cache/$sample" "$out/prefix90" \
  343981 10 100 1 PROVISIONAL metadata/phase3_selection_config.ini
# Main range only after the direction/unit gates; this particular DSID exits1.
"$build/phase4_mc_reconstruction" "$cache/$sample" "$out/reconstruction" \
  343981 100 10000 1 PROVISIONAL metadata/phase3_selection_config.ini
```

These reproduction prefix commands use the C++ reader and produce reconstruction/
truth/scalar rows, rather than byte-identical copies of the original Python probe
JSON. They reread existing file indices and must be logged separately, never
added to the recorded29,700-event cutflow. The driver accepts only explicit local
inputs, new output paths, expected DSID, ranges no larger than10000 and PROVISIONAL
units. Use the other exact filenames from the transfer ledger for346214/423103;
their recorded main runs exited0. A numerical failure is expected for343981,
must retain exit1, and must not be hidden by a shell success override.

For the original cached outputs, the report auditor performs no ROOT event reads:

```bash
python scripts/audit_phase4_matching.py \
  outputs/phase4_v1/343981/reconstruction \
  outputs/phase4_reproduce_01/343981/matching_audit.json
python scripts/audit_phase4_run.py \
  --access-dir .local/phase4_access_20261011 \
  --run-dir outputs/phase4_v1 \
  --output-dir outputs/phase4_evidence_reproduce_01 \
  --regression-log .local/phase4_final_regressions_v3.log \
  --physical-log .local/phase4_physical_run.log \
  --remaining-log .local/phase4_remaining_run.log \
  --execution-source-manifest outputs/phase4_evidence_v3/phase4_run_manifest.json
```

It rehashes the physical inputs, reproduces raw cutflow from cached rows, checks
matching denominator closure and prior-artifact preservation, and writes nine
portable CSV/JSON artifacts. Its success means **report consistency**, while its
quality-gates JSON retains physical C FAIL. Do not invoke Python with `-O` because
these audit assertions are the checks. The original final evidence output is
`outputs/phase4_evidence_v4/`; reviewed copies are under `metadata/`.
The audit command requires the preserved ignored v3 manifest as the original
physical-execution source snapshot. A checkout alone does not contain all local
inputs or snapshots; do not replace that snapshot with hashes of current source
and claim a fresh physical execution. The reviewed run manifest preserves both
original-execution and final reviewed source hashes.

## Git and figures

Phase4 is stacked directly on Phase3 commit830af3031da80c1c5f3c01ccec22e3619e95f41f,
independent of plotting PR6. The existing shared source, DATA results and cuts
remain unchanged. No PR is automatically merged.

No Phase4 PDF/PNG exists. Native diagnostic ROOT files remain local. Any future
rendered figure is LOCAL_DRAFT, may progress through QA_PASSED and
AWAITING_USER_APPROVAL, and needs exact-version approval before
APPROVED_FOR_PUSH/PUSHED. Inspect staged and all outgoing commit payloads before
every push, following [AGENTS.md](../AGENTS.md).

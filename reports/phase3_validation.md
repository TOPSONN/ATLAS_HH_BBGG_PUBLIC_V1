# Phase 3 selection validation

Executed 2026-10-10 UTC. **CTest 11/11 PASS** after the final source changes.
Step 1 and Phase 1/2 regressions are included. Fresh integrated main had already
passed Step 1 3/3 and Phase 1 5/5 before feature work; Phase 2's final fresh build
passed 9/9. Git Gate A was satisfied on main f7a3420155bd557e4146fd1959a60f68742ea930.
This Phase 3 feature is stacked on the unmerged Phase 2 branch; the new features
are not yet in main. GitHub missing CI checks are NO_CHECKS, not CI PASS.

## Numerical and execution coverage

- **37** selection boundary/configuration cases: strict pT and outer eta cuts,
  crack endpoints, inclusive mass endpoints, nextafter values around thresholds,
  multiplicities, NaN/infinity/negative mass, ordered cached candidates, missing
  jets, configurable thresholds, determinism and bad/unknown/duplicate config.
- **9** driver cases: exact synthetic cutflow, invalid-event rejection, UNKNOWN
  unit gate, duplicate/reversed entries, byte-identical repeated synthetic cutflow,
  output preservation, nonboolean flags, malformed numeric values and forbidden
  event-weight configuration. The synthetic feature rows test selection predicates;
  independent four-vector construction is tested separately by Phase 2.
- Preserved regressions: 22 schema and 8 bounded-transfer cases; 1,033 kinematic
  assertions including 500 independent Minkowski checks; 12 native-reader cases;
  10 Phase 2 driver and 7 unit-evidence cases. Tests were not weakened.

An independent Python pass over the existing derived cache reproduced all ten
C0-C9 integer counts and both optional raw-flag counts exactly. It checked one
contiguous entry sequence [100,63195), rejection arithmetic, both fraction
denominators and all histogram fill/in-range/flow identities. This check rereads
only derived CSV values, not ROOT events, and does not revalidate physical units.
The synthetic driver verifies deterministic repeated outputs in two fresh dirs.

The Phase 3 driver owns local TH1D objects detached from directories and local
canvases, uses ROOT batch mode, rejects existing output paths before writing, and
rejects malformed/cache-order errors before creating real outputs. No ROOT input
reader or remote client is used by Phase 3. The public wrapper verifies the cache
against the Phase 2 artifact hash and permits only VERIFIED/PROVISIONAL unit
evidence with the recorded permitted reconstruction verdict.

Initial compilation emitted four misleading-indentation warnings. They were
fixed without changing cut predicates; the initial log is preserved. Stream
errors are now enabled for CSV/inventory/summary writes. Final rebuild plus all
11 tests passed with zero compiler warnings. Historical reports and earlier
failure evidence remain intact.

## Actual toolchain

ROOT **6.40.04**, project and ROOT **C++20**, required ON, extensions OFF;
GNU **15.3.0** at
`/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`;
CMake **4.4.4**, Ninja **1.13.2**, existing `atlas-hh-root`.
All **16** compile commands use that compiler and `-std=c++20`. `ldd` resolves
ROOT Core/Hist, libstdc++ and libgcc_s inside the same conda prefix; none are
missing. System libc/runtime infrastructure is not mistaken for a second C++
toolchain. No unrelated environment was changed. PC2/PC3 remain PENDING.

## Reproduction and storage

From the repository in Ubuntu WSL with the existing environment:

```bash
source /home/btu/miniforge3/etc/profile.d/conda.sh
conda activate atlas-hh-root
# Must be a new build directory; validators refuse existing build paths.
bash scripts/validate_phase3.sh "$HOME/build/atlas_hh_phase3_reproduce"
# Uses the locally generated checksum-pinned Phase 2 cache, not a dataset URL.
bash scripts/run_phase3_cache.sh \
  outputs/phase2_20261010T092242Z/events.csv \
  outputs/phase3_reproduce \
  "$HOME/build/atlas_hh_phase3_reproduce"
```

Actual build: `/home/btu/build/atlas_phase3_20261010T092242Z`.
Actual derived output: `outputs/phase3_20261010T092242Z`.
Actual logs are retained under ignored `.local/multiphase_20261010T092242Z/`:
`phase3_validation.log` (initial build), `phase3_final_validation.log`,
`phase3_cutflow.log`, `phase3_linkage.log`, and `phase3_validation.json`.
Reports/configuration/small labelled PNGs/machine summaries are tracked;
collision ROOT inputs, event caches, builds and generated local outputs remain
ignored. A fresh clone must reproduce the authorized Phase 2 cache or retain its
exact local bytes before the pinned wrapper can run. Git stores these CSVs with
LF; their manifest hashes are checked against staged Git blobs before publication.

The original collision input SHA-256 remains
`01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7`.
All Phase 2 artifact hashes were rechecked unchanged. No new ROOT entry reads
or remote dataset bytes were added. The prior charged 18,883,874 bytes remain
within the cumulative 268,435,456-byte (256 MiB) budget; historical packet-wire
accounting limitations remain. Physics claims remain constrained by provisional
units, production/calibration uncertainty and skim conditioning.

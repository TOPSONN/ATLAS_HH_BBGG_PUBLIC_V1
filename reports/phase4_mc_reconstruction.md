# Phase 4 MC reconstruction and validation

Executed 2026-10-11. **Overall: PARTIAL; physical numerical Gate C = FAIL.**
The software regression suite passes 17/17, but that result does not clear the
physical closure failure described below. No historical DATA value, shared
four-vector function, exploratory cut, tolerance or previous report was changed.
The Phase 3 DATA baseline remains C0=63,095 / C9=1,689; it is not compared to the
MC counts as a luminosity-normalized prediction.

## Inputs and bounded stages

Three files from [official CERN record 93922](https://opendata.cern.ch/record/93922)
were checked against published sizes and Adler-32 checksums; local SHA-256 hashes
are recorded in [the transfer ledger](../metadata/phase4_transfer_ledger.json).
343981 and 346214 are ggF/VBF **single-Higgs** H125 to gamma gamma, not HH.
423103 is the gamma+jet DP70_140 generation slice, not a diphoton mass slice or
complete fake-photon model. See [source audit](phase4_mc_source_audit.md).

| DSID | File bytes | Actual tree entries | Native branches | Reconstructed range |
| --- | ---: | ---: | ---: | --- |
| 343981 | 32,086,416 | 94,082 | 118 | [100,10000), 9,900 |
| 346214 | 14,414,350 | 38,403 | 118 | [100,10000), 9,900 |
| 423103 | 10,489,108 | 26,366 | 118 | [100,10000), 9,900 |

The existing native ROOT inspector examined [0,10). Native reco probes then
examined [10,100); a separate truth/scalar probe revisited [0,100) in two stages.
Reco pT/E, finite eta, phi range, collection sizes and E-squared minus p-squared
consistency passed the declared numeric checks. Scale 1 to GeV and radians remain
**PROVISIONAL**, eta is dimensionless, and exact FEB2025 production/calibration
equivalence is UNKNOWN. The later v1.0.0 source supports context only.
Truth directions passed their separate checks; signed negative truth-jet mass
was preserved and is not an input to geometry or an inferred truth energy.

There are **29,700 newly reconstructed events** and **30,000 distinct file
indices inspected**, plus recorded prefix revisits and one repeat diagnostic
read of DSID343981 entry5888. The main ranges have no duplicate DSID/run/event
keys across the three files; the first100 were checked separately. This is not
a full-release, cross-prefix identity or physics sample-overlap audit. The three
DSIDs remain separate and no combined yield, shape or process mixture is made.

New charged transfer is **58,856,932 bytes**; cumulative charge is **77,740,806**,
below 128 MiB / 256 MiB. Charges are consumed HTTP bodies plus a 64 KiB reserve
per attempt, not measured wire traffic. Published EOS redirects used public
HTTP storage after validated HTTPS metadata access. No end-to-end TLS assertion
is made; opaque redirect queries are excluded from the ledger. Input SHA-256
hashes are local reproducibility hashes, not CERN-published stronger digests.

## Shared reconstruction and unchanged selection

The native same-entry MC reader supplies ROOT::VecOps::RVec<float> collections to
the unchanged AtlasKinematics functions. Leading objects, m_gg, inclusive m_jj,
DeltaR_gg/jj, photon/jet pT and eta are recorded with DSID/run/event/source index.
Selection reuses AtlasExploratorySelection and the exact
[Phase 3 configuration](../metadata/phase3_selection_config.ini). All 29,700
events passed collection validity checks, independently of the closure result.

These are **raw, unweighted counts**. Every column is a separate generated
process/slice, and every stage is cumulative. No MC weight, scale factor, branching
ratio or luminosity is applied. The first100 probes are excluded from this table.

| Stage | Requirement added | 343981 | 346214 | 423103 |
| --- | --- | ---: | ---: | ---: |
| C0 | Input entries | 9900 | 9900 | 9900 |
| C1 | Valid reconstructed collections | 9900 | 9900 | 9900 |
| C2 | At least two photons | 9900 | 9900 | 9900 |
| C3 | Leading photon pT > 35 GeV | 9794 | 9866 | 9898 |
| C4 | Subleading photon pT > 25 GeV | 9794 | 9866 | 9898 |
| C5 | Both abs(eta) < 2.37; exclude 1.37 < abs(eta) < 1.52 | 9734 | 9816 | 9805 |
| C6 | 105 <= m_gg <= 160 GeV | 9718 | 9663 | 3660 |
| C7 | At least two inclusive jets | 2073 | 2251 | 965 |
| C8 | Leading two jet pT > 25 GeV | 1125 | 1419 | 588 |
| C9 | Leading two jet abs(eta) < 2.5 | 1125 | 1419 | 588 |

An independent Python recomputation from cached event rows reproduces all stages,
and C9 flags, exactly; see [machine cutflow](../metadata/phase4_cutflow.csv).
That consistency check does not waive a failed numerical or physics gate.
The C9 populations are diagnostic counts, not signal/background predictions,
and contain no b-tagging, photon-origin validation or official ATLAS selection.

## Numerical failure retained

Each valid leading pair is compared to an independent long-double Cartesian sum
using the same raw indices and supplied energies. The fixed tolerance is
`1e-7 + 1e-10*abs(reference_mass)` GeV. Negative reference mass squared is not
clamped. The driver preserves outputs and returns exit1 when closure fails.

| DSID | Tested pairs | Failures | Max absolute deviation (GeV) | Result |
| --- | ---: | ---: | ---: | --- |
| 343981 | 12004 | 1 | 1.9124535637071727e-7 | FAIL; exit1 |
| 346214 | 12197 | 0 | 6.3440339023723702e-9 | PASS; exit0 |
| 423103 | 13220 | 0 | 3.3821119627130969e-8 | PASS; exit0 |

The failing diphoton pair is entry5888/run284500/event4385033, has no jets and
does not pass C9. Its own tolerance is 1.1239490151491467e-7 GeV, smaller than
its residual. The retained diagnostic locates precision loss in the ROOT
PtEtaPhiE pair coordinate round trip for nearly cancelled transverse momentum.
Direct Cartesian double and long-double masses differ by about 3.76e-13 GeV.
See [numerical failure report](phase4_numerical_failure.md) for exact raw inputs,
installed-header hashes and the single repeat-read evidence. No event is discarded
or tolerance relaxed, and no MC-only four-vector implementation replaces the core.

## Truth, weights and local diagnostics

Both truth groups are available in the same entry. The native inventory is in
[branch inventory](../metadata/phase4_branch_inventory.csv); no PDG/status/parents,
photon-origin or heavy-flavour labels are exported. Unique global assignment
maximizes cardinality then minimizes total wrapped DeltaR. Photon scans use
0.1/0.2/0.3 and jet scans 0.2/0.3/0.4. Eligibility and the ALL_VALID/C9 denominators
are defined in [matching report](phase4_genmatching_validation.md).
252,915 cached assignment rows passed independent consistency checks across the
three runs. These are **PROVISIONAL same-event geometry** diagnostics; official
efficiency, origin purity and b-flavour purity remain unestablished.

Negative truth-jet mass counts are 1397/2511/731, with minima
-0.19316584/-0.19456349/-0.43305293 in provisional GeV. Their interpretation is
UNKNOWN; neither signed mass nor an invented energy enters matching.
The inspected main ranges contain 14/15/0 negative generator weights, respectively,
with positive counts9886/9885/9900 and no zero weights. Signs are retained, and
synthetic negative-weight tests also pass. The first100 probes encountered only
positive generator weights; that prefix observation is not extrapolated to the
main runs, uninspected samples or complete releases.
Generator sums are diagnostics only, not validated pre-skim normalization.
Native filteff for423103 is 3.9e-5 versus3.93e-5 in later metadata, and generated
sum/production/skim/correction conventions remain unresolved. Negative
ScaleFactor_BTAG values (18/75/103) are separate scalar diagnostics, not negative
generator weights; no correction factor is multiplied.
See [normalization evidence](../metadata/phase4_weight_normalization_evidence.json)
and [b-tag feasibility](phase4_btag_feasibility.md).

Each local reconstruction contains events.csv, cutflow.csv, truth_objects.csv,
matching CSVs, normalization diagnostics, summary and native histograms.root.
Histograms have raw entries, include explicitly counted overflow, and are not
normalized predictions. No Phase4 PDF/PNG was generated. All ROOT input/output
files and individual event rows remain ignored local evidence, with hashes in
[checksum manifest](../metadata/phase4_checksum_manifest.csv).

## Regression and disposition

Fresh Step1 baseline: **3/3 PASS**. Fresh prior Phase1-3 suite: **11/11 PASS**.
Final integrated enabled Phase4 suite: **17/17 PASS**, including22 synthetic
schema cases,8 historical bounded-transfer cases,1033 kinematics assertions,
500 seeded pairs,41 native MC reader cases,4264 matching assertions/600 exhaustive
cases,44 adapter assertions,10 driver cases,8 new transfer and6 cached-unit cases.
The first integrated fixture-path failure and its logs are retained; the final
CMake fixture path was corrected without weakening any test. All previous
tracked metadata/note/reports were compared to Phase3 base and preserved.

Physical runs used the source hashes retained as physical_execution_source_sha256_lf
in the run manifest. A final review added an exact-TTree safety guard and a
persisted-TChain rejection test to the reader. The actual three analysis objects
were already measured to be TTree; this guard leaves their code path unchanged.
The final software was rebuilt/tested separately; original event outputs were
not overwritten or relabelled as a fresh physical execution of that build.
Actual driver exits1/0/0 are evidenced by the preserved subprocess exception and
ACTUAL_EXIT log records, independently of the inferred closure disposition.

Actual ROOT=6.40.04, C++20, CMake=4.4.4, GNU=15.3.0. CMake uses
`/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`;
compile commands and ROOT/libstdc++/libgcc linkage were checked against that
conda environment. These are local executed checks; GitHub CI is assessed separately.
The [regression evidence](../metadata/phase4_regression_evidence.json) records
case counts and log hashes; [matching audit evidence](../metadata/phase4_matching_audit_evidence.json)
records per-DSID cached checks without any additional event reads.

[Run manifest](../metadata/phase4_run_manifest.json) records ranges, hashes and
[gates](../metadata/phase4_quality_gates.json): A/D/I/J PASS; B/F/H UNKNOWN;
C FAIL; E/G BLOCKED. Phase5 full background modelling remains BLOCKED, including
undownloaded appropriate continuum, incomplete gamma+jet coverage, normalization,
truth/calibration uncertainty and the current numerical failure. No HH fit,
significance, limit, coupling or Data/MC agreement claim is made.

Next review should address a shared-core numerical fix in a separately authorized
task with fresh DATA/MC checks, then exact provenance/normalization and a separately
budgeted continuum sample. This Phase4 branch is for partial source/evidence review,
not automatic integration or a claim of physical reconstruction completion.

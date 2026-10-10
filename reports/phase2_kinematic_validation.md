# Phase 2 kinematic validation

Project: ATLAS_HH_BBGG_PUBLIC_V1. Verdict: **PASS_PROVISIONAL_RECONSTRUCTION**.
Checked 2026-10-10 UTC. This is numerical and exploratory validation, not a validated
ATLAS HH analysis or evidence for a Higgs signal.

## Integrated baseline and numerical implementation

PR #3 was merged by a normal merge commit `f7a3420155bd557e4146fd1959a60f68742ea930` after its unchanged
head/diff and repository protection were rechecked. The resulting tree equals the
reviewed Phase 1 tree. Fresh integrated-main Step 1 CTest 3/3 and Phase 1 CTest 5/5
passed, including 22 schema cases and 8 transfer cases. Compiler/runtime checks
passed. **PHASE2_GIT_GATE_A: PASS** before this feature branch was created.

`atlas_kinematics` constructs `ROOT::Math::PtEtaPhiEVector`, sorts by pT with
deterministic kinematic tie breakers, and returns leading-photon/leading-jet pair
mass, signed DeltaEta, wrapped DeltaPhi, and DeltaR. Jets remain inclusive jets:
**m_jj is not m_bb**. Native `TTreeReaderValue<ROOT::VecOps::RVec<float>>` readers
validate physical types, local-only input, friend/external storage exclusion, exact
collection lengths and uint64 identities. Invalid entries retain an explicit reason.

Final fresh feature build: **CTest 9/9 PASS**. Step 1 and Phase 1 are included.
New coverage: 1,033 kinematic assertions, 500 seeded independent Minkowski pair
cross-checks, 12 native reader cases, 10 driver cases and 7 unit-evidence gate cases.
Analytical photons/jets, permutation and pT ordering, ties, angular periodicity,
DeltaR, MeV/GeV scaling, zero/degenerate momentum, negative m^2, NaN/infinity,
collection mismatch, overflow and invalid scales are tested. Independent reference
uses long-double Cartesian sums with metric (+---), rather than ROOT M().
Mass tolerance: `abs(error) <= 1e-7 GeV + 1e-10 * abs(reference mass)`.
Observed maximum absolute deviation: **2.08843e-10 GeV**;
maximum relative deviation: **1.0905e-12**.

Single-object negative m^2 is allowed only within `1e-5 * max(E^2,p^2,1 GeV^2)`,
appropriate to retained Float32 input; its occurrence is explicitly counted and
the supplied energy is unchanged. **Every negative pair m^2 is rejected**, even a
small rounding-sized value. No mass or energy is silently clamped.

An initial synthetic run failed because the new reader did not normalize ROOT
scalar aliases (`Int_t` versus `int`). It was corrected before any new collision
read; the original failed log remains local. File-lifetime resource warnings in
new Python tests were corrected and the two affected suites reran successfully.
Previous scientific evidence and tests were not rewritten or weakened.

## Kinematic semantics and provenance

Eight branch classifications are in [phase2_unit_evidence.csv](../metadata/phase2_unit_evidence.csv).
All remain **PROVISIONAL** for this exact file. Photon/jet pT and E are interpreted
as GeV with scale 1; eta is dimensionless and phi is radians. No branch name alone
establishes units. The physical collection type/length compatibility is verified
for the inspected bounded sample.

The [ATLAS dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
defines the kinematic variables and GamGam >=2 photons with >=25 GeV pT. The
preserved dictionary SHA-256 is `0489c9ce38780d671b1d436e1196fd280c72f29b2a10e9114669865996492c26`.
[PhotonInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0)
and [JetInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0)
explicitly convert pT/E by 0.001 and pass through eta/phi. Their preserved hashes
match Phase 0's source register. Their July 2025 release is later than FEB2025_v0:
**exact-production association remains UNKNOWN**. The current web-tool access
attempts failed; this investigation used hash-verified preserved public snapshots,
not a claim of successful fresh retrieval. See [the original source register](../metadata/sources.md).
[ROOT's vector reference](https://root.cern.ch/doc/master/classROOT_1_1Math_1_1LorentzVector.html)
defines the PtEtaPhiE coordinates and Minkowski metric used by the implementation.

Independent Stage A raw-value checks read entries [10,100), not the previously
inspected [0,10). Photon pT ranges 25.0219–141.553, energy 26.8291–595.241;
jet pT 20.1274–212.556, energy 21.0345–343.791. The proposed GeV scale agrees with
the skim threshold and 13 TeV energy bound; a MeV interpretation with scale 0.001
would put these photons below the documented threshold. Phi lies within +/-pi.
E^2 - pT^2 cosh(eta)^2 is consistent within the declared Float32 tolerance:
minimum photon relative m^2 is -1.92737e-7; jet minimum is +0.000389750.
These checks support the provisional interpretation, not calibration or producer identity.

## Bounded real diagnostics

Input: [official collision record 93915](https://opendata.cern.ch/record/93915),
`ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root`, `analysis`, 119 branches,
63,195 metadata entries; 17,541,818 bytes; Adler-32 `037f48e7`; SHA-256
`01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7`.
Hash before/after processing matches. The 37 failed pairs are scientific evidence,
not a reason to rewrite tests or hide invalid input. They are quarantined.

| Stage | Entry range | New unique entries | Invalid events | Result |
| --- | --- | ---: | ---: | --- |
| Historical Phase 1 | [0,10) | 0 in this task | Not re-evaluated | Preserved |
| A: unit probe | [10,100) | 90 | No gross unit/energy inconsistency | PASS_PROVISIONAL |
| B: diagnostics | [100,10000) | 9,900 | 7 | PASS |
| C: diagnostics | [10000,63195) | 53,195 | 30 | PASS; end of this small file |

No overlapping entry ranges were read. New unique source entries: **63,185**;
including the preserved baseline: **63,195**. Mass histograms use **63,095** events
in [100,63195), of which **37** are rejected for negative diphoton pair m^2.
Accepted diphoton pairs: **63,058**; leading-jet pairs: **17,191**.
Single-object rounding flags: **63,299**. Per-stage invalid fraction must be <=1%
to continue; structural/binding, angular/unit contradiction and energy-overflow
failures abort immediately. Stage C stopped at the actual file end below 100,000.

Raw unweighted TH1D diagnostics: [photon pT](figures/phase2/photon_pt.png),
[photon eta](figures/phase2/photon_eta.png), [jet pT](figures/phase2/jet_pt.png),
[jet eta](figures/phase2/jet_eta.png), [m_gg](figures/phase2/m_gg.png),
[m_jj](figures/phase2/m_jj.png), [DeltaR_gg](figures/phase2/deltaR_gg.png).
No normalization, weights, fit, significance, cross-section, likelihood or HH signal
extraction was performed. Every plot declares its exploratory skim scope and
PROVISIONAL unit status. Underflow/overflow counts are retained in the inventory.
No Higgs-peak requirement is a test. The plotted masses were visually checked for
readable labels and scope text.

No additional dataset download occurred. The established charged public-input
transfer total remains **18,883,874 bytes**, below **268,435,456 bytes**. Packet-level
wire bytes were not measured, as already disclosed in Phase 1.

## Reproduction and artifact identities

ROOT 6.40.04, C++20 required/extensions OFF, GNU 15.3.0 conda compiler, CMake 4.4.4.
After activating atlas-hh-root:

```bash
bash scripts/validate_phase2.sh "$HOME/build/atlas_hh_phase2_reproduce"
bash scripts/run_phase2_local.sh \
  .local/phase1_access_20261009/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root \
  outputs/phase2_reproduce "$HOME/build/atlas_hh_phase2_reproduce"
```

The actual final test build is `/home/btu/build/atlas_phase2_final_20261010T092242Z`.
Actual diagnostics are `outputs/phase2_20261010T092242Z/`: events.csv, stages.csv,
histogram_inventory.csv and phase2_diagnostics.root. Generated ROOT/event caches
remain ignored; small labelled PNGs and checksum metadata are committed.
[Artifact manifest](../metadata/phase2_artifact_manifest.csv) records actual sizes
and SHA-256 values, including source/output identities. ROOT file timestamps can
change binary hashes on a deliberate reproduction; numeric content is the criterion.
[Run manifest](../metadata/phase2_run_manifest.json) records counts and gates.
Local failed/passing logs and Stage A raw evidence remain under
`.local/multiphase_20261010T092242Z/`.

# Phase 1 physical ROOT schema validation

Project: ATLAS_HH_BBGG_PUBLIC_V1. Step: STEP_2_PHASE_1_BOUNDED_SCHEMA_VALIDATION.
Inspection: 2026-10-10 UTC. **Decision: PARTIAL_SCHEMA_VALIDATED.**

One public collision file was physically opened and its actual schema and first ten
entries were checked. Supported native types and structural consistency passed.
Documentation discrepancies and physics semantics remain unresolved. This is not
experimental validation of an HH analysis.

## Input, scope and environment

The complete identity, byte budget, access limitations and reproduction commands are
in [root_access_audit.md](../metadata/root_access_audit.md). The sample is
`ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root`, record
[93915](https://opendata.cern.ch/record/93915), SHA-256
`01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7`.
The actual tree is **`analysis`**, with **119 top-level branches**. All were inventoried;
25 requested fields were structurally read; 94 additional fields were metadata-only
and are labelled `NOT_AUDITED` for documented compatibility.

The user explicitly approved retaining **ROOT 6.40.04 / C++20**, superseding the
attachment's C++17 line. The existing dedicated conda environment was used:

| Environment fact | Actual value |
| --- | --- |
| ROOT / ROOT C++ standard | 6.40.04 / 20 |
| Project C++ standard | 20, required ON, extensions OFF |
| CMake compiler | GNU 15.3.0 |
| Actual compiler path | `/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++` |
| CMake / Ninja | 4.4.4 / 1.13.2 |
| Metadata-only Python | 3.12.15, existing conda interpreter |
| Execution platform | Ubuntu WSL, linux-64 |

CMake uses the conda compiler explicitly and ROOT libraries from that same prefix.
The unchanged Step 1 validator also checked compiler/standard and conda runtime
linkage. No system C++ compiler or unrelated environment was substituted.

## Actual types versus documentation

[root_schema_manifest.csv](../metadata/root_schema_manifest.csv) contains the actual
branch spelling, native type, scalar/collection structure, TLeaf metadata, documented
expected type, compatibility verdict and evidence for every field. Its SHA-256 is
`a4692e9abffaada1418647d552994938f040616fafe407d95fbf6e9dad947ffc`.
The machine-readable outcome is [root_schema_summary.txt](../metadata/root_schema_summary.txt).

Expected types come from the [ATLAS 13TeV25 dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details),
using the preserved Phase 0 snapshot (2026-10-09 UTC; HTML SHA-256
`0489c9ce38780d671b1d436e1196fd280c72f29b2a10e9114669865996492c26`).
The webpage returned 403 through the web fetcher during this phase, so the previously
verified snapshot was used rather than claiming a fresh dictionary download.
Actual types come from the physical file using `TBranch::GetExpectedType`, `TClass`
and `TLeaf`. ROOT [RVec documentation](https://root.cern.ch/doc/master/classROOT_1_1VecOps_1_1RVec.html)
describes its collection interface; the installed ROOT 6.40.04 headers were used to
compile the actual reader types.

| Fields | Actual native type / structure | Documented expectation | Outcome |
| --- | --- | --- | --- |
| `photon_n`, `jet_n` | `Int_t`, scalar | int | MATCH |
| Photon and jet `pt/eta/phi/e` | `ROOT::VecOps::RVec<float>` | vector<float> | Container difference, native reader verified |
| Four photon ID/isolation decisions | `ROOT::VecOps::RVec<bool>` | vector<bool> | Container difference, native reader verified |
| `jet_btag_quantile` | `ROOT::VecOps::RVec<int>` | vector<int> | Container difference, native reader verified; quantile semantics UNKNOWN |
| `jet_jvt` | **`ROOT::VecOps::RVec<bool>`** | **vector<float>** | Container **and element-type** difference; native bool reader verified |
| `runNumber`, `channelNumber` | `UInt_t`, scalar | unsigned int | MATCH |
| `eventNumber` | `ULong64_t`, scalar | unsigned long long | MATCH |
| `trigP` | `Bool_t`, scalar | bool | MATCH; documented single-photon summary |
| Five requested weights/SFs | `Float_t`, scalar | float | All present and structurally finite; physics applicability UNKNOWN |

There are **11 exact scalar matches**, **13 supported container differences**, and
**one supported container plus element difference**. No requested branch is absent.
RVec is recorded and read as RVec, not renamed or bound to a `std::vector` address.
`channelNumber` and the five weight/SF fields are optional in collision input; their
presence does not establish that this is MC or that these values are useful weights.

The [versioned v1.0.0 producer](https://gitlab.cern.ch/atlas-outreach-data-tools/physlitetoopendata/-/tree/v1.0.0)
declares boolean JVT and documents DL1dv01-related quantiles, while the dictionary
also says DL1dv0. As recorded in Phase 0, that producer is later than FEB2025 v0.
The observed bool resolves the **physical element type for this file**; it does not
establish the exact JVT threshold, production commit, quantile boundaries, calibrated
efficiency working point, or equivalence to official GN2 tagging. Those remain UNKNOWN.

## Structural inspection, no physics selection

The first schema-only run stopped on unsupported RVec types with zero entries read.
The preserved diagnostic was followed by implementation of explicit native RVec
readers and synthetic RVec tests. The successful run inspected **entries 0 through 9**
once; no additional collision entries were inspected.

The following checks passed for those ten entries:

- Nonnegative `photon_n` and `jet_n` scalars, native unsigned event identity types,
  and successful typed-reader setup.
- All requested photon collection lengths equal `photon_n`; all requested jet/JVT/
  b-tag collection lengths equal `jet_n`.
- Requested floating kinematics and present weights/SFs are finite. Native bool/int
  collection values can be read without a type conversion. No ID/isolation cut,
  tagging threshold or weight application was performed.
- Input SHA-256 unchanged after READ-mode inspection.

This sample check does not guarantee integrity of every entry or every file. No
event values, yields, efficiency, cross section, significance, limit, distribution,
mass or four-vector was calculated. **Kinematic units and all working-point semantics
remain UNKNOWN.** Finite values or branch spelling cannot validate either.

## Eventual capability and remaining gaps

| Potential later study | What this schema establishes | Separate requirements before use |
| --- | --- | --- |
| Diphoton four-vectors | Readable aligned pt/eta/phi/e arrays | Validate units, calibration, acceptance and energy convention |
| Dijets / invariant masses | Readable aligned jet kinematics | Validate units, collection/calibration semantics and reconstruction prescription |
| Basic object identification | Four readable photon bool decisions | Establish exact ID/isolation definitions and corrections |
| Simplified b-tag study | Readable integer quantile per jet | Define and validate a simplified mapping; never equate it with GN2 |
| Event identity / duplicate checking | Native run/event fields; channel field present | Establish identity scope, overlap handling and luminosity-block information; no duplicate scan executed |

The [official journal analysis](https://doi.org/10.1016/j.physletb.2026.140280) uses
GN2 tagging, a diphoton trigger and calibrated object selections/corrections plus a
category-based likelihood and nuisance model; Phase 0 records the supporting source
sections. `trigP` is documented as a **single-photon** summary and does not certify a
35/25 GeV diphoton decision, trigger efficiency or prescales. The later public producer's
photon SF uses loose decisions, so mere presence cannot justify tight-photon SF use.

An appropriate HH signal MC sample, matched generated-weight sums, calibration and
systematic inputs, and an executable public likelihood/workspace remain unestablished.
HEPData numerical/workspace payloads remain ACCESS_UNVERIFIED from Phase 0; this
phase did not retry or validate them. No official signal strength, exclusion limit or
coupling scan is supported. These limitations were not removed from the baseline.

## Tests and regression evidence

The unchanged `bash scripts/validate_step1.sh` passed in a fresh preflight build:
ROOT I/O, RDataFrame, RooFit/RooStats and CTest **3/3**. The Phase 1 build passed
CTest **5/5**, zero failures (7.31 seconds in the measured combined run):

| CTest entry | Actual execution |
| --- | --- |
| root_io / rdataframe / roofit_roostats | All three preserved tests PASS |
| root_schema_suite | **22 synthetic cases PASS** |
| bounded_transfer | **8 offline metadata-transfer tests PASS** |

Synthetic C++ cases include std::vector/RVec and boolean JVT, missing required
branches versus optional MC fields, wrong types, unequal lengths, negative counts,
NaN kinematics/weights, empty input, a NaN beyond the ten-entry limit, explicit
smaller limits, invalid limits, output overwrite refusal, remote input rejection,
ambiguous/no tree handling and friend-tree refusal. Metadata tests cover cumulative
budget/resume, oversize/truncated/compressed responses, exact byte/hash accounting,
and unexpected redirect rejection. They do not perform physics processing.

After all changes, the unchanged validator was run again with Phase 1 default OFF:
fresh Step 1 build/smoke/compiler/linkage checks PASS, CTest 3/3 (2.25 seconds),
evidence `/home/btu/build/atlas_hh_phase1_final_step1_20261010T081759Z/step1_validation_20261010T081759Z.lWDydg`.
The final combined CTest run again passed 5/5 (3.14 seconds); verbose local transcript
`.local/phase1_final_ctest.log` confirms the 22 C++ and 8 metadata test cases executed.

`ATLAS_BUILD_PHASE1` defaults OFF so the existing validator's four-target build and
three-test contract remain intact. Phase 1 explicitly enables it. C++20 is unchanged.
Fresh build commands and bounded physical reproduction are in the access audit.
Compiler diagnostics from initial non-const ROOT reader access and the missing RVec
library link were preserved locally; the final source uses ROOT's lazy accessor API
and explicitly links `ROOT::ROOTVecOps`. No prior tests were weakened to pass.

# Phase 4 same-event geometric generator association

**SYNTHETIC_ALGORITHM = PASS; SYNTHETIC_MC_ADAPTER = PASS;
PHYSICAL_STAGED_EXECUTION = EXECUTED_WITH_FAILED_RECONSTRUCTION_GATE;
PHYSICS_ORIGIN_PURITY = BLOCKED; EXACT_RELEASE_TRUTH_DEFINITION = UNKNOWN.**

The selected GamGam MC files contain real truth directions. Their presence is
not a truth-input absence blocker. The implemented MC-only adapter permits a
scoped, provisional geometrical association between reconstructed and supplied
truth objects from the same local ROOT entry. Focused synthetic tests executed
successfully; the first completed physical reconstruction run has one independent
pair-mass closure failure, documented below. The other two scoped runs completed;
their bounded closure checks passed, but the overall numerical gate remains FAIL.
No physical matching result is inferred from synthetic fixtures.

## Physical inputs and evidence

Actual native inventories for DSIDs **343981, 346214 and 423103**, under
`outputs/phase4_v1/<DSID>/branches.csv`, establish these fields:

| Collection | Native count | Native vectors |
| --- | --- | --- |
| Truth photons | `truth_photon_n: Int_t` | `truth_photon_pt/eta/phi: ROOT::VecOps::RVec<float>` |
| Truth jets | `truth_jet_n: Int_t` | `truth_jet_pt/eta/phi/m: ROOT::VecOps::RVec<float>` |

The jet field is **mass `truth_jet_m`, not energy `truth_jet_e`**. Truth photon
energy is absent and is not invented. The first bounded unit probe found signed
negative truth-jet masses, including approximately -0.02453454, -0.01409399 and
-0.06633756 GeV in entries 10, 11 and 12 of DSID 343981. Across the three first-100
probes, negative-mass counts are respectively **15, 22 and 8**. These values are
retained; **TRUTH_MASS_QUALITY = UNKNOWN_NEGATIVE_VALUES**. There is no clamp,
inferred truth energy, truth-mass plot or assertion of physically validated jet
mass. Association uses only pT, eta and phi, whose separate native structure/unit
checks are required. The overall probe preserves its anomaly inventory and
initial failed mass assertion as evidence.

The official [educational dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
describes the truth kinematic fields. The later versioned
[event source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhysLiteToOpenData.cxx/raw?ref=v1.0.0)
retrieves TruthPhotons and AntiKt4TruthDressedWZJets within the same MC event.
The official
[TruthInfo v1.0.0 source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FTruthInfo.cxx/raw?ref=v1.0.0)
stores photons with pT >= 10 GeV and jets with pT >= 20 GeV, multiplying truth pT
and jet mass by 0.001. The freshly retrieved source is 5,745 bytes, SHA-256
`792543c179d42efa2c10588b5175bd7150c1b9e30cfa2fd7e6e7358d7dd89317`.
This later code does not establish exact producer equivalence to FEB2025 flat
files. No validated photon origin/status/ancestry or jet-flavour definition is
supplied to the adapter. See [the source audit](phase4_mc_source_audit.md).

`mc::Reader` binds reconstructed and truth collections in one `TTreeReader` at
the same local entry. The adapter retains native DSID/run/event and that explicit
source-entry index. It accepts no cross-event join mode. The native reader and
physical-entry staging are validated separately from the direction algorithm.

## Eligibility and numerical contract

The study uses **all supplied objects**, independent of the leading-object C9
event selection. Study-eligible reconstructed and supplied truth photons satisfy
**pT > 25 GeV and |eta| < 2.37**; jets satisfy **pT > 25 GeV and |eta| < 2.5**.
These boundaries are strict. No photon crack, identification, isolation, prompt
origin, b tag or jet-flavour requirement is added by the matching adapter.
Geometric association is aggregated separately over all valid inspected MC
events and the C9-selected subset; those populations must not be conflated.

Native unit status must explicitly be PROVISIONAL or VERIFIED, with separate
reco/truth conversion factors. UNKNOWN units reject the operation. Provisional
acceptance does not upgrade the exact released-file unit convention or producer
definition. Native counts/vector lengths, finite directions, physical phi range,
nonnegative scaled truth pT and existing reconstructed four-vector checks are
required. Missing truth blocks only that object collection. Signed truth mass
is deliberately unused, and no MCweight, scale factor, luminosity or correction
enters assignment or denominators.

Candidate edges require **DeltaR < threshold**, strictly, with wrapped phi using
the existing `atlas::kinematics::delta_phi`. The default study threshold scans
are **0.1/0.2/0.3 for photons** and **0.2/0.3/0.4 for jets**, including nominal
examples 0.2 and 0.3. These are sensitivity parameters, not validated ATLAS
working points, efficiency corrections or systematic uncertainties.

The reusable `atlas::matching` interface in `AtlasSyntheticMatching.h` first
maximizes the number of unique pairs, then minimizes their total DeltaR. A
unit-capacity residual network uses successive minimum-cost augmentations with
reverse edges, rather than independent nearest neighbours. Bellman-Ford handles
negative reverse costs directly. Complexity is O(F V E), with F at most
min(Nreco,Ntruth). Costs accumulate in long double, with no cardinality penalty
or epsilon tie perturbation. Stable IDs are sorted before traversal; equal-cost
paths retain the first strictly shortest path under fixed traversal. Returned
pairs are deterministic under input permutation, and no object is reused.
Duplicate IDs, nonfinite inputs, nonpositive/nonfinite thresholds and distance
overflow reject the operation. A residual predecessor cycle fails closed.

The MC adapter additionally fails closed above **128 eligible objects per
collection** or **4,096 eligible reco-times-truth candidate pairs** before
constructing an assignment network. These explicit configurable work budgets
are computational guards, not physics acceptance cuts. Exceeding them must be
reported as an invalid/work-budget event, never silently truncated or counted as
a zero-match result. Local reco candidate multiplicity and reference competition
are reported; they do not enumerate all globally equivalent optima.

## Denominators and interpretation

For each object type, threshold and event population, retain the **number of
provided reco/truth objects**, the **number satisfying study eligibility**, the
**number uniquely matched**, and the **unmatched eligible counts**. Provided
counts include out-of-acceptance stored objects; eligible counts are the actual
assignment denominators. Object storage thresholds and the GamGam event skim
already condition the available truth population.

The truth association fraction is N(unique matched supplied truth) /
N(study-eligible supplied truth). The reco association fraction is N(unique
matched reco) / N(study-eligible reco). Unmatched fractions use the same respective
denominators; zero denominators are undefined optional values, never fabricated
zeroes or ones. Population totals use ratios of summed counts, not an unweighted
average of per-event fractions. Fraction results are conditional on valid
inspected entries, the supplied stored collections, study acceptance and any C9
population restriction.

These are **geometrical association fractions**. The reco fraction is not prompt
purity, process purity, Higgs-daughter purity or flavour purity. The truth fraction
is not an official reconstruction efficiency for all generated particles. No
Higgs origin, truth-b-jet efficiency, mistag probability or calibrated detector
performance is established by nearby directions. No b label can be inferred
from a matched inclusive truth jet. Native normalization discrepancies and b-tag
sentinels remain independent unresolved issues in the source/b-tag audits; a
geometric PASS cannot resolve them.

## Actual bounded DSID 343981 diagnostics

The physical driver processed **entries [100,10000), 9,900 events**, retaining
its generated evidence under `outputs/phase4_v1/343981/reconstruction/`. All
9,900 passed the driver's reconstructed-collection checks, but the independent
Cartesian pair-mass comparison **FAILED 1 of 12,004 tested pairs**. The driver
returned **exit 1**. Therefore **RECONSTRUCTION_NUMERICAL_GATE = FAIL**; this run
does not establish reconstruction PASS or overall scientific PASS. Its raw C9
count **1,125** and all histograms/fractions remain provisional diagnostics.
The closure tolerance was not relaxed, source values were not clamped, and failed
evidence is preserved. The maximum absolute pair residual is approximately
`1.91245356e-7`; tolerances are evaluated per pair, so unrelated maxima cannot
be compared to manufacture a passing result. Generated `events.csv` locates the
failure at **entry 5888, run 284500, event 4385033**: the diphoton pair, no jets,
and C9=false. This location does not authorize waiving the numerical gate.
Numerical diagnosis is separate.

Same-entry geometry executed at all six study thresholds and both populations.
An independent **generated CSV/JSON** audit checked **83,681 assignment rows**,
**12 threshold-summary rows** and **49,430 supplied truth-object rows**. It
verified DSID/run/event/local-entry identity, in-range original object indices,
strict thresholds, unique reco/truth partners within each event/group/threshold/
scope, matched-plus-unmatched denominator closure, exact ratio-of-summed-count
fractions, threshold monotonicity, and that C9 assignments equal the ALL_VALID
assignments restricted to C9 events. Every event in this inspected range had
both supplied truth collections; missing-truth event counts are zero. No ROOT
input was reopened by this CSV audit. The audit verifies output consistency;
the independent exhaustive algorithm oracle remains a synthetic validation.

Nominal-threshold conditional counts are:

| Objects / strict threshold | Population | Matched / eligible reco | Matched / eligible supplied truth |
| --- | --- | --- | --- |
| Photons / 0.2 | ALL_VALID, 9,900 events | 19,737 / 19,828 | 19,737 / 19,899 |
| Photons / 0.2 | C9 diagnostic subset, 1,125 events | 2,241 / 2,253 | 2,241 / 2,296 |
| Jets / 0.3 | ALL_VALID, 9,900 events | 3,996 / 5,527 | 3,996 / 25,568 |
| Jets / 0.3 | C9 diagnostic subset, 1,125 events | 1,924 / 2,606 | 1,924 / 4,448 |

For photon thresholds 0.1/0.2/0.3, ALL_VALID matched counts are
**19,729 / 19,737 / 19,737**, and C9 matched counts are
**2,241 / 2,241 / 2,241**. For jet thresholds 0.2/0.3/0.4, ALL_VALID matched
counts are **3,985 / 3,996 / 4,005**, and C9 counts are
**1,918 / 1,924 / 1,927**. Nominal local ambiguous-reco/competed-truth counts
are respectively **6/4 for ALL_VALID photons** and **1/4 for ALL_VALID jets**;
the C9 values are **0/0** and **0/4**. These are local candidate diagnostics,
not globally equivalent solution counts or origin probabilities.

The full run preserves **1,397 negative signed truth-jet mass values** (minimum
approximately -0.19316584 in provisional GeV) and **18 negative b-tag SF scalar
values**. Neither mass nor SF enters geometry. Prompt/flavour purity, official
reconstruction efficiency, calibrated rates and C9 physics readiness remain
unestablished regardless of the geometrical CSV checks.

The exact CSV-audit script, result and SHA-256 hashes are retained in ignored
`.local/build_phase4_matching_agent/audit_matching_csv.py` and
`physical343981_matching_csv_audit.json`. The matching summary SHA-256 is
`f2da6044aeecf37ce3a166c785761a73edc1dbd7665eb5216dbe6c8b0a920f0d`;
assignment SHA-256 is
`f0d5f0eef5bb42aebd56e6fc9727b08d3f6e692541c10f1d832f3931f1f0021c`.
## Other executed physical runs and overall scope

Both additional runs processed **entries [100,10000), 9,900 events per DSID**.
Their summaries record zero invalid reconstructed kinematics. Bounded pair-mass
closure is **PASS for DSID 346214 (12,197 tested pairs)** and **PASS for DSID
423103 (13,220 pairs)**. These scoped results do not negate the DSID 343981
failure: **overall physical reconstruction numerical validation remains FAIL**.

| DSID | ALL_VALID events | Raw C9 diagnostic events | Unique-pair CSV audit | Negative truth-mass values / negative b-tag SF scalars |
| --- | ---: | ---: | --- | --- |
| 343981 | 9,900 | 1,125 | 83,681 assignment rows; PASS consistency | 1,397 / 18 |
| 346214 | 9,900 | 1,419 | 92,871 assignment rows; PASS consistency | 2,511 / 75 |
| 423103 | 9,900 | 588 | 76,363 assignment rows; PASS consistency | 731 / 103 |

Across these three runs the generated CSV audits examined **252,915 assignment
rows, 36 summary rows and 165,977 supplied truth-object rows**. All passed the
same identity/unique-partner/strict-threshold/denominator/population checks above,
including independently recomputing eligible truth counts from preserved pT/eta
and checking threshold monotonicity per event. Assignment rows intentionally
repeat objects across thresholds and populations; they are not the count of
distinct physical objects. Both supplied truth groups were present for every
inspected entry. Exact original object indices and signed truth mass remain
preserved; no truth energy or mass-based eligibility is fabricated.

Additional nominal conditional counts are:

| DSID / objects / threshold | Population | Matched / eligible reco | Matched / eligible supplied truth |
| --- | --- | --- | --- |
| 346214 / photons / 0.2 | ALL_VALID | 19,764 / 19,957 | 19,764 / 20,615 |
| 346214 / photons / 0.2 | C9 diagnostic | 2,829 / 2,846 | 2,829 / 3,026 |
| 346214 / jets / 0.3 | ALL_VALID | 5,895 / 7,172 | 5,895 / 29,233 |
| 346214 / jets / 0.3 | C9 diagnostic | 2,475 / 3,133 | 2,475 / 5,603 |
| 423103 / photons / 0.2 | ALL_VALID | 16,361 / 19,895 | 16,361 / 18,370 |
| 423103 / photons / 0.2 | C9 diagnostic | 953 / 1,183 | 953 / 1,060 |
| 423103 / jets / 0.3 | ALL_VALID | 7,054 / 8,723 | 7,054 / 29,216 |
| 423103 / jets / 0.3 | C9 diagnostic | 1,096 / 1,423 | 1,096 / 2,479 |

For DSID 346214, photon 0.1/0.2/0.3 matched counts are
**19,756/19,764/19,764 (ALL_VALID)** and **2,828/2,829/2,829 (C9)**; jet
0.2/0.3/0.4 counts are **5,887/5,895/5,897** and **2,471/2,475/2,476**.
For DSID 423103, the corresponding photon counts are
**16,355/16,361/16,363** and **953/953/953**, and jet counts are
**7,022/7,054/7,064** and **1,092/1,096/1,097**. These are separate process/slice
diagnostics; the samples are not combined into a background or signal prediction.
The larger local photon candidate multiplicity in the gamma+jet slice is not
proof of a prompt/fake-origin classification or a measured fake rate.

Per-file audit JSON and hashes are retained as
`physical346214_matching_csv_audit.json` and
`physical423103_matching_csv_audit.json` alongside the 343981 audit. Matching
summary SHA-256 values are respectively
`5905b0f7e6ceae3fd48ff31a12cb2b69022d5a3206a822f2200d33ee46157f0e` and
`49033752d39c6c57d096482c31bcfc4fa3bd67d628be5612dbebbcddcf493864`.
The first-100 source/unit probes and [100,10000) reconstruction runs are recorded
as distinct stages; probes are not relabelled as 10,000 reconstructed events.
The cached CSV auditor is also provided as
`scripts/audit_phase4_matching.py`, with a new-destination guard, for reproducible
identity/partner/threshold/denominator audits without rereading ROOT input.

## Executed focused tests

Executed 2026-10-11: the standalone **synthetic algorithm PASS**, exit 0,
**4,264 assertions**, **600 independently enumerated seeded cases**, and a
**40 x 40 dense fixture**. Its executable prints
`PHYSICAL_TRUTH_MATCHING=NOT_EXECUTED` and opens no MC/collision file.

The independent exhaustive oracle uses `atan2(sin DeltaPhi,cos DeltaPhi)`, not
the production wrapped-angle helper. Each seeded case has at most five reco and
five reference objects with randomized directions, exclusions and permutations.
Cardinality must equal exhaustive enumeration exactly; summed-cost closure uses
`abs(actual-reference) <= 1e-12 * max(1,abs(reference))`. Explicit cases cover
zero separation, strict 0.2/0.3 boundaries and nextafter neighbours, periodic phi,
competition, a greedy-cardinality counterexample, minimum cost, exact ties,
eligibility, undefined denominators, invalid inputs and threshold sensitivity.

The standalone **synthetic MC adapter PASS**, exit 0, **44 assertions**. It
tests retained DSID/run/event/local-entry and PROVISIONAL status, provided versus
eligible counts, both three-threshold scans, unmatched truth denominators,
missing photon truth independent of jets, invalid units/native vectors/phi/
kinematics/scans, strict pT/eta acceptance, no accidental photon crack cut, and
explicit work-budget rejection. A negative unused truth mass yields identical
partner identities, distances and assignment totals while retaining its signed
value and not fabricating energy. The
executable prints `PHYSICAL_EVENT_EXECUTION=NOT_THIS_TEST`.

Actual toolchain: ROOT **6.40.04**, ROOT/project **C++20**, conda GNU **15.3.0** at
`/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`.
Both focused builds use `-Wall -Wextra -Wpedantic -Werror` and compiled without
warnings. Exact commands/build/test logs are preserved in ignored
`.local/build_phase4_matching_agent/`. Project-wide CMake/CTest results and staged
physical MC association results are recorded in the overall Phase 4 validation,
not assumed from these focused tests.

Algorithm and adapter validation cannot upgrade Phase 0 PARTIAL, Phase 1
PARTIAL_SCHEMA_VALIDATED, existing PROVISIONAL reconstruction, UNKNOWN truth
mass/producer/origin semantics, b-tag feasibility or absolute normalization.

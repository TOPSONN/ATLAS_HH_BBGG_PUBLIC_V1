# Shared Cartesian stability review — Phase 4 numerical recovery V2

Executed 2026-10-12 from Phase 4 base `d823593b42889592897263819138170470f4dc47`. This is an additive numerical recovery review. The historical [Phase 4 failure report](phase4_numerical_failure.md) and its original FAIL remain unchanged. The result below establishes the shared implementation and deterministic stress checks; the separate [DATA/MC regression report](phase4_data_mc_regression.md) must establish physical rerun gates. A synthetic PASS does not clear those gates or validate MC normalization or HH physics.

The existing environment is ROOT **6.40.04**, C++20 and conda GNU **15.3.0** (`conda-forge gcc 15.3.0-7`). Compilation used `/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`, the same environment's headers/libraries, and `-Wall -Wextra -Wpedantic`; no warnings were emitted. This Linux toolchain has a **64-bit long-double significand**, versus 53 bits for double. Equivalent behavior is not asserted on platforms where `long double` has only double precision.

## Exact original event and A/B/C comparison

The existing local DSID 343981 file was rehashed before reproduction: SHA-256 `002e890c517e03ba59c49bc0852d0fdcd200e0d48add7ca189228a6f82965c56`, matching the [original transfer ledger](../metadata/phase4_transfer_ledger.json). Exactly one new V2 bounded read of **entry 5888**, run **284500**, event **4385033**, reproduced the original implementation using the retained original executable. The raw values match the historical diagnostic byte for byte; no collision input or original output was overwritten. That repeat is recorded separately and adds no unique event to the historical population.

| Native photon index | pT (declared GeV) | eta | phi (rad) | supplied E (declared GeV) |
|---:|---:|---:|---:|---:|
| 0 | 60.81133270263671875 | -2.322521209716796875 | 1.00584459304809570312 | 313.159759521484375 |
| 1 | 60.1185302734375 | -1.87638890743255615234 | -2.13731408119201660156 | 200.886810302734375 |

The new stress test contains this exact verified native tuple. It compares A, the original ROOT PtEtaPhiE sum, B, the actual corrected shared `leading_pair` result, and C, an independent long-double Cartesian calculation beginning with those native values. The fixture itself performs no physical input read; the full physical harness independently repeats the source-entry comparison.

| Quantity | A: original PtEtaPhiE | B: shared long-double Cartesian | C: native-input long-double reference |
|---|---:|---:|---:|
| Pair mass squared (GeV²) | 15363.3583090340544004 | 15363.3583564434008792 | 15363.3583564434008792 |
| Pair mass (GeV) | 123.949014957901354705 | 123.949015149146717363 | 123.949015149146711076 |

The unchanged mass tolerance is **`1e-7 + 1e-10*abs(reference_mass)` GeV**, equal to `1.12394901514914671104e-7` for this pair. A's absolute residual is `1.9124535637071726768e-7` and still fails. B differs from C by approximately `6.29e-15` GeV and passes. B's returned `Pair::mass` remains double; the extended precision is retained through Cartesian component conversion, summation, M² and square root before that final return-value conversion. The original event has no jets and did not pass C9; the numerical recovery does not invent a selected event.

The original sum has pT about `0.699243147456` GeV and pz about `-498.878771497` GeV. Converting that Cartesian sum back to eta and then reconstructing its momentum caused the original loss of precision. The installed ROOT headers, version and hashes supporting this diagnosis remain in the historical report. The [official ROOT GenVector guide](https://root.cern.ch/doc/master/group__GenVector.html) documents the coordinate representations; the executed code and locally installed headers establish the exact version-specific calculation.

## Shared implementation and rejected first candidate

`FourVector` remains `ROOT::Math::PtEtaPhiEVector`, preserving per-object interpretation, energy, pT ordering, coordinate restriction and the existing negative single-object roundoff flags. The shared pair calculation now converts each selected object's unchanged stored pT/eta/phi/E into extended-precision Cartesian components, then uses `ROOT::Math::LorentzVector<ROOT::Math::PxPyPzE4D<long double>>` for addition and M². Both DATA and MC use that same function. `Pair`'s interface, angular definitions, object ordering, selection definitions and unit scaling are unchanged. Negative or nonfinite pair M² is still rejected, including tiny negative values. There is no clamp, energy correction, offset or MC-only kernel.

A first candidate used ordinary double `PxPyPzEVector`. Although it repaired the exact entry 5888 discrepancy, **13,313 deterministic cases exposed 406 unchanged mass-tolerance failures and 52 additional negative-M²/sign mismatches** in high-energy near-collinear cases. Its maximum mass residual was `4.29903515172785497e-5` GeV. The first candidate therefore failed; its execution and all cases were retained at `.local/phase4_numerical_v2/stress_double_initial/19578045006/`. It was not accepted through weaker tolerances or removal of those cases.

The initial component diagnostic bound also omitted the pT-scaled inherited phi-restriction rounding when a Cartesian component approaches zero at native Float32 phi near pi. The final *secondary diagnostic* bound includes that forward-error term. This documents existing coordinate normalization precision; it does not change the independent native-value reference or the binding mass criterion. The original failed candidate and its original diagnostic-bound results remain available for review.

## Deterministic stress results

The final suite executed **15,361 cases**, with seed **20261012**, comprising the exact entry 5888 tuple once and 1,024 cases in each of these 15 categories:

| Category | Expected behavior |
|---|---|
| General massive native Float32 pairs | Finite shared pair and independent closure |
| Nearly cancelled transverse momentum with large negative pz | Cartesian sum avoids eta round trip |
| Back-to-back photons | Finite closure using native phi precision |
| Highly boosted small-opening massive pairs | Finite closure at large component-to-mass ratios |
| Extreme negative eta (-9/-10) | Finite declared-domain closure |
| Exact collinear lightlike vectors | Exact zero mass; no invented positive offset |
| Nearly massless small-opening pairs | Strict native-value mass closure |
| Negative pair from downward Float32 energy rounding | Signed negative reference and ROOT M² rejected without correction |
| Nonfinite pT/eta/phi/E | Existing input rejection retained |
| Native object permutations | Exactly identical ordered-pair mass and angular observables |
| Clearly spacelike synthetic objects | Existing object rejection retained |
| Extreme eta overflow (+/-1000) | Existing numerical-overflow rejection retained |
| High-energy near-collinear lightlike native Float32 vectors | Cases that rejected the double candidate retained and passed |
| Near-massless native Float32 phi at +/-pi | Native reference kept; inherited phi restriction explicitly tested |
| Native Float32 MeV-to-GeV scaling | Existing scale semantics retained and independently compared |

**Failed cases: 0.** There were **11,265 nonnegative-reference mass comparisons**, with **0 mass-closure failures**; 1,024 negative-reference pairs were rejected, and 3,072 deliberately invalid collections were rejected. No invalid case is counted as a positive mass-closure comparison. Exact zero references have undefined relative residual, so maximum relative values below use only nonzero references. All generated rows, including invalid cases, are retained.

| B quantity versus independent C | Comparisons | Failed checks | Maximum absolute residual | Maximum relative residual, nonzero reference |
|---|---:|---:|---:|---:|
| px (GeV) | 12289 | 0 | 4.6657989971610192e-14 | 3.4333520213581821e-7 |
| py (GeV) | 12289 | 0 | 4.8953177842512394e-14 | 4.0109070820956586e-7 |
| pz (GeV) | 12289 | 0 | 1.0336176359260207e-13 | 2.0039502122306693e-13 |
| E (GeV) | 12289 | 0 | 1.1912693054227930e-13 | 1.0101931233243037e-16 |
| M² (GeV²) | 12289 | 0 | 4.3519321479834616e-10 | 5.3993251190738998e-15 |
| Mass (GeV) | 11265 | 0 | 3.2454594567354889e-13 | 2.5946480302184798e-15 |
| DeltaEta | 11265 | 0 | 0 | 0 |
| Wrapped DeltaPhi (rad) | 11265 | 0 | 2.4502969098172400e-16 | 1.4014064238830230e-9 |
| DeltaR | 11265 | 0 | 5.8590285401116660e-16 | 1.4014064238830230e-9 |

The large-looking relative px/py or angular residuals occur when their nonzero references approach zero; the absolute residuals remain explicitly reported. They are arithmetic diagnostics, not detector or statistical uncertainties.

Mass uses the original fixed acceptance formula. The separately named component diagnostic bound is `64*double_epsilon*max(sum_abs_component_terms, sum_abs_native_pT_for_px_py, 1)`. M² uses `64*double_epsilon*max(reference_E²+reference_px²+reference_py²+reference_pz²,1)`. Angular checks use `1e-12` (radians for phi; eta and DeltaR dimensionless). These secondary forward-arithmetic checks do not replace mass closure, permit clamping or establish physics accuracy. The independent reference is always computed from the original native tuple, never a rounded ROOT pair sum. No claim of exact mathematics or validation over every possible finite input is made; more extreme conditioning or another long-double format still requires its own checks.

## Reproduction and retained evidence

The retained original executable read the existing pinned source into a **new** evidence file:

```bash
source /home/btu/miniforge3/etc/profile.d/conda.sh
conda activate atlas-hh-root
cd /mnt/c/HH
.local/build_phase4_mc_agent/build/diagnose_mass_closure \
  .local/phase4_access_20261011/ODEO_FEB2025_v0_GamGam_mc_343981.PowhegPythia8EvtGen_NNLOPS_nnlo_30_ggH125_gamgam.GamGam.root \
  343981 5888 .local/phase4_numerical_v2/343981_entry5888_original_reproduction.txt
```

That exact output already exists and must not be overwritten; use a different output filename for a separately recorded repeat. The standalone stress executable was compiled with the explicit conda compiler and the current shared source:

```bash
/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++ \
  -std=c++20 -Wall -Wextra -Wpedantic \
  -I/mnt/c/HH/include -I/home/btu/miniforge3/envs/atlas-hh-root/include \
  /mnt/c/HH/src/Kinematics.cxx /mnt/c/HH/tests/test_cartesian_stability.cxx \
  -L/home/btu/miniforge3/envs/atlas-hh-root/lib \
  -Xlinker -rpath -Xlinker /home/btu/miniforge3/envs/atlas-hh-root/lib \
  -lCore -lMathCore -lROOTVecOps \
  -o /mnt/c/HH/.local/phase4_numerical_v2/test_cartesian_stability_final
.local/phase4_numerical_v2/test_cartesian_stability_final \
  /mnt/c/HH/.local/phase4_numerical_v2/stress_final
```

Recompilation should likewise use a new executable name to preserve the recorded binary. Every stress invocation creates a distinct evidence subdirectory; no physical input is read by that test. CMake integration uses target `test_cartesian_stability`, linked to the same shared `atlas_kinematics` module. Integrated CTest and physical rerun results belong to the separate DATA/MC report and gate JSON; they are not inferred from this standalone run.

| Evidence | SHA-256 |
|---|---|
| Retained original diagnostic executable | `a97f9354bfe06fa128d209cdd35b9e8bf2746db60700f40343969706d9ebdf4e` |
| `.local/phase4_numerical_v2/343981_entry5888_original_reproduction.txt` | `cfbb9f1a2f27d7d0de6d13626100f3e02e1dce2ee6064d3bfedbaa537a31babc` |
| `.local/phase4_numerical_v2/stress_double_initial/19578045006/summary.json` | `4a71743d50974694a82ba4f8931a28f8de37beda7e173e3c348779e1b8daaeee` |
| `.local/phase4_numerical_v2/stress_final/288904775609/summary.json` | `d3ca4ac029953084ab21466185281c624b21f9bd846514d14bfd48b6826fec62` |
| `.local/phase4_numerical_v2/stress_final/288904775609/cases.csv` | `0b309035ea938aeee2ea6f3750c675a5c0a45b74c4a02e654aa4faae91af7bd1` |
| Historical `reports/phase4_numerical_failure.md`, unchanged | `c7a031deca2da58e9974906f1c4727b40aa820090c66138e0be8f568dbeda651` |

The corrected source hashes at this standalone execution were `360d8474168a6ca0643916dca03ffc2da47cac5b46947f55565133d379a9089d` for `src/Kinematics.cxx`, `1b9ba61359a0e23d7e1576c3e91bb25fbdc986987c40c58336ccf9313619bf64` for `include/AtlasKinematics.h`, and `e119eaf40ef44c3da0c12445180cdd68e8c60706820f136e4044ff0129184de6` for the new stress test. These identify this numerical run; final manifests must record the actual sources/binaries used by subsequent integrated runs.

The standalone disposition is **PASS for the reproduced failure, shared synthetic closure and stress checks, with physical gates evaluated separately**. Exact raw values, energies, unit scales, object semantics, cuts and the original mass criterion were preserved. Negative supplied Float32 invariants are still negative and invalid under those supplied values; arithmetic tests cannot infer whether an underlying real event's values arose from measurement, rounding or calibration. No new figure, fit, significance, limit, correction, normalized prediction or official truth-efficiency claim is produced by this recovery.

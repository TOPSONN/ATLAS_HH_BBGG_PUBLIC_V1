# Phase 4 numerical closure failure — retained evidence

Date: 2026-10-11. Status: **FAIL for the original numerical closure gate; Phase 4 remains PARTIAL**. ROOT is the installed **6.40.04**, confirmed by `root-config --version`, with the existing C++20 implementation. The reconstruction used the declared scale of 1 to GeV with **PROVISIONAL** unit status. This report diagnoses a numerical discrepancy; it does not validate MC normalization, origin purity, systematic uncertainties or official reconstruction efficiency.

The three bounded MC reconstructions processed `[100,10000)` independently. The original criterion is unchanged: each valid leading-pair mass must agree with an independent long-double Cartesian calculation to `1e-7 + 1e-10*abs(reference_mass)` GeV. The reference begins with the same raw object indices and supplied energies; negative mass squared is never clamped. A failing comparison preserves the reconstruction artifacts and produces a nonzero driver exit.

| DSID | Entries reconstructed | Valid pairs compared | Failed comparisons | Maximum absolute deviation (GeV) | C9 events | Original closure result |
|---|---:|---:|---:|---:|---:|---|
| 343981 | 9900 | 12004 | 1 | 1.9124535637071727e-7 | 1125 | FAIL; driver exit 1 |
| 346214 | 9900 | 12197 | 0 | 6.3440339023723702e-9 | 1419 | PASS |
| 423103 | 9900 | 13220 | 0 | 3.3821119627130969e-8 | 588 | PASS |

These results are read from the retained `outputs/phase4_v1/<DSID>/reconstruction/summary.json` files. A maximum tolerance reported for the entire sample is not the tolerance of the failed pair. The other two samples passing does not clear the failing gate for DSID 343981.

The failed event is **DSID 343981, source entry 5888, run 284500, event 4385033**. Its row in `outputs/phase4_v1/343981/reconstruction/events.csv` has `valid=1`, `photon_n=2`, `jet_n=0`, `cartesian_mass_closure_pass=0` and `C9_selected=0`. The failing pair is the two leading photons. There is no jet pair in this event. It is excluded from C9 by the required jet multiplicity; no cut or scientific value was changed after this finding.

| Raw native photon index | pT (declared GeV) | eta | phi (rad) | Supplied E (declared GeV) |
|---:|---:|---:|---:|---:|
| 0 | 60.81133270263671875 | -2.322521209716796875 | 1.00584459304809570312 | 313.159759521484375 |
| 1 | 60.1185302734375 | -1.87638890743255615234 | -2.13731408119201660156 | 200.886810302734375 |

Exactly **one additional bounded diagnostic read**, of entry 5888 only, was authorized and executed. It reused the native MC reader and the unchanged shared `atlas::kinematics::construct` and `leading_pair` functions. The diagnostic separately compared the existing ROOT sum, direct Cartesian double arithmetic and independent long-double arithmetic. No further MC input read was performed for this diagnosis. The project audit's distinct input population remains **30000 unique MC entries** across the three staged `[0,10000)` ranges; this repeat contributes **one additional diagnostic entry read**, not a new unique event or an additional reconstruction population.

| Numerical quantity | Retained diagnostic value |
|---|---:|
| Existing ROOT PtEtaPhiE pair mass (GeV) | 123.949014957901354705 |
| Direct ROOT Cartesian sum mass (GeV) | 123.949015149147086845 |
| Independent Cartesian double mass (GeV) | 123.949015149147086845 |
| Independent Cartesian long-double mass (GeV) | 123.949015149146711076 |
| Absolute discrepancy of existing pair mass (GeV) | 1.9124535637071726768e-7 |
| Relative discrepancy of existing pair mass | 1.54293566706111773081e-9 |
| Unchanged tolerance for this pair (GeV) | 1.12394901514914671104e-7 |
| Cartesian double minus long-double mass (GeV) | approximately 3.758e-13 |
| Sum transverse momentum (GeV) | 0.699243147456260927264 |
| Eta stored in the ROOT pair sum | -7.26326754193705337315 |
| Direct Cartesian double sum pz (GeV) | -498.878771497267337054 |
| ROOT pair sum reconstructed pz (GeV) | -498.878771544783319314 |
| ROOT coordinate round-trip pz difference (GeV) | -4.75159822599380277097e-8 |

The two photons almost cancel in transverse momentum while their longitudinal momenta add. The individual ROOT object pz values agree with the long-double reference to approximately `5.14e-14` and `8.94e-15` GeV. The discrepancy appears when the pair sum is converted back to the PtEtaPhiE coordinate representation. The direct Cartesian double and long-double masses closely agree, while reconstructing momentum from the pair's stored eta shifts pz and subsequently the invariant mass. These measurements locate the failure in the coordinate round trip, rather than a different raw event, weight application or unit conversion in the two compared calculations.

The locally installed ROOT headers provide the version-specific primary evidence. `LorentzVector.h` lines 424–427 adds Cartesian components via `SetXYZT`; lines 450–454 retains the left operand's coordinate type. `PtEtaPhiE4D.h` converts that Cartesian result through `PxPyPzE4D`. `PxPyPzE4D.h` lines 211–212 calls `Eta_FromRhoZ`. For the observed negative longitudinal-to-transverse ratio, installed `eta.h` uses `log(z_scaled + sqrt(z_scaled*z_scaled + 1))`, which subtracts nearly equal magnitudes before the logarithm. `PtEtaPhiE4D.h` later reconstructs pz using `pt*sinh(eta)` and evaluates mass squared using `E*E - (pt*cosh(eta))^2`. The general coordinate representations and conversions are documented in the [official ROOT GenVector guide](https://root.cern.ch/doc/master/group__GenVector.html). That rolling documentation supports the representation context; the exact executable behavior here is established by the installed headers and the measured diagnostic. A public source URL for the exact release tag was not independently verified and is not asserted.

All header paths below share the prefix `/home/btu/miniforge3/envs/atlas-hh-root/include/Math/GenVector/`.

| Installed ROOT header | SHA-256 |
|---|---|
| `eta.h` | `223df67c797b352d10c7c8170ef920f14c975575b370ef3bae907eab394caee5` |
| `PtEtaPhiE4D.h` | `f7131894a119190c155f8f94546315fd9d825e55fd5de94fd7d3ba82748e8d80` |
| `PxPyPzE4D.h` | `ec2c42a07286eea58a1f45ad3cda25962d124b3befe3cea9e0ee5919a6c43c20` |
| `LorentzVector.h` | `7cfc36725d08e296956ab4f594815e90ba272ef9a21b5f24278bb09e2d982cd6` |

The additional diagnostic text is retained at `.local/build_phase4_mc_agent/343981_entry5888_mass_diagnostic.txt`, SHA-256 `cfbb9f1a2f27d7d0de6d13626100f3e02e1dce2ee6064d3bfedbaa537a31babc`. Its ignored helper source is `.local/build_phase4_mc_agent/diagnose_mass_closure.cxx`, SHA-256 `f1ac441f867cf56fc10d935198e402b07c8e4c1bc3eff0486d100439e32cfe4a`. The text explicitly records `ADDITIONAL_BOUNDED_REPEAT_READ count=1 entry=5888` and all compared raw values and components. The existing `events.csv`, `summary.json`, cutflow, matching CSVs and native `histograms.root` were inspected but not modified.

The immediate disposition is to retain **Gate C FAIL**, the original driver exit and all generated evidence. No tolerance is relaxed, event deleted, energy corrected, invariant clamped, cut altered or old artifact rewritten. Any future proposal to use Cartesian pair summation must be a **separately authorized task in the shared four-vector module**, with the same raw inputs and fresh DATA/MC regression and scientific-value preservation review. It must not introduce an MC-only four-vector kernel or retrospectively label this run PASS. Phase 5 scientific work remains blocked by the current Phase 4 closure failure and other stated provenance/physics limitations.

# Phase6C detector-card provenance and definition

**Source review and actual complete-controller Stage A/B/C native validation PASS.**
The card is an independent `FAST_SIM_ATLAS_LIKE` methods-study configuration,
explicitly `NOT_OFFICIAL_ATLAS`, derived from the official Delphes 3.5.1 ATLAS
card at commit `28658365abeb71ee36dfc739f9670c1514c0cb10`.

The exact upstream card is preserved in
[upstream_delphes_card_ATLAS_3.5.1.tcl](../simulation/delphes/cards/upstream_delphes_card_ATLAS_3.5.1.tcl),
SHA256 `b6a97bcd6e2b4f19e218eaa07b3afe1937d66452f0519de0b8c367eff46fe69d`.
The canonical study copy is
[atlas_like_bbgg_baseline.tcl](../simulation/delphes/cards/atlas_like_bbgg_baseline.tcl),
SHA256 `cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47`.
The upstream GPLv3-or-later attribution and unmodified license are retained;
no Delphes source tree or compiled dependency is vendored.

| Change | Upstream | Study definition and motivation |
|---|---|---|
| GenJetFinder radius | anti-kT R = 0.6 | R0.4, matching the exploratory truth/reco jet definition |
| FastJetFinder radius | anti-kT R = 0.6 | R0.4, the explicitly requested reconstructed study jets |
| JetFlavorAssociation cone | DeltaR = 0.5 | DeltaR = 0.4, explicit flavour cone consistent with the chosen radius |
| Random seed | default0 | canonical610301; runtime bbgg610301/ccgg610302/jjgg610303 with exact derived-card hashes |
| Labels/attribution | generic ATLAS card | explicit independent study, working-point and licensing labels |

The stock response, smearing, isolation, jet-energy-scale and b-tag probability
functions are preserved. Radius adaptation is not a recalibration of those
functions. No pileup module is added; the original shower input remains MPI
OFF/pileup OFF/colour reconnection OFF/primordial kT ON. Changing a detector
setting creates a new physics configuration requiring separate validation.

The seed is a real setting: `modules/Delphes.cc` reads the global `::RandomSeed`
and calls ROOT's `gRandom->SetSeed` before detector modules initialize. It is
not a CLI flag or inert Tcl comment. The controller must preserve the canonical
card and exact effective per-process runtime card, together with both hashes.

## Detector response and objects

Tracking has pT-dependent acceptance inside|eta|<=2.5. Charged-hadron efficiency
above 1 GeV is 0.95 for|eta|<=1.5 and 0.85 further out, with lower efficiencies
between 0.1 and 1 GeV and zero outside the tracking region. Electrons and muons
have their own stock piecewise efficiencies and momentum-resolution functions.
The propagator uses a2 T field in a cylinder of radius 1.15 m and half-length 3.51 m.

ECAL and HCAL have separate segmentation, energy fractions and response
functions. The ECAL absolute sigma(E) is
`sqrt((0.0017*E)^2+0.101^2*E)` for|eta|<=3.2 and
`sqrt((0.0350*E)^2+0.285^2*E)` through|eta|4.9, with E inGeV.
SimpleCalorimeter uses positive log-normal energy smearing with the configured
mean/variance, then energy/significance thresholds and randomized tower centers.
This tower response is not a calibrated prompt-photon resolution curve.
HCAL retains its stock eta-dependent stochastic/constant/noise terms.

Photon candidates come from ECAL energy-flow photons. Stock efficiency is 0.95
for|eta|<=1.5 and 0.85 through|eta|2.5 above 10 GeV. Isolation uses EFlowFilter
objects with pT>=0.5 GeV inside DeltaR<=0.5, excluding the same candidate UniqueID.
The retained relative-sum threshold is 0.12. The default rho-corrected branch is
used, but no rho input is configured, so rho=0; no pileup subtraction calibration
is implied. The later HH-like analysis separately imposes its35/25GeV photon
cuts,|eta|<2.37 and open crack exclusion1.37<|eta|<1.52.

Reco jets use calorimeter towers, including separately smeared muons, rather
than the energy-flow merger. FastJet algorithm6 is anti-kT, with radius0.4 and
stock minimum jet pT20 GeV before the jet scale. The retained scale is
`sqrt((3.0-0.2*abs(eta))^2/pt+1.0)`, an upstream parametrization rather than a
current ATLAS JES calibration. The analysis applies corrected-jet pT>25 GeV
and|eta|<2.5. GenJet uses stable particles after neutrino filtering with the
same anti-kT radius and 20 GeV minimum; photons/muons remain visible inputs.

UniqueObjectFinder processes photons, electrons, muons, then jets. It removes
later objects overlapping earlier ones through shared UniqueIDs/recursive
constituents. This is not a geometric DeltaR overlap-removal procedure.
MissingET uses the negative transverse direction of the merged calorimeter
towers, including smeared muons, before jet JES and object-uniqueness filtering.
ScalarHT sums pT of the final unique jets/electrons/photons/muons.

The actual expected outputs include Particle, Track, Tower, energy-flow
collections, GenJet, Photon, Jet, electron/muon, MissingET and ScalarHT branches.
The upstream comment about tracks/towers being omitted is stale: its actual
TreeWriter branch commands are active. Physical ROOT schema/types/dictionaries
must be checked from the executed output, not inferred from this source review.

## Flavour, tagging and validation scope

The card's flavour model is parton-cone association, not hadron ghost labelling
or original-hard-only ancestry. The HepMC reader supplies nonstable quarks and
gluons; eligible partons have pT>1 GeV and|eta|<=2.5. Highest absolute matched
quark PDG 1..5 within DeltaR<=0.4 wins, gluons have lower priority (flavour 21),
and unmatched jets are0. Shower-produced heavy flavour may therefore contribute.
Details and the exact probability functions are in the separate
[b-tag report](phase6c_btag_validation.md).

Pinned card/module hashes and source semantics are recorded in
[card_source_review.json](../simulation/delphes/evidence/card_source_review.json).
The actual source files were inspected locally at the verified release; the
[official tagged card](https://github.com/delphes/delphes/blob/3.5.1/cards/delphes_card_ATLAS.tcl)
and [tagged modules](https://github.com/delphes/delphes/tree/3.5.1/modules)
provide public references. No official ATLAS reconstruction, calibration,
background composition or signal-sensitivity claim follows from these settings.
The frozen card physically passed Stage A 10 bbgg inputs, Stage B 100 inputs
per process and Stage C 1000 per process. Every successful native run has
N_input=N_read=N_processed=N_output=requested and N_invalid=N_skipped=0;
separate PyROOT readback assessed all seven outputs. The earlier failed
diagnostic runs remain local. Strict handling of native Float_t, ROOT signed
mass representation and source positions/ct units is recorded in the schema
report; existing strict HepMC physics gates were preserved. These execution
results validate this explicit study implementation, not ATLAS calibration
or precise small-sample performance. A/B prefixes do not add independent hard
statistics to Stage C.

# Phase 6C photon and jet validation

Final staged native validation: **PASS**, using Stage C 1000 events per process.
No official ATLAS or calibrated detector-performance claim is made.

The modified upstream ATLAS study card has SHA-256
cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47.
Both truth and reconstructed clustering use anti-kT R=0.4. Reco jets follow
calorimeter towers, stock energy scale, flavor/tagging and object uniqueness.
Uniqueness uses recursive constituent identity with photon/electron/muon/jet
priority, not a DeltaR veto. Acceptance, response and invisibles are intended;
reconstructed sums are not required to close the 13 TeV beams.

Native Photon P4 uses PT/Eta/Phi with zero mass; stored Photon.E is retained
independently. Jet P4 uses PT/Eta/Phi/Mass. Masses use Cartesian sums and
long-double arithmetic with a scale-dependent floating roundoff bound for
summed near-zero mass square. Event output includes leading selected photon
and jet pT, m_gamma_gamma, inclusive m_jj, tagged m_bb, m_bb_gamma_gamma,
DeltaR_gamma_gamma/jj/bb, DeltaEta_gamma_gamma and eligible jet/tag counts.
Inclusive and tagged jet masses have different object definitions.

The first genuine 10-event detector acceptance attempt exposed native signed
mass cancellation: event 3 reco Jet0 stored Mass=-6.7434956463e-7 GeV and
event 4 GenJet4 stored Mass=-4.7683715820e-7 GeV. Each had one constituent.
Their |M²|/p² were 1.5079690e-16 and 1.5873194e-16 (0.679 and 0.715
binary64 epsilon units). TreeWriter stores ROOT's signed momentum.M().
Native Jet P4 follows ROOT's negative-mass convention E²=p²-|M²|. The
adapter therefore preserves raw signed Mass and accepts a negative value
only when |M²|<=16*binary64_epsilon*p². Negative counts and the maximum ratio
are recorded, with no absolute-mass substitution or ROOT-file editing.
Independent FastJet comparison retains its signed mass too. Material
negative mass fails; Cartesian pair/combined physical gates retain their
own narrow numerical bound. This detector roundoff is distinct from a real
off-shell defect in a stable HepMC particle.

Selection thresholds and pT ordering use persisted native PT/Eta directly,
including exact boundary values; they do not use a slightly rounded
recalculation through trigonometric Cartesian components. Cartesian vectors
remain the source for pair masses and geometric matching.

Truth jets are independently reclustered with real FastJet from all known-PDG
status-1 input particles except neutrinos. They include photons/muons, as the
card's NeutrinoFilter does. GenJet count/kinematics are compared with this
clustering using float-aware tolerances. A photon-containing GenJet can lose
its reco Jet through uniqueness; multiplicity migrations remain visible.

Jet.Flavor is checked against known nonstable quarks 1..5/gluons, excluding
status -1, pT>1 GeV, |eta|<=2.5, DeltaR<=0.4. Highest absolute quark PDG wins;
gluons are lowest priority and no association gives zero. This includes
shower partons and is not ghost-hadron flavor. Near R=0.4, a conservative
2e-6 angular envelope covers persisted Float_t eta/phi. Only flavor values
attainable from definite and optional boundary candidates are allowed.
Multiple values are explicitly UNCERTAIN_FLOAT_BOUNDARY; arbitrary flavors fail.

Working point: **UPSTREAM_ATLAS_CARD_BIT0_STUDY**, selecting BTag bit0 only.
BTagAlgo/BTagPhys use separate random draws. Eligible reco jet denominators
are pT>25 GeV, |eta|<2.5 before event cuts. Actual Flavor determines b=5,
c=4, light=0/1/2/3/21 or UNKNOWN. Tagged counts, sums of the card's
pT-dependent probabilities, Wilson95 intervals, low-statistics flags and
standardized model-count residuals are reported. These are finite-sample
diagnostics, not calibrated 70% tagging or independent same-event jets.

Photon response compares stored reco E with final hard-origin photon E,
reporting pT-binned mean fractional residual and population RMS. Original LHE
momentum is a separate recoil diagnostic. The calorimeter smearing formula
is not claimed to be an observed matched resolution.

| Stage C process | Negative reco/gen Mass values retained | Maximum abs(M²)/p² | Flavor-boundary uncertain jets |
|---|---:|---:|---:|
| bbgg | 64/250 | 4.4493604e-16 | 0 |
| ccgg | 83/196 | 7.8762115e-16 | 0 |
| light-jjgg | 80/240 | 6.8682614e-16 | 0 |

All observed negative mass ratios are below 16*epsilon=3.5527137e-15.
The GenJet comparison diagnostic maxima were 1.5199953e-5, 2.3092052e-5 and
2.4367856e-5 respectively. This field is the maximum over pT/mass/eta/phi
component differences with mixed units; it is not a single GeV resolution.
The executable separately gates pT relative error, DeltaR and mass error.

For matched final hard-origin photons, fractional energy residual means/RMS
were:

| Process | Matched photons | Mean (E_reco-E_truth)/E_truth | Population RMS about mean |
|---|---:|---:|---:|
| bbgg | 1591 | -0.0005175851 | 0.012994529 |
| ccgg | 1472 | -0.0002016227 | 0.012479235 |
| light-jjgg | 1561 | +0.0003477436 | 0.011822333 |

These matched-only distributions combine the card response, object selection
and this sample's kinematics. They are not fitted intrinsic detector
resolution parameters. Native reports also retain truth-pT bins; high-pT bins
with 1–2 photons cannot establish a resolution trend.

Stable-visible truth-jet matched pT ratio means/RMS were bbgg
1.0255199/0.11880494, ccgg 1.0385172/0.12821260 and light-jjgg
1.0339889/0.12983493. Geometric selection and object uniqueness affect these
conditional samples; these are not jet-energy-scale calibrations.

Actual full-run response and validation evidence:
[bbgg](../simulation/delphes/evidence/bbgg/native_validation.json),
[ccgg](../simulation/delphes/evidence/ccgg/native_validation.json),
[light-jjgg](../simulation/delphes/evidence/jjgg/native_validation.json).

Sources:
[P4](https://github.com/delphes/delphes/blob/3.5.1/classes/DelphesClasses.cc),
[flavor](https://github.com/delphes/delphes/blob/3.5.1/modules/JetFlavorAssociation.cc),
[uniqueness](https://github.com/delphes/delphes/blob/3.5.1/modules/UniqueObjectFinder.cc),
[tags](https://github.com/delphes/delphes/blob/3.5.1/modules/BTagging.cc).

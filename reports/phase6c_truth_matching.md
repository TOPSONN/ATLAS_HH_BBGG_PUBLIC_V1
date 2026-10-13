# Phase 6C truth-to-reconstruction matching

Final staged matching results: **PASS native processing of all 3000 Stage C
events**; the following are descriptive geometric measurements.
Definitions are fixed before inspecting detector distributions.

The controller preserves original LHE photons/partons and raw Pythia truth
from verified Phase 6B source events/diagnostics. Final photon truth requires
stable photons with unambiguous hard-process/hard-photon-ancestor origin,
no produced-hadron origin, exactly one original hard root each, and both
distinct roots represented. Primordial-kT/recoil can move hard lab-frame p4;
original LHE photon matching is separately named.

Truth jets are independently reclustered with real FastJet anti-kT R=0.4,
inclusive pT>=20 GeV, stable known-PDG particles excluding neutrinos and
including photons/muons. Post-interface status-23 parton association is
separate and does not calibrate jets or establish one-hard-parton ancestry.

Associations maximize global one-to-one cardinality, then minimize total
DeltaR. Edges are strict DeltaR<0.2 for photons and <0.3 for jets.
Exact-cost ties retain ordered residual traversal: truth sorted by source ID,
reco ordered by descending pT then native index. Candidate-edge counts and
objects with multiple possible candidates are retained. No reco object is
counted twice within an association.

Every definition reports all/fiducial truth, unique matches, fiducial matches,
acceptance and conditional matching fractions. Photon fiducial truth is
pT>25 GeV, |eta|<2.37 excluding open 1.37<|eta|<1.52; jet fiducial truth is
pT>25 GeV, |eta|<2.5. Matching uses all native reco objects; the numerator
does not silently add reconstructed fiducial cuts.

Object-count Wilson95 intervals and low-count flags are descriptive;
same-event correlations are not modeled. Acceptance, uniqueness migrations
and denominators remain explicit. No calibrated efficiency is inferred.

Distinct terminal heavy-hadron IDs carry inclusive b/c flags; a B_c can
carry both without duplicating the object. Each is assigned once to the
nearest eligible reco jet at DeltaR<0.4 or counted unassociated. Several
distinct hadrons may belong to one jet. This remains separate from native
parton-based Flavor/BTag, without ROOT/Pythia barcode assumptions.

Analytic/API tests cover greedy-assignment loss, strict radius boundaries,
equal-cost duplicate ambiguities, wrapped phi, boosted Cartesian masses,
cut boundaries, attainable flavor sets and Wilson endpoint intervals.
They are not generated physics references.

Final hard-origin photon results (two truth photons per event):

| Process | All/fiducial truth | All/fiducial unique matches | Conditional fraction | Descriptive Wilson95 |
|---|---:|---:|---:|---|
| bbgg | 2000/1703 | 1591/1385 | 0.813271 | [0.794065,0.831066] |
| ccgg | 2000/1720 | 1472/1291 | 0.750581 | [0.729590,0.770456] |
| light-jjgg | 2000/1709 | 1561/1356 | 0.793446 | [0.773605,0.811972] |

No photon matching had multiple candidate truth/reconstructed edges in
these actual samples. Original-LHE photon matching gave 1095, 926 and 1134
all-truth matches respectively, substantially different from final photon
truth. This validates the importance of separating the truth definitions;
it does not attribute the difference solely to detector response.

Stable-visible anti-kT R0.4 truth-jet results:

| Process | All/fiducial truth jets | All/fiducial unique matches | Conditional fraction | Descriptive Wilson95 | Truth/reco objects with multiple candidates |
|---|---:|---:|---:|---|---:|
| bbgg | 4322/3601 | 2476/1995 | 0.554013 | [0.537729,0.570182] | 5/6 |
| ccgg | 4487/3675 | 2723/2211 | 0.601633 | [0.585706,0.617347] | 19/7 |
| light-jjgg | 4474/3661 | 2654/2100 | 0.573614 | [0.557525,0.589548] | 5/9 |

The matching solver resolves these competing edges with one-to-one
assignments and retains the ambiguity counts. Lower jet fractions do not
isolate tracking/calorimeter inefficiency: photon-containing truth jets and
final reco uniqueness have different object definitions.

Unique terminal heavy-hadron objects assigned/unassociated were bbgg
2956/2078, ccgg1451/1168 and light-jjgg135/473. These are inclusive combined
b/c terminal-object counts, not independent original-hard-quark counts or
an efficiency denominator. Heavy shower production in light-jjgg is therefore
not silently interpreted as an original b/c final state.

Full matching counters, response moments, pT bins and multiplicity migration
matrices are retained in the actual
[bbgg](../simulation/delphes/evidence/bbgg/native_validation.json),
[ccgg](../simulation/delphes/evidence/ccgg/native_validation.json) and
[light-jjgg](../simulation/delphes/evidence/jjgg/native_validation.json)
reports. Full ROOT files remain local; hashes attest their identity rather
than pretending portable CI can inspect omitted detector records.

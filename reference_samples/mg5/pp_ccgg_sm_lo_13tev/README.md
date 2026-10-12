# Actual LO charm-pair plus diphoton reference

`reference_1000.lhe.gz` contains 1000 actual MadGraph5_aMC@NLO 3.5.16 events,
seed 20261021, generated with `p p > c c~ a a QCD=2 QED=2` at sqrt(s)=13 TeV.
It is the charm component of the local 3000-event background library, alongside
the unchanged historical bbgg 1000 and the separate light-jjgg 1000 references.
The historical bbgg smoke sample is not included in that 3000-event count.

The model is bundled `sm-no_b_mass`, diagonal CKM, with a massless five-flavour
proton including g/u/d/s/c/b and antipartons. Charm is massless and receives
ordinary jet generation cuts. Built-in CTEQ6L1 is PDF ID10042; muR/muF1/muF2
are fixed at125 GeV. Photons satisfy pT>=25 GeV, |eta|<=2.5; charm jets pT>=20
GeV, |eta|<=5. Photon-photon, photon-jet and jet-jet DeltaR are >=0.4.
`maxjetflavor=4` classifies charm as a jet and bottom separately. `ptgmin=0`
disables smooth-cone isolation. Exact applied cards, cross section/integration
error, banner couplings, counts, execution timings and SHA-256 are in
`sample_manifest.json`; the integration estimate is derived from this sample.

Only the gzip container metadata is changed for deterministic publication.
Decompressed original MG5 LHE bytes and all event blocks remain unchanged.
MG5 IDWTUP=-4 with `event_norm=average` gives a positive constant XWGTUP in pb;
normalize histograms with XWGTUP/N. This convention does not make raw weights
additive cross sections, and independent process estimates should not be summed
without a defined combined observable and normalization.

From the repository root, with Python3.11 or newer:

```bash
python3 -B simulation/mg5/scripts/validate_lhe.py --background-library .
python3 -B simulation/mg5/scripts/validate_lhe.py \
  --file reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz \
  --events 1000 --profile ccgg
```

Validation covers gzip/XML integrity, all event counts, final-state PDGs,
finite values, mass shell, four-momentum, generation cuts, weights, actual cards
and provenance hashes. This is a small direct tree-level parton sample: no NLO,
shower, hadronization, charm tagging, detector response or ATLAS background
normalization is claimed. Finite parton cuts are not reconstructed selections,
and this sample does not define a full isolated-photon NLO observable.

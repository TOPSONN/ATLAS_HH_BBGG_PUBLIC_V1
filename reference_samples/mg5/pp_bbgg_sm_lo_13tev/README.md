# Actual MadGraph LO bbgg references

These are small, real MadGraph5_aMC@NLO 3.5.16 event samples, produced at tree
level with `p p > b b~ a a QCD=2 QED=2`, 13 TeV proton collisions and fixed seeds.
They are a public reproducibility reference for this project, not official
ATLAS simulation or an inclusive background prediction.

`smoke_100.lhe.gz` contains 100 events (seed 20261012).
`reference_1000.lhe.gz` contains 1000 events (seed 20261013).
The exact integration estimates, sizes, hashes and card paths are in
`sample_manifest.json`. No event records or decompressed LHE bytes were changed.
Only the gzip container was made deterministic (mtime=0, no filename).

Model: bundled `sm-no_b_mass`; MB=0 and ymb=0; diagonal CKM.
Five-flavour massless hard process with u,d,s,c,b PDFs and antiquarks, plus g.
PDF: MG5 built-in CTEQ6L1, identifier 10042, LO alpha_s(MZ)=0.130.
Both scales are fixed at 125 GeV. The b-specific cut classification is
`maxjetflavor=4`; this does not remove b from the explicitly declared proton.

Finite parton-level cuts: photons pT >=25 GeV and |eta|<=2.5; b partons
pT>=20 GeV and |eta|<=5; each gamma-gamma, b-gamma and b-bbar separation
DeltaR>=0.4. These are generation cuts. Smooth-cone isolation is disabled
(`ptgmin=0`). This finite direct tree-level phase space does not define a full
isolated-photon NLO observable or include photon fragmentation contributions.

MG5 writes IDWTUP=-4 with `event_norm=average`: each nominal XWGTUP is a positive
constant in pb approximately equal to the integrated cross section. Normalize
an event histogram using XWGTUP/N; summing these raw weights without dividing by
the event count would overcount by N. There are no negative or zero weights.

From the repository root, using Python 3.11 or newer:

```bash
python3 -B simulation/mg5/scripts/validate_lhe.py --repository .
python3 -B -m unittest discover -s simulation/mg5/tests -v
```

Validation checks actual gzip/XML/events, numerical closure, mass shell,
particle content, actual banner cards, applied seeds, file sizes and hashes.
The GitHub CI does not install or run MG5, ROOT, Pythia8 or Delphes. No shower,
detector response, NLO accuracy, HH sensitivity or ATLAS normalization is claimed.

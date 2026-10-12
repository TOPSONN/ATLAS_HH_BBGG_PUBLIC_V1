# Actual LO light-parton plus diphoton reference

`reference_1000.lhe.gz` contains 1000 actual MadGraph5_aMC@NLO 3.5.16 events,
seed 20261022, generated with `p p > a a jl jl QCD=2 QED=2` at sqrt(s)=13 TeV.
The explicit `jl = g u d s u~ d~ s~` definition excludes charm and bottom from
final-state light jets. The incoming proton remains five-flavour, including
charm and bottom PDFs. This is distinct from the bbgg and ccgg components.

The bundled model is `sm-no_b_mass`, diagonal CKM. Built-in CTEQ6L1 is PDF
ID10042; muR/muF1/muF2 are fixed at125 GeV. Photons satisfy pT>=25 GeV and
|eta|<=2.5; light partons pT>=20 GeV and |eta|<=5. Photon-photon, photon-jet
and jet-jet DeltaR are >=0.4. `maxjetflavor=4` applies ordinary jet cuts;
`ptgmin=0` disables smooth-cone isolation. The actual process/run/parameter
cards, applied seed, cross section/integration error, banner couplings,
execution timings and SHA-256 are recorded in `sample_manifest.json`.

The 3000-event library consists of the unchanged historical bbgg1000, ccgg1000
and this light-jjgg1000; bbgg smoke100 is excluded. Event counts describe these
small reference components, not inclusive rates or production statistics.
Only gzip metadata is made deterministic; decompressed MG5 LHE bytes and event
records remain exact. IDWTUP=-4 and `event_norm=average` give positive constant
XWGTUP in pb. Normalize each process histogram using XWGTUP/N and its defined
normalization; do not add raw weights or concatenate LHE headers blindly.

From the repository root, with Python3.11 or newer:

```bash
python3 -B simulation/mg5/scripts/validate_lhe.py --background-library .
python3 -B simulation/mg5/scripts/validate_lhe.py \
  --file reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz \
  --events 1000 --profile jjgg
```

Validation checks every final state for two photons and two allowed light
partons, including absence of final-state charm/bottom, plus gzip/XML, counts,
finite values, mass shell, four-momentum, cuts, weights, cards and hashes.
There is no shower, hadronization, jet reconstruction, b/charm mistag response,
detector simulation, NLO accuracy or ATLAS normalization claim. These generation
cuts do not define a complete isolated-photon NLO observable. A light-jet event
is not a bbgg detector background until the required detector/tagging model is
specified and validated.

# Phase6B shower configuration

The canonical configuration is the source-reviewed isolated baseline **v2**,
Pythia8.317 with HepMC3.3.1. Its immutable card SHA256 is
`53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389`.
The78 explicit settings were checked against the verified release XML/source;
this source check establishes setting definitions, not physical event acceptance.
Fresh v2 A/B/C runs physically passed: A10bbgg, B100per process, and C1000per
process. All3000 StageC inputs were independently assessed and written/read
back, with zero shower or validation failures. Configuration changes require
new physical runs; the prior failed OFF diagnostic remains failed.

The three existing MG5 samples remain separate LO hard-process inputs at13TeV,
with independent cross sections, source identities and full-input weight
denominators. External LHE mode reads their2212 beam identities and6500GeV beam
energies. Internal replacement hard-process generation, extra hard scattering,
matching/merging, MPI and pileup are absent. This phase has no detector simulation.

| Setting group | Explicit choice and scientific meaning |
|---|---|
| External interface | `Beams:frameType=4`, strict LHEF scale handling, original LHE bytes preserved |
| Shower | Simple pT-ordered model1, ISR and FSR ON; backwards ISR and timelike FSR |
| Upper scale | SpaceShower/TimeShower `pTmaxMatch=1`, `pTmaxFudge=1`; input SCALUP125GeV |
| Matching/recoil | ME-correction overrides OFF, ISR dipoleRecoil OFF, FSR globalRecoil OFF; no independent ME/PS matching |
| PDF/coupling | Internal CTEQ6L1 (`PDF:pSet=8`), shower alphaS(MZ)=0.130, one-loop, CMW OFF, ISR nQuarkIn5 |
| Hadronization | Lund string fragmentation ON; inherited Monash fragmentation/flavour parameters saved in effective settings |
| Decays | Applicable built-in decays ON; `limitTau0=on`, tau0Max10mm, strict c*tau>10mm stable convention |
| Heavy masses | Shower/particle-data c=1.5GeV, b=4.8GeV; original MG5 hard partons remain massless |
| Photons | Quark/lepton QED radiation ON, alphaEMorder1; gamma-to-fermion shower conversion OFF; limited hadron-level QED ON, gammaModeHad1 |
| Beam/remnant model | Stock primordial kT ON in v2; six width/damping parameters explicitly frozen below |
| Isolated baseline | MPI OFF, second hard generation OFF, colour reconnection OFF, no pileup stream |
| Variations | Shower variation bands OFF; signed nominal/raw provenance weights retained |

Respecting SCALUP is a shower starting-scale convention. It does not implement
MLM, CKKW-L, LO+PS matching or NLO+PS, and can leave harder-radiation coverage
gaps. The simple-shower recoil choices and missing matching require separate
systematic assessment before precision use. See the official
[LHE interface](https://pythia.org/latest-manual/LHEF.html),
[ISR settings](https://pythia.org/latest-manual/SpacelikeShowers.html) and
[FSR settings](https://pythia.org/latest-manual/TimelikeShowers.html).

Tune:ee7 and Tune:pp14 supply a Monash starting point, followed by explicit PDF,
coupling and isolated-event overrides. It is a modified baseline, without a
full Monash or calibrated ATLAS tune claim. Internal CTEQ6L1 is the same named
PDF fit as the hard input, but threshold/infrared treatment and interpolation
do not establish identical coupling evolution. The default running QED scheme
also need not equal the MG5 hard-process alphaEM convention. Full post-init
effective settings and particle data are mandatory evidence. See
[PDF selection](https://pythia.org/latest-manual/PDFSelection.html) and
[tune loading](https://pythia.org/latest-manual/Tunes.html).

The versioned Monash e+e- tune card assigns StringZ:aLund0.68, bLund0.98,
rFactC1.32, rFactB0.855 and StringPT:sigma0.335GeV, along with flavour fractions
including probStoUD0.217 and probQQtoQ0.081. These inherited parameters are not
retuned here. Their exact source identity and actual effective values are
separate checks. The limited hadron-level photon radiation choice is not a
complete decay-radiation calculation; disabling gamma conversion explicitly
omits that contribution. See the distributed
[Monash e+e- card](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/share/Pythia8/tunes/Monash2013-ee.cmnd)
and [decay controls](https://pythia.org/latest-manual/ParticleDecays.html).

## Preserved failed OFF configuration and v2 physical model change

The earlier additional primordialKT=OFF override is retained byte-for-byte as
[diagnostic_collinear_disabled.cmnd](../simulation/pythia8/config/diagnostic_collinear_disabled.cmnd),
SHA256 `a1e62fdaf6a6b487a1d9c696b87fa4ce9edec31c0b3b00dca5e985cba4ab7dd5`.
Its status is **NOT_APPROVED_FOR_REFERENCE**; the normal CLI and publisher
reject it. The preserved real bbgg100 diagnostic run wrote100 outputs, with
100 successful Pythia calls and zero shower failures, but the strict independent
ReaderAscii validator exited1 for a stable-particle mass-shell failure.
Its overall status is **PARTIAL**, not physical PASS.

The unmodified raw Pythia particle diagnostics independently show three stable
failures in event54: one PDG310 and two PDG22. The PDG310 mass-squared residual
is0.04337527196732083GeV² against tolerance0.00983071310329683GeV²; the photon
residuals are0.0015429833983944263 and0.028556431585457176GeV² against
1.6542891609421146e-5 and0.00030465918177574917GeV². These are failures before
HepMC serialization. No four-vector, particle mass, event block or QA tolerance
was changed to make this diagnostic pass. The failed physics files stay local.

The investigated topology contains exactly collinear beam-remnant mini-string
endpoints. In verified8.317 source, StringRegion::setUp uses binary64 Minkowski
products to construct light-cone directions. This observed event reaches the
later `pPos.e()<TINY || pNeg.e()<TINY` branch: pNeg.e≈−5.12478e−5GeV,
where high-precision evaluation of the preserved endpoints gives a positive
≈4.5844e−5GeV. It returns an empty region before constructing the transverse
basis. The upstream API test reproduces this branch. The preceding w²<m2Join
branch exists but is not the observed event54 failure. This source/diagnostic
correlation does not establish a universal failure rate. Identities are in
[baseline_v2_source_review.json](../simulation/pythia8/evidence/baseline_v2_source_review.json).

Version2 restores the documented stock nonperturbative beam/remnant model.
This is a physical configuration change, not an epsilon inserted into a bad
four-vector or a patch to upstream physics code. The explicit parameters are:

| Parameter | Frozen value | Source |
|---|---:|---|
| primordialKT | ON | Release XML default |
| primordialKTsoft |0.9GeV | Monash pp card and XML |
| primordialKThard |1.8GeV | Monash pp card and XML |
| halfScaleForKT |1.5GeV | Monash pp card and XML |
| halfMassForKT |1.0GeV | Monash pp card and XML |
| reducedKTatHighY |0.5 | XML default |
| primordialKTremnant |0.4GeV | XML default |

For the first external LHE subsystem, source bypasses the soft-scale
interpolation. Its pre-compensation Cartesian Gaussian width is
`sigma=1.8GeV*m/[m+1.0GeV*(E/m)^0.5]`; remnant components use0.4GeV.
Momentum compensation shares recoil and introduces correlations. Consequently
the quoted widths are neither fixed kick magnitudes nor the final observed pT
RMS. Normal-subsystem invariant mass and rapidity are retained by Pythia's
rotation/boost construction, while laboratory-frame subsystem/remnant momenta
change. Original hard LHE records remain separately immutable.
[Beam-remnant documentation](https://pythia.org/latest-manual/BeamRemnants.html)
and the exact versioned source hashes are the authority.

Primordial kT is distinct from MPI. MPI remains OFF, so enabling the stock
remnant model does not add a second hard scattering or establish a complete
ATLAS underlying event. It changes nonperturbative recoil distributions and
random-number consumption, requiring fresh A/B/C runs and separate diagnostics.
No universal cure, reproducibility PASS or numerical success is inferred from
the source review. Strict mass-shell, graph, weight and momentum QA remain
unchanged. Only actual independently validated v2 runs can become references.

## Acceptance and scope

The78-definition source proof is in
[baseline_xml_validation.json](../simulation/pythia8/evidence/baseline_xml_validation.json).
Normal self-service requests literal-pin the reviewed card; arbitrary custom
cards and the failed diagnostic card are unsupported. A future physics card
needs a new version, source review, immutable hash and new physical validation.
Hadron/parton flavour and photon ancestry remain distinct; unknown origins are
retained. No truth hadron is claimed to be a calibrated reconstructed ATLAS jet.

The actual v2 stage gzip identities are:

| Stage/process | Inputs/valid outputs | Gzip SHA256 |
|---|---:|---|
| A/bbgg |10/10 | `874ccb3e2a4681a5e48a4f31ce02f143ca84a8b7ae1c7126c15b3615a6e6e731` |
| B/bbgg |100/100 | `737e30b2242fe009284ae7de6939534162dfcf4d7c4e275abfccbe667933237e` |
| B/ccgg |100/100 | `99729939fe8fab4b87fa2bab5bb67b09db056b04c6f87d4fd437a90c34536232` |
| B/jjgg |100/100 | `1c8094b23b545c1122e1ad684810fbb074fe5499ca66caab78e489c3661f0077` |
| C/bbgg |1000/1000 | `a35e15942ac5442b3141960f0c0602f5a4cb63ea853f1090fa9e46f304209536` |
| C/ccgg |1000/1000 | `ad173686a9d9cb342796016bdb2ea6b70f08a5b921233da0d33d9dd8945cf9bb` |
| C/jjgg |1000/1000 | `2643f0c14440b25267a153b72a7d676c337fd182a39e62fdcbe2191361a91365` |

StageA/B are interface/physics prefix checks, with no additional independent
MG5 statistics. The published100 references are selected from StageC itself,
with its original run identities/event blocks; they are not replaced by the
separately processed StageB files. The3000-event assessment uses StageC only.

Actual StageC required-settings readback confirmed primordialKT ON and all six
stock parameters, MPI OFF and the selected shower/decay controls. Complete
ReaderAscii assessment counts are1000each, zero failed or unassessed. Maximum
stable mass-shell residual/tolerance ratios are0.0001187991/0.0042063064/
0.0006403384 for bbgg/ccgg/jjgg. Physical report identities are preserved with
the selected references; passing these tests is not a universal future guarantee.

The logs retain expected SLHA warnings: light SM MASS/DECAY imports below
SLHA:minMassSM are ignored and empty DECAY tables for6/25 contain no branching
ratios. Built-in Pythia particle data/decays and the explicit1.5/4.8GeV heavy
mass convention remain in use, with effective particle data archived. These
warnings are not evidence of unchanged hard/shower kinematics.

The ccgg1000 run additionally records one upstream HadronWidths::pickMasses
warning about angular momentum/running widths. Verified8.317 source switches
off variable-width weighting late in its attempt loop, then removes the
angular-momentum weighting for still later attempts before accepting a mass
pair and issuing this warning. It is a recorded stock fallback/approximation,
without a precision decay-model claim. The warning text alone does not identify
the event/PDGs, so that attribution remains UNKNOWN. No source/defaults or QA
threshold were changed to suppress it; the resulting event records were still
fully assessed by the strict independent validator.

No1M sample processing or Delphes runtime test was executed. Measured1000-run
CLI elapsed times14.21/16.99/15.95s and total local directory bytes
250644633/273911296/275587484 inform planning only. A linear estimate for a
single1M run with similar events and all diagnostics is approximately250–276GB
(decimal), with unknown production scaling and required headroom; it is not a
1M benchmark. The guide offers a375GiB budget example and a dry-run template.
Remote publication and final-head CI acceptance remain separate pending gates.

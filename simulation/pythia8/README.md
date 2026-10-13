# External MG5 LHE to Pythia8 and HepMC3

Phase 6B processes the three verified 1000-event MG5 references independently.
It adds a C++ external-LHE shower/hadronization runner, an event identity ledger,
real HepMC3 ReaderAscii validation, and portable publication integrity checks.
MG5 inputs, cards, cross sections and earlier scientific history are preserved.
No new MG5 events, detector simulation or million-event processing is performed
by this phase. The branch stacks on `codex/phase6a-backgrounds-1k`.

The complete operating instructions are in
[USER_GUIDE_ZH_TW.md](USER_GUIDE_ZH_TW.md). In Ubuntu WSL at `/mnt/c/HH`:

```bash
bash simulation/pythia8/scripts/shower_sample.sh \
  --input reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz \
  --process bbgg --events 1000 --seed 610201 \
  --output /home/btu/simulations/pythia8_runs/my_bbgg_1k \
  --settings simulation/pythia8/config/baseline_shower.cmnd \
  --jobs 1 --max-hours 1 --max-disk-gb 5
```

Verified dependencies are Pythia8.317 and HepMC3.3.1 (the latter's runtime string
is `3.03.01`). Pythia's [official8.317 archive](https://pythia.org/releases/pythia83/pythia8317.tgz)
was compared to official commit `83a5c9986f30746cfb390435a9b10ac55a758fca`.
Installation registration and full runs remain local. The preferred isolated
prefix is `/home/btu/opt/pythia8/`; ordinary commands reuse installed tools.
There is no automatic personal-run commit, push or release. Existing outputs
are never overwritten. A dry-run validates inputs/configuration/resources with
zero physics events. Partial processing retains counters and original source
identities, and cannot be reported as 1000 accepted outputs.

The versioned card selects the simple pT-ordered shower, ISR/FSR, Lund string
fragmentation and built-in decays. It starts from Monash parameters and then
explicitly overrides the PDF, couplings and isolated-shower switches; it is a
modified baseline with no calibrated tune claim. MPI and colour reconnection
are off. Version2 retains the documented stock primordial transverse-momentum
model for initiators/remnants, with explicit Gaussian widths and recoil sharing.
Beam remnants remain part of the physical event. No pileup stream is added.

The earlier extra override `primordialKT=off` produced a strict stable-particle
mass-shell failure in the real100-event bbgg diagnostic run. Its exact card is
preserved as `config/diagnostic_collinear_disabled.cmnd`, SHA256
`a1e62fdaf6a6b487a1d9c696b87fa4ce9edec31c0b3b00dca5e985cba4ab7dd5`,
and is **NOT_APPROVED_FOR_REFERENCE**; the normal CLI rejects it. Version2 is
SHA256 `53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389`.
This is a physical model change requiring fresh A/B/C runs with unchanged QA,
not an event repair or a guarantee of numerical success. The source-backed
[configuration report](../../reports/phase6b_shower_configuration.md) documents
the Gaussian widths, compensation and preserved failed diagnostic.

`Beams:frameType=4` reads proton identities and beam energies from LHE.
`SpaceShower:pTmaxMatch=1` and `TimeShower:pTmaxMatch=1` use its SCALUP limit,
which is125 GeV for these inputs. This is a shower starting-scale choice,
with no independent ME/PS matching or merging. It can leave hard-radiation
coverage gaps; no MLM, CKKW-L or NLO+PS accuracy is claimed.
[Pythia LHE documentation](https://pythia.org/latest-manual/LHEF.html)
describes this interface and scale behavior.

The shower uses internal CTEQ6L1 (`PDF:pSet=8`), one-loop alphaS(MZ)=0.130,
and no CMW rescaling. The inherited Monash alphaS/PDF choices are intentionally
overridden after loading the tune. Different threshold/infrared treatments
mean these settings do not establish exact equality to MG5's hard-process
coupling evolution. Full effective settings and particle data are saved.
[PDF selection](https://pythia.org/latest-manual/PDFSelection.html) and
[tune ordering](https://pythia.org/latest-manual/Tunes.html) explain the distinction.

Shower c/b masses are1.5/4.8 GeV; MG5's hard inputs remain massless.
Short-lived applicable hadrons decay, while the chosen truth convention keeps
c*tau>10 mm particles stable (the source applies a strict greater-than cutoff).
QED emission from quarks/leptons is on; limited
hadron-level QED radiation uses gammaModeHad1. Photon conversion to fermion
pairs is explicitly off in this first direct-photon baseline. This excludes
that shower contribution and is not an output repair. Hadron decays and
QED emissions can add photons; ancestry classification retains ambiguous cases.
[Decay controls](https://pythia.org/latest-manual/ParticleDecays.html) specify
the lifetime and mayDecay conditions.

Each output retains the MG5 sample hash and event index/hash, Pythia run/seed,
processing attempt/status, HepMC event index/hash and signed raw weights.
For LHE strategy-4, Pythia nominal weights are in pb; sigmaGen/sigmaErr are
in mb. The official HepMC3 converter stores weights and converts cross section
to pb. The first output weight `input_contribution_pb` is already LHE_XWGTUP/N;
the remaining named columns retain raw LHE/Pythia/converter provenance in pb.
Input sigma is never multiplied twice, and the first weight is not divided by N
again. Contributions use the original input normalization, with explicit rejection accounting; a100-event published
subset is not a new independent hard sample or the full process integral.
[Pythia weight documentation](https://pythia.org/latest-manual/CrossSectionsAndWeights.html)
and the actual installed interface are the authority.

Only selected real ASCII event blocks from validated full runs are published.
The100-event prefixes preserve every chosen event's exact bytes and identities;
only gzip container metadata is deterministic. Optional full1000 archives must
fit10 MiB each and30 MiB combined. Large outputs stay local, with exact hashes
and a concrete Draft Release proposal; no release or upload occurs automatically.
Portable Python CI checks compressed/text integrity and provenance. It does not
prove HepMC3 library compatibility; that is assessed with real local ReaderAscii.
The original full1000 JSONL ledger is also published as bounded evidence, so CI
checks exact selected-line membership in the full-run identity mapping. If full
HepMC is absent from Git, this mapping does not replace full-file library readback.

The official [Delphes HepMC3 entry point](https://github.com/delphes/delphes/blob/master/readers/DelphesHepMC3.cpp)
and [ASCII reader](https://github.com/delphes/delphes/blob/master/classes/DelphesHepMC3Reader.cc)
were inspected for future use: they read E/U/W/A/V/P records, GEV/MM units,
weights, vertices and stable status1 particles. This is source compatibility
inspection only; Delphes is neither installed nor executed in Phase6B.

Use explicit staging paths and `audit_shower.py` before pushing. Every outgoing
commit is checked for unselected archives, private data and unapproved figures.
PDF/PNG require exact-version user approval independently of tests. No PR is
automatically merged. Pythia physics and usage should cite the
[Pythia8.3 manual](https://arxiv.org/abs/2203.11601) and follow the distributed
Pythia GPLv2-or-later license and the distributed
[MCnet guidelines](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/GUIDELINES).
HepMC3 uses LGPLv3.
The dependency licenses do not replace this repository's existing license.

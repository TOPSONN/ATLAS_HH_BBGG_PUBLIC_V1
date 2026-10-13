# Real Pythia8 shower reference: jjgg

The selected `shower_100.hepmc3.gz` records are the first100 whole ASCII events
from the actual independently validated1000-input shower run. They retain
original event numbers and exact event-block bytes, with matching source ledger
rows. Gzip metadata is deterministic; no particle/event reserialization is used.
This is a subset of the full run, not a new independent MG5 physics sample.

The hard source is `reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz`:
1000 original13 TeV MG5 LO inputs, with two hard photons and two light partons from g/u/d/s and antipartons, excluding final c/b.
Its generator cross section remains 9.436556 +/- 0.0547472 pb. The exact source
SHA-256, applied Pythia seed610203, Pythia8.317/HepMC3.3.1 identities, settings,
full-output hashes, selected ledger and physical readback proof are recorded in
`sample_manifest.json`. Full1000 output is also included only when its gzip
fits10 MiB and all published full samples fit30 MiB combined; otherwise it stays
local and a concrete Draft Release proposal is recorded without any upload.
The original full1000 JSONL ledger is preserved as bounded evidence. CI checks
the exact selected raw lines against that full-run mapping; this does not read
an omitted full HepMC file or replace the actual file-bound C++ readback report.

The first weight `input_contribution_pb` already equals signed LHE_XWGTUP/1000.
Its sum across100 selected events is one tenth of the full input normalization,
subject to the explicitly assessed processing success. Remaining named columns
retain raw LHE, Pythia and converter weights in pb; they are provenance columns,
not uncertainty variations. Do not multiply by sigma or divide by event count
again. Pythia sigmaGen/sigmaErr APIs use mb, and the HepMC cross-section attribute
uses pb. These distinct quantities are separately audited.

The immutable isolated-shower baseline enables ISR/FSR, Lund fragmentation and
applicable short-lived decays, using SCALUP125 GeV as the shower upper-scale
convention. MPI, pileup and colour reconnection are off. Version2 retains the
stock primordial-kT initiator/remnant model with explicit widths and recoil
compensation; this is a nonperturbative model change from the failed OFF
diagnostic configuration, requiring fresh runs with unchanged strict QA. QED
emission/decay photons can add final photons; gamma-to-fermion shower conversion
is explicitly excluded. Extra heavy flavour can appear in showers. Hard parton
flavour, heavy-hadron ancestry and stable final-state particles are distinct.
The modified tune is not an ATLAS tune, ME/PS matching, merging, NLO+PS or a
complete underlying-event/detector model. No tagging, mistag, photon-fake,
trigger, detector-resolution or absolute ATLAS-yield claim is made.

From the repository root:

```bash
python3 -B simulation/pythia8/scripts/validate_hepmc3.py --repository .
python3 -B -m unittest discover -s simulation/pythia8/tests -v
```

Portable Python checks file/text/graph/weight/source-ledger integrity. Actual
HepMC3 ReaderAscii and Pythia ParticleData readback is a separate local physical
check, whose full-run file-bound report is preserved. Python parsing alone does
not prove library or Delphes runtime compatibility. See
[the operating guide](../../../simulation/pythia8/USER_GUIDE_ZH_TW.md) and
[configuration notes](../../../simulation/pythia8/README.md).

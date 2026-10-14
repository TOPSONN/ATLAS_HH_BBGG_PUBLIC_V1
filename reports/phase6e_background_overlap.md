# Phase6E continuum background overlap risk

**OVERLAP_RISK_UNRESOLVED. Do not stitch/subtract or combine these pilots into
an official background prediction.** The three original source records remain
unchanged. Their Born definitions differ, but reconstructed flavour categories
need not be exclusive after shower and detector association.

| Original sample | Actual Born final state | Incoming proton/PDF | Available extra radiation |
|---|---|---|---|
| bbgg | `b b~ a a`, QCD2/QED2 | Explicit5F p including c/b; CTEQ6L1, ID10042 | QCD/QED ISR/FSR; further heavy-flavour production can occur |
| ccgg | `c c~ a a`, QCD2/QED2 | Same5F p/PDF | Bottom can appear beyond Born charm; labels are not a pure c-mistag category |
| light-jjgg | `a a jl jl`, `jl=g,u,d,s` and antiquarks, QCD2/QED2 | Same5F p/PDF, despite final `jl` excluding c/b | Heavy-flavour incoming PDFs and shower production are not excluded by the final-state alias |

Actual archived run cards use 13 TeV, fixed renormalization/factorization
scale125 GeV, `ickkw=0`, `xqcut=0`. Ordinary and bottom cuts are explicit with
`maxjetflavor=4`; photon pT25 GeV/separation0.4 are finite Born definitions,
not a validated photon-fragmentation/identification model. The fixed
[Pythia baseline](../simulation/pythia8/config/baseline_shower.cmnd) enables
QCD/QED ISR/FSR and five incoming quark flavours, disables MPI/second hard
interaction and matching/merging, and honors SCALUP through pTmaxMatch1.
That scale ceiling does not provide sample partitioning or matching/merging.
Primordial kT/remnants remain enabled as recorded. No ATLAS calibration is
implied by these choices.

| Source pair | Shared possible reconstructed configuration | Risk/gate |
|---|---|---|
| bbgg ↔ ccgg | bb/cb/mixed flavour jets plus prompt photons, with extra heavy radiation or changed associations | Different lowest-order partonic states; common higher-multiplicity reconstructed regions require a heavy-flavour scheme and ME/PS definition |
| bbgg ↔ light-jjgg | Two associated-b jets after radiation, including g→bb, plus photons | Final-state names do not establish exclusivity; actual ancestry and a validated partition are required |
| ccgg ↔ light-jjgg | Charm/mixed-flavour jets after radiation | Final `jl` restriction does not suppress all shower or incoming charm; no matching boundary exists |
| Existing diphoton sources ↔ proposed bbγj | A second shower/fragmentation/nonprompt photon or photon-like detector candidate | Prompt/fake definition, QED ME/PS overlap policy and calibrated transfer/closure are missing |
| Continuum ↔ proposed ttH/ZH with H→γγ | Same selected bbγγ topology, but a resonant single Higgs | A resonance-aware definition/decay contract is required; equal topology is not identical Born physics, and interference treatment must be stated |

This is a qualitative phase-space risk matrix, not proof that a particular
existing event was generated twice, nor a numerical double-count estimate.
At the Born level the explicit final flavours distinguish matrix elements;
after shower, higher-multiplicity final states and reconstructed flavour
selections can approach the same regions without a supplied partition.
Different seeds/source hashes establish event identity, not phase-space
exclusivity. One must not invent subtraction, negative stitching weights,
drop source997, or treat native flavour disagreement as a correction.

## Actual fixed-pilot native flavour mixtures

The following fractions come from the actual all1000-event per-process
conditional analysis after the original photon/jet/two-tag/mgg selection.
They partition the **leading tagged-pair probability**, using unchanged
native `DELPHES_ASSOCIATED_FLAVOUR`. Each event retains its original weight
and denominator1000. Fractions are model-expected contributions, not observed
tag counts, calibrated efficiencies or hard/heavy-hadron truth labels.

| Process | bb % | bc % | b-light % | cc % | c-light % | light-light % |
|---|---:|---:|---:|---:|---:|---:|
| bbgg | 98.893131 | 0.883183 | 0.223637 | 0 | 0 | 0.0000495953 |
| ccgg | 0 | 18.794027 | 0.090688 | 79.764496 | 1.347626 | 0.003163134 |
| light-jjgg | 97.163602 | 0 | 1.678316 | 0 | 1.004655 | 0.153426 |

A separate **event-level tag-origin partition** gives bbgg/ccgg/jjgg fractions
with at least two native-b tags of99.164573%/0%/97.894168%; exactly one native-b
tag plus non-b tags0.835377%/19.822297%/0.948416%; zero native-b tags and at
least two non-b tags0.0000495953%/80.177703%/1.157416%. These partitions have
different definitions when events contain additional tagged jets; they must
not be interchanged or summed together. “Native associated-b” is a detector
association diagnostic; it does not alone prove a hard b, g→bb, or a specific
b hadron. The separate forensic graph investigation provides those origin
claims, with UNKNOWN retained where relationships cannot be established.

The light-jjgg final conditional expectation is0.5013245166140850 events;
source997 supplies98.52106957% in this fixed pilot. Therefore its native-b
mixture is strongly influenced by a rare event, not established as a stable
inclusive flavour fraction. All events remain authoritative. A leave-one-out
number is a diagnostic, not a repaired physical prediction. No reconstruction
working point, tag bits, shower settings, cuts or original event was modified.

The exact fractions and source bindings are in the Phase6E influence evidence
and [phase6e_flavour_decomposition.csv](../metadata/phase6e_flavour_decomposition.csv).
Overlap resolution requires an explicitly chosen heavy-flavour/matching scheme,
all needed matrix-element multiplicities and photon definitions, with actual
closure tests. The current pilots can diagnose this risk, but cannot provide
an official ATLAS background sum, a calibrated photon-fake rate, or HH signal
sensitivity.

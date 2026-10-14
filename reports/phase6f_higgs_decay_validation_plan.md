# Phase6F Higgs decay validation plan

The preferred future input is `ZH_ZBB_STABLE_H`: MG5 prepares the resonant
`p p > z h QCD=0 QED=2, z > b b~` chain with stable H, followed by a separately
audited Pythia H→γγ decay. This phase has produced **zero physics events**.
`physical_decay_validation=NOT_EXECUTED` and
`external_lhe_weight_closure=UNKNOWN` remain mandatory gates.

## Route and spin treatment

| Route | MG5 source | Decay factors present in future source normalization | Remaining decay | Assessment |
| --- | --- | --- | --- | --- |
| A | Stable ZH production | None | External Pythia Z→bb and H→γγ | Prepared alternative; external Z production-spin limitation |
| B, preferred | Resonant Z→bb chain plus stable H | `Z_to_b_bbar`, with actual source widths/window | External Pythia H→γγ | Preferred for future physical validation; no second Z BR |

The [MG5 decay-chain documentation](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/FAQ-General-6)
describes correlated matrix elements with a Breit–Wigner resonance. It is a
resonant-diagram approximation, rather than the complete nonresonant final-state
amplitude. Its integrated result depends on the fixed width and resonance window;
it must not be assumed to equal an independently calculated inclusive σZH times
a reference BR exactly.

The pinned Pythia8.317
[SigmaLHAProcess source](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/src/SigmaProcess.cc)
(`weightDecay`, lines1348–1370) leaves input decays unchanged, supplies specialized
Higgs/top angular handlers, and returns unit angular weight for the other
external mothers. The
[ProcessContainer source](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/src/ProcessContainer.cc)
starts resonance decays isotropically before applying the relevant angular
weight. Therefore route A is not a proof of production-aware Z polarization in
ZH. Route B keeps the MG5 production/decay correlations and avoids that extra
assumption. Future LHE and shower ancestry checks must confirm the actual Zbb
chain; parser success alone cannot do so.

## Exact mass, SLHA and decay settings

The unchanged Phase6B baseline has SHA256
`53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389`.
The new overlay `simulation/zh_pilot/cards/preferred_higgs_decay.cmnd` is applied
after that baseline and contains:

```text
SLHA:readFrom = 0
23:m0 = 91.188
25:m0 = 125.0
25:onMode = off
25:onIfMatch = 22 22
```

There is no Z forcing in preferred route B. The no-event comparison for route A
additionally tested `23:onMode = off` and `23:onIfMatch = 5 -5` through actual
Pythia `readString` calls.

The explicit SM-only `SLHA:readFrom=0` policy prevents future external SLHA
masses/decays from replacing the separately audited Pythia model. In the pinned
[SLHA interface](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/src/SLHAinterface.cc),
readFrom0 returns without importing a table. Default keep-SM behavior includes a
mass threshold and is insufficient to establish that a 125GeV Higgs width will
remain untouched. The source MG5 parameters are nevertheless retained verbatim:
ΓZ=2.441404GeV and ΓH=0.00638233934GeV. ΓZ governs the source Zbb propagator and
window; stable external H has no source H-decay normalization. These are fixed
restricted-model inputs, not adopted physical decay widths. Matching MH/MZ does
not make the distinct MG5/Pythia electroweak conventions identical.

## Physically executed no-event table probe

`check_decay_tables.py` compiled `inspect_decay_tables.cxx` against the existing
verified Pythia8.317 library and ran it. Its three initialized cases are inclusive,
forced A, and preferred B. Each uses `ProcessLevel:all=off`, `PartonLevel:all=off`
and `HadronLevel:all=off`; the probe never calls `next()` and has zero accepted
events. The preferred case reads the exact overlay file. Pythia initialization
recalculates model resonance widths even with the process level disabled.

The public `simulation/zh_pilot/evidence/decay_tables.json` is the exact final
actual receipt, SHA256
`b5185671b8f552477d1a46e350492d0eff3cf625733de3215ae29700eee3749b`.
It binds the probe/checker, overlay, historical baseline, installed library/XML,
compiler/binary and versioned primary-source hashes. Installation identities and
the input files were verified before and after execution.

| Initialized Pythia model at target masses | Total width, GeV | Target partial width, GeV | Inclusive model BR |
| --- | --- | --- | --- |
| Z→bb | 2.5042006900866638 | 0.38145723530671699 | 0.1523269428112472 |
| H→γγ | 0.0040834219879883659 | 9.3777064667590622e-6 | 0.0022965313147512443 |

These are exact printed binary64 model values, not physical precision estimates.
The Z mass prints as `91.188000000000002`, the binary64 representation of the
specified 91.188 input. Original XML tables, configured pre-init tables and all
post-init channels are retained. Before-init partial widths are `null` because
no initialized partial-width calculation is claimed.

Forcing leaves the initialized inclusive widths and BRs unchanged and enables
exactly the intended channels. In B the entire Z table remains equal to the
inclusive case. The single enabled H channel is drawn with conditional
probability one; its stored inclusive BR remains about0.00230. A forced selection
probability is not a physical branching fraction and supplies no normalization
closure. The
[ResonanceWidths implementation](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/src/ResonanceWidths.cc)
retains total/partial widths and separate open-channel fractions; its Higgs model
contains the γγ loop calculation. This does not insert a tree HAA vertex into
the ordinary MG5 SM model.

Intermediate probe attempts remain local: one compile API error, an ASLR-address
comparison failure, and a decimal-vs-binary64 mass comparison failure were
corrected without relaxing any physics-event validation. The final probe is the
accepted table-compatibility receipt; none of these attempts generated events.

## External references and physical adoption gate

The [CERN YR4 SM Higgs table](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR)
at MH125.00GeV lists BR(H→γγ)=0.002270 and ΓH=0.004088GeV. Their rounded central
product is9.27976e-6GeV; this is a derived comparison, not a separate calculation.
The table's uncertainty components are not adopted or combined here. The
[PDG2025 Z listing](https://pdg.lbl.gov/2025/listings/rpp2025-list-z-boson.pdf)
lists ΓZ=2.4955±0.0023GeV and the direct bb fraction0.1512±0.0005. Their rounded
central product is0.3773196GeV; its covariance/uncertainty is not inferred. The
direct fraction is different from Rb normalized to hadronic Z decays.

All these reference numbers are comparison-only. The config explicitly records
`physical_adopted_BR`, `physical_adopted_total_width_gev` and
`physical_adopted_partial_width_gev` as `UNKNOWN`. It does not combine a PDG Z
factor with the already exclusive MG source, or silently replace the Pythia model
by the YR4 Higgs BR. A future pilot must first adopt and document a consistent
width/BR/electroweak convention and then measure the actual external-LHE weight
behavior. No cross section has been integrated in this phase.

## Future acceptance sequence

After separate user authorization, retain the actual generator cards, full
original source count, strategy/init and signed weights; inspect the status2 Z
and its b/bbar daughters plus status1 H. Save inclusive and forced tables after
initialization with that exact external LHE. Record each original source ID,
H/Z copy chain, photon/bottom birth ancestry and actual Info/HepMC weight vector.
Ambiguous, cyclic, dangling or inconsistent ancestry must fail; converted/lost
final photons must not remove a source event from the denominator.

Independent HepMC readback must establish units, graph integrity, energy/mass
closure and H/Z ancestry. Detector-stage acceptance additionally requires actual
native ROOT readback; native BTag outcomes are retained, not redrawn. Closure of
raw signed LHE weights, Info weights, converter weights and the exactly-once BR
ledger must precede any exclusive rate interpretation. The current no-event
probe and synthetic algebra tests cannot satisfy those gates.

Portable contract tests physically passed24/24 on Windows and WSL. They reject
nonfinite BRs, fabricated model numbers, stale hashes, incorrect decay IDs,
duplicate factors and physical requests. These are method checks only.

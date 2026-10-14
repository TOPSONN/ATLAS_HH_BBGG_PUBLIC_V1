# Phase6F branching-ratio normalization contract

The planning contract preserves signed nominal event weights and prohibits any
physical BR correction until an actual external-LHE decay/weight closure is
measured. Current status is `METHOD_ONLY`, physical decay `NOT_EXECUTED`, closure
`UNKNOWN`, and zero new physics events. The contract is
`simulation/zh_pilot/config/decay_contract.json`; portable validation reads hashes
and tables only and never runs the native probe or a generator.

## Source scope and exactly-once IDs

Canonical IDs are `Z_to_b_bbar` and `H_to_gamma_gamma`. Source-included decays,
additional factors observed in the nominal Pythia weight, and separately applied
factors are distinct, unique, non-overlapping ledgers. The additional-nominal
ledger is relative to the original source nominal weight; it does not list the Z
factor already present in a Zbb source a second time.

| Source route | Source-included ID | Prospective additional missing ID | Current measured nominal inclusion |
| --- | --- | --- | --- |
| A stable Z/H | None | Z and H | UNKNOWN |
| B Zbb/stable H, preferred | Z | H | UNKNOWN |

Route B's source result is the exclusive resonant Zbb/H chain with its frozen
MG5 width and Breit–Wigner window. A second Z BR is forbidden. The exact source
decay-chain result is not reconstructed by multiplying an unrelated inclusive
ZH cross section. H remains undecayed at the source. The config's planning list
of missing decays is not a measurement of what Pythia may put in its nominal
weight; `missing_external_decay_ids=UNKNOWN_UNTIL_MEASURED_CLOSURE` remains explicit.

## Weight columns, denominator and units

| Column | Meaning |
| --- | --- |
| `LHE_XWGTUP_pb` | Original signed dimensional LHE weight for supported abs(IDWTUP)=4 |
| `input_contribution_pb` | Original LHE weight divided once by the full original source count |
| `Pythia_Info_weight_pb` | Actual nominal `Info::weight()` in the supported dimensional strategy |
| `converter_weight_0_pb` | Actual named HepMC converter nominal entry, required to match Info; all additional vector entries retain their actual `converter_weight_<i>_pb` names for i≥1 |
| `physical_BR_factor` | Separate, dimensionless, measured missing-factor result; absent until closure |
| `exclusive_contribution_pb` | Actual Info nominal divided by original count and multiplied only by measured missing BRs; absent until closure |

The denominator includes failed or filtered original events. Prefix counts,
accepted shower counts and detector selections never replace it. This phase
prepares a100-source-event pilot but has no such physical source. No cross section
or yield can be obtained from the planning record.

Pinned Pythia8.317 source establishes the following supported-strategy path:

1. [PhaseSpaceLHA](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/src/PhaseSpace.cc)
   converts absstrategy4 LHA weights from pb to mb with1e-9 when forming sigmaNow.
2. [ProcessContainer](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/src/ProcessContainer.cc)
   selects that dimensional nominal path and passes it to Info. Accumulated
   cross-section statistics have their own LHA-weight handling.
3. [Info::setWeight](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/include/Pythia8/Info.h)
   stores absstrategy4 nominal weights in pb. The
   [Info::weight implementation](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/src/Info.cc)
   returns that nominal with any configured shower/fragmentation variation factor.
4. The [HepMC3 exporter](https://gitlab.com/Pythia8/releases/-/blob/83a5c9986f30746cfb390435a9b10ac55a758fca/include/Pythia8Plugins/HepMC3.h)
   copies `weightValueByIndex` into the event weight vector. It separately converts
   `sigmaGen`/`sigmaErr` from mb to pb with1e9 for the cross-section attribute.

Therefore a second1e9 event-weight conversion is forbidden. Multiplying an
already dimensional XWGTUP by σ/N again is also forbidden. An unsupported input
strategy needs a separate audited convention rather than silently using these
column names. Future closure must inspect the actual init strategy and complete
weight vector, rather than assuming a strategy from a filename.

Source review of the external PhaseSpaceLHA/SigmaLHA path does not show the
generic internal-process resonance-open-fraction multiplier being inserted into
that nominal expression. Generic resonance calculations nevertheless keep open
fractions and conditional decay selection. This suggests a possible raw-nominal
behavior, but does not prove the behavior of the complete future LHE run with
forced decays, vetoes, retries, settings and export. The measured inclusion ledger
remains `UNKNOWN`; it cannot be filled from this source inference alone.

## Model values do not supply physical closure

The actual no-event initialized Pythia model has BR(H→γγ)
`0.0022965313147512443`, partial width`9.3777064667590622e-06`GeV, and total
width`0.0040834219879883659`GeV. Those dependencies are preserved in the public
receipt and checked against the contract. Forced H sampling has conditional
probability1 while retaining the inclusive model BR. Both are different from an
adopted physical branching fraction.

The [YR4 reference](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR)
at MH125.00GeV gives Hγγ BR0.002270 and total width0.004088GeV. They are
comparison-only and do not authorize replacing the model value in an event
weight. The source MG H width0.00638233934GeV is a separate restricted-model input.
The new SM-only overlay explicitly disables SLHA table import; source inputs and
the initialized Pythia widths are not conflated. For route B the initialized
Pythia Z model table is diagnostic only, and no reference Z BR is applied.

## Synthetic algebra and future physical proof

`synthetic_missing_br_factor` accepts only `SYNTHETIC_METHOD_ONLY` fixtures with
finite decimal-string BRs. For toy BRZ0.15 and BRH0.002:

| Synthetic ledger | Missing factor |
| --- | --- |
| Stable source, no factors embedded/applied | 0.15×0.002=0.00030 |
| Source includes Z, Info includes no additional factor | 0.002 |
| Source includes Z, measured additional Info ledger includes H | 1 |

These cases test double-counting algebra and are not observations of Pythia.
Duplicate/overlapping IDs, nonfinite numbers and physical fixture labels fail.
If actual Info already contains H's factor, applying it again would be wrong;
if actual Info preserves the raw source nominal, a separately adopted H factor
would be required for an exclusive rate. This distinction must be measured and
hash-bound before either interpretation is enabled.

The future receipt must bind source process/run/param cards, full LHE/init hash,
original count, settings and initialized tables, adopted BR source/scheme and
uncertainty convention, per-event source identity, signed raw/Info/converter
weights, and exact factor ledgers. Expected identities must close numerically
with stated tolerances and retain unsuccessful original events. Independent
HepMC and native ROOT checks are separate physical gates. No such receipt is
present in this readiness phase; a portable synthetic `METHOD_ONLY` result
cannot be promoted to physical acceptance.

Actual checks completed: no-event probe with exact overlay and zero `next()`
calls;24 portable decay-contract tests passed on each Windows and WSL host. No
new LHE, HepMC or ROOT sample was generated.

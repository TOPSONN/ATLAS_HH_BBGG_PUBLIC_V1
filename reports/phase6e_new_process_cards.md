# Phase6E new process-card preparation

**PASS_PARSE_ONLY. No new physical production.** The existing verified MG5
3.5.16 installation physically parsed all three candidate cards and constructed
their tree diagrams. It also parsed two separate tree decay-chain checks and
rejected ordinary-SM H→γγ with the expected `NoDiagramException`. No `output`,
`launch`, integration, event generation, model merge, install or width
calculation was executed. The installed retained source identity was verified
before and after parsing. The actual sanitized receipt is
[process_parse.json](../simulation/heavy_flavour_forensics/evidence/process_parse.json).

| Candidate card | Exact production definition | Retained amplitude orders | MG5 internal amplitude records |
|---|---|---|---:|
| [bbγj](../simulation/mg5/cards/bb_gamma_j_candidate.mg5) | `p p > b b~ a j4 QCD=3 QED=1` | QCD3, QED1 | 14 |
| [ttH](../simulation/mg5/cards/tth_candidate.mg5) | `p p > t t~ h QCD=2 QED=1` | QCD2, QED1 | 6 |
| [ZH](../simulation/mg5/cards/zh_candidate.mg5) | `p p > z h QCD=0 QED=2` | QCD0, QED2 | 5 |

All use `sm-no_b_mass` and the explicit five-flavour proton
`g u c d s b u~ c~ d~ s~ b~`. `j4` contains g/u/d/s/c and antiquarks, with no
additional bottom. It is not the preceding light-only `jl` definition.
In MG5, the displayed `QCD=n`/`QED=n` syntax is an amplitude-order upper bound;
the actual retained diagram orders were independently enumerated using the
official `Diagram.calculate_orders` API. The table gives those actual orders,
not an assumption that the syntax means equality. Internal amplitude records
need not list every beam mirror separately and are not event counts or
integration channels with measured rates.

The bbγj tree component has one Born photon. Proposed future finite cuts are
archived in [process_candidates_v1.json](../simulation/heavy_flavour_forensics/config/process_candidates_v1.json):
ordinary/bottom partons pT20 GeV, photon pT25 GeV, |eta(j,b)|5, |eta(γ)|2.5,
and jet/jet, b/b, b/jet and photon/parton separation0.4. These are unexecuted
proposal values; the matching policy, integration stability and fragmentation
treatment have not been validated. Fixed angular separation alone does not
establish an all-order photon-fragmentation prescription or a calibrated
detector isolation/fake model. A jet does not become a second detector photon
merely because it appears in the process name.

The ttH card keeps t/tbar/H undecayed at the matrix-element stage. The separate
parse check `t→bW+→be+νe`, `tbar→bbar W−→bbar j4 j4` is one charge assignment,
not inclusive top decays, the two-charge semileptonic union, or an H→γγ sample.
The no-b-mass restriction also sets charm/bottom Yukawa inputs to zero and
uses its recorded diagonal-CKM convention. Its hadronic W chain therefore
does not establish a complete physical W branching table. Production-only
ttH needs its own scale/PDF/param-card review; the preceding continuum's fixed
scale125 GeV is not silently adopted as a validated ttH choice.

The ZH card keeps Z/H undecayed. A separate `z > b b~` chain parsed while H
remained stable. This is the tree qqbar Higgsstrahlung component, including
allowed bottom PDFs; it omits loop-induced ggZH, higher-order QCD and EW.
It is not an inclusive precision ZH calculation. ZH with H→γγ is a resonant
single-Higgs background to HH, with bb from Z; it is neither continuum bbγγ
nor a new HH signal.

MG5's decay-chain prescription retains resonant diagrams and spin correlations
within its finite-width/narrow-width approximation. Successful parsing does
not measure widths, BRs, interference, cut acceptance or a decay-normalized
cross section. [Official MG5 decay-chain description](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/FAQ-General-6)
The separate [Higgs contract](phase6e_higgs_decay_contract.md) records the
missing HAA/forced-decay normalization gates. All new physical cross sections,
adopted BRs, shower/detector validation and fake transfers remain UNKNOWN or
NOT_EXECUTED in [process_readiness.json](../metadata/phase6e_process_readiness.json).

The parse-only command was physically executed:

```bash
python3 -B simulation/heavy_flavour_forensics/scripts/parse_process_cards.py \
  --output "$HOME/simulations/heavy_flavour_forensics/process_parse_01"
```

Use a fresh output directory. The public helper permits only the exact reviewed
import/define/generate sequence, including in its worker entry point. It
disables model-cache writes and automatic conversion/update, verifies source
identity, records actual coupling orders, and detects changed cards/config
during execution. Local logs retain diagnostics; only the sanitized receipt
is public. The existing self-service generator's validated profiles are
unchanged and reject these candidates.

The [Traditional Chinese guide](../simulation/heavy_flavour_forensics/USER_GUIDE_ZH_TW.md)
provides executable future100-event production-only commands, clearly gated
on separate explicit pilot authorization. A future bounded pilot must archive all
cards/seeds/weights, inspect actual widths and decay ancestry, and implement
an appropriate new LHE validation profile before a physical PASS can be claimed.

The requested resource assessment is **INCONCLUSIVE_100_EVENT_RESOURCE_ESTIMATE**
for each of bbγj, ttH and ZH. Process-specific wall time, peak RAM and disk for
100 new events remain UNKNOWN: no such physical run has been authorized or
executed. Retained measurements establish local reference scales only:

| Existing 1000-event process | MG5 recorded seconds | Pythia full CLI seconds / complete directory bytes | Delphes process seconds / ROOT bytes / sampled process VmHWM bytes |
|---|---:|---|---|
| bbγγ | 32.246294 (generator phase sum) | 14.212731 / 250644633 | 2.316689 / 28747494 / 383037440 |
| ccγγ | 13.649301 (full CLI) | 16.988926 / 273911296 | 2.714099 / 30570772 / 407277568 |
| light-jjγγ | 28.844856 (full CLI) | 15.947292 / 275587484 | 2.613713 / 30235463 / 403091456 |

Sources are the preserved [MG5 manifest](../metadata/phase6a_background_1k_manifest.json),
[Pythia resource receipt](../simulation/pythia8/evidence/resources.json) and
[Delphes native-run receipt](../simulation/delphes/evidence/native_runs.json).
The scopes differ: the Delphes column excludes input/ROOT analysis and its
sampled `/proc` child VmHWM is not a guaranteed whole-job peak; Pythia directory
sizes include full diagnostics. MG5 integration/compilation overhead and
different decay multiplicities prevent dividing these values by ten to predict
the new 100-event jobs. They supply neither a new-process runtime promise nor
a calibrated upper bound. The guide's one-job 2-hour timeout is an
administrative stopping ceiling, not a measured resource estimate. Before a
separately authorized pilot, approve its CPU/RAM/disk budget and monitor actual
usage; retain failed/partial files locally. Replace INCONCLUSIVE only with
process-specific measurements and applicable physics validation.

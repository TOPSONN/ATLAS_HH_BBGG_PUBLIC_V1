# Phase6F ZH generator contract

Status: **PASS_PARSE_AND_CARD_READBACK_ONLY**. The verified MadGraph5_aMC@NLO 3.5.16 installation physically parsed both candidate cards, constructed their tree diagrams in memory, and read the frozen run and parameter cards. No process was exported; no integration, width calculation, launch, or event generation occurred. The future 100-event pilot remains **NOT_AUTHORIZED / NOT_EXECUTED_BY_DESIGN**. Its cross section and physical decay/weight closure remain **UNKNOWN_NOT_INTEGRATED / NOT_EVALUATED**.

The machine contract is [generator_contract.json](../simulation/zh_pilot/config/generator_contract.json). The actual text receipt is [generator_checks.json](../simulation/zh_pilot/evidence/generator_checks.json); it binds the contract, checker, four cards, relevant installed source files, actual diagram records, and the complete official `RunCardLO` readback. Its before/after checks found unchanged retained MG5 source hashes and model-cache contents. `madgraph.ReadWrite=False`, disabled automatic model conversion, and Python `-B` prevent installation model-cache/conversion/bytecode writes. MG5's parser may write its own parser table into the new local scratch directory.

The source is the retained release packaged from official tag `v3.5.16`, commit `3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`. Existing MG5, Pythia, HepMC, Delphes, ROOT, historical cards, and reference samples were reused or read without modification.

The frozen process commands are:

```text
import model sm-no_b_mass
define p = g u c d s b u~ c~ d~ s~ b~
generate p p > z h QCD=0 QED=2
```

and the preferred future alternative:

```text
import model sm-no_b_mass
define p = g u c d s b u~ c~ d~ s~ b~
generate p p > z h QCD=0 QED=2, z > b b~
```

The actual parser returned five production amplitude records for each card: `u u~`, `c c~`, `d d~`, `s s~`, and `b b~` into stable `Z H`, with one diagram in each record. Every retained production diagram has amplitude coupling orders `QCD=0,QED=2`. MG5 interprets the written `QED=2` as an upper bound; inspecting the retained diagrams establishes their actual order. There is no gluon initial state, loop-induced `gg→ZH`, higher-order QCD component, or ordinary-SM tree `H→γγ` in this definition. Amplitude vertex order QED=2 corresponds to an electroweak Born rate of order αEW²; it is not a claim that an integrated cross section has been measured.

For `ZH_ZBB_STABLE_H`, the parser also constructed one `Z→b b~` diagram of amplitude orders `QCD=0,QED=1`. The factorized production-plus-decay amplitude thus has QED=3. Production QED=2 and decay QED=1 are checked separately. This route keeps the MG5 production/decay matrix-element correlation and is preferred over a stable-Z external-LHE decay lacking a production-aware Z polarization weight in Pythia's generic LHA process. The [decay plan](phase6f_higgs_decay_validation_plan.md) records that primary-source assessment and the remaining physical gates.

The exact input scheme and choices are:

| Item | Frozen value | Meaning and limit |
|---|---|---|
| Collision energy | 13,000 GeV; two 6,500 GeV proton beams | Future pilot target |
| Proton flavours | g,u,d,s,c,b and antiquarks | Five-flavour initial PDF scheme |
| Restricted masses/Yukawas | MC=MB=0; charm/bottom Yukawas zero | Actual c/b mass symbols are `ZERO`; restricted Yukawa parameters are removed, so missing independent YUKAWA entries are expected |
| MZ, MH | 91.188, 125 GeV | Exact hard-production mass inputs |
| ΓZ, ΓH | 2.441404, 0.00638233934 GeV | Fixed restricted-model inputs; not a newly calculated physical BR table |
| Electroweak inputs | αEW⁻¹=132.507; GF=1.16639×10⁻⁵ GeV⁻²; MZ | The model derives MW=80.41900244575616 GeV and sin²θW=0.22224648578577766 |
| PDF | Built-in CTEQ6L1, PDF ID 10042 | Retained LO table has order1 and five flavours; no additional PDF install |
| Scales | Fixed μR=μF1=μF2=MZ+MH=216.188 GeV | Explicit associated-production threshold-scale convention, not a tuned scale or precision prediction |
| Matching / systematics | ickkw=0; use_syst=false | No merging or uncertainty ensemble is executed |
| Output normalization template | event_norm=average; LHE3 | Future actual weights, header convention and full source denominator must still be checked |
| Template count / seed | 100 / 620101 | The prepared CLI records a requested seed override separately; this is not a generated sample |

The restricted SM input scheme derives MW using
`sqrt(MZ²/2 + sqrt(MZ⁴/4 − αEW·π·MZ²/(GF·sqrt(2))))`, with αEW=1/αEW⁻¹. The full parameter card was serialized using the actual `ParamCardWriter`. The default writer prints ΓH as `6.382339e-3`; the frozen card explicitly restores the retained restriction's full `6.38233934e-3`. The dependent MW value in the serialized interface card is printed as 80.419 GeV; MG5's actual parameter reader derives the more precise MW shown above.

CTEQ6L1's upstream implementation has two distinct αs conventions worth preserving exactly: `common_run_interface.py` updates a dependent parameter card to αs(MZ)=0.129783, while Fortran `pdfwrap.f` sets runtime `asmz=0.130` and one-loop running. The frozen SMINPUTS3 uses 0.129783 and the contract records both source values. The original restricted-model value is 0.118. The requested ZH Born diagrams have QCD=0, so their hard matrix element contains no αs coupling. This preparation does not establish a precision PDF choice, PDF uncertainty, scale uncertainty, or a shower-weight closure. `lhaid=10042` documents the same PDF identity but is inactive for a built-in `pdlabel`; no LHAPDF lookup is invoked.

The fixed scale is tied to the ZH mass threshold instead of the continuum baseline's 125 GeV. Both fixed-scale flags are true; the stored `dynamical_scale_choice=-1` is inactive. Original `RunCardLO` defaults are explicitly separated in the contract: dynamic flags false, scale and factorization values 91.188 GeV, PDF `nn23lo1`, and 10,000 events/automatic seed. No study comparing scale prescriptions was performed.

Generation acceptance minima are zero and upper bounds are disabled (`-1`), with no custom cuts, photon acceptance, analysis mbb/mγγ window, jet-merging scale, or collective HT/sorted-pT restriction. Stable external Z/H are on shell. In the decay-chain candidate, `cut_decays=false` suppresses ordinary acceptance cuts on the Z daughters; the full official readback also shows collective/sorted cuts disabled because `cut_decays` does not suppress all such cuts. `bwcutoff=15` defines the MG resonance treatment around MZ using its fixed ΓZ, corresponding to 54.56694–127.80906 GeV. This wide finite-width resonance window is part of the generated decay-chain definition and is not the downstream analysis mbb selection. It does not justify exact narrow-width factorization, especially with finite-width effects or subsequent cuts. The source implements a small-width safeguard of 10⁻⁶, which is negligible compared with the frozen ΓZ/MZ.

For preferred route B, any future integrated source cross section already contains the MG `Z_to_b_bbar` decay chain under these widths and resonance restrictions. The separately required decay ID is only `H_to_gamma_gamma`; a second Z branching factor would double count the source decay. MG's fixed Higgs width is a hard-card input for an external stable H. It must not overwrite the independently reviewed Pythia H decay table or be substituted for its initialized width or physical BR. Future execution must preserve raw source weights and separately verify the exactly-once BR ledger and pb/mb conversions. All current normalization statements are planning contracts, not measurements of a physical rate.

The four exact card SHA-256 values are:

| Card | SHA-256 |
|---|---|
| `zh_stable.mg5` | `f124bd3050aa44466019ad0110836af5c9a113d5dadd9de39d715ff52b43826a` |
| `zh_zbb_stable_h.mg5` | `411bcfdc0320d9f969b53ef4a723e98ccb26710800687ea0049cc09e32ebc2ad` |
| `run_card.dat` | `cbb6072adc7a708fd0b9d2a216cd421aa715244b367da27d9aaa8de668218e73` |
| `param_card.dat` | `17ad8b7b95f1918b30771c3403c0e2961fa018ab3db97b10f7dc02ec992074d6` |

The checker pins these reviewed digests literally in addition to comparing the manifest. Editing a card and updating its manifest digest does not authorize a new physics configuration. The independent user command can repeat this no-event check from the repository root in WSL using the retained installation:

```bash
python3 -B simulation/zh_pilot/scripts/check_generator.py \
  --output "$HOME/simulations/zh_pilot_checks/check_001"
python3 -B -m unittest discover -s simulation/zh_pilot/tests \
  -p test_generator_contract.py -v
```

The output directory must be new. The actual final check was physically executed in ignored `.local/phase6f/generator-check-final`; the public receipt is a byte-preserving copy of its text-only `generator_checks.json`. Both Windows and WSL executed all 14 generator-contract tests successfully with no skips. These tests cover reviewed hashes, edited/rehash-smuggled commands, source/order/flavour/PDF/scale changes, duplicate BR scope, forged physical authority, duplicate/nonfinite card values, and the actual installed parse receipt. They validate software and card preparation. A physical 100-event ZH, shower, HepMC, or detector sample has not been created.

Primary-source facts above were checked against the installed files at the pinned commit, whose hashes are in the receipt: [restricted SM inputs](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/models/sm/restrict_no_b_mass.dat), [EW parameter definitions](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/models/sm/parameters.py), [run-card API](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/madgraph/various/banner.py), [CTEQ6L1 table](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/Template/LO/lib/Pdfdata/cteq6l1.tbl), [runtime PDF wrapper](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/Template/LO/Source/PDF/pdfwrap.f), [dependent-card αs update](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/madgraph/interface/common_run_interface.py), [decay cuts](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/Template/LO/SubProcesses/setcuts.f), and [Breit–Wigner treatment](https://github.com/mg5amcnlo/mg5amcnlo/blob/3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7/Template/LO/SubProcesses/myamp.f).

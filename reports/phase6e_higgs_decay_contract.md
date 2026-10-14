# Phase6E Higgs diphoton decay and normalization contract

**SOURCE/MATHEMATICAL CONTRACT ONLY. PHYSICAL H→γγ VALIDATION BLOCKED.**
All canonical ttH/ZH production cards retain a stable Higgs in MG5. The
installed `sm-no_b_mass` has no HAA tree vertex; the actual `h > a a` parse
failed with the expected absence of diagrams. The installed `hgg_plugin`
contains an effective HAA vertex (HIW1) and separate Hgg vertices (HIG), but is
not a standalone full SM. No effective-model import/merge, width calculation,
forced decay or new Higgs event has been executed. Versioned source hashes
are bound in [higgs_source_review.json](../simulation/heavy_flavour_forensics/evidence/higgs_source_review.json).

H→γγ receives loop contributions, including top and W. An effective local
vertex is an approximation to that amplitude, not a tree SM decay or a
precision branching-ratio recommendation.
[Official MG5 effective-Higgs model](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/Models/HiggsEffective)

| Contract item | A: stable-H SM production plus Pythia decay | B: effective HAA decay-chain model |
|---|---|---|
| Production generator | Current `sm-no_b_mass`, stable H | Requires a separately audited full-SM/effective-model combination |
| H partial width to γγ | UNKNOWN; must extract/validate effective Pythia resonance calculation | UNKNOWN; must calculate with recorded effective coupling/parameters |
| H total width | UNKNOWN as adopted physical input | UNKNOWN as adopted physical input; must be consistent with all modeled channels |
| Physical BR | Γγγ/Γtotal, versioned source/uncertainty convention required | Γγγ/Γtotal from the adopted consistent model, or explicitly separate recommendation |
| Forced versus inclusive | Proposal `25:onMode=off`, `25:onIfMatch=22 22`; not executed | Exclusive γγ chain includes its decay amplitudes; not executed |
| Source cross section | Undecayed production σ and original LHE strategy/weights | Actual exclusive-chain σ, with widths/cuts/decay factors already present |
| Additional BR handling | Apply only missing factors after verified external-LHE closure | Never multiply already-included decay factors again |
| Physical status | NOT_EXECUTED, separate pilot required | NOT_IMPLEMENTED, model coordination and separate pilot required |

The source restriction supplies default total-width *inputs*, in GeV:
H `0.00638233934`, Z `2.441404`, W `2.047600`, top `1.491500`.
These are archived model-file defaults, not new calculated widths, validated
Higgs BRs, adopted official values or an endorsement of their precision.
No partial Γγγ or physical BR value is inferred from them. A future choice
must bind masses, couplings, model/recommendation version and width convention.
The [LHCHWG versioned XS/BR tables](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/HiggsXSBR)
are a possible source for later adopted inputs; no number is imported here.

Pythia8.317's official ParticleData/ResonanceDecays source supports channel
switches and dynamic resonance widths; allowed decay-channel sampling is
renormalized. Its general internal-process description also accounts for
resonance restrictions in process cross sections. That statement is not proof
that a custom external-LHE/IDWTUP=-4 input has acquired exactly the intended
physical BR in every exported nominal weight. The verified existing continuum
weight closure contains no forced Higgs decay, so it cannot close this new case.
The public manual endpoint returned403; the pinned official local XML/C++
source was read, hashed and recorded.
[Official Pythia8.317 source archive](https://pythia.org/releases/pythia83/pythia8317.tgz)

A future physical test must compare original production/decay scope and LHE
init σ/XWGTUP, Pythia effective decay tables/widths, raw `Info::weight`, converter
weight vector, selected-event counts and the recorded exactly-once BR ledger.
It must retain pb/mb conversion and the complete original input denominator,
including failed/filtered events. A forced sampling table with a normalized
γγ channel does not by itself supply an adopted physical BR. No extra σ/N,
luminosity, or acceptance factor may be silently added. A parsed decay command
or an algebra test does not satisfy this closure.

For production-only ttH and separately forced chosen decay modes, the NWA
bookkeeping is `σ(ttH) BR(H→γγ) BR(t→bW)^2 F_W`.
For disjoint W modes with leptonic family-set L: fully hadronic
`F_W=BRhad²`, one fixed charge assignment `F_W=BRL BRhad`, union of both
assignments `F_W=2 BRL BRhad`, dileptonic `F_W=BRL²`. Define whether L includes
tau and its decays. Require BRL+BRhad≤1 and a complete compatible CKM/W table;
the factor2 is already included if the source cross section sums both charges.
An exclusive matrix-element chain must instead declare which decay factors
its actual source cross section already includes, with no duplicate BR.

For production-only qqbar ZH with separately forced decays the intended
exclusive scope is `σ(qqbar ZH) BR(Z→bb) BR(H→γγ)`, once each. The parsed
Z→bb chain would already include that Z-decay factor after actual integration;
one must inspect its real source σ before adopting that interpretation.
Finite-width cuts, spin correlations, off-shell effects and neglected
nonresonant/interference contributions prevent an assumed exact factorization.
[MG5 resonant decay-chain scope](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/FAQ-General-6)

The pure numerical [higgs_contract.py](../simulation/heavy_flavour_forensics/scripts/higgs_contract.py)
uses explicit Decimal BR factors and decay IDs. It rejects UNKNOWN/nonfinite
BRs, invalid multiplicities, repeated factors, source-included/already-applied
IDs, inconsistent exclusive W-mode sums and non-Boolean verification flags.
External forcing remains blocked without an explicit closure gate. Synthetic
BR fixtures test this algebra only; a Boolean supplied by a test is not a
physical evidence receipt. Actual adopted BR/width inputs remain UNKNOWN.

# Phase6D new-background feasibility and physics scope

**FEASIBILITY_ONLY. No new background event was generated, showered or passed
through Delphes in this review.** Existing MG5/Pythia/Delphes installations,
cards and reference bytes are read-only. The proposed channels are not enabled
profiles of the validated generation pipeline. Their cross sections, decay
branching ratios, efficiencies and photon-fake transfers remain unvalidated.

| Candidate | Role in an HH→bbγγ study | Current feasibility | Required interpretation gate |
|---|---|---|---|
| bbγj | One hard photon plus jets; reducible two-photon background only after a separately established fake/nonprompt-photon mechanism | Tree-level hard production proposal; no calibrated fake model | Photon identification/isolation transfer, flavour/kinematic dependence, overlap partition and closure |
| ttH, H→γγ | Resonant single-Higgs background; top decays supply b jets and other objects | Stable-H tree production proposal; diphoton decay/model normalization not validated | H loop-decay treatment, top/W decay channels, spin/width checks and exactly-once BR accounting |
| ZH, Z→bb, H→γγ | Resonant single-Higgs background with bb from Z; distinct from HH and continuum bbγγ | qqbar-initiated tree production proposal; diphoton decay/model normalization not validated | H/Z widths and BRs, production components, resonance provenance and exactly-once normalization |

The ATLAS 13 TeV HH→bbγγ analysis distinguishes continuum backgrounds from
single-Higgs processes and estimates photon-misidentification components from
data. Its fitted yields, calibrations and background fractions cannot be
transferred to this simplified card and selection.
[ATLAS primary paper, Sections 3–5](https://arxiv.org/pdf/2112.11876)

## bbγj: production is not a fake-photon calibration

A minimal future hard-process proposal is:

```text
# FEASIBILITY_ONLY — not parsed, generated, integrated or executed in Phase6D
import model sm-no_b_mass
define p = g u c d s b u~ c~ d~ s~ b~
define j4 = g u c d s u~ c~ d~ s~
generate p p > b b~ a j4 QCD=3 QED=1
```

This intentionally defines the additional ordinary jet to include massless
charm and exclude additional bottom. It is a limited component, not all bbγ+jets;
an alternative light-only jet definition must explicitly exclude charm as well.
The five-flavour proton includes bottom PDFs. A LO PDF/source identity, beam
energy, αs convention, scales, seeds and cuts must be chosen and archived for
the new sample. The old continuum cards are not changed or silently reused.
With massless quarks, soft/collinear jet and photon regions require documented
generation cuts and an isolation/fragmentation treatment; a finite cut-dependent
LO result is not an inclusive background prediction. The displayed coupling
orders select a proposed dominant QCD+QED component; actual subprocess/diagram
and integration checks have not been performed.

The inspected Delphes 3.5.1 `SimpleCalorimeter` creates an ECAL photon-like
energy-flow candidate from significant neutral tower excess and assigns PID 22.
The subsequent PhotonEfficiency/isolation modules do not supply a validated
ATLAS jet→photon misidentification probability. A shower hadron-decay photon,
prompt shower photon, ECAL candidate and detector identification fake are
different definitions. Current b-tag conditional probabilities cannot be
repurposed as photon-fake probabilities.
[Pinned Delphes source](https://github.com/delphes/delphes/blob/3.5.1/modules/SimpleCalorimeter.cc)

Before a reducible-background yield is interpreted, define the photon ID and
isolation target, fake denominator and pass/fail transfer; obtain applicable
calibration or data control regions with uncertainties and closure. Include
dependence on pT, eta, jet flavour/composition, detector response and pileup as
applicable. A jet promoted to a photon changes the reconstructed object list,
isolation, overlap handling and possibly the selected bb pair; multiplying a
raw rate by an invented constant does not establish this response. No numerical
fake probability or transfer factor is introduced here.

An overlap policy must partition prompt two-photon matrix elements, a second
QED-shower photon, fragmentation/nonprompt photons and fake candidates. Adding
bbγj events with shower photons to existing bbγγ yields without ME/PS and truth
partition checks can double count physical regions. Independent source-event
IDs alone do not resolve that process overlap. Extrapolation from a fake control
region to the HH-like selection needs an independent closure test; a small
pilot or a zero observed passage is insufficient.

## ttH: choose the decay definition before counting events

The conservative production-only candidate retains a stable Higgs/top pair at
the matrix-element stage:

```text
# FEASIBILITY_ONLY — stable-H production; this does NOT generate H→γγ events
import model sm-no_b_mass
define p = g u c d s b u~ c~ d~ s~ b~
generate p p > t t~ h QCD=2 QED=1
```

The proposed tree component requires independent scale/PDF/width and diagram
review. It is not NLO ttH, and no higher-order K factor or official production
normalization is supplied. Top decays must be explicit, with invariant-mass,
mother/daughter, spin/angular and weight checks in the resulting LHE/shower
records. A hadronic-top sample cannot be labelled inclusive ttH simply because
both contain two b quarks.

For production-only normalization and separately forced decays, the desired
narrow-width bookkeeping for a chosen channel D is
`σ(ttH) × BR(H→γγ) × BR(t→bW)^2 × F_W(D)`.
For fully hadronic W decays, `F_W=BR(W→qq')^2`; for one specified leptonic
family-set L and one hadronic W, the union of both charges has
`F_W=2 BR(W→Lν) BR(W→qq')`; for both W decays in L,
`F_W=BR(W→Lν)^2`. L must state whether tau is included and how tau decays are
handled. The factor2 applies to the union of two charge assignments; it must
not be applied again if the generated exclusive channels already include both.
An inclusive top/W mixture instead requires the validated complete branching
table and all accepted decay modes. CKM assumptions and omitted W modes must
match the model and BR convention.

If a decay-chain matrix element already has a decay-normalized cross section,
do not multiply the same BR factors again. A finite-width chain may also have
cuts and off-shell effects, so its cross section is not assumed to equal a
production rate times nominal BRs. MG5 decay-chain syntax selects resonant
diagrams in a narrow-width approximation; the approximation and treatment of
nonresonant/interference terms must be documented and tested.
[MG5 decay-chain documentation](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/FAQ-General-6)

## H→γγ is a model and normalization gate

Read-only inspection of the installed MG5 v3.5.16 source found no HAA tree
vertex in `models/sm/vertices.py`; a `sm-no_b_mass` restriction cannot create
that missing vertex. Therefore appending `h > a a` to an ordinary SM tree card
is not a validated solution. The same installed source contains
`models/hgg_plugin/vertices.py`, with an effective HAA vertex (HIW order) and
Hgg vertices (HIG order). This is an extension, not a standalone full SM.
Source presence is not an executed model import, merge or decay calculation.

Two future paths require separate validation:

- Retain SM tree production with a stable H, then use a verified Pythia Higgs
  decay configuration. A proposed forcing choice is `25:onMode=off` followed by
  `25:onIfMatch=22 22`. Archive the pre-forcing widths/BRs and effective decay
  table; measure exactly what the external-LHE weight/cross-section contract
  includes. The ParticleData decay switches are real, but do not by themselves
  establish whether a physical BR is already accounted for.
- Merge a reviewed effective HAA extension in an isolated future model copy,
  record all merged source hashes and coupling-order restrictions, and test
  production amplitudes, H→γγ partial width and total width. Avoid introducing
  unwanted Hgg production contributions into the intended ttH/ZH component.
  A dedicated loop-capable treatment is another research option; its runtime,
  decays and integration compatibility are untested here.

The official MG5 effective-Higgs documentation identifies H→γγ as loop-induced
and describes the effective approximation. A model approximation is not a
precision branching-ratio calculation.
[MG5 effective-Higgs model](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/Models/HiggsEffective)
The pinned local Pythia 8.317 `ParticleDataScheme.xml`/`ResonanceDecays.xml` were
inspected for channel switches and resonance-width semantics; those files are
bound in the source evidence. The public manual endpoint was inaccessible in
this review; the verified versioned source is the primary local proof.
[Official 8.317 source archive](https://pythia.org/releases/pythia83/pythia8317.tgz)

Physical Higgs BR values must come from a versioned applicable recommendation
or independently validated model calculation with the chosen Higgs mass,
parameters, widths and uncertainty convention. They remain UNKNOWN as adopted
inputs here. Use the LHC Higgs Working Group's versioned tables as a future
source, rather than inserting an uncited number or treating a default generator
decay table as an official recommendation.
[LHCHWG XS/BR recommendations](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/HiggsXSBR)

## ZH: one resonant Higgs, not a continuum or HH signal sample

A production-only proposal is:

```text
# FEASIBILITY_ONLY — qqbar Born ZH; Z/H decay definitions remain unvalidated
import model sm-no_b_mass
define p = g u c d s b u~ c~ d~ s~ b~
generate p p > z h QCD=0 QED=2
```

For separately forced Z/H decays, the intended exclusive normalization is
`σ(qqbar→ZH) × BR(Z→bb) × BR(H→γγ)`, counted once. A Z→bb decay-chain proposal
is `generate p p > z h QCD=0 QED=2, z > b b~`; it still leaves H stable and is
unexecuted. A fully decayed effective-model chain would additionally require
the preceding HAA gate. On-shell and off-shell Z definitions, widths, b-mass
scheme, accepted cuts and interference treatment must be fixed before testing.
The tree proposal omits loop-induced gg→ZH and higher-order QCD/EW corrections;
it must not inherit an inclusive precision ZH cross section without accounting
for those components.

H→γγ produces a Higgs resonance, while the bb pair here originates from Z.
That is a single-Higgs SM background in an HH study, not nonresonant bbγγ and
not a newly generated HH signal. Its selected acceptance depends on additional
objects, overlap and any bb mass window; no mass window is optimized on current
small samples. All cross sections/BRs for the proposed new processes remain
UNKNOWN; no prospective event count is a physical yield prediction.

The source review is documented in
[new_background_source_review.json](../simulation/rare_backgrounds/evidence/new_background_source_review.json).
Generation/decay/normalization gates require actual execution in a later
authorized phase. The Phase6D numerical tools analyze existing events under an
explicit conditional tagging model; their analytic expectations do not create
new independent hard events or replace missing fake/decay calibration.
The existing LHE/shower provenance profiles are built for the current hard
diphoton samples. One-hard-photon or stable-H inputs need new process/decay
validation and prompt-photon ancestry definitions; Higgs-decay photons are not
the same provenance category as two Born LHE photons. The old gates must not be
disabled to accept these unvalidated profiles. All original incoming events,
including later selection failures, belong in any future normalization
denominator; no passing-row renormalization is proposed.

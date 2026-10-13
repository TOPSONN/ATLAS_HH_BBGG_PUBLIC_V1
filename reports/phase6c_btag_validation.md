# Phase6C b-tagging model and validation

**Source semantics and actual native model/denominator validation PASS.**
The working point is `UPSTREAM_ATLAS_CARD_BIT0_STUDY`, using the unchanged
Delphes 3.5.1 ATLAS-card probability functions. It is not a calibrated ATLAS
efficiency, modern 70%/77% working point, or continuous DL1/GN2 discriminator.

With pT inGeV, the exact functions are:

| Actual associated flavour | Tagging probability |
|---|---|
|5(b) | `0.80*tanh(0.003*pt)*(30/(1+0.086*pt))` |
|4(c) | `0.20*tanh(0.02*pt)*(1/(1+0.0034*pt))` |
| Default/light | `0.002+7.3e-06*pt` |

JetFlavorAssociation selects reader partons with pT>1 GeV,|eta|<=2.5 and
status!=-1. The HepMC reader's parton input consists of nonstable quarks/gluons
(its tau entries are rejected by this classifier). Within DeltaR<=0.4 the
highest absolute quark code 1..5 wins; gluons have lowest priority and map to21.
No match yields0. These are all eligible record partons, including showers,
rather than a unique original-hard-parton or hadron-origin assignment.

The BTagging module evaluates the probability associated with Jet.Flavor and
ORs the sampled Bernoulli result into bit 0. Select `(Jet.BTag & 1)!=0`.
BTagAlgo and BTagPhys are populated with separate random draws using different
flavour definitions; they are not alternate names for the same tag. The HepMC3
input does not supply a native original LHEF particle collection, so their
interpretation must not be inferred as validated hard-physics flavour.

The validation denominator is all eligible reconstructed Jet with pT>25 GeV and
|eta|<2.5, before photon/event-level cuts. Classify by actual Flavor 5/4 and
explicit light set0/1/2/3/21; preserve other flavours as UNKNOWN. Process labels
bbgg/ccgg/jjgg are not flavour labels for every reconstructed jet. Report
eligible counts, tagged counts, observed fractions, mean predicted probability
and descriptive Wilson 95% intervals separately. Zero/low counts require an
insufficient-statistics qualification; no observed zero is a precise zero rate.
Per-jet intervals do not replace an event-level correlation/systematics study.

The per-jet expected count is the sum of the card probabilities over the actual
eligible reconstructed kinematics. Because tags are already sampled by Delphes,
do not multiply event weights by the tagging probability again. Preserve the
original source-normalized generator contribution and event identity separately.

Hard b/c/light partons and heavy hadrons provide separate truth diagnostics.
Unique geometric matching for those studies does not change this non-unique
upstream tagging cone, and a hadron may not be counted twice as independent
hard statistics. Flavour ambiguity, shower production and unavailable ancestry
remain explicit limits.

Card hashes and pinned module identities are in
[card_source_review.json](../simulation/delphes/evidence/card_source_review.json).
The inspected official
[JetFlavorAssociation](https://github.com/delphes/delphes/blob/3.5.1/modules/JetFlavorAssociation.cc)
and [BTagging](https://github.com/delphes/delphes/blob/3.5.1/modules/BTagging.cc)
source defines the semantics. The frozen configuration physically completed
Stage C 1000 events for each process, with all native readback counters complete
and no invalid/skipped events. The following measurements use only Stage C;
the Stage A/B prefixes are not added to their hard statistics.

## Actual Stage C raw per-jet measurements

The required primary aggregate is
[phase6c_efficiencies.csv](../metadata/phase6c_efficiencies.csv), produced from
the native Stage C CSV files. This table rounds percentages for readability;
the exact counts/probabilities/intervals and file hashes are retained in
[btag_binned_statistics.json](../simulation/delphes/evidence/btag_binned_statistics.json).

| Process | Actual flavour | Eligible jets | Bit0 tags | Expected tags from card | Observed % [Wilson95 %] | Statistical scope |
|---|---|---:|---:|---:|---|---|
| bbgg | b | 1373 | 894 | 920.3798 | 65.11 [62.55,67.59] | Descriptive counts sufficient |
| bbgg | c | 38 | 4 | 4.5681 | 10.53 [4.17,24.13] | INSUFFICIENT_STATISTICS |
| bbgg | light | 686 | 1 | 1.6393 | 0.1458 [0.0257,0.8210] | INSUFFICIENT_STATISTICS |
| ccgg | b | 15 | 11 | 9.5564 | 73.33 [48.05,89.10] | INSUFFICIENT_STATISTICS |
| ccgg | c | 1514 | 189 | 188.4517 | 12.48 [10.91,14.24] | Descriptive counts sufficient |
| ccgg | light | 793 | 0 | 1.8894 | 0 [0,0.4821] | INSUFFICIENT_STATISTICS |
| jjgg | b | 21 | 16 | 14.0249 | 76.19 [54.91,89.37] | INSUFFICIENT_STATISTICS |
| jjgg | c | 67 | 7 | 8.4448 | 10.45 [5.15,20.03] | Descriptive counts sufficient |
| jjgg | light | 2130 | 10 | 5.3686 | 0.4695 [0.2552,0.8621] | Descriptive counts sufficient |

UNKNOWN has zero eligible entries in each process; its fraction and interval
are null, not measured zero. Heavy-flavour jets in the ccgg/jjgg samples are
consistent with the explicit shower-inclusive parton-cone definition; the
process name does not determine every reconstructed jet's category. The zero
ccgg light-tag observation has a positive upper interval and does not establish
a zero mistag rate. A bin flagged sufficient only meets the predefined count
criterion; it does not establish a precise calibrated performance measurement.
The jjgg light sample has10 tags versus5.3686 expected, with conditional-model
standardized residual +2.00148. This mild deviation above two Gaussian standard
deviations is a finite-sample statistical fluctuation diagnostic, not proof of
a calibrated model or a definitive systematic bias. Multiple inspected flavour
categories/bins and event correlations are not accounted for in that residual;
larger independent samples and systematics would be needed for a performance
conclusion.

## Fixed pT/eta numerical diagnostics

Before computing these binned summaries, diagnostic edges were fixed to pT
`[25,50,100,200,+infinity]` GeV and absolute eta `[0,0.8,1.6,2.5]`.
These are study choices, not ATLAS calibration bins. Strict eligible selection
is applied first; bin lower edges are inclusive and upper edges exclusive.
The pT and eta distributions are separate one-dimensional summaries, not a
joint calibration. All flavour categories and empty bins remain present.
The JSON uses a null final pT upper edge to represent infinity, never NaN.
No binning, working point or mass window was optimized on these samples;
this statement does not claim the preceding aggregate observations were blinded.

The independently executed
[summarize_btags.py](../simulation/delphes/scripts/summarize_btags.py) streamed
the actual native reco records, recomputed eligibility and bit0 counts, applied
the exact card functions, and matched every aggregate count, predicted sum,
statistical flag and Wilson interval to the native CSV. Its final execution
reproduced the public JSON bytes exactly. It binds native/reco/CSV/ROOT hashes
and original source identities; it does not execute a fresh native ROOT
readback. Each bin records raw denominator/tags, expected count, mean probability,
fraction, Wilson interval and explicit insufficient-statistics flag. The policy
flags n<30, expected tags<5, expected untagged<5 or UNKNOWN. Conditional
Bernoulli-model residuals are descriptive; event correlations, systematic
uncertainties and an independent calibration sample are absent.

The [guide](../simulation/delphes/USER_GUIDE_ZH_TW.md) gives the actual executable
summary command. No figure, optimized working point or HH sensitivity estimate
was produced. Scientific acceptance is limited to the explicit tagging model,
native source/kinematic checks and these bounded small-sample diagnostics.

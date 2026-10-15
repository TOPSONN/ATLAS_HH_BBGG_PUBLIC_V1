# Phase7B/C/D ggF HH signal campaign

The executable campaign uses the pinned finite-mass `loop_sm` implementation,
MG5 3.5.16, Pythia 8.317, HepMC3 3.3.1, Delphes 3.5.1 and ROOT 6.40.04/C++20.
Read [the Traditional Chinese operating guide](USER_GUIDE_CAMPAIGN_ZH_TW.md)
for the actual commands, quota, output locations and resume rules.

The original `README.md` and `USER_GUIDE_ZH_TW.md` document the preserved
Phase7A zero-event readiness snapshot. The campaign implementation and its
actual B100/C1000/D receipts are separate additions. Current scientific gate
states are in `metadata/phase7_quality_gates.json` at the repository root.

There are exactly 1100 new independent hard events: B100 and C1000.
Downstream prefixes and the six reweights of C1000 add no independent data.
The selected genuine references include both original production LHE and
physical mixed-decay representations, plus 100-entry HepMC/ROOT references.
The full C1000 shower and detector output stays local.

All reported decay-weighted yields use `MODEL_BR_ONLY`. Absolute normalization
is inconclusive because the two independent source integration estimates have
unresolved tension. Six backgrounds remain separate; their overlap, fake,
spin and detector-calibration limitations prohibit a combined physical yield.
No PNG/PDF figures are generated or published by this campaign.

# ZH resonant-background pilot readiness

Phase6F prepares a reproducible future100-event,13TeV tree qqbar-initiated ZH
pilot using the retained MG5 3.5.16, Pythia8 8.317, HepMC3 3.3.1, Delphes3.5.1
and ROOT6.40.04/C++20 installations. **Physical production is NOT_AUTHORIZED.**
No integration, new hard events, Pythia `next()` or detector execution is enabled.

The preferred proposal retains MG5's Z→bb production-decay chain with stableH;
the alternative stableZ/H external-LHE route has an explicit Z-spin limitation.
Actual source/model/diagram and no-event table probes are distinct from a
physical decay/weight closure receipt. Forced probability1 is not a physicalBR.
The source-included Z decay cannot be multiplied again in an exclusive-rate
ledger. Original signed source weights and full denominators remain separate
from any future exactly-once physicalBR contribution.

Run the documented local text-only dry-run in
[USER_GUIDE_ZH_TW.md](USER_GUIDE_ZH_TW.md). It checks pinned identities,
hash-bound cards/configuration and available resources, freezes local copies
and declares every missing physical gate. A non-dry request always fails before
any generator call. CPU worker policy is1; process-specific runtime/RAM/storage
costs are UNKNOWN. Time/disk limits are administrative budgets, not benchmarks.

Independent profiles ZH_STABLE, ZH_ZBB_STABLE_H and ZH_BBGG_FORCED_DECAYS
prepare topology, ancestry, mass, weights and BR-ledger checks without changing
historical validators. Synthetic methods/fixtures never confer physicalPASS.
Future native reconstruction uses Higgs-origin photons, Z-origin bottom,
native jets and the unchanged FAST_SIM_ATLAS_LIKE bit0 card. mγγ/mbb/mbbγγ
analysis readiness is separated from detector execution on a real ZH sample.

Read [generator contract](../../reports/phase6f_zh_generator_contract.md),
[decay plan](../../reports/phase6f_higgs_decay_validation_plan.md),
[BR normalization](../../reports/phase6f_br_normalization_contract.md),
[overlap](../../reports/phase6f_background_overlap.md),
[pilot readiness](../../reports/phase6f_physical_pilot_readiness.md) and
[decision](../../reports/phase6f_decision.md).

Publication contains new source/cards/config/tests and bounded text evidence.
The payload auditor rejects figures, event files, binaries, archives, vendor
code and historical modifications; audit staged files and every outgoing
commit before each push. No new reference sample, figure, installation,
stitching weight, HH physics result, official ATLAS detector claim or PR merge.

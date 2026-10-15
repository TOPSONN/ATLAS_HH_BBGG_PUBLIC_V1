# Three bounded LO background chains

This independent Phase6G module reuses the retained MG5 3.5.16, Pythia8 8.317,
HepMC3 3.3.1, Delphes 3.5.1 and ROOT 6.40.04/C++20 installations. It starts
from Phase6F commit `05cff9a5d991ba6782b339bc41932ae4da296d8c` and preserves
the earlier source, reference samples, reports and guarded Phase6F command.

Use [the Traditional Chinese operating guide](USER_GUIDE_ZH_TW.md) for the
executable local command and output locations. New personal samples stay
local. Each fresh command supports one reviewed 1000-event source at 13TeV,
one worker, and stopping budgets of at most four hours and 10GiB.

| Alias | Source component | Fixed scale | Downstream decay scope |
| --- | --- | --- | --- |
| `zh` | LO five-flavour qqbar ZH with source Z→bb, stable H | 216.188GeV | Pythia H→γγ; source Z factor already included |
| `tth` | LO QCD ttH, stable top/antitop/H | 235.5GeV | Inclusive supported Pythia top/W channels and H→γγ; production-decay spin correlations unvalidated |
| `bbgj` | Five-flavour bbγj4 with one Born photon and finite generation cuts | 125GeV | ISR/FSR, hadronization and applicable decays; photon origins kept separate |

The complete original source is independently validated before downstream
processing. Shower validation uses original prefixes10/100 and full1000;
Delphes prefixes10/100 come from the actual validated full1000 shower. These
subsets do not add independent hard-process statistics. A physical failure
stops dependent work and retains its counters and artifacts.

Raw signed source contributions use `XWGTUP/full_original_count`. Actual
LHE/Info/converter closure and initialized decay tables are required before
the separate `MODEL_BR_ONLY` H factor can be applied once. The Phase6F model
and YR4 comparison values remain separate references. There is no extra Z
factor, HH factor of two, or implicit luminosity.

The detector scope is `FAST_SIM_ATLAS_LIKE`, with the historical bit0 model
and Phase6C selections. B06 photon-fake calibration, inter-process overlap
and official detector/BR calibration remain independently blocked. These
components are not a complete physical background prediction.

Actual counts, numerical evidence and final gates are recorded in
[the final decision](../../reports/phase6g_final_decision.md) and
[the machine-readable manifest](../../metadata/phase6g_run_manifest.json).
Source preparation or method checks do not establish physical completion.

The publication helper selects genuine bounded references only after local
full1000 LHE/HepMC/ROOT QA. The portable Git/CI checker rechecks exact bytes,
CRC, records and preserved native QA receipts; it does not rerun native
simulation. Unapproved figures, vendor trees, build outputs and personal
paths are excluded from staged and every outgoing commit payload.

# Phase6G source preparation decision

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1

TASK: PHASE6G_ZH_100_EVENT_PHYSICAL_PILOT_V1

AUTHORIZATION_STATUS: NOT_AUTHORIZED

The independent stack starts at Phase6F PR16, exact head
05cff9a5d991ba6782b339bc41932ae4da296d8c. The retained command now has an explicit
one-use human gate, one campaign attempt, bounded supervision and frozen cards.
The execution bridge is reviewable; compatibility with a real ZH100 run remains
unmeasured. See [execution assessment](phase6g_execution_bridge.md),
[weight/BR contract](phase6g_br_weight_closure.md) and
[Traditional Chinese commands](../simulation/zh_pilot/phase6g/USER_GUIDE_ZH_TW.md).

| Required physical result | Current evidence |
|---|---|
| MG5_EVENTS_REQUESTED |100; future source request only|
| MG5_EVENTS_GENERATED |0|
| MG5_CROSS_SECTION_PB |NOT_EVALUATED|
| MG5_INTEGRATION_UNCERTAINTY |NOT_EVALUATED|
| PYTHIA_DECAY_EVENTS |0|
| HEPMC3_VALIDATED_EVENTS |0 physical events|
| DELPHES_ROOT_ENTRIES |0 new ZH entries|
| Z_BB_ANCESTRY |NOT_EVALUATED|
| H_GAMMAGAMMA_ANCESTRY |NOT_EVALUATED|
| INPUT_WEIGHT_CONVENTION |Frozen signed XWGTUP_pb/full original100; actual ZH values NOT_EVALUATED|
| PYTHIA_INFO_WEIGHT |NOT_EVALUATED|
| HEPMC_CONVERTER_WEIGHT |NOT_EVALUATED|
| HIGGS_BR_ADOPTION |NONE; not authorized by the100-run token|
| BR_CLOSURE_STATUS |Physical closure BLOCKED; measured transfer NOT_EVALUATED|
| PHOTON_RECO |NOT_EVALUATED|
| JET_RECO |NOT_EVALUATED|
| BTAG_MODEL |Retained Delphes bit0, FAST_SIM_ATLAS_LIKE; not official ATLAS calibration|
| ZH_CUTFLOW |NOT_EVALUATED; zero future survivors cannot establish zero background|
| TOTAL_RUNTIME |Pilot NOT_EVALUATED; compilation/test times are separate|
| PEAK_MEMORY |Pilot UNKNOWN; resource supervision is sampled|
| DISK_USAGE |Pilot NOT_EVALUATED; administrative ceiling5GiB|
| GITHUB_SAMPLES |NONE; physical references withheld until actual authorization/validation|

LOCAL_TESTS: exact executed host counts, method/log/source SHAs and real guarded
CLI dry-run are recorded in
[source_checks.json](../simulation/zh_pilot/phase6g/evidence/source_checks.json).
Native21 Pythia/HepMC3 method checks and3 ROOT numerical checks passed with0
physical events/next calls. A real historical ROOT count-mismatch probe retained
1000 observed entries and0 event reads; it is not a new ZH test.

EXISTING_REGRESSION: all16 suites PASS,42 older C++ tests, actual readonly
3x1000 original ROOT verification,452 unchanged baseline blobs and only the
required wrapper extension. Installed sources/libraries and original inputs
were preserved. The two corrected method-harness setup failures and original
failure logs are explicitly recorded in
[regressions_and_preservation.json](../simulation/zh_pilot/phase6g/evidence/regressions_and_preservation.json).

GITHUB_CI: source-only workflow and inherited readiness checks must be verified
on the exact published head; their final receipt is separate from physical
gateL. Hosted CI never installs or invokes physical production.

GATES_PASS: A(history/input preservation), B(frozen configuration/source methods).

GATES_FAIL: NONE currently evaluated.

GATES_BLOCKED: C=NOT_AUTHORIZED; D-L=NOT_EVALUATED. Physical BR adoption remains
separately blocked. Source GitHub publication does not promote physical gateL.

COMMIT_HASH: exact final Draft PR head and handoff report are authoritative.

PR_URL: the separate stacked Phase6G Draft PR is attached at publication.

FINAL_VERDICT: BLOCKED_PHYSICAL_AUTHORIZATION.

NEXT_RECOMMENDED_STEP: review the concrete source bridge, then the human may send
AUTHORIZE_PHASE6G_ZH_100_RUN to authorize exactly one source100 run within the
reviewed caps. No larger production or external physical BR adoption is implied.

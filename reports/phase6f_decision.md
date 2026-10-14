# Phase6F scoped readiness decision

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1

TASK: PHASE6F_ZH_RESONANT_BACKGROUND_PILOT_READINESS_V1

STATUS / FINAL_VERDICT:
**PASS_READINESS_METHODS_WITH_PHYSICAL_EXECUTION_NOT_AUTHORIZED.**

This task prepares and actually tests the bounded readiness methods. It does
not validate a physical ZH sample. No new physical event, detector run on ZH,
generator installation, figure, merge or force push occurs. All original inputs,
history, source997 and scientific results remain preserved.

| Required field | Decision |
|---|---|
|MG5_ZH_PROCESS|Actual parsing of stableZH and preferred Zbb/stableH passes; each has5 grouped Born amplitude records with1 diagram; preferred Zdecay has1 additional decay diagram|
|ZH_GENERATOR_MODEL|sm-no_b_mass, explicit5F proton; tree approximation with recorded b/c mass/Yukawa and diagonal CKM limits|
|ZH_PRODUCTION_ORDER|Production QCD0/QED2; Zdecay QCD0/QED1, factorized chain QED3. Loop-induced ggZH absent|
|ZH_PDF_AND_SCALES|Built-in CTEQ6L1, fixed μR=μF=MZ+MH=216.188GeV; one-loop PDF alpha_s0.130 and MG-dependent card0.129783 distinguished; no Born alpha_s coupling at QCD0|
|Z_DECAY_STRATEGY|Preferred MG Z→bb chain retains production/decay spin correlation within resonant finite-width/decay-chain approximation; external stableZ/Pythia route has a production-Z-spin limitation|
|HIGGS_DECAY_STRATEGY|Stable H followed by proposed forced Pythia H→gamma gamma; exact no-event tables/settings/source reviewed, actual decay ancestry unexecuted|
|HIGGS_GAMMAGAMMA_BR|Initialized Pythia model reference0.0022965313147512443; physical BR adoption remains UNKNOWN, not conditional forced probability1|
|Z_BB_BR|Initialized Pythia model reference0.1523269428112472; preferred MG Zbb source already includes Z decay, so no second ZBR|
|BR_WEIGHT_CONVENTION|Preserve original signed production weights/full source denominator; explicit separate exactly-once missing BR ledger requires actual LHE/Info/HepMC closure. No invented automatic factor|
|DOUBLE_COUNT_PREVENTION|Canonical Z_to_b_bbar/H_to_gamma_gamma IDs; reject overlapping included/additional/applied factors; SINGLE_HIGGS_ZH_BBGG kept distinct from continuum|
|PYTHIA_COMPATIBILITY|Pinned8.317 ABI/source and actual zero-event initialized decay tables pass; external ZH event/weight closure NOT_EXECUTED|
|HEPMC3_COMPATIBILITY|Pinned3.3.1 ABI/readback and existing31 CTests pass; future ZH named-weight/ancestry profile prepared, new physical export NOT_EXECUTED|
|DELPHES_INPUT_READINESS|Separate H-photon/Z-bottom method profile, native jets, original FAST_SIM_ATLAS_LIKE bit0 and mass definitions prepared; new native ZH execution NOT_EXECUTED|
|PHYSICAL_100_EVENT_PILOT|NOT_EXECUTED_BY_DESIGN; Gate L NOT_AUTHORIZED|
|PILOT_COMMAND|bash simulation/zh_pilot/scripts/generate_pilot.sh --process zh --events 100 --seed 20261104 --energy 13000 --output NEW_LOCAL_DIRECTORY --dry-run --max-hours 2 --max-disk-gb 5; real local example in guide|
|PILOT_RESOURCE_ESTIMATE|One-worker policy; projected runtime/RAM/storage UNKNOWN; measured availability and administrative budgets separated|
|NEW_TESTS|78 PASS on Windows and WSL, zero skips;2 actual final dry-run commands with distinct seeds and4 actual rejection commands; synthetic profiles remain METHOD_ONLY|
|EXISTING_REGRESSION|Phase6E56/Phase6D51/MG59/Pythia56/Delphes27portable+8native and42C++ checks PASS; original3×1000 ROOT inputs actual readback PASS|
|GITHUB_CI|Exact published head CI and remote byte/tree acceptance recorded after publication; portable CI does not execute native tools or a physical pilot|
|GATES_PASS|A historical/input preservation; B process; C generator assessment; D/E decay source/table assessment; F BR algebra; G retained interface/ABI assessment; H prepared profile methods; I overlap review; J tested dry-run/rejection methods; K executed regression methods|
|GATES_FAIL|NONE in the completed readiness-method scope|
|GATES_BLOCKED|Gate L NOT_AUTHORIZED; actual ZH integration/decay/weight closure and new detector execution; physical BR adoption and reviewed execution bridge|
|GATES_UNKNOWN|New physical σ, adopted physicalBR/width convention/finite-width acceptance, actual external weighting, ZH runtime/RAM/storage|
|COMMIT_HASH|Verified scientific source head recorded in publication snapshot; documentation seal final head independently reported in PR/final response|
|PR_URL|New stacked OPEN/DRAFT PR on codex/phase6e-heavy-flavor-forensics, basebe29be7255c5009c719190cb96f43f04bb144d8f; URL recorded after creation|
|NEXT_RECOMMENDED_STEP|Review/adopt the decay/BR/width/weight and execution-bridge contract, then obtain separate explicit100-event pilot authorization; no automatic larger production|

For readiness gates D/E/F/G/H, PASS means the stated source/probe/algebra/profile
assessment only; it is not physical event/decay/shower/detector acceptance.
Physical recommendations remain conditional where model and precision-input
conventions differ. A forced open channel and a Boolean unit fixture cannot
supply missing real-event receipts.

Evidence/operating entries:
[quality gates](../metadata/phase6f_quality_gates.json),
[pilot manifest](../metadata/phase6f_pilot_manifest.json),
[decay contract](../metadata/phase6f_decay_contract.json),
[generator](phase6f_zh_generator_contract.md),
[decay plan](phase6f_higgs_decay_validation_plan.md),
[BR](phase6f_br_normalization_contract.md),
[overlap](phase6f_background_overlap.md),
[readiness](phase6f_physical_pilot_readiness.md),
[Traditional Chinese guide](../simulation/zh_pilot/USER_GUIDE_ZH_TW.md).

No physical HH result or official ATLAS detector/efficiency claim is made.
Source997's FSR ancestry/concentration and original continuum predictions remain
unchanged. No fake/synthetic physics reference or unapproved PDF/PNG is published.

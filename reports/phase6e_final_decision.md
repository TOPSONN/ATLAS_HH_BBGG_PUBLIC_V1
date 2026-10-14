# Phase6E scoped scientific decision

**STATUS / FINAL_VERDICT:
PASS_EXISTING_FORENSICS_AND_BACKGROUND_PREPARATION_WITH_PHYSICAL_GATES_BLOCKED.**

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1

TASK: PHASE6E_HEAVY_FLAVOR_FORENSICS_AND_BACKGROUND_PREPARATION_V1

The source997 heavy-flavour origin is established from actual existing event
records. Original events, native labels/tag bits, cards, source weights, full
physical files and historical branches are preserved. New-process parsing and
normalization algebra pass their executed checks; they do not establish a new
H→γγ or photon-fake simulation. No physical pilot/large production was launched.

| Required field | Result |
|---|---|
|SOURCE997_IDENTITY|PASS: source SHA322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8; actual LHE/ledger/HepMC/ROOT/pilot agree|
|SOURCE997_LHE_INDEX|One-based997th event block; zero-based ROOTentry996, Event.Number997|
|SOURCE997_HARD_PARTONS|Incoming u(2),g(21); outgoing g(21),u(2), plus two photons; no hard b/c. Five-flavour proton definition does not imply this event has incoming bottom|
|SOURCE997_SHOWER_HEAVY_FLAVOUR|Actual Pythia hard g7(-23)→recoil g13(-44)→g17(-51)→b19(+5,-51)+bbar20(-5,-51); 571 unique Pythia/HepMC tuple matches,1149 reciprocal motheredges,zero mapped-edge differences|
|SOURCE997_B_HADRONS|Terminal anti-B0(-511), Pythia276, near nativejet0; B+(521), Pythia488, near nativejet4. Associated charm descendants recorded. Multi-mother string ancestry does not prove a sole b-line hadron parent|
|SOURCE997_RECO_JET_FLAVOURS|Unchanged native5,2,21,21,5; original bit0 tags1,0,0,0,0. Separate hard/shower/hadron diagnostic labels21,2,0,0,0 /5,2,21,21,5 /5,0,0,0,5|
|SOURCE997_TAG_PROBABILITIES|0.7319608791400521,0.0027465204605102538,0.0023768172760009767,0.0023580737106323243,0.6704831920949589; P(Ntags≥2)=0.4939102757862776. Persisted Float_t PT/card approximation retains Phase6D scope|
|SOURCE997_EVENT_CONTRIBUTION|98.52106957% of final jj expected count; native mgg135.55650162670545 GeV/mjj229.79333891363382 GeV; passes photon/jet cuts, actual Ntags1 so fails observed double-tag/final cuts. All10 potential leading pairs are probability weighted; observed mbb remains null|
|SOURCE997_ORIGIN_VERDICT|DIRECT_FSR_G_TO_B_BBAR_CONFIRMED, from actual graph/status/vertex cross-check, not native Flavor alone|
|JJGG_EXPECTED_FINAL_WITH_ALL_EVENTS|0.5013245166140850; source-weighted expected cross section0.004730776925334195 pb, with original1000 denominator|
|JJGG_LEAVE_ONE_OUT_DIAGNOSTIC|Other999 expected count0.007414240827807404; fixed-original-denominator weighted sum0.00006996489951051501 pb. DIAGNOSTIC_ONLY; no removal, corrected prediction or stitching weight|
|HEAVY_FLAVOUR_CONTRIBUTION|Final jj leading-pair bb97.16360211%,b-light1.67831597%; separate event-level probability with≥2 native-b tags97.89416844%. Native-associated labels are not universal hard/hadron truth or calibrated b-tagging|
|LIGHT_MISTAG_CONTRIBUTION|Final jj leading-pair light-light0.15342642%,c-light1.00465549%; bc/cc0 in this final pilot. Event-level zero-native-b category1.15741591% includes c/light and differs from leading light-light|
|SAMPLE_CONCENTRATION|Final jj top5=99.52308542%,top10=99.87429343%; contribution ratio1.030213949, pilot inverse squared relative-SE1.030245108. These are concentration/precision diagnostics, not new independent events; each source still has1000|
|BACKGROUND_OVERLAP_RISK|Born final-state definitions differ but 5F initial states and unmatched showers can populate shared reconstructed heavy-flavour topologies. No physical exclusivity, subtraction, stitching or official background sum is established|
|BBGJ_MODEL_STATUS|PASS_PARSE_ONLY:14 internal amplitude records,actualQCD3/QED1; physical σ/fake transfer/overlap closure UNKNOWN|
|TTH_MODEL_STATUS|PASS_PARSE_ONLY:6 internal amplitude records,actualQCD2/QED1,stableH/top canonical production; separate top/W tree parses. Inclusive/exclusive decay and BR/spin/width/weight closure still required|
|ZH_MODEL_STATUS|PASS_PARSE_ONLY:5 internal amplitude records,actualQCD0/QED2,qqbar tree stableZ/H canonical production; separate Z→bb tree parses. Missing ggZH and physical H decay/BR/width/weight closure prevent inclusive precision interpretation|
|HIGGS_DIPHOTON_DECAY_STATUS|Ordinary sm-no_b_mass tree h→aa correctly fails NoDiagram. Stable-H+forced Pythia and audited effective-HAA options are source-reviewed proposals, not physically executed or validated decays|
|BR_NORMALIZATION_STATUS|PASS_ALGEBRA_ONLY: exactly-once explicit decay ledger, multiplicity/charge-union checks and external-forcing closure gate; actual adopted widths/BRs remain UNKNOWN. Test Booleans/BR fixtures are not physical receipts|
|MG5_REGRESSION|59 existing tests/reference validation PASS; six actual guarded candidate/decay/model parse checks PASS; retained MG5 source identity unchanged|
|PYTHIA_REGRESSION|56 existing tests,5 C++/31 HepMC3 CTests and selected-reference validation PASS; original actual source997 graph unchanged|
|DELPHES_REGRESSION|27 portable tests PASS with8 explicit native skips, then8 actual native adversarial tests PASS; C++ analysis test and all3 full1000 native readbacks PASS|
|NEW_TESTS|56 PASS on Windows and WSL; source graph/identity/unique matching, all3000 event partitions/covariance,10 source997 pairs/masses, source cross-section preservation, coupling orders, Higgs exactly-once BR and publication guards. Nine additional corrupted-evidence controls rejected, separately counted|
|GITHUB_CI|Exact final head, Draft/base and remote bytes are checked after publication and recorded in the PR description/final response; portable CI does not execute native ROOT, MG5 parsing or physical production|
|GATES_PASS|Identity/actual readback, graph ancestry and mapping, native flavor semantics, unchanged weights/cuts, influence/covariance, overlap risk review, actual process parsing, BR algebra, independent/old regressions and preservation|
|GATES_FAIL|NONE within the completed existing-input/preparation scope|
|GATES_BLOCKED|Separate explicit100-event pilot authorization; physical Hγγ decay/weight closure; calibrated photon fake; matching/merging/overlap scheme; statistically stable rare acceptance|
|GATES_UNKNOWN|Original Pythia production coordinates/omitted HepMC positions; sole hadron-parent attribution through multi-mother string fragmentation; adopted physical new σ/widths/BRs/fake rate; new-process100-event runtime/RAM/disk|
|COMMIT_HASH|Source/evidence head is recorded at publication; documentation-only seal follows the verified source snapshot. Exact final head is reported in the PR/final response, avoiding a self-hash claim|
|PR_URL|New stacked OPEN/DRAFT PR on codex/phase6d-rare-backgrounds-statistics; URL recorded after creation in the final response|
|NEXT_RECOMMENDED_STEP|Choose a heavy-flavour/photon overlap and matching strategy, validate the selected Higgs decay/BR convention, then request a separately authorized100-event physical pilot. Do not automatically execute larger forecasts|

The original generator/shower/Delphes seeds are20261022/610203/610303, with
nominal generator weight9.4365561 pb and per-source contribution0.0094365561 pb.
Native b-flavour assignment is reproduced from the actual parton/cone semantics
with Float_t-axis uncertainty explicitly bounded. Alternative labels are
diagnostic; no working point or bit is changed. Geometric B-hadron evidence and
unique perturbative b/bbar production are distinguished from string-fragmentation
sole-parent attribution and missing production positions.

For each process the influence module retains all1000 events, including q=0
rows. It reports event contributions to expected counts/weighted yield, conditional
tag variance and source-pilot variance. Category covariance matrices preserve
negative off-diagonal conditional terms; summing category variances alone is
incorrect. Generation/shower/reconstruction source-pilot variability remains
combined because there is one realization per hard event. Original source
integration errors and physical model uncertainties are not silently included
in those conditional/pilot terms. A rare event is not removed to improve stability.

Source reports:
[source997](phase6e_source997_forensics.md),
[classification](phase6e_heavy_flavour_classification.md),
[overlap](phase6e_background_overlap.md),
[new cards](phase6e_new_process_cards.md),
[Higgs contract](phase6e_higgs_decay_contract.md).
Evidence:
[forensic manifest](../metadata/phase6e_source997_manifest.json),
[influence](../simulation/heavy_flavour_forensics/evidence/influence.json),
[independent tests](../simulation/heavy_flavour_forensics/evidence/independent_validation.json),
[executed numerical replay](../simulation/heavy_flavour_forensics/evidence/numerical_execution.json),
[regressions](../simulation/heavy_flavour_forensics/evidence/regressions.json)
and [quality gates](../metadata/phase6e_quality_gates.json).

No OFFICIAL_ATLAS_BACKGROUND, CALIBRATED_BTAGGING, PHYSICAL_PHOTON_FAKE_RATE
or HH_SIGNAL_SENSITIVITY claim is made. Full physical samples stay in their
original locations; only source/proposals/configuration/tests/small derived
evidence and reports are selected. No figures, vendored generators, automatic
merge, force push or new physical production is part of this task.

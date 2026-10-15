# Phase7A final decision

STATUS: source/model/method readiness complete within the authorized scope;
physical pilot remains blocked and unauthorized.
FINAL_VERDICT: PARTIAL_SIGNAL_MODEL_READINESS.

MG5_VERSION: 3.5.16.
LOOP_MODEL: loop_sm, finite top and bottom loop-induced LO.
LOOP_MODEL_SOURCE: official mg5amcnlo/mg5amcnlo v3.5.16,
commit3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7.
LOOP_MODEL_SHA256: 3772b2d0f75e092f82a4c556bf2288a43e239f2c7ee6cafaca22d6a11eb98065.
MODEL_COMPATIBILITY: actual native parsing, identical diagram lists and
sqrvirt standalone compilation/evaluation PASS; generic noborn standalone
export limitation documented; real integration workflow not evaluated.

PROCESS: gg→HH, future pp13TeV; PERTURBATIVE_ORDER: LO loop-induced only.
HIGGS_MASS:125GeV; TOP_MASS:173GeV; bottom mass/Yukawa4.7GeV.
PDF_SET: proposed CTEQ6L1 method baseline only, production review required.
MU_R:mHH/2 in actual ME; MU_F:mHH/2 proposed, no PDF convolution performed.
KAPPA_LAMBDA:1; KAPPA_TOP:1. Alpha_s=0.118 fixed for ME tests.
BOX_AMPLITUDE: six diagrams per top/bottom; nonzero squared components.
TRIANGLE_AMPLITUDE: two diagrams per top/bottom, attached HHH vertex verified.
INTERFERENCE_VALIDATION: four common fixed points, κλ−1/0/1/2 quadratic closure
and destructive interference PASS. FULL_TOP_MASS_DEPENDENCE: actual MT180
vs173 with fixed Yukawa/p4 changes ME. BOTTOM_LOOP_SCOPE: included finite MB;
light/charm Yukawas zero under native restriction. NUMERICAL_AMPLITUDE_TESTS:
21 configurations×6 deterministic evaluations, repeat/exchange/onshell/p4 PASS;
Ward and second amplitude provider NOT_EVALUATED. No integrated cross section.

DOUBLE_HIGGS_DECAY_ASSIGNMENT: PASS_METHOD_ONLY, unbiased independent-seed
50/50 assignment, exactly two original PDG25 lineage identifiers; native
per-lineage decayer BLOCKED. H_BB_DECAY_MODEL: proposed nonzero-bottom-Yukawa
Pythia8.317; H_GAMMAGAMMA_DECAY_MODEL: proposed Pythia8.317 initialized loop width.
BR_H_BB:null; BR_H_GAMMAGAMMA:null, not initialized/adopted for signal.
IDENTICAL_H_FACTOR:2 for missing mixed-decay probability, separate from
production symmetry divisor2. BR_DOUBLE_COUNT_PREVENTION: actual method tests
reject already-applied/in-source BR and missing factor2; no change to ZH/ttH.
SOURCE_WEIGHT_CONTRACT: signed certified pb weight/original N, missing BR once;
actual IDWTUP/XWGTUP/Info/converter/source N remain null until real closure.

FUTURE_PYTHIA_READINESS: profile/API prepared, native decayer BLOCKED.
FUTURE_HEPMC_READINESS: ReaderAscii API compiled; real signal NOT_EVALUATED.
FUTURE_DELPHES_READINESS: unchanged card SHA and ROOT6.40.04/C++20 Cartesian/null
methods compiled/executed; real signal detector chain NOT_EVALUATED.
SELF_SERVICE_DRY_RUN: actual documented shell command PASS,0events; non-dry
mode physically rejected with exit2 before output creation.
USER_GUIDE: [Traditional Chinese executable guide](../simulation/hh_signal/USER_GUIDE_ZH_TW.md).

PHYSICAL_SIGNAL_EVENTS:0_NOT_AUTHORIZED.
SIGNAL_CROSS_SECTION_PB:NOT_EVALUATED_UNTIL_REAL_INTEGRATION.
SMOKE_10_STATUS:NOT_AUTHORIZED.
PILOT_100_STATUS:NOT_AUTHORIZED.
REFERENCE_1000_STATUS:NOT_AUTHORIZED.

RESOURCE_PRECHECK: actual availability, safe fresh local output, existing tools
and source/card fingerprints verified. Numerical1worker/2h/5GiB enforcement;
final attempt 139.836 seconds, 116130647 bytes, sampled RSS 917192704 bytes.
Future4h/10GiB caps are requests, not measured production capacity or permission.
NEW_TESTS:42/42 PASS, no skips; actual native C++ interface methods PASS.
EXISTING_REGRESSION:469 discovered,461 PASS/8 explicit portable skips; reference
validators PASS; all six existing streams6000 source events and6000 actual ROOT
records rehashed/reread, exact reco/cutflow preservation. No new Delphes run.
GITHUB_CI:PENDING_PUBLICATION, NO_CHECKS is not PASS.

GATES_PASS:A–I,K–M within the explicit method/source/numerical scope.
GATES_FAIL:none for current final checks; prior attempt failures retained.
GATES_BLOCKED:J native mixed-decay bridge and physical-pilot prerequisites;
N pending publication; O NOT_AUTHORIZED.
GATES_UNKNOWN:P,Q real signal closure; Ward identity/independent amplitude
provider and future production performance NOT_EVALUATED.

COMMIT_HASH: resolve current stacked PR head; publication evidence is snapshotted
separately after remote readback. PULL_REQUEST_URL:PENDING_DRAFT_CREATION.
NEXT_RECOMMENDED_STEP: implement/validate native per-lineage decays, initialize
and adopt signal BRs, review production PDF/alpha_s and dynamic scale, then
request separate10-event authorization. Do not start a physical pilot now.

No signal LHE/HepMC/ROOT, unapproved PDF/PNG, vendor code, release or LFS payload.
No merge or force-push. Prior physics results, reports, references and PRs are
preserved. See the machine gates, model/loop/decay manifests and bounded evidence
under simulation/hh_signal/evidence for all qualifications.

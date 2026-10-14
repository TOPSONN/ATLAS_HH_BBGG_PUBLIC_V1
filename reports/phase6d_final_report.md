# Phase6D final scoped assessment

**FINAL_VERDICT: PASS_EXISTING_INPUT_ASSESSMENT_WITH_LIMITS.** The analytical
method, actual existing-input validation, bounded evidence and independent
regression are complete. A calibrated physical ATLAS background prediction
and new-process simulation are not established by this task.

| Required field | Result |
|---|---|
|ANALYTICAL_TAG_ESTIMATOR|PASS; event-level conditional independent Bernoulli, literal bit0 card functions, eligible native jets, direct saturated probability recurrence; full1000 denominator and original signed source weights|
|BBGG_EXPECTED_DOUBLE_TAGS|99.3063072879 after photon/jet selection|
|CCGG_EXPECTED_DOUBLE_TAGS|4.07895913435 after photon/jet selection|
|JJGG_EXPECTED_DOUBLE_TAGS|0.579371507280 after photon/jet selection|
|OBSERVED_VS_EXPECTED|91/7/0 versus99.3063/4.07896/0.579372; all inside conditional95 predictive bounds. After unchanged105–160 GeV mgg:28/1/0 versus30.2713/1.31214/0.501325|
|STATISTICAL_UNCERTAINTY|Final analytic acceptance source-pilot SE:0.00372865/0.000250047/0.000493911. This term includes generation+shower+reconstruction; one realization per source cannot separate them. Exact CP observed-count intervals and separate original MG5 integration errors retained|
|TAG_SAMPLING_VARIANCE|Two-tag count variances50.7094796/3.78099479/0.333201141; final mgg15.4660569/1.24796082/0.257369102. Weighted tag variance and shared-event nested-stage covariance are reported separately|
|TOY_SYSTEMATIC_SENSITIVITY|TOY_MODEL_SENSITIVITY_ONLY; fixed individual b/c/light and joint ±20% probability multipliers; no official ATLAS systematic label. Joint final expected counts19.5946–43.0937 /0.846269–1.87492 /0.321791–0.719788, illustrative variation only|
|RECOMMENDED_EVENTS_BBGG|1313 total future independent events for a conservative20% one-SD ordinary-count planning target using final observed CP95 lower acceptance endpoint;5044 for approximate95 half-width20%|
|RECOMMENDED_EVENTS_CCGG|987435 for the same conservative20% one-SD convention;3793190 for approximate95 half-width20%. These are qualified planning estimates; large production is not authorized|
|RECOMMENDED_EVENTS_JJGG|UNBOUNDED_INCONCLUSIVE using the zero observed-count lower bound. Model-assisted ordinary-count20% one-SD forecast49843 is fragile and is not a conservative recommendation|
|NEW_BACKGROUND_FEASIBILITY|FEASIBILITY_ONLY: bbγj requires calibrated photon-fake transfer/closure; ttH and ZH require validated H→γγ treatment, decays/widths/BR ledger and production components; all require overlap accounting. No new process was executed|
|REGRESSION_TESTS|51 new tests PASS/zero skips; all3000 identities/weights and27,000 scenario probabilities independently checked;216 pair-mass moments. Existing MG5 59/Pythia56/Delphes27 portable tests,8 native adversarial tests, ROOT/C++20 5/Pythia C++5/HepMC3 C++31/Delphes C++1 PASS. The initial portable Delphes discovery has8 explicit native skips, subsequently exercised in the separate native run|
|GITHUB_CI|Source/evidence snapshot10fd45321b0255ac2ecedcf9f086abb238322010: push38505845399 and pull_request38505920003 bothSUCCESS. Final publication-seal head is checked independently and reported in the PR/final response|
|GATES_PASS|Actual full1000 native ROOT/cards/weights/provenance, event estimator, unchanged selection/normalization, pair combinations, uncertainty/covariance, toy labeling, qualified intervals/planning, feasibility plan, independent regression and bounded publication|
|GATES_FAIL|NONE within the completed assessment|
|GATES_BLOCKED|Precise jj rare rate/finite conservative count; separately identifiable generation/shower/reco components; official detector/systematic calibration; new-process physical yield pending fake/decay/BR/overlap validation|
|COMMIT_HASH|Scientific source/evidence snapshot10fd45321b0255ac2ecedcf9f086abb238322010; the documentation-only publication seal follows this snapshot|
|PR_URL|[Draft PR14](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/14) — OPEN/DRAFT, stacked on codex/phase6c-delphes-fast-sim|
|NEXT_RECOMMENDED_STEP|Audit rare native-heavy-flavor configurations, especially source997, and validate the proposed decay/BR/fake/overlap models. Then scope an explicitly approved independent pilot/production plan; do not automatically run the forecast large samples|

Light-jj source997 accounts for98.5211% of the final expected yield. Zero
observed survivors out of1000 have a two-sided95 acceptance upper endpoint
0.00368208390 and one-sided95 upper limit0.00299124955. Neither the observed
zero nor the toy probability responses establish zero background, calibrated
rejection, or a reliable ordering of physical background rates.

The physical native readback and independent ROOT extraction were re-executed
after source-integrity hardening and each processed3000 existing entries.
All re-extracted public pilot bytes remained identical. The exact numerical
analysis SHA256 is
`23fa2f4a3669c2c8bf97d422e428abda90abd67c15872e0ae8830fd9ddc57b79`.
The three conditional summaries are reproduced exactly on Linux Python3.12;
cross-host libm rounding is separately bounded in the independent audit.

Evidence links: [assessment](phase6d_rare_background_assessment.md),
[statistics](phase6d_statistical_uncertainty.md),
[toy sensitivity](phase6d_toy_model_sensitivity.md),
[new-background plan](phase6d_new_background_feasibility.md),
[input/source guard execution](../simulation/rare_backgrounds/evidence/source_guard_execution.json),
[numerical execution](../simulation/rare_backgrounds/evidence/numerical_execution.json)
and [publication snapshot](../simulation/rare_backgrounds/evidence/publication_snapshot.json).
The snapshot verifies exact source-head remote bytes and CI; it is not a claim
that a later seal commit hashes itself. Final PR head/base/Draft status and CI
are read again after the final push. No PDF/PNG was generated, committed or
pushed; historical tracked paths, existing software and earlier PRs remain
unchanged. No merge, force push or large production occurred.

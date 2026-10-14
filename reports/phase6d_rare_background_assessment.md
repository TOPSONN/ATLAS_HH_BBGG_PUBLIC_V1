# Phase6D existing-input rare-background assessment

The analytical event-level method passes the executed existing-input and
numerical checks. It does not establish a calibrated ATLAS background model.
The three original full1000 ROOT files were read with the existing ROOT6.40.04,
C++20 and Delphes3.5.1 environment, and checked against their original cards,
source identities, weights, indexes, sidecars and full-file hashes. Original
files, installation bytes, selection code and historical references were not
rewritten. No new independent event, shower or detector run was produced.

Base: open Draft PR13, `codex/phase6c-delphes-fast-sim`, commit
`5e7a9522e08e50d99b1a166789500a4039c3e9b1`. This work adds an independent
stacked study. Publication and final-head CI receipts are separate from the
scientific input/numerical receipts below.

## What is estimated

For every reconstructed source event, retain the original photon selection
(pT>25 GeV, |eta|<2.37, open crack exclusion1.37<|eta|<1.52 and leading pT>35),
and jets with persisted pT>25 GeV and |eta|<2.5. Use the selected bit0 and actual
native Jet.Flavor. The literal pinned card probabilities are:

```
b:     0.80*tanh(0.003*pT)*30/(1+0.086*pT)
c:     0.20*tanh(0.02*pT)/(1+0.0034*pT)
light: 0.002+7.3e-6*pT
```

The Delphes module makes a separate Uniform comparison for each jet. Conditional
independent Bernoulli tags describe that intended stochastic study model on
fixed reconstruction, rather than measured physical independence or a replay
of deterministic tags at the fixed seed. BTagAlgo/Phys are separate draws and
are not substituted for bit0. The native flavor association can assign bottom
or charm in the nominal light-hard-process sample; no original-hard flavor or
specific shower-splitting ancestry is inferred from native Flavor alone.
[Pinned BTagging source](https://github.com/delphes/delphes/blob/3.5.1/modules/BTagging.cc)
and [flavor association](https://github.com/delphes/delphes/blob/3.5.1/modules/JetFlavorAssociation.cc).

A direct saturated 0/1/>=2 probability recurrence computes q=P(Ntags>=2),
without subtracting nearly equal numbers. The original module evaluated full
candidate pT before Float_t storage; this estimator uses persisted PT. A
Float32 enclosure, derivative bounds and Bernoulli coupling bound the possible
baseline expected-count change from probability rounding alone by
0.000228/0.00001594/0.000002995 before mgg and
0.00006555/0.000005017/0.000001487 afterward, for bb/cc/light-jj respectively.
These bounds hold at fixed persisted eligibility/flavor. Hidden original pT
and exact random draws are not recovered.

The final selection still adds the closed105–160 GeV diphoton window; no mbb
window is added. If jets a<b in pT order are the leading tagged pair, its chance
is p_a*p_b times the non-tag probabilities of all earlier jets before b except
a. Later jets are unrestricted. All such pair probabilities sum to q and
weight the mbb and mbbgg first/second moments. The observed pair is not reused
as a substitute for all possible tagged pairs. Cartesian masses preserve the
existing bounded signed native jet-mass convention.

## Counts and uncertainty

| Process | Full native cutflow | Expected two tags | Observed two tags | Expected final mgg | Observed final mgg |
|---|---|---:|---:|---:|---:|
| bbgg |1000→446→266→91→28|99.3063073|91|30.2713032|28|
| ccgg |1000→378→241→7→1|4.07895913|7|1.31214350|1|
| light-jjgg |1000→445→277→0→0|0.579371507|0|0.501324517|0|

The two-tag observed counts all lie within the fixed-pilot Poisson-binomial95
predictive bounds: bb[85,113], cc[1,8], light-jj[0,2]. Final-stage bounds are
[23,38], [0,4], [0,1]. This is a conditional comparison to the tag model,
not physical background validation. Light-jj's probability of observing zero
is46.41% before the mass cut and50.23% afterward.

The original source contributions are positive and equal within each process:
0.000066246662/0.0006274417/0.0094365561 pb per event. All1000 source rows,
including ineligible rows with q=0, remain the normalization denominator.
Cross sections are sum(w*q); no extra luminosity, sigma/N, selected-count
renormalization or tag efficiency is applied. Printed source normalization
errors are retained separately, without an unsupported quadrature combination.

Conditional tag-count variances before/final mgg are bb50.7095/15.4661,
cc3.78099/1.24796 and light-jj0.333201/0.257369. Source-event variance describes
generation plus shower plus reconstruction in the existing one-realization
pilot; those components cannot be separately identified. The independently
identified tag-randomization variance, signed weighted moments, exact
observed-count intervals and shared-event nested-stage covariance are given in
the [statistical report](phase6d_statistical_uncertainty.md) and
[machine-readable analysis](../simulation/rare_backgrounds/evidence/results/analysis.json).

Light-jj source event997 supplies98.5211% of the final expected count. Its
eligible native jet flavors are5,2,21,21,5 and its actual sampled bit0 tags
contain only one eligible tag. This event is present in the actual ROOT-derived
table with its original LHE/HepMC identity. The analytic final acceptance SE is
about98.52% of its mean; a well-measured rare rate or an ordering of background
cross sections cannot be inferred from this pilot.

For zero observed survivors out of1000, the exact two-sided95 acceptance interval
is[0,0.00368208390] and the one-sided95 upper limit is0.00299124955. Therefore
zero is compatible with nonzero backgrounds, and a finite conservative future
count cannot follow from its zero lower bound. The corresponding upper limits
on the final light-jj accepted cross section, conditional on the fixed source
normalization and IID study model, are0.0347462 pb(two-sided endpoint) and
0.0282271 pb(one-sided). Detector, generator-model and source-normalization
systematics are outside those acceptance limits.

## Sensitivity and future independent statistics

Eight predeclared b/c/light/joint ±20% probability variations are explicitly
**TOY_MODEL_SENSITIVITY_ONLY**. They reuse the same reconstructed events and
observed tags; no new independent statistics is created. They are not official
ATLAS uncertainty sources or a combined systematic band. Full variations and
clipping counts are in the [toy report](phase6d_toy_model_sensitivity.md).
Shower/PDF/scale, tracking/calorimeter response, pileup and flavor-model changes
are NOT_EVALUATED by these toys.

For final mgg ordinary event counts, conservative pilot planning using the
observed CP95 lower acceptance endpoint gives total future independent counts:

| Process |20% one-SD|20% approximate95 half-width|10% one-SD|10% approximate95 half-width|
|---|---:|---:|---:|---:|
|bbgg|1313|5044|5252|20176|
|ccgg|987435|3793190|3949740|15172760|
|light-jjgg|UNBOUNDED_INCONCLUSIVE|UNBOUNDED_INCONCLUSIVE|UNBOUNDED_INCONCLUSIVE|UNBOUNDED_INCONCLUSIVE|

These are planning conventions conditional on interval coverage and unchanged
models, not guaranteed realized precision or authorization to generate large
samples. The separate model-assisted ordinary-count20% one-SD forecasts are
801/19028/49843; analytic-q-mean forecasts are380/908/24267. Their meanings
differ. The finite light-jj forecasts are especially fragile because one event
dominates. Repeated tagging of the same events does not supply new source
kinematics or solve that limitation.

bbγj, ttH(H→γγ) and ZH(Z→bb,H→γγ) receive a
[physics/source feasibility plan](phase6d_new_background_feasibility.md).
Validated photon-fake transfer, decays/widths, branching-ratio bookkeeping,
production components and overlap models are prerequisites for their physical
interpretation. Plain SM tree H→γγ is not a validated available decay chain.
No new process was imported, generated or integrated.

## Executed evidence and boundaries

[Native full-file readback](../simulation/rare_backgrounds/evidence/input_verification.json)
and [independent ROOT extraction](../simulation/rare_backgrounds/evidence/pilot/extraction.json)
bind all3000 existing events. Numerical outputs are independently checked by
exhaustive tag configurations, original LHE source identity/weights, Cartesian
photon selection/masses and combination-weighted mass moments in the
[independent regression](../simulation/rare_backgrounds/evidence/independent_regression.json).
Portable numerical replay and GitHub CI do not open native ROOT. Native
adversarial tests use explicitly corrupted local failure fixtures, not generated
physics references. Existing installation/input regressions are recorded in
[regression evidence](../simulation/rare_backgrounds/evidence/regressions.json).

No PDF/PNG figure was created or staged. Historical files and earlier PRs remain
unchanged. The bounded source/data/evidence payload, Draft status, remote bytes
and exact final-head CI are checked separately before publication acceptance.
The next scientific step is a separately scoped investigation of rare native
heavy-flavor configurations and validated new-process models, followed by an
explicitly approved independent-production plan.

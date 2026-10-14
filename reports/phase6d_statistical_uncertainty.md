# Phase 6D event-level statistical uncertainty

Status: **analytic/API validation PASS; baseline statistics physically
executed on the verified existing 1000-event tables per process**. No physical event, detector
rerun, calibration, or new Monte Carlo sample is produced by this module.

The implementation is
[statistics.py](../simulation/rare_backgrounds/scripts/statistics.py).
It consumes all 1000 original reconstructed source events per process,
including zero-probability events outside photon/jet selection. The independent
[tests](../simulation/rare_backgrounds/tests/test_statistics.py) use analytic
numbers and explicit failure cases, not physics reference samples.

## Conditional tag model

The pinned Delphes 3.5.1 BTagging source, commit
28658365abeb71ee36dfc739f9670c1514c0cb10 and module SHA-256
367c02a87193498ed9e1dbb4702c94ad181b0e4f7ba171fc7df3cd3712c16f81,
uses a fresh pseudorandom Uniform draw for each jet's Flavor-based BTag bit.
BTagAlgo and BTagPhys consume separate draws and are not the selected tag.
Conditional independent Bernoulli tags are the **intended stochastic study
model**, not a claim of measured physical independence or PRNG independence
after conditioning on the complete fixed seed/state.
[Official source](https://github.com/delphes/delphes/blob/3.5.1/modules/BTagging.cc).

The actual module evaluates the full-precision candidate pT before ROOT
Float_t persistence. Probability evaluations from retained native PT are a
rounding-limited reconstruction of that model; they are not a replay of exact
tag draws or a new detector run. The card/flavor model and any toy probability
variation remain separate from this statistical calculation.

For event i let I_i indicate the tag-independent photon/jet eligibility, and
let q_i be the conditional probability of at least two tags. The analyzed
event probability is u_i=I_i*q_i. The diphoton mass stage adds its
tag-independent mass indicator. All quantities below use u_i over **all N
source events**, with ineligible rows retaining u_i=0.

For fixed reconstructed kinematics the actual tag-stage indicator Y_i has
mean u_i and variance u_i(1-u_i). Thus:

$$
E[C\mid X]=\sum_i u_i,\qquad
\operatorname{Var}(C\mid X)=\sum_i u_i(1-u_i).
$$

With the exact signed source contribution w_i in pb:

$$
E[S\mid X]=\sum_i w_i u_i,\qquad
\operatorname{Var}(S\mid X)=\sum_i w_i^2u_i(1-u_i).
$$

Negative weights affect the mean's sign and cancellation, while squared
weights keep the conditional variance nonnegative. No luminosity, second
cross-section factor, eligible-event renormalization, or output-count factor
is introduced.

## Source-event pilot variation

The analytic acceptance estimate is the mean over the full original pilot:

$$
\widehat f=\frac1N\sum_i u_i,\qquad
s_u^2=\frac{\sum_i(u_i-\widehat f)^2}{N-1},\qquad
\widehat{\operatorname{Var}}(\widehat f)=s_u^2/N.
$$

One shower/reconstruction realization exists per hard source event. Therefore
s_u² describes combined source-generation, shower and reconstruction
event-sampling variation. Those components cannot be individually identified
without independent replicas, which are not generated here. The identifiable
conditional tag-randomization variance is reported separately.

For source-normalized contributions w_i=raw_weight_i/N, define
a_i=N*w_i*u_i. The cross-section estimator is mean(a_i)=sum(w_i*u_i).
Its event-sampling variance estimate is s_a²/N. This handles signed and
nonconstant weights at the event level. It does not replace generator
integration uncertainty or detector/model systematics. A mean±1.95996*SE
normal diagnostic is explicitly asymptotic and unclipped, not an exact
rare-event confidence interval.

The denominator is N=1000 per process, not the number of eligible events or
jets. The different physics processes have separate cross sections and
pilot distributions. A/B prefixes, repeated tagging on the same events and
multiple jets in one event do not add independent hard-event statistics.

## Total variance and shared-stage covariance

For a new event drawn from the source/shower/reconstruction population:

$$
\operatorname{Var}(Y)
=\operatorname{Var}(u)+E[u(1-u)].
$$

The empirical-population identity uses denominator N for Var(u) and equals
mean(u)*(1-mean(u)). The unbiased N-1 pilot variance used for estimator SE
is kept distinct; substituting it into this identity without noting the
finite-pilot correction would mix two conventions.

Nested stages share the same tag decision. For stage B contained in A:

$$
\operatorname{Cov}(Y_A,Y_B\mid X_i)
=u_{B,i}(1-u_{A,i}).
$$

The conditional count covariance is its event sum, and the weighted
covariance uses w_i². Source-pilot covariance is computed from paired
event-level probabilities, or paired raw-weight integrands, across all N
events. The total empirical covariance agrees with
mean(u_B)*(1-mean(u_A)). Cut stages and correlated truth/reco variables must
not be treated as independent samples; the sample_covariance API operates
on whole paired event quantities.

## Prediction is not uncertainty on the analytic mean

On fixed kinematics the count C follows a Poisson-binomial distribution,
computed by a direct recurrence with the individual u_i. The module reports
P(C=k), P(C=0)=product(1-u_i), count tails, and a discrete equal-tail 95%
predictive interval with its actual coverage. The zero probability is also
computed through sum(log1p(-u_i)) to avoid losing small probability changes.
This interval concerns a fresh realization of tag randomness on the same
pilot. It does not measure uncertainty on the analytic mean or future
independent generated events. Conversely a small or zero sample SE of u_i
does not eliminate tag-count fluctuations or unobserved rare kinematics.

## Exact zero/low observed counts

The observed unweighted success count, not sum(u_i), can receive a
Clopper–Pearson binomial interval under an unconditional IID-event model.
The API restricts this interpretation to verified positive, equal source
weights; unequal/signed-weight yields receive no binomial yield interval.
All 1000 original events remain the trial denominator.

Exact tails are inverted numerically, without a normal approximation. With
k=0, N=1000:

$$
U_{\mathrm{two-sided},95}=1-0.025^{1/1000}
\approx0.003682084,\qquad
U_{\mathrm{one-sided},95}=1-0.05^{1/1000}
\approx0.002991250.
$$

The lower limit is zero. A zero observation is not a measured zero
background rate. Frequentist coverage is not a posterior probability that
the rate lies in this particular interval. The statistical method follows
the [NIST exact-binomial tail construction](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm);
tests independently enumerate a small binomial distribution and verify
closed-form zero/all-success endpoints.

## Planning future independent source events

For future ordinary Bernoulli event counts at acceptance p, fractional
one-SD precision r requires approximately:

$$
N_{\mathrm{future}}\ge\frac{1-p}{p\,r^2}.
$$

A normal 95% half-width target instead uses z²=1.95996² in the numerator.
The module reports 20% and 10% targets separately at z=1 and z=1.95996.
They are not the same precision target. Conservative observed-count planning
uses the exact acceptance interval's lower bound. If that bound is zero,
the result is **UNBOUNDED_INCONCLUSIVE**, rather than a finite promise.
Positive-lower-bound planning remains conditional on confidence-bound
coverage and the unchanged process/model, not an absolute guarantee.

A separate model-assisted forecast uses mean(u_i). For averaging analytic
probabilities on new independent reconstructed source events it instead
uses N>=z²*s_u²/(r²*mean(u)²). These forecasts answer different questions:
realized tag counts versus an analytic-mean estimator. The pilot variance
can miss rare phase space; zero pilot variance does not establish zero
population variance. Neither forecast includes model/systematic uncertainty,
nor turns a toy tag-probability variation into official detector calibration.

To target at least one observed event,
P(detection)=1-(1-p)^N. An **upper** rate bound gives an upper bound on
detection probability, so substituting it produces only an optimistic
minimum event count. It never guarantees detection. When the lower rate
bound is zero, no finite conservative count for 95% detection follows.

## Executed validation scope

Nineteen analytic/API tests passed under Windows and existing WSL Python.
They cover heterogeneous/signed-weight moments, all-source denominators,
predictive-versus-mean uncertainty, total variance, exact count distributions,
zero/two-trial/all-success CP identities, the NIST small-count example with
independent factorial tail checks, qualified precision/detection planning,
nested-stage covariance and rejection of invalid/duplicated inputs.
No test fixture is published as a Monte Carlo sample.

## Separately reported source normalization uncertainty

Original MG5 integration receipts report:

| Process | Init cross section (pb) | Reported integration error (pb) |
|---|---:|---:|
| bbgg | 0.06624666 | 0.0005940933 |
| ccgg | 0.6274417 | 0.005190692 |
| light-jjgg | 9.436556 | 0.0547472 |

These are fixed source-reported normalization errors, separate from pilot
variation in the conditional acceptance and fixed-kinematic tag randomness.
The statistics module conditions on the recorded event weights; it does not
estimate or remove that source normalization error. No quadrature combination
is justified here without evidence for the relevant covariance. PDF/scale,
shower, detector, flavor and tag-model systematic uncertainties remain outside
this calculation. Printed raw weights retain 0.066246662/0.6274417/9.4365561
pb totals, rather than being silently replaced by the rounded init values.

## Actual baseline pilot results

These numerical results use all original 1000 records per process. The
two-tags stage includes photon/jet eligibility; the final stage additionally
requires 105<=m_gamma_gamma<=160 GeV. Existing observed tag bits and physical
cutflows are unchanged.

| Process/stage | Observed count | Conditional expected count | Conditional tag-count variance | Fixed-pilot predictive95 |
|---|---:|---:|---:|---|
| bbgg/two tags | 91 | 99.3063073 | 50.7094796 | [85,113] |
| bbgg/final mgg | 28 | 30.2713032 | 15.4660569 | [23,38] |
| ccgg/two tags | 7 | 4.07895913 | 3.78099479 | [1,8] |
| ccgg/final mgg | 1 | 1.31214350 | 1.24796082 | [0,4] |
| light-jjgg/two tags | 0 | 0.579371507 | 0.333201141 | [0,2] |
| light-jjgg/final mgg | 0 | 0.501324517 | 0.257369102 | [0,1] |

P(observed count) is respectively 0.0284881, 0.0860332, 0.0616270,
0.360144, 0.464106 and 0.502349. These are probabilities of a particular
discrete count, not two-sided p-values. For light-jjgg, P(zero) is 0.464106
before the mass cut and 0.502349 after it; the existing zero observations are
compatible with this conditional model.

| Final-stage process | Mean source acceptance | Source-event mean SE | Analytic cross section (pb) | Pilot cross-section SE (pb) | Fixed-pilot tag SD (pb) |
|---|---:|---:|---:|---:|---:|
| bbgg | 0.0302713032 | 0.00372864550 | 0.00200537279 | 0.000247010318 | 0.000260527638 |
| ccgg | 0.00131214350 | 0.000250046961 | 0.000823293548 | 0.000156889890 | 0.000700928718 |
| light-jjgg | 0.000501324517 | 0.000493910960 | 0.00473077693 | 0.00466081848 | 0.00478731197 |

The last two columns answer different questions and must not be substituted
for one another. Generator integration uncertainty and model/systematic
uncertainty are outside both columns.

Light-jjgg source event 997 has final-stage probability 0.493910275786,
accounting for **98.5211%** of the pilot's total expected final count.
The source-event mean SE is about 98.52% of the mean. This pilot is dominated
by one realized native-flavor/kinematic configuration; it does not establish
a well-measured rare acceptance or a robust ordering of background rates.
No original-hard heavy-flavor interpretation is inferred from this native
Flavor observation. The reported normal mean diagnostic has a negative
lower endpoint, visibly demonstrating that it is not an exact physical
acceptance interval.

For the final observed counts 28/1/0, CP95 acceptance intervals are
bbgg[0.0186846862,0.0402148874],
ccgg[0.0000253174875,0.00555892428] and
light-jjgg[0,0.00368208390]. These use all 1000 source trials and verified
positive equal source weights.

Final-stage conservative ordinary-count forecasts use those lower bounds:

| Process | 20% one-SD | 20% approximate95 half-width | 10% one-SD | 10% approximate95 half-width |
|---|---:|---:|---:|---:|
| bbgg | 1313 | 5044 | 5252 | 20176 |
| ccgg | 987435 | 3793190 | 3949740 | 15172760 |
| light-jjgg | UNBOUNDED | UNBOUNDED | UNBOUNDED | UNBOUNDED |

Counts are target sample sizes for new independent source/shower/reco/tag
events, not additional generated events already available. A lower-bound
planning convention is qualified by its frequentist coverage; it does not
guarantee the realized interval width.

Using the conditional model mean instead gives final-stage ordinary-count
20% one-SD targets bbgg801, ccgg19028 and light-jjgg49843, with 10% targets
3204, 76112 and 199372. For averaging analytic probabilities, the separate
pilot-variance forecasts are 380/908/24267 at 20% one-SD and
1518/3632/97065 at 10%. These finite model-assisted numbers are especially
fragile for the event-997-dominated light-jjgg pilot. They are conditional
method comparisons, not validated future precision or an authorization to
generate the proposed samples.

Published numerical/provenance receipts:
[analysis](../simulation/rare_backgrounds/evidence/results/analysis.json),
[verified original input readback](../simulation/rare_backgrounds/evidence/input_verification.json)
and [actual ROOT-derived pilot tables](../simulation/rare_backgrounds/evidence/pilot/extraction.json).
The new tables are derived from existing events; they are not newly generated
physics samples.

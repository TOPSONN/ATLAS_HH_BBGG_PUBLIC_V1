# Phase6D toy tagging-model sensitivity

**Actual numerical execution PASS; TOY_MODEL_SENSITIVITY_ONLY.** All three
existing 1000-event pilots were analyzed under the nine fixed scenarios. No
new physical event, tag draw, detector run, calibration or optimized selection
was produced. The complete numerical result is
[analysis.json](../simulation/rare_backgrounds/evidence/results/analysis.json),
SHA256 `23fa2f4a3669c2c8bf97d422e428abda90abd67c15872e0ae8830fd9ddc57b79`.

The scenarios multiply the pinned b/c/light tag probabilities by 0.8 or 1.2,
individually or jointly. They were fixed before these nine-scenario summaries
were computed; this does not claim blinding to the preceding pilot observations.
The multipliers are illustrative study choices, not ATLAS scale factors,
calibration errors, loose/medium/tight working points or Gaussian nuisances.
Joint up/down is an illustrative common change, not a confidence envelope or
a measured nuisance-correlation model. No quadrature combination is implied.

For each retained event the model uses independent Bernoulli tags on fixed
native reconstructed jets, with actual Flavor, stored PT>25 GeV and|eta|<2.5.
The literal card functions are evaluated at persisted Float_t PT; the upstream
Delphes draw used pre-storage full precision. The resulting probabilities are
the declared persisted-kinematics model, not a recovery of hidden exact draws.
Toy values are clipped to [0,1] and clipping is counted. All clipping counters
are zero for all three processes and all nine scenarios in this pilot.

## Expected counts and fractions

Both stages retain the existing photon/jet cuts. The second also requires the
existing closed 105..160 GeV diphoton window. No mbb cut is added. E(two tags)
means the conditional expected count after photon/jet/two-tag selection;
E(mgg) includes the mass window. Fractions are 100×Σq/1000 over all source
events, including zero-probability ineligible rows. Delta is relative to the
same stage's baseline expected count, not to an observed integer. Values below
are rounded; exact decimal summaries remain public. These are expectations,
not additional events or binomial successes.

### bbgg

| Scenario | E(two tags) | Fraction % | Delta % | E(mgg) | Fraction % | Delta % |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 99.306307 | 9.9306307 | 0 | 30.271303 | 3.0271303 | 0 |
| b_down20 | 64.818394 | 6.4818394 | -34.72882 | 19.645682 | 1.9645682 | -35.10130 |
| b_up20 | 140.39658 | 14.039658 | +41.37730 | 43.048844 | 4.3048844 | +42.21008 |
| c_down20 | 99.194208 | 9.9194208 | -0.11288 | 30.231752 | 3.0231752 | -0.13066 |
| c_up20 | 99.418407 | 9.9418407 | +0.11288 | 30.310855 | 3.0310855 | +0.13066 |
| light_down20 | 99.268163 | 9.9268163 | -0.03841 | 30.260279 | 3.0260279 | -0.03642 |
| light_up20 | 99.344451 | 9.9344451 | +0.03841 | 30.282325 | 3.0282325 | +0.03641 |
| joint_down20 | 64.666899 | 6.4666899 | -34.88138 | 19.594635 | 1.9594635 | -35.26993 |
| joint_up20 | 140.53557 | 14.053557 | +41.51727 | 43.093700 | 4.3093700 | +42.35826 |

### ccgg

| Scenario | E(two tags) | Fraction % | Delta % | E(mgg) | Fraction % | Delta % |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 4.0789591 | 0.40789591 | 0 | 1.3121435 | 0.13121435 | 0 |
| b_down20 | 3.8560155 | 0.38560155 | -5.46570 | 1.2626567 | 0.12626567 | -3.77145 |
| b_up20 | 4.3341174 | 0.43341174 | +6.25547 | 1.3616303 | 0.13616303 | +3.77145 |
| c_down20 | 2.8436557 | 0.28436557 | -30.28477 | 0.88975552 | 0.088975552 | -32.19068 |
| c_up20 | 5.5593575 | 0.55593575 | +36.29353 | 1.8124881 | 0.18124881 | +38.13185 |
| light_down20 | 4.0667067 | 0.40667067 | -0.30038 | 1.3084534 | 0.13084534 | -0.28123 |
| light_up20 | 4.0912167 | 0.40912167 | +0.30051 | 1.3158363 | 0.13158363 | +0.28143 |
| joint_down20 | 2.6246361 | 0.26246361 | -35.65427 | 0.84626884 | 0.084626884 | -35.50486 |
| joint_up20 | 5.8421160 | 0.58421160 | +43.22566 | 1.8749207 | 0.18749207 | +42.88991 |

### Light-jjgg

| Scenario | E(two tags) | Fraction % | Delta % | E(mgg) | Fraction % | Delta % |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.57937151 | 0.057937151 | 0 | 0.50132452 | 0.050132452 | 0 |
| b_down20 | 0.40255852 | 0.040255852 | -30.51807 | 0.32487123 | 0.032487123 | -35.19742 |
| b_up20 | 0.79486062 | 0.079486062 | +37.19360 | 0.71645393 | 0.071645393 | +42.91221 |
| c_down20 | 0.55416023 | 0.055416023 | -4.35149 | 0.50031855 | 0.050031855 | -0.20066 |
| c_up20 | 0.60896359 | 0.060896359 | +5.10762 | 0.50233048 | 0.050233048 | +0.20066 |
| light_down20 | 0.57359296 | 0.057359296 | -0.99738 | 0.49909453 | 0.049909453 | -0.44482 |
| light_up20 | 0.58541798 | 0.058541798 | +1.04363 | 0.50361368 | 0.050361368 | +0.45662 |
| joint_down20 | 0.37224047 | 0.037224047 | -35.75099 | 0.32179105 | 0.032179105 | -35.81183 |
| joint_up20 | 0.83105205 | 0.083105205 | +43.44027 | 0.71978790 | 0.071978790 | +43.57724 |

## Normalization and limits

Original source contributions are retained exactly and the weighted result is
Σwq, with original denominator 1000. No extra sigma/N, luminosity or tag-efficiency
factor is applied. Baseline expected weighted cross sections in pb are:

| Process | Photon/jet/two-tag stage | Plus mgg window |
|---|---:|---:|
| bbgg | 0.006578711373372912 | 0.002005372788222402 |
| ccgg | 0.002559309053485225 | 0.0008232935477497697 |
| jjgg | 0.005467271731192602 | 0.0047307769253341955 |

All scenario-specific weighted values and signed pair-mass moments are in the
three conditional summaries. This table describes the explicit existing LO
pilot and study model; it is not a complete calibrated collider-background
prediction. The original generator integration errors remain separate from
tag/source-pilot terms; no evidenced covariance supports automatic quadrature
combination into a full theory/detector uncertainty.

The response is nonlinear: requiring two tags can turn a 20% per-jet change
into a change near 40% in an expected event count. The ccgg pilot primarily
responds to its c-category toy variation. The light-jjgg pilot's conditional
mgg expectation is particularly sensitive to b-category variation, despite
its hard-process label. Native flavour association includes eligible shower
partons; the label does not classify every reconstructed jet as light.
Source event 997 contributes 98.5211% of the baseline jjgg mgg expectation in
this particular pilot. The concentration ratio is 1.03021 and is only a yield
concentration diagnostic, not an effective independent-event count or a
confidence interval. That extreme concentration and unseen rare kinematics
prevent a precise general conclusion about light-background rejection.

Observed Stage C counts remain 91/7/0 at the two-tag stage and 28/1/0 after mgg
for bbgg/ccgg/jjgg. They are not overwritten by the expectations. Zero jjgg
observations do not imply zero rate; conditional predictions, exact observed
intervals and source-event uncertainty have different scopes, documented in
[statistical_uncertainty.md](phase6d_statistical_uncertainty.md). No toy shift
is a substitute for those statistical terms or missing calibration/systematics.
These observed counts and their exact intervals belong to the nominal card
only. Repeated nominal observations inside toy output are historical reference
values, not newly drawn observations or coverage claims for a varied toy card.

The complete self-service command was physically executed on Linux Python 3.12
and reproduced the saved `analysis.json` and all three conditional summaries
byte-for-byte. Local reproduction and prospective GitHub CI are separate
evidence. Native Windows libm can differ in last-bit binary64 evaluations, so
no Windows-versus-Linux bitwise probability claim is made. Independent tests
check same-host exact-model agreement and the separately recorded math-library
rounding envelope. No future background sample or figure was generated.

# Conditional rare-background statistics study

Phase6D analyzes the existing three verified 1000-event Delphes reconstructions:
bbgg, ccgg and light-jjgg. It generates no new MG5, Pythia or Delphes events and
does not alter their installations/cards/references. A compact numerical pilot
under [evidence/pilot](evidence/pilot) retains all original source identities,
signed contributions, reconstructed photons/jets and accepted cut scalars;
its bindings refer to actual compatible native ROOT readback.

For each fixed reconstructed event, `conditional_tags.py` evaluates the pinned
bit0 b/c/light probability functions and the conditional probability of at least
two tags. It uses a direct Poisson-binomial dynamic program, preserves the
original full1000 denominator, and enumerates the leading tagged-pair mass
moments. This is an independent per-jet Bernoulli model on the persisted
reconstruction. Card probabilities evaluated at stored Float_t PT approximate
the preceding full-precision kinematics used for the original Delphes draw;
the hidden exact per-draw probability is not recovered.

Nine scenarios are fixed: baseline, individual b/c/light up/down20%, and joint
up/down20%. They are `TOY_MODEL_SENSITIVITY_ONLY`, not official ATLAS efficiency
uncertainties. Probabilities are clipped to [0,1], and clipping is counted.
There is no photon-fake probability, detector recalibration or new mass-window
optimization. Existing sampled BTag bits remain the observed comparison; an
analytic expectation is not a newly generated event sample.

The independent `statistics.py` API separates conditional tagging variation
from an IID source-event pilot term covering generation, shower and
reconstruction together. One realization per hard event cannot separate those
three sources. Exact observed binomial intervals, the conditional predictive
count distribution and model expectations have distinct meanings. A zero
observed passage is not proof of a zero background. Larger-statistics forecasts
are pilot/model estimates; they do not count reused events or tag draws as
additional independent hard statistics.

The [Traditional Chinese guide](USER_GUIDE_ZH_TW.md) gives commands for the
existing compact pilot and installation-dependent native verification. Personal
numerical output stays local; these commands do not create commits, releases
or pushes. Public Python CI can reproduce numerical results and verify the
source/hash binding; it does not execute native ROOT or establish a calibrated
physical background prediction.

The full numerical entry point is `scripts/analyze_pilot.py --pilot-dir
simulation/rare_backgrounds/evidence/pilot --output NEW_LOCAL_DIRECTORY`.
Its `analysis.json` contains all scenarios, event-level uncertainty/predictive
results, nested-stage covariance, concentration diagnostics and independent
statistics forecasts. Public outputs are the three conditional summaries and
complete `evidence/results/analysis.json`, with the original pilot/bindings and
verification receipts. Full conditional event tables remain local. The reviewed
pilot caps are 2 MiB each/6 MiB combined; other new text is bounded 5 MiB. No new
ROOT/LHE/HepMC/archive/figure or historical-path change is allowed by the
Phase6D payload auditor. The Python 3.12/Ubuntu 24.04 workflow reproduces exact
public numerical bytes and never installs or executes the physics stack.

bbγj, ttH(H→γγ) and ZH(Z→bb,H→γγ) remain `FEASIBILITY_ONLY`. Their proposed
cards have not been imported, generated, integrated or validated. Plain SM tree
production lacks the HAA decay vertex; adopted new BRs/cross sections and
photon-fake transfers remain UNKNOWN. The
[feasibility report](../../reports/phase6d_new_background_feasibility.md) and
[primary-source evidence](evidence/new_background_source_review.json) state
the model, decay, normalization and overlap gates. These are research proposals,
not supported generation profiles or a complete HH background model.

No figure is produced here. Any future PDF/PNG must retain the repository's
exact-version user-approval gate before staging/pushing. Historical reports and
data remain unchanged. Actual Phase6D execution receipts and final GitHub/CI
acceptance are recorded separately; source tests alone do not establish them.
The final full command physically analyzed 3000 original events/all nine
scenarios on Linux Python 3.12. The separate final 51-test suite passed with no
skips. The analysis SHA256 is `23fa2f4a3669c2c8bf97d422e428abda90abd67c15872e0ae8830fd9ddc57b79`;
the analysis and three conditional summaries reproduced the public bytes
exactly. This scope does not claim Windows/Linux bitwise math-library identity,
native ROOT execution by CI, calibration or new independent events. The
[toy-sensitivity report](../../reports/phase6d_toy_model_sensitivity.md) retains
all scenario counts/fractions, clipping counters and explicit statistical limits.

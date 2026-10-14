# Phase6F physical-pilot readiness

**READINESS_METHODS_PREPARED; PHYSICAL_PILOT_NOT_AUTHORIZED.**
The reviewed target is100 independent13TeV tree qqbar-initiated ZH production
events with Z→bb and H→gamma gamma. No integration, new event, Pythia `next()`
or detector execution on new ZH inputs occurs in Phase6F.

The preferred route B preserves MG5's production/Z-decay chain and stable H,
then proposes a forced scalar-H diphoton decay. Route A stable Z/H externalLHE
production remains an alternative with a documented Z-spin limitation. The
two routes have different source cross-section/BR scopes. In B, source-included
Z_to_b_bbar is never multiplied again; H_to_gamma_gamma remains an explicit
missing-factor candidate, conditional on actual external-weight closure.

The generator model is sm-no_b_mass, five-flavour protons and built-in CTEQ6L1.
Frozen μR=μF=MZ+MH=216.188GeV is a threshold-scale LO pilot prescription,
not a precision prediction or continuum125GeV reuse. MH125/MZ91.188GeV,
fixed generator widths and EW inputs remain explicit model values. Pythia's
initialized inclusive widths/BR tables are recorded separately; they are not
silently substituted for the source Z propagator or adopted as calibrated BRs.
See the [generator](phase6f_zh_generator_contract.md),
[decay](phase6f_higgs_decay_validation_plan.md) and
[normalization](phase6f_br_normalization_contract.md) contracts.

The [Traditional Chinese guide](../simulation/zh_pilot/USER_GUIDE_ZH_TW.md)
provides the tested local text-only command. It checks the hash-bound bundle,
semantic generator/decay/input-profile contracts, installed versions/ABI and
available resources. Exact templates are copied locally; a separate complete
run card records only the requested seed/count/beam overrides with its own
SHA256. No generated sample directory, LHE, HepMC or ROOT is created by dry-run.

Projected CPU policy is one worker. Process-specific wall time, peak RAM and
storage cost remain **UNKNOWN**. Measured free CPU/RAM/disk describes current
availability; a2-hour/5GiB administrative budget is not a benchmark or a capacity
guarantee. Old continuum timings are not divided or extrapolated to ZH.

Future relative paths are mg5/Events/pilot100/unweighted_events.lhe.gz,
pythia/shower.hepmc3.gz and delphes/detector.root, with separate source, decay,
weight and validation ledgers. The independent profiles prepare H-photon and
Z-bottom ancestry plus m_gamma_gamma/m_bb/m_bb_gamma_gamma using native jets
and original bit0. The old continuum validators/card remain byte-identical.
The existing shower/controller's continuum assumptions cannot be bypassed;
a separately reviewed execution bridge and actual event closure are still
required. No native ZH reconstruction has been demonstrated.

Before enabling a future100-event pilot, review the adopted BR/width convention,
source-included/external factors, decay spin and resonance approximations,
SLHA/PDF/scale controls, applicable source/shower/detector adapters and resource
stopping policy. During an authorized pilot, retain every original source ID
and signed weight/full denominator; compare actual LHE, Pythia Info and named
HepMC weights, actual decay ancestors and widths, then native reconstruction.
Missing/failure/partial inputs remain explicit and are never repaired into PASS.

Synthetic tests validate algebra/serialization/rejection methods only. Gate L
is **NOT_AUTHORIZED**. A physical ZH sample PASS requires actual authorized
events and file-bound validation; neither a dry-run nor table initialization
provides that acceptance. There is no automatic100/1000/1M production.

# ccgg ATLAS-like detector reference

Selected artifact: `detector_100.root`, the unchanged bytes of an actual 100-input
Delphes run. Actual native readback, strict privacy/size checks, exact local
preparation and portable integrity passed; remote publication is sealed separately.
The accompanying manifest binds the original ROOT/card/source/native bytes. The input is the
existing `pp_ccgg_sm_lo_ps_13tev/shower_100.hepmc3.gz`, sharing the original 1000
MG5 hard-event source; it does not add 100 independent hard events.

The configuration is `FAST_SIM_ATLAS_LIKE / NOT_OFFICIAL_ATLAS`, Delphes 3.5.1,
ROOT 6.40.04/C++20, anti-kT R = 0.4 and the upstream ATLAS-card bit 0 tagging model.
The exact runtime card uses seed 610302. Jets are classified using actual
associated Flavor, rather than assuming every jet is c because of the process
label. Original source-normalized signed weights retain denominator 1000; no
luminosity or extra tag-efficiency factor.

`sample_manifest.json` records original ROOT, card, source, input/truth indices,
native readback and analysis hashes. Portable CI checks integrity and binding;
it does not physically read ROOT. Full1000 ROOT output stays local by default.
See [the guide](../../../simulation/delphes/USER_GUIDE_ZH_TW.md) and
[publication report](../../../reports/phase6c_github_publication.md).

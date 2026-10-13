# Phase 6C background cutflow

Final bbgg/ccgg/light-jjgg 1000-event detector cutflows: **PASS native
processing**, independently checked from each actual Stage C report/CSV.
No small-sample selection optimization or significance
extrapolation is performed.

| Cumulative stage | Fixed definition |
|---|---|
| 00_input | Fully source-bound and native-validated event |
| 01_photons | At least two eligible photons, leading pT>35 GeV; eligible photons pT>25, |eta|<2.37 excluding open 1.37<|eta|<1.52 |
| 02_jets | Previous stage and at least two reco jets pT>25 GeV, |eta|<2.5 |
| 03_two_btags | Previous stage and at least two eligible jets with BTag bit0 |
| 04_mgg_105_160 | Previous stage and leading eligible photon pair 105<=m_gamma_gamma<=160 GeV |

Optional m_bb window: **NOT_EVALUATED**. Inclusive m_jj uses the eligible jet
pair; m_bb uses the eligible tagged pair, which can be different jets.
m_bb_gamma_gamma combines that tagged pair with selected photons.
Missing pairs are null rather than zero physical masses.

Each stage stores raw count, exact signed source contribution sum in pb and
sum of squared contributions in pb². Input nominal contribution is
raw_LHE_weight_pb/full_source_count. The denominator stays the original
1000-source-event count, even for a 10/100 prefix. Native Float_t weights are
verified casts; accumulation uses exact source binary64 contributions.
There is no second cross-section factor, output-count renormalization,
luminosity scaling or lost-event weight repair.

Failed assessment blocks acceptance. Actual produced entries, valid/invalid
assessments and unassessed output remain separate. Invalid assessments do
not partially contribute cutflow/weight sums. A prefix retains only its
subset contribution, not the full-run cross section.

Low surviving counts, especially double tags and the diphoton mass window,
remain explicit. These exploratory continuum-sample rates from a modified
upstream study card are not an official ATLAS HH background prediction or
calibrated tagging measurement.

Actual cumulative counts use Stage C only:

| Stage | bbgg | ccgg | light-jjgg |
|---|---:|---:|---:|
| Input | 1000 | 1000 | 1000 |
| Photons | 446 | 378 | 445 |
| At least two jets | 266 | 241 | 277 |
| At least two bit0 tags | 91 | 7 | 0 |
| 105–160 GeV diphoton mass | 28 | 1 | 0 |

Exact source-weight sums in pb:

| Stage | bbgg | ccgg | light-jjgg |
|---|---:|---:|---:|
| Input | 0.066246662 | 0.6274417 | 9.4365561 |
| Photons | 0.029546011252 | 0.2371729626 | 4.1992674645 |
| At least two jets | 0.017621612092 | 0.1512134497 | 2.6139260397 |
| At least two bit0 tags | 0.006028446242 | 0.0043920919 | 0 |
| 105–160 GeV diphoton mass | 0.001854906536 | 0.0006274417 | 0 |

Final-stage sums of squared contributions are 1.2288136633e-7 pb²,
3.9368308690e-7 pb² and zero respectively. The one surviving ccgg event and
zero light-jjgg events imply insufficient statistics; zero observed survivors
does not establish a zero background rate. All 3000 source contributions in
these references are positive. Signed-weight support is an interface/test
property, not evidence that negative weights occurred in this sample.

The totals preserve printed raw LHE weights rather than replacing them with
rounded init cross sections: bbgg 0.066246662 versus init0.06624666 pb,
ccgg0.6274417 versus init0.6274417 pb, light-jjgg9.4365561 versus
init9.436556 pb. The 2e-9 and 1e-7 pb printed differences are retained;
no hidden correction or second normalization factor closes them.

Hash-bound actual full-run CSVs:
[bbgg](../simulation/delphes/evidence/bbgg/cutflow.csv),
[ccgg](../simulation/delphes/evidence/ccgg/cutflow.csv),
[light-jjgg](../simulation/delphes/evidence/jjgg/cutflow.csv).

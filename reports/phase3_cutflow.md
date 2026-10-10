# Phase 3 exploratory cutflow

Project: ATLAS_HH_BBGG_PUBLIC_V1. Executed 2026-10-10 UTC.
**Verdict: PASS_PROVISIONAL_PRESELECTION.** Unit status: **PROVISIONAL**.
These are study-defined raw counts conditional on the existing GamGam skim and
source entries [100,63195). They are not HH detection efficiencies. No weights,
trigger correction, b-tag WP, fit or luminosity normalization are used.

## Definition and actual results

The local input is the SHA-256-pinned [Phase 2 derived cache](../metadata/phase2_artifact_manifest.csv),
from record [93915](https://opendata.cern.ch/record/93915),
`ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root`. This task adds zero new ROOT
entry reads. The original Phase 1 ten entries and Phase 2 unit-probe entries 10-99
are not part of this cutflow. C0 contains exactly 63,095 unique monotonically
ordered source entries. Thirty-seven quarantined negative diphoton mass-squared
events fail C1; their physical values are not silently corrected or accepted.

[Configuration](../metadata/phase3_selection_config.ini): `study-preselection-v1`.
The baseline requires valid cached reconstruction; >=2 photons; leading pT >35
GeV; subleading pT >25 GeV; both leading photons |eta| <2.37 excluding the open
interval 1.37<|eta|<1.52; 105<=m_gg<=160 GeV; >=2 jets; both leading jets pT >25
GeV; both leading jets |eta| <2.5. Objects are ranked before acceptance cuts.
Jet cuts apply to the two highest-pT inclusive jets, not a re-ranked central or
b-tagged collection. Exact pT and outer eta thresholds fail; crack endpoints
and mass endpoints pass. Each predicate is separately testable.

| Cut | Before | After | Rejected | Conditional fraction | Cumulative fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| C0_GamGam_skim_input | 63095 | 63095 | 0 | 1 | 1 |
| C1_valid_kinematics | 63095 | 63058 | 37 | 0.99941358269276492 | 0.99941358269276492 |
| C2_two_photons | 63058 | 63058 | 0 | 1 | 0.99941358269276492 |
| C3_leading_photon_pt | 63058 | 53978 | 9080 | 0.85600558216245359 | 0.85550360567398365 |
| C4_subleading_photon_pt | 53978 | 53978 | 0 | 1 | 0.85550360567398365 |
| C5_photon_eta_acceptance | 53978 | 51136 | 2842 | 0.94734891993034198 | 0.81046041683176162 |
| C6_diphoton_mass_window | 51136 | 12564 | 38572 | 0.24569774718397996 | 0.1991282985973532 |
| C7_two_jets | 12564 | 2842 | 9722 | 0.22620184654568609 | 0.045043188842222047 |
| C8_leading_two_jet_pt | 2842 | 1689 | 1153 | 0.59429978888106971 | 0.026769157619462716 |
| C9_leading_two_jet_eta | 1689 | 1689 | 0 | 1 | 0.026769157619462716 |

Every row has `definition_version=study-preselection-v1` and
`validation_status=PROVISIONAL_EXPLORATORY`. Full-precision machine data are in
[phase3_cutflow.csv](../metadata/phase3_cutflow.csv). Conditional fraction is after/before;
cumulative fraction is after/C0; a zero preceding count produces an empty conditional
fraction rather than a fabricated zero. C9/C0 = 0.026769157619462716 (2.6769%) for
this processed skim only. The zero C4/C9 rejection counts describe this cache, not
proof that those cuts are unnecessary in other inputs.

## Optional raw photon-flag branches

The exact physical schema contains `photon_isTightID`, `photon_isLooseID`,
`photon_isTightIso`, `photon_isLooseIso` as RVec<bool>. The Phase 2 cache preserves
the tight flags belonging to the pT-ranked leading photons. The [dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
and [PhotonInfo v1.0.0](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0)
support treating these as raw boolean decisions, provisionally; the later producer
does not prove exact FEB2025 WP definitions. Loose flags are read/structurally
validated in Phase 2 but are not added to the optional cache selection branches.

Within the 1,689 C9 events, both raw tight-ID flags are true in **175** events;
both raw tight-ID and tight-isolation flags are true in **48**. Missing flag rows:
**0**. See [optional diagnostic CSV](../metadata/phase3_optional_photon_flags.csv).
These optional branches have `PROVISIONAL_RAW_FLAG_DIAGNOSTIC` status and do not
alter baseline figures/cutflow. They establish neither efficiency nor SF validity.
The installed code classifies missing required flags UNKNOWN and rejects invalid
nonboolean values. `trigP` is not an official 35/25 diphoton decision and is unused.
No version-matched b-tag quantile mapping is established: b-tag analysis is BLOCKED,
leading jets remain inclusive, and m_jj is not m_bb. Details: [readiness](phase4_readiness_assessment.md).

## Figures and histogram accounting

All figures carry the required three-line exploratory disclaimer, record/run-range
provenance, source/selected event counts, PROVISIONAL status, white backgrounds,
explicit GeV axes and raw event/object counts. All four PNGs were visually inspected.

| Figure | Filled values | Visible bins | Underflow | Overflow |
| --- | ---: | ---: | ---: | ---: |
| [m_gg_preselection.png](figures/phase3/m_gg_preselection.png) | 1689 | 1689 | 0 | 0 |
| [m_jj_preselection.png](figures/phase3/m_jj_preselection.png) | 1689 | 1680 | 0 | 9 |
| [photon_pt_selected.png](figures/phase3/photon_pt_selected.png) | 3378 | 3378 | 0 | 0 |
| [jet_pt_selected.png](figures/phase3/jet_pt_selected.png) | 3378 | 3360 | 0 | 18 |

Each pT histogram fills both leading objects per selected event. Mass histograms
fill once per selected event. Overflow counts are preserved in the
[histogram inventory](../metadata/phase3_histogram_inventory.csv), not removed
from C9. Only C9 distributions are shown; no inconsistent before/after comparison
or global normalization was added. [Artifact hashes](../metadata/phase3_artifact_manifest.csv)
cover cache identity, configuration, machine outputs and committed figures.

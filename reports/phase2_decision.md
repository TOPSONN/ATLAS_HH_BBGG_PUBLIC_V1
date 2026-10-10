# Phase 2 decision

**VERDICT: PASS_PROVISIONAL_RECONSTRUCTION.** Git integration and all numerical,
native-reader and bounded-execution gates passed. Unit interpretation is supported
by independent checks but remains PROVISIONAL for exact FEB2025 production.

Proceed automatically, within the user's authorization, to study-defined Phase 3
photon/inclusive-jet preselection. Reuse the Phase 2 derived event cache so no raw
collision entry is inspected again. Keep all cutflow quantities unweighted and
conditional on the GamGam skim and the reported bounded source range.

Do not label inclusive leading jets as b-jets; do not infer a b-tag WP, tight-ID
efficiency, official 35/25 diphoton trigger, GRL/luminosity, full calibrated selection
or HH detection efficiency. Phase 0 PARTIAL and Phase 1 PARTIAL_SCHEMA_VALIDATED
remain historical evidence, unchanged. Exact producer/calibration correspondence
and official likelihood reproduction remain unresolved.

Create a Phase 2 PR targeting main. Its merge is not authorized by this task.
Phase 3 must be stacked on this unmerged feature branch. See
[the validation report](phase2_kinematic_validation.md) for tests, tolerances,
rejected entries, processing ranges, figures, checksums and reproduction commands.

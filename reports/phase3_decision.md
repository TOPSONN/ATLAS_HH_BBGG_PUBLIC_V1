# Phase 3 decision

**VERDICT: PASS_PROVISIONAL_PRESELECTION.** Study-defined, unweighted photon and
inclusive-jet selection is implemented and tested. The physical cutflow uses the
checksum-pinned Phase 2 cache, inherits PROVISIONAL GeV/radian semantics, and adds
zero ROOT event reads and zero remote dataset bytes.

The 63,095 source events in [100,63195) yield 1,689 C9 events. This is a conditional
fraction of this GamGam skim and bounded range, not HH detection efficiency or an
inclusive collision acceptance. The source already requires two photons near the
25 GeV threshold. No fit, signal extraction, significance or event normalization
was performed. Inclusive m_jj is not m_bb.

Raw tight-ID/isolation boolean diagnostics are optional and PROVISIONAL. Their
counts do not validate exact-production working points, correction factors or
efficiencies. No flags are included in the baseline C0-C9 selection. B-tag analysis
remains **BLOCKED**: no version-matched quantile-to-WP mapping is established.
`trigP` is not used or interpreted as an official 35/25 GeV diphoton trigger.

Phase 0 **PARTIAL**, Phase 1 **PARTIAL_SCHEMA_VALIDATED**, and Phase 2
**PASS_PROVISIONAL_RECONSTRUCTION** remain unchanged. See [cutflow](phase3_cutflow.md)
and [validation](phase3_validation.md) for executed results and reproduction.

Create the Phase 3 PR targeting the unmerged Phase 2 branch
`codex/phase2-kinematic-reconstruction`. Merge of either new PR requires separate
user authorization. The [Phase 4 assessment](phase4_readiness_assessment.md) is
documentation only; an HH-like search or statistical model is not ready.

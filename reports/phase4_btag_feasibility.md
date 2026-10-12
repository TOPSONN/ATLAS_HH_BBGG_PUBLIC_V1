# Phase 4 b-tag feasibility

**BTAG_STATUS = BLOCKED.** Native `jet_btag_quantile` and `ScaleFactor_BTAG` are
present, but exact FEB2025 tagger version, quantile-to-working-point mapping,
calibration/SF validity and same-event truth flavour have not been established.
The current two-jet mass remains **m_jj of leading inclusive jets**, not m_bb.
This audit does not change historical cuts or labels.

## Evidence and unresolved semantics

The actual selected MC branch inventories contain
`jet_btag_quantile: ROOT::VecOps::RVec<int>` and `ScaleFactor_BTAG: Float_t`.
Presence and native type establish storage only. The official
[educational dictionary](https://opendata.atlas.cern/docs/data/for_education/13TeV25_details)
calls the variable a continuous DL1dv0 quantile, while its object-description
section refers to DL1dv01. The versioned
[JetInfo v1.0.0 source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0)
reads `ftag_quantile_DL1dv01_Continuous` and multiplies
`ftag_effSF_DL1dv01_Continuous_NOSYS` over retained jets for MC. This source is
later than the FEB2025 flat files and does not attest their exact tagger/tool
configuration. DL1d cannot be assumed equivalent to GN2, and no GN2 working
point is inferred from an integer quantile.

The later
[skim source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/scripts%2FskimOpenDataNtuples.py/raw?ref=v1.0.0)
uses `jet_btag_quantile >= 4` for its `sig_bjet70` expression. That is evidence
about that particular later script, not a validated 70% working point for these
FEB2025 files. Adopting it requires exact tool/tagger configuration, the full
quantile interval definition including invalid/out-of-acceptance values, and
calibration applicability to this jet collection and study selection. Numerical
quantile frequencies cannot establish any of those properties.

The newly read later
[TruthInfo source](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FTruthInfo.cxx/raw?ref=v1.0.0)
exports truth-jet kinematics but no jet flavour label. Kinematic matching to a
truth jet does not establish a b hadron, a b parton, or a validated ghost/
hadron-cone flavour association. No b-tag efficiency, c/light mistag probability,
flavour-dependent scale factor, or flavour-dependent uncertainty is measured.

| Required property | Status | Reason |
| --- | --- | --- |
| Native quantile/SF storage | PASS, bounded inspected files | Native ROOT branch inventory establishes presence/types |
| Exact FEB2025 tagger and version | UNKNOWN | Later DL1dv01 source and dictionary naming do not identify exact producer |
| Numeric quantile to WP mapping | UNKNOWN | Later `>=4` script example does not attest released-file WP semantics |
| Jet algorithm/kinematic calibration and accepted range | UNKNOWN exact configuration | Full producer/tool/acceptance provenance not established |
| SF validity for retained/selected jets | UNKNOWN | SF existence does not verify calibrated WP/selection applicability |
| Native same-event flavour evidence | NOT_ESTABLISHED | Flat truth kinematics provide no validated flavour label |
| b-tag efficiency / mistag / uncertainty study | BLOCKED | Requires the unresolved properties above |
| m_bb or HH-like category | BLOCKED | Inclusive leading jets cannot be relabelled as b jets |

## Bounded alternative and permissible scope

The live
[research PHYSLITE catalogue](https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html)
documents `AnalysisJets.HadronConeExclTruthLabelID` (5=b, 4=c, 15=tau), extended
labels and a link to `BTagging_AntiKt4EMPFlow`; that b-tag collection documents
DL1dv01 probabilities. A physical research file would still need verification
of those branches, association rules, generator/simulation provenance,
calibration and the exact tagging recipe. The suitable first listed ggF/VBF
H→γγ research files in record 80012 exceed this run's 128 MiB budget, and the
flat RVec adapter cannot read xAOD ElementLinks. See
[the source audit](phase4_mc_source_audit.md).

The first-100-entry native probes add a concrete warning: 423103 has
`ScaleFactor_BTAG` minimum **−1**, whereas `ScaleFactor_FTAG` ranges from
0.8872156143 to 1.0492935181. Both fields are positive over the bounded H probes,
but that does not establish aliasing or global validity. The negative value may
be an invalid/out-of-applicability sentinel or another production convention;
its cause is UNKNOWN. It must be preserved and audited, not interpreted as a
negative NLO generator weight, replaced with one or taken in absolute value.
Do not multiply BTAG and FTAG together without a verified convention.

Physical truth-jet direction probes pass within the first 100 entries, but the
same probes contain negative native truth-jet masses (15/22/8 objects across
343981/346214/423103). Preserve their signed values and UNKNOWN mass semantics.
A direction-only match neither uses that mass nor supplies flavour evidence.
None of these observations resolves the tagger/WP/calibration blockers above.

The completed **[100,10000)** main runs (9,900 entries per sample) further
preserve negative `ScaleFactor_BTAG` scalar counts **18 / 75 / 103** for
343981 / 346214 / 423103, with minima **−1.2101823092 / −1.2288618088 /
−1.2561054230**. These later observations do not overwrite the positive-only
first-100 H probes. No SF value is made absolute, replaced or applied.
Generator mcWeight negatives occur separately (14 / 15 / 0 in the same main
populations); a generator sign and an invalid/unknown correction convention
must remain distinct.

Main negative truth-jet mass counts are **1397 / 2511 / 731**. Their direction
association checks can pass within PROVISIONAL geometry while mass/flavour
semantics remain UNKNOWN. The overall physical reconstruction gate nevertheless
**FAILS**: 343981 has one leading-photon mass-closure failure out of 12,004
comparisons, at source entry 5888, outside raw C9. Passing geometry checks or
CTest 17/17 cannot turn this into tagging, calibrated-efficiency or overall
physics-validation PASS. See [MC reconstruction](phase4_mc_reconstruction.md),
[retained numerical failure](phase4_numerical_failure.md), and
[quality gates](../metadata/phase4_quality_gates.json).

Permissible diagnostics retain the raw quantile as an uncalibrated categorical
quantity or study inclusive jets without tagging. No quantile cut is introduced
as a validated b-tag selection, no SF is applied to manufacture a tagged rate,
and no truth-jet geometrical match upgrades a jet to b flavour. Unblocking this
requires exact released-file provenance and a reviewed public mapping plus
calibration and truth-flavour evidence; all existing PROVISIONAL/UNKNOWN labels
remain in force.

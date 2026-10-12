# Phase 5 decision: engineering passes; physical background model blocked

Date: **2026-10-12**. Project: `ATLAS_HH_BBGG_PUBLIC_V1`. Task: `PHASE5_MC_BACKGROUND_AND_NORMALIZATION_V1`. Overall status: **PARTIAL**. Verdict: **ENGINEERING_PASS_PHYSICAL_MODEL_BLOCKED**.

The new signed-normalization, ROOT shape-covariance and synthetic control-region modules pass fresh integrated tests. The official release identifies continuum DSID **302521**, but four bounded access routes obtained **zero ROOT payload bytes**. Its native schema is **NOT_EVALUATED**. Exact nominal-weight, pre-skim aggregation, completeness, filter/decay/correction and DATA exposure conventions remain unresolved. No physical normalization, weighted DATA/MC shape comparison, physical closure, likelihood fit or HH sensitivity calculation was performed.

## Dependency and preservation

The Phase 5 branch `codex/phase5-background-normalization` starts exactly at Phase 4 head `704045c6c18c313114e3ab41019e46c70beb086b`, on `codex/phase4-mc-truth-validation`. PR #7 was inspected as **OPEN / DRAFT**, with **NO_CHECKS**; missing CI is not a CI PASS. This task does not merge it or any other PR and is independent of plotting PR #6.

The preservation manifest [phase5_baseline_preservation.json](../metadata/phase5_baseline_preservation.json) verifies **134 historical tracked files and 243 immutable local artifacts**, including the original four DATA/MC ROOT inputs, old negative-M²/failure evidence, recovered results and selection configuration. CMake preserves its complete historical prefix and appends the optional Phase 5 targets. A mutable external CTest temporary-marker file is outside the immutable artifact set; original stress evidence directories remain preserved. No old scientific result, cutflow, matching definition, weight, tolerance, plot or input is repaired or replaced.

The existing Phase 4 suite was rerun before development: **18/18 PASS**. Historical physical numerical evidence remains **37,421 pair comparisons, zero closure failures**; it is checksum-preserved evidence, not a new Phase 5 physical ROOT reconstruction run.

## Executed environment and tests

| Item | Actual result |
| --- | --- |
| ROOT | 6.40.04; ROOT C++ standard 20 |
| C++ | 20; required ON; extensions OFF |
| Actual compiler | `/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++` |
| Compiler version | GNU 15.3.0, conda build 15.3.0-7 |
| CMake / Ninja | 4.4.4 / 1.13.2 |
| Fresh Step 1 validator | **3/3 PASS**: ROOT I/O, RDataFrame, RooFit/RooStats object checks; no fit |
| Fresh integrated suite, Phases 1–5 enabled | **23/23 PASS**, zero failures/skips; 17.80 seconds |
| Signed normalization | **70 assertions PASS** |
| Signed shape covariance | **81,973 assertions / 519 analytical fixtures / 33,216 PSD directions PASS** |
| Control-region contract | **1,887 assertions / 1,782 independent partitions / 51 rejection cases PASS** |
| New bounded transfer guards | **26 fake-only tests PASS**, no physical transfer used |
| Derived-cache inventory driver | **10 deterministic tests PASS** |
| Historical Phase 1 coverage | **22 synthetic schema cases + 8 bounded-transfer tests PASS** inside the integrated suite |
| Cartesian stability regression | **15,361 stress cases / 11,265 comparisons; zero failures**, existing tolerance unchanged |
| Compiler and linkage | Every compile command uses the dedicated conda compiler and `-std=c++20`; eight executables resolve ROOT, libstdc++ and libgcc to that environment |

The fresh integrated build is `/home/btu/build/atlas_phase5_background_20261012`. Its JUnit, linkage, environment and source-identity receipts are hashed in [phase5_quality_gates.json](../metadata/phase5_quality_gates.json). Source hashes were captured before compilation and checked after CTest. Existing ROOT/driver regressions use synthetic fixtures and can produce temporary synthetic figures; they do not constitute physical study plots or user figure approval.

## Source and weight audit

[Official CERN MC record 93922](https://opendata.cern.ch/record/93922) confirms the exact 302521 filename, **110,755,804 bytes**, published **adler32:b43248ea**, release/file/version/bucket UUIDs and public URI. Six DSID joins, including excluded 302520 and alternative 364352, are recorded in [phase5_dsid_manifest.csv](../metadata/phase5_dsid_manifest.csv). Detailed source URLs, local response SHA-256 and version scopes are in [phase5_mc_source_audit.md](phase5_mc_source_audit.md).

The preserved official [v1.0.0 metadata table](https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/extras%2Fmetadata.csv/raw?ref=v1.0.0) documents Pythia8/EvtGen direct diphoton 302521/e4045 with **100 < generated mγγ < 160 GeV**, two photons **pT > 20 GeV**, sigma **18.282 pb**, filter efficiency **0.44191**, k=1 and candidate generated N/signed sumW/sumW2=642,000. The later [v1.0.0 release](https://zenodo.org/records/15791092) postdates FEB2025. Exact production/configuration applicability is **UNKNOWN**; these values are not applied to normalize the released tree. Generator/reconstruction migration and filter-edge coverage remain unmeasured; no unsupported extrapolation or mass-slice stitching is done.

The new weight audit reuses **29,700 frozen reconstructed-cache rows** and matches every historical generator moment and eleven scalar-branch observations exactly. It adds bounded SumAbsW, Neff and cancellation diagnostics, never a generated denominator:

| DSID | Negative generator weights | Negative BTAG scalars | PILEUP zeros | Bounded SumAbsW | Signed Neff |
| --- | ---: | ---: | ---: | ---: | ---: |
| 343981 | 14 | 18 | 89 | 282008.7381362915 | 9844.079191919192 |
| 346214 | 15 | 75 | 93 | 37200.29511141777 | 9816.746576305852 |
| 423103 | 0 | 103 | 98 | 9900 | 9900 |

The input range is **[100,10000)** for each MC. Negative generator weights and negative correction scalars are separate phenomena. No sign is removed, no unexplained correction is replaced by unity/zero/absolute value, and no SF is applied. Native 423103 filter efficiency **0.000039** and later table **0.0000393** both remain visible. H-sample metadata sums show Float32-consistent rounding but unresolved production/aggregation scope. Extra decay branching factors are not introduced. See [normalization contract](phase5_normalization_contract.md), [weight evidence](../metadata/phase5_weight_evidence.csv) and [weight observations](../metadata/phase5_weight_observations.json).

## Transfer outcome and preserved accounting

The user's authorization covers only the pinned 302521 file, a **128 MiB** Phase 5 allocation and the historical **256 MiB** cumulative ceiling. Four routes failed: WSL CA-handshake timeout; Windows verified HTTPS metadata/HEAD followed by HTTP storage reset; WSL public HTTP storage timeout; and verified HTTPS at the same scoped storage endpoint followed by reset. HTTP attempts carry no TLS claim. No certificate verification was disabled and no remote ROOT reader was used.

The unchanged original receipt `.local/phase5_access_20261012/access.json` has raw-byte SHA-256 `be764a03f335e9cf238b9e8f1f67a8fd82bfa07aeb2ae145f490e8d6547ab134`. The published [phase5_transfer_ledger.json](../metadata/phase5_transfer_ledger.json) is its LF-canonical text copy, SHA-256 `9e8a88178bc2d2f5717d71b1e7f9d59f07eb46be0e96c185c6e2ba58997d5ece`; JSON content equality is verified. Git's CRLF-to-LF conversion changes the byte hash, not the recorded requests or accounting:

| Quantity | Bytes / status |
| --- | ---: |
| Transfer route requests | 16 |
| Transfer response bodies | 15,471; all CA certificates |
| ROOT payload / published local ROOT file | **0 / none** |
| Transfer charge, bodies plus 64 KiB per attempt | 1,064,047 |
| Metadata/documentation charge | 747,003 |
| Total Phase 5 charge | 1,811,050 / 134,217,728 |
| Preserved historical plus Phase 5 charge | 79,945,072 / 268,435,456 |

This is application-consumed response-body accounting plus reserves, **not measured wire traffic**. Browser traffic bytes are unavailable. The HEAD size/ETag match is a header check, not a computed file checksum PASS. No 302521 final or partial ROOT file exists. The transfer harness was subsequently hardened and verified with fake-response/child tests; that does not imply a later successful physical transfer. The actual failed receipt is not rewritten to describe the hardened harness. There is no further physical retry in this task.

## DATA exposure and shape feasibility

[CERN DATA record 93915](https://opendata.cern.ch/record/93915) identifies 2015 Period D at 13 TeV. The exact five exposure scopes—full period, applied GRL, trigger-effective, released skim and inspected **[100,63195)**—remain **UNKNOWN**. No luminosity is inferred from the event fraction or assumed to be 36 or 308 fb⁻¹. Native schema inventory has no luminosity-block, prescale or livetime branch.

The later converter's aggregate `trigP` single-photon OR and listed GRL filenames do not establish exact FEB2025 trigger/GRL application, diphoton efficiency or exposure. The v1.0.0 luminosity table URL is identified but its fresh request failed at DNS with zero body bytes; no uninspected table content becomes a numerical value. See [luminosity audit](phase5_luminosity_audit.md) and [13-row luminosity evidence](../metadata/phase5_luminosity_evidence.csv).

The reusable shape module implements separate raw-unweighted and nominal-generator-weighted modes, signed area, variable bin widths/flows, SumW/SumW2/SumAbsW/Neff and the full first-order normalization covariance. Physical application defaults off and UNKNOWN conventions are rejected. Only analytical synthetic shapes were executed. Trigger/calibration differences, incomplete background mixture, generator-filter migration, sample overlap, corrections and selection/unit provenance prevent a scientifically interpretable physical DATA/MC comparison. The assessed selection reuses the exact Phase 3 cuts; inclusive dijets are not identified b jets. See [shape comparison report](phase5_shape_comparison.md).

## Descriptive CR/VR inventory, not physical closure

The study domain is **105≤mγγ≤160 GeV**. A is |Δηγγ|<1 and B is |Δηγγ|≥1. CR=A sidebands **[105,120)∪[130,160]**; VR=B same sidebands; prospective SR=A **[120,130)**; B's central window stays reserved. These are explicit study choices, not official ATLAS regions. Disjoint events do not establish independence of mass, the split variable or nuisances. DATA has already been inspected; no retrospective blinding claim is made.

The fresh C++ inventory reads complete preserved derived CSV caches, uses **C5 plus separate C7–C9 jet predicates**, and keeps events outside C6 visible. It does not reopen physical ROOT trees or recompute four-vectors. Unit status stays **PROVISIONAL**; MC raw-weight semantics stay **UNKNOWN**. Eight disjoint rows conserve every input, while five diagnostic population rows overlap and must not be summed.

| Sample | Input | C5 + jets | CR | VR | Prospective SR | Reserved | Outside domain | C9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DATA | 63095 | 9037 | 443 | 931 | 100 | 215 | 7348 | **1689** |
| 343981 | 9900 | 1127 | 14 | 18 | 673 | 420 | 2 | **1125** |
| 346214 | 9900 | 1440 | 32 | 24 | 893 | 470 | 21 | **1419** |
| 423103 | 9900 | 2215 | 296 | 182 | 70 | 40 | 1627 | **588** |

All C9 counts equal historical V2 cutflows. The remaining input categories are C5 failure, jet failure and invalid input, including the **37 preserved invalid DATA rows**. The published [occupancy CSV](../metadata/phase5_region_occupancy.csv) and quality-gate hashes bind the actual cache/output identities. Per-event ledgers stay local under `outputs/phase5_v1/regions/`. No physical TF or cross-sample ratio is computed from this table; no background dominance or signal-contamination assumption is validated.

Synthetic TF, signed cancellation, contamination subtraction, covariance/nuisance propagation, overlap rejection, held-out identities and boundary sensitivity pass. Physical APIs for TF/prediction deliberately reject physical scope. Actual continuum coverage, mass/split correlations, compatible triggers/corrections, mixture composition and signal contamination remain blockers. See [control-region feasibility](phase5_control_region_feasibility.md).

## Acceptance gates

| Gate | State | Exact supported scope |
| --- | --- | --- |
| A | PASS | Phase 4 source, results, input/selection identity preserved; baseline and integrated numerical regressions executed |
| B | PASS | Current official DSID/release/file/process identity; exact producer/configuration applicability remains UNKNOWN |
| C | UNKNOWN | Exact nominal generator-weight convention |
| D | UNKNOWN | Complete signed pre-skim denominator/SumAbsW and processing accounting |
| E | UNKNOWN | Exact continuum production/filter implementation and physical edge coverage; later documented phase space only |
| F | UNKNOWN | Applicable DATA exposure across all five scopes |
| G | PASS | Compatibility **assessed** and differences documented; calibrated DATA/MC compatibility is not established |
| H | BLOCKED | Scientifically interpretable physical weighted shape comparison |
| I | BLOCKED | Physical CR/VR background model and closure |
| J | PASS | Executed 23/23 plus Step 1 3/3; compiler/linkage, source/report/input identity and metadata joins |

No gate is FAIL in the final execution. Missing physics inputs are not manufactured into a PASS. The old Phase 4 failure and an intermediate new synthetic guard failure remain preserved separately from the corrected final source tests.

## Reproduction and Git/figure policy

Use the existing environment and **new** output/build paths to preserve earlier evidence:

```bash
cd /mnt/c/HH
source /home/btu/miniforge3/etc/profile.d/conda.sh
conda activate atlas-hh-root
bash scripts/validate_step1.sh /home/btu/build/NEW_phase5_step1
bash scripts/validate_phase5.sh /home/btu/build/NEW_phase5_complete
python -B scripts/audit_phase5_weights.py --csv outputs/NEW_phase5_weights.csv --json outputs/NEW_phase5_weights.json

app=/home/btu/build/NEW_phase5_complete/phase5_region_inventory
config=metadata/phase3_selection_config.ini
"$app" outputs/phase4_numerical_v2_20261012/DATA93915/phase2/events.csv "$config" outputs/NEW_phase5_regions/DATA DATA 100 63195 PROVISIONAL
for sample in 343981 346214 423103; do
  "$app" "outputs/phase4_numerical_v2_20261012/$sample/reconstruction/events.csv" "$config" "outputs/NEW_phase5_regions/$sample" "$sample" 100 10000 PROVISIONAL
done
python -B scripts/freeze_phase5_baseline.py metadata/phase5_baseline_preservation.json --verify
```

Reproduction requires the explicitly approved local input/evidence caches; Git contains source and compact evidence, not the ROOT datasets or local per-event ledgers. Failed-transfer accounting must be carried forward on any future retry; do not reset or erase it. The Phase 5 feature is proposed in a new stacked PR without merging a dependency. Only explicit source/test/report/metadata paths are staged. Both staged paths and all outgoing intermediate commit payloads are inspected before push. No unapproved PDF/PNG/ROOT dataset is included. Previous local figure drafts retain **LOCAL_DRAFT** status; test or QA success is not user acceptance.

The next physical work is to resolve scoped CERN storage access, validate the exact 302521 ROOT schema and generation/configuration/weight bookkeeping, recover applicable run/LB/GRL/trigger/skim exposure, and establish corrections/overlap/phase-space coverage. Then design a defensible held-out closure study. Missing exposure does not block independent MC provenance work, but no absolute background prediction or HH fit follows from this engineering PASS.

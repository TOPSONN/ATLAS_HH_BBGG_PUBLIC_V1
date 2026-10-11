# ATLAS publication figure alignment V2 validation

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1
TASK: ATLAS_PUBLICATION_FIGURE_ALIGNMENT_V2
STATUS: PASS_PUBLICATION_STYLE; feature branch ready for review, pending integration
Verified: 2026-10-11 (Asia/Taipei)

V2 fixes the shared native ROOT implementation rather than editing image pixels.
It replaces large diagnostic headers/footers with three inside-pad lines and
supplies all seven Phase 2 and four Phase 3 individual vector PDFs, previews,
native ROOT objects, metadata and complete captions. All V1 artifacts and
scientific evidence remain historical outputs. No physics reconstruction,
selection, statistical definition, signal model or fitted curve was added.

## Actual environment and ROOT style

| Property | Verified value |
|---|---|
| Environment | Existing Ubuntu WSL atlas-hh-root |
| ROOT / ROOT C++ standard | 6.40.04 / 20 |
| Actual compiler | GNU 15.3.0 |
| Compiler path | /home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++ |
| CMake / Ninja | 4.4.4 / 1.13.2 |
| Build commands | All 20 translation units use conda compiler and -std=c++20 |
| Linkage | ROOT Core/Graf/Gpad, libstdc++ and libgcc resolved inside the same environment; no missing libraries |
| Style initialization | Installed built-in ATLAS TStyle; SetStyle("ATLAS"), ForceStyle(), documented overrides |
| Canvas / margins | Actual 800x600; left .16, right .05, top .05, bottom .16 |
| Fonts / sizes | ROOT 42; title .05, label .045, annotations .04/.045 |
| Markers / axes | Black style20 size.9; four-sided inward ticks; no title/stat/fit boxes |

## Publication reference and visual comparison

User reference: [CDS 2937468](https://cds.cern.ch/record/2937468/plots). CDS
presented an access challenge. The same-publication
[official ATLAS HIGP-2025-10 page](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/)
provided [Figure 2](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/fig_02.pdf)
and [Figure 3a](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/fig_03a.pdf)
native PDFs, plus Figure 4a PNG, independently inspected as layout references.
Figure 2 and Figure 3a were rendered with Poppler. Their compact margins,
inside-pad labels, sans-serif/math typography and black point/tick treatment
guided alignment. Figure 3a comparison does not authorize copying its MC stack
or ratio panel; Figure 4a does not authorize a likelihood or limit calculation.
No reference data, luminosity, curves, signal claims or official labels copied.

V2 uses ROOT TCanvas native PDF export; every PDF has zero embedded raster
image objects. Complete PDF renders were individually inspected by the primary
agent and independently by a second agent. PNG previews were also decoded.
The three annotation lines are inside low-occupancy corners. No measured
point/error bar is covered; axis titles, exponent multipliers and math glyphs
are readable. Large diagnostic headers/footers and single-series legends are
absent. Rendering/preview tool display omissions were independently resolved
against the full image pixels and PDF text; source outputs were not cropped.

| Plot | Automated / visual QA | Specific visual observation |
|---|---|---|
| phase2/deltaR_gg | PASS / PASS | Upper-left labels clear of the angular peak and counting intervals; exponent and DeltaR readable. |
| phase2/jet_eta | PASS / PASS | Upper-right labels above the broad object distribution; exponent and jet superscript readable. |
| phase2/jet_pt | PASS / PASS | Upper-right labels clear of the low-pT object peak; full 0-300 range retained. |
| phase2/m_gg | PASS / PASS | Upper-left labels clear of first-bin and diphoton peak errors; full 0-400 GeV range retained. |
| phase2/m_jj | PASS / PASS | Upper-right labels clear of the dijet peak/errors; full 0-800 GeV range retained. |
| phase2/photon_eta | PASS / PASS | Upper-left labels above the broad object distribution with modest headroom; photon superscript readable. |
| phase2/photon_pt | PASS / PASS | Upper-right labels clear of object peak; photon pT and exponent readable. |
| phase3/jet_pt_selected | PASS / PASS | Upper-right labels clear of selected object peak; visible object counts have no invented errors. |
| phase3/m_gg_preselection | PASS / PASS | Upper-right labels above local counting intervals; selected 100-170 GeV range and zero-bin upper bars retained. |
| phase3/m_jj_preselection | PASS / PASS | Upper-right labels clear of dijet peak/counting intervals; no header/footer or clipped axes. |
| phase3/photon_pt_selected | PASS / PASS | Upper-right labels clear of selected photon peak; no invented object-count error bars. |

## Actual regression and output gates

Final enabled CTest suite: **15/15 PASS**, after the last validator change.
The final direct build, CTest and output validation commands exited zero.

| Suite | Actual outcome |
|---|---|
| Step 1 | ROOT I/O, RDataFrame and RooFit/RooStats: 3/3 PASS; no fit performed |
| Phase 1 | 22 synthetic schema cases and 8 bounded-transfer cases PASS |
| Phase 2 | 1,033 kinematic assertions / 500 seeded pairs; 12 reader cases; 11 driver cases; 7 unit-gate cases PASS |
| Phase 3 | 37 selection boundary/configuration cases and 9 driver cases PASS |
| Plotting | 4 CTest tests PASS; 29 style/metadata cases; TH1D/TH2D/TGraphErrors export; 32 PDF contract cases |
| Statistical display | Saved Poisson intervals independently checked against native TH1 kPoisson, including zero counts |
| Production outputs | 11/11 PDFs readable/vector; PNG decoded; caption/JSON/ROOT identical; visual QA PASS |

Previous rejection coverage is preserved. New gates reject wrong dimensions,
margins, fonts, marker metadata, label positions, diagnostic canvas text and
missing/inconsistent captions. A demonstrated 24-byte truncated PNG formerly
passed header-only checks; actual ROOT PNG decoding and a negative regression
now reject it. Automated bbox checks establish containment rather than proving
all data-label separation; mandatory visual QA supplies that current-output check.
GitHub has **NO_CHECKS**, which is not CI PASS.

Logs: `.local/atlas_publication_v2/ctest_delivery.log`, `quality_delivery.log`,
`numeric_comparison.json`, `historical_preservation.json`, `toolchain.json`.
Build: `/home/btu/build/atlas_publication_v2_20261011`.

## Exact numerical and historical preservation

The [read-only comparator](../scripts/compare_plot_numerics.py) compared all
eleven V1/V2 native histogram/display pairs with **IEEE-754 exact identity**,
without tolerance. It checked every edge, bin content, source error, Sumw2,
flows, entries, statistics/moments, effective entries and every display point
and asymmetric error. All prior scientific metadata fields agree exactly.
V1 ROOT/sidecar identity and V2 ROOT/sidecar identity are checked independently.
Full audit and provenance hashes are in
[atlas_publication_v2_validation.json](../metadata/atlas_publication_v2_validation.json).

| Histogram | Bins / native range | Entries | Underflow / overflow |
|---|---|---|---|
| phase2/deltaR_gg | 60 / 0-6 | 63058 | 0 / 0 |
| phase2/jet_eta | 60 / -5-5 | 64556 | 0 / 0 |
| phase2/jet_pt | 60 / 0-300 | 64556 | 0 / 377 |
| phase2/m_gg | 80 / 0-400 | 63058 | 0 / 647 |
| phase2/m_jj | 80 / 0-800 | 17191 | 0 / 86 |
| phase2/photon_eta | 50 / -2.5-2.5 | 126586 | 0 / 0 |
| phase2/photon_pt | 60 / 0-300 | 126586 | 0 / 188 |
| phase3/jet_pt_selected | 60 / 0-300 | 3378 | 0 / 18 |
| phase3/m_gg_preselection | 70 / 100-170 | 1689 | 0 / 0 |
| phase3/m_jj_preselection | 80 / 0-800 | 1689 | 0 / 9 |
| phase3/photon_pt_selected | 60 / 0-300 | 3378 | 0 / 0 |

The original Phase 2 source ROOT object, derived CSV cache and selection
configuration remain checksum-pinned. No raw collision entry was reread and
no remote dataset byte was downloaded. Phase 3 cutflow/optional-flag/inventory
CSVs remain byte-identical. C0 through C9 remains:
`63095, 63058, 63058, 53978, 53978, 51136, 12564, 2842, 1689, 1689`.
Optional raw tight-ID / tight-ID-plus-isolation counts remain 175 / 48.
Object plots retain no counting errors; event plots retain the existing central
68.27% Garwood intervals. Original histogram errors are preserved in both.

Historical preservation audit against `5962329a97f68dadddc32c18a8e1b5bdf220a607`:

| Historical gate | Actual result |
|---|---|
| Baseline tracked note/report/metadata files | 73/73 byte-identical |
| Original Phase 2/3/V1 manifest entries | 75/75 size and SHA-256 match (13/15/47 rows) |
| Phase 3 CSV comparisons across original/V1/V2 | 9/9 byte-identical |
| Failures | 0 |


## Artifacts, captions and scientific limits

Current tracked native PDF/PNG/JSON/caption exports:
`reports/figures/atlas_v2/phase2/` and `reports/figures/atlas_v2/phase3/`.
Eleven native ROOT files remain ignored under
`outputs/atlas_publication_v2_20261011/phase2|phase3/`. The
[58-row manifest](../metadata/atlas_publication_v2_artifact_manifest.csv)
records 44 tracked exports, 11 ignored native object files and three unchanged
pinned numerical inputs/configuration. Published copies are byte-identical
to native exports. Fresh clones require the pinned local inputs for reproduction.
All 44 tracked export Git blobs match manifest size and SHA-256. The 57-file
staged scope passed credential and unintended-binary checks, with no deletions;
the largest staged file is 117,200 bytes. No collision/native ROOT file is staged.
Prior PNGs/PDFs/reports/manifests are unchanged historical evidence.
Permanent [AGENTS instructions](../AGENTS.md) and
[plotting contract](../docs/ATLAS_PLOTTING_STANDARD.md) enforce V2 future gates.

Phase 0 remains **PARTIAL**; units remain **PROVISIONAL**. B-tagging remains
**BLOCKED**, trigger **UNKNOWN_NOT_APPLIED**, source-production matching
**UNKNOWN**, and usable luminosity/MC normalization/systematics unvalidated.
No integrated luminosity is displayed. The inclusive full-range mgg is not
an HH signal-region study. The optional additional 105-160 GeV view is omitted.
Style PASS applies to these eleven outputs, not official analysis reproduction
or automatic approval of future plot types. PR4, PR5 and PR6 remain OPEN.
No PR merge, branch deletion, force-push or shared-history rewrite performed.

## Complete per-figure captions

The following exact caption text is also present in each JSON sidecar,
native ROOT `atlas_plot_caption` and separate `.caption.md` file.

### phase2/deltaR_gg

```text
Figure: deltaR_gg. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 63058. Entries [100,63195).
Selection: Valid kinematics; leading photon pair.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: #Delta R_{#gamma#gamma} (dimensionless). Y axis: Events / bin.
Native binning: 60 x bins over [0,6). Entries: 63058.
Underflow: 0. Overflow: 0. Original bin errors preserved.
Error bars: central 68.27% Garwood Poisson counting intervals; no systematics.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase2/jet_eta

```text
Figure: jet_eta. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 63058. Entries [100,63195).
Selection: Valid kinematics; all inclusive jet objects.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: #eta^{jet}. Y axis: Objects / bin.
Native binning: 60 x bins over [-5,5). Entries: 64556.
Underflow: 0. Overflow: 0. Original bin errors preserved.
Object-count markers without error bars; within-event correlations are not modeled.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase2/jet_pt

```text
Figure: jet_pt. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 63058. Entries [100,63195).
Selection: Valid kinematics; all inclusive jet objects.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: p_{T}^{jet} [GeV]. Y axis: Objects / 5 GeV.
Native binning: 60 x bins over [0,300). Entries: 64556.
Underflow: 0. Overflow: 377. Original bin errors preserved.
Object-count markers without error bars; within-event correlations are not modeled.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase2/m_gg

```text
Figure: m_gg. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 63058. Entries [100,63195).
Selection: Valid kinematics; leading photon pair.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: m_{#gamma#gamma} [GeV]. Y axis: Events / 5 GeV.
Native binning: 80 x bins over [0,400). Entries: 63058.
Underflow: 0. Overflow: 647. Original bin errors preserved.
Error bars: central 68.27% Garwood Poisson counting intervals; no systematics.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase2/m_jj

```text
Figure: m_jj. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 17191. Entries [100,63195).
Selection: Valid kinematics; leading inclusive jet pair.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: m_{jj} [GeV]. Y axis: Events / 10 GeV.
Native binning: 80 x bins over [0,800). Entries: 17191.
Underflow: 0. Overflow: 86. Original bin errors preserved.
Error bars: central 68.27% Garwood Poisson counting intervals; no systematics.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase2/photon_eta

```text
Figure: photon_eta. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 63058. Entries [100,63195).
Selection: Valid kinematics; all photon objects.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: #eta^{#gamma}. Y axis: Objects / bin.
Native binning: 50 x bins over [-2.5,2.5). Entries: 126586.
Underflow: 0. Overflow: 0. Original bin errors preserved.
Object-count markers without error bars; within-event correlations are not modeled.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase2/photon_pt

```text
Figure: photon_pt. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 63058. Entries [100,63195).
Selection: Valid kinematics; all photon objects.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: p_{T}^{#gamma} [GeV]. Y axis: Objects / 5 GeV.
Native binning: 60 x bins over [0,300). Entries: 126586.
Underflow: 0. Overflow: 188. Original bin errors preserved.
Object-count markers without error bars; within-event correlations are not modeled.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase3/jet_pt_selected

```text
Figure: jet_pt_selected. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 1689. Entries [100,63195).
Selection: study-preselection-v1; C9; leading photons and inclusive jets.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: p_{T}^{jet} [GeV]. Y axis: Objects / 5 GeV.
Native binning: 60 x bins over [0,300). Entries: 3378.
Underflow: 0. Overflow: 18. Original bin errors preserved.
Object-count markers without error bars; within-event correlations are not modeled.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase3/m_gg_preselection

```text
Figure: m_gg_preselection. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 1689. Entries [100,63195).
Selection: study-preselection-v1; C9; leading photons and inclusive jets.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: m_{#gamma#gamma} [GeV]. Y axis: Events / 1 GeV.
Native binning: 70 x bins over [100,170). Entries: 1689.
Underflow: 0. Overflow: 0. Original bin errors preserved.
Error bars: central 68.27% Garwood Poisson counting intervals; no systematics.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase3/m_jj_preselection

```text
Figure: m_jj_preselection. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 1689. Entries [100,63195).
Selection: study-preselection-v1; C9; leading photons and inclusive jets.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: m_{jj} [GeV]. Y axis: Events / 10 GeV.
Native binning: 80 x bins over [0,800). Entries: 1689.
Underflow: 0. Overflow: 9. Original bin errors preserved.
Error bars: central 68.27% Garwood Poisson counting intervals; no systematics.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

### phase3/photon_pt_selected

```text
Figure: photon_pt_selected. Sample: DATA.
ATLAS Open Data. Independent exploratory analysis.
Record: 93915. Period: 2015 periodD.
Collision energy: sqrt(s) = 13 TeV.
Inspected: 63095. Accepted: 1689. Entries [100,63195).
Selection: study-preselection-v1; C9; leading photons and inclusive jets.
Units: PROVISIONAL. Weighting: Raw unweighted counts.
Integrated luminosity is not shown; usable luminosity is not validated for this sample.
X axis: p_{T}^{#gamma} [GeV]. Y axis: Objects / 5 GeV.
Native binning: 60 x bins over [0,300). Entries: 3378.
Underflow: 0. Overflow: 0. Original bin errors preserved.
Object-count markers without error bars; within-event correlations are not modeled.
ATLAS Open Data exploratory diagnostic;
raw unweighted GamGam skim;
not the official ATLAS HH analysis.
```

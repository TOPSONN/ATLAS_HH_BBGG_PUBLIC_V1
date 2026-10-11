# ATLAS ROOT plotting standard validation

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1

TASK: PROJECT_WIDE_ATLAS_ROOT_PLOTTING_STANDARD_V1

STATUS: PASS; feature branch ready for review, pending integration
Verified: 2026-10-11 (Asia/Taipei)

This change establishes the permanent native ROOT plotting contract
[atlas-root-plot-v1](../docs/ATLAS_PLOTTING_STANDARD.md) and supplies seven Phase 2
and four Phase 3 individual vector PDFs, PNG previews, native ROOT objects and
required metadata. It changes presentation and output validation while retaining
the existing numerical definitions and scientific limitations.

## Environment and backend

| Property | Actual verified value |
|---|---|
| Platform / environment | Ubuntu WSL / existing atlas-hh-root |
| ROOT | 6.40.04 |
| C++ | 20; required, extensions off |
| CMake | 4.4.4 |
| Compiler | GNU 15.3.0 |
| Compiler path | /home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++ |
| ROOT library directory | /home/btu/miniforge3/envs/atlas-hh-root/lib |
| Compile commands | All 20 translation units use the conda compiler and -std=c++20 |
| Linkage | ROOT Core/Graf/Gpad, libstdc++ and libgcc resolve in that environment; no missing libraries |
| Style backend | Installed ROOT built-in ATLAS TStyle |
| Initialization | gROOT->SetStyle("ATLAS"); gROOT->ForceStyle() |

The shared [module](../include/AtlasPlotting.h) configures white canvas/pad,
font 42, four-side ticks, black axes, no title/stat/fit boxes, and consistent
markers, lines and borderless legends. PDF and PNG are exported directly by
ROOT TCanvas::SaveAs. The PDF check found no embedded raster images in any of
the eleven final PDFs.

## Actual automated tests

The final complete enabled CTest suite executed successfully: **15/15 PASS**
after all code/test changes, including the unknown-input-provenance rejection.
An earlier focused plotting verification also passed **4/4**, and the final
PDF gate executed successfully against all eleven production outputs.

| Suite | Actual result / cases |
|---|---|
| Step 1 ROOT I/O, RDataFrame, RooFit/RooStats | 3/3 PASS; RooFit object/ModelConfig smoke test, no fit performed |
| Phase 1 schema and transfer | 2/2 additional tests PASS; 22 synthetic schema cases, 8 bounded transfer cases |
| Phase 2 | 4/4 additional tests PASS; 1,033 numerical assertions / 500 seeded pairs, 12 local-reader cases, 11 driver cases, 7 unit-gate cases |
| Phase 3 | 2/2 additional tests PASS; 37 selection boundary cases, 9 driver cases |
| Plotting | 4/4 PASS; 21 style/metadata cases; native TH1D, TH2D, TGraphErrors output; 13 PDF gate cases |
| Counting intervals | Saved TGraphAsymmErrors agrees with native TH1 kPoisson for every synthetic bin, including zero counts, within 1e-7 |
| Export refusals | Existing output, incorrect declared GeV bin width and noncompliant style are rejected before export |
| Final figure quality | 11/11 automated PASS |

The 13 PDF gate cases include missing/invalid PDF, missing record, UNKNOWN units,
unvalidated or invalid luminosity, fractional counts, negative source entry,
invalid energy, prohibited collaboration-status labels, invisible metadata,
missing native ROOT objects and blank renders. No previous assertion was
removed or relaxed.

Executed local logs are retained under
.local/atlas_plotting_v1_20261010/: ctest_delivery_final.log,
plotting_ctest_final.log, pdf_quality_final.log and closure_final.log.
The build is /home/btu/build/atlas_plotting_v1_20261010.
Machine-readable results are in
[atlas_plotting_validation.json](../metadata/atlas_plotting_validation.json).

## Numerical preservation

All historical tracked files except the seven intended source/build/README/test
edits were compared byte-for-byte against the starting Phase 3 commit
830af3031da80c1c5f3c01ccec22e3619e95f41f.
This includes **37 unchanged metadata/note/report/figure files**. All **28 rows**
in the existing Phase 2/3 artifact manifests still match their file sizes and
SHA-256 values, including ignored original source objects and derived cache.

Phase 2 PDFs were generated from the existing native histograms in
outputs/phase2_20261010T092242Z/phase2_diagnostics.root, whose SHA-256 remains
78729eb927974165a2251c3ca26f93f63af70bf6ca8fbee2dfe69d6306bbdcd7.
For every one of the seven newly saved histograms, the class, all bin edges,
contents and original errors including underflow/overflow, entries and four
statistics moments **exactly match** the original ROOT histogram.

The earlier Phase 3 run did not retain its histogram objects. Its four
histograms were recreated by the existing C++ selection driver from the exact
derived event cache and unchanged configuration. The cache SHA-256 is
a50c50eda011ffae6aa224dcab02a34b1e5a3a430dd427ee6397274f9afef764;
the selection configuration SHA-256 is
77d57cd6fa204aad5a24031ac925c4e20e121b8aee35148cc29b522b39cf5751.
An independent cache selector verified all four bin definitions, contents,
errors, entries and moments, including underflow and overflow, against the
newly saved native objects. No data was inferred from PNG pixels.

The new Phase 3 cutflow, optional-photon-flag CSV and histogram inventory are
byte-identical to the original tracked versions. C0 through C9 remain:

63095, 63058, 63058, 53978, 53978, 51136, 12564, 2842, 1689, 1689.

Optional raw tight-ID and tight-ID-plus-tight-isolation counts remain 175 and
48. The selected mjj overflow is 9; selected jet-pT overflow is 18.
No raw collision ROOT entry was read and no remote dataset byte was downloaded
during this plotting regeneration.

## Final PDF and visual checks

All eleven final PDFs exist, are nonempty, are readable one-page PDFs, and
contain vector paths/text without raster image objects. Poppler reported an
A4 MediaBox (595 x 842 points), a 567 x 713 point CropBox and 90-degree page
rotation; the effective visible page is 713 x 567 points. The aspect ratio
agrees with the actual 1096 x 872 pixel ROOT canvas/PNG preview. This is ROOT's
native PDF page encoding, rather than a clipped plot.

Helvetica-compatible font 42 text and Symbol glyphs rendered correctly.
Required metadata was found using pdftotext restricted to the CropBox.
Both original page and final CropBox renders were generated with Poppler.
**Every final CropBox render was individually inspected visually** for axis
titles, Greek glyphs, labels, legend placement, clipping, overlap and nonblank
content. All eleven passed. Automated checks and visual inspection are
recorded separately per figure in the validation JSON. These are bounded
inspections of the delivered PDFs; they do not validate future plots.

| Phase | Final plot | Visual result |
|---|---|---|
| 2 | [m_gg.pdf](figures/atlas_v1/phase2/m_gg.pdf) | PASS |
| 2 | [m_jj.pdf](figures/atlas_v1/phase2/m_jj.pdf) | PASS |
| 2 | [photon_pt.pdf](figures/atlas_v1/phase2/photon_pt.pdf) | PASS |
| 2 | [photon_eta.pdf](figures/atlas_v1/phase2/photon_eta.pdf) | PASS |
| 2 | [jet_pt.pdf](figures/atlas_v1/phase2/jet_pt.pdf) | PASS |
| 2 | [jet_eta.pdf](figures/atlas_v1/phase2/jet_eta.pdf) | PASS |
| 2 | [deltaR_gg.pdf](figures/atlas_v1/phase2/deltaR_gg.pdf) | PASS |
| 3 | [m_gg_preselection.pdf](figures/atlas_v1/phase3/m_gg_preselection.pdf) | PASS |
| 3 | [m_jj_preselection.pdf](figures/atlas_v1/phase3/m_jj_preselection.pdf) | PASS |
| 3 | [photon_pt_selected.pdf](figures/atlas_v1/phase3/photon_pt_selected.pdf) | PASS |
| 3 | [jet_pt_selected.pdf](figures/atlas_v1/phase3/jet_pt_selected.pdf) | PASS |

Event-count distributions show black collision-data markers with central
68.27% Garwood Poisson counting intervals. Multiple-object distributions show
black markers without error bars because within-event correlations are not
modeled. No efficiency, systematic, MC-normalization or HH-inference uncertainty
is claimed. Histogram source errors are preserved; display intervals are saved
as separate native TGraphAsymmErrors.

All plots show ATLAS Open Data, Independent exploratory analysis, 13 TeV,
2015 periodD, record 93915, inspected/accepted counts, source range,
selection, PROVISIONAL units and Raw unweighted counts. No luminosity is shown.
The mjj Phase 2 label correctly states the 17,191 eligible leading jet pairs;
other Phase 2 figures report 63,058 valid events and Phase 3 reports 1,689
selected events. All inspect the same bounded 63,095-entry cache range.

## Artifact retention and reproducibility

The [47-row manifest](../metadata/atlas_plotting_artifact_manifest.csv) records
paths, actual file sizes, hashes and storage status for the eleven PDF/PNG/
metadata sets, eleven native ROOT files and three pinned numerical inputs.
Tracked current PDFs/PNGs/sidecars are byte-identical copies of native ROOT
exports under reports/figures/atlas_v1/phase2/ and phase3/.
Generated native objects remain in the ignored
outputs/atlas_plotting_v1_20261010/phase2/ and phase3/ directories.

Historical PNGs/reports/manifests remain at their original paths. They are not
retrospectively claimed to have passed the new PDF contract. Fresh clones need
the exact pinned source histograms/cache to reproduce the current plots;
those ignored files are retained locally. Validate the complete generated
output directory, where each sidecar has its adjacent native ROOT file.
The tracked PDF/preview directory alone is not a complete input to that gate.

Reproduction commands and future MC/fit/variable-bin extension rules are in
the plotting standard. ROOT/PDF timestamps may change binary hashes on
reproduction; bin values, configuration and scientific interpretation must
remain unchanged. The manifest identifies this actual delivered run.

## Scientific and integration limits

Scientific conclusions are unchanged: Phase 0 remains PARTIAL, source production
matching remains UNKNOWN, units remain PROVISIONAL, b-tagging is BLOCKED, and the
official diphoton trigger remains UNKNOWN_NOT_APPLIED. Luminosity, MC
normalization, calibration and systematic models are not validated by styling.
The raw-count convenience renderer requires a tested extension for weighted MC,
density normalization, stacks, ratios, fits and uncertainty bands.

The plotting branch is codex/atlas-root-plotting-standard, based on the unchanged
Phase 3 commit above. Its PR targets codex/phase3-exploratory-preselection so
that reviewed Phase 2/3 history and dependency order are preserved. PR #4 and
PR #5 remain open with their original heads/base branches. No PR is merged by
this task. GitHub NO_CHECKS is not CI PASS; the results here are executed local
tests. Permanent adoption on main follows the sequential integration workflow.
Delivery commit and PR URL are supplied in the final report.

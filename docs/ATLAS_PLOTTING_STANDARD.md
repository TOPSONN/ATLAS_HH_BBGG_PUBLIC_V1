# ATLAS-style native ROOT plotting standard

Contract: **atlas-root-plot-v1**, mandatory for all current and future physics
plots. Adopted 2026-10-11 (Asia/Taipei). It applies to reconstruction, selection,
MC comparisons, fit/statistical graphics and systematic/validation studies.
The permanent instruction is in [AGENTS.md](../AGENTS.md).

## Backend and shared API

Use **ROOT 6.40.04 / C++20** in the existing Ubuntu WSL `atlas-hh-root` environment.
`atlas_plotting` uses ROOT's built-in `ATLAS` TStyle, checked in the installed
runtime, initialized with `gROOT->SetStyle("ATLAS")` and `gROOT->ForceStyle()`.
No external style macro is vendored. ROOT documents the backend in
[TStyle](https://root.cern.ch/doc/master/classTStyle.html). Style provenance is
the ROOT release itself; the online manual is current documentation, not proof
of a different installed version.

[AtlasPlotting.h](../include/AtlasPlotting.h) provides `ApplyAtlasPlotStyle`,
`ValidatePlotMetadata`, `DrawOpenDataLabel`, `ConfigurePhysicsAxes`,
`ConfigureLegend`, `ExportPhysicsCanvas` and the 1D `RenderHistogram` convenience
function. Native TH1D/TH2D and TGraph/TGraphErrors/TGraphAsymmErrors are retained.
Future branches must extend this module and its tests for new plot types and
scientific representations; do not copy style code into analysis drivers.

The style uses white canvas/pads, black axes/ticks on all four sides, ROOT font
42, no default title/statistics/fit box, consistent line widths/markers and a
transparent borderless legend. The 1100x900 layout reserves a top metadata area
and bottom scope captions. Legends sit above the plot frame. These settings are
only the starting point: every final PDF must be rendered and visually checked.

## Required outputs and metadata

Each finalized plot produces `<name>.pdf`, `<name>.png`, `<name>.root`, and
`<name>.plot.json`. PDF is the primary output; PNG is preview only. PDF is printed
directly by ROOT `TCanvas::SaveAs`, preserving vector paths and text. A PDF that
embeds a rendered PNG/JPEG is rejected. ROOT's
[TCanvas documentation](https://root.cern.ch/doc/master/classTCanvas.html)
describes canvas export. Individual PDFs are required even if a multipage summary
is later added.

The ROOT file saves the native source histogram/graph and identical metadata.
For counting-error displays it also saves a separate TGraphAsymmErrors. Drawing
does not rebin, normalize, change bin contents, source bin errors, entries or
moments. ROOT file/PDF binary hashes identify an actual run, not a requirement
for timestamp-identical reproduction; numerical contents, configuration and
interpretation are the reproducibility criteria.

Metadata must identify sample kind (DATA, MC or SYNTHETIC), record/fixture,
period, inspected and accepted events, contiguous source range, selection,
unit-validation status and weighting. Data/MC requires validated energy metadata;
this current collision set uses sqrt(s)=13 TeV. PROVISIONAL status stays visible.
UNKNOWN/CONTRADICTED units block finalized physical figures. Missing metadata,
invalid counts/ranges, official-status wording and unvalidated luminosity fail
closed. Current plots omit integrated luminosity because the usable periodD
luminosity/GRL/trigger coverage is not validated.

For collision data/MC, use plain `ATLAS Open Data` and `Independent exploratory
analysis`. Synthetic fixtures instead say `Synthetic test` and `Independent
numerical validation`; they must not imply observed data. No ATLAS logo, official
branding, `ATLAS Preliminary`, `ATLAS Internal`, `ATLAS Official` or `ATLAS
Simulation Preliminary` label is authorized. Current GamGam data also retains
the earlier exploratory/raw-skim/not-official-HH captions.

## Axes, counting and future MC

Use ROOT physics notation: `m_{#gamma#gamma} [GeV]`, `m_{jj} [GeV]`,
`p_{T}^{#gamma} [GeV]`, `p_{T}^{jet} [GeV]`, `#eta` and `#Delta R`.
Y titles distinguish event counts from object counts, and state the actual fixed
bin width when in GeV. A declared GeV bin width that disagrees with the histogram
is rejected. The existing exploratory binning is preserved: Phase 2 mass bins
are 5/10 GeV, pT bins 5 GeV, photon eta 0.1, jet eta 1/6 and DeltaR 0.1;
Phase 3 masses use 1/10 GeV and pT 5 GeV. These are inherited broad diagnostics,
not optimized signal/fit bins. Future changes need a documented scientific
resolution/range/statistics purpose, not cosmetic tuning.

Observed data uses black markers. One-entry-per-event unweighted histograms show
central 68.27% Garwood Poisson counting intervals, computed with ROOT quantiles
and independently checked against ROOT's native TH1 Poisson intervals.
[TH1 documentation](https://root.cern.ch/doc/master/classTH1.html) describes its
counting-error modes. These bars assume Poisson counting and include neither
systematics nor inference on HH efficiency. Multiple-object histograms use markers
without errors: within-event correlations have not been modeled. Underflow and
overflow are retained in native objects/inventories even when outside the view.

Synthetic/MC standalone raw-count lines use blue (`kBlue+2`) and explicit sample
labels. The current convenience renderer supports raw unweighted, fixed-bin
counts only. A density for variable-width bins must divide by bin width when
scientifically required, declare its units, preserve the original counts, and
add numerical tests. Weighted/normalized MC, stacks, ratio panels, uncertainty
bands and fits require a tested extension plus validated weights, normalization,
overlap treatment and uncertainties. Do not invent bands or create a Data/MC
comparison before those scientific gates pass. Styling does not authorize new
physics analysis or upgrade prior PARTIAL conclusions.

## Quality gates and execution

After activating the existing environment, use a new build directory:

```bash
bash scripts/validate_plotting.sh "$HOME/build/atlas_plotting_validate"
# Existing pinned local objects/cache required; no remote input is opened.
bash scripts/regenerate_standard_plots.sh \
  "$HOME/build/atlas_plotting_validate" outputs/atlas_plots_reproduce
```

The first command runs existing regressions and four plotting CTest tests.
The second re-renders seven Phase 2 native histograms and recreates four Phase 3
histograms from the exact checksum-pinned cache/configuration. The Phase 3 cache
is a numerical source, not an image; bin/flow/cutflow closure must match the
historical results. No collision event is reread and no missing histogram is
fabricated. Existing output directories/files are refused.
The Phase 2 driver accepts the previously audited GamGam input and generated
local schema fixtures; unknown provenance stops before opening its event reader.
Collision-cache plotting in Phase 3 requires explicit record, period and energy
arguments. The reproduction wrappers verify the pinned numerical input hashes.

`scripts/validate_plot_outputs.py DIRECTORY --expected-count N --render-dir DIR`
requires PDF/PNG/ROOT/metadata for every figure, checks single readable pages,
page dimensions, fonts, visible required text and native object/sidecar agreement,
rejects raster-image PDFs, and renders pages with Poppler. Pixel checks detect
blank/malformed canvases. The gate records automated PASS separately from
`REQUIRES_HUMAN_INSPECTION`: inspect every final PDF render for axis/Greek glyph
legibility, correct labels, clipping, overlap and legend placement. A successful
preview or automated parse alone does not complete this gate.

Poppler tools (`pdfinfo`, `pdftoppm`, `pdffonts`, `pdftotext`, `pdfimages`) must be
available; CMake refuses the plotting test configuration if they are missing.
The default Step 1 build still has three tests; Phase 2/3 automatically use the
plotting library. Standalone plotting tests can enable `ATLAS_BUILD_PLOTTING`.

## Current authoritative artifacts and historical preservation

Standard-compliant Phase 2/3 PDF/PNG sets are under
`reports/figures/atlas_v1/phase2/` and `reports/figures/atlas_v1/phase3/`.
Per-plot generated ROOT objects remain ignored in `outputs/atlas_plotting_v1_20261010/`.
The new [artifact manifest](../metadata/atlas_plotting_artifact_manifest.csv) and
[validation report](../reports/atlas_plotting_standard_validation.md) identify
the rendered set and its numerical/visual checks.

Earlier reports, manifests, caches, native ROOT source and PNGs are retained as
historical evidence under their original paths; their hashes are not changed to
pretend the earlier PNG-only runs already satisfied this contract. New figures
preserve those numerical definitions and source/cutflow evidence. Fresh clones
need the exact pinned local source objects/cache or a separately authorized
reproduction. Never commit large collision inputs or waive a failed PDF gate.

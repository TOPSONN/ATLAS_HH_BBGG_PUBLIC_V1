# ATLAS publication layout with native ROOT

Contract: **atlas-root-plot-v2**, mandatory for all current and future physics
figures. Adopted 2026-10-11 (Asia/Taipei). Applies to reconstruction, selection,
MC comparisons, fits, statistics and systematic/validation studies. Permanent
instructions are in [AGENTS.md](../AGENTS.md).

## Backend, reference and shared API

Use **ROOT 6.40.04 / C++20** in the existing Ubuntu WSL `atlas-hh-root`
environment. The shared module verifies ROOT's built-in `ATLAS` TStyle,
initializes `gROOT->SetStyle("ATLAS")`, and calls `gROOT->ForceStyle()` before
its documented overrides. No external style macro is vendored. Style provenance
is the installed ROOT release; [TStyle documentation](https://root.cern.ch/doc/master/classTStyle.html)
describes the API rather than proving an installed version.

The layout reference is the ATLAS HH publication identified by
[CDS record 2937468](https://cds.cern.ch/record/2937468/plots). CDS presented an
access challenge during this task. The same publication's
[official ATLAS HIGP-2025-10 page](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/)
provides [Figure 2 PDF](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/fig_02.pdf)
and [Figure 3a PDF](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGP-2025-10/fig_03a.pdf).
Rendered comparison uses their compact margins, sans-serif/math typography,
inside-pad labels and four-sided ticks. Do not copy reference data, luminosity,
fitted shapes, models, signal claims or approved collaboration labels.

[AtlasPlotting.h](../include/AtlasPlotting.h) provides `ApplyAtlasPlotStyle`,
`ValidatePlotMetadata`, `DrawOpenDataLabel`, `ConfigurePhysicsAxes`,
`ConfigureLegend`, `ExportPhysicsCanvas` and 1D `RenderHistogram`.
Native TH1D/TH2D and TGraph/TGraphErrors/TGraphAsymmErrors are retained.
Future plot types must extend the shared module and its tests; do not copy ad
hoc style code into analysis drivers.

## Publication template

Use an actual **800x600** white canvas/pad. Margins are left **0.16**, right
**0.05**, top **0.05**, bottom **0.16**. Use font **42**, axis title size **0.05**,
axis label size **0.045**, annotation size **0.04**, and first annotation line
**0.045**. Data uses black filled round markers **20** at size **0.9**.
Black inward ticks appear on all four sides. No histogram title, statistics/fit
box or default decoration is shown. Axis titles are end-aligned. A TH2 colour
bar can use an explicitly recorded right margin of 0.16. Modest adjustments
still require visual QA.

Current collision figures contain only three inside-pad annotation lines:

```text
ATLAS Open Data
#sqrt{s} = 13 TeV, 2015 data
Exploratory, provisional
```

The renderer chooses the upper left or upper right low-occupancy corner and
uses modest vertical headroom accounting for point/error endpoints. It must
never cover a measurement or uncertainty bar. Placement is recorded in JSON.
A single dataset needs no legend. Actual comparisons can use transparent,
borderless font-42 legends.

Inspected/accepted counts, source entry ranges, selections, unit evidence,
weighting, record identifiers and the earlier three-line scope footer are absent
from the visible canvas. Large headers/footers, clipping, overlaps or excessive
unused outer margins fail visual QA. Fix ROOT code and regenerate native
outputs; never crop or post-process a PNG to satisfy the gate.

Synthetic fixtures say `Synthetic test` and `Numerical validation`; MC says
`MC simulation`. Captions identify their sample scope. No official ATLAS-only
label, logo, `ATLAS Preliminary`, `ATLAS Internal`, `ATLAS Official` or
`ATLAS Simulation Preliminary` label is authorized. Styling does not authorize
new physics analysis or upgrade prior PARTIAL conclusions.

## Required outputs and complete scientific caption

Each finalized plot produces `<name>.pdf`, `<name>.png`, `<name>.root`,
`<name>.plot.json` and `<name>.caption.md`. PDF is primary and printed directly
with ROOT `TCanvas::SaveAs`; PNG is preview only. Preserve vector paths/text.
PNG/JPEG-wrapped PDFs are rejected. See
[TCanvas documentation](https://root.cern.ch/doc/master/classTCanvas.html).
Individual PDFs remain required if a multipage summary is later added.

Preserve all information in **four places**: caption file, JSON sidecar, native
ROOT file and the phase validation report. The complete caption includes sample
kind, record/fixture, period, inspected/accepted counts, contiguous source range,
selection, units, weighting, energy, luminosity evidence/status, axis meaning,
native binning, flows, error definition and independent scope. JSON contains
its exact caption string and template/placement fields. ROOT files save identical
`atlas_plot_metadata` and `atlas_plot_caption` TNamed objects alongside source
objects and any separate display graph. Check caption identity automatically.
Include every full caption in the validation report; a link alone is insufficient.

Data/MC requires validated energy metadata. Current GamGam data uses 13 TeV
and retains `PROVISIONAL` units. UNKNOWN/CONTRADICTED units block finalized
physical figures. Missing metadata, invalid counts/ranges, official status
wording or unvalidated luminosity fails closed. Integrated luminosity remains
omitted because usable periodD luminosity/GRL/trigger coverage is not validated.
Captions retain `ATLAS Open Data exploratory diagnostic`, `raw unweighted GamGam
skim` and `not the official ATLAS HH analysis`.

## Axes and numerical integrity

Use ROOT TLatex: `m_{#gamma#gamma} [GeV]`, `m_{jj} [GeV]`,
`p_{T}^{#gamma} [GeV]`, `p_{T}^{jet} [GeV]`, `#eta`, `#Delta R` and
`#sqrt{s}`. Avoid raw Unicode math dependent on font substitution. Y titles
distinguish event/object counts and state the actual fixed GeV bin width. A
width inconsistent with the histogram is rejected. Inspect exponent multipliers
and Greek/subscript/superscript glyphs in every PDF render.

Preserve bin edges, contents, source errors, display errors, entries/moments,
selections, flows, provenance and statuses. No smoothing, rebinning, cosmetic
normalization, invented fits or Higgs models. Phase 2 mass bins remain 5/10 GeV;
pT bins 5 GeV; photon eta 0.1; jet eta 1/6; DeltaR 0.1. Phase 3 mass bins
remain 1/10 GeV and pT 5 GeV. Full-range Phase 2 mgg remains **80 bins over
0-400 GeV**. Phase 3 mgg remains **70 bins over 100-170 GeV** with its prior
preselection. No extra optional 105-160 GeV view is made in V2. These remain
exploratory distributions, not an HH signal-region interpretation.

One-entry-per-event raw data uses central **68.27% Garwood Poisson** intervals,
independently checked against ROOT's native TH1 Poisson intervals
([TH1 documentation](https://root.cern.ch/doc/master/classTH1.html)). Bars contain
neither systematics nor HH-efficiency inference. Multiple-object plots retain
markers **without errors** because within-event correlations are unmodeled.
Native source errors remain unchanged. Underflow/overflow remain preserved.

Synthetic/MC standalone raw-count lines use blue (`kBlue+2`) and explicit sample
labels. The convenience renderer supports raw unweighted fixed-bin counts only.
Weighted MC, variable-bin densities, stacks, ratio panels, bands and fits require
a tested extension with scientific weight, normalization, correlation and
uncertainty gates. Preserve original counts for any authorized transformation.
ROOT/PDF hashes identify a run; timestamp-identical binaries are not required.

## Execution and quality gates

Activate the existing environment and use new build/output directories:

```bash
bash scripts/validate_plotting.sh "$HOME/build/atlas_publication_validate"
# Requires exact pinned local objects/cache; no remote collision input is opened.
bash scripts/regenerate_standard_plots.sh \
  "$HOME/build/atlas_publication_validate" outputs/atlas_publication_reproduce
```

The first command runs existing regressions and four plotting CTest tests. The
second renders seven Phase 2 native histograms and recreates four Phase 3
histograms from checksum-pinned cache/configuration. No collision event is
reread. Bin/flow/cutflow closure must match history. Existing paths are refused.
Unknown provenance stops before event reading; collision-cache rendering requires
explicit record, period and energy metadata.

`scripts/validate_plot_outputs.py DIRECTORY --expected-count N --render-dir DIR`
requires all five outputs, readable single-page PDFs, actual canvas dimensions,
fonts/TLatex labels, compact annotations inside the pad, native axis typography
and exact caption/metadata agreement. It rejects embedded raster images and
visible diagnostic headers/footers, decodes PNG previews and renders every PDF
with Poppler. Blank-render checks complement visual review; automated checks
do not prove annotation/data separation or overall composition.

Automated `PASS` and `REQUIRES_HUMAN_INSPECTION` are separate results. Inspect
every final PDF render for glyph/multiplier legibility, clipping, annotation
collisions, margins, markers and errors. Compare published figure layouts. Only
explicit recorded visual PASS completes publication QA. Retain regression
coverage and compare native histograms/display graphs to prior numeric output.

The read-only eleven-plot TH1D/display-pair audit is reproducible with the
preserved local V1 and V2 native objects:

```bash
python scripts/compare_plot_numerics.py \
  outputs/atlas_plotting_v1_20261010 outputs/atlas_publication_v2_20261011 \
  --report outputs/atlas_numeric_identity.json
```

This comparator covers the current eleven pairs; new plot types need explicit
extensions. Omitting its new-directory argument produces a baseline inventory,
which is not a comparison PASS.

Poppler (`pdfinfo`, `pdftoppm`, `pdffonts`, `pdftotext`, `pdfimages`) is required.
Default Step 1 still has three tests; Phase 2/3 use the shared library, and
standalone tests can enable `ATLAS_BUILD_PLOTTING`.

## Current artifacts and historical evidence

Current publication-aligned files are under `reports/figures/atlas_v2/phase2/`
and `reports/figures/atlas_v2/phase3/`. Native ROOT objects remain ignored under
`outputs/atlas_publication_v2_20261011/`. The
[V2 manifest](../metadata/atlas_publication_v2_artifact_manifest.csv) and
[V2 validation report](../reports/atlas_publication_v2_validation.md) identify
outputs, exact numeric identity and per-PDF visual checks.

V1 files under `reports/figures/atlas_v1/`, their manifest/report, and all prior
reports, caches, source ROOT objects and PNGs remain unchanged. Earlier
diagnostic layouts are not retroactively declared publication compliant. Fresh
clones need pinned local objects/cache or separately authorized reproduction.
Never commit large collision inputs, waive PDF gates or automatically merge a PR.

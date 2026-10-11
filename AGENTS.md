# Permanent scientific plotting contract

All current and future physics figures must follow
[docs/ATLAS_PLOTTING_STANDARD.md](docs/ATLAS_PLOTTING_STANDARD.md), version
`atlas-root-plot-v2`. Use the shared ROOT/C++20 module in `AtlasPlotting.h` with
ROOT 6.40.04 and its built-in ATLAS style. Every finalized figure needs a native
vector PDF, PNG preview, saved ROOT histogram/graph and required provenance/status
metadata and a complete caption. PNG-wrapped PDFs and non-ROOT scientific plotting backends are prohibited.
Use plain independent Open Data labels; no official collaboration status/logo.
Do not invent luminosity, normalization, corrections or uncertainties.

Use the common 800x600 publication template: margins 0.16/0.05/0.05/0.16
(left/right/top/bottom), font 42, title size 0.05, label size 0.045, black data
markers 20 at size 0.9. Collision figures have only three compact annotation
lines inside a low-occupancy part of the pad: ATLAS Open Data, collision energy
and data year, and Exploratory/provisional status. Never cover measurements or
their errors. No diagnostic title block, footer or single-series legend.
Preserve counts, ranges, selections, unit evidence, weighting, provenance and
scope disclaimers in all four places: caption file, JSON sidecar, native ROOT
file and phase validation report. Use ROOT TLatex for mathematical notation.

Run the plotting tests and `scripts/validate_plot_outputs.py`; render and inspect
every final PDF. Missing PDFs, invalid files, metadata omissions, blank renders,
clipping, unreadable notation, annotation/data overlap or diagnostic headers/footers
prevent completion. Automated checks do not replace
visual review. Preserve scientific values/binning, prior evidence and existing
regressions. A style/format update does not upgrade PROVISIONAL/UNKNOWN semantics.
Compare source histograms and statistical display graphs against prior numerical
output, including edges, errors and flows. Never crop or post-process preview
images to manufacture publication alignment. Compare representative published
ATLAS figure layouts without copying data, luminosity, models or official labels.

Keep collision inputs and generated ROOT objects ignored. Preserve historical
artifacts; identify the current standard-compliant output set explicitly. New
physics/MC/fit/uncertainty plots must extend the same tested module and documented
contract rather than copy ad hoc style code. Obtain separate authorization for
PR merges; do not rewrite shared history or modify unrelated branches.

# Permanent scientific plotting contract

All current and future physics figures must follow
[docs/ATLAS_PLOTTING_STANDARD.md](docs/ATLAS_PLOTTING_STANDARD.md), version
`atlas-root-plot-v1`. Use the shared ROOT/C++20 module in `AtlasPlotting.h` with
ROOT 6.40.04 and its built-in ATLAS style. Every finalized figure needs a native
vector PDF, PNG preview, saved ROOT histogram/graph and required provenance/status
metadata. PNG-wrapped PDFs and non-ROOT scientific plotting backends are prohibited.
Use plain independent Open Data labels; no official collaboration status/logo.
Do not invent luminosity, normalization, corrections or uncertainties.

Run the plotting tests and `scripts/validate_plot_outputs.py`; render and inspect
every final PDF. Missing PDFs, invalid files, metadata omissions, blank renders,
clipping or unreadable notation prevent completion. Automated checks do not replace
visual review. Preserve scientific values/binning, prior evidence and existing
regressions. A style/format update does not upgrade PROVISIONAL/UNKNOWN semantics.

Keep collision inputs and generated ROOT objects ignored. Preserve historical
artifacts; identify the current standard-compliant output set explicitly. New
physics/MC/fit/uncertainty plots must extend the same tested module and documented
contract rather than copy ad hoc style code. Obtain separate authorization for
PR merges; do not rewrite shared history or modify unrelated branches.

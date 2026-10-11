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

The optional HATCHED_STEP mode is additive: ORIGINAL_DATA_POINTS remains the
default, and BOTH generates separate original and `_hatched` outputs. Preserve
every existing figure and its appearance. Hatched raw event-count data uses the
same central 68.27% Garwood intervals, blue step lines and native full-bin-width
rectangles with diagonal fill 3354. Its two-entry legend explains data and
statistical interval; it must not cover measurements or annotations. Never use
this Poisson mode for weighted MC or correlated object counts. Explicit band
support can suppress only structural zero bins outside a selection; preserve
the full source histogram/intervals, record the exclusions and reject excluded
nonzero bins. Do not change selection boundaries or reinterpret structural zeros
as measurements. Render and inspect the diagonal pattern in the native vector PDF.

Keep collision inputs and generated ROOT objects ignored. Preserve historical
artifacts; identify the current standard-compliant output set explicitly. New
physics/MC/fit/uncertainty plots must extend the same tested module and documented
contract rather than copy ad hoc style code. Obtain separate authorization for
PR merges; do not rewrite shared history or modify unrelated branches.

## Final figure approval before push

Policy: `FINAL_FIGURE_APPROVAL_BEFORE_PUSH`, effective immediately.

- Keep generated PDF and PNG figures local until the user explicitly approves
  the final version. Never automatically push generated figures.
- Exclude unapproved figure artifacts from Git staging and commits, including
  modifications to already tracked PDF/PNG figures. Stage source/documentation
  paths explicitly so a normal source-code commit cannot include draft figures.
- Continue ROOT/C++ development, testing, source commits and normal source-code
  PR workflows. Approval for source work does not approve figure artifacts.
- Before every push, inspect both staged files and all outgoing commits against
  the remote branch. A clean index alone is insufficient: no unapproved PDF/PNG
  figures may be present anywhere in the payload to be pushed.
- Only an explicitly approved final figure version may be committed and pushed.
  Record the approved paths and version identity (preferably SHA-256) with the
  user's approval, including associated scientific captions/provenance. Changed
  figures or scientific captions/provenance lose prior approval even if their
  filenames are unchanged; complete applicable QA and obtain approval again.
- Maintain distinct local versions for visual comparison; do not overwrite or
  discard earlier local drafts or approved versions.
- Successful CTest, automated checks and visual QA never constitute user approval.
  Report figure status using these exact labels:
  - `LOCAL_DRAFT`: generated locally; QA incomplete.
  - `QA_PASSED`: applicable numerical/output/visual QA completed successfully.
  - `AWAITING_USER_APPROVAL`: final candidate remains local pending explicit approval.
  - `APPROVED_FOR_PUSH`: the user approved this exact final version for publication.
  - `PUSHED`: that approved version was verified on GitHub.
- Preserve existing scientific results and already published historical artifacts.
  Prior pushes are historical facts, not approval for new or changed figures.
- Do not automatically merge pull requests; obtain separate merge authorization.

# Additive hatched histogram style validation

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1

TASK: ADD_ALTERNATIVE_HATCHED_HISTOGRAM_STYLE_V1

STATUS: PASS

Verified: 2026-10-11 Asia/Taipei

The original black-marker/vertical-error style remains the default. HATCHED_STEP
adds an independent native TH1D step with full-bin TGraphAsymmErrors rectangles;
BOTH writes separate original and alternative files. Existing original PDFs,
PNGs, captions, metadata, historical evidence and source/cache objects were not
overwritten, renamed or changed. No collision events were reread or downloaded.

## Artifacts and numerical identity

| View | Preserved original PDF | Additional PDF | Source / eligible bins | Entries / underflow / overflow |
| --- | --- | --- | --- | --- |
| Primary Phase 3, Events / 1 GeV | [Original](figures/atlas_v2/phase3/m_gg_preselection.pdf) | [Hatched](figures/hatched_v1/phase3/m_gg_hatched.pdf) | 70 over 100–170; 55 eligible | 1689 / 0 / 0 |
| Phase 2 full range, Events / 5 GeV | [Original](figures/atlas_v2/phase2/m_gg.pdf) | [Hatched](figures/hatched_v1/phase2/m_gg_hatched.pdf) | 80 over 0–400; 80 eligible | 63058 / 0 / 647 |

PNG previews, identical full captions and plot JSON accompany each additional
PDF. Native delivery objects remain locally at
`outputs/hatched_v1_20261011/delivery/phase{2,3}/m_gg_hatched.root`.
Phase 3's delivery filename is a byte-identical copy of the new
`m_gg_preselection_hatched` export; its TH1D retains `m_gg_preselection`.
The [19-row manifest](../metadata/hatched_histogram_artifact_manifest.csv)
records new files plus preserved source/original/configuration checksums.
The [validation JSON](../metadata/hatched_histogram_validation.json) contains
the per-PDF results, compiler/linkage, complete original preservation inventory
and numerical evidence.

All stored bins, edges, source errors, Sumw2, entries, moments, effective entries,
normalization and flows in both alternatives and their original controls are
IEEE-754 identical to the pinned V2 sources. Scientific metadata and every
all-bin source-interval value are identical. Every band center/asymmetric error
matches its source interval exactly; its x-errors equal the source half-width.
The default-mode PNG and JSON are byte-identical to V2. Regenerating all eleven
existing original plots passed the independent native numerical comparator,
and all eleven PNG byte hashes equal V2. The unchanged six-argument renderer
and exporter retain their source bodies and visible 2015 data labels.

The preservation audit passed 120 historical tracked metadata/note/report
files and 133 historical manifest rows, including all existing figure bytes
and the pinned ignored ROOT/cache inputs. New report/manifest files are additive.

## Statistical and rendering contract

Confidence remains exactly `0.682689492137` (displayed as 68.27%), central
Garwood Poisson. Stored intervals are unchanged; the plotting frame starts at
zero. Eligible zero bins retain their nonzero upper interval, tested with a
synthetic fixture. The full source histogram and all-bin zero-x-error graph are
saved even when structural zeros are excluded from the alternative band.
Phase 3's existing inclusive 105–160 GeV event selection is unchanged. Band
bins are 6–60 (complete [105,160) display bins); the other fifteen bins are
confirmed structural zeros. A nonzero excluded bin, including the [160,161)
bin receiving an event exactly at 160, causes refusal rather than hiding data.

Draw order: axes → rectangular band (`2 SAME`) → central step (`HIST SAME`)
→ annotations and two-entry statistical legend. Central color is `kAzure+2`
(862), width 2; band color is `kAzure+1` (861), opaque diagonal hatch 3354.
No interpolation, smoothing, fit, background model, systematic band or HH
signal interpretation is introduced. Weighted MC and correlated object counts
are rejected. Units remain PROVISIONAL; usable luminosity is unvalidated.

Both single-page native PDF exports contain vector text/paths and no embedded
raster images. Actual diagonal blue page strokes within numerical band regions
were counted: Phase 3 410; Phase 2 92. Unused PDF pattern resources and a
legend-only hatch do not satisfy this check. This ROOT-specific parser is a
bounded automated check; both complete PDF pages were also rendered with
Poppler and visually reviewed by the author and independent reviewers.

| PDF | Visual result |
| --- | --- |
| Phase 3 hatched | PASS: visible diagonal rectangles/central step, clear bin boundaries, readable labels and legend, no overlap or clipping. |
| Phase 2 hatched | PASS: full range and ×10³ scale retained; naturally thin high-count intervals have visible small diagonals; legend/annotations clear, no clipping. |

The original controls were visually inspected. Full-range intervals were not
inflated to make hatches wider. The new label is `2015 Period D`; only the
new version adds the compact two-entry legend.

Native output keys are the original TH1D, `<source>_display` for all-bin
intervals, `<source>_hatched_band` for eligible full-width rectangles,
`atlas_plot_metadata` and `atlas_plot_caption` TNamed objects. Caption/sidecar/
native metadata agreement passed. Source objects remain reproducible from the
pinned files and documented new-output commands.

## Executed validation

ROOT 6.40.04 / C++20; conda GNU 15.3.0 at
`/home/btu/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`;
CMake 4.4.4; Ninja 1.13.2. All 22 compilation commands explicitly use C++20.
ROOT/libstdc++/libgcc linkage for the renderer, new test and Phase 3 executable
resolves inside this environment. No environment or unrelated toolchain changed.

- Combined CTest: **18/18 PASS**; all prior 15 regressions retained.
- Step 1: 3/3 PASS. Phase 1: 22 schema cases and 8 transfer cases PASS.
- Plotting CTest: 7/7 PASS, including three added tests.
- Existing style: 29 cases; unchanged original PDF gate: 32 cases PASS.
- New C++ additive contract: 51 assertions/cases PASS.
- New independent Python gate: 47 cases PASS.
- Five synthetic mode exports, two production alternatives, two BOTH original
  controls, two omitted-mode defaults and eleven existing production outputs
  passed their applicable automated PDF/PNG/native-object gates.

The initial full run was 15/18 PASS. Its artifacts and diagnostics were retained.
Saved native colors were already correct; ROOT ForceStyle replaced attributes
while the C++ test deserialized objects. Tests/gates now inspect saved styles
with a scoped flag guard and restore caller state. The exact style assertions
were retained. The caption gate now recognizes equivalent explicit statistical
scope wording; negative tests still reject a missing no-systematics statement.
Successful fixture markers isolate complete current test runs without deleting
failed evidence. Production validation remains exhaustive by default.

Reproduce in the existing environment using fresh build/output paths:

```bash
bash scripts/validate_plotting.sh "$HOME/build/atlas_hatched_reproduce"
bash scripts/render_alternative_mass_plots.sh \
  "$HOME/build/atlas_hatched_reproduce" outputs/atlas_hatched_reproduce BOTH
```

Omit BOTH to exercise the ORIGINAL_DATA_POINTS default. Native input checksums
are pinned by the V2 manifest before any output is created. Fresh clones require
the ignored local pinned inputs; ROOT data files are deliberately not committed.
Actual logs are retained in `.local/hatched_v1/`, including initial/final CTest,
build, production/default/original regeneration, numerical and toolchain audits.

The implementation is an additive commit on the existing plotting branch and
updates PR #6. PR #4/#5/#6 are not merged. GitHub NO_CHECKS is not CI PASS;
PC2 and PC3 validation remain PENDING. This PASS applies to visualization and
the listed numerical/regression gates; scientific audit limitations remain.

ROOT references: [TGraphPainter rectangle option 2](https://root.cern.ch/doc/master/classTGraphPainter.html)
and [ROOT 6.40 native pad hatching](https://root.cern.ch/doc/v640/TPad_8cxx_source.html).

## Complete Phase 3 caption

```
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
Alternative HATCHED_STEP rendering of the same raw source counts; no fit, signal model, smoothing or systematics.
Statistical counting intervals only; no systematics.
Central line: native TH1D step histogram. Band: per-bin full-width rectangles, central 68.268949213699997% Garwood Poisson statistical intervals. Stored interval values are unchanged; the plotting frame clips physical y below zero.
Full source histogram (including errors, entries, moments and flows) and all-bin zero-x-error interval graph are retained.
Display-only band support: [105,160); structural zero bins outside this support are omitted from the band, never from the source histogram or all-bin intervals.
Eligible source bin indices (one-based): [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60].
Excluded structural zero source bin indices (one-based): [1,2,3,4,5,61,62,63,64,65,66,67,68,69,70].
```

## Complete Phase 2 caption

```
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
Alternative HATCHED_STEP rendering of the same raw source counts; no fit, signal model, smoothing or systematics.
Statistical counting intervals only; no systematics.
Central line: native TH1D step histogram. Band: per-bin full-width rectangles, central 68.268949213699997% Garwood Poisson statistical intervals. Stored interval values are unchanged; the plotting frame clips physical y below zero.
Full source histogram (including errors, entries, moments and flows) and all-bin zero-x-error interval graph are retained.
Eligible source bin indices (one-based): [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80].
Excluded structural zero source bin indices (one-based): [].
```

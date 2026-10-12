# Phase 5B continuum native-schema gate

**Physical status: BLOCKED_NETWORK / NOT_EVALUATED.** The independent acquisition task reported that the exact-URI XRootD metadata probe timed out after15 seconds and that no302521 ROOT payload was obtained. No verified local DSID302521 ROOT file was available to this reviewer. No302521 tree, branch, native type, entry, generator weight, truth object or reconstructed quantity was inspected. The accompanying [schema manifest](../metadata/phase5b_schema_manifest.csv) contains unperformed gate records, with observed physical fields empty; it is not an invented branch inventory. Fresh synthetic software checks described below do not establish a physical PASS. Acquisition and its new transport ledger are separate work.

## Preserved baseline

The audited starting head was `e131de92897b75185981ec2c5ce1c722e9ada6c3`, with a clean working tree before additive Phase5B work. All78 recorded tested-source LF hashes,15 recorded source/report/metadata LF hashes,8 weight-input raw hashes and243 immutable local raw file hashes/sizes matched their Phase5 evidence. LF canonicalization means only replacement of CRLF by LF in the paths whose existing manifest explicitly declares that hash convention. ROOT inputs and original access receipts were compared as raw bytes. The local independent audit is `.local/phase5b_review_20261012/baseline_audit.json`.

The immutable original Phase5 access receipt `.local/phase5_access_20261012/access.json` retains raw SHA-256 `be764a03f335e9cf238b9e8f1f67a8fd82bfa07aeb2ae145f490e8d6547ab134`. The published [Phase5 transfer ledger](../metadata/phase5_transfer_ledger.json) retains raw/LF SHA-256 `9e8a88178bc2d2f5717d71b1e7f9d59f07eb46be0e96c185c6e2ba58997d5ece`; normalizing only the original receipt's CRLF produces that same LF hash. Prior23/23 local CTest results remain historical evidence, with the prior physical-model verdict blocked. This audit did not rerun those23 tests or read historical ROOT event trees.

The target identity, as pinned in that preserved ledger, is `ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root`, published size110755804 bytes and Adler-32 `b43248ea`. These identify a proposed input; they do not establish successful access, SHA-256, a native schema or filter semantics.

## Additive metadata-only preflight

The new [local preflight](../apps/phase5b_input_preflight.cxx) uses [AtlasInputPreflight](../src/InputPreflight.cxx) and the unchanged [native MC Reader](../src/MCEvents.cxx). It accepts an existing local regular file and an explicit positive expected DSID; URI input is rejected. It opens READ only, rejects zombie, writable and `TFile::kRecovered` files, inventories every stored key/cycle and recursively enters native directories. Known tree keys must have exact native `TTree` class before deserialization; `TChain` and other tree subclasses are refused. Unresolved key classes fail closed because their inheritance is unknown.

Every inspected tree rejects friend references. All branch levels are traversed, with physical names, native types and storage filenames recorded; external files and URIs are refused before any event read. Crucially, the tree remains associated with its original directory during this inspection: ROOT's `SetDirectory(nullptr)` clears storage associations and would hide an external branch filename. Metadata traversal has explicit budgets of100000 nodes and64 levels. Non-tree payloads are inventoried by key class without being read.

The preflight then constructs the unchanged MC Reader and records its type bindings and analysis entry count. Neither `GetEntry`, `SetEntry` nor `Reader::read` is executed by the preflight. Its PASS means **local metadata integrity and MC binding compatibility only**. Actual per-entry DSID values, collection lengths, finite values, units, source provenance and physics remain `NOT_EVALUATED` or `UNKNOWN`. An empty analysis tree is refused. Native truth presence alone does not establish an eligible generator-filter pair or permit inventing photon energy or changing signed truth-jet mass.

Outputs are `keys.csv`, `trees.csv`, `branches.csv`, `reader_bindings.csv` and `summary.json` in an exclusively created fresh directory. Existing outputs are never overwritten. The CLI requires explicit `SYNTHETIC_FIXTURE` or `PHYSICAL_CANDIDATE` scope; a candidate label does not certify provenance. The summary states zero event entries read and does not label actual DSID values verified.

## Executed synthetic checks

ROOT6.40.04/C++20 compilation with `-Wall -Wextra -Wpedantic -Werror` passed. The new [synthetic test](../tests/test_input_preflight.cxx) executed **34 checks including19 rejection cases**. It covers native MC metadata, unknown extra scalar inventory, directory/tree inventory, persisted nested branch inventory, missing/wrong native required types, empty/missing analysis, top-level and nested friend references, top-level and nested external storage, stored top-level and nested TChain, zombie files, positive DSID syntax and local input guards, and preservation of an existing output directory. A child writer intentionally exited without closing its synthetic ROOT file; ROOT genuinely recovered that file and the new preflight refused it.

A fixture with wrong actual channelNumber passes metadata inspection honestly because no events are read; the unchanged MC Reader rejects that same fixture at its first explicit read. This demonstrates the boundary between a binding check and an actual event identity check. Final focused evidence is local under `.local/build_phase5b_preflight_agent/input_preflight_fixtures/53845797713/`; the earlier passing fixture and unsuccessful runs remain preserved. No302521 ROOT events were used. The final independent synthetic CLI executed successfully into `.local/build_phase5b_preflight_agent/cli_metadata_synthetic_final/`, with3 analysis metadata entries and0 event entries read. The final integrated test suite is owned by the project validation task.

## Conditional physical stages

The commands below are a reproducible plan, **not an executed302521 result**. Use a freshly built directory with the unchanged Phase1-5 dependencies and the additive preflight target. First require acquisition size, published Adler-32, local SHA-256 and budget evidence to pass. Use new output paths and log every entry range, including repeated reads. No remote ROOT operation is permitted.

```bash
cd /mnt/c/HH
source /home/btu/miniforge3/etc/profile.d/conda.sh
conda activate atlas-hh-root
build=/home/btu/build/PHASE5B_FRESH_VALIDATED_BUILD
input=/ABSOLUTE/VERIFIED/LOCAL/302521.root
out=outputs/PHASE5B_FRESH/302521
mkdir -p "$out"
"$build/phase5b_input_preflight" "$input" "$out/metadata_preflight" \
  302521 PHYSICAL_CANDIDATE
```

**STOP at the native first10 event gate.** There is no dedicated raw native MC-prefix CLI in the current repository. A future acquisition task must first provide an explicitly bounded wrapper around the unchanged `mc::Reader::read` for [0,10), with actual expected DSID, generator-weight finiteness, collection counts/lengths, and available truth/scalar raw values checked before StageB. This absent wrapper is a reproducibility limitation, not an executed failure or a reason to promote the metadata preflight to event validation. Do not run StageB or a reconstruction driver until that first10 gate has actually passed and its source/range/input evidence is retained.

Only **after** that native first10 gate, the legacy reco inventory and disjoint [10,100) raw unit probe can be used as follows. These are conditional examples, not a runnable continuation from metadata-only PASS:

```bash
"$build/inspect_root_schema" --input "$input" --tree analysis \
  --manifest "$out/reco_first10.csv" --summary "$out/reco_first10.txt" \
  --evidence PHYSICAL_MC_302521_CANDIDATE --max-entries 10
"$build/probe_kinematic_units" "$input" "$out/units_raw.csv" 10 100
python scripts/audit_phase4_units.py "$out/units_raw.csv" 302521 "$out/reco_units.json"
```

The legacy inspector's PASS audits reco fields, not actual MC channelNumber/mcWeight/truth values. Its extra-field `NOT_AUDITED` records must remain honest. The raw unit probe also uses the existing reco reader and does not itself certify MC DSID. After the raw [10,100) native MC and reco-unit/direction checks, optional reproduction with existing reconstruction tools can use the following commands. They explicitly reread the prefix, already perform pair reconstruction and geometric matching, and are **not** substitutes for the preceding raw native first10/unit gates. Those repeated reads must be accounted separately. A metadata gate cannot replace them.

```bash
"$build/phase4_mc_reconstruction" "$input" "$out/native_prefix10" \
  302521 0 10 1 PROVISIONAL metadata/phase3_selection_config.ini
"$build/phase4_mc_reconstruction" "$input" "$out/native_prefix90" \
  302521 10 100 1 PROVISIONAL metadata/phase3_selection_config.ini
```

The preceding raw native-prefix gates must establish finite nonnegative truth pT, finite eta/phi and exact native lengths before these matching-enabled drivers are invoked; the matching adapter independently checks its own eligible directions and work budgets during each read. Signed raw truth mass remains preserved and does not imply a physical mass/energy prescription. Unit scale1 is acceptable only after the bounded numerical gate, remains PROVISIONAL, and is not documentary calibration validation. Do not use a filename or three other MC samples to infer302521 truth schema, filter pair or weight semantics.

After all preceding gates, explicitly choose an end no greater than10000 and the actual entry count. The examples below require at least10000 entries; smaller inputs require a separately recorded explicit range rather than silent truncation. Both drivers reuse the corrected shared Cartesian implementation and exact unchanged Phase3 selection. The numerical regression is required in addition to reconstruction because it checks invalid/nonnegative-reference and valid/negative-reference disagreements independently.

```bash
"$build/phase4_numerical_regression" MC "$input" "$out/numerical_regression" \
  302521 100 10000 1 PROVISIONAL metadata/phase3_selection_config.ini
"$build/phase4_mc_reconstruction" "$input" "$out/reconstruction" \
  302521 100 10000 1 PROVISIONAL metadata/phase3_selection_config.ini
```

The planned distinct ranges contain at most10000 unique entries, with explicitly repeated reads by independent tools. They are not10000 independent events per tool added into one cutflow. Preserve each output/version, record repeats and binary/source/input identities, and stop dependent physics on any schema, unit, identity or mass-closure failure. The mass acceptance remains `1e-7 + 1e-10*abs(reference_mass)` GeV; no clamping, input repair, threshold changes or MC-only four-vector implementation is introduced.

No nominal generator-weighted shape, SF application, physical normalization, sample mixture/stitching, physical transfer factor, fit or figure is enabled by these engineering gates. Those require the separately audited generator-filter and weight-provenance contracts. The actual302521 schema and physical gate disposition remain **NOT_EVALUATED** here until verified acquisition and explicit bounded execution evidence exist.

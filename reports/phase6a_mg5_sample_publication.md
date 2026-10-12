# Phase 6A sample publication

Current publication state: NOT_EVALUATED (local references prepared; remote publication is not yet claimed).

Only two selected actual samples are allowlisted. Each is below 5 MiB; combined compressed bytes are 189304 (<10 MiB). Decompressed LHE bytes are identical to original generator output; only gzip metadata was normalized with mtime=0 and no filename. Event-only SHA-256 and original compressed/decompressed SHA-256 are in sample_manifest.json.

- `reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz`: `1427fd1446f6bce5627be769a5fde905206f01b684d72d2b8ee35b46a198c568`
- `reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz`: `bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343`

Exact physics cards are extracted from actual LHE banner text. MG5's mutable post-run run_card seed reset to 0 is preserved locally, not substituted for the applied seed. Settings/log evidence replaces only private local paths with placeholders; original and published hashes plus transformations are recorded. No production setting, four-momentum, ID, event or weight was changed.

Git allows only these exact two .lhe.gz exceptions and marks *.lhe.gz binary. Personal samples, full process directories, integration grids, third-party MG5 source, ROOT input data and all unapproved figures are excluded. Explicit source/report/sample staging and every-outgoing-commit payload audits precede each push. The remote final tree and downloaded blob hashes must be checked, not inferred from a local commit.

CI uses only standard Python to validate both real reference files, manifests, exact card/banner/source evidence hashes, size caps, gzip/XML/counts/particle content/finite physical values and output allowlists. Actual GitHub Actions results will be recorded after publication; NO_CHECKS is not PASS. PR base main, head codex/phase6a-mg5-lo-bbgg. PR #8 remains unchanged; no force push or automatic merge. No figures were generated or published.

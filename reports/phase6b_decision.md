# Phase 6B decision

Verdict: **PASS_PYTHIA8_SHOWER_AND_GITHUB_PUBLICATION** for the verified source/reference commit `ee58a1b5a13f6fde939c81e68ea79bdac1a91023`. All12 gates A–L passed with3,000 real valid local outputs and300 real published subset events. [Draft PR12](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/12) is OPEN/DRAFT and stacks on PR11. Actual GitHub blobs were downloaded and independently checked, the full245-blob tree matched, and both required workflows completed with their expected tests. This provenance seal receives a separate final-head CI/remote check before delivery; final checked HEAD is recorded in the local immutable receipt and PR checks/body rather than a self-referential commit hash.

Final counts: bbgg1000, ccgg1000, light-jjgg1000; total input/output3000/3000, shower failures0, validation failures0. Public references contain100+100+100 exact event blocks from the validated full runs. The three full samples exceed the10MiB policy and stay local; a [Draft Release proposal](../simulation/pythia8/evidence/large_output_release_proposal.json) exists, with no release/LFS/upload action.

The baseline is Pythia8.317 simple pT-ordered ISR/FSR plus Lund hadronization and applicable decays, MPI/pileup/CR OFF and stock primordial-kT ON. Source cards and cross sections remain MG5 LO. There is no ME/PS matching/merging, official ATLAS tune, detector response or calibrated b-tagging. The preserved OFF-card event54 failure is explicitly outside accepted references; full details and unchanged strict tolerances are in the scientific reports.

| Gate | Current state | Evidence |
|---|---|---|
| A | PASS | reports/phase6b_environment.md |
| B | PASS | reports/phase6b_hepmc3_validation.md |
| C | PASS | metadata/phase6b_input_manifest.json |
| D | PASS | reports/phase6b_lhe_interface.md |
| E | PASS | reports/phase6b_hadronization_validation.md |
| F | PASS | metadata/phase6b_event_summary.csv |
| G | PASS | reports/phase6b_event_identity.md |
| H | PASS | reports/phase6b_weight_validation.md |
| I | PASS | simulation/pythia8/evidence/*/physical_validation.json |
| J | PASS | reports/phase6b_github_publication.md |
| K | PASS | simulation/pythia8/USER_GUIDE_ZH_TW.md |
| L | PASS | actual GitHub source-head workflows56new/59MG5;5C++/31upstream;10event reproducibility |

Local regression: historical MG5 tests59/59, new portable/control tests56/56, actual linked C++ API tests5/5, upstream HepMC3 tests31/31. Actual physical reference processing and ReaderAscii tests cover3000events and are separate from deterministic synthetic/corruption/API fixtures. Ten-event repeat has identical physics records, ledgers and diagnostic bytes; the effective-settings snapshots preserve a sole scratch-input-path difference. Existing ROOT/MG5 conda-history hashes and the entire old MG5 Git tree remain unchanged.

The documented [Traditional Chinese self-service guide](../simulation/pythia8/USER_GUIDE_ZH_TW.md) reuses installed tools and supports bounded user runs without automatic Git push. `--jobs1` is the supported deterministic stream; unsupported concurrency is explicitly rejected. The actual full1000 self-service command was physically executed for all profiles. Dry-run processes0events. Future1M operation uses streaming validation/records and explicit resource limits; no1M execution claim is made.

Before each push, the staging index and every outgoing commit are audited for selected archive hashes, bounded sizes, credentials/private paths, unwanted binaries/generated trees and unapproved PDF/PNG. Figure count0. PR9/11 are preserved; the new branch targets `codex/phase6a-backgrounds-1k`. No force push, merge, large release or LFS is authorized or performed.

Remote source/reference verification physically downloaded148 artifacts. Each published gzip, decompressed event hash, source ledger and card/proof identity passed independently; remote original MG5 references remain3,000 and published shower prefixes300. PR9 and PR11 retain their exact prior heads/states. NO_CHECKS is not treated as PASS. The [committed source-head verification](../simulation/pythia8/evidence/github_source_head_verification.json) includes actual completed jobs, step conclusions and56/59 test-count logs; final provenance HEAD is rechecked after push before the final response.

Next recommended step after remote acceptance: plan a separate Phase6C Delphes study, with detector configuration and distinct validation. Do not start it as part of this phase.

# Phase6C selected ROOT publication

**Actual native references, local exact-copy preparation and portable integrity PASS;
remote verification remains NOT_EVALUATED pending the final publication seal.**
The publication helper and portable workflow do not establish remote acceptance.
Only actual validated Stage B 100-input runs are eligible for the three selected
references. Stage C full 1000 ROOT outputs remain local by default.

| Process | Selected reference path | Required native entries | Size cap |
|---|---|---:|---:|
| bbgg | `reference_samples/delphes/pp_bbgg_atlas_like/detector_100.root` | 100 | 10 MiB |
| ccgg | `reference_samples/delphes/pp_ccgg_atlas_like/detector_100.root` | 100 | 10 MiB |
| jjgg/light | `reference_samples/delphes/pp_jjgg_light_atlas_like/detector_100.root` | 100 | 10 MiB |

The total ROOT cap is 30 MiB. These selected inputs are the exact existing
published 100 HepMC events, shared with the corresponding local 1000 source;
they do not add independent hard-event statistics. Each ROOT file must be the
original Stage B output bytes, not a sliced or reserialized Stage C ROOT file.
ROOT UUIDs/dates and timing are not promised to be binary reproducible.

Actual selected ROOT bytes/SHA256 are:

| Process | Bytes | SHA256 |
|---|---:|---|
| bbgg | 2959022 | `fc73c51169d1402d496fe445769adbc2634ba6e0b99ee25726919e100b1c8c67` |
| ccgg | 3098810 | `479d628cdafce05ea885176753b51fca90db9db7f552e1dca03947b5fa46e562` |
| jjgg | 3028524 | `2a6ed16ddd26e440d15f661c359b8760af1397a947a9be6f0bd5e5ca432a160a` |

All three passed the physically executed size/signature/privacy guard and actual
native 100/100/100/100/0/0 readback; total ROOT bytes are 9,086,356.

## Exact publication contract

`simulation/delphes/scripts/publish_references.py` validates all three process
plans before writing selected references. `--dry-run` makes no publication
writes. It requires local run PASS,100 input/read/processed/output,0 invalid or
skipped, the actual native ROOT/C++20 checker report and exact ROOT/card/index
hash binding. Original input HepMC, source MG5, Pythia settings/run/seed, the
original 1000 normalization denominator and per-process generator cross section
must correspond to the preserved manifests. Full source weight columns remain
unchanged; no luminosity or extra tagging probability is introduced.

Software provenance pins Delphes 3.5.1, official tag commit
`28658365abeb71ee36dfc739f9670c1514c0cb10`, source archive SHA256
`b60d26d2ee2c84b58fbf2cf397fabd0ef3e89d3a0546d843c4ada82cc802d787`,
and ROOT 6.40.04. The archive was independently compared with 900 source files
from the tag clone. The original public source URL is
[the official tagged archive](https://codeload.github.com/delphes/delphes/tar.gz/refs/tags/3.5.1).
The frozen detector canonical card is
`cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47`;
each exact runtime card differs only by the recorded per-process RandomSeed.

The helper copies the original ROOT, runtime card, source ledger, native input
and truth indices, native validation, reconstructed-event audit and CSV bytes.
The published manifest uses repository-relative paths. Full local installation
manifests/logs with machine paths remain local. Portable signature/privacy guards
do not claim to decode every ROOT string; compatible native readback and exact
hashes establish the actual selected data identity. Nothing is stripped or
repaired inside ROOT. An exposed private path causes rejection and preserves
the original local file for investigation.

The actual earlier10-event interface smoke (404,686 bytes, ROOT SHA256
`2223339b3be9f66dd169db0198f4fae954fb2ea3f75a6ca7f09ee3f55a129326`)
physically failed the publication privacy guard: its absolute output filename
was stored four times, with home-prefix matches at offsets 133/204/393521/404606.
That diagnostic ROOT remains local and unchanged. Formal reference execution
must give Delphes the relative output argument `detector.root` inside the
already isolated per-run working directory. The fix changes the ROOT filename
metadata at creation; it neither edits the detector card nor strips existing
ROOT data. The final actual outputs must pass the same strict guard before
selection.

The actual source correspondence indices contain all per-particle p4/mass and
production-position/ct values for the selected100 inputs. Their original ASCII
sizes are7,106,574/7,568,106/7,426,217 bytes for bbgg/ccgg/jjgg respectively
(total22,100,897). The initial arbitrary5 MiB evidence cap rejected preflight
before any reference writes. The reviewed bounded policy now permits only the
three exact `input_event_index.dat` reference paths up to10 MiB each and a
separate30 MiB combined, preserving their physical source correspondence.
All other new selected evidence stays below5 MiB; ROOT caps remain unchanged.
No new compressed-index format, lossy rewrite or scientific gate relaxation
was introduced. Publisher, portable checker and payload auditor share these
path-specific caps.

If any genuine selected ROOT exceeds 10 MiB, the helper writes only a concrete
local draft-release proposal containing the actual proposed asset hashes and
sizes. It creates no GitHub release, uploads no asset, enables no Git LFS and
does not claim complete reference publication. User review of that concrete
proposal precedes any separate release authorization. The proposed individual
GitHub asset preflight uses the documented 2 GiB cap, independent of this study's
stricter 10 MiB repository policy. [GitHub release documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## CI and final remote acceptance

`.github/workflows/delphes_reference_samples.yml` uses Python on Linux. It
validates exact selected ROOT magic/hash/size, source relationships, CRC and
raw HepMC/input-index identity, runtime cards, and existing native report hash
bindings. The portable truth checker verifies the provenance envelope; it does
not rerun raw ancestry analysis. It does not install or execute Delphes/ROOT,
and reports native ROOT readback as `NOT_EXECUTED_BY_PORTABLE_CI`. Previous
MG5/Pythia integrity/regression checks remain part of the workflow.

The payload auditor checks the index and every outgoing commit individually.
Only the three selected ROOT paths are allowed as new generated binary assets;
unselected event archives, vendored builds, private paths and unapproved PDF/PNG
figures fail. Documented local operating paths are allowed in Markdown, never
in reference machine manifests or ROOT payloads. No figure was generated by
this task, and no prior test or publication approves a new figure version.

Final acceptance requires the uploaded ROOT blobs to exist with the selected
hashes/bytes, a draft PR to the Phase6B feature base, and successful actual CI
for the final remote PR HEAD. A local portable PASS, a CI run for an older
commit or a prepared manifest is insufficient. The final commit, PR URL,
remote blob checks and final-head CI are pending the separate publication seal.

| Gate | Current evidence status |
|---|---|
| Official source/card/installation review | PASS; real 10-event interface/schema smoke recorded separately |
| Selected Stage B native100 references | PASS; actual counts, original hashes and strict privacy/size guards |
| Local selected-copy helper execution | PASS; actual preflight and33 copied/manifest artifacts, no Git action |
| Local portable selected-reference validation | PASS; three100 references and exact index/native-report bindings |
| Staged and every outgoing commit audit | NOT_EVALUATED until explicit staging/commit preparation |
| Remote ROOT blobs / final draft PR HEAD CI | NOT_EVALUATED pending remote publication |

The [Traditional Chinese guide](../simulation/delphes/USER_GUIDE_ZH_TW.md)
provides the executable commands. Personal samples stay local and never trigger
a commit, push or release automatically. No automatic merge is performed.

Actual run/readback receipts are
[native_runs.json](../simulation/delphes/evidence/native_runs.json) and
[independent_readback.json](../simulation/delphes/evidence/independent_readback.json).
The selected manifests/cards/indices preserve the exact original Stage B files.
All full1000 ROOT outputs remain local; public Stage C numerical/native summaries
are separate evidence, not replacement ROOT samples. Scientific reproducibility
is documented in [reproducibility.json](../simulation/delphes/evidence/reproducibility.json):
the repeated final10 input run has equal scientific-content hashes while ROOT
binary hashes differ. B100/C1000 first100 comparisons match all three scientific
content hashes and explicitly add no independent hard statistics.

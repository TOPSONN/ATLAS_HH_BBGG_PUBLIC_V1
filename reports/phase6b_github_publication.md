# Phase6B GitHub shower publication

**LOCAL_PHYSICAL_AND_REFERENCE_PREPARATION_PASS; remote publication and final
PR-head CI remain NOT_EVALUATED until actual GitHub verification.**
The intended stacked Draft PR is from `codex/phase6b-pythia8-shower-1k` into
`codex/phase6a-backgrounds-1k`; PR9/11 remain unchanged and no merge is requested.

Each process has a real100-event reference selected from its actual validated
1000-input v2 shower run, in the three specified bbgg/ccgg/light-jjgg directories.
The original MG5 archives, cards, manifests and cross sections are preserved.
No synthetic test fixture may enter a reference directory.

`publish_shower_references.py` performs bounded local preparation without Git,
GitHub release creation or upload. It requires PASS full-run manifests, exact
MG5 source/seed/count/version identities, the reviewed v2 settings hash and
actual full1000 ReaderAscii reports bound to full ASCII SHA256 and run identity.
It independently validates the full ASCII and CRC/decompressed identity of its
retained gzip before preparing any artifacts. All three processes must pass
preflight before public files are written. Existing public artifacts are never
overwritten.

Selection preserves complete original ASCII event blocks, banners/footer,
event numbers and exact matching raw JSONL ledger lines. There is no particle
reserialization or loss of numerical precision. Only the gzip container is
deterministic. The full1000 ledger remains bounded public evidence so CI can
check selected raw-line membership and source/run identities; it is not a
substitute for reading an omitted full physics file with HepMC3.

Optional full1000 archives are eligible only if they fit10MiB each and30MiB
combined. Oversized full files stay local with exact gzip/decompressed hashes,
sizes and event counts. Their concrete
`large_output_release_proposal.json` lists actual candidate assets for a future
Draft Release, including hashes and the official individual asset-size
preflight. It records `release_created=false`, `assets_uploaded=false` and no
Git LFS. Creating/uploading that release requires separate explicit user
authorization. See the official
[GitHub release size policy](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

Lightweight GitHub Actions use standard Python to validate file presence,
schema, gzip CRC, three hashes, original MG5 identity, events/units, graph links,
finite weights, exact selected/full ledger relationships and size limits.
Separate committed actual C++ ReaderAscii reports provide physical library
readback evidence. CI does not install Pythia or claim that Python text parsing
proves full library/Delphes compatibility. The existing MG5 library validation
and59-test regression are also run.

Publication uses explicit staging paths, narrow gzip exceptions and binary
attributes. `audit_shower.py` inspects the index and every outgoing commit for
unselected archives, oversized files, private data, vendored dependencies and
unapproved PDF/PNG figures. Figure approval remains a separate exact-version
user gate. Personal/full local runs are never automatically pushed.

The actual locally prepared references are:

| Process | Events | Gzip bytes | Gzip SHA256 |
|---|---:|---:|---|
| bbgg |100 |2518254 | `6d2ec0c5624dde2c33608c29b4ecec125f10666ac49126596bbb8caf6f31d944` |
| ccgg |100 |2697887 | `143793553369b2ca21aa38781920129b6a7f1d6b72f0c2619d52eb8137c5b7d5` |
| jjgg |100 |2650794 | `02581f704f398b3935bb76ded39311439525ba09ab66b5e883e39e116a4d60a4` |

Their decompressed SHA256 values, respectively, are
`aceaf0b619c5cd28cb7e092493c4af3ac2bba60507becbbfa1c351eeb6dc0ce3`,
`62b31ecb9bc5d06af6129b810253ede7479c1121fe5b90b65042646ffb7a35ab`,
and `3a93e667501efb9a83209e71b36a8a79cafec4209dd554295973b0a9f82325d9`.
Total selected gzip payload is7866935bytes, with100events per process.
Every full1000 gzip exceeds10MiB:25204359/27381014/27259142bytes,
respectively, so all three stay local and the concrete Draft Release proposal
was prepared. Its actual assets retain the full-run hashes listed in the
configuration report; no release was created or uploaded.

Final acceptance still needs pre-push payload audit, remote blob verification,
a Draft PR URL and successful checks on the final submitted PR head. At this snapshot:

| Item | State |
|---|---|
| Actual v2 full1000 samples | PASS;1000each,3000total, zero shower/validation failures |
| Selected real references | PASS_LOCAL;100each, exact original StageC blocks/ledgers |
| Local publisher physical-data preflight | PASS; actually executed,28artifacts prepared locally |
| Remote sample SHA256 verification | NOT_EVALUATED |
| Final PR head/URL | UNKNOWN |
| Final-head GitHub CI | UNKNOWN; NO_CHECKS is not PASS |
| Large release creation/upload | NOT_EVALUATED; not authorized by the bounded reference push |

The failed OFF configuration is preserved only as diagnostic source/evidence
with **NOT_APPROVED_FOR_REFERENCE** status. Its failed physics files are local
and excluded from publication. Final acceptance cannot be inferred from source
checks, API tests or a successful Pythia call alone.

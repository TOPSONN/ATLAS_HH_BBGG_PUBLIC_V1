# Phase 6B event identity

The source mapping is based on the actual official LHE reader's consumption, including internal Pythia retries. Output row order alone is never used to assign a source event. Original MG5 files and exact raw event bytes remain the authority for hard-process provenance; modified shower momenta are recorded separately.

| Source | Original event count | Original compressed SHA256 |
|---|---:|---|
| bbgg | 1000 | `bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343` |
| ccgg | 1000 | `3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef` |
| light-jjgg | 1000 | `606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030` |

Before processing, the streaming LHE preflight verifies the full gzip CRC, compressed/decompressed hashes, LHE initialization, process profile, source cards, finite hard-event records, source count and weight convention. The original file is rehashed after showering. A scratch `input.lhe` preserves the exact decompressed bytes; neither numerical reformatting nor replacement hard-event generation occurs.

`source_events.jsonl` archives every original source index, raw-event SHA256, nominal weight/scale and original hard-particle identities, mothers, colour tags and four-momenta/masses. The scratch LHE retains the complete original record. Event indices are one-based. Each source hash is SHA256 of the exact bytes from `<event>` through `</event>`, including original line endings and spacing within those markers. `source_index.dat` is a numerical comparison sidecar with the six LHE event-header fields and all thirteen particle columns. Its decimal text is for reader comparison; it does not redefine the source-byte hash.

The `TrackedLHA` adapter uses `Pythia8::LHAupLHEF` for all physics parsing. It retains `Beams:frameType=4` and the explicit verified `Beams:LHEF` path. Installed `BeamSetup.cc` honors a supplied LHA object for frame 4 when `useExternal()` is true; `setLHAupPtr` selects that object. The adapter copies the official reader's beam/PDF/process information and event record into the base LHA interface. It does not substitute frame 5, invent input particles or patch the upstream parser.

Every successful official `setEvent()` increments the raw-read cursor immediately. Independent comparison then checks the matching sidecar ordinal, process, weight, scale/couplings, particle count, IDs, statuses, mother indices, colour tags, momenta, masses, lifetime and spin. Only a fully compared record increments the verified cursor. A comparison failure therefore records a consumed input even though its verified identity is blocked; the source-event hash remains `UNKNOWN`, and the dependent run stops. Raw consumption and verified identity are separate counters.

A single `Pythia::next()` call can consume several LHE records. The adapter records these actual reads per processing attempt. Earlier verified reads that were internally rejected receive `INTERNAL_REJECTION` ledger rows; the actual selected source receives `WRITTEN`, `SHOWER_FAILED` or `PROCESSING_FAILED`. There is no replacement LHE generation. A bound of 64 source reads per `next()` protects this per-attempt in-memory audit; exceeding it stops with partial evidence. Requested limits are checked before asking the reader for another event, and an intentional limit is distinct from actual source EOF/truncation.

Each ledger row records:

- `source_sample_id`, original compressed `source_file_sha256`, one-based `source_event_index`, exact `source_event_content_hash`;
- deterministic `pythia_run_id`, fixed `pythia_seed`, `processing_attempt` and `processing_status`;
- one-based `output_event_index` equal to the actual HepMC event number, and exact `output_event_hash`, or null for a failed/unwritten record;
- signed original LHE weight, Pythia nominal weight, full-source normalization denominator, per-source cross-section contribution, SCALUP, converter weights and an explicit interpretation string.

The corresponding provenance fields are stored as HepMC event attributes. The output hash covers the exact ASCII event block from its `E` line up to the next event or the official footer. Each event is serialized once with the actual `WriterAscii` at 17-digit precision. Exact event bytes are retained in the combined file; gzip adds deterministic transport compression without changing them. No lossy reserialization or four-vector repair is used to pass QA or shrink publication samples.

The portable validator independently streams the original LHE, ledger and exact ASCII blocks and checks their hashes, indices, source identities, weights and output correspondence. A separately built real `ReaderAscii` validator checks physical event graphs, statuses, particle IDs, full stable-state charge/four-momentum accounting and mass-shell criteria. Its report binds the exact full decompressed ASCII SHA256. Both validators must inspect the same bytes before the CLI can report `PASS`.

The actual-reader API fixture was physically executed against an unchanged real LHE prefix. Correct metadata produced raw-read=verified-read=1; intentionally corrupt comparison metadata produced raw-read=1, verified-read=0, identity-failure=1; the limit fixture stopped before a further source read. This fixture calls no `Pythia::next()` and generates no physics event. Independent physical-run receipts supply the actual successful mapping counts and reproducibility evidence.

Run IDs are deterministic UUID5 values over source hash, settings hash, process, seed, requested prefix length and library versions. A separate random `execution_id` distinguishes local executions and stays in the manifest. This prevents a random execution label from changing the HepMC physics/provenance byte stream when testing the identical serial configuration. It does not claim reproducibility across threads, library/compiler changes or altered settings.

`particle_diagnostics.jsonl` preserves all original Pythia record entries, statuses, mother/daughter lists and four-vectors. No equivalence between Pythia indices and HepMC particle barcodes is assumed. Photon ancestry uses actual status-23 hard roots, excludes incoming beam protons from produced-hadron ancestry, and distinguishes a direct hadron decay path from an ambiguous hadron ancestor or shower path. Ambiguous origins remain explicit. Heavy-hadron record and terminal counts are diagnostic flavour categories; they do not assign every shower-produced heavy hadron to a particular original b/c parton. B_c is included in both inclusive heavy-flavour categories.

The preserved original primordial-kT-OFF 100-event bbgg run illustrates why execution and acceptance are separate. Pythia wrote 100 verified-source outputs, but the unchanged strict ReaderAscii audit assessed all 100 and found one invalid event (source/output index 54), with three stable particles failing mass-shell checks. The run remains `PARTIAL`; it is not a reference. The CLI now retains `N_readback=100`, `N_passed_validation=99`, `N_failed_validation=1`, `N_not_assessed=0` and `mass_shell_failed_particle_count=3` when such a report is returned. A failed invocation without an event-count report instead records `UNKNOWN`, not an invented failure count. The original failed output and original card remain unchanged.

Ten-/100-event stage runs, reproducibility repeats and published 100-event subsets reuse the corresponding original 1,000 hard events. They are not added to the unique hard-event statistics. The three physics categories retain separate source IDs and cross sections. Only successful final 1,000-input runs can contribute to the stated target of 3,000 assessed hard inputs.

The approved v2 command was physically executed for Stage A (10 bbgg), Stage B (100 each), Stage C (1,000 each) and a separate same-configuration 10-event reproducibility repeat. All final stage commands passed both independent validators. The final 1,000-event manifests, ledger rows and exact output-byte bindings were then inspected read-only; no additional events were generated by that inspection.

| Final full source | Raw inputs / attempts | Verified source identities | Successful showers / written / read back | Source identity failures / shower failures / internal rejections / validation failures |
|---|---:|---:|---:|---:|
| bbgg, seed 610201 | 1000 / 1000 | 1000 | 1000 / 1000 / 1000 | 0 / 0 / 0 / 0 |
| ccgg, seed 610202 | 1000 / 1000 | 1000 | 1000 / 1000 / 1000 | 0 / 0 / 0 / 0 |
| light-jjgg, seed 610203 | 1000 / 1000 | 1000 | 1000 / 1000 / 1000 | 0 / 0 / 0 / 0 |

Every final ledger has exactly 1,000 `WRITTEN` rows, distinct source indices/hashes and distinct output-event hashes. The actual source index equals the output number for these zero-rejection runs; this equality is an observed result of the reader audit, not an order-based fallback. Each source has 1,000 passed physical records and zero unassessed records. The raw consumed/verified totals are 3,000; prefix stages and repeats add zero independent hard statistics.

| Final full output | SHA256 of exact decompressed HepMC3 bytes |
|---|---|
| bbgg | `97ebc8dcbdd7ff249581a584f23e42e4d722961f65e8a370f6ca052d85c98db0` |
| ccgg | `8259af7279df4828249da9e0f68dc9b3bf8ffc54ae8e8a112e2c9c16adba83bc` |
| light-jjgg | `c62ba365bba6ddc4d4d1e613288af3215b89dce02d837f548f137b258d84ec5f` |

For each full run, this exact hash agrees among the saved file, ReaderAscii report and portable source-ledger report. The runner binary used for all three full runs is SHA256 `9e6e5973d6ecbdef14a204f30540797cca93f709e0521106970b0fea1094acda`; CLI source is `5ee33a7c42b89cef512d0531455d981e1607688e530db15380ac47f35685541f`. These identities bind the physically tested self-service implementation.

The actual same-source/settings/seed/limit/version 10-event repeat produced identical raw HepMC3 (`12381b3d2315c80f3c158088dbedfdd35ac4d809120158dabdcf98094b9bfa69`) and gzip (`874ccb3e2a4681a5e48a4f31ce02f143ca84a8b7ae1c7126c15b3615a6e6e731`) hashes. Ledger, source sidecar, original-Pythia diagnostics, ParticleData snapshot and both independent validation reports were also byte-identical. Direct diff verified that the only nonidentical effective-settings line is `Beams:LHEF`, which stores the different local scratch directory for the two executions. The complete settings snapshots were preserved rather than edited to manufacture identity. This is ten-event serial reproducibility in the tested installed environment, not a full 1,000-event repeated-run, cross-platform or multithread claim. Public receipt: [reproducibility_10.json](../simulation/pythia8/evidence/reproducibility_10.json).

**Final physical-run source mapping: PASS**, with the original failed v1 diagnostic run retained separately and excluded from the valid reference accounting.

# Phase 6C isolated Delphes and ROOT environment

Official Delphes 3.5.1 was built in an isolated user-owned WSL prefix against the existing ROOT 6.40.04/C++20 environment. The installed official `DelphesHepMC3` interface has physically processed a genuine ten-event bbgg prefix, and native ROOT opened its output with the actual Delphes dictionaries. This interface smoke establishes installation compatibility; formal self-service stages and scientific object/ancestry validation are separate acceptance evidence.

| Component | Verified identity |
|---|---|
| Delphes | Official tag `3.5.1`, commit `28658365abeb71ee36dfc739f9670c1514c0cb10` |
| Delphes source | [Official repository](https://github.com/delphes/delphes/tree/3.5.1) |
| Versioned archive | [Official tag archive](https://codeload.github.com/delphes/delphes/tar.gz/refs/tags/3.5.1) |
| Archive bytes/SHA256 | 5,012,371 / `b60d26d2ee2c84b58fbf2cf397fabd0ef3e89d3a0546d843c4ada82cc802d787` |
| Archive verification | Gzip CRC PASS; 900 source files match independent pinned Git bytes |
| Native ROOT | Existing 6.40.04; C++20 |
| Delphes compiler | Existing ROOT conda toolchain, GCC/G++ 15.3.0 |
| Dependency strategy | Upstream bundled Tcl 8.0.5 and FastJet 3.5.1; optional internal Pythia reader disabled |

The official source/derived-card license is GPLv3-or-later; original attribution and license text are retained. Upstream source is not vendored into the project repository and no upstream simulation source is patched. Existing Pythia/HepMC sources and installations are reused read-only for input validation.

Actual paths below replace only the local home prefix by `${HOME}` for publication:

| Purpose | Installed layout |
|---|---|
| Delphes prefix | `${HOME}/opt/delphes` |
| Native interface | `${HOME}/opt/delphes/bin/DelphesHepMC3` |
| Delphes library/dictionaries | `${HOME}/opt/delphes/lib/libDelphes.so` and five installed PCM files |
| Headers | `${HOME}/opt/delphes/include/classes`, `include/external/ExRootAnalysis` |
| Existing ROOT prefix | `${HOME}/miniforge3/envs/atlas-hh-root` |
| Official source/build | `${HOME}/.local/share/atlas-hh-phase6c/src/delphes-3.5.1`, `build/delphes-3.5.1` |
| Independent analyzer | `${HOME}/.local/share/atlas-hh-phase6c/build/analyzer/analyze_delphes` |
| Personal output root | `${HOME}/simulations/delphes_runs` |
| Local registration | `.local/delphes_installation.json`, or `DELPHES_LOCAL_CONFIG` |

The actual build used Release, `CMAKE_CXX_STANDARD=20`, required C++20, the existing conda C/C++ compilers, the existing ROOT prefix and parallelism two. `CMAKE_DISABLE_FIND_PACKAGE_Pythia8=ON` disables an unnecessary optional reader; this phase invokes the real HepMC3 interface. Actual bundled headers identify Tcl 8.0.5 and FastJet 3.5.1; the environment's external Tcl 8.6 is not loaded by this Delphes executable. The included implementations avoid new system packages. No sudo, ROOT reinstall, MG5/Pythia change or global compiler replacement occurred.

The initial resource snapshot recorded 7,862,480 KiB WSL memory and 1,007,966,097,408 free bytes on the checked filesystem. These are installation-time observations, not a continuing resource guarantee. The self-service controller rechecks live memory/storage, records CPU availability, processes one serial sample at a time and applies finite elapsed/output budgets. ROOT size/runtime predictions remain `UNKNOWN` until measured. Large personal ROOT files remain outside Git.

The upstream-interface smoke read an exact ten-event raw-block prefix of the published bbgg HepMC100 input. It produced 404,686 bytes of genuine ROOT output (SHA256 `2223339b3be9f66dd169db0198f4fae954fb2ea3f75a6ca7f09ee3f55a129326`). Native ROOT 6.40.04 confirmed ten `Delphes` entries and real `TClonesArray` branches including Event, Particle, Photon, Jet, MissingET, ScalarHT, Track and Tower, plus EFlow and GenJet. That smoke's initial receipt predates the subsequent native-schema readback; the separate schema evidence establishes readability. This smoke is not substituted for formal source-ledger/particle-content validation or independent hard statistics.

Installed source inspection confirms `DelphesHepMC3 card output.root input.hepmc3` uses a plain-file reader, parses the original HepMC event number, preserves it in `Event.Number`, stores the first weight in `Event.Weight` and persists the weight vector. Source p4/mass/weights are represented as `Float_t` in ROOT. The native adapter therefore compares actual event numbers and multiplicity-preserving source-particle tuples after explicit float32 conversion. Position identity includes original explicit-vertex x/y/z/ct in mm; implicit vertices are zero by the actual reader's construction. Native GenParticle X/Y/Z remain mm, while T is stored in seconds, `float(ct_mm*1e-3/2.99792458e8)`. It does not infer source identity solely from ROOT row order or invent Pythia/HepMC barcode equivalence. The official reader reorders candidates by vertex groups, making direct P-line index equality inappropriate.

The canonical detector card is SHA256 `cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47`. Runtime cards change only the global seed line to 610301/610302/610303. Actual `modules/Delphes.cc` applies `gRandom->SetSeed(confReader->GetInt("::RandomSeed",0))`; both canonical/runtime hashes and the effective source-defined seed are recorded. This is a study card, `FAST_SIM_ATLAS_LIKE` / `NOT_OFFICIAL_ATLAS`; its response and tagging functions are not an official ATLAS calibration.

The controller verifies pinned Delphes source, library/header/dictionary/binary hashes, actual ROOT/C++ build metadata, resolved ROOT/Delphes runtime paths and the unchanged Phase6B native-reader installation signatures. Exact input, source-manifest, ledger, Pythia settings and original MG5 cards/weights are bound before processing. Input limits copy exact ASCII event blocks and never reserialize physics content. Time/disk/stop failures retain local files and atomic status evidence; unknown native counts remain `UNKNOWN` rather than being inferred from a subprocess return code.

Fifteen controller/API tests physically passed, including timeout termination of a nonphysics process, stop/disk/overwrite protections, immutable card/seed transformation, bounded provenance records, observed native failure-counter retention, explicit/implicit position construction, exact two-event source-prefix/truth-index checks on existing real shower records, verified reader-library inspection under deliberately inherited incorrect Pythia environment values and the exact relative ROOT output argument. These tests invoke no Delphes processing and generate no MG5/Pythia physics events. Portable CI verifies published ROOT signatures, hashes, size limits, exact source/card/index relationships and hash-bound native reports; it does not execute a native ROOT readback or independently establish detector physics.

An activated ROOT shell initially supplied an inherited Pythia 8.312 data directory during the old Pythia C++ regression: two of five tests failed, and that result was preserved. Repeating with the original verified Pythia 8.317 data path and pinned scientific runtime directories passed all five tests; HepMC3's 31 upstream tests also passed. No source, data file, tolerance or installation was changed to obtain those results. The new controller scopes `PYTHIA8DATA` and the Pythia/HepMC library paths separately for source-reader verification and native input readback, so an activated ROOT shell cannot silently select the older data directory. Parent shell environment values remain unchanged. Existing portable suites passed 59 MG5 and 56 Pythia tests; final native/self-service regression results are recorded with the physical receipts.

Initial preserved environment signatures are ROOT conda history `b34431d29b37459623cf34ffd1dc8bb3fe54f9f7377bd108c40503459dbf81a7`, MG5 history `734fe80dec6447fd3d3ffb162752e898b9b7272282cb05472cab00c5e41bc3ce`, Pythia library `80291086e976c1caa2d47c6dec3bd0fe2e41bfe67637458101a43bba6e54620f`, HepMC3 library `f669ba0b71e6d011709535b1c61075105dc5b093251335aaac618df417af2bfc`, existing ROOT Core library `fcb0392d82ac33b7f41e310099cfde0e3165e0c83ca4ef89911df72e479e4472` and compatible ROOT-prefix C++ runtime `10f0d3c46c070acd4abea2ccf2500ff0ec77e9b90154b82ea2720dba05510cb9`. Final preservation/regression is reported after the formal runs.

Raw install, archive comparison, dictionary/runtime and smoke logs remain in ignored `.local/phase6c/`. The public evidence retains source/software hashes and omits the machine hostname and user-specific home prefix. No full1000 ROOT file, native binary or unapproved PDF/PNG figure is an automatic publication artifact.

The final self-service command was physically executed for all required stages. Stage A selects an exact ten-event prefix of the published100 bbgg input; Stage B processes the published100 inputs separately; Stage C reuses each checksum-pinned local Phase6B full1000 output. `--events` was therefore physically tested as a genuine unchanged event-prefix limit, not just a parser option. The source-reader preflight processes no detector events, and the formal dry-run returned `detector_events_processed=0` without creating the requested output directory.

| Stage/process | Input / read / processed / ROOT output | Invalid / skipped | Actual ROOT bytes | Whole-command seconds |
|---|---:|---:|---:|---:|
| A bbgg | 10 / 10 / 10 / 10 | 0 / 0 | 404,337 | 5.51 |
| B bbgg | 100 / 100 / 100 / 100 | 0 / 0 | 2,959,022 | 4.78 |
| B ccgg | 100 / 100 / 100 / 100 | 0 / 0 | 3,098,810 | 5.52 |
| B light-jjgg | 100 / 100 / 100 / 100 | 0 / 0 | 3,028,524 | 6.03 |
| C bbgg | 1000 / 1000 / 1000 / 1000 | 0 / 0 | 28,747,494 | 24.34 |
| C ccgg | 1000 / 1000 / 1000 / 1000 | 0 / 0 | 30,570,772 | 30.75 |
| C light-jjgg | 1000 / 1000 / 1000 / 1000 | 0 / 0 | 30,235,463 | 26.68 |
| Repeated A bbgg | 10 / 10 / 10 / 10 | 0 / 0 | 404,397 | 5.29 |

Every row passed actual C++ ROOT/dictionary/schema, source-event number, float32 particle/position/weight and analysis validation; the eight run receipts are in [native_runs.json](../simulation/delphes/evidence/native_runs.json). A separate real PyROOT audit recomputed per-event source/native weights, sorted photon/jet quantities, Cartesian masses, tags and source-weighted cutflows for the seven required stage runs and passed. The documented standalone native analyzer recheck was also physically executed and passed; it reuses existing ROOT records and adds no detector or hard events. Observed Delphes `VmHWM` samples for the C runs were 383,037,440 / 407,277,568 / 403,091,456 bytes; the controller labels these sampled child high-water observations rather than promising an unsampled peak or million-event performance. The full1000 ROOT files remain local.

The physically tested final controller source is SHA256 `ccfe87604fa669a9cecfbd46e9f997da0e5616654711f25e33ec34dd89d2353e`. A same-input/card/seed/version ten-event repeat produced identical scientific JSONL SHA256 `ab8026584d1b94edb1ca93e5f3162e35b0a03d62cebc913fbb47a1a2470fc340`. The actual ROOT hashes differed (`32cc87e062ff1d831b5413e5c870231d5be476ba0b3adceddd89022b4c9c26ca` versus `69df3fdf1d9c577d8161df6aa728620f8629d572b9e9c665dae4110a32834311`) because ROOT UUID/timing metadata is excluded from the scientific comparison. All three B100 scientific streams also exactly match the first100 records from their corresponding C1000 stream. This establishes scoped serial reproducibility; these repeats/subsets add no independent hard-process statistics. See [reproducibility.json](../simulation/delphes/evidence/reproducibility.json).

The initial A run is preserved as a failed diagnostic. Delphes wrote all ten entries; the first analyzer rejected a tiny signed native jet mass arising from double-precision cancellation. The source-defined ROOT signed-mass convention and a quantified double-cancellation bound were then implemented in the separate analyzer, preserving the raw signed mass and all actual ROOT event bytes. This was a representation fix, not physical event replacement, output repair or a relaxed detector selection. The separate publication-path issue was resolved by generating the revised sample with the relative output name `detector.root`; no private-path stripping or ROOT reserialization occurred. See [stage_a_initial_failure.json](../simulation/delphes/evidence/stage_a_initial_failure.json).

Final local Python discovery ran 35 tests: 27 active controls passed (15 controller/API, nine publication/audit and three statistical boundaries), and eight native tests were explicitly skipped in that environment. Two controller checks use existing verified local installation/source fixtures; portable CI also skips these two, giving 25 active controls and ten explicit skips. The native analyzer CTest passed 1/1; a separate compatible native run passed all eight adversarial ROOT checks, including short-tree counts, missing branch, event identity, momentum/position, nonfinite field and secondary-weight corruption. Existing MG5 59/Pythia 56 portable, Pythia C++ 5 and HepMC3 upstream 31 checks passed in their verified runtime contexts. These local physical checks remain separate from final submitted-head GitHub CI.

**Formal self-service Stage A/B/C and local environment compatibility: PASS.** Three thousand unique existing hard events were processed in Stage C; prefix stages and repeats do not increase that count. GitHub publication and final remote CI are assessed in the separate publication/decision reports.

# Phase 6B isolated environment

The real C++ external-LHE runner and independent HepMC3 reader build against verified Pythia 8.317 and HepMC3 3.3.1. Installation and build evidence was inspected on 2026-10-13. Source verification and API tests establish software readiness; the actual shower runs and scientific acceptance are reported separately.

| Component | Observed identity |
|---|---|
| Execution platform | Ubuntu WSL2, Linux 6.6.87.2, x86_64 |
| Pythia8 | 8.317; `PYTHIA_VERSION_INTEGER=8317` |
| Pythia official tag/commit | `pythia8317` / `83a5c9986f30746cfb390435a9b10ac55a758fca` |
| HepMC3 | Release 3.3.1; installed header/API version `3.03.01`, code `3003001` |
| HepMC3 official tag/commit | `3.3.1` / `beb66aa1a2ac263066becdee26d18ead83edec95` |
| Compiler | Ubuntu G++ 13.3.0; C++20 (`__cplusplus=202002`) |
| Build tools | CMake 3.28.3; Python 3.12.3; system zlib 1.3 |

Pythia was obtained from the [official versioned archive](https://pythia.org/releases/pythia83/pythia8317.tgz). Its compressed archive is 31,291,506 bytes and SHA256 is `1ae551d14dac495ddfe6b344792035ebe410fe6c6004d44a335e0ece0e745adf`. Gzip CRC and bounded tar extraction passed. An independent official Git checkout at the pinned commit was compared with the extracted release: 1,495 retained files matched byte-for-byte; no missing or different files were found. No upstream physics source was patched. HepMC3 was built from the pinned [official repository](https://gitlab.cern.ch/hepmc/HepMC3/-/tree/3.3.1). The supplied COPYING files contain GNU GPL version 2 for Pythia and GNU LGPL version 3 for HepMC3; the original source and license files remain local.

The following paths are the actual installed layout, with the machine-specific home prefix replaced by `${HOME}` for publication. Local configuration stores the resolved absolute paths.

| Purpose | Path |
|---|---|
| Pythia prefix | `${HOME}/opt/pythia8` |
| HepMC3 prefix | `${HOME}/opt/hepmc3` |
| Pythia XML/particle data | `${HOME}/opt/pythia8/share/Pythia8/xmldoc` |
| Source trees | `${HOME}/.local/share/atlas-hh-phase6b/src/pythia8317`, `src/hepmc3-3.3.1` |
| Runner build directory | `${HOME}/.local/share/atlas-hh-phase6b/build/runner` |
| Executables | `shower_lhef`, `validate_hepmc3` in that build directory |
| Local run root | `${HOME}/simulations/pythia8_runs` |
| Local installation contract | `.local/pythia8_installation.json` in the checkout |

Pythia configuration physically recorded `-O2 -std=c++20 -fPIC -Wall -Wextra -DGZIP`, with the isolated HepMC3 prefix enabled. HepMC3 used a Release/C++20 build with ROOT I/O, Python bindings and protobuf disabled. Its 31 upstream tests passed. The project uses the installed `Pythia8Plugins/HepMC3.h`, real `Pythia8ToHepMC3`, `WriterAscii` and `ReaderAscii` APIs. Both project binaries link to the exact isolated libraries through absolute RPATH; `ldd` resolved them without missing dependencies. The recorded library SHA256 values are:

| Library | SHA256 |
|---|---|
| `libpythia8.so` | `80291086e976c1caa2d47c6dec3bd0fe2e41bfe67637458101a43bba6e54620f` |
| `libHepMC3.so.4` | `f669ba0b71e6d011709535b1c61075105dc5b093251335aaac618df417af2bfc` |

Every self-service invocation checks recorded library, interface-header and installed XML hashes, actual binary version metadata and loaded library paths. Each run records the runner/independent-validator binary hashes. Merely finding a header or shared library is not treated as successful conversion.

An unmodified upstream `main224` example was physically run on a ten-event prefix of the existing bbgg LHE and its ASCII output was independently read. This was an interface compatibility smoke test. Its estimation/shower loops reuse the same prefix, and its example cross-section normalization is not used for the project references or counted as new independent hard statistics.

The project C++ suite physically passed five tests: SHA256 known vectors, photon-origin graph fixtures, actual ParticleData heavy-hadron classification, actual official LHE-reader cursor/failure/limit checks, and an installed `StringRegion::setUp` numerical failure reproduction. The cursor fixture calls the actual LHA reader but never `Pythia::next`; the StringRegion fixture evaluates only supplied four-vectors. None of these fixtures is a generated shower reference. Sixteen self-service control tests passed, including real nonphysics child-process timeout termination, stop/disk paths, streaming gzip preservation, unchanged LHE sidecar hashes, unsupported concurrency rejection and observed validation-failure counters.

The approved v2 self-service dry-run was physically executed, read back primordial-kT ON with the six explicit stock parameters, validated the complete 1,000-event source and processed zero physics events. It created no shower output directory. The baseline settings hash is `53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389`.

The same frozen command then physically passed the final Stage A ten-event bbgg test, Stage B 100 events per process and Stage C 1,000 events per process, with both independent validation layers. The three final full runs used runner binary SHA256 `9e6e5973d6ecbdef14a204f30540797cca93f709e0521106970b0fea1094acda` and CLI source SHA256 `5ee33a7c42b89cef512d0531455d981e1607688e530db15380ac47f35685541f`. A genuine ten-event serial repeat passed byte comparisons for the HepMC, ledger and original-Pythia diagnostic records; [event identity](phase6b_event_identity.md) states its exact scope and the preserved scratch-path difference in the effective-settings files.

The existing ROOT and MG5 conda histories were rehashed after these builds and tests, retaining `b34431d29b37459623cf34ffd1dc8bb3fe54f9f7377bd108c40503459dbf81a7` and `734fe80dec6447fd3d3ffb162752e898b9b7272282cb05472cab00c5e41bc3ce`, respectively. The runner invokes system Python and the isolated scientific libraries; it does not activate either existing environment. These history checks support environment preservation and do not substitute for the separate scientific regression suites.

The installation snapshot recorded 7,862,496 KiB total WSL memory. Live free RAM, logical CPUs, output-filesystem capacity and verified decompression bytes are recorded at each command invocation. The genuinely supported processing limit is one deterministic thread; `--jobs >1` is rejected. Runtime and HepMC output-size predictions remain `UNKNOWN` until measured; no million-event throughput or successful million-event execution is claimed. The CLI enforces finite elapsed/disk budgets, free-space reserve, process-group stop/timeout handling and atomic local manifests. No sudo, global toolchain change, ROOT/MG5 reinstall or Delphes installation is part of this workflow.

Raw installation/source-comparison logs, upstream smoke evidence, local signatures and control-test logs remain under ignored `.local/phase6b/`. Public reports retain software/source identities while omitting the local hostname and user-specific path prefix. Native binaries, source archives and large personal outputs are not publication payloads.

Remote source/reference acceptance is recorded in [GitHub publication](phase6b_github_publication.md). It uses exact downloaded bytes and actual successful jobs, separately from the physical tests above.

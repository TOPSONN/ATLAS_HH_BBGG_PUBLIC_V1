# MG5 V2 environment verification

MG5 3.5.16 was already installed. V2 reuses the same release-mode installation and isolated Python/compiler toolchain through a preferred user-owned symlink. No downloads, dependency reinstalls, ROOT changes, Pythia or Delphes installation were needed in V2.

Official source: https://github.com/mg5amcnlo/mg5amcnlo.git, tag v3.5.16, commit 3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7. The live GitHub tag was checked again. The upstream packaging recipe and all 4658 retained file hashes were verified. Source archive SHA256: 04d480ac64bdb5529351a9641aa0f328d11b2238c40d4777de3d2ad9afa906ca. Original setup/packaging/license evidence is retained, clearly distinct from the V2 reuse.

Actual tools: Python 3.12.15, GCC/G++/gfortran 14.4.0, make 4.4.1, six 1.17.0. MG5 directory measured 133902351 bytes; reused isolated toolchain 1247545255 bytes. These are apparent directory bytes, not new V2 download sizes or a complete account of shared conda caches. Preferred operator paths are documented in the Traditional Chinese guide; captured private paths are redacted in public evidence.

The interactive wrapper was physically started, given help/help generate and quit, and exited successfully. It validates installation identity and starts outside Git. Reference preflights measured 8 logical CPUs and about 7 GiB available RAM; CPU concurrency was explicitly 2 for references and 1 for the final CLI acceptance test. Resource snapshots are in per-run manifests. No large-run throughput or memory benchmark is claimed.

ROOT still reports 6.40.04 / C++20. Its conda history SHA256 before and after V2 remains b34431d29b37459623cf34ffd1dc8bb3fe54f9f7377bd108c40503459dbf81a7. The preserved main-baseline CTest build passed 5/5 again. This is the main baseline, not the unmerged Phase 5 test suite.

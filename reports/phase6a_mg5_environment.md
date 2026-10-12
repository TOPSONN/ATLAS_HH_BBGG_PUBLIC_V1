# Phase 6A environment evidence

Verified official source tag `v3.5.16`, commit `3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`, from [upstream MG5](https://github.com/mg5amcnlo/mg5amcnlo/tree/v3.5.16). VERSION reports 3.5.16 and 2026-06-03. License: adapted University of Illinois/NCSA. No existing MG5 or Fortran compiler was found during preflight.

Ubuntu WSL2, Python 3.12.15, six 1.17.0, conda-forge GCC/G++/gfortran 14.4.0 and make 4.4.1 are installed in a separate user-owned prefix. Initial WSL RAM: 7,678 MiB total, 7,182 MiB available; 8 logical CPUs. Initial free disk: about 943 GiB Linux, 687 GiB Windows. Resolved new download payload: 240,466,524 bytes (about 229.3 MiB). Source/tree and exact package URLs/hashes are recorded in simulation/mg5/evidence/environment.json and toolchain-linux-64.explicit.txt.

Official Launchpad requests timed out (30-second release HEAD and 20-second API request). No Launchpad tarball was downloaded. Instead the official pinned Git source was packaged locally using only upstream bin/create_release.py's directory transformations: remove developer utilities, rename compile utility and README. All 4658 retained files are checked byte-for-byte by SHA-256 before each self-service run; no physics source was patched. Source archive SHA-256: `04d480ac64bdb5529351a9641aa0f328d11b2238c40d4777de3d2ad9afa906ca`.

The raw Git checkout intentionally warns UNKNOWN DEVELOPMENT VERSION because it retains bin/create_release.py. Its ANSI comment bytes break XML. A separate verified release-mode directory is used for final samples; the original attempt is retained locally. Built-in CTEQ6L1 PDF source and table are hashed; LHAPDF, FastJet, eMELA and numpy/scipy are not required for these actual LO runs. Optional-tool warnings were retained in logs rather than misreported as installations.

No sudo, system package changes, Windows Python changes or global compiler changes occurred. The atlas-hh-root conda history SHA-256 remains `b34431d29b37459623cf34ffd1dc8bb3fe54f9f7377bd108c40503459dbf81a7`. ROOT 6.40.04 / C++20 was checked and its existing main baseline CTest ran fresh: 5/5 PASS. This is the main baseline suite, not Phase 5's 28-test branch suite.

Exact commands and outputs: simulation/mg5/USER_GUIDE_ZH_TW.md and simulation/mg5/evidence/. Raw installation commands/logs and source snapshot stay in the ignored local evidence directory. Public logs replace only machine-specific paths with documented placeholders.

Installed compiler license metadata: GCC/gfortran GPL-3.0-only WITH GCC-exception-3.1; make GPL-3.0-or-later; Python Python-2.0; six MIT. Exact package identities and hashes are in toolchain-package-identities.json; actual install and successful generation commands are in installation_and_generation_commands.txt.

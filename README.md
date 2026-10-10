# ATLAS_HH_BBGG_PUBLIC_V1

Independent project infrastructure for a future study of Higgs-boson pair
production in the bb gamma gamma final state using publicly released materials.
This is not an official ATLAS Collaboration project, result, or endorsement.

## Infrastructure and bounded exploratory scope

This repository contains Git initialization, environment reporting, a shared
development workflow for three independent computers, and compiled synthetic
ROOT smoke tests, public-source/schema audits, and bounded exploratory kinematic
reconstruction. Collision inputs are not committed. Phase 2 uses provisional
unit evidence and inclusive jets; it does not reproduce the official HH analysis.
See [Phase 2 validation](reports/phase2_kinematic_validation.md) and
[the Phase 2 decision](reports/phase2_decision.md). The additional CMake features
are opt-in, preserving the default Step 1 regression configuration.

Step 1 uses **C++20**, **CERN ROOT 6.40.04**, **CMake >= 3.20**, and **Ninja**
in the dedicated conda-forge environment `atlas-hh-root`. The selected ROOT
binary is also built with C++20. Missing ROOT or CMake remains acceptable for
the original Step 0 checks.

See [the Step 1 setup and validation guide](docs/STEP1_ROOT_CPP_SETUP.md) for
environment creation, explicit compiler selection, and the `linux-64` package
lock. After activating `atlas-hh-root`, run:

```bash
bash scripts/validate_step1.sh
```

Build products and synthetic ROOT files go to
`$HOME/build/atlas_hh_bbgg_public_v1`, outside this repository. PC2 and PC3
remain **PENDING** until this procedure is independently executed there.

## Public-data-only policy

- Use only data and documentation explicitly released for public use. Record
  source URLs, release versions, and applicable usage terms when analysis begins.
- Never commit internal ATLAS data, collaboration-restricted documents, private
  results, credentials, tokens, private keys, or personal environment files.
- Keep downloaded datasets, generated ROOT files, build products, and large
  outputs outside Git. The ignore rules are a first safeguard; review the actual
  staged diff and filenames before every commit and push.
- Public repository visibility does not grant rights to redistribute third-party
  materials. Respect their original licenses and attribution requirements.

## Three-computer development

PC1, PC2, and PC3 clone the same repository and authenticate independently.
Each task uses a distinct `feature/<task-name>` branch and a pull request.
After the initial Step 0 commit, task work must never be committed directly to
`main`. Merge only after explicit review and approval; then pull the latest
`main` on each computer with `--ff-only`.

The intended remote is `TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1`. Use the clone commands
in [the three-PC workflow](docs/THREE_PC_WORKFLOW.md) only after the publication
report confirms that the public remote and `origin/main` exist. Actual PC2 and
PC3 validation remains PENDING until performed on those computers.

## Read-only environment checks

Run from the project folder in PowerShell:

```powershell
powershell -NoProfile -File ./scripts/check_environment.ps1
```

Or in Bash on Linux, macOS, or Git Bash for Windows:

```bash
bash ./scripts/check_environment.sh
```

The scripts locate this repository from their own location, report Git, GitHub
CLI/authentication, compiler, CMake, ROOT, branch, origin, upstream, and working
tree state, and install nothing. They do not fetch, commit, merge, push, or alter
the working tree. Exit code `1` means a local Step 0 prerequisite needs attention;
missing compiler, CMake, or ROOT alone does not cause that exit code. Exit code
`0` describes local readiness only, not successful remote publication or testing
on another computer. Compiler presence does not establish C++20 compatibility.

See [THREE_PC_WORKFLOW.md](docs/THREE_PC_WORKFLOW.md) for authentication,
publication recovery, daily development, pull requests, and conflict recovery.

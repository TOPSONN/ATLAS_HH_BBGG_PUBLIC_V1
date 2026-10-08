# ATLAS_HH_BBGG_PUBLIC_V1

Independent project infrastructure for a future study of Higgs-boson pair
production in the bb gamma gamma final state using publicly released materials.
This is not an official ATLAS Collaboration project, result, or endorsement.

## Step 0 scope

This repository contains Git initialization, environment reporting, and a shared
development workflow for three independent computers. It contains no physics
analysis, scientific implementation, datasets, or ROOT installation.

The planned scientific stack is **C++17**, **CERN ROOT 6**, and **CMake**.
Compiler compatibility, ROOT configuration, and build configuration belong to
`STEP_1_ROOT_CPP_CMAKE_ENVIRONMENT`, which requires separate authorization.
Missing ROOT or CMake is acceptable during Step 0.

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
on another computer. Compiler presence does not establish C++17 compatibility.

See [THREE_PC_WORKFLOW.md](docs/THREE_PC_WORKFLOW.md) for authentication,
publication recovery, daily development, pull requests, and conflict recovery.

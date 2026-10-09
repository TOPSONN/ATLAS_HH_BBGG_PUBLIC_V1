# Step 1: ROOT, C++20, CMake, and Ninja

This step establishes software infrastructure on PC1 (Ubuntu WSL). All inputs
are deterministic synthetic values. The tests check ROOT I/O, RDataFrame,
and basic RooFit/RooStats object functionality; they do not validate a physics
analysis or perform a likelihood fit. PC2 and PC3 remain **PENDING**.

The project and installed ROOT binary both require **C++20**, with standard
extensions disabled. ROOT 6.40.04's selected conda-forge binary is
`root_base=6.40.04=cxx20_h8e038c3_1`. `root_base` supplies the compiled Core,
RIO, Tree, Hist, ROOTDataFrame, RooFit, and RooStats components used here.

## Environment creation

Use an existing user-local Miniforge installation. On PC1 it is already
installed under `$HOME/miniforge3`; this step does not reinstall it, change
global configuration, or modify unrelated environments. The installer was
Miniforge 26.7.2-0, verified against its official SHA256 before installation.
If another PC needs Miniforge, use the [official installation instructions](https://github.com/conda-forge/miniforge#install)
and verify the release checksum; do not pipe a downloaded installer into Bash.

From the repository's existing Linux/WSL source directory:

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
mamba env create --root-prefix "$HOME/miniforge3" --name atlas-hh-root \
  --no-rc --override-channels --channel conda-forge --strict-channel-priority \
  --platform linux-64 --file environment.yml --yes
conda activate atlas-hh-root
```

The environment name must be dedicated to this project. If it already exists,
inspect `conda list -n atlas-hh-root` first. Do not remove other environments or
silently replace an environment with unexpected contents. `environment.yml`
pins ROOT, its C++20 variant, and the tested compiler family/version; the
remaining requirements are solved at installation time.

For the exact tested `linux-64` package set, use the explicit specification
instead of solving `environment.yml`:

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda create --name atlas-hh-root --file environment-linux-64.lock.txt --yes
conda activate atlas-hh-root
```

The lock records every conda package URL and SHA256, includes `linux-64` and
`noarch` packages, and contains no environment prefix or credentials. It is
specific to Linux x86_64, including Ubuntu WSL; it is not a Windows or macOS
lock. Package availability, compatible host glibc, and a working Linux/WSL
installation remain prerequisites. This exact lock selects `x86_64_v3` CPU
packages; PC2/PC3 must support that instruction level. If another Linux x86_64
CPU cannot use this lock, solve `environment.yml` there and validate its own
resolved package set. ROOT was not installed with pip.

## Compiler selection and build

Keep sources in the existing repository (`/mnt/c/HH` on PC1). Build on the
Linux filesystem at `$HOME/build/atlas_hh_bbgg_public_v1`. Do not move or
duplicate the source repository for this step.

The installed `cxx-compiler` 2.0.0 package provides compiler binaries without
setting `CXX` during activation. Select ROOT's named conda compiler explicitly:

```bash
conda activate atlas-hh-root
export CXX="$CONDA_PREFIX/bin/$(root-config --cxx)"
"$CXX" --version
root-config --version
root-config --cflags
cmake --version
ninja --version
bash scripts/validate_step1.sh
```

The script also makes this compiler selection when `CXX` is unset. An existing
`CXX` outside the active environment is rejected. It checks the compiler stored
by CMake, every generated compile command (`-std=c++20`), ROOT's C++ standard,
and dynamically resolved ROOT/C++ libraries. The system C/C++ compiler is not
used. The conda compiler and development headers are 15.3.0; the conda solver
supplies libgcc/libstdc++ 16.2.0 as required by this ROOT binary. These runtime
libraries must resolve inside the same environment. System glibc and the Linux
dynamic loader are expected host dependencies.

The validation script executes these configure/build commands, using the
resolved compiler path, and then checks dynamic linkage and runs the tests:

```bash
cmake -S . -B "$HOME/build/atlas_hh_bbgg_public_v1" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_CXX_COMPILER="$CXX" -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
  -DROOT_DIR="$CONDA_PREFIX/cmake"
cmake --build "$HOME/build/atlas_hh_bbgg_public_v1" --parallel 2
env -u DISPLAY "$HOME/build/atlas_hh_bbgg_public_v1/root_smoke"
env -u DISPLAY ctest --test-dir "$HOME/build/atlas_hh_bbgg_public_v1" \
  --verbose --output-on-failure
```

Every executable also sets ROOT batch mode. `root_smoke` and each of the three
test executables can be invoked independently from the build directory.

## Test contracts and evidence

| Executable / CTest name | Deterministic checks |
| --- | --- |
| `root_smoke` (run separately) | ROOT initialization; TH1D write/reopen; 8 entries, integral 8, four bins containing 2 each, no flow entries |
| `test_root_io` / `root_io` | Weighted histogram write/reopen; 7 entries, integral 15, integral including flow bins 23; stored Sumw2 errors and four TTree rows |
| `test_rdataframe` / `rdataframe` | Eight in-memory rows; sum 32, squared sum 170, transformed sum 72; filtered count 4/sum 14; column values and histogram contents |
| `test_root_statistics` / `roofit_roostats` | RooGaussian evaluation/symmetry, workspace import, and ModelConfig object references; no fit |

Each validation run writes logs into a unique `step1_validation_<UTC>.<suffix>`
subdirectory of the chosen build directory, preserving earlier diagnostics:

- `step1_runtime_environment.txt`: actual versions, compiler path, ROOT flags,
  and key installed package build identifiers.
- `step1_cmake_environment.txt`, `CMakeCache.txt`, `compile_commands.json`:
  actual CMake compiler/ROOT configuration and C++20 compile commands (also
  retained at the build directory's top level).
- `step1_configure.log`, `step1_build.log`, `step1_linkage.log`,
  `step1_smoke.log`, `step1_ctest.log`, and a copy of CTest's `LastTest.log`.

`root_smoke.root` and `test_root_io.root` are generated synthetic I/O fixtures
at the build directory's top level. Running the tests regenerates these fixtures.

Logs, machine-specific paths, and generated ROOT files are not committed.
Earlier C++17 solver diagnostics and the six pre-resume drafts are preserved
locally under the ignored `.local` directory.

## PC1 resolved software and validation

Validated on 2026-10-09 (UTC) on PC1, Ubuntu 24.04.4 LTS, x86_64,
WSL 2.6.3.0 / Linux 6.6.87.2-microsoft-standard-WSL2. The existing manager
is Miniforge 26.7.2-0 / conda 26.7.2 / Mamba 2.9.0.

| Item | Actual validated value |
| --- | --- |
| ROOT | 6.40.04; `root_base` build `cxx20_h8e038c3_1` |
| ROOT / project C++ standard | 20 / 20; `CMAKE_CXX_STANDARD_REQUIRED=ON`, `CMAKE_CXX_EXTENSIONS=OFF`; all four compile commands use `-std=c++20` |
| Actual CMake compiler | GNU 15.3.0, conda-forge gcc 15.3.0-7 |
| Compiler location | `$HOME/miniforge3/envs/atlas-hh-root/bin/x86_64-conda-linux-gnu-c++`; the full resolved machine path is recorded in local evidence |
| Compiler implementation packages | `gcc_impl_linux-64=15.3.0=h6ad849d_7`, `gxx_impl_linux-64=15.3.0=h90d9265_7` |
| C++ runtime packages | `libgcc=16.2.0=ha9f2e26_7`, `libstdcxx=16.2.0=h934c35e_7`; `ldd` resolved both inside `atlas-hh-root` |
| CMake / Ninja | 4.4.4 / 1.13.2 |
| Build | Ninja Release; all four executables compiled and linked; parallelism 2 |
| Smoke test | PASS: 8 entries, integral 8, histogram reopened and bins checked |
| ROOT I/O | PASS: weighted histogram contents/errors and all four TTree rows checked |
| RDataFrame | PASS: all documented numerical, transformation, filtering, and histogram checks |
| RooFit / RooStats | PASS: object evaluation, workspace import, ModelConfig references; no fit |
| CTest | 3/3 PASS, 0 failures; successful run completed in 1.51 seconds |

The successful evidence directory is
`$HOME/build/atlas_hh_bbgg_public_v1/step1_validation_20261009T072335Z.rKTBiS`.
The initial compiled build and earlier checker diagnostics remain in the same
build tree. Before publication, the updated manifest was also checked with
`mamba install --file environment.yml --dry-run`: all requested packages were
already installed and no package changes were proposed. The explicit lock
contains all 186 conda packages with SHA256 hashes. Any Python distribution
metadata supplied by these packages is covered by the owning conda package.
An offline Mamba replay dry-run successfully planned all 186 exact lock
packages without creating another environment.

| Quality gate | Evidence / result |
| --- | --- |
| A: ROOT installation and components | PASS: ROOT version/flags, imported CMake targets, and seven dynamically linked ROOT components |
| B: C++20/compiler compatibility | PASS: CMake's actual GNU compiler, exact C++20 static assertions, generated compile commands, and conda runtime resolution |
| C: CMake configuration | PASS: exact ROOT CONFIG discovery and out-of-source Ninja configuration |
| D: Compiled executables | PASS: four C++ executables built and smoke executed successfully |
| E: ROOT I/O | PASS: smoke round trip and independent `root_io` test |
| F: RDataFrame | PASS: deterministic in-memory `rdataframe` test |
| G: RooFit/RooStats | PASS: dynamic linkage and `roofit_roostats` object checks |
| H: CTest | PASS: 3/3 tests, no display required |
| I: Reproducibility | PASS: manifest consistency and offline lock replay dry-runs, complete explicit linux-64 lock, commands, actual versions, and documented CPU requirements |
| J: Feature branch and PR | Publication requires `feature/step1-root-cpp-cmake` and a PR targeting `main`; the final publication evidence is recorded on GitHub and in the Step 1 report |

## Reproducing on PC2 and PC3

Clone or update the repository using the existing three-PC workflow; check out
`feature/step1-root-cpp-cmake` while its PR is pending, or the reviewed `main`
after an explicitly approved merge. Create and activate a separate local
`atlas-hh-root` environment using the lock above, then run the validation script.
Record that computer's actual compiler path, software versions, output logs,
and CTest result. A successful PC1 run does not validate PC2 or PC3.

To export a newly validated Linux environment, run the following only after
reviewing its package set and testing it:

```bash
conda list --name atlas-hh-root --explicit --sha256 > environment-linux-64.lock.txt
```

## Troubleshooting and scope boundary

- If ROOT's version/standard differs, inspect `root-config` and the installed
  `root_base`/`root_cxx_standard` records. Do not silently substitute a release
  or lower the project's standard.
- If a shell retains system `CXX`, explicitly set it to the conda compiler shown
  above. Keep CMake, Ninja, ROOT, compiler headers, and C++ runtimes in the same
  environment. The script rejects missing libraries or conda libraries resolved
  outside that environment.
- If an existing CMake cache belongs to another compiler or source directory,
  preserve it and pass a fresh Linux build directory as the script's first
  argument. Do not delete existing diagnostics to repair a cache mismatch.
- Installation failures should be recorded and repaired in `atlas-hh-root`
  only. No system package replacement or ROOT source build is part of this setup.

Work stops after Step 1 validation and creation of the feature-branch PR.
Step 2, ATLAS datasets, event selection, Monte Carlo, and physics likelihood
studies require separate authorization. The PR must not be merged automatically.

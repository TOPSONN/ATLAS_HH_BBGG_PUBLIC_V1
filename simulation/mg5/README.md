# Local MadGraph generation and independent references

Phase 6A is independent of Phase 5 PR #8 and starts at verified main
`f7a3420155bd557e4146fd1959a60f68742ea930`. It adds only a MadGraph tree-level
generation workflow. Historical ROOT data, reports and selections are preserved.

The user interface is documented in [USER_GUIDE_ZH_TW.md](USER_GUIDE_ZH_TW.md).
Use `scripts/mg5_cli.sh` for interactive MG5 and `scripts/generate_sample.sh`
for local, noninteractive generation. The latter reuses the registered
installation, validates every event and preserves actual cards, logs, banners,
LHE/LHE.GZ, cross sections and hashes. It has no Git publication operation.

Two explicit process profiles are provided: `cards/bbgg.mg5` and
`cards/diphoton.mg5`. Unknown process commands are rejected until their process
content and physical validation profile are implemented and reviewed. The
diphoton run is a separate self-service exercise, not a bbgg reference substitute.

Official source: [MG5 upstream](https://github.com/mg5amcnlo/mg5amcnlo), tag
`v3.5.16`, commit `3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`.
The source-only local release directory uses the upstream `bin/create_release.py`
directory packaging recipe. `prepare_release.py` performs that bounded recipe
without upstream tagging/pushing. It hashes all 4,658 unchanged retained files;
`installation.py` verifies them before every self-service run. No physics-source
patches are applied. The adapted University of Illinois/NCSA license was checked;
third-party source and process build directories are not committed here.

The Git checkout includes developer utilities that trigger an UNKNOWN DEVELOPMENT
VERSION warning and XML-invalid ANSI characters in its proc-card comments.
It is retained locally for provenance; only the verified release-mode directory
is registered for successful reference generation. An attempted complete hidden
card also exposed a legacy BEL character in a SysCalc comment; normal upstream
card writing with explicit user fields avoids it. Failed attempts are retained
locally and never published as validated references.

MG5 resets its mutable `Cards/run_card.dat` seed to 0 after finishing a run.
The actual card preserved here is the exact run-card text from the generated LHE
banner, checked against requested events, seed and energy. The post-run card is
kept separately in local run outputs. No seed is inferred from a template.

The independent `validate_lhe.py` uses only Python's standard library and
imports no MG5 code. Four-momentum tolerance is `1e-6 GeV + 5e-9 * incoming E`;
mass-shell tolerance is `1e-6 GeV^2 + 5e-9 * max(E^2,p^2,m^2,1)`.
These account for LHE decimal serialization and do not measure physics accuracy.
Every event is checked; failures reject the whole sample without event deletion.

The selected references and provenance manifest live under
`reference_samples/mg5/pp_bbgg_sm_lo_13tev/`. The CI checks them without installing
generators. Publication uses explicit paths and checks every staged and outgoing
commit payload; PDF/PNG figures remain subject to separate exact-version user
approval. This phase generates no figures and runs neither Pythia8 nor Delphes.

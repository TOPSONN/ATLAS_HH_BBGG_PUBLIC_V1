# Local MG5 self-service generation

Phase 6A V2 starts from verified `origin/main`, independently of unmerged Phase 5
PR #8. It reuses isolated MG5/tools and publishes only selected 100/1000-event
references. Production 10k/100k/1M generation and large-sample Release publication
are **NOT_EXECUTED_BY_DESIGN / NOT_EVALUATED** in this acceptance.

The Traditional Chinese operating instructions are in
[USER_GUIDE_ZH_TW.md](USER_GUIDE_ZH_TW.md). From Ubuntu WSL at `/mnt/c/HH`:

```bash
bash simulation/mg5/scripts/mg5_cli.sh
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 100 --seed 12345 --energy 13000 \
  --output "$HOME/simulations/mg5_runs/my_bbgg_100"
python3 -B simulation/mg5/scripts/validate_sample.py \
  --run "$HOME/simulations/mg5_runs/my_bbgg_100"
```

Local installation registration is ignored by Git. The preferred entry on this
machine is `/home/btu/opt/mg5amcnlo`, pointing to the verified existing release
directory. Ordinary commands reuse it. User outputs, process builds, grids and
logs stay outside Git under `~/simulations/mg5_runs/`. Each successful run saves
exact banner cards, original LHE bytes, deterministic gzip, independent per-event
validation, cross sections, counts and SHA-256. There is no automatic push.

`--dry-run` checks requests/resources without events. `--jobs`, `--max-hours` and
`--max-disk-gb` bound resources. A STOP file requests monitored termination;
partial attempts do not count. `--resume` revalidates completed runs or preserves
an interrupted attempt and starts a complete new attempt with the same request.
It does not resume partial MG5 integration. `generate_batches.sh` plans, runs,
monitors, stops, resumes and validates independent sequential batches. Sum counts
only after validation; repeated estimates of one cross section are not additive.

The frozen bbgg process uses `sm-no_b_mass`, a five-flavour proton and
`p p > b b~ a a QCD=2 QED=2`, tree level αs²αem². Built-in CTEQ6L1 is ID10042;
`maxjetflavor=4` applies b-specific cuts while retaining five-flavour initial
partons. Fixed muR/muF=125 GeV and finite pT/eta/ΔR cuts are in actual cards and
manifests. No NLO, shower, detector simulation or official ATLAS normalization is
claimed. The diphoton profile is separate; new processes need physics review and
corresponding validator code.

Official source: [MG5 upstream](https://github.com/mg5amcnlo/mg5amcnlo), tag
`v3.5.16`, commit `3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`. The source-only release
uses upstream `bin/create_release.py` directory packaging. `prepare_release.py`
performs that bounded recipe without upstream tagging/pushing. All 4658 retained
files are checked before generation. No physics sources, third-party packages or
large builds are committed; Pythia8 and Delphes are neither installed nor run.

MG5 may reset post-run `Cards/run_card.dat` iseed to0. The saved authoritative card
is the exact LHE banner card, checked against requested events, seed and beams.
Streaming `validate_sample.py` imports no MG5 code and checks all events, gzip,
XML, generator/model, finite values, PDGs/status, mass shell, four-momentum, cuts,
weights, cards, counts and hashes. Decimal-serialization tolerances do not measure
physics accuracy or production performance.

Only two allowlisted reference LHE.GZ files enter
`reference_samples/mg5/pp_bbgg_sm_lo_13tev/`, with provenance and bounded CI.
Standard-library CI needs no generator installation. Future selected large
samples use `publish_release.sh`: local read-only preflight by default; explicit
`--publish` uploads a draft and verifies remote sizes/downloaded SHA-256. Invalid
inputs, duplicate event content and oversized assets are rejected. No production
Release is created in this phase.
[GitHub's documented limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
are checked; no paid LFS is configured.

Stage explicit source/report/reference paths; audit staged files and each outgoing
commit before every push. New/modified PDF/PNG require separate user approval of
exact bytes and captions/provenance. This phase creates no figures, preserves
historical inputs and ROOT, never force-pushes and never automatically merges PRs.

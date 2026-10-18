# Phase7I next authorization: build and restart are separate

Current state: scientific source/method proposal only. **PRODUCTION_BUILD_EXECUTED: NO. PHYSICAL_RESTART_EXECUTED: NO. NEW_GENUINE_ME_CALLS / INTEGRALS / INDEPENDENT_EVENTS:0/0/0.** The prior one-attempt authorization remains consumed. The original stopped attempt, PID460 evidence and all old receipts/binaries remain immutable.

The next requested action is an explicit review and **BUILD approval** of the exact containing commit, Route-A scientific argument, corrected guard SHA256 `404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123`, proposed builder SHA256 `e74ee57c747e1a7d744a143789e7ee1fc15d5dde10ff41880ce1c454b32241c2`, dependency/card/toolchain contract and isolated build scope. No current metadata file is that authorization. A later approved build may perform only its separately approved preparation and zero-ME initialization checks; a new exact binary/source review is still required.

After an actual approved build, record new executable and dependency hashes, every immutable copied file, source bindings and complete unedited build receipt. Inspect real zero-ME preflights and resource/output safeguards. Use a never-used output directory; reject symlinks, old stopped outputs and modified receipts. Review preparation timestamps/resource measurements separately from binary identity and from the complete receipt predicate. If any identity differs from the approved review, stop and seek exact review rather than editing a receipt.

Only then request a separate explicit **PHYSICAL RESTART approval**, bound to the exact approved executable revision, reader/source binding, actual frozen receipt identity and reviewed fresh output directory. Stage A must start with seed910001 and stop on the first scientific/output/resource gate failure. Do not reuse the old executable or infer approval from passing tests, a Draft PR, CI, build completion or a source proposal. Other seeds require true Stage A acceptance under that later bounded authorization; no automatic retry or replacement seed.

The unchanged physics contract SHA256 is `a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`: MG5 3.5.16 loop_sm, full finite mt/mb LO gg->HH, MH125/MT173/MB4.7 GeV,13TeV beams, kappa_lambda=kappa_top=1, CTEQ6L1/alpha_s(MZ)=.130/one-loop, muR=muF=mHH/2, multichannel0, exact helicity sum, configuration1. Seeds remain910001,910019,910037,910061. Preserve14400s aggregate CPU and14400s wall,1 job/1 worker,5GiB extra disk and0 permanent physical LHE records. No Pythia, Delphes, corrected-SM1000 generation, alternative integrator or automatic budget reset is included.

The documented review command below was actually executed with the installed compiler and runs only nonphysical guard/RNG/source/receipt methods:

```sh
python3 -B -m unittest simulation.hh_signal.final_closure.guard_correction.test_correction -v
```

Set `FC` to the existing gfortran when it is not on PATH. A fresh local method-evidence directory can be created without any production dispatch:

```sh
python3 -B -m simulation.hh_signal.final_closure.guard_correction.methods \
  --output "$PWD/.local/guard_method_review_01" --optimization O0
```

Both-O0/-O2 routes were physically executed as scalar method fixtures. No production build or Stage A command is offered as authorized. The historical failed predicate remains `UNKNOWN_UNLESS_NEW_EVIDENCE_EXISTS`; this source correction does not retrospectively identify it.

# Phase7I exact-source authorized restart: stopped Stage A

**FINAL_VERDICT: BLOCKED_NATIVE_RUNTIME. One authorized CLI invocation and one real native dispatch occurred. Stage A exited92; measurement and the other three seeds were never started.**

The executed source is **`58d39888a024028e32f3071db9215c0db6fe0a89`** from the approved standalone checkout. The report-only head `be106725481a58873b8e13a0dd72f03599865ac9` was not executed. The frozen build remains **`98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281`**. No runtime code, native source, binary or receipt was rebuilt, patched, refreshed or replaced. No automatic restart followed the failure.

The approved output role is `LOCAL_HOME/simulations/hh_final_closure/restart_feasibility_58d39888_01`. Public evidence replaces private roots by roles; original local records remain unchanged. Actual source and later report-publication HEAD are different identities. The containing report commit and exact final-head CI are recorded after publication in PR24 and the final delivery, avoiding a self-referential commit hash.

## What actually ran

The separate mandatory pre-dispatch audit passed, including full Git verification in20.832652s, complete build/source binding, exact3493-file prepared inventory, frozen physics/cards/static and dynamic dependencies, RAM/disk, Landlock ABI3, sealing support, no competing native process/lock and full historical preservation. The existing reviewed execution command then independently passed its own full1257-tracked-file Git precheck in32.828157s. This execution therefore crossed the previous Git blocker.

The actual supervised executable for seed910001 ran as **PID460**, reached native configuration/input parsing and initialized RANMAR, then terminated with **`STOP 92` / `NATIVE_EXIT:92`**. The receipt class is `REAL_NATIVE_SUPERVISED`, not a method or pre-ME fixture. Captured scalar records were:

```text
HH_PRE_SAMPLING_CONFIG_PASS 910001 0 0
HI_INPUTS 250 4 4 2 0 F
HI_PDF cteq6l1 cteq6l1 cteq6l1
HI_ALPHA 0.13000000000000000 1
HI_MASS 125 173 4.7
HI_SCALE 4 0.5 F F F
HI_BEAMS 6500 6500 1 1
HI_SEED 910001 0 0 1 26066 23739
```

These are normalized whitespace renderings of actual retained scalar lines; the public receipt contains their original text. The initial guard also checks the one-loop alpha_s value at250GeV, PDFSUP10042, masses and beam/scaling settings. These initial checks do not prove the subsequent per-point guard passed.

There are **zero flushed `HI_ME_ENTRY`/`HI_ME_RETURN` observations**. No `HI_COUNTS`, `HI_NATIVE_LOOP_COUNT`, `HI_LOOP_CODE`, `HI_ITERATION`, `HI_RESULT` or `HI_COMPLETE` was emitted. Source inspection places `hi_point(PP,G1,G2)` immediately before `SMATRIX1(P1,DSIGUU)`, with three flushed instrumentation sites covering the outer loop entries. Thus no instrumented outer HH ME entry was reached in the captured protocol. A final numerical ME counter was not emitted, and the integrand-call count is **unavailable**, rather than a fabricated zero. No complete integral, cross section or native uncertainty exists.

## Failure localization and limits

The frozen `hi_point` has five STOP92 branches: nonpositive point scale or negative gluon PDF; renormalization-scale mismatch; factorization-scale mismatch; nonpositive coupling-derived alpha_s; and mismatch with the required one-loop running value. The actual exit does not identify a branch or retain rejected point values. This report therefore does **not** attribute the failure to a particular PDF, scale, coupling or numerical tolerance. No debugger, replay, new diagnostic point or alternative executable was run. STOP92 is the Fortran process stop, not a MadLoop return-code observation.

The synthetic point-method review remains historical method evidence. It manually supplies valid synthetic scale/coupling/PDF values and cannot certify their actual native point setup. Initial configuration acceptance and synthetic tests must not be relabelled as a completed full-loop runtime validation. See [source map](phase7i_exact_restart_evidence/failure_source_map.json).

## Stage, statistics and retention

| Field | Actual result |
| --- | --- |
| STAGE_A_STATUS | FAILED_PARTIAL_PRESERVED, native exit92 |
| STAGE_A_ACTUAL_ME_CALLS | zero flushed outer-entry observations; final counter not emitted |
| STAGE_A_CROSS_SECTION_PB | UNAVAILABLE |
| STAGE_A_INTERNAL_ERROR_PB | UNAVAILABLE |
| STAGE_A_GRID | ftn26 empty,0 bytes; no validated grid |
| STAGE_A_LOOP_DIAGNOSTICS | NOT_REACHED |
| STAGE_A_WRITER_VALIDATION | NOT_REACHED; no H_IO/tail protocol |
| STAGE_A_ZERO_RETENTION | PASS filesystem postcondition only |
| REPLICA_910001 | adaptation failed; no measurement |
| REPLICA_910019 /910037 /910061 | NOT_STARTED |
| COMPLETED_REPLICAS | 0 |
| INTEGRATION_MEAN_PB / BETWEEN_REPLICA_SE / INTERNAL_ERRORS | UNAVAILABLE; no estimates |
| CONVERGENCE_VERDICT | NOT_EVALUABLE_NO_COMPLETED_INTEGRALS |
| NEW_INDEPENDENT_EVENTS / RETAINED_PHYSICAL_LHE | 0 /0 |

No useful grid hash exists: the empty ftn26 SHA256 is e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855, an empty-file fingerprint rather than grid provenance. results.dat and grid_information are also empty. The seven actual Stage A files and empty temporary directory pass an independent event-output audit. This proves the final filesystem retention condition; it does not validate scratch writer/readback behavior that was never reached. Zero sampled anonymous files is not a claim that no transient inode ever existed.

The physics target remains finite mt/mb full-loop LO gg->HH, loop_sm/MG53.5.16;13TeV;MH/MT/MB125/173/4.7GeV;kappa_lambda=kappa_top=1;CTEQ6L1;alpha_s(MZ)=0.130 one-loop;muR=muF=mHH/2;coherent multichannel0;exact helicity sum;configuration1. Physics SHA256 `a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`. No HEFT, NLO/K-factor, shower, HepMC, Delphes or corrected SM1000 production occurred.

## Resources and immutable preservation

| Measurement scope | Actual value |
| --- | --- |
| Runtime Budget CPU / wall | 1.095151761s / 1.808457469s |
| Whole CLI including Git | user1.65s +system2.87s CPU;37.31s wall (GNU time rounded) |
| Supervised native stage wall | 0.292279523s |
| CLI kernel ru_maxrss | 27908KiB; process-tree maximum, not simultaneous RSS sum or native-only peak |
| Runtime peak accounted disk | 1132695157 bytes |
| New runtime files | 8 files / 28158 bytes |
| Resource stop | NONE; native exit92 caused the stop |

The original14400s CPU/14400s wall, one job/worker,5GiB cap and stricter2GiB disk stop remained in force. The supervisor killed/reaped the process group. No further stage, seed, replacement workspace or budget expansion followed. Native-only peak memory was not separately sampled during the0.292s lifetime.

All **3493 prepared files**, all **five aggregate/per-replica build receipts** and all3488 frozen artifacts remain byte-identical. The previous stopped attempt remains **3603 unchanged files**, inventory `5164541051b85a11d8ebe94c43373da88f9a2c43490a055e6afc450887c23d16`, old Git-timeout failure SHA256 `a68d27baf2a23f3a850a4cf683682eb56029cdd60e6bb7b0da2e2ea0b2b1d11e`. All **8420 historical campaign files /752305317 bytes** match the protected SHA256 inventory, preserving B100/C1000/D6000 and historical PDF/alpha_s identities. The new stopped output has3501 files, inventory `6f00d59c8a9dc36ed262091f2a5a7b2ffb7e4edf2ffdf0f3961f848c8a021999`, original execution receipt SHA256 `c263adf18b77b16d9322cc71cd379e709cc7ee25d1408715a1a42e3c2fd198e4`. Its execution marker now forbids reuse; the older stopped-output guard also remains effective.

## Regression, publication and next step

**60 exact-source nonphysical runtime/Git/hash/kernel method tests,10 independent partial-receipt tests and seven read-only reference/evidence validators passed.** The independent scalar auditor imports no runtime module and cannot dispatch native physics. Negative tests reject method-as-native claims, source/seed drift, a promoted completed result, invented final counters and any measurement/other seed following Stage A failure. These are method/preservation successes, not a passing integration or convergence claim. Historical validators retain their historical authorization labels; this additive receipt records the newly authorized failed attempt separately.

Only bounded source-level audit code/tests, scalar protocol, hashes, resource summaries and reports are published. No binaries, grids, scratch candidates, LHE, installations/caches or unapproved PDF/PNG are staged. PR24 stays OPEN/Draft, with no merge or force push. Final-head GitHub CI is read only after completion and recorded in PR24 and final delivery; a passing CI cannot turn the failed physical Stage A into PASS.

**GATES_PASS:** exact authorization/source/build/freshness/resource/kernel/Git gates, actual native dispatch and initial seed/configuration, failure cleanup, zero-retention postcondition, historical/frozen preservation, nonphysical regression.

**GATES_FAIL:** actual Stage A point validation exited92.

**GATES_BLOCKED:** measurement, other seeds, further physical attempts; full ME/grid/writer/tail/result validation and cross-section interpretation.

**GATES_UNKNOWN:** precise STOP92 predicate and point values, final counters, loop/writer behavior, native-only peak memory and any cross section/error/convergence.

**NEXT_RECOMMENDED_STEP:** separate read-only review of the native point/observer diagnostic contract. Any diagnostic source revision, rebuild or physical retry requires new explicit review and authorization. Preserve both stopped outputs. No corrective patch or retry is part of this delivery.

All requested fields are in [final_report.json](phase7i_exact_restart_evidence/final_report.json). The [original scalar receipt public projection](phase7i_exact_restart_evidence/execution_receipt.public.json), [preservation](phase7i_exact_restart_evidence/preservation.json), [independent audit](phase7i_exact_restart_evidence/independent_receipt_audit.json) and [regression](phase7i_exact_restart_evidence/regression.json) retain the distinctions above.

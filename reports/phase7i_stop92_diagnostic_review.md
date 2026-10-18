# Phase7I diagnostic overlay review

Verdict: **BLOCKED_POINT_GUARD_SEMANTICS** for a physical restart; **PASS_NONPHYSICAL_METHODS_ONLY** for the proposed failure observability. This proposal neither fixes nor bypasses the scale-ownership discrepancy.

Original guard SHA256: `5cbe786a92c872cdbcd43440f8c5b8894b6d27da1ec883c66fc4ba6d402dabfb`.

Candidate full guard SHA256: `f235b6030461f4e71f4cb6563ef816201e775ad4c6255d337839ad6584571bc2`.

The [exact overlay](../simulation/hh_signal/final_closure/stop92_diagnostic/native_checks_diagnostic.f), [diff](../simulation/hh_signal/final_closure/stop92_diagnostic/native_checks_diagnostic.patch) and deterministic [generator/reversal validator](../simulation/hh_signal/final_closure/stop92_diagnostic/overlay.py) are isolated from `integration_runtime/`. The original guard, supervisor, production builder and frozen executables remain byte-identical. This commit's containing Git revision identifies the review proposal; the candidate is not a reviewed production binary. Source-file hashes and evidence hashes are also recorded in metadata.

Each of the five exact predicates gets its own identifier and scalar schema. One formatted WRITE contains the whole record, followed by explicit FLUSH(6), immediate STOP92 and ENDIF. There is no failure recovery, point replacement, widened tolerance, new physics prescription or success-path I/O. NaN/Inf behavior, predicate precedence and the existing unchecked-q2fact gap remain as measured in the [predicate audit](phase7i_stop92_predicate_audit.md).

## Supervisor and partial receipt

The existing supervisor appends a complete HI_ line before raising on HI_FAILURE, then kills/reaps the process group. A two-line diagnostic would risk losing the scalar line; this design uses a single line. Its `failure` string and `records` retain the same complete first record. The independent strict parser accepts only the five schemas, caps bytes and rejects event/vector fields. It is a review/receipt reader and is not wired into a physical execution route.

Six compiled artificial failures were run through the **unchanged** supervisor: all five STOP92 IDs and the original STOP90 nonfinite path. Every partial receipt preserved exactly one complete first-failure record, raw streams were discarded, all allowed output files remained empty and scratch stayed empty. Group cleanup was performed. A supervised exit may be92 or a kill signal because HI_FAILURE remains immediately fatal; the direct method tests independently verify STOP92. No artificial delay or weakened supervisor was introduced to force a particular exit race. See both method evidence files.

The diagnostic only writes to existing stdout. It requests no filesystem exception, named scratch or writer permission. Landlock, anonymous scratch restrictions, resource budgets and output retention rules remain unmodified. Actual Landlock-supervised method tests passed; these are not a replay of physical Stage A.

## Actual validation and limitations

Eight new regression tests cover the full24-case matrix at both optimization levels, exact reversible projection, source drift/weakened predicates, finite semantics, scalar schema/bounds and concurrent stateless receipt readers. The native jobs themselves run sequentially. Independently seeded physics or genuine RNG sampling is absent. Seventeen scalar native ALPHAS probes and441 deterministic scale-expression checks passed independent numerical comparisons.

The broader local suite passed143 tests, including Phase7H native I/O semantics, Phase7I native configuration, Git layout/timeouts/negative checks and source-binding protections. Seven existing validator commands also passed: closure interpretation, published native-readback evidence, signal references, new-background references, MG5 LHE library, Pythia HepMC library and Delphes references. These portable validators inspect old evidence/files; they do not constitute fresh shower, detector or ROOT production. The old interpretation validator intentionally retains its original authorization status; no historical report was rewritten to match this later task.

The only pre-existing source changes outside the new diagnostic directory are an added nonphysical CI step and **one exact required metadata pathname** added to two payload allowlists, including its declared compatibility variant and negative regression. No general metadata prefix was opened. No PDF/PNG, executable, object, archive or sample is in this delivery.

[Preservation evidence](phase7i_stop92_evidence/preservation.json) verifies all3501 stopped-attempt files,3603 older stopped-attempt files and8420 campaign files, all four original executables, old published failure evidence, original15 runtime sources and old local CI evidence. The original failed Stage A remains a genuine failed validation attempt.

Final-head hosted CI and remote byte readback are post-publication observations, reported on PR24 and the final delivery receipt. They are not predicted here. The [next runtime plan](phase7i_stop92_next_runtime_plan.md) defines the still-closed physical gates.

# Route-A actual builder and strict receipt-reader activation

Source engineering only, based on `1b0b34bb0ee57b7ea8b073ffa49262b5e434cf00`.
The exact new source revision is the containing commit published on PR24. Separate explicit BUILD_ONLY
approval must name that complete SHA; no build or physical restart was authorized or executed here.

The production builder now uses the reviewed Route-A guard `404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123` in fresh subprocess copies.
The exact old proposal (`e74ee57c747e1a7d744a143789e7ee1fc15d5dde10ff41880ce1c454b32241c2`) and its reversible
original-builder projection remain preserved. The activation diff adds the actual reader contract,
out-of-band human gates, explicit compile/link planning, and bounded sequential child bookkeeping.
Active builder SHA256: `1cdb81e25d0544b5d7b630d8a34bdb1dd92d36083b00925017d900ab032a0736`.
Reader aggregate SHA256 (six explicitly enumerated files): `7b7f00107b93a6177564faa05230cf571cccc6b1a7e27a94c3dbcbacf02e18ea`.
Complete source-binding identity (276 source/card/contract entries): `ad48f3f5a79227faf3a9444b599d31ee83340874eddcc4cc4d2e36632a2fa038`.

The actual reader retains schema `HH_ROUTE_A_GUARD_BUILD_REVIEW_V1`, checks exact source revision,
physics and guard, complete source/card bindings, original copies plus the reviewed overlays,
four seeds, actual executable/dependency/toolchain hashes, the immutable inventory and compile plan,
real zero-ME initialization records, retained-output postconditions and exit80 entry-denial evidence.
`verify-build` is non-executing and reports pending binary review. Dynamic linkage re-evaluation is
permitted only after independent exact-full-receipt human binary review. A self-edited receipt cannot
create the process-local HumanReview capability or reuse its exact receipt digest.

BUILD_ONLY, BINARY_REVIEW and PHYSICAL_RESTART have distinct action/revision/source/output/receipt
scope digests. No JSON, CLI approval flag or environment value issues approval. A trusted external
human decision must precede the controlling-terminal confirmation; this is an operator boundary,
not protection against arbitrary code execution by the account owner. The default programmatic
physical dispatcher rejects absent approval before creating output or native capabilities.

FULL_BUILD_RECEIPT_IDENTITY hashes the complete canonical JSON including all actual timestamps,
PIDs, CPU/wall/resource and preflight observations. IMMUTABLE_BINARY_SOURCE_IDENTITY covers actual
compiled scientific/source/card/executable/library/compile-plan identities, excluding observations.
No new production executable hash exists in this delivery. The installed toolchain inventory was
read and hashed only; no production compilation, installation or reinstallation occurred.

Nonphysical validation: **189-test final full suite and seven reference validators passed**.
Additional focused32-method checks also passed. Cases exercise terminal I/O, SONAMEs, descendant CPU,
canonical ordering, lossless inventory encoding and strict bounded Git blob batches. The guard matrix
exercises 47 cases across original/diagnostic/corrected source at O0 and O2, plus frozen RNG,
bookkeeping, independent arithmetic and bounded fatal diagnostics. The new32 tests cover active
compile/link planning, binary/source/dependency/receipt edits, wrong schema/guard/seeds, missing
preflights/entry-denial, stale/fake human approval, consumed workspaces and Python-only process
budget termination. Positive synthetic receipt checks are METHOD ONLY and mock the production
clone/toolchain/dependency context; they do not verify an actual newly built executable.
An isolated PTY probe exposed Python r+ requiring a seekable stream; the final terminal implementation
uses separate read/write streams and the final32 methods pass, including real isolated PTY I/O.
The reader preserves the loader SONAME separately from the resolved shared-library filename;
hashes bind the actual resolved bytes and reviewed dynamic-linkage readback binds the SONAME.
The build supervisor conservatively charges elapsed one-core group time against remaining CPU while
compiler descendants are alive, before their reaped CPU usage becomes visible. A Python-only
descendant fixture verifies group termination under that aggregate CPU reserve.
Source bindings sort by canonical POSIX spelling rather than host-dependent Path ordering, keeping
the complete manifest identity identical between the Windows review and Linux execution environment.
The unpublished first candidate's full tracked preflight stopped at GIT_OUTPUT_CAP because its
1397619-byte toolchain ledger exceeded the existing1MiB Git output bound. The corrected source uses
lossless parent-directory grouping (886809bytes), restoring all8166 identical path/hash rows and their
canonical list identity ecfbf6ad24584259f97ddb11d33dbabf45685fcb9defad0bc572f7c7149981cc.
The Git output cap and all physical budgets remain unchanged. The unpublished candidate is retained
locally, and the exact final containing revision requires independent build approval. No build ran.
The second unpublished candidate reached the unchanged180s Git watchdog while invoking per-file Git
processes for the expanded276-entry source binding. Bounded cat-file batches replace only those repeated
blob reads, with exact SHA1 headers and SHA256 body checks; both full tracked status scans, race checks,
30s CPU,180s overall and1MiB output limits remain. Missing/truncated/wrong-hash/extra batch data and
two550kB method fixtures exercise fail-closed parsing and exact full-worktree semantics.
An intermediate extra focused command omitted FC and did not start its two native matrix cases;
the final182-test command explicitly binds the existing compiler and passes without reinstalling.

SHA256 preservation passed for8420 historical campaign files,3501 genuine stopped files and3603
older stopped files, plus568 protected public artifacts. Historical receipt identity
`98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281` and its four executable hashes remain
unchanged and independently audit-readable. The prior Python-only rebinding exception was not widened;
the new historical path checks the frozen historical identity and grants audit access only.
PID460 and its actual STOP92 branch remain unchanged/UNKNOWN. B100/C1000/D6000 events, cards and weights
were not rewritten. The existing CRLF working-copy difference recorded in preservation.json was retained.

The scientific target and resource envelope remain frozen: finite-mass no-Born LO only; seeds
910001/910019/910037/910061; aggregate wall/CPU14400s;1job/1worker;5GiB additional disk;
0retained physical LHE. No genuine ME, new integral, hard event, Pythia or Delphes production ran.
Native scientific convergence and future build/preflight behavior remain unmeasured pending approval.

See [Traditional Chinese build guide](../simulation/hh_signal/final_closure/integration_runtime/BUILD_GUIDE_ZH_TW.md),
[bounded evidence](phase7i_route_a_activation_evidence/source_activation_audit.json),
and [future build contract](../metadata/phase7_final_route_a_build_contract.json).

CI and raw remote blob checks must be verified for the final exact head after publication; those
post-commit observations are delivered separately with that SHA. PR24 must remain OPEN/DRAFT.
No PDF/PNG, binary, object, physical sample or scratch is part of this payload.

Source activation verdict: PASS_ROUTE_A_SOURCE_ACTIVATION_READY_FOR_BUILD_APPROVAL.
Next step: separate explicit BUILD_ONLY approval of the exact new commit; no further readiness-only phase.

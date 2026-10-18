# Phase7I minimal scientific guard proposal

Route A is justified in the [ownership/dependency audit](phase7i_scale_ownership_final.md). The original active guard, diagnostic-only candidate and stopped executable are unchanged. The [corrected candidate](../simulation/hh_signal/final_closure/guard_correction/native_checks_corrected.f) is an isolated source proposal.

| Source | SHA256 |
| --- | --- |
| Original guard |5cbe786a92c872cdbcd43440f8c5b8894b6d27da1ec883c66fc4ba6d402dabfb|
| Diagnostic-only candidate |f235b6030461f4e71f4cb6563ef816201e775ad4c6255d337839ad6584571bc2|
| Corrected scientific candidate |404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123|

The [exact reversible diff](../simulation/hh_signal/final_closure/guard_correction/native_checks_corrected.patch) is generated and reversed by [overlay.py](../simulation/hh_signal/final_closure/guard_correction/overlay.py). Reversal restores the original exact bytes. The corrected predicate itself is intentionally **not** byte-identical or failure-equivalent to the original.

## Intentional semantic changes

1. Check each incoming component of legs1/2 for finiteness before computing the invariant. This prevents max(0,NaN) from concealing a nonfinite momentum. Use the existing `HI_FAILURE NONFINITE`, FLUSH and STOP90; no momentum values are logged.
2. Check native scale and both q2fact elements for finiteness before **any scale ratio**. NaN/+Inf/-Inf factorization values now give STOP90. Previously NaN could pass and Inf gave finite-mismatch STOP92. Negative finite QF² still fails STOP92 without clamping.
3. Replace abs(model MU_R/q-1)>1e-10 with abs(native scale/q-1)>1e-10, retaining1e-10. Also require native scale and the independent model reduction reference to be positive; nonpositive values give the renormalization-scale STOP92 identifier. Model MU_R remains finite-checked, but a legitimate positive reference is not forced equal to q.
4. Retain all five branch identifiers, bounded scalar-only messages, explicit flush and immediate STOP92. The renormalization record now labels `native_scale_over_q` and `model_MU_R_GeV` distinctly. A versioned strict parser rejects the old renormalization schema rather than silently relabeling its model ratio.

Nonfinite incoming components are checked first, then q/model-reference/PDF finiteness, then native-scale/QF finiteness. Only afterward are the ordered Q-or-PDF, renormalization, factorization, nonpositive-alpha and running-alpha predicates evaluated. Thus new finite coverage intentionally outranks finite mismatch tests in multiple-invalid cases. Derived-alpha finiteness still occurs after the three scale/PDF predicates, preserving that part of the old order.

Finite negative PDF values still fail `POINT92_Q_OR_PDF`; zero gluon densities pass. No PDF floor, table, luminosity, bias, weight or sign convention is changed. G is never assigned by the guard. The alpha_actual=G²/(4*pi) arithmetic and fixed-nf5 expected formula are unchanged, with the same1e-10 threshold. Their scope is the on-shell HH scale domain near125..6500 GeV; lower-scale scalar tests exercise the exact native piecewise ALPHAS helper, not a false claim that fixed nf5 applies to every positive Q.

The guard makes no sampler/RNG, candidate, weight, grid, stopping or estimator calls. Its only called routine is the unchanged finite checker. There is no success-path stdout, full event/four-vector output or per-point trace. The existing supervisor remains fatal on HI_FAILURE and saves the complete one-line first failure before group cleanup.

The new finite tests and native-scale correction are reviewable source changes, not evidence that the old historical attempt failed a particular predicate. No genuine HH call or new integral was used to develop this proposal.

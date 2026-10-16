# Phase7I five-predicate audit

The exact original guard is `integration_runtime/native_checks.f:73-97`, SHA256 `5cbe786a92c872cdbcd43440f8c5b8894b6d27da1ec883c66fc4ba6d402dabfb`. The [frozen-source ledger and excerpts](phase7i_stop92_evidence/native_source_ledger.json) establish upstream identities. **None of these five IDs was observed in the old genuine attempt.**

| Original line / predicate | Proposed ID | Origin, units and interpretation at callsite |
| --- | --- | --- |
|87: q<=0 OR g1<0 OR g2<0|POINT92_Q_OR_PDF|q is half the invariant mass of the two incoming PP momenta, GeV. g1/g2 are native dimensionless proton gluon PDFs, evaluated after PASSCUTS scales. Zero densities are permitted. q is mathematically nonnegative because of max(0,...).|
|88: abs(MU_R/q-1)>1e-10|POINT92_RENORMALIZATION_SCALE|MU_R is the model `/RSCALE/` reference in GeV. Native choice4 updates the separate `/to_scale/` scale. Treating model MU_R as point-specific is a source-supported semantic blocker. Ratio and residual are dimensionless.|
|89: any(abs(q2fact/q**2-1)>1e-10)|POINT92_FACTORIZATION_SCALE|q2fact has two GeV² entries in `/to_collider/`. Both should equal the squared choice4 result for the reviewed unfixed scales; beam permutation does not change this common choice. Each comparison is dimensionless.|
|92: a<=0, a=G²/(4*pi)|POINT92_ALPHA_NONPOSITIVE|G is native strong coupling in `/STRONG/`; a is dimensionless. Zero G fails. A negative finite G alone squares to the same alpha and is not a new failure predicate. Underflow can also produce zero.|
|95: abs(a/expected-1)>1e-10|POINT92_ALPHA_RUNNING_MISMATCH|expected uses asmz=.13, MZ91.188 GeV and fixed nf5 one-loop beta. Correct prescription for q>=4.7 in this native implementation; not generally correct below b/c matching. The actual native G update precedes the guard.|

The five exact conditions, their order and `1e-10` constants remain unchanged. Finite(q), finite(MU_R), finite(g1), finite(g2) precede predicate1; finite(a) occurs only after predicates1-3. Thus finite(MU_R) can win over a simultaneously negative PDF, while a malformed G is examined only after earlier scale predicates. Fortran need not short-circuit logical OR/array expressions; diagnostics run only after the same original expression is true.

The one-line records use ES25.16E3, reflecting binary64 scalar values with17 significant decimal digits. Units are encoded in field labels. The exact format and field order are in the [overlay source](../simulation/hh_signal/final_closure/stop92_diagnostic/overlay.py) and [proposed diff](../simulation/hh_signal/final_closure/stop92_diagnostic/native_checks_diagnostic.patch). Each line begins `HI_FAILURE POINT92 <ID>` and includes only that branch's reviewed scalar fields. Native scale is included to distinguish it from model MU_R. There are no momentum arrays, event records or MadLoop vectors.

## Actual artificial native matrix

The same24 cases ran against the extracted original and diagnostic guard at-O0 and-O2. Inputs were constructed constants, with the complete exact finite/statistics module and frozen common-block includes. No production library, HH SMATRIX/MadLoop or genuine sampler was linked. Exact method-binary symbol scans rejected ME/sampler/RANMAR names. Original/diagnostic exits and all successful post-state output were equal.

| Case(s) | Artificial inputs | Observed result in both versions |
| --- | --- | --- |
|0,14|Consistent values; also both PDFs exactly zero|Success; points increments13->14; other numerical state unchanged|
|1,2,3|q=0, negative g1, negative g2|STOP92 / Q_OR_PDF|
|4,23|MU_R offset; model-reference91.188 against q250|STOP92 / RENORMALIZATION_SCALE|
|5,6,13|Wrong QF1², wrong QF2², Inf QF1²|STOP92 / FACTORIZATION_SCALE|
|7|G=0|STOP92 / ALPHA_NONPOSITIVE|
|8|G shifted1%|STOP92 / ALPHA_RUNNING_MISMATCH|
|9,10,11,18,19,20,21|NaN MU_R; Inf g1; NaN G; negative PDF plus NaN MU_R; NaN g2; Inf MU_R; Inf G|Original HI_FAILURE NONFINITE / STOP90; no new POINT92 record|
|12|NaN first q2fact, other fields valid|**Inherited success in these compiler modes**; unordered comparison is false. No finite check was added.|
|15,16,17|Multiple invalid PDF/renormalization/factorization/G fields|First applicable predicate1,2,3 respectively; exactly one diagnostic|
|22|NaN in artificial incoming energy|max(0,NaN expression) yielded q=0 with the tested compiler; STOP92 / Q_OR_PDF. This is measured compiler behavior, not universal NaN propagation.|

The [O0 evidence](phase7i_stop92_evidence/method_O0.json) and [O2 evidence](phase7i_stop92_evidence/method_O2.json) include all exact bounded records. The largest measured record was291 bytes; the strict downstream parser cap is768 bytes, below the unchanged supervisor's4096-character record cap. NaN/Inf scalar representations are explicit nullable values in JSON, never silently substituted zeros. Unknown identifiers, extra fields, split lines, overlength records and unreviewed tokens are rejected independently.

## Scope of noninterference

Overlay reversal reproduces the complete original guard file byte-for-byte. It expands only each failing one-line IF into IF/WRITE/FLUSH/STOP92/ENDIF. No successful-path arithmetic, RNG call, candidate selection, weight, grid update, stopping criterion or estimator was changed. Successful fixtures verify bitwise numerical arrays, unchanged artificial RNG/candidate/weight/grid sentinels and exact observer state. These sentinels are **not an executed native integrator's RNG/grid state**. Actual genuine-runtime equivalence remains **NOT_EVALUATED_UNTIL_AUTHORIZED**; no convergence or scientific cross section is claimed.

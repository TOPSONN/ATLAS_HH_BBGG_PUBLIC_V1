# Double-Higgs decay assignment: method boundary

PASS_METHOD_ONLY: exactly two distinct original PDG25 lineage identifiers,
one assigned bb and the other γγ. A domain-separated SHA256 bit of independent
assignment seed/source index chooses the γγ lineage with probability1/2.
Sorted lineage IDs make input order irrelevant; no pT ranking, fake PDGs,
daughter replacement or momentum mutation. The recorded 10000 identifier-only
trials test balance and reproducibility, not physical event statistics.

BLOCKED_NATIVE_DECAYER: this task does not implement or physically validate
a per-lineage Pythia decayer. Global PDG25 switches cannot independently assign
different modes. The future bridge must bind two original LHE entries, retain
copy chains and source indices, use validated nonzero-bottom-Yukawa Hbb and
loop-induced Hγγ decay models, and check mother/daughter/p4 closure and unbiased
source handling. The C++ API compiles but creates no particles.

Real decay closure Gate P is NOT_EVALUATED. A method-level assignment pass
does not authorize a physical 10-event pilot or establish full-chain readiness.

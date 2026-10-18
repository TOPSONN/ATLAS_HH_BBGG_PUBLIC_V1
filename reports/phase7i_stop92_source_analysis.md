# Phase7I STOP92 frozen-source analysis

Task: `PHASE7I_NATIVE_STOP92_DIAGNOSTIC_RECOVERY_V1`. Verdict: **BLOCKED_POINT_GUARD_SEMANTICS**. The diagnostic method is ready for review; physical execution remains unauthorized. The original genuine failure is unchanged and its exact failed predicate remains **UNKNOWN**.

## Identities and evidence boundary

Executed source: `58d39888a024028e32f3071db9215c0db6fe0a89`. Failure-report head: `dcb499e1cc436ae71fcb716c36cc32cb93aa92a9`. Frozen build identity: `98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281`. Physics contract SHA256: `a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`.

The seed910001 adaptation attempt, PID460, exited92 after 0.292279523 native stage wall seconds. Its receipt SHA256 is `c263adf18b77b16d9322cc71cd379e709cc7ee25d1408715a1a42e3c2fd198e4`. Initial PDF/alpha/masses/beams/scale/seed checks passed. No flushed ME-entry/return, iteration, result or final counters were recorded. Complete physical counters and the rejected scalars remain unavailable; absence of final counters is not a measured zero. See the preserved [original report](phase7i_exact_source_restart.md).

This task executed only artificial scalar methods. New genuine ME calls, new integrals and new events: **0/0/0**. No production binary, MG5 installation, old receipt or stopped output was modified.

All line numbers below refer to the actual frozen process sources, rather than assumed upstream filenames. Full SHA256 values are in the [source ledger](phase7i_stop92_evidence/native_source_ledger.json); [numbered excerpts](phase7i_stop92_evidence/frozen_source_excerpts.txt) retain the relevant code. The actual scale file is `SubProcesses/P0_gg_hh/setscales.f`; PDF wrappers reside under `Source/PDF/`.

## Actual call order

1. `driver.f:203-204`: `hi_endpoint` then `sample_full`.
2. `Source/dsample.f:132-145`: choose integration coordinates, `x_to_f_arg`, `pass_point`, `hi_integrand`, `dsig`, then multiply the weight and update graphs/grid. `genps.f:60` calls `gen_mom`; these genuine routines were inspected, never linked into the new method executables.
3. `auto_dsig.f:476-511`: incoming-particle permutation and beam bookkeeping, then `PASSCUTS(P1)` and `DSIG1(P1,...)`.
4. `cuts.f:1218-1254`: dynamic renormalization scale into native **scale**, update `G=sqrt(4*pi*ALPHAS(scale))`, dynamic factorization scales, `setclscales`, then `UPDATE_AS_PARAM`. This coupling update precedes PDF evaluation at the DSIG1 callsite.
5. `reweight.f:631-642`: with the reviewed ickkw=0, xqcut=0 and positive native scales, clustering returns without replacing those scales.
6. `auto_dsig1.f:125-137`: evaluate both gluon PDFs at `sqrt(Q2FACT(i))`. Lines142-146 optionally boost PP into P1. Line147 calls `hi_point(PP,G1,G2)`; line148 subsequently calls `SMATRIX1(P1,...)`.
7. `matrix1.f:231,248,321`: flushed outer-ME entry instrumentation immediately precedes the relevant SLOOP calls. There was no historical flushed entry observation; the runtime point and complete counter values cannot be reconstructed here.

PP at hi_point is the incoming DSIG1 argument, after the earlier permutation; P1 is its optional matrix-element-frame copy. The mass of the incoming sum is Lorentz invariant in exact arithmetic. Swapping the two identical incoming gluons leaves that sum unchanged; beam IDs and x values are permuted upstream.

## Scale ownership: a source-supported blocker

`run.inc` places native **scale** in `/to_scale/` and q2fact in `/to_collider/`. `Source/MODEL/coupl.inc:11-12` places **MU_R** in the separate `/RSCALE/` common block. They are different storage, not aliases.

`Source/MODEL/param_read.inc:5` includes the frozen generated `Source/param_card.inc`, whose line1 initializes MU_R to91.188 GeV. `cuts.f:1221` updates scale, not MU_R. `UPDATE_AS_PARAM` (`couplings.f:37-76`) recalculates dependent parameters and COUP2 but does not assign MU_R. `intparam_definition.inc:149,159` derives AS from G and derives MDL_MU_R powers from the existing MU_R. The distinct `UPDATE_AS_PARAM2` can set MU_R (`couplings.f:91`), but the only frozen explicit caller found is the f2py wrapper, not the audited pre-hi_point integration path. Standalone check_sa assignments are a different entry point. The bounded [ownership search](phase7i_stop92_evidence/MU_R_ownership.json) includes print-string matches explicitly; a printed assignment-looking string is not an executable assignment.

Therefore branch2's identification of model MU_R with the point-specific native scale is unsupported by the frozen call path. With an on-shell HH point q>=125 GeV, a model reference of91.188 cannot satisfy MU_R/q=1. A synthetic q=250, MU_R=91.188 probe produces the proposed renormalization diagnostic, as expected. **This is source-supported candidate causal evidence, not an observation of the historical failed branch.** Confidence is high in the variable-ownership discrepancy; historical branch attribution remains unknown. The guard is after native scale/coupling/PDF updates but before any demonstrated synchronization of model MU_R.

No scale, model parameter, guard location or tolerance was corrected in this task. Resolving this scientific comparison requires a separate minimal, justified source proposal and exact-revision review before a production rebuild.

## Dynamic scale arithmetic

`setscales.f:71-73,92` sets choice4 to `sqrt(max(0,SumDot(p1,p2,1)))*scalefact`; scalefact=.5 gives mHH/2. `set_fac_scale:180-183` uses that same result squared for both unfixed factorization entries. `SumDot` (`kin_functions.f:46-74`) forms the four-vector sum then calls dot. The guard directly forms its invariant and divides by2.

The valid on-shell HH /13TeV-beam domain implies 125<=q<=6500 GeV. This is a conditional kinematic bound, not a recovered historical point. The exact scalar SumDot/dot projections and extracted choice4 expression were compared with the guard expression on441 deterministic beam pairs spanning125..6500 GeV, including asymmetric longitudinal sums. Both maximum relative residuals were0 in the recorded tests. These checks support keeping `1e-10` for these arithmetic probes; they do not bound arbitrary highly boosted/cancelling four-vectors or establish genuine sampler behavior. No tolerance was widened.

## Actual alpha_s prescription

`Source/setrun.f:132-139` obtains PDF-associated running through `pdfwrap`; `pdfwrap.f:233-235` sets CTEQ6L1 to asmz=.130, nloop=1. These values were also genuinely observed in the stopped initial checks. The stale generated model AS default is not the effective running value. G is owned by `/STRONG/` (`coupl.inc:5-6`) and is updated from native ALPHAS before hi_point.

The linked implementation is `libgeneric.a:alfas_functions.o`; the actual routine is `Source/alfas_functions.f:74-156`. It uses MZ91.188, matching at b=4.7 and c=1.42 GeV, with nf5 above b, nf4 between c and b, nf3 below c. Its fixed B0 constants are truncated binary64 decimal coefficients. NEWTON1 line189 returns the one-loop closed form immediately at line190. The iterative `5e-4` tolerance belongs to higher-loop branches and does not set one-loop accuracy. This ALPHAS has **no top threshold**, including above173 GeV. Model NF/NL parameters and the separate electroweak `alfaw` routine do not change that observation.

The guard's fixed-nf5 formula agrees with this prescription above4.7 GeV, including the conditional physical HH range. Seventeen exact scalar ALPHAS probes cover125,173,250,1000,6500, MZ and both sides of1.42/4.7/173. An independently implemented reciprocal-alpha, piecewise-matched formula agrees to at most6.55e-15 relative; the maximum physical-range discrepancy from the guard is1.34e-15. Below4.7, the guard generally disagrees (e.g. ~3.08% at2 GeV); that artificial low-scale discrepancy must not be called a physical HH failure. See [both optimization results](phase7i_stop92_evidence/method_O0.json).

## PDF semantics and numerical zeros

`pdg2pdf.f:138-142,273-293` maps gluon IDs21/0 to parton0 and, for the reviewed proton beams, returns `Ctq6Pdf(ipart,x,Q)` directly. Thus g1/g2 at this callsite are dimensionless gluon densities f_g(x,QF); they do not contain the phase-space Jacobian, a beam-energy multiplier or an extra x factor. The Jacobian is in the sampler weight upstream. The `PD(IPROC)=G1*G2` product is separate.

`pdg2pdf.f:81-97` returns zero at x=0 and rejects unsupported negative/out-of-proton-support arguments. `Ctq6Pdf.f:72-92` enforces X support and its low-Q condition, interpolates/extrapolates the table and applies its existing negative-value clamp. The documented interpolation grid is approximately 1e-6<x<1 and1.3<Q<10000 GeV; partonic x outside that interpolation grid is not automatically a new physical failure. PDF fit metadata and native running threshold choices are distinct. No new PDF evaluation or PDF-model substitution was executed here.

The original predicate permits zero g1/g2. Artificial zero-PDF success cases remain successful. No positive floor or signed-weight reinterpretation was introduced. Original finite checks reject nonfinite q/MU_R/g1/g2/derived alpha with STOP90; q2fact has no finite check. The measured inherited NaN q2fact acceptance is documented separately in the [predicate audit](phase7i_stop92_predicate_audit.md).

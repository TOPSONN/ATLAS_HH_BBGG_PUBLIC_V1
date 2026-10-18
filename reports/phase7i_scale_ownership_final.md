# Phase7I scale ownership: Route A for the frozen finite LO process

Task: `PHASE7I_POINT_GUARD_SCIENTIFIC_CORRECTION_V1`. Base: `4b1635073b6b1cd3096ee268a3c7858dea3da3b1`. **Selected route: A**, scoped to the exact full-mass, no-Born, LO gg->HH process and frozen model/library identities. No genuine amplitude, production binary or integral was executed in this task.

## Complete source boundary

The [dependency ledger](phase7i_guard_correction_evidence/dependency_ledger.json) hashes all 54 .f/.inc files directly in the frozen `Source/MODEL` and generated loop directory, plus 6 native scale/callsite sources:60 files total. Each was matched to the original frozen build inventory. The [builder contract](../metadata/phase7i_builder_review_contract.json) additionally freezes all 11 linked process archives, 24 existing card files and compiler/GCC/linker identities. The [numbered excerpts](phase7i_guard_correction_evidence/dependency_excerpts.txt) and [reduction-source excerpts](phase7i_guard_correction_evidence/reduction_excerpts.txt) give exact line references. Four installed reduction sources also matched the pinned installation manifest; all 4658 retained installation sources were verified without reinstalling. This is source/archive provenance, not a new source-to-binary reproduction.

The requested model param-card location differs in this generated layout: `Source/MODEL/param_read.inc:5` includes `Source/param_card.inc`; there is no separate generated `Source/MODEL/param_card.inc` to substitute.

An additional [whole-process symbol search](phase7i_guard_correction_evidence/global_model_scale_search.json) inspected all 629 frozen Fortran/C/include sources, including 17 DHELAS sources. Its 40 model-scale matches add only copied common-block declarations/initialization outside the model/loop consumers described below; no overlooked DHELAS scale consumer was found. Every scanned file matched the frozen inventory hash.

## A. Dynamic production scale

`SubProcesses/P0_gg_hh/setscales.f:71-73,92` computes choice4 sqrt(shat)*.5 into native `scale`, owned by `/to_scale/`. `cuts.f:1221-1254` evaluates native ALPHAS(scale), updates G, computes both QF² entries, and calls UPDATE_AS_PARAM before DSIG1 evaluates PDFs. `auto_dsig1.f:125-148` evaluates g1/g2, guards PP, then calls SMATRIX1 with its optional frame copy. Native scale therefore supplies the physical dynamic argument of alpha_s; both QF² entries supply PDF scales. The original model-MU_R comparison did not check this native variable.

## B. Actual model/reduction dependencies

Model MU_R belongs to `/RSCALE/`, is initialized to91.188 GeV by `Source/param_card.inc:1` and is not updated by the production pre-guard UPDATE_AS_PARAM path. It is **not unused**: `CT_interface.f:118` passes it as the third CTSXCUT argument, and `TIR_interface.f:196-197` passes it to IREGI. CutTools `cts_cutroutines.f90:1,70,154-166` maps that argument to muscale, calls OneLOop's scale setter, or sets musq for QCDLoop. The separate LSCALE/rootsvalue argument is not the running-alpha scale. IREGI's installed interface likewise carries the scale into scalar reduction. Individual Laurent coefficients/integrals may depend on this reference.

The complete model scan finds MU_R² defined at `intparam_definition.inc:159` and its MP counterpart, but no use in the active generated coupling formulas. `couplings1.f:21-27` contains the Higgs self/Yukawa couplings; `couplings2.f:15-27` contains GC_5 and four R2 couplings, depending on G, fixed masses and Yukawas, with no MU_R/log(MU_R) dependence. The MP formulas have the same dependency structure. `helas_calls_ampb_1.f:98-106` supplies exactly four finite R2 amplitudes: bottom/top ggHH and ggH. These are not UV-renormalization counterterms. `loop_matrix.f:1111-1119` has an empty UVtree section; `NBORNAMPS=0` at2486 and `NSQSO_BORN=0` at93. `loop_CT_calls_1.f` evaluates 16 massive bottom/top triangle/box loops. No mass or coupling UV counterterm is generated at this leading loop order.

## C–E. Scientific interpretation and decision

The MadLoop implementation paper states that finite loop-induced processes require R2 terms but no UV counterterms, and that the regulator prefactor does not introduce physical renormalization-scale dependence beyond running alpha_s (section2.1; printed page27, footnote16). [Hirschi–Mattelaer, arXiv:1507.00020v3](https://arxiv.org/pdf/1507.00020v3#page=28).

Our inference for this explicitly no-Born, massive-quark source is Route A: keep the positive fixed reduction reference, while checking the native dynamic alpha_s/PDF scale. For a Laurent sum C2/epsilon²+C1/epsilon+C0, changing the reference by L shifts the finite coefficient by L*C1+L²*C2/2; that vanishes when the complete pole residues vanish. Individual diagrams need not be reference independent. A synthetic zero-pole algebra check and nonzero-pole counterexample are included, **not a measured HH pole cancellation**.

No synchronization API is required for this scoped leading finite amplitude. UPDATE_AS_PARAM2 exists and would update MU_R, MODEL_SCALE, G and dependent couplings; inserting it would change more numerical state and is not justified here. No manual MU_R assignment or model/counterterm change is proposed. This conclusion cannot be transferred to NLO virtual amplitudes with Born contributions, a different model, running masses or changed counterterms. Exact dependency hashes close that scope in the proposed builder.

The independent physical scale checks are native scale/q and both QF²/q², plus the verified one-loop alpha formula on the HH domain. A passing guard does not prove loop physics: genuine pole/stability behavior, finite-precision reduction-reference independence and complete integrator behavior remain `NOT_EVALUATED_UNTIL_AUTHORIZED`. Preserve existing loop failure/stability gates; separately review any future actual-ME diagnostic scope. The historical failed STOP92 branch remains **UNKNOWN**.

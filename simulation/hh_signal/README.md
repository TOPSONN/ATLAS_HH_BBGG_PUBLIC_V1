# S01 ggF HH SM loop-model readiness

Phase7A contains a guarded dry-run, isolated deterministic matrix-element
checks, method tests, and a future interface contract. It authorizes **zero
physical signal events**. There is no event-generation backend in this module.

Use the [Traditional Chinese guide](USER_GUIDE_ZH_TW.md). The installed MG5
3.5.16 `loop_sm` is reused; the bounded numerical command copies existing
source into private scratch and compiles the bundled reduction source there.
No validated installation or historical background is modified.

The selected candidate is `g g > h h [noborn=QCD]`. Native MadLoop standalone
uses `[sqrvirt=QCD]`; actual diagram lists from both paths must agree. Top and
bottom box/triangle loops and their R2 rational terms are retained with finite
masses. This is LO loop-induced accuracy. R2 local vertices are required
rational loop terms; they are not a heavy-top EFT substitution.

Results and limits are in [the final decision](../../reports/phase7a_final_decision.md),
[numerical evidence](../../metadata/phase7a_loop_validation.json), and
[model audit](models/MODEL_SOURCE_AUDIT.md). No integrated signal cross section,
NLO normalization, official ATLAS sensitivity, or real decay/weight/shower/
detector closure is claimed.

The decay planner selects distinct original PDG25 lineages with a reproducible
50/50 assignment independent of kinematics. It creates no daughters. A working
native per-lineage decayer and initialized/adopted BRs remain required before
any physical pilot. `H1` and `H2` are analysis identifiers, never new PDG IDs.

Personal receipts and compiler outputs stay local. Publication is source and
bounded numerical evidence only; no automatic sample upload, release, merge,
force push, or figure publication is provided.

# Exactly-once branching-ratio contract

For undecayed identical HH production, the disjoint assignments (H1→bb,H2→γγ)
and (H1→γγ,H2→bb) have total physical probability 2*BRbb*BRγγ. This factor is
separate from the production identical-H symmetry divisor. Apply only missing
factors after certifying source-included decays; the default contract is undecayed
production, and the ledger rejects already-applied BRs or missing factor2.

GENERATOR_MODEL_BR: null, signal-specific inclusive initialization not done.
EXTERNAL_REFERENCE_BR: null, no external precision BR adopted.
ADOPTED_STUDY_BR: null, BLOCKED until explicit model/reference choice and source.
FORCED_SAMPLING_PROBABILITY: 1/2 for each assignment,1 for the stipulated mixed
mode conditional plan; these are not physical Higgs branching ratios.

Historical ZH/ttH initialized BRs are not copied into this signal. A nonzero
bottom-Yukawa decay model is required. The arbitrary0.6/0.002 unit-test numbers
are ALGEBRA_ONLY and never enter a signal manifest/normalization. Duplicate BR,
already-decayed source and wrong-identical-factor failure tests execute.
No HH factor is applied to ZH/ttH or any historical weight ledger.

# Native full-loop model feasibility

Native `loop_sm` selected from official MG5 3.5.16 commit
`3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`.
Model bundle SHA256: `3772b2d0f75e092f82a4c556bf2288a43e239f2c7ee6cafaca22d6a11eb98065`.
Per-file hashes and LICENSE identity are in `metadata/phase7a_model_manifest.json`.
See [source audit](../simulation/hh_signal/models/MODEL_SOURCE_AUDIT.md).

`g g > h h [noborn=QCD]` parsing/diagram creation: PASS.
Native MadLoop `[sqrvirt=QCD]` standalone compilation/numerics: PASS.
The generic standalone export of noborn itself failed; this is documented,
not silently presented as a working export path. Both actual diagram lists agree.
Box counts {'5': 6, '6': 6}, triangle counts {'5': 2, '6': 2}; no Born or UVCT
diagrams. Rational R2 terms remain included. Finite top AND bottom loops are
present; default light/charm Yukawas zero. LO only, no K factor or NLO claim.

The old official HH package is a documented top-only full-mass backup, but its
archive identity/license/modern compatibility remain ACCESS_UNVERIFIED after
retrieval failures. It was not selected or vendored. HEFT is ineligible for
full-MT acceptance. No physical signal sample or cross section was generated.

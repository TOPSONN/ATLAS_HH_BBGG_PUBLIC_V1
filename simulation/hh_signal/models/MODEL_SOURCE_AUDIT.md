# Full-loop source decision

Selected: installed official MG5_aMC 3.5.16, `loop_sm`, upstream commit
`3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`.
The [source manifest](../../../metadata/phase7a_model_manifest.json) records
actual installed model-file SHA256 values and a canonical bundle digest.
The repository contains original readiness code/cards/evidence, not a copied
MG5/UFO/reduction-library distribution.

The installed MG5 LICENSE is the MadTeam open-source license adapted from
Illinois/NCSA, with copyright/license/disclaimer retention and no endorsement.
Its exact hash is retained in the manifest. Local isolated compilation of the
already present bundled CutTools/IREGI source does not alter the validated
installation. Optional Ninja/COLLIER/Samurai/Golem installers are disabled.

Actual MG5 parsing accepts `import model loop_sm` followed by
`generate g g > h h [noborn=QCD]`. The generic standalone exporter in this
version fails with missing `wavefunction_rank` analytic information. Native
MadLoop `[sqrvirt=QCD]` standalone succeeds; the adapter requires identical
diagram lists for both commands. This compatibility qualification must remain
visible. Neither command here launches integration or event generation.

The actual diagrams contain six box and two triangle diagrams for each of top
and bottom. Attached external tree structures contain the HHH vertex; looking
only at loop-cycle vertices incorrectly misses it. Light-quark/charm Yukawas
are zero under the default restriction. This is finite MT and MB LO, with a
restricted SM quark-loop scope; it is not a claim to all SM corrections.

The trilinear vertex is `GC_30=-6*i*lam*v`, `lam=MH**2/(2*v**2)`, and
`GC_37=-i*yt/sqrt(2)`, `yt=sqrt(2)*YUKAWA[6]/v`. `MASS[6]` independently sets
the top propagator mass. Diagnostic κλ scales GC_30 in double and quadruple
precision after parameter initialization. No arbitrary BSM production scan is
provided. Actual generated R2 ggH/ggHH terms are rational loop counterterms,
not HEFT effective operators; removing these terms would invalidate the loop.

The generated denominator is 512 = 4 initial helicities × 64 initial colors ×
2 identical final Higgs permutations. The mixed bb/γγ factor of two belongs
to the later decay probability and is separate from this production symmetry.

The official [HiggsPairProduction page](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/HiggsPairProduction)
describes an older top-only form-factor implementation based on
[Plehn, Spira and Zerwas](https://arxiv.org/abs/hep-ph/9603205), citing
[Frederix et al.](https://arxiv.org/abs/1401.7340).
It is an independently reviewed backup candidate, not an accepted modern UFO.
The wiki was read successfully, but tool retrieval of its archive failed and
the direct TLS retrieval timed out. Archive version, SHA256, internal files,
compiler compatibility and redistribution license are **ACCESS_UNVERIFIED**.
No archive was installed, compiled, vendored or selected. These unknowns do
not transfer to the independently checked installed native model.

HEFT would be `HEFT_APPROXIMATION_ONLY`, ineligible for the finite-MT gate.
The [loop-induced MG5 methodology paper](https://arxiv.org/abs/1507.00020)
explains squared loop amplitudes and the required rational terms; actual
acceptance here rests on installed-source inspection and executed fixed-point
numerics, not the paper or model name alone.

Ward-polarization replacement and a second independent amplitude provider
were not executed. Finiteness, pole residuals, numerical stability, κλ closure,
exchange symmetry and mass/Yukawa sensitivity are narrower evidence.

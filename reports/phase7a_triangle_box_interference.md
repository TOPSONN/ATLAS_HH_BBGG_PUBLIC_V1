# Actual triangle, box and interference checks

These are squared matrix elements at explicit common on-shell 2→2 phase-space
points, not cross sections or generated events. The returned MG5 normalization
includes spin/color averages and identical-H symmetry denominator 512.
Both top and bottom loop contributions and rational terms enter each component.

For q(k)=|B+kT|², B²=q(0), T²=[q(1)+q(-1)]/2-q(0),
I=[q(1)-q(-1)]/2=2 Re(B T*). An independent κλ=2 call tests q(2)=B²+2I+4T².
Individual complex helicity amplitudes were not separately exported.

| mHH GeV | box squared | triangle squared | interference κλ=1 | κλ=2 closure |
|---:|---:|---:|---:|---:|
| 250.001 | 2.05451453502e-06 | 1.66919877262e-06 | -3.70174031948e-06 | 2.39e-15 |
| 300.0 | 4.95397242548e-06 | 1.67469823271e-06 | -5.75621747829e-06 | 3.21e-14 |
| 400.0 | 3.21547711477e-05 | 2.88651738299e-06 | -1.88379223596e-05 | 1.64e-11 |
| 800.0 | 4.29218730893e-05 | 9.59877218723e-07 | -1.03787756433e-05 | 1.3e-15 |

All four pilot points show destructive interference. This does not establish
an integrated interference fraction. The 250.001 GeV default-tolerance test
failed strict closure; final MLStabThres=CTStabThres=1e-9 triggers successful
native QP rescue. Failure history is retained, not counted as PASS.

The evidence contains 21 configurations × 6 calls at their same fixed point.
No random phase-space generator is used; helicity filtering is disabled.
Ward identity NOT_EVALUATED: no reviewed polarization-replacement driver was
executed. Independent amplitude-provider comparison NOT_EVALUATED.

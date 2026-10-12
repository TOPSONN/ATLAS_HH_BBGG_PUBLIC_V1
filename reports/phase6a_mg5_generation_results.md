# Phase 6A actual generation and independent results

Both stages ran sequentially through the shipped self-service command. Stage B started only after the real 100-event gate passed. Exact actual banner cards, process/integration logs and source hashes are retained in simulation/mg5/cards/ and evidence/.

| Sample | Actual events | Actual seed | Cross section ± integration error [pb] | Gzip bytes |
|---|---:|---:|---:|---:|
| smoke_100 | 100 | 20261012 | 0.06597578 ± 0.0006215035 | 22486 |
| reference_1000 | 1000 | 20261013 | 0.06624666 ± 0.0005940933 | 166818 |

The two integration estimates differ by 0.315 times their combined reported integration uncertainty, an internal Monte Carlo consistency observation; it does not validate ATLAS background normalization. Neither event count is a cross-section accuracy guarantee.

LHE 3.0 structure and gzip CRC passed. Every event was checked without filtering: final-state identities, particle records, finite momenta, mother/color records, mass shell, initial charge, beam bounds, generation cuts, nominal weights and four-momentum closure. Both samples have zero negative and zero zero weights. MG5 writes IDWTUP=-4 and event_norm=average; constant nominal XWGTUP is the generated cross section in pb. Histograms use XWGTUP/N.

Maximum four-momentum component residual: 100 events 5.69998519495e-08 GeV; 1000 events 9.69998836808e-08 GeV. Maximum mass-shell residuals: 0.000125140417367 and 0.000272020697594 GeV^2. Tolerances are 1e-6 GeV + 5e-9 incoming energy and 1e-6 GeV^2 + 5e-9 max(E^2,p^2,m^2,1), respectively, to accommodate decimal serialization. Raw residual values must not be interpreted as physics precision.

The validator uses only Python's standard library, no MG5 imports. Adversarial tests mutate copies of real generator events, never reference originals. The final test count and actual CI evidence are recorded separately. ROOT baseline tests are 5/5 PASS.

A supplied-card 23-event diphoton run at 14 TeV, seed 20261014, pta=30 and etaa=2.4 physically exercised all seven user-facing options. A final seven-event bbgg run at seed 20261018 tested the hardened command with supplied cards. Both stay LOCAL_ONLY. An actual PTY opened the interactive MG5 prompt, executed help generate and quit with exit 0. No 10000-event run or cross-platform bitwise reproduction was performed.

Initial diagnostic attempts remain local: developer-checkout ANSI header; validator's corrected assumption about IDWTUP; all-hidden-card legacy SysCalc BEL comment; and post-run iseed reset. Exact final samples use normal release-mode headers and actual banner-applied seeds. No event values were repaired or deleted.

Final local checks: 22/22 portable adversarial tests PASS; final three-event bbgg run using the shipped isolated-output command PASS. No generator parser/build cache remains at the repository root. Additional three-event output remains LOCAL_ONLY.

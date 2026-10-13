# Phase 6B real shower and hadronization assessment

The final v2 command physically processed all three existing MG5 hard samples independently. Each produced 1,000 valid HepMC3 events, with zero shower/internal-rejection/source-identity/validation failures. The original 3,000 hard events are reused without MG5 regeneration. Ten/100-event smoke runs and the deterministic repeat share these events and add no independent hard statistics.

| Process | Input/attempted/success/written/readback | Failed shower/validation | Mean stable | Mean charged | Mean neutral | Mean neutrinos | Mean stable light hadrons |
|---|---|---|---|---|---|---|---|
| bbgg | 1000/1000/1000/1000/1000 | 0/0 | 160.434 | 71.616 | 88.818 | 1.160 | 82.523 |
| ccgg | 1000/1000/1000/1000/1000 | 0/0 | 170.802 | 77.508 | 93.294 | 0.524 | 89.744 |
| jjgg | 1000/1000/1000/1000/1000 | 0/0 | 167.127 | 75.848 | 91.279 | 0.115 | 88.051 |

Here stable means the actual Pythia final state under the cτ>10mm stability convention. Neutrinos and beam remnants are retained in global closure; the visible-particle pT histogram alone excludes neutrinos12/14/16. No detector, calibrated jets, flavour tagging, trigger or photon-fake inference is made.

Each [independent diagnostic JSON](../simulation/pythia8/evidence/) binds the original LHE, full output, raw Pythia diagnostic and source-sidecar hashes. `scripts/analyze_shower.py` independently re-reads immutable source rows, compares every original PDG/mother/colour/p4/mass/weight field, rejects raw mother-graph cycles/dangling links, recomputes ISR/FSR/hadron/decay counts from all statuses, and cross-checks charge and final multiplicities with the separate actual ReaderAscii result.

| Process | ISR parton record entries | FSR parton record entries | Hadron record entries | Decay-product record entries | Mean all-record b/c hadrons |
|---|---|---|---|---|---|
| bbgg | 41950 | 61979 | 165719 | 168723 | 3.518/4.663 |
| ccgg | 49455 | 74423 | 174561 | 168484 | 0.124/3.752 |
| jjgg | 45666 | 83811 | 169015 | 159529 | 0.173/0.760 |

ISR parton statuses41–49 and FSR51–59 are actual quark/gluon development records; these entry totals include copies/history and are not exclusive emission rates. Hadron entries include intermediate copies and beam hadrons; stable light hadrons are separately counted. Heavy-hadron histograms use inclusive quark content and retain both signs; B_c may belong to both categories. All-record, terminal-heavy and stable-heavy counts are distinct. All three runs have zero stable b/c hadrons because applicable heavy decays execute. The terminal criterion means no immediate daughter hadron carrying that flavour, not a detector-level tag or guaranteed direct origin.

Original hard outputs are exactly bbgg=(b,bbar,γ,γ), ccgg=(c,cbar,γ,γ), and jjgg=(two u/d/s/antiquark/gluon light partons,γ,γ). The source proton PDF also permits incoming c/b in the 5F scheme; incoming identities are recorded separately. Later shower heavy-quark records and gluon-parent ±heavy-child ancestry candidates are preserved in each JSON. They establish shower heavy-flavour development without claiming every later heavy hadron descends directly from the named hard parton, or that candidate counts are exclusive splitting rates.

| Process | Hard-photon ancestry stable γ | Hadron-decay γ or descendants | Shower γ without produced-hadron ancestry | Shower γ with produced-hadron ancestry |
|---|---|---|---|---|
| bbgg | 2000 | 72871 | 65 | 3 |
| ccgg | 2000 | 76990 | 78 | 0 |
| jjgg | 2000 | 75902 | 51 | 3 |

Photon ancestry is an event-record diagnostic. Independent traversal excludes beam entries/statuses11–19, includes the hard root itself and retains ambiguous overlapping origins. A hadron ancestor alone does not prove direct photon decay; the decay-path criterion also requires the photon status91–94. The last column has overlapping remnant/hadron ancestry and is not assigned a unique prompt origin. None of these labels is a reconstructed photon or experimental prompt-isolation definition. Final photons are numerous because decays and QED showers are retained; there is no exactly-two-final-photons constraint.

Pythia may restore heavy masses and apply shower/primordial recoil. Original LHE p4 remain byte-preserved separately; hard Pythia-record photon momenta need not equal them. Unordered minimal p4 differences are reported only as diagnostics, without invented LHE/Pythia/HepMC barcode equivalence.

| Process | Max full beam→stable component residual [GeV] | Max stable shell residual [GeV²] | Max shell residual/tolerance |
|---|---|---|---|
| bbgg | 7.69606823195e-06 | 2.39746020814e-08 | 0.000118799120896 |
| ccgg | 8.37606175619e-06 | 2.35910915247e-08 | 0.00420630642644 |
| jjgg | 9.68320252624e-06 | 2.66545195915e-08 | 0.000640338401568 |

The unchanged closure gate is 1e-5GeV +1e-9×13,000GeV =2.3e-5GeV per component. Stable shell gate is |E²−p²−m_generated²|≤1e-7GeV²+1e-9×max(E²,1GeV²); intermediate virtual shower particles are not subjected to stable on-shell requirements. Actual ParticleData validates PDGs, charge and absence of any stable coloured object. Full stable charge equals the two proton charges for every event. No vector/particle was repaired, dropped or replaced.

The initial diagnostic card disabled primordial kT and produced a genuine failed bbgg100 run: Pythia reported100 successes but unchanged strict ReaderAscii readback found99 valid events and one invalid event54 containing two photons and one K_S. The exact OFF card, output hashes and full failure details remain preserved, including the source-linked StringRegion collinear numerical reproduction. It is excluded from reference publication. The v2 baseline restores the stock physical primordial-kT model with explicit parameters, changes recoil/random history and was rerun through fresh A/B/C. This is a documented physical configuration change, not a tolerance relaxation or vendor-source patch; success for these3,000 events does not guarantee every future record.

Actual generator warnings are retained in [source/configuration assessment](phase6b_shower_configuration.md): expected SLHA SM mass/decay-table ignores and one ccgg HadronWidths fallback. Event-level attribution of that warning is UNKNOWN from its text; strict final record QA passed. Pythia itself does not constitute independently calibrated decay precision.

All photon/heavy multiplicity and stable-visible-pT distributions are in per-process diagnostic JSON. No figure was generated. ROOT/MG5 historical definitions and results are untouched. The complete local gzip outputs are25,204,359/27,381,014/27,259,142bytes (bbgg/ccgg/jjgg); each exceeds10MiB. Only losslessly selected100-event prefixes from these full verified runs are candidates for GitHub.

Resource evidence separately records physics-runner time, entire CLI elapsed time, exact ASCII/gzip/whole-run bytes and runner getrusage RSS. Future-million-event storage projections scale measured1k whole-run bytes by1000 and remain extrapolations, not a physical million-event or performance acceptance test. No Delphes installation/execution or detector simulation was performed.

Remote source/reference acceptance is recorded in [GitHub publication](phase6b_github_publication.md). It uses exact downloaded bytes and actual successful jobs, separately from the physical tests above.

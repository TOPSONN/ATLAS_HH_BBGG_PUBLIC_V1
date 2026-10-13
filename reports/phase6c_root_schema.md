# Phase 6C native Delphes ROOT schema validation

Status: **PASS for actual Stage C native readback: 1000 events per process,
3000 total**. Final A_v2 (10 bbgg events) and B (100 per process) also passed
their stage gates and are not added to the Stage C scientific denominators.

The independent executable and adapter are
simulation/delphes/src/analyze_delphes.cxx and include/DelphesAdapter.hxx.
They use existing ROOT 6.40.04 / C++20 and the actual Delphes 3.5.1 dictionary
library. Historical ATLAS readers and the top-level CMake are unchanged.
Verified upstream source commit: 28658365abeb71ee36dfc739f9670c1514c0cb10.

The adapter requires a readable, non-zombie, unrecovered ROOT file and actual
Delphes TTree. It checks real TClonesArray containers, clone classes, loaded
dictionaries, disk streamer versions/checksums, actual entry reads, size leaves
and object classes. Required branches are Event, Weight, Particle, Photon,
Jet, GenJet, MissingET and ScalarHT. Track, Tower, EFlow, Electron, Muon and
GenMissingET are inspected when present. Full branch inventory and each mapped
branch's presence/class/version/checksum are retained. Numeric float/double
members, bounded arrays and nested Jet four-vectors must be finite.

Event.Number must match the original HepMC3 E record. Event.Weight and all
Weight entries must equal the **Float_t cast** of the exact input weight
vector. No output-count normalization is introduced. Exact signed binary64
source contributions are retained separately.

The official reader groups particles by production vertex, so ROOT order is
not a HepMC/Pythia barcode mapping. Retained Particle PID, status, Cartesian
p4, mass and position are compared as a multiplicity-preserving Float_t tuple
multiset. Duplicate indistinguishable tuples are counted. Source GeV/mm units
are preflight-validated. Native X/Y/Z are mm; native T is seconds:
Float_t(ct_mm * 1e-3 / 2.99792458e8). Mother/daughter indices are checked for
bounds separately; this is not a complete source-DAG equality proof. The
existing strict binary64 HepMC physical gate remains upstream.

Actual tree entries are N_output, including on failure. A short readable file
is assessed for its available prefix, then fails the count gate. N_read counts
successful native reads; N_processed counts fully valid assessments;
N_invalid records failed assessment; N_unassessed_output_entries records
remaining unassessed rows. N_skipped is the requested-versus-produced count
shortfall, not an invented missing-source identity. Unavailable entry counts
remain null. Failed events do not partially contribute aggregate statistics.

Reports bind actual ROOT/input-index/truth-index/runtime-card SHA-256.
The runtime card must match the reviewed card after restoring only its
recorded seed to canonical 610301. Scientific content SHA hashes exact
analysis JSONL and numeric native-branch content, excluding ROOT UUID/date,
timing and TRef/UniqueID details. Binary identity and scientific reproducibility
are distinct.

| Stage C process | N_input/read/processed/output | Invalid/skipped/unassessed | Finite numeric fields | Duplicate indistinguishable Particle tuples |
|---|---|---|---:|---:|
| bbgg | 1000/1000/1000/1000 | 0/0/0 | 10,953,904 | 15 |
| ccgg | 1000/1000/1000/1000 | 0/0/0 | 11,795,310 | 7 |
| light-jjgg | 1000/1000/1000/1000 | 0/0/0 | 11,885,274 | 9 |

All 16 mapped object branches were present, including Track, Tower and all
three EFlow branches. Their matching size leaves were inspected per event.
Actual dictionary versions were HepMCEvent3, Weight1, GenParticle2, Photon4,
Jet5, MissingET1, ScalarHT1, Track4, Tower5, Electron4 and Muon4. Duplicate
tuples preserve multiplicity; they limit individual source-barcode attribution.

Scientific JSONL SHA-256 values:

| Process | Scientific content SHA-256 | Full local ROOT SHA-256 |
|---|---|---|
| bbgg | 8e2bcda669213e75a4aa84223c267a7f49f9105650b7edc1100f956e56a05fa0 | 5fdbd45889767cb46672c92cf7e858bf3483d68c39fc2c43e4d07e8ddeb1d111 |
| ccgg | 89d312bcf4134e99a49c5dd7483b9d9f08090154f9af26821306d2c8eb896725 | 2c649ea219e0c83b949bb22eba11d63c31be60aa46171dc63b45c564a8d893c2 |
| light-jjgg | 0debed16185a97e9ccc97b816a21a3dc95ca6182a5e51ed1f41c28333b05abbf | 06724b4803753e002c084b9ea81596bafcb1d6b5032d82dbd57df0bee0694e0e |

The eight executed native tests used genuine immutable A10 records and
explicitly derived corruptions, never accepted synthetic references. They
covered unmodified readback, wrong identity, retained p4/position, secondary
weight, NaN, missing required branch and a readable short tree. The short
9-row fixture reported N_output/read/processed=9/9/9, invalid0, skipped1
for requested10. These tests and the separate analytic CTest establish
failure behavior, not additional detector events or calibration.

Full-run physical reports:
[bbgg](../simulation/delphes/evidence/bbgg/native_validation.json),
[ccgg](../simulation/delphes/evidence/ccgg/native_validation.json),
[light-jjgg](../simulation/delphes/evidence/jjgg/native_validation.json).
These attest actual native parsing of the full local ROOT files; portable CI
can verify these report hashes and selected ROOT identities without claiming
to have executed ROOT or independently read omitted full ROOT files.

Sources:
[reader](https://github.com/delphes/delphes/blob/3.5.1/classes/DelphesHepMC3Reader.cc),
[TreeWriter](https://github.com/delphes/delphes/blob/3.5.1/modules/TreeWriter.cc),
[classes](https://github.com/delphes/delphes/blob/3.5.1/classes/DelphesClasses.h).

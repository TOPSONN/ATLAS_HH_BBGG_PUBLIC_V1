# Future Pythia, HepMC, Delphes and ROOT interfaces

Independent S01 profile prepares ISR/FSR/hadronization and external LHE mode.
It intentionally provides no global PDG25 mixed-decay switch. Native per-lineage
decay implementation, signal initialization, source-index/signed-weight and
mother/daughter/conservation closure remain blocked/not evaluated.

C++20 methods were actually compiled/executed against retained ROOT6.40.04,
Pythia8.317 and HepMC3.3.1 headers: const Event interface, ReaderAscii type,
Cartesian invariant mass, null missing pairs and spacelike rejection. This is
API/method evidence only, no native signal HepMC readback and no signal ROOT.

Delphes3.5.1 baseline card unchanged, SHA256
cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47.
Phase6C cuts retained: ≥2 photons pT>25GeV, |eta|<2.37, crack excluded
1.37<|eta|<1.52, leading pT>35GeV; jets pT>25GeV, |eta|<2.5;≥2 bit0 tags;
105≤mgg≤160GeV. ATLAS-like fast simulation only, no official calibration claim.

Future observables: mgg, mbb, mbbgg, mjj, leading/subleading photon/jet pT,
photon/jet/tag multiplicities and ΔRγγ/ΔRbb. Missing pairs are null, H1/H2 only
analysis labels. No optimization before genuine signal; no historical selection
or card changed. All6000 existing ROOT entries were independently reread with
exact reconstructed-record/cutflow preservation and source original-N ledgers.

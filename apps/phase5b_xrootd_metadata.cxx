#include <ROOT/RRawFile.hxx>
#include <cstdint>
#include <iostream>
#include <string>

// This helper opens only the exact official URI and calls GetSize(). It has
// no byte-read, TFile, TTree, staging, copying or output-file operation.
int main(int argc,char** argv) {
  if(argc!=2 || std::string(argv[1])!="--metadata-only") return 2;
  constexpr const char* uri=
    "root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/"
    "ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root";
  try {
    ROOT::Internal::RRawFile::ROptions options;
    options.fBlockSize=0;
    auto remote=ROOT::Internal::RRawFile::Create(uri,options);
    remote->SetBuffering(false);
    if(remote->IsBuffering()) return 3;
    const std::uint64_t size=remote->GetSize();
    std::cout<<"SIZE "<<size<<"\n";
    return 0;
  } catch(...) {
    // XRootD exceptions can include redirect capability URLs. The controller
    // discards stderr and publishes only this fixed diagnostic status.
    std::cout<<"BLOCKED_XROOTD_METADATA\n";
    return 1;
  }
}

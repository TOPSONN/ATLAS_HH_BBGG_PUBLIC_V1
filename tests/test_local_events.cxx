#include "AtlasLocalEvents.h"
#include <TFile.h>
#include <TTree.h>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
int cases = 0;
void check(bool v, const char* m) { ++cases; if (!v) throw std::runtime_error(m); }
template<class F> void refuses(F operation) { bool rejected=false; try { operation(); } catch (...) { rejected=true; } check(rejected, "Unsafe input accepted"); }
void fixture(const std::filesystem::path& path, int mode) {
  TFile file(path.c_str(), "RECREATE"); TTree tree("analysis", "synthetic native RVec input");
  Int_t np=2,nj=2; UInt_t run=1; ULong64_t event=9007199254740993ULL;
  atlas::kinematics::RVec pt{40,30}, eta{0,0}, phi{0,3.14F}, energy{40,30}, jpt{30,25}, je{40,35};
  ROOT::VecOps::RVec<bool> flags{true,false}; std::vector<float> wrong{40,30};
  tree.Branch("photon_n", &np); tree.Branch("jet_n", &nj); tree.Branch("runNumber", &run); tree.Branch("eventNumber", &event);
  if (mode==1) tree.Branch("photon_pt", &wrong); else tree.Branch("photon_pt", &pt);
  tree.Branch("photon_eta", &eta); if (mode!=2) tree.Branch("photon_phi", &phi); tree.Branch("photon_e", &energy);
  tree.Branch("jet_pt", &jpt); tree.Branch("jet_eta", &eta); tree.Branch("jet_phi", &phi); tree.Branch("jet_e", &je);
  for (auto name : {"photon_isTightID", "photon_isLooseID", "photon_isTightIso", "photon_isLooseIso"}) tree.Branch(name, &flags);
  if(mode==3) np=3;
  for(int i=0;i<3;++i) { tree.Fill(); ++event; }
  if(mode==4) { TTree other("friend", "synthetic"); other.Branch("n", &np); other.Fill(); tree.AddFriend(&other); other.Write(); tree.Write(); return; }
  tree.Write();
}
}
int main() {
  try {
    const auto dir = std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR) / "local_events_fixtures";
    std::filesystem::create_directories(dir);
    for(int mode=0;mode<5;++mode) fixture(dir / (std::to_string(mode)+".root"), mode);
    atlas::events::Reader reader(dir/"0.root"); check(reader.entries()==3, "Entry metadata");
    auto event=reader.read(0); check(event.event==9007199254740993ULL, "uint64 event identity");
    check(event.photon_pt.size()==2 && event.tight_id.size()==2, "Native RVec bindings");
    check(reader.read(2).event==9007199254740995ULL, "Explicit entry order");
    refuses([&]{reader.read(-1);}); refuses([&]{reader.read(3);});
    refuses([&]{atlas::events::Reader r("root://example.invalid/input.root");});
    refuses([&]{atlas::events::Reader r(dir/"absent.root");});
    refuses([&]{atlas::events::Reader r(dir/"1.root");});
    refuses([&]{atlas::events::Reader r(dir/"2.root");});
    refuses([&]{atlas::events::Reader r(dir/"3.root"); r.read(0);});
    refuses([&]{atlas::events::Reader r(dir/"4.root");});
    std::cout << "PASS native local reader cases=" << cases << '\n'; return 0;
  } catch(const std::exception& e) { std::cerr << "FAIL: " << e.what() << '\n'; return 1; }
}

#pragma once
#include "Phase8Event.hxx"
#include "DelphesAdapter.hxx"
namespace atlas_hh::phase8 {
class TruthReader {
 std::ifstream input;std::string format;std::unique_ptr<atlas_hh::delphes::TruthIndex> continuum;
 public: TruthReader(const fs::path& path,const std::string& fmt);
 void next(const atlas_hh::delphes::InputEvent& source,Event& event);
 void finish();
};
}

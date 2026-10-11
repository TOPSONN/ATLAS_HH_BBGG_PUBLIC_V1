#pragma once
#include "AtlasLocalEvents.h"
#include <filesystem>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace atlas::mc {
struct NativeField {
  std::string name,type,role;
};
struct TruthCollection {
  bool available=false;
  int count=0;
  kinematics::RVec pt,eta,phi,energy,mass;
  bool energy_available=false,mass_available=false;
};
struct RawEvent {
  events::RawEvent reconstructed;
  std::uint32_t dsid=0;
  double generator_weight=0;
  // Preserved scalar values only; never multiplied into reconstructed counts.
  std::map<std::string,double> diagnostics;
  std::map<std::string,bool> photon_flag_available;
  // Raw native truth objects only; presence does not establish origin/status,
  // matching eligibility, or a validated photon energy prescription.
  TruthCollection truth_photons,truth_jets;
};
// One native TTreeReader binds all values from the same explicit local entry.
// The generator weight accepts only an audited Float_t or Double_t binding.
// MC channel identity is checked at every read; no URI/chain/friend is allowed.
class Reader {
 public:
  Reader(const std::filesystem::path& input,std::uint32_t expected_dsid);
  ~Reader();
  std::int64_t entries() const;
  RawEvent read(std::int64_t index);
  const std::vector<NativeField>& schema() const;
 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};
}

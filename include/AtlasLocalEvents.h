#pragma once
#include "AtlasKinematics.h"
#include <filesystem>
#include <memory>
#include <cstdint>

namespace atlas::events {
struct RawEvent {
  std::uint32_t run = 0;
  std::uint64_t event = 0;
  int photon_n = 0, jet_n = 0;
  kinematics::RVec photon_pt, photon_eta, photon_phi, photon_e;
  kinematics::RVec jet_pt, jet_eta, jet_phi, jet_e;
  ROOT::VecOps::RVec<bool> tight_id, loose_id, tight_iso, loose_iso;
};
// Every read is an explicit local entry index; no URI, chain, friend, or external
// branch storage is allowed. Native RVec types are validated before entry reads.
class Reader {
 public:
  explicit Reader(const std::filesystem::path& input);
  ~Reader();
  std::int64_t entries() const;
  RawEvent read(std::int64_t index);
 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};
}  // namespace atlas::events

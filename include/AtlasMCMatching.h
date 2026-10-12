#pragma once
#include "AtlasMCEvents.h"
#include "AtlasSyntheticMatching.h"
#include <cstdint>
#include <vector>

namespace atlas::mc_matching {
enum class UnitStatus { Unknown, Provisional, Verified };
struct Config {
  UnitStatus unit_status = UnitStatus::Unknown;
  double reco_scale_to_gev = 1, truth_scale_to_gev = 1;
  // Study-defined acceptance for ALL objects, independent of the C9 event
  // selection. No photon crack, ID/isolation, prompt-origin or flavour cut.
  double photon_pt_min = 25, photon_abs_eta_max = 2.37;
  double jet_pt_min = 25, jet_abs_eta_max = 2.5;
  std::vector<double> photon_thresholds{.1, .2, .3};
  std::vector<double> jet_thresholds{.2, .3, .4};
  // Fail closed before constructing the assignment network for pathological
  // multiplicities. These limits are computational, not physics acceptance.
  std::size_t max_eligible_objects_per_collection = 128;
  std::size_t max_candidate_pairs = 4096;
};
struct ThresholdResult {
  double threshold;
  matching::Result assignments;
};
struct ObjectResult {
  bool truth_available = false;
  std::size_t reco_provided = 0, truth_provided = 0;
  std::vector<ThresholdResult> thresholds;
};
struct EventResult {
  std::uint32_t dsid, run;
  std::uint64_t event;
  std::int64_t source_entry;
  UnitStatus unit_status;
  ObjectResult photons, jets;
};
// MC-only adapter: use one RawEvent from the native mc::Reader, which binds
// reco and truth collections in the SAME local entry. Cross-event joins are
// not an input mode. The source entry/identity is retained, not inferred from
// angular proximity. A nonzero native DSID and explicit unit gate are required.
// Missing truth blocks that collection only. Truth photons need no invented
// energy or mass; matching uses documented pt/eta/phi only. Returned assignment
// fractions are conditional geometrical association, not prompt/flavour purity
// or official ATLAS reconstruction efficiencies.
EventResult match_event(const mc::RawEvent&, std::int64_t source_entry, const Config&);
}  // namespace atlas::mc_matching

#include "AtlasMCMatching.h"
#include <algorithm>
#include <cmath>
#include <numbers>
#include <stdexcept>

namespace atlas::mc_matching {
namespace {
void validate_config(const Config& config) {
  if (config.unit_status != UnitStatus::Provisional && config.unit_status != UnitStatus::Verified)
    throw std::invalid_argument("MC geometric matching unit gate is UNKNOWN");
  if (!config.max_eligible_objects_per_collection || !config.max_candidate_pairs)
    throw std::invalid_argument("MC matching work budgets must be positive");
  for (const double value : {config.reco_scale_to_gev, config.truth_scale_to_gev,
                            config.photon_abs_eta_max, config.jet_abs_eta_max})
    if (!std::isfinite(value) || value <= 0) throw std::invalid_argument("Invalid MC matching scale/acceptance");
  for (const double value : {config.photon_pt_min, config.jet_pt_min})
    if (!std::isfinite(value) || value < 0) throw std::invalid_argument("Invalid MC matching pT threshold");
  for (const auto* thresholds : {&config.photon_thresholds, &config.jet_thresholds}) {
    if (thresholds->empty()) throw std::invalid_argument("MC matching threshold scan is empty");
    double previous = 0;
    for (const double value : *thresholds) {
      if (!std::isfinite(value) || value <= previous)
        throw std::invalid_argument("MC matching thresholds must be positive, unique and increasing");
      previous = value;
    }
  }
}
std::vector<matching::Direction> reco_directions(const kinematics::Collection& objects,
                                               double pt_min, double eta_max) {
  if (!objects.valid) throw std::invalid_argument("Invalid reconstructed MC collection for matching");
  std::vector<matching::Direction> directions;
  for (const auto& object : objects.ordered) {
    const double pt = object.p4.Pt(), eta = object.p4.Eta(), phi = object.p4.Phi();
    directions.push_back({static_cast<std::uint64_t>(object.input_index), eta, phi,
                          pt > pt_min && std::abs(eta) < eta_max});
  }
  return directions;
}
std::vector<matching::Direction> truth_directions(const mc::TruthCollection& truth,
                                                double scale, double pt_min, double eta_max) {
  if (truth.count < 0 || truth.pt.size() != static_cast<std::size_t>(truth.count) ||
      truth.eta.size() != truth.pt.size() || truth.phi.size() != truth.pt.size())
    throw std::invalid_argument("Native MC truth collection length mismatch");
  std::vector<matching::Direction> directions;
  for (std::size_t index = 0; index < truth.pt.size(); ++index) {
    const double pt = static_cast<double>(truth.pt[index]) * scale;
    const double eta = truth.eta[index], phi = truth.phi[index];
    if (!std::isfinite(pt) || pt < 0 || !std::isfinite(eta) || !std::isfinite(phi) ||
        std::abs(phi) > std::numbers::pi + 1e-5)
      throw std::invalid_argument("Invalid native MC truth pt/eta/phi");
    directions.push_back({static_cast<std::uint64_t>(index), eta, phi,
                          pt > pt_min && std::abs(eta) < eta_max});
  }
  return directions;
}
ObjectResult match_objects(const kinematics::Collection& reco, const mc::TruthCollection& truth,
                           double truth_scale, double pt_min, double eta_max,
                           const std::vector<double>& thresholds, const Config& config) {
  ObjectResult result; result.reco_provided = reco.ordered.size(); result.truth_available = truth.available;
  if (!truth.available) return result;
  const auto reconstructed = reco_directions(reco, pt_min, eta_max);
  const auto references = truth_directions(truth, truth_scale, pt_min, eta_max);
  result.truth_provided = references.size();
  const auto eligible_reco = static_cast<std::size_t>(std::count_if(reconstructed.begin(), reconstructed.end(),
      [](const auto& object) { return object.eligible; }));
  const auto eligible_truth = static_cast<std::size_t>(std::count_if(references.begin(), references.end(),
      [](const auto& object) { return object.eligible; }));
  if (eligible_reco > config.max_eligible_objects_per_collection ||
      eligible_truth > config.max_eligible_objects_per_collection ||
      (eligible_truth && eligible_reco > config.max_candidate_pairs / eligible_truth))
    throw std::invalid_argument("MC matching assignment work budget exceeded");
  for (const double threshold : thresholds)
    result.thresholds.push_back({threshold, matching::match(reconstructed, references, threshold)});
  return result;
}
}  // namespace

EventResult match_event(const mc::RawEvent& raw, std::int64_t source_entry, const Config& config) {
  validate_config(config);
  if (!raw.dsid || source_entry < 0) throw std::invalid_argument("MC matching requires native DSID and local source entry");
  const auto& event = raw.reconstructed;
  for (const auto* angles : {&event.photon_phi, &event.jet_phi})
    for (const float phi : *angles)
      if (!std::isfinite(phi) || std::abs(static_cast<double>(phi)) > std::numbers::pi + 1e-5)
        throw std::invalid_argument("Invalid native reconstructed MC phi");
  const auto photons = kinematics::construct(event.photon_pt, event.photon_eta, event.photon_phi,
                                             event.photon_e, event.photon_n, config.reco_scale_to_gev);
  const auto jets = kinematics::construct(event.jet_pt, event.jet_eta, event.jet_phi,
                                         event.jet_e, event.jet_n, config.reco_scale_to_gev);
  if (!photons.valid || !jets.valid) throw std::invalid_argument("Invalid reconstructed MC kinematics for matching");
  EventResult result{raw.dsid, event.run, event.event, source_entry, config.unit_status, {}, {}};
  result.photons = match_objects(photons, raw.truth_photons, config.truth_scale_to_gev,
                                config.photon_pt_min, config.photon_abs_eta_max, config.photon_thresholds, config);
  result.jets = match_objects(jets, raw.truth_jets, config.truth_scale_to_gev,
                             config.jet_pt_min, config.jet_abs_eta_max, config.jet_thresholds, config);
  return result;
}
}  // namespace atlas::mc_matching

#include "AtlasKinematics.h"
#include <algorithm>
#include <cmath>
#include <numbers>
#include <stdexcept>
#include <tuple>

namespace atlas::kinematics {
double delta_phi(double first, double second) {
  if (!std::isfinite(first) || !std::isfinite(second))
    throw std::invalid_argument("Nonfinite angle");
  return std::remainder(first - second, 2 * std::numbers::pi);
}
Collection construct(const RVec& pt, const RVec& eta, const RVec& phi,
                     const RVec& energy, int count, double scale) {
  Collection result;
  auto reject = [&](const std::string& why) { result.valid = false; result.issue = why; result.ordered.clear(); };
  if (!std::isfinite(scale) || scale <= 0) { reject("invalid_unit_scale"); return result; }
  if (count < 0 || pt.size() != static_cast<std::size_t>(count) || eta.size() != pt.size() ||
      phi.size() != pt.size() || energy.size() != pt.size()) { reject("collection_size_mismatch"); return result; }
  for (std::size_t i = 0; i < pt.size(); ++i) {
    const double p = double(pt[i]) * scale, e = double(energy[i]) * scale;
    if (!std::isfinite(p) || !std::isfinite(e) || !std::isfinite(eta[i]) || !std::isfinite(phi[i]) || p < 0 || e < 0) {
      reject("nonfinite_or_negative_input"); return result;
    }
    const double momentum = p * std::cosh(double(eta[i]));
    if (!std::isfinite(momentum) || !std::isfinite(e * e) || !std::isfinite(momentum * momentum)) {
      reject("numerical_overflow"); return result;
    }
    const double mass2 = e * e - momentum * momentum;
    const double tolerance = object_mass2_relative_tolerance * std::max({e * e, momentum * momentum, 1.});
    if (mass2 < -tolerance) { reject("spacelike_object"); return result; }
    const bool roundoff = mass2 < 0;
    result.roundoff_objects += roundoff;
    result.ordered.push_back({FourVector(p, eta[i], phi[i], e), i, roundoff});
  }
  // Equal-pT objects use kinematic tie breakers, then original index. Permuting
  // physically identical objects cannot alter the reconstructed observables.
  std::sort(result.ordered.begin(), result.ordered.end(), [](const Candidate& a, const Candidate& b) {
    return std::tuple(-a.p4.Pt(), a.p4.Eta(), a.p4.Phi(), a.p4.E(), a.input_index) <
           std::tuple(-b.p4.Pt(), b.p4.Eta(), b.p4.Phi(), b.p4.E(), b.input_index);
  });
  return result;
}
Pair leading_pair(const Collection& collection) {
  Pair result;
  if (!collection.valid) { result.issue = collection.issue; return result; }
  if (collection.ordered.size() < 2) { result.issue = "fewer_than_two_objects"; return result; }
  result.available = true;
  const auto& a = collection.ordered[0].p4;
  const auto& b = collection.ordered[1].p4;
  const auto sum = a + b;
  const double mass2 = sum.M2();
  // Negative pair m^2 is rejected and reported, including tiny negatives.
  // We never hide it by clamping an invariant mass or modifying energy.
  if (!std::isfinite(mass2) || mass2 < 0) { result.issue = "negative_or_nonfinite_pair_mass2"; return result; }
  result.mass = std::sqrt(mass2);
  result.delta_eta = a.Eta() - b.Eta();
  result.delta_phi = delta_phi(a.Phi(), b.Phi());
  result.delta_r = std::hypot(result.delta_eta, result.delta_phi);
  result.valid = std::isfinite(result.mass) && std::isfinite(result.delta_r);
  if (!result.valid) result.issue = "nonfinite_pair_observable";
  return result;
}
}  // namespace atlas::kinematics

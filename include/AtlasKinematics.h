#pragma once
#include <Math/Vector4D.h>
#include <ROOT/RVec.hxx>
#include <cstddef>
#include <string>
#include <vector>

namespace atlas::kinematics {
using RVec = ROOT::VecOps::RVec<float>;
using FourVector = ROOT::Math::PtEtaPhiEVector;
// Float input rounding may produce small negative single-object m^2. We retain
// the supplied energy and explicitly count these; no four-vector is corrected.
inline constexpr double object_mass2_relative_tolerance = 1e-5;
struct Candidate { FourVector p4; std::size_t input_index; bool negative_roundoff; };
struct Collection {
  bool valid = true;
  std::string issue;
  std::vector<Candidate> ordered;
  std::size_t roundoff_objects = 0;
};
struct Pair {
  bool available = false, valid = false;
  double mass = 0, delta_eta = 0, delta_phi = 0, delta_r = 0;
  std::string issue;
};
Collection construct(const RVec& pt, const RVec& eta, const RVec& phi,
                     const RVec& energy, int count, double scale_to_gev);
double delta_phi(double first, double second);
Pair leading_pair(const Collection& collection);
}  // namespace atlas::kinematics

#pragma once
// Future interface contract only. This header has no event-production calls.
#include <Pythia8/Pythia.h>
#include <HepMC3/ReaderAscii.h>
#include <Math/Vector4D.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <optional>
#include <stdexcept>
#include <string>

namespace hh_signal {
using P4 = ROOT::Math::PxPyPzEVector;
struct DecayPlan {
  int bbOriginalPythiaIndex;
  int gammaOriginalPythiaIndex;
  double samplingProbability = 0.5;
};
inline void validateOriginalPair(const Pythia8::Event& process,
                                const std::array<int, 2>& originalLHEHiggsIndices,
                                const DecayPlan& plan) {
  const auto a=originalLHEHiggsIndices[0], b=originalLHEHiggsIndices[1];
  if(a<=0 || b<=0 || a==b || a>=process.size() || b>=process.size() ||
     process[a].id()!=25 || process[b].id()!=25 ||
     plan.bbOriginalPythiaIndex==plan.gammaOriginalPythiaIndex ||
     !((plan.bbOriginalPythiaIndex==a && plan.gammaOriginalPythiaIndex==b) ||
       (plan.bbOriginalPythiaIndex==b && plan.gammaOriginalPythiaIndex==a)) ||
     plan.samplingProbability!=0.5)
    throw std::runtime_error("S01 original PDG25 lineage/assignment contract failed");
  // Input indices MUST be bound to two original source PDG25 entries by the
  // future LHA ancestry adapter. PDG alone cannot establish original lineage.
}
inline std::optional<double> pairMass(const std::optional<P4>& a,
                                      const std::optional<P4>& b) {
  if(!a || !b) return std::nullopt;
  const auto p=*a+*b;
  const auto m2=p.E()*p.E()-p.Px()*p.Px()-p.Py()*p.Py()-p.Pz()*p.Pz();
  const auto tolerance=1e-12*std::max(1.,p.E()*p.E());
  if(!std::isfinite(m2) || m2 < -tolerance)
    throw std::runtime_error("nonfinite/spacelike Cartesian pair");
  return std::sqrt(std::max(0.,m2));
}
inline constexpr const char* physicalGenerationGate =
  "PHYSICAL_SIGNAL_GENERATION_NOT_AUTHORIZED";
inline constexpr const char* realHepMCAndDelphesGate = "NOT_EVALUATED";
} // namespace hh_signal

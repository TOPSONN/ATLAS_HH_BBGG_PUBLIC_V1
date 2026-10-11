#include "AtlasMCMatching.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace atlas::mc_matching;
namespace {
int assertions = 0;
void check(bool value, const char* message) { ++assertions; if (!value) throw std::runtime_error(message); }
template<class F> void rejected(F action) {
  bool threw = false; try { action(); } catch (const std::exception&) { threw = true; }
  check(threw, "Invalid MC matching fixture accepted");
}
atlas::mc::RawEvent fixture() {
  atlas::mc::RawEvent raw; raw.dsid = 42; raw.generator_weight = -2;
  auto& reco = raw.reconstructed; reco.run = 1; reco.event = 999;
  reco.photon_n = 3; reco.photon_pt = {40,30,25}; reco.photon_eta = {0,.1F,.2F}; reco.photon_phi = {0,0,0};
  for (std::size_t i=0;i<reco.photon_pt.size();++i)
    reco.photon_e.push_back(static_cast<float>(reco.photon_pt[i]*std::cosh(reco.photon_eta[i])));
  reco.jet_n = 2; reco.jet_pt = {50,25}; reco.jet_eta = {0,1}; reco.jet_phi = {0,0}; reco.jet_e = {60,40};
  auto& photons = raw.truth_photons; photons.available = true; photons.count = 4;
  photons.pt = {38,28,25,60}; photons.eta = {.01F,.11F,.2F,3}; photons.phi = {0,0,0,0};
  auto& jets = raw.truth_jets; jets.available = true; jets.count = 2;
  jets.pt = {48,30}; jets.eta = {.01F,2}; jets.phi = {0,0}; jets.mass = {10,12}; jets.mass_available = true;
  return raw;
}
}  // namespace

int main() {
  try {
    Config config; config.unit_status = UnitStatus::Provisional; auto raw = fixture();
    const auto result = match_event(raw,10,config);
    check(result.dsid==42 && result.run==1 && result.event==999 && result.source_entry==10, "Same-entry MC identity lost");
    check(result.unit_status==UnitStatus::Provisional, "Provisional unit status upgraded");
    check(result.photons.reco_provided==3 && result.photons.truth_provided==4, "Provided photon denominators confused with eligible");
    check(result.jets.reco_provided==2 && result.jets.truth_provided==2, "Provided jet denominators incorrect");
    check(result.photons.thresholds.size()==3 && result.jets.thresholds.size()==3, "Threshold sensitivity scan missing");
    for (const auto& threshold : result.photons.thresholds) {
      check(threshold.assignments.eligible_reco==2 && threshold.assignments.eligible_reference==2, "Study photon eligibility incorrect");
      check(threshold.assignments.assignments.size()==2, "Eligible same-entry synthetic photons not matched");
    }
    for (const auto& threshold : result.jets.thresholds) {
      check(threshold.assignments.eligible_reco==1 && threshold.assignments.eligible_reference==2, "Study jet eligibility incorrect");
      check(threshold.assignments.assignments.size()==1 && threshold.assignments.reference_match_fraction()==.5, "Unmatched truth jet denominator omitted");
    }
    check(raw.generator_weight==-2 && raw.truth_photons.pt[2]==25 && !raw.truth_photons.energy_available, "Adapter mutated weight/source or invented photon energy");
    auto signed_mass=raw; signed_mass.truth_jets.mass[0]=-.02453454F;
    const auto signed_result=match_event(signed_mass,10,config);
    for (std::size_t index=0;index<result.jets.thresholds.size();++index) {
      const auto& expected=result.jets.thresholds[index].assignments;
      const auto& actual=signed_result.jets.thresholds[index].assignments;
      check(actual.assignments.size()==expected.assignments.size() && actual.total_delta_r==expected.total_delta_r,
            "Unused signed truth mass changed geometric assignments");
      bool identical=actual.assignments.size()==expected.assignments.size();
      for (std::size_t pair=0;identical && pair<expected.assignments.size();++pair)
        identical=actual.assignments[pair].reco_id==expected.assignments[pair].reco_id &&
                  actual.assignments[pair].reference_id==expected.assignments[pair].reference_id &&
                  actual.assignments[pair].delta_r==expected.assignments[pair].delta_r;
      check(identical, "Unused signed truth mass changed exact partner identities or distances");
    }
    check(signed_mass.truth_jets.mass[0]==-.02453454F && !signed_mass.truth_jets.energy_available,
          "Signed native truth mass mutated or used to invent energy");
    auto missing=raw; missing.truth_photons.available=false;
    const auto partial=match_event(missing,10,config);
    check(!partial.photons.truth_available && partial.photons.thresholds.empty() && partial.jets.thresholds.size()==3, "Missing photon truth blocked unrelated jet matching");
    auto unknown=config; unknown.unit_status=UnitStatus::Unknown; rejected([&]{match_event(raw,10,unknown);});
    auto data=raw; data.dsid=0; rejected([&]{match_event(data,10,config);});
    rejected([&]{match_event(raw,-1,config);});
    auto malformed=raw; malformed.truth_photons.count=5; rejected([&]{match_event(malformed,10,config);});
    malformed=raw; malformed.truth_jets.eta.clear(); rejected([&]{match_event(malformed,10,config);});
    malformed=raw; malformed.truth_photons.pt[0]=-1; rejected([&]{match_event(malformed,10,config);});
    malformed=raw; malformed.truth_photons.phi[0]=4; rejected([&]{match_event(malformed,10,config);});
    malformed=raw; malformed.truth_jets.eta[0]=std::numeric_limits<float>::quiet_NaN(); rejected([&]{match_event(malformed,10,config);});
    malformed=raw; malformed.reconstructed.photon_e[0]=1; rejected([&]{match_event(malformed,10,config);});
    malformed=raw; malformed.reconstructed.jet_phi[0]=4; rejected([&]{match_event(malformed,10,config);});
    auto invalid=config; invalid.photon_thresholds={.2,.2}; rejected([&]{match_event(raw,10,invalid);});
    invalid=config; invalid.jet_thresholds={}; rejected([&]{match_event(raw,10,invalid);});
    invalid=config; invalid.truth_scale_to_gev=0; rejected([&]{match_event(raw,10,invalid);});
    invalid=config; invalid.max_candidate_pairs=0; rejected([&]{match_event(raw,10,invalid);});
    invalid=config; invalid.max_candidate_pairs=3; rejected([&]{match_event(raw,10,invalid);});
    invalid=config; invalid.max_eligible_objects_per_collection=1; rejected([&]{match_event(raw,10,invalid);});
    auto no_crack=raw; no_crack.reconstructed.photon_eta[0]=1.4F;
    no_crack.reconstructed.photon_e[0]=static_cast<float>(40*std::cosh(1.4F)); no_crack.truth_photons.eta[0]=1.4F;
    check(match_event(no_crack,10,config).photons.thresholds[1].assignments.eligible_reco==2, "Matching accidentally applied C9 photon crack selection");
    auto boundary=raw; boundary.reconstructed.photon_eta[0]=.125F; boundary.reconstructed.photon_e[0]=static_cast<float>(40*std::cosh(.125));
    boundary.truth_photons.eta[0]=.125F; auto exact_eta=config; exact_eta.photon_abs_eta_max=.125;
    check(match_event(boundary,10,exact_eta).photons.thresholds[1].assignments.eligible_reco==1 && match_event(boundary,10,exact_eta).photons.thresholds[1].assignments.eligible_reference==1, "Outer eta boundary must be strict");
    std::cout << "PASS SYNTHETIC_MC_ADAPTER assertions=" << assertions << " thresholds=photon0.1/0.2/0.3;jet0.2/0.3/0.4\nPHYSICAL_EVENT_EXECUTION=NOT_THIS_TEST\n";
    return 0;
  } catch (const std::exception& error) {std::cerr << "FAIL MC matching fixture: " << error.what() << '\n'; return 1;}
}

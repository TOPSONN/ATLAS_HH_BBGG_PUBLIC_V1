#pragma once
#include <array>
#include <filesystem>
#include <limits>
#include <string>

namespace atlas::selection {
struct Config {
  std::string version="study-preselection-v1";
  double leading_photon_pt=35, subleading_photon_pt=25, photon_eta_max=2.37;
  double crack_low=1.37, crack_high=1.52, mass_low=105, mass_high=160;
  double jet_pt=25, jet_eta_max=2.5;
};
struct Event {
  bool source_valid=false;
  int photons=0, jets=0;
  std::array<double,2> photon_pt{},photon_eta{},jet_pt{},jet_eta{};
  double mgg=std::numeric_limits<double>::quiet_NaN(), mjj=std::numeric_limits<double>::quiet_NaN();
  std::array<int,2> tight_id{-1,-1}, tight_iso{-1,-1};
};
Config read_config(const std::filesystem::path& path);
bool valid_kinematics(const Event&);
bool photon_multiplicity(const Event&);
bool leading_photon_pt(const Event&,const Config&);
bool subleading_photon_pt(const Event&,const Config&);
bool photon_acceptance(const Event&,const Config&);
bool diphoton_window(const Event&,const Config&);
bool jet_multiplicity(const Event&);
bool jet_pt(const Event&,const Config&);
bool jet_acceptance(const Event&,const Config&);
std::array<bool,10> evaluate(const Event&,const Config&);
}  // namespace atlas::selection

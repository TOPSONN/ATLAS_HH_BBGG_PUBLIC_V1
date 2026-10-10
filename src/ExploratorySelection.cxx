#include "AtlasExploratorySelection.h"
#include <algorithm>
#include <cmath>
#include <cctype>
#include <fstream>
#include <map>
#include <stdexcept>

namespace atlas::selection {
Config read_config(const std::filesystem::path& path) {
  std::ifstream input(path); if(!input) throw std::runtime_error("Cannot read selection configuration");
  std::map<std::string,std::string> fields;
  for(std::string line; std::getline(input,line);) {
    if(!line.empty() && line.back()=='\r') line.pop_back();
    if(line.empty() || line[0]=='#') continue;
    const auto pos=line.find('=');
    if(pos==std::string::npos || !fields.emplace(line.substr(0,pos),line.substr(pos+1)).second)
      throw std::invalid_argument("Malformed or duplicate configuration field");
  }
  if(fields.size()!=10) throw std::invalid_argument("All ten declared configuration fields are required; unknown fields forbidden");
  auto number=[&](const std::string& name) {
    std::size_t used=0; const auto& text=fields.at(name); const double value=std::stod(text,&used);
    if(used!=text.size() || !std::isfinite(value)) throw std::invalid_argument("Invalid finite configuration value: "+name);
    return value;
  };
  Config c;
  c.version=fields.at("definition_version");
  if(c.version.empty() || !std::all_of(c.version.begin(),c.version.end(),[](unsigned char ch){return std::isalnum(ch)||ch=='-'||ch=='_'||ch=='.';}))
    throw std::invalid_argument("Invalid definition version");
  c.leading_photon_pt=number("photon_leading_pt_min_gev"); c.subleading_photon_pt=number("photon_subleading_pt_min_gev");
  c.photon_eta_max=number("photon_abs_eta_max"); c.crack_low=number("photon_crack_low"); c.crack_high=number("photon_crack_high");
  c.mass_low=number("diphoton_mass_low_gev"); c.mass_high=number("diphoton_mass_high_gev");
  c.jet_pt=number("jet_pt_min_gev"); c.jet_eta_max=number("jet_abs_eta_max");
  if(c.subleading_photon_pt<0 || c.leading_photon_pt<c.subleading_photon_pt || c.jet_pt<0 || c.jet_eta_max<=0 ||
     c.crack_low<0 || c.crack_low>=c.crack_high || c.crack_high>=c.photon_eta_max || c.mass_low<0 || c.mass_low>=c.mass_high)
    throw std::invalid_argument("Inconsistent selection thresholds");
  return c;
}
bool valid_kinematics(const Event& e) {
  if(!e.source_valid || e.photons<0 || e.jets<0) return false;
  auto objects=[](int n,const auto& pt,const auto& eta,double mass) {
    for(int i=0;i<std::min(n,2);++i) if(!std::isfinite(pt[i]) || pt[i]<0 || !std::isfinite(eta[i])) return false;
    if(n>=2 && (!std::isfinite(mass) || mass<0 || pt[0]<pt[1])) return false;
    return true;
  };
  return objects(e.photons,e.photon_pt,e.photon_eta,e.mgg) && objects(e.jets,e.jet_pt,e.jet_eta,e.mjj);
}
bool photon_multiplicity(const Event& e) { return e.photons>=2; }
bool leading_photon_pt(const Event& e,const Config& c) { return photon_multiplicity(e) && e.photon_pt[0]>c.leading_photon_pt; }
bool subleading_photon_pt(const Event& e,const Config& c) { return photon_multiplicity(e) && e.photon_pt[1]>c.subleading_photon_pt; }
bool photon_acceptance(const Event& e,const Config& c) {
  if(!photon_multiplicity(e)) return false;
  for(auto eta:e.photon_eta) { const double a=std::abs(eta); if(!(a<c.photon_eta_max) || (a>c.crack_low && a<c.crack_high)) return false; }
  return true;
}
bool diphoton_window(const Event& e,const Config& c) { return photon_multiplicity(e) && e.mgg>=c.mass_low && e.mgg<=c.mass_high; }
bool jet_multiplicity(const Event& e) { return e.jets>=2; }
bool jet_pt(const Event& e,const Config& c) { return jet_multiplicity(e) && e.jet_pt[0]>c.jet_pt && e.jet_pt[1]>c.jet_pt; }
bool jet_acceptance(const Event& e,const Config& c) { return jet_multiplicity(e) && std::abs(e.jet_eta[0])<c.jet_eta_max && std::abs(e.jet_eta[1])<c.jet_eta_max; }
std::array<bool,10> evaluate(const Event& e,const Config& c) {
  std::array<bool,10> passed{true,valid_kinematics(e),photon_multiplicity(e),leading_photon_pt(e,c),subleading_photon_pt(e,c),
                           photon_acceptance(e,c),diphoton_window(e,c),jet_multiplicity(e),jet_pt(e,c),jet_acceptance(e,c)};
  for(std::size_t i=1;i<passed.size();++i) passed[i]=passed[i-1]&&passed[i];
  return passed;
}
}  // namespace atlas::selection

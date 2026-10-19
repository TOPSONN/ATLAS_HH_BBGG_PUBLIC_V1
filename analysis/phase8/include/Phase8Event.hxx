#pragma once
#include "Phase8Dataset.hxx"
#include "Physics.hxx"
#include <array>
#include <map>
#include <optional>
#include <vector>
namespace atlas_hh::phase8 {
using P4=atlas_hh::delphes::P4;
struct Object {int index=0;double pt=0,eta=0,phi=0,mass=0;P4 p;unsigned flavour=0,btag=0;};
struct Event {
 std::string dataset,source_hash,hepmc_hash,weight_scope;long ordinal=0,native_number=0,original=0;
 double weight=0,raw_weight=0;std::vector<Object> photons,jets,selected,eligible,tagged;
 std::array<bool,5> stages{};std::map<std::string,std::optional<double>> observables;
 Json reconstruction=Json::object();
 Json truth=Json{{"status","NOT_APPLICABLE"}};long negative_native_jet_masses=0;
};
inline constexpr std::array<const char*,5> stage_names{"INPUT","PHOTONS","JETS","TWO_BTAGS","FINAL_MGG"};
const std::vector<std::string>& observable_names();
Json event_json(const Event& event);
}

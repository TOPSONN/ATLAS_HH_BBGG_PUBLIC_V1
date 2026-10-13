#pragma once
#include <set>
#include <string>
#include <vector>

namespace atlas_hh {
struct PhotonOrigin {
  std::string label;
  std::vector<int> hard_roots;
  bool original=false,produced_hadron=false,direct_hadron_decay=false,shower_photon=false;
};
// Apply only event-record diagnostics supported by actual status/graph edges.
// Beam status 11..19 and entries 1/2 are never a produced-hadron origin.
template<class Event> PhotonOrigin photon_origin(const Event& event,int index,const std::set<int>& roots){
  PhotonOrigin out;out.original=roots.count(index)!=0;
  std::vector<int> todo{index};std::set<int> seen;
  auto produced_hadron=[&](int i){return i>2&&event[i].isHadron()&&
    !(event[i].statusAbs()>=11&&event[i].statusAbs()<=19);};
  while(!todo.empty()){
    int child=todo.back();todo.pop_back();
    if(child<=0||child>=event.size()||!seen.insert(child).second)continue;
    if(roots.count(child))out.hard_roots.push_back(child);
    if(event[child].id()==22&&event[child].statusAbs()>=41&&event[child].statusAbs()<60)out.shower_photon=true;
    for(int mother:event[child].motherList()){
      if(mother<=0||mother>=event.size())continue;
      if(produced_hadron(mother)){
        out.produced_hadron=true;
        // 91/92: normal/oscillated decay; 93/94: external decay products.
        // A hadron ancestor alone does not establish a direct photon decay.
        if(event[child].id()==22&&event[child].statusAbs()>=91&&event[child].statusAbs()<=94)
          out.direct_hadron_decay=true;
      }
      todo.push_back(mother);
    }
  }
  if(out.direct_hadron_decay&&out.shower_photon)out.label="HADRON_DECAY_AND_SHOWER_ANCESTRY_AMBIGUOUS";
  else if(out.direct_hadron_decay)out.label="HADRON_DECAY_PHOTON_OR_DESCENDANT";
  else if(out.produced_hadron&&out.shower_photon)out.label="SHOWER_WITH_PRODUCED_HADRON_ANCESTOR";
  else if(out.produced_hadron)out.label="HADRON_ANCESTOR_AMBIGUOUS";
  else if(out.original)out.label="HARD_PROCESS_PHOTON";
  else if(!out.hard_roots.empty())out.label="HARD_PHOTON_ANCESTOR";
  else if(out.shower_photon)out.label="SHOWER_WITHOUT_HADRON_ANCESTOR";
  else out.label="AMBIGUOUS";
  return out;
}
}

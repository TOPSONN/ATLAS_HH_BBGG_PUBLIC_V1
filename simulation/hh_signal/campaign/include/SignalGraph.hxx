#pragma once
#include "BackgroundAncestry.hxx"
#include "HepMC3/ReaderAscii.h"
#include <iomanip>

namespace signal {
using zh::require;
struct Lineage {int bb=0,gg=0;std::vector<int>bottoms,photons,finalPhotons;};
inline Lineage inspect(const zh::Graph& graph) {
  std::vector<int> roots;
  for(const auto&[id,node]:graph)if(node.pdg==25){bool copy=false;
    for(int parent:zh::ancestors(graph,id))if(graph.at(parent).pdg==25)copy=true;
    if(!copy)roots.push_back(id);
  }
  require(roots.size()==2,"HH requires two distinct original PDG25 lineages");
  Lineage result;
  for(int root:roots){
    int matches=0;
    for(const auto&[id,node]:graph)if(node.pdg==25&&(id==root||zh::ancestors(graph,id).count(root))){
      std::vector<int> pdgs;for(int child:node.daughters)pdgs.push_back(graph.at(child).pdg);
      std::sort(pdgs.begin(),pdgs.end());
      if(pdgs==std::vector<int>{-5,5}){require(!result.bb,"duplicate Hbb");result.bb=root;result.bottoms=node.daughters;++matches;}
      if(pdgs==std::vector<int>{22,22}){require(!result.gg,"duplicate Hgamma gamma");result.gg=root;result.photons=node.daughters;++matches;}
    }
    require(matches==1,"missing/duplicate direct Higgs decay vertex");
  }
  require(result.bb&&result.gg&&result.bb!=result.gg,"same/missing Higgs decay assignment");
  for(const auto&[id,node]:graph)if(node.pdg==22&&node.status==1){
    std::set<int> origins;
    for(int birth:result.photons)if(zh::photon_copy_from(graph,id,birth))origins.insert(birth);
    if(!origins.empty()){require(origins.size()==1,"ambiguous Higgs photon lineage");result.finalPhotons.push_back(id);}
  }
  require(result.finalPhotons.size()==2,"Hgamma gamma final photons not both retained");
  return result;
}
inline void localClosure(const HepMC3::GenEvent& event,const Lineage& h){
  std::map<int,HepMC3::ConstGenParticlePtr> all;for(const auto&p:event.particles())all[p->id()]=p;
  for(const auto&ids:{h.bottoms,h.photons}){
    auto vertex=all.at(ids.front())->production_vertex();require(bool(vertex),"missing real H decay vertex");
    require(vertex->particles_in().size()==1&&vertex->particles_in().front()->pid()==25&&vertex->particles_out().size()==2,
            "ambiguous H decay mother/daughter vertex");
    HepMC3::FourVector residual;for(const auto&p:vertex->particles_in())residual+=p->momentum();
    for(const auto&p:vertex->particles_out())residual-=p->momentum();
    for(double v:{residual.px(),residual.py(),residual.pz(),residual.e()})require(std::isfinite(v)&&std::abs(v)<1e-5,"native H decay momentum closure failure");
  }
  for(int id:{h.bb,h.gg}){auto p=all.at(id);zh::check_resonance_mass(25,125.,p->generated_mass(),p->momentum());}
}
inline std::string json(const Lineage&h){
  return "{\"H_bb_original\":"+std::to_string(h.bb)+",\"H_gammagamma_original\":"+std::to_string(h.gg)+
    ",\"bottom_birth_ids\":"+zh::integers(h.bottoms)+",\"photon_birth_ids\":"+zh::integers(h.photons)+
    ",\"final_H_photon_ids\":"+zh::integers(h.finalPhotons)+"}";
}
inline void ids(std::ostream&out,const char*tag,const std::vector<int>&v){out<<tag<<' '<<v.size();for(int i:v)out<<' '<<i;out<<'\n';}
} // namespace signal

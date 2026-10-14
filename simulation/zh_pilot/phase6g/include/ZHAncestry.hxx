#pragma once
#include "Authorization.hxx"
#include "Json.hxx"
#include "HepMC3/GenEvent.h"
#include "HepMC3/GenParticle.h"
#include "HepMC3/GenVertex.h"
#include "Pythia8/Pythia.h"
#include <algorithm>
#include <map>
#include <set>
#include <sstream>
#include <vector>

namespace zh {
struct Node {int id=0,pdg=0,status=0;std::vector<int> mothers,daughters;};
using Graph=std::map<int,Node>;
inline void complete_graph(Graph& graph){
  require(!graph.empty()&&graph.size()<=100000,"Empty/unbounded resonance graph");
  for(auto&[id,node]:graph){require(id>0&&id==node.id,"Invalid graph identity");node.daughters.clear();
    require(std::set<int>(node.mothers.begin(),node.mothers.end()).size()==node.mothers.size(),"Duplicate graph mother");}
  for(const auto&[id,node]:graph)for(int parent:node.mothers){require(parent!=id&&graph.count(parent),"Dangling/self graph mother");graph[parent].daughters.push_back(id);}
  std::map<int,int> degrees;std::vector<int> pending;std::size_t visited=0;
  for(const auto&[id,node]:graph){degrees[id]=node.mothers.size();if(!degrees[id])pending.push_back(id);}
  while(!pending.empty()){int id=pending.back();pending.pop_back();++visited;for(int child:graph.at(id).daughters)if(--degrees[child]==0)pending.push_back(child);}
  require(visited==graph.size(),"Cycle in resonance graph");
}
inline Graph hepmc_graph(const HepMC3::GenEvent& event){
  Graph graph;
  for(const auto&p:event.particles()){
    Node node{p->id(),p->pid(),p->status(),{}, {}};
    if(auto vertex=p->production_vertex())for(const auto&parent:vertex->particles_in())node.mothers.push_back(parent->id());
    require(graph.emplace(node.id,node).second,"Duplicate HepMC particle identity");
  }complete_graph(graph);return graph;
}
inline Graph pythia_graph(const Pythia8::Event& event){
  Graph graph;
  for(int i=1;i<event.size();++i){auto mothers=event[i].motherList();mothers.erase(std::remove(mothers.begin(),mothers.end(),0),mothers.end());
    graph.emplace(i,Node{i,event[i].id(),event[i].isFinal()?1:2,mothers,{}});}
  complete_graph(graph);return graph;
}
inline std::set<int> ancestors(const Graph& graph,int id){
  require(graph.count(id),"Missing graph identity");std::vector<int> pending=graph.at(id).mothers;std::set<int> seen;
  while(!pending.empty()){int p=pending.back();pending.pop_back();if(seen.insert(p).second){const auto&m=graph.at(p).mothers;pending.insert(pending.end(),m.begin(),m.end());}}
  return seen;
}
inline int unique_root(const Graph& graph,int pdg){
  std::vector<int> roots;
  for(const auto&[id,node]:graph)if(node.pdg==pdg){bool copy=false;for(int parent:ancestors(graph,id))if(graph.at(parent).pdg==pdg)copy=true;if(!copy)roots.push_back(id);}
  require(roots.size()==1,"Multiple/missing original resonance lineages");return roots.front();
}
struct Lineage {int h=0,z=0;std::vector<int> photons,bottoms,final_photons;std::map<int,int> final_to_birth;};
inline void check_resonance_mass(int pdg,double source_mass,double generated_mass,const HepMC3::FourVector& p){
  require((pdg==25||pdg==23)&&std::isfinite(source_mass)&&std::isfinite(generated_mass)&&source_mass>0&&generated_mass>0&&
    std::isfinite(p.px())&&std::isfinite(p.py())&&std::isfinite(p.pz())&&std::isfinite(p.e())&&p.e()>0,
    "Missing/nonfinite source or HepMC resonance mass/four-vector");
  const double energy2=p.e()*p.e(),momentum2=p.px()*p.px()+p.py()*p.py()+p.pz()*p.pz(),mass2=source_mass*source_mass;
  const double shell=energy2-momentum2;
  // PhaseF's frozen printed-LHE bound is in GeV^2, scaled by the actual
  // kinematics to allow e17.10 rounding and binary64 cancellation at high boost.
  // It does not replace the separate tight generated-mass token comparison.
  const double shell_tolerance=1e-6+5e-9*std::max({energy2,momentum2,mass2,1.0});
  require(std::isfinite(shell)&&shell>0&&std::isfinite(shell_tolerance)&&std::abs(shell-mass2)<=shell_tolerance,
    "Independent source/HepMC resonance invariant mass-squared mismatch; no repair");
  const double tolerance=1e-5+1e-9*std::max(source_mass,generated_mass);
  require(std::abs(generated_mass-source_mass)<=tolerance,
    "Independent source-to-HepMC generated resonance mass mismatch; no repair");
  if(pdg==25)require(std::abs(source_mass-125.0)<=1e-5+1e-9*125.0,"Source H mass differs from frozen125GeV");
  else require(source_mass>=91.188-15*2.441404-tolerance&&source_mass<=91.188+15*2.441404+tolerance,
    "Source Z mass outside frozen15-width MG resonance window");
}
inline std::vector<int> births(const Graph& graph,int pdg,int root,int other,const std::vector<int>& products){
  std::vector<std::vector<int>> choices;
  for(const auto&[id,node]:graph)if(node.pdg==pdg){
    if(id!=root&&!ancestors(graph,id).count(root))continue;
    std::vector<int> child_pdgs;for(int child:node.daughters)child_pdgs.push_back(graph.at(child).pdg);
    auto expected=products;std::sort(child_pdgs.begin(),child_pdgs.end());std::sort(expected.begin(),expected.end());
    if(child_pdgs!=expected)continue;
    bool direct=true;for(int child:node.daughters)if(graph.at(child).mothers!=std::vector<int>{id}||ancestors(graph,child).count(other))direct=false;
    if(direct)choices.push_back(node.daughters);
  }
  require(choices.size()==1,"Missing/ambiguous direct resonance two-body birth");return choices.front();
}
inline Lineage inspect(const Graph& graph){
  Lineage result;result.h=unique_root(graph,25);result.z=unique_root(graph,23);
  require(!ancestors(graph,result.h).count(result.z)&&!ancestors(graph,result.z).count(result.h),"Mixed H/Z original lineage");
  result.photons=births(graph,25,result.h,result.z,{22,22});result.bottoms=births(graph,23,result.z,result.h,{5,-5});
  std::set<int> used;
  for(const auto&[id,node]:graph)if(node.pdg==22&&node.status==1){
    std::vector<int> pending{id};std::set<int> seen,reached;bool pure=true;
    while(!pending.empty()){int current=pending.back();pending.pop_back();if(!seen.insert(current).second)continue;
      if(std::find(result.photons.begin(),result.photons.end(),current)!=result.photons.end()){reached.insert(current);continue;}
      const auto&record=graph.at(current);if(record.pdg!=22||record.mothers.empty()){pure=false;break;}
      for(int parent:record.mothers){if(graph.at(parent).pdg!=22){pure=false;break;}pending.push_back(parent);}if(!pure)break;
    }
    if(!pure||reached.empty())continue;
    require(reached.size()==1&&used.insert(*reached.begin()).second,"Ambiguous/duplicate final H-photon birth copy");
    result.final_photons.push_back(id);result.final_to_birth[id]=*reached.begin();
  }
  require(result.final_photons.size()<=2,"More than two selected direct-H final photons");return result;
}
inline std::string integers(const std::vector<int>& values){std::ostringstream out;out<<'[';for(std::size_t i=0;i<values.size();++i){if(i)out<<',';out<<values[i];}out<<']';return out.str();}
inline std::string lineage_json(const Lineage& value){
  std::ostringstream out;out<<"{\"resonance_ids\":{\"H\":"<<value.h<<",\"Z\":"<<value.z<<"},\"higgs_photon_birth_ids\":"<<integers(value.photons)
    <<",\"z_bottom_birth_ids\":"<<integers(value.bottoms)<<",\"higgs_final_photon_ids\":"<<integers(value.final_photons)<<",\"final_photon_to_birth\":{";
  bool first=true;for(const auto&[id,birth]:value.final_to_birth){if(!first)out<<',';first=false;out<<atlas_hh::quoted(std::to_string(id))<<':'<<birth;}
  out<<"},\"mapping_scope\":\"Native graph IDs; no Pythia-HepMC barcode equivalence assumed\"}";return out.str();
}
}

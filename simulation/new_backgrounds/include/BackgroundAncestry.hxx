#pragma once
#include "Authorization.hxx"
#include "Json.hxx"
#include "HepMC3/GenEvent.h"
#include "HepMC3/GenParticle.h"
#include "HepMC3/GenVertex.h"
#include "HepMC3/Attribute.h"
#include "Pythia8/Pythia.h"
#include <algorithm>
#include <map>
#include <set>
#include <sstream>
#include <vector>

namespace zh {
struct Node {int id=0,pdg=0,status=0;std::vector<int> mothers,daughters;int pythia_status=0;bool hadron=false;};
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
    const auto retained=p->attribute_as_string("original_pythia_status");
    require(!retained.empty(),"Missing native Pythia status identity attribute");
    node.pythia_status=std::stoi(retained);
    auto hadron=p->attribute_as_string("original_pythia_is_hadron");
    require(hadron=="0"||hadron=="1","Missing native particle-data hadron classification");node.hadron=hadron=="1";
    if(auto vertex=p->production_vertex())for(const auto&parent:vertex->particles_in())node.mothers.push_back(parent->id());
    require(graph.emplace(node.id,node).second,"Duplicate HepMC particle identity");
  }complete_graph(graph);return graph;
}
inline Graph pythia_graph(const Pythia8::Event& event){
  Graph graph;
  for(int i=1;i<event.size();++i){auto mothers=event[i].motherList();mothers.erase(std::remove(mothers.begin(),mothers.end(),0),mothers.end());
    graph.emplace(i,Node{i,event[i].id(),event[i].isFinal()?1:2,mothers,{},event[i].status(),event[i].isHadron()});}
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
struct Lineage {int h=0,z=0,t=0,tbar=0,wplus=0,wminus=0,born_photon=0;
  std::vector<int> photons,bottoms,final_photons,born_final,shower_final,hadron_final,other_final,w_products;
  std::map<int,int> final_to_birth;};
inline void check_resonance_mass(int pdg,double source_mass,double generated_mass,const HepMC3::FourVector& p){
  require((pdg==25||pdg==23||std::abs(pdg)==6)&&std::isfinite(source_mass)&&std::isfinite(generated_mass)&&source_mass>0&&generated_mass>0&&
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
  else if(std::abs(pdg)==6)require(std::abs(source_mass-173.0)<=1e-5+1e-9*173.0,"Source top mass differs from frozen173GeV");
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
inline std::vector<int> top_birth(const Graph&graph,int root,int sign){
  std::vector<std::vector<int>> choices;
  for(const auto&[id,node]:graph)if(node.pdg==sign*6&&(id==root||ancestors(graph,id).count(root))&&node.daughters.size()==2){
    int q=0,w=0;bool direct=true;
    for(int child:node.daughters){const auto&v=graph.at(child);if(v.pdg==sign*24)w=child;
      if(v.pdg==sign||v.pdg==sign*3||v.pdg==sign*5)q=child;
      if(v.mothers!=std::vector<int>{id})direct=false;}
    if(q&&w&&direct)choices.push_back({q,w});
  }
  require(choices.size()==1,"Missing/ambiguous inclusive top-to-down-type-quark W birth");return choices.front();
}
inline std::vector<int> w_birth(const Graph&graph,int root,int sign){
  std::vector<std::vector<int>> choices;
  for(const auto&[id,node]:graph)if(node.pdg==sign*24&&(id==root||ancestors(graph,id).count(root))&&node.daughters.size()==2){
    bool direct=true;std::vector<int> pdgs;
    for(int child:node.daughters){pdgs.push_back(graph.at(child).pdg);if(graph.at(child).mothers!=std::vector<int>{id})direct=false;}
    bool valid=false;
    for(int up:{2,4})for(int down:{1,3,5})if(std::find(pdgs.begin(),pdgs.end(),sign*up)!=pdgs.end()&&std::find(pdgs.begin(),pdgs.end(),-sign*down)!=pdgs.end())valid=true;
    for(int charged:{11,13,15})if(std::find(pdgs.begin(),pdgs.end(),-sign*charged)!=pdgs.end()&&std::find(pdgs.begin(),pdgs.end(),sign*(charged+1))!=pdgs.end())valid=true;
    if(valid&&direct)choices.push_back(node.daughters);
  }
  require(choices.size()==1,"Missing/ambiguous inclusive supported W two-fermion birth");return choices.front();
}
inline int hard_root(const Graph&graph,int pdg){
  std::vector<int> found;
  for(const auto&[id,node]:graph)if(node.pdg==pdg&&std::abs(node.pythia_status)==23)found.push_back(id);
  require(found.size()==1,"Missing/ambiguous native hard-final-state identity");return found.front();
}
inline bool photon_copy_from(const Graph&graph,int id,int birth){
  if(!birth)return false;
  std::vector<int> pending{id};std::set<int> seen,reached;
  while(!pending.empty()){int current=pending.back();pending.pop_back();if(!seen.insert(current).second)continue;
    if(current==birth){reached.insert(current);continue;}
    const auto&node=graph.at(current);if(node.pdg!=22||node.mothers.empty())return false;
    for(int parent:node.mothers){if(graph.at(parent).pdg!=22)return false;pending.push_back(parent);}}
  return reached==std::set<int>{birth};
}
inline Lineage inspect(const Graph& graph,const std::string& process){
  Lineage result;
  require(process=="zh"||process=="tth"||process=="bbgj","Unsupported source profile");
  if(process!="bbgj")result.h=unique_root(graph,25);
  if(process=="zh"){
    result.z=unique_root(graph,23);
    require(!ancestors(graph,result.h).count(result.z)&&!ancestors(graph,result.z).count(result.h),"Mixed H/Z original lineage");
    result.bottoms=births(graph,23,result.z,result.h,{5,-5});
  }else if(process=="tth"){
    result.t=unique_root(graph,6);result.tbar=unique_root(graph,-6);
    auto top=top_birth(graph,result.t,1),anti=top_birth(graph,result.tbar,-1);
    result.wplus=top[1];result.wminus=anti[1];
    for(int q:{top[0],anti[0]})if(std::abs(graph.at(q).pdg)==5)result.bottoms.push_back(q);
    auto a=w_birth(graph,result.wplus,1),b=w_birth(graph,result.wminus,-1);
    result.w_products=a;result.w_products.insert(result.w_products.end(),b.begin(),b.end());
  }else{
    result.born_photon=hard_root(graph,22);result.bottoms={hard_root(graph,5),hard_root(graph,-5)};
  }
  if(result.h)result.photons=births(graph,25,result.h,result.z,{22,22});
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
  require(result.final_photons.size()<=2,"More than two selected direct-H final photons");
  for(const auto&[id,node]:graph)if(node.pdg==22&&node.status==1){
    if(photon_copy_from(graph,id,result.born_photon)){result.born_final.push_back(id);continue;}
    bool hadron=false,radiation=false;
    for(int parent:ancestors(graph,id)){const auto&p=graph.at(parent);if(p.hadron&&p.status!=4&&std::abs(p.pythia_status)!=12)hadron=true;}
    const auto status=std::abs(node.pythia_status);
    if((status>=41&&status<60))radiation=true;
    for(int parent:ancestors(graph,id))if(graph.at(parent).pdg==22){int s=std::abs(graph.at(parent).pythia_status);if(s>=41&&s<60)radiation=true;}
    if(hadron)result.hadron_final.push_back(id);else if(radiation)result.shower_final.push_back(id);else result.other_final.push_back(id);
  }
  return result;
}
inline std::string integers(const std::vector<int>& values){std::ostringstream out;out<<'[';for(std::size_t i=0;i<values.size();++i){if(i)out<<',';out<<values[i];}out<<']';return out.str();}
inline std::string lineage_json(const Lineage& value){
  std::ostringstream out;out<<"{\"resonance_ids\":{\"H\":"<<value.h<<",\"Z\":"<<value.z<<"},\"higgs_photon_birth_ids\":"<<integers(value.photons)
    <<",\"bottom_birth_ids\":"<<integers(value.bottoms)<<",\"bottom_birth_origin\":"<<atlas_hh::quoted(value.z?"SOURCE_Z_DECAY":value.t?"PYTHIA_TOP_DECAY_SUPPORTED_B_CHANNELS":"SOURCE_HARD_B_PARTONS")
    <<",\"z_bottom_birth_ids\":"<<(value.z?integers(value.bottoms):"[]")<<",\"higgs_final_photon_ids\":"<<integers(value.final_photons)<<",\"final_photon_to_birth\":{";
  bool first=true;for(const auto&[id,birth]:value.final_to_birth){if(!first)out<<',';first=false;out<<atlas_hh::quoted(std::to_string(id))<<':'<<birth;}
  out<<"},\"top_root\":"<<value.t<<",\"antitop_root\":"<<value.tbar<<",\"Wplus_root\":"<<value.wplus<<",\"Wminus_root\":"<<value.wminus
     <<",\"W_birth_products\":"<<integers(value.w_products)<<",\"Born_photon_root\":"<<value.born_photon<<",\"Born_photon_final_ids\":"<<integers(value.born_final)
     <<",\"shower_photon_final_ids\":"<<integers(value.shower_final)<<",\"hadron_decay_photon_final_ids\":"<<integers(value.hadron_final)
     <<",\"other_photon_final_ids\":"<<integers(value.other_final)
     <<",\"mapping_scope\":\"Native graph IDs; original Pythia statuses retained through exact converter graph bijection; no barcode equality assumed\"}";return out.str();
}

// The official converter reorders particles topologically. Recover its actual
// graph bijection using exact native tuples and already mapped mother sets.
// Ambiguous tuples fail; no barcode-index equivalence or momentum repair.
inline void retain_pythia_identity(const Pythia8::Event& source,HepMC3::GenEvent& output){
  auto graph=pythia_graph(source);std::map<int,int> mapped;std::set<int> used;
  std::map<int,HepMC3::GenParticlePtr> particles;for(const auto&p:output.particles())particles.emplace(p->id(),p);
  auto same=[](double a,double b){return a==b;};
  while(mapped.size()<graph.size()){
    bool progress=false;
    for(const auto&[index,node]:graph){if(mapped.count(index))continue;bool ready=true;std::set<int> parents;
      for(int parent:node.mothers){if(!mapped.count(parent)){ready=false;break;}parents.insert(mapped.at(parent));}if(!ready)continue;
      const auto&s=source[index];std::vector<int> candidates;
      for(const auto&[id,p]:particles){if(used.count(id)||p->pid()!=s.id()||p->status()!=s.statusHepMC())continue;
        const auto&v=p->momentum();if(!same(v.px(),s.px())||!same(v.py(),s.py())||!same(v.pz(),s.pz())||!same(v.e(),s.e())||!same(p->generated_mass(),s.m()))continue;
        std::set<int> actual;if(auto vertex=p->production_vertex())for(const auto&parent:vertex->particles_in())actual.insert(parent->id());
        if(actual==parents)candidates.push_back(id);
      }
      require(candidates.size()==1,"Ambiguous/missing exact native converter particle graph mapping");
      int id=candidates.front();mapped[index]=id;used.insert(id);auto p=particles.at(id);
      p->add_attribute("original_pythia_index",std::make_shared<HepMC3::IntAttribute>(index));
      p->add_attribute("original_pythia_status",std::make_shared<HepMC3::IntAttribute>(s.status()));progress=true;
      p->add_attribute("original_pythia_is_hadron",std::make_shared<HepMC3::IntAttribute>(s.isHadron()?1:0));
    }
    require(progress,"Native converter identity mapping stalled");
  }
  require(used.size()==particles.size(),"Converter added/omitted unmapped native particles");
}
}

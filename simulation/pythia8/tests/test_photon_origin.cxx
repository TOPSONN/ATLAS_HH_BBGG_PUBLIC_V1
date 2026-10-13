// Synthetic graph fixtures test classification logic; no physical events.
#include "PhotonOrigin.hxx"
#include <cstdlib>
#include <iostream>
#include <vector>
struct Particle {
  int pid,status;bool hadron;std::vector<int> mothers;
  int id()const{return pid;}int statusAbs()const{return std::abs(status);}
  bool isHadron()const{return hadron;}std::vector<int> motherList()const{return mothers;}
};
int main(){
  std::vector<Particle> event={{0,0,false,{}},{2212,-12,true,{}},{2212,-12,true,{}},
    {2,-21,false,{1}},{-2,-21,false,{2}},{22,23,false,{3,4}},
    {111,-83,true,{3,4}},{22,91,false,{6}},{11,-91,false,{6}},
    {22,51,false,{8}},{22,51,false,{3}},{22,1,false,{}},{22,1,false,{5}}};
  auto check=[&](int i,const std::string&expected){auto result=atlas_hh::photon_origin(event,i,{5});
    if(result.label!=expected){std::cerr<<i<<' '<<result.label<<" != "<<expected<<'\n';return false;}return true;};
  if(!check(5,"HARD_PROCESS_PHOTON")||!check(7,"HADRON_DECAY_PHOTON_OR_DESCENDANT")
     ||!check(9,"SHOWER_WITH_PRODUCED_HADRON_ANCESTOR")||!check(10,"SHOWER_WITHOUT_HADRON_ANCESTOR")
     ||!check(11,"AMBIGUOUS")||!check(12,"HARD_PHOTON_ANCESTOR"))return 1;
  auto hard=atlas_hh::photon_origin(event,5,{5});if(hard.produced_hadron||!hard.original||hard.hard_roots!=std::vector<int>{5})return 1;
  return 0;
}

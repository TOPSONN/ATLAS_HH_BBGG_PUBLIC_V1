#include "Physics.hxx"
#include <iostream>
using namespace atlas_hh::delphes;
int main(){try{
  const auto a=polar(50,0,0,0),b=polar(50,0,std::acos(-1.),0);
  require(std::abs((a+b).mass()-100)<1e-12,"back-to-back Cartesian mass");
  const auto c=polar(100,6,0,0),d=polar(100,6,std::acos(-1.),0);
  require(std::abs((c+d).mass()-200)<1e-8,"boosted Cartesian mass");
  require(dr(polar(30,0,3.13,0),polar(30,0,-3.13,0))<.03,"phi wrapping");
  auto match=unique_match({polar(30,0,0,0),polar(30,.19,0,0)},{polar(30,.10,0,0),polar(30,-.12,0,0)},.21);
  require(match.pairs.size()==2&&match.pairs[0].reco==1&&match.pairs[1].reco==0,"global assignment defeats greedy loss");
  auto none=unique_match({polar(30,0,0,0)},{polar(30,0,.2,0)},.2);
  require(none.pairs.empty(),"matching radius strict boundary");
  auto tied=unique_match({a,a},{a,a},.2);require(tied.pairs.size()==2&&tied.ambiguous_truth==2&&tied.ambiguous_reco==2,"deterministic duplicate ambiguity");
  require(!photon_fiducial(polar(25,0,0,0))&&photon_fiducial(polar(25.01,0,0,0)),"photon pT strict cut");
  require(!photon_fiducial(polar(50,1.4,0,0))&&!jet_fiducial(polar(25,0,0,0)),"crack/jet cuts");
  require(!photon_fiducial(25,0)&&!jet_fiducial(25,0),"native exact PT25 boundary independent of phi");
  require(photon_fiducial(50,1.37)&&photon_fiducial(50,1.52)&&!photon_fiducial(50,2.37),"native exact eta/crack boundaries");
  const auto signed_jet=polar(50,0,.723,-5e-7);
  require(signed_jet.e<50.000000000001L,"bounded ROOT signed mass convention");
  bool rejected=false;try{(void)polar(50,0,.723,-.01);}catch(const std::runtime_error&){rejected=true;}
  require(rejected,"materially spacelike native jet rejected");
  require(flavor_category(5)==5&&flavor_category(4)==4&&flavor_category(21)==0&&flavor_category(6)==-1,"actual-flavour categories");
  require(possible_flavors(2,{4,5})==std::set<unsigned>({2,4,5}),"boundary permits only attainable flavors");
  require(possible_flavors(5,{0,4})==std::set<unsigned>({5}),"lower-priority boundary cannot change b flavor");
  require(possible_flavors(-1,{0})==std::set<unsigned>({0,21}),"unmatched versus boundary gluon");
  auto interval=wilson(0,10);require(interval.low==0&&interval.high>.27&&interval.high<.29,"zero-success uncertainty");
  auto all=wilson(10,10);require(all.low>.72&&all.low<.73&&all.high==1,"all-success uncertainty");
  require(tag_probability(5,50)>.67&&tag_probability(5,50)<.68&&tag_probability(4,50)>.12&&tag_probability(0,50)>.002,"source-reviewed tag formulas");
  std::cout<<"PASS: analytic/API fixtures only; no generated detector events\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}

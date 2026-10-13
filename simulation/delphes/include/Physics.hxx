#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <set>
#include <vector>

namespace atlas_hh::delphes {
inline void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
struct P4 {
  long double x=0,y=0,z=0,e=0;
  P4 operator+(const P4& b)const{return{x+b.x,y+b.y,z+b.z,e+b.e};}
  long double pt()const{return std::hypot(x,y);}
  long double eta()const{return pt()>0?std::asinh(z/pt()):std::copysign(999.9L,z);}
  long double phi()const{return std::atan2(y,x);}
  long double mass()const{
    const auto p=std::hypot(std::hypot(x,y),z),m2=(e-p)*(e+p);
    const auto tol=64*std::numeric_limits<long double>::epsilon()*std::max(e*e,1.0L);
    require(m2>=-tol,"unphysical summed Cartesian four-vector");
    return std::sqrt(std::max(m2,0.0L));
  }
};
inline P4 polar(double pt,double eta,double phi,double mass){
  require(std::isfinite(pt)&&std::isfinite(eta)&&std::isfinite(phi)&&std::isfinite(mass)&&pt>=0,"invalid polar object");
  P4 p{pt*std::cos((long double)phi),pt*std::sin((long double)phi),pt*std::sinh((long double)eta),0};
  const long double p2=p.x*p.x+p.y*p.y+p.z*p.z,m2=(long double)mass*std::abs(mass);
  if(mass<0)require(-m2<=16*std::numeric_limits<double>::epsilon()*p2,"native negative mass exceeds double-cancellation bound");
  // ROOT SetXYZM uses signed M: negative M gives E²=p²-|M²|.
  p.e=std::sqrt(p2+m2);return p;
}
inline long double dr(const P4&a,const P4&b){
  return std::hypot(a.eta()-b.eta(),std::remainder(a.phi()-b.phi(),2*std::acos(-1.0L)));
}
inline bool photon_fiducial(const P4&p){auto a=std::abs(p.eta());return p.pt()>25&&a<2.37L&&!(a>1.37L&&a<1.52L);}
inline bool jet_fiducial(const P4&p){return p.pt()>25&&std::abs(p.eta())<2.5L;}
inline bool photon_fiducial(double pt,double eta){auto a=std::abs(eta);return pt>25&&a<2.37&&!(a>1.37&&a<1.52);}
inline bool jet_fiducial(double pt,double eta){return pt>25&&std::abs(eta)<2.5;}
inline int flavor_category(unsigned f){return f==5?5:f==4?4:(f==0||f==1||f==2||f==3||f==21)?0:-1;}
// Definite candidates must be included. A boundary candidate may be included
// or excluded: highest-quark-PDG priority permits only these resulting flavors.
inline std::set<unsigned> possible_flavors(int definite,const std::vector<int>&boundary){
  std::set<int>priorities{definite};
  for(int candidate:boundary){auto old=priorities;for(int value:old)priorities.insert(std::max(value,candidate));}
  std::set<unsigned>out;for(int value:priorities)out.insert(value<0?0:value==0?21:value);return out;
}
inline double tag_probability(unsigned flavor,double pt){
  if(flavor==5)return .80*std::tanh(.003*pt)*(30/(1+.086*pt));
  if(flavor==4)return .20*std::tanh(.02*pt)/(1+.0034*pt);
  return .002+7.3e-6*pt;
}
struct Interval{double estimate=0,low=0,high=0;};
inline Interval wilson(long k,long n){
  require(n>0&&k>=0&&k<=n,"invalid efficiency counts");
  constexpr double z=1.959963984540054;const double p=double(k)/n,d=1+z*z/n;
  const double center=(p+z*z/(2*n))/d,half=z*std::sqrt(p*(1-p)/n+z*z/(4.*n*n))/d;
  return {p,k==0?0.:std::max(0.,center-half),k==n?1.:std::min(1.,center+half)};
}
struct Pair{int truth,reco;long double distance;};
struct Match{std::vector<Pair> pairs;long candidate_edges=0,ambiguous_truth=0,ambiguous_reco=0;};
// Successive shortest residual paths: maximum cardinality first, then minimum
// total distance. Exact equal costs retain first edge in ordered traversal;
// no numerical epsilon changes geometry or costs.
inline Match unique_match(const std::vector<P4>&truth,const std::vector<P4>&reco,long double radius){
  struct Edge{int to,reverse,capacity;long double cost;};
  const int nt=truth.size(),nr=reco.size(),sink=nt+nr+1,n=sink+1;
  std::vector<std::vector<Edge>> graph(n);std::vector<int> td(nt),rd(nr);Match result;
  auto add=[&](int a,int b,long double cost){int ai=graph[a].size(),bi=graph[b].size();graph[a].push_back({b,bi,1,cost});graph[b].push_back({a,ai,0,-cost});};
  for(int i=0;i<nt;++i)add(0,i+1,0);
  for(int j=0;j<nr;++j)add(nt+1+j,sink,0);
  for(int i=0;i<nt;++i)for(int j=0;j<nr;++j){auto distance=dr(truth[i],reco[j]);if(distance<radius){add(i+1,nt+1+j,distance);++td[i];++rd[j];++result.candidate_edges;}}
  for(auto degree:td)result.ambiguous_truth+=degree>1;
  for(auto degree:rd)result.ambiguous_reco+=degree>1;
  while(true){
    std::vector<long double> distance(n,std::numeric_limits<long double>::infinity());std::vector<int> parent(n,-1),edge(n,-1);distance[0]=0;
    for(int step=0;step<n-1;++step){
      bool changed=false;
      for(int a=0;a<n;++a)if(std::isfinite(distance[a])){
        for(int k=0;k<int(graph[a].size());++k){
          const auto&v=graph[a][k];
          if(v.capacity&&distance[a]+v.cost<distance[v.to]){
            distance[v.to]=distance[a]+v.cost;parent[v.to]=a;edge[v.to]=k;changed=true;
          }
        }
      }
      if(!changed)break;
    }
    if(parent[sink]<0)break;
    int hops=0;for(int v=sink;v!=0;v=parent[v]){require(parent[v]>=0&&++hops<=n,"invalid residual matching path");auto&e=graph[parent[v]][edge[v]];--e.capacity;++graph[v][e.reverse].capacity;}
  }
  for(int i=0;i<nt;++i)for(const auto&e:graph[i+1])if(e.to>=nt+1&&e.to<nt+1+nr&&e.capacity==0)result.pairs.push_back({i,e.to-nt-1,e.cost});
  return result;
}
}

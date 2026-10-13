#pragma once
#include "Physics.hxx"
#include "classes/DelphesClasses.h"
#include <TBranchElement.h>
#include <TClass.h>
#include <TClonesArray.h>
#include <TFile.h>
#include <TLeaf.h>
#include <TStreamerInfo.h>
#include <TTree.h>
#include <array>
#include <bit>
#include <fstream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <tuple>

namespace atlas_hh::delphes {
struct InputParticle{int id,pid,status,vertex;P4 p;double mass;std::array<double,4>position{};};
struct InputEvent{long ordinal,number,source_index,source_count;std::string hash,source_hash;double contribution,raw;std::vector<double>weights;std::vector<InputParticle>particles;};
struct TruthObject{int id,pid,b=0,c=0;P4 p;double mass=0;};
struct TruthEvent{long ordinal,number,source_index;std::string source_hash,run;int seed;std::vector<TruthObject>lhe_photons,final_photons,lhe_partons,hard_partons,heavy;};
inline double read_real(std::istream&in){double v;require(bool(in>>v)&&std::isfinite(v),"invalid/non-finite source index real");return v;}
class InputIndex{
  std::ifstream in;
public:
  explicit InputIndex(const std::string&path):in(path){std::string magic;require(bool(in>>magic)&&magic=="ATLAS_DELPHES_INPUT_V1","invalid native input index magic");}
  bool next(InputEvent&e){
    std::string key;if(!(in>>key)){require(in.eof(),"input index read error");return false;}
    int np,nw;require(key=="E"&&bool(in>>e.ordinal>>e.number>>e.hash>>e.source_index>>e.source_hash),"invalid E input index");
    e.contribution=read_real(in);e.raw=read_real(in);require(bool(in>>e.source_count>>np>>nw)&&e.source_count>0&&np>0&&np<=100000&&nw>0&&nw<=256,"invalid/bounded input counts");
    require(std::abs(e.contribution-e.raw/e.source_count)<=1e-12*std::max(1.,std::abs(e.contribution)),"input contribution denominator mismatch");
    require(bool(in>>key)&&key=="W","missing W input index");e.weights.clear();for(int i=0;i<nw;++i)e.weights.push_back(read_real(in));
    require(e.weights.front()==e.contribution,"input nominal vector/contribution mismatch");
    e.particles.clear();for(int i=0;i<np;++i){InputParticle p{};require(bool(in>>key>>p.id>>p.pid>>p.status)&&key=="P","invalid P input index");p.p={read_real(in),read_real(in),read_real(in),read_real(in)};p.mass=read_real(in);require(bool(in>>p.vertex),"missing source production vertex");for(auto&v:p.position)v=read_real(in);e.particles.push_back(p);}return true;
  }
};
class TruthIndex{
  std::ifstream in;
  void objects(std::vector<TruthObject>&out,int n,char type){out.clear();for(int i=0;i<n;++i){char key;TruthObject o;require(bool(in>>key>>o.id>>o.pid)&&key==type,"invalid truth object row");if(type=='H')require(bool(in>>o.b>>o.c),"invalid terminal heavy flags");o.p={read_real(in),read_real(in),read_real(in),read_real(in)};o.mass=read_real(in);out.push_back(o);}}
public:
  explicit TruthIndex(const std::string&path):in(path){std::string magic;require(bool(in>>magic)&&magic=="ATLAS_DELPHES_TRUTH_V1","invalid native truth index magic");}
  bool next(TruthEvent&e){std::string key;if(!(in>>key)){require(in.eof(),"truth index read error");return false;}int nl,ng,nq,nr,nh;
    require(key=="E"&&bool(in>>e.ordinal>>e.number>>e.source_index>>e.source_hash>>e.run>>e.seed>>nl>>ng>>nq>>nr>>nh),"invalid truth E row");
    require(nl==2&&ng==2&&nq==2&&nr==2&&nh>=0&&nh<=100000,"baseline hard/truth cardinality mismatch");
    objects(e.lhe_photons,nl,'L');objects(e.final_photons,ng,'G');objects(e.lhe_partons,nq,'Q');objects(e.hard_partons,nr,'R');objects(e.heavy,nh,'H');return true;
  }
};
struct Branch{std::string name,clone;bool required,present=false;int version=0;unsigned checksum=0;TClonesArray*array=nullptr;};
class Adapter{
public:
  std::unique_ptr<TFile>file;TTree*tree=nullptr;std::map<std::string,Branch>branches;
  std::vector<std::pair<std::string,std::string>>inventory;
  explicit Adapter(const std::string&path,long* entries=nullptr):file(TFile::Open(path.c_str(),"READ")){
    require(file&&!file->IsZombie()&&!file->IsWritable()&&!file->TestBit(TFile::kRecovered),"invalid/zombie/recovered ROOT file");
    file->GetObject("Delphes",tree);require(tree,"actual Delphes tree missing");
    if(entries)*entries=tree->GetEntries();
    require(!tree->GetListOfFriends()||tree->GetListOfFriends()->GetEntries()==0,"external ROOT friends refused");
    const std::map<std::string,std::string>expected{{"Event","HepMCEvent"},{"Weight","Weight"},{"Particle","GenParticle"},{"Photon","Photon"},{"Jet","Jet"},{"GenJet","Jet"},{"MissingET","MissingET"},{"ScalarHT","ScalarHT"},{"Track","Track"},{"Tower","Tower"},{"Electron","Electron"},{"Muon","Muon"},{"EFlowTrack","Track"},{"EFlowPhoton","Tower"},{"EFlowNeutralHadron","Tower"},{"GenMissingET","MissingET"}};
    TIter next(tree->GetListOfBranches());while(auto*b=dynamic_cast<TBranch*>(next()))inventory.emplace_back(b->GetName(),b->GetClassName());
    for(const auto&[name,clone]:expected){auto&entry=branches[name];entry={name,clone,name=="Event"||name=="Weight"||name=="Particle"||name=="Photon"||name=="Jet"||name=="GenJet"||name=="MissingET"||name=="ScalarHT"};auto*branch=tree->GetBranch(name.c_str());entry.present=branch;
      if(!branch){require(!entry.required,"required Delphes branch missing");continue;}
      require(std::string(branch->GetClassName())=="TClonesArray","branch is not real TClonesArray");
      auto*element=dynamic_cast<TBranchElement*>(branch);require(element&&std::string(element->GetClonesName())==clone,"wrong Delphes clones class");
      auto*cls=TClass::GetClass(clone.c_str());require(cls&&cls->IsLoaded()&&cls->GetClassInfo(),"actual Delphes dictionary unavailable");entry.version=cls->GetClassVersion();entry.checksum=cls->GetCheckSum();
      auto*disk=dynamic_cast<TStreamerInfo*>(file->GetStreamerInfoList()->FindObject(clone.c_str()));require(disk&&disk->GetClassVersion()==entry.version&&disk->GetCheckSum()==entry.checksum,"Delphes streamer/dictionary mismatch");
      require(tree->SetBranchAddress(name.c_str(),&entry.array)>=0,"cannot bind actual clones branch");
    }
  }
  void read(long entry){require(tree->GetEntry(entry)>0,"ROOT basket/entry read failure");for(const auto&[name,b]:branches)if(b.present){require(b.array&&b.array->GetClass()->GetName()==b.clone,"runtime clones dictionary mismatch");auto*size=tree->GetLeaf((name+"_size").c_str());require(size&&std::string(size->GetTypeName())=="Int_t"&&size->GetValue()==b.array->GetEntriesFast(),"clones array/size leaf disagreement");for(int i=0;i<b.array->GetEntriesFast();++i)require(b.array->At(i)&&b.array->At(i)->IsA()==TClass::GetClass(b.clone.c_str()),"wrong/null runtime clone object");}}
  template<class T>std::vector<T*> get(const char*name)const{std::vector<T*>v;const auto&b=branches.at(name);if(b.present)for(int i=0;i<b.array->GetEntriesFast();++i)v.push_back(static_cast<T*>(b.array->At(i)));return v;}
};
// Candidate order changes in the official reader. Canonical float32 tuples
// retain multiplicities, without invented ROOT/Pythia/HepMC barcode equality.
using ParticleTuple=std::tuple<int,int,float,float,float,float,float,float,float,float,float>;
inline ParticleTuple tuple(const InputParticle&p){return{p.pid,p.status,float(p.p.x),float(p.p.y),float(p.p.z),float(p.p.e),float(p.mass),float(p.position[0]),float(p.position[1]),float(p.position[2]),float(p.position[3]*1e-3/2.99792458e8)};}
inline ParticleTuple tuple(const GenParticle&p){return{p.PID,p.Status,p.Px,p.Py,p.Pz,p.E,p.Mass,p.X,p.Y,p.Z,p.T};}
}

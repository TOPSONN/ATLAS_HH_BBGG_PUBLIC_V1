#include "Phase8Reader.hxx"
#include <TDataMember.h>
#include <TDataType.h>
#include <RVersion.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <map>
#include <set>
namespace p8=atlas_hh::phase8;
namespace dp=atlas_hh::delphes;
using Json=p8::Json;
namespace {
struct Summary {
 long n=0, finite=0, nonzero=0; double low=std::numeric_limits<double>::infinity(),high=-std::numeric_limits<double>::infinity();
 std::set<double> unique; bool capped=false;
 void add(double v){++n;if(!std::isfinite(v))return;++finite;if(v!=0)++nonzero;low=std::min(low,v);high=std::max(high,v);if(unique.size()<64)unique.insert(v);else if(!unique.count(v))capped=true;}
 Json json()const{Json j{{"objects",n},{"finite",finite},{"nonfinite",n-finite},{"nonzero",nonzero},{"distinct_values_up_to_64",unique},{"distinct_values_capped",capped},{"nontrivial",finite>0&&(low!=high||low!=0)}};j["minimum"]=finite?Json(low):Json(nullptr);j["maximum"]=finite?Json(high):Json(nullptr);return j;}
};
struct Field {std::string name,type;long offset;int elements;std::map<int,Summary> values;};
bool numeric(const std::string&t){return t=="Float_t"||t=="float"||t=="Double_t"||t=="double"||t=="Int_t"||t=="int"||t=="UInt_t"||t=="unsigned int"||t=="Bool_t"||t=="bool";}
template<class T>double as(const char*p){T v{};std::memcpy(&v,p,sizeof(v));return v;}
std::size_t width(const std::string&t){if(t=="Double_t"||t=="double")return sizeof(double);if(t=="Bool_t"||t=="bool")return sizeof(bool);return sizeof(float);}
double value(const char*p,const std::string&t){if(t=="Float_t"||t=="float")return as<float>(p);if(t=="Double_t"||t=="double")return as<double>(p);if(t=="Int_t"||t=="int")return as<int>(p);if(t=="UInt_t"||t=="unsigned int")return as<unsigned>(p);return as<bool>(p);}
std::vector<Field> fields(const std::string&name){
 auto*cls=TClass::GetClass(name.c_str());p8::demand(cls,"missing object class");std::vector<Field> out;TIter it(cls->GetListOfDataMembers());
 while(auto*m=dynamic_cast<TDataMember*>(it())){
  const std::string t=m->GetTrueTypeName();if(!numeric(t)||m->GetOffset()<0||(m->Property()&kIsStatic))continue;
  int n=1;for(int d=0;d<m->GetArrayDim();++d){p8::demand(m->GetMaxIndex(d)>0&&m->GetMaxIndex(d)<=64,"unbounded observable array");n*=m->GetMaxIndex(d);}p8::demand(n<=64,"oversized observable array");out.push_back({m->GetName(),t,m->GetOffset(),n,{}});
 }
 p8::demand(!out.empty(),"empty scalar observable inventory");return out;
}
}
int main(int argc,char**argv){try{
 p8::demand(argc==5&&std::string(argv[1])=="--manifest"&&std::string(argv[3])=="--output","usage: phase10_photon_observability --manifest RESOLVED_PHASE8_MANIFEST --output FRESH_JSON");
 auto all=p8::datasets(p8::read_json(argv[2]));Json rows=Json::array();long total=0;std::set<std::string> ids;
 for(const auto&d:all){if(d.id.size()!=3||d.id[0]!='B')continue;p8::demand(ids.insert(d.id).second&&d.full&&d.entries==1000,"six full frozen backgrounds required");p8::verify_dataset_files(d);
  long entries=-1;dp::Adapter a(d.root.string(),&entries);p8::demand(entries==d.entries,"entry count changed");std::map<std::string,std::vector<Field>> f;for(const auto&name:{"Photon","Electron","Jet"})f[name]=fields(name);
  std::map<std::string,long> objects;std::set<long> eventnumbers;
  for(long i=0;i<entries;++i){a.read(i);auto ev=a.get<HepMCEvent>("Event");p8::demand(ev.size()==1&&eventnumbers.insert(ev[0]->Number).second,"invalid native event identity");
   for(auto&[name,ff]:f){const auto&b=a.branches.at(name);if(!b.present)continue;for(int j=0;j<b.array->GetEntriesFast();++j){auto*o=b.array->At(j);++objects[name];for(auto&field:ff){const char*base=reinterpret_cast<const char*>(o)+field.offset;for(int e=0;e<field.elements;++e)field.values[e].add(value(base+e*width(field.type),field.type));}}}
  }
  Json branches=Json::object();for(const auto&[name,ff]:f){const auto&b=a.branches.at(name);Json members=Json::array();for(const auto&field:ff){Json vv=Json::array();for(int e=0;e<field.elements;++e){auto it=field.values.find(e);auto v=it==field.values.end()?Summary{}.json():it->second.json();v["array_index"]=e;vv.push_back(v);}members.push_back({{"name",field.name},{"type",field.type},{"elements",field.elements},{"profiles",vv}});}branches[name]={{"present",b.present},{"class",b.clone},{"dictionary_version",b.version},{"dictionary_checksum",b.checksum},{"objects",objects[name]},{"numeric_members",members}};}
  p8::verify_dataset_files(d);total+=entries;rows.push_back({{"dataset_id",d.id},{"events_read",entries},{"root_sha256",d.root_hash},{"card_sha256",d.card_hash},{"branches",branches},{"source_hashes_unchanged_after_loop",true}});
 }
 p8::demand(ids==std::set<std::string>{"B01","B02","B03","B04","B05","B06"}&&total==6000,"incomplete 6000 background observable profile");
 Json out{{"schema_version",1},{"evidence_class","ACTUAL_EXISTING_DATA_READBACK"},{"status","PASS_NATIVE_OBSERVABLE_PROFILE_WITH_LIMITS"},{"scope","Native scalar observability only; full source joins retained in Phase9; no photon ID reinterpretation"},{"readback_reason","Phase8/9 normalized outputs omit ID/isolation/conversion/control scalar fields; inspect real values, not dictionary presence alone"},{"ROOT_version",ROOT_RELEASE},{"CXX_standard",20},{"actual_existing_background_events",total},{"datasets",rows},{"new_ME_calls",0},{"new_integrals",0},{"new_hard_events",0},{"new_Pythia_events",0},{"new_Delphes_events",0}};
 p8::write_json(argv[4],out);std::cout<<Json{{"status",out["status"]},{"events_read",total},{"output",argv[4]}}.dump()<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<Json{{"status","BLOCKED_OBSERVABILITY_READBACK"},{"reason",e.what()}}.dump()<<'\n';return 2;}}

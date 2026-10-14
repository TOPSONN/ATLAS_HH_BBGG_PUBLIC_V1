// Read-only ZH ROOT adapter: original Phase6C selections and native tag bits.
#include "DelphesAdapter.hxx"
#include "Json.hxx"
#include "Sha256.hxx"
#include <TDataMember.h>
#include <RVersion.h>
#include <filesystem>
#include <iostream>
#include <iomanip>
#include <map>
#include <set>
using namespace atlas_hh::delphes;
using atlas_hh::quoted;
namespace fs=std::filesystem;
static_assert(__cplusplus == 202002L, "Requires C++20");
namespace {
std::string sha(const std::string& path) {
  std::ifstream in(path,std::ios::binary);require(in.good(),"cannot hash native input");
  atlas_hh::Sha256 h;std::array<char,65536>b;
  while(in.read(b.data(),b.size())||in.gcount())h.update(b.data(),in.gcount());
  require(in.eof(),"native hash read error");return h.finish();
}
std::ofstream out(const std::string& path) {
  require(!fs::exists(path),"preserve prior readback evidence");std::ofstream f(path);
  require(f.good(),"cannot create readback evidence");f<<std::setprecision(17);return f;
}
void finite_p4(const TLorentzVector& p) {
  require(std::isfinite(p.Px())&&std::isfinite(p.Py())&&std::isfinite(p.Pz())&&std::isfinite(p.E()),"nonfinite native nested p4");
}
void finite_members(TObject* object) {
  TIter it(object->IsA()->GetListOfDataMembers());
  while(auto* m=dynamic_cast<TDataMember*>(it())) {
    std::string t=m->GetTrueTypeName();
    if(m->GetOffset()<0||(t!="float"&&t!="Float_t"&&t!="double"&&t!="Double_t"))continue;
    int n=1;for(int d=0;d<m->GetArrayDim();++d){require(m->GetMaxIndex(d)>0&&m->GetMaxIndex(d)<=1000,"unbounded native member");n*=m->GetMaxIndex(d);}
    const auto* base=reinterpret_cast<const char*>(object)+m->GetOffset();
    for(int i=0;i<n;++i)require(std::isfinite((t=="float"||t=="Float_t")?reinterpret_cast<const float*>(base)[i]:reinterpret_cast<const double*>(base)[i]),"nonfinite ROOT numeric member");
  }
  if(auto* j=dynamic_cast<Jet*>(object)){finite_p4(j->Area);finite_p4(j->SoftDroppedJet);finite_p4(j->SoftDroppedSubJet1);finite_p4(j->SoftDroppedSubJet2);for(int i=0;i<5;++i){finite_p4(j->TrimmedP4[i]);finite_p4(j->PrunedP4[i]);finite_p4(j->SoftDroppedP4[i]);}}
}
void card(const std::string& path) {
  std::ifstream file(path,std::ios::binary);std::string text((std::istreambuf_iterator<char>(file)),{});
  const std::string marker="set RandomSeed ";auto pos=text.find(marker);
  require(pos!=std::string::npos&&text.find(marker,pos+marker.size())==std::string::npos,"ambiguous detector seed");
  auto begin=pos+marker.size(),end=text.find('\n',begin);require(end!=std::string::npos,"truncated detector seed");
  auto seed=text.substr(begin,end-begin);require(!seed.empty()&&seed.find_first_not_of("0123456789")==std::string::npos&&std::stol(seed)>0&&std::stol(seed)<=900000000,"invalid detector seed");
  text.replace(begin,end-begin,"610301");
  require(atlas_hh::Sha256::digest(text)=="cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47","original Delphes physics card changed");
}
struct Truth {long ordinal,index;int h,z;std::vector<int>birth,final,bottom;};
bool truth_next(std::istream& in,Truth& t) {
  std::string key;if(!(in>>key)){require(in.eof(),"truth read failure");return false;}
  int nh,nf,nb;require(key=="E"&&bool(in>>t.ordinal>>t.index>>t.h>>t.z>>nh>>nf>>nb),"invalid ZH truth row");
  require(nh==2&&nf>=0&&nf<=2&&nb==2,"invalid ZH birth/descendant counts");
  auto ids=[&](const char* tag,int n,std::vector<int>&v){require(bool(in>>key)&&key==tag,"missing truth ID row");v.clear();for(int i=0;i<n;++i){int id;require(bool(in>>id)&&id>0,"invalid truth ID");v.push_back(id);}require(std::set<int>(v.begin(),v.end()).size()==v.size(),"duplicate truth ID");};
  ids("H",nh,t.birth);ids("G",nf,t.final);ids("B",nb,t.bottom);return true;
}
struct Object {int index;double pt,eta;P4 p;unsigned tag=0;};
struct Count {long raw=0;long double sum=0,sum2=0;void add(double w){++raw;sum+=w;sum2+=(long double)w*w;}};
void derived_p4(const P4& p){require(std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z)&&std::isfinite(p.e)&&std::isfinite(p.mass()),"nonfinite derived native p4 or mass");}
void mass(std::ostream& stream,bool available,const P4& p){if(available){derived_p4(p);stream<<p.mass();}else stream<<"null";}
}
int main(int argc,char**argv) {
  long observed_entries=-1,assessed=0,read=0,processed=0,invalid=0;
  bool active_event=false;std::string summary_path;
  try {
    if(argc==2&&std::string(argv[1])=="--build-info"){
      std::cout<<"{\"profile\":\"ZH_RESONANCE_ORIGIN\",\"root_version\":"<<quoted(ROOT_RELEASE)<<",\"cpp_standard\":20,\"events_processed\":0}\n";return 0;
    }
    if(argc==2&&std::string(argv[1])=="--method-tests"){
      derived_p4(polar(40,.3,1,10));
      auto rejects=[](const P4& p){bool rejected=false;try{derived_p4(p);}catch(const std::exception&){rejected=true;}require(rejected,"derived-p4 overflow was accepted");};
      rejects(polar(25,20000,0,0));
      rejects(P4{0,0,0,std::numeric_limits<long double>::infinity()});
      std::cout<<"{\"status\":\"METHOD_ONLY\",\"checks\":3,\"events_processed\":0,\"scope\":\"finite derived p4 and overflow rejection; no ROOT input\"}\n";return 0;
    }
    std::map<std::string,std::string> options;
    for(int i=1;i<argc;i+=2){require(i+1<argc,"missing native argument");require(options.emplace(argv[i],argv[i+1]).second,"duplicate native argument");}
    if(options.count("--summary"))summary_path=options.at("--summary");
    const std::set<std::string> expected{"--input","--input-index","--truth-index","--card","--summary","--events-jsonl","--cutflow","--events"};
    std::set<std::string> keys;for(auto&[k,v]:options)keys.insert(k);require(keys==expected,"unknown/missing native arguments");
    const long count=std::stol(options.at("--events"));require(count==100,"physical ZH ROOT readback requires100 full source events");
    std::map<std::string,std::string> input_hashes;
    for(const char* key:{"--input","--input-index","--truth-index","--card"})input_hashes.emplace(key,sha(options.at(key)));
    card(options.at("--card"));Adapter adapter(options.at("--input"),&observed_entries);require(observed_entries==count,"ROOT entries differ from source100");
    InputIndex input(options.at("--input-index"));std::ifstream truth(options.at("--truth-index"));std::string magic;
    require(bool(truth>>magic)&&magic=="ATLAS_ZH_TRUTH_V1","wrong resonance truth profile");
    auto events=out(options.at("--events-jsonl"));std::map<std::string,Count> cuts;
    for(const char* stage:{"00_input","01_photons","02_jets","03_two_btags","04_mgg_105_160"})cuts.emplace(stage,Count{});
    long total_photons=0,total_jets=0,matched_h_photons=0,ambiguous_h_matches=0;
    for(long ordinal=1;ordinal<=count;++ordinal) {
      active_event=true;++assessed;
      InputEvent source;Truth lineage;require(input.next(source)&&truth_next(truth,lineage),"native input/truth truncated");
      require(source.ordinal==ordinal&&source.source_index==ordinal&&source.source_count==100&&lineage.ordinal==ordinal&&lineage.index==ordinal,"source event mapping mismatch");
      adapter.read(ordinal-1);++read;for(auto&[name,branch]:adapter.branches)if(branch.present)for(int i=0;i<branch.array->GetEntriesFast();++i)finite_members(branch.array->At(i));
      auto event=adapter.get<HepMCEvent>("Event");require(event.size()==1&&event[0]->Number==source.number&&event[0]->Weight==float(source.weights.front()),"ROOT Event/source identity or nominal weight mismatch");
      auto weights=adapter.get<Weight>("Weight");require(weights.size()==source.weights.size(),"ROOT source weight vector missing");
      for(std::size_t i=0;i<weights.size();++i)require(weights[i]->Weight==float(source.weights[i]),"ROOT named weight value mismatch");
      auto particles=adapter.get<GenParticle>("Particle");require(particles.size()==source.particles.size(),"ROOT retained source particle count mismatch");
      std::vector<ParticleTuple> actual,expected_particles;std::map<int,const InputParticle*> byid;
      for(auto&p:source.particles){require(byid.emplace(p.id,&p).second,"duplicate HepMC particle ID");expected_particles.push_back(tuple(p));}
      for(auto*p:particles){require(p->IsPU==0,"unexpected pileup");for(int relative:{p->M1,p->M2,p->D1,p->D2})require(relative>=-1&&relative<int(particles.size()),"native ancestry index out of bounds");actual.push_back(tuple(*p));}
      std::sort(actual.begin(),actual.end());std::sort(expected_particles.begin(),expected_particles.end());require(actual==expected_particles,"native float32 p4/mass/position multiset differs from actual HepMC");
      require(byid.at(lineage.h)->pid==25&&byid.at(lineage.z)->pid==23,"H/Z truth identities absent");
      for(int id:lineage.birth)require(byid.at(id)->pid==22,"H birth is not photon");
      std::set<int> bottom;for(int id:lineage.bottom)bottom.insert(byid.at(id)->pid);require(bottom==std::set<int>{-5,5},"Z bottom birth mismatch");
      std::vector<P4> truth_photons;for(int id:lineage.final){require(byid.at(id)->pid==22&&byid.at(id)->status==1,"wrong final H photon");truth_photons.push_back(byid.at(id)->p);}
      std::vector<Object> photons,jets;int index=0;
      for(auto*p:adapter.get<Photon>("Photon")){require(p->E>=0,"negative photon energy");photons.push_back({index++,p->PT,p->Eta,polar(p->PT,p->Eta,p->Phi,0),0});}
      index=0;for(auto*j:adapter.get<Jet>("Jet")){require((j->BTag&~1U)==0,"unexpected native tag bits");jets.push_back({index++,j->PT,j->Eta,polar(j->PT,j->Eta,j->Phi,j->Mass),j->BTag});}
      for(const auto& p:photons)derived_p4(p.p);
      for(const auto& j:jets)derived_p4(j.p);
      auto order=[](const Object&a,const Object&b){return a.pt>b.pt||(a.pt==b.pt&&a.index<b.index);};
      std::sort(photons.begin(),photons.end(),order);std::sort(jets.begin(),jets.end(),order);
      total_photons+=photons.size();total_jets+=jets.size();std::vector<P4> reco;
      for(auto&p:photons)reco.push_back(p.p);
      auto match=unique_match(truth_photons,reco,.2);
      matched_h_photons+=match.pairs.size();ambiguous_h_matches+=match.ambiguous_truth+match.ambiguous_reco;
      std::vector<Object> selected,eligible,tagged;
      for(auto&p:photons)if(photon_fiducial(p.pt,p.eta))selected.push_back(p);
      for(auto&j:jets)if(jet_fiducial(j.pt,j.eta)){eligible.push_back(j);if(j.tag&1)tagged.push_back(j);}
      bool photons_cut=selected.size()>=2&&selected.front().pt>35;
      bool jets_cut=photons_cut&&eligible.size()>=2,tags_cut=jets_cut&&tagged.size()>=2;
      const bool have_gg=selected.size()>=2,have_bb=tagged.size()>=2;
      P4 gg{},bb{};if(have_gg)gg=selected[0].p+selected[1].p;if(have_bb)bb=tagged[0].p+tagged[1].p;
      if(have_gg)derived_p4(gg);
      if(have_bb)derived_p4(bb);
      if(have_gg&&have_bb)derived_p4(bb+gg);
      bool mass_cut=tags_cut&&gg.mass()>=105&&gg.mass()<=160;
      cuts["00_input"].add(source.contribution);if(photons_cut)cuts["01_photons"].add(source.contribution);if(jets_cut)cuts["02_jets"].add(source.contribution);if(tags_cut)cuts["03_two_btags"].add(source.contribution);if(mass_cut)cuts["04_mgg_105_160"].add(source.contribution);
      events<<"{\"source_event_index\":"<<ordinal<<",\"source_event_sha256\":"<<quoted(source.source_hash)<<",\"hepmc_event_sha256\":"<<quoted(source.hash)<<",\"source_contribution_pb\":"<<source.contribution<<",\"selected_photons\":"<<selected.size()<<",\"eligible_jets\":"<<eligible.size()<<",\"tagged_bit0\":"<<tagged.size()<<",\"H_origin_final_truth_photons\":"<<truth_photons.size()<<",\"H_origin_reco_matches\":"<<match.pairs.size()<<",\"m_gamma_gamma\":";
      mass(events,have_gg,gg);events<<",\"m_bb\":";mass(events,have_bb,bb);events<<",\"m_bb_gamma_gamma\":";mass(events,have_bb&&have_gg,bb+gg);
      events<<",\"H_origin_reco_match_pairs\":[";bool first_match=true;
      for(const auto& pair:match.pairs){if(!first_match)events<<',';first_match=false;events<<"{\"truth_H_photon_id\":"<<lineage.final.at(pair.truth)<<",\"native_Photon_index\":"<<photons.at(pair.reco).index<<",\"delta_R\":"<<pair.distance<<'}';}
      events<<']';
      events<<",\"cut_photons\":"<<(photons_cut?"true":"false")<<",\"cut_jets\":"<<(jets_cut?"true":"false")<<",\"cut_two_btags\":"<<(tags_cut?"true":"false")<<",\"cut_mgg\":"<<(mass_cut?"true":"false")<<"}\n";
      require(events.good(),"native event receipt write failure");
      ++processed;active_event=false;
    }
    InputEvent extra;Truth extra_truth;require(!input.next(extra)&&!truth_next(truth,extra_truth),"extra source/truth rows");
    events.close();auto csv=out(options.at("--cutflow"));csv<<"stage,raw_events,source_weight_sum_pb,source_weight_sum_squared_pb2\n";
    for(auto&[stage,value]:cuts)csv<<stage<<','<<value.raw<<','<<value.sum<<','<<value.sum2<<'\n';
    csv.close();
    for(auto&[key,value]:input_hashes)require(sha(options.at(key))==value,"ROOT/source index/truth/card changed during native readback");
    auto summary=out(options.at("--summary"));summary<<"{\"schema_version\":1,\"status\":\"PASS_NATIVE_ZH_RECORD_READBACK\",\"profile\":\"H_DECAY_PHOTONS_Z_DECAY_BOTTOMS\",\"ROOT_entries\":"<<observed_entries<<",\"source_events\":100,\"events_assessed\":"<<assessed<<",\"read\":"<<read<<",\"processed\":"<<processed<<",\"invalid\":0,\"skipped\":0,\"events_not_assessed\":0,\"root_version\":"<<quoted(ROOT_RELEASE)<<",\"root_sha256\":"<<quoted(input_hashes.at("--input"))<<",\"input_index_sha256\":"<<quoted(input_hashes.at("--input-index"))<<",\"truth_index_sha256\":"<<quoted(input_hashes.at("--truth-index"))<<",\"card_sha256\":"<<quoted(input_hashes.at("--card"))<<",\"reco_photons\":"<<total_photons<<",\"reco_jets\":"<<total_jets<<",\"H_photon_reco_matches\":"<<matched_h_photons<<",\"ambiguous_H_match_edges\":"<<ambiguous_h_matches<<",\"exclusive_physical_normalization\":\"BLOCKED_NO_ADOPTED_PHYSICAL_BR\",\"ancestry_scope\":\"inherited from exact bound upstream ReaderAscii graph; native particle tuples verified\",\"selected_pair_scope\":\"inclusive Phase6C leading selected pair; H-origin matches are separate diagnostics\",\"btag_model\":\"FAST_SIM_ATLAS_LIKE_BIT0_NOT_OFFICIAL_ATLAS\"}\n";
    require(summary.good(),"summary write failure");return 0;
  } catch(const std::exception& error){
    if(active_event)++invalid;
    if(!summary_path.empty()&&!fs::exists(summary_path)){
      std::ofstream report(summary_path);if(report.good())report<<"{\"schema_version\":1,\"status\":\"FAILED_NATIVE_ZH_RECORD_READBACK\",\"expected_events\":100,\"ROOT_entries\":"<<(observed_entries<0?"null":std::to_string(observed_entries))<<",\"events_assessed\":"<<assessed<<",\"read\":"<<read<<",\"processed\":"<<processed<<",\"invalid\":"<<invalid<<",\"events_not_assessed\":"<<(observed_entries<0?"null":std::to_string(std::max(0L,observed_entries-assessed)))<<",\"diagnostic\":"<<quoted(error.what())<<",\"physical_pilot_acceptance\":false}\n";
    }
    std::cerr<<"FAILED_NATIVE_ZH_VALIDATION: "<<error.what()<<'\n';return 2;
  }
}

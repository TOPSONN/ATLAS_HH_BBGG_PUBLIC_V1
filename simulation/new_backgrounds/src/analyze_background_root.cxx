// Read-only native B04/B05/B06 ROOT adapter. Original Phase6C cuts and tag bits.
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
struct Truth {long ordinal,index;int h,z,t,tbar,wp,wm;std::vector<int>birth,final,bottom,born,shower,hadron,other;};
bool truth_next(std::istream& in,Truth& t) {
  std::string key;if(!(in>>key)){require(in.eof(),"truth read failure");return false;}
  require(key=="E"&&bool(in>>t.ordinal>>t.index>>t.h>>t.z>>t.t>>t.tbar>>t.wp>>t.wm),"invalid background truth row");
  auto ids=[&](const char* tag,std::vector<int>&v){int n;require(bool(in>>key>>n)&&key==tag&&n>=0&&n<=100000,"missing/bounded truth ID row");v.clear();for(int i=0;i<n;++i){int id;require(bool(in>>id)&&id>0,"invalid truth ID");v.push_back(id);}require(std::set<int>(v.begin(),v.end()).size()==v.size(),"duplicate truth ID");};
  ids("H",t.birth);ids("G",t.final);ids("B",t.bottom);ids("O",t.born);ids("S",t.shower);ids("D",t.hadron);ids("X",t.other);return true;
}
struct Object {int index;double pt,eta;P4 p;unsigned tag=0;};
struct Count {long raw=0;long double sum=0,sum2=0;void add(double w){++raw;sum+=w;sum2+=(long double)w*w;}};
void finite_cartesian(const P4& p){require(std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z)&&std::isfinite(p.e),"nonfinite derived native p4");}
void derived_p4(const P4& p){finite_cartesian(p);require(std::isfinite(p.mass()),"nonfinite derived native mass");}
void mass(std::ostream& stream,bool available,const P4& p){if(available){derived_p4(p);stream<<p.mass();}else stream<<"null";}
void pt(std::ostream& stream,const std::vector<Object>& objects,int index){if(int(objects.size())>index)stream<<objects[index].pt;else stream<<"null";}
void delta_r(std::ostream& stream,bool available,const P4& a,const P4& b){if(available){auto value=dr(a,b);require(std::isfinite(value),"nonfinite derived DeltaR");stream<<value;}else stream<<"null";}
std::vector<P4> final_photons(const std::vector<int>& ids,const std::map<int,const InputParticle*>& byid){std::vector<P4> result;for(int id:ids){const auto* p=byid.at(id);require(p->pid==22&&p->status==1,"wrong final truth photon");result.push_back(p->p);}return result;}
void matches(std::ostream& stream,const std::vector<int>& ids,const std::vector<Object>& photons,const Match& match){stream<<'[';bool first=true;for(const auto& pair:match.pairs){if(!first)stream<<',';first=false;stream<<"{\"truth_photon_id\":"<<ids.at(pair.truth)<<",\"native_Photon_index\":"<<photons.at(pair.reco).index<<",\"delta_R\":"<<pair.distance<<'}';}stream<<']';}
}
int main(int argc,char**argv) {
  long observed_entries=-1,assessed=0,read=0,processed=0,invalid=0;
  long count=0;bool active_event=false;std::string summary_path;
  try {
    if(argc==2&&std::string(argv[1])=="--build-info"){
      std::cout<<"{\"profile\":\"B04_B05_B06_NATIVE_SOURCE_CORRESPONDENCE\",\"root_version\":"<<quoted(ROOT_RELEASE)<<",\"cpp_standard\":20,\"events_processed\":0}\n";return 0;
    }
    if(argc==2&&std::string(argv[1])=="--method-tests"){
      derived_p4(polar(40,.3,1,10));
      auto rejects=[](const P4& p){bool rejected=false;try{derived_p4(p);}catch(const std::exception&){rejected=true;}require(rejected,"derived-p4 overflow was accepted");};
      rejects(polar(25,20000,0,0));
      rejects(P4{0,0,0,std::numeric_limits<long double>::infinity()});
      // Actual retained prefix100 event14 Jet0: signed ROOT mass is within the
      // historical polar() double-cancellation bound. Preserve its exact p4.
      const auto tiny_signed_jet=polar(108.878387451171875,.1113665848970413208,2.0700531005859375,-1.348699129266606178e-6);
      finite_cartesian(tiny_signed_jet);
      bool negative_rejected=false;try{auto p=polar(100,.1,2,-1);(void)p;}catch(const std::exception&){negative_rejected=true;}
      require(negative_rejected,"materially negative native jet mass was accepted");
      rejects(P4{1,0,0,0}+P4{1,0,0,0});
      std::cout<<"{\"status\":\"METHOD_ONLY\",\"checks\":6,\"events_processed\":0,\"scope\":\"finite derived p4, overflow rejection, actual bounded signed native jet, material negative input and spacelike summed-vector rejection; no ROOT input\"}\n";return 0;
    }
    std::map<std::string,std::string> options;
    for(int i=1;i<argc;i+=2){require(i+1<argc,"missing native argument");require(options.emplace(argv[i],argv[i+1]).second,"duplicate native argument");}
    if(options.count("--summary"))summary_path=options.at("--summary");
    const std::set<std::string> expected{"--input","--input-index","--truth-index","--card","--summary","--events-jsonl","--cutflow","--events","--source-events","--process"};
    std::set<std::string> keys;for(auto&[k,v]:options)keys.insert(k);require(keys==expected,"unknown/missing native arguments");
    count=std::stol(options.at("--events"));require(count==10||count==100||count==1000,"background ROOT readback requires10/100/1000 existing source subset");
    const long full_count=std::stol(options.at("--source-events"));require(full_count==1000,"original source denominator must be1000");
    const auto process=options.at("--process");require(process=="zh"||process=="tth"||process=="bbgj","unknown native process");
    std::map<std::string,std::string> input_hashes;
    for(const char* key:{"--input","--input-index","--truth-index","--card"})input_hashes.emplace(key,sha(options.at(key)));
    card(options.at("--card"));Adapter adapter(options.at("--input"),&observed_entries);require(observed_entries==count,"ROOT entries differ from exact input subset");
    InputIndex input(options.at("--input-index"));std::ifstream truth(options.at("--truth-index"));std::string magic;
    require(bool(truth>>magic)&&magic=="ATLAS_NEW_BACKGROUND_TRUTH_V1","wrong background truth profile");
    auto events=out(options.at("--events-jsonl"));std::map<std::string,Count> cuts;
    for(const char* stage:{"00_input","01_photons","02_jets","03_two_btags","04_mgg_105_160"})cuts.emplace(stage,Count{});
    if(process=="bbgj")for(const char* stage:{"control_00_input","control_01_one_photon","control_02_jets","control_03_two_btags"})cuts.emplace(stage,Count{});
    long total_photons=0,total_jets=0,matched_h_photons=0,ambiguous_h_matches=0;
    for(long ordinal=1;ordinal<=count;++ordinal) {
      active_event=true;++assessed;
      InputEvent source;Truth lineage;require(input.next(source)&&truth_next(truth,lineage),"native input/truth truncated");
      require(source.ordinal==ordinal&&source.source_index==ordinal&&source.source_count==full_count&&lineage.ordinal==ordinal&&lineage.index==ordinal,"source event mapping mismatch");
      adapter.read(ordinal-1);++read;for(auto&[name,branch]:adapter.branches)if(branch.present)for(int i=0;i<branch.array->GetEntriesFast();++i)finite_members(branch.array->At(i));
      auto event=adapter.get<HepMCEvent>("Event");require(event.size()==1&&event[0]->Number==source.number&&event[0]->Weight==float(source.weights.front()),"ROOT Event/source identity or nominal weight mismatch");
      auto weights=adapter.get<Weight>("Weight");require(weights.size()==source.weights.size(),"ROOT source weight vector missing");
      for(std::size_t i=0;i<weights.size();++i)require(weights[i]->Weight==float(source.weights[i]),"ROOT named weight value mismatch");
      auto particles=adapter.get<GenParticle>("Particle");require(particles.size()==source.particles.size(),"ROOT retained source particle count mismatch");
      std::vector<ParticleTuple> actual,expected_particles;std::map<int,const InputParticle*> byid;
      for(auto&p:source.particles){require(byid.emplace(p.id,&p).second,"duplicate HepMC particle ID");expected_particles.push_back(tuple(p));}
      for(auto*p:particles){require(p->IsPU==0,"unexpected pileup");for(int relative:{p->M1,p->M2,p->D1,p->D2})require(relative>=-1&&relative<int(particles.size()),"native ancestry index out of bounds");actual.push_back(tuple(*p));}
      std::sort(actual.begin(),actual.end());std::sort(expected_particles.begin(),expected_particles.end());require(actual==expected_particles,"native float32 p4/mass/position multiset differs from actual HepMC");
      if(process=="bbgj")require(lineage.h==0&&lineage.z==0&&lineage.t==0&&lineage.tbar==0&&lineage.wp==0&&lineage.wm==0&&lineage.birth.empty()&&lineage.final.empty(),"B06 must not invent H/Z/top lineage");
      else {require(byid.at(lineage.h)->pid==25&&lineage.birth.size()==2&&lineage.final.size()<=2,"actual H truth identities absent");for(int id:lineage.birth)require(byid.at(id)->pid==22,"H birth is not photon");}
      if(process=="zh")require(byid.at(lineage.z)->pid==23&&lineage.t==0&&lineage.tbar==0&&lineage.wp==0&&lineage.wm==0,"B04 Z lineage mismatch");
      if(process=="tth")require(lineage.z==0&&byid.at(lineage.t)->pid==6&&byid.at(lineage.tbar)->pid==-6&&byid.at(lineage.wp)->pid==24&&byid.at(lineage.wm)->pid==-24,"B05 top/W lineage mismatch");
      std::set<int> bottom;for(int id:lineage.bottom){const auto pid=byid.at(id)->pid;require(std::abs(pid)==5&&bottom.insert(pid).second,"invalid or duplicate bottom birth");}
      if(process=="tth")require(lineage.bottom.size()<=2,"inclusive top decay has excessive bottom births");
      else require(lineage.bottom.size()==2&&bottom==std::set<int>{-5,5},"hard bottom birth mismatch");
      std::set<int> all_photon_ids,categorized;
      for(auto&[id,p]:byid)if(p->pid==22&&p->status==1)all_photon_ids.insert(id);
      for(const auto* ids:{&lineage.born,&lineage.shower,&lineage.hadron,&lineage.other})for(int id:*ids){require(byid.at(id)->pid==22&&byid.at(id)->status==1&&categorized.insert(id).second,"invalid/overlapping stable photon origin category");}
      require(categorized==all_photon_ids,"stable photon origin categories do not cover full source event");
      const auto truth_photons=final_photons(lineage.final,byid);
      std::vector<Object> photons,jets;int index=0;
      for(auto*p:adapter.get<Photon>("Photon")){require(p->E>=0,"negative photon energy");photons.push_back({index++,p->PT,p->Eta,polar(p->PT,p->Eta,p->Phi,0),0});}
      index=0;for(auto*j:adapter.get<Jet>("Jet")){require((j->BTag&~1U)==0,"unexpected native tag bits");jets.push_back({index++,j->PT,j->Eta,polar(j->PT,j->Eta,j->Phi,j->Mass),j->BTag});}
      for(const auto& p:photons)derived_p4(p.p);
      // polar() already validates signed native Mass with the historical
      // double-cancellation bound. Strict mass() applies to summed vectors.
      for(const auto& j:jets)finite_cartesian(j.p);
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
      const bool have_gg=selected.size()>=2,have_bb=tagged.size()>=2,have_jj=eligible.size()>=2;
      P4 gg{},bb{},jj{};if(have_gg)gg=selected[0].p+selected[1].p;if(have_bb)bb=tagged[0].p+tagged[1].p;if(have_jj)jj=eligible[0].p+eligible[1].p;
      if(have_gg)derived_p4(gg);
      if(have_bb)derived_p4(bb);
      if(have_jj)derived_p4(jj);
      if(have_gg&&have_bb)derived_p4(bb+gg);
      bool mass_cut=tags_cut&&gg.mass()>=105&&gg.mass()<=160;
      cuts["00_input"].add(source.contribution);if(photons_cut)cuts["01_photons"].add(source.contribution);if(jets_cut)cuts["02_jets"].add(source.contribution);if(tags_cut)cuts["03_two_btags"].add(source.contribution);if(mass_cut)cuts["04_mgg_105_160"].add(source.contribution);
      const bool one_photon_cut=!selected.empty()&&selected.front().pt>35;
      if(process=="bbgj"){cuts["control_00_input"].add(source.contribution);if(one_photon_cut)cuts["control_01_one_photon"].add(source.contribution);if(one_photon_cut&&have_jj)cuts["control_02_jets"].add(source.contribution);if(one_photon_cut&&have_jj&&have_bb)cuts["control_03_two_btags"].add(source.contribution);}
      events<<"{\"process\":"<<quoted(process)<<",\"source_event_index\":"<<ordinal<<",\"source_event_sha256\":"<<quoted(source.source_hash)<<",\"hepmc_event_sha256\":"<<quoted(source.hash)<<",\"original_source_events\":1000,\"raw_LHE_XWGTUP_pb\":"<<source.raw<<",\"source_contribution_pb\":"<<source.contribution<<",\"photon_multiplicity\":"<<photons.size()<<",\"jet_multiplicity\":"<<jets.size()<<",\"selected_photons\":"<<selected.size()<<",\"eligible_jets\":"<<eligible.size()<<",\"tagged_bit0\":"<<tagged.size()<<",\"H_origin_final_truth_photons\":"<<truth_photons.size()<<",\"H_origin_reco_matches\":"<<match.pairs.size();
      events<<",\"pT_gamma1\":";pt(events,photons,0);events<<",\"pT_gamma2\":";pt(events,photons,1);events<<",\"pT_jet1\":";pt(events,jets,0);events<<",\"pT_jet2\":";pt(events,jets,1);
      events<<",\"pT_selected_gamma1\":";pt(events,selected,0);events<<",\"pT_selected_gamma2\":";pt(events,selected,1);
      events<<",\"m_gamma_gamma\":";mass(events,have_gg,gg);events<<",\"m_jj\":";mass(events,have_jj,jj);events<<",\"m_bb\":";mass(events,have_bb,bb);events<<",\"m_bb_gamma_gamma\":";mass(events,have_bb&&have_gg,bb+gg);
      events<<",\"DeltaR_gamma_gamma\":";delta_r(events,have_gg,have_gg?selected[0].p:P4{},have_gg?selected[1].p:P4{});
      events<<",\"DeltaR_bb\":";delta_r(events,have_bb,have_bb?tagged[0].p:P4{},have_bb?tagged[1].p:P4{});
      events<<",\"H_origin_reco_match_pairs\":";matches(events,lineage.final,photons,match);
      events<<",\"stable_photon_origin_counts\":{\"born_prompt\":"<<lineage.born.size()<<",\"shower_radiation\":"<<lineage.shower.size()<<",\"hadron_decay\":"<<lineage.hadron.size()<<",\"other\":"<<lineage.other.size()<<"},\"photon_origin_geometric_matches\":{";
      bool first_origin=true;for(const auto&[name,ids]:std::vector<std::pair<std::string,const std::vector<int>*>>{{"born_prompt",&lineage.born},{"shower_radiation",&lineage.shower},{"hadron_decay",&lineage.hadron},{"other",&lineage.other}}){if(!first_origin)events<<',';first_origin=false;events<<quoted(name)<<':';matches(events,*ids,photons,unique_match(final_photons(*ids,byid),reco,.2));}events<<'}';
      events<<",\"cut_photons\":"<<(photons_cut?"true":"false")<<",\"cut_jets\":"<<(jets_cut?"true":"false")<<",\"cut_two_btags\":"<<(tags_cut?"true":"false")<<",\"cut_mgg\":"<<(mass_cut?"true":"false")<<",\"control_cut_one_photon\":"<<(one_photon_cut?"true":"false")<<",\"control_cut_jets\":"<<(one_photon_cut&&have_jj?"true":"false")<<",\"control_cut_two_btags\":"<<(one_photon_cut&&have_jj&&have_bb?"true":"false")<<"}\n";
      require(events.good(),"native event receipt write failure");
      ++processed;active_event=false;
    }
    InputEvent extra;Truth extra_truth;require(!input.next(extra)&&!truth_next(truth,extra_truth),"extra source/truth rows");
    events.close();auto csv=out(options.at("--cutflow"));csv<<"stage,raw_events,source_weight_sum_pb,source_weight_sum_squared_pb2\n";
    for(auto&[stage,value]:cuts)csv<<stage<<','<<value.raw<<','<<value.sum<<','<<value.sum2<<'\n';
    csv.close();
    for(auto&[key,value]:input_hashes)require(sha(options.at(key))==value,"ROOT/source index/truth/card changed during native readback");
    auto summary=out(options.at("--summary"));summary<<"{\"schema_version\":1,\"status\":\"PASS_NATIVE_BACKGROUND_RECORD_READBACK\",\"process\":"<<quoted(process)<<",\"profile\":\"ACTUAL_SOURCE_GRAPH_AND_NATIVE_RECO\",\"ROOT_entries\":"<<observed_entries<<",\"source_events\":1000,\"subset_events\":"<<count<<",\"events_assessed\":"<<assessed<<",\"read\":"<<read<<",\"processed\":"<<processed<<",\"invalid\":0,\"skipped\":0,\"events_not_assessed\":0,\"root_version\":"<<quoted(ROOT_RELEASE)<<",\"root_sha256\":"<<quoted(input_hashes.at("--input"))<<",\"input_index_sha256\":"<<quoted(input_hashes.at("--input-index"))<<",\"truth_index_sha256\":"<<quoted(input_hashes.at("--truth-index"))<<",\"card_sha256\":"<<quoted(input_hashes.at("--card"))<<",\"reco_photons\":"<<total_photons<<",\"reco_jets\":"<<total_jets<<",\"H_photon_reco_matches\":"<<matched_h_photons<<",\"ambiguous_H_match_edges\":"<<ambiguous_h_matches<<",\"normalization_scope\":\"RAW_SOURCE_CONTRIBUTION_ONLY; BR_MODEL_ADJUSTMENT_SEPARATE\",\"ancestry_scope\":\"exact bound upstream ReaderAscii graph and actual truth IDs; native particle tuples verified\",\"selected_pair_scope\":\"inclusive Phase6C leading eligible pair for masses/DeltaR; leading all-reco objects for pT; H-origin/origin matches separate diagnostics\",\"photon_match_scope\":\"category matches independent geometric diagnostics; not calibrated photon efficiency or jet fake rate\",\"btag_model\":\"FAST_SIM_ATLAS_LIKE_BIT0_NOT_OFFICIAL_ATLAS\",\"schema\":[";
    bool first_schema=true;for(const auto&[name,branch]:adapter.branches){if(!first_schema)summary<<',';first_schema=false;summary<<"{\"branch\":"<<quoted(name)<<",\"present\":"<<(branch.present?"true":"false")<<",\"clone_class\":"<<quoted(branch.clone)<<",\"dictionary_version\":"<<branch.version<<",\"dictionary_checksum\":"<<branch.checksum<<'}';}summary<<"]}\n";
    require(summary.good(),"summary write failure");return 0;
  } catch(const std::exception& error){
    if(active_event)++invalid;
    if(!summary_path.empty()&&!fs::exists(summary_path)){
      std::ofstream report(summary_path);if(report.good())report<<"{\"schema_version\":1,\"status\":\"FAILED_NATIVE_BACKGROUND_RECORD_READBACK\",\"expected_events\":"<<count<<",\"ROOT_entries\":"<<(observed_entries<0?"null":std::to_string(observed_entries))<<",\"events_assessed\":"<<assessed<<",\"read\":"<<read<<",\"processed\":"<<processed<<",\"invalid\":"<<invalid<<",\"events_not_assessed\":"<<(observed_entries<0?"null":std::to_string(std::max(0L,observed_entries-assessed)))<<",\"diagnostic\":"<<quoted(error.what())<<",\"physical_pilot_acceptance\":false}\n";
    }
    std::cerr<<"FAILED_NATIVE_BACKGROUND_VALIDATION: "<<error.what()<<'\n';return 2;
  }
}

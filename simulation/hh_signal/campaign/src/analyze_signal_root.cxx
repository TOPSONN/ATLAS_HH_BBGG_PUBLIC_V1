// Reuse the exact historical native schema, finite-member and selection helpers.
// The old main is never called; no historical source is modified.
#define main retained_phase6g_background_main
#include "../../../new_backgrounds/src/analyze_background_root.cxx"
#undef main

struct SignalTruth {long index;std::string hash;int bb,gg;std::vector<int>photons,bottoms;};
bool signal_truth_next(std::istream&in,SignalTruth&t){
 std::string key;if(!(in>>key))return false;
 require(key=="E"&&bool(in>>t.index>>t.hash>>t.bb>>t.gg)&&t.bb!=t.gg,"invalid signal lineage row");
 auto read=[&](const char*tag,std::vector<int>&ids){int n;require(bool(in>>key>>n)&&key==tag&&n==2,"invalid signal daughter count");ids.clear();for(int i=0;i<n;++i){int id;require(bool(in>>id)&&id>0,"invalid truth daughter");ids.push_back(id);}require(ids[0]!=ids[1],"duplicate signal daughter");};
 read("G",t.photons);read("B",t.bottoms);return true;
}
int main(int argc,char**argv){
 long processed=0;
 try{
  require(argc==9,"input ROOT/index/truth/card/output/count/original-count/authorization required");
  const std::string input=argv[1],indexpath=argv[2],truthpath=argv[3],cardpath=argv[4],folder=argv[5];
  const int count=std::stoi(argv[6]),total=std::stoi(argv[7]);
  require((total==100||total==1000)&&(count==10||count==100||count==1000)&&count<=total,"unapproved signal ROOT count");
  // The authority file is supplied by the outer live campaign controller.
  std::ifstream authority(argv[8]);require(authority.good(),"missing native campaign authority");
  require(!fs::exists(folder),"preserve previous native signal readback");fs::create_directory(folder);
  card(cardpath);long entries=-1;Adapter adapter(input,&entries);require(entries==count,"actual signal ROOT entry count mismatch");
  InputIndex source(indexpath);std::ifstream truth(truthpath);std::string magic;require(bool(truth>>magic)&&magic=="S01_SIGNAL_TRUTH_V1","bad signal truth magic");
  auto events=out(folder+"/reco_events.jsonl");
  std::map<std::string,Count> cuts;for(const char*name:{"00_input","01_photons","02_jets","03_two_btags","04_mgg_105_160"})cuts.emplace(name,Count{});
  for(int ordinal=1;ordinal<=count;++ordinal){
   InputEvent s;SignalTruth h;require(source.next(s)&&signal_truth_next(truth,h),"truncated signal source/truth");
   require(s.ordinal==ordinal&&s.source_index==ordinal&&s.source_count==total&&h.index==ordinal&&s.source_hash==h.hash,"signal source bijection failure");
   adapter.read(ordinal-1);for(auto&[name,b]:adapter.branches)if(b.present)for(int i=0;i<b.array->GetEntriesFast();++i)finite_members(b.array->At(i));
   auto event=adapter.get<HepMCEvent>("Event");require(event.size()==1&&event[0]->Number==s.number&&event[0]->Weight==float(s.weights[0]),"native Event source/weight failure");
   std::vector<ParticleTuple>actual,expected;std::map<int,const InputParticle*>byid;
   for(auto*p:adapter.get<GenParticle>("Particle")){require(p->IsPU==0,"unexpected pileup");actual.push_back(tuple(*p));}
   for(const auto&p:s.particles){require(byid.emplace(p.id,&p).second,"duplicate source particle");expected.push_back(tuple(p));}
   std::sort(actual.begin(),actual.end());std::sort(expected.begin(),expected.end());require(actual==expected,"native signal particle p4/mass/position multiset mismatch");
   require(byid.at(h.bb)->pid==25&&byid.at(h.gg)->pid==25,"lost two Higgs lineages");
   std::vector<Object>photons,jets,selected,eligible,tagged;
   int n=0;for(auto*p:adapter.get<Photon>("Photon")){auto v=polar(p->PT,p->Eta,p->Phi,0);derived_p4(v);photons.push_back({n++,p->PT,p->Eta,v,0});}
   n=0;for(auto*j:adapter.get<Jet>("Jet")){auto v=polar(j->PT,j->Eta,j->Phi,j->Mass);finite_cartesian(v);jets.push_back({n++,j->PT,j->Eta,v,j->BTag});}
   auto order=[](const Object&a,const Object&b){return a.pt>b.pt;};std::stable_sort(photons.begin(),photons.end(),order);std::stable_sort(jets.begin(),jets.end(),order);
   for(const auto&p:photons)if(photon_fiducial(p.pt,p.eta))selected.push_back(p);
   for(const auto&j:jets)if(jet_fiducial(j.pt,j.eta)){eligible.push_back(j);if(j.tag&1U)tagged.push_back(j);}
   const bool havegg=selected.size()>=2,havejj=eligible.size()>=2,havebb=tagged.size()>=2;
   P4 gg{},jj{},bb{};if(havegg)gg=selected[0].p+selected[1].p;if(havejj)jj=eligible[0].p+eligible[1].p;if(havebb)bb=tagged[0].p+tagged[1].p;
   const bool cp=havegg&&selected[0].pt>35,cj=cp&&havejj,ct=cj&&havebb,cm=ct&&gg.mass()>=105&&gg.mass()<=160;
   cuts["00_input"].add(s.contribution);if(cp)cuts["01_photons"].add(s.contribution);if(cj)cuts["02_jets"].add(s.contribution);if(ct)cuts["03_two_btags"].add(s.contribution);if(cm)cuts["04_mgg_105_160"].add(s.contribution);
   std::vector<P4>truthgamma=final_photons(h.photons,byid),recogamma;for(auto&p:photons)recogamma.push_back(p.p);
   auto match=unique_match(truthgamma,recogamma,.2);
   std::vector<P4>truthb,recojets;for(int id:h.bottoms){require(std::abs(byid.at(id)->pid)==5,"wrong Hbb birth");truthb.push_back(byid.at(id)->p);}for(auto&j:eligible)recojets.push_back(j.p);
   auto bmatch=unique_match(truthb,recojets,.4);
   events<<"{\"process\":\"ggf_hh_sm\",\"source_event_index\":"<<ordinal<<",\"source_event_sha256\":"<<quoted(s.source_hash)<<",\"hepmc_event_sha256\":"<<quoted(s.hash)<<",\"original_source_events\":"<<total<<",\"raw_LHE_XWGTUP_pb\":"<<s.raw<<",\"source_contribution_pb\":"<<s.contribution;
   events<<",\"photon_multiplicity\":"<<photons.size()<<",\"jet_multiplicity\":"<<jets.size()<<",\"selected_photons\":"<<selected.size()<<",\"eligible_jets\":"<<eligible.size()<<",\"tagged_bit0\":"<<tagged.size()<<",\"H_origin_reco_matches\":"<<match.pairs.size()<<",\"H_bottom_geometric_jet_matches\":"<<bmatch.pairs.size();
   events<<",\"pT_gamma1\":";pt(events,photons,0);events<<",\"pT_gamma2\":";pt(events,photons,1);events<<",\"pT_jet1\":";pt(events,jets,0);events<<",\"pT_jet2\":";pt(events,jets,1);
   events<<",\"m_gamma_gamma\":";mass(events,havegg,gg);events<<",\"m_bb\":";mass(events,havebb,bb);events<<",\"m_jj\":";mass(events,havejj,jj);events<<",\"m_bb_gamma_gamma\":";mass(events,havebb&&havegg,bb+gg);
   events<<",\"pT_gamma_gamma\":"<<(havegg?std::to_string(gg.pt()):"null")<<",\"pT_bb\":"<<(havebb?std::to_string(bb.pt()):"null");
   events<<",\"DeltaR_gamma_gamma\":";delta_r(events,havegg,havegg?selected[0].p:P4{},havegg?selected[1].p:P4{});events<<",\"DeltaR_bb\":";delta_r(events,havebb,havebb?tagged[0].p:P4{},havebb?tagged[1].p:P4{});
   events<<",\"cut_photons\":"<<(cp?"true":"false")<<",\"cut_jets\":"<<(cj?"true":"false")<<",\"cut_two_btags\":"<<(ct?"true":"false")<<",\"cut_mgg\":"<<(cm?"true":"false")<<"}\n";
   require(events.good(),"native signal output write failure");++processed;
  }
  InputEvent extra;SignalTruth hx;require(!source.next(extra)&&!signal_truth_next(truth,hx),"extra input records");events.close();auto csv=out(folder+"/cutflow.csv");csv<<"stage,raw_events,source_weight_sum_pb,source_weight_sum_squared_pb2\n";
  for(auto&[name,c]:cuts)csv<<name<<','<<c.raw<<','<<c.sum<<','<<c.sum2<<'\n';csv.close();
  auto summary=out(folder+"/native_validation.json");summary<<"{\"status\":\"PASS_NATIVE_SIGNAL_ROOT_READBACK\",\"ROOT_version\":"<<quoted(ROOT_RELEASE)<<",\"CXX_standard\":20,\"entries\":"<<entries<<",\"validated\":"<<processed<<",\"original_source_count\":"<<total<<",\"invalid\":0,\"skipped\":0,\"ROOT_sha256\":"<<quoted(sha(input))<<",\"input_index_sha256\":"<<quoted(sha(indexpath))<<",\"truth_index_sha256\":"<<quoted(sha(truthpath))<<",\"card_sha256\":"<<quoted(sha(cardpath))<<",\"reco_sha256\":"<<quoted(sha(folder+"/reco_events.jsonl"))<<",\"selection\":\"UNCHANGED_PHASE6C\",\"detector_scope\":\"FAST_SIM_ATLAS_LIKE_NOT_OFFICIAL_ATLAS\",\"missing_pair_values\":null}\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<"SIGNAL_NATIVE_ROOT_FAILED after "<<processed<<": "<<e.what()<<'\n';return 2;}
}

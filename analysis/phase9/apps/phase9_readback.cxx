#include "Phase8Reader.hxx"
#include "Phase8Selection.hxx"
#include "Phase8Reconstruction.hxx"
#include <RVersion.h>
#include <algorithm>
#include <iostream>
#include <set>
namespace p8=atlas_hh::phase8;
namespace dp=atlas_hh::delphes;
using Json=p8::Json;
int main(int argc,char**argv){
 try{
  p8::demand(argc==5&&std::string(argv[1])=="--manifest"&&std::string(argv[3])=="--output","usage: phase9_readback --manifest EXISTING_MANIFEST --output FRESH_DIRECTORY");
  auto manifest=p8::read_json(argv[2]);auto all=p8::datasets(manifest);std::vector<p8::Dataset> data;
  for(const auto& d:all)if(d.id.size()==3&&d.id[0]=='B')data.push_back(d);
  p8::demand(data.size()==6,"complete six-background manifest required");for(const auto&d:data){p8::demand(d.full&&d.entries==1000,"full original background cohort required");p8::verify_dataset_files(d);}
  const std::filesystem::path output=argv[4];p8::fresh_directory(output);auto events=p8::exclusive_text(output/"phase9_native_events.jsonl");Json summaries=Json::array();long total=0;
  for(const auto&d:data){
   long count=-1;dp::Adapter a(d.root.string(),&count);p8::demand(count==d.entries,"native ROOT entry count changed");dp::InputIndex index(d.index.string());std::set<long> native_numbers;std::array<long,5> cuts{};atlas_hh::Sha256 identity;long particles_seen=0,electrons_seen=0,photons_seen=0;
   for(long ordinal=1;ordinal<=count;++ordinal){
    dp::InputEvent source;p8::demand(index.next(source),"missing source index event");p8::demand(source.ordinal==ordinal&&source.source_index==ordinal&&source.source_count==d.original,"source identity/denominator mismatch");a.read(ordinal-1);
    auto ev=a.get<HepMCEvent>("Event");p8::demand(ev.size()==1&&ev[0]->Number==source.number&&native_numbers.insert(source.number).second,"duplicate or mismatched native event number");p8::demand(ev[0]->Weight==float(source.contribution),"native nominal weight differs from exact bound source");auto weights=a.get<Weight>("Weight");p8::demand(weights.size()==source.weights.size(),"native weight vector size mismatch");for(std::size_t i=0;i<weights.size();++i)p8::demand(weights[i]->Weight==float(source.weights[i]),"native named weight mismatch");
    auto particles=a.get<GenParticle>("Particle");p8::demand(particles.size()==source.particles.size(),"native particle count mismatch");std::vector<dp::ParticleTuple> expected,actual;std::set<int> upstream_ids;
    for(const auto& p:source.particles){p8::demand(upstream_ids.insert(p.id).second,"duplicate upstream particle identity");expected.push_back(dp::tuple(p));}
    for(auto*p:particles){p8::demand(p->IsPU==0,"unexpected pileup source");for(int relative:{p->M1,p->M2,p->D1,p->D2})p8::demand(relative>=-1&&relative<int(particles.size()),"native ancestry index out of bounds");actual.push_back(dp::tuple(*p));}
    std::sort(expected.begin(),expected.end());std::sort(actual.begin(),actual.end());p8::demand(expected==actual,"native/source particle tuple multiset mismatch");particles_seen+=particles.size();
    p8::Event e;e.dataset=d.id;e.ordinal=ordinal;e.native_number=source.number;e.original=d.original;e.source_hash=source.source_hash;e.hepmc_hash=source.hash;e.weight=source.contribution;e.raw_weight=source.raw;e.weight_scope=d.scope;
    int pos=0;for(auto*p:a.get<Photon>("Photon")){p8::demand(std::isfinite(p->PT)&&p->PT>=0&&std::isfinite(p->Eta)&&std::isfinite(p->Phi)&&std::isfinite(p->E)&&p->E>=0,"nonfinite native photon");auto v=dp::polar(p->PT,p->Eta,p->Phi,0);p8::demand(std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z)&&std::isfinite(v.e),"nonfinite photon Cartesian P4");e.photons.push_back({pos++,p->PT,p->Eta,p->Phi,0,v,0,0});}
    Json native_jets=Json::array();pos=0;for(auto*j:a.get<Jet>("Jet")){auto v=dp::polar(j->PT,j->Eta,j->Phi,j->Mass);p8::demand(std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z)&&std::isfinite(v.e),"invalid native jet P4");e.jets.push_back({pos,j->PT,j->Eta,j->Phi,j->Mass,v,j->Flavor,j->BTag});if(j->Mass<0)++e.negative_native_jet_masses;native_jets.push_back({{"index",pos++},{"pt",j->PT},{"eta",j->Eta},{"phi",j->Phi},{"mass",j->Mass},{"flavour",j->Flavor},{"flavour_algo",j->FlavorAlgo},{"flavour_phys",j->FlavorPhys},{"native_btag_bits",j->BTag},{"btag_algo",j->BTagAlgo},{"btag_phys",j->BTagPhys}});}
    p8::select(e);auto ht=a.get<ScalarHT>("ScalarHT");p8::demand(ht.size()<=1,"ambiguous native ScalarHT");p8::reconstruct(e,ht.empty()?std::nullopt:std::optional<double>(ht[0]->HT));Json row=p8::event_json(e);Json photons=Json::array(),electrons=Json::array();
    for(const auto&p:e.photons){bool selected=std::any_of(e.selected.begin(),e.selected.end(),[&](const auto&q){return p.index==q.index;});photons.push_back({{"index",p.index},{"pt",p.pt},{"eta",p.eta},{"phi",p.phi},{"mass",0},{"selected",selected}});}
    pos=0;for(auto*l:a.get<Electron>("Electron")){p8::demand(std::isfinite(l->PT)&&l->PT>=0&&std::isfinite(l->Eta)&&std::isfinite(l->Phi),"nonfinite native electron");electrons.push_back({{"index",pos++},{"pt",l->PT},{"eta",l->Eta},{"phi",l->Phi},{"charge",l->Charge}});}
    row["photons"]=photons;row["electrons"]=electrons;row["electrons_available"]=a.branches.at("Electron").present;row["all_jets"]=native_jets;row["evidence_class"]="ACTUAL_EXISTING_DATA_READBACK";row["source_ROOT_sha256"]=d.root_hash;row["truth_matching"]={{"status","PHASE9_ORIGINS_IN_SEPARATE_ANCESTRY_JOIN"}};
    photons_seen+=photons.size();electrons_seen+=electrons.size();events<<row.dump()<<'\n';p8::demand(events.good(),"native output write failure");for(std::size_t k=0;k<5;++k)cuts[k]+=e.stages[k];auto key=d.id+":"+std::to_string(ordinal)+":"+source.source_hash+":"+source.hash+"\n";identity.update(key.data(),key.size());
   }
   dp::InputEvent extra;p8::demand(!index.next(extra),"extra source index event");p8::verify_dataset_files(d);std::vector<long> actual_cuts(cuts.begin(),cuts.end());p8::demand(actual_cuts==d.expected,"Phase9 background cutflow differs from frozen Phase8");total+=count;Json branches=Json::array();for(const auto&[name,b]:a.branches)branches.push_back({{"name",name},{"present",b.present},{"class",b.clone},{"dictionary_version",b.version},{"dictionary_checksum",b.checksum}});
   summaries.push_back({{"dataset_id",d.id},{"actual_ROOT_entries",count},{"N_original",d.original},{"cutflow",actual_cuts},{"expected_cutflow",d.expected},{"native_particle_tuples_compared",particles_seen},{"native_photons",photons_seen},{"native_electrons",electrons_seen},{"electrons_available",a.branches.at("Electron").present},{"ordered_source_identity_sha256",identity.finish()},{"root_sha256",d.root_hash},{"input_index_sha256",d.index_hash},{"card_sha256",d.card_hash},{"branches",branches},{"status","PASS_FULL_EXISTING_BACKGROUND_NATIVE_READBACK"}});
  }
  events.close();Json result{{"schema_version",1},{"status","PASS_FULL_EXISTING_BACKGROUND_NATIVE_READBACK"},{"evidence_class","ACTUAL_EXISTING_DATA_READBACK"},{"actual_native_background_events",total},{"signal_original_sources_reused_from_Phase8",1100},{"new_signal_full_ROOT_event_loop",false},{"prefix_events_reread",0},{"ROOT_version",ROOT_RELEASE},{"CXX_standard",20},{"datasets",summaries},{"new_ME_calls",0},{"new_integrals",0},{"new_hard_events",0},{"new_Pythia_events",0},{"new_Delphes_events",0}};p8::write_json(output/"phase9_native_readback.json",result);std::cout<<Json{{"status",result["status"]},{"native_background_events",total},{"new_events",0}}.dump()<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<Json{{"status","BLOCKED_PHASE9_NATIVE_READBACK"},{"reason",e.what()},{"new_ME_calls",0},{"new_events",0}}.dump()<<'\n';return 2;}
}
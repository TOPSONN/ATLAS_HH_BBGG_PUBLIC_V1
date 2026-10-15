// Native external-LHE shower, preserving source records and physical decays.
#include "SignalGraph.hxx"
#include "TrackedLHA.hxx"
#include "SourceAttempt.hxx"
#include "Pythia8Plugins/HepMC3.h"
#include "HepMC3/GenRunInfo.h"
#include "HepMC3/GenCrossSection.h"
#include <fstream>
#include <filesystem>
#include <iostream>
using atlas_hh::quoted;using atlas_hh::real;using signal::require;
namespace fs=std::filesystem;
class SingleReadLHA:public atlas_hh::TrackedLHA {
  zh::SingleSourceRead guard;
public:
  using TrackedLHA::TrackedLHA;
  void begin(){guard.begin();beginAttempt();}
  bool setEvent(int p=0)override{guard.permit();return TrackedLHA::setEvent(p);}
};
int main(int argc,char**argv){
 long attempted=0,written=0;std::string output;
 try{
  require(argc==12,"BLOCKED_PHYSICAL_AUTHORIZATION: fixed signal source/stage arguments required");
  const std::string input=argv[1],index=argv[2],roles=argv[3],xml=argv[4],baseline=argv[5];output=argv[6];
  const int count=std::stoi(argv[7]),total=std::stoi(argv[8]),seed=std::stoi(argv[9]);
  const std::string original_sha=argv[10],authorization=argv[11];
  require((total==100||total==1000)&&(count==10||count==100||count==1000)&&count<=total,"unapproved stage count");
  auto auth=zh::parse_json(zh::read_file(authorization));
  require(auth.at("task").string()=="PHASE7B_7C_7D_GGF_HH_SIGNAL_CAMPAIGN_V1"&&
   auth.at("events").number()==count&&auth.at("original_count").number()==total&&
   auth.at("source_sha256").string()==original_sha&&auth.at("input_sha256").string()==zh::file_sha(input)&&
   auth.at("index_sha256").string()==zh::file_sha(index)&&auth.at("roles_sha256").string()==zh::file_sha(roles),"stale source/stage authorization");
  require(auth.at("executable_sha256").string()==zh::file_sha(argv[0]),"stale native executable");
  require(!fs::exists(output),"output exists");fs::create_directory(output);
  Pythia8::Pythia p(xml,false);require(p.readFile(baseline),"baseline read failed");
  for(const char*s:{"SLHA:readFrom = 0","25:mayDecay = off","25:m0 = 125","6:m0 = 173","24:m0 = 80.419"})require(p.readString(s),"bad signal physics setting");
  require(p.readString("Random:seed = "+std::to_string(seed)),"seed failed");
  auto source=std::make_shared<SingleReadLHA>(input,index,count);require(p.setLHAupPtr(source),"LHA adapter failed");
  require(p.init(),"native external signal initialization failed");
  for(const char*k:{"PartonLevel:ISR","PartonLevel:FSR","HadronLevel:Hadronize","HadronLevel:Decay"})require(p.settings.flag(k),"required shower/decay switch off");
  require(!p.settings.flag("PartonLevel:MPI")&&!p.settings.flag("JetMatching:merge")&&!p.settings.flag("Merging:doKTMerging"),"unapproved MPI/matching");
  require(p.particleData.m0(5)==4.8&&!p.particleData.mayDecay(25),"external physical decay policy mismatch");
  p.settings.writeFile(output+"/effective_settings.cmnd",true);p.particleData.listXML(output+"/effective_particle_data.xml");
  auto info=std::make_shared<HepMC3::GenRunInfo>();
  info->set_weight_names({"input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb","converter_weight_0_pb"});
  info->tools().push_back({"Pythia8","8.317","genuine full-mass HH source with physical external scalar mixed decays"});
  HepMC3::Pythia8ToHepMC3 converter;HepMC3::WriterAscii writer(output+"/shower.hepmc3",info);writer.set_precision(17);
  std::ifstream role(roles);require(role.good(),"missing source role ledger");
  std::ofstream ledger(output+"/attempt_ledger.jsonl");long ordinal;std::string sourcehash;int bb,gg;
  for(int i=1;i<=count;++i){
   require(!fs::exists(fs::path(output)/"STOP"),"PARTIAL_STOPPED");
   require(bool(role>>ordinal>>sourcehash>>bb>>gg)&&ordinal==i&&bb!=gg,"source role index mismatch");
   source->begin();++attempted;const bool ok=p.next();
   ledger<<"{\"source_event_index\":"<<i<<",\"production_event_sha256\":"<<quoted(sourcehash)<<",\"attempted\":true,\"pythia_next_success\":"<<(ok?"true":"false")<<"}\n";ledger.flush();
   require(ok&&source->cursor()==i&&source->consumed().size()==1,"PHYSICAL_SHOWER_FAILED_NO_REPLACEMENT");
   const auto&s=source->consumed().front();require(s.index==i&&s.nup==8,"derived LHE identity failure");
   require(p.info.lhaStrategy()==-4&&p.info.nMPI()<=1,"source weight strategy or MPI changed");
   HepMC3::GenEvent event(info,HepMC3::Units::GEV,HepMC3::Units::MM);
   require(converter.fill_next_event(p,&event,i),"HepMC conversion failed");
   const double raw=s.weight,py=p.info.weight();auto converted=event.weights();require(!converted.empty(),"converter omitted nominal weight");
   require(std::abs(converted[0]-py)<1e-12*std::max(1.,std::abs(py)),"Info/converter mismatch");
   require(std::abs(py-raw)<1e-12*std::max(1.,std::abs(raw)),"unexpected physical BR or source weight bias applied");
   zh::retain_pythia_identity(p.event,event);auto h=signal::inspect(zh::hepmc_graph(event));signal::localClosure(event,h);
   event.weights()={raw/total,raw,py,converted[0]};
   if(event.cross_section())event.cross_section()->set_cross_section(p.info.sigmaGen()*1e9,p.info.sigmaErr()*1e9);
   auto attr=[&](const std::string&k,const std::string&v){event.add_attribute(k,std::make_shared<HepMC3::StringAttribute>(v));};
   attr("source_file_sha256",original_sha);attr("source_event_content_hash",sourcehash);attr("source_event_index",std::to_string(i));
   attr("source_sample_id",total==100?"S01_PHASE7B100":"S01_PHASE7C1000");attr("pythia_run_id",original_sha.substr(0,20));
   attr("pythia_seed",std::to_string(seed));attr("output_event_index",std::to_string(i));attr("source_total_events",std::to_string(total));
   attr("derived_decayed_event_sha256",s.hash);attr("signal_decay_lineage",signal::json(h));
   attr("source_H_bb_index",std::to_string(bb));attr("source_H_gammagamma_index",std::to_string(gg));
   attr("normalization_scope","RAW_PRODUCTION_WEIGHT_MODEL_BR_SEPARATE");
   writer.write_event(event);require(!writer.failed(),"native HepMC write failed");++written;
   if(i%10==0)std::cout<<"source="<<i<<" written="<<written<<"\n"<<std::flush;
  }
  writer.close();p.stat();std::ofstream report(output+"/run_summary.json");
  report<<"{\"status\":\"SHOWER_WRITTEN_REQUIRES_NATIVE_READER\",\"attempted\":"<<attempted<<",\"written\":"<<written<<",\"source_count\":"<<total<<",\"source_identity_failures\":"<<source->identityErrors()<<",\"next_calls\":"<<attempted<<",\"replacement_events\":0,\"new_independent_hard_events\":0,\"source_sha256\":"<<quoted(original_sha)<<",\"pythia_seed\":"<<seed<<"}\n";
  return 0;
 }catch(const std::exception&e){
  if(!output.empty()&&fs::is_directory(output)){std::ofstream f(output+"/failure.json");f<<"{\"status\":\"FAILED_PHYSICAL_SIGNAL_STAGE\",\"attempted\":"<<attempted<<",\"written\":"<<written<<",\"reason\":"<<quoted(e.what())<<"}\n";}
  std::cerr<<e.what()<<'\n';return 2;
 }
}

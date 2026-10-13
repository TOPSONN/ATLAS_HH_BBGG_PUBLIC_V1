// Real external-LHE shower/hadronization. Never generates replacement hard events.
#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC3.h"
#include "HepMC3/Attribute.h"
#include "HepMC3/GenCrossSection.h"
#include "HepMC3/GenRunInfo.h"
#include "HepMC3/Version.h"
#include "Json.hxx"
#include "PhotonOrigin.hxx"
#include "Sha256.hxx"
#include "TrackedLHA.hxx"

#include <chrono>
#include <csignal>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <sys/resource.h>

namespace fs=std::filesystem;
using atlas_hh::quoted;
using atlas_hh::real;
namespace {
volatile std::sig_atomic_t stopping=0;
void stop_requested(int){stopping=1;}
void require(bool ok,const std::string& text){if(!ok)throw std::runtime_error(text);}
struct Options {
  std::string input,index,output,settings,xml,source_hash,sample,run_id;
  long events=0,source_total=0;
  int seed=0;
  double source_sigma=0,source_error=0,max_hours=1,max_disk_gb=5;
  bool dry=false,build_info=false;
};
Options options(int argc,char**argv){
  Options o;
  for(int i=1;i<argc;++i){std::string key=argv[i];
    if(key=="--dry-run"){o.dry=true;continue;}
    if(key=="--build-info"){o.build_info=true;continue;}
    require(i+1<argc,"missing option value: "+key);std::string v=argv[++i];
    if(key=="--input")o.input=v;else if(key=="--source-index")o.index=v;
    else if(key=="--output")o.output=v;else if(key=="--settings")o.settings=v;
    else if(key=="--xml")o.xml=v;else if(key=="--source-sha256")o.source_hash=v;
    else if(key=="--sample-id")o.sample=v;else if(key=="--run-id")o.run_id=v;
    else if(key=="--events")o.events=std::stol(v);else if(key=="--source-total")o.source_total=std::stol(v);
    else if(key=="--seed")o.seed=std::stoi(v);else if(key=="--source-sigma-pb")o.source_sigma=std::stod(v);
    else if(key=="--source-error-pb")o.source_error=std::stod(v);else if(key=="--max-hours")o.max_hours=std::stod(v);
    else if(key=="--max-disk-gb")o.max_disk_gb=std::stod(v);else throw std::runtime_error("unknown option: "+key);
  }
  return o;
}

std::string required_settings(Pythia8::Pythia& p){
  std::ostringstream out;out<<'{';bool first=true;
  for(const auto&key:{"ProcessLevel:all","PartonLevel:all","PartonLevel:ISR","PartonLevel:FSR",
      "HadronLevel:all","HadronLevel:Hadronize","HadronLevel:Decay","Beams:strictLHEFscale","Random:setSeed",
      "BeamRemnants:primordialKT"}){
    require(p.settings.flag(key),std::string("required physics switch off: ")+key);
    if(!first)out<<',';
    first=false;out<<quoted(key)<<":true";
  }
  for(const auto&key:{"PartonLevel:MPI","SecondHard:generate","HardQCD:all","SoftQCD:all",
      "JetMatching:merge","Merging:doKTMerging","Merging:doMGMerging","Merging:doPTLundMerging","UncertaintyBands:doVariations"}){
    require(!p.settings.flag(key),std::string("unsupported additional process/matching/variations: ")+key);
    out<<','<<quoted(key)<<":false";
  }
  require(p.settings.mode("Beams:frameType")==4,"requires actual frameType=4");
  require(p.settings.mode("PartonShowers:model")==1,"requires validated simple shower model 1");
  require(p.settings.mode("SpaceShower:pTmaxMatch")==1&&p.settings.mode("TimeShower:pTmaxMatch")==1,
    "requires explicit SCALUP-based pTmaxMatch=1");
  for(const auto& setting:std::map<std::string,double>{{"BeamRemnants:primordialKTsoft",0.9},
      {"BeamRemnants:primordialKThard",1.8},{"BeamRemnants:halfScaleForKT",1.5},
      {"BeamRemnants:halfMassForKT",1.0},{"BeamRemnants:reducedKTatHighY",0.5},
      {"BeamRemnants:primordialKTremnant",0.4}}){
    const double actual=p.settings.parm(setting.first);
    require(actual==setting.second,"reviewed stock primordial-kT parameter changed: "+setting.first);
    out<<','<<quoted(setting.first)<<':'<<real(actual);
  }
  out<<",\"Beams:frameType\":4,\"PartonShowers:model\":1,\"SpaceShower:pTmaxMatch\":1,\"TimeShower:pTmaxMatch\":1"
    <<",\"Random:seed\":"<<p.settings.mode("Random:seed")
    <<",\"SpaceShower:alphaSvalue\":"<<real(p.settings.parm("SpaceShower:alphaSvalue"))
    <<",\"TimeShower:alphaSvalue\":"<<real(p.settings.parm("TimeShower:alphaSvalue"))
    <<",\"PDF:pSet\":"<<quoted(p.settings.word("PDF:pSet"))
    <<",\"4:m0\":"<<real(p.particleData.m0(4))<<",\"5:m0\":"<<real(p.particleData.m0(5))<<'}';
  return out.str();
}

struct Counters {
  long calls=0,success=0,failed=0,written=0,consumed=0,internal_rejected=0;
  long final_particles=0,charged=0,photons=0,b_terminal=0,c_terminal=0;
  long isr_records=0,fsr_records=0,hadron_records=0,decay_records=0;
  long double sum_w=0,sum_abs_w=0,sum_w2=0;
};
std::string ledger_row(const Options&o,const atlas_hh::SourceEvent&s,long attempt,const std::string&status,
  long output,const std::string&hash,double pyweight,const std::vector<double>&converter,const std::string&reason){
  std::ostringstream x;x<<"{\"source_sample_id\":"<<quoted(o.sample)<<",\"source_file_sha256\":"<<quoted(o.source_hash)
    <<",\"source_event_index\":"<<s.index<<",\"source_event_content_hash\":"<<quoted(s.hash)
    <<",\"pythia_run_id\":"<<quoted(o.run_id)<<",\"pythia_seed\":"<<o.seed
    <<",\"processing_attempt\":"<<attempt<<",\"processing_status\":"<<quoted(status)
    <<",\"output_event_index\":"<<(output?std::to_string(output):"null")
    <<",\"output_event_hash\":"<<(output?quoted(hash):"null")
    <<",\"nominal_generator_weight\":"<<real(s.weight)<<",\"lhe_weight_pb\":"<<real(s.weight)
    <<",\"pythia_weight_pb\":"<<(std::isfinite(pyweight)?real(pyweight):"null")<<",\"input_contribution_pb\":"<<real(s.weight/o.source_total)
    <<",\"weight_interpretation\":\"IDWTUP=-4; signed LHE and Pythia nominal weights in pb; contribution=LHE_XWGTUP/full_original_source_count; provenance columns are not variation weights\""
    <<",\"source_total_events\":"<<o.source_total<<",\"scale_gev\":"<<real(s.scale)
    <<",\"diagnostic\":"<<quoted(reason)<<",\"converter_weights_pb\":[";
  for(std::size_t i=0;i<converter.size();++i){if(i)x<<',';x<<real(converter[i]);}x<<"]}";return x.str();
}

bool contains_flavour(int id,int flavour){
  id=std::abs(id);return id<1000000000 && ((id/10)%10==flavour||(id/100)%10==flavour||(id/1000)%10==flavour);
}
std::string integers(const std::vector<int>& values){std::ostringstream x;x<<'[';
  for(std::size_t i=0;i<values.size();++i){if(i)x<<',';x<<values[i];}x<<']';return x.str();}

void diagnostics(Pythia8::Pythia&p,const atlas_hh::SourceEvent&s,long output,std::ostream&out,Counters&c){
  std::set<int> hard_photons;long n_final=0,n_charged=0,n_photons=0,n_b=0,n_c=0,n_isr=0,n_fsr=0,n_had=0,n_decay=0;
  for(int i=1;i<p.event.size();++i)if(p.event[i].id()==22&&p.event[i].statusAbs()==23)hard_photons.insert(i);
  require(hard_photons.size()==2,"hard-photon Pythia status-23 ancestry roots are not exactly two; identity audit stops");
  std::ostringstream records;records<<'[';bool first=true;
  for(int i=1;i<p.event.size();++i){const auto&v=p.event[i];
    if(v.isFinal()){++n_final;if(v.chargeType()!=0)++n_charged;if(v.id()==22)++n_photons;}
    const bool parton=v.id()==21||std::abs(v.id())<=6;
    if(parton&&v.statusAbs()>=41&&v.statusAbs()<50)++n_isr;
    if(parton&&v.statusAbs()>=51&&v.statusAbs()<60)++n_fsr;
    if(v.isHadron())++n_had;
    if(v.statusAbs()>=91&&v.statusAbs()<100)++n_decay;
    const bool b=v.isHadron()&&contains_flavour(v.id(),5),charm=v.isHadron()&&contains_flavour(v.id(),4);
    bool b_terminal=b,c_terminal=charm;
    for(int child:v.daughterList())if(child>0&&child<p.event.size()&&p.event[child].isHadron()){
      if(contains_flavour(p.event[child].id(),5))b_terminal=false;
      if(contains_flavour(p.event[child].id(),4))c_terminal=false;
    }
    if(b_terminal)++n_b;
    if(c_terminal)++n_c;
    // Preserve every original Pythia entry/status/mother/daughter. No inferred
    // Pythia-to-HepMC barcode relation is invented.
    if(!first)records<<',';
    first=false;
    records<<"{\"pythia_index\":"<<i<<",\"pdg_id\":"<<v.id()<<",\"status\":"<<v.status()
      <<",\"mothers\":"<<integers(v.motherList())<<",\"daughters\":"<<integers(v.daughterList())
      <<",\"p4_gev\":["<<real(v.px())<<','<<real(v.py())<<','<<real(v.pz())<<','<<real(v.e())<<']'
      <<",\"mass_gev\":"<<real(v.m())<<",\"charge_times_three\":"<<v.chargeType()
      <<",\"is_final\":"<<(v.isFinal()?"true":"false")<<",\"is_hadron\":"<<(v.isHadron()?"true":"false")
      <<",\"terminal_b_hadron\":"<<(b_terminal?"true":"false")<<",\"terminal_c_hadron\":"<<(c_terminal?"true":"false");
    if(v.id()==22&&v.isFinal()){
      const auto origin=atlas_hh::photon_origin(p.event,i,hard_photons);
      records<<",\"photon_origin_diagnostic\":"<<quoted(origin.label)<<",\"hard_photon_ancestors\":"<<integers(origin.hard_roots)
        <<",\"is_original_hard_photon\":"<<(origin.original?"true":"false")
        <<",\"has_produced_hadron_ancestor\":"<<(origin.produced_hadron?"true":"false")
        <<",\"has_direct_hadron_decay_photon_path\":"<<(origin.direct_hadron_decay?"true":"false")
        <<",\"has_shower_photon_path\":"<<(origin.shower_photon?"true":"false");
    }
    records<<'}';
  }
  records<<']';
  out<<"{\"source_event_index\":"<<s.index<<",\"output_event_index\":"<<output
    <<",\"final_particle_count\":"<<n_final<<",\"charged_final_count\":"<<n_charged
    <<",\"photon_final_count\":"<<n_photons<<",\"terminal_b_hadron_count\":"<<n_b
    <<",\"terminal_c_hadron_count\":"<<n_c<<",\"isr_parton_record_entries\":"<<n_isr
    <<",\"fsr_parton_record_entries\":"<<n_fsr<<",\"hadron_record_entries\":"<<n_had
    <<",\"decay_record_entries\":"<<n_decay<<",\"hard_photon_roots\":"<<integers(std::vector<int>(hard_photons.begin(),hard_photons.end()))
    <<",\"pythia_hepmc_particle_mapping\":\"NO_BARCODE_EQUIVALENCE_ASSUMED\",\"particles\":"<<records.str()<<"}\n";
  c.final_particles+=n_final;c.charged+=n_charged;c.photons+=n_photons;c.b_terminal+=n_b;c.c_terminal+=n_c;
  c.isr_records+=n_isr;c.fsr_records+=n_fsr;c.hadron_records+=n_had;c.decay_records+=n_decay;
}

class RawAsciiWriter {
  std::ofstream output_;std::string header_,footer_;bool started_=false,closed_=false;
public:
  explicit RawAsciiWriter(const fs::path& path):output_(path,std::ios::binary){require(output_.good(),"cannot open HepMC output");}
  std::string write(const HepMC3::GenEvent& event){
    std::ostringstream text;
    {HepMC3::WriterAscii writer(text,event.run_info());writer.set_precision(17);writer.write_event(event);writer.close();require(!writer.failed(),"official WriterAscii failed");}
    const auto raw=text.str();const auto start=raw.find("\nE "),stop=raw.find("HepMC::Asciiv3-END_EVENT_LISTING");
    require(start!=std::string::npos&&stop!=std::string::npos&&start+1<stop,"one-event serialization envelope missing");
    const auto header=raw.substr(0,start+1),footer=raw.substr(stop),block=raw.substr(start+1,stop-start-1);
    if(!started_){header_=header;footer_=footer;output_<<header_;started_=true;}
    else require(header==header_&&footer==footer_,"run-info header changed between event serializations");
    output_<<block;output_.flush();require(output_.good(),"HepMC output write failed");
    return atlas_hh::Sha256::digest(block);
  }
  void close(){if(closed_)return;if(started_)output_<<footer_;output_.flush();output_.close();closed_=true;}
  ~RawAsciiWriter(){close();}
};

void summary(const Options&o,const Counters&c,Pythia8::Pythia&p,const std::string&status,const std::string&reason,
  const std::string&settings,double elapsed,const atlas_hh::TrackedLHA& source){
  struct rusage usage{};getrusage(RUSAGE_SELF,&usage);
  std::ofstream out(fs::path(o.output)/"run_summary.json");
  out<<"{\"schema_version\":1,\"status\":"<<quoted(status)<<",\"diagnostic\":"<<quoted(reason)
    <<",\"pythia_version\":"<<quoted("8.317")<<",\"hepmc3_version\":"<<quoted(HepMC3::version())
    <<",\"source_sample_id\":"<<quoted(o.sample)<<",\"source_file_sha256\":"<<quoted(o.source_hash)
    <<",\"pythia_run_id\":"<<quoted(o.run_id)<<",\"pythia_seed\":"<<o.seed
    <<",\"source_total_events\":"<<o.source_total<<",\"events_requested\":"<<o.events
    <<",\"N_input\":"<<c.consumed<<",\"N_attempted\":"<<c.consumed<<",\"N_pythia_next_calls\":"<<c.calls
    <<",\"N_source_identity_verified\":"<<source.verifiedCursor()
    <<",\"N_source_identity_failed\":"<<source.identityErrors()
    <<",\"event_identity\":"<<quoted(source.identityErrors()?"BLOCKED":"PASS")
    <<",\"unverified_source_event_hash\":"<<(source.identityErrors()?quoted("UNKNOWN"):"null")
    <<",\"N_shower_success\":"<<c.success<<",\"N_shower_failed\":"<<c.failed<<",\"N_internal_rejected\":"<<c.internal_rejected
    <<",\"N_written\":"<<c.written<<",\"input_cross_section_pb\":"<<real(o.source_sigma)
    <<",\"input_cross_section_uncertainty_pb\":"<<real(o.source_error)
    <<",\"pythia_sigma_gen_mb\":"<<real(p.info.sigmaGen())<<",\"pythia_sigma_error_mb\":"<<real(p.info.sigmaErr())
    <<",\"pythia_n_tried\":"<<p.info.nTried()<<",\"pythia_n_selected\":"<<p.info.nSelected()
    <<",\"pythia_n_accepted\":"<<p.info.nAccepted()<<",\"required_settings\":"<<settings
    <<",\"elapsed_seconds\":"<<real(elapsed)<<",\"peak_rss_bytes\":"<<(usage.ru_maxrss*1024L)
    <<",\"weight_sum_contribution_pb\":"<<real(static_cast<double>(c.sum_w))
    <<",\"weight_sum_abs_contribution_pb\":"<<real(static_cast<double>(c.sum_abs_w))
    <<",\"weight_sum_squared_contribution_pb2\":"<<real(static_cast<double>(c.sum_w2))
    <<",\"final_particle_count\":"<<c.final_particles<<",\"charged_final_count\":"<<c.charged
    <<",\"photon_final_count\":"<<c.photons<<",\"terminal_b_hadron_count\":"<<c.b_terminal
    <<",\"terminal_c_hadron_count\":"<<c.c_terminal<<",\"isr_parton_record_entries\":"<<c.isr_records
    <<",\"fsr_parton_record_entries\":"<<c.fsr_records<<",\"hadron_record_entries\":"<<c.hadron_records
    <<",\"decay_record_entries\":"<<c.decay_records<<"}\n";
}
}

int main(int argc,char**argv){
  try{
    auto o=options(argc,argv);
    if(o.build_info){std::cout<<"{\"pythia_version\":\"8.317\",\"pythia_version_integer\":"<<PYTHIA_VERSION_INTEGER
      <<",\"hepmc3_version\":"<<quoted(HepMC3::version())<<",\"cxx_standard\":"<<__cplusplus<<"}\n";return 0;}
    require(PYTHIA_VERSION_INTEGER==8317&&HEPMC3_VERSION_CODE==3003001,"unverified generator/library build version");
    require(!o.xml.empty()&&!o.settings.empty()&&o.seed>0&&o.seed<=900000000,"settings/xml/valid fixed seed required");
    Pythia8::Pythia p(o.xml,false);require(p.readFile(o.settings),"settings card rejected by installed Pythia");
    require(p.readString("Random:setSeed = on")&&p.readString("Random:seed = "+std::to_string(o.seed)),"seed rejected");
    auto readback=required_settings(p);
    if(o.dry){std::cout<<"{\"status\":\"DRY_RUN\",\"events_processed\":0,\"required_settings\":"<<readback<<"}\n";return 0;}
    require(o.events>0&&o.events<=o.source_total&&!o.output.empty()&&!o.index.empty()&&!o.input.empty(),"invalid event/input/output request");
    require(o.source_hash.size()==64&&!o.run_id.empty()&&!o.sample.empty(),"source identity required");
    require(p.readString("Beams:LHEF = "+o.input),"LHE input setting rejected");
    auto source=std::make_shared<atlas_hh::TrackedLHA>(o.input,o.index,o.events);
    require(p.setLHAupPtr(source),"tracked official LHE reader pointer rejected");
    require(p.init(),"Pythia initialization failed");
    require(source->cursor()==0,"EVENT_IDENTITY: initialization consumed source events unexpectedly");
    readback=required_settings(p);
    require(p.settings.writeFile((fs::path(o.output)/"effective_settings.cmnd").string(),true),"settings snapshot failed");
    p.particleData.listXML((fs::path(o.output)/"effective_particle_data.xml").string());
    std::signal(SIGINT,stop_requested);std::signal(SIGTERM,stop_requested);
    std::ofstream ledger(fs::path(o.output)/"event_ledger.jsonl"),particle(fs::path(o.output)/"particle_diagnostics.jsonl");
    require(ledger.good()&&particle.good(),"cannot open streaming diagnostics");
    HepMC3::Pythia8ToHepMC3 converter;converter.set_print_inconsistency(true);
    auto runinfo=std::make_shared<HepMC3::GenRunInfo>();
    runinfo->tools().push_back({"Pythia8","8.317","External MG5 LO LHE; ISR/FSR/hadronization; no ME/PS matching or merging"});
    runinfo->tools().push_back({"HepMC3",HepMC3::version(),"Official Pythia8Plugins/HepMC3.h + WriterAscii, GeV/mm"});
    RawAsciiWriter writer(fs::path(o.output)/"shower.hepmc3");Counters c;
    const auto start=std::chrono::steady_clock::now();std::string status="PASS",reason="";double last_disk=-10;long finalized_source=0;
    try{
      while(source->cursor()<o.events){
        const auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        if(stopping||fs::exists(fs::path(o.output)/"STOP"))throw std::runtime_error("PARTIAL_STOPPED");
        if(elapsed>o.max_hours*3600)throw std::runtime_error("PARTIAL_TIMEOUT");
        if(elapsed-last_disk>=5){std::uintmax_t bytes=0;for(auto&v:fs::recursive_directory_iterator(o.output))if(v.is_regular_file())bytes+=v.file_size();
          require(bytes<=o.max_disk_gb*1024*1024*1024,"PARTIAL_DISK");last_disk=elapsed;}
        source->beginAttempt();++c.calls;bool ok=p.next();c.consumed=source->cursor();
        const auto&consumed=source->consumed();
        require(!consumed.empty(),source->physical_eof?"PARTIAL_INPUT_EOF":"EVENT_IDENTITY: next() did not consume a new verified source event");
        for(std::size_t i=0;i+1<consumed.size();++i){ledger<<ledger_row(o,consumed[i],c.calls,"INTERNAL_REJECTION",0,"",0,{},"Source read during an internal Pythia retry")<<'\n';++c.failed;++c.internal_rejected;finalized_source=consumed[i].index;}
        const auto&s=consumed.back();
        if(!ok){ledger<<ledger_row(o,s,c.calls,"SHOWER_FAILED",0,"",p.info.weight(),{},"Pythia next() returned false")<<'\n';++c.failed;finalized_source=s.index;ledger.flush();continue;}
        ++c.success;require(p.info.lhaStrategy()==-4,"input weight strategy changed");
        require(p.info.nMPI()<=1,"additional MPI found despite MPI-off baseline");
        HepMC3::GenEvent event(runinfo,HepMC3::Units::GEV,HepMC3::Units::MM);
        require(converter.fill_next_event(p,&event,c.written+1),"HepMC3 conversion failed");
        auto converter_weights=event.weights();require(!converter_weights.empty(),"converter omitted nominal weight");
        const double pyweight=p.info.weight(),contribution=s.weight/o.source_total;
        require(std::isfinite(pyweight)&&std::abs(pyweight-s.weight)<=1e-8*std::max(1.0,std::abs(s.weight)),"Pythia nominal weight changed; normalization requires separate audit");
        std::vector<std::string> names={"input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb"};
        for(std::size_t i=0;i<converter_weights.size();++i)names.push_back("converter_weight_"+std::to_string(i)+"_pb");
        if(runinfo->weight_names().empty())runinfo->set_weight_names(names);else require(runinfo->weight_names()==names,"weight names changed");
        event.weights()={contribution,s.weight,pyweight};event.weights().insert(event.weights().end(),converter_weights.begin(),converter_weights.end());
        event.cross_section()->set_cross_section(p.info.sigmaGen()*1e9,p.info.sigmaErr()*1e9);
        auto attr=[&](const std::string&name,const std::string&value){event.add_attribute(name,std::make_shared<HepMC3::StringAttribute>(value));};
        attr("source_sample_id",o.sample);attr("source_file_sha256",o.source_hash);attr("source_event_index",std::to_string(s.index));
        attr("source_event_content_hash",s.hash);attr("pythia_run_id",o.run_id);attr("pythia_seed",std::to_string(o.seed));
        attr("output_event_index",std::to_string(c.written+1));attr("nominal_generator_weight",real(s.weight));
        attr("weight_interpretation","IDWTUP=-4; pb; contribution=LHE_XWGTUP/full_original_source_count; columns are provenance, not variations");
        attr("input_cross_section_pb",real(o.source_sigma));attr("input_cross_section_uncertainty_pb",real(o.source_error));
        attr("source_total_events",std::to_string(o.source_total));attr("source_scalup_gev",real(s.scale));
        attr("pythia_nMPI_including_primary",std::to_string(p.info.nMPI()));
        diagnostics(p,s,c.written+1,particle,c);
        const auto hash=writer.write(event);++c.written;
        ledger<<ledger_row(o,s,c.calls,"WRITTEN",c.written,hash,pyweight,converter_weights,"")<<'\n';ledger.flush();particle.flush();
        finalized_source=s.index;
        c.sum_w+=contribution;c.sum_abs_w+=std::abs(contribution);c.sum_w2+=static_cast<long double>(contribution)*contribution;
        if(c.written%10==0)std::cout<<"processed="<<c.consumed<<" written="<<c.written<<" failed="<<c.failed<<std::endl;
      }
      if(c.failed||c.written!=o.events||c.consumed!=o.events){status="PARTIAL";reason="Some requested source inputs did not yield a valid written output";}
    }catch(const std::exception&e){status="PARTIAL";reason=e.what();c.consumed=source->cursor();
      for(const auto&s:source->consumed())if(s.index>finalized_source)
        ledger<<ledger_row(o,s,c.calls,"PROCESSING_FAILED",0,"",p.info.weight(),{},reason)<<'\n';
    }
    writer.close();ledger.close();particle.close();p.stat();
    auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    summary(o,c,p,status,reason,readback,elapsed,*source);
    std::cout<<status<<": consumed="<<c.consumed<<" written="<<c.written<<" failed="<<c.failed<<std::endl;
    return status=="PASS"?0:2;
  }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<std::endl;return 1;}
}

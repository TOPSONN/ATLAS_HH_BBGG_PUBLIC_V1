// Real external-LHE shower/hadronization. Never generates replacement hard events.
#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC3.h"
#include "HepMC3/Attribute.h"
#include "HepMC3/GenCrossSection.h"
#include "HepMC3/GenRunInfo.h"
#include "HepMC3/Version.h"
#include "Json.hxx"
#include "BackgroundAncestry.hxx"
#include "Sha256.hxx"
#include "TrackedLHA.hxx"
#include "SourceAttempt.hxx"

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
  std::string input,index,output,settings,overlay,xml,source_hash,sample,process,run_id,authorization,authorization_sha,bridge_sha,index_hash,stage;
  long events=0,source_total=0;
  int seed=0,mg_seed=0;
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
    else if(key=="--overlay")o.overlay=v;
    else if(key=="--authorization")o.authorization=v;else if(key=="--authorization-sha256")o.authorization_sha=v;
    else if(key=="--bridge-sha256")o.bridge_sha=v;else if(key=="--index-sha256")o.index_hash=v;
    else if(key=="--stage")o.stage=v;else if(key=="--xml")o.xml=v;else if(key=="--source-sha256")o.source_hash=v;
    else if(key=="--sample-id")o.sample=v;else if(key=="--process")o.process=v;else if(key=="--run-id")o.run_id=v;
    else if(key=="--events")o.events=std::stol(v);else if(key=="--source-total")o.source_total=std::stol(v);
    else if(key=="--seed")o.seed=std::stoi(v);else if(key=="--source-sigma-pb")o.source_sigma=std::stod(v);
    else if(key=="--source-error-pb")o.source_error=std::stod(v);else if(key=="--max-hours")o.max_hours=std::stod(v);
    else if(key=="--max-disk-gb")o.max_disk_gb=std::stod(v);else throw std::runtime_error("unknown option: "+key);
  }
  return o;
}

std::string required_settings(Pythia8::Pythia& p,const std::string&process){
  require(p.settings.mode("SLHA:readFrom")==0,"SM-only SLHA policy changed");
  require(p.particleData.m0(25)==125.0&&p.particleData.m0(23)==91.188,"Reviewed resonance masses changed");
  auto h=p.particleData.particleDataEntryPtr(25),z=p.particleData.particleDataEntryPtr(23);
  require(bool(h)&&bool(z),"Missing H/Z model table");
  int h_enabled=0,z_enabled=0;
  for(int i=0;i<h->sizeChannels();++i){const auto&ch=h->channel(i);if(ch.onMode()==1||ch.onMode()==2){++h_enabled;
      if(process!="bbgj")require(ch.multiplicity()==2&&ch.product(0)==22&&ch.product(1)==22,"Unexpected enabled H channel");}}
  for(int i=0;i<z->sizeChannels();++i)if(z->channel(i).onMode()==1||z->channel(i).onMode()==2)++z_enabled;
  require((process=="bbgj"?h_enabled>1:h_enabled==1)&&z_enabled>1,"H mode policy missing or Z incorrectly forced again");
  if(process=="tth"){require(p.particleData.m0(6)==173&&p.particleData.m0(24)==80.419,"Explicit top/W masses differ");
    for(int id:{6,24}){auto e=p.particleData.particleDataEntryPtr(id);require(bool(e),"Missing top/W table");int n=0;for(int i=0;i<e->sizeChannels();++i)if(e->channel(i).onMode()!=0&&e->channel(i).bRatio()>0)++n;require(n>0,"Inclusive top/W channels absent");}}
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
  out<<",\"SLHA:readFrom\":0,\"H_forcing\":"<<quoted(process=="bbgj"?"NONE":"25:onMode=off;25:onIfMatch=22 22")<<",\"Z_forcing\":\"NONE\",\"Beams:frameType\":4,\"PartonShowers:model\":1,\"SpaceShower:pTmaxMatch\":1,\"TimeShower:pTmaxMatch\":1"
    <<",\"process\":"<<quoted(process)<<",\"top_W_mode\":\"inclusive supported Pythia channels; production-decay spin correlations unvalidated\""
    <<",\"Random:seed\":"<<p.settings.mode("Random:seed")
    <<",\"SpaceShower:alphaSvalue\":"<<real(p.settings.parm("SpaceShower:alphaSvalue"))
    <<",\"TimeShower:alphaSvalue\":"<<real(p.settings.parm("TimeShower:alphaSvalue"))
    <<",\"PDF:pSet\":"<<quoted(p.settings.word("PDF:pSet"))
    <<",\"LesHouches:setQuarkMass\":"<<p.settings.mode("LesHouches:setQuarkMass")
    <<",\"LesHouches:setLeptonMass\":"<<p.settings.mode("LesHouches:setLeptonMass")
    <<",\"LesHouches:smearHadronMass\":"<<p.settings.mode("LesHouches:smearHadronMass")
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
  std::ostringstream x;x<<"{\"process_alias\":"<<quoted(o.process)<<",\"source_sample_id\":"<<quoted(o.sample)<<",\"source_file_sha256\":"<<quoted(o.source_hash)
    <<",\"source_event_index\":"<<s.index<<",\"source_event_content_hash\":"<<quoted(s.hash)
    <<",\"pythia_run_id\":"<<quoted(o.run_id)<<",\"pythia_seed\":"<<o.seed
    <<",\"source_generation_seed\":"<<o.mg_seed
    <<",\"processing_attempt\":"<<attempt<<",\"processing_status\":"<<quoted(status)
    <<",\"output_event_index\":"<<(output?std::to_string(output):"null")
    <<",\"output_event_hash\":"<<(output?quoted(hash):"null")
    <<",\"nominal_generator_weight\":"<<real(s.weight)<<",\"lhe_weight_pb\":"<<real(s.weight)
    <<",\"pythia_weight_pb\":"<<(std::isfinite(pyweight)?real(pyweight):"null")<<",\"input_contribution_pb\":"<<real(s.weight/o.source_total)
    <<",\"weight_interpretation\":\"IDWTUP=-4; signed LHE and Pythia nominal weights in pb; contribution=LHE_XWGTUP/full_original_source_count; provenance columns are not variation weights\""
    <<",\"source_total_events\":"<<o.source_total<<",\"scale_gev\":"<<real(s.scale)
    <<",\"actual_Info_to_LHE_ratio\":"<<(s.weight!=0&&std::isfinite(pyweight)?real(pyweight/s.weight):"null")
    <<",\"source_included_Z_decay\":"<<(o.process=="zh"?"true":"false")
    <<",\"top_W_decay_convention\":\"inclusive supported Pythia channels; no exclusive top/W BR factor applied\""
    <<",\"diagnostic\":"<<quoted(reason)<<",\"converter_weights_pb\":[";
  for(std::size_t i=0;i<converter.size();++i){if(i)x<<',';x<<real(converter[i]);}x<<"]}";return x.str();
}

std::string integers(const std::vector<int>& values){std::ostringstream x;x<<'[';
  for(std::size_t i=0;i<values.size();++i){if(i)x<<',';x<<values[i];}x<<']';return x.str();}

struct SourceRoles {int h=0,z=0,b=0,bbar=0,t=0,tbar=0,photon=0,jet=0;};
SourceRoles source_roles(const atlas_hh::SourceEvent& s,const std::string&process){
  SourceRoles r;
  for(std::size_t i=0;i<s.particles.size();++i){const auto&v=s.particles[i];int index=i+1;
    auto set=[&](int&field){require(!field,"Duplicate original source role");field=index;};
    if(v.id==25&&v.status==1)set(r.h);
    if(v.id==23&&v.status==2)set(r.z);
    if(v.id==6&&v.status==1)set(r.t);
    if(v.id==-6&&v.status==1)set(r.tbar);
    if(v.id==5&&v.status==1)set(r.b);
    if(v.id==-5&&v.status==1)set(r.bbar);
    if(v.id==22&&v.status==1)set(r.photon);
    if(v.status==1&&(v.id==21||(std::abs(v.id)>=1&&std::abs(v.id)<=4)))set(r.jet);
  }
  if(process=="zh"){
    require(r.h&&r.z&&r.b&&r.bbar&&!r.t&&!r.tbar&&!r.photon&&!r.jet,"Missing/extra source Zbb/stableH topology");
    for(int index:{r.b,r.bbar}){const auto&p=s.particles.at(index-1);require(p.m1==r.z&&p.m2==r.z,"Source bottom ancestry is not exact source Z");}
  }else if(process=="tth")require(r.h&&r.t&&r.tbar&&!r.z&&!r.b&&!r.bbar&&!r.photon&&!r.jet,"Missing/extra stable t tbar H topology");
  else require(process=="bbgj"&&!r.h&&!r.z&&!r.t&&!r.tbar&&r.b&&r.bbar&&r.photon&&r.jet,"Missing/extra b bbar one-Born-photon j4 topology");
  return r;
}
std::string source_roles_json(const SourceRoles&r){return "{\"H\":"+std::to_string(r.h)+",\"Z\":"+std::to_string(r.z)+",\"b\":"+std::to_string(r.b)+",\"bbar\":"+std::to_string(r.bbar)+",\"t\":"+std::to_string(r.t)+",\"tbar\":"+std::to_string(r.tbar)+",\"photon\":"+std::to_string(r.photon)+",\"jet\":"+std::to_string(r.jet)+"}";}
void decay_tables(Pythia8::Pythia&p,const fs::path&path,bool initialized,const std::string&process){
  std::ofstream out(path);require(out.good(),"Cannot save actual decay-table readback");
  out<<"{\"schema_version\":1,\"initialized_external_lhe\":"<<(initialized?"true":"false")
     <<",\"physical_BR_adoption\":\"PENDING_ACTUAL_CLOSURE\",\"source_Z_decay_already_included\":"<<(process=="zh"?"true":"false")<<",\"top_W_decay_scope\":\"inclusive supported Pythia channels; production-decay spin correlations unvalidated\",\"tables\":{";
  bool first=true;
  for(int id:{6,23,24,25}){auto entry=p.particleData.particleDataEntryPtr(id);if(!first)out<<',';first=false;
    out<<quoted(std::to_string(id))<<":{\"mass_gev\":"<<quoted(real(entry->m0()))<<",\"total_width_gev\":"<<quoted(real(entry->mWidth()))<<",\"channels\":[";
    for(int i=0;i<entry->sizeChannels();++i){const auto&ch=entry->channel(i);if(i)out<<',';
      out<<"{\"index\":"<<i<<",\"on_mode\":"<<ch.onMode()<<",\"stored_inclusive_BR\":"<<quoted(real(ch.bRatio()))
         <<",\"partial_width_gev\":"<<(initialized?quoted(real(ch.onShellWidth())):"null")<<",\"products\":[";
      for(int j=0;j<ch.multiplicity();++j){if(j)out<<',';out<<ch.product(j);}out<<"]}";
    }out<<"]}";
  }out<<"}}\n";require(out.good(),"Decay table write failed");
}
struct HiggsValues {double total=0,partial=0,br=0,conditional=0;};
HiggsValues higgs_values(Pythia8::Pythia&p){
  auto entry=p.particleData.particleDataEntryPtr(25);require(bool(entry),"Initialized H model table missing");
  HiggsValues value;value.total=entry->mWidth();double enabled_sum=0;int targets=0;
  for(int i=0;i<entry->sizeChannels();++i){const auto&ch=entry->channel(i);
    if(ch.onMode()==1||ch.onMode()==2)enabled_sum+=ch.bRatio();
    if(ch.multiplicity()==2&&ch.product(0)==22&&ch.product(1)==22){++targets;value.partial=ch.onShellWidth();value.br=ch.bRatio();}}
  require(targets==1&&std::isfinite(value.total)&&std::isfinite(value.partial)&&std::isfinite(value.br)&&
    value.total>0&&value.partial>0&&value.partial<=value.total&&value.br>0&&value.br<=1&&enabled_sum>0,
    "Invalid actual initialized H widths/BR");
  require(std::abs(value.partial/value.total-value.br)<=2e-12,"Actual H partial/total width differs from inclusive model BR");
  value.conditional=value.br/enabled_sum;return value;
}
class NoReplacementLHA:public atlas_hh::TrackedLHA{
  zh::SingleSourceRead attempt_;
public:
  using atlas_hh::TrackedLHA::TrackedLHA;
  long refused_reads()const{return attempt_.denied();}
  void beginAttempt(){attempt_.begin();atlas_hh::TrackedLHA::beginAttempt();}
  bool setEvent(int process=0)override{
    attempt_.permit();return atlas_hh::TrackedLHA::setEvent(process);
  }
};
void diagnostics(const Options&o,Pythia8::Pythia&p,const atlas_hh::SourceEvent&s,long output,std::ostream&out,Counters&c){
  const auto lineage=zh::inspect(zh::pythia_graph(p.event),o.process);
  if(o.process=="tth"){
    auto graph=zh::pythia_graph(p.event);
    for(const auto&entry:std::vector<std::pair<int,std::vector<int>>>{{6,zh::top_birth(graph,lineage.t,1)},
        {-6,zh::top_birth(graph,lineage.tbar,-1)},{24,zh::w_birth(graph,lineage.wplus,1)},
        {-24,zh::w_birth(graph,lineage.wminus,-1)}}){
      auto table=p.particleData.particleDataEntryPtr(entry.first);require(bool(table),"Actual top/W model table missing");
      std::vector<int> actual;for(int id:entry.second)actual.push_back(graph.at(id).pdg);std::sort(actual.begin(),actual.end());
      bool supported=false;
      for(int i=0;i<table->sizeChannels();++i){const auto&channel=table->channel(i);
        const bool enabled=entry.first>0?(channel.onMode()==1||channel.onMode()==2):(channel.onMode()==1||channel.onMode()==3);
        if(!enabled||channel.bRatio()<=0||channel.multiplicity()!=int(actual.size()))continue;
        std::vector<int> products;for(int j=0;j<channel.multiplicity();++j){int pdg=channel.product(j);
          products.push_back(entry.first<0&&p.particleData.hasAnti(pdg)?-pdg:pdg);}
        std::sort(products.begin(),products.end());if(products==actual)supported=true;
      }
      require(supported,"Actual top/W channel absent from enabled positive-BR initialized inclusive model table");
    }
  }
  const auto roles=source_roles(s,o.process);
  std::map<int,int> process_roles;
  for(int role:{roles.h,roles.z,roles.t,roles.tbar,roles.b,roles.bbar,roles.photon,roles.jet})if(role){
    const auto&source=s.particles.at(role-1);std::vector<int> matches;
    const bool resonance=source.id==25||source.id==23||std::abs(source.id)==6;
    for(int i=1;i<p.process.size();++i){const auto&q=p.process[i];if(q.id()!=source.id)continue;
      if(!resonance&&q.statusAbs()!=23)continue;
      bool close=true;if(resonance)for(const auto&v:std::vector<std::pair<double,double>>{{source.px,q.px()},{source.py,q.py()},{source.pz,q.pz()},{source.e,q.e()},{source.m,q.m()}})
        if(std::abs(v.first-v.second)>1e-6+1e-9*std::max(std::abs(v.first),std::abs(v.second)))close=false;
      if(close)matches.push_back(i);
    }
    require(matches.size()==1,"Source-to-process PDG/four-momentum identity missing or ambiguous");process_roles[role]=matches.front();
  }
  out<<"{\"source_event_index\":"<<s.index<<",\"source_event_content_hash\":"<<quoted(s.hash)
     <<",\"output_event_index\":"<<output<<",\"source_lhe_roles\":"<<source_roles_json(roles)
     <<",\"process_source_roles_verified\":true"
     <<",\"source_to_process_scope\":\"Official LHE reader checks all original tuples exactly; reviewed LesHouches quark-mass reshuffling allowed after read; resonance process momenta compared separately before ISR\",\"source_to_process_indices\":{";
  bool first_role=true;for(const auto&[source_id,process_id]:process_roles){if(!first_role)out<<',';first_role=false;out<<quoted(std::to_string(source_id))<<':'<<process_id;}
  out<<"},\"lineage\":"<<zh::lineage_json(lineage)<<",\"pythia_hepmc_particle_mapping\":\"NO_BARCODE_EQUIVALENCE_ASSUMED\",\"particles\":[";
  for(int i=1;i<p.event.size();++i){const auto&v=p.event[i];if(i>1)out<<',';
    out<<"{\"pythia_index\":"<<i<<",\"pdg_id\":"<<v.id()<<",\"status\":"<<v.status()
       <<",\"mothers\":"<<integers(v.motherList())<<",\"daughters\":"<<integers(v.daughterList())
       <<",\"p4_gev\":["<<real(v.px())<<','<<real(v.py())<<','<<real(v.pz())<<','<<real(v.e())<<']'
       <<",\"mass_gev\":"<<real(v.m())<<",\"is_final\":"<<(v.isFinal()?"true":"false")
       <<",\"is_hadron\":"<<(v.isHadron()?"true":"false")<<",\"production_xyzt_mm\":["
       <<real(v.xProd())<<','<<real(v.yProd())<<','<<real(v.zProd())<<','<<real(v.tProd())<<"]}";
    if(v.isFinal()){++c.final_particles;if(v.chargeType()!=0)++c.charged;if(v.id()==22)++c.photons;}
    if(v.isHadron())++c.hadron_records;
    bool terminal_b=v.isHadron()&&p.particleData.nQuarksInCode(v.id(),5)>0;
    bool terminal_c=v.isHadron()&&p.particleData.nQuarksInCode(v.id(),4)>0;
    for(int child:v.daughterList())if(child>0&&child<p.event.size()&&p.event[child].isHadron()){
      if(p.particleData.nQuarksInCode(p.event[child].id(),5)>0)terminal_b=false;
      if(p.particleData.nQuarksInCode(p.event[child].id(),4)>0)terminal_c=false;
    }
    if(terminal_b){++c.b_terminal;}if(terminal_c){++c.c_terminal;}
    if(v.statusAbs()>=91&&v.statusAbs()<100)++c.decay_records;
    if((v.id()==21||std::abs(v.id())<=6)&&v.statusAbs()>=41&&v.statusAbs()<50)++c.isr_records;
    if((v.id()==21||std::abs(v.id())<=6)&&v.statusAbs()>=51&&v.statusAbs()<60)++c.fsr_records;
  }
  out<<"]}\n";
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
  const std::string&settings,double elapsed,const NoReplacementLHA& source){
  struct rusage usage{};getrusage(RUSAGE_SELF,&usage);
  std::ofstream out(fs::path(o.output)/"run_summary.json");
  const auto h=o.process=="bbgj"?HiggsValues{}:higgs_values(p);
  out<<"{\"schema_version\":1,\"status\":"<<quoted(status=="PASS"?"SHOWER_WRITTEN_REQUIRES_INDEPENDENT_READER":status)<<",\"exclusive_physical_normalization\":\"BLOCKED\",\"physical_BR_adoption\":\"UNKNOWN_NOT_APPLIED\""<<",\"diagnostic\":"<<quoted(reason)
    <<",\"initialized_higgs_decay\":{\"applicable\":"<<(o.process=="bbgj"?"false":"true")<<",\"inclusive_model_BR_gamma_gamma\":"<<real(h.br)<<",\"total_width_GeV\":"<<real(h.total)
    <<",\"partial_width_gamma_gamma_GeV\":"<<real(h.partial)<<",\"conditional_forced_probability\":"<<real(h.conditional)
    <<",\"inclusive_table_sha256\":"<<quoted(zh::file_sha(fs::path(o.output)/"decay_tables_inclusive_initialized.json"))
    <<",\"effective_table_sha256\":"<<quoted(zh::file_sha(fs::path(o.output)/"decay_tables_initialized.json"))
    <<",\"original_preinit_table_sha256\":"<<quoted(zh::file_sha(fs::path(o.output)/"decay_tables_original_preinit.json"))
    <<",\"original_particle_data_sha256\":"<<quoted(zh::file_sha(fs::path(o.output)/"original_particle_data.xml"))
    <<",\"inclusive_particle_data_sha256\":"<<quoted(zh::file_sha(fs::path(o.output)/"inclusive_initialized_particle_data.xml"))
    <<",\"effective_particle_data_sha256\":"<<quoted(zh::file_sha(fs::path(o.output)/"effective_particle_data.xml"))
    <<",\"scope\":\"Actual initialized inclusive-vs-forced model tables, no adopted physical BR or nominal-inclusion inference\"}"
    <<",\"pythia_version\":"<<quoted("8.317")<<",\"hepmc3_version\":"<<quoted(HepMC3::version())
    <<",\"process_alias\":"<<quoted(o.process)<<",\"source_sample_id\":"<<quoted(o.sample)<<",\"source_file_sha256\":"<<quoted(o.source_hash)
    <<",\"pythia_run_id\":"<<quoted(o.run_id)<<",\"pythia_seed\":"<<o.seed
    <<",\"source_generation_seed\":"<<o.mg_seed
    <<",\"source_total_events\":"<<o.source_total<<",\"events_requested\":"<<o.events
    <<",\"N_input\":"<<c.consumed<<",\"N_attempted\":"<<c.consumed<<",\"N_pythia_next_calls\":"<<c.calls
    <<",\"N_source_identity_verified\":"<<source.verifiedCursor()
    <<",\"N_source_identity_failed\":"<<source.identityErrors()
    <<",\"event_identity\":"<<quoted(source.identityErrors()?"BLOCKED":"PASS")
    <<",\"unverified_source_event_hash\":"<<(source.identityErrors()?quoted("UNKNOWN"):"null")
    <<",\"N_shower_success\":"<<c.success<<",\"N_shower_failed\":"<<c.failed<<",\"N_internal_rejected\":"<<c.internal_rejected
    <<",\"N_refused_internal_source_read_attempts\":"<<source.refused_reads()
    <<",\"internal_retry_scope\":\"N_internal_rejected counts consumed hard-source records only; second reads are refused; intra-event shower retries are not separately exposed\""
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
    if(!o.dry){zh::StageRequest request{o.authorization,o.authorization_sha,o.bridge_sha,o.input,o.index,o.index_hash,o.source_hash,o.output,o.stage,o.events,o.source_total,o.seed,o.max_hours,o.max_disk_gb,o.process};
      auto authority=zh::check_authorization(request,"native_runner_sha256");o.mg_seed=authority.at("source_request").at("seed").integer();}
    require(!o.xml.empty()&&!o.settings.empty()&&!o.overlay.empty()&&o.seed>0&&o.seed<=900000000,"settings/xml/valid fixed seed required");
    require(zh::file_sha(o.settings)=="53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389","Reviewed baseline bytes changed");
    const std::map<std::string,std::string> overlays{
      {"zh","f2315b863cf39bf6a8b5e87da29397d1e3a773b703ec429a0b78666656d8d2f6"},
      {"tth","26e3c29bfc6c22a557a47bbf35c83c10d0b8c8e46061f1caa3b27ee252d1481c"},
      {"bbgj","0d53adaceb4eb9ca7de9fea2ba7b2bed6f0b4699da7b7a2752d24ee1c400947e"}};
    require(overlays.count(o.process)&&zh::file_sha(o.overlay)==overlays.at(o.process),"Reviewed process overlay bytes changed");
    Pythia8::Pythia p(o.xml,false);require(p.readFile(o.settings),"settings card rejected by installed Pythia");
    std::vector<int> original_h_modes;auto original_h=p.particleData.particleDataEntryPtr(25);
    for(int i=0;i<original_h->sizeChannels();++i)original_h_modes.push_back(original_h->channel(i).onMode());
    if(!o.dry){decay_tables(p,fs::path(o.output)/"decay_tables_original_preinit.json",false,o.process);
      p.particleData.listXML((fs::path(o.output)/"original_particle_data.xml").string());}
    require(p.readFile(o.overlay),"Preferred H-only overlay rejected");
    require(p.readString("Random:setSeed = on")&&p.readString("Random:seed = "+std::to_string(o.seed)),"seed rejected");
    auto readback=required_settings(p,o.process);
    if(o.dry){std::cout<<"{\"status\":\"DRY_RUN\",\"events_processed\":0,\"required_settings\":"<<readback<<"}\n";return 0;}
    require(o.events>0&&o.events<=o.source_total&&!o.output.empty()&&!o.index.empty()&&!o.input.empty(),"invalid event/input/output request");
    require(o.source_hash.size()==64&&!o.run_id.empty()&&!o.sample.empty(),"source identity required");
    require(std::isfinite(o.source_sigma)&&o.source_sigma>0&&std::isfinite(o.source_error)&&o.source_error>=0,"Invalid source cross section/uncertainty");
    decay_tables(p,fs::path(o.output)/"decay_tables_before_init.json",false,o.process);
    // Actual source-header model comparator only. It never calls next(), and
    // a separate official reader must remain at cursor0 on the SAME full100 input.
    Pythia8::Pythia inclusive(o.xml,false);
    require(inclusive.readFile(o.settings)&&inclusive.readFile(o.overlay),"Inclusive comparator settings rejected");
    auto inclusive_h=inclusive.particleData.particleDataEntryPtr(25);
    require(inclusive_h->sizeChannels()==int(original_h_modes.size()),"H channel table changed during comparator setup");
    for(int i=0;i<inclusive_h->sizeChannels();++i)inclusive_h->channel(i).onMode(original_h_modes.at(i));
    require(inclusive.readString("Random:setSeed = on")&&inclusive.readString("Random:seed = "+std::to_string(o.seed))&&
      inclusive.readString("Beams:LHEF = "+o.input),"Inclusive comparator external settings rejected");
    auto inclusive_source=std::make_shared<NoReplacementLHA>(o.input,o.index,o.events);
    require(inclusive.setLHAupPtr(inclusive_source)&&inclusive.init(),"Inclusive no-next external-LHE initialization failed");
    require(inclusive_source->cursor()==0&&inclusive.info.nAccepted()==0,"Inclusive comparator consumed a source event");
    const auto inclusive_values=o.process=="bbgj"?HiggsValues{}:higgs_values(inclusive);
    decay_tables(inclusive,fs::path(o.output)/"decay_tables_inclusive_initialized.json",true,o.process);
    inclusive.particleData.listXML((fs::path(o.output)/"inclusive_initialized_particle_data.xml").string());
    require(inclusive.settings.writeFile((fs::path(o.output)/"inclusive_initialized_settings.cmnd").string(),true),"Inclusive settings snapshot failed");
    require(p.readString("Beams:LHEF = "+o.input),"LHE input setting rejected");
    auto source=std::make_shared<NoReplacementLHA>(o.input,o.index,o.events);
    require(p.setLHAupPtr(source),"tracked official LHE reader pointer rejected");
    require(p.init(),"Pythia initialization failed");
    require(source->cursor()==0,"EVENT_IDENTITY: initialization consumed source events unexpectedly");
    require(source->sizeProc()==1&&std::abs(source->xSec(0)-o.source_sigma)<=1e-13*std::max(1.0,std::abs(o.source_sigma))&&
      std::abs(source->xErr(0)-o.source_error)<=1e-13*std::max(1.0,std::abs(o.source_error)),"Actual external LHE init cross section differs from source receipt");
    decay_tables(p,fs::path(o.output)/"decay_tables_initialized.json",true,o.process);
    const auto forced_values=o.process=="bbgj"?HiggsValues{}:higgs_values(p);
    require(o.process=="bbgj"||(std::abs(inclusive_values.total-forced_values.total)<=1e-13&&std::abs(inclusive_values.partial-forced_values.partial)<=1e-13&&
      std::abs(inclusive_values.br-forced_values.br)<=1e-13&&forced_values.conditional==1.0),
      "Inclusive and forced initialized H model tables do not preserve one reviewed width/BR convention");
    readback=required_settings(p,o.process);
    require(p.settings.writeFile((fs::path(o.output)/"effective_settings.cmnd").string(),true),"settings snapshot failed");
    p.particleData.listXML((fs::path(o.output)/"effective_particle_data.xml").string());
    std::signal(SIGINT,stop_requested);std::signal(SIGTERM,stop_requested);
    std::ofstream ledger(fs::path(o.output)/"event_ledger.jsonl"),particle(fs::path(o.output)/"particle_diagnostics.jsonl");
    require(ledger.good()&&particle.good(),"cannot open streaming diagnostics");
    HepMC3::Pythia8ToHepMC3 converter;converter.set_print_inconsistency(true);
    auto runinfo=std::make_shared<HepMC3::GenRunInfo>();
    runinfo->tools().push_back({"Pythia8","8.317","External reviewed 1000-source stream; profile-specific decays; raw nominal preserved; model normalization requires actual closure"});
    runinfo->tools().push_back({"HepMC3",HepMC3::version(),"Official Pythia8Plugins/HepMC3.h + WriterAscii, GeV/mm"});
    RawAsciiWriter writer(fs::path(o.output)/"shower.hepmc3");Counters c;
    const auto start=std::chrono::steady_clock::now();std::string status="PASS",reason="";double last_disk=-10;long finalized_source=0;
    try{
      while(source->cursor()<o.events){
        const auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        if(stopping||fs::exists(fs::path(o.output)/"STOP"))throw std::runtime_error("PARTIAL_STOPPED");
        if(elapsed>o.max_hours*3600)throw std::runtime_error("PARTIAL_TIMEOUT");
        auto authorization=zh::parse_json(zh::read_file(o.authorization));auto request=authorization.at("source_request");
        zh::check_live_state(authorization,zh::parse_json(zh::read_file(fs::path(request.at("output").string())/"run_manifest.json")),double(std::time(nullptr)));
        if(elapsed-last_disk>=5){std::uintmax_t bytes=0;for(auto&v:fs::recursive_directory_iterator(o.output))if(v.is_regular_file())bytes+=v.file_size();
          require(bytes<=o.max_disk_gb*1024*1024*1024,"PARTIAL_DISK");last_disk=elapsed;}
        source->beginAttempt();++c.calls;bool ok=p.next();c.consumed=source->cursor();
        const auto&consumed=source->consumed();
        require(!consumed.empty(),source->physical_eof?"PARTIAL_INPUT_EOF":"EVENT_IDENTITY: next() did not consume a new verified source event");
        for(std::size_t i=0;i+1<consumed.size();++i){ledger<<ledger_row(o,consumed[i],c.calls,"INTERNAL_REJECTION",0,"",0,{},"Source read during an internal Pythia retry")<<'\n';++c.failed;++c.internal_rejected;finalized_source=consumed[i].index;}
        require(consumed.size()==1,"PARTIAL_SOURCE_MAPPING: exactly one source read per attempt required");
        const auto&s=consumed.back();
        if(!ok){ledger<<ledger_row(o,s,c.calls,"SHOWER_FAILED",0,"",p.info.weight(),{},"Pythia next() returned false; no replacement/retry")<<'\n';++c.failed;finalized_source=s.index;ledger.flush();throw std::runtime_error("PARTIAL_SHOWER_FAILED");}
        ++c.success;require(p.info.lhaStrategy()==-4,"input weight strategy changed");
        require(p.info.nMPI()<=1,"additional MPI found despite MPI-off baseline");
        HepMC3::GenEvent event(runinfo,HepMC3::Units::GEV,HepMC3::Units::MM);
        require(converter.fill_next_event(p,&event,c.written+1),"HepMC3 conversion failed");
        auto converter_weights=event.weights();require(!converter_weights.empty(),"converter omitted nominal weight");
        const double pyweight=p.info.weight(),contribution=s.weight/o.source_total;
        require(std::isfinite(pyweight),"Nonfinite actual Pythia nominal weight");
        for(double value:converter_weights)require(std::isfinite(value),"Nonfinite converter weight");
        require(std::abs(pyweight-converter_weights.front())<=1e-12*std::max({1.0,std::abs(pyweight),std::abs(converter_weights.front())}),"Actual Info/converter nominal mismatch");
        zh::retain_pythia_identity(p.event,event);
        const auto hepmc_lineage=zh::inspect(zh::hepmc_graph(event),o.process);
        const auto lhe_roles=source_roles(s,o.process);
        std::vector<std::string> names={"input_contribution_pb","LHE_XWGTUP_pb","Pythia_Info_weight_pb"};
        for(std::size_t i=0;i<converter_weights.size();++i)names.push_back("converter_weight_"+std::to_string(i)+"_pb");
        if(runinfo->weight_names().empty())runinfo->set_weight_names(names);else require(runinfo->weight_names()==names,"weight names changed");
        event.weights()={contribution,s.weight,pyweight};event.weights().insert(event.weights().end(),converter_weights.begin(),converter_weights.end());
        event.cross_section()->set_cross_section(p.info.sigmaGen()*1e9,p.info.sigmaErr()*1e9);
        auto attr=[&](const std::string&name,const std::string&value){event.add_attribute(name,std::make_shared<HepMC3::StringAttribute>(value));};
        attr("source_lhe_profile",o.sample);attr("process_alias",o.process);attr("source_included_decay_ids",o.process=="zh"?"Z_to_b_bbar":"NONE");
        attr("physical_BR_adoption","UNKNOWN_NOT_APPLIED");attr("exclusive_physical_normalization","BLOCKED");
        attr("source_lhe_roles",source_roles_json(lhe_roles));attr("background_decay_lineage",zh::lineage_json(hepmc_lineage));
        attr("source_sample_id",o.sample);attr("source_file_sha256",o.source_hash);attr("source_event_index",std::to_string(s.index));
        attr("source_event_content_hash",s.hash);attr("pythia_run_id",o.run_id);attr("pythia_seed",std::to_string(o.seed));
        attr("output_event_index",std::to_string(c.written+1));attr("nominal_generator_weight",real(s.weight));
        attr("weight_interpretation","IDWTUP=-4; pb; contribution=LHE_XWGTUP/full_original_source_count; columns are provenance, not variations");
        attr("input_cross_section_pb",real(o.source_sigma));attr("input_cross_section_uncertainty_pb",real(o.source_error));
        attr("source_total_events",std::to_string(o.source_total));attr("source_scalup_gev",real(s.scale));
        attr("pythia_nMPI_including_primary",std::to_string(p.info.nMPI()));
        diagnostics(o,p,s,c.written+1,particle,c);
        const auto hash=writer.write(event);++c.written;
        ledger<<ledger_row(o,s,c.calls,"WRITTEN",c.written,hash,pyweight,converter_weights,"")<<'\n';ledger.flush();particle.flush();
        finalized_source=s.index;
        c.sum_w+=contribution;c.sum_abs_w+=std::abs(contribution);c.sum_w2+=static_cast<long double>(contribution)*contribution;
        if(c.written%10==0)std::cout<<"processed="<<c.consumed<<" written="<<c.written<<" failed="<<c.failed<<std::endl;
      }
      if(c.failed||c.written!=o.events||c.consumed!=o.events){status="PARTIAL";reason="Some requested source inputs did not yield a valid written output";}
    }catch(const std::exception&e){status="PARTIAL";reason=e.what();c.consumed=source->cursor();
      for(const auto&s:source->consumed())if(s.index>finalized_source){
        ledger<<ledger_row(o,s,c.calls,"PROCESSING_FAILED",0,"",p.info.weight(),{},reason)<<'\n';++c.failed;}
    }
    writer.close();ledger.close();particle.close();p.stat();
    require(zh::file_sha(o.authorization)==o.authorization_sha,"Stage authorization receipt changed during shower");
    require(zh::file_sha(o.input)==zh::parse_json(zh::read_file(o.authorization)).at("source_lhe_sha256").string()&&
      zh::file_sha(o.index)==o.index_hash,"Source bytes changed during shower");
    auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    summary(o,c,p,status,reason,readback,elapsed,*source);
    std::cout<<status<<": consumed="<<c.consumed<<" written="<<c.written<<" failed="<<c.failed<<std::endl;
    return status=="PASS"?0:2;
  }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<std::endl;return 2;}
}

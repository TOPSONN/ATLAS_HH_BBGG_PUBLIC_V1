// Reuse unchanged strict Phase6B graph/units/stable-shell physics readback,
// then independently inspect actual ReaderAscii Z/H ancestry and source weights.
#define main phase6b_reader_main
#include "../../../pythia8/src/validate_hepmc3.cxx"
#undef main
#include "ZHAncestry.hxx"
#include "TrackedLHA.hxx"
#include "Json.hxx"
#include <filesystem>

namespace zhreader {
namespace fs=std::filesystem;
struct Request {
  zh::StageRequest stage;
  std::string hepmc,xml,sample,report;
  bool build_info=false;
};
Request parse(int argc,char**argv){
  Request r;
  for(int i=1;i<argc;++i){std::string k=argv[i];if(k=="--build-info"){r.build_info=true;continue;}
    zh::require(i+1<argc,"Missing native reader argument");std::string v=argv[++i];
    if(k=="--input")r.hepmc=v;else if(k=="--source-lhe")r.stage.input=v;
    else if(k=="--source-index")r.stage.index=v;else if(k=="--index-sha256")r.stage.index_sha=v;
    else if(k=="--output")r.stage.output=v;else if(k=="--stage")r.stage.stage=v;
    else if(k=="--authorization")r.stage.authorization=v;else if(k=="--authorization-sha256")r.stage.authorization_sha=v;
    else if(k=="--bridge-sha256")r.stage.bridge_sha=v;else if(k=="--source-sha256")r.stage.source_hash=v;
    else if(k=="--events")r.stage.events=std::stol(v);else if(k=="--source-total")r.stage.total=std::stol(v);
    else if(k=="--seed")r.stage.seed=std::stoi(v);else if(k=="--max-hours")r.stage.max_hours=std::stod(v);
    else if(k=="--max-disk-gb")r.stage.max_disk_gb=std::stod(v);else if(k=="--xml")r.xml=v;
    else if(k=="--sample-id")r.sample=v;else if(k=="--report")r.report=v;
    else throw std::runtime_error("Unknown reader argument: "+k);
  }return r;
}
std::vector<atlas_hh::SourceEvent> load_index(const fs::path& path){
  std::ifstream stream(path);zh::require(stream.good(),"Cannot read trusted source DAT");std::vector<atlas_hh::SourceEvent> result;
  std::string marker;
  while(stream>>marker){atlas_hh::SourceEvent s{};
    zh::require(marker=="E"&&bool(stream>>s.index>>s.hash>>s.nup>>s.process>>s.weight>>s.scale>>s.alpha_qed>>s.alpha_qcd),"Malformed source DAT header");
    zh::require(s.index==long(result.size()+1)&&s.hash.size()==64&&s.nup>0&&s.nup<100000&&std::isfinite(s.weight),"Invalid trusted source DAT identity/count/weight");
    for(int i=0;i<s.nup;++i){atlas_hh::SourceParticle p{};zh::require(bool(stream>>marker>>p.id>>p.status>>p.m1>>p.m2>>p.c1>>p.c2>>p.px>>p.py>>p.pz>>p.e>>p.m>>p.tau>>p.spin)&&marker=="P","Malformed source DAT particle");s.particles.push_back(p);}
    result.push_back(s);zh::require(result.size()<=100,"More than100 source inputs");
  }zh::require(stream.eof()&&result.size()==100,"Trusted source DAT must contain full100 source inputs");return result;
}
std::vector<std::string> block_hashes(const fs::path& path){
  std::ifstream stream(path,std::ios::binary);zh::require(stream.good(),"Cannot read exact raw ASCII blocks");
  std::vector<std::string> result;std::string line,block;
  while(std::getline(stream,line)){zh::require(line.find('\r')==std::string::npos,"Unexpected non-LF native ASCII serialization");
    if(line.rfind("E ",0)==0){if(!block.empty())result.push_back(atlas_hh::Sha256::digest(block));block=line+'\n';}
    else if(line=="HepMC::Asciiv3-END_EVENT_LISTING"){if(!block.empty()){result.push_back(atlas_hh::Sha256::digest(block));block.clear();}}
    else if(!block.empty())block+=line+'\n';
  }zh::require(stream.eof()&&block.empty()&&result.size()<=100,"Incomplete or excessive raw ASCII blocks");return result;
}
void vector_ids(std::ostream&out,const char*marker,const std::vector<int>&ids){out<<marker;for(int id:ids)out<<' '<<id;out<<'\n';}
bool close_number(double a,double b){return std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=1e-13*std::max({1.0,std::abs(a),std::abs(b)});}
void source_resonance_masses(const atlas_hh::SourceEvent&source,const HepMC3::GenEvent&event,const zh::Lineage&lineage){
  const atlas_hh::SourceParticle* h=nullptr;const atlas_hh::SourceParticle* z=nullptr;
  for(const auto&p:source.particles){
    if(p.id==25&&p.status==1){zh::require(!h,"Multiple source H identities in trusted DAT");h=&p;}
    if(p.id==23&&p.status==2){zh::require(!z,"Multiple source Z identities in trusted DAT");z=&p;}
  }
  zh::require(h&&z,"Exact source H/Z identities absent from trusted DAT");
  std::map<int,HepMC3::ConstGenParticlePtr> particles;for(const auto&p:event.particles())particles.emplace(p->id(),p);
  for(const auto&pair:std::vector<std::pair<const atlas_hh::SourceParticle*,int>>{{h,lineage.h},{z,lineage.z}}){
    auto p=particles.at(pair.second);zh::require(p->pid()==pair.first->id,"Source-to-HepMC resonance PDG mismatch");
    const auto& original=*pair.first;
    zh::check_resonance_mass(original.id,original.m,original.m,
      HepMC3::FourVector(original.px,original.py,original.pz,original.e));
    zh::check_resonance_mass(pair.first->id,pair.first->m,p->generated_mass(),p->momentum());
  }
}
void local_resonance_closure(const HepMC3::GenEvent&event,const zh::Lineage&lineage){
  for(const auto&ids:std::vector<std::vector<int>>{lineage.photons,lineage.bottoms}){
    std::map<int,HepMC3::ConstGenParticlePtr> particles;
    for(const auto&p:event.particles())particles.emplace(p->id(),p);
    auto a=particles.at(ids.at(0)),b=particles.at(ids.at(1));
    auto vertex=a->production_vertex();zh::require(vertex&&vertex==b->production_vertex()&&vertex->particles_in().size()==1,"Ambiguous resonance decay vertex");
    auto mother=vertex->particles_in().front();auto sum=a->momentum()+b->momentum();
    auto x=components(sum),y=components(mother->momentum());
    for(int i=0;i<4;++i)zh::require(std::abs(x[i]-y[i])<=1e-5+1e-9*std::max(1.0,std::abs(y[3])),"Resonance birth four-momentum closure failure");
  }
}
int run(const Request&r){
  zh::check_authorization(r.stage,"native_validator_sha256");
  fs::path out=fs::weakly_canonical(r.stage.output),input=fs::weakly_canonical(r.hepmc);
  zh::require(input==out/"shower.hepmc3"&&fs::weakly_canonical(r.report)==out/"zh_hepmc_validation.json","Reader input/report must match exact authorized stage paths");
  long count=0,passed=0;bool assessing=false;std::string original_sha;
  try{
  original_sha=zh::file_sha(input);
  std::vector<std::string> args{"generic_reader","--input",r.hepmc,"--xml",r.xml,"--events",std::to_string(r.stage.events),
    "--source-sha256",r.stage.source_hash,"--sample-id",r.sample,"--seed",std::to_string(r.stage.seed),"--report",(out/"generic_physics_validation.json").string()};
  std::vector<char*> pointers;for(auto&value:args)pointers.push_back(value.data());
  zh::require(phase6b_reader_main(pointers.size(),pointers.data())==0,"Strict generic ReaderAscii physics validation failed; immutable records retained");
  auto sources=load_index(r.stage.index);auto hashes=block_hashes(input);
  zh::require(hashes.size()==std::size_t(r.stage.events),"Raw block count does not match authorized prefix/full stage");
  std::ofstream index(out/"input_event_index.dat"),truth(out/"zh_truth_index.dat"),rows(out/"hepmc_ancestry.jsonl");
  zh::require(index.good()&&truth.good()&&rows.good(),"Cannot create native verified indices");
  index<<"ATLAS_DELPHES_INPUT_V1\n";truth<<"ATLAS_ZH_TRUTH_V1\n";
  HepMC3::ReaderAscii reader(r.hepmc);long double raw_sum=0,info_sum=0,converter_sum=0;
  while(true){HepMC3::GenEvent event;if(!reader.read_event(event)||reader.failed())break;++count;
    assessing=true;
    zh::require(count<=r.stage.events&&event.event_number()==count,"Nonsequential/excessive actual reader event");
    const auto&s=sources.at(count-1);auto attr=[&](const std::string&key){return event.attribute_as_string(key);};
    zh::require(attr("source_lhe_profile")=="ZH_ZBB_STABLE_H"&&attr("source_event_index")==std::to_string(s.index)&&
      attr("source_event_content_hash")==s.hash&&attr("source_file_sha256")==r.stage.source_hash&&
      attr("source_sample_id")==r.sample&&attr("pythia_seed")==std::to_string(r.stage.seed)&&
      attr("source_total_events")=="100","Exact source mapping/header profile mismatch");
    const auto&weights=event.weights();const auto&names=event.run_info()->weight_names();
    zh::require(weights.size()>=4&&weights.size()<=259&&names.size()==weights.size()&&
      names[0]=="input_contribution_pb"&&names[1]=="LHE_XWGTUP_pb"&&names[2]=="Pythia_Info_weight_pb","Actual named weight vector missing");
    for(std::size_t i=3;i<weights.size();++i)zh::require(names[i]=="converter_weight_"+std::to_string(i-3)+"_pb","Converter vector name/index mismatch");
    zh::require(close_number(weights[0],s.weight/100.0)&&close_number(weights[1],s.weight)&&close_number(weights[2],weights[3]),"Actual signed source/denominator/Info-converter closure mismatch");
    auto graph=zh::hepmc_graph(event);auto lineage=zh::inspect(graph);local_resonance_closure(event,lineage);
    source_resonance_masses(s,event,lineage);
    raw_sum+=weights[1];info_sum+=weights[2];converter_sum+=weights[3];
    index<<"E "<<count<<' '<<event.event_number()<<' '<<hashes.at(count-1)<<' '<<s.index<<' '<<s.hash<<' '
      <<atlas_hh::real(weights[0])<<' '<<atlas_hh::real(s.weight)<<" 100 "<<event.particles().size()<<' '<<weights.size()<<"\nW";
    for(double value:weights){index<<' '<<atlas_hh::real(value);}index<<'\n';
    for(const auto&p:event.particles()){
      auto vertex=p->production_vertex();auto v=vertex?vertex->position():HepMC3::FourVector();
      const auto&k=p->momentum();
      index<<"P "<<p->id()<<' '<<p->pid()<<' '<<p->status()<<' '<<atlas_hh::real(k.px())<<' '<<atlas_hh::real(k.py())<<' '
        <<atlas_hh::real(k.pz())<<' '<<atlas_hh::real(k.e())<<' '<<atlas_hh::real(p->generated_mass())<<' '<<(vertex?vertex->id():0)<<' '
        <<atlas_hh::real(v.x())<<' '<<atlas_hh::real(v.y())<<' '<<atlas_hh::real(v.z())<<' '<<atlas_hh::real(v.t())<<'\n';
    }
    truth<<"E "<<count<<' '<<s.index<<' '<<lineage.h<<' '<<lineage.z<<' '<<lineage.photons.size()<<' '<<lineage.final_photons.size()<<' '<<lineage.bottoms.size()<<'\n';
    vector_ids(truth,"H",lineage.photons);vector_ids(truth,"G",lineage.final_photons);vector_ids(truth,"B",lineage.bottoms);
    rows<<"{\"source_event_index\":"<<s.index<<",\"source_event_content_hash\":"<<atlas_hh::quoted(s.hash)<<",\"event_block_sha256\":"<<atlas_hh::quoted(hashes.at(count-1))
      <<",\"lineage\":"<<zh::lineage_json(lineage)<<",\"source_total_events\":100,\"weight_names\":[";
    for(std::size_t i=0;i<names.size();++i){if(i)rows<<',';rows<<atlas_hh::quoted(names[i]);}
    rows<<"],\"weights_pb\":[";for(std::size_t i=0;i<weights.size();++i){if(i)rows<<',';rows<<atlas_hh::real(weights[i]);}
    rows<<"],\"physical_BR_adoption\":\"UNKNOWN_NOT_APPLIED\",\"exclusive_physical_normalization\":\"BLOCKED\"}\n";
    zh::require(index.good()&&truth.good()&&rows.good(),"Verified index/ancestry write failed");
    ++passed;assessing=false;
  }
  reader.close();index.close();truth.close();rows.close();zh::require(count==r.stage.events,"Actual ancestry ReaderAscii count mismatch");
  zh::require(zh::file_sha(input)==original_sha,"HepMC input changed during actual readback");
  zh::check_authorization(r.stage,"native_validator_sha256");
  std::ofstream report(r.report);zh::require(report.good(),"Cannot create actual ancestry validation receipt");
  report<<"{\"schema_version\":1,\"validation_status\":\"PASS_ZH_HEPMC_RECORDS\",\"N_readback\":"<<count
    <<",\"N_passed_validation\":"<<count<<",\"N_failed_validation\":0,\"source_total_events\":100,\"source_file_sha256\":"<<atlas_hh::quoted(r.stage.source_hash)
    <<",\"decompressed_file_sha256\":"<<atlas_hh::quoted(original_sha)<<",\"input_index_sha256\":"<<atlas_hh::quoted(zh::file_sha(out/"input_event_index.dat"))
    <<",\"truth_index_sha256\":"<<atlas_hh::quoted(zh::file_sha(out/"zh_truth_index.dat"))<<",\"generic_physics_report_sha256\":"<<atlas_hh::quoted(zh::file_sha(out/"generic_physics_validation.json"))
    <<",\"raw_LHE_weight_sum_pb\":"<<atlas_hh::real(static_cast<double>(raw_sum))<<",\"Info_weight_sum_pb\":"<<atlas_hh::real(static_cast<double>(info_sum))
    <<",\"converter_nominal_weight_sum_pb\":"<<atlas_hh::real(static_cast<double>(converter_sum))
    <<",\"Higgs_BR_adoption\":\"UNKNOWN_NOT_APPLIED\",\"exclusive_physical_normalization\":\"BLOCKED\",\"source_Z_BR_reapplied\":false"
    <<",\"resonance_mass_check\":\"Independent source and HMC root invariant mass-squared vs exact source mass token; HMC generated mass token compared separately; Lorentz recoil allowed; no p4 identity/repair\",\"resonance_generated_mass_atol_GeV\":1e-5,\"resonance_generated_mass_rtol\":1e-9"
    <<",\"resonance_invariant_mass_squared_atol_GeV2\":1e-6,\"resonance_invariant_mass_squared_rtol\":5e-9,\"resonance_invariant_mass_squared_scale\":\"max(E^2,|p|^2,m_source^2,1GeV^2): frozen PhaseF printed-LHE precision and binary64 cancellation bound\""
    <<",\"pythia_version\":\"8.317\",\"hepmc3_version\":\"3.3.1\",\"hepmc3_reported_version\":"<<atlas_hh::quoted(HepMC3::version())<<"}\n";
  zh::require(report.good(),"Actual ancestry receipt write failed");return 0;
  }catch(const std::exception&error){
    std::ofstream report(r.report);
    if(report.good())report<<"{\"schema_version\":1,\"validation_status\":\"FAIL_ZH_HEPMC_RECORDS\",\"N_readback\":"<<count
      <<",\"N_passed_validation\":"<<passed<<",\"N_failed_validation\":"<<(assessing?1:0)<<",\"N_not_assessed\":"<<std::max(0L,r.stage.events-count)
      <<",\"fatal_error\":"<<atlas_hh::quoted(error.what())<<",\"decompressed_file_sha256\":"<<(original_sha.empty()?"null":atlas_hh::quoted(original_sha))
      <<",\"source_total_events\":100,\"count_scope\":\"Actual second ReaderAscii ancestry pass; separate generic physics report retains its own observed counts\""
      <<",\"exclusive_physical_normalization\":\"BLOCKED\",\"physical_BR_adoption\":\"UNKNOWN_NOT_APPLIED\"}\n";
    throw;
  }
}
}
int main(int argc,char**argv){
  try{auto request=zhreader::parse(argc,argv);
    if(request.build_info){std::cout<<"{\"pythia_version_integer\":"<<PYTHIA_VERSION_INTEGER<<",\"hepmc3_version\":"<<atlas_hh::quoted(HepMC3::version())<<",\"cxx_standard\":"<<__cplusplus<<"}\n";return 0;}
    return zhreader::run(request);
  }catch(const std::exception&error){std::cerr<<"BLOCKED_OR_FAILED: "<<error.what()<<'\n';return 2;}
}

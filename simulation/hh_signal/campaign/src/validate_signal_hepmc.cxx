// Independent installed ReaderAscii readback, after the generic physics reader.
#include "SignalGraph.hxx"
#include "TrackedLHA.hxx"
#include <fstream>
#include <iostream>
#include <filesystem>
using signal::require;using atlas_hh::quoted;using atlas_hh::real;
std::vector<atlas_hh::SourceEvent> sources(const std::string&path){
 std::ifstream in(path);std::vector<atlas_hh::SourceEvent> rows;std::string k;
 while(in>>k){atlas_hh::SourceEvent s{};require(k=="E"&&bool(in>>s.index>>s.hash>>s.nup>>s.process>>s.weight>>s.scale>>s.alpha_qed>>s.alpha_qcd),"invalid source index");
  require(s.nup==4&&s.index==long(rows.size()+1),"wrong production source topology/index");
  for(int i=0;i<s.nup;++i){atlas_hh::SourceParticle p{};require(bool(in>>k>>p.id>>p.status>>p.m1>>p.m2>>p.c1>>p.c2>>p.px>>p.py>>p.pz>>p.e>>p.m>>p.tau>>p.spin)&&k=="P","truncated source tuple");s.particles.push_back(p);}
  rows.push_back(s);
 }return rows;
}
std::vector<std::string> blocks(const std::string&path){
 std::ifstream in(path,std::ios::binary);std::string line,current;std::vector<std::string> out;bool ended=false;
 while(std::getline(in,line)){line+='\n';require(line.size()<8*1024*1024,"unbounded ASCII line");
  if(line.rfind("E ",0)==0){if(!current.empty())out.push_back(atlas_hh::Sha256::digest(current));current=line;}
  else if(line.rfind("HepMC::Asciiv3-END_EVENT_LISTING",0)==0){require(!ended&&!current.empty(),"bad native trailer");out.push_back(atlas_hh::Sha256::digest(current));current.clear();ended=true;}
  else if(!current.empty())current+=line;
  require(current.size()<32*1024*1024&&out.size()<=1000,"unbounded event/file");
 }require(ended&&current.empty(),"incomplete native ASCII file");return out;
}
int main(int argc,char**argv){
 long count=0;
 try{
  require(argc==8,"fixed reader input/source/output/count/total/hash/receipt arguments required");
  const std::string input=argv[1],source=argv[2],output=argv[3],original=argv[6];
  const int expected=std::stoi(argv[4]),total=std::stoi(argv[5]);
  auto auth=zh::parse_json(zh::read_file(argv[7]));
  require(auth.at("source_sha256").string()==original&&auth.at("events").number()==expected&&auth.at("original_count").number()==total,"stale reader authorization");
  auto raw=sources(source);require(raw.size()==std::size_t(total),"original source N mismatch");
  auto hashes=blocks(input);require(hashes.size()==std::size_t(expected),"actual HepMC block count mismatch");
  require(!std::filesystem::exists(output),"reader output exists");std::filesystem::create_directory(output);
  std::ofstream index(output+"/input_event_index.dat"),truth(output+"/signal_truth.dat"),ancestry(output+"/hepmc_ancestry.jsonl");
  index<<"ATLAS_DELPHES_INPUT_V1\n";truth<<"S01_SIGNAL_TRUTH_V1\n";
  HepMC3::ReaderAscii reader(input);long double sum=0,info=0,converter=0;double max_info_ratio=0;
  while(true){HepMC3::GenEvent event;if(!reader.read_event(event)||reader.failed())break;++count;
   require(count<=expected&&event.event_number()==count,"bad native event numbering");const auto&s=raw.at(count-1);
   auto attr=[&](const std::string&k){return event.attribute_as_string(k);};
   require(attr("source_event_index")==std::to_string(count)&&attr("source_event_content_hash")==s.hash&&attr("source_file_sha256")==original&&attr("source_total_events")==std::to_string(total),"source/HepMC bijection failure");
   const auto&w=event.weights();require(w.size()==4&&event.run_info()&&event.run_info()->weight_names().size()==4,"missing weight names/vector");
   for(double v:w)require(std::isfinite(v),"nonfinite auxiliary weight");
   require(std::abs(w[0]-s.weight/total)<1e-15&&w[1]==s.weight&&std::abs(w[2]-s.weight)<1e-12&&w[2]==w[3],"raw/source/Info/converter weight closure failure");
   auto graph=zh::hepmc_graph(event);auto h=signal::inspect(graph);signal::localClosure(event,h);
   const auto lineage=signal::json(h);require(lineage==attr("signal_decay_lineage"),"writer/reader independent ancestry mismatch");
   index<<"E "<<count<<' '<<event.event_number()<<' '<<hashes[count-1]<<' '<<count<<' '<<s.hash<<' '<<real(w[0])<<' '<<real(s.weight)<<' '<<total<<' '<<event.particles().size()<<" 4\nW";
   for(double v:w)index<<' '<<real(v);index<<'\n';
   for(const auto&p:event.particles()){auto vertex=p->production_vertex();auto v=vertex?vertex->position():HepMC3::FourVector();auto k=p->momentum();
    index<<"P "<<p->id()<<' '<<p->pid()<<' '<<p->status()<<' '<<real(k.px())<<' '<<real(k.py())<<' '<<real(k.pz())<<' '<<real(k.e())<<' '<<real(p->generated_mass())<<' '<<(vertex?vertex->id():0)<<' '<<real(v.x())<<' '<<real(v.y())<<' '<<real(v.z())<<' '<<real(v.t())<<'\n';}
   truth<<"E "<<count<<' '<<s.hash<<' '<<h.bb<<' '<<h.gg<<'\n';signal::ids(truth,"G",h.finalPhotons);signal::ids(truth,"B",h.bottoms);
   ancestry<<"{\"source_event_index\":"<<count<<",\"source_event_sha256\":"<<quoted(s.hash)<<",\"hepmc_event_sha256\":"<<quoted(hashes[count-1])<<",\"lineage\":"<<lineage<<",\"H_bb_source_index\":"<<attr("source_H_bb_index")<<",\"H_gammagamma_source_index\":"<<attr("source_H_gammagamma_index")<<",\"weight_vector_pb\":[";
   for(int i=0;i<4;++i){if(i)ancestry<<',';ancestry<<real(w[i]);}ancestry<<"]}\n";
   sum+=w[1];info+=w[2];converter+=w[3];max_info_ratio=std::max(max_info_ratio,std::abs(w[2]/w[1]-1));
  }
  reader.close();require(count==expected,"native signal readback count failure");
  index.close();truth.close();ancestry.close();std::ofstream r(output+"/native_validation.json");
  r<<"{\"status\":\"PASS_ACTUAL_NATIVE_SIGNAL_HEPMC_READBACK\",\"validated_events\":"<<count<<",\"original_source_count\":"<<total<<",\"invalid\":0,\"skipped\":0,\"Hbb_and_Hgammagamma_events\":"<<count<<",\"raw_LHE_weight_sum_pb\":"<<real(double(sum))<<",\"Info_weight_sum_pb\":"<<real(double(info))<<",\"converter_weight_sum_pb\":"<<real(double(converter))<<",\"max_Info_over_LHE_deviation\":"<<real(max_info_ratio)<<",\"source_sha256\":"<<quoted(original)<<",\"HepMC_sha256\":"<<quoted(zh::file_sha(input))<<",\"input_index_sha256\":"<<quoted(zh::file_sha(output+"/input_event_index.dat"))<<",\"truth_index_sha256\":"<<quoted(zh::file_sha(output+"/signal_truth.dat"))<<"}\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<"PHYSICAL_SIGNAL_READER_FAILURE at "<<count<<": "<<e.what()<<'\n';return 2;}
}

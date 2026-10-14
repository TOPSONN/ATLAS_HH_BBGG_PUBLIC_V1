// Synthetic graph/JSON algebra only. No Pythia initialization or next().
#include "ZHAncestry.hxx"
#include "SourceAttempt.hxx"
#include "HepMC3/ReaderAscii.h"
#include "HepMC3/WriterAscii.h"
#include "HepMC3/Attribute.h"
#include <iostream>
#include <sstream>

int main(){
  try{
    auto value=zh::parse_json("{\"events\":100,\"status\":\"METHOD_ONLY\"}");
    zh::require(value.at("events").integer()==100,"Strict JSON integer method failed");
    for(const auto&text:{"{\"x\":1,\"x\":2}","{\"x\":NaN}","{\"x\":01}","{} garbage"}){
      bool rejected=false;try{zh::parse_json(text);}catch(const std::exception&){rejected=true;}zh::require(rejected,"Invalid JSON accepted");}
    zh::Graph graph;
    graph.emplace(1,zh::Node{1,1,2,{}, {}});graph.emplace(2,zh::Node{2,-1,2,{}, {}});
    graph.emplace(3,zh::Node{3,25,2,{1,2}, {}});graph.emplace(4,zh::Node{4,23,2,{1,2}, {}});
    graph.emplace(5,zh::Node{5,22,1,{3}, {}});graph.emplace(6,zh::Node{6,22,1,{3}, {}});
    graph.emplace(7,zh::Node{7,5,2,{4}, {}});graph.emplace(8,zh::Node{8,-5,2,{4}, {}});
    zh::complete_graph(graph);auto lineage=zh::inspect(graph);
    zh::require(lineage.h==3&&lineage.z==4&&lineage.photons.size()==2&&lineage.bottoms.size()==2&&lineage.final_photons.size()==2,"Synthetic routeB lineage method failed");
    auto cycle=graph;cycle.at(1).mothers={5};bool rejected=false;
    try{zh::complete_graph(cycle);}catch(const std::exception&){rejected=true;}zh::require(rejected,"Cycle fixture accepted");
    auto wrong=graph;wrong.at(6).mothers={4};zh::complete_graph(wrong);rejected=false;
    try{zh::inspect(wrong);}catch(const std::exception&){rejected=true;}zh::require(rejected,"Wrong-H fixture accepted");
    auto duplicate=graph;duplicate.at(5).status=2;duplicate.emplace(9,zh::Node{9,22,1,{5}, {}});duplicate.emplace(10,zh::Node{10,22,1,{5}, {}});
    zh::complete_graph(duplicate);rejected=false;try{zh::inspect(duplicate);}catch(const std::exception&){rejected=true;}zh::require(rejected,"Duplicate birth claim fixture accepted");
    zh::StageRequest request;rejected=false;try{zh::check_authorization(request,"native_runner_sha256");}catch(const std::exception&){rejected=true;}zh::require(rejected,"Missing authorization accepted");
    zh::SingleSourceRead reads;reads.begin();reads.permit();rejected=false;
    try{reads.permit();}catch(const std::exception&){rejected=true;}zh::require(rejected&&reads.denied()==1,"Second source read fixture accepted or hidden");reads.begin();reads.permit();
    // An intentionally synthetic in-memory record tests SDK serialization and
    // ancestry API identity only. It is never a generator/physics reference.
    HepMC3::GenEvent toy(HepMC3::Units::GEV,HepMC3::Units::MM);
    auto make=[](int pdg,int status,double energy){auto p=std::make_shared<HepMC3::GenParticle>(HepMC3::FourVector(0,0,0,energy),pdg,status);p->set_generated_mass(energy);return p;};
    auto q=make(1,2,200),qb=make(-1,2,200),h=make(25,2,125),z=make(23,2,91.188);
    auto g1=make(22,1,62.5),g2=make(22,1,62.5),b=make(5,2,45.594),bb=make(-5,2,45.594);
    auto production=std::make_shared<HepMC3::GenVertex>();production->add_particle_in(q);production->add_particle_in(qb);production->add_particle_out(h);production->add_particle_out(z);toy.add_vertex(production);
    auto hd=std::make_shared<HepMC3::GenVertex>();hd->add_particle_in(h);hd->add_particle_out(g1);hd->add_particle_out(g2);toy.add_vertex(hd);
    auto zd=std::make_shared<HepMC3::GenVertex>();zd->add_particle_in(z);zd->add_particle_out(b);zd->add_particle_out(bb);toy.add_vertex(zd);
    toy.add_attribute("simulation_scope",std::make_shared<HepMC3::StringAttribute>("SYNTHETIC_METHOD_ONLY"));
    std::ostringstream serialized;{HepMC3::WriterAscii writer(serialized);writer.set_precision(17);writer.write_event(toy);writer.close();zh::require(!writer.failed(),"Synthetic SDK WriterAscii failed");}
    std::istringstream input(serialized.str());HepMC3::ReaderAscii reader(input);HepMC3::GenEvent loaded;
    zh::require(reader.read_event(loaded)&&!reader.failed()&&loaded.attribute_as_string("simulation_scope")=="SYNTHETIC_METHOD_ONLY","Synthetic ReaderAscii method failed");
    auto actual=zh::inspect(zh::hepmc_graph(loaded));zh::require(actual.photons.size()==2&&actual.bottoms.size()==2,"Synthetic ReaderAscii identity/ancestry method failed");reader.close();
    auto state=zh::parse_json("{\"ticket_id\":\"SYNTHETIC_METHOD_ONLY\",\"deadline_epoch_seconds\":200}");
    auto live=zh::parse_json("{\"status\":\"AUTHORIZED_EXECUTION_IN_PROGRESS\",\"ticket_id\":\"SYNTHETIC_METHOD_ONLY\"}");
    zh::check_live_state(state,live,100);
    for(const auto&wrong_state:{"{\"status\":\"CLOSED\",\"ticket_id\":\"SYNTHETIC_METHOD_ONLY\"}",
                               "{\"status\":\"AUTHORIZED_EXECUTION_IN_PROGRESS\",\"ticket_id\":\"WRONG_METHOD_ID\"}"}){
      rejected=false;try{zh::check_live_state(state,zh::parse_json(wrong_state),100);}catch(const std::exception&){rejected=true;}zh::require(rejected,"Stale/different live-state fixture accepted");}
    rejected=false;try{zh::check_live_state(state,live,200);}catch(const std::exception&){rejected=true;}zh::require(rejected,"Expired live-state fixture accepted");
    zh::check_resonance_mass(25,125,125,HepMC3::FourVector(75,0,0,std::sqrt(125*125+75*75)));
    zh::check_resonance_mass(23,89,89,HepMC3::FourVector(0,0,30,std::sqrt(89*89+30*30)));
    // Synthetic e17.10-scale high-boost rounding: the invariant mass can differ
    // by >10 micro-GeV while the frozen GeV^2 precision bound remains valid.
    const double high_p=6000.123456,high_e=std::sqrt(high_p*high_p+125*125)+3e-7;
    const double high_m=std::sqrt(high_e*high_e-high_p*high_p);
    zh::require(std::isfinite(high_m)&&std::abs(high_m-125)>1e-5,"High-boost method fixture did not exercise source rounding");
    zh::check_resonance_mass(25,125,125,HepMC3::FourVector(0,0,high_p,high_e));
    for(const auto&tuple:std::vector<std::vector<double>>{{25,125,124,125},{25,125,125,124},{23,150,150,150}}){
      rejected=false;try{zh::check_resonance_mass(int(tuple[0]),tuple[1],tuple[2],HepMC3::FourVector(0,0,0,tuple[3]));}
      catch(const std::exception&){rejected=true;}zh::require(rejected,"Wrong resonance mass/window fixture accepted");}
    std::cout<<"{\"status\":\"METHOD_ONLY\",\"new_physics_events\":0,\"next_calls\":0,\"checks\":21,\"ReaderAscii_API\":\"PASS_SYNTHETIC_METHOD_ONLY\"}\n";return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}

// Synthetic content is used only to require explicit failure-path rejection.
// SDK parsing/serialization and table loading do not call init() or next().
#include "BackgroundAncestry.hxx"
#include "SourceAttempt.hxx"
#include "HepMC3/ReaderAscii.h"
#include "HepMC3/WriterAscii.h"
#include "Pythia8Plugins/HepMC3.h"
#include <functional>
#include <iostream>
#include <sstream>
int main(){
  try{
    int checks=0;
    auto rejects=[&](const std::function<void()>& action,const std::string& reason){bool failed=false;
      try{action();}catch(const std::exception&){failed=true;}zh::require(failed,reason);++checks;};
    for(const auto&text:{"{\"x\":1,\"x\":2}","{\"x\":NaN}","{\"x\":01}","{} garbage"})rejects([&]{zh::parse_json(text);},"Malformed receipt accepted");
    zh::Graph graph{{1,{1,1,2,{},{}}},{2,{2,-1,2,{},{}}},{3,{3,25,2,{1,2},{}}},{4,{4,23,2,{1,2},{}}},
      {5,{5,22,1,{3},{}}},{6,{6,22,1,{3},{}}},{7,{7,5,2,{4},{}}},{8,{8,-5,2,{4},{}}}};
    auto cycle=graph;cycle.at(1).mothers={5};rejects([&]{zh::complete_graph(cycle);},"Cycle fixture accepted");
    auto wrong=graph;wrong.at(6).mothers={4};zh::complete_graph(wrong);rejects([&]{zh::inspect(wrong,"zh");},"Wrong H birth accepted");
    auto duplicate=graph;duplicate.at(5).status=2;duplicate.emplace(9,zh::Node{9,22,1,{5},{}});duplicate.emplace(10,zh::Node{10,22,1,{5},{}});
    zh::complete_graph(duplicate);rejects([&]{zh::inspect(duplicate,"zh");},"Duplicate photon birth claim accepted");
    zh::StageRequest request;rejects([&]{zh::check_authorization(request,"native_runner_sha256");},"Missing authorization accepted");
    zh::SingleSourceRead reads;reads.begin();reads.permit();rejects([&]{reads.permit();},"Second source read accepted");zh::require(reads.denied()==1,"Denied source read hidden");
    // Deliberately wrong H decay topology through actual SDK ReaderAscii.
    HepMC3::GenEvent toy;auto make=[](int pdg,int status){return std::make_shared<HepMC3::GenParticle>(HepMC3::FourVector(),pdg,status);};
    auto q=make(1,2),qb=make(-1,2),h=make(25,2),z=make(23,2),g=make(22,1),mu=make(13,1),b=make(5,2),bb=make(-5,2);
    auto production=std::make_shared<HepMC3::GenVertex>();production->add_particle_in(q);production->add_particle_in(qb);production->add_particle_out(h);production->add_particle_out(z);toy.add_vertex(production);
    auto hd=std::make_shared<HepMC3::GenVertex>();hd->add_particle_in(h);hd->add_particle_out(g);hd->add_particle_out(mu);toy.add_vertex(hd);
    auto zd=std::make_shared<HepMC3::GenVertex>();zd->add_particle_in(z);zd->add_particle_out(b);zd->add_particle_out(bb);toy.add_vertex(zd);
    for(const auto&p:toy.particles()){
      p->add_attribute("original_pythia_status",std::make_shared<HepMC3::IntAttribute>(p->status()==1?23:-22));
      p->add_attribute("original_pythia_is_hadron",std::make_shared<HepMC3::IntAttribute>(0));
    }
    std::ostringstream raw;{HepMC3::WriterAscii writer(raw);writer.write_event(toy);writer.close();zh::require(!writer.failed(),"SDK failure-fixture serialization failed");}
    std::istringstream input(raw.str());HepMC3::ReaderAscii reader(input);HepMC3::GenEvent loaded;
    zh::require(reader.read_event(loaded)&&!reader.failed(),"SDK could not parse its failure fixture");
    rejects([&]{zh::inspect(zh::hepmc_graph(loaded),"zh");},"Wrong decay accepted after actual ReaderAscii");reader.close();
    auto state=zh::parse_json("{\"campaign_id\":\"METHOD_ONLY\",\"deadline_epoch_seconds\":200}");
    for(const auto&live:{"{\"status\":\"CLOSED\",\"campaign_id\":\"METHOD_ONLY\"}","{\"status\":\"AUTHORIZED_EXECUTION_IN_PROGRESS\",\"campaign_id\":\"OTHER\"}"})
      rejects([&]{zh::check_live_state(state,zh::parse_json(live),100);},"Stale/different live campaign accepted");
    auto live=zh::parse_json("{\"status\":\"AUTHORIZED_EXECUTION_IN_PROGRESS\",\"campaign_id\":\"METHOD_ONLY\"}");
    rejects([&]{zh::check_live_state(state,live,200);},"Expired native stage accepted");
    for(const auto&v:std::vector<std::vector<double>>{{25,125,124,125},{25,125,125,124},{23,150,150,150},{6,172.5,172.5,172.5}})
      rejects([&]{zh::check_resonance_mass(int(v[0]),v[1],v[2],HepMC3::FourVector(0,0,0,v[3]));},"Wrong resonance mass accepted");
    zh::Graph continuum{{1,{1,1,2,{},{},-21}},{2,{2,-1,2,{},{},-21}},{3,{3,5,2,{1,2},{},-23}},{4,{4,-5,2,{1,2},{},-23}},
      {5,{5,22,1,{1,2},{},23}},{6,{6,21,2,{1,2},{},-23}},{7,{7,22,1,{6},{},51}}};zh::complete_graph(continuum);
    auto absent=continuum;absent.at(5).pythia_status=51;rejects([&]{zh::inspect(absent,"bbgj");},"Absent Born-photon identity accepted");
    auto two=continuum;two.at(7).pythia_status=23;rejects([&]{zh::inspect(two,"bbgj");},"Two Born photons accepted for one-Born profile");
    zh::Graph top{{1,{1,21,2,{},{}}},{2,{2,21,2,{},{}}},{3,{3,25,2,{1,2},{}}},{4,{4,6,2,{1,2},{}}},{5,{5,-6,2,{1,2},{}}},
      {6,{6,22,1,{3},{}}},{7,{7,22,1,{3},{}}},{8,{8,5,2,{4},{}}},{9,{9,24,2,{4},{}}},{10,{10,-5,2,{5},{}}},{11,{11,-24,2,{5},{}}},
      {12,{12,-11,1,{9},{}}},{13,{13,-12,1,{9},{}}},{14,{14,-2,2,{11},{}}},{15,{15,1,2,{11},{}}}};zh::complete_graph(top);
    rejects([&]{zh::inspect(top,"tth");},"Wrong-charge W decay accepted");
    top.at(13).pdg=12;top.at(8).pdg=-5;rejects([&]{zh::inspect(top,"tth");},"Wrong-charge top quark accepted");
    auto missing_top=top;missing_top.at(4).pdg=4;rejects([&]{zh::inspect(missing_top,"tth");},"Missing original top root accepted");
    // Corrupt actual SDK converter output must fail native tuple/graph mapping.
    Pythia8::Pythia table("",false);Pythia8::Event native;native.init("METHOD_ONLY",&table.particleData);native.reset();
    native.append(2212,-12,0,0,3,4,0,0,0,0,100,100,0);native.append(2212,-12,0,0,3,4,0,0,0,0,-100,100,0);
    native.append(25,-22,1,2,5,6,0,0,0,0,0,125,125);native.append(23,23,1,2,0,0,0,0,0,0,0,75,75);
    native.append(22,23,3,3,0,0,0,0,62.5,0,0,62.5,0);native.append(22,23,3,3,0,0,0,0,-62.5,0,0,62.5,0);
    HepMC3::GenEvent converted;HepMC3::Pythia8ToHepMC3 sdk;sdk.set_free_parton_warnings(false);
    zh::require(sdk.fill_next_event(native,&converted,1),"SDK could not construct corrupted mapping fixture");
    converted.particles().back()->set_momentum(HepMC3::FourVector(999,0,0,999));
    rejects([&]{zh::retain_pythia_identity(native,converted);},"Corrupt converter identity accepted");
    rejects([&]{zh::inspect(graph,"UNVALIDATED");},"Unknown profile accepted");
    std::cout<<"{\"status\":\"METHOD_ONLY\",\"synthetic_scope\":\"FAILURE_PATH_ONLY\",\"new_physics_events\":0,\"next_calls\":0,\"checks\":"<<checks<<"}\n";return 0;
  }catch(const std::exception&error){std::cerr<<error.what()<<'\n';return 1;}
}

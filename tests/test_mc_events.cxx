#include "AtlasMCEvents.h"
#include <TFile.h>
#include <TTree.h>
#include <TChain.h>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {
int cases=0;
void check(bool condition,const char* message){++cases;if(!condition)throw std::runtime_error(message);}
template<class Function> void refuses(Function&& operation) {
  bool rejected=false;try{operation();}catch(const std::exception&){rejected=true;}check(rejected,"Unsafe MC schema/input accepted");
}
void fixture(const std::filesystem::path& path,int mode) {
  TFile file(path.c_str(),"RECREATE");
  if(mode==26) {
    TChain chain("analysis","Synthetic persisted forbidden chain");
    // The member deliberately does not exist: rejection must occur by native
    // class before virtual branch introspection attempts to open that member.
    chain.Add("synthetic-chain-member-must-not-be-opened.root");
    if(chain.Write()<=0)throw std::runtime_error("Could not persist synthetic TChain fixture");
    return;
  }
  TTree tree("analysis","Synthetic native MC reconstruction input only");
  Int_t np=2,nj=2,dsid_signed=600001,bad_weight=1;UInt_t run=1,dsid=600001;ULong64_t event=9007199254740993ULL;
  Float_t weight=-1.25F,cross_section=2.5F,sf=.9F,btag_sf=1.F;Double_t double_weight=-2.5;
  Double_t sum_weights=3.25;Int_t truth_photon_n=2,truth_jet_n=2;
  atlas::kinematics::RVec pt{70,60},eta{0,0},phi{0,3.14159265F},energy{70,60},jpt{45,30},jenergy{45,30};
  ROOT::VecOps::RVec<bool> flags{true,false};std::vector<float> wrong{70,60};
  atlas::kinematics::RVec truth_mass{0,0};
  tree.Branch("runNumber",&run);tree.Branch("eventNumber",&event);tree.Branch("photon_n",&np);tree.Branch("jet_n",&nj);
  if(mode!=2) {
    if(mode==3)tree.Branch("channelNumber",&double_weight);
    else if(mode==4 || mode==5)tree.Branch("channelNumber",&dsid_signed);
    else tree.Branch("channelNumber",&dsid);
  }
  if(mode!=6) {
    if(mode==1)tree.Branch("mcWeight",&double_weight);
    else if(mode==7)tree.Branch("mcWeight",&bad_weight);
    else tree.Branch("mcWeight",&weight);
  }
  if(mode==8)tree.Branch("photon_pt",&wrong);else tree.Branch("photon_pt",&pt);
  tree.Branch("photon_eta",&eta);if(mode!=9)tree.Branch("photon_phi",&phi);tree.Branch("photon_e",&energy);
  tree.Branch("jet_pt",&jpt);tree.Branch("jet_eta",&eta);tree.Branch("jet_phi",&phi);tree.Branch("jet_e",&jenergy);
  if(mode!=10)for(auto name:{"photon_isTightID","photon_isLooseID","photon_isTightIso","photon_isLooseIso"})tree.Branch(name,&flags);
  tree.Branch("crossSection",&cross_section);
  tree.Branch("sum_of_weights",&sum_weights);tree.Branch("ScaleFactor_PHOTON",&sf);tree.Branch("ScaleFactor_BTAG",&btag_sf);
  if(mode==11)tree.Branch("scaleFactor_TEST",&bad_weight);else tree.Branch("scaleFactor_TEST",&sf);
  if(mode==4)dsid_signed=-1;
  if(mode==12)np=3;
  if(mode==13)flags={true};
  if(mode==14)weight=std::numeric_limits<Float_t>::infinity();
  if(mode==15)dsid=600002;
  if(mode>=19) {
    tree.Branch("truth_photon_n",&truth_photon_n);tree.Branch("truth_jet_n",&truth_jet_n);
    if(mode==21)tree.Branch("truth_photon_pt",&wrong);else tree.Branch("truth_photon_pt",&pt);
    tree.Branch("truth_photon_eta",&eta);if(mode!=20)tree.Branch("truth_photon_phi",&phi);
    tree.Branch("truth_jet_pt",&jpt);tree.Branch("truth_jet_eta",&eta);tree.Branch("truth_jet_phi",&phi);
    if(mode==24)tree.Branch("truth_jet_m",&wrong);else tree.Branch("truth_jet_m",&truth_mass);
    if(mode==22)truth_photon_n=3;
    if(mode==23)truth_mass={0};
    if(mode==25){truth_mass={-.0245F,.0141F};btag_sf=-1.F;}
  }
  for(int index=0;index<3;++index) {
    if(mode==16)weight=index==0?-1.F:(index==1?2.F:0.F);
    tree.Fill();if(mode!=17)++event;
  }
  if(mode==18) {
    TTree friend_tree("friend","Synthetic forbidden friend");friend_tree.Branch("n",&np);friend_tree.Fill();tree.AddFriend(&friend_tree);friend_tree.Write();
  }
  tree.Write();
}
}
int main() {
  try {
    const auto parent=std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR)/"mc_events_fixtures";
    const auto directory=parent/std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    std::filesystem::create_directories(directory);
    for(int mode=0;mode<27;++mode)fixture(directory/(std::to_string(mode)+".root"),mode);
    atlas::mc::Reader reader(directory/"0.root",600001);check(reader.entries()==3,"MC entry metadata incorrect");
    const auto event=reader.read(0);check(event.dsid==600001&&event.reconstructed.event==9007199254740993ULL,"MC same-event identity precision lost");
    check(event.generator_weight==-1.25&&event.reconstructed.photon_pt.size()==2,"MC Float_t negative weight/native RVec binding wrong");
    check(event.diagnostics.at("crossSection")==2.5&&std::abs(event.diagnostics.at("scaleFactor_TEST")-.9)<1e-7,"Diagnostic scalars changed/applied");
    check(event.diagnostics.at("sum_of_weights")==3.25&&std::abs(event.diagnostics.at("ScaleFactor_PHOTON")-.9)<1e-7,"Actual native normalization/uppercase SF fields missing");
    check(event.photon_flag_available.at("photon_isTightID")&&event.reconstructed.tight_id.size()==2,"Optional native photon flags lost");
    check(reader.read(2).reconstructed.event==9007199254740995ULL,"MC explicit entry order incorrect");
    atlas::mc::Reader twice(directory/"1.root",600001);check(twice.read(0).generator_weight==-2.5,"MC Double_t generator weight binding wrong");
    atlas::mc::Reader signed_channel(directory/"5.root",600001);check(signed_channel.read(0).dsid==600001,"Audited positive Int_t DSID binding wrong");
    atlas::mc::Reader no_flags(directory/"10.root",600001);
    check(!no_flags.read(0).photon_flag_available.at("photon_isTightID"),"Absent flag silently inferred");
    atlas::mc::Reader signs(directory/"16.root",600001);
    check(signs.read(0).generator_weight==-1&&signs.read(1).generator_weight==2&&signs.read(2).generator_weight==0,"Negative/positive/zero generator weights changed");
    check(!event.truth_photons.available&&!event.truth_jets.available,"Absent truth silently inferred");
    atlas::mc::Reader truth_reader(directory/"19.root",600001);const auto truth=truth_reader.read(0);
    check(truth.truth_photons.available&&truth.truth_photons.count==2&&truth.truth_photons.pt.size()==2,"Native same-entry truth photons missing");
    check(truth.truth_jets.available&&truth.truth_jets.mass_available&&truth.truth_jets.mass.size()==2&&!truth.truth_jets.energy_available,"Truth jet mass/energy availability invented");
    check(!truth.truth_photons.energy_available&&!truth.truth_photons.mass_available,"Truth photon mass or energy invented");
    atlas::mc::Reader signed_mass_reader(directory/"25.root",600001);const auto signed_mass=signed_mass_reader.read(0);
    check(signed_mass.truth_jets.mass[0]==-.0245F&&signed_mass.diagnostics.at("ScaleFactor_BTAG")==-1,"Signed native truth mass or negative diagnostic SF was changed");
    refuses([&]{reader.read(-1);});refuses([&]{reader.read(3);});
    refuses([&]{atlas::mc::Reader r("root://example.invalid/input.root",600001);});
    refuses([&]{atlas::mc::Reader r(directory/"absent.root",600001);});
    refuses([&]{atlas::mc::Reader r(directory/"0.root",0);});
    refuses([&]{atlas::mc::Reader r(directory/"0.root",600002);r.read(0);});
    for(int mode:{2,3,6,7,8,9,11,18,20,21,24})refuses([&]{atlas::mc::Reader r(directory/(std::to_string(mode)+".root"),600001);});
    for(int mode:{4,12,13,14,15,22,23})refuses([&]{atlas::mc::Reader r(directory/(std::to_string(mode)+".root"),600001);r.read(0);});
    bool chain_rejected_by_class=false;
    try{atlas::mc::Reader r(directory/"26.root",600001);}
    catch(const std::exception& error){chain_rejected_by_class=std::string(error.what()).find("exact TTree")!=std::string::npos;}
    check(chain_rejected_by_class,"Persisted TChain was not rejected before native branch introspection");
    std::ofstream marker(parent/"current_fixture_path.txt");marker<<directory.string()<<'\n';marker.close();
    std::cout<<"PASS native same-entry MC reader cases="<<cases<<"; fixtures="<<directory<<'\n';
  }catch(const std::exception& error){std::cerr<<"FAIL: "<<error.what()<<'\n';return 1;}
}

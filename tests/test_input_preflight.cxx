#include "AtlasInputPreflight.h"
#include <TBranch.h>
#include <TChain.h>
#include <TDirectory.h>
#include <TFile.h>
#include <TNamed.h>
#include <TObjArray.h>
#include <TTree.h>
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#if defined(__unix__)
#include <sys/wait.h>
#include <unistd.h>
#endif
#ifndef ATLAS_STEP1_OUTPUT_DIR
#define ATLAS_STEP1_OUTPUT_DIR "."
#endif

namespace {
using atlas::input_preflight::EvidenceKind;
int checks=0,rejections=0;
void check(bool condition,const char* message) { ++checks;if(!condition)throw std::runtime_error(message); }
template<class Operation> void refuses(Operation&& operation,const std::string& reason="") {
  bool refused=false;std::string observed="accepted";
  try{operation();}catch(const std::exception& error) {
    observed=error.what();
    refused=reason.empty() || std::string(error.what()).find(reason)!=std::string::npos;
  }
  ++checks;if(!refused)throw std::runtime_error("Unsafe preflight guard expected '"+reason+"', observed '"+observed+"'");++rejections;
}
std::string text(const std::filesystem::path& path) {
  std::ifstream stream(path,std::ios::binary);return {std::istreambuf_iterator<char>(stream),{}};
}
enum class Mode { Good, Missing, WrongVector, WrongWeight, WrongDsid, Empty, Friend,
                  NestedFriend, External, NestedExternal, NestedGood, NoAnalysis };
void fixture(const std::filesystem::path& path,Mode mode) {
  TFile file(path.c_str(),"RECREATE");
  Int_t n=2,integer_weight=1,auxiliary=3;UInt_t run=1,dsid=mode==Mode::WrongDsid?600002:600001;
  ULong64_t event=9007199254740993ULL;Float_t weight=-1.25F,extra=.75F;
  atlas::kinematics::RVec pt{70,60},eta{0,0},phi{0,3.14159265F},energy{70,60};
  std::vector<float> wrong{70,60};
  TTree tree(mode==Mode::NoAnalysis?"other":"analysis","SYNTHETIC_FIXTURE only");
  tree.Branch("photon_n",&n);tree.Branch("jet_n",&n);tree.Branch("runNumber",&run);tree.Branch("eventNumber",&event);
  tree.Branch("channelNumber",&dsid);
  if(mode==Mode::WrongWeight)tree.Branch("mcWeight",&integer_weight);else tree.Branch("mcWeight",&weight);
  if(mode==Mode::WrongVector)tree.Branch("photon_pt",&wrong);else tree.Branch("photon_pt",&pt);
  tree.Branch("photon_eta",&eta);if(mode!=Mode::Missing)tree.Branch("photon_phi",&phi);tree.Branch("photon_e",&energy);
  tree.Branch("jet_pt",&pt);tree.Branch("jet_eta",&eta);tree.Branch("jet_phi",&phi);tree.Branch("jet_e",&energy);
  tree.Branch("unrecognized_scalar",&extra);
  if(mode==Mode::External)tree.GetBranch("photon_pt")->SetFile((path.parent_path()/"synthetic_external.root").c_str());
  if(mode==Mode::NestedExternal || mode==Mode::NestedGood) {
    auto* parent=tree.Branch("container",&auxiliary,"container/I");
    auto* child=tree.Branch("nested_value",&auxiliary,"nested_value/I");
    tree.GetListOfBranches()->Remove(child);parent->GetListOfBranches()->Add(child);
    if(mode==Mode::NestedExternal)child->SetFile((path.parent_path()/"synthetic_nested_external.root").c_str());
  }
  if(mode!=Mode::Empty)for(int index=0;index<3;++index){tree.Fill();++event;}
  TTree friend_tree("friend","SYNTHETIC_FIXTURE friend");friend_tree.Branch("n",&n);friend_tree.Fill();
  if(mode==Mode::Friend){tree.AddFriend(&friend_tree);friend_tree.Write();}
  tree.Write();
  auto* directory=file.mkdir("nested");directory->cd();
  TTree auxiliary_tree("metadata_tree","SYNTHETIC_FIXTURE auxiliary native tree");
  auxiliary_tree.Branch("auxiliary",&auxiliary);auxiliary_tree.Fill();
  if(mode==Mode::NestedFriend)auxiliary_tree.AddFriend(&friend_tree);
  auxiliary_tree.Write();file.cd();
  TNamed label("scope_label","SYNTHETIC_FIXTURE");label.Write();
}
void recovered_fixture(const std::filesystem::path& path) {
#if defined(__unix__)
  const auto pid=fork();if(pid<0)throw std::runtime_error("Cannot fork the synthetic unclean-writer fixture");
  if(pid==0) {
    auto* file=TFile::Open(path.c_str(),"RECREATE");
    if(!file || file->IsZombie())std::_Exit(2);
    auto* tree=new TTree("analysis","SYNTHETIC_FIXTURE intentionally unclean writer");
    Int_t value=7;tree->Branch("value",&value);tree->Fill();
    if(tree->AutoSave("FlushBaskets")<=0)std::_Exit(3);
    file->Flush();std::_Exit(0); // Deliberately omit Close(), as a crashed writer would.
  }
  int status=0;if(waitpid(pid,&status,0)!=pid || !WIFEXITED(status) || WEXITSTATUS(status)!=0)
    throw std::runtime_error("Synthetic unclean writer failed");
#else
  (void)path;throw std::runtime_error("The recovered-file fixture requires the declared Ubuntu WSL test environment");
#endif
}
}
int main() {
  try {
    const auto parent=std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR)/"input_preflight_fixtures";
    const auto directory=parent/std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    std::filesystem::create_directories(directory);
    const auto good=directory/"good.root";fixture(good,Mode::Good);
    const auto result=atlas::input_preflight::inspect_local_file(good,600001,EvidenceKind::SyntheticFixture);
    check(result.analysis_entries==3 && result.expected_dsid==600001,"Native analysis metadata or expected DSID altered");
    check(result.trees.size()==2,"Recursive native tree inventory incomplete");
    bool nested=false,unknown=false,scope=false;
    for(const auto& tree:result.trees)nested|=tree.path=="nested/metadata_tree" && tree.entries==1;
    for(const auto& branch:result.branches)unknown|=branch.path=="unrecognized_scalar" && branch.native_type=="Float_t";
    for(const auto& key:result.keys)scope|=key.path=="scope_label" && key.native_class=="TNamed";
    check(nested&&unknown&&scope,"Actual nested keys/extra native branches not recorded");
    check(result.reader_bindings.size()>=14,"Unchanged MC Reader native type contract not reused");
    const auto output=directory/"metadata_output";atlas::input_preflight::write_new_outputs(result,output);
    const auto summary=text(output/"summary.json");
    check(summary.find("\"scope\": \"SYNTHETIC_FIXTURE\"")!=std::string::npos,"Synthetic scope not explicit");
    check(summary.find("\"event_entries_read\": 0")!=std::string::npos && summary.find("\"actual_dsid_values\": \"NOT_EVALUATED\"")!=std::string::npos,"Metadata incorrectly promoted to event identity validation");
    for(const auto* filename:{"keys.csv","trees.csv","branches.csv","reader_bindings.csv"})check(std::filesystem::file_size(output/filename)>0,"Inventory output missing");
    refuses([&]{atlas::input_preflight::write_new_outputs(result,output);},"already exists");
    check(text(output/"summary.json")==summary,"Existing preflight evidence was overwritten");
    const auto wrong_dsid=directory/"wrong_event_dsid.root";fixture(wrong_dsid,Mode::WrongDsid);
    const auto untested=atlas::input_preflight::inspect_local_file(wrong_dsid,600001,EvidenceKind::SyntheticFixture);
    check(untested.analysis_entries==3,"Metadata-only gate unexpectedly reads actual event DSID");
    refuses([&]{atlas::mc::Reader reader(wrong_dsid,600001);reader.read(0);},"DSID");
    const auto nested_good=directory/"nested_good.root";fixture(nested_good,Mode::NestedGood);
    const auto nested_result=atlas::input_preflight::inspect_local_file(nested_good,600001,EvidenceKind::SyntheticFixture);
    bool nested_branch=false;for(const auto& branch:nested_result.branches)nested_branch|=branch.path=="container/nested_value" && branch.native_type=="Int_t";
    check(nested_branch,"Recursive physical branch inventory omitted the persisted child");
    const std::vector<std::pair<Mode,std::string>> unsafe{
      {Mode::Missing,""},{Mode::WrongVector,""},{Mode::WrongWeight,""},{Mode::Empty,"Empty"},
      {Mode::Friend,"Friend"},{Mode::NestedFriend,"Friend"},{Mode::External,"External branch"},
      {Mode::NestedExternal,"External branch"},{Mode::NoAnalysis,""}};
    for(std::size_t index=0;index<unsafe.size();++index) {
      const auto path=directory/("rejection_"+std::to_string(index)+".root");fixture(path,unsafe[index].first);
      refuses([&]{atlas::input_preflight::inspect_local_file(path,600001,EvidenceKind::SyntheticFixture);},unsafe[index].second);
    }
    const auto chain_path=directory/"chain.root";
    {TFile file(chain_path.c_str(),"RECREATE");TChain chain("analysis","SYNTHETIC_FIXTURE forbidden chain");
      chain.Add("synthetic-chain-member-must-not-be-opened.root");check(chain.Write()>0,"Persisted chain fixture failed");}
    refuses([&]{atlas::input_preflight::inspect_local_file(chain_path,600001,EvidenceKind::SyntheticFixture);},"exact TTree");
    const auto nested_chain_path=directory/"nested_chain.root";
    {TFile file(nested_chain_path.c_str(),"RECREATE");auto* nested_directory=file.mkdir("nested");nested_directory->cd();
      TChain chain("auxiliary","SYNTHETIC_FIXTURE nested forbidden chain");chain.Add("synthetic-chain-member-must-not-be-opened.root");chain.Write();}
    refuses([&]{atlas::input_preflight::inspect_local_file(nested_chain_path,600001,EvidenceKind::SyntheticFixture);},"exact TTree");
    const auto corrupt=directory/"zombie.root";{std::ofstream stream(corrupt);stream<<"SYNTHETIC_FIXTURE invalid ROOT header\n";}
    refuses([&]{atlas::input_preflight::inspect_local_file(corrupt,600001,EvidenceKind::SyntheticFixture);},"Zombie");
    const auto recovered=directory/"recovered.root";recovered_fixture(recovered);
    {TFile file(recovered.c_str(),"READ");check(!file.IsZombie()&&file.TestBit(TFile::kRecovered),"Unclean synthetic writer did not create a genuinely recovered ROOT file");}
    refuses([&]{atlas::input_preflight::inspect_local_file(recovered,600001,EvidenceKind::SyntheticFixture);},"Recovered");
    refuses([&]{atlas::input_preflight::inspect_local_file("root://example.invalid/input.root",600001,EvidenceKind::SyntheticFixture);},"Remote");
    refuses([&]{atlas::input_preflight::inspect_local_file(directory/"absent.root",600001,EvidenceKind::SyntheticFixture);},"regular");
    refuses([&]{atlas::input_preflight::inspect_local_file(directory,600001,EvidenceKind::SyntheticFixture);},"regular");
    refuses([&]{atlas::input_preflight::inspect_local_file(good,0,EvidenceKind::SyntheticFixture);},"positive");
    std::ofstream marker(parent/"current_fixture_path.txt");marker<<directory.string()<<'\n';
    std::cout<<"PASS SYNTHETIC_FIXTURE metadata-only preflight checks="<<checks<<" rejections="<<rejections
      <<" event_entries_read_by_preflight=0 fixtures="<<directory<<'\n';
  }catch(const std::exception& error){std::cerr<<"FAIL: "<<error.what()<<'\n';return 1;}
}

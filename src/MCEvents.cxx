#include "AtlasMCEvents.h"
#include <TFile.h>
#include <TTree.h>
#include <TBranch.h>
#include <TClass.h>
#include <TDataType.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <set>
#include <stdexcept>

namespace atlas::mc {
namespace {
std::unique_ptr<TFile> open_local(const std::filesystem::path& input) {
  if(input.string().find("://")!=std::string::npos || !std::filesystem::is_regular_file(input))
    throw std::invalid_argument("Only an existing regular local MC file is allowed");
  std::unique_ptr<TFile> file(TFile::Open(std::filesystem::canonical(input).c_str(),"READ"));
  if(!file || file->IsZombie() || file->IsWritable())throw std::runtime_error("Corrupt or writable MC ROOT file");
  return file;
}
std::string branch_type(TTree& tree,const std::string& name) {
  auto* branch=tree.GetBranch(name.c_str());if(!branch)throw std::runtime_error("Missing MC branch: "+name);
  TClass* cls=nullptr;EDataType type=kOther_t;
  if(branch->GetExpectedType(cls,type)!=0)throw std::runtime_error("Unresolved MC branch type: "+name);
  std::string result=cls?cls->GetName():TDataType::GetTypeName(type);
  result.erase(std::remove(result.begin(),result.end(),' '),result.end());
  if(result=="Int_t")result="int";
  if(result=="UInt_t")result="unsignedint";
  if(result=="ULong64_t")result="unsignedlonglong";
  if(result=="Float_t")result="float";
  if(result=="Double_t")result="double";
  return result;
}
void require(TTree& tree,const std::string& name,const std::string& type) {
  const auto actual=branch_type(tree,name);
  if(actual!=type)throw std::runtime_error("Incompatible native MC branch type: "+name+"="+actual);
}
TTree* checked_tree(TFile& file,const std::filesystem::path& input) {
  TTree* tree=nullptr;file.GetObject("analysis",tree);if(!tree)throw std::runtime_error("MC analysis TTree absent");
  // Reject persisted chains/subclasses before any tree introspection can load
  // an external member. This reader admits exactly one native local TTree.
  if(tree->IsA()!=TTree::Class())throw std::runtime_error("MC analysis must be an exact TTree; chains and subclasses forbidden");
  if(tree->GetListOfFriends() && tree->GetListOfFriends()->GetEntries())throw std::runtime_error("MC friend trees forbidden");
  TIter iterate(tree->GetListOfBranches());
  while(auto* branch=dynamic_cast<TBranch*>(iterate())) {
    const std::string external=branch->GetFileName();
    if(!external.empty() && std::filesystem::weakly_canonical(external)!=std::filesystem::canonical(input))
      throw std::runtime_error("MC external branch storage forbidden");
  }
  for(auto name:{"photon_pt","photon_eta","photon_phi","photon_e","jet_pt","jet_eta","jet_phi","jet_e"})
    require(*tree,name,"ROOT::VecOps::RVec<float>");
  require(*tree,"photon_n","int");require(*tree,"jet_n","int");require(*tree,"runNumber","unsignedint");require(*tree,"eventNumber","unsignedlonglong");
  const auto channel=branch_type(*tree,"channelNumber");
  if(channel!="int" && channel!="unsignedint")throw std::runtime_error("Incompatible native MC channelNumber type: "+channel);
  const auto weight=branch_type(*tree,"mcWeight");
  if(weight!="float" && weight!="double")throw std::runtime_error("MC mcWeight must be native Float_t or Double_t");
  return tree;
}
struct Scalar {
  std::string name,type;
  std::unique_ptr<TTreeReaderValue<Float_t>> single;
  std::unique_ptr<TTreeReaderValue<Double_t>> twice;
  Scalar(TTree& tree,TTreeReader& reader,const std::string& branch):name(branch),type(branch_type(tree,branch)) {
    if(type=="float")single=std::make_unique<TTreeReaderValue<Float_t>>(reader,branch.c_str());
    else if(type=="double")twice=std::make_unique<TTreeReaderValue<Double_t>>(reader,branch.c_str());
    else throw std::runtime_error("MC diagnostic scalar must be native Float_t or Double_t: "+branch+"="+type);
  }
  double value() const {return single?static_cast<double>(**single):**twice;}
};
const std::set<std::string> normalization_fields{
  "crossSection","xSection","kFactor","filterEfficiency","sumWeights",
  "num_events","sum_of_weights","sum_of_weights_squared","xsec","kfac","filteff"};
const std::array<const char*,4> photon_flags{
  "photon_isTightID","photon_isLooseID","photon_isTightIso","photon_isLooseIso"};
struct TruthBinding {
  std::unique_ptr<TTreeReaderValue<Int_t>> count;
  std::unique_ptr<TTreeReaderValue<kinematics::RVec>> pt,eta,phi,energy,mass;
  TruthBinding(TTree& tree,TTreeReader& reader,const std::string& prefix,std::vector<NativeField>& fields) {
    const std::array<std::string,4> basic{prefix+"_n",prefix+"_pt",prefix+"_eta",prefix+"_phi"};
    bool any=tree.GetBranch((prefix+"_e").c_str()) || tree.GetBranch((prefix+"_m").c_str());
    for(const auto& name:basic)any=any || tree.GetBranch(name.c_str());
    if(!any)return;
    require(tree,basic[0],"int");
    for(std::size_t index=1;index<basic.size();++index)require(tree,basic[index],"ROOT::VecOps::RVec<float>");
    count=std::make_unique<TTreeReaderValue<Int_t>>(reader,basic[0].c_str());
    pt=std::make_unique<TTreeReaderValue<kinematics::RVec>>(reader,basic[1].c_str());
    eta=std::make_unique<TTreeReaderValue<kinematics::RVec>>(reader,basic[2].c_str());
    phi=std::make_unique<TTreeReaderValue<kinematics::RVec>>(reader,basic[3].c_str());
    for(const auto& name:basic)fields.push_back({name,branch_type(tree,name),"raw_truth_kinematics_uninterpreted"});
    const auto e=prefix+"_e";
    if(tree.GetBranch(e.c_str())) {
      require(tree,e,"ROOT::VecOps::RVec<float>");energy=std::make_unique<TTreeReaderValue<kinematics::RVec>>(reader,e.c_str());
      fields.push_back({e,branch_type(tree,e),"raw_truth_kinematics_uninterpreted"});
    }
    const auto m=prefix+"_m";
    if(tree.GetBranch(m.c_str())) {
      require(tree,m,"ROOT::VecOps::RVec<float>");mass=std::make_unique<TTreeReaderValue<kinematics::RVec>>(reader,m.c_str());
      fields.push_back({m,branch_type(tree,m),"raw_truth_kinematics_uninterpreted"});
    }
  }
  TruthCollection value() const {
    TruthCollection result;if(!count)return result;
    result.available=true;result.count=**count;result.pt=**pt;result.eta=**eta;result.phi=**phi;
    result.energy_available=bool(energy);if(energy)result.energy=**energy;
    result.mass_available=bool(mass);if(mass)result.mass=**mass;
    if(result.count<0 || result.count>100000 || result.pt.size()!=static_cast<std::size_t>(result.count) ||
       result.eta.size()!=result.pt.size() || result.phi.size()!=result.pt.size() || (energy&&result.energy.size()!=result.pt.size()) || (mass&&result.mass.size()!=result.pt.size()))
      throw std::runtime_error("MC native truth collection count/length mismatch");
    return result;
  }
};
}
struct Reader::Impl {
  std::unique_ptr<TFile> file;
  TTree* tree;
  TTreeReader reader;
  std::uint32_t expected;
  TTreeReaderValue<Int_t> np,nj;
  TTreeReaderValue<UInt_t> run;
  TTreeReaderValue<ULong64_t> event;
  TTreeReaderValue<kinematics::RVec> pp,pe,pf,pE,jp,je,jf,jE;
  std::unique_ptr<TTreeReaderValue<Int_t>> channel_signed;
  std::unique_ptr<TTreeReaderValue<UInt_t>> channel_unsigned;
  Scalar weight;
  std::vector<Scalar> diagnostics;
  std::map<std::string,std::unique_ptr<TTreeReaderValue<ROOT::VecOps::RVec<bool>>>> flags;
  std::vector<NativeField> fields;
  std::unique_ptr<TruthBinding> truth_photons,truth_jets;
  Impl(const std::filesystem::path& input,std::uint32_t expected_dsid)
    :file(open_local(input)),tree(checked_tree(*file,input)),reader(tree),expected(expected_dsid),
     np(reader,"photon_n"),nj(reader,"jet_n"),run(reader,"runNumber"),event(reader,"eventNumber"),
     pp(reader,"photon_pt"),pe(reader,"photon_eta"),pf(reader,"photon_phi"),pE(reader,"photon_e"),
     jp(reader,"jet_pt"),je(reader,"jet_eta"),jf(reader,"jet_phi"),jE(reader,"jet_e"),weight(*tree,reader,"mcWeight") {
    if(!expected)throw std::invalid_argument("Expected MC DSID must be positive");
    const auto channel=branch_type(*tree,"channelNumber");
    if(channel=="int")channel_signed=std::make_unique<TTreeReaderValue<Int_t>>(reader,"channelNumber");
    else channel_unsigned=std::make_unique<TTreeReaderValue<UInt_t>>(reader,"channelNumber");
    for(auto name:{"photon_pt","photon_eta","photon_phi","photon_e","jet_pt","jet_eta","jet_phi","jet_e","photon_n","jet_n","runNumber","eventNumber"})
      fields.push_back({name,branch_type(*tree,name),"reconstructed_kinematics_or_identity"});
    fields.push_back({"channelNumber",channel,"dataset_identity"});fields.push_back({"mcWeight",weight.type,"generator_weight_diagnostic_only"});
    for(auto name:photon_flags)if(tree->GetBranch(name)) {
      require(*tree,name,"ROOT::VecOps::RVec<bool>");flags.emplace(name,std::make_unique<TTreeReaderValue<ROOT::VecOps::RVec<bool>>>(reader,name));
      fields.push_back({name,branch_type(*tree,name),"raw_flag_diagnostic_only"});
    }
    TIter iterate(tree->GetListOfBranches());
    while(auto* branch=dynamic_cast<TBranch*>(iterate())) {
      const std::string name=branch->GetName();
      if(normalization_fields.contains(name) || name.starts_with("scaleFactor_") || name.starts_with("ScaleFactor_")) {
        diagnostics.emplace_back(*tree,reader,name);
        fields.push_back({name,diagnostics.back().type,normalization_fields.contains(name)?"normalization_diagnostic_only":"scale_factor_diagnostic_only"});
      }
    }
    truth_photons=std::make_unique<TruthBinding>(*tree,reader,"truth_photon",fields);
    truth_jets=std::make_unique<TruthBinding>(*tree,reader,"truth_jet",fields);
  }
};
Reader::Reader(const std::filesystem::path& input,std::uint32_t expected_dsid):impl_(std::make_unique<Impl>(input,expected_dsid)) {}
Reader::~Reader()=default;
std::int64_t Reader::entries() const{return impl_->tree->GetEntries();}
const std::vector<NativeField>& Reader::schema() const{return impl_->fields;}
RawEvent Reader::read(std::int64_t index) {
  auto& x=*impl_;
  if(index<0 || index>=entries())throw std::out_of_range("MC entry index outside local tree");
  if(x.reader.SetEntry(index)!=TTreeReader::kEntryValid)throw std::runtime_error("MC reader entry setup failure");
  const std::int64_t channel=x.channel_signed?static_cast<std::int64_t>(**x.channel_signed):static_cast<std::int64_t>(**x.channel_unsigned);
  if(channel<=0 || static_cast<std::uint64_t>(channel)!=x.expected)throw std::runtime_error("Unexpected MC channelNumber / DSID at entry "+std::to_string(index));
  RawEvent result;result.dsid=static_cast<std::uint32_t>(channel);result.generator_weight=x.weight.value();
  if(!std::isfinite(result.generator_weight))throw std::runtime_error("Nonfinite MC generator weight");
  auto& r=result.reconstructed;r.run=*x.run;r.event=*x.event;r.photon_n=*x.np;r.jet_n=*x.nj;
  r.photon_pt=*x.pp;r.photon_eta=*x.pe;r.photon_phi=*x.pf;r.photon_e=*x.pE;r.jet_pt=*x.jp;r.jet_eta=*x.je;r.jet_phi=*x.jf;r.jet_e=*x.jE;
  if(r.photon_n<0 || r.jet_n<0 || r.photon_n>100000 || r.jet_n>100000)throw std::runtime_error("Invalid MC collection count");
  for(auto* collection:{&r.photon_pt,&r.photon_eta,&r.photon_phi,&r.photon_e})
    if(collection->size()!=static_cast<std::size_t>(r.photon_n))throw std::runtime_error("MC photon collection length mismatch");
  for(auto* collection:{&r.jet_pt,&r.jet_eta,&r.jet_phi,&r.jet_e})
    if(collection->size()!=static_cast<std::size_t>(r.jet_n))throw std::runtime_error("MC jet collection length mismatch");
  auto flag=[&](const char* name,ROOT::VecOps::RVec<bool>& output) {
    const auto found=x.flags.find(name);result.photon_flag_available[name]=found!=x.flags.end();
    if(found!=x.flags.end()) {
      output=**found->second;
      if(output.size()!=static_cast<std::size_t>(r.photon_n))throw std::runtime_error("MC photon flag length mismatch");
    }
  };
  flag(photon_flags[0],r.tight_id);flag(photon_flags[1],r.loose_id);flag(photon_flags[2],r.tight_iso);flag(photon_flags[3],r.loose_iso);
  for(const auto& scalar:x.diagnostics)result.diagnostics.emplace(scalar.name,scalar.value());
  result.truth_photons=x.truth_photons->value();result.truth_jets=x.truth_jets->value();
  return result;
}
}

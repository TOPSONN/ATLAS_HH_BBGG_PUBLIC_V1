#include "AtlasInputPreflight.h"
#include <TBranch.h>
#include <TClass.h>
#include <TDataType.h>
#include <TDirectory.h>
#include <TFile.h>
#include <TKey.h>
#include <TLeaf.h>
#include <TList.h>
#include <TObjArray.h>
#include <TTree.h>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <system_error>

namespace atlas::input_preflight {
namespace {
constexpr std::size_t maximum_nodes=100000;
constexpr unsigned maximum_depth=64;
struct Budget {
  std::size_t nodes=0;
  void visit(unsigned depth) {
    if(depth>maximum_depth || ++nodes>maximum_nodes)
      throw std::runtime_error("ROOT metadata traversal exceeds the documented safety budget");
  }
};
bool uri(const std::string& text) { return text.find("://")!=std::string::npos; }
std::string child_path(const std::string& parent,const std::string& name) {
  return parent.empty()?name:parent+"/"+name;
}
std::string expected_type(TBranch& branch) {
  TClass* cls=nullptr;EDataType type=kOther_t;
  if(branch.GetExpectedType(cls,type)==0) {
    if(cls)return cls->GetName();
    if(type!=kOther_t && type!=kNoType_t)return TDataType::GetTypeName(type);
  }
  const char* classname=branch.GetClassName();
  if(classname&&*classname)return classname;
  std::string leaves;
  if(auto* list=branch.GetListOfLeaves())for(int index=0;index<list->GetEntriesFast();++index) {
    auto* leaf=dynamic_cast<TLeaf*>(list->At(index));
    if(!leaf)throw std::runtime_error("Non-native leaf metadata encountered");
    if(!leaves.empty())leaves+=';';
    leaves+=std::string(leaf->GetName())+":"+leaf->GetTypeName();
  }
  return leaves.empty()?"UNKNOWN":leaves;
}
void inspect_branches(TObjArray* branches,const std::string& tree_path,int cycle,
                      const std::string& parent,unsigned depth,Budget& budget,Result& result) {
  if(!branches)return;
  for(int index=0;index<branches->GetEntriesFast();++index) {
    budget.visit(depth);
    auto* branch=dynamic_cast<TBranch*>(branches->At(index));
    if(!branch)throw std::runtime_error("Non-native branch metadata encountered");
    const std::string path=child_path(parent,branch->GetName());
    const char* native_file=branch->GetFileName();
    const std::string storage=native_file?native_file:"";
    if(!storage.empty()) {
      if(uri(storage))throw std::runtime_error("External branch URI forbidden: "+path);
      auto candidate=std::filesystem::path(storage);
      if(candidate.is_relative())candidate=result.canonical_input.parent_path()/candidate;
      std::error_code error;
      const auto resolved=std::filesystem::weakly_canonical(candidate,error);
      if(error || resolved!=result.canonical_input)
        throw std::runtime_error("External branch storage forbidden: "+path);
    }
    result.branches.push_back({tree_path,path,branch->GetName(),expected_type(*branch),
                               branch->GetClassName(),storage,cycle});
    inspect_branches(branch->GetListOfBranches(),tree_path,cycle,path,depth+1,budget,result);
  }
}
void inspect_directory(TDirectory& directory,const std::string& parent,unsigned depth,
                       Budget& budget,Result& result) {
  TIter next(directory.GetListOfKeys());
  while(auto* object=next()) {
    budget.visit(depth);
    auto* key=dynamic_cast<TKey*>(object);
    if(!key)throw std::runtime_error("Non-native key metadata encountered");
    const std::string path=child_path(parent,key->GetName());
    const std::string classname=key->GetClassName();
    result.keys.push_back({path,classname,key->GetCycle()});
    auto* cls=TClass::GetClass(classname.c_str());
    if(!cls)throw std::runtime_error("Unresolved stored key class cannot be certified as non-tree metadata: "+path);
    if(cls->InheritsFrom(TTree::Class())) {
      // Check the stored native type before deserialization or any virtual tree
      // introspection. TChain can otherwise open its member files implicitly.
      if(cls!=TTree::Class())throw std::runtime_error("Stored tree must have exact TTree class: "+path);
      std::unique_ptr<TObject> loaded(key->ReadObj());
      auto* tree=dynamic_cast<TTree*>(loaded.get());
      if(!tree || tree->IsA()!=TTree::Class())throw std::runtime_error("Loaded tree must have exact TTree class: "+path);
      // Keep the tree's original directory association while inspecting branch
      // storage. SetDirectory(nullptr) clears file associations and can hide an
      // external branch filename. Deletion unregisters this loaded tree safely.
      if(tree->GetListOfFriends() && tree->GetListOfFriends()->GetEntries()!=0)
        throw std::runtime_error("Friend trees forbidden: "+path);
      if(tree->GetEntries()<0)throw std::runtime_error("Negative native tree entry count: "+path);
      result.trees.push_back({path,classname,key->GetCycle(),tree->GetEntries()});
      inspect_branches(tree->GetListOfBranches(),path,key->GetCycle(),"",depth+1,budget,result);
    } else if(cls->InheritsFrom(TDirectory::Class())) {
      std::unique_ptr<TObject> loaded(key->ReadObj());
      auto* subdirectory=dynamic_cast<TDirectory*>(loaded.get());
      if(!subdirectory)throw std::runtime_error("Directory key could not be loaded: "+path);
      inspect_directory(*subdirectory,path,depth+1,budget,result);
    }
    // Non-tree payloads are inventoried by key metadata without reading them.
  }
}
std::string csv(const std::string& value) {
  std::string result="\"";for(char character:value){if(character=='\"')result+='\"';result+=character;}
  return result+'\"';
}
std::string json(const std::string& value) {
  std::ostringstream stream;stream<<'\"';
  for(unsigned char character:value) {
    switch(character) {
      case '\"':stream<<"\\\"";break;case '\\':stream<<"\\\\";break;
      case '\n':stream<<"\\n";break;case '\r':stream<<"\\r";break;case '\t':stream<<"\\t";break;
      default:if(character<32)stream<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<static_cast<unsigned>(character)<<std::dec;
              else stream<<character;
    }
  }
  stream<<'\"';return stream.str();
}
std::ofstream fresh_file(const std::filesystem::path& path) {
  std::ofstream stream;stream.exceptions(std::ios::failbit|std::ios::badbit);
  stream.open(path,std::ios::out|std::ios::binary);return stream;
}
}
Result inspect_local_file(const std::filesystem::path& input,std::uint32_t expected_dsid,
                          EvidenceKind evidence_kind) {
  if(expected_dsid==0)throw std::runtime_error("Expected DSID must be positive");
  if(uri(input.string()))throw std::runtime_error("Remote ROOT inputs forbidden");
  if(!std::filesystem::is_regular_file(input))throw std::runtime_error("Input must be an existing local regular file");
  Result result;result.canonical_input=std::filesystem::canonical(input);
  result.input_bytes=std::filesystem::file_size(result.canonical_input);
  result.expected_dsid=expected_dsid;result.evidence_kind=evidence_kind;
  std::unique_ptr<TFile> file(TFile::Open(result.canonical_input.c_str(),"READ"));
  if(!file || file->IsZombie())throw std::runtime_error("Zombie or unreadable ROOT file rejected");
  if(file->IsWritable())throw std::runtime_error("ROOT input unexpectedly writable");
  if(file->TestBit(TFile::kRecovered))throw std::runtime_error("Recovered ROOT file rejected");
  Budget budget;inspect_directory(*file,"",0,budget,result);
  file->Close();
  // Reuse the unchanged, independently tested native MC type contract. This
  // constructor binds metadata only; event-level identity remains untested.
  mc::Reader reader(result.canonical_input,expected_dsid);
  result.analysis_entries=reader.entries();result.reader_bindings=reader.schema();
  if(result.analysis_entries<=0)throw std::runtime_error("Empty analysis tree cannot enter the staged event-validation gates");
  return result;
}
void write_new_outputs(const Result& result,const std::filesystem::path& output) {
  if(uri(output.string()) || output.empty())throw std::runtime_error("Output must be a fresh local directory");
  if(!std::filesystem::create_directory(output))throw std::runtime_error("Output directory already exists; no overwrite permitted");
  {auto stream=fresh_file(output/"keys.csv");stream<<"key_path,key_cycle,native_class\n";
    for(const auto& key:result.keys)stream<<csv(key.path)<<','<<key.cycle<<','<<csv(key.native_class)<<'\n';}
  {auto stream=fresh_file(output/"trees.csv");stream<<"tree_path,key_cycle,native_class,entries\n";
    for(const auto& tree:result.trees)stream<<csv(tree.path)<<','<<tree.cycle<<','<<csv(tree.native_class)<<','<<tree.entries<<'\n';}
  {auto stream=fresh_file(output/"branches.csv");stream<<"tree_path,tree_cycle,branch_path,branch_name,native_type,native_class,storage_file\n";
    for(const auto& branch:result.branches)stream<<csv(branch.tree_path)<<','<<branch.tree_cycle<<','<<csv(branch.path)<<','<<csv(branch.name)<<','<<csv(branch.native_type)<<','<<csv(branch.native_class)<<','<<csv(branch.storage_file)<<'\n';}
  {auto stream=fresh_file(output/"reader_bindings.csv");stream<<"branch_name,native_type,binding_role\n";
    for(const auto& binding:result.reader_bindings)stream<<csv(binding.name)<<','<<csv(binding.type)<<','<<csv(binding.role)<<'\n';}
  {auto stream=fresh_file(output/"summary.json");
    stream<<"{\n  \"schema_version\": 1,\n  \"scope\": "
      <<json(result.evidence_kind==EvidenceKind::SyntheticFixture?"SYNTHETIC_FIXTURE":"PHYSICAL_CANDIDATE")
      <<",\n  \"input\": "<<json(result.canonical_input.string())
      <<",\n  \"input_bytes\": "<<result.input_bytes<<",\n  \"expected_dsid\": "<<result.expected_dsid
      <<",\n  \"metadata_integrity\": \"PASS\",\n  \"mc_native_type_contract\": \"PASS_METADATA_ONLY\",\n"
      <<"  \"actual_dsid_values\": \"NOT_EVALUATED\",\n  \"actual_event_structure\": \"NOT_EVALUATED\",\n"
      <<"  \"units\": \"UNKNOWN\",\n  \"provenance\": \"UNKNOWN\",\n  \"event_entries_read\": 0,\n"
      <<"  \"analysis_entries\": "<<result.analysis_entries<<",\n  \"key_records\": "<<result.keys.size()
      <<",\n  \"tree_records\": "<<result.trees.size()<<",\n  \"branch_records\": "<<result.branches.size()
      <<",\n  \"reader_bindings\": "<<result.reader_bindings.size()
      <<",\n  \"maximum_metadata_nodes\": "<<maximum_nodes<<",\n  \"maximum_metadata_depth\": "<<maximum_depth
      <<",\n  \"zombie\": false,\n  \"recovered\": false,\n  \"chains\": false,\n  \"friends\": false,\n"
      <<"  \"external_branch_storage\": false,\n  \"physical_validation\": \"NOT_EVALUATED\"\n}\n";}
}
}

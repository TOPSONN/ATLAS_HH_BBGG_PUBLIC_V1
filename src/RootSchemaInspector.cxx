#include "AtlasRootSchema.h"
#include <TBranch.h>
#include <TClass.h>
#include <TDataType.h>
#include <TFile.h>
#include <TKey.h>
#include <TLeaf.h>
#include <TTree.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <ROOT/RVec.hxx>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <map>
#include <memory>
#include <stdexcept>
#include <type_traits>

namespace atlas::schema {
namespace {
const std::string dictionary = "https://opendata.atlas.cern/docs/data/for_education/13TeV25_details";
std::vector<Field> expected() {
  std::vector<Field> fields;
  auto add = [&](std::string group, std::string name, std::string type, bool required = true) {
    Field field;
    field.group = std::move(group); field.name = std::move(name);
    field.expected_type = std::move(type); field.required = required;
    fields.push_back(std::move(field));
  };
  add("photon", "photon_n", "int");
  for (auto name : {"photon_pt", "photon_eta", "photon_phi", "photon_e"}) add("photon", name, "vector<float>");
  for (auto name : {"photon_isTightID", "photon_isLooseID", "photon_isTightIso", "photon_isLooseIso"}) add("photon", name, "vector<bool>");
  add("jet", "jet_n", "int");
  for (auto name : {"jet_pt", "jet_eta", "jet_phi", "jet_e", "jet_jvt"}) add("jet", name, "vector<float>");
  add("btag", "jet_btag_quantile", "vector<int>");
  add("event", "runNumber", "unsigned int");
  add("event", "eventNumber", "unsigned long long");
  add("event", "channelNumber", "unsigned int", false);  // Documented simulation DSID.
  add("trigger", "trigP", "bool");
  for (auto name : {"mcWeight", "ScaleFactor_PHOTON", "ScaleFactor_BTAG", "ScaleFactor_PILEUP", "ScaleFactor_JVT"}) add("weight", name, "float", false);
  return fields;
}
std::string normalized(std::string type) {
  for (std::size_t pos; (pos = type.find("std::")) != std::string::npos;) type.erase(pos, 5);
  type.erase(std::remove(type.begin(), type.end(), ' '), type.end());
  const std::map<std::string, std::string> aliases{{"Int_t", "int"}, {"UInt_t", "unsignedint"},
    {"ULong64_t", "unsignedlonglong"}, {"Bool_t", "bool"}, {"Float_t", "float"}, {"Double_t", "double"}};
  auto found = aliases.find(type);
  return found == aliases.end() ? type : found->second;
}
struct Value {
  virtual ~Value() = default;
  virtual bool ready() const = 0;
  virtual bool finite() const = 0;
  virtual bool vector() const = 0;
  virtual std::size_t size() const = 0;
  virtual long long count() const = 0;
};
template<class T> struct Scalar final : Value {
  mutable TTreeReaderValue<T> value;  // ROOT lazily loads through non-const accessors.
  Scalar(TTreeReader& reader, const std::string& name) : value(reader, name.c_str()) {}
  bool ready() const override { return value.GetSetupStatus() >= 0; }
  bool finite() const override { const auto* p = value.Get(); return p && std::isfinite(static_cast<long double>(*p)); }
  bool vector() const override { return false; }
  std::size_t size() const override { return 1; }
  long long count() const override {
    if constexpr (std::is_same_v<T, Int_t>) { const auto* p = value.Get(); return p ? *p : -1; }
    return -1;  // Only the two documented int object counts are used as sizes.
  }
};
template<class T, class Collection = std::vector<T>> struct Vector final : Value {
  mutable TTreeReaderValue<Collection> value;
  Vector(TTreeReader& reader, const std::string& name) : value(reader, name.c_str()) {}
  bool ready() const override { return value.GetSetupStatus() >= 0; }
  bool finite() const override {
    const auto* p = value.Get();
    if (!p) return false;
    for (auto x : *p) if (!std::isfinite(static_cast<long double>(x))) return false;
    return true;
  }
  bool vector() const override { return true; }
  std::size_t size() const override { const auto* p = value.Get(); return p ? p->size() : static_cast<std::size_t>(-1); }
  long long count() const override { return -1; }
};
std::unique_ptr<Value> make_value(TTreeReader& reader, const Field& field) {
  const auto type = normalized(field.actual_type);
  if (type == "int") return std::make_unique<Scalar<Int_t>>(reader, field.name);
  if (type == "unsignedint") return std::make_unique<Scalar<UInt_t>>(reader, field.name);
  if (type == "unsignedlonglong") return std::make_unique<Scalar<ULong64_t>>(reader, field.name);
  if (type == "bool") return std::make_unique<Scalar<Bool_t>>(reader, field.name);
  if (type == "float") return std::make_unique<Scalar<Float_t>>(reader, field.name);
  if (type == "vector<float>") return std::make_unique<Vector<float>>(reader, field.name);
  if (type == "vector<int>") return std::make_unique<Vector<int>>(reader, field.name);
  if (type == "vector<bool>") return std::make_unique<Vector<bool>>(reader, field.name);
  if (type == "ROOT::VecOps::RVec<float>") return std::make_unique<Vector<float, ROOT::VecOps::RVec<float>>>(reader, field.name);
  if (type == "ROOT::VecOps::RVec<int>") return std::make_unique<Vector<int, ROOT::VecOps::RVec<int>>>(reader, field.name);
  if (type == "ROOT::VecOps::RVec<bool>") return std::make_unique<Vector<bool, ROOT::VecOps::RVec<bool>>>(reader, field.name);
  throw std::runtime_error("Unsupported actual type: " + field.name);
}
std::string quote(std::string text) {
  std::string result = "\"";
  for (char c : text) { if (c == '"') result += '"'; result += c; }
  return result + '"';
}
std::ofstream new_output(const std::filesystem::path& path) {
  if (std::filesystem::exists(path)) throw std::runtime_error("Output already exists: " + path.string());
  std::ofstream output(path);
  if (!output) throw std::runtime_error("Cannot create output: " + path.string());
  output.exceptions(std::ios::badbit | std::ios::failbit);
  return output;
}
}  // namespace

Result inspect(const std::filesystem::path& input, std::size_t max_entries, const std::string& tree_name) {
  if (max_entries > 10 || max_entries == 0) throw std::invalid_argument("Entry limit must be 1..10.");
  if (input.string().find("://") != std::string::npos || !std::filesystem::is_regular_file(input))
    throw std::invalid_argument("Only an existing regular local input file is allowed.");
  auto path = std::filesystem::canonical(input);
  std::unique_ptr<TFile> file(TFile::Open(path.c_str(), "READ"));
  if (!file || file->IsZombie() || file->IsWritable()) throw std::runtime_error("Cannot open read-only ROOT input.");
  Result result;
  result.fields = expected();
  std::vector<std::string> trees;
  TIter keys(file->GetListOfKeys());
  while (auto* key = dynamic_cast<TKey*>(keys())) {
    auto* cls = TClass::GetClass(key->GetClassName());
    if (cls && cls->InheritsFrom(TTree::Class()) && std::find(trees.begin(), trees.end(), key->GetName()) == trees.end()) trees.emplace_back(key->GetName());
  }
  if (tree_name.empty() && trees.size() != 1) throw std::runtime_error("Expected one top-level TTree; specify --tree for multiple trees.");
  result.tree_name = tree_name.empty() ? trees.front() : tree_name;
  TTree* tree = nullptr;
  file->GetObject(result.tree_name.c_str(), tree);
  if (!tree) throw std::runtime_error("Requested TTree is absent.");
  if (tree->GetListOfFriends() && tree->GetListOfFriends()->GetEntries() != 0) throw std::runtime_error("Friend trees are refused to prevent external file access.");
  TIter branches(tree->GetListOfBranches());
  result.schema_pass = true;
  while (auto* branch = dynamic_cast<TBranch*>(branches())) {
    const std::string external = branch->GetFileName();
    if (!external.empty() && std::filesystem::weakly_canonical(external) != path) throw std::runtime_error("External branch storage refused.");
    auto found = std::find_if(result.fields.begin(), result.fields.end(), [&](const Field& f) { return f.name == branch->GetName(); });
    if (found == result.fields.end()) {
      Field extra; extra.group = "extra"; extra.name = branch->GetName(); extra.expected_type = "NOT_AUDITED";
      result.fields.push_back(std::move(extra)); found = result.fields.end() - 1;
    }
    auto& field = *found;
    field.present = true;
    TClass* cls = nullptr; EDataType type = kOther_t;
    const auto status = branch->GetExpectedType(cls, type);
    field.actual_type = status == 0 ? (cls ? cls->GetName() : TDataType::GetTypeName(type)) : "UNKNOWN";
    const auto actual = normalized(field.actual_type);
    const bool rvec = actual.starts_with("ROOT::VecOps::RVec<");
    const auto comparable = rvec ? "vector<" + actual.substr(std::string("ROOT::VecOps::RVec<").size()) : actual;
    field.structure = rvec ? "RVec" : (cls && actual.starts_with("vector<") ? "vector" : (cls ? "object" : "scalar"));
    TIter leaves(branch->GetListOfLeaves());
    while (auto* leaf = dynamic_cast<TLeaf*>(leaves())) {
      if (!field.leaves.empty()) field.leaves += ";";
      field.leaves += std::string(leaf->GetName()) + ":" + leaf->GetTypeName() + ":len=" + std::to_string(leaf->GetLenStatic());
      if (!cls && (leaf->GetLeafCount() || leaf->GetLenStatic() != 1)) field.structure = "array";
    }
    if (field.group == "extra") field.compatibility = "NOT_AUDITED";
    else if (field.structure != "array" && comparable == normalized(field.expected_type)) {
      field.compatibility = rvec ? "DOCUMENTED_CONTAINER_DIFFERENCE_SUPPORTED" : "MATCH";
      result.documented_type_difference = result.documented_type_difference || rvec;
    }
    else if (field.name == "jet_jvt" && comparable == "vector<bool>") {
      field.compatibility = rvec ? "DOCUMENTED_CONTAINER_AND_ELEMENT_DIFFERENCE_SUPPORTED" : "DOCUMENTED_TYPE_DIFFERENCE_SUPPORTED";
      result.documented_type_difference = true;
    } else {
      field.compatibility = "FAIL_TYPE"; result.schema_pass = false;
      result.issues.push_back("Type/structure mismatch: " + field.name);
    }
  }
  for (auto& field : result.fields) if (!field.present) {
    field.actual_type = "ABSENT"; field.structure = "ABSENT";
    field.compatibility = field.required ? "FAIL_MISSING" : "NOT_APPLICABLE";
    if (field.required) { result.schema_pass = false; result.issues.push_back("Missing required branch: " + field.name); }
  }
  if (!result.schema_pass) return result;  // No entry access after a failed schema gate.
  TTreeReader reader(tree);
  std::map<std::string, std::unique_ptr<Value>> values;
  for (const auto& field : result.fields) if (field.present && field.group != "extra") values[field.name] = make_value(reader, field);
  const auto count = std::min<Long64_t>(tree->GetEntries(), static_cast<Long64_t>(max_entries));
  result.structure_pass = count > 0;
  if (count == 0) result.issues.push_back("No entries: structural sample is UNKNOWN.");
  for (Long64_t i = 0; i < count; ++i) {
    if (reader.SetEntry(i) != TTreeReader::kEntryValid) {
      result.structure_pass = false; result.issues.push_back("Reader entry setup failed."); break;
    }
    bool ready = true;
    for (const auto& [name, value] : values) if (!value->ready()) {
      ready = false; result.issues.push_back("Reader type setup failed: " + name);
    }
    if (!ready) { result.structure_pass = false; break; }
    ++result.entries_inspected;
    for (const auto& [name, value] : values) {
      bool valid = value->finite();
      if (name == "photon_n" || name == "jet_n") valid = valid && value->count() >= 0;
      if (value->vector()) {
        const auto n = values.at(name.starts_with("photon_") ? "photon_n" : "jet_n")->count();
        valid = valid && n >= 0 && value->size() == static_cast<std::size_t>(n);
      }
      if (!valid) { result.structure_pass = false; result.issues.push_back("Structural failure at entry " + std::to_string(i) + ": " + name); }
    }
  }
  return result;
}

void write_manifest(const Result& result, const std::filesystem::path& output, const std::string& evidence) {
  auto stream = new_output(output);
  stream << "group,requested_branch,required,present,actual_branch,root_type,structure,leaf_metadata,documented_expected_type,compatibility,documentation_source,physical_evidence,kinematic_units,working_point_semantics\n";
  for (const auto& f : result.fields) {
    const std::vector<std::string> row{f.group, f.name, f.required ? "yes" : "no", f.present ? "yes" : "no", f.present ? f.name : "ABSENT",
      f.actual_type, f.structure, f.leaves, f.expected_type, f.compatibility, f.group == "extra" ? "NOT_AUDITED" : dictionary,
      evidence + ";tree=" + result.tree_name + ";TBranch::GetExpectedType/TLeaf", "UNKNOWN", "UNKNOWN"};
    for (std::size_t i = 0; i < row.size(); ++i) { if (i) stream << ','; stream << quote(row[i]); }
    stream << '\n';
  }
}
void write_summary(const Result& result, const std::filesystem::path& output) {
  auto stream = new_output(output);
  stream << "TREE_NAME=" << result.tree_name << "\nENTRIES_INSPECTED=" << result.entries_inspected
         << "\nSCHEMA=" << (result.schema_pass ? "PASS" : "FAIL")
         << "\nSTRUCTURE=" << (result.structure_pass ? "PASS" : (result.entries_inspected ? "FAIL" : "UNKNOWN"))
         << "\nDOCUMENTED_TYPE_DIFFERENCE=" << (result.documented_type_difference ? "yes" : "no") << '\n';
  for (const auto& issue : result.issues) stream << "ISSUE=" << issue << '\n';
}
}  // namespace atlas::schema

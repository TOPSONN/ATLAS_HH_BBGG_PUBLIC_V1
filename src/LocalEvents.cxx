#include "AtlasLocalEvents.h"
#include <TFile.h>
#include <TTree.h>
#include <TBranch.h>
#include <TClass.h>
#include <TDataType.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <algorithm>
#include <stdexcept>

namespace atlas::events {
namespace {
std::unique_ptr<TFile> open_local(const std::filesystem::path& input) {
  if (input.string().find("://") != std::string::npos || !std::filesystem::is_regular_file(input))
    throw std::invalid_argument("Only an existing regular local file is allowed");
  std::unique_ptr<TFile> file(TFile::Open(std::filesystem::canonical(input).c_str(), "READ"));
  if (!file || file->IsZombie() || file->IsWritable()) throw std::runtime_error("Corrupt or writable ROOT file");
  return file;
}
TTree* checked_tree(TFile& file, const std::filesystem::path& path) {
  TTree* tree = nullptr; file.GetObject("analysis", tree);
  if (!tree) throw std::runtime_error("analysis TTree absent");
  if (tree->GetListOfFriends() && tree->GetListOfFriends()->GetEntries()) throw std::runtime_error("Friend trees forbidden");
  TIter it(tree->GetListOfBranches());
  while (auto* branch = dynamic_cast<TBranch*>(it())) {
    const std::string external = branch->GetFileName();
    if (!external.empty() && std::filesystem::weakly_canonical(external) != std::filesystem::canonical(path))
      throw std::runtime_error("External branch storage forbidden");
  }
  auto check = [&](const std::string& name, const std::string& expected) {
    auto* branch = tree->GetBranch(name.c_str());
    if (!branch) throw std::runtime_error("Missing branch: " + name);
    TClass* cls = nullptr; EDataType type = kOther_t;
    if (branch->GetExpectedType(cls, type) != 0) throw std::runtime_error("Unresolved branch type: " + name);
    std::string actual = cls ? cls->GetName() : TDataType::GetTypeName(type);
    actual.erase(std::remove(actual.begin(), actual.end(), ' '), actual.end());
    if (actual == "Int_t") actual = "int";
    if (actual == "UInt_t") actual = "unsignedint";
    if (actual == "ULong64_t") actual = "unsignedlonglong";
    std::string target = expected; target.erase(std::remove(target.begin(), target.end(), ' '), target.end());
    if (actual != target) throw std::runtime_error("Incompatible native branch type: " + name + "=" + actual);
  };
  for (auto name : {"photon_pt", "photon_eta", "photon_phi", "photon_e", "jet_pt", "jet_eta", "jet_phi", "jet_e"})
    check(name, "ROOT::VecOps::RVec<float>");
  for (auto name : {"photon_isTightID", "photon_isLooseID", "photon_isTightIso", "photon_isLooseIso"})
    check(name, "ROOT::VecOps::RVec<bool>");
  check("photon_n", "int"); check("jet_n", "int");
  check("runNumber", "unsigned int"); check("eventNumber", "unsigned long long");
  return tree;
}
}  // namespace
struct Reader::Impl {
  std::unique_ptr<TFile> file;
  TTree* tree;
  TTreeReader reader;
  TTreeReaderValue<Int_t> np, nj;
  TTreeReaderValue<UInt_t> run;
  TTreeReaderValue<ULong64_t> event;
  TTreeReaderValue<kinematics::RVec> pp, pe, pf, pE, jp, je, jf, jE;
  TTreeReaderValue<ROOT::VecOps::RVec<bool>> ti, li, ts, ls;
  explicit Impl(const std::filesystem::path& input)
      : file(open_local(input)), tree(checked_tree(*file, input)), reader(tree),
        np(reader, "photon_n"), nj(reader, "jet_n"), run(reader, "runNumber"), event(reader, "eventNumber"),
        pp(reader, "photon_pt"), pe(reader, "photon_eta"), pf(reader, "photon_phi"), pE(reader, "photon_e"),
        jp(reader, "jet_pt"), je(reader, "jet_eta"), jf(reader, "jet_phi"), jE(reader, "jet_e"),
        ti(reader, "photon_isTightID"), li(reader, "photon_isLooseID"), ts(reader, "photon_isTightIso"), ls(reader, "photon_isLooseIso") {}
};
Reader::Reader(const std::filesystem::path& input) : impl_(std::make_unique<Impl>(input)) {}
Reader::~Reader() = default;
std::int64_t Reader::entries() const { return impl_->tree->GetEntries(); }
RawEvent Reader::read(std::int64_t index) {
  auto& x = *impl_;
  if (index < 0 || index >= entries()) throw std::out_of_range("Entry index outside local tree");
  if (x.reader.SetEntry(index) != TTreeReader::kEntryValid) throw std::runtime_error("Reader entry setup failure");
  RawEvent result{*x.run, *x.event, *x.np, *x.nj, *x.pp, *x.pe, *x.pf, *x.pE, *x.jp, *x.je, *x.jf, *x.jE,
                  *x.ti, *x.li, *x.ts, *x.ls};
  if (result.photon_n < 0 || result.jet_n < 0) throw std::runtime_error("Negative collection count");
  const auto pn = static_cast<std::size_t>(result.photon_n), jn = static_cast<std::size_t>(result.jet_n);
  for (auto* v : {&result.photon_pt, &result.photon_eta, &result.photon_phi, &result.photon_e})
    if (v->size() != pn) throw std::runtime_error("Photon collection length mismatch");
  for (auto* v : {&result.jet_pt, &result.jet_eta, &result.jet_phi, &result.jet_e})
    if (v->size() != jn) throw std::runtime_error("Jet collection length mismatch");
  for (auto* v : {&result.tight_id, &result.loose_id, &result.tight_iso, &result.loose_iso})
    if (v->size() != pn) throw std::runtime_error("Photon flag length mismatch");
  return result;
}
}  // namespace atlas::events

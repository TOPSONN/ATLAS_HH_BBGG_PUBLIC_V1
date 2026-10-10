#include "AtlasRootSchema.h"
#include <TFile.h>
#include <TTree.h>
#include <ROOT/RVec.hxx>
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>

namespace {
void require(bool condition, const std::string& message) {
  if (!condition) throw std::runtime_error(message);
}
template<template<class> class Collection>
void fixture_impl(const std::filesystem::path& path, const std::string& mode) {
  TFile file(path.c_str(), "RECREATE");
  TTree tree("fixture", "Synthetic structural fixture; no collision physics");
  Int_t photon_n = 2, jet_n = 1;
  UInt_t run = 42;
  ULong64_t event = (ULong64_t{1} << 40);
  Bool_t trigger = true;
  Float_t weight = 1, wrong_pt = 1;
  std::map<std::string, Collection<float>> floats;
  std::map<std::string, Collection<bool>> booleans;
  Collection<int> quantile{3};
  tree.Branch("photon_n", &photon_n); tree.Branch("jet_n", &jet_n);
  for (auto name : {"photon_pt", "photon_eta", "photon_phi", "photon_e", "jet_pt", "jet_eta", "jet_phi", "jet_e"}) {
    floats[name] = Collection<float>(std::string(name).starts_with("photon_") ? 2 : 1, 1.0f);
    if (mode == "wrong_type" && std::string(name) == "photon_pt") tree.Branch(name, &wrong_pt);
    else tree.Branch(name, &floats.at(name));
  }
  for (auto name : {"photon_isTightID", "photon_isLooseID", "photon_isTightIso", "photon_isLooseIso"}) {
    booleans[name] = {true, false}; tree.Branch(name, &booleans.at(name));
  }
  if (mode == "float_jvt") { floats["jet_jvt"] = {1}; tree.Branch("jet_jvt", &floats.at("jet_jvt")); }
  else { booleans["jet_jvt"] = {true}; tree.Branch("jet_jvt", &booleans.at("jet_jvt")); }
  tree.Branch("jet_btag_quantile", &quantile);
  tree.Branch("runNumber", &run); tree.Branch("eventNumber", &event);
  if (mode != "missing_trigger") tree.Branch("trigP", &trigger);
  if (mode == "nan_weight") tree.Branch("mcWeight", &weight);
  for (int i = 0; i < (mode == "empty" ? 0 : 20); ++i) {
    if ((mode == "short_vector" || mode == "rvec_short_vector") && i == 3) floats["photon_eta"].pop_back();
    if (mode == "negative_count" && i == 2) jet_n = -1;
    if (mode == "nan" && i == 5) floats["jet_pt"][0] = std::numeric_limits<float>::quiet_NaN();
    if (mode == "late_nan" && i == 15) floats["jet_pt"][0] = std::numeric_limits<float>::quiet_NaN();
    if (mode == "nan_weight" && i == 1) weight = std::numeric_limits<float>::quiet_NaN();
    event += 1; tree.Fill();
  }
  tree.Write();
  if (mode == "multiple" || mode == "friend") {
    TTree other("other", "Extra synthetic tree"); other.Write();
    if (mode == "friend") { tree.AddFriend(&other); tree.Write(); }
  }
  file.Close();
}
template<class T> using StdVector = std::vector<T>;
void fixture(const std::filesystem::path& path, const std::string& mode) {
  if (mode.starts_with("rvec_")) fixture_impl<ROOT::VecOps::RVec>(path, mode);
  else fixture_impl<StdVector>(path, mode);
}
template<class Fn> void rejected(Fn function, const std::string& reason) {
  bool threw = false;
  try { function(); } catch (const std::exception&) { threw = true; }
  require(threw, reason);
}
}
int main() {
  try {
    const auto directory = std::filesystem::current_path() / ("schema_fixtures_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    require(std::filesystem::create_directory(directory), "New fixture directory required.");
    unsigned cases = 0;
    for (const std::string mode : {"valid", "float_jvt", "rvec_valid", "rvec_short_vector", "missing_trigger", "wrong_type", "short_vector", "negative_count", "nan", "late_nan", "nan_weight", "empty"}) {
      const auto path = directory / (mode + ".root"); fixture(path, mode);
      const auto before_time = std::filesystem::last_write_time(path);
      const auto before_size = std::filesystem::file_size(path);
      const auto result = atlas::schema::inspect(path);
      require(before_time == std::filesystem::last_write_time(path) && before_size == std::filesystem::file_size(path), "Read-only input changed.");
      if (mode == "missing_trigger" || mode == "wrong_type") require(!result.schema_pass && result.entries_inspected == 0, "Schema failure must prevent entry reads.");
      else if (mode == "empty") require(result.schema_pass && !result.structure_pass && result.entries_inspected == 0, "Empty sample cannot pass structural gate.");
      else if (mode == "valid" || mode == "float_jvt" || mode == "late_nan" || mode == "rvec_valid") {
        require(result.schema_pass && result.structure_pass && result.entries_inspected == 10, "Valid bounded fixture failed.");
        require(result.documented_type_difference == (mode != "float_jvt"), "jet_jvt discrepancy must be explicit.");
        const auto field = std::find_if(result.fields.begin(), result.fields.end(), [](const auto& f) { return f.name == "mcWeight"; });
        require(field != result.fields.end() && field->compatibility == "NOT_APPLICABLE", "Missing MC weight must be optional for collision data.");
      } else require(result.schema_pass && !result.structure_pass, "Bad structural content must fail.");
      ++cases;
      if (mode == "valid") {
        atlas::schema::write_manifest(result, directory / "manifest.csv", "synthetic");
        rejected([&] { atlas::schema::write_manifest(result, directory / "manifest.csv", "synthetic"); }, "Existing output must be preserved.");
        rejected([&] { atlas::schema::inspect(path, 11); }, "Limit above ten must be rejected.");
        rejected([&] { atlas::schema::inspect(path, 0); }, "Zero limit must be rejected.");
        require(atlas::schema::inspect(path, 1).entries_inspected == 1, "Explicit smaller limit ignored.");
        cases += 4;
      }
    }
    rejected([] { atlas::schema::inspect("root://example.invalid/file.root"); }, "Remote ROOT URL must be rejected before opening."); ++cases;
    rejected([&] { atlas::schema::inspect(directory / "missing.root"); }, "Missing local input must be rejected."); ++cases;
    fixture(directory / "multiple.root", "multiple");
    rejected([&] { atlas::schema::inspect(directory / "multiple.root"); }, "Ambiguous trees require explicit selection."); ++cases;
    require(atlas::schema::inspect(directory / "multiple.root", 10, "fixture").structure_pass, "Explicit tree selection failed."); ++cases;
    { TFile file((directory / "no_tree.root").c_str(), "RECREATE"); file.Close(); }
    rejected([&] { atlas::schema::inspect(directory / "no_tree.root"); }, "No-tree input must be rejected."); ++cases;
    fixture(directory / "friend.root", "friend");
    rejected([&] { atlas::schema::inspect(directory / "friend.root", 10, "fixture"); }, "Friend trees must be refused before entry access."); ++cases;
    std::cout << "PASS: " << cases << " synthetic structural/safety cases; no physics selection\n";
    return 0;
  } catch (const std::exception& error) { std::cerr << "FAIL: " << error.what() << '\n'; return 1; }
}

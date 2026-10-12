#pragma once
#include "AtlasMCEvents.h"
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace atlas::input_preflight {
enum class EvidenceKind { SyntheticFixture, PhysicalCandidate };
struct KeyInfo { std::string path, native_class; int cycle=0; };
struct TreeInfo { std::string path, native_class; int cycle=0; std::int64_t entries=0; };
struct BranchInfo {
  std::string tree_path, path, name, native_type, native_class, storage_file;
  int tree_cycle=0;
};
struct Result {
  std::filesystem::path canonical_input;
  std::uintmax_t input_bytes=0;
  std::uint32_t expected_dsid=0;
  EvidenceKind evidence_kind=EvidenceKind::SyntheticFixture;
  std::int64_t analysis_entries=0;
  std::vector<KeyInfo> keys;
  std::vector<TreeInfo> trees;
  std::vector<BranchInfo> branches;
  std::vector<mc::NativeField> reader_bindings;
};
// Metadata only: no GetEntry(), SetEntry(), or Reader::read(). A successful
// result establishes local structural/type compatibility, never actual DSID
// values, branch lengths, event physics, units, or provenance.
Result inspect_local_file(const std::filesystem::path& input,
                          std::uint32_t expected_dsid, EvidenceKind evidence_kind);
// All outputs are written into an exclusively created fresh directory. The
// caller must finish inspect_local_file() before requesting output creation.
void write_new_outputs(const Result& result, const std::filesystem::path& output);
}

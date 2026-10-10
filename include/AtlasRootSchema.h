#pragma once
#include <cstddef>
#include <filesystem>
#include <string>
#include <vector>

namespace atlas::schema {
struct Field {
  std::string group, name, actual_type, structure, leaves, expected_type, compatibility;
  bool required = false, present = false;
};
struct Result {
  std::string tree_name;
  std::size_t entries_inspected = 0;
  bool schema_pass = false, structure_pass = false, documented_type_difference = false;
  std::vector<Field> fields;
  std::vector<std::string> issues;
};
// Opens only a regular local file, in READ mode. No remote ROOT access, selection,
// units inference, quantile interpretation, or reconstruction is performed.
Result inspect(const std::filesystem::path& input, std::size_t max_entries = 10,
               const std::string& tree_name = "");
void write_manifest(const Result&, const std::filesystem::path& output,
                    const std::string& evidence);
void write_summary(const Result&, const std::filesystem::path& output);
}  // namespace atlas::schema

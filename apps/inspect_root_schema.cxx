#include "AtlasRootSchema.h"
#include <iostream>
#include <stdexcept>

int main(int argc, char** argv) {
  try {
    std::string input, manifest, summary, tree, evidence;
    std::size_t entries = 10;
    for (int i = 1; i < argc; i += 2) {
      if (i + 1 >= argc) throw std::invalid_argument("Each option requires a value.");
      const std::string key = argv[i], value = argv[i + 1];
      if (key == "--input") input = value;
      else if (key == "--manifest") manifest = value;
      else if (key == "--summary") summary = value;
      else if (key == "--tree") tree = value;
      else if (key == "--evidence") evidence = value;
      else if (key == "--max-entries") {
        if (value.size() > 2 || value.find_first_not_of("0123456789") != std::string::npos) throw std::invalid_argument("Invalid entry limit.");
        entries = std::stoul(value);
      } else throw std::invalid_argument("Unknown option: " + key);
    }
    if (input.empty() || manifest.empty() || summary.empty() || evidence.empty()) throw std::invalid_argument("Required: --input LOCAL_FILE --manifest NEW_CSV --summary NEW_TXT --evidence LABEL [--max-entries 1..10] [--tree NAME]");
    if (std::filesystem::exists(manifest) || std::filesystem::exists(summary)) throw std::invalid_argument("Outputs must be new files.");
    const auto result = atlas::schema::inspect(input, entries, tree);
    atlas::schema::write_manifest(result, manifest, evidence);
    atlas::schema::write_summary(result, summary);
    std::cout << "TREE=" << result.tree_name << " ENTRIES_INSPECTED=" << result.entries_inspected
              << " SCHEMA=" << (result.schema_pass ? "PASS" : "FAIL") << " STRUCTURE=" << (result.structure_pass ? "PASS" : "FAIL/UNKNOWN") << '\n';
    return result.schema_pass && result.structure_pass ? 0 : 2;
  } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}

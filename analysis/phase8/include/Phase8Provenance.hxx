#pragma once
#include "Sha256.hxx"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <set>
#include <string>
namespace atlas_hh::phase8 {
using Json=nlohmann::json;
namespace fs=std::filesystem;
void demand(bool ok,const std::string& why);
std::string file_sha256(const fs::path& path);
Json read_json(const fs::path& path);
void write_json(const fs::path& path,const Json& value);
std::ofstream exclusive_text(const fs::path& path);
void fresh_directory(const fs::path& path);
}

#pragma once
#include "Phase8Statistics.hxx"
#include <filesystem>
namespace phase8 {
inline constexpr std::array<double,6> kappaBenchmarks{-1.,0.,1.,2.,2.5,5.};
struct KappaRow {
 std::size_t sourceOrdinal{};
 std::string sourceHash;
 std::array<double,6> production{},model{},ratio{};
};
std::vector<KappaRow> loadKappaRows(const std::filesystem::path& csv,
 const std::vector<Json>& events,double modelBR,std::size_t expectedSources=1000);
Json analyzeKappa(const std::vector<KappaRow>& rows,const std::vector<Json>& events,
 const Json& edges,const std::filesystem::path& output);
}

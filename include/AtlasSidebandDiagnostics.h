#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

namespace atlas::sidebands {
inline constexpr std::size_t categories=9;
inline constexpr std::array<double,categories> mass_low{105,110,115,130,135,140,145,150,155};
inline constexpr std::array<double,categories> mass_high{110,115,120,135,140,145,150,155,160};
inline constexpr std::string_view protocol_sha256="e9916da8772902c5464ea141397340a5230cb1733bb05e7c86800d9681295f66";
std::string sha256(std::string_view);
std::string sha256_file(const std::filesystem::path&,std::uint64_t limit=64*1024*1024);
std::string canonical_identity(std::uint32_t run,std::uint64_t event);
int identity_fold(std::uint32_t run,std::uint64_t event);
// -1 is outside the two fixed sidebands, including the whole central window.
int mass_category(double mass);
struct Statistic {std::size_t n=0,n_other=0;bool defined=false;long double value=0;};
Statistic pearson(const std::vector<long double>&,const std::vector<long double>&);
std::vector<long double> tied_ranks(const std::vector<long double>&);
Statistic empirical_ks(std::vector<double>,std::vector<double>);
struct Contingency {
  Statistic association;
  std::size_t populated_columns=0,zero_cells=0,cells_below_five=0;
  std::array<std::size_t,2> row_totals{};
};
Contingency cramers_v(const std::array<std::size_t,categories>&,
                     const std::array<std::size_t,categories>&);
struct Shape {
  std::size_t total=0;
  bool defined=false;
  std::array<long double,categories> fraction{};
  std::array<std::array<long double,categories>,categories> covariance{};
};
Shape conditional_shape(const std::array<std::size_t,categories>&);
std::array<long double,2> wilson95(std::size_t successes,std::size_t trials);
}  // namespace atlas::sidebands

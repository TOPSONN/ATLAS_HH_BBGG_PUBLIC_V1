#include <ROOT/RDataFrame.hxx>
#include <TROOT.h>

#include <cmath>
#include <iostream>
#include <stdexcept>

static_assert(__cplusplus == 202002L, "Step 1 requires exactly C++20.");

namespace {
void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
bool close(double actual, double expected) {
  return std::abs(actual - expected) < 1e-12;
}
}

int main() {
  try {
    gROOT->SetBatch(true);
    ROOT::DisableImplicitMT();
    ROOT::RDataFrame input(8);
    auto data = input.Define("x", [](ULong64_t entry) { return static_cast<double>(entry) + 0.5; }, {"rdfentry_"})
                     .Define("square", [](double x) { return x * x; }, {"x"})
                     .Define("transformed", [](double x) { return 2. * x + 1.; }, {"x"});
    auto count = data.Count();
    auto sum = data.Sum<double>("x");
    auto sum_squares = data.Sum<double>("square");
    auto transformed_sum = data.Sum<double>("transformed");
    auto values = data.Take<double>("x");
    auto histogram = data.Histo1D<double>({"synthetic", "In-memory infrastructure fixture", 8, 0., 8.}, "x");
    auto selected = data.Filter([](ULong64_t entry) { return entry % 2 == 0; }, {"rdfentry_"});
    auto selected_count = selected.Count();
    auto selected_sum = selected.Sum<double>("x");

    require(*count == 8, "Entry count differs");
    require(close(*sum, 32.), "Sum differs");
    require(close(*sum_squares, 170.), "Squared transformation differs");
    require(close(*transformed_sum, 72.), "Linear transformation differs");
    require(*selected_count == 4 && close(*selected_sum, 14.), "Synthetic filter output differs");
    require(values->size() == 8, "Materialized column size differs");
    for (std::size_t i = 0; i < values->size(); ++i) {
      require(close((*values)[i], static_cast<double>(i) + 0.5), "Materialized row value differs");
    }
    require(close(histogram->GetEntries(), 8.) && close(histogram->Integral(), 8.), "Histogram count differs");
    require(close(histogram->GetMean(), 4.), "Histogram numerical mean differs");
    for (int bin = 1; bin <= 8; ++bin) require(close(histogram->GetBinContent(bin), 1.), "Histogram bin differs");
    require(close(histogram->GetBinContent(0), 0.) && close(histogram->GetBinContent(9), 0.), "Unexpected flow bins");
    std::cout << "PASS RDataFrame: count=8 sum=32 sum_squares=170 transformed_sum=72 selected_count=4 selected_sum=14\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL RDataFrame: " << error.what() << '\n';
    return 1;
  }
}

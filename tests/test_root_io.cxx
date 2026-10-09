#include <TFile.h>
#include <TH1D.h>
#include <TROOT.h>
#include <TTree.h>

#include <array>
#include <cmath>
#include <filesystem>
#include <iostream>
#include <memory>
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
    const auto output = std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR) / "test_root_io.root";
    {
      TFile file(output.string().c_str(), "RECREATE");
      require(!file.IsZombie() && file.IsWritable(), "Cannot create I/O ROOT file");
      TH1D histogram("weighted", "Synthetic weighted I/O fixture", 4, 0., 4.);
      histogram.SetDirectory(nullptr);
      histogram.Sumw2();
      constexpr std::array<double, 7> values{-0.25, 0.25, 0.75, 1.25, 2.25, 3.25, 4.25};
      constexpr std::array<double, 7> weights{2., 1., 2., 3., 4., 5., 6.};
      for (std::size_t i = 0; i < values.size(); ++i) histogram.Fill(values[i], weights[i]);
      require(histogram.Write() > 0, "Weighted histogram write failed");

      TTree tree("synthetic_rows", "Four deterministic infrastructure rows");
      tree.SetDirectory(nullptr);
      int index = 0;
      double value = 0.;
      require(tree.Branch("index", &index, "index/I") != nullptr, "Index branch creation failed");
      require(tree.Branch("value", &value, "value/D") != nullptr, "Value branch creation failed");
      for (index = 0; index < 4; ++index) {
        value = static_cast<double>(index) + 0.5;
        require(tree.Fill() > 0, "Tree filling failed");
      }
      require(tree.Write() > 0, "Tree write failed");
      file.Close();
    }

    std::unique_ptr<TFile> input(TFile::Open(output.string().c_str(), "READ"));
    require(input && !input->IsZombie(), "Cannot reopen I/O ROOT file");
    TH1D* histogram = nullptr;
    input->GetObject("weighted", histogram);
    require(histogram != nullptr, "Weighted histogram retrieval failed");
    require(histogram->GetNbinsX() == 4, "Histogram bin count differs");
    require(close(histogram->GetEntries(), 7.), "Weighted entries differ");
    require(close(histogram->Integral(), 15.), "Visible-bin weighted integral differs");
    require(close(histogram->Integral(0, 5), 23.), "Integral with flow bins differs");
    constexpr std::array<double, 6> contents{2., 3., 3., 4., 5., 6.};
    constexpr std::array<double, 6> error_squares{4., 5., 9., 16., 25., 36.};
    for (int bin = 0; bin <= 5; ++bin) {
      require(close(histogram->GetBinContent(bin), contents[bin]), "Weighted bin content differs");
      require(close(histogram->GetBinError(bin), std::sqrt(error_squares[bin])), "Stored Sumw2 error differs");
    }
    TTree* tree = nullptr;
    input->GetObject("synthetic_rows", tree);
    require(tree && tree->GetEntries() == 4, "Tree retrieval or row count differs");
    int index = -1;
    double value = -1.;
    require(tree->SetBranchAddress("index", &index) >= 0, "Cannot read index branch");
    require(tree->SetBranchAddress("value", &value) >= 0, "Cannot read value branch");
    for (Long64_t row = 0; row < 4; ++row) {
      require(tree->GetEntry(row) > 0, "Tree row read failed");
      require(index == row && close(value, static_cast<double>(row) + 0.5), "Tree row content differs");
    }
    tree->ResetBranchAddresses();
    std::cout << "PASS ROOT I/O: entries=7 integral=15 flow_integral=23 tree_rows=4\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL ROOT I/O: " << error.what() << '\n';
    return 1;
  }
}

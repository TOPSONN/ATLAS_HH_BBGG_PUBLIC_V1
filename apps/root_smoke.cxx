#include <TFile.h>
#include <TH1D.h>
#include <TROOT.h>

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
    require(gROOT != nullptr, "ROOT initialization failed");
    gROOT->SetBatch(true);
    const auto output = std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR) / "root_smoke.root";
    {
      TFile file(output.string().c_str(), "RECREATE");
      require(!file.IsZombie() && file.IsWritable(), "Cannot create smoke ROOT file");
      TH1D histogram("synthetic_histogram", "Deterministic infrastructure smoke test", 4, 0., 4.);
      histogram.SetDirectory(nullptr);
      for (double value : std::array<double, 8>{0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75}) {
        histogram.Fill(value);
      }
      require(close(histogram.GetEntries(), 8.), "Unexpected entries before writing");
      require(close(histogram.Integral(), 8.), "Unexpected integral before writing");
      require(histogram.Write() > 0, "Histogram write failed");
      file.Close();
    }
    std::unique_ptr<TFile> input(TFile::Open(output.string().c_str(), "READ"));
    require(input && !input->IsZombie(), "Cannot reopen smoke ROOT file");
    TH1D* restored = nullptr;
    input->GetObject("synthetic_histogram", restored);
    require(restored != nullptr, "Histogram is absent or has the wrong type");
    require(close(restored->GetEntries(), 8.), "Read-back entries differ");
    require(close(restored->Integral(), 8.), "Read-back integral differs");
    for (int bin = 1; bin <= 4; ++bin) {
      require(close(restored->GetBinContent(bin), 2.), "Read-back bin content differs");
    }
    require(close(restored->GetBinContent(0), 0.), "Unexpected underflow");
    require(close(restored->GetBinContent(5), 0.), "Unexpected overflow");
    std::cout << "PASS ROOT " << gROOT->GetVersion()
              << " entries=8 integral=8 output=" << output << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL root_smoke: " << error.what() << '\n';
    return 1;
  }
}

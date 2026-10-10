#include "AtlasLocalEvents.h"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
int main(int argc, char** argv) {
  try {
    if (argc != 5) throw std::invalid_argument("Usage: probe_kinematic_units local.root output.csv start exclusive_end (<=100)");
    const auto start = std::stoll(argv[3]), end = std::stoll(argv[4]);
    if (start < 0 || end <= start || end > 100) throw std::invalid_argument("Probe range must be within [0,100)");
    if (std::filesystem::exists(argv[2])) throw std::runtime_error("Output exists; refusing duplicate probe/overwrite");
    atlas::events::Reader reader(argv[1]);
    if (end > reader.entries()) throw std::out_of_range("Probe exceeds available entries");
    std::ofstream out(argv[2]); out.exceptions(std::ios::failbit | std::ios::badbit);
    out << "entry,collection,index,count,pt,eta,phi,energy\n" << std::setprecision(17);
    for (auto i = start; i < end; ++i) {
      const auto event = reader.read(i);
      auto emit = [&](const char* kind, const auto& pt, const auto& eta, const auto& phi, const auto& energy) {
        for (std::size_t j = 0; j < pt.size(); ++j)
          out << i << ',' << kind << ',' << j << ',' << pt.size() << ',' << pt[j] << ',' << eta[j] << ',' << phi[j] << ',' << energy[j] << '\n';
      };
      emit("photon", event.photon_pt, event.photon_eta, event.photon_phi, event.photon_e);
      emit("jet", event.jet_pt, event.jet_eta, event.jet_phi, event.jet_e);
    }
    std::cout << "PROBE_START=" << start << "\nPROBE_END_EXCLUSIVE=" << end << "\nUNIQUE_ENTRIES=" << end-start
              << "\nTREE_ENTRIES=" << reader.entries() << "\nNo invariant-mass reconstruction or plots performed.\n";
    return 0;
  } catch (const std::exception& error) { std::cerr << "FAIL: " << error.what() << '\n'; return 1; }
}

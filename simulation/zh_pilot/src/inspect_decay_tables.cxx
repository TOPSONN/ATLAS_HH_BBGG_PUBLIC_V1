#include <Pythia8/Pythia.h>
#include "Json.hxx"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

using Pythia8::Pythia;
using atlas_hh::quoted;
using atlas_hh::real;

void table(std::ostream& out, Pythia& p, int id, bool initialized) {
  auto entry = p.particleData.particleDataEntryPtr(id);
  if (!entry) throw std::runtime_error("Missing resonance");
  out << "{\"pdg_id\":" << id << ",\"mass_gev\":" << quoted(real(entry->m0()))
      << ",\"total_width_gev\":" << quoted(real(entry->mWidth()))
      << ",\"is_resonance\":" << (entry->isResonance() ? "true" : "false")
      << ",\"may_decay\":" << (entry->mayDecay() ? "true" : "false")
      << ",\"channels\":[";
  bool first = true;
  double enabledSum = 0.;
  for (int i = 0; i < entry->sizeChannels(); ++i) {
    const auto& ch = entry->channel(i);
    if (!first) out << ',';
    first = false;
    out << "{\"index\":" << i << ",\"on_mode\":" << ch.onMode()
        << ",\"stored_inclusive_br\":" << quoted(real(ch.bRatio()))
        << ",\"me_mode\":" << ch.meMode() << ",\"partial_width_gev\":";
    if (initialized) out << quoted(real(ch.onShellWidth()));
    else out << "null";
    out << ",\"products\":[";
    for (int j = 0; j < ch.multiplicity(); ++j) {
      if (j) out << ',';
      out << ch.product(j);
    }
    out << "]}";
    if (ch.onMode() == 1 || ch.onMode() == 2) enabledSum += ch.bRatio();
  }
  out << "],\"enabled_stored_br_sum\":" << quoted(real(enabledSum))
      << ",\"enabled_sum_scope\":\"table diagnostic, not a cross-section BR factor\"}";
}

void state(std::ostream& out, Pythia& p, bool initialized) {
  out << "{\"initialized_without_process\":" << (initialized ? "true" : "false")
      << ",\"n_accepted\":" << p.info.nAccepted()
      << ",\"event_record_size\":" << p.event.size()
      << ",\"process_level_all\":" << (p.settings.flag("ProcessLevel:all") ? "true" : "false")
      << ",\"parton_level_all\":" << (p.settings.flag("PartonLevel:all") ? "true" : "false")
      << ",\"hadron_level_all\":" << (p.settings.flag("HadronLevel:all") ? "true" : "false")
      << ",\"slha_read_from\":" << p.settings.mode("SLHA:readFrom")
      << ",\"pdf_p_set\":" << quoted(p.settings.word("PDF:pSet"))
      << ",\"frame_type\":" << p.settings.mode("Beams:frameType") << ",\"Z\":";
  table(out, p, 23, initialized);
  out << ",\"H\":";
  table(out, p, 25, initialized);
  out << '}';
}

std::unique_ptr<Pythia> setup(const char* xml, const char* baseline, const char* overlay,
                            bool forceZ, bool forceH) {
  auto p = std::make_unique<Pythia>(xml, false);
  if (!p->readFile(baseline)) throw std::runtime_error("Reviewed baseline failed to parse");
  const std::vector<std::string> common = {
    "Beams:frameType = 1", "Beams:eCM = 13000", "ProcessLevel:all = off",
    "PartonLevel:all = off", "HadronLevel:all = off", "Random:seed = 610601",
    "23:m0 = 91.188", "25:m0 = 125.0", "SLHA:readFrom = 0", "Init:showChangedSettings = off",
    "Init:showChangedParticleData = off", "Check:event = off"};
  for (const auto& command : common)
    if (!p->readString(command)) throw std::runtime_error("Common no-event setting rejected");
  if (forceZ)
    for (const auto& command : {"23:onMode = off", "23:onIfMatch = 5 -5"})
      if (!p->readString(command)) throw std::runtime_error("Exact Z switch rejected");
  if (forceH && !forceZ) {
    if (!p->readFile(overlay)) throw std::runtime_error("Exact preferred overlay rejected");
  } else if (forceH)
    for (const auto& command : {"25:onMode = off", "25:onIfMatch = 22 22"})
      if (!p->readString(command)) throw std::runtime_error("Exact H switch rejected");
  return p;
}

int main(int argc, char** argv) {
  try {
    if (argc != 5) throw std::runtime_error("Usage: probe XML BASELINE PREFERRED_OVERLAY OUTPUT_JSON");
    std::ofstream out(argv[4]);
    if (!out) throw std::runtime_error("Cannot create probe JSON");
    auto original = std::make_unique<Pythia>(argv[1], false);
    out << "{\"schema_version\":1,\"pythia_version\":\"8.317\",\"pythia_version_integer\":"
        << PYTHIA_VERSION_INTEGER << ",\"status\":\"PASS_NO_EVENT_DECAY_TABLE_PROBE\","
        << "\"physical_events_generated\":0,\"next_calls\":0,\"original_xml_tables\":";
    state(out, *original, false);
    for (const auto& mode : {std::string("inclusive"), std::string("forced_A_Z_and_H"), std::string("preferred_B_H_only")}) {
      auto p = setup(argv[1], argv[2], argv[3], mode == "forced_A_Z_and_H", mode != "inclusive");
      out << ',' << quoted(mode + "_before_init") << ':';
      state(out, *p, false);
      if (!p->init()) throw std::runtime_error("ProcessLevel-off initialization failed");
      if (p->info.nAccepted() != 0) throw std::runtime_error("Unexpected accepted event count");
      out << ',' << quoted(mode + "_after_init") << ':';
      state(out, *p, true);
    }
    out << "}\n";
    if (!out) throw std::runtime_error("Probe write failed");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}

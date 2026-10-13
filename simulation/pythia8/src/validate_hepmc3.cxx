// Independent readback with the installed HepMC3 library and Pythia PDG table.
// This executable never generates, repairs, filters, or rewrites any event.
#include "HepMC3/GenEvent.h"
#include "HepMC3/GenParticle.h"
#include "HepMC3/GenVertex.h"
#include "HepMC3/ReaderAscii.h"
#include "HepMC3/Version.h"
#include "Pythia8/Pythia.h"
#include "Sha256.hxx"

#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr double closure_atol = 1e-5;
constexpr double closure_rtol = 1e-9;
constexpr double shell_atol = 1e-7;
constexpr double shell_rtol = 1e-9;
constexpr std::size_t max_failure_details = 64;

void require(bool ok, const std::string& reason) {
  if (!ok) throw std::runtime_error(reason);
}

bool finite(const HepMC3::FourVector& p) {
  return std::isfinite(p.x()) && std::isfinite(p.y()) &&
         std::isfinite(p.z()) && std::isfinite(p.t());
}

std::array<double, 4> components(const HepMC3::FourVector& p) {
  return {p.px(), p.py(), p.pz(), p.e()};
}

std::string quoted(const std::string& text) {
  std::string result = "\"";
  for (char c : text) {
    if (c == '\\' || c == '"') result += '\\';
    if (c == '\n') result += "\\n";
    else if (c == '\r') result += "\\r";
    else result += c;
  }
  return result + '"';
}

struct Options {
  std::string input, report, xml, source_hash, sample_id;
  long events = -1;
  int seed = -1;
  bool format_smoke = false;
};

Options options(int argc, char** argv) {
  Options opt;
  for (int i = 1; i < argc; ++i) {
    std::string key = argv[i];
    if (key == "--format-smoke") { opt.format_smoke = true; continue; }
    require(i + 1 < argc, "missing value for " + key);
    std::string value = argv[++i];
    if (key == "--input") opt.input = value;
    else if (key == "--events") opt.events = std::stol(value);
    else if (key == "--report") opt.report = value;
    else if (key == "--xml") opt.xml = value;
    else if (key == "--source-sha256") opt.source_hash = value;
    else if (key == "--sample-id") opt.sample_id = value;
    else if (key == "--seed") opt.seed = std::stoi(value);
    else throw std::runtime_error("unknown option: " + key);
  }
  require(!opt.input.empty() && !opt.xml.empty() && opt.events > 0,
          "required: --input plain.hepmc3 --xml installed/xmldoc --events positive_count");
  return opt;
}

void complete_ascii(const std::string& path) {
  std::ifstream input(path);
  require(input.good(), "cannot open HepMC3 input");
  std::string line;
  bool version = false, start = false, end = false;
  while (std::getline(input, line)) {
    require(line.size() < 1024 * 1024, "overlong ASCII line");
    if (line.rfind("HepMC::Version ", 0) == 0) {
      require(!version && !start, "duplicate/out-of-order version line");
      version = true;
    } else if (line == "HepMC::Asciiv3-START_EVENT_LISTING") {
      require(version && !start, "duplicate/out-of-order start marker");
      start = true;
    } else if (line == "HepMC::Asciiv3-END_EVENT_LISTING") {
      require(start && !end, "duplicate/out-of-order end marker");
      end = true;
    } else if (end) {
      require(line.empty(), "data after HepMC3 end marker");
    }
  }
  require(input.eof() && version && start && end, "incomplete HepMC3 ASCII envelope");
}

struct Failure {
  long output_index = 0, source_index = -1;
  int particle_id = 0, pdg_id = 0, status = 0;
  std::string reason;
  bool mass_shell = false;
  std::array<double, 4> p4{};
  double mass = 0, signed_shell = 0, residual = 0, tolerance = 0;
  double calculated_mass = 0, energy_difference = 0, native_mass_fraction = 0;
};

struct Summary {
  long readback = 0, passed = 0, failed = 0, failure_count = 0, shell_failed_particles = 0;
  long events = 0, particles = 0, vertices = 0, stable = 0, charged = 0;
  long positive = 0, negative = 0, zero = 0;
  long min_stable = -1, max_stable = 0;
  long stable_colored = 0, stable_quarks = 0, stable_gluons = 0, stable_diquarks = 0;
  long double sum_w = 0, sum_abs_w = 0, sum_w2 = 0;
  double max_residual = 0, max_stable_shell = 0, max_shell_ratio = 0, max_native_mass_fraction = 0;
  std::map<int, long> statuses, pdg_counts, photon_hist, b_hadron_hist, c_hadron_hist;
  std::map<int, long> stable_b_hadron_hist, stable_c_hadron_hist;
  std::string source_hash, sample_id, run_id, input_hash;
  int seed = 0;
  int first_event_number = -1;
  std::vector<Failure> failures;
  std::string fatal_error;
};

void failure(Summary& summary, Failure detail) {
  ++summary.failure_count;
  if (summary.failures.size() < max_failure_details) summary.failures.push_back(std::move(detail));
}

void event_check(const HepMC3::GenEvent& event, Pythia8::ParticleData& data,
                 const Options& opt, Summary& summary) {
  const long index = summary.readback;
  require(event.event_number() == (opt.format_smoke ? summary.first_event_number + index - 1 : index) &&
          event.event_number() >= 0, "non-sequential output event number");
  require(event.momentum_unit() == HepMC3::Units::GEV && event.length_unit() == HepMC3::Units::MM,
          "event units must be GeV/mm");
  require(!event.particles().empty() && !event.vertices().empty(), "empty event graph");
  require(!event.weights().empty(), "event weights missing");
  for (double weight : event.weights()) require(std::isfinite(weight), "non-finite event weight");
  const double weight = event.weights().front();
  summary.sum_w += weight;
  summary.sum_abs_w += std::abs(weight);
  summary.sum_w2 += static_cast<long double>(weight) * weight;
  ++(weight > 0 ? summary.positive : weight < 0 ? summary.negative : summary.zero);
  if (!opt.format_smoke) {
  auto attribute = [&](const std::string& name) { return event.attribute_as_string(name); };
  require(std::stol(attribute("output_event_index")) == index, "output identity attribute mismatch");
  require(std::stol(attribute("source_event_index")) > 0, "source event index missing");
  require(attribute("source_event_content_hash").size() == 64 && attribute("source_file_sha256").size() == 64,
          "source hash attributes missing");
  require(!attribute("source_sample_id").empty() && !attribute("pythia_run_id").empty(), "source/run identity missing");
  if (!opt.source_hash.empty()) require(attribute("source_file_sha256") == opt.source_hash, "source file identity mismatch");
  if (!opt.sample_id.empty()) require(attribute("source_sample_id") == opt.sample_id, "source sample identity mismatch");
  if (opt.seed >= 0) require(std::stoi(attribute("pythia_seed")) == opt.seed, "Pythia seed mismatch");
  if (summary.run_id.empty()) {
    summary.source_hash = attribute("source_file_sha256");
    summary.sample_id = attribute("source_sample_id");
    summary.run_id = attribute("pythia_run_id");
    summary.seed = std::stoi(attribute("pythia_seed"));
  }
  require(summary.source_hash == attribute("source_file_sha256") &&
          summary.sample_id == attribute("source_sample_id") && summary.run_id == attribute("pythia_run_id") &&
          summary.seed == std::stoi(attribute("pythia_seed")), "mixed source/run/seed metadata");
  require(event.run_info() && event.run_info()->weight_names().size() == event.weights().size() &&
          event.weights().size() >= 4, "missing/incorrect named weight vector");
  const auto& names = event.run_info()->weight_names();
  require(names[0] == "input_contribution_pb" && names[1] == "LHE_XWGTUP_pb" &&
          names[2] == "Pythia_Info_weight_pb", "named weight interpretation mismatch");
  }

  std::map<int, HepMC3::ConstGenParticlePtr> particles;
  std::map<int, HepMC3::ConstGenVertexPtr> vertices;
  for (const auto& vertex : event.vertices()) {
    require(vertex->id() < 0 && vertices.emplace(vertex->id(), vertex).second, "duplicate/invalid vertex ID");
    require(vertex->parent_event() == &event && finite(vertex->position()), "invalid vertex owner/position");
    require(!vertex->particles_in().empty() && !vertex->particles_out().empty(), "dangling empty vertex");
  }
  for (const auto& particle : event.particles()) {
    require(particle->id() > 0 && particles.emplace(particle->id(), particle).second, "duplicate/invalid particle ID");
    require(particle->parent_event() == &event && finite(particle->momentum()) &&
            std::isfinite(particle->generated_mass()), "invalid particle owner/four-vector/mass");
    require(particle->pid() != 0 && data.isParticle(particle->pid()), "PDG ID absent from installed Pythia ParticleData");
    const int status = particle->status();
    require((status == 1 || status == 2 || status == 4 || (status >= 11 && status <= 200)) &&
            particle->momentum().e() >= 0, "invalid Pythia/HepMC particle status/energy");
    ++summary.statuses[particle->status()];
    ++summary.pdg_counts[particle->pid()];
  }
  for (const auto& [id, vertex] : vertices) {
    std::set<int> ins, outs;
    for (const auto& incoming : vertex->particles_in()) {
      require(particles.count(incoming->id()) && particles.at(incoming->id()) == incoming &&
              ins.insert(incoming->id()).second && incoming->end_vertex() == vertex,
              "inconsistent incoming vertex endpoint");
    }
    for (const auto& outgoing : vertex->particles_out()) {
      require(particles.count(outgoing->id()) && particles.at(outgoing->id()) == outgoing &&
              outs.insert(outgoing->id()).second && outgoing->production_vertex() == vertex && !ins.count(outgoing->id()),
              "inconsistent outgoing vertex endpoint/self-link");
    }
  }
  std::array<long double, 4> incoming{}, stable{};
  long beam_count = 0, stable_count = 0, charged_count = 0, charge_in = 0, charge_out = 0;
  long photons = 0, b_hadrons = 0, c_hadrons = 0, stable_b_hadrons = 0, stable_c_hadrons = 0;
  long stable_colored = 0;
  for (const auto& [id, particle] : particles) {
    auto production = particle->production_vertex();
    auto end = particle->end_vertex();
    require(!production || production->id() == 0 || vertices.count(production->id()), "dangling production vertex");
    require(!end || vertices.count(end->id()), "dangling end vertex");
    if (particle->status() == 4) {
      require(particle->pid() == 2212 && (!production || production->id() == 0) && end,
              "invalid full proton beam record");
      require(std::abs(particle->momentum().e() - 6500) <= 1e-6, "beam energy differs from input 6500 GeV");
      ++beam_count;
      charge_in += data.chargeType(particle->pid());
      const auto vector = components(particle->momentum());
      for (int component = 0; component < 4; ++component) incoming[component] += vector[component];
    } else {
      require(production && production->id() != 0, "orphan non-beam particle");
    }
    if (particle->status() == 1) {
      require(!end, "stable final particle has descendants");
      ++stable_count;
      if (data.colType(particle->pid()) != 0) ++stable_colored;
      if (data.isQuark(particle->pid())) ++summary.stable_quarks;
      if (data.isGluon(particle->pid())) ++summary.stable_gluons;
      if (data.isDiquark(particle->pid())) ++summary.stable_diquarks;
      const int charge = data.chargeType(particle->pid());
      charge_out += charge;
      if (charge) ++charged_count;
      const auto vector = components(particle->momentum());
      for (int component = 0; component < 4; ++component) stable[component] += vector[component];
      const auto& p = particle->momentum();
      const double mass = particle->generated_mass();
      const double m2 = p.e()*p.e() - p.px()*p.px() - p.py()*p.py() - p.pz()*p.pz();
      const double signed_shell = m2 - mass*mass;
      const double shell = std::abs(signed_shell);
      const double tolerance = shell_atol + shell_rtol * std::max(p.e()*p.e(), 1.0);
      require(mass >= 0 && std::isfinite(m2) && std::isfinite(shell) && std::isfinite(tolerance),
              "invalid/overflowing stable-particle mass-shell calculation");
      const double calculated_mass = m2 >= 0 ? std::sqrt(m2) : -std::sqrt(-m2);
      const double native_fraction = std::abs(calculated_mass - mass) / std::max(1.0, p.e());
      summary.max_stable_shell = std::max(summary.max_stable_shell, shell);
      summary.max_shell_ratio = std::max(summary.max_shell_ratio, shell / tolerance);
      summary.max_native_mass_fraction = std::max(summary.max_native_mass_fraction, native_fraction);
      if (shell > tolerance) {
        Failure detail;
        detail.output_index = index;
        const auto source = event.attribute_as_string("source_event_index");
        if (!source.empty()) detail.source_index = std::stol(source);
        detail.particle_id = id; detail.pdg_id = particle->pid(); detail.status = particle->status();
        detail.reason = "stable-particle mass-shell failure"; detail.mass_shell = true;
        detail.p4 = components(p); detail.mass = mass; detail.signed_shell = signed_shell;
        detail.residual = shell; detail.tolerance = tolerance; detail.calculated_mass = calculated_mass;
        detail.energy_difference = p.e() - std::sqrt(p.px()*p.px() + p.py()*p.py() + p.pz()*p.pz() + mass*mass);
        detail.native_mass_fraction = native_fraction;
        ++summary.shell_failed_particles;
        failure(summary, std::move(detail));
      }
      if (particle->pid() == 22) ++photons;
    } else {
      require(static_cast<bool>(end), "non-final particle has no end vertex");
    }
    if (data.isHadron(particle->pid())) {
      if (data.nQuarksInCode(particle->pid(), 5) > 0) {
        ++b_hadrons;
        if (particle->status() == 1) ++stable_b_hadrons;
      }
      if (data.nQuarksInCode(particle->pid(), 4) > 0) {
        ++c_hadrons;
        if (particle->status() == 1) ++stable_c_hadrons;
      }
    }
  }
  require(beam_count == 2 && stable_count > 0, "missing beams/stable final state");
  summary.stable_colored += stable_colored;
  require(stable_colored == 0, "incomplete baseline hadronization: stable colored particle remains");
  require(charge_in == charge_out, "full beam-to-stable electric-charge conservation failure");
  for (int component = 0; component < 4; ++component) {
    const double residual = std::abs(incoming[component] - stable[component]);
    summary.max_residual = std::max(summary.max_residual, residual);
    require(residual <= closure_atol + closure_rtol * incoming[3], "full beam-to-stable four-momentum closure failure");
  }
  std::map<int, int> colors;
  std::function<void(int)> visit = [&](int id) {
    require(colors[id] != 1, "cycle in mother/descendant graph");
    if (colors[id] == 2) return;
    colors[id] = 1;
    auto end = particles.at(id)->end_vertex();
    if (end) for (const auto& child : end->particles_out()) visit(child->id());
    colors[id] = 2;
  };
  for (const auto& [id, particle] : particles) if (particle->status() == 4) visit(id);
  require(colors.size() == particles.size(), "particle disconnected from full beam graph");
  ++summary.events;
  summary.particles += particles.size();
  summary.vertices += vertices.size();
  summary.stable += stable_count;
  summary.charged += charged_count;
  summary.min_stable = summary.min_stable < 0 ? stable_count : std::min(summary.min_stable, stable_count);
  summary.max_stable = std::max(summary.max_stable, stable_count);
  ++summary.photon_hist[photons];
  ++summary.b_hadron_hist[b_hadrons];
  ++summary.c_hadron_hist[c_hadrons];
  ++summary.stable_b_hadron_hist[stable_b_hadrons];
  ++summary.stable_c_hadron_hist[stable_c_hadrons];
}

void json_map(std::ostream& out, const std::map<int, long>& values) {
  out << '{';
  bool first = true;
  for (const auto& [key, value] : values) {
    if (!first) out << ',';
    first = false;
    out << quoted(std::to_string(key)) << ':' << value;
  }
  out << '}';
}

void report(std::ostream& out, const Summary& s, const Options& opt) {
  const bool passed = s.failed == 0 && s.fatal_error.empty() && s.readback == opt.events;
  out << std::setprecision(17) << "{\n\"validation_status\":" << quoted(passed ? "PASS" : "FAIL") << ",\n"
      << "\"validator\":" << quoted(opt.format_smoke ? "actual_HepMC3_ReaderAscii_and_Pythia_ParticleData_UNTRACKED_SMOKE"
                                      : "actual_HepMC3_ReaderAscii_and_Pythia_ParticleData") << ",\n"
      << "\"source_identity\":" << quoted(opt.format_smoke ? "NOT_EVALUATED" : passed ? "ATTRIBUTES_VERIFIED" : "SEE_EVENT_FAILURES") << ",\n"
      << "\"hepmc3_version\":" << quoted(HepMC3::version()) << ",\n"
      << "\"pythia_version\":" << quoted(std::to_string(PYTHIA_VERSION).substr(0, 5)) << ",\n"
      << "\"decompressed_file_sha256\":" << quoted(s.input_hash) << ",\n"
      << "\"source_file_sha256\":" << quoted(s.source_hash) << ",\n"
      << "\"source_sample_id\":" << quoted(s.sample_id) << ",\n"
      << "\"pythia_run_id\":" << quoted(s.run_id) << ",\n\"pythia_seed\":" << s.seed << ",\n"
      << "\"N_requested_validation\":" << opt.events << ",\n"
      << "\"N_readback\":" << s.readback << ",\n\"N_passed_validation\":" << s.passed << ",\n"
      << "\"N_failed_validation\":" << s.failed << ",\n"
      << "\"N_not_assessed\":" << std::max(0L, opt.events - s.readback) << ",\n"
      << "\"N_events_with_complete_physics_assessment\":" << s.events << ",\n"
      << "\"summary_scope\":\"All events completing graph/metadata/global checks, including explicitly listed mass-shell failures; events aborting assessment excluded from distributions\",\n"
      << "\"fatal_error\":" << (s.fatal_error.empty() ? "null" : quoted(s.fatal_error)) << ",\n"
      << "\"total_particles\":" << s.particles << ",\n\"total_vertices\":" << s.vertices << ",\n"
      << "\"mean_final_multiplicity\":";
  if (s.events) out << double(s.stable)/s.events; else out << "null";
  out << ",\n\"mean_charged_final_multiplicity\":";
  if (s.events) out << double(s.charged)/s.events; else out << "null";
  out << ",\n"
      << "\"min_final_multiplicity\":" << s.min_stable << ",\n\"max_final_multiplicity\":" << s.max_stable << ",\n"
      << "\"max_beam_to_stable_residual_gev\":" << s.max_residual << ",\n"
      << "\"stable_colored_particle_count\":" << s.stable_colored << ",\n"
      << "\"stable_free_quark_count\":" << s.stable_quarks << ",\n"
      << "\"stable_free_gluon_count\":" << s.stable_gluons << ",\n"
      << "\"stable_free_diquark_count\":" << s.stable_diquarks << ",\n"
      << "\"hadronization_completion_test\":\"No stable ParticleData.colType!=0 object; no filtering\",\n"
      << "\"max_stable_mass_shell_residual_gev2\":" << s.max_stable_shell << ",\n"
      << "\"max_stable_mass_shell_residual_to_tolerance\":" << s.max_shell_ratio << ",\n"
      << "\"max_stable_energy_normalized_mass_difference\":" << s.max_native_mass_fraction << ",\n"
      << "\"mass_shell_atol_gev2\":" << shell_atol << ",\n\"mass_shell_rtol_energy_squared\":" << shell_rtol << ",\n"
      << "\"mass_shell_test\":\"abs(E^2-|p|^2-m_generated^2) <= 1e-7 GeV^2 + 1e-9*max(E^2,1 GeV^2); generator-native mass fraction is diagnostic only, never an alternate acceptance gate\",\n"
      << "\"mass_shell_failed_particle_count\":" << s.shell_failed_particles << ",\n"
      << "\"closure_atol_gev\":" << closure_atol << ",\n\"closure_rtol\":" << closure_rtol << ",\n"
      << "\"beam_remnants_included\":true,\n\"intermediate_particles_excluded_from_global_sum\":true,\n"
      << "\"weight_sum\":" << s.sum_w << ",\n\"weight_abs_sum\":" << s.sum_abs_w << ",\n"
      << "\"weight_sum_squared\":" << s.sum_w2 << ",\n"
      << "\"positive_weights\":" << s.positive << ",\n\"negative_weights\":" << s.negative << ",\n\"zero_weights\":" << s.zero << ",\n"
      << "\"particle_status_counts\":"; json_map(out, s.statuses);
  out << ",\n\"particle_pdg_counts\":"; json_map(out, s.pdg_counts);
  out << ",\n\"final_photon_multiplicity_histogram\":"; json_map(out, s.photon_hist);
  out << ",\n\"all_record_b_hadron_multiplicity_histogram\":"; json_map(out, s.b_hadron_hist);
  out << ",\n\"all_record_c_hadron_multiplicity_histogram\":"; json_map(out, s.c_hadron_hist);
  out << ",\n\"stable_b_hadron_multiplicity_histogram\":"; json_map(out, s.stable_b_hadron_hist);
  out << ",\n\"stable_c_hadron_multiplicity_histogram\":"; json_map(out, s.stable_c_hadron_hist);
  out << ",\n\"heavy_hadron_count_definition\":\"inclusive installed ParticleData.nQuarksInCode(pid,5/4)>0; particle/antiparticle symmetric; B_c appears in both categories; all-record and stable are separate; no direct-hard-origin assignment\"";
  out << ",\n\"failure_detail_count\":" << s.failure_count
      << ",\n\"failure_details_truncated\":" << (s.failure_count > long(s.failures.size()) ? "true" : "false")
      << ",\n\"failures\":[";
  bool first = true;
  for (const auto& detail : s.failures) {
    if (!first) out << ',';
    first = false;
    out << "{\"output_event_index\":" << detail.output_index << ",\"source_event_index\":";
    if (detail.source_index >= 0) out << detail.source_index; else out << "null";
    out << ",\"reason\":" << quoted(detail.reason);
    if (detail.mass_shell) {
      out << ",\"particle_id\":" << detail.particle_id << ",\"pdg_id\":" << detail.pdg_id
          << ",\"status\":" << detail.status << ",\"p4_gev\":[";
      for (int component = 0; component < 4; ++component) {
        if (component) out << ',';
        out << detail.p4[component];
      }
      out << "],\"generated_mass_gev\":" << detail.mass
          << ",\"calculated_mass_gev\":" << detail.calculated_mass
          << ",\"signed_mass_shell_residual_gev2\":" << detail.signed_shell
          << ",\"mass_shell_residual_gev2\":" << detail.residual
          << ",\"mass_shell_tolerance_gev2\":" << detail.tolerance
          << ",\"energy_difference_gev\":" << detail.energy_difference
          << ",\"energy_normalized_mass_difference\":" << detail.native_mass_fraction;
    }
    out << '}';
  }
  out << ']';
  out << "\n}\n";
}
} // namespace

int main(int argc, char** argv) {
  Options opt;
  Summary summary;
  try {
    opt = options(argc, argv);
    std::ifstream hashing_input(opt.input, std::ios::binary);
    require(hashing_input.good(), "cannot open HepMC3 input for hashing");
    atlas_hh::Sha256 hash;
    std::array<char, 65536> buffer{};
    while (hashing_input.read(buffer.data(), buffer.size()) || hashing_input.gcount())
      hash.update(buffer.data(), hashing_input.gcount());
    require(hashing_input.eof(), "failed input hashing");
    summary.input_hash = hash.finish();
    complete_ascii(opt.input);
    Pythia8::Pythia database(opt.xml, false);
    require(database.particleData.isParticle(2212) && database.particleData.isParticle(22) &&
            database.particleData.chargeType(2212) == 3, "Pythia particle table did not load");
    HepMC3::ReaderAscii reader(opt.input);
    while (true) {
      HepMC3::GenEvent event;
      if (!reader.read_event(event) || reader.failed()) break;
      ++summary.readback;
      if (summary.readback == 1) summary.first_event_number = event.event_number();
      // Commit event distributions only after completing assessment.  A physics
      // failure remains a failure while subsequent immutable records are read.
      Summary inspected = summary;
      try {
        require(summary.readback <= opt.events, "read past requested output event count");
        event_check(event, database.particleData, opt, inspected);
        if (inspected.failure_count == summary.failure_count) ++inspected.passed;
        else ++inspected.failed;
        summary = std::move(inspected);
      } catch (const std::exception& error) {
        // Preserve any mass-shell diagnostics reached before another check
        // aborted this event, without adding partial multiplicity distributions.
        summary.max_stable_shell = std::max(summary.max_stable_shell, inspected.max_stable_shell);
        summary.max_residual = std::max(summary.max_residual, inspected.max_residual);
        summary.max_shell_ratio = std::max(summary.max_shell_ratio, inspected.max_shell_ratio);
        summary.max_native_mass_fraction = std::max(summary.max_native_mass_fraction, inspected.max_native_mass_fraction);
        summary.shell_failed_particles = inspected.shell_failed_particles;
        summary.failure_count = inspected.failure_count;
        summary.failures = std::move(inspected.failures);
        Failure detail;
        detail.output_index = summary.readback;
        detail.reason = error.what();
        try {
          const auto source = event.attribute_as_string("source_event_index");
          if (!source.empty()) detail.source_index = std::stol(source);
        } catch (const std::exception&) { /* corrupt source field recorded by event check */ }
        failure(summary, std::move(detail));
        ++summary.failed;
      }
    }
    reader.close();
    require(summary.readback == opt.events, "ReaderAscii event count mismatch or parse failure");
  } catch (const std::exception& error) {
    summary.fatal_error = error.what();
  }
  try {
    if (!opt.report.empty()) {
      std::ofstream output(opt.report);
      require(output.good(), "cannot write validation report");
      report(output, summary, opt);
      require(output.good(), "failed writing validation report");
    }
    report(std::cout, summary, opt);
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
  if (summary.failed || !summary.fatal_error.empty() || summary.readback != opt.events) {
    if (!summary.fatal_error.empty()) std::cerr << "FAIL: " << summary.fatal_error << '\n';
    for (const auto& detail : summary.failures) {
      std::cerr << "FAIL: output event " << detail.output_index << " source event " << detail.source_index
                << ": " << detail.reason;
      if (detail.mass_shell)
        std::cerr << std::setprecision(17) << "; particle " << detail.particle_id << " PDG " << detail.pdg_id
                  << "; residual " << detail.residual << " GeV^2 > tolerance " << detail.tolerance << " GeV^2";
      std::cerr << '\n';
    }
    return 1;
  }
  return 0;
}

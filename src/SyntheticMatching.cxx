#include "AtlasSyntheticMatching.h"
#include "AtlasKinematics.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>

namespace atlas::matching {
namespace {
std::optional<double> fraction(std::size_t numerator, std::size_t denominator) {
  if (!denominator) return std::nullopt;
  return static_cast<double>(numerator) / static_cast<double>(denominator);
}
std::vector<Direction> validated(const std::vector<Direction>& input) {
  std::unordered_set<std::uint64_t> ids;
  std::vector<Direction> eligible;
  for (const auto& object : input) {
    if (!ids.insert(object.id).second) throw std::invalid_argument("Duplicate geometric matching ID");
    if (!std::isfinite(object.eta) || !std::isfinite(object.phi))
      throw std::invalid_argument("Nonfinite geometric matching direction");
    if (object.eligible) eligible.push_back(object);
  }
  std::sort(eligible.begin(), eligible.end(), [](const auto& a, const auto& b) { return a.id < b.id; });
  return eligible;
}
struct Edge { std::size_t to, reverse; int capacity; long double cost; };
using Network = std::vector<std::vector<Edge>>;
void add_edge(Network& network, std::size_t from, std::size_t to, long double cost) {
  const auto forward_index = network[from].size(), reverse_index = network[to].size();
  network[from].push_back({to, reverse_index, 1, cost});
  network[to].push_back({from, forward_index, 0, -cost});
}
struct CandidateEdge { std::size_t reco, reference, index; double delta_r; };
}  // namespace

std::optional<double> Result::reference_match_fraction() const { return fraction(assignments.size(), eligible_reference); }
std::optional<double> Result::reco_match_fraction() const { return fraction(assignments.size(), eligible_reco); }
std::optional<double> Result::reference_unmatched_fraction() const { return fraction(unmatched_reference_ids.size(), eligible_reference); }
std::optional<double> Result::reco_unmatched_fraction() const { return fraction(unmatched_reco_ids.size(), eligible_reco); }

Result match(const std::vector<Direction>& reco_input,
             const std::vector<Direction>& synthetic_reference, double max_delta_r) {
  if (!std::isfinite(max_delta_r) || max_delta_r <= 0)
    throw std::invalid_argument("Matching threshold must be positive and finite");
  const auto reco = validated(reco_input), reference = validated(synthetic_reference);
  Result result; result.eligible_reco = reco.size(); result.eligible_reference = reference.size();
  if (reco.size() > std::numeric_limits<std::size_t>::max() - reference.size() - 2)
    throw std::length_error("Geometric matching network size overflow");
  const std::size_t source = 0, reco_begin = 1, reference_begin = 1 + reco.size();
  const std::size_t sink = reference_begin + reference.size(), vertices = sink + 1;
  Network network(vertices); std::vector<CandidateEdge> candidates;
  std::vector<std::size_t> reco_degree(reco.size()), reference_degree(reference.size());
  for (std::size_t r = 0; r < reco.size(); ++r) add_edge(network, source, reco_begin + r, 0);
  for (std::size_t t = 0; t < reference.size(); ++t) add_edge(network, reference_begin + t, sink, 0);
  for (std::size_t r = 0; r < reco.size(); ++r) {
    for (std::size_t t = 0; t < reference.size(); ++t) {
      const double deta = reco[r].eta - reference[t].eta;
      const double dphi = kinematics::delta_phi(reco[r].phi, reference[t].phi);
      const double dr = std::hypot(deta, dphi);
      if (!std::isfinite(dr)) throw std::overflow_error("Geometric matching angular distance overflow");
      if (!(dr < max_delta_r)) continue;
      const auto index = network[reco_begin + r].size();
      add_edge(network, reco_begin + r, reference_begin + t, static_cast<long double>(dr));
      candidates.push_back({r, t, index, dr}); ++reco_degree[r]; ++reference_degree[t];
    }
  }
  result.candidate_edges = candidates.size();
  for (std::size_t r = 0; r < reco.size(); ++r)
    if (reco_degree[r] > 1) result.locally_ambiguous_reco_ids.push_back(reco[r].id);
  for (std::size_t t = 0; t < reference.size(); ++t)
    if (reference_degree[t] > 1) result.competed_reference_ids.push_back(reference[t].id);

  // Successive minimum-cost augmentations. Reverse edges allow an earlier
  // assignment to be displaced when that increases cardinality or lowers total
  // cost. Bellman-Ford directly handles negative residual costs; no large
  // cardinality penalty, epsilon tie perturbation or reduced-cost clamp is used.
  const auto infinity = std::numeric_limits<long double>::infinity();
  const auto absent = std::numeric_limits<std::size_t>::max();
  for (;;) {
    std::vector<long double> distance(vertices, infinity);
    std::vector<std::size_t> previous_vertex(vertices, absent), previous_edge(vertices, absent);
    distance[source] = 0;
    for (std::size_t iteration = 1; iteration < vertices; ++iteration) {
      bool changed = false;
      for (std::size_t from = 0; from < vertices; ++from) {
        if (!std::isfinite(distance[from])) continue;
        for (std::size_t index = 0; index < network[from].size(); ++index) {
          const auto& edge = network[from][index];
          if (!edge.capacity) continue;
          const auto cost = distance[from] + edge.cost;
          if (cost < distance[edge.to]) {
            distance[edge.to] = cost; previous_vertex[edge.to] = from; previous_edge[edge.to] = index; changed = true;
          }
        }
      }
      if (!changed) break;
    }
    if (previous_vertex[sink] == absent) break;
    // Fail closed if numerical residual behavior produces a predecessor cycle.
    std::vector<bool> visited(vertices); std::size_t vertex = sink;
    while (vertex != source) {
      if (visited[vertex] || previous_vertex[vertex] == absent)
        throw std::runtime_error("Invalid geometric matching residual path");
      visited[vertex] = true; vertex = previous_vertex[vertex];
    }
    for (vertex = sink; vertex != source; vertex = previous_vertex[vertex]) {
      const auto from = previous_vertex[vertex], index = previous_edge[vertex];
      auto& edge = network[from][index]; --edge.capacity; ++network[vertex][edge.reverse].capacity;
    }
  }
  std::vector<bool> used_reco(reco.size()), used_reference(reference.size());
  for (const auto& candidate : candidates) {
    if (network[reco_begin + candidate.reco][candidate.index].capacity) continue;
    if (used_reco[candidate.reco] || used_reference[candidate.reference])
      throw std::runtime_error("Nonunique geometric matching assignment");
    used_reco[candidate.reco] = true; used_reference[candidate.reference] = true;
    result.assignments.push_back({reco[candidate.reco].id, reference[candidate.reference].id, candidate.delta_r});
    result.total_delta_r += candidate.delta_r;
  }
  for (std::size_t r = 0; r < reco.size(); ++r)
    if (!used_reco[r]) result.unmatched_reco_ids.push_back(reco[r].id);
  for (std::size_t t = 0; t < reference.size(); ++t)
    if (!used_reference[t]) result.unmatched_reference_ids.push_back(reference[t].id);
  return result;
}
}  // namespace atlas::matching

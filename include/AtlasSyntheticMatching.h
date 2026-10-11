#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

// This interface is a geometric algorithm, not a physical truth reader.
// No generator status, photon origin, heavy-flavour label or event association
// can be inferred from an eta/phi direction. Real MC matching remains gated by
// independently validated same-event truth collections and eligibility rules.
namespace atlas::matching {
struct Direction {
  std::uint64_t id;
  double eta, phi;
  bool eligible = true;
};
struct Assignment {
  std::uint64_t reco_id, reference_id;
  double delta_r;
};
struct Result {
  std::vector<Assignment> assignments;
  std::vector<std::uint64_t> unmatched_reco_ids, unmatched_reference_ids;
  // Local candidate multiplicity/competition is reported, not interpreted as
  // a count of equally optimal global solutions or a physical origin label.
  std::vector<std::uint64_t> locally_ambiguous_reco_ids;
  std::vector<std::uint64_t> competed_reference_ids;
  std::size_t eligible_reco = 0, eligible_reference = 0, candidate_edges = 0;
  long double total_delta_r = 0;
  // Denominators include unmatched eligible objects. Empty denominators are
  // undefined (nullopt), never an invented zero or one. The reco fraction is
  // geometric matching only, not a validated process/flavour purity.
  std::optional<double> reference_match_fraction() const;
  std::optional<double> reco_match_fraction() const;
  std::optional<double> reference_unmatched_fraction() const;
  std::optional<double> reco_unmatched_fraction() const;
};

// Edges require deltaR < max_delta_r (strict). Objective: maximize unique pair
// cardinality, then minimize summed deltaR. Stable IDs define sorted residual
// traversal and first strictly shortest-path tie handling; input order cannot
// alter assignments. Angular wrapping reuses AtlasKinematics::delta_phi.
// All coordinates and the positive finite threshold are checked, including
// ineligible inputs; IDs must be unique within each collection.
Result match(const std::vector<Direction>& reco,
             const std::vector<Direction>& reference,
             double max_delta_r);
}  // namespace atlas::matching
// Preserve the explicitly synthetic fixture API while allowing the audited
// MC-only adapter to reuse the same independently tested assignment algorithm.
namespace atlas { namespace synthetic_matching = matching; }

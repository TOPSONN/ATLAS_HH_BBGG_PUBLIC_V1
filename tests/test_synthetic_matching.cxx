#include "AtlasSyntheticMatching.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <numbers>
#include <random>
#include <set>
#include <stdexcept>
#include <tuple>

using namespace atlas::synthetic_matching;
namespace {
std::size_t assertions = 0, oracle_cases = 0;
void check(bool value, const char* message) { ++assertions; if (!value) throw std::runtime_error(message); }
void close(long double actual, long double expected) {
  check(std::abs(actual - expected) <= 1e-12L * std::max(1.L, std::abs(expected)), "Matching numerical closure failed");
}
template<class F> void rejected(F action) {
  bool threw = false; try { action(); } catch (const std::exception&) { threw = true; }
  check(threw, "Invalid synthetic matching input accepted");
}
using IdPairs = std::vector<std::pair<std::uint64_t, std::uint64_t>>;
IdPairs pairs(const Result& result) {
  IdPairs ids; for (const auto& a : result.assignments) ids.emplace_back(a.reco_id, a.reference_id); return ids;
}
// Independent angular wrapping uses atan2(sin,cos), rather than the production
// remainder-based helper. Enumeration does not use the residual-flow solver.
long double independent_distance(const Direction& a, const Direction& b) {
  const long double phi = static_cast<long double>(a.phi) - b.phi;
  return std::hypot(static_cast<long double>(a.eta) - b.eta, std::atan2(std::sin(phi), std::cos(phi)));
}
std::pair<std::size_t, long double> exhaustive(const std::vector<Direction>& reco,
                                            const std::vector<Direction>& reference, double threshold) {
  std::size_t best_count = 0; long double best_cost = 0; std::vector<bool> used(reference.size());
  std::function<void(std::size_t,std::size_t,long double)> visit = [&](auto r, auto count, auto cost) {
    if (r == reco.size()) {
      if (count > best_count || (count == best_count && cost < best_cost)) { best_count = count; best_cost = cost; }
      return;
    }
    visit(r + 1, count, cost);
    if (!reco[r].eligible) return;
    for (std::size_t t = 0; t < reference.size(); ++t) {
      if (used[t] || !reference[t].eligible) continue;
      const auto dr = independent_distance(reco[r], reference[t]);
      if (!(dr < threshold)) continue;
      used[t] = true; visit(r + 1, count + 1, cost + dr); used[t] = false;
    }
  };
  visit(0, 0, 0); return {best_count, best_cost};
}
void invariants(const Result& result, double threshold) {
  std::set<std::uint64_t> reco, reference; long double total = 0;
  for (const auto& a : result.assignments) {
    check(reco.insert(a.reco_id).second && reference.insert(a.reference_id).second, "Shared matching partner");
    check(a.delta_r >= 0 && a.delta_r < threshold, "Nonphysical or inclusive threshold edge"); total += a.delta_r;
  }
  close(total, result.total_delta_r);
  check(result.assignments.size() + result.unmatched_reco_ids.size() == result.eligible_reco, "Reco denominator lost unmatched inputs");
  check(result.assignments.size() + result.unmatched_reference_ids.size() == result.eligible_reference, "Reference denominator lost unmatched inputs");
}
}  // namespace

int main() {
  try {
    const auto empty = match({}, {}, .2);
    check(empty.assignments.empty() && !empty.reco_match_fraction() && !empty.reference_match_fraction(), "Empty denominator fabricated");
    check(!empty.reco_unmatched_fraction() && !empty.reference_unmatched_fraction(), "Empty unmatched denominator fabricated");
    const auto zero = match({{1,0,0}}, {{1,0,0}}, .2);
    check(pairs(zero) == IdPairs{{1,1}}, "Exact-zero direction did not match"); close(zero.total_delta_r, 0);
    for (const double threshold : {.2, .3}) {
      check(match({{1,0,0}}, {{2,threshold,0}}, threshold).assignments.empty(), "Exact threshold must fail");
      check(match({{1,0,0}}, {{2,std::nextafter(threshold,0.),0}}, threshold).assignments.size() == 1, "Just-below threshold must pass");
      check(match({{1,0,0}}, {{2,std::nextafter(threshold,1.),0}}, threshold).assignments.empty(), "Just-above threshold must fail");
    }
    const double pi = std::numbers::pi;
    const auto wrapped = match({{1,0,pi-.01}}, {{2,0,-pi+.01}}, .2);
    check(wrapped.assignments.size() == 1, "Phi boundary not wrapped"); close(wrapped.total_delta_r, .02);
    const auto periodic = match({{1,.1,.4+8*pi}}, {{2,.1,.4}}, .2);
    check(periodic.assignments.size() == 1, "Equivalent periodic directions separated"); close(periodic.total_delta_r, 0);
    const auto competition = match({{10,0,0},{20,.18,0}}, {{30,.05,0},{40,-.10,0}}, .2);
    check(pairs(competition) == IdPairs{{10,40},{20,30}}, "Global cardinality lost to local nearest assignment"); close(competition.total_delta_r, .23);
    check(competition.locally_ambiguous_reco_ids == std::vector<std::uint64_t>{10} && competition.competed_reference_ids == std::vector<std::uint64_t>{30}, "Local candidate ambiguity missing");
    const auto mincost = match({{1,.1,0},{2,.2,0}}, {{3,0,0},{4,.3,0}}, .3);
    check(pairs(mincost) == IdPairs{{1,3},{2,4}}, "Minimum cost among maximum-cardinality solutions failed"); close(mincost.total_delta_r, .2);
    const auto only_one = match({{1,0,0},{2,.1,0}}, {{3,.09,0}}, .2);
    check(pairs(only_one) == IdPairs{{2,3}} && only_one.unmatched_reco_ids == std::vector<std::uint64_t>{1}, "Competing reco objects shared reference");
    const auto ambiguous = match({{20,0,0},{10,0,0}}, {{40,0,0},{30,0,0}}, .2);
    const auto permuted = match({{10,0,0},{20,0,0}}, {{30,0,0},{40,0,0}}, .2);
    check(pairs(ambiguous) == pairs(permuted) && pairs(permuted) == IdPairs{{10,30},{20,40}}, "Stable-ID exact tie policy changed with input order");
    const auto denominators = match({{1,0,0},{2,1,0},{3,4,0,false}}, {{10,.01,0},{11,2,0},{12,3,0},{13,4,0,false}}, .2);
    check(denominators.eligible_reco == 2 && denominators.eligible_reference == 3, "Eligibility denominator incorrect");
    close(*denominators.reco_match_fraction(), .5); close(*denominators.reference_match_fraction(), 1.L/3);
    close(*denominators.reco_unmatched_fraction(), .5); close(*denominators.reference_unmatched_fraction(), 2.L/3);
    invariants(denominators, .2);
    const auto no_reference = match({{1,0,0}}, {}, .2), no_reco = match({}, {{1,0,0}}, .2);
    check(no_reference.reco_match_fraction() == 0. && !no_reference.reference_match_fraction(), "No-reference fractions incorrect");
    check(!no_reco.reco_match_fraction() && no_reco.reference_match_fraction() == 0., "No-reco fractions incorrect");
    const std::vector<Direction> sensitivity_reco{{1,0,0}}, sensitivity_ref{{2,.25,0}};
    check(match(sensitivity_reco,sensitivity_ref,.2).assignments.empty() && match(sensitivity_reco,sensitivity_ref,.3).assignments.size() == 1, "Threshold sensitivity not separate");
    for (const double bad : {0., -1., std::numeric_limits<double>::infinity(), std::numeric_limits<double>::quiet_NaN()})
      rejected([&]{match({}, {}, bad);});
    for (const double bad : {std::numeric_limits<double>::infinity(), std::numeric_limits<double>::quiet_NaN()}) {
      rejected([&]{match({{1,bad,0}}, {}, .2);}); rejected([&]{match({}, {{1,0,bad}}, .2);});
      rejected([&]{match({{1,0,bad,false}}, {}, .2);});
    }
    rejected([&]{match({{1,0,0},{1,1,0,false}}, {}, .2);});
    rejected([&]{match({}, {{1,0,0},{1,1,0}}, .2);});
    rejected([&]{match({{1,std::numeric_limits<double>::max(),0}}, {{2,-std::numeric_limits<double>::max(),0}}, .2);});
    std::mt19937 random(20261011); std::uniform_real_distribution<double> eta(-.4,.4), phi(-pi,pi), local_phi(-.4,.4);
    for (std::size_t trial = 0; trial < 600; ++trial) {
      const std::size_t nr = random()%6, nt = random()%6; const double threshold = trial%2 ? .2 : .3;
      std::vector<Direction> reco, reference;
      for (std::size_t r = 0; r < nr; ++r) reco.push_back({100+r,eta(random),trial%3 ? local_phi(random) : phi(random),random()%5!=0});
      for (std::size_t t = 0; t < nt; ++t) reference.push_back({200+t,eta(random),trial%3 ? local_phi(random) : phi(random),random()%5!=0});
      const auto actual = match(reco,reference,threshold); const auto expected = exhaustive(reco,reference,threshold); ++oracle_cases;
      check(actual.assignments.size() == expected.first, "Independent exhaustive maximum cardinality failed"); close(actual.total_delta_r, expected.second); invariants(actual,threshold);
      std::shuffle(reco.begin(),reco.end(),random); std::shuffle(reference.begin(),reference.end(),random);
      check(pairs(actual) == pairs(match(reco,reference,threshold)), "Random input permutation changed matching");
    }
    std::vector<Direction> dense_reco, dense_reference;
    for (std::size_t i=0;i<40;++i) {dense_reco.push_back({i,.001*static_cast<double>(i),0});dense_reference.push_back({100+i,.001*static_cast<double>(i),0});}
    const auto dense = match(dense_reco,dense_reference,.2); check(dense.assignments.size()==40,"Dense matching cardinality failed"); close(dense.total_delta_r,0); invariants(dense,.2);
    std::cout << "PASS SYNTHETIC_ONLY global unique matching assertions=" << assertions << " exhaustive_seeded_cases=" << oracle_cases
              << " dense_objects=40 thresholds=0.2,0.3\nPHYSICAL_TRUTH_MATCHING=NOT_EXECUTED\n";
    return 0;
  } catch (const std::exception& error) {std::cerr << "FAIL synthetic matching: " << error.what() << '\n'; return 1;}
}

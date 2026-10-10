#include "AtlasKinematics.h"
#include <array>
#include <cmath>
#include <iostream>
#include <limits>
#include <numbers>
#include <random>
#include <stdexcept>
#include <algorithm>

using namespace atlas::kinematics;
namespace {
int cases = 0;
double max_absolute = 0, max_relative = 0;
void check(bool value, const char* message) { ++cases; if (!value) throw std::runtime_error(message); }
void close(double value, long double reference) {
  const double absolute = std::abs(value - double(reference));
  const double relative = absolute / std::max(std::abs(double(reference)), 1e-15);
  max_absolute = std::max(max_absolute, absolute); max_relative = std::max(max_relative, relative);
  check(absolute <= 1e-7 + 1e-10 * std::abs(reference), "Independent Minkowski tolerance exceeded");
}
long double independent_mass(const Collection& c) {
  std::array<long double, 4> sum{};
  for (std::size_t i = 0; i < 2; ++i) {
    const auto& p = c.ordered[i].p4;
    // Independent component formula and long-double arithmetic, not ROOT M().
    sum[0] += static_cast<long double>(p.Pt()) * std::cos(static_cast<long double>(p.Phi()));
    sum[1] += static_cast<long double>(p.Pt()) * std::sin(static_cast<long double>(p.Phi()));
    sum[2] += static_cast<long double>(p.Pt()) * std::sinh(static_cast<long double>(p.Eta()));
    sum[3] += p.E();
  }
  return std::sqrt(sum[3]*sum[3] - sum[0]*sum[0] - sum[1]*sum[1] - sum[2]*sum[2]);
}
}
int main() {
  try {
    const float pi = float(std::numbers::pi);
    auto photons = construct({40, 30}, {0, 0}, {0, pi}, {40, 30}, 2, 1);
    auto pair = leading_pair(photons);
    check(photons.valid && pair.valid, "Back-to-back photon pair"); close(pair.mass, 2 * std::sqrt(1200.L));
    auto jets = construct({40, 30}, {0, 0}, {0, pi}, {50, 40}, 2, 1);
    close(leading_pair(jets).mass, std::sqrt(8000.L));
    auto reordered = construct({30, 40}, {0, 0}, {pi, 0}, {30, 40}, 2, 1);
    close(leading_pair(reordered).mass, pair.mass); check(reordered.ordered[0].input_index == 1, "pT ordering");
    auto tie1 = construct({20,20,20}, {1,-1,0}, {0,0,1}, {40,40,30}, 3, 1);
    auto tie2 = construct({20,20,20}, {0,1,-1}, {1,0,0}, {30,40,40}, 3, 1);
    close(leading_pair(tie1).mass, leading_pair(tie2).mass);
    close(delta_phi(3.1, -3.1), 6.2L - 2 * std::numbers::pi_v<long double>);
    close(delta_phi(.4 + 8 * std::numbers::pi, -.2), .6L);
    auto angular = construct({20,20}, {1,-1}, {.2F,-.3F}, {40,40}, 2, 1);
    close(leading_pair(angular).delta_r, std::hypot(2.L, static_cast<long double>(float(.2)) - float(-.3)));
    auto mev = construct({40000,30000}, {0,0}, {0,pi}, {40000,30000}, 2, .001);
    close(leading_pair(mev).mass, pair.mass);
    auto zero = construct({0,0}, {0,0}, {0,0}, {0,0}, 2, 1);
    check(zero.valid && leading_pair(zero).valid && leading_pair(zero).mass == 0, "Zero momentum");
    auto collinear = construct({20,10}, {0,0}, {0,0}, {20,10}, 2, 1);
    check(leading_pair(collinear).valid && leading_pair(collinear).mass == 0, "Collinear lightlike pair");
    check(!leading_pair(construct({}, {}, {}, {}, 0, 1)).available, "Empty collection");
    check(!leading_pair(construct({1}, {0}, {0}, {1}, 1, 1)).available, "Single object");
    check(!construct({10}, {0}, {0}, {9}, 1, 1).valid, "Gross negative mass-squared");
    auto rounding = construct({10}, {0}, {0}, {std::nextafter(10.F, 0.F)}, 1, 1);
    check(rounding.valid && rounding.roundoff_objects == 1, "Explicit float roundoff flag");
    check(rounding.ordered[0].p4.E() == std::nextafter(10.F, 0.F), "No silent energy correction");
    auto negative_pair = construct({10,10}, {0,0}, {0,0}, {std::nextafter(10.F,0.F),std::nextafter(10.F,0.F)}, 2, 1);
    check(!leading_pair(negative_pair).valid, "Negative pair mass-squared is not clamped");
    for (float bad : {std::numeric_limits<float>::quiet_NaN(), std::numeric_limits<float>::infinity()}) {
      check(!construct({bad}, {0}, {0}, {10}, 1, 1).valid, "Nonfinite pT");
      check(!construct({10}, {bad}, {0}, {10}, 1, 1).valid, "Nonfinite eta");
      check(!construct({10}, {0}, {bad}, {10}, 1, 1).valid, "Nonfinite phi");
      check(!construct({10}, {0}, {0}, {bad}, 1, 1).valid, "Nonfinite energy");
    }
    check(!construct({-1}, {0}, {0}, {1}, 1, 1).valid, "Negative pT");
    check(!construct({1}, {0}, {0}, {-1}, 1, 1).valid, "Negative energy");
    check(!construct({1}, {0}, {}, {1}, 1, 1).valid, "Mismatched collection");
    check(!construct({}, {}, {}, {}, -1, 1).valid, "Negative count");
    check(!construct({1}, {1000}, {0}, {1}, 1, 1).valid, "Overflow");
    check(!construct({1}, {0}, {0}, {1}, 1, 0).valid, "Invalid units scale");
    bool threw = false; try { delta_phi(std::numeric_limits<double>::infinity(), 0); } catch (...) { threw = true; }
    check(threw, "Nonfinite angular operation");
    std::mt19937 rng(20261010); std::uniform_real_distribution<float> pt(1,200), eta(-2.5,2.5), phi(-3.14,3.14);
    for (int i = 0; i < 500; ++i) {
      RVec p{pt(rng),pt(rng)}, h{eta(rng),eta(rng)}, f{phi(rng),phi(rng)}, e;
      for (int j=0; j<2; ++j) e.push_back(float(std::hypot(double(p[j])*std::cosh(h[j]), 10.)));
      auto c = construct(p,h,f,e,2,1); auto v = leading_pair(c);
      check(c.valid && v.valid, "Seeded physical pair"); close(v.mass, independent_mass(c));
    }
    std::cout << "PASS kinematics assertions=" << cases << " seeded_pairs=500\n"
              << "MASS_ABS_TOL=1e-7+1e-10*abs(reference)\n" << "MAX_ABSOLUTE_DEVIATION=" << max_absolute
              << "\nMAX_RELATIVE_DEVIATION=" << max_relative << '\n';
    return 0;
  } catch (const std::exception& e) { std::cerr << "FAIL: " << e.what() << '\n'; return 1; }
}

#pragma once
#include "AtlasExploratorySelection.h"
#include "AtlasNormalization.h"
#include <cstdint>
#include <compare>
#include <string>
#include <vector>

namespace atlas::regions {
// Study partition, not an official signal region or a blinded analysis.
struct Config {
  std::string version="study-regions-v1";
  selection::Config selection;
  double sr_mass_low=120, sr_mass_high=130;
  double photon_abs_delta_eta_split=1;
};
enum class Region { Control, Validation, ProspectiveSignal,
                    ReservedWindowPartition, OutsideStudyDomain,
                    FailsPreMassSelection, FailsJetSelection, InvalidInput };
void validate_config(const Config&);
// C5 is evaluated before the mass window; C7-C9 jet predicates are then used
// individually. Events outside C6 are never reconstructed from the C9 sample.
Region classify(const selection::Event&,const Config& = {});
const char* name(Region);

// namespace_id is a canonical fixture/sample identity, not a region label.
// The same event keeps the same identity after a different cut or reweighting.
struct EventIdentity {
  std::string namespace_id;
  std::uint64_t run=0,event=0;
  auto operator<=>(const EventIdentity&) const = default;
};
struct Population {
  std::string label; std::vector<EventIdentity> events;
  bool operator==(const Population&) const = default;
};
void require_disjoint_populations(const std::vector<Population>&);
struct Yield { Population population; normalization::SignedSums sums; };

// Values use exactly the order of the input yields. With includes_nuisances
// false the diagonal must equal sumw2. A nuisance model is only a caller's
// explicit synthetic covariance; this interface does not fit its parameters.
struct Covariance {
  std::vector<std::vector<long double>> values;
  std::string model;
  bool includes_nuisances=false;
};
Covariance independent_counting_covariance(const std::vector<Yield>&);

struct TransferContract {
  normalization::Scope scope=normalization::Scope::Synthetic;
  Yield mc_sr,mc_cr;
  Covariance covariance; // [MC_SR, MC_CR]
  normalization::Conditioning conditioning;
  normalization::SampleCombination samples;
};
struct TransferResult {
  normalization::Scope scope=normalization::Scope::Synthetic;
  long double factor=0,variance=0,mc_sr=0,mc_cr=0;
  std::vector<Population> calibration_populations;
  std::string covariance_model;
  bool includes_nuisances=false;
  std::string interpretation="SYNTHETIC_METHOD_TEST_ONLY; NO_PHYSICAL_BACKGROUND_PREDICTION";
 private:
  bool validated_=false;
  long double validated_factor_=0,validated_variance_=0;
  long double validated_sr_=0,validated_cr_=0;
  bool validated_nuisances_=false;
  std::string validated_model_,validated_interpretation_;
  std::vector<Population> validated_populations_;
  friend TransferResult transfer_factor(const TransferContract&);
  friend struct TransferAccess;
};
// T=MC_SR/MC_CR; J=(1/CR,-SR/CR^2), Var(T)=J C J^T.
// Physical application is deliberately unavailable in Phase 5.
TransferResult transfer_factor(const TransferContract&);

struct ResidualContract {
  normalization::Scope scope=normalization::Scope::Synthetic;
  Yield data_cr;
  std::vector<Yield> other_backgrounds_cr;
  Covariance covariance; // [Data_CR, background_1_CR, ...]
  // Must cover the union of transfer calibration and residual namespaces,
  // including main-MC/contamination pairwise generator-overlap disposition.
  normalization::SampleCombination samples;
};
struct Prediction {
  long double residual_cr=0,residual_variance=0,prediction_sr=0,variance=0;
  bool includes_nuisances=false;
  std::string interpretation="SYNTHETIC_METHOD_TEST_ONLY; NO_PHYSICAL_BACKGROUND_PREDICTION";
 private:
  bool validated_=false;
  std::vector<Population> calibration_populations_;
  friend Prediction predict_background(const TransferResult&,const ResidualContract&,long double);
  friend void require_held_out_validation(const Prediction&,const Population&);
};
// X=Data_CR-sum(other_CR); Var(X)=a C a^T, a=(1,-1,...).
// B=T*X; Var(B)=X^2 Var(T)+T^2 Var(X)+2 T X Cov(T,X).
// A nonzero cross covariance must be supplied explicitly. This is first-order
// propagation, not an exact ratio interval, likelihood or nuisance fit.
Prediction predict_background(const TransferResult&,const ResidualContract&,
                              long double covariance_transfer_residual=0);
// Disjoint held-out validation identities are mandatory even in fixtures.
// Event disjointness never proves independence of shape/nuisance parameters.
void require_held_out_validation(const TransferResult&,const Population& validation);
// After a prediction, additionally excludes its DATA_CR and contamination
// input identities from a held-out validation population.
void require_held_out_validation(const Prediction&,const Population& validation);
} // namespace atlas::regions

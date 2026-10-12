#pragma once
#include <cstdint>
#include <limits>
#include <string>
#include <vector>

class TH1D;

namespace atlas::normalization {
enum class Scope { Synthetic, Physical };
enum class Verification { Unknown, Verified, Rejected };
struct Evidence {
  Verification state=Verification::Unknown;
  std::string reference,description;
};

// Public totals are read-only by contract. Use add/merge/from_aggregates rather
// than modifying them; no weight sign is removed or interpreted as an SF.
struct SignedSums {
  std::uint64_t entries=0,positive=0,negative=0,zero=0;
  bool sign_counts_known=true;
  long double sumw=0,sumw2=0,sumabs=0;
  void add(long double weight);
  void merge(const SignedSums& other);
  long double effective_entries() const;
  static SignedSums from_aggregates(long double sumw,long double sumw2,
                                  long double sumabs,std::uint64_t entries=0);
 private:
  long double w_acc_=0,w_correction_=0,w2_acc_=0,w2_correction_=0;
  long double abs_acc_=0,abs_correction_=0;
};
struct Conditioning {
  // Reject zero or |sumw|/sumabs <= this threshold. This is an explicit
  // numerical conditioning policy, not a physics/statistical-significance cut.
  long double minimum_relative_signed_sum=1e-12L;
};
long double require_stable_signed_sum(const SignedSums&,const Conditioning& = {});

enum class OverlapDisposition { Unknown, Disjoint, Overlap };
struct SamplePair {
  std::string first,second;
  OverlapDisposition disposition=OverlapDisposition::Unknown;
  Evidence evidence;
};
struct SampleCombination {
  Scope scope=Scope::Physical;
  bool enable_physical=false;
  std::vector<std::string> sample_ids;
  std::vector<SamplePair> pairs;
};
// Every pair needs explicit disjoint evidence; process names or mass boxes do
// not establish physical disjointness. A one-sample contract is not a mixture.
void validate_sample_combination(const SampleCombination&);

struct GeneratorNormalizationContract {
  Scope scope=Scope::Physical;
  bool enable_physical=false;
  std::string sample_id,production_tag;
  long double luminosity_pb_inverse=std::numeric_limits<long double>::quiet_NaN();
  long double cross_section_pb=std::numeric_limits<long double>::quiet_NaN();
  long double filter_efficiency=std::numeric_limits<long double>::quiet_NaN();
  long double k_factor=std::numeric_limits<long double>::quiet_NaN();
  SignedSums signed_pre_skim_generated;
  Conditioning conditioning;
  Evidence sample_provenance,generator_weight_semantics,pre_skim_denominator;
  Evidence cross_section_convention,filter_efficiency_convention,k_factor_convention;
  Evidence branching_ratio_convention,processing_completeness,luminosity_applicability;
  // This module prepares generator-level scaling only. It does not multiply
  // any SF or attest reconstructed-level efficiencies/normalization.
  bool apply_scale_factors=false;
};
struct GeneratorScale {
  Scope scope=Scope::Physical;
  long double factor=0;
  bool scale_factors_applied=false;
  std::string interpretation="GENERATOR_LEVEL_ONLY; RECONSTRUCTED_SF_APPLICABILITY_NOT_VALIDATED";
 private:
  bool validated_=false;
  long double validated_factor_=0;
  Scope validated_scope_=Scope::Physical;
  friend GeneratorScale generator_normalization_factor(const GeneratorNormalizationContract&);
  friend long double scaled_generator_weight(long double,const GeneratorScale&);
};
GeneratorScale generator_normalization_factor(const GeneratorNormalizationContract&);
long double scaled_generator_weight(long double signed_generator_weight,
                                    const GeneratorScale&);

enum class ShapeMode { RawUnweightedDiagnostic, GeneratorWeightedShape };
enum class FlowPolicy { Exclude, Include };
struct ShapeContract {
  Scope scope=Scope::Physical;
  bool enable_physical=false;
  ShapeMode mode=ShapeMode::RawUnweightedDiagnostic;
  int first_bin=1,last_bin=-1;
  FlowPolicy flow_policy=FlowPolicy::Exclude;
  bool density=false;
  std::string selection_id,variable_id,units;
  Evidence histogram_semantics,nominal_generator_weight_semantics;
  // Diagonal source sumw2 is justified only for independent selected bin
  // yields (e.g. one event contributes to at most one bin). Sumw2 alone does
  // not supply clustered multi-object/event or cross-histogram covariance.
  Evidence independent_selected_bin_statistics;
  Conditioning conditioning;
  // Weighted histograms require the event ledger, including flow bins. This
  // exposes within-bin signed cancellations which abs(bin contents) conceals.
  std::vector<SignedSums> event_sums_by_bin;
};
struct ShapeResult {
  Scope scope=Scope::Physical;
  ShapeMode mode=ShapeMode::RawUnweightedDiagnostic;
  FlowPolicy flow_policy=FlowPolicy::Exclude;
  bool density=false;
  std::string selection_id,variable_id,units;
  std::vector<int> bin_indices;
  std::vector<long double> widths,lower_edges,upper_edges,source_sumw,source_sumw2,values,errors;
  std::vector<std::vector<long double>> covariance;
  SignedSums selected;
  long double effective_entries=0;
  long double normalization_denominator=0;
};
// Conditional on fixed nominal weights and independent selected bin yields:
// J_ik=(delta_ik*S-x_i)/(S*S), C=J diag(sumw2) J^T. Density rescales
// rows/columns by bin widths. Source histogram and its statistics are untouched.
ShapeResult normalize_shape(const TH1D&,const ShapeContract&);
void require_compatible_shapes(const ShapeResult&,const ShapeResult&);
}

#include "AtlasNormalization.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {
using namespace atlas::normalization;
std::size_t checks=0;
void check(bool value,const std::string& message) {++checks;if(!value)throw std::runtime_error(message);}
void close(long double value,long double expected,const std::string& message) {
  check(std::abs(value-expected)<=1e-15L*std::max({std::abs(value),std::abs(expected),1.L}),message);
}
void rejected(const std::function<void()>& action,const std::string& message) {
  bool caught=false;try{action();}catch(const std::invalid_argument&){caught=true;}check(caught,message);
}
Evidence fixture(const std::string& definition="Analytical synthetic fixture; no physical provenance claim") {
  return {Verification::Verified,"synthetic:test_normalization",definition};
}
GeneratorNormalizationContract contract() {
  GeneratorNormalizationContract result;result.scope=Scope::Synthetic;
  result.sample_id="SYNTHETIC_SIGNED";result.production_tag="synthetic-v1";
  result.luminosity_pb_inverse=100;result.cross_section_pb=4;result.filter_efficiency=.5L;result.k_factor=2;
  for(const auto weight:{3.L,-1.L,2.L})result.signed_pre_skim_generated.add(weight);
  result.sample_provenance=result.generator_weight_semantics=result.pre_skim_denominator=fixture();
  result.cross_section_convention=result.filter_efficiency_convention=result.k_factor_convention=fixture();
  result.branching_ratio_convention=result.processing_completeness=result.luminosity_applicability=fixture();return result;
}
}
int main() {
  try {
    SignedSums sums;for(const auto weight:{3.L,-1.L,2.L,0.L})sums.add(weight);
    close(sums.sumw,4,"Signed sum changed");close(sums.sumw2,14,"Squared sum incorrect");close(sums.sumabs,6,"Absolute diagnostic sum incorrect");
    check(sums.entries==4&&sums.positive==2&&sums.negative==1&&sums.zero==1&&sums.sign_counts_known,"Signed event counts incorrect");
    close(sums.effective_entries(),16.L/14,"Neff uses an unsigned denominator");
    SignedSums first,second;first.add(3);first.add(-1);second.add(2);second.add(0);first.merge(second);
    check(first.sumw==sums.sumw&&first.sumw2==sums.sumw2&&first.sumabs==sums.sumabs&&first.entries==sums.entries,"Partition merge inconsistent");
    SignedSums cancellation;for(const auto weight:{1e20L,1.L,-1e20L})cancellation.add(weight);
    close(cancellation.sumw,1,"Compensated signed sum lost low-order residual");
    rejected([&]{require_stable_signed_sum(cancellation);},"Extreme cancellation accepted");
    SignedSums zero;zero.add(1);zero.add(-1);close(zero.effective_entries(),0,"Zero signed Neff incorrect");
    rejected([&]{require_stable_signed_sum(zero);},"Zero signed denominator accepted");
    SignedSums near;near.add(1);near.add(-1+1e-14L);
    rejected([&]{require_stable_signed_sum(near);},"Near-zero signed denominator accepted");
    SignedSums negative;negative.add(-4);negative.add(1);close(require_stable_signed_sum(negative),-3,"Negative stable denominator discarded");
    close(negative.effective_entries(),9.L/17,"Negative signed Neff incorrect");
    rejected([&]{sums.add(std::numeric_limits<long double>::quiet_NaN());},"NaN weight accepted");
    rejected([&]{sums.add(std::numeric_limits<long double>::infinity());},"Infinite weight accepted");
    rejected([&]{sums.add(std::numeric_limits<long double>::max());},"Squared-weight overflow accepted");
    rejected([&]{SignedSums::from_aggregates(2,1,1);},"Impossible signed/absolute aggregate accepted");
    rejected([&]{SignedSums::from_aggregates(1,0,1);},"Zero sumw2 with nonzero sum accepted");
    rejected([&]{SignedSums::from_aggregates(1,4,1);},"Impossible squared/absolute aggregate accepted");
    rejected([&]{SignedSums::from_aggregates(0,1e-30L,0);},"Tiny inconsistent absolute-weight aggregate accepted");
    rejected([&]{SignedSums::from_aggregates(1,1,10,2);},"Aggregate count Cauchy bound bypassed");
    rejected([&]{require_stable_signed_sum(sums,Conditioning{0});},"Disabled condition guard accepted");
    rejected([&]{require_stable_signed_sum(sums,Conditioning{1});},"Invalid condition threshold accepted");
    auto aggregate=SignedSums::from_aggregates(4,14,6,4);check(!aggregate.sign_counts_known,"Unknown sign counts invented");
    close(aggregate.effective_entries(),16.L/14,"Aggregate Neff incorrect");

    const auto synthetic=contract();const auto scale=generator_normalization_factor(synthetic);
    close(scale.factor,100,"Analytical L*sigma*eff*k/signedSumW incorrect");
    check(scale.scope==Scope::Synthetic&&!scale.scale_factors_applied,"Synthetic generator scale misclassified");
    check(scale.interpretation.find("RECONSTRUCTED_SF_APPLICABILITY_NOT_VALIDATED")!=std::string::npos,"SF scope falsely validated");
    close(scaled_generator_weight(-1,scale),-100,"Negative generator weight replaced");
    close(scaled_generator_weight(2,scale),200,"Positive generator weight incorrect");
    rejected([&]{scaled_generator_weight(1,GeneratorScale{});},"Default unvalidated scale accepted");
    auto changed=scale;changed.factor=1;rejected([&]{scaled_generator_weight(1,changed);},"Tampered scale accepted");
    changed=scale;changed.scope=Scope::Physical;rejected([&]{scaled_generator_weight(1,changed);},"Synthetic scale relabelled physical");
    auto disabled=synthetic;disabled.scope=Scope::Physical;
    rejected([&]{generator_normalization_factor(disabled);},"Default physical application enabled");
    // A declared contract can be unit-tested; this fixture is not evidence for
    // any actual MC file, DATA luminosity or correction applicability.
    disabled.enable_physical=true;disabled.generator_weight_semantics.state=Verification::Unknown;
    rejected([&]{generator_normalization_factor(disabled);},"Enabled physical contract bypassed unknown weight semantics");
    const std::vector<Evidence GeneratorNormalizationContract::*> ingredients{
      &GeneratorNormalizationContract::sample_provenance,&GeneratorNormalizationContract::generator_weight_semantics,
      &GeneratorNormalizationContract::pre_skim_denominator,&GeneratorNormalizationContract::cross_section_convention,
      &GeneratorNormalizationContract::filter_efficiency_convention,&GeneratorNormalizationContract::k_factor_convention,
      &GeneratorNormalizationContract::branching_ratio_convention,&GeneratorNormalizationContract::processing_completeness,
      &GeneratorNormalizationContract::luminosity_applicability};
    for(const auto member:ingredients) {
      auto missing=synthetic;(missing.*member).state=Verification::Unknown;
      rejected([&]{generator_normalization_factor(missing);},"Unknown ingredient accepted");
      missing=synthetic;(missing.*member).reference.clear();
      rejected([&]{generator_normalization_factor(missing);},"Unreferenced ingredient accepted");
    }
    auto sf=synthetic;sf.apply_scale_factors=true;
    rejected([&]{generator_normalization_factor(sf);},"Unvalidated SF applied");
    auto invalid=synthetic;invalid.filter_efficiency=1.1;
    rejected([&]{generator_normalization_factor(invalid);},"Invalid filter efficiency accepted");
    invalid=synthetic;invalid.luminosity_pb_inverse=0;
    rejected([&]{generator_normalization_factor(invalid);},"Zero luminosity accepted");
    invalid=synthetic;invalid.signed_pre_skim_generated=SignedSums::from_aggregates(4,14,6);
    rejected([&]{generator_normalization_factor(invalid);},"Missing generated event count accepted");
    invalid=synthetic;invalid.signed_pre_skim_generated=zero;
    rejected([&]{generator_normalization_factor(invalid);},"Zero generated denominator replaced");
    invalid=synthetic;invalid.signed_pre_skim_generated=near;
    rejected([&]{generator_normalization_factor(invalid);},"Near-zero generated denominator accepted");
    invalid=synthetic;invalid.signed_pre_skim_generated=negative;
    close(generator_normalization_factor(invalid).factor,-400.L/3,"Signed generated denominator made absolute");
    auto underflow=synthetic;underflow.luminosity_pb_inverse=1;underflow.cross_section_pb=std::numeric_limits<long double>::denorm_min();
    underflow.filter_efficiency=.5L;underflow.k_factor=1;
    rejected([&]{generator_normalization_factor(underflow);},"Nonzero scale factor underflow accepted");
    underflow=synthetic;underflow.luminosity_pb_inverse=1;underflow.cross_section_pb=1e-100L;
    underflow.filter_efficiency=1;underflow.k_factor=1;
    const auto tiny_scale=generator_normalization_factor(underflow);
    rejected([&]{scaled_generator_weight(std::numeric_limits<long double>::denorm_min(),tiny_scale);},"Nonzero signed event underflow silently zeroed");

    SampleCombination combination;combination.scope=Scope::Synthetic;combination.sample_ids={"a","b"};
    rejected([&]{validate_sample_combination(combination);},"Unknown sample overlap accepted");
    combination.pairs.push_back({"a","b",OverlapDisposition::Disjoint,fixture("Explicit synthetic disjoint sample construction")});
    validate_sample_combination(combination);++checks;
    auto overlap=combination;overlap.pairs[0].disposition=OverlapDisposition::Overlap;
    rejected([&]{validate_sample_combination(overlap);},"Known sample overlap accepted");
    overlap=combination;overlap.pairs[0].evidence.state=Verification::Unknown;
    rejected([&]{validate_sample_combination(overlap);},"Unverified disjoint label accepted");
    overlap=combination;overlap.sample_ids.push_back("a");
    rejected([&]{validate_sample_combination(overlap);},"Duplicate/alternative sample identity accepted");
    overlap=combination;overlap.sample_ids.push_back("c");
    rejected([&]{validate_sample_combination(overlap);},"Incomplete three-sample overlap matrix accepted");
    overlap=combination;overlap.pairs.push_back({"b","a",OverlapDisposition::Disjoint,fixture()});
    rejected([&]{validate_sample_combination(overlap);},"Duplicated pairwise evidence accepted");
    overlap=combination;overlap.scope=Scope::Physical;
    rejected([&]{validate_sample_combination(overlap);},"Physical combination enabled by default");
    std::cout<<"PASS normalization contract: "<<checks<<" deterministic assertions; no physical input or SF applied\n";return 0;
  } catch(const std::exception& error){std::cerr<<"FAIL normalization contract: "<<error.what()<<'\n';return 1;}
}

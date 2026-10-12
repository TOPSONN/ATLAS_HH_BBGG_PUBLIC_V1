#include "AtlasNormalization.h"
#include <TH1D.h>
#include <TArrayD.h>
#include <algorithm>
#include <cmath>
#include <limits>
#include <iterator>
#include <set>
#include <stdexcept>
#include <utility>

namespace atlas::normalization {
namespace {
void require(bool condition,const std::string& message) {
  if(!condition)throw std::invalid_argument(message);
}
void finite(long double value,const std::string& name) {
  require(std::isfinite(value),name+" must be finite");
}
void compensated_add(long double value,long double& accumulator,long double& correction) {
  const auto next=accumulator+value;
  correction+=std::abs(accumulator)>=std::abs(value)
    ? (accumulator-next)+value : (value-next)+accumulator;
  accumulator=next;
  finite(accumulator,"accumulator");finite(correction,"compensation");
}
bool consistent(long double first,long double second,long double scale) {
  // A named histogram/ledger serialization bound, not a changed reconstruction
  // tolerance or permission to repair either source.
  const auto local_scale=std::max({std::abs(first),std::abs(second),std::abs(scale)});
  return local_scale==0?first==second:
    std::abs(first-second)<=64*std::numeric_limits<double>::epsilon()*local_scale;
}
bool moment_consistent(long double first,long double second) {
  return std::abs(first-second)<=64*std::numeric_limits<long double>::epsilon()*
    std::max(std::abs(first),std::abs(second));
}
void validate_sums(const SignedSums& sums) {
  finite(sums.sumw,"sumw");finite(sums.sumw2,"sumw2");finite(sums.sumabs,"sumabs");
  require(sums.sumw2>=0&&sums.sumabs>=0,"Negative squared/absolute weight sum");
  require(std::abs(sums.sumw)<=sums.sumabs||moment_consistent(std::abs(sums.sumw),sums.sumabs),
          "Signed total exceeds absolute total");
  if(sums.sumw2==0)require(sums.sumw==0&&sums.sumabs==0,"Zero sumw2 with nonzero weights");
  if(sums.sumw2>0) {
    const auto root=std::sqrt(sums.sumw2);
    require(sums.sumabs>0,"Positive sumw2 with zero absolute-weight sum");
    require(root<=sums.sumabs||moment_consistent(root,sums.sumabs),"Squared sum exceeds possible absolute-weight sum");
    if(sums.entries>0)require(sums.sumabs/root<=std::sqrt(static_cast<long double>(sums.entries))*
      (1+64*std::numeric_limits<double>::epsilon()),"Absolute-weight sum violates generated/selected count Cauchy bound");
  }
  if(sums.sign_counts_known) {
    require(sums.positive<=sums.entries&&sums.negative<=sums.entries&&sums.zero<=sums.entries-sums.negative&&
            sums.positive==sums.entries-sums.negative-sums.zero,"Inconsistent signed entry counts");
  }
}
void verified(const Evidence& evidence,const std::string& name) {
  require(evidence.state==Verification::Verified&&!evidence.reference.empty()&&
          !evidence.description.empty(),name+" lacks explicitly verified scope/reference");
}
void enabled(Scope scope,bool enable,const std::string& name) {
  require(scope==Scope::Synthetic||enable,name+" physical application is disabled");
}
long double conditioned_denominator(long double sumw,long double sumabs,const Conditioning& conditioning) {
  finite(sumw,"Signed denominator");finite(sumabs,"Absolute-weight diagnostic");
  finite(conditioning.minimum_relative_signed_sum,"Condition threshold");
  require(conditioning.minimum_relative_signed_sum>0&&conditioning.minimum_relative_signed_sum<1,
          "Condition threshold must lie strictly between zero and one");
  require(sumw!=0&&sumabs>0&&std::abs(sumw)/sumabs>conditioning.minimum_relative_signed_sum,
          "Zero or numerically unstable signed normalization denominator");
  return sumw;
}
std::pair<std::string,std::string> canonical(const std::string& first,const std::string& second) {
  return first<second?std::make_pair(first,second):std::make_pair(second,first);
}
}

void SignedSums::add(long double weight) {
  finite(weight,"Signed event weight");const auto square=weight*weight;finite(square,"Squared event weight");
  require(weight==0||square>0,"Squared nonzero weight underflow");
  require(entries<std::numeric_limits<std::uint64_t>::max(),"Entry count overflow");
  compensated_add(weight,w_acc_,w_correction_);
  compensated_add(square,w2_acc_,w2_correction_);
  compensated_add(std::abs(weight),abs_acc_,abs_correction_);
  sumw=w_acc_+w_correction_;sumw2=w2_acc_+w2_correction_;sumabs=abs_acc_+abs_correction_;
  finite(sumw,"sumw");finite(sumw2,"sumw2");finite(sumabs,"sumabs");
  ++entries;if(weight>0)++positive;else if(weight<0)++negative;else ++zero;
}
void SignedSums::merge(const SignedSums& other) {
  validate_sums(*this);validate_sums(other);
  require(other.entries<=std::numeric_limits<std::uint64_t>::max()-entries,"Entry count overflow");
  compensated_add(other.sumw,w_acc_,w_correction_);
  compensated_add(other.sumw2,w2_acc_,w2_correction_);
  compensated_add(other.sumabs,abs_acc_,abs_correction_);
  sumw=w_acc_+w_correction_;sumw2=w2_acc_+w2_correction_;sumabs=abs_acc_+abs_correction_;
  entries+=other.entries;positive+=other.positive;negative+=other.negative;zero+=other.zero;
  sign_counts_known=sign_counts_known&&other.sign_counts_known;
  validate_sums(*this);
}
SignedSums SignedSums::from_aggregates(long double weight,long double squared,long double absolute,std::uint64_t count) {
  SignedSums result;result.sumw=result.w_acc_=weight;result.sumw2=result.w2_acc_=squared;
  result.sumabs=result.abs_acc_=absolute;result.entries=count;result.sign_counts_known=false;
  validate_sums(result);return result;
}
long double SignedSums::effective_entries() const {
  validate_sums(*this);return sumw2>0?(sumw/std::sqrt(sumw2))*(sumw/std::sqrt(sumw2)):0;
}
long double require_stable_signed_sum(const SignedSums& sums,const Conditioning& conditioning) {
  validate_sums(sums);return conditioned_denominator(sums.sumw,sums.sumabs,conditioning);
}
void validate_sample_combination(const SampleCombination& contract) {
  enabled(contract.scope,contract.enable_physical,"Sample combination");
  require(!contract.sample_ids.empty(),"No explicit sample identity");
  std::set<std::string> ids;
  for(const auto& id:contract.sample_ids)require(!id.empty()&&ids.insert(id).second,"Empty/duplicate sample identity");
  std::set<std::pair<std::string,std::string>> pairs;
  for(const auto& pair:contract.pairs) {
    require(pair.first!=pair.second&&ids.contains(pair.first)&&ids.contains(pair.second),"Invalid sample pair identity");
    require(pairs.insert(canonical(pair.first,pair.second)).second,"Duplicate pairwise sample evidence");
    require(pair.disposition==OverlapDisposition::Disjoint,"Sample overlap is present or unresolved");
    verified(pair.evidence,"Pairwise disjointness");
  }
  for(auto first=ids.begin();first!=ids.end();++first)
    for(auto second=std::next(first);second!=ids.end();++second)
      require(pairs.contains(canonical(*first,*second)),"Missing pairwise disjointness evidence");
}
GeneratorScale generator_normalization_factor(const GeneratorNormalizationContract& contract) {
  enabled(contract.scope,contract.enable_physical,"Generator normalization");
  require(!contract.sample_id.empty()&&!contract.production_tag.empty(),"Missing sample/production identity");
  require(contract.signed_pre_skim_generated.entries>0,"Generated event count is missing");
  require(!contract.apply_scale_factors,"Scale-factor application is not implemented or validated by this module");
  verified(contract.sample_provenance,"Sample provenance");verified(contract.generator_weight_semantics,"Nominal generator weight");
  verified(contract.pre_skim_denominator,"Signed pre-skim denominator");verified(contract.cross_section_convention,"Cross section");
  verified(contract.filter_efficiency_convention,"Filter efficiency");verified(contract.k_factor_convention,"k-factor");
  verified(contract.branching_ratio_convention,"Branching ratio");verified(contract.processing_completeness,"Processing completeness");
  verified(contract.luminosity_applicability,"Luminosity applicability");
  finite(contract.luminosity_pb_inverse,"Luminosity");finite(contract.cross_section_pb,"Cross section");
  finite(contract.filter_efficiency,"Filter efficiency");finite(contract.k_factor,"k-factor");
  require(contract.luminosity_pb_inverse>0&&contract.cross_section_pb>=0&&
          contract.filter_efficiency>0&&contract.filter_efficiency<=1&&contract.k_factor>0,"Invalid normalization scalar");
  const auto denominator=require_stable_signed_sum(contract.signed_pre_skim_generated,contract.conditioning);
  GeneratorScale result;result.scope=contract.scope;
  result.factor=contract.luminosity_pb_inverse*contract.cross_section_pb*
    contract.filter_efficiency*contract.k_factor/denominator;
  require(contract.cross_section_pb==0||result.factor!=0,"Nonzero generator normalization factor underflow");
  finite(result.factor,"Generator scale");result.validated_=true;
  result.validated_factor_=result.factor;result.validated_scope_=result.scope;return result;
}
long double scaled_generator_weight(long double weight,const GeneratorScale& scale) {
  finite(weight,"Signed generator weight");finite(scale.factor,"Generator scale");
  require(scale.validated_&&scale.factor==scale.validated_factor_&&scale.scope==scale.validated_scope_,
          "Generator scale was not validated or was subsequently modified");
  require(!scale.scale_factors_applied,"Unvalidated SF application");
  const auto result=weight*scale.factor;finite(result,"Scaled generator weight");
  require(weight==0||scale.factor==0||result!=0,"Nonzero scaled generator weight underflow");return result;
}

ShapeResult normalize_shape(const TH1D& histogram,const ShapeContract& contract) {
  enabled(contract.scope,contract.enable_physical,"Shape normalization");
  require(!contract.selection_id.empty()&&!contract.variable_id.empty()&&!contract.units.empty(),
          "No explicit selection/variable/unit identity");
  verified(contract.histogram_semantics,"Histogram weight semantics");
  verified(contract.independent_selected_bin_statistics,"Independent selected-bin statistical model");
  const bool weighted=contract.mode==ShapeMode::GeneratorWeightedShape;
  if(weighted)verified(contract.nominal_generator_weight_semantics,"Nominal generator-weight semantics");
  require(histogram.GetDimension()==1,"Only native one-dimensional histograms are supported");
  const int count=histogram.GetNbinsX();const int last=contract.last_bin==-1?count:contract.last_bin;
  require(count>0&&contract.first_bin>=1&&last<=count&&contract.first_bin<=last,"Invalid selected regular-bin range");
  require(histogram.GetSumw2N()==0||histogram.GetSumw2N()==count+2,"Malformed ROOT Sumw2 storage");
  require(!(contract.density&&contract.flow_policy==FlowPolicy::Include),
          "Density for unbounded under/overflow bins is undefined");
  if(weighted)require(histogram.GetSumw2N()==count+2&&contract.event_sums_by_bin.size()==static_cast<std::size_t>(count+2),
                      "Weighted shape requires explicit ROOT Sumw2 and full per-bin signed event ledger");
  ShapeResult result;result.scope=contract.scope;result.mode=contract.mode;result.flow_policy=contract.flow_policy;
  result.density=contract.density;result.selection_id=contract.selection_id;
  result.variable_id=contract.variable_id;result.units=contract.units;
  if(contract.flow_policy==FlowPolicy::Include)result.bin_indices.push_back(0);
  for(int bin=contract.first_bin;bin<=last;++bin)result.bin_indices.push_back(bin);
  if(contract.flow_policy==FlowPolicy::Include)result.bin_indices.push_back(count+1);
  for(const auto bin:result.bin_indices) {
    const long double value=histogram.GetBinContent(bin);finite(value,"Source bin content");
    long double variance=0;
    if(histogram.GetSumw2N()!=0)variance=histogram.GetSumw2()->At(bin);
    else variance=value;
    finite(variance,"Source bin variance");require(variance>=0,"Negative bin sumw2");
    SignedSums sums;
    if(weighted) {
      sums=contract.event_sums_by_bin[bin];validate_sums(sums);
      require(consistent(value,sums.sumw,sums.sumabs)&&consistent(variance,sums.sumw2,sums.sumw2),
              "ROOT bin content/Sumw2 disagrees with signed event ledger");
    } else {
      require(value>=0&&std::floor(value)==value&&consistent(variance,value,value),
              "Raw-unweighted diagnostic requires integer counts and Poisson count variance");
      require(value<=std::numeric_limits<std::uint64_t>::max(),"Raw count cannot be represented");
      sums=SignedSums::from_aggregates(value,value,value,static_cast<std::uint64_t>(value));
      sums.positive=sums.entries;sums.sign_counts_known=true;
    }
    result.selected.merge(sums);result.source_sumw.push_back(value);result.source_sumw2.push_back(variance);
    const long double width=(bin>0&&bin<=count)?histogram.GetBinWidth(bin):0;
    finite(width,"Bin width");
    require(width>0||(bin==0||bin==count+1),"Nonpositive regular bin width");result.widths.push_back(width);
    result.lower_edges.push_back(bin==0?-std::numeric_limits<long double>::infinity():histogram.GetBinLowEdge(bin));
    result.upper_edges.push_back(bin==count+1?std::numeric_limits<long double>::infinity():histogram.GetBinLowEdge(bin+1));
  }
  // Use the signed histogram denominator for the stored histogram itself;
  // sumabs from the event ledger supplies the conditioning test. Both sources
  // remain intact; serialized-bin roundoff is not repaired.
  long double denominator=0;for(const auto value:result.source_sumw)denominator+=value;
  // Do not mix serialized ROOT sums with the event ledger into a fictitious
  // single moment set: each original source has already been checked locally.
  denominator=conditioned_denominator(denominator,result.selected.sumabs,contract.conditioning);
  result.normalization_denominator=denominator;result.effective_entries=result.selected.effective_entries();
  const auto size=result.bin_indices.size();result.covariance.assign(size,std::vector<long double>(size));
  std::vector<std::vector<long double>> jacobian(size,std::vector<long double>(size));
  for(std::size_t i=0;i<size;++i) {
    const auto factor=contract.density?1/result.widths[i]:1.L;
    result.values.push_back(result.source_sumw[i]/denominator*factor);
    for(std::size_t k=0;k<size;++k)
      jacobian[i][k]=(((i==k)?1.L:0.L)-result.source_sumw[i]/denominator)/denominator*factor;
  }
  for(std::size_t i=0;i<size;++i)for(std::size_t j=i;j<size;++j) {
    long double covariance=0;for(std::size_t k=0;k<size;++k)
      covariance+=jacobian[i][k]*result.source_sumw2[k]*jacobian[j][k];
    finite(covariance,"Normalized covariance");result.covariance[i][j]=result.covariance[j][i]=covariance;
  }
  for(std::size_t i=0;i<size;++i) {
    require(result.covariance[i][i]>=0,"Negative normalized variance");
    result.errors.push_back(std::sqrt(result.covariance[i][i]));finite(result.values[i],"Normalized bin");
  }
  return result;
}
void require_compatible_shapes(const ShapeResult& first,const ShapeResult& second) {
  require(first.scope==second.scope,"Synthetic/physical shape scopes cannot be combined");
  require(first.selection_id==second.selection_id&&!first.selection_id.empty(),"Different or missing selection identities");
  require(first.variable_id==second.variable_id&&first.units==second.units&&!first.variable_id.empty()&&!first.units.empty(),
          "Different or missing variable/unit identities");
  require(first.mode==second.mode&&first.density==second.density&&first.flow_policy==second.flow_policy,
          "Incompatible normalization modes or flow policies");
  require(first.bin_indices==second.bin_indices&&first.widths==second.widths&&
          first.lower_edges==second.lower_edges&&first.upper_edges==second.upper_edges,"Incompatible selected bins/edges/widths");
}
}

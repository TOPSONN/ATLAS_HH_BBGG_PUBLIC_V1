#include "AtlasControlRegions.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <set>
#include <stdexcept>
#include <utility>

namespace atlas::regions {
struct TransferAccess {
  static void require_validated(const TransferResult& t) {
    if(!t.validated_ || t.factor!=t.validated_factor_ || t.variance!=t.validated_variance_ ||
       t.mc_sr!=t.validated_sr_ || t.mc_cr!=t.validated_cr_ ||
       t.includes_nuisances!=t.validated_nuisances_ || t.covariance_model!=t.validated_model_ ||
       t.interpretation!=t.validated_interpretation_ || t.calibration_populations!=t.validated_populations_)
      throw std::invalid_argument("Transfer result unvalidated or modified after validation");
  }
};
namespace {
void finite(long double x,const char* field) {
  if(!std::isfinite(x)) throw std::invalid_argument(std::string("Nonfinite ")+field);
}
void synthetic(normalization::Scope scope) {
  if(scope!=normalization::Scope::Synthetic)
    throw std::invalid_argument("Physical transfer factors/predictions are BLOCKED; synthetic framework only");
}
void validate_yield(const Yield& y) {
  if(y.population.label.empty()) throw std::invalid_argument("Unnamed yield population");
  (void)y.sums.effective_entries(); // Reuse normalization's signed-moment integrity guard.
  if(y.sums.entries==0 && (y.sums.sumw!=0 || y.sums.sumw2!=0 || y.sums.sumabs!=0))
    throw std::invalid_argument("Nonzero moments without any event identities");
  if(y.sums.entries!=y.population.events.size()) throw std::invalid_argument("Incomplete event-population ledger");
  require_disjoint_populations({y.population});
}
void samples_for(const normalization::SampleCombination& samples,const std::vector<Population>& populations) {
  synthetic(samples.scope); normalization::validate_sample_combination(samples);
  const std::set<std::string> ids(samples.sample_ids.begin(),samples.sample_ids.end());
  for(const auto& population:populations) for(const auto& event:population.events)
    if(!ids.contains(event.namespace_id)) throw std::invalid_argument("Event identity absent from sample contract");
}
long double arithmetic_bound(long double scale,std::size_t n) {
  return 64*std::numeric_limits<long double>::epsilon()*static_cast<long double>(std::max<std::size_t>(1,n))*scale;
}
void validate_covariance(const Covariance& c,const std::vector<Yield>& yields) {
  const auto n=yields.size();
  if(n==0 || n>64 || c.values.size()!=n || c.model.empty()) throw std::invalid_argument("Missing/oversized covariance model");
  for(const auto& row:c.values) if(row.size()!=n) throw std::invalid_argument("Covariance dimensions differ");
  long double scale=0;
  for(std::size_t i=0;i<n;++i) for(std::size_t j=0;j<n;++j) {
    finite(c.values[i][j],"covariance"); scale=std::max(scale,std::abs(c.values[i][j]));
    if(c.values[i][j]!=c.values[j][i]) throw std::invalid_argument("Asymmetric covariance");
  }
  for(std::size_t i=0;i<n;++i) {
    if(c.values[i][i]<0) throw std::invalid_argument("Negative covariance diagonal");
    if(c.includes_nuisances) {
      if(c.values[i][i]<yields[i].sums.sumw2) throw std::invalid_argument("Nuisance covariance smaller than counting variance");
    } else if(c.values[i][i]!=yields[i].sums.sumw2) throw std::invalid_argument("Counting covariance diagonal differs from sumw2");
  }
  // Pivoted symmetric Schur complements validate positive semidefiniteness.
  // The tolerance is only an arithmetic residual bound; no mass/physics gate
  // is changed, and negative propagated variance is still rejected below.
  auto work=c.values; const auto tolerance=arithmetic_bound(scale,n);
  for(std::size_t k=0;k<n;++k) {
    std::size_t pivot=k;
    for(std::size_t i=k+1;i<n;++i) if(work[i][i]>work[pivot][pivot]) pivot=i;
    if(pivot!=k) {
      std::swap(work[pivot],work[k]);
      for(auto& row:work) std::swap(row[pivot],row[k]);
    }
    const auto p=work[k][k];
    if(p < -tolerance) throw std::invalid_argument("Indefinite covariance");
    if(p<=tolerance) {
      for(std::size_t i=k;i<n;++i) for(std::size_t j=k;j<n;++j)
        if(std::abs(work[i][j])>tolerance) throw std::invalid_argument("Indefinite covariance null block");
      break;
    }
    for(std::size_t i=k+1;i<n;++i) for(std::size_t j=i;j<n;++j) {
      const auto residual=work[i][j]-work[i][k]*work[j][k]/p;
      finite(residual,"covariance elimination"); work[i][j]=work[j][i]=residual;
    }
  }
}
long double quadratic(const std::vector<long double>& derivative,const Covariance& c) {
  long double result=0;
  for(std::size_t i=0;i<derivative.size();++i) for(std::size_t j=0;j<derivative.size();++j)
    result+=derivative[i]*c.values[i][j]*derivative[j];
  finite(result,"propagated variance");
  if(result<0) throw std::invalid_argument("Negative propagated variance; no clipping permitted");
  return result;
}
void cross_covariance(long double va,long double vb,long double cov) {
  finite(cov,"transfer/residual covariance");
  if(va<0 || vb<0) throw std::invalid_argument("Negative input variance");
  // Compare using square roots to avoid overflow in va*vb or cov*cov.
  const long double bound=std::sqrt(va)*std::sqrt(vb);
  finite(bound,"cross covariance bound");
  if(std::abs(cov)>bound) throw std::invalid_argument("Indefinite transfer/residual covariance");
}
} // namespace

void validate_config(const Config& c) {
  const auto& s=c.selection;
  for(double value:{s.leading_photon_pt,s.subleading_photon_pt,s.photon_eta_max,s.crack_low,s.crack_high,
                    s.mass_low,s.mass_high,s.jet_pt,s.jet_eta_max,c.sr_mass_low,c.sr_mass_high,c.photon_abs_delta_eta_split})
    finite(value,"region threshold");
  if(c.version.empty() || s.version.empty() || s.subleading_photon_pt<0 || s.leading_photon_pt<s.subleading_photon_pt ||
     s.photon_eta_max<=0 || s.crack_low<0 || s.crack_low>=s.crack_high || s.crack_high>=s.photon_eta_max ||
     s.jet_pt<0 || s.jet_eta_max<=0 || s.mass_low<0 || !(s.mass_low<c.sr_mass_low) ||
     !(c.sr_mass_low<c.sr_mass_high) || !(c.sr_mass_high<s.mass_high) || c.photon_abs_delta_eta_split<=0)
    throw std::invalid_argument("Inconsistent study region thresholds");
}
Region classify(const selection::Event& e,const Config& c) {
  validate_config(c);
  const auto passed=selection::evaluate(e,c.selection);
  if(!passed[1]) return Region::InvalidInput;
  if(!passed[5]) return Region::FailsPreMassSelection;
  if(!selection::jet_multiplicity(e) || !selection::jet_pt(e,c.selection) || !selection::jet_acceptance(e,c.selection))
    return Region::FailsJetSelection;
  if(e.mgg<c.selection.mass_low || e.mgg>c.selection.mass_high) return Region::OutsideStudyDomain;
  const bool partition_a=std::abs(e.photon_eta[0]-e.photon_eta[1])<c.photon_abs_delta_eta_split;
  const bool window=e.mgg>=c.sr_mass_low && e.mgg<c.sr_mass_high;
  if(window) return partition_a ? Region::ProspectiveSignal : Region::ReservedWindowPartition;
  return partition_a ? Region::Control : Region::Validation;
}
const char* name(Region r) {
  switch(r) {
    case Region::Control:return "CR"; case Region::Validation:return "VR";
    case Region::ProspectiveSignal:return "PROSPECTIVE_SR";
    case Region::ReservedWindowPartition:return "RESERVED_WINDOW_PARTITION";
    case Region::OutsideStudyDomain:return "OUTSIDE_STUDY_DOMAIN";
    case Region::FailsPreMassSelection:return "FAILS_C5";
    case Region::FailsJetSelection:return "FAILS_JET_SELECTION";
    case Region::InvalidInput:return "INVALID_INPUT";
  }
  throw std::invalid_argument("Unknown region enumeration");
}
void require_disjoint_populations(const std::vector<Population>& populations) {
  std::set<EventIdentity> seen; std::set<std::string> labels;
  for(const auto& p:populations) {
    if(p.label.empty() || !labels.insert(p.label).second) throw std::invalid_argument("Empty/duplicate population label");
    for(const auto& event:p.events) {
      if(event.namespace_id.empty()) throw std::invalid_argument("Missing canonical event namespace");
      if(!seen.insert(event).second) throw std::invalid_argument("Repeated event within/across populations");
    }
  }
}
Covariance independent_counting_covariance(const std::vector<Yield>& yields) {
  Covariance result; result.model="Independent synthetic counting yields; diagonal sumw2";
  result.values.assign(yields.size(),std::vector<long double>(yields.size()));
  for(std::size_t i=0;i<yields.size();++i) { validate_yield(yields[i]); result.values[i][i]=yields[i].sums.sumw2; }
  return result;
}
TransferResult transfer_factor(const TransferContract& c) {
  synthetic(c.scope);
  const std::vector<Yield> yields{c.mc_sr,c.mc_cr};
  for(const auto& y:yields) validate_yield(y);
  require_disjoint_populations({c.mc_sr.population,c.mc_cr.population});
  samples_for(c.samples,{c.mc_sr.population,c.mc_cr.population}); validate_covariance(c.covariance,yields);
  const auto denominator=normalization::require_stable_signed_sum(c.mc_cr.sums,c.conditioning);
  TransferResult result; result.mc_sr=c.mc_sr.sums.sumw; result.mc_cr=denominator;
  result.factor=result.mc_sr/denominator; finite(result.factor,"transfer factor");
  const std::vector<long double> j{1/denominator,-result.factor/denominator};
  result.variance=quadratic(j,c.covariance);
  result.calibration_populations={c.mc_sr.population,c.mc_cr.population};
  result.covariance_model=c.covariance.model;
  result.includes_nuisances=c.covariance.includes_nuisances;
  result.validated_=true; result.validated_factor_=result.factor; result.validated_variance_=result.variance;
  result.validated_sr_=result.mc_sr; result.validated_cr_=result.mc_cr;
  result.validated_nuisances_=result.includes_nuisances; result.validated_model_=result.covariance_model;
  result.validated_interpretation_=result.interpretation;
  result.validated_populations_=result.calibration_populations;
  return result;
}
Prediction predict_background(const TransferResult& t,const ResidualContract& c,long double cov) {
  synthetic(t.scope); synthetic(c.scope); finite(t.factor,"transfer factor"); finite(t.variance,"transfer variance");
  TransferAccess::require_validated(t);
  if(t.variance<0 || t.calibration_populations.size()!=2 || t.covariance_model.empty())
    throw std::invalid_argument("Invalid transfer result contract");
  std::vector<Yield> yields{c.data_cr}; yields.insert(yields.end(),c.other_backgrounds_cr.begin(),c.other_backgrounds_cr.end());
  auto populations=t.calibration_populations;
  for(const auto& y:yields) { validate_yield(y); populations.push_back(y.population); }
  require_disjoint_populations(populations); samples_for(c.samples,populations); validate_covariance(c.covariance,yields);
  std::vector<long double> a(yields.size(),-1); a[0]=1;
  Prediction result; result.residual_cr=c.data_cr.sums.sumw;
  for(const auto& y:c.other_backgrounds_cr) result.residual_cr-=y.sums.sumw;
  finite(result.residual_cr,"subtracted CR yield"); result.residual_variance=quadratic(a,c.covariance);
  cross_covariance(t.variance,result.residual_variance,cov);
  result.prediction_sr=t.factor*result.residual_cr;
  result.variance=result.residual_cr*result.residual_cr*t.variance+t.factor*t.factor*result.residual_variance+
                  2*t.factor*result.residual_cr*cov;
  finite(result.prediction_sr,"predicted yield"); finite(result.variance,"predicted variance");
  if(result.variance<0) throw std::invalid_argument("Negative prediction variance; no clipping permitted");
  result.includes_nuisances=t.includes_nuisances || c.covariance.includes_nuisances;
  result.validated_=true; result.calibration_populations_=std::move(populations);
  return result;
}
void require_held_out_validation(const TransferResult& t,const Population& validation) {
  synthetic(t.scope);
  TransferAccess::require_validated(t);
  if(t.calibration_populations.size()!=2 || validation.events.empty()) throw std::invalid_argument("Missing held-out validation ledger");
  auto populations=t.calibration_populations; populations.push_back(validation); require_disjoint_populations(populations);
}
void require_held_out_validation(const Prediction& p,const Population& validation) {
  if(!p.validated_ || validation.events.empty()) throw std::invalid_argument("Missing prediction/held-out validation ledger");
  auto populations=p.calibration_populations_; populations.push_back(validation); require_disjoint_populations(populations);
}
} // namespace atlas::regions

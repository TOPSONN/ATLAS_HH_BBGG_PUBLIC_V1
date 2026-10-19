#include "Phase8Statistics.hxx"
#include "Phase8Weights.hxx"
#include <TMatrixDSym.h>
#include <TMatrixDSymEigen.h>
#include <TVectorD.h>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <numeric>
#include <set>
#include <stdexcept>
namespace phase8 {
namespace {
void require(bool ok,const char* reason){if(!ok)throw std::invalid_argument(reason);}
double checked(long double x){const auto y=static_cast<double>(x);require(std::isfinite(y),"NONFINITE_STATISTIC");return y;}
Json optionalNumber(std::optional<double> x){return x?Json(*x):Json(nullptr);}
Json edgeMap(const Json& input){
 if(input.contains("edges"))return input.at("edges");
 if(input.contains("observables"))return input.at("observables");
 return input;
}
std::vector<double> validatedEdges(const Json& raw){
 const auto edges=(raw.is_array()?raw:raw.at("edges")).get<std::vector<double>>();
 require(edges.size()>=2,"INVALID_HISTOGRAM_EDGES");
 for(std::size_t j=0;j<edges.size();++j)require(std::isfinite(edges[j])&&(j==0||edges[j]>edges[j-1]),"INVALID_HISTOGRAM_EDGES");
 return edges;
}
}
WeightSummary summarizeWeights(std::span<const double> x,std::size_t n){
 require(n>=2&&x.size()==n,"FULL_ORIGINAL_N_DENOMINATOR_REQUIRED");
 WeightSummary s;s.originalN=n;
 long double sum=0,square=0,absSum=0,maxAbs=0,shiftSum=0;
 const long double origin=x.front();
 for(auto value:x){require(std::isfinite(value),"NONFINITE_WEIGHT");const long double v=value;
  sum+=v;square+=v*v;absSum+=std::abs(v);maxAbs=std::max(maxAbs,std::abs(v));shiftSum+=v-origin;
  s.positive+=value>0;s.negative+=value<0;s.zero+=value==0;
 }
 const long double shiftedMean=shiftSum/n;
 long double centered=0;
 for(auto value:x){const long double d=(static_cast<long double>(value)-origin)-shiftedMean;centered+=d*d;}
 require(centered>=0,"NEGATIVE_CENTERED_VARIANCE");
 s.sumw=checked(sum);s.sumw2=checked(square);s.sumAbs=checked(absSum);s.mean=checked(sum/n);
 s.sampleVariance=checked(centered/(n-1));s.fixedNVariance=checked(centered*n/(n-1));
 if(square>0)s.ess=checked(sum*sum/square);
 if(absSum>0){s.cancellationRatio=checked(std::abs(sum)/absSum);s.largestFraction=checked(maxAbs/absSum);}
 return s;
}
double fixedNCovariance(std::span<const double> a,std::span<const double> b){
 require(a.size()==b.size()&&a.size()>=2,"PAIRED_FULL_SOURCE_REQUIRED");
 const auto n=a.size();long double da=0,db=0;
 for(std::size_t i=0;i<n;++i){require(std::isfinite(a[i])&&std::isfinite(b[i]),"NONFINITE_COVARIANCE_INPUT");da+=static_cast<long double>(a[i])-a[0];db+=static_cast<long double>(b[i])-b[0];}
 da/=n;db/=n;long double cross=0;
 for(std::size_t i=0;i<n;++i)cross+=((static_cast<long double>(a[i])-a[0])-da)*((static_cast<long double>(b[i])-b[0])-db);
 return checked(cross*n/(n-1));
}
double zeroSuccessUpper(std::size_t n,double confidence){
 require(n>0&&std::isfinite(confidence)&&confidence>0&&confidence<1,"INVALID_ZERO_COUNT_BOUND");
 return -std::expm1(std::log1p(-confidence)/static_cast<double>(n));
}
Json weightSummaryJson(const WeightSummary&s){
 return {{"N_original",s.originalN},{"sumw",s.sumw},{"sumw2",s.sumw2},{"sum_absw",s.sumAbs},
 {"mean_weight",s.mean},{"weight_sample_variance",s.sampleVariance},{"fixed_N_source_sampling_variance",s.fixedNVariance},
 {"ESS",optionalNumber(s.ess)},{"ESS_status",s.ess?"DEFINED":"UNDEFINED_ZERO_SECOND_MOMENT"},
 {"cancellation_ratio",optionalNumber(s.cancellationRatio)},{"largest_absolute_fraction",optionalNumber(s.largestFraction)},
 {"N_positive",s.positive},{"N_negative",s.negative},{"N_zero",s.zero},
 {"sampling_scope","same original source cohort including zero after cuts; realized shower/detector/tag variation already present"}};
}
TagProbabilities conditionalTags(std::span<const double> probabilities){
 long double p0=1,p1=0,p2=0;
 for(double value:probabilities){require(std::isfinite(value)&&value>=0&&value<=1,"INVALID_BERNOULLI_PROBABILITY");const long double p=value;
  p2+=p1*p;p1=p1*(1-p)+p0*p;p0*=1-p;
 }
 const long double mass=p0+p1+p2;
 require(std::abs(mass-1)<=128*std::numeric_limits<long double>::epsilon()*std::max<std::size_t>(1,probabilities.size()),"TAG_DP_MASS_FAILURE");
 return {checked(p0),checked(p1),checked(p2)};
}
double nativeTagProbability(int flavour,double pt){
 require(std::isfinite(pt)&&pt>=0,"INVALID_PERSISTED_JET_PT");double p=0;
 if(flavour==5)p=.80*std::tanh(.003*pt)*30./(1.+.086*pt);
 else if(flavour==4)p=.20*std::tanh(.02*pt)/(1.+.0034*pt);
 else {require(flavour==0||flavour==1||flavour==2||flavour==3||flavour==21,"UNSUPPORTED_NATIVE_JET_FLAVOUR");p=.002+7.3e-6*pt;}
 return std::clamp(p,0.,1.);
}
std::vector<Json> readEventSummaries(const std::string& path,const std::string& datasetFilter){
 std::ifstream input(path);require(input.good(),"MISSING_EVENT_SUMMARY");std::vector<Json> result;std::string line;
 std::set<std::size_t> ordinals;std::string dataset;
 while(std::getline(input,line)){require(!line.empty()&&line.size()<2*1024*1024,"INVALID_EVENT_SUMMARY_LINE");auto row=Json::parse(line);
  if(!datasetFilter.empty()&&row.at("dataset_id").get<std::string>()!=datasetFilter)continue;
  const auto ordinal=row.at("source_event_ordinal").get<std::size_t>();require(ordinal>0&&ordinals.insert(ordinal).second,"DUPLICATE_SOURCE_EVENT");
  const auto name=row.at("dataset_id").get<std::string>();if(dataset.empty())dataset=name;require(name==dataset,"MIXED_DATASET_EVENT_SUMMARY");
  require(row.at("stages").is_array()&&row.at("stages").size()==5,"INVALID_STAGE_VECTOR");
  for(auto& stage:row.at("stages"))require(stage.is_boolean(),"NONBOOLEAN_STAGE");
  require(row.at("stages")[0].get<bool>(),"INPUT_STAGE_FALSE");
  for(std::size_t j=1;j<5;++j)require(!row.at("stages")[j].get<bool>()||row.at("stages")[j-1].get<bool>(),"NONNESTED_CUTFLOW");
  require(std::isfinite(row.at("source_weight_pb").get<double>()),"NONFINITE_SOURCE_WEIGHT");result.push_back(std::move(row));
 }
 require(result.size()>=2,"EMPTY_OR_SINGLE_EVENT_SUMMARY");
 std::sort(result.begin(),result.end(),[](const Json&a,const Json&b){return a.at("source_event_ordinal").get<std::size_t>()<b.at("source_event_ordinal").get<std::size_t>();});
 for(std::size_t i=0;i<result.size();++i)require(result[i].at("source_event_ordinal").get<std::size_t>()==i+1&&result[i].at("N_original").get<std::size_t>()==result.size(),"MISSING_SOURCE_EVENT_OR_WRONG_N");
 return result;
}
Json commonSourceCovariance(const std::vector<std::array<double,6>>& events){
 require(events.size()>=2,"COVARIANCE_NEEDS_ORIGINAL_EVENTS");
 std::array<std::vector<double>,6> columns;for(auto&e:events)for(std::size_t k=0;k<6;++k)columns[k].push_back(e[k]);
 TMatrixDSym matrix(6);double largest=0;Json cov=Json::array(),corr=Json::array();
 for(int k=0;k<6;++k)for(int l=0;l<6;++l){matrix(k,l)=fixedNCovariance(columns[k],columns[l]);largest=std::max(largest,std::abs(matrix(k,l)));}
 for(int k=0;k<6;++k){Json c=Json::array(),r=Json::array();require(matrix(k,k)>=0,"NEGATIVE_COVARIANCE_DIAGONAL");
  for(int l=0;l<6;++l){c.push_back(matrix(k,l));const auto d=std::sqrt(matrix(k,k)*matrix(l,l));r.push_back(d>0?Json(matrix(k,l)/d):Json(nullptr));require(matrix(k,l)==matrix(l,k),"NONSYMMETRIC_COVARIANCE");}cov.push_back(c);corr.push_back(r);}
 const auto eigen=TMatrixDSymEigen(matrix).GetEigenValues();double minimum=eigen[0];for(int k=1;k<6;++k)minimum=std::min(minimum,eigen[k]);
 const double tolerance=256*std::numeric_limits<double>::epsilon()*6*std::max(largest,std::numeric_limits<double>::min());
 require(minimum>=-tolerance,"COVARIANCE_NOT_POSITIVE_SEMIDEFINITE");
 return {{"N_original",events.size()},{"covariance",cov},{"correlation",corr},{"minimum_eigenvalue",minimum},{"PSD_absolute_tolerance",tolerance},{"PSD_status","PASS_WITH_ARITHMETIC_TOLERANCE"},{"eigenvalues_modified",false},{"common_source_pairing",true}};
}
Json analyzeEventStatistics(const std::vector<Json>& events,double factor,int applied,const Json& edgeInput){
 const auto n=events.size();require(n>=2,"ORIGINAL_SOURCE_COHORT_REQUIRED");
 WeightContract contract{factor==1.?"RAW_SOURCE":"MODEL_BR_ONLY",factor,applied};
 std::vector<double> model;for(auto&e:events){require(e.at("N_original").get<std::size_t>()==n,"ORIGINAL_N_MISMATCH");model.push_back(contract.applyModelFactor(e.at("source_weight_pb").get<double>()));}
 Json stages=Json::array(),tag=Json::array(),bins=Json::array();
 const std::array<std::string,5> names{"INPUT","PHOTONS","JETS","TWO_BTAGS","FINAL_MGG"};
 const auto edges=edgeMap(edgeInput);
 for(std::size_t stage=0;stage<5;++stage){std::vector<double> contribution(n);std::size_t passed=0;
  for(std::size_t i=0;i<n;++i)if(events[i].at("stages")[stage].get<bool>()){contribution[i]=model[i];++passed;}
  auto s=weightSummaryJson(summarizeWeights(contribution,n));s["stage"]=names[stage];s["N_pass"]=passed;s["efficiency_original_N"]=static_cast<double>(passed)/n;
  s["zero_count_one_sided95_proposal_upper"]=passed==0?Json(zeroSuccessUpper(n)):Json(nullptr);
  s["weighted_rate_upper_bound"]=nullptr;s["ILLUSTRATIVE_MODEL_YIELD_100fb"]=illustrativeYield(s["sumw"].get<double>());stages.push_back(s);
  for(auto it=edges.begin();it!=edges.end();++it){if(!it.value().is_array()&&!it.value().is_object())continue;
   const auto e=validatedEdges(it.value());std::vector<std::vector<double>> values(e.size()+1,std::vector<double>(n));std::vector<std::size_t> counts(e.size()+1);std::size_t missing=0;
   for(std::size_t i=0;i<n;++i){if(!events[i].at("stages")[stage].get<bool>())continue;const auto&obs=events[i].at("observables");
    if(!obs.contains(it.key())||obs.at(it.key()).is_null()){++missing;continue;}const auto v=obs.at(it.key()).get<double>();require(std::isfinite(v),"NONFINITE_OBSERVABLE");
    const auto b=std::upper_bound(e.begin(),e.end(),v)-e.begin();values[b][i]=model[i];++counts[b];}
   for(std::size_t b=0;b<values.size();++b){auto bs=weightSummaryJson(summarizeWeights(values[b],n));bs["stage"]=names[stage];bs["observable"]=it.key();bs["bin"]=b;bs["flow"]=b==0?"underflow":b==e.size()?"overflow":"regular";
    bs["N_original_sources_contributing"]=counts[b];bs["missing_kinematics"]=missing;
    bs["quality_flag"]=counts[b]==0?"EMPTY_BIN":!bs["cancellation_ratio"].is_null()&&bs["cancellation_ratio"].get<double>()<1e-12?"CANCELLATION_DOMINATED":bs["ESS"].is_null()?"EMPTY_BIN":bs["ESS"].get<double>()<10?"LOW_ESS_LT10":bs["ESS"].get<double>()<20?"LOW_ESS_LT20":bs["largest_absolute_fraction"].get<double>()>.1?"HIGH_SINGLE_EVENT_DOMINANCE":"VALID_DESCRIPTIVE_ONLY";bins.push_back(bs);}
  }
 }
 for(std::size_t stage: {std::size_t(3),std::size_t(4)}){std::vector<double> expected(n),observed(n),q(n);long double count=0,countVariance=0,weightedVariance=0,zeroCount=0,oneCount=0;std::size_t tagEligible=0;
  for(std::size_t i=0;i<n;++i){const auto&e=events[i];const bool eligible=e.at("stages")[2].get<bool>();
   std::vector<double> probabilities;for(auto&jet:e.at("eligible_jets")){require(jet.at("pt").get<double>()>25&&std::abs(jet.at("eta").get<double>())<2.5,"INELIGIBLE_JET_IN_TAG_MODEL");probabilities.push_back(nativeTagProbability(jet.at("flavour").get<int>(),jet.at("pt").get<double>()));}
   const auto p=conditionalTags(probabilities);bool mass=true;const auto&obs=e.at("observables");
   if(stage==4){const auto&m=obs.at("m_gamma_gamma");mass=!m.is_null()&&m.get<double>()>=105&&m.get<double>()<=160;}
   if(eligible&&mass){zeroCount+=p.zero;oneCount+=p.one;++tagEligible;}
   q[i]=eligible&&mass?p.atLeastTwo:0.;expected[i]=model[i]*q[i];observed[i]=e.at("stages")[stage].get<bool>()?model[i]:0.;count+=q[i];countVariance+=q[i]*(1-q[i]);weightedVariance+=static_cast<long double>(model[i])*model[i]*q[i]*(1-q[i]);
  }
  require(std::abs(zeroCount+oneCount+count-tagEligible)<=1e-10L,"TAG_CATEGORY_EXPECTATION_PARTITION_FAILURE");
  tag.push_back({{"stage",names[stage]},{"N_original",n},{"eligible_before_tag_count",tagEligible},{"expected_tag0_count",checked(zeroCount)},{"expected_tag1_count",checked(oneCount)},{"expected_count",checked(count)},{"conditional_count_variance",checked(countVariance)},
   {"conditional_weighted_variance_pb2",checked(weightedVariance)},{"analytic_expectation",weightSummaryJson(summarizeWeights(expected,n))},
   {"observed_actual_tag_draw",weightSummaryJson(summarizeWeights(observed,n))},{"variance_components_added",false},
   {"interpretation","CONDITIONAL_ANALYTIC_EXPECTATION; independent Bernoulli given pinned reconstructed jets; persisted Float_t PT approximation; never add tag variance to observed-outcome source sampling variance"},
   {"mass_distribution_scope","actual leading tagged pair only; analytic tag count is not a conditional m_bb or m_HH distribution"}});
 }
 return {{"dataset_id",events.front().at("dataset_id")},{"N_original",n},{"weight_scope",factor==1.?"RAW_SOURCE_EXPLORATORY":"MODEL_BR_ONLY_EXPLORATORY"},{"model_BR_factor",factor},{"factor_applications",factor==1.?0:1},{"stages",stages},{"conditional_tags",tag},{"bin_quality",bins},{"physical_combined_background","BLOCKED_OVERLAP_AND_CALIBRATION"}};
}
}

#include "Phase8Kappa.hxx"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <set>
#include <sstream>
#include <stdexcept>
namespace phase8 {
namespace {
void require(bool v,const char* msg){if(!v)throw std::invalid_argument(msg);}
std::vector<std::string> split(const std::string& line){std::vector<std::string> out;std::stringstream stream(line);std::string cell;while(std::getline(stream,cell,','))out.push_back(cell);return out;}
double number(const std::string&s){std::size_t used=0;const auto d=std::stod(s,&used);require(used==s.size()&&std::isfinite(d),"NONFINITE_OR_INVALID_KAPPA_VALUE");return d;}
bool near(double a,double b){return std::abs(a-b)<=1e-11*std::max({std::abs(a),std::abs(b),1e-20});}
void save(const std::filesystem::path&p,const Json&value){require(!std::filesystem::exists(p),"REFUSE_OUTPUT_OVERWRITE");std::ofstream out(p);require(out.good(),"OUTPUT_CREATE_FAILED");out<<value.dump(2)<<'\n';}
Json edgeMap(const Json&j){if(j.contains("edges"))return j.at("edges");if(j.contains("observables"))return j.at("observables");return j;}
std::vector<double> edgesOf(const Json&j){const auto v=(j.is_array()?j:j.at("edges")).get<std::vector<double>>();require(v.size()>=2,"INVALID_KAPPA_EDGES");for(std::size_t i=0;i<v.size();++i)require(std::isfinite(v[i])&&(i==0||v[i]>v[i-1]),"INVALID_KAPPA_EDGES");return v;}
std::string flag(const WeightSummary&s,std::size_t count){if(count==0)return "EMPTY_BIN";if(s.cancellationRatio&&*s.cancellationRatio<1e-12)return "CANCELLATION_DOMINATED";if(!s.ess)return "EMPTY_BIN";if(*s.ess<10)return "LOW_ESS_LT10";if(*s.ess<20)return "LOW_ESS_LT20";if(s.largestFraction&&*s.largestFraction>.1)return "HIGH_SINGLE_EVENT_DOMINANCE";return "VALID_DESCRIPTIVE_ONLY";}
}
std::vector<KappaRow> loadKappaRows(const std::filesystem::path&csv,const std::vector<Json>&events,double br,std::size_t n){
 require(events.size()==n&&n>=2&&std::isfinite(br)&&br>0&&br<=1,"KAPPA_SOURCE_COHORT_OR_BR_INVALID");
 std::ifstream in(csv);require(in.good(),"MISSING_KAPPA_CSV");std::string line;std::getline(in,line);
 const std::string header="source_event_index,source_event_sha256,source_alpha_s,source_scale_gev,kappa_lambda,full_mass_squared_ME,SM_denominator,ratio,source_contribution_pb,MODEL_BR_ONLY_weight_pb,return_code,precision,quadratic_residual,SM_repeat_relative_residual";
 require(line==header,"UNSUPPORTED_KAPPA_CSV_SCHEMA");std::vector<KappaRow> rows(n);std::vector<std::array<bool,6>> seen(n);std::vector<double> alpha(n),scale(n);std::size_t count=0;
 while(std::getline(in,line)){const auto v=split(line);require(v.size()==14,"INVALID_KAPPA_CSV_ROW");std::size_t used=0;const auto ordinal=std::stoul(v[0],&used);require(used==v[0].size()&&ordinal>=1&&ordinal<=n,"KAPPA_SOURCE_ORDINAL_OUT_OF_RANGE");const auto i=ordinal-1;
  require(events[i].at("source_event_ordinal").get<std::size_t>()==ordinal&&events[i].at("source_event_sha256").get<std::string>()==v[1],"KAPPA_NATIVE_SOURCE_HASH_MISMATCH");
  const auto kappa=number(v[4]);const auto it=std::find(kappaBenchmarks.begin(),kappaBenchmarks.end(),kappa);require(it!=kappaBenchmarks.end(),"UNEXPECTED_KAPPA_LABEL");const auto k=it-kappaBenchmarks.begin();require(!seen[i][k],"DUPLICATE_SOURCE_KAPPA_ROW");
  const auto as=number(v[2]),sc=number(v[3]),me=number(v[5]),den=number(v[6]),ratio=number(v[7]);const auto w=number(v[8]),wm=number(v[9]);
  require(as>0&&sc>0&&me>=0&&den>0&&ratio>=0&&near(ratio,me/den),"INVALID_HISTORICAL_ME_RATIO");
  require(near(w,ratio*events[i].at("source_weight_pb").get<double>()),"UNEXPECTED_KAPPA_WEIGHT_NORMALIZATION");require(near(wm,w*br),"DUPLICATE_OR_MISSING_KAPPA_BR");
  require(number(v[10])>=0&&std::floor(number(v[10]))==number(v[10]),"INVALID_HISTORICAL_RETURN_CODE");
  require(number(v[11])>=0&&number(v[12])>=0&&number(v[13])>=0,"INVALID_HISTORICAL_ME_DIAGNOSTIC");
  if(rows[i].sourceOrdinal){require(rows[i].sourceHash==v[1]&&alpha[i]==as&&scale[i]==sc,"KAPPA_SOURCE_METADATA_DRIFT");}else{rows[i].sourceOrdinal=ordinal;rows[i].sourceHash=v[1];alpha[i]=as;scale[i]=sc;}
  rows[i].production[k]=w;rows[i].model[k]=wm;rows[i].ratio[k]=ratio;seen[i][k]=true;++count;
 }
 require(count==n*6,"MISSING_KAPPA_ROWS");for(std::size_t i=0;i<n;++i){require(std::all_of(seen[i].begin(),seen[i].end(),[](bool x){return x;}),"MISSING_KAPPA_BENCHMARK");require(near(rows[i].ratio[2],1.),"SM_REWEIGHT_NOT_IDENTITY");}
 return rows;
}
Json analyzeKappa(const std::vector<KappaRow>&rows,const std::vector<Json>&events,const Json&edgeInput,const std::filesystem::path&out){
 const auto n=rows.size();require(n==events.size()&&n>=2,"INVALID_KAPPA_PAIRED_EVENTS");
 const std::array<std::string,5> stages{"INPUT","PHOTONS","JETS","TWO_BTAGS","FINAL_MGG"};
 Json summaries=Json::array(),tails=Json::array(),matrices=Json::array(),binResults=Json::array();
 std::ofstream csvSummary(out/"phase8_kappa_summary.csv"),csvCov(out/"phase8_kappa_covariance.csv"),csvCorr(out/"phase8_kappa_correlations.csv"),csvBins(out/"phase8_kappa_bin_quality.csv");
 require(csvSummary.good()&&csvCov.good()&&csvCorr.good()&&csvBins.good(),"KAPPA_OUTPUT_FAILED");
 for(auto*f:{&csvSummary,&csvCov,&csvCorr,&csvBins})*f<<std::setprecision(17);
 csvSummary<<"kappa_lambda,N_original,sumw_raw_production_pb,sumw2_raw_production_pb2,sum_absw_raw_production_pb,mean_weight_pb,weight_sample_variance_pb2,max_weight_ratio,top1_fraction,top5_fraction,top10_fraction,input_ESS,final_ESS,negative_count,zero_count,status\n";
 csvCov<<"stage,weight_scope,kappa_a,kappa_b,covariance_pb2,N_original\n";csvCorr<<"stage,weight_scope,kappa_a,kappa_b,correlation,N_original\n";
 csvBins<<"stage,observable,kappa_lambda,bin,flow,N_original,N_original_sources_contributing,sumw,sumw2,sum_absw,ESS,largest_fraction,missing_kinematics,quality_flag\n";
 for(std::size_t k=0;k<6;++k){std::vector<double> raw(n),final(n);double maxRatio=0;std::vector<std::pair<double,std::size_t>> ranked;
  for(std::size_t i=0;i<n;++i){raw[i]=rows[i].production[k];final[i]=events[i].at("stages")[4].get<bool>()?rows[i].model[k]:0.;maxRatio=std::max(maxRatio,rows[i].ratio[k]);ranked.emplace_back(std::abs(raw[i]),i);}
  std::stable_sort(ranked.begin(),ranked.end(),[](auto&a,auto&b){return a.first>b.first;});const auto s=summarizeWeights(raw,n),f=summarizeWeights(final,n);long double top1=0,top5=0,top10=0;Json dominant=Json::array();
  for(std::size_t rank=0;rank<std::min<std::size_t>(10,n);++rank){if(rank==0)top1+=ranked[rank].first;if(rank<5)top5+=ranked[rank].first;top10+=ranked[rank].first;
   const auto i=ranked[rank].second;dominant.push_back({{"source_event_ordinal",rows[i].sourceOrdinal},{"source_event_sha256",rows[i].sourceHash},{"ratio",rows[i].ratio[k]},{"production_weight_pb",raw[i]},{"final_selected",events[i].at("stages")[4]}});}
  const auto fraction=[&](long double x){return s.sumAbs>0?static_cast<double>(x/s.sumAbs):0.;};
  const std::string status=(kappaBenchmarks[k]==2.5||kappaBenchmarks[k]==5.)?"INCONCLUSIVE_REWEIGHTING":"VALID_DESCRIPTIVE_ONLY";
  Json item={{"kappa_lambda",kappaBenchmarks[k]},{"input",weightSummaryJson(s)},{"final",weightSummaryJson(f)},{"max_weight_ratio",maxRatio},{"top1_contribution_fraction",fraction(top1)},{"top5_contribution_fraction",fraction(top5)},{"top10_contribution_fraction",fraction(top10)},{"nonfinite_count",0},{"status",status},{"absolute_rate_status","INCONCLUSIVE_HISTORICAL_PDF_ALPHA_S_AND_INTEGRAL_NORMALIZATION"}};summaries.push_back(item);tails.push_back({{"kappa_lambda",kappaBenchmarks[k]},{"dominant_sources",dominant},{"status",status}});
  csvSummary<<kappaBenchmarks[k]<<','<<n<<','<<s.sumw<<','<<s.sumw2<<','<<s.sumAbs<<','<<s.mean<<','<<s.sampleVariance<<','<<maxRatio<<','<<fraction(top1)<<','<<fraction(top5)<<','<<fraction(top10)<<',';if(s.ess)csvSummary<<*s.ess;csvSummary<<',';if(f.ess)csvSummary<<*f.ess;csvSummary<<','<<s.negative<<','<<s.zero<<','<<status<<'\n';
 }
 for(std::size_t stage=0;stage<5;++stage){std::vector<std::array<double,6>> contribution(n);
  for(std::size_t i=0;i<n;++i)for(std::size_t k=0;k<6;++k)contribution[i][k]=events[i].at("stages")[stage].get<bool>()?rows[i].model[k]:0.;
  auto matrix=commonSourceCovariance(contribution);matrix["stage"]=stages[stage];matrix["weight_scope"]="MODEL_BR_ONLY";matrices.push_back(matrix);
  for(std::size_t k=0;k<6;++k)for(std::size_t l=0;l<6;++l){csvCov<<stages[stage]<<",MODEL_BR_ONLY,"<<kappaBenchmarks[k]<<','<<kappaBenchmarks[l]<<','<<matrix["covariance"][k][l]<<','<<n<<'\n';csvCorr<<stages[stage]<<",MODEL_BR_ONLY,"<<kappaBenchmarks[k]<<','<<kappaBenchmarks[l]<<',';if(!matrix["correlation"][k][l].is_null())csvCorr<<matrix["correlation"][k][l];csvCorr<<','<<n<<'\n';}
  const auto edges=edgeMap(edgeInput);
  for(auto it=edges.begin();it!=edges.end();++it){if(!it.value().is_array()&&!it.value().is_object())continue;const auto e=edgesOf(it.value());std::vector<std::optional<std::size_t>> assignments(n);std::size_t missing=0;
   for(std::size_t i=0;i<n;++i){if(!events[i].at("stages")[stage].get<bool>())continue;const auto&obs=events[i].at("observables");if(!obs.contains(it.key())||obs.at(it.key()).is_null()){++missing;continue;}const auto v=obs.at(it.key()).get<double>();require(std::isfinite(v),"NONFINITE_KAPPA_OBSERVABLE");assignments[i]=std::upper_bound(e.begin(),e.end(),v)-e.begin();}
   for(std::size_t k=0;k<6;++k)for(std::size_t b=0;b<=e.size();++b){std::vector<double> values(n);std::size_t count=0;for(std::size_t i=0;i<n;++i)if(assignments[i]&&*assignments[i]==b){values[i]=rows[i].model[k];++count;}
    const auto s=summarizeWeights(values,n);const std::string flow=b==0?"underflow":b==e.size()?"overflow":"regular";const auto quality=flag(s,count);
    Json item=weightSummaryJson(s);item.update({{"stage",stages[stage]},{"observable",it.key()},{"kappa_lambda",kappaBenchmarks[k]},{"bin",b},{"flow",flow},{"N_original_sources_contributing",count},{"missing_kinematics",missing},{"quality_flag",quality}});binResults.push_back(item);
    csvBins<<stages[stage]<<','<<it.key()<<','<<kappaBenchmarks[k]<<','<<b<<','<<flow<<','<<n<<','<<count<<','<<s.sumw<<','<<s.sumw2<<','<<s.sumAbs<<',';if(s.ess)csvBins<<*s.ess;csvBins<<',';if(s.largestFraction)csvBins<<*s.largestFraction;csvBins<<','<<missing<<','<<quality<<'\n';
   }
  }
 }
 Json result={{"status","PASS_COMMON_SOURCE_KAPPA_DIAGNOSTICS_WITH_LIMITS"},{"N_original_independent_sources",n},{"weight_rows",n*6},{"new_ME_calls",0},{"new_events",0},{"benchmarks",kappaBenchmarks},{"summaries",summaries},{"covariance_by_stage",matrices},{"bin_quality_rows",binResults.size()},{"source_PDF","NNPDF23_LO"},{"alpha_s_running","TWO_LOOP"},{"source_seed",20261122},{"physical_kappa_interval","NOT_EVALUATED"}};
 save(out/"phase8_kappa_weight_tails.json",tails);save(out/"phase8_kappa_summary.json",result);save(out/"phase8_kappa_bin_quality.json",binResults);return result;
}
}

#include "Phase8Statistics.hxx"
#include "Phase8Weights.hxx"
#include "Phase8Kappa.hxx"
#include <cmath>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
namespace {int count=0;void require(bool x,const char*s){++count;if(!x)throw std::runtime_error(s);}template<class F>bool rejects(F f){try{f();return false;}catch(const std::invalid_argument&){return true;}}}
int main(){try{
 using namespace phase8;
 const std::vector<double>x{1,2,3,4},zero{0,0,0,0},signedWeights{1,-1,0,0},constant{.01,.01,.01,.01};
 const auto a=summarizeWeights(x,4);require(a.sumw==10&&a.sumw2==30,"sum moments");require(std::abs(a.fixedNVariance-20./3.)<1e-14,"fixed original N variance");require(a.ess&&std::abs(*a.ess-100./30.)<1e-14,"ESS");require(a.positive==4&&a.zero==0,"sign counts");
 require(summarizeWeights(constant,4).fixedNVariance==0,"exact constant zero variance");const auto sw=summarizeWeights(signedWeights,4);require(sw.sumw==0&&sw.ess&&*sw.ess==0&&sw.cancellationRatio&&*sw.cancellationRatio==0,"signed cancellation retained");require(std::abs(sw.fixedNVariance-8./3.)<1e-14,"signed variance");require(!summarizeWeights(zero,4).ess,"zero ESS undefined");require(rejects([&]{summarizeWeights(x,2);}),"selected subset denominator rejected");
 require(rejects([&]{auto bad=x;bad[1]=std::numeric_limits<double>::quiet_NaN();summarizeWeights(bad,4);}),"nonfinite rejected");require(std::abs(fixedNCovariance(x,x)-a.fixedNVariance)<1e-14,"covariance diagonal");require(fixedNCovariance(x,constant)==0,"constant covariance zero");require(fixedNCovariance(x,signedWeights)==fixedNCovariance(signedWeights,x),"symmetry");
 require(std::abs(zeroSuccessUpper(1000)-.0029912495450953314)<1e-15,"zero proposal upper");require(rejects([]{zeroSuccessUpper(0);}),"invalidzero N");
 const auto p=conditionalTags(std::vector<double>{.2,.3,.4});require(std::abs(p.zero-.336)<1e-14&&std::abs(p.one-.452)<1e-14&&std::abs(p.atLeastTwo-.212)<1e-14,"tag DP enumeration");
 require(conditionalTags(std::vector<double>{1,1,0}).atLeastTwo==1,"deterministic tags");require(conditionalTags(std::vector<double>{}).zero==1,"empty tags");require(std::abs(conditionalTags(std::vector<double>{1e-14,1e-14}).atLeastTwo-1e-28)<1e-42,"tiny direct >=2 tail");require(rejects([]{conditionalTags(std::vector<double>{1.01});}),"invalid probability");
 require(std::abs(nativeTagProbability(0,100)-.00273)<1e-15,"light formula");require(std::abs(nativeTagProbability(4,100)-.2*std::tanh(2)/1.34)<1e-15,"charm formula");require(std::abs(nativeTagProbability(5,100)-.8*std::tanh(.3)*30/9.6)<1e-15,"bformula");require(rejects([]{nativeTagProbability(6,100);}),"unknown flavour");
 WeightContract model{"MODEL_BR_ONLY",.002653445906720871,0};require(model.applyModelFactor(-2)==-2*model.modelFactor,"signed BR once");require(rejects([&]{auto d=model;d.alreadyApplied=1;d.applyModelFactor(1);}),"BR twice rejection");require(rejects([]{WeightContract{"RAW_SOURCE",.2,0}.applyModelFactor(1);}),"rawscope nonidentity reject");require(illustrativeYield(.001)==100.,"pb fb conversion");
 std::vector<std::array<double,6>> c(4);for(std::size_t i=0;i<4;++i)for(std::size_t k=0;k<6;++k)c[i][k]=(i+1)*(k+1)*1e-6;const auto cov=commonSourceCovariance(c);require(cov.at("common_source_pairing").get<bool>(),"common source");require(cov.at("PSD_status")=="PASS_WITH_ARITHMETIC_TOLERANCE","PSD rank deficient");require(std::abs(cov["correlation"][0][5].get<double>()-1)<1e-14,"paired correlation");
 std::vector<KappaRow> toyRows(4);std::vector<Json> toyEvents(4);
 for(std::size_t i=0;i<4;++i){toyRows[i].sourceOrdinal=i+1;toyRows[i].sourceHash=std::string(64,'0');for(std::size_t k=0;k<6;++k){toyRows[i].production[k]=(i+1)*(k+1)*1e-5;toyRows[i].model[k]=toyRows[i].production[k]*.002;toyRows[i].ratio[k]=k+1;}toyEvents[i]={{"stages",Json::array({true,false,false,false,false})},{"observables",{{"m_gamma_gamma",nullptr}}}};}
 const auto fixture=std::filesystem::temp_directory_path()/("phase8_synthetic_zero_support_"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));require(std::filesystem::create_directory(fixture),"synthetic fixture fresh output");
 const auto zeroKappa=analyzeKappa(toyRows,toyEvents,{{"m_gamma_gamma",Json::array({105,120,130,160})}},fixture);
 require(zeroKappa["summaries"][0]["final"]["ESS"].is_null(),"zero selected kappa ESS null");
 require(std::filesystem::file_size(fixture/"phase8_kappa_summary.csv")>0,"zero support CSV emitted safely");
 std::vector<Json> loadEvents;for(std::size_t i=0;i<4;++i)loadEvents.push_back({{"source_event_ordinal",i+1},{"source_event_sha256",std::string(64,'a')},{"source_weight_pb",.01}});
 const auto writeFixture=[&](const std::filesystem::path&path,bool duplicate,bool omit){std::ofstream csv(path);csv<<"source_event_index,source_event_sha256,source_alpha_s,source_scale_gev,kappa_lambda,full_mass_squared_ME,SM_denominator,ratio,source_contribution_pb,MODEL_BR_ONLY_weight_pb,return_code,precision,quadratic_residual,SM_repeat_relative_residual\n";for(std::size_t i=0;i<4;++i)for(std::size_t k=0;k<6;++k){if(omit&&i==3&&k==5)continue;csv<<i+1<<','<<std::string(64,'a')<<",0.13,200,"<<kappaBenchmarks[k]<<",1,1,1,0.01,0.00002,211,1e-12,0,0\n";}if(duplicate)csv<<"1,"<<std::string(64,'a')<<",0.13,200,-1,1,1,1,0.01,0.00002,211,1e-12,0,0\n";};
 writeFixture(fixture/"valid_synthetic_rows.csv",false,false);require(loadKappaRows(fixture/"valid_synthetic_rows.csv",loadEvents,.002,4).size()==4,"six per source synthetic Kappa identity");
 writeFixture(fixture/"duplicate_synthetic_rows.csv",true,false);require(rejects([&]{loadKappaRows(fixture/"duplicate_synthetic_rows.csv",loadEvents,.002,4);}),"duplicate Kappa pair rejected");
 writeFixture(fixture/"missing_synthetic_rows.csv",false,true);require(rejects([&]{loadKappaRows(fixture/"missing_synthetic_rows.csv",loadEvents,.002,4);}),"missing Kappa row rejected");
 auto wrongHash=loadEvents;wrongHash[1]["source_event_sha256"]=std::string(64,'b');require(rejects([&]{loadKappaRows(fixture/"valid_synthetic_rows.csv",wrongHash,.002,4);}),"wrong Kappa source hash rejected");
 require(rejects([&]{loadKappaRows(fixture/"valid_synthetic_rows.csv",loadEvents,.003,4);}),"wrong Kappa BR rejected");

 std::cout<<"PASS SYNTHETIC_METHOD_TEST statistics checks="<<count<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL SYNTHETIC_METHOD_TEST "<<e.what()<<'\n';return 1;}}

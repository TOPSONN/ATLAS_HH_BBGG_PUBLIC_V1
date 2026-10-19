#include "Phase8Statistics.hxx"
#include "Phase8Kappa.hxx"
#include "Phase8Likelihood.hxx"
#include "Sha256.hxx"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
namespace {
using phase8::Json;
void require(bool ok,const char*why){if(!ok)throw std::invalid_argument(why);}
Json readJson(const std::string&path){std::ifstream in(path);require(in.good(),"MISSING_JSON_INPUT");return Json::parse(in);}
void save(const std::filesystem::path&p,const Json&j){require(!std::filesystem::exists(p),"REFUSE_OUTPUT_OVERWRITE");std::ofstream out(p);require(out.good(),"OUTPUT_CREATE_FAILED");out<<j.dump(2)<<'\n';}
std::string need(const std::map<std::string,std::string>&args,const std::string&key){auto it=args.find(key);require(it!=args.end(),("MISSING_OPTION_"+key).c_str());return it->second;}
std::filesystem::path newOutput(const std::map<std::string,std::string>&args){const std::filesystem::path out=need(args,"--output");require(!out.empty()&&!std::filesystem::exists(out),"REFUSE_EXISTING_OUTPUT_DIRECTORY");require(std::filesystem::is_directory(out.parent_path()),"OUTPUT_PARENT_MISSING");require(std::filesystem::create_directory(out),"OUTPUT_DIRECTORY_CREATE_FAILED");return out;}
void statsCSVs(const std::filesystem::path&out,const Json&j){
 std::ofstream w(out/"phase8_weight_accounting.csv"),b(out/"phase8_btag_conditional_diagnostics.csv"),q(out/"phase8_bin_quality.csv");require(w.good()&&b.good()&&q.good(),"STATISTICS_CSV_OUTPUT_FAILED");w<<std::setprecision(17);b<<std::setprecision(17);q<<std::setprecision(17);
 w<<"dataset_id,stage,N_original,N_pass,sumw,sumw2,sum_absw,ESS,fixed_N_source_sampling_variance,model_BR_factor,BR_factor_applications,ILLUSTRATIVE_MODEL_YIELD_100fb\n";
 for(auto&s:j.at("stages")){w<<j.at("dataset_id").get<std::string>()<<','<<s.at("stage").get<std::string>()<<','<<s.at("N_original")<<','<<s.at("N_pass")<<','<<s.at("sumw")<<','<<s.at("sumw2")<<','<<s.at("sum_absw")<<',';if(!s.at("ESS").is_null())w<<s.at("ESS");w<<','<<s.at("fixed_N_source_sampling_variance")<<','<<j.at("model_BR_factor")<<','<<j.at("factor_applications")<<','<<s.at("ILLUSTRATIVE_MODEL_YIELD_100fb")<<'\n';}
 b<<"dataset_id,stage,N_original,eligible_before_tag_count,expected_tag0_count,expected_tag1_count,expected_count,conditional_count_variance,conditional_weighted_variance_pb2,analytic_expected_weight_pb,observed_weight_pb,observed_fixed_N_sampling_variance,variance_components_added\n";
 for(auto&s:j.at("conditional_tags"))b<<j.at("dataset_id").get<std::string>()<<','<<s.at("stage").get<std::string>()<<','<<s.at("N_original")<<','<<s.at("eligible_before_tag_count")<<','<<s.at("expected_tag0_count")<<','<<s.at("expected_tag1_count")<<','<<s.at("expected_count")<<','<<s.at("conditional_count_variance")<<','<<s.at("conditional_weighted_variance_pb2")<<','<<s.at("analytic_expectation").at("sumw")<<','<<s.at("observed_actual_tag_draw").at("sumw")<<','<<s.at("observed_actual_tag_draw").at("fixed_N_source_sampling_variance")<<",false\n";
 q<<"dataset_id,stage,observable,bin,flow,N_original,N_original_sources_contributing,sumw,sumw2,sum_absw,ESS,largest_fraction,missing_kinematics,quality_flag\n";
 for(auto&s:j.at("bin_quality")){q<<j.at("dataset_id").get<std::string>()<<','<<s.at("stage").get<std::string>()<<','<<s.at("observable").get<std::string>()<<','<<s.at("bin")<<','<<s.at("flow").get<std::string>()<<','<<s.at("N_original")<<','<<s.at("N_original_sources_contributing")<<','<<s.at("sumw")<<','<<s.at("sumw2")<<','<<s.at("sum_absw")<<',';if(!s.at("ESS").is_null())q<<s.at("ESS");q<<',';if(!s.at("largest_absolute_fraction").is_null())q<<s.at("largest_absolute_fraction");q<<','<<s.at("missing_kinematics")<<','<<s.at("quality_flag").get<std::string>()<<'\n';}
}
}
int main(int argc,char**argv){
 try{
  require(argc>=2,"MISSING_METHOD_SUBCOMMAND");const std::string mode=argv[1];require(mode=="methods-test"||mode=="analyze-statistics"||mode=="kappa","INVALID_ANALYSIS_MODE");
  std::map<std::string,std::string>args;const std::set<std::string>allowed{"--output","--events","--dataset","--factor","--factor-applications","--edges","--weights","--source-sha256","--model-br"};
  for(int i=2;i<argc;i+=2){require(i+1<argc,"MISSING_OPTION_VALUE");const std::string key=argv[i];require(allowed.count(key)&&!args.count(key),"UNKNOWN_OR_DUPLICATE_OPTION");args.emplace(key,argv[i+1]);}
  Json result;
  if(mode=="methods-test"){
   require(args.size()==1&&args.count("--output"),"METHODS_TEST_ACCEPTS_NO_PHYSICAL_INPUT");const auto out=newOutput(args);result=phase8::runSyntheticLikelihoodMethods();save(out/"phase8_likelihood_method_tests.json",result);save(out/"phase8_toy_closure.json",{{"label","SYNTHETIC_METHOD_ONLY"},{"status",result.at("status")},{"tests",result.at("tests")},{"physical_inference","NOT_EVALUATED"}});
  }else{
   auto events=phase8::readEventSummaries(need(args,"--events"),mode=="kappa"?"S01_C1000":need(args,"--dataset"));const auto edges=readJson(need(args,"--edges"));
   if(mode=="analyze-statistics"){
    require(args.size()==6,"UNEXPECTED_STATISTICS_OPTION");const auto dataset=need(args,"--dataset");require(events.front().at("dataset_id").get<std::string>()==dataset,"UNKNOWN_OR_WRONG_DATASET");
    std::size_t used=0;const auto ftext=need(args,"--factor");const auto factor=std::stod(ftext,&used);require(used==ftext.size(),"INVALID_MODEL_FACTOR");const auto atext=need(args,"--factor-applications");used=0;const auto applied=std::stoi(atext,&used);require(used==atext.size(),"INVALID_BR_APPLICATION_COUNT");
    result=phase8::analyzeEventStatistics(events,factor,applied,edges);const auto out=newOutput(args);save(out/"phase8_statistical_uncertainty.json",result);statsCSVs(out,result);
   }else{
    require(args.size()==6,"UNEXPECTED_KAPPA_OPTION");const auto source=need(args,"--source-sha256");require(source=="b13e5010f80b734495598492c97f5a7f73da72568c296134b2fb15b302a69eac","WRONG_HISTORICAL_C1000_SOURCE");require(events.front().at("dataset_id").get<std::string>()=="S01_C1000","KAPPA_REQUIRES_C1000_DATASET");
    std::size_t used=0;const auto btext=need(args,"--model-br");const auto br=std::stod(btext,&used);require(used==btext.size(),"INVALID_KAPPA_BR");std::ifstream frozen(need(args,"--weights"),std::ios::binary);require(frozen.good(),"MISSING_KAPPA_CSV");atlas_hh::Sha256 hash;std::array<char,65536>buffer{};while(frozen){frozen.read(buffer.data(),buffer.size());hash.update(buffer.data(),static_cast<std::size_t>(frozen.gcount()));}require(hash.finish()=="c76dd54b9236ee8110385fe746eb465125c70f1f30e0d580ac95acacc03a9e0f","WRONG_FROZEN_KAPPA_CSV_HASH");const auto rows=phase8::loadKappaRows(need(args,"--weights"),events,br);const auto out=newOutput(args);result=phase8::analyzeKappa(rows,events,edges,out);
   }
  }
  std::cout<<Json{{"status",result.value("status","PASS_EVENT_LEVEL_STATISTICS")},{"mode",mode},{"new_ME_calls",0},{"new_events",0},{"physical_inference","NOT_EVALUATED"}}.dump()<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<Json{{"status","BLOCKED_PHASE8_STATISTICAL_METHODS"},{"reason",e.what()},{"new_ME_calls",0},{"new_events",0}}.dump()<<'\n';return 2;}
}

#include "Phase8Provenance.hxx"
#include <TEfficiency.h>
#include <RVersion.h>
#include <iostream>
#include <cmath>
#include <algorithm>
namespace p8=atlas_hh::phase8;
int main(int argc,char**argv){try{
 p8::demand(argc==5&&std::string(argv[1])=="--input"&&std::string(argv[3])=="--output","usage: phase9_binomial_reference --input CASES --output FRESH_JSON");
 auto cases=p8::read_json(argv[2]);p8::Json rows=p8::Json::array();double largest=0;long comparisons=0;
 for(const auto&c:cases.at("cases")){
  const auto n=c.at("N").get<int>(),k=c.at("k").get<int>();const double level=c.value("confidence",0.95);
  p8::demand(n>0&&k>=0&&k<=n&&level>0&&level<1,"invalid binomial test case");
  const double lower=TEfficiency::ClopperPearson(n,k,level,false),upper=TEfficiency::ClopperPearson(n,k,level,true);
  const double dl=std::abs(lower-c.at("lower").get<double>()),du=std::abs(upper-c.at("upper").get<double>());
  largest=std::max({largest,dl,du});comparisons+=2;
  p8::demand(dl<2e-10&&du<2e-10,"ROOT exact-binomial disagreement");
  rows.push_back({{"N",n},{"k",k},{"confidence",level},{"ROOT_CP_lower",lower},{"ROOT_CP_upper",upper},{"absolute_difference_lower",dl},{"absolute_difference_upper",du}});
 }
 p8::demand(comparisons>=8,"insufficient independent binomial cases");
 p8::write_json(argv[4],{{"status","PASS_INDEPENDENT_ROOT_BINOMIAL_REFERENCE"},{"evidence_class","NUMERICAL_METHOD_CROSSCHECK_ACTUAL_ACCEPTANCE_COUNTS"},{"ROOT_version",ROOT_RELEASE},{"input_sha256",p8::file_sha256(argv[2])},{"comparisons",comparisons},{"largest_absolute_difference",largest},{"cases",rows},{"new_ME_calls",0},{"new_integrals",0},{"new_events",0}});
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
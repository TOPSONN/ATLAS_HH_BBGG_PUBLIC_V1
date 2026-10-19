#include "Phase8Likelihood.hxx"
#include <iostream>
int main(){try{const auto result=phase8::runSyntheticLikelihoodMethods();std::cout<<result.dump(2)<<'\n';return result.at("status")=="PASS_SYNTHETIC_METHOD_ONLY"?0:1;}catch(const std::exception&e){std::cerr<<"FAIL SYNTHETIC_METHOD_TEST "<<e.what()<<'\n';return 1;}}

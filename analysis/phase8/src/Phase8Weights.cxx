#include "Phase8Weights.hxx"
#include <cmath>
#include <stdexcept>
namespace phase8 {
double WeightContract::applyModelFactor(double x) const {
 if(!std::isfinite(x)||!std::isfinite(modelFactor)||modelFactor<=0||modelFactor>1)
  throw std::invalid_argument("INVALID_WEIGHT_OR_BR_FACTOR");
 if(alreadyApplied!=0) throw std::invalid_argument("DUPLICATE_BR_APPLICATION_REJECTED");
 if(scope!="MODEL_BR_ONLY"&&scope!="RAW_SOURCE") throw std::invalid_argument("UNKNOWN_WEIGHT_SCOPE");
 if(scope=="RAW_SOURCE"&&modelFactor!=1.) throw std::invalid_argument("RAW_SOURCE_WITH_BR_FACTOR");
 const double result=x*modelFactor;
 if(!std::isfinite(result)) throw std::invalid_argument("NONFINITE_MODEL_WEIGHT");
 return result;
}
double illustrativeYield(double x,double luminosity) {
 if(!std::isfinite(x)||!std::isfinite(luminosity)||luminosity<0)throw std::invalid_argument("INVALID_YIELD_INPUT");
 const auto y=x*1000.*luminosity;
 if(!std::isfinite(y))throw std::invalid_argument("NONFINITE_YIELD");
 return y;
}
}

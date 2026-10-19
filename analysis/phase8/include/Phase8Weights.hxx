#pragma once
#include <string>
namespace phase8 {
struct WeightContract {
 std::string scope;
 double modelFactor{1.};
 int alreadyApplied{0};
 double applyModelFactor(double sourceContributionPb) const;
};
double illustrativeYield(double selectedPb,double luminosityFb=100.);
}

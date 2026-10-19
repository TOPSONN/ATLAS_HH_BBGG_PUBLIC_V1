#pragma once
#include "Phase8Statistics.hxx"
#include <string>
#include <vector>
namespace phase8 {
struct TemplateRepresentation {
 std::string datasetId,process,region,observable,sourceIdentity;
 std::string signedWeightStatus,normalizationScope,overlapScope;
 std::string systematicsAvailability,validationState;
 std::vector<double> binEdges,expected,sumw2;
 bool syntheticOnly{false};
};
void validateTemplate(const TemplateRepresentation&,bool requirePhysical=false);
double poissonLogLikelihood(double observed,double expected);
Json runSyntheticLikelihoodMethods();
}

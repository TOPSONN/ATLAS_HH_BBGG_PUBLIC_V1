#pragma once
#include <array>
#include <cstddef>
#include <optional>
#include <span>
#include <vector>
#include <nlohmann/json.hpp>
namespace phase8 {
using Json=nlohmann::json;
struct WeightSummary {
 std::size_t originalN{},positive{},negative{},zero{};
 double sumw{},sumw2{},sumAbs{},mean{},sampleVariance{},fixedNVariance{};
 std::optional<double> ess,cancellationRatio,largestFraction;
};
WeightSummary summarizeWeights(std::span<const double> contributions,std::size_t originalN);
double fixedNCovariance(std::span<const double> first,std::span<const double> second);
double zeroSuccessUpper(std::size_t originalN,double confidence=.95);
Json weightSummaryJson(const WeightSummary&);
struct TagProbabilities {double zero{},one{},atLeastTwo{};};
TagProbabilities conditionalTags(std::span<const double> probabilities);
double nativeTagProbability(int flavour,double pt);
Json analyzeEventStatistics(const std::vector<Json>& events,double factor,int alreadyApplied,
                            const Json& histogramEdges);
std::vector<Json> readEventSummaries(const std::string& path,const std::string& datasetFilter="");
Json commonSourceCovariance(const std::vector<std::array<double,6>>& contributions);
}

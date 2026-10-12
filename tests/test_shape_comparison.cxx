#include "AtlasNormalization.h"
#include <TH1D.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>

namespace {
using namespace atlas::normalization;
std::size_t checks=0,fixtures=0,quadratic_checks=0;
void check(bool value,const std::string& message){++checks;if(!value)throw std::runtime_error(message);}
void close(long double value,long double expected,const std::string& message) {
  check(std::abs(value-expected)<=2e-14L*std::max({std::abs(value),std::abs(expected),1.L}),message);
}
void rejected(const std::function<void()>& action,const std::string& message) {
  bool caught=false;try{action();}catch(const std::invalid_argument&){caught=true;}check(caught,message);
}
ShapeContract contract(bool weighted=false) {
  ShapeContract result;result.scope=Scope::Synthetic;result.selection_id="SYNTHETIC_EXCLUSIVE_EVENT_BINS";
  result.variable_id="synthetic_x";result.units="synthetic_unit";
  result.histogram_semantics={Verification::Verified,"synthetic:test_shape_comparison","Exact analytical fixture weight definition"};
  result.independent_selected_bin_statistics={Verification::Verified,"synthetic:test_shape_comparison","One independent event per fill; disjoint bin populations"};
  result.nominal_generator_weight_semantics={Verification::Verified,"synthetic:test_shape_comparison","Signed fixed nominal fixture weights"};
  if(weighted)result.mode=ShapeMode::GeneratorWeightedShape;
  return result;
}
void fill(TH1D& histogram,ShapeContract& policy,int bin,long double weight) {
  const auto x=bin==0?histogram.GetBinLowEdge(1)-1:
    bin==histogram.GetNbinsX()+1?histogram.GetBinLowEdge(bin)+1:histogram.GetBinCenter(bin);
  const auto native_weight=static_cast<double>(weight);
  histogram.Fill(x,native_weight);policy.event_sums_by_bin[bin].add(native_weight);
}
std::vector<double> snapshot(const TH1D& histogram) {
  std::vector<double> result{histogram.GetEntries()};
  std::array<double,4> statistics{};histogram.GetStats(statistics.data());
  result.insert(result.end(),statistics.begin(),statistics.end());
  for(int bin=0;bin<=histogram.GetNbinsX()+1;++bin) {
    result.push_back(histogram.GetBinContent(bin));result.push_back(histogram.GetBinError(bin));
    result.push_back(histogram.GetBinLowEdge(bin));
  }
  return result;
}
void independent_checks(const ShapeResult& result,std::mt19937& random) {
  ++fixtures;const auto size=result.values.size();const auto sum=result.normalization_denominator;
  long double q=0;for(const auto value:result.source_sumw2)q+=value;
  long double area=0;for(std::size_t i=0;i<size;++i)area+=result.values[i]*(result.density?result.widths[i]:1.L);
  close(area,1,"Signed normalized area differs from one");
  for(std::size_t i=0;i<size;++i) {
    long double weighted_row_sum=0;
    for(std::size_t j=0;j<size;++j) {
      const auto x=result.source_sumw[i],y=result.source_sumw[j];
      const auto vi=result.source_sumw2[i],vj=result.source_sumw2[j];
      // Expanded independent analytical expression, not the implementation's
      // Jacobian loops, provides the covariance oracle.
      auto expected=(i==j?vi/(sum*sum):0)-(x*vj+y*vi)/(sum*sum*sum)+x*y*q/(sum*sum*sum*sum);
      if(result.density)expected/=result.widths[i]*result.widths[j];
      close(result.covariance[i][j],expected,"Independent analytical covariance mismatch");
      check(result.covariance[i][j]==result.covariance[j][i],"Covariance asymmetric");
      weighted_row_sum+=result.covariance[i][j]*(result.density?result.widths[j]:1.L);
    }
    close(weighted_row_sum,0,"Normalization covariance null direction missing");
    close(result.errors[i]*result.errors[i],result.covariance[i][i],"Errors inconsistent with covariance");
  }
  // Deterministic independent quadratic forms exercise PSD in many directions.
  // This complements the analytical J diag(q>=0) J^T identity; it is not an
  // empirical proof for every possible matrix or future source covariance.
  for(int direction=0;direction<64;++direction) {
    std::vector<long double> vector(size);for(auto& value:vector)value=static_cast<int>(random()%33)-16;
    long double quadratic=0,absolute_terms=0;
    for(std::size_t i=0;i<size;++i)for(std::size_t j=0;j<size;++j) {
      const auto term=vector[i]*result.covariance[i][j]*vector[j];quadratic+=term;absolute_terms+=std::abs(term);
    }
    check(quadratic>=-128*std::numeric_limits<long double>::epsilon()*std::max(absolute_terms,1.L),"Covariance not PSD at arithmetic precision");
    ++quadratic_checks;
  }
}
}
int main() {
  try {
    std::mt19937 random(20261012);const double edges[]{0,1,3,6};
    TH1D raw("raw_fixture","raw_fixture",3,edges);raw.SetDirectory(nullptr);raw.Sumw2();
    for(int i=0;i<2;++i)raw.Fill(.5);
    for(int i=0;i<6;++i)raw.Fill(2);
    auto raw_policy=contract();raw_policy.last_bin=2;const auto raw_before=snapshot(raw);
    const auto raw_shape=normalize_shape(raw,raw_policy);
    close(raw_shape.values[0],.25L,"Raw first fraction incorrect");close(raw_shape.values[1],.75L,"Raw second fraction incorrect");
    close(raw_shape.covariance[0][0],.0234375L,"Raw multinomial variance incorrect");
    close(raw_shape.covariance[0][1],-.0234375L,"Raw normalization anticorrelation absent");
    check(raw_shape.selected.entries==8&&raw_shape.selected.positive==8&&raw_shape.selected.sign_counts_known,"Raw entries/sign counts incorrect");
    close(raw_shape.effective_entries,8,"Raw Neff incorrect");independent_checks(raw_shape,random);
    raw_policy.density=true;const auto density=normalize_shape(raw,raw_policy);
    close(density.values[0],.25L,"First density incorrect");close(density.values[1],.375L,"Variable-width density incorrect");
    close(density.covariance[0][1],-.01171875L,"Density covariance width rescaling incorrect");independent_checks(density,random);
    check(snapshot(raw)==raw_before,"Raw histogram content/errors/entries/edges changed");

    TH1D signed_hist("signed_fixture","signed_fixture",3,edges);signed_hist.SetDirectory(nullptr);signed_hist.Sumw2();
    auto signed_policy=contract(true);signed_policy.event_sums_by_bin.resize(5);
    fill(signed_hist,signed_policy,1,3);fill(signed_hist,signed_policy,1,-1);
    fill(signed_hist,signed_policy,2,-1);fill(signed_hist,signed_policy,3,3);
    fill(signed_hist,signed_policy,0,2);fill(signed_hist,signed_policy,4,-.5L);
    const auto signed_before=snapshot(signed_hist);const auto signed_shape=normalize_shape(signed_hist,signed_policy);
    close(signed_shape.selected.sumw,4,"Selected signed SumW incorrect");close(signed_shape.selected.sumw2,20,"Selected SumW2 incorrect");
    close(signed_shape.selected.sumabs,8,"Within-bin absolute weights lost");close(signed_shape.effective_entries,.8L,"Signed shape Neff incorrect");
    close(signed_shape.values[1],-.25L,"Negative weighted bin clipped");
    close(signed_shape.covariance[0][0],.3125L,"Signed analytical variance incorrect");
    close(signed_shape.covariance[0][1],-.03125L,"Signed analytical covariance incorrect");independent_checks(signed_shape,random);
    signed_policy.density=true;independent_checks(normalize_shape(signed_hist,signed_policy),random);
    signed_policy.density=false;signed_policy.first_bin=2;const auto selected=normalize_shape(signed_hist,signed_policy);
    close(selected.normalization_denominator,2,"Selected-bin denominator incorrect");close(selected.selected.sumw2,10,"Selected-bin SumW2 incorrect");
    check(selected.bin_indices==std::vector<int>({2,3}),"Selected-bin range ignored");independent_checks(selected,random);
    signed_policy.flow_policy=FlowPolicy::Include;const auto flows=normalize_shape(signed_hist,signed_policy);
    close(flows.normalization_denominator,3.5L,"Explicit flow denominator incorrect");close(flows.selected.sumw2,14.25L,"Flow SumW2 incorrect");
    check(flows.bin_indices==std::vector<int>({0,2,3,4}),"Flow/bin mask incorrect");independent_checks(flows,random);
    signed_policy.density=true;rejected([&]{normalize_shape(signed_hist,signed_policy);},"Undefined flow density accepted");
    check(snapshot(signed_hist)==signed_before,"Signed histogram contents/errors/entries/flows/edges changed");
    auto missing=contract(true);rejected([&]{normalize_shape(signed_hist,missing);},"Weighted normalization without event ledger accepted");
    TH1D without_sumw2(signed_hist);without_sumw2.SetDirectory(nullptr);without_sumw2.Sumw2(false);
    missing=signed_policy;missing.density=false;
    rejected([&]{normalize_shape(without_sumw2,missing);},"Weighted normalization without explicit Sumw2 accepted");
    missing=signed_policy;missing.density=false;missing.nominal_generator_weight_semantics.state=Verification::Unknown;
    rejected([&]{normalize_shape(signed_hist,missing);},"Unknown nominal generator weights accepted");
    missing=signed_policy;missing.density=false;missing.independent_selected_bin_statistics.state=Verification::Unknown;
    rejected([&]{normalize_shape(signed_hist,missing);},"Unknown selected-bin covariance model accepted");
    missing=signed_policy;missing.density=false;missing.event_sums_by_bin[2]=SignedSums::from_aggregates(-1,2,2,2);
    rejected([&]{normalize_shape(signed_hist,missing);},"Disagreeing Sumw2 ledger accepted");
    missing=contract();missing.scope=Scope::Physical;rejected([&]{normalize_shape(raw,missing);},"Physical shape enabled by default");
    missing=contract();rejected([&]{normalize_shape(signed_hist,missing);},"Weighted/negative bins accepted as raw counts");
    auto incompatible=raw_shape;incompatible.selection_id="OTHER_SELECTION";
    rejected([&]{require_compatible_shapes(raw_shape,incompatible);},"Different selections compared");
    incompatible=raw_shape;incompatible.lower_edges[0]+=1;
    rejected([&]{require_compatible_shapes(raw_shape,incompatible);},"Shifted equal-width bins compared");
    incompatible=raw_shape;incompatible.variable_id="other_variable";
    rejected([&]{require_compatible_shapes(raw_shape,incompatible);},"Different variables compared");
    incompatible=raw_shape;incompatible.scope=Scope::Physical;
    rejected([&]{require_compatible_shapes(raw_shape,incompatible);},"Synthetic result relabelled as physical comparison");
    require_compatible_shapes(raw_shape,raw_shape);++checks;

    TH1D cancel("cancel_fixture","cancel_fixture",2,0,2);cancel.SetDirectory(nullptr);cancel.Sumw2();
    auto cancel_policy=contract(true);cancel_policy.event_sums_by_bin.resize(4);
    fill(cancel,cancel_policy,1,1);fill(cancel,cancel_policy,2,-1);
    rejected([&]{normalize_shape(cancel,cancel_policy);},"Zero signed shape denominator accepted");
    TH1D near("near_fixture","near_fixture",2,0,2);near.SetDirectory(nullptr);near.Sumw2();
    auto near_policy=contract(true);near_policy.event_sums_by_bin.resize(4);
    fill(near,near_policy,1,1);fill(near,near_policy,2,-1+1e-14L);
    rejected([&]{normalize_shape(near,near_policy);},"Near-zero signed shape denominator accepted");

    TH1D tiny("tiny_fixture","tiny_fixture",2,0,2);tiny.SetDirectory(nullptr);tiny.Sumw2();
    auto tiny_policy=contract(true);tiny_policy.event_sums_by_bin.resize(4);
    fill(tiny,tiny_policy,1,1e-100L);fill(tiny,tiny_policy,2,2e-100L);
    const auto tiny_shape=normalize_shape(tiny,tiny_policy);
    close(tiny_shape.values[0],1.L/3,"Valid tiny-weight shape rejected or changed");
    independent_checks(tiny_shape,random);
    auto contradictory=tiny_policy;contradictory.event_sums_by_bin[1]=SignedSums::from_aggregates(1e-98L,1e-196L,1e-98L,1);
    rejected([&]{normalize_shape(tiny,contradictory);},"Contradictory tiny signed ledger accepted by absolute floor");
    contradictory=tiny_policy;contradictory.event_sums_by_bin[1]=SignedSums::from_aggregates(1e-100L,2.5e-200L,2e-100L,2);
    rejected([&]{normalize_shape(tiny,contradictory);},"Contradictory tiny Sumw2 ledger accepted by absolute floor");

    for(int trial=0;trial<512;++trial) {
      const int count=3+trial%7;std::vector<double> variable_edges{0};
      for(int bin=0;bin<count;++bin)variable_edges.push_back(variable_edges.back()+1+(bin+trial)%3);
      TH1D histogram(("stress_"+std::to_string(trial)).c_str(),"synthetic signed fixture",count,variable_edges.data());
      histogram.SetDirectory(nullptr);histogram.Sumw2();auto policy=contract(true);policy.event_sums_by_bin.resize(count+2);
      const long double sign=trial%2?-1.L:1.L;
      for(int bin=1;bin<=count;++bin) {
        const long double base=1+(bin+trial)%5;
        fill(histogram,policy,bin,sign*base);fill(histogram,policy,bin,-sign*base/4);
      }
      policy.density=trial%3==0;const auto before=snapshot(histogram);
      const auto result=normalize_shape(histogram,policy);independent_checks(result,random);
      close(result.selected.sumabs,std::abs(result.selected.sumw)*5/3,"Signed ledger cancellation statistics inconsistent");
      check(snapshot(histogram)==before,"Stress input histogram mutated");
    }
    std::cout<<"PASS shape comparison: "<<checks<<" assertions; "<<fixtures<<" analytical fixtures; "<<quadratic_checks
             <<" deterministic PSD directions; no physical input/figures\n";return 0;
  } catch(const std::exception& error){std::cerr<<"FAIL shape comparison: "<<error.what()<<'\n';return 1;}
}

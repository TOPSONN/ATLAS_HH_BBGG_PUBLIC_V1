#include "AtlasControlRegions.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>

namespace r=atlas::regions;
namespace n=atlas::normalization;
namespace {
std::size_t assertions=0,rejection_cases=0,partition_cases=0;
void check(bool result,const char* message) {
  ++assertions; if(!result) throw std::runtime_error(message);
}
void close(long double actual,long double expected) {
  check(std::isfinite(actual) && std::abs(actual-expected)<=1e-13L*std::max(1.L,std::abs(expected)),
        "Independent synthetic analytical result disagrees");
}
template<class F> void rejects(F action) {
  bool threw=false; try { action(); } catch(const std::invalid_argument&) { threw=true; }
  ++rejection_cases; check(threw,"Invalid control-region/transfer contract accepted");
}
atlas::selection::Event event(double mass=115,double delta_eta=.5) {
  atlas::selection::Event e; e.source_valid=true; e.photons=2; e.jets=2;
  e.photon_pt={50,30}; e.photon_eta={delta_eta/2,-delta_eta/2};
  e.jet_pt={45,35}; e.jet_eta={.2,-.2}; e.mgg=mass; e.mjj=90; return e;
}
r::Yield counts(std::string label,std::string space,std::uint64_t first,std::size_t count) {
  r::Yield y; y.population.label=std::move(label);
  for(std::size_t i=0;i<count;++i) { y.population.events.push_back({space,1,first+i}); y.sums.add(1); }
  return y;
}
r::Yield weighted(std::string label,std::string space,std::uint64_t first,const std::vector<long double>& weights) {
  r::Yield y; y.population.label=std::move(label);
  for(std::size_t i=0;i<weights.size();++i) { y.population.events.push_back({space,1,first+i}); y.sums.add(weights[i]); }
  return y;
}
n::SampleCombination sample_contract(const std::vector<std::string>& ids) {
  n::SampleCombination c; c.scope=n::Scope::Synthetic; c.sample_ids=ids;
  for(std::size_t i=0;i<ids.size();++i) for(std::size_t j=i+1;j<ids.size();++j)
    c.pairs.push_back({ids[i],ids[j],n::OverlapDisposition::Disjoint,
                      {n::Verification::Verified,"synthetic://distinct-fixture-generators","Disjoint deterministic fixture populations only"}});
  return c;
}
r::TransferContract transfer() {
  r::TransferContract c; c.mc_sr=counts("calibration-SR","fixture_mc",1,40);
  c.mc_cr=counts("calibration-CR","fixture_mc",1001,100);
  c.covariance=r::independent_counting_covariance({c.mc_sr,c.mc_cr}); c.samples=sample_contract({"fixture_mc"}); return c;
}
r::ResidualContract residual() {
  r::ResidualContract c; c.data_cr=counts("data-CR","fixture_data",1,200);
  c.other_backgrounds_cr={counts("other-A-CR","fixture_other_a",1,30),counts("other-B-CR","fixture_other_b",1,20)};
  c.covariance=r::independent_counting_covariance({c.data_cr,c.other_backgrounds_cr[0],c.other_backgrounds_cr[1]});
  c.samples=sample_contract({"fixture_mc","fixture_data","fixture_other_a","fixture_other_b"}); return c;
}
}
int main(int argc,char** argv) {
  try {
    r::Config c; if(argc==2) c.selection=atlas::selection::read_config(argv[1]);
    else if(argc!=1) throw std::invalid_argument("Only optional Phase3 configuration path accepted");
    check(c.selection.version=="study-preselection-v1" && c.selection.mass_low==105 && c.selection.mass_high==160,
          "Historical study selection changed");
    check(c.selection.leading_photon_pt==35 && c.selection.subleading_photon_pt==25 && c.selection.jet_pt==25 &&
          c.selection.photon_eta_max==2.37 && c.selection.jet_eta_max==2.5 && c.selection.crack_low==1.37 && c.selection.crack_high==1.52,
          "Historical photon/jet predicates changed");
    for(double split:{.75,1.,1.25}) for(double lo:{119.,120.,121.}) for(double hi:{129.,130.,131.}) {
      auto varied=c; varied.photon_abs_delta_eta_split=split; varied.sr_mass_low=lo; varied.sr_mass_high=hi;
      for(double mass:{104.999,105.,119.,120.,121.,125.,129.,130.,131.,160.,160.001})
        for(double deta:{0.,.5,.75,1.,1.25,1.8}) {
          const auto actual=r::classify(event(mass,deta),varied);
          // Independent partition oracle; no production classifier or selection helper.
          const auto expected=mass<105 || mass>160 ? r::Region::OutsideStudyDomain :
            mass>=lo && mass<hi ? (deta<split?r::Region::ProspectiveSignal:r::Region::ReservedWindowPartition) :
            (deta<split?r::Region::Control:r::Region::Validation);
          ++partition_cases; check(actual==expected,"Partition/boundary sensitivity oracle failed");
        }
    }
    for(double mass:{105.,120.,130.,160.}) {
      const auto low=std::nextafter(mass,-std::numeric_limits<double>::infinity());
      const auto high=std::nextafter(mass,std::numeric_limits<double>::infinity());
      const auto exact=r::classify(event(mass),c);
      check(exact==(mass==120?r::Region::ProspectiveSignal:r::Region::Control),"Mass boundary ownership wrong");
      if(mass==105) check(r::classify(event(low),c)==r::Region::OutsideStudyDomain && r::classify(event(high),c)==r::Region::Control,"Lower outer edge wrong");
      if(mass==120) check(r::classify(event(low),c)==r::Region::Control && r::classify(event(high),c)==r::Region::ProspectiveSignal,"Lower window edge wrong");
      if(mass==130) check(r::classify(event(low),c)==r::Region::ProspectiveSignal && r::classify(event(high),c)==r::Region::Control,"Upper window edge wrong");
      if(mass==160) check(r::classify(event(low),c)==r::Region::Control && r::classify(event(high),c)==r::Region::OutsideStudyDomain,"Upper outer edge wrong");
    }
    check(r::classify(event(115,1))==r::Region::Validation,"Exact split belongs to VR partition");
    check(r::classify(event(125,1))==r::Region::ReservedWindowPartition,"Central B partition was silently reused");
    check(r::classify(event(115,std::nextafter(1.,0.)))==r::Region::Control,"Just-below split excluded");
    check(r::classify(event(115,std::nextafter(1.,2.)))==r::Region::Validation,"Just-above split excluded");
    auto e=event(100); check(atlas::selection::evaluate(e,c.selection)[5] && !atlas::selection::evaluate(e,c.selection)[9] &&
                          r::classify(e,c)==r::Region::OutsideStudyDomain,"Outside C6 event lost through C9 filtering");
    e=event(); e.source_valid=false; check(r::classify(e,c)==r::Region::InvalidInput,"Invalid reconstruction accepted");
    e=event(); e.mgg=-1; check(r::classify(e,c)==r::Region::InvalidInput,"Negative native mass accepted");
    e=event(); e.mgg=std::numeric_limits<double>::quiet_NaN(); check(r::classify(e,c)==r::Region::InvalidInput,"NaN mass accepted");
    e=event(); e.photon_pt[0]=35; check(r::classify(e,c)==r::Region::FailsPreMassSelection,"Photon strict pT changed");
    e=event(); e.photon_pt[1]=25; check(r::classify(e,c)==r::Region::FailsPreMassSelection,"Subleading strict pT changed");
    e=event(); e.photon_eta={1.4,0}; check(r::classify(e,c)==r::Region::FailsPreMassSelection,"Crack predicate changed");
    e=event(); e.photon_eta={2.37,0}; check(r::classify(e,c)==r::Region::FailsPreMassSelection,"Eta strict edge changed");
    e=event(); e.jets=1; check(r::classify(e,c)==r::Region::FailsJetSelection,"Jet multiplicity predicate changed");
    e=event(); e.jet_pt[1]=25; check(r::classify(e,c)==r::Region::FailsJetSelection,"Jet strict pT changed");
    e=event(); e.jet_eta[0]=2.5; check(r::classify(e,c)==r::Region::FailsJetSelection,"Jet strict eta changed");
    e=event(); e.tight_id={0,0}; e.tight_iso={0,0}; check(r::classify(e,c)==r::Region::Control,"Optional ID/isolation silently added as baseline cuts");
    for(auto value:{105.,130.,160.,std::numeric_limits<double>::quiet_NaN()}) rejects([&]{auto bad=c;bad.sr_mass_low=value;r::validate_config(bad);});
    rejects([&]{auto bad=c;bad.photon_abs_delta_eta_split=0;r::validate_config(bad);});
    rejects([&]{auto bad=c;bad.selection.leading_photon_pt=20;r::validate_config(bad);});
    rejects([&]{auto bad=c;bad.selection.crack_high=bad.selection.photon_eta_max;r::validate_config(bad);});

    auto t_input=transfer(); const auto t=r::transfer_factor(t_input);
    close(t.factor,.4L); close(t.variance,.0056L);
    check(t.interpretation.find("SYNTHETIC_METHOD_TEST_ONLY")!=std::string::npos,"Synthetic scope absent");
    const auto p=r::predict_background(t,residual());
    close(p.residual_cr,150); close(p.residual_variance,250); close(p.prediction_sr,60); close(p.variance,166);
    auto single=residual(); single.other_backgrounds_cr.clear(); single.samples=sample_contract({"fixture_mc","fixture_data"});
    single.covariance=r::independent_counting_covariance({single.data_cr});
    const auto sp=r::predict_background(t,single); close(sp.prediction_sr,80); close(sp.variance,256);
    auto correlated=transfer(); correlated.covariance.values={{40,10},{10,100}};
    correlated.covariance.model="Synthetic correlated counting yields";
    const auto ct=r::transfer_factor(correlated); close(ct.factor,.4L); close(ct.variance,.0048L);
    auto nuisance=residual(); nuisance.covariance.values={{204,2,4},{2,31,2},{4,2,24}};
    nuisance.covariance.includes_nuisances=true; nuisance.covariance.model="Synthetic shared nuisance outer product plus counting diagonal";
    const auto np=r::predict_background(t,nuisance,.05L);
    // extra covariance outer product v v^T, v=(2,1,2); a*v=-1.
    close(np.residual_variance,251); close(np.prediction_sr,60); close(np.variance,172.16L);
    check(np.includes_nuisances,"Explicit nuisance scope lost");
    auto nuisance_t=transfer(); nuisance_t.covariance.values={{44,10},{10,125}};
    nuisance_t.covariance.includes_nuisances=true; nuisance_t.covariance.model="Synthetic SR/CR common nuisance v=(2,5)";
    const auto nt=r::transfer_factor(nuisance_t); close(nt.variance,.0056L);
    check(r::predict_background(nt,single).includes_nuisances,"Transfer-side nuisance metadata lost");

    // Independent held-out fixture: CR400, SR160, VR100. Calibrating SR/CR
    // yields0.4; unrelated validation CR250 predicts100 observed VR events.
    r::TransferContract closure; closure.mc_sr=counts("closure-MC-SR","closure_mc",1,160);
    closure.mc_cr=counts("closure-MC-CR","closure_mc",1001,400); closure.samples=sample_contract({"closure_mc"});
    closure.covariance=r::independent_counting_covariance({closure.mc_sr,closure.mc_cr});
    const auto closure_t=r::transfer_factor(closure);
    const auto held=counts("held-out-VR","closure_validation",1,100); r::require_held_out_validation(closure_t,held.population);
    r::ResidualContract validation; validation.data_cr=counts("validation-CR","closure_validation",1001,250);
    validation.samples=sample_contract({"closure_mc","closure_validation"}); validation.covariance=r::independent_counting_covariance({validation.data_cr});
    const auto vp=r::predict_background(closure_t,validation); close(vp.prediction_sr,held.sums.sumw); close(vp.variance,127.5L);
    r::require_held_out_validation(vp,held.population);
    // This verifies engineered toy closure only; it does not assert an actual
    // VR/CR transfer equality or any physical background/signal purity.
    r::require_disjoint_populations({validation.data_cr.population,held.population});
    rejects([&]{r::require_held_out_validation(t,t_input.mc_sr.population);});
    rejects([&]{r::require_held_out_validation(t,{});});
    rejects([&]{r::require_held_out_validation(p,residual().data_cr.population);});
    rejects([&]{r::require_held_out_validation(p,residual().other_backgrounds_cr[0].population);});
    rejects([&]{r::require_held_out_validation(r::Prediction{},held.population);});
    rejects([&]{auto pop=t_input.mc_sr.population;pop.label="renamed-cut";r::require_disjoint_populations({t_input.mc_sr.population,pop});});
    rejects([&]{auto pop=held.population;pop.events.push_back(pop.events.front());r::require_disjoint_populations({pop});});
    rejects([&]{auto pop=held.population;pop.events.front().namespace_id.clear();r::require_disjoint_populations({pop});});
    rejects([&]{r::require_disjoint_populations({held.population,held.population});});

    auto signed_t=transfer(); signed_t.mc_sr=weighted("signed-SR","fixture_mc",1,{1,-3,2});
    signed_t.mc_cr=weighted("signed-CR","fixture_mc",1001,{4,-1,2});
    signed_t.covariance=r::independent_counting_covariance({signed_t.mc_sr,signed_t.mc_cr});
    const auto zero_num=r::transfer_factor(signed_t); close(zero_num.factor,0); close(zero_num.variance,14.L/25);
    signed_t.mc_sr=weighted("signed-SR","fixture_mc",1,{-2,1});
    signed_t.covariance=r::independent_counting_covariance({signed_t.mc_sr,signed_t.mc_cr});
    const auto negative=r::transfer_factor(signed_t); close(negative.factor,-.2L); close(negative.variance,(5+.04L*21)/25);
    check(r::predict_background(negative,single).prediction_sr<0,"Signed toy prediction clipped");
    signed_t.mc_cr=weighted("signed-CR","fixture_mc",1001,{-4,1,-2});
    signed_t.covariance=r::independent_counting_covariance({signed_t.mc_sr,signed_t.mc_cr});
    close(r::transfer_factor(signed_t).factor,.2L);
    for(const auto& weights:std::vector<std::vector<long double>>{{1,-1},{1,-1+1e-14L},{0,0}})
      rejects([&]{auto bad=signed_t;bad.mc_cr=weighted("signed-CR","fixture_mc",1001,weights);bad.covariance=r::independent_counting_covariance({bad.mc_sr,bad.mc_cr});r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.conditioning.minimum_relative_signed_sum=0;r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.scope=n::Scope::Physical;r::transfer_factor(bad);});
    rejects([&]{auto bad=residual();bad.scope=n::Scope::Physical;r::predict_background(t,bad);});
    rejects([&]{auto fake=r::TransferResult{};r::predict_background(fake,single);});
    rejects([&]{auto changed=t;changed.factor=1;r::predict_background(changed,single);});
    rejects([&]{auto changed=t;changed.includes_nuisances=true;r::predict_background(changed,single);});
    rejects([&]{auto changed=t;changed.covariance_model="Changed provenance";r::predict_background(changed,single);});
    rejects([&]{auto changed=t;changed.calibration_populations.clear();r::require_held_out_validation(changed,held.population);});
    rejects([&]{auto bad=transfer();bad.mc_sr.population.events.pop_back();r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.mc_sr.population.events.front()=bad.mc_cr.population.events.front();r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.samples.sample_ids.push_back("fixture_mc");r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.samples.sample_ids={"wrong_mc"};r::transfer_factor(bad);});
    rejects([&]{auto bad=residual();bad.samples.pairs.clear();r::predict_background(t,bad);});
    rejects([&]{auto bad=residual();bad.samples=sample_contract({"fixture_data","fixture_other_a","fixture_other_b"});r::predict_background(t,bad);});
    rejects([&]{auto bad=residual();bad.samples.pairs.erase(std::find_if(bad.samples.pairs.begin(),bad.samples.pairs.end(),[](const auto& pair){return pair.first=="fixture_mc" && pair.second=="fixture_other_a";}));r::predict_background(t,bad);});
    for(auto overlap:{n::OverlapDisposition::Overlap,n::OverlapDisposition::Unknown})
      rejects([&]{auto bad=residual();for(auto& pair:bad.samples.pairs) if(pair.first=="fixture_mc" && pair.second=="fixture_other_a") pair.disposition=overlap;r::predict_background(t,bad);});
    for(auto overlap:{n::OverlapDisposition::Overlap,n::OverlapDisposition::Unknown})
      rejects([&]{auto bad=residual();bad.samples.pairs[0].disposition=overlap;r::predict_background(t,bad);});
    rejects([&]{auto bad=residual();bad.samples.pairs[0].evidence.state=n::Verification::Unknown;r::predict_background(t,bad);});
    rejects([&]{auto bad=residual();bad.data_cr.population.events[0]=t_input.mc_sr.population.events[0];bad.samples=sample_contract({"fixture_mc","fixture_data","fixture_other_a","fixture_other_b"});r::predict_background(t,bad);});
    rejects([&]{auto bad=transfer();bad.covariance={};r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.covariance.values={{40,0},{0,99}};r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.covariance.values={{40,1},{0,100}};r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.covariance.values={{40,100},{100,100}};r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.covariance.values[0][0]=std::numeric_limits<long double>::infinity();r::transfer_factor(bad);});
    rejects([&]{auto bad=transfer();bad.covariance.values={{-1,0},{0,100}};r::transfer_factor(bad);});
    rejects([&]{auto bad=nuisance;bad.covariance.values[0][0]=199;r::predict_background(t,bad);});
    rejects([&]{r::predict_background(t,single,2);});
    rejects([&]{r::predict_background(t,single,std::numeric_limits<long double>::quiet_NaN());});
    auto singular=transfer(); singular.mc_sr=counts("calibration-SR","fixture_mc",1,100);
    singular.covariance.values={{100,100},{100,100}}; singular.covariance.model="Synthetic rank-one counting covariance";
    close(r::transfer_factor(singular).variance,0);
    auto empty_sr=transfer();empty_sr.mc_sr=counts("calibration-SR","fixture_mc",1,0);
    empty_sr.covariance=r::independent_counting_covariance({empty_sr.mc_sr,empty_sr.mc_cr});
    close(r::transfer_factor(empty_sr).factor,0); close(r::transfer_factor(empty_sr).variance,0);
    rejects([&]{auto bad=empty_sr;bad.covariance.values={{0,1},{1,100}};r::transfer_factor(bad);});
    rejects([&]{auto bad=empty_sr;bad.mc_sr.sums=n::SignedSums::from_aggregates(1,1,1);bad.covariance=r::independent_counting_covariance({bad.mc_sr,bad.mc_cr});r::transfer_factor(bad);});
    std::cout<<"PASS control-region contract: "<<assertions<<" assertions, "<<partition_cases
             <<" independent partition fixtures, "<<rejection_cases<<" rejection cases; SYNTHETIC ONLY\n";
    return 0;
  } catch(const std::exception& e) { std::cerr<<"FAIL control-region contract: "<<e.what()<<'\n'; return 1; }
}

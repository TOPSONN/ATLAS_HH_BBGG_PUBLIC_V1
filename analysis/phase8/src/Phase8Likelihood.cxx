#include "Phase8Likelihood.hxx"
#include <RooAbsData.h>
#include <RooAbsReal.h>
#include <RooArgList.h>
#include <RooArgSet.h>
#include <RooConstVar.h>
#include <RooDataSet.h>
#include <RooFitResult.h>
#include <RooFormulaVar.h>
#include <RooGaussian.h>
#include <RooLognormal.h>
#include <RooMinimizer.h>
#include <RooMsgService.h>
#include <RooPoisson.h>
#include <RooProdPdf.h>
#include <RooRandom.h>
#include <RooRealVar.h>
#include <RooStats/AsymptoticCalculator.h>
#include <RooStats/LikelihoodInterval.h>
#include <RooStats/ModelConfig.h>
#include <RooStats/ProfileLikelihoodCalculator.h>
#include <RooWorkspace.h>
#include <TROOT.h>
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
namespace phase8 {
namespace {
void require(bool value,const char* message){if(!value)throw std::invalid_argument(message);}
std::string str(double value){std::ostringstream s;s<<std::setprecision(17)<<value;return s.str();}
}
void validateTemplate(const TemplateRepresentation&t,bool physical){
 require(!t.datasetId.empty()&&!t.process.empty()&&!t.region.empty()&&!t.observable.empty()&&!t.sourceIdentity.empty(),"MISSING_TEMPLATE_PROVENANCE");
 require(!t.signedWeightStatus.empty()&&!t.normalizationScope.empty()&&!t.overlapScope.empty()&&!t.systematicsAvailability.empty()&&!t.validationState.empty(),"MISSING_TEMPLATE_VALIDATION_SCOPE");
 require(t.binEdges.size()==t.expected.size()+1&&t.expected.size()==t.sumw2.size()&&!t.expected.empty(),"INVALID_TEMPLATE_DIMENSIONS");
 for(std::size_t j=0;j<t.binEdges.size();++j)require(std::isfinite(t.binEdges[j])&&(j==0||t.binEdges[j]>t.binEdges[j-1]),"INVALID_TEMPLATE_BIN_EDGES");
 for(std::size_t j=0;j<t.expected.size();++j){require(std::isfinite(t.expected[j])&&t.expected[j]>=0,"NEGATIVE_OR_NONFINITE_POISSON_EXPECTATION");require(std::isfinite(t.sumw2[j])&&t.sumw2[j]>=0,"INVALID_TEMPLATE_SUMW2");}
 require(t.signedWeightStatus=="POSITIVE_ONLY"||t.signedWeightStatus=="UNWEIGHTED_COUNTS","SIGNED_WEIGHT_POISSON_MODEL_NOT_ESTABLISHED");
 if(physical){require(!t.syntheticOnly,"SYNTHETIC_INPUT_IS_NOT_PHYSICAL");require(t.normalizationScope=="VALIDATED_PHYSICAL_YIELD"&&t.overlapScope=="OVERLAP_VALIDATED_EXCLUSIVE"&&t.systematicsAvailability=="VALIDATED"&&t.validationState=="VALIDATED_PHYSICAL","PHYSICAL_TEMPLATE_GATE_BLOCKED");}
 else require(t.syntheticOnly&&t.validationState=="SYNTHETIC_METHOD_ONLY","METHOD_TEST_REQUIRES_EXPLICIT_SYNTHETIC_INPUT");
}
double poissonLogLikelihood(double n,double lambda){
 require(std::isfinite(n)&&n>=0&&std::isfinite(lambda)&&lambda>=0,"INVALID_POISSON_INPUT");
 if(lambda==0)return n==0?0.:-std::numeric_limits<double>::infinity();
 return n*std::log(lambda)-lambda-std::lgamma(n+1.);
}
Json runSyntheticLikelihoodMethods(){
 gROOT->SetBatch(true);RooMsgService::instance().setGlobalKillBelow(RooFit::ERROR);
 constexpr unsigned toySeed=820019;RooRandom::randomGenerator()->SetSeed(toySeed);
 Json checks=Json::array();auto check=[&](const std::string&name,bool pass,const Json&detail=Json::object()){checks.push_back({{"name",name},{"pass",pass},{"evidence_class","SYNTHETIC_METHOD_TEST"},{"details",detail}});require(pass,("SYNTHETIC_METHOD_FAILURE_"+name+" "+detail.dump()).c_str());};
 // A one-bin model has a known analytic MLE and likelihood ratio.
 RooRealVar n("count","synthetic count",30.,0.,200.);
 RooRealVar mu("mu_count","synthetic signal strength",.6,0.,5.);
 RooConstVar signal("signal_count","synthetic signal",10.);
 RooConstVar background("background_count","synthetic background",20.);
 RooFormulaVar mean("mean_count","@0*@1+@2",RooArgList(mu,signal,background));
 RooPoisson poisson("poisson_count","synthetic Poisson",n,mean,true);
 RooArgSet countObs(n);RooDataSet countData("count_data","one synthetic Asimov entry",countObs);countData.add(countObs);
 auto countNll=poisson.createNLL(countData,RooFit::Offset(false));
 RooMinimizer countMin(*countNll);countMin.setPrintLevel(-1);countMin.setStrategy(1);const int countStatus=countMin.migrad();countMin.hesse();auto countFit=std::unique_ptr<RooFitResult>(countMin.save());
 check("count_parameter_recovery",countStatus==0&&std::abs(mu.getVal()-1.)<2e-4,{{"mu_hat",mu.getVal()},{"fit_status",countStatus}});
 check("count_covariance",countFit&&countFit->covQual()>=2&&std::abs(countFit->covarianceMatrix()(0,0)-.3)<.005,{{"mu_error",mu.getError()},{"mu_error_squared",mu.getError()*mu.getError()},{"covariance_matrix_variance",countFit?countFit->covarianceMatrix()(0,0):-1.},{"analytic_variance",.3},{"covariance_quality",countFit?countFit->covQual():-1},{"compared_quantity","external Hessian covariance matrix; bounded RooRealVar symmetric error is a separate Minuit transformed-error diagnostic"}});
 mu.setVal(1.);const auto nllAt1=countNll->getVal();mu.setVal(2.);const auto rooLR=2*(countNll->getVal()-nllAt1);const auto analyticLR=2*(poissonLogLikelihood(30,30)-poissonLogLikelihood(30,40));
 check("count_likelihood_ratio",std::abs(rooLR-analyticLR)<1e-7,{{"RooFit_minus2logLR",rooLR},{"analytic_minus2logLR",analyticLR}});
 mu.setVal(1.);n.setVal(30.);check("expected_log_likelihood",std::abs(std::log(poisson.getVal())-poissonLogLikelihood(30,30))<1e-10);
 check("zero_count_zero_expectation",poissonLogLikelihood(0,0)==0.);
 check("positive_count_zero_expectation",std::isinf(poissonLogLikelihood(1,0))&&poissonLogLikelihood(1,0)<0);
 check("small_positive_expectation",std::isfinite(poissonLogLikelihood(0,1e-300))&&std::abs(poissonLogLikelihood(0,1e-300)+1e-300)<1e-310);
 // RooStats independently builds an Asimov count at the model expectation.
 std::unique_ptr<RooAbsData> asimov(RooStats::AsymptoticCalculator::GenerateAsimovData(poisson,countObs));
 check("RooStats_Asimov",asimov&&asimov->numEntries()==1&&std::abs(asimov->get(0)->getRealValue("count")-30.)<1e-8,{{"entries",asimov?asimov->numEntries():0}});
 RooWorkspace workspace("synthetic_only_workspace");require(!workspace.import(poisson),"SYNTHETIC_WORKSPACE_IMPORT_FAILED");
 RooStats::ModelConfig countModel("synthetic_count_model",&workspace);countModel.SetPdf(*workspace.pdf("poisson_count"));countModel.SetObservables(RooArgSet(*workspace.var("count")));countModel.SetParametersOfInterest(RooArgSet(*workspace.var("mu_count")));
 RooStats::ProfileLikelihoodCalculator calculator(countData,countModel);calculator.SetConfidenceLevel(.682689492137);std::unique_ptr<RooStats::LikelihoodInterval> interval(calculator.GetInterval());
 workspace.var("mu_count")->setVal(1.);check("RooStats_profile_likelihood_interval",interval&&interval->IsInInterval(RooArgSet(*workspace.var("mu_count"))));
 // The boundary MLE is mu=0 for observed count below the known background.
 n.setVal(0.);RooDataSet zeroData("zero_data","synthetic zero",countObs);zeroData.add(countObs);mu.setVal(.5);
 auto zeroNll=poisson.createNLL(zeroData,RooFit::Offset(false));RooMinimizer zeroMin(*zeroNll);zeroMin.setPrintLevel(-1);const auto zeroStatus=zeroMin.migrad();check("signal_strength_boundary",zeroStatus==0&&mu.getVal()<1e-5,{{"mu_hat_zero_count",mu.getVal()}});
 // Artificial Gaussian peak integrates over bins; no point-sampled template.
 const std::vector<double> edges{100,110,118,123,127,132,140,160};std::vector<double>s,b,sw2;
 for(std::size_t j=0;j+1<edges.size();++j){const double fraction=.5*(std::erf((edges[j+1]-125)/(std::sqrt(2.)*2.))-std::erf((edges[j]-125)/(std::sqrt(2.)*2.)));s.push_back(20*fraction);b.push_back(3*(edges[j+1]-edges[j]));sw2.push_back(b.back()*b.back()/100.);}
 TemplateRepresentation templ{"SYNTHETIC","artificial_peak_plus_smooth","TOY","mass","hardcoded_synthetic_fixture_v1","POSITIVE_ONLY","SYNTHETIC_POSITIVE_YIELD","SYNTHETIC_DISJOINT","METHOD_ONLY","SYNTHETIC_METHOD_ONLY",edges,b,sw2,true};validateTemplate(templ);
 long double signalTotal=0;for(double x:s)signalTotal+=x;check("template_bin_integration",std::abs(static_cast<double>(signalTotal)-20)<1e-9,{{"integrated_signal",static_cast<double>(signalTotal)}});
 RooRealVar strength("mu_binned","synthetic signal strength",.8,0.,4.);
 RooRealVar theta("theta_norm","Gaussian background normalization nuisance",.1,-5.,5.);
 RooRealVar shape("theta_shape","normalized template shape nuisance",.1,-5.,5.);
 RooRealVar beta("beta_rate","positive log-normal background rate nuisance",1.03,.2,3.);
 RooRealVar thetaObs("theta_aux","Gaussian auxiliary observation",0.,-10.,10.);thetaObs.setConstant();
 RooRealVar shapeObs("shape_aux","shape auxiliary observation",0.,-10.,10.);shapeObs.setConstant();
 RooRealVar betaObs("beta_aux","log-normal auxiliary observation",1.,.00001,10.);betaObs.setConstant();
 RooConstVar unitSigma("unit_sigma","unit Gaussian auxiliary width",1.);
 RooConstVar lognormalK("lognormal_k","exp(0.10) synthetic width",std::exp(.10));
 RooGaussian normConstraint("norm_constraint","Gaussian auxiliary",thetaObs,theta,unitSigma);
 RooGaussian shapeConstraint("shape_constraint","Gaussian shape auxiliary",shapeObs,shape,unitSigma);
 RooLognormal rateConstraint("rate_constraint","positive log-normal rate auxiliary",betaObs,beta,lognormalK);
 RooFormulaVar rate("background_rate","@0*exp(0.10*@1)",RooArgList(beta,theta));
 RooArgSet productTerms(normConstraint,shapeConstraint,rateConstraint),observables,globalObs(thetaObs,shapeObs,betaObs),nuisances(theta,shape,beta);
 std::vector<std::unique_ptr<RooRealVar>> counts,gamma,mcObs;
 std::vector<std::unique_ptr<RooFormulaVar>> means,mcMeans;
 std::vector<std::unique_ptr<RooPoisson>> countPdfs,mcPdfs;
 std::vector<std::unique_ptr<RooConstVar>> taus;
 std::string denominator;double backgroundTotal=0;for(auto v:b)backgroundTotal+=v;
 for(std::size_t j=0;j<b.size();++j){if(j)denominator+='+';denominator+=str(b[j])+"*exp("+str((static_cast<double>(j)-3)*.04)+"*@2)";}
 for(std::size_t j=0;j<b.size();++j){const auto suffix=std::to_string(j);counts.push_back(std::make_unique<RooRealVar>(("n"+suffix).c_str(),"synthetic bin count",s[j]+b[j],0.,1000.));observables.add(*counts.back());
  gamma.push_back(std::make_unique<RooRealVar>(("gamma_mc"+suffix).c_str(),"scaled-Poisson MC-stat nuisance",1.01,.05,3.));nuisances.add(*gamma.back());
  mcObs.push_back(std::make_unique<RooRealVar>(("mc_aux"+suffix).c_str(),"effective MC auxiliary count",100.,0.,1000.));mcObs.back()->setConstant();globalObs.add(*mcObs.back());
  taus.push_back(std::make_unique<RooConstVar>(("tau"+suffix).c_str(),"synthetic effective MC count",100.));
  mcMeans.push_back(std::make_unique<RooFormulaVar>(("mc_mean"+suffix).c_str(),"@0*@1",RooArgList(*taus.back(),*gamma.back())));
  mcPdfs.push_back(std::make_unique<RooPoisson>(("mc_constraint"+suffix).c_str(),"scaled-Poisson auxiliary",*mcObs.back(),*mcMeans.back(),true));productTerms.add(*mcPdfs.back());
  const auto expression="@0*"+str(s[j])+"+@1*@3*("+str(backgroundTotal*b[j])+"*exp("+str((static_cast<double>(j)-3)*.04)+"*@2)/("+denominator+"))";
  means.push_back(std::make_unique<RooFormulaVar>(("mean_bin"+suffix).c_str(),expression.c_str(),RooArgList(strength,rate,shape,*gamma.back())));
  countPdfs.push_back(std::make_unique<RooPoisson>(("pdf_bin"+suffix).c_str(),"extended binned Poisson",*counts.back(),*means.back(),true));productTerms.add(*countPdfs.back());
 }
 RooProdPdf model("synthetic_binned_model","SYNTHETIC_METHOD_ONLY extended binned product",productTerms);
 RooDataSet data("synthetic_binned_asimov","artificial Gaussian peak over smooth background",observables);data.add(observables);
 auto nll=model.createNLL(data,RooFit::GlobalObservables(globalObs),RooFit::Constrain(nuisances),RooFit::Offset(false));
 RooMinimizer minimizer(*nll);minimizer.setPrintLevel(-1);minimizer.setStrategy(2);minimizer.setEps(1e-7);minimizer.setMaxIterations(5000);minimizer.setMaxFunctionCalls(20000);const auto fitStatus=minimizer.migrad();minimizer.hesse();auto result=std::unique_ptr<RooFitResult>(minimizer.save());
 double maxGammaPull=0;for(auto&g:gamma)maxGammaPull=std::max(maxGammaPull,std::abs(g->getVal()-1.));
 check("extended_binned_Asimov_recovery",fitStatus==0&&std::abs(strength.getVal()-1.)<.003&&std::abs(theta.getVal())<.01&&std::abs(shape.getVal())<.01&&std::abs(beta.getVal()-1.)<.003&&maxGammaPull<.003,{{"mu_hat",strength.getVal()},{"Gaussian_norm_pull",theta.getVal()},{"shape_pull",shape.getVal()},{"lognormal_rate",beta.getVal()},{"max_MC_factor_minus_one",maxGammaPull},{"fit_status",fitStatus},{"EDM",result?result->edm():-1.},{"minimizer_strategy",2},{"minimizer_tolerance",1e-7}});
 check("binned_covariance_matrix",result&&result->covQual()>=2&&result->covarianceMatrix().GetNrows()==static_cast<int>(nuisances.getSize()+1),{{"covariance_quality",result?result->covQual():-1},{"dimension",result?result->covarianceMatrix().GetNrows():0}});
 RooArgSet normAux(thetaObs);std::unique_ptr<RooAbsReal> gaussianIntegral(normConstraint.createIntegral(normAux,RooFit::NormSet(normAux)));
 RooArgSet logAux(betaObs);std::unique_ptr<RooAbsReal> lognormalIntegral(rateConstraint.createIntegral(logAux,RooFit::NormSet(logAux)));
 check("Gaussian_constraint_normalization",std::abs(gaussianIntegral->getVal()-1.)<1e-12);check("lognormal_constraint_normalization",std::abs(lognormalIntegral->getVal()-1.)<1e-12);
 const double fittedTheta=theta.getVal(),fittedBeta=beta.getVal();theta.setVal(0.);beta.setVal(1.);thetaObs.setVal(0.);betaObs.setVal(1.);
 check("Gaussian_analytic_density",std::abs(normConstraint.getVal(&normAux)-1./std::sqrt(2*std::acos(-1.)))<1e-12);
 check("lognormal_analytic_density",std::abs(rateConstraint.getVal(&logAux)-1./(.10*std::sqrt(2*std::acos(-1.))))<1e-10);
 theta.setVal(fittedTheta);beta.setVal(fittedBeta);

 strength.setVal(1);theta.setVal(0);shape.setVal(0);beta.setVal(1);for(auto&g:gamma)g->setVal(1);
 double sumExpected=0,sumObserved=0,logProduct=0,logMultinomial=0;
 for(std::size_t j=0;j<b.size();++j){sumExpected+=means[j]->getVal();sumObserved+=counts[j]->getVal();logProduct+=poissonLogLikelihood(counts[j]->getVal(),means[j]->getVal());logMultinomial-=std::lgamma(counts[j]->getVal()+1.);}
 logMultinomial+=std::lgamma(sumObserved+1.);for(std::size_t j=0;j<b.size();++j)logMultinomial+=counts[j]->getVal()*std::log(means[j]->getVal()/sumExpected);
 check("extended_binned_likelihood_identity",std::abs(logProduct-(poissonLogLikelihood(sumObserved,sumExpected)+logMultinomial))<1e-9);
 // Shape interpolation preserves its nominal integral before independent MC factors.
 shape.setVal(1.);double variedTotal=0;for(std::size_t j=0;j<b.size();++j)variedTotal+=means[j]->getVal()-s[j];check("shape_nuisance_normalized_integral",std::abs(variedTotal-backgroundTotal)<1e-9);
 RooRandom::randomGenerator()->SetSeed(toySeed);const auto randomFirst=RooRandom::randomGenerator()->Poisson(30.);RooRandom::randomGenerator()->SetSeed(toySeed);const auto randomAgain=RooRandom::randomGenerator()->Poisson(30.);check("deterministic_toy_seed",randomFirst==randomAgain,{{"seed",toySeed},{"toy_count",randomFirst}});
 auto rejects=[&](TemplateRepresentation bad,bool physical){try{validateTemplate(bad,physical);return false;}catch(const std::invalid_argument&){return true;}};
 auto bad=templ;bad.expected[0]=-1;check("negative_expectation_rejected",rejects(bad,false));bad=templ;bad.expected[0]=std::numeric_limits<double>::quiet_NaN();check("nonfinite_expectation_rejected",rejects(bad,false));bad=templ;bad.signedWeightStatus="SIGNED_UNMODELED";check("signed_weight_model_rejected",rejects(bad,false));bad=templ;bad.sourceIdentity.clear();check("missing_provenance_rejected",rejects(bad,false));check("synthetic_cannot_unlock_physical_fit",rejects(templ,true));
 bad=templ;bad.syntheticOnly=false;bad.validationState="VALIDATED_PHYSICAL";bad.normalizationScope="VALIDATED_PHYSICAL_YIELD";bad.overlapScope="OVERLAP_UNKNOWN";bad.systematicsAvailability="UNKNOWN";check("unknown_overlap_and_nuisance_rejected",rejects(bad,true));
 return {{"status","PASS_SYNTHETIC_METHOD_ONLY"},{"label","SYNTHETIC_METHOD_ONLY"},{"tests",checks},{"test_count",checks.size()},{"toy_seed",toySeed},
 {"template_shape_nuisance","exponential positive morph normalized to fixed background integral"},{"MC_statistical_treatment","synthetic scaled-Poisson effective-count auxiliary (tau=b^2/sumw2=100); approximate effective-count model, not a calibrated physical uncertainty"},
 {"physical_combined_likelihood","BLOCKED_OVERLAP_AND_CALIBRATION"},{"physical_significance","NOT_EVALUATED"},{"physical_CLs_limit","NOT_EVALUATED"},{"physical_kappa_interval","NOT_EVALUATED"},{"actual_HH_events_used",0}};
}
}

#include <RooArgSet.h>
#include <RooGaussian.h>
#include <RooRealVar.h>
#include <RooStats/ModelConfig.h>
#include <RooWorkspace.h>
#include <TROOT.h>

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

static_assert(__cplusplus == 202002L, "Step 1 requires exactly C++20.");

namespace {
void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
}

int main() {
  try {
    gROOT->SetBatch(true);
    RooRealVar x("x", "Synthetic observable", 0., -5., 5.);
    RooRealVar mean("mean", "Synthetic location", 0., -1., 1.);
    RooRealVar sigma("sigma", "Synthetic width", 1., 0.1, 3.);
    RooGaussian gaussian("gaussian", "Basic RooFit object fixture", x, mean, sigma);
    RooArgSet observables(x);
    const double center = gaussian.getVal(&observables);
    x.setVal(1.);
    const double positive = gaussian.getVal(&observables);
    x.setVal(-1.);
    const double negative = gaussian.getVal(&observables);
    require(std::isfinite(center) && center > 0., "Normalized RooFit object evaluation failed");
    require(std::abs(positive / center - std::exp(-0.5)) < 1e-12, "Gaussian value ratio differs");
    require(std::abs(positive - negative) < 1e-12, "Gaussian symmetry differs");
    x.setVal(0.);

    RooWorkspace workspace("synthetic_workspace");
    require(!workspace.import(gaussian), "RooWorkspace import failed");
    require(workspace.pdf("gaussian") && workspace.var("x") && workspace.var("mean") && workspace.var("sigma"),
            "Imported RooFit objects are missing");
    RooStats::ModelConfig model("synthetic_model", &workspace);
    model.SetPdf(*workspace.pdf("gaussian"));
    model.SetObservables(RooArgSet(*workspace.var("x")));
    model.SetParametersOfInterest(RooArgSet(*workspace.var("mean")));
    model.SetNuisanceParameters(RooArgSet(*workspace.var("sigma")));
    require(model.GetPdf() && std::string(model.GetPdf()->GetName()) == "gaussian", "ModelConfig PDF differs");
    require(model.GetObservables() && model.GetObservables()->getSize() == 1 && model.GetObservables()->find("x"),
            "ModelConfig observable differs");
    require(model.GetParametersOfInterest() && model.GetParametersOfInterest()->getSize() == 1
            && model.GetParametersOfInterest()->find("mean"), "ModelConfig parameter differs");
    require(model.GetNuisanceParameters() && model.GetNuisanceParameters()->getSize() == 1
            && model.GetNuisanceParameters()->find("sigma"), "ModelConfig nuisance parameter differs");
    std::cout << "PASS RooFit/RooStats: Gaussian object evaluation and ModelConfig references; no fit performed\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL RooFit/RooStats: " << error.what() << '\n';
    return 1;
  }
}

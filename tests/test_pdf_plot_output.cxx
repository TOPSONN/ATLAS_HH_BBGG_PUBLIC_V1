#include "AtlasPlotting.h"
#include <TCanvas.h>
#include <TFile.h>
#include <TGraphErrors.h>
#include <TGraphAsymmErrors.h>
#include <TH1D.h>
#include <TH2D.h>
#include <chrono>
#include <cmath>
#include <TROOT.h>
#include <TStyle.h>
#include <TNamed.h>
#include <fstream>
#include <iostream>
#include <stdexcept>
int main() {
  try {
    const auto directory=std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR)/"plot_test_outputs";
    // A fresh unique child keeps repeated CTest runs non-destructive.
    std::filesystem::create_directories(directory);
    const auto out=directory/ std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    atlas::plotting::Metadata m;m.record="synthetic-fixture";m.period="Synthetic fixture";m.selection="Synthetic numerical test";
    m.unit_status="VERIFIED";m.inspected=4;m.accepted=4;m.end=4;
    TH1D h("synthetic_mass","",4,100,140);h.SetDirectory(nullptr);
    for(double x:{105.,115.,115.,125.})h.Fill(x);
    const double counts=h.Integral(),entries=h.GetEntries();
    atlas::plotting::RenderHistogram(h,out/"synthetic_mass",m,"m_{#gamma#gamma} [GeV]","Events / 10 GeV",true);
    if(h.Integral()!=counts||h.GetEntries()!=entries)throw std::runtime_error("Plotting changed histogram values");
    atlas::plotting::ApplyAtlasPlotStyle();
    const double x[]{1,2,3},y[]{2,4,3},dx[]{0,0,0},dy[]{.1,.2,.1};TGraphErrors graph(3,x,y,dx,dy);graph.SetName("synthetic_graph");
    TCanvas gc("graph_canvas","",800,600);gc.SetCanvasSize(800,600);graph.SetMarkerStyle(20);graph.SetMarkerSize(.9);graph.SetMarkerColor(kBlue+2);graph.SetLineColor(kBlue+2);
    graph.Draw("AP");atlas::plotting::ConfigurePhysicsAxes(*graph.GetHistogram(),"p_{T}^{jet} [GeV]","Synthetic response");
    atlas::plotting::DrawOpenDataLabel(m);atlas::plotting::ExportPhysicsCanvas(gc,graph,out/"synthetic_graph",m);
    TH2D h2("synthetic_density","",4,0,4,4,-2,2);h2.SetDirectory(nullptr);h2.Fill(1,-1);h2.Fill(2,1);h2.Fill(3,1);h2.Fill(3,1);
    TCanvas dc("density_canvas","",800,600);dc.SetCanvasSize(800,600);dc.SetRightMargin(.16);
    atlas::plotting::ConfigurePhysicsAxes(h2,"p_{T}^{#gamma} [GeV]","#eta^{#gamma}","Raw counts / bin");h2.Draw("COLZ");
    auto density_metadata=m;density_metadata.label_placement=atlas::plotting::LabelPlacement::UpperLeft;
    atlas::plotting::DrawOpenDataLabel(density_metadata);atlas::plotting::ExportPhysicsCanvas(dc,h2,out/"synthetic_density",density_metadata);
    TFile root((out/"synthetic_mass.root").c_str(),"READ");auto* saved=root.Get<TH1D>("synthetic_mass");
    if(!saved||saved->GetEntries()!=4||saved->GetBinContent(2)!=2||!root.Get("atlas_plot_metadata"))throw std::runtime_error("ROOT object preservation failure");
    auto* caption=root.Get<TNamed>("atlas_plot_caption");
    std::ifstream caption_file(out/"synthetic_mass.caption.md");
    const std::string caption_text((std::istreambuf_iterator<char>(caption_file)),std::istreambuf_iterator<char>());
    if(!caption||caption_text!=std::string(caption->GetTitle()))throw std::runtime_error("Figure caption/native ROOT preservation failure");
    auto* errors=root.Get<TGraphAsymmErrors>("synthetic_mass_display");
    TH1D poisson=h;poisson.SetDirectory(nullptr);poisson.SetBinErrorOption(TH1::kPoisson);
    if(!errors||errors->GetN()!=4)throw std::runtime_error("Counting interval object missing");
    for(int i=0;i<4;++i)if(std::abs(errors->GetErrorYlow(i)-poisson.GetBinErrorLow(i+1))>1e-7 || std::abs(errors->GetErrorYhigh(i)-poisson.GetBinErrorUp(i+1))>1e-7)
      throw std::runtime_error("Independent native ROOT Poisson interval cross-check failed");
    bool refused=false;try{atlas::plotting::ExportPhysicsCanvas(gc,graph,out/"synthetic_graph",m);}catch(const std::runtime_error&){refused=true;}
    if(!refused)throw std::runtime_error("Existing outputs overwritten");
    bool width_refused=false;
    try{atlas::plotting::RenderHistogram(h,out/"wrong_width",m,"m_{#gamma#gamma} [GeV]","Events / 5 GeV",true);}catch(const std::invalid_argument&){width_refused=true;}
    if(!width_refused || std::filesystem::exists(out/"wrong_width.pdf"))throw std::runtime_error("Wrong bin-width label was exported");
    gStyle->SetOptStat(1);bool style_refused=false;
    try{atlas::plotting::ExportPhysicsCanvas(gc,graph,out/"wrong_style",m);}catch(const std::invalid_argument&){style_refused=true;}
    atlas::plotting::ApplyAtlasPlotStyle();
    if(!style_refused || std::filesystem::exists(out/"wrong_style.pdf"))throw std::runtime_error("Noncompliant style was exported");
    std::cout<<"PASS native TH1D/TH2D/TGraphErrors PDF/PNG/ROOT export and preservation; output="<<out<<'\n';
  }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}

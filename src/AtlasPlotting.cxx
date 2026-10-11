#include "AtlasPlotting.h"
#include <TCanvas.h>
#include <TFile.h>
#include <TDirectory.h>
#include <TGraphAsymmErrors.h>
#include <TH1.h>
#include <TLatex.h>
#include <TLegend.h>
#include <TNamed.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TGaxis.h>
#include <Math/QuantFuncMathCore.h>
#include <algorithm>
#include <cctype>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace atlas::plotting {
namespace {
void text_field(const std::string& value,std::size_t maximum) {
  if(value.empty() || value.size()>maximum || std::any_of(value.begin(),value.end(),[](unsigned char c){return c<32 || c>126;}))
    throw std::invalid_argument("Missing, oversized or unsupported plot metadata text");
  std::string lower=value;
  std::transform(lower.begin(),lower.end(),lower.begin(),[](unsigned char c){return std::tolower(c);});
  for(const char* forbidden:{"atlas preliminary","atlas internal","atlas official","atlas simulation preliminary"})
    if(lower.find(forbidden)!=std::string::npos) throw std::invalid_argument("Forbidden collaboration-status label");
}
std::string quote(const std::string& value) {
  std::string result="\"";
  for(char c:value) {if(c=='"'||c=='\\')result+='\\';result+=c;}
  return result+'"';
}
const char* kind_name(SampleKind kind) {
  switch(kind) {case SampleKind::Data:return "DATA";case SampleKind::Simulation:return "MC";case SampleKind::Synthetic:return "SYNTHETIC";}
  throw std::invalid_argument("Invalid sample kind");
}
std::string metadata_json(const Metadata& m,int width,int height) {
  std::ostringstream s;s<<std::setprecision(17);
  s<<"{\"standard\":\"atlas-root-plot-v1\",\"root_version\":\""<<gROOT->GetVersion()<<"\",\"style\":\"ATLAS\",\"sample_kind\":"<<quote(kind_name(m.kind))
   <<",\"record\":"<<quote(m.record)<<",\"period\":"<<quote(m.period)<<",\"selection\":"<<quote(m.selection)
   <<",\"unit_status\":"<<quote(m.unit_status)<<",\"weighting\":"<<quote(m.weighting)
   <<",\"inspected\":"<<m.inspected<<",\"accepted\":"<<m.accepted<<",\"start\":"<<m.start<<",\"end\":"<<m.end
   <<",\"energy_tev\":"<<(m.energy_tev?std::to_string(*m.energy_tev):"null")
   <<",\"luminosity_pb\":"<<(m.luminosity_pb?std::to_string(*m.luminosity_pb):"null")
   <<",\"luminosity_validated\":"<<(m.luminosity_validated?"true":"false")
   <<",\"luminosity_evidence\":"<<quote(m.luminosity_evidence)
   <<",\"canvas_width\":"<<width<<",\"canvas_height\":"<<height<<"}\n";
  return s.str();
}
}
void ApplyAtlasPlotStyle() {
  if(std::string(gROOT->GetVersion())!="6.40.04") throw std::runtime_error("Plotting contract requires ROOT 6.40.04");
  if(!gROOT->GetStyle("ATLAS")) throw std::runtime_error("Built-in ATLAS style unavailable");
  gROOT->SetBatch(true);
  gROOT->SetStyle("ATLAS");
  gROOT->ForceStyle();
  gStyle->SetCanvasColor(0);gStyle->SetPadColor(0);gStyle->SetFrameFillColor(0);
  gStyle->SetCanvasBorderMode(0);gStyle->SetPadBorderMode(0);gStyle->SetFrameBorderMode(0);
  gStyle->SetTextFont(42);gStyle->SetLabelFont(42,"XYZ");gStyle->SetTitleFont(42,"XYZ");
  gStyle->SetOptTitle(0);gStyle->SetOptStat(0);gStyle->SetOptFit(0);
  gStyle->SetPadLeftMargin(.14);gStyle->SetPadRightMargin(.045);
  gStyle->SetPadBottomMargin(.22);gStyle->SetPadTopMargin(.28);
  gStyle->SetPadTickX(1);gStyle->SetPadTickY(1);
  gStyle->SetAxisColor(kBlack,"XYZ");gStyle->SetLabelColor(kBlack,"XYZ");gStyle->SetTitleColor(kBlack,"XYZ");
  gStyle->SetHistLineWidth(2);gStyle->SetLineWidth(2);gStyle->SetMarkerStyle(20);gStyle->SetMarkerSize(.65);
  gStyle->SetLegendBorderSize(0);gStyle->SetLegendFont(42);gStyle->SetPaperSize(26,20);
  TGaxis::SetMaxDigits(3);
}
void ValidatePlotMetadata(const Metadata& m) {
  kind_name(m.kind);
  text_field(m.record,40);text_field(m.period,40);text_field(m.selection,76);text_field(m.weighting,76);
  if(m.unit_status!="VERIFIED"&&m.unit_status!="PROVISIONAL") throw std::invalid_argument("Unknown/contradicted units block finalized physics plots");
  if(!m.inspected || m.accepted>m.inspected || m.end<=m.start || m.end-m.start!=m.inspected)
    throw std::invalid_argument("Invalid inspected/accepted event counts or source range");
  if(m.weighting!="Raw unweighted counts") throw std::invalid_argument("Weighted/normalized plots require a separately validated extension");
  if(m.kind!=SampleKind::Synthetic && (!m.energy_tev || !std::isfinite(*m.energy_tev) || *m.energy_tev<=0))
    throw std::invalid_argument("Collision data/MC energy metadata missing");
  if(m.energy_tev && (!std::isfinite(*m.energy_tev)||*m.energy_tev<=0)) throw std::invalid_argument("Invalid collision energy");
  if(m.luminosity_pb && (m.kind==SampleKind::Synthetic || !m.luminosity_validated || m.luminosity_evidence.empty() || !std::isfinite(*m.luminosity_pb) || *m.luminosity_pb<=0))
    throw std::invalid_argument("Unvalidated luminosity cannot be shown");
}
void DrawOpenDataLabel(const Metadata& m) {
  ValidatePlotMetadata(m);
  TLatex t;t.SetNDC();t.SetTextFont(42);t.SetTextColor(kBlack);t.SetTextSize(.028);
  t.DrawLatex(.14,.961,m.kind==SampleKind::Synthetic?"Synthetic test":"ATLAS Open Data");
  t.DrawLatex(.14,.925,m.kind==SampleKind::Synthetic?"Independent numerical validation":"Independent exploratory analysis");
  t.SetTextSize(.022);
  std::ostringstream energy;if(m.energy_tev)energy<<std::setprecision(6)<<*m.energy_tev;
  const std::string source=(m.energy_tev?"#sqrt{s} = "+energy.str()+" TeV | ":"")+m.period+" | Record "+m.record+" | "+kind_name(m.kind);
  t.DrawLatex(.14,.884,source.c_str());
  const auto counts="Inspected "+std::to_string(m.inspected)+"; accepted "+std::to_string(m.accepted)+"; entries ["+std::to_string(m.start)+","+std::to_string(m.end)+")";
  t.DrawLatex(.14,.850,counts.c_str());
  t.DrawLatex(.14,.816,("Selection: "+m.selection).c_str());
  t.DrawLatex(.14,.782,("Units: "+m.unit_status+" | "+m.weighting).c_str());
  if(m.luminosity_pb) t.DrawLatex(.63,.925,("L = "+std::to_string(*m.luminosity_pb)+" pb^{-1}").c_str());
  t.SetTextSize(.020);
  if(m.kind==SampleKind::Data) {
    t.DrawLatex(.14,.082,"ATLAS Open Data exploratory diagnostic;");
    t.DrawLatex(.14,.053,m.record=="93915"?"raw unweighted GamGam skim;":"raw unweighted collision data;");
    t.DrawLatex(.14,.024,"not the official ATLAS HH analysis.");
  } else {
    t.DrawLatex(.14,.053,m.kind==SampleKind::Synthetic?"Synthetic test; no collision data or MC.":"MC simulation; no observed collision data.");
    t.DrawLatex(.14,.024,"Independent work; not an official ATLAS measurement.");
  }
}
void ConfigurePhysicsAxes(TH1& h,const std::string& x,const std::string& y,const std::string& z) {
  text_field(x,100);text_field(y,100);
  h.SetTitle("");h.SetStats(false);h.GetXaxis()->SetTitle(x.c_str());h.GetYaxis()->SetTitle(y.c_str());
  if(!z.empty())h.GetZaxis()->SetTitle(z.c_str());
  for(auto* axis:{h.GetXaxis(),h.GetYaxis(),h.GetZaxis()}) {
    axis->SetLabelFont(42);axis->SetTitleFont(42);axis->SetLabelSize(.034);axis->SetTitleSize(.040);
    axis->SetAxisColor(kBlack);axis->SetLabelColor(kBlack);axis->SetTitleColor(kBlack);
  }
  h.GetXaxis()->SetTitleOffset(1.10);h.GetYaxis()->SetTitleOffset(1.15);
}
void ConfigureLegend(TLegend& legend) {legend.SetFillStyle(0);legend.SetBorderSize(0);legend.SetTextFont(42);legend.SetTextSize(.021);}
void ExportPhysicsCanvas(TCanvas& canvas,TObject& object,const std::filesystem::path& base,const Metadata& m,TObject* display) {
  ValidatePlotMetadata(m);
  if(std::string(gStyle->GetName())!="ATLAS" || gStyle->GetTextFont()!=42 || gStyle->GetOptTitle() || gStyle->GetOptStat() || gStyle->GetOptFit() ||
     canvas.GetFillColor()!=0 || canvas.GetTickx()!=1 || canvas.GetTicky()!=1)
    throw std::invalid_argument("Canvas/style does not satisfy the ATLAS plotting contract");
  for(const char* ext:{".pdf",".png",".root",".plot.json"}) if(std::filesystem::exists(base.string()+ext)) throw std::runtime_error("Plot output exists; refusing overwrite");
  if(!base.parent_path().empty())std::filesystem::create_directories(base.parent_path());
  canvas.Modified();canvas.Update();
  canvas.SaveAs((base.string()+".pdf").c_str());canvas.SaveAs((base.string()+".png").c_str());
  const auto json=metadata_json(m,canvas.GetWw(),canvas.GetWh());
  TDirectory::TContext preserve_directory;
  TFile root((base.string()+".root").c_str(),"CREATE");
  if(root.IsZombie() || object.Write(object.GetName())<=0)throw std::runtime_error("Cannot preserve native plot object");
  if(display && display->Write(display->GetName())<=0)throw std::runtime_error("Cannot preserve display uncertainties");
  TNamed metadata("atlas_plot_metadata",json.c_str());metadata.Write();root.Close();
  std::ofstream sidecar(base.string()+".plot.json");sidecar.exceptions(std::ios::badbit|std::ios::failbit);sidecar<<json;sidecar.close();
  for(const char* ext:{".pdf",".png",".root"}) if(!std::filesystem::is_regular_file(base.string()+ext) || !std::filesystem::file_size(base.string()+ext)) throw std::runtime_error("Missing plot output");
}
void RenderHistogram(TH1& h,const std::filesystem::path& base,const Metadata& m,const std::string& x,const std::string& y,bool event_counts) {
  ValidatePlotMetadata(m);ApplyAtlasPlotStyle();
  if(h.GetDimension()!=1 || h.GetEntries()<=0) throw std::invalid_argument("Need nonempty native 1D histogram");
  ConfigurePhysicsAxes(h,x,y);h.SetLineWidth(2);h.SetMarkerStyle(20);h.SetMarkerSize(.65);h.SetMinimum(0);
  if(y.find("GeV")!=std::string::npos) {
    const auto slash=y.find('/');std::istringstream advertised(slash==std::string::npos?"":y.substr(slash+1));double width=0;std::string unit;
    if(!(advertised>>width>>unit) || unit!="GeV" || x.find("GeV")==std::string::npos)throw std::invalid_argument("Invalid declared bin-width axis label");
    for(int bin=1;bin<=h.GetNbinsX();++bin)if(std::abs(h.GetBinWidth(bin)-width)>1e-9*std::max(1.,width))
      throw std::invalid_argument("Declared bin-width normalization does not match raw bins");
  }
  TGraphAsymmErrors display;display.SetName((std::string(h.GetName())+"_display").c_str());
  constexpr double tail=(1.-.682689492137)/2.;double maximum=0;
  for(int bin=1;bin<=h.GetNbinsX();++bin) {
    const double n=h.GetBinContent(bin);
    if(!std::isfinite(n)||n<0 || std::abs(n-std::round(n))>1e-8)throw std::invalid_argument("Raw counts must be nonnegative integers");
    double lo=0,hi=0;
    if(event_counts) {lo=n>0?n-ROOT::Math::gamma_quantile(tail,n,1.):0;hi=ROOT::Math::gamma_quantile_c(tail,n+1,1.)-n;}
    if(n>0 || event_counts) {const auto p=display.GetN();display.SetPoint(p,h.GetBinCenter(bin),n);display.SetPointError(p,0,0,lo,hi);}
    maximum=std::max(maximum,n+hi);
  }
  h.SetMaximum(maximum*1.12);h.SetLineColor(m.kind==SampleKind::Data?kBlack:kBlue+2);
  display.SetMarkerStyle(20);display.SetMarkerSize(.65);display.SetMarkerColor(kBlack);display.SetLineColor(kBlack);display.SetLineWidth(1);
  TCanvas canvas("atlas_physics_canvas","atlas-root-plot-v1",1100,900);
  h.Draw(m.kind==SampleKind::Data?"AXIS":"HIST");
  if(m.kind==SampleKind::Data)display.Draw(event_counts?"PZ SAME":"P SAME");
  DrawOpenDataLabel(m);
  TLegend legend(.53,.737,.94,.769);ConfigureLegend(legend);
  const auto label=m.kind==SampleKind::Data?(event_counts?"Collision data; Poisson 68.27%":"Collision data; object counts"):kind_name(m.kind);
  legend.AddEntry(m.kind==SampleKind::Data?static_cast<TObject*>(&display):static_cast<TObject*>(&h),label,m.kind==SampleKind::Data?"p":"l");legend.Draw();
  ExportPhysicsCanvas(canvas,h,base,m,(m.kind==SampleKind::Data || event_counts)?&display:nullptr);
}
}

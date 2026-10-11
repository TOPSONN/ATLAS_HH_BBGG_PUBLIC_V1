#include "AtlasPlotting.h"
#include <TCanvas.h>
#include <TFile.h>
#include <TDirectory.h>
#include <TGraphAsymmErrors.h>
#include <TGraph.h>
#include <TH1.h>
#include <TLatex.h>
#include <TLegend.h>
#include <TNamed.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TGaxis.h>
#include <TPad.h>
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
  for(char c:value) {
    if(c=='\n'){result+="\\n";continue;}if(c=='\r'){result+="\\r";continue;}if(c=='\t'){result+="\\t";continue;}
    if(c=='"'||c=='\\')result+='\\';
    result+=c;
  }
  return result+'"';
}
const char* kind_name(SampleKind kind) {
  switch(kind) {case SampleKind::Data:return "DATA";case SampleKind::Simulation:return "MC";case SampleKind::Synthetic:return "SYNTHETIC";}
  throw std::invalid_argument("Invalid sample kind");
}
double label_x(const Metadata& m,double left,double right) {
  return m.label_placement==LabelPlacement::UpperLeft?left+.035:1.-right-.035;
}
std::string figure_caption(const Metadata& m,TObject& object,TObject* display) {
  std::ostringstream s;s<<std::setprecision(17);
  s<<"Figure: "<<object.GetName()<<". Sample: "<<kind_name(m.kind)<<".\n";
  s<<(m.kind==SampleKind::Synthetic?"Synthetic test. Independent numerical validation.":"ATLAS Open Data. Independent exploratory analysis.")<<"\n";
  s<<"Record: "<<m.record<<". Period: "<<m.period<<".\n";
  if(m.energy_tev)s<<"Collision energy: sqrt(s) = "<<*m.energy_tev<<" TeV.\n";
  s<<"Inspected: "<<m.inspected<<". Accepted: "<<m.accepted<<". Entries ["<<m.start<<","<<m.end<<").\n";
  s<<"Selection: "<<m.selection<<".\nUnits: "<<m.unit_status<<". Weighting: "<<m.weighting<<".\n";
  if(m.luminosity_pb)s<<"Validated luminosity: "<<*m.luminosity_pb<<" pb^-1; evidence: "<<m.luminosity_evidence<<".\n";
  else s<<"Integrated luminosity is not shown; usable luminosity is not validated for this sample.\n";
  auto* h=dynamic_cast<TH1*>(&object);auto* graph=dynamic_cast<TGraph*>(&object);
  auto* axes=h?h:(graph?graph->GetHistogram():nullptr);
  if(axes)s<<"X axis: "<<axes->GetXaxis()->GetTitle()<<". Y axis: "<<axes->GetYaxis()->GetTitle()<<".\n";
  if(h) {
    s<<"Native binning: "<<h->GetNbinsX()<<" x bins over ["<<h->GetXaxis()->GetXmin()<<","<<h->GetXaxis()->GetXmax()<<"). Entries: "<<h->GetEntries()<<".\n";
    if(h->GetDimension()==1)s<<"Underflow: "<<h->GetBinContent(0)<<". Overflow: "<<h->GetBinContent(h->GetNbinsX()+1)<<". Original bin errors preserved.\n";
  }
  auto* errors=dynamic_cast<TGraphAsymmErrors*>(display);bool intervals=false;
  if(errors)for(int i=0;i<errors->GetN();++i)intervals=intervals || errors->GetErrorYhigh(i)>0 || errors->GetErrorYlow(i)>0;
  if(m.kind==SampleKind::Data)s<<(intervals?"Error bars: central 68.27% Garwood Poisson counting intervals; no systematics.":"Object-count markers without error bars; within-event correlations are not modeled.")<<"\n";
  else s<<"Synthetic/MC native error definitions are retained; standalone raw-count histograms use a distinct line.\n";
  if(m.kind==SampleKind::Data)s<<"ATLAS Open Data exploratory diagnostic;\n"<<(m.record=="93915"?"raw unweighted GamGam skim;\n":"raw unweighted collision data;\n")<<"not the official ATLAS HH analysis.\n";
  else s<<(m.kind==SampleKind::Synthetic?"Synthetic test; no collision data or MC.":"MC simulation; no observed collision data.")<<"\nIndependent work; not an official ATLAS measurement.\n";
  return s.str();
}
std::string metadata_json(const Metadata& m,const TCanvas& canvas,const std::string& caption) {
  std::ostringstream s;s<<std::setprecision(17);
  s<<"{\"standard\":\"atlas-root-plot-v2\",\"root_version\":\""<<gROOT->GetVersion()<<"\",\"style\":\"ATLAS\",\"sample_kind\":"<<quote(kind_name(m.kind))
   <<",\"record\":"<<quote(m.record)<<",\"period\":"<<quote(m.period)<<",\"selection\":"<<quote(m.selection)
   <<",\"unit_status\":"<<quote(m.unit_status)<<",\"weighting\":"<<quote(m.weighting)
   <<",\"inspected\":"<<m.inspected<<",\"accepted\":"<<m.accepted<<",\"start\":"<<m.start<<",\"end\":"<<m.end
   <<",\"energy_tev\":"<<(m.energy_tev?std::to_string(*m.energy_tev):"null")
   <<",\"luminosity_pb\":"<<(m.luminosity_pb?std::to_string(*m.luminosity_pb):"null")
   <<",\"luminosity_validated\":"<<(m.luminosity_validated?"true":"false")
   <<",\"luminosity_evidence\":"<<quote(m.luminosity_evidence)
   <<",\"canvas_width\":"<<canvas.GetWw()<<",\"canvas_height\":"<<canvas.GetWh()
   <<",\"caption\":"<<quote(caption)<<",\"layout\":{\"nominal_width\":800,\"nominal_height\":600"
   <<",\"left_margin\":"<<canvas.GetLeftMargin()<<",\"right_margin\":"<<canvas.GetRightMargin()
   <<",\"top_margin\":"<<canvas.GetTopMargin()<<",\"bottom_margin\":"<<canvas.GetBottomMargin()
   <<",\"axis_title_size\":0.05,\"axis_label_size\":0.045,\"text_size\":0.04,\"experiment_text_size\":0.045,\"marker_style\":20,\"marker_size\":0.9"
   <<",\"label_position\":"<<quote(m.label_placement==LabelPlacement::UpperLeft?"upper_left":"upper_right")
   <<",\"label_x\":"<<label_x(m,canvas.GetLeftMargin(),canvas.GetRightMargin())<<",\"label_y\":"<<m.label_y<<",\"single_series_legend\":false}}\n";
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
  gStyle->SetPadLeftMargin(.16);gStyle->SetPadRightMargin(.05);
  gStyle->SetPadBottomMargin(.16);gStyle->SetPadTopMargin(.05);
  gStyle->SetPadTickX(1);gStyle->SetPadTickY(1);
  gStyle->SetAxisColor(kBlack,"XYZ");gStyle->SetLabelColor(kBlack,"XYZ");gStyle->SetTitleColor(kBlack,"XYZ");
  gStyle->SetHistLineWidth(2);gStyle->SetLineWidth(2);gStyle->SetMarkerStyle(20);gStyle->SetMarkerSize(.9);
  gStyle->SetLabelSize(.045,"XYZ");gStyle->SetTitleSize(.05,"XYZ");gStyle->SetTextSize(.04);
  gStyle->SetLegendBorderSize(0);gStyle->SetLegendFont(42);gStyle->SetPaperSize(20,15);
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
  if(!std::isfinite(m.label_y) || m.label_y<.80 || m.label_y>.90)throw std::invalid_argument("Publication labels must remain inside the plotting frame");
}
void DrawOpenDataLabel(const Metadata& m) {
  ValidatePlotMetadata(m);
  if(!gPad)throw std::runtime_error("Publication label requires an active ROOT pad");
  TLatex t;t.SetNDC();t.SetTextFont(42);t.SetTextColor(kBlack);t.SetTextSize(.045);
  t.SetTextAlign(m.label_placement==LabelPlacement::UpperLeft?11:31);
  const double x=label_x(m,gPad->GetLeftMargin(),gPad->GetRightMargin());
  t.DrawLatex(x,m.label_y,m.kind==SampleKind::Synthetic?"Synthetic test":"ATLAS Open Data");
  t.SetTextSize(.04);
  if(m.kind==SampleKind::Synthetic) {
    t.DrawLatex(x,m.label_y-.055,"Numerical validation");
    t.DrawLatex(x,m.label_y-.110,m.unit_status=="PROVISIONAL"?"Provisional fixture":"Verified fixture");
  } else {
    std::ostringstream source;source<<"#sqrt{s} = "<<std::setprecision(6)<<*m.energy_tev<<" TeV, ";
    const bool has_year=m.period.size()>=4 && std::all_of(m.period.begin(),m.period.begin()+4,[](unsigned char c){return std::isdigit(c);});
    if(has_year)source<<m.period.substr(0,4)<<' ';
    source<<(m.kind==SampleKind::Data?"data":"MC simulation");
    t.DrawLatex(x,m.label_y-.055,source.str().c_str());
    t.DrawLatex(x,m.label_y-.110,m.unit_status=="PROVISIONAL"?"Exploratory, provisional":"Exploratory, verified");
  }
}
void ConfigurePhysicsAxes(TH1& h,const std::string& x,const std::string& y,const std::string& z) {
  text_field(x,100);text_field(y,100);
  h.SetTitle("");h.SetStats(false);h.GetXaxis()->SetTitle(x.c_str());h.GetYaxis()->SetTitle(y.c_str());
  if(!z.empty())h.GetZaxis()->SetTitle(z.c_str());
  for(auto* axis:{h.GetXaxis(),h.GetYaxis(),h.GetZaxis()}) {
    axis->SetLabelFont(42);axis->SetTitleFont(42);axis->SetLabelSize(.045);axis->SetTitleSize(.05);axis->CenterTitle(false);
    axis->SetAxisColor(kBlack);axis->SetLabelColor(kBlack);axis->SetTitleColor(kBlack);
  }
  h.GetXaxis()->SetTitleOffset(1.10);h.GetYaxis()->SetTitleOffset(1.40);
}
void ConfigureLegend(TLegend& legend) {legend.SetFillStyle(0);legend.SetBorderSize(0);legend.SetTextFont(42);legend.SetTextSize(.04);}
void ExportPhysicsCanvas(TCanvas& canvas,TObject& object,const std::filesystem::path& base,const Metadata& m,TObject* display) {
  ValidatePlotMetadata(m);
  if(std::string(gStyle->GetName())!="ATLAS" || gStyle->GetTextFont()!=42 || gStyle->GetOptTitle() || gStyle->GetOptStat() || gStyle->GetOptFit() ||
     canvas.GetFillColor()!=0 || canvas.GetTickx()!=1 || canvas.GetTicky()!=1)
    throw std::invalid_argument("Canvas/style does not satisfy the ATLAS plotting contract");
  for(const char* ext:{".pdf",".png",".root",".plot.json",".caption.md"}) if(std::filesystem::exists(base.string()+ext)) throw std::runtime_error("Plot output exists; refusing overwrite");
  if(!base.parent_path().empty())std::filesystem::create_directories(base.parent_path());
  canvas.Modified();canvas.Update();
  canvas.SaveAs((base.string()+".pdf").c_str());canvas.SaveAs((base.string()+".png").c_str());
  const auto caption=figure_caption(m,object,display);const auto json=metadata_json(m,canvas,caption);
  TDirectory::TContext preserve_directory;
  TFile root((base.string()+".root").c_str(),"CREATE");
  if(root.IsZombie() || object.Write(object.GetName())<=0)throw std::runtime_error("Cannot preserve native plot object");
  if(display && display->Write(display->GetName())<=0)throw std::runtime_error("Cannot preserve display uncertainties");
  TNamed metadata("atlas_plot_metadata",json.c_str());metadata.Write();
  TNamed native_caption("atlas_plot_caption",caption.c_str());native_caption.Write();root.Close();
  std::ofstream sidecar(base.string()+".plot.json");sidecar.exceptions(std::ios::badbit|std::ios::failbit);sidecar<<json;sidecar.close();
  std::ofstream caption_file(base.string()+".caption.md");caption_file.exceptions(std::ios::badbit|std::ios::failbit);caption_file<<caption;caption_file.close();
  for(const char* ext:{".pdf",".png",".root"}) if(!std::filesystem::is_regular_file(base.string()+ext) || !std::filesystem::file_size(base.string()+ext)) throw std::runtime_error("Missing plot output");
}
void RenderHistogram(TH1& h,const std::filesystem::path& base,const Metadata& m,const std::string& x,const std::string& y,bool event_counts) {
  ValidatePlotMetadata(m);ApplyAtlasPlotStyle();
  if(h.GetDimension()!=1 || h.GetEntries()<=0) throw std::invalid_argument("Need nonempty native 1D histogram");
  ConfigurePhysicsAxes(h,x,y);h.SetLineWidth(2);h.SetMarkerStyle(20);h.SetMarkerSize(.9);h.SetMinimum(0);
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
  // Choose the least occupied upper corner; only the displayed y limit changes.
  // Conservative NDC bounds include the full three-line annotation and marker/error extent.
  auto drawing=m;double headroom=1.12;bool clear=false;
  for(;headroom<=1.60 && !clear;headroom+=.04) {
    for(const auto placement:{LabelPlacement::UpperLeft,LabelPlacement::UpperRight}) {
      const double left=placement==LabelPlacement::UpperLeft?.185:.57;
      const double right=placement==LabelPlacement::UpperLeft?.535:.935;
      const double bottom=m.label_y-.13,top=m.label_y+.05;
      bool occupied=false;
      for(int i=0;i<display.GetN();++i) {
        const double px=.16+(display.GetPointX(i)-h.GetXaxis()->GetXmin())/(h.GetXaxis()->GetXmax()-h.GetXaxis()->GetXmin())*.79;
        const double low=.16+(display.GetPointY(i)-display.GetErrorYlow(i))/(maximum*headroom)*.79;
        const double high=.16+(display.GetPointY(i)+display.GetErrorYhigh(i))/(maximum*headroom)*.79;
        if(px>=left && px<=right && high>=bottom-.012 && low<=top+.012) {occupied=true;break;}
      }
      if(!occupied){drawing.label_placement=placement;clear=true;break;}
    }
  }
  if(!clear)throw std::runtime_error("No clear publication annotation corner; review a plot-specific layout");
  h.SetMaximum(maximum*(headroom-.04));h.SetLineColor(m.kind==SampleKind::Data?kBlack:kBlue+2);
  display.SetMarkerStyle(20);display.SetMarkerSize(.9);display.SetMarkerColor(kBlack);display.SetLineColor(kBlack);display.SetLineWidth(1);
  TCanvas canvas("atlas_physics_canvas","atlas-root-plot-v2",800,600);canvas.SetCanvasSize(800,600);
  h.Draw(m.kind==SampleKind::Data?"AXIS":"HIST");
  if(m.kind==SampleKind::Data)display.Draw(event_counts?"PZ SAME":"P SAME");
  DrawOpenDataLabel(drawing);
  ExportPhysicsCanvas(canvas,h,base,drawing,(m.kind==SampleKind::Data || event_counts)?&display:nullptr);
}
}

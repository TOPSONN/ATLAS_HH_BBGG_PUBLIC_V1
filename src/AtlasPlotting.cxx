#include "AtlasPlotting.h"
#include <TCanvas.h>
#include <TFile.h>
#include <TDirectory.h>
#include <TGraphAsymmErrors.h>
#include <TGraph.h>
#include <TH1.h>
#include <TH1D.h>
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
#include <memory>
#include <sstream>
#include <stdexcept>
#include <vector>

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

namespace {
constexpr double hatched_confidence=.682689492137;
struct HatchedPlan {
  std::vector<int> eligible,excluded;
};
struct Box {double left,bottom,right,top;};
void preflight_stem(const std::filesystem::path& base) {
  for(const char* ext:{".pdf",".png",".root",".plot.json",".caption.md"})
    if(std::filesystem::exists(base.string()+ext))throw std::runtime_error("Plot output exists; refusing overwrite");
  if(!base.parent_path().empty() && std::filesystem::exists(base.parent_path()) && !std::filesystem::is_directory(base.parent_path()))
    throw std::invalid_argument("Plot parent must be a directory");
}
HatchedPlan plan_hatched(const TH1& h,const Metadata& m,const std::string& x,const std::string& y,bool event_counts,const RenderOptions& options) {
  ValidatePlotMetadata(m);
  if(m.kind==SampleKind::Simulation || !event_counts || m.weighting!="Raw unweighted counts")
    throw std::invalid_argument("Hatched intervals require raw unweighted DATA event counts or a synthetic counting fixture");
  if(std::string(h.ClassName())!="TH1D" || h.GetDimension()!=1 || h.GetEntries()<=0)
    throw std::invalid_argument("Hatched template requires a nonempty native TH1D");
  text_field(x,100);text_field(y,100);
  if(y.find("GeV")!=std::string::npos) {
    const auto slash=y.find('/');std::istringstream advertised(slash==std::string::npos?"":y.substr(slash+1));double width=0;std::string unit;
    if(!(advertised>>width>>unit) || unit!="GeV" || x.find("GeV")==std::string::npos)throw std::invalid_argument("Invalid declared bin-width axis label");
    for(int bin=1;bin<=h.GetNbinsX();++bin)if(std::abs(h.GetBinWidth(bin)-width)>1e-9*std::max(1.,width))
      throw std::invalid_argument("Declared bin-width normalization does not match raw bins");
  }
  for(int bin=0;bin<h.GetNcells();++bin) {
    const double n=h.GetBinContent(bin);
    if(!std::isfinite(n) || n<0 || std::abs(n-std::round(n))>1e-8)
      throw std::invalid_argument("Hatched raw counts must be nonnegative integers, including flows");
    if(h.GetSumw2N()>0 && std::abs(h.GetSumw2()->At(bin)-n)>1e-8*std::max(1.,n))
      throw std::invalid_argument("Weighted source errors cannot be declared raw unweighted Poisson counts");
  }
  const auto edge_match=[&](double value) {
    for(int bin=1;bin<=h.GetNbinsX()+1;++bin)
      if(std::abs(value-h.GetXaxis()->GetBinLowEdge(bin))<=1e-9*std::max(1.,std::abs(value)))return true;
    return false;
  };
  if(options.band_support) {
    const auto [low,high]=*options.band_support;
    if(!std::isfinite(low)||!std::isfinite(high)||low>=high||!edge_match(low)||!edge_match(high))
      throw std::invalid_argument("Display-only band support must align with native bin edges");
  }
  HatchedPlan plan;
  for(int bin=1;bin<=h.GetNbinsX();++bin) {
    const bool eligible=!options.band_support ||
      (h.GetXaxis()->GetBinLowEdge(bin)>=options.band_support->first-1e-9 &&
       h.GetXaxis()->GetBinUpEdge(bin)<=options.band_support->second+1e-9);
    if(eligible)plan.eligible.push_back(bin);
    else {
      if(h.GetBinContent(bin)!=0)throw std::invalid_argument("Band support would suppress a nonzero out-of-selection bin");
      plan.excluded.push_back(bin);
    }
  }
  if(plan.eligible.empty())throw std::invalid_argument("Display-only band support contains no complete native bins");
  return plan;
}
std::string indices_json(const std::vector<int>& bins) {
  std::ostringstream s;s<<'[';for(std::size_t i=0;i<bins.size();++i){if(i)s<<',';s<<bins[i];}s<<']';return s.str();
}
std::string box_json(const Box& b) {
  std::ostringstream s;s<<std::setprecision(17)<<'['<<b.left<<','<<b.bottom<<','<<b.right<<','<<b.top<<']';return s.str();
}
std::string visible_hatched_period(const Metadata& m) {
  return m.period=="2015 periodD"?"2015 Period D":m.period;
}
void draw_hatched_label(const Metadata& m) {
  TLatex t;t.SetNDC();t.SetTextFont(42);t.SetTextColor(kBlack);t.SetTextSize(.045);
  t.SetTextAlign(m.label_placement==LabelPlacement::UpperLeft?11:31);
  const double x=label_x(m,gPad->GetLeftMargin(),gPad->GetRightMargin());
  t.DrawLatex(x,m.label_y,m.kind==SampleKind::Synthetic?"Synthetic test":"ATLAS Open Data");
  t.SetTextSize(.04);
  if(m.kind==SampleKind::Synthetic) {
    t.DrawLatex(x,m.label_y-.055,"Numerical validation");
    t.DrawLatex(x,m.label_y-.110,m.unit_status=="PROVISIONAL"?"Provisional fixture":"Verified fixture");
  } else {
    std::ostringstream source;source<<"#sqrt{s} = "<<std::setprecision(6)<<*m.energy_tev<<" TeV, "<<visible_hatched_period(m);
    t.DrawLatex(x,m.label_y-.055,source.str().c_str());
    t.DrawLatex(x,m.label_y-.110,m.unit_status=="PROVISIONAL"?"Exploratory, provisional":"Exploratory, verified");
  }
}
void export_hatched(TCanvas& canvas,TH1& histogram,TGraphAsymmErrors& intervals,TGraphAsymmErrors& band,
                    const std::filesystem::path& base,const Metadata& metadata,const RenderOptions& options,
                    const HatchedPlan& plan,const Box& annotation,const Box& legend,double headroom) {
  ValidatePlotMetadata(metadata);preflight_stem(base);
  const std::string central_label=metadata.kind==SampleKind::Synthetic?"Synthetic counts (step histogram)":"Data (step histogram)";
  std::ostringstream details;details<<std::setprecision(17);
  details<<"Alternative HATCHED_STEP rendering of the same raw source counts; no fit, signal model, smoothing or systematics.\n"
         <<"Statistical counting intervals only; no systematics.\n"
         <<"Central line: native TH1D step histogram. Band: per-bin full-width rectangles, central "<<100.*hatched_confidence
         <<"% Garwood Poisson statistical intervals. Stored interval values are unchanged; the plotting frame clips physical y below zero.\n"
         <<"Full source histogram (including errors, entries, moments and flows) and all-bin zero-x-error interval graph are retained.\n";
  if(options.band_support)details<<"Display-only band support: ["<<options.band_support->first<<","<<options.band_support->second
    <<"); structural zero bins outside this support are omitted from the band, never from the source histogram or all-bin intervals.\n";
  details<<"Eligible source bin indices (one-based): "<<indices_json(plan.eligible)<<".\n"
         <<"Excluded structural zero source bin indices (one-based): "<<indices_json(plan.excluded)<<".\n";
  const auto caption=figure_caption(metadata,histogram,&intervals)+details.str();
  auto json=metadata_json(metadata,canvas,caption);
  const auto last=json.find_last_of('}');json.erase(last);
  std::ostringstream extension;extension<<std::setprecision(17);
  extension<<",\"plot_mode\":\"HATCHED_STEP\",\"source_object_name\":"<<quote(histogram.GetName())
    <<",\"source_intervals_object_name\":"<<quote(intervals.GetName())<<",\"band_object_name\":"<<quote(band.GetName())
    <<",\"confidence_level\":"<<hatched_confidence<<",\"statistical_model\":\"central Garwood Poisson\""
    <<",\"eligible_bin_indices\":"<<indices_json(plan.eligible)<<",\"structural_zero_exclusions\":"<<indices_json(plan.excluded)
    <<",\"band_support\":";
  if(options.band_support)extension<<"{\"low\":"<<options.band_support->first<<",\"high\":"<<options.band_support->second<<'}';
  else extension<<"null";
  extension<<",\"hatched_style\":{\"line_color\":"<<kAzure+2<<",\"line_width\":2,\"band_color\":"<<kAzure+1
    <<",\"band_fill_style\":3354,\"band_draw_option\":\"2 SAME\",\"line_draw_option\":\"HIST SAME\",\"legend_labels\":["
    <<quote(central_label)<<",\"68.27% Poisson statistical interval\"],\"legend_box\":"<<box_json(legend)
    <<",\"annotation_box\":"<<box_json(annotation)<<",\"legend_text_size\":0.032,\"y_headroom_factor\":"<<headroom
    <<",\"visible_period\":"<<quote(visible_hatched_period(metadata))<<",\"occupancy_guard\":\"full bin rectangles and central steps\"}}\n";
  json+=extension.str();
  if(!base.parent_path().empty())std::filesystem::create_directories(base.parent_path());
  canvas.Modified();canvas.Update();canvas.SaveAs((base.string()+".pdf").c_str());canvas.SaveAs((base.string()+".png").c_str());
  TDirectory::TContext preserve_directory;TFile root((base.string()+".root").c_str(),"CREATE");
  if(root.IsZombie() || histogram.Write(histogram.GetName())<=0 || intervals.Write(intervals.GetName())<=0 || band.Write(band.GetName())<=0)
    throw std::runtime_error("Cannot preserve hatched source and interval objects");
  TNamed native_metadata("atlas_plot_metadata",json.c_str());native_metadata.Write();
  TNamed native_caption("atlas_plot_caption",caption.c_str());native_caption.Write();root.Close();
  std::ofstream sidecar(base.string()+".plot.json");sidecar.exceptions(std::ios::badbit|std::ios::failbit);sidecar<<json;sidecar.close();
  std::ofstream caption_file(base.string()+".caption.md");caption_file.exceptions(std::ios::badbit|std::ios::failbit);caption_file<<caption;caption_file.close();
  for(const char* ext:{".pdf",".png",".root",".plot.json",".caption.md"})
    if(!std::filesystem::is_regular_file(base.string()+ext) || !std::filesystem::file_size(base.string()+ext))throw std::runtime_error("Missing hatched output");
}
void render_hatched(TH1& h,const std::filesystem::path& base,const Metadata& m,const std::string& x,const std::string& y,
                    const RenderOptions& options,const HatchedPlan& plan) {
  ApplyAtlasPlotStyle();ConfigurePhysicsAxes(h,x,y);h.SetMinimum(0);h.SetLineColor(kAzure+2);h.SetLineWidth(2);h.SetFillStyle(0);
  TGraphAsymmErrors intervals,band;intervals.SetName((std::string(h.GetName())+"_display").c_str());
  band.SetName((std::string(h.GetName())+"_hatched_band").c_str());
  constexpr double tail=(1.-hatched_confidence)/2.;double maximum=0;
  for(int bin=1;bin<=h.GetNbinsX();++bin) {
    const double n=h.GetBinContent(bin);
    const double low=n>0?n-ROOT::Math::gamma_quantile(tail,n,1.):0;
    const double high=ROOT::Math::gamma_quantile_c(tail,n+1,1.)-n;
    intervals.SetPoint(bin-1,h.GetBinCenter(bin),n);intervals.SetPointError(bin-1,0,0,low,high);
    if(std::binary_search(plan.eligible.begin(),plan.eligible.end(),bin)) {
      const int point=band.GetN();band.SetPoint(point,h.GetBinCenter(bin),n);
      band.SetPointError(point,h.GetBinWidth(bin)/2.,h.GetBinWidth(bin)/2.,low,high);maximum=std::max(maximum,n+high);
    }
    maximum=std::max(maximum,n);
  }
  band.SetFillColor(kAzure+1);band.SetFillStyle(3354);band.SetLineColor(kAzure+1);band.SetLineWidth(1);
  auto drawing=m;Box annotation{},legend{};double headroom=0;bool clear=false;
  const auto overlaps=[&](const Box& box,double xlow,double xhigh,double ylow,double yhigh) {
    return xhigh>=box.left-.012 && xlow<=box.right+.012 && yhigh>=box.bottom-.012 && ylow<=box.top+.012;
  };
  for(int increment=0;increment<=12 && !clear;++increment) {
    const double factor=1.12+.04*increment;
    for(const auto placement:{LabelPlacement::UpperLeft,LabelPlacement::UpperRight}) {
      const Box labels=placement==LabelPlacement::UpperLeft?Box{.185,m.label_y-.13,.68,m.label_y+.05}:Box{.44,m.label_y-.13,.935,m.label_y+.05};
      const Box entries=placement==LabelPlacement::UpperLeft?Box{.185,m.label_y-.275,.68,m.label_y-.16}:Box{.44,m.label_y-.275,.935,m.label_y-.16};
      bool occupied=false;
      const auto px=[&](double value){return .16+(value-h.GetXaxis()->GetXmin())/(h.GetXaxis()->GetXmax()-h.GetXaxis()->GetXmin())*.79;};
      const auto py=[&](double value){return .16+std::max(0.,value)/(maximum*factor)*.79;};
      for(int point=0;point<band.GetN() && !occupied;++point) {
        const double xlow=px(band.GetPointX(point)-band.GetErrorXlow(point)),xhigh=px(band.GetPointX(point)+band.GetErrorXhigh(point));
        const double ylow=py(band.GetPointY(point)-band.GetErrorYlow(point)),yhigh=py(band.GetPointY(point)+band.GetErrorYhigh(point));
        occupied=overlaps(labels,xlow,xhigh,ylow,yhigh)||overlaps(entries,xlow,xhigh,ylow,yhigh);
      }
      for(int bin=1;bin<=h.GetNbinsX() && !occupied;++bin) {
        const double level=py(h.GetBinContent(bin));
        occupied=overlaps(labels,px(h.GetXaxis()->GetBinLowEdge(bin)),px(h.GetXaxis()->GetBinUpEdge(bin)),level,level)||
                 overlaps(entries,px(h.GetXaxis()->GetBinLowEdge(bin)),px(h.GetXaxis()->GetBinUpEdge(bin)),level,level);
      }
      if(!occupied){drawing.label_placement=placement;annotation=labels;legend=entries;headroom=factor;clear=true;break;}
    }
  }
  if(!clear)throw std::runtime_error("No clear hatched annotation/legend corner; review plot-specific layout");
  h.SetMaximum(maximum*headroom);
  TCanvas canvas("atlas_hatched_canvas","atlas-root-plot-v2-hatched",800,600);canvas.SetCanvasSize(800,600);
  h.Draw("AXIS");band.Draw("2 SAME");h.Draw("HIST SAME");
  draw_hatched_label(drawing);TLegend key(legend.left,legend.bottom,legend.right,legend.top);ConfigureLegend(key);key.SetTextSize(.032);key.SetMargin(.12);
  key.AddEntry(&h,m.kind==SampleKind::Synthetic?"Synthetic counts (step histogram)":"Data (step histogram)","l");
  key.AddEntry(&band,"68.27% Poisson statistical interval","f");key.Draw();canvas.RedrawAxis();
  export_hatched(canvas,h,intervals,band,base,drawing,options,plan,annotation,legend,headroom);
}
}
void RenderHistogram(TH1& h,const std::filesystem::path& base,const Metadata& m,const std::string& x,const std::string& y,bool event_counts,const RenderOptions& options) {
  if(options.mode==PlotMode::ORIGINAL_DATA_POINTS) {
    if(options.band_support)throw std::invalid_argument("Band support applies only to the additive hatched mode");
    RenderHistogram(h,base,m,x,y,event_counts);return;
  }
  if(options.mode!=PlotMode::HATCHED_STEP && options.mode!=PlotMode::BOTH)throw std::invalid_argument("Invalid plot mode");
  const auto plan=plan_hatched(h,m,x,y,event_counts,options);
  const auto hatched_base=std::filesystem::path(base.string()+"_hatched");
  if(options.mode==PlotMode::BOTH)preflight_stem(base);
  preflight_stem(hatched_base);
  std::unique_ptr<TH1> hatched(static_cast<TH1*>(h.Clone()));hatched->SetDirectory(nullptr);
  if(options.mode==PlotMode::BOTH) {
    std::unique_ptr<TH1> original(static_cast<TH1*>(h.Clone()));original->SetDirectory(nullptr);
    RenderHistogram(*original,base,m,x,y,event_counts);
  }
  render_hatched(*hatched,hatched_base,m,x,y,options,plan);
}
}

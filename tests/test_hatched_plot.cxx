#include "AtlasPlotting.h"
#include <TH1D.h>
#include <TFile.h>
#include <TGraphAsymmErrors.h>
#include <TNamed.h>
#include <TROOT.h>
#include <array>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
struct Snapshot {
  std::vector<double> edges,contents,errors,sumw2;
  std::array<double,13> stats{};
  double entries,mean,stddev,effective,norm;
  int error_option;
  bool operator==(const Snapshot&) const=default;
};
Snapshot snapshot(const TH1D& h) {
  Snapshot s;
  for(int bin=1;bin<=h.GetNbinsX()+1;++bin)s.edges.push_back(h.GetXaxis()->GetBinLowEdge(bin));
  for(int bin=0;bin<h.GetNcells();++bin){s.contents.push_back(h.GetBinContent(bin));s.errors.push_back(h.GetBinError(bin));}
  for(int bin=0;bin<h.GetSumw2N();++bin)s.sumw2.push_back(h.GetSumw2()->At(bin));
  h.GetStats(s.stats.data());s.entries=h.GetEntries();s.mean=h.GetMean();s.stddev=h.GetStdDev();
  s.effective=h.GetEffectiveEntries();s.norm=h.GetNormFactor();s.error_option=h.GetBinErrorOption();return s;
}
std::string read(const std::filesystem::path& path) {
  std::ifstream input(path,std::ios::binary);if(!input)throw std::runtime_error("Missing test output");
  return std::string(std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>());
}
bool same_graph(const TGraphAsymmErrors& a,const TGraphAsymmErrors& b) {
  if(a.GetN()!=b.GetN())return false;
  for(int point=0;point<a.GetN();++point)
    if(a.GetPointX(point)!=b.GetPointX(point)||a.GetPointY(point)!=b.GetPointY(point)||
       a.GetErrorXlow(point)!=b.GetErrorXlow(point)||a.GetErrorXhigh(point)!=b.GetErrorXhigh(point)||
       a.GetErrorYlow(point)!=b.GetErrorYlow(point)||a.GetErrorYhigh(point)!=b.GetErrorYhigh(point))return false;
  return true;
}
template<class Object> Object* native_read(TFile& file,const char* name) {
  // ForceStyle is required for authoring, but would replace serialized colors
  // during ROOT deserialization. Inspect the actual saved attributes instead.
  struct RestoreForceStyle {
    bool previous=gROOT->GetForceStyle();
    RestoreForceStyle(){gROOT->ForceStyle(false);}
    ~RestoreForceStyle(){gROOT->ForceStyle(previous);}
  } preserve;
  return file.Get<Object>(name);
}
}
int main() {
  try {
    using namespace atlas::plotting;
    int cases=0;
    const auto check=[&](bool value,const char* message){++cases;if(!value)throw std::runtime_error(message);};
    const auto directory=std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR)/"hatched_test_outputs";
    const auto out=directory/std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    std::filesystem::create_directories(out);
    Metadata m;m.record="synthetic-fixture";m.period="Synthetic fixture";m.selection="Synthetic counting support test";
    m.unit_status="VERIFIED";m.inspected=8;m.accepted=6;m.end=8;
    TH1D h("hatched_support_fixture","",6,100,160);h.SetDirectory(nullptr);h.Sumw2();
    for(double value:{115.,115.,115.,115.,115.,115.,95.,165.})h.Fill(value);
    const auto source=snapshot(h);const int original_color=h.GetLineColor();const int original_fill=h.GetFillStyle();
    RenderOptions both;both.mode=PlotMode::BOTH;both.band_support={{110.,150.}};
    RenderHistogram(h,out/"hatched_support_fixture",m,"m_{#gamma#gamma} [GeV]","Events / 10 GeV",true,both);
    check(snapshot(h)==source,"BOTH changed source scientific values");
    check(h.GetLineColor()==original_color&&h.GetFillStyle()==original_fill,"BOTH changed input histogram appearance");
    for(const char* stem:{"hatched_support_fixture","hatched_support_fixture_hatched"})
      for(const char* ext:{".pdf",".png",".root",".plot.json",".caption.md"})
        check(std::filesystem::file_size(out/(std::string(stem)+ext))>0,"Required mode output absent");
    TFile original((out/"hatched_support_fixture.root").c_str(),"READ"),hatched((out/"hatched_support_fixture_hatched.root").c_str(),"READ");
    auto* hs=native_read<TH1D>(hatched,h.GetName());auto* os=native_read<TH1D>(original,h.GetName());
    check(hs&&os&&snapshot(*hs)==source&&snapshot(*os)==source,"Native source bins/errors/moments/flows changed");
    check(hs->GetLineColor()==kAzure+2&&hs->GetLineWidth()==2,"Hatched central histogram style incorrect");
    auto* old_errors=native_read<TGraphAsymmErrors>(original,"hatched_support_fixture_display");
    auto* intervals=native_read<TGraphAsymmErrors>(hatched,"hatched_support_fixture_display");
    auto* band=native_read<TGraphAsymmErrors>(hatched,"hatched_support_fixture_hatched_band");
    check(old_errors&&intervals&&same_graph(*old_errors,*intervals),"Original source interval values changed");
    check(intervals->GetN()==6&&band&&band->GetN()==4,"Source or eligible interval count incorrect");
    check(band->GetFillColor()==kAzure+1&&band->GetFillStyle()==3354,"Hatched fill style incorrect");
    for(int point=0;point<band->GetN();++point) {
      const int source_point=point+1;
      check(band->GetPointX(point)==intervals->GetPointX(source_point)&&band->GetPointY(point)==intervals->GetPointY(source_point),"Band interpolated or changed central values");
      check(band->GetErrorYlow(point)==intervals->GetErrorYlow(source_point)&&band->GetErrorYhigh(point)==intervals->GetErrorYhigh(source_point),"Band changed statistical errors");
      check(band->GetErrorXlow(point)==5&&band->GetErrorXhigh(point)==5,"Band does not cover exact full bin width");
    }
    check(band->GetPointY(1)==0&&band->GetErrorYhigh(1)>0&&band->GetErrorYlow(1)==0,"Eligible zero-count upper interval lost");
    check(intervals->GetPointY(0)==0&&intervals->GetErrorYhigh(0)>0&&intervals->GetErrorXhigh(0)==0,"Excluded structural zero source interval lost");
    const auto metadata=read(out/"hatched_support_fixture_hatched.plot.json");
    check(metadata.find("\"plot_mode\":\"HATCHED_STEP\"")!=std::string::npos&&metadata.find("\"eligible_bin_indices\":[2,3,4,5]")!=std::string::npos&&
          metadata.find("\"structural_zero_exclusions\":[1,6]")!=std::string::npos,"Band support metadata incorrect");
    check(hatched.Get<TNamed>("atlas_plot_metadata")&&metadata==std::string(hatched.Get<TNamed>("atlas_plot_metadata")->GetTitle()),"Native and sidecar metadata disagree");
    check(hatched.Get<TNamed>("atlas_plot_caption")&&read(out/"hatched_support_fixture_hatched.caption.md")==std::string(hatched.Get<TNamed>("atlas_plot_caption")->GetTitle()),"Caption not preserved in ROOT");
    check(read(out/"hatched_support_fixture.plot.json").find("plot_mode")==std::string::npos,"Original metadata acquired alternative fields");
    // Default options must delegate to the old overload without alternative metadata.
    TH1D legacy=h;legacy.SetDirectory(nullptr);TH1D defaults=h;defaults.SetDirectory(nullptr);
    const auto legacy_base=out/"legacy_control"/h.GetName(),default_base=out/"default_control"/h.GetName();
    RenderHistogram(legacy,legacy_base,m,"m_{#gamma#gamma} [GeV]","Events / 10 GeV",true);
    RenderHistogram(defaults,default_base,m,"m_{#gamma#gamma} [GeV]","Events / 10 GeV",true,RenderOptions{});
    check(read(legacy_base.string()+".plot.json")==read(default_base.string()+".plot.json"),"Default overload changed legacy metadata");
    check(read(legacy_base.string()+".png")==read(default_base.string()+".png"),"Default overload changed legacy rendering");
    const auto rejects=[&](TH1D& candidate,const Metadata& meta,const RenderOptions& options,bool events,const char* stem) {
      bool refused=false;try{RenderHistogram(candidate,out/stem,meta,"m_{#gamma#gamma} [GeV]","Events / 10 GeV",events,options);}catch(const std::exception&){refused=true;}
      check(refused&&!std::filesystem::exists(out/(std::string(stem)+".pdf"))&&!std::filesystem::exists(out/(std::string(stem)+"_hatched.pdf")),"Invalid alternative wrote outputs");
    };
    auto mc=m;mc.kind=SampleKind::Simulation;mc.energy_tev=13.;rejects(h,mc,both,true,"reject_mc");
    rejects(h,m,both,false,"reject_object_counts");
    auto weighted=m;weighted.weighting="Weighted counts";rejects(h,weighted,both,true,"reject_weighted_metadata");
    auto mismatch=both;mismatch.band_support={{111.,150.}};rejects(h,m,mismatch,true,"reject_unaligned_support");
    auto no_bins=both;no_bins.band_support={{90.,100.}};rejects(h,m,no_bins,true,"reject_outside_support");
    TH1D outside=h;outside.SetDirectory(nullptr);outside.Fill(105.);rejects(outside,m,both,true,"reject_nonzero_excluded");
    TH1D boundary=h;boundary.SetDirectory(nullptr);boundary.Fill(150.);rejects(boundary,m,both,true,"reject_nonzero_upper_boundary");
    TH1D weighted_hist=h;weighted_hist.SetDirectory(nullptr);weighted_hist.Fill(115.,2.);rejects(weighted_hist,m,both,true,"reject_weighted_source");
    auto unknown=both;unknown.mode=static_cast<PlotMode>(99);rejects(h,m,unknown,true,"reject_unknown_mode");
    auto misplaced=RenderOptions{};misplaced.band_support={{110.,150.}};rejects(h,m,misplaced,true,"reject_original_support");
    const auto blocked=out/"preflight_control";
    {std::ofstream file(blocked.string()+"_hatched.caption.md");file<<"sentinel";}
    rejects(h,m,both,true,"preflight_control");
    check(read(blocked.string()+"_hatched.caption.md")=="sentinel"&&!std::filesystem::exists(blocked.string()+".plot.json"),"BOTH preflight overwrote or partially exported");
    RenderOptions only;only.mode=PlotMode::HATCHED_STEP;
    RenderHistogram(h,out/"all_bin_fixture",m,"m_{#gamma#gamma} [GeV]","Events / 10 GeV",true,only);
    TFile all((out/"all_bin_fixture_hatched.root").c_str(),"READ");
    auto* all_band=native_read<TGraphAsymmErrors>(all,"hatched_support_fixture_hatched_band");
    check(all_band&&all_band->GetN()==6&&!std::filesystem::exists(out/"all_bin_fixture.pdf"),"HATCHED_STEP/null support output scope incorrect");
    check(snapshot(h)==source&&h.GetLineColor()==original_color,"HATCHED_STEP mutated input");
    // Record only a fully successful run; retained failed runs remain evidence.
    std::ofstream marker(directory/"current_fixture_path.txt");marker.exceptions(std::ios::badbit|std::ios::failbit);marker<<out.string()<<'\n';marker.close();
    std::cout<<"PASS additive hatched rendering contract cases="<<cases<<"; output="<<out<<'\n';
  }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}

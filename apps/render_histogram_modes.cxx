#include "AtlasPlotting.h"
#include <TFile.h>
#include <TH1D.h>
#include <TNamed.h>
#include <iostream>
#include <memory>
#include <stdexcept>

int main(int argc,char** argv) {
  try {
    if(argc!=17)throw std::invalid_argument(
      "Usage: render_histogram_modes source.root object new_output mode record period selection units "
      "inspected accepted start end energy_tev support_low|NONE support_high|NONE PINNED_NATIVE_PLOT_SOURCE");
    const std::filesystem::path source_path(argv[1]),out(argv[3]);
    if(!std::filesystem::is_regular_file(source_path) || std::string(argv[1]).find("://")!=std::string::npos)
      throw std::invalid_argument("Local native source histogram required; no event reader is used");
    if(std::filesystem::exists(out))throw std::runtime_error("Output exists; refusing overwrite");
    if(std::string(argv[16])!="PINNED_NATIVE_PLOT_SOURCE")throw std::invalid_argument("Explicit pinned-source declaration required");
    atlas::plotting::RenderOptions options;
    const std::string mode(argv[4]);
    if(mode=="ORIGINAL_DATA_POINTS")options.mode=atlas::plotting::PlotMode::ORIGINAL_DATA_POINTS;
    else if(mode=="HATCHED_STEP")options.mode=atlas::plotting::PlotMode::HATCHED_STEP;
    else if(mode=="BOTH")options.mode=atlas::plotting::PlotMode::BOTH;
    else throw std::invalid_argument("Unknown plotting mode");
    if(std::string(argv[14])!="NONE" || std::string(argv[15])!="NONE") {
      if(std::string(argv[14])=="NONE" || std::string(argv[15])=="NONE")throw std::invalid_argument("Both support bounds are required");
      options.band_support=std::pair{std::stod(argv[14]),std::stod(argv[15])};
    }
    atlas::plotting::Metadata m;m.kind=atlas::plotting::SampleKind::Data;
    m.record=argv[5];m.period=argv[6];m.selection=argv[7];m.unit_status=argv[8];
    m.inspected=std::stoull(argv[9]);m.accepted=std::stoull(argv[10]);
    m.start=std::stoull(argv[11]);m.end=std::stoull(argv[12]);m.energy_tev=std::stod(argv[13]);
    atlas::plotting::ValidatePlotMetadata(m);
    TFile source(source_path.c_str(),"READ");
    if(source.IsZombie() || !source.Get<TNamed>("atlas_plot_metadata"))throw std::runtime_error("Audited source metadata missing");
    auto* h=source.Get<TH1D>(argv[2]);
    if(!h || h->GetDimension()!=1)throw std::runtime_error("Named native TH1D source missing");
    std::unique_ptr<TH1D> histogram(static_cast<TH1D*>(h->Clone()));histogram->SetDirectory(nullptr);
    const std::string x=histogram->GetXaxis()->GetTitle(),y=histogram->GetYaxis()->GetTitle();
    source.Close();
    atlas::plotting::RenderHistogram(*histogram,out/histogram->GetName(),m,x,y,true,options);
    std::cout<<"PASS mode="<<mode<<" source="<<histogram->GetName()
             <<" bins="<<histogram->GetNbinsX()<<" range="<<histogram->GetXaxis()->GetXmin()
             <<':'<<histogram->GetXaxis()->GetXmax()<<" entries="<<histogram->GetEntries()
             <<" new collision entries=0\n";
  }catch(const std::exception& error){std::cerr<<"FAIL: "<<error.what()<<'\n';return 1;}
}

#include "AtlasPlotting.h"
#include <TFile.h>
#include <TH1D.h>
#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
int main(int argc,char** argv) {
  try {
    if(argc!=9)throw std::invalid_argument("Usage: render_phase2_histograms source.root new_output inspected accepted start end VERIFIED|PROVISIONAL PINNED_RECORD_93915");
    if(!std::filesystem::is_regular_file(argv[1]) || std::string(argv[1]).find("://")!=std::string::npos)throw std::invalid_argument("Local native histogram file required");
    const std::filesystem::path out(argv[2]);if(std::filesystem::exists(out))throw std::runtime_error("Output exists");
    atlas::plotting::Metadata m;m.kind=atlas::plotting::SampleKind::Data;m.record="93915";m.period="2015 periodD";m.energy_tev=13.;
    m.inspected=std::stoull(argv[3]);m.accepted=std::stoull(argv[4]);m.start=std::stoull(argv[5]);m.end=std::stoull(argv[6]);m.unit_status=argv[7];
    // Explicit source hash is checked by the public reproduction wrapper.
    if(std::string(argv[8])!="PINNED_RECORD_93915")throw std::invalid_argument("Explicit pinned-source declaration required");
    m.selection="Valid kinematics";atlas::plotting::ValidatePlotMetadata(m);
    TFile source(argv[1],"READ");if(source.IsZombie())throw std::runtime_error("Invalid source ROOT file");
    const std::array<const char*,7> names{"photon_pt","photon_eta","jet_pt","jet_eta","m_gg","m_jj","deltaR_gg"};
    const std::array<const char*,7> x{"p_{T}^{#gamma} [GeV]","#eta^{#gamma}","p_{T}^{jet} [GeV]","#eta^{jet}","m_{#gamma#gamma} [GeV]","m_{jj} [GeV]","#Delta R_{#gamma#gamma} (dimensionless)"};
    const std::array<const char*,7> y{"Objects / 5 GeV","Objects / bin","Objects / 5 GeV","Objects / bin","Events / 5 GeV","Events / 10 GeV","Events / bin"};
    const std::array<const char*,7> selection{"Valid kinematics; all photon objects","Valid kinematics; all photon objects","Valid kinematics; all inclusive jet objects","Valid kinematics; all inclusive jet objects","Valid kinematics; leading photon pair","Valid kinematics; leading inclusive jet pair","Valid kinematics; leading photon pair"};
    std::array<std::unique_ptr<TH1D>,7> hist;
    for(std::size_t i=0;i<names.size();++i) {
      auto* h=source.Get<TH1D>(names[i]);if(!h)throw std::runtime_error("Missing native source histogram; no data fabrication permitted");
      hist[i].reset(static_cast<TH1D*>(h->Clone()));hist[i]->SetDirectory(nullptr);
    }
    source.Close();std::filesystem::create_directories(out);
    const auto valid_events=m.accepted;
    for(std::size_t i=0;i<names.size();++i) {m.selection=selection[i];m.accepted=i==5?static_cast<std::uint64_t>(hist[i]->GetEntries()):valid_events;atlas::plotting::RenderHistogram(*hist[i],out/names[i],m,x[i],y[i],i>=4);}
    std::cout<<"PASS: 7 native histogram PDFs/PNGs/ROOT objects; no event reads\n";
  }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}

#include "AtlasPlotting.h"
#include <TROOT.h>
#include <TStyle.h>
#include <TH1D.h>
#include <TLegend.h>
#include <cmath>
#include <iostream>
#include <stdexcept>
int main() {
  try {
    int cases=0;auto check=[&](bool value){++cases;if(!value)throw std::runtime_error("Style/metadata contract failure");};
    const auto close=[](double actual,double expected){return std::abs(actual-expected)<1e-6;};
    atlas::plotting::ApplyAtlasPlotStyle();
    check(std::string(gStyle->GetName())=="ATLAS");check(gStyle->GetOptTitle()==0&&gStyle->GetOptStat()==0&&gStyle->GetOptFit()==0);
    check(gStyle->GetCanvasColor()==0&&gStyle->GetPadColor()==0);check(gStyle->GetTextFont()==42);
    check(gStyle->GetPadTickX()==1&&gStyle->GetPadTickY()==1);check(gStyle->GetLabelFont("X")==42&&gStyle->GetTitleFont("Y")==42);
    check(close(gStyle->GetPadLeftMargin(),.16)&&close(gStyle->GetPadBottomMargin(),.16));
    check(close(gStyle->GetPadRightMargin(),.05)&&close(gStyle->GetPadTopMargin(),.05));
    check(close(gStyle->GetTextSize(),.04));check(gStyle->GetMarkerStyle()==20&&close(gStyle->GetMarkerSize(),.9));
    TH1D h("style_fixture","unwanted title",4,0,4);h.SetDirectory(nullptr);
    atlas::plotting::ConfigurePhysicsAxes(h,"m_{#gamma#gamma} [GeV]","Events / 1 GeV");
    check(std::string(h.GetTitle()).empty());check(h.GetXaxis()->GetTitleFont()==42&&h.GetYaxis()->GetLabelColor()==kBlack);
    check(close(h.GetXaxis()->GetTitleSize(),.05)&&close(h.GetYaxis()->GetTitleSize(),.05));
    check(close(h.GetXaxis()->GetLabelSize(),.045)&&close(h.GetYaxis()->GetLabelSize(),.045));
    TLegend legend;atlas::plotting::ConfigureLegend(legend);check(legend.GetTextFont()==42&&legend.GetBorderSize()==0&&legend.GetFillStyle()==0);
    check(close(legend.GetTextSize(),.04));
    atlas::plotting::Metadata good;good.record="synthetic-fixture";good.period="Synthetic fixture";good.selection="Boundary test";
    good.unit_status="VERIFIED";good.inspected=3;good.accepted=2;good.end=3;atlas::plotting::ValidatePlotMetadata(good);check(true);
    check(good.label_placement==atlas::plotting::LabelPlacement::UpperRight&&close(good.label_y,.88));
    auto left=good;left.label_placement=atlas::plotting::LabelPlacement::UpperLeft;atlas::plotting::ValidatePlotMetadata(left);check(true);
    for(int mutation=0;mutation<9;++mutation) {
      auto m=good;
      switch(mutation) {
        case 0:m.record="";break;case 1:m.selection="";break;case 2:m.unit_status="UNKNOWN";break;
        case 3:m.accepted=4;break;case 4:m.end=4;break;case 5:m.weighting="Normalized";break;
        case 6:m.selection="ATLAS Preliminary";break;case 7:m.kind=atlas::plotting::SampleKind::Data;break;
        case 8:m.luminosity_pb=308000;break;
      }
      bool rejected=false;try{atlas::plotting::ValidatePlotMetadata(m);}catch(const std::invalid_argument&){rejected=true;}check(rejected);
    }
    auto data=good;data.kind=atlas::plotting::SampleKind::Data;data.energy_tev=13.;data.luminosity_pb=100;
    bool rejected=false;try{atlas::plotting::ValidatePlotMetadata(data);}catch(const std::invalid_argument&){rejected=true;}check(rejected);
    std::cout<<"PASS ATLAS style and metadata cases="<<cases<<'\n';
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}

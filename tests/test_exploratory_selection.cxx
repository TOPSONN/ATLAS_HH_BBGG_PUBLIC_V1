#include "AtlasExploratorySelection.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace atlas::selection;
namespace {
int cases=0;
void check(bool value,const char* name) {++cases;if(!value)throw std::runtime_error(name);}
Event good() { Event e;e.source_valid=true;e.photons=2;e.jets=2;e.photon_pt={50,30};e.photon_eta={0,1};e.jet_pt={40,30};e.jet_eta={0,1};e.mgg=125;e.mjj=100;return e; }
}
int main(int argc,char** argv) {
  try {
    if(argc!=2)throw std::runtime_error("Test configuration required");
    const auto c=read_config(argv[1]); auto e=good();
    check(c.leading_photon_pt==35&&c.subleading_photon_pt==25,"Declared defaults");
    auto result=evaluate(e,c);check(std::all_of(result.begin(),result.end(),[](bool b){return b;}),"Baseline selection");
    e.photon_pt[0]=35;check(!leading_photon_pt(e,c),"Leading photon exact threshold rejects");
    e.photon_pt[0]=std::nextafter(35.,100.);check(leading_photon_pt(e,c),"Leading photon just above threshold");
    e=good();e.photon_pt[1]=25;check(!subleading_photon_pt(e,c),"Subleading exact threshold rejects");
    e.photon_pt[1]=std::nextafter(25.,100.);check(subleading_photon_pt(e,c),"Subleading just above threshold");
    for(double eta:{2.37,-2.37}) {e=good();e.photon_eta[0]=eta;check(!photon_acceptance(e,c),"Photon eta exact boundary rejects");}
    for(double eta:{1.37,-1.37,1.52,-1.52}) {e=good();e.photon_eta[0]=eta;check(photon_acceptance(e,c),"Open crack boundaries accepted");}
    for(double eta:{1.4,-1.4}) {e=good();e.photon_eta[0]=eta;check(!photon_acceptance(e,c),"Crack interior excluded");}
    for(double mass:{105.,160.}) {e=good();e.mgg=mass;check(diphoton_window(e,c),"Inclusive mass boundary accepted");}
    e.mgg=std::nextafter(105.,0.);check(!diphoton_window(e,c),"Mass just below window");
    e.mgg=std::nextafter(160.,200.);check(!diphoton_window(e,c),"Mass just above window");
    for(int index:{0,1}) {e=good();e.jet_pt[index]=25;check(!jet_pt(e,c),"Jet exact pT rejects");}
    for(double eta:{2.5,-2.5}) {e=good();e.jet_eta[1]=eta;check(!jet_acceptance(e,c),"Jet exact eta rejects");}
    e=good();e.photons=1;check(!photon_multiplicity(e)&&!evaluate(e,c)[2],"Photon multiplicity");
    e=good();e.jets=1;check(!jet_multiplicity(e)&&!evaluate(e,c)[7],"Jet multiplicity");
    e=good();e.source_valid=false;check(!valid_kinematics(e)&&!evaluate(e,c)[9],"Invalid source never accepted");
    e=good();e.photon_pt[0]=std::numeric_limits<double>::quiet_NaN();check(!valid_kinematics(e),"NaN quarantined");
    e=good();e.jet_eta[0]=std::numeric_limits<double>::infinity();check(!valid_kinematics(e),"Infinity quarantined");
    e=good();e.mgg=-1;check(!valid_kinematics(e),"Negative mass");
    e=good();e.photon_pt={30,50};check(!valid_kinematics(e),"Nonordered photon cache rejected");
    e=good();e.jet_pt={30,40};check(!valid_kinematics(e),"Nonordered jet cache rejected");
    e=good();e.jets=0;e.jet_pt={NAN,NAN};e.jet_eta={NAN,NAN};e.mjj=NAN;check(valid_kinematics(e)&&!evaluate(e,c)[7],"Absent jets are multiplicity failure, not fabricated kinematics");
    e=good();Config changed=c;changed.leading_photon_pt=60;check(!leading_photon_pt(e,changed),"Configurable threshold");
    check(evaluate(e,c)==evaluate(e,c),"Deterministic predicate evaluation");
    std::ifstream input(argv[1]);std::string original((std::istreambuf_iterator<char>(input)),{});
    const auto path=std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR)/"selection_bad.ini";
    for(const auto& content:{original+"btag_wp=70\n",original+"definition_version=duplicate\n",std::string("definition_version=incomplete\n"),original+"event_weight=2\n"}) {
      {std::ofstream out(path);out<<content;}bool rejected=false;try{read_config(path);}catch(...){rejected=true;}check(rejected,"Unknown/duplicate/incomplete configuration rejected");
    }
    std::cout << "PASS selection boundary/configuration cases=" << cases << '\n';return 0;
  }catch(const std::exception& e){std::cerr << "FAIL: " << e.what() << '\n';return 1;}
}

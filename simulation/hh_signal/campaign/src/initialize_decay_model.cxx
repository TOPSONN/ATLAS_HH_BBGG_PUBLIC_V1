#include <Pythia8/Pythia.h>
#include "Json.hxx"
#include <fstream>
#include <iostream>
int main(int argc,char**argv) {
  try {
    if(argc!=4) throw std::runtime_error("expected xml, baseline, fresh output");
    Pythia8::Pythia p(argv[1],false);
    if(!p.readFile(argv[2]))throw std::runtime_error("settings read failed");
    for(const char*s:{"SLHA:readFrom = 0","Beams:frameType = 1","Beams:eCM = 13000",
        "HiggsSM:gg2H = on","25:m0 = 125","6:m0 = 173","24:m0 = 80.419",
        "25:onMode = on"})if(!p.readString(s))throw std::runtime_error("bad model setting");
    if(!p.init())throw std::runtime_error("zero-event model initialization failed");
    auto h=p.particleData.particleDataEntryPtr(25);double bb=0,gg=0;
    std::ofstream out(argv[3]);out<<"{\"status\":\"PASS_ACTUAL_INITIALIZED_MODEL_TABLE_ZERO_EVENTS\",\"scope\":\"MODEL_BR_ONLY\",\"events_generated\":0,\"H_mass_gev\":125,\"W_mass_gev\":80.419,\"top_mass_gev\":173,\"bottom_kinematic_mass_gev\":4.8,\"H_total_width_gev\":"<<atlas_hh::real(h->mWidth())<<",\"channels\":[";
    for(int i=0;i<h->sizeChannels();++i){auto&c=h->channel(i);if(i)out<<',';
      if(c.multiplicity()==2&&c.product(0)==5&&c.product(1)==-5)bb=c.bRatio();
      if(c.multiplicity()==2&&c.product(0)==22&&c.product(1)==22)gg=c.bRatio();
      if(c.onShellWidth()>0&&std::abs(c.onShellWidth()/h->mWidth()-c.bRatio())>2e-12)throw std::runtime_error("partial/total model BR mismatch");
      out<<"{\"BR\":"<<atlas_hh::real(c.bRatio())<<",\"partial_width_gev\":"<<atlas_hh::real(c.onShellWidth())<<",\"products\":[";
      for(int j=0;j<c.multiplicity();++j){if(j)out<<',';out<<c.product(j);}out<<"]}";
    }
    if(!(bb>0&&gg>0&&bb+gg<1))throw std::runtime_error("missing physical model BR");
    out<<"],\"BR_H_bb\":"<<atlas_hh::real(bb)<<",\"BR_H_gammagamma\":"<<atlas_hh::real(gg)
       <<",\"mixed_decay_factor\":"<<atlas_hh::real(2*bb*gg)<<",\"forced_sampling_probability\":1,\"assignment_probability\":0.5,\"external_reference_BR\":null,\"adopted_physical_BR\":null}\n";
    if(!out.good())throw std::runtime_error("model receipt write failed");return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}
}

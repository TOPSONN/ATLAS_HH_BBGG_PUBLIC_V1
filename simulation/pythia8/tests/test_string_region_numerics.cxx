// Reproduce an observed upstream numerical failure with pure StringRegion math.
// No Pythia event generation, showers, hadronization, output repair or QA waiver.
// Inputs: stage_b_bbgg_100, source event 54, Pythia remnant entries 296/297.
#include "Pythia8/FragmentationSystems.h"
#include <iomanip>
#include <iostream>

int main(){
  const Pythia8::Vec4 first(0,0,-1754.7496081116615,1754.7496391417294);
  const Pythia8::Vec4 second(0,0,-2060.729802265181,2060.7298629233023);
  Pythia8::StringRegion region;
  region.setUp(first,second,0,0);
  std::cout<<std::setprecision(17)<<"{\"scope\":\"NO_EVENTS_PURE_UPSTREAM_STRING_REGION_API\","
    <<"\"source_event_index\":54,\"observed_upstream_degenerate_case\":true,"
    <<"\"is_empty\":"<<(region.isEmpty?"true":"false")
    <<",\"p_positive_energy_gev\":"<<region.pPos.e()<<",\"p_negative_energy_gev\":"<<region.pNeg.e()
    <<",\"transverse_eX_norm_squared\":"<<region.eX.pAbs2()
    <<",\"transverse_eY_norm_squared\":"<<region.eY.pAbs2()<<"}\n";
  if(!region.isEmpty||region.pNeg.e()>=0||region.eX.pAbs2()!=0||region.eY.pAbs2()!=0){
    std::cerr<<"Observed upstream numerical case did not reproduce on this build\n";return 1;}
  return 0;
}

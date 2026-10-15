#include "SignalInterface.hxx"
#include <type_traits>
// Compiled and executed method checks only. No Pythia instance, init(), next(),
// HepMC file, Delphes processing, ROOT tree, or manufactured signal events.
int main() {
  using namespace hh_signal;
  static_assert(__cplusplus>=202002L);
  static_assert(std::is_base_of_v<HepMC3::Reader,HepMC3::ReaderAscii>);
  if(pairMass(std::nullopt,std::nullopt)) return 1;
  if(pairMass(P4(3.,0.,4.,5.),P4(-3.,0.,-4.,5.))!=10.) return 2;
  bool rejected=false;
  try { (void)pairMass(P4(10.,0.,0.,1.),P4(10.,0.,0.,1.)); }
  catch(const std::runtime_error&) {rejected=true;}
  if(!rejected) return 3;
  return 0;
}

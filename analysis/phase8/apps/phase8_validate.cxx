#include "Phase8Histogram.hxx"
#include <iostream>
int main(int argc,char**argv){try{atlas_hh::phase8::demand(argc==2,"existing Phase8 output directory required");std::cout<<atlas_hh::phase8::validate_histograms(argv[1]).dump(2)<<'\n';return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}

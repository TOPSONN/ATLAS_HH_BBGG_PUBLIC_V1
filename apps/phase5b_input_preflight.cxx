#include "AtlasInputPreflight.h"
#include <charconv>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc,char** argv) {
  try {
    if(argc!=5)throw std::runtime_error("Usage: phase5b_input_preflight local.root FRESH_output expected_DSID SYNTHETIC_FIXTURE|PHYSICAL_CANDIDATE");
    std::uint32_t dsid=0;const std::string raw=argv[3];
    const auto parsed=std::from_chars(raw.data(),raw.data()+raw.size(),dsid);
    if(parsed.ec!=std::errc{} || parsed.ptr!=raw.data()+raw.size() || dsid==0)
      throw std::runtime_error("Expected DSID must be a positive UInt_t integer");
    const std::string kind=argv[4];
    if(kind!="SYNTHETIC_FIXTURE" && kind!="PHYSICAL_CANDIDATE")throw std::runtime_error("Explicit evidence scope required");
    const auto result=atlas::input_preflight::inspect_local_file(argv[1],dsid,
      kind=="SYNTHETIC_FIXTURE"?atlas::input_preflight::EvidenceKind::SyntheticFixture:atlas::input_preflight::EvidenceKind::PhysicalCandidate);
    atlas::input_preflight::write_new_outputs(result,argv[2]);
    std::cout<<"PASS metadata-only "<<kind<<"; analysis_entries="<<result.analysis_entries
      <<"; event_entries_read=0; actual DSID/units/provenance NOT_EVALUATED\n";
  }catch(const std::exception& error){std::cerr<<"FAIL: "<<error.what()<<'\n';return 1;}
}

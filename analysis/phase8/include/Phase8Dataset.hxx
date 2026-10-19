#pragma once
#include "Phase8Provenance.hxx"
namespace atlas_hh::phase8 {
struct Dataset {
 std::string id,process,truth_format,scope;
 fs::path root,index,truth,card;
 std::string root_hash,index_hash,truth_hash,card_hash;
 long entries=0,original=0;bool full=false;double br=1;
 std::vector<long> expected;
};
std::vector<Dataset> datasets(const Json& manifest);
void verify_dataset_files(const Dataset& d);
void verify_selection(const Json& j);
}

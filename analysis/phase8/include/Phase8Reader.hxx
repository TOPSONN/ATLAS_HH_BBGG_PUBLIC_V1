#pragma once
#include "Phase8TruthMatching.hxx"
#include <functional>
namespace atlas_hh::phase8 {
Json schema_audit(const Dataset& d);
Json read_dataset(const Dataset& d,const std::function<void(const Event&)>& consume);
}

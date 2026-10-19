#pragma once
#include "Phase8Event.hxx"
namespace atlas_hh::phase8 {
void reconstruct(Event& e,std::optional<double> ht);
double delta_phi(const P4& a,const P4& b);
Json descriptive(const std::vector<double>& values,long total);
}

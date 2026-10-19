#pragma once
#include "Phase8Event.hxx"
#include <TH1D.h>
#include <TH2D.h>
#include <TFile.h>
namespace atlas_hh::phase8 {
struct HistogramDefinition{std::vector<double> edges;std::string unit;};
using Definitions=std::map<std::string,HistogramDefinition>;
Definitions histogram_definitions(const Json& j);
class HistogramBook {
 struct One{std::unique_ptr<TH1D>raw,source;long missing=0,invalid=0;long double absw=0;};
 struct Two{std::unique_ptr<TH2D>raw,source;long missing=0;long double absw=0;};
 Dataset dataset;Definitions defs;std::map<std::string,One> one;std::map<std::string,Two>two;
 public: HistogramBook(const Dataset& d,const Definitions& definitions);
 void fill(const Event& e);
 Json write(TFile& root,std::ostream& csv,atlas_hh::Sha256& digest);
};
Json validate_histograms(const fs::path& output);
}

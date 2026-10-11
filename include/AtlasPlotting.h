#pragma once
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <utility>
class TH1;
class TCanvas;
class TLegend;
class TObject;

namespace atlas::plotting {
enum class SampleKind { Data, Simulation, Synthetic };
enum class LabelPlacement { UpperLeft, UpperRight };
enum class PlotMode { ORIGINAL_DATA_POINTS, HATCHED_STEP, BOTH };
struct RenderOptions {
  PlotMode mode=PlotMode::ORIGINAL_DATA_POINTS;
  // Display-only band support. Bounds must coincide with source bin edges;
  // excluded bins must be structural zeros. The full source histogram and
  // all-bin 68.2689492137% Garwood intervals are always retained.
  std::optional<std::pair<double,double>> band_support;
};
struct Metadata {
  SampleKind kind=SampleKind::Synthetic;
  std::string record,period,selection,unit_status,weighting="Raw unweighted counts";
  std::uint64_t inspected=0,accepted=0,start=0,end=0;
  std::optional<double> energy_tev,luminosity_pb;
  bool luminosity_validated=false;
  std::string luminosity_evidence;
  LabelPlacement label_placement=LabelPlacement::UpperRight;
  double label_y=.88;
};
void ApplyAtlasPlotStyle();
void ValidatePlotMetadata(const Metadata&);
void DrawOpenDataLabel(const Metadata&);
void ConfigurePhysicsAxes(TH1&,const std::string& x,const std::string& y,const std::string& z="");
void ConfigureLegend(TLegend&);
void ExportPhysicsCanvas(TCanvas&,TObject&,const std::filesystem::path& base,const Metadata&,TObject* display=nullptr);
// Data event counts: central 68.27% Garwood intervals. Multiple-object counts:
// markers only; their within-event correlations are not approximated as Poisson.
void RenderHistogram(TH1&,const std::filesystem::path& base,const Metadata&,
                     const std::string& x,const std::string& y,bool event_counts);
// Additive alternative; the original overload and its metadata remain intact.
// HATCHED_STEP writes base_hatched. BOTH preflights both stems before export.
void RenderHistogram(TH1&,const std::filesystem::path& base,const Metadata&,
                     const std::string& x,const std::string& y,bool event_counts,
                     const RenderOptions&);
}

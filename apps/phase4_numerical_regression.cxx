#include "AtlasLocalEvents.h"
#include "AtlasMCEvents.h"
#include "AtlasExploratorySelection.h"
#include <TFile.h>
#include <TH1D.h>
#include <TNamed.h>
#include <TROOT.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <numbers>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

// Additive evidence generator: no canvases, fits, normalization, or input edits.
// Legacy leading_pair below is the exact algebra at d823593b42889592897263819138170470f4dc47.
namespace {
using Collection=atlas::kinematics::Collection;
using Pair=atlas::kinematics::Pair;
using RVec=atlas::kinematics::RVec;
constexpr long double absent=std::numeric_limits<long double>::quiet_NaN();
constexpr const char* original_commit="d823593b42889592897263819138170470f4dc47";
constexpr std::array<const char*,9> observables{"px","py","pz","energy","mass2","mass","delta_eta","delta_phi","delta_r"};
using Values=std::array<long double,9>;

long long integer(const char* input) {
  std::size_t used=0;const std::string text=input;const auto value=std::stoll(text,&used);
  if(used!=text.size())throw std::invalid_argument("Expected complete integer argument");
  return value;
}
double positive(const char* input) {
  std::size_t used=0;const std::string text=input;const auto value=std::stod(text,&used);
  if(used!=text.size()||!std::isfinite(value)||value<=0)throw std::invalid_argument("Expected positive finite scale");
  return value;
}
template<class T> std::string number(T value) {
  std::ostringstream text;text<<std::setprecision(std::numeric_limits<T>::max_digits10)<<value;return text.str();
}
std::string real(long double value) {return std::isfinite(value)?number(value):"";}
std::string json_real(long double value) {return std::isfinite(value)?number(value):"null";}
std::string json_quote(const std::string& value) {
  std::ostringstream text;text<<'"';
  for(unsigned char c:value) {
    if(c=='"'||c=='\\')text<<'\\'<<c;
    else if(c<32)text<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;
    else text<<c;
  }
  text<<'"';return text.str();
}
struct Csv {
  std::ofstream file;
  explicit Csv(const std::filesystem::path& path):file(path) {file.exceptions(std::ios::badbit|std::ios::failbit);}
  void row(const std::vector<std::string>& fields) {
    for(std::size_t index=0;index<fields.size();++index) {
      if(index)file<<',';
      const auto& text=fields[index];
      if(text.find_first_of(",\"\r\n")==std::string::npos)file<<text;
      else {file<<'"';for(char c:text){if(c=='"')file<<'"';file<<c;}file<<'"';}
    }
    file<<'\n';
  }
};
void append(std::vector<std::string>& row,const Values& values) {for(auto value:values)row.push_back(real(value));}
Pair original_leading_pair(const Collection& collection) {
  Pair result;
  if(!collection.valid){result.issue=collection.issue;return result;}
  if(collection.ordered.size()<2){result.issue="fewer_than_two_objects";return result;}
  result.available=true;
  const auto& a=collection.ordered[0].p4;
  const auto& b=collection.ordered[1].p4;
  const auto sum=a+b;
  const double mass2=sum.M2();
  if(!std::isfinite(mass2)||mass2<0){result.issue="negative_or_nonfinite_pair_mass2";return result;}
  result.mass=std::sqrt(mass2);
  result.delta_eta=a.Eta()-b.Eta();
  result.delta_phi=atlas::kinematics::delta_phi(a.Phi(),b.Phi());
  result.delta_r=std::hypot(result.delta_eta,result.delta_phi);
  result.valid=std::isfinite(result.mass)&&std::isfinite(result.delta_r);
  if(!result.valid)result.issue="nonfinite_pair_observable";
  return result;
}
long double half_ulp(float value) {
  if(!std::isfinite(value))return absent;
  const float lower=std::nextafter(value,-std::numeric_limits<float>::infinity());
  const float upper=std::nextafter(value,std::numeric_limits<float>::infinity());
  if(!std::isfinite(lower)||!std::isfinite(upper))return absent;
  return std::max(static_cast<long double>(value)-lower,static_cast<long double>(upper)-value)/2;
}
struct RawVectors {const RVec& pt;const RVec& eta;const RVec& phi;const RVec& energy;};
Values native_components(const RawVectors& raw,std::size_t index,double scale) {
  Values values;values.fill(absent);
  const long double pt=static_cast<long double>(raw.pt.at(index))*scale;
  const long double eta=raw.eta.at(index),phi=raw.phi.at(index),energy=static_cast<long double>(raw.energy.at(index))*scale;
  values[0]=pt*std::cos(phi);values[1]=pt*std::sin(phi);values[2]=pt*std::sinh(eta);values[3]=energy;
  values[4]=energy*energy-values[0]*values[0]-values[1]*values[1]-values[2]*values[2];
  if(values[4]>=0)values[5]=std::sqrt(values[4]);
  return values;
}
std::array<long double,4> perturbation_bounds(const RawVectors& raw,std::size_t index,double scale) {
  const long double hp=half_ulp(raw.pt[index]),he=half_ulp(raw.energy[index]);
  const long double heta=half_ulp(raw.eta[index]),hphi=half_ulp(raw.phi[index]);
  const long double p=std::abs(static_cast<long double>(raw.pt[index]));
  const long double maximum_eta=std::abs(static_cast<long double>(raw.eta[index]))+heta;
  // Conservative Lipschitz bounds for independent half-ULP perturbations of
  // native float tuples. Compatibility is not proof that rounding caused m2<0.
  const long double transverse=scale*(hp+(p+hp)*hphi);
  return {transverse,transverse,scale*(hp*std::sinh(maximum_eta)+(p+hp)*std::cosh(maximum_eta)*heta),scale*he};
}
long double mass2_perturbation_bound(const Values& v,const std::array<long double,4>& delta) {
  long double bound=0;
  for(std::size_t index=0;index<4;++index)bound+=2*std::abs(v[index])*delta[index]+delta[index]*delta[index];
  return bound;
}
struct Comparison {
  Values old_values{},new_values{},reference{},tolerances{};
  Pair old_pair,new_pair;
  bool available=false;
  long double input_half_ulp_mass2_bound=absent;
  std::string classification="NO_PAIR";
};
Comparison compare(const Collection& collection,const RawVectors& raw,double scale) {
  Comparison c;c.old_values.fill(absent);c.new_values.fill(absent);c.reference.fill(absent);c.tolerances.fill(absent);
  c.old_pair=original_leading_pair(collection);c.new_pair=atlas::kinematics::leading_pair(collection);
  c.available=collection.valid&&collection.ordered.size()>=2;
  if(!c.available){c.classification=collection.valid?"FEWER_THAN_TWO_OBJECTS":"INVALID_SUPPLIED_COLLECTION";return c;}
  const auto& a=collection.ordered[0].p4;const auto& b=collection.ordered[1].p4;
  const auto old_sum=a+b;
  // B diagnostic components follow the shared extended-precision ROOT type;
  // actual B observables below always come from the shared public Pair API.
  const auto cartesian=[](const atlas::kinematics::FourVector& object) {
    const long double pt=object.Pt(),eta=object.Eta(),phi=object.Phi();
    return atlas::kinematics::CartesianFourVector(pt*std::cos(phi),pt*std::sin(phi),pt*std::sinh(eta),object.E());
  };
  const auto ca=cartesian(a),cb=cartesian(b);
  const auto new_sum=ca+cb;
  c.old_values={old_sum.Px(),old_sum.Py(),old_sum.Pz(),old_sum.E(),old_sum.M2(),absent,absent,absent,absent};
  c.new_values={new_sum.Px(),new_sum.Py(),new_sum.Pz(),new_sum.E(),new_sum.M2(),absent,absent,absent,absent};
  // Mass and angles are the actual public Pair returns, not a substituted sum.
  if(c.old_pair.valid){c.old_values[5]=c.old_pair.mass;c.old_values[6]=c.old_pair.delta_eta;c.old_values[7]=c.old_pair.delta_phi;c.old_values[8]=c.old_pair.delta_r;}
  if(c.new_pair.valid){c.new_values[5]=c.new_pair.mass;c.new_values[6]=c.new_pair.delta_eta;c.new_values[7]=c.new_pair.delta_phi;c.new_values[8]=c.new_pair.delta_r;}
  std::array<long double,4> delta{};
  for(std::size_t rank=0;rank<2;++rank) {
    const auto index=collection.ordered[rank].input_index;const auto v=native_components(raw,index,scale);const auto d=perturbation_bounds(raw,index,scale);
    for(std::size_t component=0;component<4;++component){if(rank==0)c.reference[component]=0;c.reference[component]+=v[component];delta[component]+=d[component];}
  }
  const auto& r=c.reference;
  c.reference[4]=r[3]*r[3]-r[0]*r[0]-r[1]*r[1]-r[2]*r[2];
  if(r[4]>=0)c.reference[5]=std::sqrt(r[4]);
  const auto i=collection.ordered[0].input_index,j=collection.ordered[1].input_index;
  c.reference[6]=static_cast<long double>(raw.eta[i])-raw.eta[j];
  const long double angle=static_cast<long double>(raw.phi[i])-raw.phi[j];
  c.reference[7]=std::atan2(std::sin(angle),std::cos(angle));
  c.reference[8]=std::hypot(r[6],r[7]);
  for(std::size_t component=0;component<4;++component)c.tolerances[component]=1e-9L+1e-12L*std::abs(r[component]);
  long double arithmetic_scale=0;for(std::size_t component=0;component<4;++component)arithmetic_scale+=r[component]*r[component];
  c.tolerances[4]=1e-9L+64*std::numeric_limits<double>::epsilon()*arithmetic_scale;
  if(std::isfinite(r[5]))c.tolerances[5]=1e-7L+1e-10L*std::abs(r[5]);
  c.tolerances[6]=c.tolerances[7]=c.tolerances[8]=1e-12L;
  c.input_half_ulp_mass2_bound=mass2_perturbation_bound(r,delta);
  if(!std::isfinite(r[4])||!std::isfinite(c.new_values[4])||!std::isfinite(c.old_values[4]))c.classification="NONFINITE_NUMERICAL_RESULT";
  else if(r[4]<0) {
    c.classification=std::abs(r[4])<=c.input_half_ulp_mass2_bound?"NEGATIVE_SUPPLIED_FLOAT32_TUPLE_HALF_ULP_COMPATIBLE_ORIGIN_UNKNOWN":"NEGATIVE_SUPPLIED_FLOAT32_TUPLE_OUTSIDE_HALF_ULP_BOUND_ORIGIN_UNKNOWN";
    if(c.new_values[4]>=0)c.classification="MASS2_SIGN_DISAGREEMENT_REQUIRES_REVIEW";
  } else if(c.new_values[4]<0)c.classification="MASS2_SIGN_DISAGREEMENT_REQUIRES_REVIEW";
  else if(c.old_values[4]<0)c.classification="OLD_COORDINATE_CONVERSION_NEGATIVE_SIGN_ARTIFACT";
  else if(std::abs(c.old_values[5]-r[5])>c.tolerances[5]&&std::abs(c.new_values[5]-r[5])<=c.tolerances[5])c.classification="OLD_COORDINATE_CONVERSION_MASS_CLOSURE_FAILURE";
  else c.classification="NONNEGATIVE_REFERENCE";
  return c;
}
long double difference(long double measured,long double reference,std::size_t component) {
  const auto delta=measured-reference;
  return std::abs(component==7?std::remainder(delta,2*std::numbers::pi_v<long double>):delta);
}
struct Metric {
  std::uint64_t tested=0,failed=0;long double maximum_absolute=0,maximum_relative=0,maximum_tolerance=0;
  void observe(long double value,long double reference,long double tolerance,std::size_t component) {
    if(!std::isfinite(value)||!std::isfinite(reference)||!std::isfinite(tolerance))return;
    ++tested;const auto error=difference(value,reference,component);failed+=error>tolerance;
    maximum_absolute=std::max(maximum_absolute,error);maximum_tolerance=std::max(maximum_tolerance,tolerance);
    if(reference!=0)maximum_relative=std::max(maximum_relative,error/std::abs(reference));
  }
};
struct GroupTotals {
  std::uint64_t available=0,old_valid=0,new_valid=0,old_negative=0,new_negative=0,reference_negative=0;
  std::uint64_t corrected_invalid_nonnegative_reference=0,corrected_valid_negative_reference=0,nonfinite=0;
  std::map<std::string,std::uint64_t> classifications;
  std::array<Metric,9> old_metrics{},new_metrics{};
  void observe(const Comparison& c) {
    ++classifications[c.classification];if(!c.available)return;
    ++available;old_valid+=c.old_pair.valid;new_valid+=c.new_pair.valid;
    old_negative+=c.old_values[4]<0;new_negative+=c.new_values[4]<0;reference_negative+=c.reference[4]<0;
    corrected_invalid_nonnegative_reference+=std::isfinite(c.reference[4])&&c.reference[4]>=0&&!c.new_pair.valid;
    corrected_valid_negative_reference+=c.reference[4]<0&&c.new_pair.valid;
    nonfinite+=!std::isfinite(c.reference[4])||!std::isfinite(c.new_values[4]);
    for(std::size_t k=0;k<observables.size();++k){old_metrics[k].observe(c.old_values[k],c.reference[k],c.tolerances[k],k);new_metrics[k].observe(c.new_values[k],c.reference[k],c.tolerances[k],k);}
  }
};
enum class Kind {PhotonPt,PhotonEta,JetPt,JetEta,Mgg,Mjj,Dgg,Djj};
struct Histogram {
  std::string name;Kind kind;bool selected;
  std::array<std::unique_ptr<TH1D>,2> hist;
  Histogram(std::string label,Kind family,bool c9,int bins,double low,double high):name(std::move(label)),kind(family),selected(c9) {
    for(std::size_t version=0;version<2;++version) {
      const auto object_name=name+(version?"__corrected":"__original");
      hist[version]=std::make_unique<TH1D>(object_name.c_str(),"Raw unweighted diagnostic;native coordinates;Raw counts / bin",bins,low,high);
      hist[version]->SetDirectory(nullptr);
    }
  }
};
std::vector<Histogram> histogram_definitions(bool mc) {
  std::vector<Histogram> h;
  const auto add=[&](const char* name,Kind kind,bool selected,int bins,double low,double high){h.emplace_back(name,kind,selected,bins,low,high);};
  if(mc) {
    add("mc_m_gg",Kind::Mgg,false,80,0,400);add("mc_m_jj",Kind::Mjj,false,80,0,800);
    add("mc_deltaR_gg",Kind::Dgg,false,60,0,6);add("mc_deltaR_jj",Kind::Djj,false,60,0,6);
    add("mc_photon_pt",Kind::PhotonPt,false,60,0,300);add("mc_jet_pt",Kind::JetPt,false,60,0,300);
    add("mc_m_gg_C9",Kind::Mgg,true,70,100,170);add("mc_m_jj_C9",Kind::Mjj,true,80,0,800);
    add("mc_photon_pt_C9",Kind::PhotonPt,true,60,0,300);add("mc_jet_pt_C9",Kind::JetPt,true,60,0,300);
  } else {
    add("photon_pt",Kind::PhotonPt,false,60,0,300);add("photon_eta",Kind::PhotonEta,false,50,-2.5,2.5);
    add("jet_pt",Kind::JetPt,false,60,0,300);add("jet_eta",Kind::JetEta,false,60,-5,5);
    add("m_gg",Kind::Mgg,false,80,0,400);add("m_jj",Kind::Mjj,false,80,0,800);add("deltaR_gg",Kind::Dgg,false,60,0,6);
    add("m_gg_preselection",Kind::Mgg,true,70,100,170);add("m_jj_preselection",Kind::Mjj,true,80,0,800);
    add("photon_pt_selected",Kind::PhotonPt,true,60,0,300);add("jet_pt_selected",Kind::JetPt,true,60,0,300);
  }
  return h;
}
atlas::selection::Event selection_event(const atlas::events::RawEvent& raw,const Collection& photons,const Collection& jets,
                                      const Comparison& gg,const Comparison& jj,bool valid,bool corrected) {
  atlas::selection::Event result;result.source_valid=valid;result.photons=raw.photon_n;result.jets=raw.jet_n;
  const auto& p=corrected?gg.new_pair:gg.old_pair;const auto& j=corrected?jj.new_pair:jj.old_pair;
  for(std::size_t index=0;index<2;++index) {
    result.photon_pt[index]=valid&&index<photons.ordered.size()?photons.ordered[index].p4.Pt():double(absent);
    result.photon_eta[index]=valid&&index<photons.ordered.size()?photons.ordered[index].p4.Eta():double(absent);
    result.jet_pt[index]=valid&&index<jets.ordered.size()?jets.ordered[index].p4.Pt():double(absent);
    result.jet_eta[index]=valid&&index<jets.ordered.size()?jets.ordered[index].p4.Eta():double(absent);
  }
  result.mgg=valid&&p.valid?p.mass:double(absent);result.mjj=valid&&j.valid?j.mass:double(absent);
  return result;
}
std::string event_issue(const Collection& photons,const Collection& jets,const Pair& gg,const Pair& jj,bool angular,bool energy) {
  return !photons.valid?"photon_"+photons.issue:(!jets.valid?"jet_"+jets.issue:(!angular?"invalid_phi_convention":(!energy?"energy_exceeds_13TeV_or_nonfinite":
    (gg.available&&!gg.valid?"gg_"+gg.issue:(jj.available&&!jj.valid?"jj_"+jj.issue:"")))));
}
std::vector<std::string> identity(const std::string& mode,std::uint32_t dsid,long long entry,const atlas::events::RawEvent& raw) {
  return {mode,number(dsid),number(entry),number(raw.run),number(raw.event)};
}
void write_pair(Csv& csv,const std::vector<std::string>& id,const std::string& group,const Collection& collection,const Comparison& c) {
  auto row=id;row.insert(row.end(),{group,number(c.available),number(collection.valid),collection.issue,
    c.available?number(collection.ordered[0].input_index):"",c.available?number(collection.ordered[1].input_index):"",
    number(c.old_pair.valid),c.old_pair.issue,number(c.new_pair.valid),c.new_pair.issue,c.classification,
    real(c.input_half_ulp_mass2_bound),c.available?number(std::isfinite(c.reference[4])&&std::abs(c.reference[4])<=c.input_half_ulp_mass2_bound):""});
  append(row,c.old_values);append(row,c.new_values);append(row,c.reference);append(row,c.tolerances);
  for(const auto* measured:{&c.old_values,&c.new_values})for(std::size_t k=0;k<observables.size();++k) {
    const auto value=(*measured)[k],reference=c.reference[k];
    const bool tested=std::isfinite(value)&&std::isfinite(reference)&&std::isfinite(c.tolerances[k]);
    const auto error=tested?difference(value,reference,k):absent;
    row.push_back(real(error));row.push_back(tested&&reference!=0?real(error/std::abs(reference)):"");
    row.push_back(tested?number(error>c.tolerances[k]):"");
  }
  csv.row(row);
}
void write_objects(Csv& csv,const std::vector<std::string>& id,const std::string& group,const RawVectors& raw,const Collection& collection,
                   double scale,const atlas::events::RawEvent& source,bool id_known,bool iso_known) {
  for(std::size_t index=0;index<raw.pt.size();++index) {
    auto row=id;const auto rank=std::find_if(collection.ordered.begin(),collection.ordered.end(),[&](const auto& c){return c.input_index==index;});
    const auto values=native_components(raw,index,scale);const auto bound=mass2_perturbation_bound(values,perturbation_bounds(raw,index,scale));
    row.insert(row.end(),{group,number(index),rank==collection.ordered.end()?"":number(std::distance(collection.ordered.begin(),rank)),number(collection.valid),collection.issue,
      number(raw.pt[index]),number(raw.eta[index]),number(raw.phi[index]),number(raw.energy[index]),real(static_cast<long double>(raw.pt[index])*scale),real(static_cast<long double>(raw.energy[index])*scale)});
    // Actual ROOT per-object components alongside an independent native reference.
    if(rank!=collection.ordered.end()) {
      const auto& p=rank->p4;for(double v:{p.Px(),p.Py(),p.Pz(),p.E(),p.M2()})row.push_back(real(v));
    } else for(int k=0;k<5;++k)row.emplace_back();
    for(std::size_t k=0;k<5;++k)row.push_back(real(values[k]));
    row.insert(row.end(),{rank==collection.ordered.end()?"":number(rank->negative_roundoff),real(bound),number(std::isfinite(values[4])&&values[4]<0&&std::abs(values[4])<=bound),
      group=="photon"&&id_known?number(bool(source.tight_id.at(index))):"",group=="photon"&&iso_known?number(bool(source.tight_iso.at(index))):"","RAW_PRESERVED_ORIGIN_UNKNOWN"});
    csv.row(row);
  }
}
void group_json(std::ostream& out,const GroupTotals& totals) {
  out<<"{\"available_pairs\":"<<totals.available<<",\"original_valid_pairs\":"<<totals.old_valid<<",\"corrected_valid_pairs\":"<<totals.new_valid
    <<",\"original_negative_mass2\":"<<totals.old_negative<<",\"corrected_negative_mass2\":"<<totals.new_negative<<",\"reference_negative_mass2\":"<<totals.reference_negative
    <<",\"corrected_invalid_nonnegative_reference\":"<<totals.corrected_invalid_nonnegative_reference<<",\"corrected_valid_negative_reference\":"<<totals.corrected_valid_negative_reference
    <<",\"nonfinite_results\":"<<totals.nonfinite<<",\"classifications\":{";
  bool first=true;for(const auto& [name,count]:totals.classifications){if(!first)out<<',';first=false;out<<json_quote(name)<<':'<<count;}out<<"},\"metrics\":{";
  for(std::size_t k=0;k<observables.size();++k) {
    if(k)out<<',';
    out<<json_quote(observables[k])<<":{";
    for(std::size_t version=0;version<2;++version) {
      if(version)out<<',';
      const auto& m=version?totals.new_metrics[k]:totals.old_metrics[k];
      out<<json_quote(version?"corrected":"original")<<":{\"tested\":"<<m.tested<<",\"failed\":"<<m.failed
        <<",\"maximum_absolute\":"<<json_real(m.maximum_absolute)<<",\"maximum_relative\":"<<json_real(m.maximum_relative)
        <<",\"maximum_tolerance\":"<<json_real(m.maximum_tolerance)<<'}';
    }
    out<<'}';
  }
  out<<"}}";
}
}

int main(int argc,char** argv) {
  try {
    if(argc!=10)throw std::invalid_argument("Usage: phase4_numerical_regression DATA|MC input.root NEW_output expected_DSID start exclusive_end scale_to_GeV PROVISIONAL selection.ini");
    const std::string mode=argv[1];if(mode!="DATA"&&mode!="MC")throw std::invalid_argument("Mode must be DATA or MC");const bool mc=mode=="MC";
    const auto expected=integer(argv[4]),start=integer(argv[5]),end=integer(argv[6]);const double scale=positive(argv[7]);
    if(expected<0||static_cast<unsigned long long>(expected)>std::numeric_limits<std::uint32_t>::max()||(mc&&expected==0)||(!mc&&expected!=0))throw std::invalid_argument("Expected DSID must be positive uint32 for MC and zero for DATA");
    if(start<0||end<=start||end>100000||(mc&&end-start>10000))throw std::invalid_argument("Require positive explicit bounded range, at most 100000 end and 10000 MC entries");
    if(std::string(argv[8])!="PROVISIONAL")throw std::invalid_argument("Unit provenance must remain PROVISIONAL");
    const std::filesystem::path input=argv[2],output=argv[3];
    if(std::filesystem::exists(output))throw std::runtime_error("Output exists; refusing overwrite of any evidence");
    if(!std::filesystem::is_regular_file(input)||input.string().find("://")!=std::string::npos)throw std::invalid_argument("Explicit local native input required");
    const auto config=atlas::selection::read_config(argv[9]);
    std::unique_ptr<atlas::events::Reader> data_reader;std::unique_ptr<atlas::mc::Reader> mc_reader;
    if(mc)mc_reader=std::make_unique<atlas::mc::Reader>(input,static_cast<std::uint32_t>(expected));else data_reader=std::make_unique<atlas::events::Reader>(input);
    const auto available_entries=mc?mc_reader->entries():data_reader->entries();if(end>available_entries)throw std::out_of_range("Requested range exceeds tree; no silent truncation allowed");
    std::filesystem::create_directories(output);gROOT->SetBatch(true);
    Csv objects(output/"objects.csv"),pairs(output/"pairs.csv"),events(output/"events.csv"),placements(output/"histogram_placements.csv"),event_diff(output/"event_histogram_diff.csv");
    const std::vector<std::string> identity_columns{"mode","dsid","entry","run","event"};
    auto header=identity_columns;header.insert(header.end(),{"group","input_index","leading_rank_zero_based","collection_valid","collection_issue","raw_pt","raw_eta","raw_phi","raw_energy","scaled_pt","scaled_energy",
      "root_px","root_py","root_pz","root_energy","root_mass2","reference_px","reference_py","reference_pz","reference_energy","reference_mass2","negative_roundoff_object","half_ulp_mass2_bound","negative_half_ulp_compatible","raw_tight_id","raw_tight_iso","interpretation"});objects.row(header);
    header=identity_columns;header.insert(header.end(),{"group","pair_available","collection_valid","collection_issue","leading_input_index","subleading_input_index","original_valid","original_issue","corrected_valid","corrected_issue","mass2_classification","half_ulp_mass2_bound","mass2_zero_half_ulp_compatible"});
    for(const std::string prefix:{"original_","corrected_","reference_","tolerance_"})for(auto field:observables)header.push_back(prefix+field);
    for(const std::string prefix:{"original_","corrected_"})for(auto field:observables)for(const std::string suffix:{"_absolute_residual","_relative_residual","_diagnostic_failed"})header.push_back(prefix+field+suffix);
    pairs.row(header);
    header=identity_columns;header.insert(header.end(),{"raw_generator_weight","photon_n","jet_n","roundoff_objects","original_valid","original_issue","corrected_valid","corrected_issue","validity_changed"});
    for(const std::string prefix:{"original_","corrected_"}) {
      for(const std::string field:{"photon1_pt","photon2_pt","photon1_eta","photon2_eta","jet1_pt","jet2_pt","jet1_eta","jet2_eta","m_gg","m_jj","deltaEta_gg","deltaPhi_gg","deltaR_gg","deltaEta_jj","deltaPhi_jj","deltaR_jj"})header.push_back(prefix+field);
      for(std::size_t k=0;k<10;++k)header.push_back(prefix+"C"+number(k));
    }
    header.insert(header.end(),{"cumulative_selection_changed","histogram_event_changed","p1_tight_id","p2_tight_id","p1_tight_iso","p2_tight_iso","photon_pair_classification","jet_pair_classification"});events.row(header);
    header=identity_columns;header.insert(header.end(),{"histogram","population","object_group","input_index","original_fill","corrected_fill","original_value","corrected_value","original_bin","corrected_bin","placement_changed"});placements.row(header);
    header=identity_columns;header.insert(header.end(),{"histogram","bin","original_event_contribution","corrected_event_contribution","delta","reason"});event_diff.row(header);
    auto histograms=histogram_definitions(mc);std::array<std::array<std::uint64_t,10>,2> counts{};
    std::array<std::uint64_t,2> invalid{},raw_tight{},raw_tight_iso{},missing_flags{};
    std::uint64_t validity_changes=0,selection_changes=0,histogram_event_changes=0,histogram_contribution_changes=0,roundoff=0,positive_weights=0,negative_weights=0,zero_weights=0;
    GroupTotals photon_totals,jet_totals;std::set<std::tuple<std::uint32_t,std::uint32_t,std::uint64_t>> identities;
    for(auto entry=start;entry<end;++entry) {
      atlas::events::RawEvent raw;std::uint32_t dsid=0;double weight=std::numeric_limits<double>::quiet_NaN();bool id_known=true,iso_known=true;
      if(mc) {
        const auto source=mc_reader->read(entry);raw=source.reconstructed;dsid=source.dsid;weight=source.generator_weight;
        id_known=source.photon_flag_available.at("photon_isTightID");iso_known=source.photon_flag_available.at("photon_isTightIso");
        positive_weights+=weight>0;negative_weights+=weight<0;zero_weights+=weight==0;
      } else raw=data_reader->read(entry);
      if(!identities.emplace(dsid,raw.run,raw.event).second)throw std::runtime_error("Duplicate native DSID/run/event within bounded input range");
      const auto id=identity(mode,dsid,entry,raw);
      const RawVectors photon_raw{raw.photon_pt,raw.photon_eta,raw.photon_phi,raw.photon_e},jet_raw{raw.jet_pt,raw.jet_eta,raw.jet_phi,raw.jet_e};
      const auto photons=atlas::kinematics::construct(raw.photon_pt,raw.photon_eta,raw.photon_phi,raw.photon_e,raw.photon_n,scale);
      const auto jets=atlas::kinematics::construct(raw.jet_pt,raw.jet_eta,raw.jet_phi,raw.jet_e,raw.jet_n,scale);
      const auto gg=compare(photons,photon_raw,scale),jj=compare(jets,jet_raw,scale);
      photon_totals.observe(gg);jet_totals.observe(jj);
      write_objects(objects,id,"photon",photon_raw,photons,scale,raw,id_known,iso_known);write_objects(objects,id,"jet",jet_raw,jets,scale,raw,false,false);
      write_pair(pairs,id,"photon",photons,gg);write_pair(pairs,id,"jet",jets,jj);
      bool angular=true,energy=true;
      for(const auto* values:{&raw.photon_phi,&raw.jet_phi})for(float value:*values)angular=angular&&std::isfinite(value)&&std::abs(value)<=std::numbers::pi+1e-5;
      for(const auto* values:{&raw.photon_e,&raw.jet_e})for(float value:*values)energy=energy&&std::isfinite(value)&&double(value)*scale<=13000.;
      if(!mc&&(!angular||!energy))throw std::runtime_error("DATA angular/energy convention contradicted; historical driver would stop");
      std::array<bool,2> valid{};std::array<std::string,2> issues{};std::array<atlas::selection::Event,2> selected{};std::array<std::array<bool,10>,2> passed{};
      for(std::size_t version=0;version<2;++version) {
        const auto& p=version?gg.new_pair:gg.old_pair;const auto& j=version?jj.new_pair:jj.old_pair;
        valid[version]=photons.valid&&jets.valid&&(!p.available||p.valid)&&(!j.available||j.valid)&&angular&&energy;
        issues[version]=event_issue(photons,jets,p,j,angular,energy);invalid[version]+=!valid[version];
        selected[version]=selection_event(raw,photons,jets,gg,jj,valid[version],version!=0);
        passed[version]=atlas::selection::evaluate(selected[version],config);for(std::size_t k=0;k<10;++k)counts[version][k]+=passed[version][k];
      }
      std::array<int,2> tight{-1,-1},iso{-1,-1};
      for(std::size_t rank=0;rank<2&&rank<photons.ordered.size();++rank) {
        const auto index=photons.ordered[rank].input_index;if(id_known)tight[rank]=raw.tight_id.at(index);if(iso_known)iso[rank]=raw.tight_iso.at(index);
      }
      for(std::size_t version=0;version<2;++version)if(passed[version][9]) {
        missing_flags[version]+=tight[0]<0||tight[1]<0||iso[0]<0||iso[1]<0;
        raw_tight[version]+=tight[0]==1&&tight[1]==1;raw_tight_iso[version]+=tight[0]==1&&tight[1]==1&&iso[0]==1&&iso[1]==1;
      }
      const bool validity_changed=valid[0]!=valid[1],selection_changed=passed[0]!=passed[1];validity_changes+=validity_changed;selection_changes+=selection_changed;
      bool hist_event_changed=false;
      for(auto& histogram:histograms) {
        std::array<std::map<int,int>,2> contributions;
        const auto placement=[&](const std::string& group,const std::string& input_index,long double old_value,long double new_value) {
          std::array<long double,2> values{old_value,new_value};std::array<bool,2> fill{};std::array<int,2> bins{};
          for(std::size_t version=0;version<2;++version) {
            fill[version]=(histogram.selected?passed[version][9]:valid[version])&&std::isfinite(values[version]);
            if(fill[version]){bins[version]=histogram.hist[version]->FindFixBin(double(values[version]));histogram.hist[version]->Fill(double(values[version]));++contributions[version][bins[version]];}
          }
          const bool changed=fill[0]!=fill[1]||(fill[0]&&bins[0]!=bins[1]);
          auto row=id;row.insert(row.end(),{histogram.name,histogram.selected?"C9":"WHOLE_EVENT_VALID",group,input_index,number(fill[0]),number(fill[1]),real(old_value),real(new_value),fill[0]?number(bins[0]):"",fill[1]?number(bins[1]):"",number(changed)});placements.row(row);
        };
        if(histogram.kind==Kind::PhotonPt||histogram.kind==Kind::PhotonEta||histogram.kind==Kind::JetPt||histogram.kind==Kind::JetEta) {
          const bool photon=histogram.kind==Kind::PhotonPt||histogram.kind==Kind::PhotonEta;const auto& collection=photon?photons:jets;
          const bool pt=histogram.kind==Kind::PhotonPt||histogram.kind==Kind::JetPt;
          const auto limit=histogram.selected?std::min<std::size_t>(2,collection.ordered.size()):collection.ordered.size();
          for(std::size_t rank=0;rank<limit;++rank){const auto& object=collection.ordered[rank];const auto value=pt?object.p4.Pt():object.p4.Eta();placement(photon?"photon":"jet",number(object.input_index),value,value);}
        } else {
          const bool photon=histogram.kind==Kind::Mgg||histogram.kind==Kind::Dgg;const auto& comparison=photon?gg:jj;
          const bool mass=histogram.kind==Kind::Mgg||histogram.kind==Kind::Mjj;
          placement(photon?"photon_pair":"jet_pair","",comparison.old_pair.valid?(mass?comparison.old_pair.mass:comparison.old_pair.delta_r):absent,comparison.new_pair.valid?(mass?comparison.new_pair.mass:comparison.new_pair.delta_r):absent);
        }
        std::set<int> bins;for(const auto& contribution:contributions)for(const auto& [bin,count]:contribution){(void)count;bins.insert(bin);}
        for(int bin:bins)if(contributions[0][bin]!=contributions[1][bin]) {
          hist_event_changed=true;++histogram_contribution_changes;auto row=id;row.insert(row.end(),{histogram.name,number(bin),number(contributions[0][bin]),number(contributions[1][bin]),number(contributions[1][bin]-contributions[0][bin]),validity_changed?"EVENT_VALIDITY_CHANGED":(selection_changed?"CUMULATIVE_SELECTION_CHANGED":"PAIR_NUMERICAL_BIN_BOUNDARY_CHANGED")});event_diff.row(row);
        }
      }
      histogram_event_changes+=hist_event_changed;const auto rounded=photons.roundoff_objects+jets.roundoff_objects;roundoff+=rounded;
      auto row=id;row.insert(row.end(),{real(weight),number(raw.photon_n),number(raw.jet_n),number(rounded),number(valid[0]),issues[0],number(valid[1]),issues[1],number(validity_changed)});
      for(std::size_t version=0;version<2;++version) {
        const auto& e=selected[version];for(auto value:e.photon_pt)row.push_back(real(value));for(auto value:e.photon_eta)row.push_back(real(value));for(auto value:e.jet_pt)row.push_back(real(value));for(auto value:e.jet_eta)row.push_back(real(value));
        row.push_back(real(e.mgg));row.push_back(real(e.mjj));
        const auto& p=version?gg.new_pair:gg.old_pair;const auto& j=version?jj.new_pair:jj.old_pair;
        for(double value:{p.delta_eta,p.delta_phi,p.delta_r})row.push_back(valid[version]&&p.valid?real(value):"");
        for(double value:{j.delta_eta,j.delta_phi,j.delta_r})row.push_back(valid[version]&&j.valid?real(value):"");
        for(bool value:passed[version])row.push_back(number(value));
      }
      row.insert(row.end(),{number(selection_changed),number(hist_event_changed),tight[0]>=0?number(tight[0]):"",tight[1]>=0?number(tight[1]):"",iso[0]>=0?number(iso[0]):"",iso[1]>=0?number(iso[1]):"",gg.classification,jj.classification});events.row(row);
    }
    objects.file.close();pairs.file.close();events.file.close();placements.file.close();event_diff.file.close();
    Csv cutflow(output/"cutflow.csv");cutflow.row({"cut","original_events","corrected_events","delta","definition_version"});
    for(std::size_t k=0;k<10;++k)cutflow.row({"C"+number(k),number(counts[0][k]),number(counts[1][k]),number(static_cast<long long>(counts[1][k])-static_cast<long long>(counts[0][k])),config.version});
    cutflow.file.close();
    Csv flag_counts(output/"optional_photon_flags.csv");flag_counts.row({"version","C9_events","raw_tight_id_both","raw_tight_id_and_tight_iso_both","missing_flags","usage"});
    for(std::size_t version=0;version<2;++version)flag_counts.row({version?"corrected":"original",number(counts[version][9]),number(raw_tight[version]),number(raw_tight_iso[version]),number(missing_flags[version]),"DIAGNOSTIC_ONLY_NOT_SELECTION"});
    flag_counts.file.close();
    Csv bins(output/"histogram_bins.csv");bins.row({"histogram","population","bin","bin_class","low_edge","high_edge","original_content","corrected_content","delta","original_entries","corrected_entries"});
    std::uint64_t differing_bins=0;TFile root((output/"histograms.root").c_str(),"CREATE");if(root.IsZombie())throw std::runtime_error("Cannot create diagnostic native histogram file");
    for(auto& h:histograms) {
      const auto count=h.hist[0]->GetNbinsX();for(int bin=0;bin<=count+1;++bin) {
        const double old=h.hist[0]->GetBinContent(bin),fresh=h.hist[1]->GetBinContent(bin);differing_bins+=old!=fresh;
        bins.row({h.name,h.selected?"C9":"WHOLE_EVENT_VALID",number(bin),bin==0?"UNDERFLOW":(bin==count+1?"OVERFLOW":"REGULAR"),bin==0?"":real(h.hist[0]->GetXaxis()->GetBinLowEdge(bin)),bin==count+1?"":real(h.hist[0]->GetXaxis()->GetBinUpEdge(bin)),real(old),real(fresh),real(fresh-old),real(h.hist[0]->GetEntries()),real(h.hist[1]->GetEntries())});
      }
      for(auto& histogram:h.hist)if(histogram->Write()<=0)throw std::runtime_error("Cannot write native histogram evidence");
    }
    bins.file.close();
    const auto mass_failures=photon_totals.new_metrics[5].failed+jet_totals.new_metrics[5].failed+photon_totals.corrected_invalid_nonnegative_reference+jet_totals.corrected_invalid_nonnegative_reference+photon_totals.corrected_valid_negative_reference+jet_totals.corrected_valid_negative_reference+photon_totals.nonfinite+jet_totals.nonfinite;
    std::uint64_t other_diagnostic_failures=0;
    for(std::size_t k=0;k<observables.size();++k)if(k!=5)other_diagnostic_failures+=photon_totals.new_metrics[k].failed+jet_totals.new_metrics[k].failed;
    const auto failures=mass_failures+other_diagnostic_failures;
    std::ostringstream summary;summary<<std::setprecision(std::numeric_limits<long double>::max_digits10)
      <<"{\"schema\":\"phase4-numerical-regression-v2\",\"mode\":"<<json_quote(mode)<<",\"dsid\":"<<expected<<",\"declared_source_record\":"<<(mc?93922:93915)
      <<",\"source_identity_verification\":\"EXTERNAL_SHA256_MANIFEST_REQUIRED; mode and native schema alone do not verify public record membership\""
      <<",\"input_path\":"<<json_quote(input.string())<<",\"input_tree_entries\":"<<available_entries<<",\"start_entry\":"<<start<<",\"end_exclusive\":"<<end<<",\"entries_read\":"<<counts[0][0]
      <<",\"original_kernel_commit\":"<<json_quote(original_commit)<<",\"original_kernel\":\"PtEtaPhiEVector leading pair sum\",\"corrected_kernel\":\"shared leading_pair extended-precision ROOT Cartesian sum\""
      <<",\"reference\":\"independent long-double Cartesian arithmetic from native Float32 tuples and unchanged leading input indices\""
      <<",\"ROOT_version\":"<<json_quote(gROOT->GetVersion())<<",\"double_mantissa_bits\":"<<std::numeric_limits<double>::digits<<",\"long_double_mantissa_bits\":"<<std::numeric_limits<long double>::digits
      <<",\"unit_status\":\"PROVISIONAL\",\"scale_to_gev\":"<<scale<<",\"selection_definition\":"<<json_quote(config.version)<<",\"selection_config_path\":"<<json_quote(argv[9])
      <<",\"original_invalid_events\":"<<invalid[0]<<",\"corrected_invalid_events\":"<<invalid[1]<<",\"event_validity_changes\":"<<validity_changes<<",\"cumulative_selection_changes\":"<<selection_changes
      <<",\"original_C9\":"<<counts[0][9]<<",\"corrected_C9\":"<<counts[1][9]<<",\"histogram_event_changes\":"<<histogram_event_changes<<",\"histogram_contribution_changes\":"<<histogram_contribution_changes<<",\"differing_histogram_bins\":"<<differing_bins
      <<",\"negative_roundoff_objects\":"<<roundoff<<",\"raw_generator_weight_positive\":"<<positive_weights<<",\"raw_generator_weight_negative\":"<<negative_weights<<",\"raw_generator_weight_zero\":"<<zero_weights
      <<",\"mass_closure_tolerance\":\"1e-7+1e-10*abs(long_double_reference_mass)\",\"component_diagnostic_tolerance\":\"1e-9+1e-12*abs(reference_component)\""
      <<",\"mass2_diagnostic_tolerance\":\"1e-9+64*double_epsilon*(reference_E2+reference_px2+reference_py2+reference_pz2)\",\"angle_diagnostic_tolerance\":\"1e-12; deltaPhi residual wrapped modulo 2pi\""
      <<",\"half_ulp_diagnostic\":\"conservative independent native-float half-ULP perturbation bound; compatibility does not establish rounding origin or physical validity\""
      <<",\"histogram_policy\":\"d823 Phase2/Phase4 whole-event-valid raw unweighted histograms; selected histograms use unchanged cumulative C9; underflow and overflow preserved\""
      <<",\"weighting\":\"RAW_UNWEIGHTED\",\"normalization_applied\":false,\"scale_factors_applied\":false,\"truth_matching_performed\":false,\"figures_generated\":false"
      <<",\"corrected_mass_gate_failures\":"<<mass_failures<<",\"corrected_other_diagnostic_failures\":"<<other_diagnostic_failures<<",\"corrected_observable_gate_failures\":"<<failures
      <<",\"corrected_mass_gate_status\":"<<json_quote(mass_failures?"FAIL":(photon_totals.new_metrics[5].tested+jet_totals.new_metrics[5].tested?"PASS":"NOT_TESTED"))<<",\"photon_pairs\":";
    group_json(summary,photon_totals);summary<<",\"jet_pairs\":";group_json(summary,jet_totals);summary<<"}\n";
    TNamed metadata("phase4_numerical_regression_metadata",summary.str().c_str());if(metadata.Write()<=0)throw std::runtime_error("Cannot write native metadata");root.Close();
    std::ofstream json(output/"summary.json");json.exceptions(std::ios::badbit|std::ios::failbit);json<<summary.str();json.close();
    std::cout<<(failures?"FAIL":"COMPLETE")<<" numerical regression mode="<<mode<<" dsid="<<expected<<" range=["<<start<<','<<end<<") original_C9="<<counts[0][9]<<" corrected_C9="<<counts[1][9]<<" corrected_mass_gate_failures="<<failures<<" units=PROVISIONAL normalization=NOT_APPLIED\n";
    return failures?1:0;
  }catch(const std::exception& error){std::cerr<<"FAIL: "<<error.what()<<'\n';return 1;}
}

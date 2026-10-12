#include "AtlasKinematics.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numbers>
#include <random>
#include <stdexcept>
#include <string>

namespace {
using namespace atlas::kinematics;
struct Input { RVec pt,eta,phi,energy;double scale=1; };
struct Reference {
  std::array<long double,4> sum{},component_scale{};
  long double transverse_input_scale=0;
  long double mass2=0,delta_eta=0,delta_phi=0,delta_r=0;
};
struct Residual {
  std::uint64_t compared=0,failed=0;
  long double max_absolute=0,max_relative=0,max_tolerance=0;
  void observe(long double value,long double reference,long double tolerance) {
    ++compared;const auto difference=std::abs(value-reference);
    max_absolute=std::max(max_absolute,difference);max_tolerance=std::max(max_tolerance,tolerance);
    if(reference!=0)max_relative=std::max(max_relative,difference/std::abs(reference));
    failed+=!std::isfinite(difference)||difference>tolerance;
  }
};
struct Audit {
  std::map<std::string,Residual> metrics;
  std::map<std::string,std::uint64_t> categories;
  std::uint64_t cases=0,failed_cases=0,invalid_collections=0,negative_reference_pairs=0,old_negative_pairs=0,new_negative_pairs=0;
};
Reference reference(const Input& input,const Collection& collection) {
  Reference result;
  for(std::size_t position=0;position<2;++position) {
    const auto index=collection.ordered[position].input_index;
    const long double p=static_cast<long double>(input.pt[index])*input.scale;
    const long double eta=input.eta[index],phi=input.phi[index],energy=static_cast<long double>(input.energy[index])*input.scale;
    result.transverse_input_scale+=std::abs(p);
    const std::array<long double,4> component{p*std::cos(phi),p*std::sin(phi),p*std::sinh(eta),energy};
    for(std::size_t axis=0;axis<4;++axis){result.sum[axis]+=component[axis];result.component_scale[axis]+=std::abs(component[axis]);}
  }
  const auto& v=result.sum;result.mass2=v[3]*v[3]-v[0]*v[0]-v[1]*v[1]-v[2]*v[2];
  const auto first=collection.ordered[0].input_index,second=collection.ordered[1].input_index;
  result.delta_eta=static_cast<long double>(input.eta[first])-input.eta[second];
  result.delta_phi=std::remainder(static_cast<long double>(input.phi[first])-input.phi[second],2*std::numbers::pi_v<long double>);
  result.delta_r=std::hypot(result.delta_eta,result.delta_phi);
  return result;
}
long double mass_tolerance(long double mass){return 1e-7L+1e-10L*std::abs(mass);}
long double arithmetic_bound(long double scale) {
  // A separately named diagnostic bound, not a replacement mass criterion.
  return 64*std::numeric_limits<double>::epsilon()*std::max(scale,1.L);
}
std::uint64_t total_failed(const Audit& audit) {
  std::uint64_t total=0;for(const auto& [name,value]:audit.metrics)if(name.starts_with("B_"))total+=value.failed;
  return total;
}
void run(Audit& audit,std::ofstream& rows,const std::string& category,const Input& input,bool expected_invalid=false) {
  const auto before=total_failed(audit);bool pass=true;++audit.cases;++audit.categories[category];
  const auto collection=construct(input.pt,input.eta,input.phi,input.energy,static_cast<int>(input.pt.size()),input.scale);
  const auto pair=leading_pair(collection);
  rows<<audit.cases<<','<<category<<','<<input.scale<<','<<collection.valid<<','<<pair.valid;
  for(std::size_t index=0;index<2;++index)rows<<','<<input.pt[index]<<','<<input.eta[index]<<','<<input.phi[index]<<','<<input.energy[index];
  if(!collection.valid) {
    ++audit.invalid_collections;pass=expected_invalid&&!pair.valid;
    rows<<",,,,,,,,,"<<expected_invalid<<','<<pass<<'\n';audit.failed_cases+=!pass;return;
  }
  bool source_preserved=true;
  for(const auto& object:collection.ordered) {
    const auto index=object.input_index;
    source_preserved=source_preserved&&object.p4.Pt()==double(input.pt[index])*input.scale&&object.p4.E()==double(input.energy[index])*input.scale&&object.p4.Eta()==input.eta[index];
  }
  const auto c=reference(input,collection);const auto& a=collection.ordered[0].p4;const auto& b=collection.ordered[1].p4;
  const auto old_sum=a+b;
  const auto cartesian=[](const FourVector& object) {
    const long double pt=object.Pt(),eta=object.Eta(),phi=object.Phi();
    return CartesianFourVector(pt*std::cos(phi),pt*std::sin(phi),pt*std::sinh(eta),object.E());
  };
  const auto cart_a=cartesian(a),cart_b=cartesian(b);
  const auto new_sum=cart_a+cart_b;
  const std::array<long double,4> old_values{old_sum.Px(),old_sum.Py(),old_sum.Pz(),old_sum.E()},new_values{new_sum.Px(),new_sum.Py(),new_sum.Pz(),new_sum.E()};
  const std::array<const char*,4> labels{"px","py","pz","E"};
  for(std::size_t axis=0;axis<4;++axis) {
    // Include the inherited double-precision phi restriction's pT-scaled
    // angular-rounding term, even when a Cartesian component nearly vanishes.
    const auto scale=axis<2?std::max(c.component_scale[axis],c.transverse_input_scale):c.component_scale[axis];
    audit.metrics[std::string("A_")+labels[axis]].observe(old_values[axis],c.sum[axis],arithmetic_bound(scale));
    audit.metrics[std::string("B_")+labels[axis]].observe(new_values[axis],c.sum[axis],arithmetic_bound(scale));
  }
  long double invariant_scale=0;for(const auto value:c.sum)invariant_scale+=value*value;
  audit.metrics["A_mass2"].observe(old_sum.M2(),c.mass2,arithmetic_bound(invariant_scale));
  audit.metrics["B_mass2"].observe(new_sum.M2(),c.mass2,arithmetic_bound(invariant_scale));
  const bool reference_negative=c.mass2<0,old_negative=old_sum.M2()<0,new_negative=new_sum.M2()<0;
  audit.negative_reference_pairs+=reference_negative;audit.old_negative_pairs+=old_negative;audit.new_negative_pairs+=new_negative;
  if(reference_negative) {
    pass=source_preserved&&expected_invalid&&!pair.valid&&pair.issue=="negative_or_nonfinite_pair_mass2"&&new_negative;
    rows<<','<<c.mass2<<','<<old_sum.M2()<<','<<new_sum.M2()<<",,,,,"<<expected_invalid<<','<<pass<<'\n';
  } else {
    const long double mass=std::sqrt(c.mass2),tolerance=mass_tolerance(mass);
    if(!old_negative)audit.metrics["A_mass"].observe(std::sqrt(old_sum.M2()),mass,tolerance);
    pass=source_preserved&&!expected_invalid&&pair.valid&&!new_negative;
    if(pair.valid) {
      audit.metrics["B_mass"].observe(pair.mass,mass,tolerance);
      audit.metrics["B_delta_eta"].observe(pair.delta_eta,c.delta_eta,1e-12L);
      audit.metrics["B_delta_phi"].observe(pair.delta_phi,c.delta_phi,1e-12L);
      audit.metrics["B_delta_r"].observe(pair.delta_r,c.delta_r,1e-12L);
      // The actual shared Pair mass must come from the Cartesian sum being audited.
      pass=pass&&pair.mass==double(std::sqrt(new_sum.M2()));
    }
    rows<<','<<c.mass2<<','<<old_sum.M2()<<','<<new_sum.M2()<<',';
    if(!old_negative)rows<<std::sqrt(old_sum.M2());
    rows<<',';
    if(pair.valid)rows<<pair.mass;
    rows<<','<<mass<<','<<tolerance<<','<<expected_invalid;
    pass=pass&&total_failed(audit)==before;rows<<','<<pass<<'\n';
  }
  audit.failed_cases+=!pass;
}
Input physical(float p0,float p1,float eta0,float eta1,float phi0,float phi1,double object_mass) {
  Input input{{p0,p1},{eta0,eta1},{phi0,phi1},{}};
  for(std::size_t index=0;index<2;++index)input.energy.push_back(float(std::hypot(double(input.pt[index])*std::cosh(double(input.eta[index])),object_mass)));
  return input;
}
void save_summary(const Audit& audit,const std::filesystem::path& path) {
  std::ofstream file(path);file.exceptions(std::ios::badbit|std::ios::failbit);file<<std::setprecision(21);
  file<<"{\"deterministic_seed\":20261012,\"cases\":"<<audit.cases<<",\"failed_cases\":"<<audit.failed_cases
      <<",\"invalid_collections\":"<<audit.invalid_collections<<",\"negative_reference_pairs\":"<<audit.negative_reference_pairs
      <<",\"old_negative_pairs\":"<<audit.old_negative_pairs<<",\"new_negative_pairs\":"<<audit.new_negative_pairs
      <<",\"mass_tolerance\":\"1e-7+1e-10*abs(native_input_long_double_reference_mass)\""
      <<",\"component_diagnostic_bound\":\"64*double_epsilon*max(sum_abs_component_terms,sum_abs_native_pT_for_px_py,1); includes inherited phi restriction rounding\""
      <<",\"mass2_diagnostic_bound\":\"64*double_epsilon*max(E2+px2+py2+pz2,1)\""
      <<",\"angular_diagnostic_bound\":\"1e-12 radians (eta dimensionless)\""
      <<",\"relative_residual_convention\":\"only nonzero references; undefined for exact zero\""
      <<",\"long_double_mantissa_bits\":"<<std::numeric_limits<long double>::digits<<",\"categories\":{";
  bool comma=false;for(const auto& [name,count]:audit.categories){if(comma)file<<',';comma=true;file<<'"'<<name<<"\":"<<count;}
  file<<"},\"metrics\":{";comma=false;
  for(const auto& [name,value]:audit.metrics) {
    if(comma)file<<',';
    comma=true;
    file<<'"'<<name<<"\":{\"compared\":"<<value.compared<<",\"failed\":"<<value.failed<<",\"max_absolute\":"<<value.max_absolute
        <<",\"max_relative_nonzero_reference\":"<<value.max_relative<<",\"max_tolerance\":"<<value.max_tolerance<<'}';
  }
  file<<"}}\n";file.close();
}
}
int main(int argc,char** argv) {
  try {
    if(argc>2)throw std::invalid_argument("Optional argument: local stress evidence parent directory");
#ifdef ATLAS_STEP1_OUTPUT_DIR
    const auto default_parent=std::filesystem::path(ATLAS_STEP1_OUTPUT_DIR)/"cartesian_stability";
#else
    const auto default_parent=std::filesystem::temp_directory_path()/"atlas_cartesian_stability";
#endif
    const auto parent=argc==2?std::filesystem::path(argv[1]):default_parent;
    const auto directory=parent/std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    if(std::filesystem::exists(directory))throw std::runtime_error("Stress evidence directory exists");
    std::filesystem::create_directories(directory);
    std::ofstream rows(directory/"cases.csv");rows.exceptions(std::ios::badbit|std::ios::failbit);rows<<std::setprecision(21)
      <<"case_id,category,scale,collection_valid,B_pair_valid,pt0,eta0,phi0,E0,pt1,eta1,phi1,E1,C_mass2,A_mass2,B_mass2,A_mass,B_mass,C_mass,mass_tolerance,expected_invalid,case_pass\n";
    Audit audit;
    // Native Float_t values from checksum-pinned DSID343981 entry5888:
    // source SHA256002e890c517e03ba59c49bc0852d0fdcd200e0d48add7ca189228a6f82965c56.
    const Input original{{60.81133270263671875F,60.1185302734375F},{-2.322521209716796875F,-1.87638890743255615234F},
      {1.00584459304809570312F,-2.13731408119201660156F},{313.159759521484375F,200.886810302734375F}};
    run(audit,rows,"exact_verified_MC343981_entry5888",original);
    const auto exact_collection=construct(original.pt,original.eta,original.phi,original.energy,2,1.);
    const auto exact_reference=reference(original,exact_collection);const auto old=exact_collection.ordered[0].p4+exact_collection.ordered[1].p4;
    if(std::abs(std::sqrt(old.M2())-std::sqrt(exact_reference.mass2))<=mass_tolerance(std::sqrt(exact_reference.mass2)))
      throw std::runtime_error("Original coordinate conversion failure was not reproduced");
    std::mt19937 random(20261012);const auto uniform=[&](double low,double high){return float(low+(high-low)*(double(random())/double(std::mt19937::max())));};
    for(int index=0;index<1024;++index) {
      const float p=uniform(5,200),q=uniform(5,200),eta=uniform(-2.5,2.5),phi=uniform(-3,3);
      run(audit,rows,"general_massive_native_float32",physical(p,q,eta,uniform(-2.5,2.5),phi,uniform(-3,3),10));
      const auto cancel=physical(p,std::nextafter(p,0.F),uniform(-4,-2),uniform(-4,-2),phi,float(phi+std::numbers::pi),5);
      run(audit,rows,"nearly_cancelled_transverse_large_negative_pz",cancel);
      run(audit,rows,"back_to_back_photons",physical(p,q,0,0,0,float(std::numbers::pi),0));
      run(audit,rows,"boosted_small_opening_massive",physical(uniform(200,1000),uniform(200,1000),eta,float(eta+.01F),phi,float(phi+.002F),10));
      run(audit,rows,"extreme_negative_eta",physical(uniform(.05,1),uniform(.05,1),-9,-10,phi,float(phi+2),10));
      const float binary=float(1+(index%127));
      run(audit,rows,"exact_collinear_lightlike",{{binary,binary*.5F},{0,0},{0,0},{binary,binary*.5F}});
      run(audit,rows,"nearly_massless_small_opening",physical(p,q,0,0,0,uniform(.001,.01),0));
      const Input negative_pair{{binary,binary},{0,0},{0,0},{std::nextafter(binary,0.F),std::nextafter(binary,0.F)}};
      run(audit,rows,"negative_pair_float32_energy_rounding",negative_pair,true);
      Input bad=physical(p,q,eta,eta,phi,phi,10);const auto nonfinite=(index%2)?std::numeric_limits<float>::infinity():std::numeric_limits<float>::quiet_NaN();
      switch(index%4){case 0:bad.pt[0]=nonfinite;break;case 1:bad.eta[0]=nonfinite;break;case 2:bad.phi[0]=nonfinite;break;default:bad.energy[0]=nonfinite;}
      run(audit,rows,"nonfinite_input_rejection",bad,true);
      Input permutation=physical(p,q,eta,-eta,phi,-phi,10);const auto baseline=leading_pair(construct(permutation.pt,permutation.eta,permutation.phi,permutation.energy,2,1));
      for(auto* values:{&permutation.pt,&permutation.eta,&permutation.phi,&permutation.energy})std::reverse(values->begin(),values->end());
      run(audit,rows,"native_object_permutation",permutation);
      const auto reversed=leading_pair(construct(permutation.pt,permutation.eta,permutation.phi,permutation.energy,2,1));
      if(baseline.mass!=reversed.mass||baseline.delta_eta!=reversed.delta_eta||baseline.delta_phi!=reversed.delta_phi||baseline.delta_r!=reversed.delta_r)++audit.failed_cases;
      run(audit,rows,"genuine_spacelike_object_rejection",{{binary,binary},{0,0},{0,0},{binary*.9F,binary*.9F}},true);
      run(audit,rows,"extreme_eta_overflow_rejection",{{1,1},{1000,-1000},{0,0},{1,1}},true);
      const float high_pt=float(256+(index%16)*256),tiny_angle=float(std::pow(10.,uniform(-8,-3)));
      run(audit,rows,"high_energy_near_collinear_lightlike_native_float32",{{high_pt,high_pt},{0,0},{0,tiny_angle},{high_pt,high_pt}});
      run(audit,rows,"near_massless_native_float32_plus_minus_pi",{{high_pt,high_pt},{0,0},{float(std::numbers::pi),-float(std::numbers::pi)},{high_pt,high_pt}});
      Input scaled=physical(p,q,eta,-eta,phi,-phi,10);
      for(auto* values:{&scaled.pt,&scaled.energy})for(float& value:*values)value*=1000.F;
      scaled.scale=.001;run(audit,rows,"native_float32_mev_to_gev_scale",scaled);
    }
    rows.close();save_summary(audit,directory/"summary.json");
    std::ofstream marker(parent/"current_stress_path.txt");marker<<directory.string()<<'\n';marker.close();
    const auto& mass=audit.metrics.at("B_mass");
    std::cout<<"CARTESIAN_STRESS_CASES="<<audit.cases<<" FAILED_CASES="<<audit.failed_cases<<" MASS_COMPARISONS="<<mass.compared<<" MASS_CLOSURE_FAILURES="<<mass.failed
             <<std::setprecision(21)<<"\nMAX_MASS_ABSOLUTE_ERROR="<<mass.max_absolute<<"\nMAX_MASS_RELATIVE_ERROR="<<mass.max_relative
             <<"\nMASS_TOLERANCE=1e-7+1e-10*abs(reference_mass)\nEVIDENCE="<<directory<<'\n';
    if(audit.cases<10000||audit.failed_cases||total_failed(audit))throw std::runtime_error("Cartesian independent stress contract failed; all evidence retained");
    std::cout<<"PASS deterministic native-input Cartesian stability\n";
  }catch(const std::exception& error){std::cerr<<"FAIL: "<<error.what()<<'\n';return 1;}
}

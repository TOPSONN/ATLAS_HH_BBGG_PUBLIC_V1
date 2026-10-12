#include "AtlasMCEvents.h"
#include "AtlasExploratorySelection.h"
#include "AtlasMCMatching.h"
#include <TH1D.h>
#include <TFile.h>
#include <TNamed.h>
#include <array>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <map>
#include <numbers>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace {
long long integer(const char* input) {
  std::size_t used=0;const std::string text=input;const auto value=std::stoll(text,&used);
  if(used!=text.size())throw std::invalid_argument("Expected complete integer argument");
  return value;
}
double positive(const char* input) {
  std::size_t used=0;const std::string text=input;const auto value=std::stod(text,&used);
  if(used!=text.size() || !std::isfinite(value) || value<=0)throw std::invalid_argument("Expected positive finite scale");
  return value;
}
std::string quote(const std::string& value) {
  std::string escaped="\"";
  for(char c:value){if(c=='"'||c=='\\')escaped+='\\';escaped+=c;}
  return escaped+'"';
}
std::string number_or_null(const std::optional<double>& value) {
  if(!value)return "null";
  std::ostringstream text;text<<std::setprecision(17)<<*value;return text.str();
}
std::string number_array(const std::vector<double>& values) {
  std::ostringstream text;text<<std::setprecision(17)<<'[';
  for(std::size_t index=0;index<values.size();++index){if(index)text<<',';text<<values[index];}
  text<<']';return text.str();
}
struct MassClosure {
  std::uint64_t tested=0,failed=0;
  long double max_absolute=0,max_relative=0,max_tolerance=0;
  bool observe(const atlas::kinematics::Collection& collection,const atlas::kinematics::Pair& pair,
               const atlas::kinematics::RVec& pt,const atlas::kinematics::RVec& eta,
               const atlas::kinematics::RVec& phi,const atlas::kinematics::RVec& energy,double scale) {
    if(!pair.valid)return true;
    ++tested;long double px=0,py=0,pz=0,e=0;
    // Independent Cartesian arithmetic starts from the same two raw indices.
    // It neither reads ROOT p4 components nor clamps a negative invariant.
    for(std::size_t position=0;position<2;++position) {
      const auto index=collection.ordered[position].input_index;
      const long double p=static_cast<long double>(pt[index])*scale;
      px+=p*std::cos(static_cast<long double>(phi[index]));py+=p*std::sin(static_cast<long double>(phi[index]));
      pz+=p*std::sinh(static_cast<long double>(eta[index]));e+=static_cast<long double>(energy[index])*scale;
    }
    const long double square=e*e-px*px-py*py-pz*pz;
    if(!std::isfinite(square) || square<0){++failed;return false;}
    const long double reference=std::sqrt(square),difference=std::abs(static_cast<long double>(pair.mass)-reference);
    const long double tolerance=1e-7L+1e-10L*std::abs(reference);
    max_absolute=std::max(max_absolute,difference);max_tolerance=std::max(max_tolerance,tolerance);
    if(reference>0)max_relative=std::max(max_relative,difference/reference);
    const bool pass=std::isfinite(difference)&&difference<=tolerance;failed+=!pass;return pass;
  }
};
struct MatchTotals {
  std::uint64_t events=0,truth_available_events=0,truth_missing_events=0,reco_provided=0,truth_provided=0;
  std::uint64_t eligible_reco=0,eligible_truth=0,matched=0,unmatched_reco=0,unmatched_truth=0;
  std::uint64_t candidate_edges=0,locally_ambiguous_reco=0,competed_truth=0,events_with_local_ambiguity=0;
};
using MatchKey=std::tuple<std::string,double,std::string>;
void accumulate_matching(std::map<MatchKey,MatchTotals>& totals,std::ofstream& output,
                         const atlas::mc_matching::EventResult& event,bool selected,const atlas::mc_matching::Config& config) {
  const auto collection=[&](const std::string& group,const atlas::mc_matching::ObjectResult& objects,const std::vector<double>& thresholds) {
    for(const std::string scope:{"ALL_VALID","C9"}) {
      if(scope=="C9"&&!selected)continue;
      for(std::size_t index=0;index<thresholds.size();++index) {
        auto& sum=totals.at({group,thresholds[index],scope});++sum.events;sum.reco_provided+=objects.reco_provided;
        if(!objects.truth_available){++sum.truth_missing_events;continue;}
        ++sum.truth_available_events;sum.truth_provided+=objects.truth_provided;
        const auto& scan=objects.thresholds.at(index);
        if(scan.threshold!=thresholds[index])throw std::runtime_error("MC matching threshold identity changed");
        const auto& matching=scan.assignments;
        sum.eligible_reco+=matching.eligible_reco;sum.eligible_truth+=matching.eligible_reference;sum.matched+=matching.assignments.size();
        sum.unmatched_reco+=matching.unmatched_reco_ids.size();sum.unmatched_truth+=matching.unmatched_reference_ids.size();sum.candidate_edges+=matching.candidate_edges;
        sum.locally_ambiguous_reco+=matching.locally_ambiguous_reco_ids.size();sum.competed_truth+=matching.competed_reference_ids.size();
        sum.events_with_local_ambiguity+=!matching.locally_ambiguous_reco_ids.empty()||!matching.competed_reference_ids.empty();
        for(const auto& assignment:matching.assignments)
          output<<event.dsid<<','<<event.run<<','<<event.event<<','<<event.source_entry<<','<<group<<','<<scan.threshold<<','<<scope<<','
                <<assignment.reco_id<<','<<assignment.reference_id<<','<<assignment.delta_r<<'\n';
      }
    }
  };
  collection("photon",event.photons,config.photon_thresholds);collection("jet",event.jets,config.jet_thresholds);
}
}
int main(int argc,char** argv) {
  try {
    if(argc!=9)throw std::invalid_argument("Usage: phase4_mc_reconstruction input.root NEW_output expected_DSID start exclusive_end scale_to_GeV PROVISIONAL selection.ini");
    const auto channel=integer(argv[3]),start=integer(argv[4]),end=integer(argv[5]);const double scale=positive(argv[6]);
    if(channel<=0 || static_cast<unsigned long long>(channel)>std::numeric_limits<std::uint32_t>::max())throw std::invalid_argument("Expected DSID must fit positive uint32");
    if(start<0 || end<=start || end-start>10000)throw std::invalid_argument("MC range must be positive, explicit and bounded by 10000 entries");
    if(std::string(argv[7])!="PROVISIONAL")throw std::invalid_argument("Phase 4 MC unit status must remain PROVISIONAL");
    const std::filesystem::path output(argv[2]);if(std::filesystem::exists(output))throw std::runtime_error("MC output exists; refusing overwrite");
    const auto config=atlas::selection::read_config(argv[8]);
    atlas::mc::Reader reader(argv[1],static_cast<std::uint32_t>(channel));
    if(end>reader.entries())throw std::out_of_range("Requested MC range extends beyond local tree");
    std::filesystem::create_directories(output);
    std::ofstream rows(output/"events.csv"),diagnostics(output/"normalization_sf_diagnostics.csv"),schema(output/"native_bindings.csv"),assignments(output/"matching_assignments.csv"),truth_objects(output/"truth_objects.csv");
    rows.exceptions(std::ios::badbit|std::ios::failbit);diagnostics.exceptions(std::ios::badbit|std::ios::failbit);schema.exceptions(std::ios::badbit|std::ios::failbit);
    assignments.exceptions(std::ios::badbit|std::ios::failbit);truth_objects.exceptions(std::ios::badbit|std::ios::failbit);
    rows<<std::setprecision(17)<<"dsid,entry,run,event,mc_weight,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,C9_selected,roundoff_objects,invalid_reason,cartesian_mass_closure_pass\n";
    diagnostics<<std::setprecision(17)<<"dsid,entry,run,event,branch,native_type,value,value_status,usage\n";
    schema<<"branch,native_type,role\n";for(const auto& field:reader.schema())schema<<field.name<<','<<field.type<<','<<field.role<<'\n';
    assignments<<std::setprecision(17)<<"dsid,run,event,entry,object_group,threshold,scope,reco_index,truth_index,delta_r\n";
    truth_objects<<std::setprecision(17)<<"dsid,run,event,entry,object_group,index,raw_pt,raw_eta,raw_phi,raw_mass,raw_energy,mass_available,energy_available,usage\n";
    std::vector<std::unique_ptr<TH1D>> histograms;
    const auto add=[&](const char* name,int bins,double low,double high) {
      auto histogram=std::make_unique<TH1D>(name,"Raw unweighted MC counts;native diagnostic;Raw counts / bin",bins,low,high);
      histogram->SetDirectory(nullptr);histograms.push_back(std::move(histogram));
    };
    add("mc_m_gg",80,0,400);add("mc_m_jj",80,0,800);add("mc_deltaR_gg",60,0,6);add("mc_deltaR_jj",60,0,6);
    add("mc_photon_pt",60,0,300);add("mc_jet_pt",60,0,300);
    add("mc_m_gg_C9",70,100,170);add("mc_m_jj_C9",80,0,800);add("mc_photon_pt_C9",60,0,300);add("mc_jet_pt_C9",60,0,300);
    std::array<std::uint64_t,10> counts{};std::uint64_t positive_weights=0,negative_weights=0,zero_weights=0,invalid=0,roundoff=0;
    std::uint64_t negative_truth_jet_mass=0,nonfinite_truth_jet_mass=0,negative_btag_sf=0;
    std::optional<double> minimum_truth_jet_mass,minimum_btag_sf;
    long double sumw=0,sumw2=0;std::set<std::tuple<std::uint32_t,std::uint32_t,std::uint64_t>> identities;
    MassClosure closure;
    atlas::mc_matching::Config matching_config;matching_config.unit_status=atlas::mc_matching::UnitStatus::Provisional;
    matching_config.reco_scale_to_gev=scale;matching_config.truth_scale_to_gev=scale;
    std::map<MatchKey,MatchTotals> matching_totals;
    for(const std::string scope:{"ALL_VALID","C9"}) {
      for(double threshold:matching_config.photon_thresholds)matching_totals.emplace(MatchKey{"photon",threshold,scope},MatchTotals{});
      for(double threshold:matching_config.jet_thresholds)matching_totals.emplace(MatchKey{"jet",threshold,scope},MatchTotals{});
    }
    for(auto entry=start;entry<end;++entry) {
      const auto raw=reader.read(entry);const auto& source=raw.reconstructed;
      if(!identities.emplace(raw.dsid,source.run,source.event).second)throw std::runtime_error("Duplicate MC DSID/run/event identity inside processed file range");
      const auto weight=raw.generator_weight;positive_weights+=weight>0;negative_weights+=weight<0;zero_weights+=weight==0;sumw+=weight;sumw2+=static_cast<long double>(weight)*weight;
      for(const auto& [name,value]:raw.diagnostics) {
        const auto field=std::find_if(reader.schema().begin(),reader.schema().end(),[&](const auto& f){return f.name==name;});
        diagnostics<<raw.dsid<<','<<entry<<','<<source.run<<','<<source.event<<','<<name<<','<<field->type<<','<<value<<','<<(std::isfinite(value)?"FINITE_DIAGNOSTIC":"NONFINITE_DIAGNOSTIC")<<",NOT_APPLIED\n";
        if(name=="ScaleFactor_BTAG" && std::isfinite(value)) {
          negative_btag_sf+=value<0;
          minimum_btag_sf=minimum_btag_sf?std::min(*minimum_btag_sf,value):value;
        }
      }
      if(raw.truth_jets.mass_available)for(float value:raw.truth_jets.mass) {
        if(!std::isfinite(value)){++nonfinite_truth_jet_mass;continue;}
        negative_truth_jet_mass+=value<0;
        minimum_truth_jet_mass=minimum_truth_jet_mass?std::min(*minimum_truth_jet_mass,double(value)):double(value);
      }
      const auto save_truth=[&](const char* group,const atlas::mc::TruthCollection& collection) {
        if(!collection.available)return;
        for(std::size_t index=0;index<collection.pt.size();++index) {
          truth_objects<<raw.dsid<<','<<source.run<<','<<source.event<<','<<entry<<','<<group<<','<<index<<','<<collection.pt[index]<<','<<collection.eta[index]<<','<<collection.phi[index]<<',';
          if(collection.mass_available)truth_objects<<collection.mass[index];
          truth_objects<<',';
          if(collection.energy_available)truth_objects<<collection.energy[index];
          truth_objects<<','<<collection.mass_available<<','<<collection.energy_available<<",RAW_PRESERVED_NO_MASS_OR_ENERGY_IN_GEOMETRY\n";
        }
      };
      save_truth("photon",raw.truth_photons);save_truth("jet",raw.truth_jets);
      const auto photons=atlas::kinematics::construct(source.photon_pt,source.photon_eta,source.photon_phi,source.photon_e,source.photon_n,scale);
      const auto jets=atlas::kinematics::construct(source.jet_pt,source.jet_eta,source.jet_phi,source.jet_e,source.jet_n,scale);
      const auto gg=atlas::kinematics::leading_pair(photons),jj=atlas::kinematics::leading_pair(jets);
      bool angular=true,energy=true;
      for(const auto* values:{&source.photon_phi,&source.jet_phi})for(float value:*values)
        angular=angular&&std::isfinite(value)&&std::abs(value)<=std::numbers::pi+1e-5;
      for(const auto* values:{&source.photon_e,&source.jet_e})for(float value:*values)
        energy=energy&&std::isfinite(value)&&double(value)*scale<=13000.;
      const bool valid=photons.valid&&jets.valid&&(!gg.available||gg.valid)&&(!jj.available||jj.valid)&&angular&&energy;
      bool closure_pass=true;
      if(valid) {
        closure_pass=closure.observe(photons,gg,source.photon_pt,source.photon_eta,source.photon_phi,source.photon_e,scale);
        closure_pass=closure.observe(jets,jj,source.jet_pt,source.jet_eta,source.jet_phi,source.jet_e,scale)&&closure_pass;
      }
      std::string issue=!photons.valid?"photon_"+photons.issue:(!jets.valid?"jet_"+jets.issue:(!angular?"invalid_phi_convention":(!energy?"energy_exceeds_13TeV_or_nonfinite":
        (gg.available&&!gg.valid?"gg_"+gg.issue:(jj.available&&!jj.valid?"jj_"+jj.issue:"")))));
      invalid+=!valid;const auto rounded=photons.roundoff_objects+jets.roundoff_objects;roundoff+=rounded;
      atlas::selection::Event selected;selected.source_valid=valid;selected.photons=source.photon_n;selected.jets=source.jet_n;
      const double missing=std::numeric_limits<double>::quiet_NaN();
      const auto object_value=[&](const auto& collection,std::size_t index,bool pt) {
        return valid&&index<collection.ordered.size()?(pt?collection.ordered[index].p4.Pt():collection.ordered[index].p4.Eta()):missing;
      };
      for(std::size_t index=0;index<2;++index) {
        selected.photon_pt[index]=object_value(photons,index,true);selected.photon_eta[index]=object_value(photons,index,false);
        selected.jet_pt[index]=object_value(jets,index,true);selected.jet_eta[index]=object_value(jets,index,false);
      }
      selected.mgg=valid&&gg.valid?gg.mass:missing;selected.mjj=valid&&jj.valid?jj.mass:missing;
      const auto passed=atlas::selection::evaluate(selected,config);for(std::size_t index=0;index<counts.size();++index)counts[index]+=passed[index];
      if(valid)accumulate_matching(matching_totals,assignments,atlas::mc_matching::match_event(raw,entry,matching_config),passed[9],matching_config);
      rows<<raw.dsid<<','<<entry<<','<<source.run<<','<<source.event<<','<<weight<<','<<valid<<','<<source.photon_n<<','<<source.jet_n;
      for(double value:{selected.photon_pt[0],selected.photon_pt[1],selected.photon_eta[0],selected.photon_eta[1],selected.jet_pt[0],selected.jet_pt[1],selected.jet_eta[0],selected.jet_eta[1],
                        selected.mgg,selected.mjj,valid&&gg.valid?gg.delta_r:missing,valid&&jj.valid?jj.delta_r:missing}) {
        rows<<',';if(std::isfinite(value))rows<<value;
      }
      rows<<','<<passed[9]<<','<<rounded<<','<<issue<<','<<closure_pass<<'\n';
      if(valid) {
        if(gg.valid){histograms[0]->Fill(gg.mass);histograms[2]->Fill(gg.delta_r);}
        if(jj.valid){histograms[1]->Fill(jj.mass);histograms[3]->Fill(jj.delta_r);}
        for(const auto& object:photons.ordered)histograms[4]->Fill(object.p4.Pt());
        for(const auto& object:jets.ordered)histograms[5]->Fill(object.p4.Pt());
      }
      if(passed[9]) {
        histograms[6]->Fill(gg.mass);histograms[7]->Fill(jj.mass);
        for(double value:selected.photon_pt)histograms[8]->Fill(value);
        for(double value:selected.jet_pt)histograms[9]->Fill(value);
      }
    }
    rows.close();diagnostics.close();schema.close();assignments.close();truth_objects.close();
    const std::array<const char*,10> names{"C0_GamGam_MC_input","C1_valid_kinematics","C2_two_photons","C3_leading_photon_pt","C4_subleading_photon_pt","C5_photon_eta_acceptance","C6_diphoton_mass_window","C7_two_jets","C8_leading_two_jet_pt","C9_leading_two_jet_eta"};
    std::ofstream cutflow(output/"cutflow.csv");cutflow.exceptions(std::ios::badbit|std::ios::failbit);
    cutflow<<std::setprecision(17)<<"dsid,selection_name,events_before,events_after,rejected_events,conditional_fraction,cumulative_fraction,definition_version,validation_status\n";
    for(std::size_t index=0;index<counts.size();++index) {
      const auto before=index?counts[index-1]:counts[0];cutflow<<channel<<','<<names[index]<<','<<before<<','<<counts[index]<<','<<before-counts[index]<<',';
      if(before)cutflow<<double(counts[index])/double(before);
      cutflow<<','<<double(counts[index])/double(counts[0])<<','<<config.version<<",PROVISIONAL_RAW_UNWEIGHTED_MC\n";
    }
    cutflow.close();
    std::ofstream matching_summary(output/"matching_threshold_summary.csv");matching_summary.exceptions(std::ios::badbit|std::ios::failbit);
    matching_summary<<std::setprecision(17)<<"dsid,object_group,threshold,scope,events,truth_available_events,truth_missing_events,reco_provided,truth_provided,eligible_reco,eligible_truth,matched_pairs,unmatched_reco,unmatched_truth,candidate_edges,locally_ambiguous_reco,competed_truth,events_with_local_ambiguity,geometric_reco_match_fraction,geometric_truth_match_fraction,classification\n";
    for(const auto& [key,value]:matching_totals) {
      const auto& [group,threshold,scope]=key;
      matching_summary<<channel<<','<<group<<','<<threshold<<','<<scope<<','<<value.events<<','<<value.truth_available_events<<','<<value.truth_missing_events<<','<<value.reco_provided<<','<<value.truth_provided<<','
        <<value.eligible_reco<<','<<value.eligible_truth<<','<<value.matched<<','<<value.unmatched_reco<<','<<value.unmatched_truth<<','<<value.candidate_edges<<','<<value.locally_ambiguous_reco<<','<<value.competed_truth<<','<<value.events_with_local_ambiguity<<',';
      if(value.eligible_reco)matching_summary<<double(value.matched)/double(value.eligible_reco);
      matching_summary<<',';
      if(value.eligible_truth)matching_summary<<double(value.matched)/double(value.eligible_truth);
      matching_summary<<",PROVISIONAL_GEOMETRIC_ONLY_NOT_ORIGIN_PURITY_OR_OFFICIAL_EFFICIENCY\n";
    }
    matching_summary.close();
    std::ostringstream summary;summary<<std::setprecision(17)
      <<"{\"dsid\":"<<channel<<",\"start_entry\":"<<start<<",\"end_exclusive\":"<<end<<",\"entries_read\":"<<counts[0]
      <<",\"invalid_kinematics\":"<<invalid<<",\"C9_selected\":"<<counts[9]<<",\"scale_to_gev\":"<<scale<<",\"unit_status\":\"PROVISIONAL\""
      <<",\"selection_definition\":"<<quote(config.version)<<",\"negative_roundoff_objects\":"<<roundoff
      <<",\"mass_closure_status\":"<<quote(closure.failed?"FAIL":(closure.tested?"PASS":"NOT_TESTED"))
      <<",\"mass_closure_pairs\":"<<closure.tested<<",\"mass_closure_failures\":"<<closure.failed
      <<",\"mass_max_absolute_deviation\":"<<closure.max_absolute<<",\"mass_max_relative_deviation\":"<<closure.max_relative
      <<",\"mass_closure_max_tolerance\":"<<closure.max_tolerance<<",\"mass_closure_tolerance\":\"1e-7+1e-10*abs(long_double_reference_mass)\""
      <<",\"mass_closure_reference\":\"independent long-double Cartesian sum from same raw leading-pair indices; negative mass2 is never clamped\""
      <<",\"weighting\":\"RAW_UNWEIGHTED\",\"normalization_applied\":false,\"scale_factors_applied\":false"
      <<",\"truth_matching\":\"PROVISIONAL_SAME_EVENT_GEOMETRIC_ONLY\",\"truth_matching_population\":\"all valid reconstructed events; C9 is a separately reported subset\""
      <<",\"truth_scale_to_gev\":"<<scale<<",\"matching_eligibility\":\"all objects with photon pt>25 and abs(eta)<2.37; jet pt>25 and abs(eta)<2.5; no photon crack/ID/isolation/origin/flavour cut\""
      <<",\"photon_matching_thresholds\":"<<number_array(matching_config.photon_thresholds)<<",\"jet_matching_thresholds\":"<<number_array(matching_config.jet_thresholds)
      <<",\"max_eligible_objects_per_collection\":"<<matching_config.max_eligible_objects_per_collection<<",\"max_candidate_pairs\":"<<matching_config.max_candidate_pairs
      <<",\"matching_denominator_scope\":\"eligible objects in truth-available valid reconstructed events; empty denominators have undefined CSV fractions\""
      <<",\"truth_mass_quality\":\"UNKNOWN_SIGNED_NATIVE_MASS_PRESERVED_UNUSED_GEOMETRY\",\"truth_energy_inferred\":false"
      <<",\"negative_truth_jet_mass_values\":"<<negative_truth_jet_mass<<",\"nonfinite_truth_jet_mass_values\":"<<nonfinite_truth_jet_mass
      <<",\"minimum_truth_jet_mass\":"<<number_or_null(minimum_truth_jet_mass)
      <<",\"negative_btag_scale_factors\":"<<negative_btag_sf<<",\"minimum_btag_scale_factor\":"<<number_or_null(minimum_btag_sf)
      <<",\"raw_diagnostic_population\":\"all processed entries, including invalid reconstructed events\""
      <<",\"btag_classification\":\"NOT_APPLIED\",\"duplicate_identity_scope\":\"processed entry range within this file\"}\n";
    std::ofstream summary_file(output/"summary.json");summary_file.exceptions(std::ios::badbit|std::ios::failbit);summary_file<<summary.str();summary_file.close();
    std::ofstream weights(output/"weight_diagnostics.json");weights.exceptions(std::ios::badbit|std::ios::failbit);
    weights<<std::setprecision(21)<<"{\"dsid\":"<<channel<<",\"entries\":"<<counts[0]<<",\"positive\":"<<positive_weights<<",\"negative\":"<<negative_weights
      <<",\"zero\":"<<zero_weights<<",\"sumw\":"<<sumw<<",\"sumw2\":"<<sumw2<<",\"usage\":\"DIAGNOSTIC_ONLY_NOT_NORMALIZATION\"}\n";weights.close();
    TFile root((output/"histograms.root").c_str(),"CREATE");if(root.IsZombie())throw std::runtime_error("Cannot preserve raw MC histogram objects");
    std::ofstream inventory(output/"histogram_inventory.csv");inventory.exceptions(std::ios::badbit|std::ios::failbit);inventory<<"name,filled_values,in_range,underflow,overflow,weighting\n";
    for(const auto& histogram:histograms) {
      if(histogram->Write()<=0)throw std::runtime_error("Cannot write native MC histogram");
      inventory<<std::setprecision(17)<<histogram->GetName()<<','<<histogram->GetEntries()<<','<<histogram->Integral()<<','<<histogram->GetBinContent(0)<<','<<histogram->GetBinContent(histogram->GetNbinsX()+1)<<",RAW_UNWEIGHTED\n";
    }
    TNamed metadata("phase4_mc_metadata",summary.str().c_str());metadata.Write();root.Close();
    inventory.close();
    if(closure.failed)throw std::runtime_error("Independent Cartesian MC pair-mass closure failed; diagnostic evidence retained");
    std::cout<<"PASS bounded raw MC reconstruction DSID="<<channel<<" read="<<counts[0]<<" C9="<<counts[9]<<" invalid="<<invalid
      <<" negative_weights="<<negative_weights<<" units=PROVISIONAL normalization=NOT_APPLIED\n";
  }catch(const std::exception& error){std::cerr<<"FAIL: "<<error.what()<<'\n';return 1;}
}

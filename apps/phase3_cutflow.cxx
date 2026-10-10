#include "AtlasExploratorySelection.h"
#include <TCanvas.h>
#include <TH1D.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TLatex.h>
#include <TLegend.h>
#include <TGaxis.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <vector>
#include <stdexcept>
#include <cmath>
#include <cstdint>

namespace {
std::vector<std::string> split(const std::string& line) {
  std::vector<std::string> fields; std::size_t first=0;
  for(std::size_t i=0;i<=line.size();++i) if(i==line.size() || line[i]==',') { fields.push_back(line.substr(first,i-first)); first=i+1; }
  return fields;
}
double number(const std::string& text) {
  if(text.empty()) return std::numeric_limits<double>::quiet_NaN();
  std::size_t used=0; const double value=std::stod(text,&used);
  if(used!=text.size()) throw std::invalid_argument("Invalid numeric cache column");
  return value;
}
long long integer(const std::string& text) {
  std::size_t used=0; const auto value=std::stoll(text,&used);
  if(used!=text.size()) throw std::invalid_argument("Invalid integer cache column");
  return value;
}
}
int main(int argc,char** argv) {
  try {
    if(argc!=5) throw std::invalid_argument("Usage: phase3_cutflow phase2_events.csv selection.ini new_output_dir VERIFIED|PROVISIONAL");
    const std::string status=argv[4]; if(status!="VERIFIED" && status!="PROVISIONAL") throw std::invalid_argument("Unit/reconstruction gate blocks real selection");
    if(!std::filesystem::is_regular_file(argv[1]) || std::string(argv[1]).find("://")!=std::string::npos) throw std::invalid_argument("Local derived cache required");
    const auto config=atlas::selection::read_config(argv[2]); const std::filesystem::path output(argv[3]);
    if(std::filesystem::exists(output)) throw std::runtime_error("Output exists; refusing overwrite");
    std::ifstream input(argv[1]); std::string line; std::getline(input,line); if(!line.empty()&&line.back()=='\r') line.pop_back();
    const auto header=split(line); std::map<std::string,std::size_t> columns;
    for(std::size_t i=0;i<header.size();++i) if(!columns.emplace(header[i],i).second) throw std::runtime_error("Duplicate cache header");
    if(header.size()!=28) throw std::runtime_error("Expected Phase 2 cache schema v1 with 28 columns");
    for(auto key:{"entry","valid","photon_n","jet_n","photon1_pt","photon2_pt","photon1_eta","photon2_eta","jet1_pt","jet2_pt","jet1_eta","jet2_eta","m_gg","m_jj","p1_tight_id","p2_tight_id","p1_tight_iso","p2_tight_iso"})
      if(!columns.contains(key)) throw std::runtime_error("Required cache field missing");
    std::array<std::uint64_t,10> counts{}; std::uint64_t selected_tight=0,selected_tight_iso=0,missing_flags=0;
    long long previous=-1,first=-1;
    TH1D mgg("m_gg_preselection",";m_{#gamma#gamma} [GeV];Raw selected events / bin",70,100,170);
    TH1D mjj("m_jj_preselection",";m_{jj} [GeV] (inclusive leading jets);Raw selected events / bin",80,0,800);
    TH1D ppt("photon_pt_selected",";Selected leading-photon p_{T} [GeV];Raw selected objects / bin",60,0,300);
    TH1D jpt("jet_pt_selected",";Selected leading-jet p_{T} [GeV];Raw selected objects / bin",60,0,300);
    for(auto* h:{&mgg,&mjj,&ppt,&jpt}) h->SetDirectory(nullptr);
    while(std::getline(input,line)) {
      if(!line.empty()&&line.back()=='\r') line.pop_back();
      const auto fields=split(line);
      if(fields.size()!=header.size()) throw std::runtime_error("Cache row length mismatch");
      auto get=[&](const char* key)->const std::string& {return fields.at(columns.at(key));};
      const auto entry=integer(get("entry")); if(entry<=previous) throw std::runtime_error("Duplicate or non-increasing entry order");
      if(first<0) first=entry;
      previous=entry;
      const auto valid=integer(get("valid")),np=integer(get("photon_n")),nj=integer(get("jet_n"));
      if((valid!=0&&valid!=1) || np<0 || nj<0 || np>100000 || nj>100000) throw std::runtime_error("Invalid cache counts/valid flag");
      atlas::selection::Event e; e.source_valid=valid==1; e.photons=static_cast<int>(np);e.jets=static_cast<int>(nj);
      e.photon_pt={number(get("photon1_pt")),number(get("photon2_pt"))};e.photon_eta={number(get("photon1_eta")),number(get("photon2_eta"))};
      e.jet_pt={number(get("jet1_pt")),number(get("jet2_pt"))};e.jet_eta={number(get("jet1_eta")),number(get("jet2_eta"))};
      e.mgg=number(get("m_gg"));e.mjj=number(get("m_jj"));
      auto flag=[&](const char* key) {if(get(key).empty()) return -1; const auto value=integer(get(key)); if(value!=0&&value!=1) throw std::runtime_error("Nonboolean raw photon flag");return static_cast<int>(value);};
      e.tight_id={flag("p1_tight_id"),flag("p2_tight_id")}; e.tight_iso={flag("p1_tight_iso"),flag("p2_tight_iso")};
      const auto passed=atlas::selection::evaluate(e,config); for(std::size_t i=0;i<counts.size();++i) counts[i]+=passed[i];
      if(!passed.back()) continue;
      mgg.Fill(e.mgg);mjj.Fill(e.mjj);for(auto value:e.photon_pt)ppt.Fill(value);for(auto value:e.jet_pt)jpt.Fill(value);
      if(e.tight_id[0]<0||e.tight_id[1]<0||e.tight_iso[0]<0||e.tight_iso[1]<0) ++missing_flags;
      if(e.tight_id[0]==1&&e.tight_id[1]==1) {++selected_tight;if(e.tight_iso[0]==1&&e.tight_iso[1]==1)++selected_tight_iso;}
    }
    if(counts[0]==0) throw std::runtime_error("Empty cache; no real selection result");
    std::filesystem::create_directories(output); std::ofstream csv(output/"cutflow.csv");csv.exceptions(std::ios::badbit|std::ios::failbit);
    csv << "selection_name,events_before,events_after,rejected_events,conditional_fraction,cumulative_fraction,definition_version,validation_status\n" << std::setprecision(17);
    const std::array<const char*,10> names{"C0_GamGam_skim_input","C1_valid_kinematics","C2_two_photons","C3_leading_photon_pt","C4_subleading_photon_pt","C5_photon_eta_acceptance","C6_diphoton_mass_window","C7_two_jets","C8_leading_two_jet_pt","C9_leading_two_jet_eta"};
    for(std::size_t i=0;i<counts.size();++i) {
      const auto before=i?counts[i-1]:counts[0]; csv << names[i] << ',' << before << ',' << counts[i] << ',' << before-counts[i] << ',';
      if(before) csv << double(counts[i])/double(before);
      csv << ',' << double(counts[i])/double(counts[0]) << ',' << config.version << ',' << status << "_EXPLORATORY\n";
    }
    std::ofstream optional(output/"optional_photon_flags.csv");
    optional.exceptions(std::ios::badbit|std::ios::failbit);
    optional << "diagnostic,base_C9_events,flag_true_events,missing_flag_events,validation_status\n";
    optional << "raw_tightID_both," << counts[9] << ',' << selected_tight << ',' << missing_flags << ',' << (missing_flags?"UNKNOWN_MISSING_FLAGS":"PROVISIONAL_RAW_FLAG_DIAGNOSTIC") << '\n';
    optional << "raw_tightID_and_tightIso_both," << counts[9] << ',' << selected_tight_iso << ',' << missing_flags << ',' << (missing_flags?"UNKNOWN_MISSING_FLAGS":"PROVISIONAL_RAW_FLAG_DIAGNOSTIC") << '\n';
    gROOT->SetBatch(true);gStyle->SetOptStat(0);gStyle->SetCanvasColor(0);gStyle->SetPadColor(0);gStyle->SetPadTickX(1);gStyle->SetPadTickY(1);TGaxis::SetMaxDigits(3);
    std::ofstream inventory(output/"histogram_inventory.csv");
    inventory.exceptions(std::ios::badbit|std::ios::failbit);
    inventory << "name,filled_values,in_range,underflow,overflow\n";
    const bool synthetic=std::filesystem::path(argv[1]).filename().string().find("synthetic")!=std::string::npos;
    for(auto* h:{&mgg,&mjj,&ppt,&jpt}) {
      inventory << h->GetName() << ',' << h->GetEntries() << ',' << h->Integral() << ',' << h->GetBinContent(0) << ',' << h->GetBinContent(h->GetNbinsX()+1) << '\n';
      TCanvas canvas("selection_canvas","exploratory preselection",1100,850);canvas.SetLeftMargin(.14);canvas.SetBottomMargin(.13);canvas.SetTopMargin(.29);
      h->SetLineWidth(2);h->SetLineColor(kBlue+2);h->SetMinimum(0);h->Draw("HIST");
      TLatex text;text.SetNDC();text.SetTextFont(42);text.SetTextSize(.028);
      text.DrawLatex(.14,.955,"ATLAS Open Data exploratory diagnostic;");text.DrawLatex(.14,.918,"raw unweighted GamGam skim;");text.DrawLatex(.14,.881,"not the official ATLAS HH analysis.");
      text.SetTextSize(.023);const std::string provenance=(synthetic?"Synthetic cache":"Record 93915 / data15 periodD")+std::string(" | unit status: ")+status;
      text.DrawLatex(.14,.837,provenance.c_str());
      const std::string caption="Source entries ["+std::to_string(first)+","+std::to_string(previous+1)+"); C0="+std::to_string(counts[0])+"; C9="+std::to_string(counts[9])+" | "+config.version;
      text.DrawLatex(.14,.802,caption.c_str());
      TLegend legend(.56,.655,.94,.713);legend.SetFillStyle(0);legend.SetBorderSize(0);legend.SetTextSize(.021);legend.AddEntry(h,"Study-defined C9; inclusive jets","l");legend.Draw();
      canvas.SaveAs((output/(std::string(h->GetName())+".png")).c_str());
    }
    std::ofstream summary(output/"summary.json");
    summary.exceptions(std::ios::badbit|std::ios::failbit);
    summary << "{\"input_events\":" << counts[0] << ",\"selected_events\":" << counts[9] << ",\"start_entry\":" << first << ",\"end_exclusive\":" << previous+1 << ",\"new_ROOT_entry_reads\":0,\"unit_status\":\"" << status << "\",\"definition_version\":\"" << config.version << "\"}\n";
    std::cout << "PASS exploratory cutflow: C0=" << counts[0] << " C9=" << counts[9] << " definition=" << config.version << " unit_status=" << status << " new ROOT entries=0\n";return 0;
  } catch(const std::exception& e) {std::cerr << "FAIL: " << e.what() << '\n';return 1;}
}

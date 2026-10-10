#include "AtlasLocalEvents.h"
#include <TCanvas.h>
#include <TH1D.h>
#include <TFile.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TLatex.h>
#include <TLegend.h>
#include <TGaxis.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numbers>
#include <stdexcept>
#include <cmath>

using namespace atlas;
int main(int argc, char** argv) {
  try {
    if (argc != 7) throw std::invalid_argument("Usage: phase2_diagnostics input.root new_output_dir start exclusive_end scale_to_GeV VERIFIED|PROVISIONAL");
    const auto start = std::stoll(argv[3]), requested_end = std::stoll(argv[4]);
    const double scale = std::stod(argv[5]); const std::string status = argv[6];
    if (status != "PROVISIONAL" && status != "VERIFIED") throw std::invalid_argument("Unit gate does not allow physical diagnostics");
    if (!std::isfinite(scale) || scale <= 0 || start < 0 || requested_end <= start || requested_end > 100000)
      throw std::invalid_argument("Invalid scale or bounded entry range");
    const std::filesystem::path output(argv[2]);
    if (std::filesystem::exists(output)) throw std::runtime_error("Output exists; refusing overwrite or accidental duplicate processing");
    events::Reader reader(argv[1]);
    const auto end = std::min<std::int64_t>(requested_end, reader.entries());
    if (start >= end) throw std::out_of_range("No available entries in requested range");
    std::filesystem::create_directories(output);
    std::ofstream rows(output/"events.csv"), stages(output/"stages.csv");
    rows.exceptions(std::ios::badbit|std::ios::failbit); stages.exceptions(std::ios::badbit|std::ios::failbit);
    rows << "entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue\n" << std::setprecision(17);
    stages << "stage,start_entry,end_exclusive,unique_entries,invalid_events,status\n";
    std::vector<std::unique_ptr<TH1D>> hist;
    auto add = [&](const char* name, const char* axis, int bins, double low, double high) {
      auto h = std::make_unique<TH1D>(name, (std::string(";")+axis+";Raw unweighted entries / bin").c_str(), bins, low, high);
      h->SetDirectory(nullptr); hist.push_back(std::move(h));
    };
    add("photon_pt", "Photon p_{T} [GeV] (all valid objects)", 60, 0, 300);
    add("photon_eta", "Photon #eta (all valid objects)", 50, -2.5, 2.5);
    add("jet_pt", "Jet p_{T} [GeV] (all valid objects)", 60, 0, 300);
    add("jet_eta", "Jet #eta (all valid objects)", 60, -5, 5);
    add("m_gg", "Leading-photon m_{#gamma#gamma} [GeV]", 80, 0, 400);
    add("m_jj", "Leading-jet m_{jj} [GeV] (inclusive jets)", 80, 0, 800);
    add("deltaR_gg", "Leading-photon #DeltaR (dimensionless)", 60, 0, 6);
    std::int64_t seen=0, invalid=0, photon_pairs=0, jet_pairs=0, roundoff=0;
    auto number = [&](double value) { if(std::isfinite(value)) rows << value; };
    const double absent = std::numeric_limits<double>::quiet_NaN();
    for (auto stage_end : {std::min<std::int64_t>(10000,end), end}) {
      const auto stage_start = start + seen;
      if (stage_start >= stage_end) continue;
      std::int64_t stage_invalid=0;
      for (auto entry=stage_start; entry<stage_end; ++entry) {
        auto raw = reader.read(entry); ++seen;
        for (const auto* phi : {&raw.photon_phi, &raw.jet_phi})
          for (auto value : *phi) if(!std::isfinite(value) || std::abs(value)>std::numbers::pi+1e-5)
            throw std::runtime_error("CONTRADICTED angular convention at entry "+std::to_string(entry));
        for (const auto* energy : {&raw.photon_e, &raw.jet_e})
          for (auto value : *energy) if(std::isfinite(value) && value*scale>13000.)
            throw std::runtime_error("CONTRADICTED energy scale: object exceeds 13 TeV total collision energy");
        const auto photons = kinematics::construct(raw.photon_pt,raw.photon_eta,raw.photon_phi,raw.photon_e,raw.photon_n,scale);
        const auto jets = kinematics::construct(raw.jet_pt,raw.jet_eta,raw.jet_phi,raw.jet_e,raw.jet_n,scale);
        const auto gg = kinematics::leading_pair(photons), jj = kinematics::leading_pair(jets);
        const bool valid = photons.valid && jets.valid && (!gg.available || gg.valid) && (!jj.available || jj.valid);
        if(!valid) { ++invalid; ++stage_invalid; }
        std::string issue = !photons.valid ? "photon_"+photons.issue : (!jets.valid ? "jet_"+jets.issue :
                            (gg.available&&!gg.valid ? "gg_"+gg.issue : (jj.available&&!jj.valid ? "jj_"+jj.issue : "")));
        const auto rounded = photons.roundoff_objects+jets.roundoff_objects; roundoff += rounded;
        rows << entry << ',' << raw.run << ',' << raw.event << ',' << valid << ',' << raw.photon_n << ',' << raw.jet_n;
        auto object_value = [&](const auto& collection, std::size_t index, bool pt) {
          return valid && index<collection.ordered.size() ? (pt ? collection.ordered[index].p4.Pt() : collection.ordered[index].p4.Eta()) : absent;
        };
        for(auto value : {object_value(photons,0,true),object_value(photons,1,true),object_value(photons,0,false),object_value(photons,1,false),
                          object_value(jets,0,true),object_value(jets,1,true),object_value(jets,0,false),object_value(jets,1,false),
                          valid&&gg.valid ? gg.mass : absent,valid&&jj.valid ? jj.mass : absent,
                          valid&&gg.valid ? gg.delta_r : absent,valid&&jj.valid ? jj.delta_r : absent,
                          valid&&gg.valid ? gg.delta_eta : absent,valid&&gg.valid ? gg.delta_phi : absent,
                          valid&&jj.valid ? jj.delta_eta : absent,valid&&jj.valid ? jj.delta_phi : absent}) { rows << ','; number(value); }
        for (const auto* flags : {&raw.tight_id, &raw.tight_iso})
          for(std::size_t i=0;i<2;++i) { rows << ','; if(photons.valid && i<photons.ordered.size()) rows << bool((*flags)[photons.ordered[i].input_index]); }
        rows << ',' << rounded << ',' << issue << '\n';
        if (!valid) continue;
        for(const auto& p : photons.ordered) { hist[0]->Fill(p.p4.Pt()); hist[1]->Fill(p.p4.Eta()); }
        for(const auto& p : jets.ordered) { hist[2]->Fill(p.p4.Pt()); hist[3]->Fill(p.p4.Eta()); }
        if(gg.valid) { ++photon_pairs; hist[4]->Fill(gg.mass); hist[6]->Fill(gg.delta_r); }
        if(jj.valid) { ++jet_pairs; hist[5]->Fill(jj.mass); }
      }
      rows.flush();
      const auto processed=stage_end-stage_start;
      const bool stage_pass = double(stage_invalid)/double(processed) <= .01;
      stages << (stage_start<10000 ? "B" : "C") << ',' << stage_start << ',' << stage_end << ',' << processed << ',' << stage_invalid << ',' << (stage_pass?"PASS":"FAIL_NUMERICAL_GATE") << '\n'; stages.flush();
      if(!stage_pass) throw std::runtime_error("More than 1% invalid events in stage; dependent processing stopped, rows preserved");
    }
    gROOT->SetBatch(true); gStyle->SetOptStat(0); gStyle->SetCanvasColor(0); gStyle->SetPadColor(0);
    gStyle->SetPadTickX(1); gStyle->SetPadTickY(1); TGaxis::SetMaxDigits(3);
    const bool audited = std::filesystem::path(argv[1]).filename()=="ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root";
    std::ofstream inventory(output/"histogram_inventory.csv");
    inventory << "name,filled_values,in_range,underflow,overflow\n" << std::setprecision(17);
    TFile root((output/"phase2_diagnostics.root").c_str(),"CREATE");
    if(root.IsZombie()) throw std::runtime_error("Cannot create histogram ROOT output");
    for(auto& h : hist) {
      inventory << h->GetName() << ',' << h->GetEntries() << ',' << h->Integral() << ',' << h->GetBinContent(0) << ',' << h->GetBinContent(h->GetNbinsX()+1) << '\n';
      h->Write();
      TCanvas canvas("diagnostic_canvas","exploratory diagnostic",1100,850);
      canvas.SetLeftMargin(.14); canvas.SetBottomMargin(.13); canvas.SetTopMargin(.29);
      h->SetLineColor(kBlue+2); h->SetLineWidth(2); h->SetMinimum(0); h->Draw("HIST");
      TLatex text; text.SetNDC(); text.SetTextFont(42); text.SetTextSize(.028);
      text.DrawLatex(.14,.955,"ATLAS Open Data exploratory diagnostic;");
      text.DrawLatex(.14,.918,"raw unweighted GamGam skim;");
      text.DrawLatex(.14,.881,"not the official ATLAS HH analysis.");
      text.SetTextSize(.023);
      const std::string label=(audited?"Record 93915 / data15 periodD":"Synthetic/local test input")+std::string(" | unit status: ")+status;
      text.DrawLatex(.14,.837,label.c_str());
      const std::string counts="Unique source entries ["+std::to_string(start)+","+std::to_string(end)+"): "+std::to_string(seen)+"; invalid events excluded: "+std::to_string(invalid);
      text.DrawLatex(.14,.802,counts.c_str());
      TLegend legend(.59,.655,.94,.713); legend.SetBorderSize(0); legend.SetFillStyle(0); legend.SetTextSize(.022);
      legend.AddEntry(h.get(),"Raw counts; no event weights","l"); legend.Draw();
      canvas.SaveAs((output/(std::string(h->GetName())+".png")).c_str());
    }
    root.Close();
    std::ofstream summary(output/"summary.json");
    summary << "{\n\"unit_status\":\"" << status << "\",\n\"scale_to_gev\":" << scale << ",\n\"start_entry\":" << start
            << ",\n\"end_exclusive\":" << end << ",\n\"unique_entries\":" << seen << ",\n\"invalid_events\":" << invalid
            << ",\n\"photon_pairs\":" << photon_pairs << ",\n\"jet_pairs\":" << jet_pairs << ",\n\"negative_roundoff_objects\":" << roundoff << "\n}\n";
    std::cout << "PASS bounded diagnostics: entries=" << seen << " range=[" << start << ',' << end << ") invalid=" << invalid
              << " photon_pairs=" << photon_pairs << " jet_pairs=" << jet_pairs << " unit_status=" << status << '\n';
    return 0;
  } catch(const std::exception& e) { std::cerr << "FAIL: " << e.what() << '\n'; return 1; }
}

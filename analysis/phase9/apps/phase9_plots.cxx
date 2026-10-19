#include "Phase8Provenance.hxx"
#include <TCanvas.h>
#include <TPad.h>
#include <TGraphAsymmErrors.h>
#include <TH1D.h>
#include <TLegend.h>
#include <TLatex.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TError.h>
#include <RVersion.h>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <vector>
namespace p8=atlas_hh::phase8;
using Json=p8::Json;
struct Drawing {std::vector<std::unique_ptr<TH1D>> hist;std::vector<std::unique_ptr<TGraphAsymmErrors>> graphs;std::vector<std::unique_ptr<TLegend>> legends;std::vector<std::unique_ptr<TLatex>> texts;};
void text(Drawing&own,double x,double y,const std::string&s,double size=0.032,int color=kBlack){auto t=std::make_unique<TLatex>(x,y,s.c_str());t->SetNDC();t->SetTextFont(42);t->SetTextSize(size);t->SetTextColor(color);t->Draw();own.texts.push_back(std::move(t));}
const int colors[]={kAzure+2,kOrange+7,kGreen+2,kViolet+1,kRed+1,kTeal+3,kGray+2,kMagenta+2};
void draw_panel(const Json&p,Drawing&own,const std::string&uid){
 gPad->SetLeftMargin(.15);gPad->SetBottomMargin(.16);gPad->SetTopMargin(.15);gPad->SetRightMargin(p.at("series").size()>3?.30:.05);gPad->SetTicks(1,1);
 double ymax=0;
 for(const auto&s:p.at("series"))if(!s.value("undefined",false)){
  if(s.contains("edges")){for(std::size_t k=0;k<s.at("values").size();++k){const double v=s["values"][k],var=s["variances"][k];p8::demand(std::isfinite(v)&&std::isfinite(var)&&var>=0,"nonfinite histogram or fabricated variance");ymax=std::max(ymax,v+std::sqrt(var));}}
  else for(const auto&q:s.at("points")){p8::demand(q.size()==6,"graph point must be x,y,xlo,xhi,ylo,yhi");for(const auto&v:q)p8::demand(std::isfinite(v.get<double>()),"nonfinite graph");p8::demand(q[4].get<double>()>=0&&q[5].get<double>()>=0,"negative uncertainty");ymax=std::max(ymax,q[1].get<double>()+q[5].get<double>());}
 }
 double yhigh=p.value("ymax",ymax>0?ymax*1.35:1.0);if(yhigh<=0)yhigh=1;
 auto frame=std::make_unique<TH1D>((uid+"_frame").c_str(),"",1,p.at("xmin").get<double>(),p.at("xmax").get<double>());
 frame->SetDirectory(nullptr);frame->SetMinimum(0);frame->SetMaximum(yhigh);frame->GetXaxis()->SetTitle(p.at("x_title").get<std::string>().c_str());frame->GetYaxis()->SetTitle(p.at("y_title").get<std::string>().c_str());
 frame->GetXaxis()->SetTitleSize(.048);frame->GetYaxis()->SetTitleSize(.047);frame->GetXaxis()->SetLabelSize(.039);frame->GetYaxis()->SetLabelSize(.039);frame->GetYaxis()->SetTitleOffset(1.45);frame->GetXaxis()->SetTitleOffset(1.25);if(p.contains("x_labels"))frame->GetXaxis()->SetLabelSize(0);frame->Draw("AXIS");own.hist.push_back(std::move(frame));
 const bool many=p.at("series").size()>3;auto legend=std::make_unique<TLegend>(many?.73:.48,many?.48:.66,many?.99:.94,.84);legend->SetBorderSize(0);legend->SetFillStyle(0);legend->SetTextSize(.031);int index=0;
 for(const auto&s:p.at("series")){
  const int color=colors[index%8];const auto label=s.at("label").get<std::string>();const auto name=uid+"_s"+std::to_string(index++);
  if(s.value("undefined",false)){text(own,.18,.77-.055*(index-1),label+": undefined (zero support)",.030,kGray+2);continue;}
  if(s.contains("edges")){
   const auto edges=s.at("edges").get<std::vector<double>>(),vals=s.at("values").get<std::vector<double>>(),vars=s.at("variances").get<std::vector<double>>();p8::demand(edges.size()==vals.size()+1&&vars.size()==vals.size(),"bin arrays disagree");p8::demand(std::is_sorted(edges.begin(),edges.end())&&std::adjacent_find(edges.begin(),edges.end())==edges.end(),"bad histogram edges");
   auto h=std::make_unique<TH1D>(name.c_str(),"",static_cast<int>(vals.size()),edges.data());h->SetDirectory(nullptr);h->SetLineColor(color);h->SetLineWidth(2);h->SetMarkerColor(color);h->SetMarkerStyle(20+(index%5));h->SetMarkerSize(.55);
   for(std::size_t k=0;k<vals.size();++k){h->SetBinContent(k+1,vals[k]);h->SetBinError(k+1,std::sqrt(vars[k]));}h->Draw("HIST SAME");h->Draw("E1 SAME");legend->AddEntry(h.get(),label.c_str(),"lp");own.hist.push_back(std::move(h));
  }else{
   auto g=std::make_unique<TGraphAsymmErrors>();int k=0;for(const auto&q:s.at("points")){g->SetPoint(k,q[0].get<double>(),q[1].get<double>());g->SetPointError(k,q[2].get<double>(),q[3].get<double>(),q[4].get<double>(),q[5].get<double>());++k;}
   g->SetLineColor(color);g->SetMarkerColor(color);g->SetLineWidth(2);g->SetMarkerStyle(20+(index%5));g->SetMarkerSize(.8);g->Draw(s.value("draw","LP").c_str());legend->AddEntry(g.get(),label.c_str(),"lp");own.graphs.push_back(std::move(g));
  }
 }
 if(!p.value("hide_legend",false))legend->Draw();own.legends.push_back(std::move(legend));text(own,.15,.90,p.at("title").get<std::string>(),.040);
 // Detail notes remain in the figure specification and scientific caption, outside plotted data.
 if(p.contains("x_labels")){double xx=p.at("xmin"),dx=(p.at("xmax").get<double>()-xx)/p.at("x_labels").size();int i=0;for(const auto&label:p.at("x_labels")){const double frac=(i+.5)/p.at("x_labels").size();text(own,.15+frac*.80-.035,.055,label.get<std::string>(),.030);++i;}(void)dx;}
 gPad->RedrawAxis();
}
int main(int argc,char**argv){try{
 p8::demand(argc==5&&std::string(argv[1])=="--input"&&std::string(argv[3])=="--output","usage: phase9_plots --input VERIFIED_PLOT_SPEC --output FRESH_DIRECTORY");
 const auto spec=p8::read_json(argv[2]);p8::demand(spec.at("plots").size()==12,"exact bounded twelve figures required");p8::demand(spec.at("physical_total_background")=="BLOCKED","physical background sum prohibited");
 const std::filesystem::path out=argv[4];p8::fresh_directory(out);gROOT->SetBatch(true);gStyle->SetOptStat(0);gStyle->SetTextFont(42);gStyle->SetLineWidth(2);gErrorIgnoreLevel=kWarning;Json produced=Json::array();
 for(const auto&p:spec.at("plots")){
  const auto id=p.at("id").get<std::string>();p8::demand(id.size()<80&&id.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_")==std::string::npos,"unsafe figure ID");const int count=p.at("panels").size();p8::demand(count>=1&&count<=6,"bounded panels required");
  const int cols=count<=1?1:count<=3?count:3,rows=(count+cols-1)/cols;TCanvas canvas((id+"_canvas").c_str(),"",count==1?1150:1600,count==1?820:rows==1?850:1250);canvas.SetFillColor(kWhite);Drawing own;
  text(own,.065,.955,"ATLAS HH bb#gamma#gamma | Existing Monte Carlo diagnostics",count==1?.028:.024);
  text(own,.065,.915,p.at("title").get<std::string>(),count==1?.025:.022);
  TPad content((id+"_content").c_str(),"",.025,count==1?.235:.20,.985,.875);content.SetFillColor(kWhite);content.Draw();content.cd();content.Divide(cols,rows,.015,.015);
  for(int n=0;n<count;++n){content.cd(n+1);draw_panel(p.at("panels")[n],own,id+std::to_string(n));}
  canvas.cd();double y=count==1?.19:.163;const double fs=count==1?.0185:.0165;for(const auto&line:p.at("caption_lines")){text(own,.065,y,line.get<std::string>(),fs,kGray+2);y-=count==1?.032:.027;}
  p8::demand(y>=0,"caption exceeds bounded canvas");const auto pdf=out/(id+".pdf"),png=out/(id+".png");gStyle->SetPaperSize(20.0,20.0*canvas.GetWh()/canvas.GetWw());canvas.Print(pdf.c_str(),"pdf Portrait");canvas.SaveAs(png.c_str());std::ifstream signature(pdf,std::ios::binary);std::string header(5,' ' );signature.read(header.data(),5);p8::demand(header=="%PDF-","ROOT exporter did not produce PDF bytes");p8::demand(std::filesystem::file_size(pdf)>1000&&std::filesystem::file_size(png)>1000,"empty exported figure");
  produced.push_back({{"figure_id",id},{"pdf",pdf.string()},{"png",png.string()},{"pdf_sha256",p8::file_sha256(pdf)},{"png_sha256",p8::file_sha256(png)},{"specification",p},{"status","LOCAL_DRAFT"},{"publication_authorized",false}});
 }
 p8::write_json(out/"phase9_plot_manifest.json",{{"status","LOCAL_DRAFT"},{"ROOT_version",ROOT_RELEASE},{"renderer","CERN_ROOT_NATIVE_CXX20"},{"plot_spec_sha256",p8::file_sha256(argv[2])},{"figure_count",12},{"figures",produced},{"physical_total_background","BLOCKED"},{"physical_significance","NOT_EVALUATED"},{"new_events",0}});
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
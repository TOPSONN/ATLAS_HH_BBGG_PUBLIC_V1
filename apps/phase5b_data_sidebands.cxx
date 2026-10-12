#include "AtlasControlRegions.h"
#include <TH1D.h>
#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace fs=std::filesystem;
namespace sel=atlas::selection;
namespace reg=atlas::regions;
namespace {
constexpr std::uint64_t max_entries=64000,max_bytes=64*1024*1024;
constexpr std::size_t max_line=65536;
const std::string header="entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue";
void require(bool ok,const char* message) { if(!ok) throw std::invalid_argument(message); }
// Portable SHA-256 over bounded local files. Fixtures compare its result to
// Python hashlib, including block-boundary and multi-block inputs.
std::string sha256(const fs::path& path) {
  require(fs::is_regular_file(path)&&fs::file_size(path)<=max_bytes,"Hash input must be a bounded regular file");
  std::ifstream in(path,std::ios::binary); require(static_cast<bool>(in),"Hash input unreadable");
  std::vector<std::uint8_t> data; data.reserve(static_cast<std::size_t>(fs::file_size(path))+72);
  char c=0; while(in.get(c)) { require(data.size()<max_bytes,"Hash input exceeds bound"); data.push_back(static_cast<std::uint8_t>(c)); }
  require(!in.bad(),"Hash input read failed"); const auto bits=static_cast<std::uint64_t>(data.size())*8;
  data.push_back(0x80); while(data.size()%64!=56) data.push_back(0);
  for(int i=7;i>=0;--i) data.push_back(static_cast<std::uint8_t>(bits>>(8*i)));
  std::array<std::uint32_t,8> h{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
  constexpr std::array<std::uint32_t,64> k{
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
  for(std::size_t block=0;block<data.size();block+=64) {
    std::array<std::uint32_t,64> w{};
    for(std::size_t i=0;i<16;++i) for(std::size_t j=0;j<4;++j) w[i]=(w[i]<<8)|data[block+4*i+j];
    for(std::size_t i=16;i<64;++i) {
      const auto s0=std::rotr(w[i-15],7)^std::rotr(w[i-15],18)^(w[i-15]>>3);
      const auto s1=std::rotr(w[i-2],17)^std::rotr(w[i-2],19)^(w[i-2]>>10);
      w[i]=w[i-16]+s0+w[i-7]+s1;
    }
    auto a=h[0],b=h[1],cc=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
    for(std::size_t i=0;i<64;++i) {
      const auto t1=hh+(std::rotr(e,6)^std::rotr(e,11)^std::rotr(e,25))+((e&f)^((~e)&g))+k[i]+w[i];
      const auto t2=(std::rotr(a,2)^std::rotr(a,13)^std::rotr(a,22))+((a&b)^(a&cc)^(b&cc));
      hh=g;g=f;f=e;e=d+t1;d=cc;cc=b;b=a;a=t1+t2;
    }
    h[0]+=a;h[1]+=b;h[2]+=cc;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;
  }
  std::ostringstream out; out<<std::hex<<std::setfill('0'); for(auto value:h) out<<std::setw(8)<<value; return out.str();
}
std::uint64_t integer(std::string_view text) {
  require(!text.empty() && std::all_of(text.begin(),text.end(),[](unsigned char c){return c>='0'&&c<='9';}),"Invalid unsigned integer");
  std::uint64_t value=0;auto result=std::from_chars(text.data(),text.data()+text.size(),value);
  require(result.ec==std::errc{}&&result.ptr==text.data()+text.size(),"Integer overflow");return value;
}
bool boolean(std::string_view text) { require(text=="0"||text=="1","Boolean must be0 or1");return text=="1"; }
double number(std::string_view text) {
  if(text.empty()) return std::numeric_limits<double>::quiet_NaN();
  double value=0;auto result=std::from_chars(text.data(),text.data()+text.size(),value);
  require(result.ec==std::errc{}&&result.ptr==text.data()+text.size()&&std::isfinite(value),"Malformed/nonfinite scalar");return value;
}
bool line(std::istream& in,std::string& text) {
  text.clear();char c=0;while(in.get(c)) {if(c=='\n')break;require(text.size()<max_line,"Oversized line");text.push_back(c);}
  require(!in.bad(),"Cache read failed");if(text.empty()&&!in&&c!='\n')return false;
  if(!text.empty()&&text.back()=='\r')text.pop_back();
  return true;
}
std::vector<std::string> fields(const std::string& text) {
  require(text.find('"')==std::string::npos&&text.find('\0')==std::string::npos,"Quoted/binary cache unsupported");
  std::vector<std::string> result;std::size_t begin=0;
  while(true) {auto end=text.find(',',begin);result.push_back(text.substr(begin,end-begin));if(end==std::string::npos)break;begin=end+1;}return result;
}
std::string json(const std::string& text) {
  std::string out="\"";for(unsigned char c:text) {require(c>=32,"Control character in provenance");if(c=='"'||c=='\\')out+='\\';out+=static_cast<char>(c);}return out+'"';
}
struct Point {std::uint64_t entry,run,event;double mass,deta;int fold;};
int fold(std::uint64_t run,std::uint64_t event) {
  const auto text="DATA:"+std::to_string(run)+":"+std::to_string(event);
  std::uint64_t h=14695981039346656037ULL;for(unsigned char c:text) {h^=c;h*=1099511628211ULL;}return static_cast<int>(h&1);
}
bool sideband(double mass) {return (mass>=105&&mass<120)||(mass>=130&&mass<=160);}
struct Correlation {std::size_t n=0;long double value=0;bool defined=false;};
Correlation pearson(const std::vector<long double>& x,const std::vector<long double>& y) {
  require(x.size()==y.size(),"Correlation size mismatch");long double mx=0,my=0,xx=0,yy=0,xy=0;std::size_t n=0;
  for(std::size_t i=0;i<x.size();++i) {++n;const auto dx=x[i]-mx,dy=y[i]-my;mx+=dx/n;my+=dy/n;xx+=dx*(x[i]-mx);yy+=dy*(y[i]-my);xy+=dx*(y[i]-my);}
  Correlation r;r.n=n;if(n>=2&&xx>0&&yy>0) {r.value=xy/std::sqrt(xx*yy);require(std::isfinite(r.value),"Nonfinite correlation");r.defined=true;}return r;
}
std::vector<long double> ranks(const std::vector<long double>& v) {
  std::vector<std::size_t> order(v.size());std::iota(order.begin(),order.end(),0);std::stable_sort(order.begin(),order.end(),[&](auto a,auto b){return v[a]<v[b];});
  std::vector<long double> out(v.size());for(std::size_t i=0;i<v.size();) {auto j=i+1;while(j<v.size()&&v[order[j]]==v[order[i]])++j;const auto rank=(static_cast<long double>(i+j-1)/2)+1;for(auto k=i;k<j;++k)out[order[k]]=rank;i=j;}return out;
}
std::pair<long double,long double> wilson(std::size_t successes,std::size_t n) {
  require(n>0&&successes<=n,"Invalid fraction denominator");constexpr long double z=1.959963984540054L;const auto p=static_cast<long double>(successes)/n;
  const auto den=1+z*z/n,centre=(p+z*z/(2*n))/den,half=z*std::sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return {centre-half,centre+half};
}
}
int main(int argc,char** argv) {
 try {
  require(argc==7,"Usage: phase5b_data_sidebands input.csv selection.ini NEW_output start end_exclusive PROVISIONAL");
  const fs::path input=argv[1],config_path=argv[2],output=argv[3];const auto start=integer(argv[4]),end=integer(argv[5]);
  require(end>start&&end-start<=max_entries&&end<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Invalid bounded range");
  require(std::string_view(argv[6])=="PROVISIONAL","Preserved PROVISIONAL units required");
  require(!fs::exists(output)&&!fs::is_symlink(fs::symlink_status(output)),"Output must be new");
  require(fs::is_regular_file(input)&&fs::file_size(input)>0&&fs::file_size(input)<=max_bytes,"Invalid bounded cache file");
  const auto input_hash=sha256(input),config_hash=sha256(config_path);reg::Config cfg;cfg.selection=sel::read_config(config_path);reg::validate_config(cfg);
  require(cfg.selection.mass_low==105&&cfg.selection.mass_high==160,"Fixed study domain must preserve105..160");
  std::ifstream in(input,std::ios::binary);std::string text;require(line(in,text)&&text==header,"Exact DATA28 header required");
  const auto columns=fields(text);std::map<std::string,std::size_t> index;for(std::size_t i=0;i<columns.size();++i)index.emplace(columns[i],i);
  std::vector<Point> points;std::set<std::pair<std::uint64_t,std::uint64_t>> ids;
  std::uint64_t entries=0,valid=0,c5=0,c5jets=0,c9=0,outside=0;
  while(line(in,text)) {
   require(!text.empty()&&entries<end-start,"Blank/extra row");const auto row=fields(text);require(row.size()==columns.size(),"Wrong row width");
   const auto field=[&](const char* name)->const std::string& {return row[index.at(name)];};
   const auto entry=integer(field("entry")),run=integer(field("run")),event=integer(field("event"));require(entry==start+entries,"Noncontiguous entry range");
   require(run<=std::numeric_limits<std::uint32_t>::max()&&ids.emplace(run,event).second,"Invalid/duplicate event identity");
   const auto np=integer(field("photon_n")),nj=integer(field("jet_n"));require(np<=100000&&nj<=100000,"Invalid object count");
   require(integer(field("roundoff_objects"))<=np+nj,"Invalid roundoff count");sel::Event e;e.source_valid=boolean(field("valid"));e.photons=static_cast<int>(np);e.jets=static_cast<int>(nj);
   e.photon_pt={number(field("photon1_pt")),number(field("photon2_pt"))};e.photon_eta={number(field("photon1_eta")),number(field("photon2_eta"))};
   e.jet_pt={number(field("jet1_pt")),number(field("jet2_pt"))};e.jet_eta={number(field("jet1_eta")),number(field("jet2_eta"))};e.mgg=number(field("m_gg"));e.mjj=number(field("m_jj"));
   const auto presence=[&](double value,bool expected) {require(std::isfinite(value)==expected,"Valid/multiplicity scalar contract mismatch");};
   for(std::size_t i=0;i<2;++i) {presence(e.photon_pt[i],e.source_valid&&np>i);presence(e.photon_eta[i],e.source_valid&&np>i);presence(e.jet_pt[i],e.source_valid&&nj>i);presence(e.jet_eta[i],e.source_valid&&nj>i);}
   for(const char* name:{"m_gg","deltaR_gg","deltaEta_gg","deltaPhi_gg"})presence(number(field(name)),e.source_valid&&np>=2);
   for(const char* name:{"m_jj","deltaR_jj","deltaEta_jj","deltaPhi_jj"})presence(number(field(name)),e.source_valid&&nj>=2);
   for(const char* name:{"p1_tight_id","p2_tight_id","p1_tight_iso","p2_tight_iso"})if(!field(name).empty())(void)boolean(field(name));
   require(!e.source_valid||sel::valid_kinematics(e),"Invalid kinematics labelled valid");
   if(e.source_valid&&np>=2)require(std::abs(number(field("deltaEta_gg"))-(e.photon_eta[0]-e.photon_eta[1]))<=1e-10,"Cached photon deltaEta mismatch");
   const auto passed=sel::evaluate(e,cfg.selection);const bool jets=passed[5]&&sel::jet_multiplicity(e)&&sel::jet_pt(e,cfg.selection)&&sel::jet_acceptance(e,cfg.selection);
   ++entries;valid+=e.source_valid;c5+=passed[5];c5jets+=jets;c9+=passed[9];outside+=reg::classify(e,cfg)==reg::Region::OutsideStudyDomain;
   if(jets&&sideband(e.mgg))points.push_back({entry,run,event,e.mgg,number(field("deltaEta_gg")),fold(run,event)});
  }
  require(entries==end-start,"Incomplete requested range");require(sha256(input)==input_hash&&sha256(config_path)==config_hash,"Input changed during read");
  fs::create_directories(output.parent_path().empty()?fs::path("."):output.parent_path());require(fs::create_directory(output),"Fresh output creation failed");
  std::ofstream events(output/"sideband_events.csv"),metrics(output/"region_diagnostics.csv"),histograms(output/"mass_histograms.csv"),summary(output/"summary.json");
  for(auto stream:{&events,&metrics,&histograms,&summary})stream->exceptions(std::ios::failbit|std::ios::badbit);
  events<<std::setprecision(17)<<"entry,run,event,m_gg,deltaEta_gg,abs_deltaEta_gg,baseline_partition,sideband,holdout_fold,scope\n";
  for(const auto& p:points)events<<p.entry<<','<<p.run<<','<<p.event<<','<<p.mass<<','<<p.deta<<','<<std::abs(p.deta)<<','<<(std::abs(p.deta)<1?"A":"B")<<','<<(p.mass<120?"LOWER":"UPPER")<<','<<p.fold<<",DATA_ONLY_DESCRIPTIVE\n";
  metrics<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<"diagnostic,population,partition,split_abs_delta_eta,mass_low,mass_high,n,value,interval_low,interval_high,state,scope\n";
  const auto metric=[&](const char* name,const std::string& population,const std::string& partition,double split,double low,double high,std::size_t n,long double value,bool defined=true,long double il=std::numeric_limits<long double>::quiet_NaN(),long double ih=std::numeric_limits<long double>::quiet_NaN()) {
   metrics<<name<<','<<population<<','<<partition<<','<<split<<','<<low<<','<<high<<','<<n<<',';if(defined)metrics<<value;metrics<<',';if(std::isfinite(il))metrics<<il;metrics<<',';if(std::isfinite(ih))metrics<<ih;metrics<<','<<(defined?"PASS_DESCRIPTIVE":"UNDEFINED")<<",NO_PHYSICAL_MODEL_OR_CLOSURE\n";
  };
  const auto select=[&](const std::string& partition,double split,double low,double high,int wanted_fold=-1) {std::vector<Point> selected;for(const auto& p:points)if(p.mass>=low&&p.mass<=high&&(partition=="ALL"||(std::abs(p.deta)<split)==(partition=="A"))&&(wanted_fold<0||p.fold==wanted_fold))selected.push_back(p);return selected;};
  const auto fraction=[&](const std::string& population,double split,double low,double high,const std::vector<Point>& all) {const auto a=static_cast<std::size_t>(std::count_if(all.begin(),all.end(),[&](const auto& p){return std::abs(p.deta)<split;}));if(all.empty())metric("A_fraction",population,"A",split,low,high,0,0,false);else {const auto interval=wilson(a,all.size());metric("A_fraction",population,"A",split,low,high,all.size(),static_cast<long double>(a)/all.size(),true,interval.first,interval.second);}};
  for(double split:{.8,1.,1.2})for(const auto& partition:{std::string("A"),std::string("B")}) {
   const auto all=select(partition,split,105,160),lower=select(partition,split,105,std::nextafter(120.,0.)),upper=select(partition,split,130,160);
   metric("occupancy","SIDEBANDS",partition,split,105,160,all.size(),all.size());metric("occupancy","LOWER",partition,split,105,120,lower.size(),lower.size());metric("occupancy","UPPER",partition,split,130,160,upper.size(),upper.size());
   metric("raw_count_per_GeV","LOWER",partition,split,105,120,lower.size(),static_cast<long double>(lower.size())/15);
   metric("raw_count_per_GeV","UPPER",partition,split,130,160,upper.size(),static_cast<long double>(upper.size())/30);
   metric("upper_over_lower_density_ratio","SIDEBANDS",partition,split,105,160,all.size(),lower.empty()?0:static_cast<long double>(upper.size())/(2*lower.size()),!lower.empty());
   if(all.empty())metric("upper_fraction","SIDEBANDS",partition,split,105,160,0,0,false);else {const auto interval=wilson(upper.size(),all.size());metric("upper_fraction","SIDEBANDS",partition,split,105,160,all.size(),static_cast<long double>(upper.size())/all.size(),true,interval.first,interval.second);}
  }
  for(const auto& partition:{std::string("ALL"),std::string("A"),std::string("B")})for(const auto& population:{std::string("SIDEBANDS"),std::string("LOWER"),std::string("UPPER")}) {
   const auto low=population=="UPPER"?130.:105.,high=population=="LOWER"?std::nextafter(120.,0.):160.;const auto all=select(partition,1,low,high);
   std::vector<long double> mass,signed_eta,absolute_eta;for(const auto& p:all){mass.push_back(p.mass);signed_eta.push_back(p.deta);absolute_eta.push_back(std::abs(p.deta));}
   for(bool absolute:{false,true}) {const auto& eta=absolute?absolute_eta:signed_eta;const auto p=pearson(mass,eta),s=pearson(ranks(mass),ranks(eta));metric(absolute?"pearson_mass_absDeltaEta":"pearson_mass_deltaEta",population,partition,1,low,high,p.n,p.value,p.defined);metric(absolute?"spearman_mass_absDeltaEta":"spearman_mass_deltaEta",population,partition,1,low,high,s.n,s.value,s.defined);}
  }
  for(double split:{.8,1.,1.2})for(const auto& bounds:{std::pair{105.,160.},std::pair{110.,160.},std::pair{105.,155.},std::pair{110.,155.}})fraction("FIXED_OUTER_BOUNDARY",split,bounds.first,bounds.second,select("ALL",split,bounds.first,bounds.second));
  for(int bin=0;bin<11;++bin) {const double low=105+5*bin,high=low+5;std::vector<Point> all;for(const auto& p:points)if(p.mass>=low&&(p.mass<high||(bin==10&&p.mass==160)))all.push_back(p);fraction("FIXED_5GEV_BIN",1,low,high,all);}
  for(const auto& partition:{std::string("A"),std::string("B")})for(int f=0;f<2;++f)for(const auto& population:{std::string("LOWER"),std::string("UPPER")}) {auto low=population=="LOWER"?105.:130.,high=population=="LOWER"?std::nextafter(120.,0.):160.;const auto all=select(partition,1,low,high,f);metric("holdout_occupancy",population+"_FOLD"+std::to_string(f),partition,1,low,high,all.size(),all.size());}
  for(const auto& bounds:{std::pair{110.,115.},std::pair{140.,145.}})for(const auto& partition:{std::string("A"),std::string("B")}) {const auto all=select(partition,1,bounds.first,std::nextafter(bounds.second,0.));metric("pseudo_window_occupancy","FIXED_SIDEBAND_PSEUDO_WINDOW",partition,1,bounds.first,bounds.second,all.size(),all.size());}
  TH1D a("sideband_A","sideband A;supplied m_{gg} [PROVISIONAL GeV];raw count",11,105,160),b("sideband_B","sideband B;supplied m_{gg} [PROVISIONAL GeV];raw count",11,105,160);a.SetDirectory(nullptr);b.SetDirectory(nullptr);a.Sumw2();b.Sumw2();
  for(const auto& p:points)(std::abs(p.deta)<1?a:b).Fill(p.mass);
  histograms<<std::setprecision(17)<<"partition,root_bin,mass_low,mass_high,raw_count,sumw2,bin_semantics,scope\n";
  for(auto hist:{&a,&b})for(int bin=0;bin<=12;++bin)histograms<<(hist==&a?"A":"B")<<','<<bin<<','<<hist->GetXaxis()->GetBinLowEdge(bin)<<','<<hist->GetXaxis()->GetBinUpEdge(bin)<<','<<hist->GetBinContent(bin)<<','<<std::pow(hist->GetBinError(bin),2)<<','<<(bin==0?"UNDERFLOW":bin==12?"OVERFLOW_GE_160":"LOW_INCLUSIVE_HIGH_EXCLUSIVE")<<",SIDEBANDS_ONLY\n";
  summary<<"{\n\"status\":\"PASS_BOUNDED_DATA_SIDEBAND_DIAGNOSTICS\",\n\"scope\":\"DESCRIPTIVE_ONLY_NO_PHYSICAL_TF_OR_FIT\",\n"
    <<"\"input_cache\":"<<json(fs::absolute(input).lexically_normal().string())<<",\n\"input_cache_sha256\":"<<json(input_hash)<<",\n\"selection_file\":"<<json(fs::absolute(config_path).lexically_normal().string())<<",\n\"selection_sha256\":"<<json(config_hash)<<",\n"
    <<"\"cache_schema\":\"DATA_PHASE2_28\",\n\"sample_id\":\"DATA\",\n\"start\":"<<start<<",\n\"end_exclusive\":"<<end<<",\n\"entries\":"<<entries<<",\n\"cache_valid\":"<<valid<<",\n\"C5\":"<<c5<<",\n\"C5_plus_jets\":"<<c5jets<<",\n\"C9\":"<<c9<<",\n\"outside_study_domain\":"<<outside<<",\n\"sideband_entries\":"<<points.size()<<",\n"
    <<"\"selection_definition\":"<<json(cfg.selection.version)<<",\n\"unit_status\":\"PROVISIONAL\",\n\"baseline_abs_delta_eta_split\":1,\n\"fixed_alternative_splits\":[0.8,1,1.2],\n\"central_window\":\"[120,130); never used for correlation or alternative-boundary diagnostics\",\n\"sidebands\":\"[105,120) union [130,160]\",\n"
    <<"\"fraction_interval\":\"95% Wilson binomial counting interval; no model or selection systematics\",\n\"correlation\":\"descriptive Pearson and tied-rank Spearman; no independence test or physical closure\",\n\"holdout_rule\":\"FNV1a64 ASCII DATA:run:event low bit; fixed prospective design; historical DATA already viewed\",\n\"histogram_edge\":\"ROOT upper edge160 is overflow; semantic diagnostic final bin includes160\",\n"
    <<"\"native_ROOT_read\":false,\n\"source_ROOT_identity_verified_by_app\":false,\n\"normalization_applied\":false,\n\"scale_factors_applied\":false,\n\"physical_transfer_factor_applied\":false,\n\"physical_closure_executed\":false,\n\"figures_generated\":0,\n\"blinded_analysis\":false,\n\"background_dominance\":\"UNKNOWN\",\n\"single_H_contamination\":\"UNKNOWN\"\n}\n";
  events.close();metrics.close();histograms.close();summary.close();std::cout<<"PASS DATA-only descriptive sidebands: entries="<<entries<<" C9="<<c9<<" sidebands="<<points.size()<<"; no physical TF/fit\n";return 0;
 } catch(const std::exception& e) {std::cerr<<"FAIL DATA sidebands: "<<e.what()<<'\n';return 1;}
}

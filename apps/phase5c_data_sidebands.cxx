#include "AtlasExploratorySelection.h"
#include "AtlasSidebandDiagnostics.h"
#include <TH1D.h>
#include <algorithm>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <vector>

namespace fs=std::filesystem;
namespace sel=atlas::selection;
namespace sb=atlas::sidebands;
namespace {
constexpr std::uint64_t max_entries=64000,max_bytes=64*1024*1024;
constexpr std::size_t max_line=65536;
constexpr std::string_view physical_cache_sha="c242e256d76d6832031b2e4b2dfeeb342b5b05885c2a6bdf53d2d5eab71201c7";
constexpr std::string_view selection_sha="77d57cd6fa204aad5a24031ac925c4e20e121b8aee35148cc29b522b39cf5751";
const std::string header="entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue";
void require(bool ok,const char* message) {if(!ok)throw std::invalid_argument(message);}
std::uint64_t integer(std::string_view text) {
  require(!text.empty()&&std::all_of(text.begin(),text.end(),[](unsigned char c){return c>='0'&&c<='9';}),"Invalid unsigned integer");
  std::uint64_t v=0;auto r=std::from_chars(text.data(),text.data()+text.size(),v);
  require(r.ec==std::errc{}&&r.ptr==text.data()+text.size(),"Integer overflow");return v;
}
bool boolean(std::string_view text) {require(text=="0"||text=="1","Boolean must be0 or1");return text=="1";}
double number(std::string_view text) {
  if(text.empty())return std::numeric_limits<double>::quiet_NaN();
  double v=0;
  auto r=std::from_chars(text.data(),text.data()+text.size(),v);
  require(r.ec==std::errc{}&&r.ptr==text.data()+text.size()&&std::isfinite(v),"Malformed/nonfinite scalar");return v;
}
bool line(std::istream& in,std::string& text) {
  text.clear();char c=0;while(in.get(c)){if(c=='\n')break;require(text.size()<max_line,"Oversized line");text.push_back(c);}
  require(!in.bad(),"Cache read failed");if(text.empty()&&!in&&c!='\n')return false;
  if(!text.empty()&&text.back()=='\r')text.pop_back();
  return true;
}
std::vector<std::string> fields(const std::string& text) {
  require(text.find('"')==std::string::npos&&text.find('\0')==std::string::npos,"Quoted/binary cache unsupported");
  std::vector<std::string> out;std::size_t begin=0;
  while(true){auto end=text.find(',',begin);out.push_back(text.substr(begin,end-begin));if(end==std::string::npos)break;begin=end+1;}return out;
}
std::string json(const std::string& text) {
  std::string out="\"";for(unsigned char c:text){require(c>=32,"Control character in provenance");if(c=='"'||c=='\\')out+='\\';out+=static_cast<char>(c);}return out+'"';
}
struct Point {std::uint64_t entry,run,event;double mass,deta;int category,fold;std::string digest;};
std::vector<Point> select(const std::vector<Point>& points,const std::string& partition,double split,int fold=-1,double low=105,double high=160) {
  std::vector<Point> out;
  for(const auto& p:points)if(p.mass>=low&&p.mass<=high&&(fold<0||p.fold==fold)&&
      (partition=="ALL"||(std::abs(p.deta)<split)==(partition=="A")))out.push_back(p);
  return out;
}
std::array<std::size_t,sb::categories> counts(const std::vector<Point>& points) {
  std::array<std::size_t,sb::categories> out{};for(const auto& p:points)++out.at(static_cast<std::size_t>(p.category));return out;
}
std::vector<double> masses(const std::vector<Point>& points) {std::vector<double> out;for(const auto& p:points)out.push_back(p.mass);return out;}
}
int main(int argc,char** argv) {
 try {
  require(argc==9,"Usage: phase5c_data_sidebands input.csv selection.ini frozen_protocol.json NEW_output start end_exclusive PROVISIONAL DATA93915|SYNTHETIC");
  const fs::path input=argv[1],config_path=argv[2],protocol=argv[3],output=argv[4];
  const auto start=integer(argv[5]),end=integer(argv[6]);const std::string sample=argv[8];
  require(end>start&&end-start<=max_entries&&end<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Invalid bounded range");
  require(std::string_view(argv[7])=="PROVISIONAL","Preserved PROVISIONAL units required");
  require(sample=="DATA93915"||sample=="SYNTHETIC","Explicit DATA93915 or SYNTHETIC scope required");
  require(!fs::exists(output)&&!fs::is_symlink(fs::symlink_status(output)),"Output must be new");
  // Validate the frozen protocol and unchanged selection before opening the cache.
  const auto protocol_hash=sb::sha256_file(protocol,max_line),config_hash=sb::sha256_file(config_path,max_line);
  require(protocol_hash==sb::protocol_sha256,"Frozen protocol bytes/hash changed");
  require(config_hash==selection_sha,"Unchanged checksum-pinned Phase3 selection required");
  const auto cfg=sel::read_config(config_path);
  require(fs::is_regular_file(input)&&fs::file_size(input)>0&&fs::file_size(input)<=max_bytes,"Invalid bounded cache file");
  const auto input_hash=sb::sha256_file(input);
  if(sample=="DATA93915")require(start==100&&end==63195&&input_hash==physical_cache_sha,"Physical DATA requires exact pinned cache and range");
  std::ifstream in(input,std::ios::binary);std::string text;require(line(in,text)&&text==header,"Exact DATA28 header required");
  const auto columns=fields(text);std::map<std::string,std::size_t> index;for(std::size_t i=0;i<columns.size();++i)index.emplace(columns[i],i);
  std::vector<Point> points;std::set<std::pair<std::uint64_t,std::uint64_t>> identities;
  std::uint64_t entries=0,valid=0,c5=0,c5jets=0,c9=0,outside=0,central_excluded=0;
  while(line(in,text)) {
   require(!text.empty()&&entries<end-start,"Blank/extra row");const auto row=fields(text);require(row.size()==columns.size(),"Wrong row width");
   const auto field=[&](const char* name)->const std::string&{return row[index.at(name)];};
   const auto entry=integer(field("entry")),run=integer(field("run")),event=integer(field("event"));require(entry==start+entries,"Noncontiguous entry range");
   require(run<=std::numeric_limits<std::uint32_t>::max()&&identities.emplace(run,event).second,"Invalid/duplicate canonical identity");
   const auto np=integer(field("photon_n")),nj=integer(field("jet_n"));require(np<=100000&&nj<=100000,"Invalid object count");
   require(integer(field("roundoff_objects"))<=np+nj,"Invalid roundoff count");sel::Event e;e.source_valid=boolean(field("valid"));e.photons=static_cast<int>(np);e.jets=static_cast<int>(nj);
   e.photon_pt={number(field("photon1_pt")),number(field("photon2_pt"))};e.photon_eta={number(field("photon1_eta")),number(field("photon2_eta"))};
   e.jet_pt={number(field("jet1_pt")),number(field("jet2_pt"))};e.jet_eta={number(field("jet1_eta")),number(field("jet2_eta"))};e.mgg=number(field("m_gg"));e.mjj=number(field("m_jj"));
   const auto presence=[&](double value,bool expected){require(std::isfinite(value)==expected,"Valid/multiplicity scalar contract mismatch");};
   for(std::size_t i=0;i<2;++i){presence(e.photon_pt[i],e.source_valid&&np>i);presence(e.photon_eta[i],e.source_valid&&np>i);presence(e.jet_pt[i],e.source_valid&&nj>i);presence(e.jet_eta[i],e.source_valid&&nj>i);}
   for(const char* name:{"m_gg","deltaR_gg","deltaEta_gg","deltaPhi_gg"})presence(number(field(name)),e.source_valid&&np>=2);
   for(const char* name:{"m_jj","deltaR_jj","deltaEta_jj","deltaPhi_jj"})presence(number(field(name)),e.source_valid&&nj>=2);
   for(const char* name:{"p1_tight_id","p2_tight_id","p1_tight_iso","p2_tight_iso"})if(!field(name).empty())(void)boolean(field(name));
   require(!e.source_valid||sel::valid_kinematics(e),"Invalid kinematics labelled valid");
   if(e.source_valid&&np>=2)require(std::abs(number(field("deltaEta_gg"))-(e.photon_eta[0]-e.photon_eta[1]))<=1e-10,"Cached photon deltaEta mismatch");
   const auto passed=sel::evaluate(e,cfg);const bool jets=passed[5]&&sel::jet_multiplicity(e)&&sel::jet_pt(e,cfg)&&sel::jet_acceptance(e,cfg);
   ++entries;valid+=e.source_valid;c5+=passed[5];c5jets+=jets;c9+=passed[9];outside+=jets&&!(e.mgg>=105&&e.mgg<=160);
   central_excluded+=jets&&e.mgg>=120&&e.mgg<130;
   if(jets) {const int bin=sb::mass_category(e.mgg);if(bin>=0) {
     const auto digest=sb::sha256(sb::canonical_identity(static_cast<std::uint32_t>(run),event));
     points.push_back({entry,run,event,e.mgg,number(field("deltaEta_gg")),bin,sb::identity_fold(static_cast<std::uint32_t>(run),event),digest});
   }}
  }
  require(entries==end-start,"Incomplete requested range");
  require(c9==points.size()+central_excluded,"C9 sideband/central accounting mismatch");
  require(sb::sha256_file(input)==input_hash&&sb::sha256_file(config_path,max_line)==config_hash&&sb::sha256_file(protocol,max_line)==protocol_hash,"Input changed during read");
  std::array<std::size_t,2> fold_count{};std::array<std::set<std::pair<std::uint64_t,std::uint64_t>>,2> fold_ids;
  for(const auto& p:points){++fold_count.at(static_cast<std::size_t>(p.fold));require(fold_ids[p.fold].emplace(p.run,p.event).second,"Duplicate sideband identity");}
  for(const auto& id:fold_ids[0])require(!fold_ids[1].contains(id),"Calibration/validation identity leakage");
  require(fold_count[0]+fold_count[1]==points.size(),"Fold union differs from sideband population");
  fs::create_directories(output.parent_path().empty()?fs::path("."):output.parent_path());require(fs::create_directory(output),"Fresh output creation failed");
  std::ofstream events(output/"sideband_events.csv"),audit(output/"sideband_audit.csv"),histograms(output/"root_mass_counts.csv"),summary(output/"summary.json");
  for(auto stream:{&events,&audit,&histograms,&summary})stream->exceptions(std::ios::failbit|std::ios::badbit);
  events<<std::setprecision(17)<<"entry,run,event,m_gg,deltaEta_gg,abs_deltaEta_gg,mass_category,baseline_partition,sideband,fold,role,identity_sha256,scope\n";
  const auto scope=sample=="DATA93915"?"RETROSPECTIVE_DATA_ONLY_DESCRIPTIVE":"SYNTHETIC_DIAGNOSTIC_VALIDATION";
  for(const auto& p:points)events<<p.entry<<','<<p.run<<','<<p.event<<','<<p.mass<<','<<p.deta<<','<<std::abs(p.deta)<<','<<p.category<<','<<(std::abs(p.deta)<1?"A":"B")<<','<<(p.mass<120?"LOWER":"UPPER")<<','<<p.fold<<','<<(p.fold==0?"CALIBRATION":"VALIDATION")<<','<<p.digest<<','<<scope<<'\n';
  audit<<std::setprecision(std::numeric_limits<long double>::max_digits10)<<"diagnostic,population,partition,split_abs_delta_eta,mass_low,mass_high,category,other_category,n,n_other,value,interval_low,interval_high,state,scope\n";
  const auto nan=std::numeric_limits<long double>::quiet_NaN();std::size_t audit_rows=0;
  const auto emit=[&](const std::string& name,const std::string& population,const std::string& partition,double split,double low,double high,int bin,int other,std::size_t n,std::size_t n_other,long double value,bool defined=true,long double il=std::numeric_limits<long double>::quiet_NaN(),long double ih=std::numeric_limits<long double>::quiet_NaN()) {
    audit<<name<<','<<population<<','<<partition<<','<<split<<','<<low<<','<<high<<','<<bin<<','<<other<<','<<n<<','<<n_other<<',';if(defined)audit<<value;audit<<',';if(std::isfinite(il))audit<<il;audit<<',';if(std::isfinite(ih))audit<<ih;
    audit<<','<<(defined?"DEFINED_DESCRIPTIVE":"UNDEFINED")<<','<<scope<<'\n';++audit_rows;
  };
  const auto statistic=[&](const std::string& name,const std::string& population,const std::string& partition,double split,double low,double high,const sb::Statistic& s){emit(name,population,partition,split,low,high,-1,-1,s.n,s.n_other,s.value,s.defined);};
  const auto table=[&](const std::string& population,double split,int fold,double low,double high,bool full_shapes) {
    const auto ap=select(points,"A",split,fold,low,high),bp=select(points,"B",split,fold,low,high),all=select(points,"ALL",split,fold,low,high);
    const auto a=counts(ap),b=counts(bp);const auto contingency=sb::cramers_v(a,b);
    statistic("cramers_v_mass_category_partition",population,"A_vs_B",split,low,high,contingency.association);
    statistic("empirical_ks_mass_A_vs_B",population,"A_vs_B",split,low,high,sb::empirical_ks(masses(ap),masses(bp)));
    emit("populated_mass_categories",population,"A_vs_B",split,low,high,-1,-1,all.size(),0,contingency.populated_columns);
    emit("zero_contingency_cells",population,"A_vs_B",split,low,high,-1,-1,all.size(),0,contingency.zero_cells);
    emit("contingency_cells_below5",population,"A_vs_B",split,low,high,-1,-1,all.size(),0,contingency.cells_below_five);
    for(const auto& partition:{std::string("A"),std::string("B")}) {
      const auto& chosen=partition=="A"?ap:bp;emit("occupancy",population,partition,split,low,high,-1,-1,chosen.size(),0,chosen.size());
      const auto lower=static_cast<std::size_t>(std::count_if(chosen.begin(),chosen.end(),[](const auto& p){return p.mass<120;}));
      const auto upper=chosen.size()-lower;
      emit("lower_sideband_count",population,partition,split,low,high,-1,-1,lower,0,lower);
      emit("upper_sideband_count",population,partition,split,low,high,-1,-1,upper,0,upper);
    }
    for(std::size_t i=0;i<sb::categories;++i) {
      emit("mass_category_A_count",population,"A",split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),-1,a[i],0,a[i]);
      emit("mass_category_B_count",population,"B",split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),-1,b[i],0,b[i]);
      emit("raw_count_sqrt_n_uncertainty",population,"A",split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),-1,a[i],0,std::sqrt(static_cast<long double>(a[i])));
      emit("raw_count_sqrt_n_uncertainty",population,"B",split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),-1,b[i],0,std::sqrt(static_cast<long double>(b[i])));
      const auto n=a[i]+b[i];const auto interval=n?sb::wilson95(a[i],n):std::array<long double,2>{nan,nan};
      emit("mass_conditional_A_fraction_Wilson95",population,"A",split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),-1,n,0,n?static_cast<long double>(a[i])/n:0,n>0,interval[0],interval[1]);
    }
    if(full_shapes)for(const auto& partition:{std::string("ALL"),std::string("A"),std::string("B")}) {
      const auto c=counts(partition=="ALL"?all:(partition=="A"?ap:bp));const auto shape=sb::conditional_shape(c);
      for(std::size_t i=0;i<sb::categories;++i) {
        emit("conditional_mass_fraction",population,partition,split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),-1,shape.total,c[i],shape.fraction[i],shape.defined);
        emit("conditional_fraction_counting_sd",population,partition,split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),-1,shape.total,c[i],std::sqrt(shape.covariance[i][i]),shape.defined);
        for(std::size_t j=0;j<sb::categories;++j)emit("conditional_multinomial_covariance",population,partition,split,sb::mass_low[i],sb::mass_high[i],static_cast<int>(i),static_cast<int>(j),shape.total,0,shape.covariance[i][j],shape.defined);
      }
    }
  };
  for(int fold=-1;fold<2;++fold) {
    const auto population=fold<0?std::string("POOLED_SIDEBANDS"):(fold==0?std::string("FOLD0_CALIBRATION"):std::string("FOLD1_VALIDATION"));
    for(double split:{.8,1.,1.2})table(population,split,fold,105,160,split==1);
    for(const auto& partition:{std::string("ALL"),std::string("A"),std::string("B")})for(int band=-1;band<2;++band) {
      const auto low=band==1?130.:105.,high=band==0?std::nextafter(120.,0.):160.;const auto chosen=select(points,partition,1,fold,low,high);
      std::vector<long double> x,y;for(const auto& p:chosen){x.push_back(p.mass);y.push_back(std::abs(p.deta));}
      const auto suffix=band<0?"_ALL":(band==0?"_LOWER":"_UPPER");
      statistic("pearson_mass_absDeltaEta",population+suffix,partition,1,low,high,sb::pearson(x,y));
      statistic("spearman_mass_absDeltaEta",population+suffix,partition,1,low,high,sb::pearson(sb::tied_ranks(x),sb::tied_ranks(y)));
    }
  }
  // Fixed outer trims are overlapping descriptive probes, never an optimized region.
  for(const auto& bounds:{std::pair{110.,160.},std::pair{105.,155.},std::pair{110.,155.}})for(double split:{.8,1.,1.2})
    table("FIXED_OUTER_TRIM_"+std::to_string(static_cast<int>(bounds.first))+"_"+std::to_string(static_cast<int>(bounds.second)),split,-1,bounds.first,bounds.second,false);
  for(double split:{.8,1.,1.2})for(const auto& partition:{std::string("ALL"),std::string("A"),std::string("B")}) {
    const auto a=select(points,partition,split,0),b=select(points,partition,split,1);
    statistic("empirical_ks_mass_fold0_vs_fold1","RETROSPECTIVE_HELDOUT",partition,split,105,160,sb::empirical_ks(masses(a),masses(b)));
  }
  // ROOT regular bins exclude160; the semantic nine-category table includes160.
  // Both inventories are saved, with their differing edge policies declared.
  TH1D a("phase5c_sideband_A","raw cache sidebands A",11,105,160),b("phase5c_sideband_B","raw cache sidebands B",11,105,160);
  a.SetDirectory(nullptr);b.SetDirectory(nullptr);a.Sumw2();b.Sumw2();for(const auto& p:points)(std::abs(p.deta)<1?a:b).Fill(p.mass);
  histograms<<std::setprecision(17)<<"partition,root_bin,mass_low,mass_high,raw_count,sumw2,edge_semantics,scope\n";
  for(auto h:{&a,&b})for(int bin=0;bin<=12;++bin)histograms<<(h==&a?"A":"B")<<','<<bin<<','<<h->GetXaxis()->GetBinLowEdge(bin)<<','<<h->GetXaxis()->GetBinUpEdge(bin)<<','<<h->GetBinContent(bin)<<','<<std::pow(h->GetBinError(bin),2)<<','<<(bin==0?"UNDERFLOW":bin==12?"OVERFLOW_GE160":"LOW_INCLUSIVE_HIGH_EXCLUSIVE")<<','<<scope<<'\n';
  events.close();audit.close();histograms.close();
  summary<<"{\n\"status\":\"PASS_EXECUTED_DESCRIPTIVE_DIAGNOSTICS\",\n\"scope\":"<<json(scope)<<",\n\"sample_id\":"<<json(sample)<<",\n"
    <<"\"input_cache\":"<<json(fs::absolute(input).lexically_normal().string())<<",\n\"input_cache_sha256\":"<<json(input_hash)<<",\n\"selection_file\":"<<json(fs::absolute(config_path).lexically_normal().string())<<",\n\"selection_sha256\":"<<json(config_hash)<<",\n"
    <<"\"protocol_file\":"<<json(fs::absolute(protocol).lexically_normal().string())<<",\n\"protocol_sha256\":"<<json(protocol_hash)<<",\n\"protocol_frozen_at_utc\":\"2026-10-12T07:05:36Z\",\n"
    <<"\"cache_schema\":\"DATA_PHASE2_28\",\n\"start\":"<<start<<",\n\"end_exclusive\":"<<end<<",\n\"entries\":"<<entries<<",\n\"cache_valid\":"<<valid<<",\n\"C5\":"<<c5<<",\n\"C5_plus_jets\":"<<c5jets<<",\n\"C9\":"<<c9<<",\n\"outside_study_domain\":"<<outside<<",\n\"sideband_entries\":"<<points.size()<<",\n"
    <<"\"central_window_rows_excluded_from_statistics\":"<<central_excluded<<",\n\"fold0_calibration_entries\":"<<fold_count[0]<<",\n\"fold1_validation_entries\":"<<fold_count[1]<<",\n\"fold_identity_intersection\":0,\n\"fold_union_entries\":"<<points.size()<<",\n\"whole_cache_unique_identities\":"<<identities.size()<<",\n\"audit_rows\":"<<audit_rows<<",\n"
    <<"\"selection_definition\":"<<json(cfg.version)<<",\n\"unit_status\":\"PROVISIONAL\",\n\"historical_DATA_already_viewed\":true,\n\"blinded_analysis\":false,\n\"untouched_validation\":false,\n"
    <<"\"count_uncertainty\":\"Wilson95 for conditional A fractions; raw sqrt(n); full multinomial shape covariance conditional on N; no systematics\",\n\"pvalues_computed\":false,\n\"independence_claimed\":false,\n\"best_boundary_selected\":false,\n\"calibration_fit_performed\":false,\n"
    <<"\"native_ROOT_event_reads\":0,\n\"source_ROOT_identity_verified_by_app\":false,\n\"downloaded_bytes\":0,\n\"normalization_applied\":false,\n\"scale_factors_applied\":false,\n\"physical_transfer_factor_applied\":false,\n\"background_prediction_performed\":false,\n\"physical_closure_executed\":false,\n\"figures_generated\":0,\n"
    <<"\"background_dominance\":\"UNKNOWN\",\n\"single_H_contamination\":\"UNKNOWN\",\n\"shape_stability_inference\":\"DESCRIPTIVE_STATISTICS_ONLY_NO_PHYSICAL_TRANSFER_APPROVAL\",\n"
    <<"\"sideband_events_sha256\":"<<json(sb::sha256_file(output/"sideband_events.csv"))<<",\n\"sideband_audit_sha256\":"<<json(sb::sha256_file(output/"sideband_audit.csv"))<<",\n\"root_mass_counts_sha256\":"<<json(sb::sha256_file(output/"root_mass_counts.csv"))<<"\n}\n";
  summary.close();std::cout<<"PASS Phase5C DATA-cache descriptive diagnostics: entries="<<entries<<" C9="<<c9<<" sidebands="<<points.size()<<" folds="<<fold_count[0]<<'/'<<fold_count[1]<<"; no physical TF/fit\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL Phase5C sidebands: "<<e.what()<<'\n';return 1;}
}

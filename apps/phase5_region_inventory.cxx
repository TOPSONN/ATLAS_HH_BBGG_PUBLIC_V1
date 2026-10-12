#include "AtlasControlRegions.h"
#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace fs=std::filesystem;
namespace r=atlas::regions;
namespace n=atlas::normalization;
namespace {
constexpr std::uint64_t maximum_entries=64000,maximum_input_bytes=64*1024*1024;
constexpr std::size_t maximum_line_bytes=65536;
const std::string data_header="entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue";
const std::string mc_header="dsid,entry,run,event,mc_weight,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,C9_selected,roundoff_objects,invalid_reason,cartesian_mass_closure_pass";
void require(bool condition,const char* message) {
  if(!condition) throw std::invalid_argument(message);
}
std::uint64_t integer(std::string_view text) {
  require(!text.empty() && std::all_of(text.begin(),text.end(),[](unsigned char ch){return ch>='0'&&ch<='9';}),"Invalid unsigned integer");
  std::uint64_t value=0; const auto result=std::from_chars(text.data(),text.data()+text.size(),value);
  require(result.ec==std::errc{} && result.ptr==text.data()+text.size(),"Unsigned integer overflow"); return value;
}
bool boolean(std::string_view text) {
  require(text=="0" || text=="1","Boolean must be exact0 or1"); return text=="1";
}
double number(std::string_view text,bool optional=false) {
  if(text.empty()) {
    require(optional,"Required numeric field missing"); return std::numeric_limits<double>::quiet_NaN();
  }
  double value=0; const auto result=std::from_chars(text.data(),text.data()+text.size(),value);
  require(result.ec==std::errc{} && result.ptr==text.data()+text.size() && std::isfinite(value),"Malformed/nonfinite numeric cache field");
  return value;
}
std::vector<std::string> fields(const std::string& line) {
  require(line.find('"')==std::string::npos && line.find('\0')==std::string::npos,"Quoted/binary content is not the native cache schema");
  std::vector<std::string> result; std::size_t begin=0;
  while(true) {
    const auto end=line.find(',',begin); result.push_back(line.substr(begin,end-begin));
    if(end==std::string::npos) break;
    begin=end+1;
  }
  return result;
}
bool bounded_line(std::istream& input,std::string& line) {
  line.clear(); char ch=0;
  while(input.get(ch)) {
    if(ch=='\n') break;
    require(line.size()<maximum_line_bytes,"CSV line exceeds declared bound"); line.push_back(ch);
  }
  require(!input.bad(),"CSV read failed");
  if(line.empty() && !input && ch!='\n') return false;
  if(!line.empty() && line.back()=='\r') line.pop_back();
  return true;
}
std::string json_string(const std::string& text) {
  std::string result="\"";
  for(unsigned char ch:text) {
    if(ch=='"' || ch=='\\') { result.push_back('\\'); result.push_back(static_cast<char>(ch)); }
    else if(ch<32) throw std::invalid_argument("Control character in output provenance path");
    else result.push_back(static_cast<char>(ch));
  }
  return result+'"';
}
struct Row {
  std::uint64_t entry=0,run=0,event=0;
  bool cache_valid=false,c5=false,c5_jets=false,c9=false;
  r::Region region=r::Region::InvalidInput;
  double weight=1;
};
constexpr std::array<r::Region,8> region_order{
  r::Region::Control,r::Region::Validation,r::Region::ProspectiveSignal,r::Region::ReservedWindowPartition,
  r::Region::OutsideStudyDomain,r::Region::FailsPreMassSelection,r::Region::FailsJetSelection,r::Region::InvalidInput};
}
int main(int argc,char** argv) {
  try {
    require(argc==8,"Usage: phase5_region_inventory input.csv selection.ini NEW_output DATA|positive_DSID start exclusive_end PROVISIONAL");
    const fs::path input=argv[1],selection_path=argv[2],output=argv[3]; const std::string sample=argv[4];
    const bool data=sample=="DATA"; const auto dsid=data?0:integer(sample);
    require(data || (dsid>0 && dsid<=static_cast<std::uint64_t>(std::numeric_limits<int>::max())),"DSID must be positive native Int_t");
    const auto start=integer(argv[5]),end=integer(argv[6]);
    require(end>start && end-start<=maximum_entries && end<=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),"Invalid/oversized contiguous entry range");
    require(std::string_view(argv[7])=="PROVISIONAL","Only preserved PROVISIONAL unit status permitted");
    require(!fs::exists(output) && !fs::is_symlink(fs::symlink_status(output)),"Output path must be new; existing work is preserved");
    require(fs::is_regular_file(input) && fs::file_size(input)>0 && fs::file_size(input)<=maximum_input_bytes,"Missing/oversized regular derived-cache input");
    r::Config config; config.selection=atlas::selection::read_config(selection_path); r::validate_config(config);
    const auto input_path=json_string(fs::absolute(input).lexically_normal().string());
    const auto selection_json=json_string(fs::absolute(selection_path).lexically_normal().string());
    std::ifstream source(input,std::ios::binary); require(static_cast<bool>(source),"Cannot open derived cache");
    std::string line; require(bounded_line(source,line),"Missing cache header");
    const auto header=fields(line); std::set<std::string> unique_header;
    for(const auto& column:header) require(!column.empty() && unique_header.insert(column).second,"Missing/duplicate header column");
    require(line==(data?data_header:mc_header),"Input does not match exact published DATA28/MC24 cache schema");
    std::map<std::string,std::size_t> columns;
    for(std::size_t i=0;i<header.size();++i) columns.emplace(header[i],i);
    std::vector<Row> rows; rows.reserve(static_cast<std::size_t>(end-start));
    std::set<std::pair<std::uint64_t,std::uint64_t>> identities;
    while(bounded_line(source,line)) {
      require(!line.empty(),"Blank CSV row"); require(rows.size()<end-start,"Extra rows outside exact requested range");
      const auto row=fields(line); require(row.size()==header.size(),"CSV row width differs from native schema");
      const auto field=[&](const char* key)->const std::string& { return row[columns.at(key)]; };
      Row record; record.entry=integer(field("entry")); record.run=integer(field("run"));record.event=integer(field("event"));
      require(record.entry==start+rows.size(),"Entry order is not exact contiguous requested range");
      require(record.run<=std::numeric_limits<std::uint32_t>::max(),"run exceeds native UInt_t");
      require(identities.emplace(record.run,record.event).second,"Duplicate sample/run/event identity");
      record.cache_valid=boolean(field("valid"));
      const auto np=integer(field("photon_n")),nj=integer(field("jet_n"));
      require(np<=100000 && nj<=100000,"Object multiplicity exceeds preserved structural sanity bound");
      require(integer(field("roundoff_objects"))<=np+nj,"Invalid roundoff object count");
      if(!data) {
        require(integer(field("dsid"))==dsid,"Cache DSID does not match requested sample"); record.weight=number(field("mc_weight"));
        const bool closure=boolean(field("cartesian_mass_closure_pass"));
        require(!record.cache_valid || closure,"Valid MC row has unresolved numerical closure failure");
      }
      atlas::selection::Event e; e.source_valid=record.cache_valid; e.photons=static_cast<int>(np);e.jets=static_cast<int>(nj);
      e.photon_pt={number(field("photon1_pt"),true),number(field("photon2_pt"),true)};
      e.photon_eta={number(field("photon1_eta"),true),number(field("photon2_eta"),true)};
      e.jet_pt={number(field("jet1_pt"),true),number(field("jet2_pt"),true)};
      e.jet_eta={number(field("jet1_eta"),true),number(field("jet2_eta"),true)};
      e.mgg=number(field("m_gg"),true);e.mjj=number(field("m_jj"),true);
      const auto require_presence=[&](double value,bool expected) {
        require(std::isfinite(value)==expected,"Object/pair fields contradict published valid/multiplicity cache contract");
      };
      for(std::size_t i=0;i<2;++i) {
        const bool photon=record.cache_valid && np>i,jet=record.cache_valid && nj>i;
        require_presence(e.photon_pt[i],photon);require_presence(e.photon_eta[i],photon);
        require_presence(e.jet_pt[i],jet);require_presence(e.jet_eta[i],jet);
      }
      require_presence(e.mgg,record.cache_valid && np>=2);require_presence(e.mjj,record.cache_valid && nj>=2);
      require_presence(number(field("deltaR_gg"),true),record.cache_valid && np>=2);
      require_presence(number(field("deltaR_jj"),true),record.cache_valid && nj>=2);
      if(data) {
        for(const char* key:{"deltaEta_gg","deltaPhi_gg"}) require_presence(number(field(key),true),record.cache_valid && np>=2);
        for(const char* key:{"deltaEta_jj","deltaPhi_jj"}) require_presence(number(field(key),true),record.cache_valid && nj>=2);
        for(const char* key:{"p1_tight_id","p2_tight_id","p1_tight_iso","p2_tight_iso"})
          if(!field(key).empty()) (void)boolean(field(key));
      }
      require(!record.cache_valid || atlas::selection::valid_kinematics(e),"Valid cache row contradicts existing kinematic validity predicates");
      const auto passed=atlas::selection::evaluate(e,config.selection);
      record.c5=passed[5]; record.c9=passed[9];
      record.c5_jets=record.c5 && atlas::selection::jet_multiplicity(e) && atlas::selection::jet_pt(e,config.selection) && atlas::selection::jet_acceptance(e,config.selection);
      record.region=r::classify(e,config);
      if(!data) require(boolean(field("C9_selected"))==record.c9,"MC cached C9 does not match unchanged selection");
      rows.push_back(record);
    }
    require(rows.size()==end-start,"Incomplete requested cache range");
    // All parser and semantic guards finish before a new output directory is
    // created. Failed validation never overwrites or discards existing work.
    fs::create_directories(output.parent_path().empty()?fs::path("."):output.parent_path());
    require(fs::create_directory(output),"Cannot create fresh output directory");
    std::ofstream ledger(output/"event_regions.csv"),counts(output/"region_counts.csv"),summary(output/"summary.json");
    for(auto* stream:{&ledger,&counts,&summary}) stream->exceptions(std::ios::badbit|std::ios::failbit);
    ledger<<std::setprecision(17)<<"sample_id,entry,run,event,cache_valid,C5,C5_plus_jets,C9,region,raw_weight,unit_status,weight_scope\n";
    std::map<r::Region,n::SignedSums> by_region;
    for(auto region:region_order) by_region.emplace(region,n::SignedSums{});
    std::array<n::SignedSums,5> by_population;
    const std::string weight_scope=data?"RAW_UNWEIGHTED_DATA_DIAGNOSTIC":"RAW_MC_WEIGHT_DIAGNOSTIC_SEMANTICS_UNKNOWN";
    for(const auto& row:rows) {
      ledger<<sample<<','<<row.entry<<','<<row.run<<','<<row.event<<','<<row.cache_valid<<','<<row.c5<<','<<row.c5_jets<<','<<row.c9<<','<<r::name(row.region)<<','<<row.weight<<",PROVISIONAL,"<<weight_scope<<'\n';
      by_region.at(row.region).add(row.weight); by_population[0].add(row.weight);
      if(row.cache_valid) by_population[1].add(row.weight);
      if(row.c5) by_population[2].add(row.weight);
      if(row.c5_jets) by_population[3].add(row.weight);
      if(row.c9) by_population[4].add(row.weight);
    }
    counts<<std::setprecision(std::numeric_limits<long double>::max_digits10)
          <<"category,kind,raw_entries,positive_weights,negative_weights,zero_weights,sumW,sumW2,sumAbsW,effective_entries,weight_scope\n";
    const auto write_count=[&](const char* category,const char* kind,const n::SignedSums& s) {
      counts<<category<<','<<kind<<','<<s.entries<<','<<s.positive<<','<<s.negative<<','<<s.zero<<','<<s.sumw<<','<<s.sumw2<<','<<s.sumabs<<','<<s.effective_entries()<<','<<weight_scope<<'\n';
    };
    for(auto region:region_order) write_count(r::name(region),"DISJOINT_REGION",by_region.at(region));
    constexpr std::array<const char*,5> population_names{"INPUT","CACHE_VALID","C5","C5_PLUS_JETS","C9"};
    for(std::size_t i=0;i<population_names.size();++i) write_count(population_names[i],"OVERLAPPING_DIAGNOSTIC_POPULATION",by_population[i]);
    summary<<"{\n  \"status\":\"PASS_BOUNDED_DERIVED_CACHE_INVENTORY\",\n  \"scope\":\"DESCRIPTIVE_ONLY_NO_PHYSICAL_BACKGROUND_PREDICTION\",\n"
           <<"  \"sample_id\":"<<json_string(sample)<<",\n  \"input_cache\":"<<input_path<<",\n  \"selection_file\":"<<selection_json<<",\n"
           <<"  \"cache_schema\":\""<<(data?"DATA_PHASE2_28":"MC_PHASE4_24")<<"\",\n  \"region_definition\":\"study-regions-v1\",\n"
           <<"  \"selection_definition\":"<<json_string(config.selection.version)<<",\n  \"start\":"<<start<<",\n  \"end_exclusive\":"<<end<<",\n"
           <<"  \"entries\":"<<rows.size()<<",\n  \"C5\":"<<by_population[2].entries<<",\n  \"C5_plus_jets\":"<<by_population[3].entries<<",\n  \"C9\":"<<by_population[4].entries<<",\n"
           <<"  \"outside_study_domain\":"<<by_region.at(r::Region::OutsideStudyDomain).entries<<",\n"
           <<"  \"unit_status\":\"PROVISIONAL\",\n  \"generator_weight_semantics\":\""<<(data?"NOT_APPLICABLE":"UNKNOWN")<<"\",\n"
           <<"  \"weight_scope\":"<<json_string(weight_scope)<<",\n  \"normalization_applied\":false,\n  \"scale_factors_applied\":false,\n  \"physical_transfer_factor_applied\":false,\n"
           <<"  \"physical_closure_status\":\"BLOCKED\",\n  \"native_ROOT_read_by_this_app\":false,\n  \"source_ROOT_identity_verified_by_this_app\":false,\n"
           <<"  \"limits\":{\"max_entries\":"<<maximum_entries<<",\"max_input_bytes\":"<<maximum_input_bytes<<",\"max_line_bytes\":"<<maximum_line_bytes<<"}\n}\n";
    ledger.close();counts.close();summary.close();
    std::cout<<"PASS descriptive region inventory: "<<rows.size()<<" entries, C9="<<by_population[4].entries<<", outside-domain="<<by_region.at(r::Region::OutsideStudyDomain).entries<<"; PROVISIONAL; NO PHYSICAL TF\n";
    return 0;
  } catch(const std::exception& e) { std::cerr<<"FAIL region inventory: "<<e.what()<<'\n'; return 1; }
}

#include "Phase8Dataset.hxx"
#include <array>
#include <iomanip>
#include <cmath>
namespace atlas_hh::phase8 {
void demand(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}
std::string file_sha256(const fs::path& p){std::ifstream in(p,std::ios::binary);demand(in.good(),"missing/unreadable input "+p.string());atlas_hh::Sha256 h;std::array<char,65536>b;while(in.read(b.data(),b.size())||in.gcount())h.update(b.data(),in.gcount());demand(in.eof(),"hash read error");return h.finish();}
Json read_json(const fs::path& p){std::ifstream f(p);demand(f.good(),"missing JSON "+p.string());return Json::parse(f);}
std::ofstream exclusive_text(const fs::path& p){demand(!fs::exists(p),"refuse existing output "+p.string());std::ofstream s(p);demand(s.good(),"cannot create output");s<<std::setprecision(17);return s;}
void write_json(const fs::path& p,const Json& j){auto f=exclusive_text(p);f<<j.dump(2)<<'\n';demand(f.good(),"JSON write failure");}
void fresh_directory(const fs::path& p){demand(!fs::exists(p),"refuse existing output directory");demand(fs::is_directory(p.parent_path()),"output parent missing");demand(fs::create_directory(p),"cannot create output directory");}
std::vector<Dataset> datasets(const Json& j){
 demand(j.contains("datasets")&&j.at("datasets").is_array(),"manifest datasets missing");std::vector<Dataset> result;std::set<std::string>ids;
 const std::set<std::string> allowed{"S01_B100","S01_C1000","B01","B02","B03","B04","B05","B06"};
 for(const auto& v:j.at("datasets")){
  Dataset d;d.id=v.at("dataset_id");d.process=v.at("process");d.truth_format=v.at("truth_format");d.scope=v.at("source_weight_scope");
  demand(allowed.count(d.id)&&ids.insert(d.id).second,"unknown/duplicate dataset");d.root=v.at("root_path").get<std::string>();d.index=v.at("input_index_path").get<std::string>();d.truth=v.at("truth_index_path").get<std::string>();d.card=v.at("card_path").get<std::string>();
  d.root_hash=v.at("root_sha256");d.index_hash=v.at("input_index_sha256");d.truth_hash=v.at("truth_index_sha256");d.card_hash=v.at("card_sha256");d.entries=v.at("expected_entries");d.original=v.at("N_original");d.full=v.at("is_full");d.br=v.value("model_br_factor",1.0);d.expected=v.at("expected_cutflow").get<std::vector<long>>();
  demand(d.entries>0&&d.original>1&&d.entries<=d.original&&d.expected.size()==5,"invalid source denominator/count");demand(d.original==(d.id=="S01_B100"?100:1000),"wrong dataset source version");demand(d.full==(d.entries==d.original),"prefix/full inconsistency");demand(std::isfinite(d.br)&&d.br>0&&d.br<=1,"invalid model BR");
  demand(d.truth_format=="signal"||d.truth_format=="continuum"||d.truth_format=="new_background","unsupported truth format");
  for(const auto& h:{d.root_hash,d.index_hash,d.truth_hash,d.card_hash})demand(h.size()==64&&h.find_first_not_of("0123456789abcdef")==std::string::npos,"invalid expected SHA256");
  result.push_back(std::move(d));
 }demand(!result.empty(),"empty manifest");return result;
}
void verify_dataset_files(const Dataset& d){for(const auto& [p,h]:std::vector<std::pair<fs::path,std::string>>{{d.root,d.root_hash},{d.index,d.index_hash},{d.truth,d.truth_hash},{d.card,d.card_hash}})demand(file_sha256(p)==h,"input hash mismatch "+d.id+" "+p.filename().string());
 std::ifstream in(d.card);std::string t((std::istreambuf_iterator<char>(in)),{});std::string key="set RandomSeed ";auto b=t.find(key);demand(b!=std::string::npos&&t.find(key,b+key.size())==std::string::npos,"ambiguous native card seed");b+=key.size();auto end=t.find('\n',b);demand(end!=std::string::npos,"truncated card seed");auto s=t.substr(b,end-b);demand(!s.empty()&&s.find_first_not_of("0123456789")==std::string::npos,"invalid card seed");t.replace(b,end-b,"610301");demand(atlas_hh::Sha256::digest(t)=="cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47","unreviewed Delphes efficiency/physics card");
}
void verify_selection(const Json& j){for(const auto&[k,v]:std::map<std::string,double>{{"photon_leading_pt",35},{"photon_subleading_pt",25},{"photon_max_abs_eta",2.37},{"photon_crack_min",1.37},{"photon_crack_max",1.52},{"jet_min_pt",25},{"jet_max_abs_eta",2.5},{"btag_mask",1},{"mgg_min",105},{"mgg_max",160}})demand(j.contains(k)&&j.at(k).is_number()&&j.at(k).get<double>()==v,"baseline selection mismatch "+k);}
}

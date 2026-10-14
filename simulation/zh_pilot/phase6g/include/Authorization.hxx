#pragma once
#include "StrictJson.hxx"
#include "Sha256.hxx"
#include <array>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <regex>
#include <stdexcept>
#include <string>

namespace zh {
namespace fs=std::filesystem;
inline void require(bool ok,const std::string& text){if(!ok)throw std::runtime_error(text);}
inline std::string read_file(const fs::path& path,std::uintmax_t cap=1024*1024){
  require(fs::is_regular_file(path)&&!fs::is_symlink(path)&&fs::file_size(path)<=cap,"Invalid bounded receipt/input file");
  std::ifstream stream(path,std::ios::binary);require(stream.good(),"Cannot open bounded file");
  return std::string(std::istreambuf_iterator<char>(stream),{});
}
inline std::string file_sha(const fs::path& path){
  std::ifstream stream(path,std::ios::binary);require(stream.good(),"Cannot hash input file");
  atlas_hh::Sha256 hash;std::array<char,65536> bytes{};
  while(stream.read(bytes.data(),bytes.size())||stream.gcount())hash.update(bytes.data(),stream.gcount());
  require(stream.eof(),"Input hashing failed");return hash.finish();
}
inline bool beneath(const fs::path& child,const fs::path& parent){
  auto c=fs::weakly_canonical(child),p=fs::weakly_canonical(parent);auto ci=c.begin();
  for(auto pi=p.begin();pi!=p.end();++pi,++ci)if(ci==c.end()||*ci!=*pi)return false;
  return ci!=c.end();
}
struct StageRequest {
  std::string authorization,authorization_sha,bridge_sha,input,index,index_sha,source_hash,output,stage;
  long events=0,total=0;int seed=0;double max_hours=0,max_disk_gb=0;
};
inline void check_live_state(const Json& stage,const Json& live,double now){
  const double deadline=stage.at("deadline_epoch_seconds").number();
  require(live.at("status").string()=="AUTHORIZED_EXECUTION_IN_PROGRESS"&&
    live.at("ticket_id").string()==stage.at("ticket_id").string(),"BLOCKED_PHYSICAL_AUTHORIZATION: root job closed or different ticket");
  require(std::isfinite(deadline)&&deadline>now,"BLOCKED_PHYSICAL_AUTHORIZATION: stage deadline expired");
}
inline Json check_authorization(const StageRequest& args,const std::string& executable_key){
  require(!args.authorization.empty(),"BLOCKED_PHYSICAL_AUTHORIZATION: missing stage receipt");
  fs::path output=fs::weakly_canonical(args.output),auth=fs::weakly_canonical(args.authorization);
  require(fs::path(args.output).is_absolute()&&fs::path(args.authorization).is_absolute(),"Absolute stage output/receipt required");
  require(auth==output/"execution_authorization.json","Authorization receipt must be in exact stage output");
  std::string bytes=read_file(args.authorization);require(atlas_hh::Sha256::digest(bytes)==args.authorization_sha,"Authorization receipt hash changed");
  auto value=parse_json(bytes);
  require(value.at("schema_version").integer()==1&&value.at("status").string()=="AUTHORIZED_EXECUTION_IN_PROGRESS"&&
    value.at("authorization_command").string()=="AUTHORIZE_PHASE6G_ZH_100_RUN","BLOCKED_PHYSICAL_AUTHORIZATION: invalid command/status");
  require(value.at("reviewed_base_head").string()=="05cff9a5d991ba6782b339bc41932ae4da296d8c","Unreviewed physical bridge base");
  require(std::regex_match(value.at("ticket_id").string(),std::regex("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")),"Missing exact ticket identity");
  auto request=value.at("source_request");
  require(request.at("process").string()=="zh"&&request.at("events").integer()==100&&request.at("energy_gev").integer()==13000,
    "Authorization target differs from zh10013TeV");
  require(request.at("seed").integer()==args.seed&&args.seed>0&&args.seed<=900000000,"Authorization seed mismatch");
  const double hours=request.at("max_hours").number(),disk=request.at("max_disk_gb").number();
  require(std::isfinite(hours)&&std::isfinite(disk)&&hours>0&&hours<=2&&disk>0&&disk<=5&&
    std::isfinite(args.max_hours)&&args.max_hours>0&&args.max_hours<=hours&&
    std::isfinite(args.max_disk_gb)&&args.max_disk_gb>0&&args.max_disk_gb<=disk,"Authorization resource ceiling mismatch");
  require(value.at("child_stage").string()==args.stage&&
    ((args.stage=="prefix10"&&args.events==10)||(args.stage=="full100"&&args.events==100))&&args.total==100&&
    value.at("source_total_events").integer()==100,"Authorization stage/source count mismatch");
  require(fs::weakly_canonical(value.at("child_output").string())==output&&beneath(output,request.at("output").string()),"Authorization child output mismatch");
  if(executable_key=="native_runner_sha256"){
    auto root=fs::weakly_canonical(request.at("output").string());
    auto live=parse_json(read_file(root/"run_manifest.json"));
    check_live_state(value,live,static_cast<double>(std::time(nullptr)));
  }
  require(value.at("bridge_sha256").string()==args.bridge_sha&&args.bridge_sha.size()==64,"Reviewed bridge hash mismatch");
  require(file_sha("/proc/self/exe")==value.at(executable_key).string(),"Native executable identity mismatch");
  require(value.at("source_original_sha256").string()==args.source_hash&&args.source_hash.size()==64,"Original LHE identity mismatch");
  require(fs::weakly_canonical(value.at("source_lhe_path").string())==fs::weakly_canonical(args.input)&&
    file_sha(args.input)==value.at("source_lhe_sha256").string(),"Full plain source LHE bytes changed");
  require(fs::weakly_canonical(value.at("source_index_path").string())==fs::weakly_canonical(args.index)&&
    file_sha(args.index)==value.at("source_index_sha256").string()&&file_sha(args.index)==args.index_sha,"Source index bytes changed");
  return value;
}
}

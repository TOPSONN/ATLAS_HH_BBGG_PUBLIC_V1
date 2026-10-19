"""Exact private MG5 source copy and an explicitly unapproved config proposal.
No MG5/Python-model imports, shell commands, process execution or normalization.
"""
from __future__ import annotations
import hashlib,json,os,stat
from pathlib import Path

COUNTERS={"new_MG5_processes":0,"new_ME_calls":0,"new_integrals":0,
          "new_hard_events":0,"new_pythia_events":0,"new_delphes_events":0}
def require(ok,reason):
 if not ok:raise ValueError(reason)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return digest(json.dumps(value,sort_keys=True,separators=(",",":")).encode())
def write_new(path,raw,mode=0o600):
 fd=os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,"O_NOFOLLOW",0),mode)
 with os.fdopen(fd,"wb") as stream:stream.write(raw)
def write_json(path,value):write_new(path,(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode())
def ensure_fresh_output(path,allowed_parent):
 path,allowed_parent=Path(path),Path(allowed_parent)
 require(path.is_absolute() and ".." not in path.parts,"OUTPUT_PATH_TRAVERSAL")
 require(path.parent.is_dir() and not path.exists() and not path.is_symlink(),"FRESH_EXISTING_PARENT_REQUIRED")
 for parent in (path.parent,*path.parent.parents):require(not parent.is_symlink(),"OUTPUT_PARENT_SYMLINK")
 resolved=path.resolve();require(resolved!=allowed_parent.resolve() and resolved.is_relative_to(allowed_parent.resolve()),"OUTPUT_OUTSIDE_REVIEW_WORKSPACE")
 return resolved
def relative_path(text):
 path=Path(text);require(text and not path.is_absolute() and ".." not in path.parts and path.as_posix()==text,"INVALID_MANIFEST_RELATIVE_PATH")
 return path
def file_identity(path):
 path=Path(path);fd=os.open(str(path),os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
 with os.fdopen(fd,"rb") as stream:
  before=os.fstat(stream.fileno());require(stat.S_ISREG(before.st_mode),"SOURCE_NOT_REGULAR")
  h=hashlib.sha256()
  for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
  after=os.fstat(stream.fileno())
 require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),"SOURCE_CHANGED_DURING_READ")
 return {"bytes":after.st_size,"sha256":h.hexdigest(),"device":after.st_dev,"inode":after.st_ino,
         "mode":stat.S_IMODE(after.st_mode),"mtime_ns":after.st_mtime_ns,"ctime_ns":after.st_ctime_ns}
def inspect_tree(root,limits):
 root=Path(root).resolve(strict=True);require(root.is_dir(),"SOURCE_ROOT_NOT_DIRECTORY");rows=[];identities={};total=0;regular=0;links=0;broken=0
 for base,dirs,files in os.walk(root,followlinks=False):
  base=Path(base)
  for name in sorted(dirs+files):
   path=base/name;rel=path.relative_to(root).as_posix();relative_path(rel);value=path.lstat()
   require(not (value.st_mode & (stat.S_ISUID|stat.S_ISGID)),"PRIVILEGED_SOURCE_MODE_NOT_REVIEWED")
   if path.is_symlink():
    if name in dirs:dirs.remove(name)
    target=os.readlink(path);require(not Path(target).is_absolute(),"ABSOLUTE_SOURCE_SYMLINK")
    try:resolved=path.resolve()
    except (OSError,RuntimeError) as error:raise ValueError("SOURCE_SYMLINK_LOOP_OR_ERROR") from error
    require(resolved.is_relative_to(root),"SOURCE_SYMLINK_ESCAPES_RUNTIME")
    exists=path.exists();links+=1;broken+=not exists
    rows.append({"relative_path":rel,"type":"SYMLINK" if exists else "BROKEN_INTERNAL_SYMLINK",
                 "link_target":target,"resolved_relative_path":resolved.relative_to(root).as_posix(),
                 "target_exists":exists,"bytes":None,"sha256":None})
   elif stat.S_ISDIR(value.st_mode):
    rows.append({"relative_path":rel,"type":"DIRECTORY","mode":stat.S_IMODE(value.st_mode)})
   elif stat.S_ISREG(value.st_mode):
    info=file_identity(path);require(info["bytes"]<=limits["max_single_file_bytes"],"SINGLE_SOURCE_FILE_SIZE_LIMIT")
    total+=info["bytes"];regular+=1
    rows.append({"relative_path":rel,"type":"FILE","bytes":info["bytes"],"sha256":info["sha256"],"mode":info["mode"]})
    identities[rel]={key:info[key] for key in ("device","inode","mtime_ns","ctime_ns")}
   else:raise ValueError("SPECIAL_SOURCE_FILE_NOT_REVIEWED:"+rel)
   require(len(rows)<=limits["max_entries"] and total<=limits["max_total_regular_bytes"],"SOURCE_TREE_LIMIT")
 rows.sort(key=lambda row:row["relative_path"])
 return {"root":str(root),"entries":rows,"content_manifest_sha256":canonical(rows),"source_stat_identity":identities,
         "entry_count":len(rows),"regular_file_count":regular,"regular_bytes":total,
         "symlink_count":links,"broken_internal_symlink_count":broken}
def independent_copy(source,destination,manifest):
 source,destination=Path(source).resolve(),Path(destination)
 require(not destination.exists() and not destination.is_symlink(),"COPY_DESTINATION_EXISTS")
 require(not destination.resolve().is_relative_to(source),"COPY_INSIDE_ORIGINAL_FORBIDDEN")
 destination.mkdir(mode=0o700)
 directories=[row for row in manifest["entries"] if row["type"]=="DIRECTORY"]
 for row in sorted(directories,key=lambda row:len(Path(row["relative_path"]).parts)):
  (destination/relative_path(row["relative_path"])).mkdir()
 for row in manifest["entries"]:
  rel=relative_path(row["relative_path"]);src,dst=source/rel,destination/rel
  if row["type"]=="FILE":
   require(src.is_file() and not src.is_symlink(),"SOURCE_FILE_TYPE_CHANGED")
   source_fd=os.open(str(src),os.O_RDONLY|getattr(os,"O_NOFOLLOW",0));target_fd=None;h=hashlib.sha256()
   try:
    before=os.fstat(source_fd);require((before.st_dev,before.st_ino)==tuple(manifest["source_stat_identity"][str(rel)][key] for key in ("device","inode")),"SOURCE_INODE_CHANGED")
    target_fd=os.open(str(dst),os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
    with os.fdopen(source_fd,"rb",closefd=False) as reader,os.fdopen(target_fd,"wb",closefd=False) as writer:
     for block in iter(lambda:reader.read(1024*1024),b""):writer.write(block);h.update(block)
    after=os.fstat(source_fd)
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),"SOURCE_CHANGED_DURING_COPY")
    require(after.st_size==row["bytes"] and h.hexdigest()==row["sha256"],"STALE_SOURCE_BYTES_DURING_COPY")
   finally:
    os.close(source_fd)
    if target_fd is not None:os.close(target_fd)
   os.chmod(dst,row["mode"])
  elif row["type"] in ("SYMLINK","BROKEN_INTERNAL_SYMLINK"):
   require(src.is_symlink() and os.readlink(src)==row["link_target"],"SOURCE_SYMLINK_CHANGED")
   dst.symlink_to(row["link_target"])
 for row in sorted(directories,key=lambda row:len(Path(row["relative_path"]).parts),reverse=True):
  os.chmod(destination/row["relative_path"],row["mode"])
 return destination
def verify_copy(source_manifest,copied_manifest):
 require(source_manifest["entries"]==copied_manifest["entries"],"COPIED_BYTES_OR_LINK_LAYOUT_MISMATCH")
 originals={(row["device"],row["inode"]) for row in source_manifest["source_stat_identity"].values()}
 copies=[(row["device"],row["inode"]) for row in copied_manifest["source_stat_identity"].values()]
 require(not originals.intersection(copies),"SHARED_ORIGINAL_HARDLINK")
 require(len(copies)==len(set(copies)),"COPIED_FILES_SHARE_HARDLINKS")
 return {"exact_content_and_link_manifest_equal":True,"no_shared_original_inodes":True,
         "no_copied_regular_file_hardlinks":True,"symlinks_resolve_inside_new_tree":True,
         "broken_internal_links_explicitly_retained":copied_manifest["broken_internal_symlink_count"]}
def config_settings(raw):
 result={}
 for line in raw.decode().splitlines():
  line=line.split("#",1)[0].strip()
  if not line:continue
  require("=" in line,"UNKNOWN_CONFIG_LINE")
  key,value=(part.strip() for part in line.split("=",1));require(key not in result,"DUPLICATE_CONFIG_KEY");result[key]=value
 return result
def proposed_config(raw,old_root,new_root):
 """One explicit semantic edit in a new candidate only; never activate it."""
 before=config_settings(raw);require(before.get("mg5_path")==str(Path(old_root)),"EMBEDDED_MG5_PATH_NOT_REVIEWED")
 lines=raw.splitlines(keepends=True);found=0;out=[]
 for line in lines:
  active=line.split(b"#",1)[0].strip()
  if b"=" in active and active.split(b"=",1)[0].strip()==b"mg5_path":
   require(b"#" not in line,"MG5_PATH_COMMENT_REQUIRES_REVIEW")
   newline=b"\n" if line.endswith(b"\n") else b""
   out.append(b"mg5_path = "+str(Path(new_root)).encode()+newline);found+=1
  else:out.append(line)
 require(found==1,"EXACT_ONE_MG5_PATH_REQUIRED")
 candidate=b"".join(out);after=config_settings(candidate)
 require(set(before)==set(after) and [key for key in before if before[key]!=after[key]]==["mg5_path"],"UNREVIEWED_CONFIG_TRANSFORMATION")
 require(digest(raw)!=digest(candidate),"CONFIG_PROPOSAL_DID_NOT_CHANGE")
 return candidate,{"status":"PROPOSED_UNAPPROVED_UNACTIVATED","old_raw_identity":{"bytes":len(raw),"sha256":digest(raw)},
                   "proposed_raw_identity":{"bytes":len(candidate),"sha256":digest(candidate)},
                   "changed_setting_keys":["mg5_path"],"original_installed_config_modified":False,
                   "exact_copied_raw_config_modified":False,"activated":False,"new_baseline_approved":False,
                   "reason":"An explicit private candidate rebinds only mg5_path to the isolated MG5 copy; no whitespace normalization or old-gate promotion",
                   "historical_writer":"UNKNOWN","old_phase11_gate":"BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT"}
def validate_policy(policy):
 require(policy.get("schema_version")==1,"LAYOUT_SCHEMA")
 require(policy.get("MG5_version")=="3.5.16" and policy.get("parser_executed") is False,"NO_MG5_EXECUTION")
 require(policy.get("physical_authorization") is False and policy.get("dispatcher") is None and policy.get("new_baseline_approved") is False,"NO_EXECUTION_OR_APPROVAL")
 require(policy.get("historical_writer")=="UNKNOWN" and policy.get("old_phase11_gate")=="BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT","HISTORICAL_PROVENANCE_REQUIRED")
 require(policy.get("source_root")=="/home/btu/opt/mg5amcnlo" and policy.get("source_resolved_root")=="/home/btu/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16","UNREVIEWED_SOURCE_ROOT")
 require(policy.get("allowed_output_parent")=="/home/btu/simulations/hh_phase13/run_01","UNREVIEWED_OUTPUT_ROOT")
 require(policy.get("expected_config")=={"bytes":9302,"sha256":"e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1"},"UNREVIEWED_CONFIG_BASELINE")
 require(policy.get("limits")=={"max_entries":8192,"max_single_file_bytes":33554432,"max_total_regular_bytes":268435456},"UNREVIEWED_COPY_LIMITS")
 return True
def prepare(source,output,policy):
 validate_policy(policy);source=Path(source).resolve(strict=True)
 require(str(source)==policy["source_resolved_root"],"RESOLVED_SOURCE_ROOT_CHANGED")
 output=ensure_fresh_output(output,policy["allowed_output_parent"])
 config=source/"input/mg5_configuration.txt";config_before=file_identity(config)
 require({key:config_before[key] for key in ("bytes","sha256")}==policy["expected_config"],"STALE_RUNTIME_CONFIG_BASELINE")
 before=inspect_tree(source,policy["limits"]);output.mkdir(mode=0o700);private=output/"private";private.mkdir(mode=0o700)
 write_json(private/"original_source_manifest.json",before)
 runtime=independent_copy(source,private/"mg5",before)
 copied=inspect_tree(runtime,policy["limits"]);proof=verify_copy(before,copied)
 after=inspect_tree(source,policy["limits"]);require(before==after,"ORIGINAL_RUNTIME_CHANGED_DURING_PREPARATION")
 write_json(private/"copied_source_manifest.json",copied);write_json(private/"original_source_manifest_after.json",after)
 for name in ("home","tmp","output","logs","xdg_config","xdg_cache","xdg_state","config_proposals","synthetic_write_fixtures"):(private/name).mkdir(mode=0o700)
 raw=(runtime/"input/mg5_configuration.txt").read_bytes()
 require({"bytes":len(raw),"sha256":digest(raw)}==policy["expected_config"],"COPIED_CONFIG_HASH_MISMATCH")
 candidate,proposal=proposed_config(raw,source,runtime);proposal_path=private/"config_proposals/mg5_configuration_proposed_v1.txt";write_new(proposal_path,candidate)
 write_new(private/"synthetic_write_fixtures/copied_config_fixture.txt",raw)
 proposal.update(path=str(proposal_path),copied_raw_config_path=str(runtime/"input/mg5_configuration.txt"))
 environment={"HOME":str(private/"home"),"TMPDIR":str(private/"tmp"),"TMP":str(private/"tmp"),"TEMP":str(private/"tmp"),
              "XDG_CONFIG_HOME":str(private/"xdg_config"),"XDG_CACHE_HOME":str(private/"xdg_cache"),
              "XDG_STATE_HOME":str(private/"xdg_state"),"PYTHONDONTWRITEBYTECODE":"1"}
 result={"schema_version":1,"evidence_class":"ACTUAL_PRIVATE_RUNTIME_COPY","status":"EXACT_COPY_PREPARED_NOT_EXECUTED",
         "source_root":str(source),"isolated_runtime_root":str(runtime),"source_manifest_sha256":before["content_manifest_sha256"],
         "copied_manifest_sha256":copied["content_manifest_sha256"],"regular_files":before["regular_file_count"],
         "regular_bytes":before["regular_bytes"],"symlink_count":before["symlink_count"],
         "broken_internal_symlinks":[row for row in before["entries"] if row["type"]=="BROKEN_INTERNAL_SYMLINK"],
         "copy_isolation_proof":proof,"installed_runtime_unchanged_during_copy":True,
         "original_config_identity":policy["expected_config"],"copied_raw_config_identity":{"bytes":len(raw),"sha256":digest(raw)},
         "embedded_old_runtime_path_in_raw_config":True,"configuration_proposal":proposal,
         "fresh_environment_proposal":environment,"fresh_output":str(private/"output"),
         "synthetic_write_fixture":str(private/"synthetic_write_fixtures/copied_config_fixture.txt"),
         "OS_write_confinement_status":"ROOT_SEPARATE_ENFORCEMENT_REVIEW_REQUIRED",
         "future_MG5_startup_success":"UNVERIFIED_NOT_EXECUTED",
         "parser_execution_authorized":False,"new_baseline_approved":False,"historical_writer":"UNKNOWN",
         "original_Phase11_gate":"BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT",
         "private_source_config_binaries_or_test_event_fixtures_published":False,
         "private_manifest_files":{str(path):digest(path.read_bytes()) for path in (
          private/"original_source_manifest.json",private/"copied_source_manifest.json",private/"original_source_manifest_after.json")},
         **COUNTERS}
 config_final=file_identity(config)
 require(config_final==config_before,"ORIGINAL_CONFIG_CHANGED_DURING_PREPARATION")
 write_json(output/"isolated_runtime_identity.json",result)
 write_json(output/"installed_runtime_preservation.json",{"status":"PASS_EXACT_ORIGINAL_PRESERVATION_DURING_COPY",
            "source_manifest_before":before["content_manifest_sha256"],"source_manifest_after":after["content_manifest_sha256"],
            "source_stat_identity_unchanged":before["source_stat_identity"]==after["source_stat_identity"],
            "config_identity_before":{key:config_before[key] for key in ("bytes","sha256")},
            "config_identity_after":{key:config_final[key] for key in ("bytes","sha256")},
            "original_installed_writes_performed":False,**COUNTERS})
 return result

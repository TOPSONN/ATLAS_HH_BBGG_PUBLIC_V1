"""Bounded, read-only runtime observations and independent string algebra.
Never imports MG5, dispatches a generator, normalizes or writes installed files.
"""
from __future__ import annotations
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat
import time

HISTORICAL = {
 "A": {"bytes": 9212, "sha256": "83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85"},
 "B": {"bytes": 9239, "sha256": "9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506"},
 "C": {"bytes": 9266, "sha256": "82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a"},
}
KEYS = ("fortran_compiler", "cpp_compiler", "auto_update")
PUBLIC_SETTINGS = KEYS
COUNTERS = {"new_ME_calls": 0, "new_integrals": 0, "new_hard_events": 0,
            "new_pythia_events": 0, "new_delphes_events": 0}
def demand(ok, reason):
 if not ok: raise ValueError(reason)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat(timespec="microseconds")
def identity(raw): return {"bytes": len(raw), "sha256": sha(raw)}
def json_hash(value): return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
def private_write(path, raw):
 """New local artifacts only; never replace an existing path."""
 descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
 with os.fdopen(descriptor, "wb") as stream: stream.write(raw)
def write_json(path, value):
 private_write(path, (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n").encode())
def safe_output(path, allowed_root, forbidden_roots):
 resolved, allowed = Path(path).resolve(), Path(allowed_root).resolve()
 demand(resolved != allowed and resolved.is_relative_to(allowed), "OUTPUT_OUTSIDE_NEW_REVIEW_WORKSPACE")
 for root in forbidden_roots:
  demand(not resolved.is_relative_to(Path(root).resolve()), "INSTALLED_PATH_WRITE_FORBIDDEN")
 return resolved
def validate_policy(policy):
 demand(policy.get("schema_version") == 1, "POLICY_SCHEMA")
 expected={"target":"/home/btu/opt/mg5amcnlo/input/mg5_configuration.txt",
           "expected_resolved":"/home/btu/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16/input/mg5_configuration.txt",
           "allowed_output_root":"/home/btu/simulations/hh_phase12",
           "serializer_source":"/home/btu/opt/mg5amcnlo/madgraph/interface/extended_cmd.py"}
 demand(all(policy.get(key)==value for key,value in expected.items()),"UNREVIEWED_RUNTIME_PATH_POLICY")
 demand(set(policy.get("forbidden_write_roots",[]))=={"/home/btu/opt","/home/btu/.local/share/atlas-hh-phase6a","/home/btu/miniforge3"},"INSTALLED_WRITE_GUARD_REMOVED")
 demand(type(policy.get("worker_timeout_seconds")) is int and policy["worker_timeout_seconds"]==30,"UNBOUNDED_SNAPSHOT_WORKER")
 demand(policy.get("new_baseline_approved") is False, "SILENT_BASELINE_APPROVAL")
 demand(policy.get("physical_execution_authorized") is False, "PHYSICAL_EXECUTION_NOT_AUTHORIZED")
 demand(policy.get("dispatcher") is None, "PRODUCTION_DISPATCHER_FORBIDDEN")
 demand(policy.get("old_phase11_raw_gate") == "BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT", "HISTORICAL_GATE_FALSE_PROMOTION")
 demand(policy.get("max_config_bytes") == 65536 and policy.get("snapshot_count") == 3, "BOUNDED_SNAPSHOT_POLICY")
 demand(bool(policy.get("independent_review_requirements")), "MISSING_INDEPENDENT_REVIEW")
 return True
def semantic_settings(raw):
 """Read MG5-style key/value text; no evaluation, environment expansion or default filling."""
 result = {}
 for line in raw.decode("utf-8").splitlines():
  line = line.split("#", 1)[0].strip()
  if not line: continue
  demand("=" in line, "UNKNOWN_ACTIVE_CONFIGURATION_LINE")
  key, value = (part.strip() for part in line.split("=", 1))
  demand(key and key not in result, "DUPLICATE_OR_EMPTY_SETTING")
  result[key] = value
 return result
def public_settings(settings):
 return {key: settings[key] for key in PUBLIC_SETTINGS if key in settings}
def stat_identity(value):
 return {"device": value.st_dev, "device_major": os.major(value.st_dev) if hasattr(os,"major") else None,
         "device_minor": os.minor(value.st_dev) if hasattr(os,"minor") else None, "inode": value.st_ino,
         "mode_octal": oct(stat.S_IMODE(value.st_mode)), "uid": getattr(value,"st_uid",None),
         "gid": getattr(value,"st_gid",None), "links": value.st_nlink, "bytes": value.st_size,
         "atime_ns": value.st_atime_ns, "mtime_ns": value.st_mtime_ns, "ctime_ns": value.st_ctime_ns}
def filesystem_identity(path):
 result = {}
 try:
  v = os.statvfs(path)
  result = {"filesystem_id": getattr(v,"f_fsid",None), "block_size": v.f_bsize,
            "fragment_size": v.f_frsize, "flags": v.f_flag}
 except (AttributeError, OSError): result["statvfs_available"] = False
 mountinfo = Path("/proc/self/mountinfo")
 if mountinfo.is_file():
  candidates = []
  for line in mountinfo.read_text().splitlines():
   if " - " not in line: continue
   left,right=line.split(" - ",1); a,b=left.split(),right.split()
   point=a[4].replace("\\040"," ").replace("\\134","\\")
   if Path(path).is_relative_to(Path(point)): candidates.append((len(point),a,b))
  if candidates:
   _,a,b=max(candidates,key=lambda item:item[0])
   result.update(mount_id=a[0],mount_device=a[2],mount_point=a[4],filesystem_type=b[0],mount_source=b[1])
 return result
def snapshot(target, expected_resolved, private_dir, max_bytes=65536):
 """One exact read by this process; writes only a fresh private evidence directory."""
 target, expected_resolved, folder = Path(target), Path(expected_resolved), Path(private_dir)
 demand(target.resolve(strict=True) == expected_resolved, "TARGET_RESOLUTION_CHANGED")
 started, stamp = time.monotonic_ns(), utc()
 descriptor = os.open(str(expected_resolved), os.O_RDONLY | getattr(os,"O_NOFOLLOW",0))
 with os.fdopen(descriptor,"rb") as stream:
  before=os.fstat(stream.fileno()); demand(stat.S_ISREG(before.st_mode),"TARGET_NOT_REGULAR")
  demand(before.st_size <= max_bytes,"CONFIG_SIZE_LIMIT")
  raw=stream.read(max_bytes+1); after=os.fstat(stream.fileno())
 demand(len(raw)<=max_bytes,"CONFIG_SIZE_LIMIT")
 named=expected_resolved.stat()
 stable=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 demand(stable(before)==stable(after)==stable(named),"RUNTIME_INPUT_CHANGED_DURING_READ")
 demand(target.resolve(strict=True)==expected_resolved,"TARGET_RESOLUTION_CHANGED")
 settings=semantic_settings(raw)
 folder.mkdir(mode=0o700)
 raw_path=folder/"runtime_config.raw.txt";private_write(raw_path,raw)
 write_json(folder/"semantic_settings.private.json",settings)
 result={"schema_version":1,"evidence_class":"ACTUAL_RAW_RUNTIME_OBSERVATION",
         "status":"PASS_BOUNDED_READ_ONLY_SNAPSHOT","observation_started_utc":stamp,"observation_finished_utc":utc(),
         "duration_ns":time.monotonic_ns()-started,"pid":os.getpid(),"parent_pid":os.getppid(),
         "path":str(target),"resolved_path":str(expected_resolved),"raw_identity":identity(raw),
         "file_metadata_before":stat_identity(before),"file_metadata_after":stat_identity(after),
         "filesystem_identity":filesystem_identity(expected_resolved),
         "semantic_sha256":json_hash(settings),"effective_settings_allowlisted":public_settings(settings),
         "unpublished_other_setting_count":len(set(settings)-set(PUBLIC_SETTINGS)),
         "private_raw_copy":str(raw_path),"private_raw_copy_sha256":sha(raw),
         "installed_file_write_performed":False,"cold_cache_independence_claimed":False,**COUNTERS}
 write_json(folder/"snapshot_metadata.json",result)
 return result
def summarize_snapshots(rows):
 demand(len(rows)==3,"THREE_SNAPSHOTS_REQUIRED")
 demand(len({row["pid"] for row in rows})==3,"SNAPSHOT_PROCESSES_NOT_DISTINCT")
 demand(all(row["status"]=="PASS_BOUNDED_READ_ONLY_SNAPSHOT" for row in rows),"FAILED_RUNTIME_SNAPSHOT")
 raw_stable=len({(row["raw_identity"]["bytes"],row["raw_identity"]["sha256"]) for row in rows})==1
 fields=("device","inode","bytes","mtime_ns","ctime_ns")
 file_stable=len({tuple(row["file_metadata_after"][key] for key in fields)+(row["resolved_path"],) for row in rows})==1
 return {"schema_version":1,"evidence_class":"ACTUAL_RAW_RUNTIME_OBSERVATION",
         "status":"THREE_SEQUENTIAL_SNAPSHOTS_STABLE_WITH_LIMITS" if raw_stable and file_stable else "BLOCKED_PHASE12_RUNTIME_DRIFT",
         "raw_bytes_stable":raw_stable,"file_identity_stable":file_stable,"snapshots":rows,
         "current_raw_identity":rows[-1]["raw_identity"],"current_semantic_sha256":rows[-1]["semantic_sha256"],
         "distinct_snapshot_pids":[row["pid"] for row in rows],
         "observation_scope":"Three sequential same-host observations; shared caches; not independent cold-cache tests or future immutability",
         "writer_identified":False,"actual_writer":"UNKNOWN","old_phase11_raw_gate":"BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT",
         "new_baseline_approved":False,**COUNTERS}
def inverse_padding(raw, rounds):
 """Recover candidate bytes in memory; accepted only by an exact known historical SHA."""
 lines=raw.splitlines(keepends=True);out=[];index=0;found=set()
 while index<len(lines):
  line=lines[index]; key=next((key for key in KEYS if line.startswith(key.encode()+b" =")),None)
  if key:
   demand(key not in found,"DUPLICATE_SERIALIZER_KEY");found.add(key)
   if rounds:
    demand(line.endswith(b" "*rounds+b"\n"),"INVERSE_PADDING_NOT_AVAILABLE")
    out.append(line[:-rounds-1]+b"\n")
   else:out.append(line)
   index+=1
   for _ in range(rounds):
    demand(index<len(lines) and lines[index]==b" \n","INVERSE_BLANK_PADDING_NOT_AVAILABLE")
    index+=1
  else:out.append(line);index+=1
 demand(found==set(KEYS),"THREE_SERIALIZER_KEYS_REQUIRED")
 return b"".join(out)
def serializer_round(raw):
 """Independent string algebra from the inspected serializer, without importing its code."""
 settings=semantic_settings(raw);out=""
 for line in raw.decode().splitlines(keepends=True):
  if "=" not in line:out+=line;continue
  data,value=line.split("=",1);key=data.strip().lstrip("#").strip()
  if key not in KEYS:out+=line;continue
  comment=value.split("#",1)[1] if "#" in value else ""
  out+="%s = %s # %s \n"%(key,settings[key],comment)
 return out.encode()
def serializer_source_identity(path):
 raw=Path(path).read_bytes();demand(len(raw)<=1024*1024,"SERIALIZER_SOURCE_SIZE_LIMIT")
 text=raw.decode()
 anchors=["for line in open(basefile):","value, comment = value.split('#',1)",
          "new_line = '%s = %s # %s \\n' % (key, value, comment)","writer = open(filepath,'w')"]
 witnesses=[]
 for anchor in anchors:
  matches=[{"line":index,"text":line.strip()} for index,line in enumerate(text.splitlines(),1) if anchor in line]
  demand(matches,"SERIALIZER_SOURCE_WITNESS_MISSING");witnesses+=matches
 return {"evidence_class":"HISTORICAL_SOURCE_AUDIT","path":str(path),"resolved_path":str(Path(path).resolve()),
         **identity(raw),"witnesses":witnesses,"imported_or_executed":False}
def exact_diff_and_reproduction(current, serializer, private_dir):
 private_dir=Path(private_dir);recovered={};diffs=[];chain=[]
 for rounds in range(65):
  try:candidate=inverse_padding(current,rounds)
  except ValueError:continue
  for name,expected in HISTORICAL.items():
   if identity(candidate)==expected:
    recovered[name]=candidate
    private_write(private_dir/("reconstructed_"+name+".raw.txt"),candidate)
    oldsettings,newsettings=semantic_settings(candidate),semantic_settings(current)
    operations=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,candidate,current,autojunk=False).get_opcodes():
     if tag=="equal":continue
     operations.append({"operation":tag,"old_range":[i1,i2],"new_range":[j1,j2],
                        "old_chunk_sha256":sha(candidate[i1:i2]),"new_chunk_sha256":sha(current[j1:j2]),
                        "old_bytes":i2-i1,"new_bytes":j2-j1,
                        "changed_bytes_whitespace_only":all(chr(value).isspace() for value in candidate[i1:i2]+current[j1:j2])})
    private_write(private_dir/("diff_"+name+"_to_current.private.txt"),
                  "".join(difflib.unified_diff(candidate.decode().splitlines(keepends=True),current.decode().splitlines(keepends=True))).encode())
    diffs.append({"historical_name":name,"historical_identity":expected,"current_identity":identity(current),
                  "historical_payload_evidence":"EXACT_KNOWN_HASH_RECONSTRUCTION_NOT_A_LIVE_OR_BACKUP_READ",
                  "inverse_rounds_per_key":rounds,"raw_equal":candidate==current,"semantic_equal":oldsettings==newsettings,
                  "old_semantic_sha256":json_hash(oldsettings),"current_semantic_sha256":json_hash(newsettings),
                  "semantic_changed_setting_count":sum(oldsettings.get(key)!=newsettings.get(key) for key in set(oldsettings)|set(newsettings)),
                  "raw_operations":operations})
 if "A" in recovered:
  replay=recovered["A"]
  for round_index in range(65):
   matches=[name for name,expected in HISTORICAL.items() if identity(replay)==expected]
   chain.append({"rounds_all_three_keys":round_index,**identity(replay),"matches_known_historical":matches,"matches_current":replay==current})
   if replay==current:break
   replay=serializer_round(replay)
 reproduced=bool(chain and chain[-1]["matches_current"] and all(name in recovered for name in HISTORICAL))
 result={"schema_version":1,"evidence_class":"INDEPENDENT_ALGEBRA_METHOD_TEST","historical_identities":HISTORICAL,
         "current_identity":identity(current),"historical_comparisons":diffs,"serialization_chain":chain,
         "serializer_source_identity":serializer,
         "serializer_behavior":"SERIALIZER_BEHAVIOR_REPRODUCED" if reproduced else "NOT_REPRODUCED_FOR_ALL_HISTORICAL_IDENTITIES",
         "actual_writer":"UNKNOWN","actual_writer_identified":False,"private_config_bytes_published":False,
         "limits":"An exact transformation match does not identify its historical caller",**COUNTERS}
 write_json(private_dir/"runtime_exact_diff.private.json",result)
 return result
def task_record_summary(paths):
 records=[]
 for path in paths:
  path=Path(path);raw=path.read_bytes();demand(len(raw)<=256*1024,"TASK_RECORD_SIZE_LIMIT")
  data=json.loads(raw)
  records.append({"path":str(path),**identity(raw),
                  "label":data.get("label"),"exit_code":data.get("exit_code"),
                  "wall_seconds":data.get("wall_seconds"),"cpu_seconds":data.get("cpu_seconds"),
                  "direct_writer_attribution_from_summary":"NOT_ESTABLISHED"})
 return records
def propose_baseline(summary,policy,private_copy):
 validate_policy(policy)
 stable=summary["raw_bytes_stable"] and summary["file_identity_stable"]
 return {"schema_version":1,"evidence_class":"FUTURE_UNEXECUTED_PROPOSAL","version":policy["proposal_version"],
         "status":"PROPOSED_UNAPPROVED" if stable else "BLOCKED_PHASE12_RUNTIME_DRIFT",
         "new_baseline_approved":False,"physical_execution_authorized":False,"dispatcher":None,
         "old_raw_identities":HISTORICAL,"new_observed_raw_identity":summary["current_raw_identity"],
         "versioned_private_byte_copy":str(private_copy) if private_copy is not None else None,
         "private_copy_sha256":summary["current_raw_identity"]["sha256"] if stable else None,
         "observed_effective_settings_allowlisted":summary["snapshots"][-1]["effective_settings_allowlisted"],
         "observed_full_semantic_sha256":summary["current_semantic_sha256"],
         "reason_for_proposed_rebinding":"Preserve original Phase11 hash failure while proposing an independently reviewed current exact-byte binding",
         "historical_writer":"UNKNOWN","old_phase11_raw_gate":"BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT",
         "independent_review_requirements":policy["independent_review_requirements"],
         "approval_scope":"No current or future physical authorization; no modification of historical receipt identities"}

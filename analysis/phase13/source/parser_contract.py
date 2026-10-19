"""Future exact-source parser authorization: preparation never imports MG5.
Approval is a user decision, not something this mechanical gate can authenticate.
"""
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
BASE="d95ca4c98352f460af955a1bad5372f63cfcee4a"
COMMANDS=["import model sm","define p4 = g u u~ d d~ s s~ c c~","generate p4 p4 > b b~ a a QCD=2 QED=2","quit"]
LIMITS={"cpu_seconds":2,"wall_seconds":3,"address_space_bytes":536870912,"output_file_bytes":65536}
FULL_LAUNCH_ENVELOPE_IMPLEMENTED=False # No current source path is authorized to dispatch MG5.
DELIVERY={"metadata/phase13_source_manifest.json","metadata/phase13_quality_gates.json","reports/phase13_final_report.md"}
SCHEMA={"schema_version":1,"evidence_class":"FUTURE_UNEXECUTED_PROPOSAL","base_revision":BASE,
 "scope":"SYMBOLIC_MODEL_ALIAS_PROCESS_AND_DIAGRAM_ENUMERATION_ONLY","commands":COMMANDS,
 "diagram_enumeration":True,"code_generation":False,"numerical_ME":False,"integration":False,
 "event_production":False,"output_process_build":False,"launch":False,"Pythia":False,"Delphes":False,
 "StageA":False,"check_process":False,"limits":LIMITS,"concurrent_jobs":1,"workers":1,
 "filesystem":"READ_ONLY_CHILD_EXCEPT_PREOPENED_STDOUT_STDERR","child_processes":0,"network":False,
 "PDF_dependency":"NOT_REQUIRED_FOR_SYMBOLIC_PARSER; NUMERICAL_MG5_BINDING_UNVERIFIED",
 "configuration_activation":"ONLY_PINNED_PRIVATE_MG5_PATH_PROPOSAL_AFTER_NEW_APPROVAL",
 "human_confirmation":"NEW_EXPLICIT_USER_APPROVAL_AND_EXACT_TERMINAL_CHALLENGE; NO_OLD_AUTHORIZATION_REUSE",
 "parser_approved":False,"parser_executed":False,
 "forbidden_commands":["check","output","launch","install","save","set","shell","!","import command"],
 "receipt_fields":["source_revision","package_sha256","approval_sha256","runtime_before","runtime_after","exit_code","resource_stop","wall_seconds","stdout_sha256","stderr_sha256","parser_completed","new_ME_calls","new_integrals","new_hard_events","new_pythia_events","new_delphes_events"],
 "stop_conditions":["missing_or_stale_approval","source_config_runtime_mismatch","unexpected_write_or_child_or_network","resource_limit","native_guard_unavailable","nonzero_exit","post_run_identity_drift"],
 "startup_compatibility":"UNVERIFIED; IMPLICIT_WRITE_OR_SHORT_LIMIT_MUST_STOP",
 "full_launch_envelope_verification_required":True}
def require(value,reason):
 if not value:raise ValueError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return sha(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode())
def read_json(path):
 p=Path(path);require(p.is_file() and not p.is_symlink() and p.stat().st_size<=2*1024*1024,"BOUNDED_REGULAR_JSON_REQUIRED")
 return json.loads(p.read_text())
def identity(path):
 p=Path(path);require(p.is_file() and not p.is_symlink(),"REGULAR_IDENTITY_INPUT_REQUIRED")
 raw=p.read_bytes();return {"bytes":len(raw),"sha256":sha(raw)}
def no_symlink(path):
 p=Path(path);require(p.is_absolute() and ".." not in p.parts,"ABSOLUTE_NO_TRAVERSAL_REQUIRED")
 require(not any(a.is_symlink() for a in (p,*p.parents)),"SYMLINK_PATH_FORBIDDEN")
 return p
def fresh_output(path,root):
 p=no_symlink(path);base=no_symlink(root).resolve(strict=True)
 require(p.parent.is_dir() and not p.exists() and p.resolve().is_relative_to(base) and p.resolve()!=base,"FRESH_TASK_LOCAL_OUTPUT_REQUIRED")
 return p

def git(repo,*args):
 env=dict(os.environ,GIT_OPTIONAL_LOCKS="0")
 return subprocess.check_output(["git","-C",str(repo),*args],env=env,stderr=subprocess.PIPE)
def validate_contract(value):require(value==SCHEMA,"PARSER_SCOPE_OR_LIMIT_DRIFT");return value

def source_inputs(repo):
 names=git(repo,"ls-files","-z","analysis/phase13/source","analysis/phase13/scripts","analysis/phase13/config","analysis/phase13/tests","analysis/phase13/README_ZH_TW.md",".github/workflows/phase13-source.yml","metadata/phase13_parser_review_contract.json","reports/phase13a_runtime_isolation.md","reports/phase13b_pdf_backend_binding.md","reports/phase13c_alpha_s_semantics.md","reports/phase13d_photon_ir_and_model.md","reports/phase13e_parser_execution_contract.md").decode().split("\0")
 return {name:identity(Path(repo)/name) for name in sorted(filter(None,names))}
def verify_checkout(repo,revision,inputs):
 require(bool(re.fullmatch("[0-9a-f]{40}",revision)),"FULL_SOURCE_REVISION_REQUIRED")
 head=git(repo,"rev-parse","HEAD").decode().strip()
 git(repo,"merge-base","--is-ancestor",revision,head)
 changed=set(filter(None,git(repo,"diff","--name-only",revision,head).decode().splitlines()))
 require(changed<=DELIVERY,"EXECUTION_HEAD_CONTAINS_NON_DELIVERY_CHANGES")
 require(not git(repo,"diff","--name-only","HEAD").strip() and not git(repo,"diff","--cached","--name-only").strip(),"TRACKED_WORKTREE_DIRTY")
 require(inputs and source_inputs(repo)==inputs,"EXACT_SOURCE_FILE_CLOSURE_MISMATCH")
 for name,expected in inputs.items():require({"bytes":len(raw:=git(repo,"show",revision+":"+name)),"sha256":sha(raw)}==expected,"REVIEWED_COMMIT_SOURCE_MISMATCH")
 return {"reviewed_source_revision":revision,"observed_HEAD":head,"only_explicit_delivery_paths_differ":True,"exact_reviewed_source_bytes":True}
def runtime_check(package):
 from runtime_layout import inspect_tree
 root=no_symlink(package["runtime_root"]).resolve(strict=True)
 limits={"max_single_file_bytes":64*1024**2,"max_entries":10000,"max_total_regular_bytes":512*1024**2}
 manifest=inspect_tree(root,limits)
 require(manifest["content_manifest_sha256"]==package["runtime_manifest_sha256"],"RUNTIME_TREE_MISMATCH")
 require(identity(root/"input/mg5_configuration.txt")==package["raw_configuration_identity"],"RAW_CONFIGURATION_MISMATCH")
 proposal=no_symlink(package["configuration_proposal_path"])
 require(identity(proposal)==package["configuration_proposal_identity"],"CONFIGURATION_PROPOSAL_MISMATCH")
 require(str(root)!=package["original_installed_runtime"],"ORIGINAL_RUNTIME_DISPATCH_FORBIDDEN")
 return manifest

def prepare(repo,runtime_receipt,resource_receipt,output,revision,future_output):
 repo=no_symlink(repo);output=no_symlink(output)
 require(not output.exists() and output.parent.is_dir(),"FRESH_PACKAGE_REQUIRED")
 contract=validate_contract(read_json(repo/"metadata/phase13_parser_review_contract.json"))
 runtime=read_json(runtime_receipt);resources=read_json(resource_receipt)
 require(runtime.get("status")=="EXACT_COPY_PREPARED_NOT_EXECUTED" and runtime.get("new_MG5_processes")==0,"UNEXECUTED_EXACT_RUNTIME_REQUIRED")
 require(resources.get("status")=="PASS_NATIVE_RESOURCE_FIXTURES" and resources.get("enforcement_verified") is True,"RESOURCE_ENFORCEMENT_NOT_PROVEN")
 require(resources.get("limits")==LIMITS,"RESOURCE_FIXTURE_LIMITS_MISMATCH")
 require(type(resources.get("full_launch_envelope_verified")) is bool,"EXPLICIT_FULL_ENVELOPE_STATUS_REQUIRED")
 proposal=runtime["configuration_proposal"]
 require(proposal["status"]=="PROPOSED_UNAPPROVED_UNACTIVATED" and proposal["activated"] is False,"UNAPPROVED_PROPOSAL_MUST_REMAIN_UNACTIVATED")
 future=fresh_output(future_output,Path(runtime_receipt).resolve().parents[1])
 inputs=source_inputs(repo);verify_checkout(repo,revision,inputs)
 package={"schema_version":1,"evidence_class":"FUTURE_UNEXECUTED_PROPOSAL","source_revision":revision,"source_repository":str(repo),"source_inputs":inputs,
 "contract":contract,"contract_sha256":canonical(contract),"runtime_root":runtime["isolated_runtime_root"],"original_installed_runtime":runtime["source_root"],
 "runtime_manifest_sha256":runtime["copied_manifest_sha256"],"raw_configuration_identity":runtime["copied_raw_config_identity"],
 "configuration_proposal_path":proposal["path"],"configuration_proposal_identity":proposal["proposed_raw_identity"],
 "runtime_receipt":{"path":str(runtime_receipt),**identity(runtime_receipt)},"resource_receipt":{"path":str(resource_receipt),**identity(resource_receipt)},
 "future_output":str(future),"fresh_environment":runtime["fresh_environment_proposal"],"python":{"path":str(Path(sys.executable).resolve()),**identity(Path(sys.executable).resolve())},
 "human_approval_status":"NOT_AUTHORIZED","execution_eligible":bool(FULL_LAUNCH_ENVELOPE_IMPLEMENTED and resources["full_launch_envelope_verified"]),"resource_blockers":resources.get("full_launch_blockers",[])+([] if FULL_LAUNCH_ENVELOPE_IMPLEMENTED else ["CURRENT_SOURCE_FULL_LAUNCH_ENVELOPE_NOT_IMPLEMENTED"]),"package_status":"READY_FOR_SEPARATE_APPROVAL" if FULL_LAUNCH_ENVELOPE_IMPLEMENTED and resources["full_launch_envelope_verified"] else "BLOCKED_PHASE13_RESOURCE_ENFORCEMENT","parser_executed":False,"new_ME_calls":0,"new_integrals":0,"new_hard_events":0,"new_pythia_events":0,"new_delphes_events":0,
 "startup_success":"UNVERIFIED_NOT_EXECUTED","new_physical_production_authorized":False,
 "model_restriction":{"model":"sm","restriction":"default","MB_GeV":4.7,"MC_GeV":0.0,"evidence_level":"STATIC_SOURCE_ONLY_NOT_MODEL_IMPORT","restrict_default":identity(Path(runtime["isolated_runtime_root"])/"models/sm/restrict_default.dat"),"parameters":identity(Path(runtime["isolated_runtime_root"])/"models/sm/parameters.py")},
 "process_text":COMMANDS[:3],"PDF_dependency":{"classification":"NOT_REQUIRED_FOR_SYMBOLIC_PARSER","numeric_MG5_binding":"UNVERIFIED_NOT_EXECUTED","set":"NNPDF30_lo_as_0130_nf_4","member":0,"LHAPDF_ID":263400,"DataVersion":2,"info_sha256":"85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162","member_sha256":"e3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e"}}
 runtime_check(package)
 with output.open("x") as stream:json.dump(package,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write("\n")
 return package

def authorization(package_path,approval_path,terminal_input=None,is_tty=None):
 # Missing human authorization is rejected before any checkout, activation, mkdir or child.
 require(approval_path is not None and Path(approval_path).is_file(),"MISSING_NEW_EXPLICIT_USER_APPROVAL")
 package=read_json(package_path)
 require(FULL_LAUNCH_ENVELOPE_IMPLEMENTED and package.get("execution_eligible") is True and package.get("package_status")=="READY_FOR_SEPARATE_APPROVAL","FULL_LAUNCH_ENVELOPE_NOT_PROVEN; NO_DISPATCH")
 approve=read_json(approval_path)
 require(package.get("human_approval_status")=="NOT_AUTHORIZED" and package.get("parser_executed") is False,"PREEXECUTION_PACKAGE_REQUIRED")
 validate_contract(package["contract"])
 expected={"authorization_type":"EXPLICIT_USER_PARSER_APPROVAL","package_sha256":identity(package_path)["sha256"],"source_revision":package["source_revision"],"contract_sha256":package["contract_sha256"],"future_output":package["future_output"],"one_attempt":True}
 require(approve==expected,"NEW_EXACT_SCOPE_APPROVAL_MISMATCH")
 require((sys.stdin.isatty() if is_tty is None else is_tty),"HUMAN_TERMINAL_REQUIRED")
 challenge="AUTHORIZE SYMBOLIC_PARSER "+identity(package_path)["sha256"]
 print("NEW EXPLICIT USER AUTHORIZATION REQUIRED; EXACT SCOPE:",flush=True)
 print(json.dumps({"source":package["source_revision"],"commands":COMMANDS,"limits":LIMITS,"output":package["future_output"],"config_activation":package["configuration_proposal_identity"]},indent=2),flush=True)
 print(challenge,flush=True)
 line=(input("> ") if terminal_input is None else terminal_input())
 require(line==challenge,"EXACT_HUMAN_SCOPE_CONFIRMATION_REQUIRED")
 return package,approve

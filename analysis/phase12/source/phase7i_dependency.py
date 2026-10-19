"""Static Phase7I Route-A dependency review. Never import historical runtime code."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import subprocess

REVISION='b80e16775bf141e45f4048c7197a8a99befaed51'
TARGET=Path('/home/btu/opt/mg5amcnlo/input/mg5_configuration.txt')
RUNTIME='simulation/hh_signal/final_closure/integration_runtime/'
CLOSURE='simulation/hh_signal/final_closure/'
LOCK='simulation/hh_signal/config_lock/configuration_lock.json'
BUILDER='metadata/phase7i_builder_review_contract.json'
MODEL='metadata/phase7a_model_manifest.json'
TOOLS='metadata/phase7_final_route_a_toolchain.json'
SOURCE_FILES=[RUNTIME+n for n in ['route_a.py','build.py','build_plan.py','run.py','contract.py','approval.py','validate.py','containment.py','git_precheck.py','build_process.py']]+[
 CLOSURE+'guard_correction/review_contract.py',CLOSURE+'src/plans.py',CLOSURE+'src/contracts.py',
 'simulation/hh_signal/config_lock/contract.py',LOCK,'simulation/hh_signal/campaign/common.py',MODEL,BUILDER,
 'metadata/phase7_final_route_a_build_contract.json',TOOLS,'metadata/phase7i_guard_correction_status.json',
 CLOSURE+'config/physics_contract.json','simulation/hh_signal/semantics_recovery/src/anonymous_io.c',
 'simulation/hh_signal/semantics_recovery/src/io_and_rng.f90',CLOSURE+'guard_correction/native_checks_corrected.f']
WITNESSES={
 'full_repository_binding':(RUNTIME+'route_a.py',['def full_sources():',"REPO/'simulation/hh_signal',REPO/'simulation/mg5/scripts'","p.suffix in ['.py','.f','.f90','.c','.sh','.inc','.dat','.patch']"]),
 'frozen_binding':(RUNTIME+'route_a.py',["lock()['frozen_runtime_sources']+lock()['runtime_build_auxiliary']","'cards':build_contract()['frozen_card_identities']"]),
 'toolchain_binding':(RUNTIME+'route_a.py',["m['groups'].items()","len(rows)==m['file_count']==8166","sha(root/item['path'])==item['sha256']"]),
 'builder_dependencies':(CLOSURE+'guard_correction/review_contract.py',["contract['frozen_process_dependencies']","p=Path(process)/row['path']","sha(p)==row['sha256']"]),
 'build_configuration_read':(RUNTIME+'build.py',["cfg=read_json(REPO/'.local/mg5_installation.json')","mg_environment(cfg)","native=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'","verify_model_sources(cfg['mg5_path']","compiler=Path(cfg['toolchain_prefix'])"]),
 'frozen_copy_and_compile':(RUNTIME+'build.py',["target.write_bytes((native/r['path']).read_bytes())","jobs=plan(process,folder,compiler)","invoke(argv,sub,env)","supervise([exe],work"]),
 'explicit_compile_plan':(RUNTIME+'build_plan.py',["flags=[compiler,'-O0'","'-c',p,'-o',obj","'-L'+str(process/'lib')"]),
 'model_verification':(CLOSURE+'src/plans.py',['def verify_model_sources(root,rows):',"sha(Path(root)/name)==value"]),
 'environment_construction':('simulation/hh_signal/campaign/common.py',['def mg_environment(config):',"p=Path(config['toolchain_prefix'])","env['PATH']","env['LD_LIBRARY_PATH']"]),
 'receipt_runtime_validation':(RUNTIME+'run.py',['def check_build(root,revision=None',"validate_receipt(review,root,revision,full_sources(),check_linkage=True)"]),
 'native_preflight_fields':(RUNTIME+'validate.py',['def validate_preflight(r,seed):',"one(records,'HI_PDF')","one(records,'HI_ALPHA')","one(records,'HI_SCALE')"]),
 'legacy_approval_consumed':(RUNTIME+'approval.py',['CONSUMED=','class HumanReview'])}

def digest_bytes(raw):return hashlib.sha256(raw).hexdigest()
def canonical_sha(obj):return digest_bytes(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def git_read(root,*args):
    # Fixed read-only Git queries only. Never run historical Python, MG5 or native tools.
    return subprocess.check_output(['git','-C',str(root),*args],timeout=30)
def require_revision(root):
    head=git_read(root,'rev-parse','HEAD').decode().strip()
    if head!=REVISION:raise ValueError('EXACT_PHASE7I_REVISION_REQUIRED')
    return head

def validate_inventory(rows):
    if not isinstance(rows,list) or not rows:raise ValueError('NONEMPTY_EXPLICIT_INVENTORY_REQUIRED')
    seen=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError('INVENTORY_ROW_OBJECT')
        name=row.get('path');p=PurePosixPath(name) if isinstance(name,str) else None
        if p is None or not p.parts or p.is_absolute() or '..' in p.parts or name!=p.as_posix():raise ValueError('UNSAFE_INVENTORY_PATH')
        if name in seen:raise ValueError('DUPLICATE_INVENTORY_PATH')
        seen.add(name)
        if not isinstance(row.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',row['sha256']):raise ValueError('INVALID_INVENTORY_HASH')
    return rows

def inventory_scope(name,rows,base,target):
    validate_inventory(rows)
    target=Path(target).resolve()
    matches=[r for r in rows if (Path(base)/r['path']).resolve()==target]
    return {'name':name,'member_count':len(rows),'declared_path_base':str(base),'canonical_members_sha256':canonical_sha(rows),
            'target_matches':matches,'classification':'DIRECT_DEPENDENCY' if matches else 'NOT_BOUND_BY_REVIEWED_CONTRACT',
            'payloads_rehashed':False,'scope':'Complete declared path/hash descriptor membership; not a fresh build or payload-validation certificate.'}

def classify_dependency(scopes,*,positive_callchain_review,explicit_indirect_read=False):
    if not scopes:raise ValueError('DEPENDENCY_SCOPES_REQUIRED')
    if any(s['target_matches'] for s in scopes):return 'DIRECT_DEPENDENCY'
    if explicit_indirect_read:return 'INDIRECT_DEPENDENCY'
    return 'NOT_BOUND_BY_REVIEWED_CONTRACT' if positive_callchain_review else 'UNKNOWN'

def function_record(raw,name):
    text=raw.decode();tree=ast.parse(text)
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(nodes)!=1:raise ValueError('EXACT_FUNCTION_WITNESS_REQUIRED:'+name)
    n=nodes[0]
    return {'function':name,'line_start':n.lineno,'line_end':n.end_lineno,
            'calls':sorted(set(ast.unparse(v.func) for v in ast.walk(n) if isinstance(v,ast.Call))),
            'literal_mg5_configuration_target_present':any(isinstance(v,ast.Constant) and isinstance(v.value,str) and 'mg5_configuration.txt' in v.value for v in ast.walk(n))}

def source_records(root):
    records=[];raws={}
    for rel in SOURCE_FILES:
        raw=(root/rel).read_bytes();blob=git_read(root,'cat-file','blob',REVISION+':'+rel)
        if raw!=blob:raise ValueError('HISTORICAL_SOURCE_DIFFERS_FROM_EXACT_GIT_BLOB:'+rel)
        raws[rel]=raw
        records.append({'path':rel,'bytes':len(raw),'sha256':digest_bytes(raw),'matches_exact_git_revision':True})
    return records,raws

def witnesses(raws):
    out=[]
    for identity,(rel,anchors) in WITNESSES.items():
        lines=raws[rel].decode().splitlines();found=[]
        for anchor in anchors:
            hits=[{'line':i+1,'text':line.strip()} for i,line in enumerate(lines) if anchor in line]
            if not hits:raise ValueError('SOURCE_WITNESS_MISSING:'+identity+':'+anchor)
            found.append({'anchor':anchor,'matches':hits})
        out.append({'id':identity,'path':rel,'sha256':digest_bytes(raws[rel]),'witnesses':found})
    return out

def full_repository_rows(root,builder):
    paths=set()
    for base in [root/'simulation/hh_signal',root/'simulation/mg5/scripts']:
        paths.update(p for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.f','.f90','.c','.sh','.inc','.dat','.patch'])
    paths.update(p for p in (root/'simulation/hh_signal').rglob('*.json') if 'evidence' not in p.parts)
    paths.update(root/r['path'] for r in builder['frozen_card_identities'])
    paths.update(root/r for r in [MODEL,BUILDER,'metadata/phase7i_guard_correction_status.json','metadata/phase7_final_route_a_build_contract.json',TOOLS])
    return [{'path':p.relative_to(root).as_posix(),'sha256':digest_bytes(p.read_bytes())} for p in sorted(paths,key=lambda p:p.relative_to(root).as_posix())]

def audit(root):
    root=Path(root).resolve();head=require_revision(root);before,raws=source_records(root);proof=witnesses(raws)
    lock=json.loads(raws[LOCK]);builder=json.loads(raws[BUILDER]);model=json.loads(raws[MODEL]);tools=json.loads(raws[TOOLS])
    cfg_path=root/'.local/mg5_installation.json'
    cfg_raw=cfg_path.read_bytes();cfg=json.loads(cfg_raw)
    process=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'
    toolrows=sorted([{'path':(PurePosixPath(parent)/name).as_posix(),'sha256':h} for parent,items in tools['groups'].items() for name,h in items],key=lambda x:x['path'])
    validate_inventory(toolrows)
    if len(toolrows)!=8166 or tools['file_count']!=8166 or canonical_sha(toolrows)!=tools['complete_file_list_sha256']:raise ValueError('TOOLCHAIN_DESCRIPTOR_IDENTITY_MISMATCH')
    repo_rows=full_repository_rows(root,builder)
    scopes=[inventory_scope('frozen_runtime_sources',lock['frozen_runtime_sources'],process,TARGET),
      inventory_scope('runtime_build_auxiliary',lock['runtime_build_auxiliary'],process,TARGET),
      inventory_scope('frozen_process_dependencies',builder['frozen_process_dependencies'],process,TARGET),
      inventory_scope('frozen_card_identities',builder['frozen_card_identities'],root,TARGET),
      inventory_scope('installed_model_files',[{'path':p,'sha256':h} for p,h in model['installed_model_files'].items()],Path(cfg['mg5_path']),TARGET),
      inventory_scope('toolchain_complete_inventory',toolrows,Path(cfg['toolchain_prefix']),TARGET),
      inventory_scope('route_a_full_repository_source_binding',repo_rows,root,TARGET)]
    expected={'frozen_runtime_sources':682,'runtime_build_auxiliary':149,'frozen_process_dependencies':71,'frozen_card_identities':24,'installed_model_files':28,'toolchain_complete_inventory':8166}
    if any(s['member_count']!=expected[s['name']] for s in scopes if s['name'] in expected):raise ValueError('EXACT_CONTRACT_CARDINALITY_MISMATCH')
    names=[(RUNTIME+'build.py','prepare'),(RUNTIME+'route_a.py','full_sources'),(RUNTIME+'route_a.py','frozen_inputs'),(RUNTIME+'route_a.py','toolchain_rows'),(RUNTIME+'route_a.py','validate_receipt'),(RUNTIME+'build_plan.py','plan'),(RUNTIME+'run.py','check_build'),('simulation/hh_signal/campaign/common.py','mg_environment'),(CLOSURE+'src/plans.py','verify_model_sources'),(RUNTIME+'validate.py','validate_preflight')]
    functions=[{'path':rel,**function_record(raws[rel],name)} for rel,name in names]
    if any(f['literal_mg5_configuration_target_present'] for f in functions):raise ValueError('UNREVIEWED_TARGET_READ_IN_DECLARED_CALLCHAIN')
    after,unused=source_records(root)
    if before!=after or require_revision(root)!=head or cfg_path.read_bytes()!=cfg_raw:raise ValueError('SOURCE_OR_SELECTOR_CHANGED_DURING_STATIC_AUDIT')
    status=classify_dependency(scopes,positive_callchain_review=True)
    return {'schema_version':1,'evidence_class':'HISTORICAL_SOURCE_AUDIT','scope':'EXACT_PHASE7I_ROUTE_A_STATIC_CONTRACT_AND_CALLCHAIN_REVIEW_ONLY',
      'status':status,'phase7i_source_revision':head,'target':{'path':str(TARGET),'resolved_path':str(TARGET.resolve()),'target_raw_bytes_read_by_this_audit':False},
      'inventory_scopes':scopes,'source_records':before,'source_witnesses':proof,'reviewed_function_call_sites':functions,
      'local_installation_selector':{'path':str(cfg_path),'bytes':len(cfg_raw),'sha256':digest_bytes(cfg_raw),'source_commit':cfg['source_commit'],'review_scope':'Distinct .local/mg5_installation.json selector is read by builder/runtime; installed input/mg5_configuration.txt is not this file. Raw selector not published.'},
      'positive_dataflow':['build.prepare reads distinct local installation selector and constructs environment via campaign.common.mg_environment.','build.prepare verifies explicit installed model files and copies frozen B100 process rows; does not regenerate a process.','build_plan.plan explicitly lists compiler arguments, Fortran/C files and frozen libraries; no MG5 interface invocation.','route_a.validate_receipt binds repo/cards/toolchain/copied files/executable/dependencies and validates saved native preflight protocol.','run.check_build delegates exact source/Git/receipt/linkage checks; native preflight checks parsed cards/PDF/alpha/masses/scales.'],
      'not_a_grep_absence_claim':True,'implicit_unreviewed_external_runtime_reads':'UNKNOWN','actual_current_build_or_runtime_validation':'NOT_EXECUTED',
      'phase11_drift_automatically_invalidates_phase7i':False,'phase7i_build_receipt_currently_validated':False,
      'historical_frozen_receipt_identity':'98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281',
      'legacy_BUILD_ONLY_authorization_reusable':False,'physical_restart_authorized':False,
      'source_descriptor_bytes_unchanged':True,'installed_payloads_rehashed':False,'old_sources_modified':False,
      'limits':['Contract membership and statically traced selected callchain only.','No compiler, loader, actual zero-ME preflight, prepare-review, HumanReview or Stage A executed.','External runtime/compiler implicit behaviour remains UNKNOWN; no current Phase7I PASS certificate.','Existing frozen process generation may have historical MG5 provenance; frozen bytes are not regenerated here.'],
      'new_MG5_parser_calls':0,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,'new_Route_A_builds':0,'new_Stage_A_runs':0}

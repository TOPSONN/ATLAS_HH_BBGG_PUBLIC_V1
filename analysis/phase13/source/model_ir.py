"""Exact-source model/photon-IR audit. Never imports or dispatches MG5."""
import ast
import hashlib
import json
import math
from pathlib import Path

PROCESS_COMMANDS = (
    'import model sm',
    'define p4 = g u u~ d d~ s s~ c c~',
    'generate p4 p4 > b b~ a a QCD=2 QED=2',
)
INACTIVE_PROCESS_TEXT = ('# Phase13：未授權執行的 process 審查文字。所有命令保持註解。\n'
                         '# generate 的未來 scope 包含 symbolic diagram enumeration；不含 code generation。\n'
                         + ''.join('# ' + line + '\n' for line in PROCESS_COMMANDS))
SOURCE_IDENTITIES = {
 'models/sm/restrict_default.dat': {'bytes':1437,'sha256':'cc9e735d3dea306b31dcf3ef179719fceeefb505406bd163308324dc9aebda53'},
 'models/sm/parameters.py': {'bytes':15693,'sha256':'2e4046c3566f1fb62fad92ffa705eef66a0124cc2a1cf4cc0d0ff2dc7f94c8fc'},
 'models/sm/particles.py': {'bytes':10444,'sha256':'5a18af7aadba847f6b70749dcd2a787f95f9075c4c8de4406b2138314defe414'},
 'models/sm/coupling_orders.py': {'bytes':443,'sha256':'c89fc6f38d118a50a1e562da8653a2ccc96a9e00be22696bf5fb771a4df313b4'},
 'models/import_ufo.py': {'bytes':127324,'sha256':'d030835ea14a700ab40c29e4e2fb73df4d7f4fd846cf4ba22db3589a14549a38'},
 'madgraph/interface/madgraph_interface.py': {'bytes':458046,'sha256':'be96f305974bfee0108089af04d12dac55fccbdcd7791787fc8976ce8f930bc3'},
 'Template/LO/SubProcesses/cuts.f': {'bytes':55278,'sha256':'c077cc390dc052a8526ddb187c98005e08bab7e5d999c8c879b66a1500b65c2c'},
 'Template/LO/SubProcesses/setcuts.f': {'bytes':35393,'sha256':'f0e3e5e3ad3f5599fa56aa7baef614112e383ee51701caa38d16c977185cab18'},
 'madgraph/various/banner.py': {'bytes':279713,'sha256':'9877e00f80da4ef8a23d6a11377238e5b31c91c346b2aa73307ab52f64d9cc2a'},
}
PROPOSED_CUT_VALUES = {'maxjetflavor':4,'ptgmin':20.0,'r0gamma':0.4,'xn':1.0,
 'epsgamma':1.0,'isoem':False,'pta':0.0,'draj':0.0,'drab':0.4,'draa':0.4,
 'mmaa':None,'ptb':None,'etab':None,'etaa':None}
UNRESOLVED_CONVENTIONS = ('ickkw','xqcut','kt_durham','dynamical_scale_choice',
                         'mu_R_definition','mu_F_definition')
WITNESSES = {
 'default_restriction_loader':('models/import_ufo.py',225,230),
 'massive_bottom_and_massless_charm':('models/sm/restrict_default.dat',16,19),
 'raw_UFO_charm_default':('models/sm/parameters.py',133,139),
 'raw_UFO_bottom_default':('models/sm/parameters.py',149,155),
 'flavour_cut_classification':('Template/LO/SubProcesses/setcuts.f',215,224),
 'photon_pt_minimum':('Template/LO/SubProcesses/setcuts.f',297,303),
 'draj_and_drab_categories':('Template/LO/SubProcesses/setcuts.f',350,357),
 'diphoton_invariant_mass':('Template/LO/SubProcesses/setcuts.f',391,394),
 'photon_isolation_gate':('Template/LO/SubProcesses/cuts.f',1088,1090),
 'frixione_hadronic_membership':('Template/LO/SubProcesses/cuts.f',1098,1106),
 'hadronic_profile_comparison':('Template/LO/SubProcesses/cuts.f',1156,1166),
 'electromagnetic_membership':('Template/LO/SubProcesses/cuts.f',1119,1134),
 'pseudorapidity_distance':('Template/LO/SubProcesses/cuts.f',1287,1296),
 'smooth_cone_profile':('Template/LO/SubProcesses/cuts.f',1341,1353),
 'isolation_run_card_normalization':('madgraph/various/banner.py',4244,4251),
 'amplitude_order_bounds':('madgraph/interface/madgraph_interface.py',4847,4855),
 'generate_symbolic_dispatch':('madgraph/interface/madgraph_interface.py',4711,4721),
 'tree_MultiProcess_enumeration':('madgraph/interface/madgraph_interface.py',3259,3277),
}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def raw_identity(raw):
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def validate_plan(c, inactive_text):
    require(c['schema_version']==1 and type(c['schema_version']) is int,'SCHEMA_VERSION')
    require(c['model']=='sm' and c['restriction']=='models/sm/restrict_default.dat','EXACT_DEFAULT_RESTRICTED_SM')
    require(c['restricted_masses_GeV']=={'MB':4.7,'MC':0.0},'EXACT_RESTRICTED_MB_MC')
    require(c['source_identities']==SOURCE_IDENTITIES,'REVIEWED_SOURCE_MANIFEST_REQUIRED')
    require(c['process_commands']==list(PROCESS_COMMANDS),'EXACT_THREE_COMMANDS_ONLY')
    require(inactive_text==INACTIVE_PROCESS_TEXT,'EXACT_INACTIVE_PROCESS_TEXT_REQUIRED')
    require(c['amplitude_order_interpretation']=='QCD<=2; QED<=2; NOT_VERIFIED_DIAGRAM_SET','ORDER_BOUNDS_NOT_EQUALITY')
    require(c['future_symbolic_diagram_enumeration_in_scope'] is True,'GENERATE_ENUMERATION_MUST_BE_EXPLICIT')
    require(all(c[key] is False for key in ['MG5_parser_executed','parser_authorized','code_generation_authorized','numerical_ME_authorized','physical_configuration_validated','ATLAS_detector_isolation_equivalence_claimed']),'NO_EXECUTION_OR_PHYSICAL_APPROVAL')
    require(set(c['candidate_generation_cuts'])==set(PROPOSED_CUT_VALUES),'EXPLICIT_CUT_FIELD_SET')
    for name, expected in PROPOSED_CUT_VALUES.items():
        row=c['candidate_generation_cuts'][name]
        require(type(row['value']) is type(expected) and row['value']==expected,'EXACT_PROPOSED_CUT_'+name)
        label='UNRESOLVED_BLOCKS_PHYSICAL_EVALUATION' if expected is None else 'PROPOSED_NOT_PHYSICALLY_VALIDATED'
        require(row['evidence_level']==label,'EXPLICIT_EVIDENCE_LEVEL_'+name)
        require(isinstance(row['rationale'],str) and bool(row['rationale'].strip()),'CUT_RATIONALE_'+name)
        require(isinstance(row['required_acceptance_evidence'],str) and bool(row['required_acceptance_evidence'].strip()),'CUT_ACCEPTANCE_REQUIREMENT_'+name)
    require(set(c['unresolved_generator_conventions'])==set(UNRESOLVED_CONVENTIONS),'EXPLICIT_MATCHING_SCALE_FIELDS')
    for name in UNRESOLVED_CONVENTIONS:
        row=c['unresolved_generator_conventions'][name]
        require(row['value'] is None and row['evidence_level']=='UNRESOLVED_BLOCKS_PHYSICAL_EVALUATION' and bool(row['required_acceptance_evidence'].strip()),'NO_UNREVIEWED_GENERATOR_DEFAULT_'+name)
    return True

def restriction_masses(text):
    block=None; values={}
    for line in text.splitlines():
        fields=line.split('#',1)[0].split()
        if not fields:continue
        if fields[0].lower()=='block':
            require(len(fields)>=2,'MALFORMED_BLOCK');block=fields[1].lower();continue
        if fields[0].lower()=='decay':block=None
        if block=='mass' and fields[0] in ('4','5'):
            require(len(fields)==2 and fields[0] not in values,'DUPLICATE_OR_MALFORMED_RESTRICTED_MASS')
            v=float(fields[1].replace('D','e').replace('d','e'))
            require(math.isfinite(v) and v>=0,'NONFINITE_OR_NEGATIVE_MASS');values[fields[0]]=v
    require(set(values)=={'4','5'},'MISSING_RESTRICTED_MB_MC')
    return {'MC':values['4'],'MB':values['5']}

def ast_parameter_defaults(text):
    found={}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='Parameter':
            names=[t.id for t in node.targets if isinstance(t,ast.Name)]
            for name in names:
                if name in ('MC','MB'):
                    require(name not in found,'DUPLICATE_UFO_PARAMETER')
                    kw={x.arg:x.value for x in node.value.keywords}
                    found[name]=ast.literal_eval(kw['value'])
    require(set(found)=={'MC','MB'},'MISSING_UFO_PARAMETER');return found

def ast_particle_mass_refs(text):
    found={}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='Particle':
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in ('b','c'):
                    require(target.id not in found,'DUPLICATE_UFO_PARTICLE')
                    m=next(k.value for k in node.value.keywords if k.arg=='mass')
                    require(isinstance(m,ast.Attribute) and isinstance(m.value,ast.Name) and m.value.id=='Param','EXPECTED_MASS_PARAMETER_REFERENCE')
                    found[target.id]=m.attr
    require(set(found)=={'b','c'},'MISSING_UFO_PARTICLE');return found

def cut_flavour_category(pdg, maxjetflavor):
    """Independent static reconstruction of inspected setcuts.f PDG branch, not Fortran execution."""
    require(type(pdg) is int and type(maxjetflavor) is int and 1<=maxjetflavor<=6,'INVALID_CLASSIFICATION_INPUT')
    apdg=abs(pdg)
    if apdg<=min(maxjetflavor,6) or apdg==21:return 'is_a_j'
    if maxjetflavor+1<=apdg<=5:return 'is_a_b'
    return 'neither'

def read_exact_sources(root, manifest):
    root=Path(root)
    require(root.is_absolute() and root.is_dir() and root.resolve()==root,'REGULAR_RESOLVED_SOURCE_ROOT_REQUIRED')
    out={};identities={}
    for rel, expected in manifest.items():
        rp=Path(rel)
        require(not rp.is_absolute() and '..' not in rp.parts,'SOURCE_PATH_TRAVERSAL')
        p=root/rp
        require(p.is_file() and not p.is_symlink() and p.resolve()==p,'SOURCE_SYMLINK_OR_MISSING')
        raw=p.read_bytes();identity=raw_identity(raw)
        require(identity==expected,'RAW_SOURCE_IDENTITY_MISMATCH_'+rel)
        out[rel]=raw.decode('utf-8');identities[rel]={**identity,'resolved_path':str(p.resolve())}
    return out,identities

def audit_model_ir(root, config, inactive_text):
    validate_plan(config,inactive_text)
    source,before=read_exact_sources(root,SOURCE_IDENTITIES)
    masses=restriction_masses(source['models/sm/restrict_default.dat'])
    require(masses=={'MB':4.7,'MC':0.0},'ACTUAL_DEFAULT_RESTRICTION_MISMATCH')
    defaults=ast_parameter_defaults(source['models/sm/parameters.py'])
    require(defaults=={'MC':1.27,'MB':4.7},'RAW_UFO_DEFAULTS_CHANGED')
    refs=ast_particle_mass_refs(source['models/sm/particles.py'])
    require(refs=={'b':'MB','c':'MC'},'UFO_PARTICLE_MASS_REFERENCE_CHANGED')
    witnesses={name:{'source':rel,'first_line':lo,'last_line':hi,'lines':[{'line':i+1,'text':line} for i,line in enumerate(source[rel].splitlines()) if lo<=i+1<=hi]} for name,(rel,lo,hi) in WITNESSES.items()}
    _,after=read_exact_sources(root,SOURCE_IDENTITIES)
    require(before==after,'SOURCE_CHANGED_DURING_AUDIT')
    return {'schema_version':1,'evidence_class':'EXACT_SOURCE_STATIC_AUDIT_NOT_MG5_EXECUTION','status':'PASS_MODEL_AND_PHOTON_IR_SOURCE_AUDIT_WITH_PHYSICAL_CUTS_BLOCKED',
      'source_root':str(root),'source_identities_before':before,'source_identities_after':after,'source_witnesses':witnesses,
      'model_restriction':{'model':'sm','restriction':'restrict_default.dat','restricted_masses_GeV':masses,'raw_UFO_defaults_GeV':defaults,'particle_mass_refs':refs,'actual_import_status':'NOT_EXECUTED'},
      'process':{'commands':list(PROCESS_COMMANDS),'amplitude_order_bounds':{'QCD':2,'QED':2},'diagram_count':None,'diagram_set_validation':'NOT_EXECUTED','future_generate_scope':'SYMBOLIC_DIAGRAM_ENUMERATION_INCLUDED; CODE_GENERATION_EXCLUDED'},
      'photon_IR':{'maxjetflavor':4,'source_derived_final_coloured_categories':{str(pdg):cut_flavour_category(pdg,4) for pdg in [5,-5,4,-4,21]},'Frixione_hadronic_member_predicate':'is_a_j only','massive_bottom_in_Frixione_hadronic_sum_at_maxjetflavor4':False,'target_Born_final_coloured_legs':['b','b~'],'source_derived_target_Born_hadronic_Frixione_member_count':0,'Fortran_or_generated_process_executed':False,'ptgmin_nonzero_enables_template_isolation_branch':True,'positive_ptgmin_normalizes_away':['pta','draj'],'drab_remains_separate_in_inspected_normalization_branch':True,'mmaa_remains_separate_photon_pair_mass_cut':True,'candidate_generation_cuts':config['candidate_generation_cuts'],'unresolved_generator_conventions':config['unresolved_generator_conventions'],'physical_readiness':'BLOCKED_UNFIXED_CUT_ACCEPTANCE_AND_GENERATOR_CONVENTIONS','ATLAS_fixed_cone_equivalence':'NOT_ESTABLISHED'},
      'runtime_configuration_read_or_written':False,'MG5_module_imported':False,'MG5_parser_executed':False,'actual_generator_dispatch':False,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,'physical_component_validated':False,'external_human_approval':False}
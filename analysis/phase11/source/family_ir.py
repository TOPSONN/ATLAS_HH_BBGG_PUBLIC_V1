"""Version-bound source review only. Never import or dispatch generator code."""
from __future__ import annotations
import hashlib
import math
import re
from pathlib import Path

FLAVOURS_5F = [-5,-4,-3,-2,-1,1,2,3,4,5,21]
# Each witness binds the whole file SHA256, exact source path and matching lines.
WITNESSES = [
 ('MG5_VERSION','mg5','VERSION',['3.5.16']),
 ('PYTHIA_VERSION','pythia','share/Pythia8/xmldoc/Version.xml',['8.317']),
 ('MODEL_NO_B_MASS','mg5','models/sm/restrict_no_b_mass.dat',['0.000000e+00 # MC','0.000000e+00 # MB']),
 ('COUPLING_OPERATORS','mg5','madgraph/interface/madgraph_interface.py',['request exactly that number of coupling while','elif type == "==":','squared_orders[name] = (2 * value,']),
 ('LO_ISOLATION','mg5','Template/LO/SubProcesses/cuts.f',['if (ptgmin.ne.0d0) then','if (is_a_j(j)) then','if(isoEM)then','Etsum(nin)=Etsum(nin-1)+pt(pQCD(0,isorted(i)))']),
 ('LO_ISOLATION_FUNCTION','mg5','Template/LO/SubProcesses/cuts.f',['axn=abs(xn)','tmp=epsgamma*pTgamma','tmp=tmp*( (1-cos(dr))/(1-cos(R0)) )**axn']),
 ('JET_FLAVOUR_CLASSIFICATION','mg5','Template/LO/SubProcesses/setcuts.f',['if (abs(idup(i,1,iproc)).le.min(maxjetflavor,6)) then','is_a_b(i)=.true.','if (abs(idup(i,1,iproc)).eq.21)  is_a_j(i)=.true.']),
 ('PHOTON_CUT_MAPPING','mg5','Template/LO/SubProcesses/setcuts.f',['etmin(i) = max(pta, ptgmin)','etamax(i)=etaa','r2min(j,i)=drab','s_min(j,i)=mmaa*dabs(mmaa)']),
 ('POSITIVE_PTGMIN_CUT_OVERRIDE','mg5','madgraph/various/banner.py',["if self['ptgmin'] > 0:","self['pta'] = 0.0","self['draj'] = 0.0"]),
 ('GENERIC_CUT_ORDER','mg5','Template/LO/SubProcesses/cuts.f',['c     p_t min & max cuts','abs(rap(p(0,i))) .gt. etamax(i)','tmp .lt. r2min(j,i)','tmp .lt. s_min(j,i)','c Begin photon isolation']),
 ('MG5_LO_INTERFACE','mg5','Template/LO/Cards/pythia8_card_default.dat',["turned on by setting ickkw to '1'",'JetMatching:qCut         = -1.0','Merging:Process          = <set_by_user>','Merging:TMS              = -1.0']),
 ('MLM_HEADER_PRECEDENCE','pythia','include/Pythia8Plugins/JetMatching.h',['if (setMad) {','par.getParamAsInt("maxjetflavor")','settingsPtr->parm("JetMatching:qCut", par.getParam("xqcut"))']),
 ('MLM_FLAVOUR','pythia','include/Pythia8Plugins/JetMatching.h',['eventProcess[i].idAbs() <= nQmatch','eventProcess[i].idAbs() > nQmatch','exclusive = (nParton == nJetMax) ? false : true;']),
 ('MLM_UNMATCHED_B','pythia','share/Pythia8/htmldoc/JetMatching.html',['Bottom quarks are treated separately.  Currently, they are unmatched.','requires event samples that are specifically generated for this task.']),
 ('CKKWL_PHOTON_CORE','pythia','share/Pythia8/htmldoc/CKKWLMerging.html',['<code>t</code> (all SM quarks), <code>a</code>','Please use this feature with caution.']),
 ('CKKWL_GUESS_IMPLEMENTATION','pythia','include/Pythia8Plugins/aMCatNLOHooks.h',['settingsPtr->word("Merging:Process") == "guess"','workEvent[i].colType() == 0','workEvent[i].idAbs() > nQuarksMerge']),
 ('CKKWL_FLAVOUR','pythia','share/Pythia8/htmldoc/CKKWLMerging.html',['Merging:nQuarksMerge','unnecessary double-counting might occur otherwise.','Merging:includeMassive']),
 ('CKKWL_WEIGHT','pythia','share/Pythia8/htmldoc/CKKWLMerging.html',['Info::mergingWeight() * Info::weight()','Info::sigmaGen()','only known after the run.']),
 ('QCD_QED_SHOWER','pythia','share/Pythia8/htmldoc/TimelikeShowers.html',['TimeShower:nGluonToQuark','TimeShower:QEDshowerByQ','TimeShower:alphaSorder']),
 ('ISR_QCD_QED','pythia','share/Pythia8/htmldoc/SpacelikeShowers.html',['SpaceShower:QEDshowerByQ','SpaceShower:nQuarkIn','SpaceShower:alphaSorder']),
]

def classify_order_token(token):
    """Independent string interpretation; does NOT call the MG5 parser."""
    m=re.fullmatch(r'(QCD|QED)(\^2)?(==|<=|=|>)(\d+)',token)
    if not m: raise ValueError('UNSUPPORTED_ORDER_TOKEN')
    name,squared,operator,number=m.groups()
    return {'coupling':name,'target':'SQUARED_MATRIX_ELEMENT' if squared else 'AMPLITUDE',
            'relation':'<=' if operator=='=' else operator,'order':int(number),
            'parser_execution':False}

def jet_cut_class(pdg,maxjetflavor):
    p=abs(pdg)
    if p==21 or p<=min(maxjetflavor,6):return 'is_a_j'
    if maxjetflavor+1<=p<=5:return 'is_a_b'
    return 'other'

def frixione_bound(r,R,epsilon,pT,n):
    """Independent algebraic reproduction of LO chi_gamma_iso; method only."""
    if not all(math.isfinite(v) for v in [r,R,epsilon,pT,n]):raise ValueError('NONFINITE')
    if not (0<=r<=R<math.pi) or R==0 or epsilon<0 or pT<=0:raise ValueError('DOMAIN')
    return epsilon*pT*((1-math.cos(r))/(1-math.cos(R)))**abs(n) if n else epsilon*pT

def signed_merging_product(source_weight,merging_weight):
    if not all(math.isfinite(v) for v in (source_weight,merging_weight)):raise ValueError('NONFINITE_WEIGHT')
    return source_weight*merging_weight

def inactive_card_errors(text):
    return ['ACTIVE_GENERATOR_LINE'] if any(x.strip() and not x.lstrip().startswith('#') for x in text.splitlines()) else []

def _unresolved_errors(c):
    errors=[]
    if not c.get('unresolved_fields'):errors.append('MISSING_UNRESOLVED_FIELDS')
    for k,v in c.get('unresolved_fields',{}).items():
        if not isinstance(v,dict) or v.get('value','MISSING') is not None or v.get('status')!='BLOCKED' or not v.get('reason') or not v.get('evidence_required'):errors.append('UNRESOLVED_NOT_NULL_BLOCKED:'+k)
    if c.get('execution_authorized') is not False:errors.append('EXECUTION_NOT_INACTIVE')
    return errors

def validate_candidate_b(c):
    errors=_unresolved_errors(c)
    expected={'schema_version':1,'candidate_id':'B_COMMON_5F_AA_JETS','status':'SOURCE_CONDITIONAL_NOT_READY','model':'sm-no_b_mass','model_masses_GeV':{'bottom':0,'charm':0},'incoming_pdg_ids':FLAVOURS_5F,'additional_parton_pdg_ids':FLAVOURS_5F,'multiplicities':[0,1,2],'tree_level_only':True,'loop_induced_gg_aa_included':False,'fragmentation_contribution_included':False,'separate_explicit_HF_addition_allowed':False,'parser_validated':False,'physical_pilot_executed':False,'matching_validated':False}
    errors += ['INVARIANT:'+k for k,v in expected.items() if c.get(k)!=v or (isinstance(v,bool) and c.get(k) is not v)]
    if any(type(v) not in (int,float) for v in c.get('model_masses_GeV',{}).values()):errors.append('MASS_TYPE')
    if c.get('pdf')!={'set':None,'member':None,'lhaid':None,'sha256':None}:errors.append('UNREVIEWED_PDF')
    if c.get('alpha_s')!={'value_MZ':None,'running_order':None,'thresholds_GeV':None}:errors.append('UNREVIEWED_ALPHA_S')
    m=c.get('matching',{})
    for k in ['selected_prescription','numerical_scale_GeV']:
        if m.get(k,'MISSING') is not None:errors.append('UNREVIEWED_MATCHING:'+k)
    for k in ['mlm_required_nQmatch','ckkwl_required_nQuarksMerge','required_maxjetflavor']:
        if m.get(k)!=5:errors.append('FLAVOUR_MISMATCH:'+k)
    for k in ['weight_writer_closure_validated','highest_multiplicity_validated','ckkwl_core_string_parser_validated']:
        if m.get(k) is not False:errors.append('UNVALIDATED_MATCHING_FLAG_PROMOTION:'+k)
    if m.get('FxFx_for_historical_LO')!='INAPPLICABLE':errors.append('LO_FXFX_FALSE_PROMOTION')
    ps=c.get('process_definitions',[])
    if len(ps)!=3:errors.append('MULTIPLICITY_CARD_COUNT')
    for n,p in enumerate(ps):
        prefix='generate' if n==0 else 'add process'
        expected_text=prefix+' p5 p5 > a a'+' j5'*n+f' QCD=={n} QED==2 @{n}'
        if p.get('multiplicity')!=n or p.get('exact_order_text')!=expected_text:errors.append('EXACT_ORDER_PROPOSAL:'+str(n))
    if not c.get('shower_selected_settings') or any(v is not None for v in c.get('shower_selected_settings',{}).values()):errors.append('UNREVIEWED_SHOWER_VALUE')
    return errors

def validate_photon_ir(c):
    errors=_unresolved_errors(c)
    if c.get('schema_version')!=1 or c.get('method_proposal')!='SMOOTH_CONE_DIRECT_PHOTON':errors.append('PHOTON_SCHEMA')
    if c.get('status')!='DEFINITION_SOURCE_SUPPORTED_PARAMETERS_BLOCKED':errors.append('PHOTON_STATUS_FALSE_PROMOTION')
    required={'ptgmin_GeV','r0gamma','xn','epsgamma','isoEM','etaa','mmaa_GeV','draa','draj','drab'}
    p=c.get('selected_parameters',{})
    if set(p)!=required or any(v is not None for v in p.values()):errors.append('UNREVIEWED_PHOTON_PARAMETER')
    j=c.get('selected_generation_jet_cuts',{})
    if not j or any(v is not None for v in j.values()):errors.append('UNREVIEWED_JET_CUT')
    s=c.get('source_semantics',{})
    if s.get('QCD_energy_sum')!='is_a_j only; not is_a_b':errors.append('BOTTOM_ISOLATION_COVERAGE_MISSTATED')
    if s.get('disabled_by_positive_ptgmin')!=['pta','draj'] or 'drab' not in s.get('not_disabled',[]):errors.append('CUT_OVERRIDE_MISSTATED')
    if any(s.get(k) is not False for k in ['fixed_cone_equivalence_established','fragmentation_calibrated','cut_independence_established']):errors.append('PHOTON_CLOSURE_FALSE_PROMOTION')
    return errors

def audit_sources(mg5_root,pythia_root):
    roots={'mg5':Path(mg5_root),'pythia':Path(pythia_root)}
    rows=[]; files={}
    for identity,kind,rel,anchors in WITNESSES:
        path=roots[kind]/rel
        raw=path.read_bytes(); lines=raw.decode('utf-8',errors='strict').splitlines()
        digest=hashlib.sha256(raw).hexdigest()
        record={'path':str(path),'resolved_path':str(path.resolve()),'bytes':len(raw),'sha256':digest}
        key=kind+'/'+rel
        files[key]=record
        witnesses=[]
        for anchor in anchors:
            found=[{'line':i+1,'text':line.strip()} for i,line in enumerate(lines) if anchor in line]
            if not found:raise ValueError('SOURCE_WITNESS_MISSING:'+identity+':'+anchor)
            witnesses.append({'anchor':anchor,'matches':found[:12]})
        rows.append({'id':identity,'file_key':key,'sha256':digest,'witnesses':witnesses})
    return {'evidence_class':'HISTORICAL_SOURCE_AUDIT','scope':'STATIC_TEXT_AND_HASH_NO_GENERATOR_IMPORT_OR_INVOCATION','software_versions':{'MG5':'3.5.16','Pythia':'8.317'},'files':files,'source_witnesses':rows,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,'generator_parser_executed':False,'physical_pilot_executed':False}

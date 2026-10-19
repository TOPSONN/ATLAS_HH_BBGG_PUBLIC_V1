"""Phase12 explicit PDF metadata checks. No network, MG5 or native PDF imports.

The small parser accepts the one-line scalar/flow-list subset used by this
selected LHAPDF distribution, not arbitrary YAML. Native member readability
and interpolation are separate, actually executed checks owned by the caller.
"""
import ast
from collections import Counter
import hashlib
import math
from pathlib import Path

SET_NAME='NNPDF30_lo_as_0130_nf_4'
SET_INDEX=263400
DATA_VERSION=2
FOUR_FLAVOURS=frozenset((-4,-3,-2,-1,1,2,3,4,21))
CONFIG_DOC='https://www.lhapdf.org/config.html'
REQUIRED=('SetDesc','SetIndex','Authors','Reference','Format','DataVersion','NumMembers','Particle','Flavors','OrderQCD','FlavorScheme','NumFlavors','XMin','XMax','QMin','QMax','MZ','MCharm','MBottom','MTop','AlphaS_MZ','AlphaS_OrderQCD','AlphaS_Type','AlphaS_Qs','AlphaS_Vals')


def require(ok,reason):
    if not ok:raise ValueError(reason)


def integer(value,name,minimum=0):
    require(type(value) is int and value>=minimum,'INVALID_INTEGER_'+name)
    return value


def finite(value,name,positive=False):
    require(type(value) in (int,float),'INVALID_NUMBER_'+name)
    v=float(value)
    require(math.isfinite(v) and (v>0 if positive else True),'NONFINITE_OR_INVALID_'+name)
    return v


def scalar(text):
    value=text.strip()
    require(value!='','EMPTY_METADATA_VALUE')
    if value[0] in ('[','\"',"'"):
        try:return ast.literal_eval(value)
        except (ValueError,SyntaxError) as error:raise ValueError('UNSUPPORTED_METADATA_LITERAL') from error
    if value in ('true','True'):return True
    if value in ('false','False'):return False
    try:return int(value)
    except ValueError:pass
    try:return float(value)
    except ValueError:return value


def parse_metadata(text):
    require(isinstance(text,str) and len(text.encode('utf-8'))<=1024**2,'METADATA_SIZE_OR_TYPE')
    result={}
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):continue
        require(line!='---' and ':' in line,'UNSUPPORTED_METADATA_LAYOUT')
        key,value=line.split(':',1);key=key.strip()
        require(key and key not in result,'DUPLICATE_OR_EMPTY_METADATA_KEY')
        require(key.replace('_','').isalnum(),'INVALID_METADATA_KEY')
        result[key]=scalar(value)
    return result


def validate_metadata(info,member=0):
    require(isinstance(info,dict),'METADATA_MAPPING_REQUIRED')
    require(all(key in info for key in REQUIRED),'MISSING_SCIENTIFIC_METADATA')
    require(all(isinstance(info[key],str) and info[key].strip() for key in ('SetDesc','Authors','Reference')),'EMPTY_SCIENTIFIC_DESCRIPTION_OR_REFERENCE')
    integer(member,'member');require(member==0,'ONLY_REVIEWED_CENTRAL_MEMBER_ZERO')
    require(integer(info['SetIndex'],'SetIndex')==SET_INDEX,'WRONG_SELECTED_SET_INDEX')
    require(integer(info['DataVersion'],'DataVersion',1)==DATA_VERSION,'UNREVIEWED_DATA_VERSION')
    members=integer(info['NumMembers'],'NumMembers',1);require(members==101 and member<members,'SELECTED_MEMBER_RANGE')
    require(integer(info['Particle'],'Particle')==2212,'NON_PROTON_PARENT')
    require(info['Format']=='lhagrid1','UNSUPPORTED_GRID_FORMAT')
    require(integer(info['OrderQCD'],'OrderQCD')==0,'NON_LO_PDF_ORDER')
    require(integer(info['NumFlavors'],'NumFlavors',1)==4,'PDF_NOT_MAXIMUM_FOUR_FLAVOURS')
    flavours=info['Flavors'];require(isinstance(flavours,list),'FLAVOUR_LIST_REQUIRED')
    require(all(type(v) is int for v in flavours),'INVALID_FLAVOUR_ID')
    require(len(flavours)==len(set(flavours)) and set(flavours)==FOUR_FLAVOURS,'WRONG_FOUR_FLAVOUR_SCOPE_OR_BOTTOM_ACTIVATION')
    scheme=info['FlavorScheme'];require(scheme in ('fixed','variable'),'UNKNOWN_FLAVOUR_SCHEME')
    alpha_scheme=info.get('AlphaS_FlavorScheme',scheme)
    require(alpha_scheme in ('fixed','variable'),'UNKNOWN_ALPHA_FLAVOUR_SCHEME')
    alpha_nf=info.get('AlphaS_NumFlavors',info['NumFlavors'])
    require(integer(alpha_nf,'AlphaS_NumFlavors',1)==4,'ALPHA_NOT_MAXIMUM_FOUR_FLAVOURS')
    require(integer(info['AlphaS_OrderQCD'],'AlphaS_OrderQCD')==0,'NON_LO_ALPHA_ORDER')
    require(info['AlphaS_Type']=='ipol','UNREVIEWED_ALPHA_EVALUATION_TYPE')
    reference_scale=finite(info['MZ'],'MZ',True);reference_value=finite(info['AlphaS_MZ'],'AlphaS_MZ',True)
    xmin=finite(info['XMin'],'XMin',True);xmax=finite(info['XMax'],'XMax',True)
    qmin=finite(info['QMin'],'QMin',True);qmax=finite(info['QMax'],'QMax',True)
    require(0<xmin<xmax<=1 and 0<qmin<qmax,'INVALID_DECLARED_DOMAIN')
    require(qmin<=reference_scale<=qmax,'ALPHA_REFERENCE_OUTSIDE_DECLARED_Q_RANGE')
    qs=info['AlphaS_Qs'];values=info['AlphaS_Vals']
    require(isinstance(qs,list) and isinstance(values,list) and len(qs)==len(values) and len(qs)>=2,'INVALID_ALPHA_INTERPOLATION_LISTS')
    qq=[finite(v,'AlphaS_Qs',True) for v in qs];aa=[finite(v,'AlphaS_Vals',True) for v in values]
    require(all(a<=b for a,b in zip(qq,qq[1:])) and qq[0]<qq[-1],'UNORDERED_ALPHA_Q_NODES')
    require(qq[0]<=reference_scale<=qq[-1],'ALPHA_REFERENCE_OUTSIDE_ALPHA_TABLE')
    thresholds={}
    for pdg,name in [(4,'Charm'),(5,'Bottom'),(6,'Top')]:
        mass=finite(info['M'+name],'M'+name,True)
        pdf_key='Threshold'+name if 'Threshold'+name in info else 'M'+name
        pdf_threshold=finite(info[pdf_key],pdf_key,True)
        if 'AlphaS_Threshold'+name in info:alpha_key='AlphaS_Threshold'+name
        elif 'Threshold'+name in info:alpha_key='Threshold'+name
        elif 'AlphaS_M'+name in info:alpha_key='AlphaS_M'+name
        else:alpha_key='M'+name
        thresholds[name]={'pdg_id':pdg,'declared_evolution_mass_GeV':mass,'pdf_threshold_GeV':pdf_threshold,'pdf_threshold_source_key':pdf_key,'alpha_threshold_GeV':finite(info[alpha_key],alpha_key,True),'alpha_threshold_source_key':alpha_key,'activation_permitted_by_maximum_flavours':pdg<=4,'not_ME_pole_mass':True}
    duplicate_nodes=sorted(q for q,c in Counter(qq).items() if c>1)
    return {'schema_version':1,'status':'SOURCE_SUPPORTED_METADATA_ONLY','evidence_class':'PUBLIC_SOURCE_AUDIT','set_name':SET_NAME,'data_version':DATA_VERSION,'set_index':SET_INDEX,'member':member,'member_lhaid':SET_INDEX+member,'declared_released_members':members,'parent_pdg_id':2212,'flavours':flavours,'bottom_pdf_activation':False,'PDF_order_QCD':0,'PDF_flavour_scheme':scheme,'PDF_maximum_flavours':4,'alpha_order_QCD':0,'alpha_type':'ipol','alpha_flavour_scheme':alpha_scheme,'alpha_flavour_scheme_source_key':'AlphaS_FlavorScheme' if 'AlphaS_FlavorScheme' in info else 'FlavorScheme_DOCUMENTED_FALLBACK','alpha_maximum_flavours':alpha_nf,'alpha_maximum_flavours_source_key':'AlphaS_NumFlavors' if 'AlphaS_NumFlavors' in info else 'NumFlavors_DOCUMENTED_FALLBACK','alpha_reference':{'scale_GeV':reference_scale,'value':reference_value,'scale_source_key':'MZ','value_source_key':'AlphaS_MZ','interpretation':'SET_SPECIFIC_REFERENCE_SCALE; NOT_ASSUMED_ELECTROWEAK_Z_MASS','name_0130_does_not_define_value_at_reference':True},'thresholds':thresholds,'alpha_table_nodes':len(qq),'duplicate_alpha_Q_nodes_GeV':duplicate_nodes,'duplicate_nodes_not_proof_of_all_physical_thresholds':True,'declared_domain':{'xmin':xmin,'xmax':xmax,'Qmin_GeV':qmin,'Qmax_GeV':qmax},'ForcePositive':info.get('ForcePositive'),'reference':info['Reference'],'source_semantics_document':CONFIG_DOC,'catalogue_does_not_prove_payload_present':True,'native_member_readability':'NOT_TESTED_BY_METADATA_VALIDATION','MG5_parser_validated':False,'physical_component_validated':False}


def read_member_header(path):
    require(Path(path).is_file() and not Path(path).is_symlink(),'ACTUAL_MEMBER_MISSING_OR_SYMLINK')
    lines=[];size=0;terminated=False
    with Path(path).open('rb') as stream:
        for raw in stream:
            size+=len(raw);require(size<=64*1024,'OVERSIZED_MEMBER_HEADER')
            if raw.strip()==b'---':terminated=True;break
            lines.append(raw.decode('utf-8'))
    require(terminated,'MISSING_MEMBER_HEADER_TERMINATOR')
    return parse_metadata(''.join(lines))


def inspect_local_pair(info_path,member_path,member=0):
    info_path=Path(info_path);member_path=Path(member_path)
    require(info_path.is_file() and not info_path.is_symlink(),'ACTUAL_INFO_MISSING_OR_SYMLINK')
    require(info_path.name==SET_NAME+'.info' and member_path.name==SET_NAME+'_0000.dat','SELECTED_FILENAMES_MISMATCH')
    info=parse_metadata(info_path.read_text());header=read_member_header(member_path)
    merged=dict(info);merged.update(header)
    kind=header.get('MemType',header.get('PdfType'))
    require(kind=='central','SELECTED_MEMBER_NOT_CENTRAL')
    result=validate_metadata(merged,member)
    result['status']='LOCAL_PAYLOAD_METADATA_AND_HEADER_CHECKED'
    result['evidence_class']='LOCAL_PAYLOAD_METADATA_AUDIT'
    result['member_header']=header
    result['member_override_keys']=sorted(k for k in header if k in info and info[k]!=header[k])
    for label,path in [('info',info_path),('member',member_path)]:
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
        result[label+'_identity']={'path':str(path),'bytes':path.stat().st_size,'sha256':h.hexdigest()}
    return result
#!/usr/bin/env python3
"""Actually read one isolated member with installed LHAPDF; never imports MG5."""
import argparse,hashlib,json,math,os,sys,shutil,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from pdf_metadata import inspect_local_pair,parse_metadata
from pdf_interface import require,in_domain,guarded_xfx,value,validate_points,validate_readback_paths

def identity(path):
 path=Path(path);raw=path.read_bytes();return {'path':str(path),'resolved_path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def run(root,policy,out):
 root,out=validate_readback_paths(root,out);validate_points(policy)
 acquisition=json.loads((root/'acquisition_receipt.json').read_text());require(acquisition['status']=='PASS_COMPLETE_SELECTED_MEMBER_ACQUISITION' and acquisition['aggregate_body_bytes']==sum(row['received_bytes'] for row in acquisition['files'])<=134217728,'ACTUAL_COMPLETE_ACQUISITION_REQUIRED')
 for row in acquisition['files']:
  p=root/row['relative_path'];require(p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and identity(p)['sha256']==row['sha256'],'ACQUIRED_BYTES_CHANGED_OR_MISSING')
 name=policy['candidate'];info=root/name/(name+'.info');member=root/name/(name+'_0000.dat');metadata=inspect_local_pair(info,member);out.mkdir()
 # Preserve exact existing backend defaults only in the external validation folder; never install data.
 backendconf=Path('/home/btu/miniforge3/envs/atlas-hh-root/share/LHAPDF/lhapdf.conf');copy=root/'lhapdf.conf';
 if not copy.exists():shutil.copyfile(backendconf,copy)
 require(copy.read_bytes()==backendconf.read_bytes(),'BACKEND_CONFIG_COPY_CHANGED')
 backendindex=backendconf.parent/'pdfsets.index';indexcopy=root/'pdfsets.index'
 if not indexcopy.exists():shutil.copyfile(backendindex,indexcopy)
 require(indexcopy.read_bytes()==backendindex.read_bytes(),'CATALOGUE_COPY_CHANGED')
 protected=[info,member,backendconf,copy,backendindex,indexcopy,Path(sys.executable),Path('/home/btu/miniforge3/envs/atlas-hh-root/lib/libLHAPDF.so')]
 native_package=Path('/home/btu/miniforge3/envs/atlas-hh-root/lib/python3.12/site-packages/lhapdf');protected+=[native_package/'__init__.py',native_package/'lhapdf.so']
 before={str(p):identity(p) for p in protected}
 os.environ['LHAPDF_DATA_PATH']=str(root);os.environ['LHAPDF_DATA_PREFIX']=str(root)
 import lhapdf
 require(lhapdf.version()==policy['expected_LHAPDF_version'],'EXACT_EXISTING_READER_VERSION');lhapdf.setPaths([str(root)]);require(lhapdf.paths()==[str(root),str(backendconf.parent)],'UNEXPECTED_NATIVE_SEARCH_PATH');require(not (backendconf.parent/name).exists(),'LIVE_INSTALLED_MEMBER_SHADOW_RISK');lhapdf.setVerbosity(0)
 for p in (info,member,copy,indexcopy):require(Path(lhapdf.findFile(str(p.relative_to(root)))).resolve()==p.resolve(),'NATIVE_FILE_RESOLUTION_NOT_ISOLATED')
 pdf=lhapdf.mkPDF(name,0);flavours=list(pdf.flavors());require(set(flavours)==set(metadata['flavours']) and not pdf.hasFlavor(5) and not pdf.hasFlavor(-5),'WRONG_NATIVE_FOUR_FLAVOUR_SCOPE');require(value(pdf,'lhapdfID')==263400,'NATIVE_MEMBER_ID')
 domain={'xmin':float(value(pdf,'xMin')),'xmax':float(value(pdf,'xMax')),'Qmin_GeV':math.sqrt(float(value(pdf,'q2Min'))),'Qmax_GeV':math.sqrt(float(value(pdf,'q2Max')))};require(domain==metadata['declared_domain'],'NATIVE_DOMAIN_METADATA_DISAGREES')
 rows=[]
 for x,q in policy['finite_xQ_points']:
  rows.append({'x':x,'Q_GeV':q,'xfxQ':{str(pdg):guarded_xfx(pdf,pdg,x,q,domain) for pdg in flavours}})
 ref=metadata['alpha_reference'];qvalues=sorted(set([q for _,q in policy['finite_xQ_points']]+[ref['scale_GeV']]));alphas=[]
 for q in qvalues:
  require(domain['Qmin_GeV']<=q<=domain['Qmax_GeV'],'ALPHA_POINT_OUTSIDE_DECLARED_DOMAIN');v=pdf.alphasQ(q);require(math.isfinite(v) and v>0,'NONFINITE_OR_INVALID_ALPHA');alphas.append({'Q_GeV':q,'alpha_s':v})
 refactual=next(x['alpha_s'] for x in alphas if x['Q_GeV']==ref['scale_GeV']);reference_close=math.isclose(refactual,ref['value'],rel_tol=policy['alpha_reference_relative_tolerance'])
 declared_info=parse_metadata(info.read_text());qnodes=declared_info['AlphaS_Qs'];anodes=declared_info['AlphaS_Vals'];qref=ref['scale_GeV'];bracket=[{'Q_GeV':q,'alpha_s':a} for q,a in zip(qnodes,anodes) if q==max(q for q in qnodes if q<=qref) or q==min(q for q in qnodes if q>=qref)]
 reference_diagnostic={'declared_reference':ref,'native_alpha_at_declared_Q':refactual,'absolute_difference':refactual-ref['value'],'relative_difference':(refactual-ref['value'])/ref['value'],'within_strict_diagnostic_tolerance':reference_close,'strict_diagnostic_relative_tolerance':policy['alpha_reference_relative_tolerance'],'comparison_role':policy['alpha_reference_comparison_role'],'reference_is_exact_alpha_table_knot':qref in qnodes,'alpha_table_bracket':bracket,'publisher_interpolation_accuracy_bound':None,'physical_ME_or_shower_alpha_binding':'UNVERIFIED_NOT_EXECUTED'}
 rejected=[]
 for x,q in [(0.,10.),(1.1,10.),(.1,domain['Qmin_GeV']/2),(.1,domain['Qmax_GeV']*2),(float('nan'),10.)]:
  try:guarded_xfx(pdf,21,x,q,domain)
  except ValueError as error:rejected.append({'x':str(x),'Q_GeV':q,'rejection':str(error),'native_xfxQ_called':False})
  else:raise ValueError('OUT_OF_DOMAIN_NOT_REJECTED')
 after={str(p):identity(p) for p in protected};require(before==after,'NATIVE_INPUT_OR_DEPENDENCY_RAW_DRIFT');dependencies=list(after.values())
 result={'schema_version':1,'evidence_class':'ACTUAL_ISOLATED_PDF_READBACK','status':'PASS_ISOLATED_NATIVE_PDF_INTERFACE_WITH_LIMITS','observed_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'PID':os.getpid(),'reader_version':lhapdf.version(),'observed_data_paths':lhapdf.paths(),'selected_member_resolution':'EXCLUSIVE_EXTERNAL_MEMBER; BUILTIN_METADATA_FALLBACK_OBSERVED_AND_NO_SAME_NAME_INSTALLED_SET','native_file_resolution_checked':True,'raw_inputs_and_dependencies_before':before,'raw_inputs_and_dependencies_after':after,'metadata':metadata,'native_flavours':flavours,'native_LHAPDF_ID':value(pdf,'lhapdfID'),'bottom_active':False,'domain':domain,'finite_pdf_points':rows,'finite_xfx_values':sum(len(row['xfxQ']) for row in rows),'alpha_values':alphas,'alpha_reference_diagnostic':reference_diagnostic,'nonfinite_errors':0,'interpolation_errors':0,'out_of_domain_guard_rejections':rejected,'native_default_extrapolation_tested':False,'domain_guard_interpretation':policy['domain_policy'],'backend_dependencies':dependencies,'source_sha256':{str(p):identity(p)['sha256'] for p in (Path(__file__),Path(__file__).parents[1]/'source/pdf_interface.py',Path(__file__).parents[1]/'source/pdf_metadata.py',Path(__file__).parents[1]/'source/pdf_acquisition.py',Path(__file__).parents[1]/'config/readback_points.json')},'MG5_parser_executed':False,'matching_validated':False,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,'physical_component_validated':False,'installed_directory_writes':False}
 alpha={'schema_version':1,'evidence_class':'ACTUAL_ISOLATED_PDF_READBACK','status':'MEASURED_DECLARED_REFERENCE_AND_NATIVE_IPOL_DIAGNOSTIC','declared':ref,'actual_alpha_at_declared_reference':refactual,'reference_diagnostic':reference_diagnostic,'strict_diagnostic_tolerance_not_official_accuracy_bound':True,'finite_alpha_values':alphas,'reference_scale_not_assumed_91_1876':True,'set_name_not_used_to_define_reference':True,'alpha_type':metadata['alpha_type'],'thresholds':metadata['thresholds'],'native_alpha_scheme_from_metadata_fallback_not_ME_or_shower_binding':True,'MG5_binding':'UNVERIFIED_NOT_EXECUTED'}
 for name,obj in [('pdf_member_readback.json',result),('pdf_alpha_reference_checks.json',alpha)]:
  with (out/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--payload-root',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();r=run(a.payload_root,json.loads(a.policy.read_text()),a.output_dir);print(json.dumps({'status':r['status'],'finite_xfx_values':r['finite_xfx_values'],'alpha_points':len(r['alpha_values']),'guard_rejections':len(r['out_of_domain_guard_rejections'])}))

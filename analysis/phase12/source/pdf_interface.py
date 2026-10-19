"""Finite standalone PDF-interface guards; no generator or production API."""
import math,re
from pathlib import Path
from pdf_acquisition import verify_output_parent

def require(ok,msg):
 if not ok:raise ValueError(msg)
def in_domain(x,q,domain):
 return all(type(v) in (float,int) and math.isfinite(v) for v in (x,q)) and domain['xmin']<=x<=domain['xmax'] and domain['Qmin_GeV']<=q<=domain['Qmax_GeV']
def guarded_xfx(pdf,pdg,x,q,domain):
 require(in_domain(x,q,domain),'OUT_OF_DOMAIN_REJECTED_BEFORE_NATIVE_CALL')
 require(pdf.inRangeX(x) and pdf.inRangeQ(q),'NATIVE_RANGE_DISAGREES')
 value=pdf.xfxQ(pdg,x,q);require(math.isfinite(value),'NONFINITE_NATIVE_INTERPOLATION');return value
def value(obj,name):
 v=getattr(obj,name);return v() if callable(v) else v
def validate_points(c):
 require(c['candidate']=='NNPDF30_lo_as_0130_nf_4' and c['member']==0 and type(c['member']) is int,'EXACT_CENTRAL_MEMBER')
 require(c['finite_xQ_points']==[[0.0001,10.0],[0.01,91.1876],[0.1,1000.0],[0.5,100.0]],'DOCUMENTED_FINITE_POINTS_ONLY')
 require(c['alpha_reference_comparison_role']=='DIAGNOSTIC_NOT_OFFICIAL_ACCURACY_TEST','REFERENCE_INTERPOLATION_NOT_OFFICIAL_ACCURACY_GATE')
 require(type(c['alpha_reference_relative_tolerance']) is float and c['alpha_reference_relative_tolerance']==1e-6,'UNREVIEWED_ALPHA_REFERENCE_TOLERANCE')
 require(c['MG5_parser_executed'] is False and c['matching_validated'] is False and c['physical_generation_authorized'] is False,'NO_GENERATOR_AUTHORITY');return True

def validate_readback_paths(root,out):
 root=Path(root).absolute();out=Path(out).absolute();expected=Path('/home/btu/simulations/hh_phase12/run_01/public_pdf_01')
 require(root==expected,'ONLY_REVIEWED_EXTERNAL_PAYLOAD');verify_output_parent(root)
 require(out.parent==expected.parent and re.fullmatch(r'pdf_readback_[0-9]{2}',out.name),'UNEXPECTED_INSTALLED_OUTPUT_WRITE');verify_output_parent(out.parent)
 require(not out.exists() and not out.is_symlink(),'FRESH_READBACK_OUTPUT_REQUIRED');return root,out

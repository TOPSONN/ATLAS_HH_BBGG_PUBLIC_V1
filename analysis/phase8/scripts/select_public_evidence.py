#!/usr/bin/env python3
"""Select bounded numerical evidence; does not stage, commit, push or copy event files."""
import argparse,csv,json,hashlib
from pathlib import Path
from summarize_outputs import copy,read,save,sha
MASS={'m_gamma_gamma','m_bb','m_HH'}
def subset(src,dst,predicate):
 with Path(src).open() as i,Path(dst).open('x',newline='') as o:
  r=csv.DictReader(i);w=csv.DictWriter(o,fieldnames=r.fieldnames);w.writeheader()
  for row in r:
   if predicate(row):w.writerow(row)
def portable(obj):
 if isinstance(obj,str):return obj.replace(str(Path.home()),'${LOCAL_HOME}')
 if isinstance(obj,list):return [portable(x) for x in obj]
 if isinstance(obj,dict):return {portable(k):portable(v) for k,v in obj.items()}
 return obj

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('REFUSE_EXISTING_EVIDENCE_DIRECTORY')
 a.output.mkdir(parents=True)
 names=['phase8_cutflow_raw.csv','phase8_cutflow_weighted.csv','phase8_reconstruction_statistics.csv','phase8_control_regions.csv','phase8_region_closure.json','phase8_weight_accounting.csv','phase8_btag_conditional_diagnostics.csv','phase8_kappa_summary.csv','phase8_kappa_covariance.csv','phase8_kappa_correlations.csv','phase8_kappa_weight_tails.json','phase8_shape_variants.csv','phase8_systematics_readiness.csv','phase8_background_overlap_matrix.json','phase8_fake_photon_readiness.json','phase8_likelihood_method_tests.json','phase8_toy_closure.json','independent_statistics_validation.json','independent_native_validation_02.json','repeatability_validation.json','phase8_input_preservation_after.json','phase8_historical_workspace_preservation.json']
 for n in names:copy(a.result/n,a.output/n)
 subset(a.result/'phase8_kappa_bin_quality.csv',a.output/'phase8_kappa_final_mass_bin_quality.csv',lambda r:r['stage']=='FINAL_MGG' and r['observable'] in MASS)
 subset(a.result/'phase8_bin_quality.csv',a.output/'phase8_final_mass_bin_quality.csv',lambda r:r['stage']=='FINAL_MGG' and r['observable'] in MASS)
 subset(a.result/'phase8_shape_comparisons.csv',a.output/'phase8_final_mass_shape_comparisons.csv',lambda r:r['stage']=='FINAL_MGG' and r['observable'] in MASS)
 t=read(a.result/'phase8_template_manifest.json');t['templates']=[r for r in t['templates'] if r['observable'] in MASS];t['public_subset']='FINAL_MGG three masses only; complete26observable templates stay local with exact SHA';save(a.output/'phase8_template_manifest.json',t)
 result=portable(read(a.result/'phase8_analysis_results.json'));save(a.output/'phase8_analysis_results.json',result)
 execution=portable(read(a.result/'phase8_execution_manifest.json'));save(a.output/'phase8_execution_manifest.json',execution)
 local=read(a.result/'phase8_output_hashes.json');save(a.output/'phase8_local_output_hashes.json',local)
 payload={str(p.relative_to(a.output)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(a.output.rglob('*')) if p.is_file()}
 if any(p.suffix.lower() in ['.png','.pdf','.root','.so','.lhe','.gz','.jsonl'] for p in a.output.rglob('*') if p.is_file()):raise ValueError('FORBIDDEN_PUBLIC_OUTPUT_TYPE')
 if sum(v['bytes'] for v in payload.values())>5*1024*1024:raise ValueError('BOUNDED_EVIDENCE_EXCEEDS_5MIB')
 save(a.output/'manifest.json',{'schema_version':1,'scope':'SOURCE_AND_BOUNDED_NUMERICAL_EVIDENCE_NO_FIGURES_NO_PHYSICAL_EVENT_FILES','evidence_class':'ACTUAL_FULL_DATA_READBACK_LOCAL_RECEIPTS','full_native_ROOT_is_reexecuted_on_GitHub':False,'numerical_histogram_content_sha256':result['NUMERICAL_HISTOGRAM_CONTENT_HASH'],'files':payload,'publication_head_and_CI':'Final exact head receipt saved locally after publication; GitHub checks attached to PR are authoritative.'});print('BOUNDED_EVIDENCE_READY',len(payload),sum(v['bytes'] for v in payload.values()))
if __name__=='__main__':main()
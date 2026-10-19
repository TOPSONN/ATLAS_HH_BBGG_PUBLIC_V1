#!/usr/bin/env python3
"""Validate actual bounded evidence and emit a fresh fail-closed policy matrix."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from physical_gates import assemble,demand

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('source-review','heavy-flavour','photon','sideband','precision','pilot'):p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();items={};data={}
 for key in ('source_review','heavy_flavour','photon','sideband','precision','pilot'):
  f=getattr(a,key);raw=f.read_bytes();d=json.loads(raw);data[key]=d;items[key]={'path':str(f),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'evidence_class':d['evidence_class'],'status':d['status']}
 review,hf,ph,side,prec,pilot=[data[k] for k in ('source_review','heavy_flavour','photon','sideband','precision','pilot')]
 demand(review['status'].startswith('PASS'),'SOURCE_REVIEW_FAILED')
 demand(hf['status']=='VALIDATED_WITH_LIMITS' and hf['source_events_joined']==6000 and hf['source_events_stratified']==3000,'HF_NOT_ACTUAL')
 demand(hf['heavy_flavour_generator_exclusivity']=='UNVERIFIED','GENERATOR_EXCLUSIVITY_UNVALIDATED')
 demand(ph['status']=='BLOCKED_MISSING_COMPATIBLE_OBSERVABLES' and ph['actual_existing_events_joined']==6000 and ph['physical_fake_rate']=='UNKNOWN','UNSUPPORTED_PHOTON_GATE')
 demand(ph['compatible_public_calibration_imported'] is False and ph['synthetic_result_used_in_physical_output'] is False,'INVALID_FAKE_IMPORT')
 demand(side['evidence_class']=='SYNTHETIC_METHOD_ONLY' and side['status']=='PASS_SYNTHETIC_METHOD_ONLY' and all(side['checks'].values()) and side['import_into_physical_results'] is False,'SIDEBAND_SCOPE')
 demand(prec['status']=='PASS_INDEPENDENT_PRECISION_ARITHMETIC_WITH_LIMITS' and prec['error_count']==0,'PRECISION_AUDIT_FAILED')
 demand(pilot['status']=='PREPARED_INACTIVE_BLOCKED' and pilot['execution_authorized'] is False and pilot['physical_pilot_executed'] is False and pilot['instantiable'] is False,'PILOT_NOT_INACTIVE')
 demand(review['new_physical_events']==0 and review['external_independent_human_approval'] is False,'SOURCE_REVIEW_SCOPE')
 demand(hf['new_physical_events']==0 and side['new_physical_events']==0 and prec['new_independent_hard_events']==0,'NEW_PRODUCTION_IN_EVIDENCE')
 demand(all(type(ph[k]) is int and ph[k]==0 for k in ('new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events')),'PHOTON_PRODUCTION')
 demand(set(pilot['actual_new_production'])=={'new_me_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events'} and all(type(v) is int and v==0 for v in pilot['actual_new_production'].values()),'PILOT_PRODUCTION_COUNTERS')
 demand(pilot['offline_validation']['valid_inactive_contract'] is True and not pilot['offline_validation'].get('errors'), 'PILOT_OFFLINE_VALIDATION_FAILED')
 matrix=assemble(items)
 with a.output.open('x') as f:json.dump(matrix,f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS_PHYSICAL_GATE_POLICY','output':str(a.output),'physical_total':'BLOCKED'}))
if __name__=='__main__':main()

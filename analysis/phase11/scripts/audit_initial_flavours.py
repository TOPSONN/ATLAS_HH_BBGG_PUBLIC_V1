#!/usr/bin/env python3
"""Read-only exact incoming b/c audit of existing B01--3 source LHE bytes.

This tests ONLY the proposed p4 incoming PDG domain. No filtering creates a
physical 4F sample; old masses, PDFs, shower and source normalization remain old.
"""
import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'simulation/pythia8/scripts'))
from validate_lhe_stream import iter_lhe_events

STAGES=('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')
P4=frozenset((21,1,-1,2,-2,3,-3,4,-4))


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()


def incoming(rows):
    nup=int(rows[0][0]);require(len(rows)>=nup+1,'LHE_PARTICLE_ROWS')
    values=tuple(int(r[0]) for r in rows[1:nup+1] if int(r[1])==-1)
    require(len(values)==2,'EXACTLY_TWO_LHE_INCOMING_PARTONS')
    require(all(p in P4 or abs(p)==5 for p in values),'UNSUPPORTED_EXISTING_INITIAL_PDG')
    return values


def classes(ids):
    bottom=any(abs(p)==5 for p in ids);charm=any(abs(p)==4 for p in ids)
    return {'ANY_INCOMING_BOTTOM':bottom,'ANY_INCOMING_CHARM':charm,
            'CHARM_WITHOUT_BOTTOM':charm and not bottom,'NO_INCOMING_B_OR_C':not(bottom or charm),
            'SOURCE_INITIAL_PDG_ALLOWED_BY_P4_ONLY':all(p in P4 for p in ids),
            'ANY_PYTHIA_ME_INITIAL_HEAVY_RECORD':False}


def covariance(xs,ys):
    require(len(xs)==len(ys) and len(xs)>1,'FIXED_ORIGINAL_N_REQUIRED')
    n=len(xs);x=[Fraction(str(a)) for a in xs];y=[Fraction(str(a)) for a in ys]
    return float(Fraction(n,n-1)*(sum((a*b for a,b in zip(x,y)),Fraction(0))-sum(x)*sum(y)/n))


def index_events(path):
    # Frozen ATLAS_DELPHES_INPUT_V1 E-row schema, as in Phase10 source joins.
    with path.open() as stream:
        require(next(stream).strip()=='ATLAS_DELPHES_INPUT_V1','INPUT_INDEX_SCHEMA')
        for line in stream:
            fields=line.split()
            if fields and fields[0]=='E':
                require(len(fields)==11,'INPUT_INDEX_EVENT_SCHEMA')
                yield {'ordinal':int(fields[1]),'source_ordinal':int(fields[4]),'source_sha':fields[5],
                       'hepmc_sha':fields[3],'source_weight_pb':float(fields[6]),'raw_weight_pb':float(fields[7]),'N':int(fields[8])}


def persisted(path,key):
    result={}
    with path.open() as stream:
        for line in stream:
            row=json.loads(line)
            if row['dataset_id'] not in ('B01','B02','B03'):continue
            identity=(row['dataset_id'],row[key]);require(identity not in result,'DUPLICATE_PERSISTED_EVENT');result[identity]=row
    require(len(result)==3000,'FULL_HISTORICAL_3000_REQUIRED');return result


def metrics(mask,weights):
    selected=[w if p else 0. for p,w in zip(mask,weights)]
    s=math.fsum(selected);q=math.fsum(w*w for w in selected);k=sum(mask);n=len(weights)
    return {'original_N':n,'events':k,'sumw_pb':s,'sumw2_pb2':q,'fixed_N_variance_pb2':covariance(selected,selected),'ESS_signed_sum':s*s/q if q else None,'zero_one_sided95_acceptance_upper':-math.expm1(math.log(.05)/n) if k==0 else None}


def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,lineterminator='\n');writer.writeheader();writer.writerows(rows)


def run(manifest_path,phase9,output):
    require(not output.exists(),'FRESH_OUTPUT_REQUIRED')
    origins_path=phase9/'origins_03/phase9_origins_event_details.jsonl';native_path=phase9/'native/phase9_native_events.jsonl'
    parser_paths=[REPO/'simulation/pythia8/scripts/validate_lhe_stream.py',REPO/'simulation/mg5/scripts/validate_lhe.py']
    files=[manifest_path,origins_path,native_path,*parser_paths]
    before={str(p):sha(p) for p in files}
    origins=persisted(origins_path,'source_event_index');native=persisted(native_path,'source_event_ordinal')
    require(set(origins)==set(native),'ORIGIN_NATIVE_KEY_SETS')
    manifest=json.loads(manifest_path.read_text());datasets=[d for d in manifest['datasets'] if d['dataset_id'] in ('B01','B02','B03')]
    require(len(datasets)==3,'EXACT_THREE_HISTORICAL_SOURCES')
    event_rows=[];count_rows=[];cov_rows=[];summaries={}
    for ds in datasets:
        name=ds['dataset_id'];lhe=Path(ds['lhe_path']);index=Path(ds['input_index_path'])
        for role,path in [('lhe',lhe),('input_index',index)]:
            require(path.is_file() and not path.is_symlink(),'SOURCE_FILE_TYPE');require(sha(path)==ds[role+'_sha256'],'FROZEN_'+role.upper()+'_HASH');before[str(path)]=sha(path);files.append(path)
        cohort=[];identity_hash=hashlib.sha256();pair_counts=Counter()
        for ordinal,(source,idx) in enumerate(itertools.zip_longest(iter_lhe_events(lhe),index_events(index)),1):
            require(source is not None and idx is not None,'LHE_INDEX_LENGTH_MISMATCH');key=(name,ordinal)
            require(key in origins and key in native,'MISSING_PERSISTED_JOIN');o=origins[key];n=native[key]
            require(ordinal==source['source_event_index']==idx['ordinal']==idx['source_ordinal'],'ORIGINAL_ORDINAL_JOIN')
            require(source['source_event_content_hash']==idx['source_sha']==o['source_event_sha256']==n['source_event_sha256'],'SOURCE_SHA_JOIN')
            require(idx['hepmc_sha']==o['hepmc_event_sha256']==n['hepmc_event_sha256'],'HEPMC_ID_JOIN')
            require(idx['N']==n['N_original']==ds['N_original']==1000,'ORIGINAL_DENOMINATOR')
            require(o['stages']==n['stages'],'STAGE_JOIN')
            raw=source['nominal_generator_weight'];weight=raw/1000
            require(all(math.isclose(weight,float(x),rel_tol=1e-13,abs_tol=1e-20) for x in [idx['source_weight_pb'],o['weight_pb'],n['source_weight_pb']]),'SOURCE_WEIGHT_JOIN')
            require(math.isclose(raw,idx['raw_weight_pb'],rel_tol=1e-13,abs_tol=1e-18),'RAW_WEIGHT_JOIN')
            ids=incoming(source['rows']);flags=classes(ids);flags['ANY_PYTHIA_ME_INITIAL_HEAVY_RECORD']=o['heavy_flavour']['heavy_quark_birth_counts'].get('ME_INITIAL_HEAVY_FLAVOUR_RECORD',0)>0
            pair=','.join(map(str,ids));pair_counts[pair]+=1;cohort.append({'incoming':ids,'flags':flags,'weight':weight,'stages':n['stages']})
            event_rows.append({'dataset_id':name,'source_event_ordinal':ordinal,'source_event_sha256':source['source_event_content_hash'],'hepmc_event_sha256':idx['hepmc_sha'],'incoming_beam1_pdg':ids[0],'incoming_beam2_pdg':ids[1],'raw_source_weight_pb':weight,**flags})
            identity_hash.update(f"{name}:{ordinal}:{source['source_event_content_hash']}:{ids[0]},{ids[1]}\n".encode())
        require(len(cohort)==1000,'FULL_1000_SOURCE_COHORT')
        weights=[e['weight'] for e in cohort];names=sorted(cohort[0]['flags']);vectors={}
        for feature in names:
            for i,stage in enumerate(STAGES):
                mask=[e['flags'][feature] and e['stages'][i] for e in cohort]
                count_rows.append({'dataset_id':name,'incoming_category':feature,'stage':stage,**metrics(mask,weights)})
                vectors[feature+':'+stage]=[w if p else 0. for w,p in zip(weights,mask)]
        for pair,count in sorted(pair_counts.items()):
            for i,stage in enumerate(STAGES):
                mask=[','.join(map(str,e['incoming']))==pair and e['stages'][i] for e in cohort]
                count_rows.append({'dataset_id':name,'incoming_category':'EXACT_ORDERED_PDG_PAIR:'+pair,'stage':stage,**metrics(mask,weights)})
        names=sorted(vectors)
        for i,a in enumerate(names):
            for b in names[i:]:cov_rows.append({'dataset_id':name,'vector_a':a,'vector_b':b,'original_N':1000,'fixed_N_covariance_pb2':covariance(vectors[a],vectors[b]),'triangle':'UPPER_SYMMETRIC'})
        exact_flags={f:sum(e['flags'][f] for e in cohort) for f in cohort[0]['flags']}
        mixed=exact_flags['ANY_PYTHIA_ME_INITIAL_HEAVY_RECORD'];hard_hf=sum(e['flags']['ANY_INCOMING_BOTTOM'] or e['flags']['ANY_INCOMING_CHARM'] for e in cohort)
        summaries[name]={'original_N':1000,'incoming_event_counts':exact_flags,'ordered_incoming_PDG_pair_event_counts':dict(sorted(pair_counts.items())),'ordered_source_identity_sha256':identity_hash.hexdigest(),'Pythia_combined_record_vs_LHE_hard_incoming_HF_count_equal':mixed==hard_hf,'physical_4F_reinterpretation_allowed':False}
    after={str(p):sha(p) for p in files};require(before==after,'HISTORICAL_INPUT_OR_PARSER_MUTATED')
    output.mkdir(parents=True)
    write_csv(output/'phase11_initial_flavour_source_events.csv',event_rows);write_csv(output/'phase11_initial_flavour_stage_counts.csv',count_rows);write_csv(output/'phase11_initial_flavour_covariance.csv',cov_rows)
    result={'schema_version':1,'status':'VALIDATED_HISTORICAL_INCOMING_PDG_WITH_LIMITS','evidence_class':'ACTUAL_EXISTING_DATA_READBACK','source_events':3000,'event_rows':len(event_rows),'stage_rows':len(count_rows),'covariance_rows':len(cov_rows),'datasets':summaries,'allowed_p4_initial_PDG_ids':sorted(P4),'classification_scope':'LHE_ISTUP_MINUS1_EXACT_RAW_EVENT_BYTES_JOINED_TO_ORIGINAL_INDEX_AND_PERSISTED_NATIVE_ORIGINS','combined_Pythia_initial_HF_is_not_incoming_bottom':True,'P4_domain_scope':'INITIAL_PDG_DOMAIN_ONLY_NOT_PDF_MASS_ALPHA_S_OR_PHYSICAL_4F_COMPATIBILITY','source_weights_preserved':True,'no_physical_B01_B02_B03_sum':True,'cross_dataset_physical_covariance':None,'input_hashes_before':before,'input_hashes_after':after,'new_ROOT_loops':0,'new_ME_calls':0,'new_integrals':0,'new_events':0}
    with (output/'phase11_initial_flavour_audit.json').open('x') as stream:json.dump(result,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--phase9',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run(a.manifest,a.phase9,a.output);print(json.dumps({k:result[k] for k in ('status','source_events','stage_rows','covariance_rows')}))

if __name__=='__main__':main()
"""Portable SHA/CRC/count/weight/covariance regression; native receipts separate."""
import gzip,re,csv,hashlib,math
from .common import *
from .lhe import load_lhe,validate_production
from .publication import REF

def validate_phase(folder,n):
    folder=Path(folder);manifest=read_json(folder/'manifest.json');validation=read_json(folder/'validation.json')
    require(manifest['source_events']==n and manifest['HepMC_events']==manifest['ROOT_entries']==100,'REFERENCE_COUNTS')
    expected={d['path'] for d in manifest['files']}|{'manifest.json'}
    require({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}==expected,'UNDECLARED_OR_MISSING_REFERENCE_FILES')
    for d in manifest['files']:
        p=folder/d['path'];require(not p.is_symlink() and p.resolve().is_relative_to(folder.resolve()),'UNSAFE_REFERENCE')
        require(sha(p)==d['sha256'] and p.stat().st_size==d['bytes'],'REFERENCE_HASH_OR_SIZE')
    full=read_json(folder/'full_source_and_chain_validation.json')
    effective=full['source']['validation']['effective_seed']
    require(n==100 and effective==21 or n==1000 and effective==20261122,'DOCUMENTED_EFFECTIVE_REFERENCE_SEED_DIFFERS')
    lhe=folder/('reference_'+str(n)+'.lhe.gz');source=load_lhe(lhe);validate_production(source,n,effective)
    require(sha(lhe)==validation['source_LHE_sha256'],'SOURCE_REFERENCE_IDENTITY')
    derived=load_lhe(folder/('physically_decayed_same_source_'+str(n)+'.lhe.gz'))
    require(hashlib.sha256(derived['raw']).hexdigest()==validation['physically_decayed_LHE_plain_sha256'] and
        len(derived['records'])==n,'ACTUAL_PHYSICAL_DECAY_REPRESENTATION')
    for original,decayed in zip(source['records'],derived['records']):
        require(decayed['nup']==8 and original['weight']==decayed['weight'] and original['scale']==decayed['scale'],'DERIVED_WEIGHT_OR_SCALE_CHANGED')
        for a,b in zip(original['particles'],decayed['particles'][:4]):
            require(a['id']==b['id'] and a['p4']==b['p4'] and a['mass']==b['mass'],'DERIVED_ORIGINAL_MOMENTUM_CHANGED')
        require([p['status'] for p in decayed['particles']]==[-1,-1,2,2,1,1,1,1] and
            sorted(p['id'] for p in decayed['particles'][4:])==[-5,5,22,22],'PHYSICAL_MIXED_DECAY_TOPOLOGY')
    h=gzip.decompress((folder/'reference_100.hepmc3.gz').read_bytes())
    require(hashlib.sha256(h).hexdigest()==validation['source_native_HepMC_sha256'],'EXACT_NATIVE_HEPMC_TRANSFER')
    require(len(re.findall(rb'^E ',h,re.M))==100 and h.rstrip().endswith(b'HepMC::Asciiv3-END_EVENT_LISTING'),'HEPMC_REFERENCE_COUNT_OR_ENVELOPE')
    require((folder/'detector_100.root').read_bytes()[:4]==b'root' and sha(folder/'detector_100.root')==validation['selected_native_ROOT_sha256'],'ROOT_REFERENCE_BYTES')
    reco=[json.loads(s) for s in (folder/'reco_events_100.jsonl').read_text().splitlines()]
    ancestry=[json.loads(s) for s in (folder/'hepmc_ancestry_100.jsonl').read_text().splitlines()]
    require(len(reco)==len(ancestry)==100,'REAL_PREFIX_LEDGER_COUNT')
    for i,(a,b) in enumerate(zip(reco,ancestry),1):
        original=source['records'][i-1];require(a['source_event_index']==b['source_event_index']==i and a['source_event_sha256']==b['source_event_sha256']==original['hash'],'SOURCE_PREFIX_BIJECTION')
        require(a['original_source_events']==n and abs(a['source_contribution_pb']-original['weight']/n)<1e-15,'ORIGINAL_SOURCE_DENOMINATOR')
        require(b['lineage']['H_bb_original']!=b['lineage']['H_gammagamma_original'],'TWO_DISTINCT_HIGGS')
    full=read_json(folder/'full_source_and_chain_validation.json');require(full['full_count']==n and full['stages']['full'+str(n)]['validated_events']==n,'MISSING_FULL_NATIVE_PROOF')
    # Public payload may not contain host paths; inspect compressed LHE/HepMC.
    for data in [source['raw'],h,*[p.read_bytes() for p in folder.rglob('*') if p.is_file() and p.suffix not in ['.gz','.root']]]:
        require(re.search(rb'(?:/[h]ome/[^ /]+/|/[m]nt/[a-z]/|[A-Z]:[\\/](?:Users|HH)[\\/])',data) is None,'PRIVATE_PATH_IN_REFERENCE')
    return {'source_events':n,'HepMC_events':100,'ROOT_entries':100,'portable_status':'PASS_HASH_CRC_COUNT_WEIGHTS',
        'native_ReaderAscii_ROOT_execution':'NOT_RERUN_BY_PORTABLE_CI; exact bound actual receipts retained'}

def validate_all():
    gates=read_json(REPO/'metadata/phase7_quality_gates.json')
    results={}
    for phase,name,n in [('7b','phase7b_100',100),('7c','phase7c_1000',1000)]:
        folder=REF/name
        if folder.exists():results[phase]=validate_phase(folder,n)
        else:require(gates['phases'][phase]!='PASS','MISSING_REQUIRED_PHYSICAL_REFERENCE')
    folder=REF/'phase7d_klambda'
    if folder.exists():
        m=read_json(folder/'manifest.json')
        require({p.name for p in folder.iterdir()}=={d['path'] for d in m['files']}|{'manifest.json'},'REWEIGHT_REFERENCE_FILE_SET')
        for d in m['files']:
            require(Path(d['path']).name==d['path'] and (folder/d['path']).stat().st_size==d['bytes'] and
                sha(folder/d['path'])==d['sha256'],'REWEIGHT_REFERENCE_HASH_OR_SIZE')
        rows=list(csv.DictReader((folder/'event_reweights.csv').open()));require(len(rows)==6000,'REWEIGHT_REFERENCE_COUNT')
        grouped={}
        for r in rows:grouped.setdefault(int(r['source_event_index']),{})[float(r['kappa_lambda'])]=r
        require(set(grouped)==set(range(1,1001)),'REWEIGHT_SOURCE_COHORT')
        for i,group in grouped.items():
            require(set(group)=={-1.,0.,1.,2.,2.5,5.},'REWEIGHT_BENCHMARK_GRID')
            require(abs(float(group[1.]['ratio'])-1)<1e-12,'SM_RATIO_CLOSURE')
            from .reweight import quadratic
            v={k:float(r['full_mass_squared_ME']) for k,r in group.items()}
            require(quadratic(v)[3]<1e-7,'INDEPENDENT_HELD_OUT_QUADRATIC_REGRESSION')
        from .independent_regression import validate_scan
        measured=read_json(folder/'validation.json')
        for name,key in [('phase7d_weighted_histograms.csv','histogram_sha256'),('phase7d_signal_background_cutflow.csv','cutflow_sha256')]:
            require(sha(REPO/'metadata'/name)==measured['comparison'][key],'PUBLISHED_NUMERICAL_COMPARISON_BINDING_CHANGED')
        independent=validate_scan(folder/'event_reweights.csv',REF/'phase7c_1000/reference_1000.lhe.gz',measured['model_BR_factor'])
        for k,row in independent['summaries'].items():
            original=measured['summaries'][k]
            for a,b in [('sum_pb','sum'),('sumw2_pb2','sumw2'),('ESS','ESS')]:
                require(abs(row[a]-original[b])<=1e-10*max(abs(row[a]),1e-300),'INDEPENDENT_DECIMAL_SUMMARY_REGRESSION')
        results['7d']={'source_events':1000,'benchmarks':6,'new_independent_events':0,'portable_status':'PASS_REAL_NUMERICAL_EVIDENCE_REGRESSION'}
    else:require(not gates['phases']['7d'].startswith('PASS') and gates['gates']['K']['status']!='PASS','MISSING_REWEIGHT_REFERENCE')
    return results

if __name__=='__main__':print(json.dumps(validate_all(),indent=2))

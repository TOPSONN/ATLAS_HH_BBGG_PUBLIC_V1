#!/usr/bin/env python3
"""Independent Phase9A review of frozen Phase8 evidence; no ROOT dispatch or generation."""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import subprocess

BASE = '8ecd91106acb1dae065cde14f1d62867d10b073f'
EXECUTED = '19faeaf487fb1f9b49ff00f5cf85eeeb1c949930'
STAGES = ('INPUT','PHOTONS','JETS','TWO_BTAGS','FINAL_MGG')
EXPECTED = {'S01_B100':[100,45,38,18,18], 'S01_C1000':[1000,484,403,143,143],
 'B01':[1000,446,266,91,28], 'B02':[1000,378,241,7,1],
 'B03':[1000,445,277,0,0], 'B04':[1000,370,220,77,75],
 'B05':[1000,327,322,131,131], 'B06':[1000,2,2,2,0]}
D = lambda v: Decimal(str(v))

def demand(condition, reason):
    if not condition: raise ValueError(reason)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load(path):
    with Path(path).open(encoding='utf-8') as f: return json.load(f)

def rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))

def close(a,b,reason):
    a,b=D(a),D(b)
    demand(abs(a-b)<=Decimal('8e-13')*max(abs(a),abs(b),Decimal('1e-28')),reason)

def moment(values):
    """Full fixed-original-N covariance, retaining zero contributions."""
    n=len(values); demand(n>1,'INSUFFICIENT_ORIGINAL_COHORT')
    mean=sum(values)/D(n)
    return sum((x-mean)**2 for x in values)*D(n)/D(n-1)

def covariance(a,b):
    demand(len(a)==len(b) and len(a)>1,'COVARIANCE_COHORT_MISMATCH')
    n=len(a); am=sum(a)/D(n); bm=sum(b)/D(n)
    return sum((x-am)*(y-bm) for x,y in zip(a,b))*D(n)/D(n-1)

def region(event):
    demand(event['stages'][2], 'REGION_REQUIRES_PHOTON_JET_ELIGIBILITY')
    tags=event['native_btag_multiplicity']
    tag='TAG_0' if tags==0 else 'TAG_1' if tags==1 else 'TAG_GE2'
    m=event['observables']['m_gamma_gamma']
    mass='UNDEFINED_MGG' if m is None else 'LOW' if 105<=m<120 else 'HIGGS' if 120<=m<=130 else 'HIGH' if 130<m<=160 else 'OUTSIDE_MGG'
    return tag,mass

def validate_bit0_event(event):
    jets=event['eligible_jets']
    for jet in jets:
        demand(jet['pt']>25 and abs(jet['eta'])<2.5,'NON_ELIGIBLE_NATIVE_JET')
        demand(bool(jet['native_btag_bits']&1)==jet['tagged'],'BIT0_TAG_MISMATCH')
    demand(sum(jet['tagged'] for jet in jets)==event['native_btag_multiplicity'],'NATIVE_TAG_MULTIPLICITY_MISMATCH')
    return len(jets)

def event_index(path):
    result={}
    with Path(path).open() as f:
        demand(f.readline().strip()=='ATLAS_DELPHES_INPUT_V1','UNSUPPORTED_INPUT_INDEX')
        for line in f:
            if not line.startswith('E '): continue
            v=line.split(); ordinal=int(v[1]); demand(ordinal not in result,'DUPLICATE_INPUT_ORDINAL')
            result[ordinal]={'number':int(v[2]),'hepmc':v[3],'source':int(v[4]),'hash':v[5],
                             'contribution':D(v[6]),'raw':D(v[7]),'N':int(v[8])}
    return result

def review(source, previous, output):
    source=Path(source).resolve(); previous=Path(previous).resolve(); output=Path(output).resolve()
    demand(not output.exists(),'REVIEW_OUTPUT_MUST_BE_FRESH')
    demand(output!=previous and previous not in output.parents,'HISTORICAL_OUTPUT_MUST_REMAIN_IMMUTABLE')
    evidence={}; matrix=[]
    def ref(path,scope,root=None):
        path=Path(path); root=Path(root or previous)
        logical=('PHASE8_SOURCE/' if root==source else 'PHASE8_LOCAL/')+str(path.relative_to(root))
        evidence[logical]={'sha256':sha(path),'bytes':path.stat().st_size,'scope':scope}
        return logical
    def check(name,detail,refs,scope='HISTORICAL_EVIDENCE_AUDIT'):
        matrix.append({'check':name,'status':'PASS','evidence_class':scope,'detail':detail,'evidence':refs,
                       'independent_review':'Phase9 science reviewer; source plus independent Decimal70 calculations'})
    files=subprocess.run(['git','ls-tree','-r','--name-only',BASE,'analysis/phase8','metadata/phase7e_audit.json','metadata/phase8_dataset_manifest.json'],cwd=source,text=True,capture_output=True,check=True).stdout.splitlines()
    pinned=[]
    for name in files:
        blob=subprocess.run(['git','show',BASE+':'+name],cwd=source,capture_output=True,check=True).stdout
        demand(hashlib.sha256(blob).hexdigest()==sha(source/name),'EXACT_PUBLISHED_SOURCE_CHANGED:'+name)
        if name.startswith('analysis/phase8/') and any('/'+x+'/' in name for x in ('include','src','config','apps')):
            old=subprocess.run(['git','show',EXECUTED+':'+name],cwd=source,capture_output=True,check=True).stdout
            demand(blob==old,'EXECUTED_AND_PUBLISHED_ANALYSIS_DIFFER:'+name)
        pinned.append(ref(source/name,'EXACT_PUBLISHED_SOURCE',source))
    check('EXACT_PHASE8_SOURCE',{'revision':BASE,'executed_core':EXECUTED,'tracked_files_verified':len(files)},pinned)
    man=load(previous/'phase8_local_manifest.json'); datasets={d['dataset_id']:d for d in man['datasets']}
    demand(set(datasets)==set(EXPECTED),'DATASET_SET_MISMATCH')
    events=defaultdict(list)
    eventfile=previous/'native/phase8_events.jsonl'
    for line in eventfile.open():
        event=json.loads(line); demand(event['dataset_id'] in datasets,'UNKNOWN_EVENT_DATASET'); events[event['dataset_id']].append(event)
    eventref=ref(eventfile,'PERSISTED_ACTUAL_EXISTING_ROOT_EVENT_READBACK')
    weightrows={(r['dataset_id'],r['stage']):r for r in rows(previous/'phase8_cutflow_weighted.csv')}
    modelrows={(r['dataset_id'],r['stage']):r for r in rows(previous/'phase8_weight_accounting.csv')}
    cohort=[]; identity=[]; bit0=0
    for did,ds in datasets.items():
        evs=events[did]; n=ds['N_original']; demand(len(evs)==n==EXPECTED[did][0],'FULL_COHORT_COUNT_MISMATCH:'+did)
        ind=event_index(ds['input_index_path']); demand(len(ind)==n,'SOURCE_INDEX_COUNT_MISMATCH:'+did)
        for key in ('root','input_index','truth_index','card','lhe'):
            p=Path(ds[key+'_path']); demand(sha(p)==ds[key+'_sha256'],'SOURCE_INPUT_BYTES_CHANGED:'+did+':'+key)
            evidence['INPUT/'+did+'/'+key]={'sha256':sha(p),'bytes':p.stat().st_size,'scope':'ACTUAL_FILE_HASH_AVAILABILITY_NOT_FRESH_ROOT_READBACK'}
        seen=set()
        for ordinal,e in enumerate(evs,1):
            ix=ind[ordinal]; key=(did,e['source_event_ordinal'],e['native_event_number'],e['source_event_sha256'])
            demand(key not in seen,'DUPLICATE_EVENT_IDENTITY'); seen.add(key)
            demand(e['source_event_ordinal']==ordinal==ix['source'] and e['native_event_number']==ix['number'] and e['source_event_sha256']==ix['hash'] and e['hepmc_event_sha256']==ix['hepmc'],'SOURCE_IDENTITY_MISMATCH:'+did)
            demand(e['N_original']==ix['N']==n,'ORIGINAL_DENOMINATOR_MISMATCH')
            close(e['source_weight_pb'],ix['contribution'],'INDEX_SOURCE_WEIGHT_MISMATCH')
            close(e['raw_LHE_XWGTUP_pb'],ix['raw'],'INDEX_RAW_WEIGHT_MISMATCH')
            close(D(e['source_weight_pb'])*D(n),e['raw_LHE_XWGTUP_pb'],'SOURCE_WEIGHT_NOT_RAW_DIVIDED_BY_N_ONCE')
            demand(e['model_factor_applied']==0,'SOURCE_EVENT_PREAPPLIED_BR')
            demand(e['stages'][0] and all(not e['stages'][i] or e['stages'][i-1] for i in range(1,5)),'NON_NESTED_SELECTION')
            jets=e['eligible_jets']
            bit0+=validate_bit0_event(e)
            demand(e['stages'][2]==(e['stages'][1] and len(jets)>=2),'JET_SELECTION_MISMATCH')
            demand(e['stages'][3]==(e['stages'][2] and e['native_btag_multiplicity']>=2),'TAG_SELECTION_MISMATCH')
            m=e['observables']['m_gamma_gamma']; demand(e['stages'][4]==(e['stages'][3] and m is not None and 105<=m<=160),'MASS_SELECTION_MISMATCH')
        actual=[sum(e['stages'][i] for e in evs) for i in range(5)]
        demand(actual==EXPECTED[did]==ds['expected_cutflow'],'CUTFLOW_MISMATCH:'+did)
        for i,stage in enumerate(STAGES):
            x=[D(e['source_weight_pb']) if e['stages'][i] else D(0) for e in evs]
            w=weightrows[did,stage]; m=modelrows[did,stage]
            close(sum(x),w['sumw'],'RAW_SUMW_MISMATCH');close(sum(v*v for v in x),w['sumw2'],'RAW_SUMW2_MISMATCH')
            close(moment(x),w['source_event_sampling_variance'],'FIXED_N_VARIANCE_MISMATCH')
            f=D(ds['model_br_factor']); applications=0 if f==1 else 1
            demand(int(m['BR_factor_applications'])==applications,'MODEL_BR_APPLICATION_COUNT_MISMATCH')
            close(sum(x)*f,m['sumw'],'MODEL_BR_NOT_APPLIED_ONCE')
            close(moment(x)*f*f,m['fixed_N_source_sampling_variance'],'MODEL_VARIANCE_SCALE_MISMATCH')
        cohort.append({'dataset_id':did,'N_original':n,'cutflow':actual,'status':'PASS'})
        identity.append({'dataset_id':did,'unique_source_keys':len(seen),'input_index_sha256':ds['input_index_sha256']})
    check('FULL_COHORTS',{'unique_independent_sources':sum(len(e) for e in events.values()),'datasets':cohort,'prefix_independent_count_increment':0},[eventref])
    check('SOURCE_EVENT_IDENTITY',identity,[eventref,ref(previous/'phase8a_event_identity_audit.json','FROZEN_INDEX_LHE_IDENTITY_RECEIPT')])
    check('SOURCE_WEIGHTS_AND_FIXED_N_VARIANCE',{'normalization':'raw XWGTUP / original N once','variance':'centered fixed original N, failed selections retained as zero','stage_rows':len(weightrows)},[eventref,ref(previous/'phase8_cutflow_weighted.csv','INDEPENDENTLY_RECOMPUTED')])
    check('MODEL_BR_ONCE',{'HH':datasets['S01_C1000']['model_br_factor'],'ZH':datasets['B04']['model_br_factor'],'ttH':datasets['B05']['model_br_factor'],'background_without_Higgs_BR':'B01 B02 B03 B06','rows':len(modelrows)},[ref(previous/'phase8_weight_accounting.csv','INDEPENDENTLY_RECOMPUTED')])
    check('NATIVE_BIT0',{'eligible_native_jets_checked':bit0,'predicate':'(BTag & 1) != 0','reco_flavour_not_substituted_for_tag':True},[eventref,ref(source/'analysis/phase8/src/Phase8Selection.cxx','SOURCE_SELECTION_REVIEW',source)])
    pdf=load(source/'metadata/phase7e_audit.json')
    for prefix,did in [('B','S01_B100'),('C','S01_C1000')]:
        ds=datasets[did]; demand(ds['actual_effective_PDF']==pdf[prefix+'_effective_PDF'],'EFFECTIVE_PDF_MISMATCH')
        demand(ds['actual_alpha_running']==('ONE_LOOP' if pdf[prefix+'_effective_running_loops']==1 else 'TWO_LOOP'),'EFFECTIVE_ALPHA_RUNNING_MISMATCH')
        close(ds['actual_alpha_s_MZ'],pdf[prefix+'_effective_alpha_s_MZ'],'ALPHA_MZ_MISMATCH')
    demand(datasets['S01_B100']['actual_effective_seed']==21,'B100_EFFECTIVE_SEED_RELABELLED')
    check('SIGNAL_PDF_ALPHA_IDENTITY',{'B100_PDF':pdf['B_effective_PDF'],'B100_alpha_loops':1,'B100_effective_seed':21,'C1000_PDF':pdf['C_effective_PDF'],'C1000_alpha_loops':2,'pooling':'FORBIDDEN_DIFFERENT_EFFECTIVE_CONFIGURATIONS'},[ref(source/'metadata/phase7e_audit.json','EFFECTIVE_RUNTIME_CONFIGURATION_AUDIT',source)])
    regional=Counter(); sumregions=defaultdict(Decimal)
    for did,evs in events.items():
        for e in evs:
            if e['stages'][2]:
                tag,mass=region(e); regional[did,tag,mass]+=1;sumregions[did,tag,mass]+=D(e['source_weight_pb'])
    rr=rows(previous/'phase8_control_regions.csv');demand(len(rr)==120,'REGION_ROW_COUNT')
    for r in rr:
        key=(r['dataset_id'],r['tag_region'],r['mass_region'])
        demand(int(r['N_region'])==regional[key],'REGION_COUNT_NOT_EXCLUSIVE')
        close(r['sumw'],sumregions[key],'REGION_SUMW_MISMATCH')
        if r['tag_region']!='TAG_GE2': demand(r['mbb_definition']=='UNDEFINED_NO_TWO_TAG_PAIR','FAKE_BB_CANDIDATE')
    check('CONTROL_REGION_PARTITION',{'rows':len(rr),'eligible_total':sum(regional.values()),'all_weighted_count_closures':True},[eventref,ref(previous/'phase8_control_regions.csv','INDEPENDENTLY_RECOMPUTED')])
    hm=load(previous/'phase8_histogram_manifest.json');hv=load(previous/'native/phase8_native_histogram_validation.json');finalhash=load(previous/'phase8_output_hashes_final.json')['SHA256']
    demand(hm['numerical_histogram_content_sha256']==hv['numerical_histogram_content_sha256'],'HISTORICAL_CANONICAL_HASH_MISMATCH')
    demand(hv['TH1D_count']==4052 and hv['TH2D_count']==616,'HISTORICAL_ROOT_OBJECT_COUNT_MISMATCH')
    for p in ('native/phase8_histograms.root','phase8_histograms.root','native/phase8_histogram_manifest.json'):
        demand(sha(previous/p)==finalhash[p],'PRESERVED_ROOT_OR_MANIFEST_BYTES_CHANGED')
        ref(previous/p,'EXACT_HISTORICAL_ROOT_BYTES_OR_MANIFEST')
    demand(sum(x['status']=='DEFINED' for x in hm['histograms'])==4668,'HISTOGRAM_MANIFEST_COUNT_MISMATCH')
    for h in hm['histograms']:
        ds=datasets[h['dataset_id']]; demand(h['N_original']==ds['N_original'] and h['source_ROOT_sha256']==ds['root_sha256'],'HISTOGRAM_SOURCE_IDENTITY_MISMATCH')
        if h['status']=='DEFINED':
            yield_mode=h['normalization_mode']=='EXPLORATORY_LUMINOSITY_YIELD'
            demand(h['BR_applications']==(1 if yield_mode and ds['model_br_factor']!=1 else 0),'HISTOGRAM_BR_APPLICATION_MISMATCH')
            if yield_mode: close(h['normalization_scale'],D(ds['model_br_factor'])*100000,'HISTOGRAM_MODEL_BR_SCALE_MISMATCH')
    check('HISTOGRAM_HASH_BINDING',{'canonical_content_sha256':hm['numerical_histogram_content_sha256'],'native_objects':4668,'fresh_ROOT_readback_in_this_script':False,'fresh_Phase9_native_receipt':'ROOT_ORCHESTRATOR_SEPARATE_EVIDENCE'},[ref(previous/'native/phase8_native_histogram_validation.json','HISTORICAL_ACTUAL_NATIVE_ROOT_DIGEST_VALIDATION'),ref(previous/'repeatability_validation.json','HISTORICAL_ACTUAL_NATIVE_REPEATABILITY')])
    c=events['S01_C1000']; bysource={e['source_event_ordinal']:e for e in c}; kpath=source/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7d_klambda/event_reweights.csv'
    frozen_kappa=subprocess.run(['git','show',BASE+':'+str(kpath.relative_to(source))],cwd=source,capture_output=True,check=True).stdout
    demand(hashlib.sha256(frozen_kappa).hexdigest()==sha(kpath),'FROZEN_KAPPA_WEIGHT_FILE_CHANGED')
    kw=defaultdict(dict)
    for w in rows(kpath):
        ordinal=int(w['source_event_index']); k=w['kappa_lambda'];e=bysource[ordinal]
        demand(e['source_event_sha256']==w['source_event_sha256'],'KAPPA_SOURCE_IDENTITY_MISMATCH')
        close(w['source_contribution_pb'],D(e['source_weight_pb'])*D(w['ratio']),'KAPPA_PRODUCTION_WEIGHT_NOT_RATIO_TIMES_SOURCE_WEIGHT')
        close(w['MODEL_BR_ONLY_weight_pb'],D(w['source_contribution_pb'])*D(datasets['S01_C1000']['model_br_factor']),'KAPPA_BR_NOT_APPLIED_ONCE')
        demand(ordinal not in kw[k],'DUPLICATE_KAPPA_SOURCE_KEY'); kw[k][ordinal]=D(w['MODEL_BR_ONLY_weight_pb'])
    demand(len(kw)==6 and all(len(v)==1000 for v in kw.values()),'KAPPA_NOT_SIX_SHARED_1000_SOURCE_VECTORS')
    covrows=rows(previous/'phase8_kappa_covariance.csv');demand(len(covrows)==180,'KAPPA_COVARIANCE_ROW_COUNT')
    for w in covrows:
        stage=STAGES.index(w['stage']);a=[kw[w['kappa_a']][i] if bysource[i]['stages'][stage] else D(0) for i in range(1,1001)];b=[kw[w['kappa_b']][i] if bysource[i]['stages'][stage] else D(0) for i in range(1,1001)]
        close(covariance(a,b),w['covariance_pb2'],'COMMON_SOURCE_KAPPA_COVARIANCE_MISMATCH')
    ks=rows(previous/'phase8_kappa_summary.csv')
    for w in ks:
        k=w['kappa_lambda'];v=list(kw[k].values());f=[kw[k][i] for i in range(1,1001) if bysource[i]['stages'][4]]
        close(sum(v)**2/sum(x*x for x in v),w['input_ESS'],'INPUT_KAPPA_ESS_MISMATCH');close(sum(f)**2/sum(x*x for x in f),w['final_ESS'],'FINAL_KAPPA_ESS_MISMATCH')
        if k in ('2.5','5'): demand(w['status']=='INCONCLUSIVE_REWEIGHTING','LOW_SUPPORT_BENCHMARK_UNBLOCKED')
    check('KAPPA_COMMON_SOURCE_COVARIANCE_AND_ESS',{'shared_sources':1000,'rows_not_independent_samples':6000,'covariance_entries_independently_recomputed':180,'kappa_statuses':{w['kappa_lambda']:w['status'] for w in ks}},[ref(kpath,'FROZEN_REWEIGHTING_NO_NEW_ME',source),ref(previous/'phase8_kappa_covariance.csv','INDEPENDENT_DECIMAL70_RECOMPUTATION'),ref(previous/'phase8_kappa_summary.csv','INDEPENDENT_DECIMAL70_ESS')])
    flags={}
    for file in ('phase8_bin_quality.csv','phase8_kappa_bin_quality.csv'):
        counts=Counter()
        for row in rows(previous/file):
            n=int(row['N_original_sources_contributing']); flag=row['quality_flag']
            if n==0: demand('EMPTY_BIN' in flag and row['ESS']=='','EMPTY_BIN_TREATED_AS_FINITE_ESS')
            if row['ESS'] and float(row['ESS'])<10: demand('LOW_ESS' in flag,'LOW_ESS_FLAG_ABSENT')
            counts[flag]+=1
        flags[file]=dict(counts);ref(previous/file,'QUALITY_FLAGS_INDEPENDENT_REVIEW')
    check('EMPTY_LOW_ESS_GUARDS',flags,['PHASE8_LOCAL/phase8_bin_quality.csv','PHASE8_LOCAL/phase8_kappa_bin_quality.csv'])
    overlap=load(previous/'phase8_background_overlap_matrix.json'); fake=load(previous/'phase8_fake_photon_readiness.json'); template=load(previous/'phase8_template_manifest.json'); methods=load(previous/'phase8_likelihood_method_tests.json')
    demand(overlap['combined_physical_background']=='BLOCKED','UNVALIDATED_PHYSICAL_BACKGROUND_SUM')
    demand(fake['numerical_fake_rate'] is None and not fake['zero_selected_events_implies_zero_background'],'MISSING_FAKE_MODEL_BECAME_ZERO')
    demand(template['physical_significance']==template['physical_CLs']==template['physical_kappa_limit']=='NOT_EVALUATED','PHYSICAL_INFERENCE_BYPASS')
    demand(methods['label']=='SYNTHETIC_METHOD_ONLY' and methods['actual_HH_events_used']==0,'SYNTHETIC_METHOD_RELABELLED_PHYSICAL')
    nuisances=rows(previous/'phase8_systematics_readiness.csv');demand(len(nuisances)==22 and all(not x['physical_value'] and not x['correlation_model'] for x in nuisances),'UNKNOWN_PHYSICAL_NUISANCES_FILLED')
    check('NO_PHYSICAL_SUM_AND_INFERENCE_BLOCKERS',{'background_sum':'BLOCKED','fake_model':'UNKNOWN_NOT_ZERO','physical_significance_CLs_kappa':'NOT_EVALUATED','unknown_physical_nuisance_rows':22},[ref(previous/x,'PHYSICAL_READINESS_CONTRACT') for x in ('phase8_background_overlap_matrix.json','phase8_fake_photon_readiness.json','phase8_template_manifest.json','phase8_systematics_readiness.csv','phase8_likelihood_method_tests.json')])
    pub=load(previous/'phase8_publication_receipt.json');demand(pub['PR_HEAD_REVISION']==BASE and 'native full ROOT readback is separately' in pub['CI_scope'],'CI_EVIDENCE_SCOPE_CONFLATED')
    check('EVIDENCE_SCOPE_SEPARATION',{'historical_local_native_ROOT':'ACTUAL_EXISTING_DATA_READBACK','this_review':'HISTORICAL_EVIDENCE_AUDIT plus independent persisted-event numerical recomputation','GitHub_CI':pub['CI_scope'],'published_numeric_summaries':'frozen bounded subset, not new ROOT readback'},[ref(previous/'phase8_publication_receipt.json','HISTORICAL_GITHUB_PUBLICATION_RECEIPT')])
    result={'schema_version':1,'task':'PHASE9A_INDEPENDENT_PHASE8_SCIENCE_REVIEW','status':'PASS_INDEPENDENT_SCIENCE_REVIEW_WITH_PHYSICAL_BLOCKERS','reviewed_source_revision':BASE,'executed_core_source_revision':EXECUTED,'reviewer':'Independent Phase9 science-review agent','signoff_meaning':'All stated source/persisted-event checks were physically executed; this signoff does not approve a physical likelihood or claim a new native ROOT readback.','source_events_independently_recomputed':7100,'additional_independent_sources':0,'fresh_native_ROOT_dispatches':0,'fresh_Phase9_native_ROOT_receipt_status':'PENDING_ROOT_ORCHESTRATOR','new_ME_calls':0,'new_integrals':0,'new_events':0,'matrix':matrix,'evidence':evidence,'physical_total_background':'BLOCKED','physical_significance':'NOT_EVALUATED','physical_CLs':'NOT_EVALUATED','physical_kappa_interval':'NOT_EVALUATED'}
    output.mkdir(parents=True);(output/'phase9a_independent_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--phase8-results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with localcontext() as ctx:
        ctx.prec=70;result=review(a.source,a.phase8_results,a.output)
    print(json.dumps({'status':result['status'],'checks':len(result['matrix']),'independent_source_events':7100}));return 0

if __name__=='__main__':raise SystemExit(main())
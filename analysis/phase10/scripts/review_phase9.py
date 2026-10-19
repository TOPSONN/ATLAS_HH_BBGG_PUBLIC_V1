#!/usr/bin/env python3
"""Independent Phase9 audit: exact source bytes, raw joins, selected arithmetic.

Reuses only historical streaming byte parsers. Does not import Phase9 classifiers,
production statistics, event reconstruction, or review result implementations.
"""
import argparse
import bisect
from collections import Counter,defaultdict
from decimal import Decimal,localcontext
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import csv
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'analysis/phase10/source'))
from hf_stratification import STAGES,demand,flags,me_class,rare_exact,read_jsonl,sha,validate_join,wilson,write_json
sys.path.insert(0,str(REPO/'simulation/pythia8/scripts'))
from validate_lhe_stream import iter_lhe_events
from validate_hepmc3 import iter_ascii
BASE='ebae34fdaf9ccb09c77bd47cb1c7827fa560de0a'
EXECUTED='2584e342b80b20c314392d20d77d92a6ccb850c4'
EXPECTED_DELIVERY_PATHS={'metadata/phase9_quality_gates.json','metadata/phase9_source_manifest.json','reports/phase9_final_report.md'}


def close(actual,expected,reason):
    if expected is None:
        demand(actual in (None,''),'UNDEFINED_BECAME_NUMBER_'+reason);return
    a=Decimal(str(actual));e=Decimal(str(expected))
    demand(a.is_finite() and abs(a-e)<=max(Decimal('2e-23'),abs(e)*Decimal('5e-11')),'NUMERIC_MISMATCH_'+reason)


def independent_moments(values):
    with localcontext() as ctx:
        ctx.prec=70;n=Decimal(len(values));x=[Decimal(str(v)) for v in values];s=sum(x);q=sum(v*v for v in x)
        variance=n/(n-1)*(q-s*s/n)
        return dict(sumw=s,sumw2=q,variance=variance,ESS=s*s/q if q else None)


def independent_selection(row):
    photons=sorted([p for p in row['photons'] if p['pt']>25 and abs(p['eta'])<2.37 and not 1.37<abs(p['eta'])<1.52],key=lambda p:(-p['pt'],p['index']))
    jets=sorted([j for j in row['all_jets'] if j['pt']>25 and abs(j['eta'])<2.5],key=lambda j:(-j['pt'],j['index']))
    tags=[j for j in jets if int(j['native_btag_bits'])&1]
    two=len(photons)>=2 and photons[0]['pt']>35
    mass=None
    if len(photons)>=2:
        a,b=photons[:2];mass=math.sqrt(max(0.,2*a['pt']*b['pt']*(math.cosh(a['eta']-b['eta'])-math.cos(a['phi']-b['phi']))))
    stages=[True,two,two and len(jets)>=2,two and len(jets)>=2 and len(tags)>=2,False]
    stages[4]=stages[3] and 105<=mass<=160
    return stages,photons,jets,tags,mass


def raw_h3_events(path):
    for kind,raw in iter_ascii(path,max_decompressed_gb=4):
        if kind!='event':continue
        attrs={};number=None
        for line in raw.decode().splitlines():
            fields=line.split(' ',3)
            if fields[0]=='E':number=int(fields[1])
            if len(fields)==4 and fields[0]=='A' and fields[1]=='0':attrs[fields[2]]=fields[3]
        yield dict(event_number=number,event_sha256=hashlib.sha256(raw).hexdigest(),attributes=attrs)


def index_events(path):
    with Path(path).open() as f:
        demand(next(f).strip()=='ATLAS_DELPHES_INPUT_V1','WRONG_INPUT_INDEX_FORMAT')
        for line in f:
            x=line.split()
            if x and x[0]=='E':
                demand(len(x)==11,'INPUT_INDEX_EVENT_SCHEMA')
                yield dict(ordinal=int(x[1]),number=int(x[2]),hepmc_hash=x[3],source_index=int(x[4]),source_hash=x[5],contribution=Decimal(x[6]),raw=Decimal(x[7]),N=int(x[8]),particles=int(x[9]),weights=int(x[10]))


def graph_births(particles):
    """Separate status/mother implementation; no Phase9 graph classifier reuse."""
    byid={p['pythia_index']:p for p in particles};counts=Counter();bottom=charm=0;gmothers=set()
    for p in particles:
        flavour=abs(p['pdg_id'])
        if flavour not in (4,5):continue
        status=abs(p['status']);mothers=[byid[m] for m in p['mothers'] if m]
        if status==23:category='ME_HEAVY_FLAVOUR_RECORD'
        elif status==21:category='ME_INITIAL_HEAVY_FLAVOUR_RECORD'
        elif any(m['pdg_id']==p['pdg_id'] for m in mothers):continue
        elif 41<=status<=59:category='SHOWER_HEAVY_FLAVOUR_BIRTH'
        elif any(m['is_hadron'] for m in mothers):category='HADRON_DECAY_HEAVY_QUARK'
        else:category='OTHER_OR_UNCLASSIFIED_HEAVY_QUARK_BIRTH'
        counts[category]+=1
        if category=='SHOWER_HEAVY_FLAVOUR_BIRTH':
            bottom+=flavour==5;charm+=flavour==4
            for m in mothers:
                if m['pdg_id']!=21 or not 41<=abs(m['status'])<=59:continue
                children=[byid[d] for d in m['daughters']]
                if all(any(c['pdg_id']==signed and 41<=abs(c['status'])<=59 for c in children) for signed in (flavour,-flavour)):gmothers.add(m['pythia_index'])
    return dict(heavy_quark_birth_counts=dict(counts),shower_bottom_births=bottom,shower_charm_births=charm,direct_gluon_splitting_mothers=sorted(gmothers),terminal_b_hadrons=sum(p['terminal_b_hadron'] for p in particles),terminal_c_hadrons=sum(p['terminal_c_hadron'] for p in particles))


def dr(j,p):
    px,py,pz,e=p['p4_gev'];pt=math.hypot(px,py)
    eta=math.asinh(pz/pt) if pt else math.copysign(math.inf,pz)
    phi=math.atan2(py,px);dp=math.remainder(j['phi']-phi,2*math.pi)
    return math.hypot(j['eta']-eta,dp)


def witness_hadron_labels(particles,jets):
    assigned=defaultdict(list);ambiguous=[]
    for p in particles:
        if not (p['terminal_b_hadron'] or p['terminal_c_hadron']):continue
        distances=sorted((dr(j,p),j['index']) for j in jets)
        if not distances or distances[0][0]>=.4:continue
        if len(distances)>1 and abs(distances[0][0]-distances[1][0])<=1e-12:ambiguous.append(p['pythia_index'])
        else:assigned[distances[0][1]].append(p)
    return {j['index']:5 if any(p['terminal_b_hadron'] for p in assigned[j['index']]) else 4 if any(p['terminal_c_hadron'] for p in assigned[j['index']]) else 0 for j in jets},ambiguous


def source_checks(p8,cohorts,origins):
    manifest=json.loads((p8/'phase8_local_manifest.json').read_text());records=[];files=[];witnesses=[]
    for d in manifest['datasets']:
        ds=d['dataset_id']
        if ds not in cohorts:continue
        for role in ('root','input_index','lhe','hepmc','card'):
            path=Path(d[role+'_path']);demand(path.is_file() and not path.is_symlink(),'MISSING_OR_SYMLINK_SOURCE_'+str(path));actual=sha(path);demand(actual==d[role+'_sha256'],'SOURCE_HASH_'+str(path));files.append(dict(dataset_id=ds,role=role,path=str(path),sha256=actual,bytes=path.stat().st_size))
        identity=hashlib.sha256();n=0
        streams=(cohorts[ds],origins[ds],iter_lhe_events(d['lhe_path']),raw_h3_events(d['hepmc_path']),index_events(d['input_index_path']))
        for reco,origin,lhe,h3,index in itertools.zip_longest(*streams):
            demand(all(x is not None for x in (reco,origin,lhe,h3,index)),'INCOMPLETE_SOURCE_JOIN_'+ds);n+=1
            source=lhe['source_event_content_hash'];hhash=h3['event_sha256'];a=h3['attributes'];raw=Decimal(str(lhe['nominal_generator_weight']))
            demand(n==reco['source_event_ordinal']==origin['source_event_index']==lhe['source_event_index']==index['ordinal']==index['source_index']==int(a['source_event_index']),'SOURCE_EVENT_ORDINAL_'+ds)
            demand(source==reco['source_event_sha256']==origin['source_event_sha256']==index['source_hash']==a['source_event_content_hash'],'LHE_SOURCE_EVENT_SHA_'+ds)
            demand(hhash==reco['hepmc_event_sha256']==origin['hepmc_event_sha256']==index['hepmc_hash'],'RAW_HEPMC_EVENT_SHA_'+ds)
            demand(h3['event_number']==reco['native_event_number']==index['number'],'NATIVE_EVENT_NUMBER_'+ds)
            demand(reco['N_original']==d['N_original']==index['N']==int(a['source_total_events'])==1000,'ORIGINAL_DENOMINATOR_'+ds)
            close(index['raw'],raw,'INDEX_RAW');close(index['contribution'],raw/1000,'INDEX_WEIGHT');close(reco['source_weight_pb'],raw/1000,'NATIVE_WEIGHT');close(reco['raw_LHE_XWGTUP_pb'],raw,'NATIVE_RAW_WEIGHT')
            outgoing=[int(p[0]) for p in lhe['rows'][1:int(lhe['rows'][0][0])+1] if int(p[1])==1]
            demand(outgoing==origin['hard_outgoing_pdg_ids'],'HARD_OUTGOING_LHE_PID_'+ds)
            identity.update(f'{ds}:{n}:{source}:{hhash}\n'.encode())
        demand(n==1000,'NOT_FULL_SOURCE_COHORT_'+ds);records.append(dict(dataset_id=ds,source_joins=n,ordered_source_identity_sha256=identity.hexdigest()))
        if ds in ('B01','B02','B03'):
            wi=997 if ds=='B03' else 1;name={'B01':'bbgg','B02':'ccgg','B03':'jjgg'}[ds];base=Path('/home/btu/simulations/pythia8_runs')/(name+'_1k');run=json.loads((base/'run_manifest.json').read_text());path=base/'particle_diagnostics.jsonl';demand(sha(path)==run['files'][path.name]['sha256'],'PYTHIA_WITNESS_SOURCE_HASH')
            raw=next(e for e in read_jsonl(path) if e['source_event_index']==wi);h=origins[ds][wi-1]['heavy_flavour'];independent=graph_births(raw['particles'])
            for key,val in independent.items():demand(h[key]==val,'RAW_GRAPH_WITNESS_'+ds+'_'+key)
            labels,amb=witness_hadron_labels(raw['particles'],h['jets']);demand(labels=={j['index']:j['heavy_hadron_flavour'] for j in h['jets']} and amb==h['ambiguous_hadron_assignment_ids'],'RAW_HADRON_CONE_WITNESS_'+ds)
            witnesses.append(dict(dataset_id=ds,source_event_index=wi,source_event_sha256=origins[ds][wi-1]['source_event_sha256'],raw_diagnostic_file_sha256=sha(path),independent_graph_counts=independent,independent_hadron_jet_labels=labels,unknown_endpoint_preserved=True))
    return manifest,records,files,witnesses


def arithmetic_checks(p9,cohorts,origins,manifest):
    rare=list(csv.DictReader((p9/'statistics_02/phase9_rare_event_precision.csv').open()));region=list(csv.DictReader((p9/'statistics_02/phase9_region_diagnostics.csv').open()));hf=list(csv.DictReader((p9/'origins_03/phase9_heavy_flavour_origins.csv').open()));datasets={d['dataset_id']:d for d in manifest['datasets']};stages={};numerical=0;tag_jets=0
    selected_photons=Counter();unknown=0
    for ds,events in cohorts.items():
        cuts=[0]*5
        for e,o in zip(events,origins[ds]):
            validate_join(o,e);close(o['model_br_factor'],datasets[ds]['model_br_factor'],'ORIGIN_MODEL_BR_FACTOR');calculated,photons,jets,tags,mgg=independent_selection(e);demand(calculated==e['stages'],'INDEPENDENT_CUT_FLAGS_'+ds);demand(len(tags)==e['native_btag_multiplicity'],'BIT0_MULTIPLICITY')
            demand({j['index'] for j in jets}=={j['index'] for j in e['eligible_jets']},'ELIGIBLE_JET_IDENTITY');demand({p['index'] for p in photons}=={p['index'] for p in e['photons'] if p['selected']},'SELECTED_PHOTON_IDENTITY');tag_jets+=len(jets)
            if mgg is not None:close(e['observables']['m_gamma_gamma'],mgg,'INDEPENDENT_MGG')
            cuts=[a+int(b) for a,b in zip(cuts,calculated)];p=o['photon_origin'];labels=Counter(q['origin'] for q in p['reco_photons'] if q['selected']);selected_photons.update(labels);demand(all(labels[k]==v for k,v in p['selected_reco_photon_counts'].items()),'PHOTON_SELECTED_OBJECT_COUNTS');demand(p['calibrated_fake_probability'] is None and p['fake_rate_status']=='BLOCKED_CALIBRATION_UNAVAILABLE','UNKNOWN_FAKE_RATE_LOST')
            assigned=[q['matched_truth_id'] for q in p['reco_photons'] if q['matched_truth_id'] is not None];demand(len(assigned)==len(set(assigned)),'NONEXCLUSIVE_PHOTON_TRUTH_MATCH')
            for q in p['reco_photons']:
                if q['origin']=='PROMPT_HARD_PROCESS':demand(set(q['truth_origin']['copy_chain_ids'])&set(p['verified_hard_photon_roots']),'PROMPT_WITHOUT_HARD_ROOT')
                if q['origin']=='SHOWER_RADIATION':demand(any(41<=abs(s)<=59 for s in q['truth_origin']['birth_original_pythia_statuses']),'RADIATION_WITHOUT_SHOWER_STATUS')
                if q['origin']=='UNCLASSIFIED':unknown+=1
        demand(cuts==datasets[ds]['expected_cutflow'],'HISTORICAL_CUTFLOW_CHANGED');stages[ds]=cuts
    demand(selected_photons==Counter(PROMPT_HARD_PROCESS=6298,SHOWER_RADIATION=24,ELECTRON_ASSOCIATED=3,UNCLASSIFIED=674),'PUBLISHED_SELECTED_PHOTON_TOTALS')
    for r in rare:
        ds=r['dataset_id']
        if ds not in cohorts:continue
        ev=cohorts[ds];k=STAGES.index(r['stage']);x=[e['source_weight_pb'] if e['stages'][k] else 0. for e in ev];m=independent_moments(x);count=sum(e['stages'][k] for e in ev);demand(int(r['k'])==count and int(r['N'])==1000,'RARE_STAGE_DENOMINATOR')
        for name,val in [('source_sumw_pb',m['sumw']),('source_sumw2_pb2',m['sumw2']),('fixed_original_N_sampling_variance_pb2',m['variance']),('ESS',m['ESS']),('MODEL_BR_ONLY_sumw_pb',m['sumw']*Decimal(str(datasets[ds]['model_br_factor'])))]:close(r[name],val,'RARE_'+name);numerical+=1
        lo,hi=wilson(count,1000);close(r['wilson_lower'],lo,'WILSON_LOW');close(r['wilson_upper'],hi,'WILSON_HIGH');el,eh,one=rare_exact(count,1000)
        if el is not None:close(r['lower'],el,'RARE_EXACT_LOW');close(r['upper'],eh,'RARE_EXACT_HIGH')
        if count==0:close(r['one_sided95_upper_if_zero'],one,'ZERO_EXACT_UPPER')
    for r in region:
        ds=r['dataset_id']
        if ds not in cohorts:continue
        ev=cohorts[ds];selected=[]
        for e in ev:
            if not e['stages'][2]:selected.append(False);continue
            tags=e['native_btag_multiplicity'];tag='TAG_0' if tags==0 else 'TAG_1' if tags==1 else 'TAG_GE2';m=e['observables']['m_gamma_gamma'];mass='UNDEFINED_MGG' if m is None else 'LOW' if 105<=m<120 else 'HIGGS' if 120<=m<=130 else 'HIGH' if 130<m<=160 else 'OUTSIDE_MGG';selected.append((tag,mass)==(r['tag_region'],r['mass_region']))
            if tags<2:demand(e['observables']['m_bb'] is None and e['observables']['m_HH'] is None,'NULL_TAG_CANDIDATE_LOST')
        m=independent_moments([e['source_weight_pb'] if s else 0 for e,s in zip(ev,selected)]);demand(sum(selected)==int(r['N_region']),'EXCLUSIVE_REGION_COUNT')
        for name,val in [('source_sumw_pb',m['sumw']),('source_sumw2_pb2',m['sumw2']),('fixed_N_variance_pb2',m['variance']),('MODEL_BR_ONLY_sumw_pb',m['sumw']*Decimal(str(datasets[ds]['model_br_factor'])))]:close(r[name],val,'REGION_'+name);numerical+=1
    hf_checks=0
    for r in hf:
        if r['classification_unit']!='SOURCE_EVENT_INDICATOR_NONEXCLUSIVE_ORIGIN_FLAGS':continue
        ev=origins[r['dataset_id']];k=STAGES.index(r['stage']);indicator=[e['stages'][k] and flags(e)[r['category']] for e in ev];m=independent_moments([e['weight_pb'] if v else 0 for e,v in zip(ev,indicator)]);demand(sum(indicator)==int(r['events']),'HF_FLAG_COUNT')
        for name,val in [('sumw_pb',m['sumw']),('sumw2_pb2',m['sumw2']),('source_sampling_variance_pb2',m['variance']),('ESS',m['ESS'])]:close(r[name],val,'HF_'+name);hf_checks+=1
    hchecks=0;hcount=0
    for h in json.loads((p9/'statistics_02/phase9_plot_data.json').read_text())['histograms']:
        ds=h['dataset_id']
        if ds not in cohorts:continue
        hcount+=1;ev=cohorts[ds];stage=STAGES.index(h['stage']);edges=h['edges'];buckets=[[] for _ in range(len(edges)+1)];defined=[]
        for e in ev:
            x=e['observables'][h['observable']]
            if e['stages'][stage] and x is not None:
                index=bisect.bisect_right(edges,x);buckets[index].append(e);defined.append((e,index))
        total=math.fsum(e['source_weight_pb'] for e,i in defined);persisted=[h['underflow']]+h['bins']+[h['overflow']]
        demand(h['N_defined']==len(defined),'HIST_DEFINED_DENOMINATOR')
        for index,(bucket,b) in enumerate(zip(buckets,persisted)):
            demand(len(bucket)==b['N'],'HIST_BIN_COUNT');bucket_ids={e['source_event_ordinal'] for e in bucket};m=independent_moments([e['source_weight_pb'] if e['source_event_ordinal'] in bucket_ids else 0 for e in ev]);close(b['sumw'],m['sumw'],'HIST_SUMW');close(b['source_variance'],m['variance'],'HIST_FIXED_N_VAR');hchecks+=2
            ratio=math.fsum(e['source_weight_pb'] for e in bucket)/total if total else None;close(b['value'],ratio,'HIST_FRACTION')
            residual=[e['source_weight_pb']*((where==index)-ratio) for e,where in defined] if ratio is not None else None
            if residual is not None:
                residual+= [0.]*(1000-len(residual));variance=independent_moments(residual)['variance']/Decimal(str(total))**2;close(b['variance'],variance,'HIST_BIN_TOTAL_COVARIANCE');hchecks+=1
    return dict(cutflows=stages,eligible_native_jets_bit0_checked=tag_jets,selected_photon_objects=dict(selected_photons),unclassified_native_photon_objects=unknown,stage_region_Decimal70_comparisons=numerical,HF_Decimal70_comparisons=hf_checks,background_histograms_recomputed=hcount,histogram_comparisons=hchecks,raw_source_BR_applied_once=True)


def validate_delivery_boundary(changed,declared):
    demand(set(declared)==EXPECTED_DELIVERY_PATHS,'TAMPERED_DELIVERY_ALLOWLIST')
    demand(set(changed)==EXPECTED_DELIVERY_PATHS,'EXECUTED_SOURCE_CHANGED_BEYOND_DECLARED_DELIVERY')
    return set(declared)


def verify_frozen_publication_blob(base_blob,saved_remote,expected_sha,expected_bytes,current_worktree=None):
    demand(base_blob==saved_remote and hashlib.sha256(base_blob).hexdigest()==expected_sha and len(base_blob)==expected_bytes,'EXACT_SAVED_REMOTE_BASE_BLOB_IDENTITY')
    return current_worktree==base_blob if current_worktree is not None else None


def exact_publication(p9,initial_audit,old_source):
    published=json.loads((p9/'phase9_remote_blob_verification.json').read_text());manifest=json.loads((old_source/'metadata/phase9_source_manifest.json').read_text());demand(published['head']==BASE and published['source_payload_commit']==EXECUTED,'WRONG_PHASE9_RECEIPT_HEAD');source_count=0;delivery_records=[];current_worktree_divergences=[]
    initial=json.loads(initial_audit.read_text());old_head=subprocess.check_output(['git','--no-optional-locks','rev-parse','HEAD'],cwd=old_source,text=True).strip()
    old_index=old_source/'.git/index';old_index_hash=sha(old_index)
    demand(initial['base_revision']==BASE and old_head==BASE and old_index_hash==initial['old_phase9_index_sha256'],'OLD_PHASE9_HEAD_INDEX_CHANGED')
    demand(not subprocess.check_output(['git','--no-optional-locks','status','--porcelain'],cwd=old_source,text=True).strip(),'OLD_PHASE9_CHECKOUT_DIRTY')
    final=json.loads((p9/'FINAL_REPORT.json').read_text())
    changed=subprocess.check_output(['git','diff','--name-only',EXECUTED,BASE],cwd=REPO,text=True).splitlines()
    delivery=validate_delivery_boundary(changed,final['SOURCE_HASH_CLOSURE']['final_report_only_paths'])
    for row in manifest['source_files']:
        revision=BASE if row['path'] in delivery else EXECUTED
        raw=subprocess.check_output(['git','show',revision+':'+row['path']],cwd=REPO);demand(hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['bytes'],'EXACT_DECLARED_REVISION_BLOB_IDENTITY_'+row['path'])
        if revision==EXECUTED:source_count+=1
        else:delivery_records.append(dict(path=row['path'],revision=BASE,sha256=row['sha256'],reason='EXPLICIT_FINAL_REPORT_ONLY_DELIVERY_PATH_NOT_EXECUTABLE_SCIENTIFIC_SOURCE'))
    csvs=[]
    for row in published['records']:
        raw=subprocess.check_output(['git','show',BASE+':'+row['path']],cwd=REPO);saved=(p9/'remote_final_head'/row['path']).read_bytes();local=(REPO/row['path']).read_bytes()
        matches=verify_frozen_publication_blob(raw,saved,row['sha256'],row['bytes'],local)
        demand((old_source/row['path']).read_bytes()==raw,'OLD_PHASE9_CHECKOUT_BLOB_'+row['path'])
        if not matches:current_worktree_divergences.append(dict(path=row['path'],historical_BASE_sha256=row['sha256'],current_Phase10_worktree_sha256=hashlib.sha256(local).hexdigest(),interpretation='NEW_PHASE10_WORKTREE_VARIATION_NOT_A_CHANGE_TO_OLD_PHASE9_CHECKOUT'))
        if row['path'].endswith('.csv'):csvs.append(dict(path=row['path'],sha256=row['sha256'],CRLF=raw.count(b'\r\n'),LF=raw.count(b'\n'),git_blob_bytes_equal=True))
    demand(not any(r['path'].lower().endswith(('.png','.pdf')) for r in published['records']),'UNAPPROVED_FIGURE_IN_RECEIPT')
    return dict(reviewed_base_revision=BASE,executed_source_revision=EXECUTED,executed_source_files_verified=source_count,executed_to_base_changed_paths=changed,final_delivery_manifest_source_records=delivery_records,published_files_verified=len(published['records']),csv_exact_byte_records=csvs,old_phase9_checkout=dict(path=str(old_source),HEAD=old_head,index_sha256=old_index_hash,initial_audit_sha256=sha(initial_audit),clean=True),current_Phase10_worktree_divergences=current_worktree_divergences,scope='BASE_GIT_BLOBS_EQUALS_ACTUAL_SAVED_PHASE9_REMOTE_DOWNLOADS_EQUALS_RECEIPT_HASHES_AND_OLD_PHASE9_CHECKOUT; NO_FRESH_REMOTE_DOWNLOAD',figure_publication_authorized=False)


def validate_historical_histogram_binding(manifest,receipt):
    demand(manifest['numerical_histogram_content_sha256']==receipt['numerical_histogram_content_sha256'],'HISTORICAL_ROOT_CANONICAL_DIGEST_CHANGED')
    defined=[h for h in manifest['histograms'] if h['status']=='DEFINED'];undefined=[h for h in manifest['histograms'] if h['status']=='UNDEFINED_ILL_CONDITIONED_OR_EMPTY_SHAPE']
    demand(len(defined)+len(undefined)==len(manifest['histograms']),'UNKNOWN_HISTOGRAM_DESCRIPTOR_STATUS')
    counts=Counter(h['dimension'] for h in defined)
    demand(set(counts)<={1,2} and counts[1]==receipt['TH1D_count'] and counts[2]==receipt['TH2D_count'] and len(defined)==4668,'HISTORICAL_ROOT_OBJECT_DESCRIPTOR_COUNT')
    demand(all(h['numerical_content_sha256'] is None and 'dimension' not in h for h in undefined),'UNDEFINED_HISTOGRAM_DESCRIPTOR_BECAME_OBJECT')
    return dict(logical_descriptors=len(manifest['histograms']),actual_ROOT_objects=len(defined),undefined_shape_descriptors=len(undefined),TH1D_count=counts[1],TH2D_count=counts[2],canonical_sha256=manifest['numerical_histogram_content_sha256'],fresh_ROOT_readback=False,scope='EXACT_FROZEN_MANIFEST_TO_HISTORICAL_NATIVE_ROOT_DIGEST_AND_OBJECT_COUNTS')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase9-local',type=Path,required=True);p.add_argument('--phase8-local',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--phase9-source',type=Path,default=Path('/home/btu/projects/atlas_hh_phase9_v1'));a=p.parse_args();demand(not a.output.exists(),'PRESERVE_PRIOR_RESULTS_OUTPUT_MUST_BE_FRESH')
    publication=exact_publication(a.phase9_local,a.output.parent/'workspace_initial_audit.json',a.phase9_source)
    native=list(read_jsonl(a.phase9_local/'native/phase9_native_events.jsonl'));details=list(read_jsonl(a.phase9_local/'origins_03/phase9_origins_event_details.jsonl'));demand(len(native)==len(details)==6000,'FULL6000_REQUIRED');cohorts=defaultdict(list);origins=defaultdict(list)
    for n,o in zip(native,details):validate_join(o,n);cohorts[n['dataset_id']].append(n);origins[o['dataset_id']].append(o)
    demand(set(cohorts)=={f'B{i:02}' for i in range(1,7)},'SIX_BACKGROUND_COHORTS_REQUIRED')
    manifest,joins,files,witnesses=source_checks(a.phase8_local,cohorts,origins);arithmetic=arithmetic_checks(a.phase9_local,cohorts,origins,manifest)
    receipt=json.loads((a.phase9_local/'native/phase9_native_readback.json').read_text());demand(receipt['actual_native_background_events']==6000 and receipt['ROOT_version']=='6.40.04','HISTORICAL_NATIVE_RECEIPT')
    for r in joins:demand(r['ordered_source_identity_sha256']==next(x for x in receipt['datasets'] if x['dataset_id']==r['dataset_id'])['ordered_source_identity_sha256'],'ORDERED_SOURCE_IDENTITY_RECEIPT')
    hm=json.loads((a.phase8_local/'phase8_histogram_manifest.json').read_text());hv=json.loads((a.phase8_local/'native/phase8_native_histogram_validation.json').read_text());histogram_binding=validate_historical_histogram_binding(hm,hv)
    checklist=[dict(check=name,status='PASS',evidence_class=kind) for name,kind in [('EXACT_PHASE9_SOURCE_AND_PUBLICATION_BYTES','HISTORICAL_SOURCE_AUDIT'),('FULL_6000_RAW_LHE_HEPMC_INDEX_NATIVE_PERSISTED_JOINS','ACTUAL_EXISTING_DATA_READBACK'),('INDEPENDENT_SELECTION_BIT0_WEIGHTS_REGIONS','ACTUAL_EXISTING_DATA_READBACK'),('SELECTED_RAW_PYTHIA_GRAPH_WITNESSES','ACTUAL_EXISTING_DATA_READBACK'),('INDEPENDENT_RARE_INTERVALS_AND_FIXED_N_STATISTICS','ACTUAL_EXISTING_DATA_READBACK'),('PHOTON_UNKNOWN_AND_MULTI_MOTHER_UNKNOWN_PRESERVED','ACTUAL_EXISTING_DATA_READBACK'),('HISTORICAL_4668_ROOT_CANONICAL_BINDING','HISTORICAL_SOURCE_AUDIT'),('EXACT_CRLF_CSV_GIT_BLOB_IDENTITY','HISTORICAL_SOURCE_AUDIT'),('SCIENTIFIC_PHYSICAL_BLOCKERS_PRESERVED','HISTORICAL_SOURCE_AUDIT')]]
    final=json.loads((a.phase9_local/'FINAL_REPORT.json').read_text());demand(final['PHYSICAL_TOTAL_BACKGROUND']=='BLOCKED' and final['PHYSICAL_SIGNIFICANCE']=='NOT_EVALUATED','PHYSICAL_BLOCKER_REMOVED')
    result=dict(schema_version=1,status='PASS_INDEPENDENT_PHASE9_REVIEW_WITH_LIMITS',reviewer='SEPARATE_PHASE10_IMPLEMENTATION_AGENT',external_independent_human_approval=False,evidence_class='ACTUAL_EXISTING_DATA_READBACK',source_scope=['ACTUAL_EXISTING_DATA_READBACK','HISTORICAL_SOURCE_AUDIT'],actual_existing_source_events_joined=6000,fresh_native_ROOT_loops_in_this_review=0,new_physical_events=0,checklist=checklist,source_joins=joins,input_file_hashes=files,selected_raw_graph_witnesses=witnesses,independent_arithmetic=arithmetic,publication=publication,historical_ROOT_histogram_binding=histogram_binding,limits=['Persisted Phase9 native records are not a fresh ROOT loop. Historical tuple validation is bound by exact original ROOT/index file hashes and original native receipt.','Three selected raw Pythia graph witnesses are independent selected checks, not independent all-event graph reclassification.','Hadron multi-mother endpoints and native flavour boundary ambiguity remain UNKNOWN.','Phase-space overlap does not establish ME/PS double counting or generator exclusivity.','Unclassified photons remain unclassified; no physical fake-rate estimate.','No external independent human signoff is claimed.','No physical total background or significance/CLs/kappa inference is evaluated.'])
    a.output.mkdir(parents=True);write_json(a.output/'phase10a_review_receipt.json',result);print(json.dumps(dict(status=result['status'],events=6000,source_input_files=len(files),checklist=len(checklist))))
if __name__=='__main__':main()

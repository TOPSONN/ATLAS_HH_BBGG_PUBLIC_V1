"""Phase11 source trace and persisted-event diagnostics; no generator/native dispatcher.

All ancestry labels are frozen Phase9 evidence. Arithmetic is independent, uses
original event clusters, and never adds physically overlapping datasets.
"""
from collections import Counter
from decimal import Decimal, localcontext
import csv
import hashlib
import json
import math
from pathlib import Path
import re

STAGES = ('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')
MASS_REGIONS = ('LOW_SIDEBAND','HIGGS_LIKE','HIGH_SIDEBAND','OUTSIDE_MGG','UNDEFINED_MGG')
TAGS = ('TAG_0','TAG_1','TAG_GE2')
HF = ('B01','B02','B03')
FIXTURE_SELECTION = {'photon_subleading_pt':25.,'photon_leading_pt':35.,'photon_max_abs_eta':2.37,'photon_crack_min':1.37,'photon_crack_max':1.52,'jet_min_pt':25.,'jet_max_abs_eta':2.5,'mgg_min':105.,'mgg_max':160.,'btag_mask':1}
ISOLATION_FIELDS = ('IsolationVar','IsolationVarRhoCorr','SumPtCharged','SumPtNeutral','SumPtChargedPU','SumPt')


def demand(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path):
    with Path(path).open('rb') as stream:
        for line in stream:
            demand(len(line) < 16 * 1024**2, 'OVERSIZED_EVENT_ROW')
            yield json.loads(line)


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def write_csv(path, rows):
    demand(bool(rows), 'EMPTY_OUTPUT')
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def covariance(xs, ys):
    """Unbiased fixed-N source-sum covariance; original N, not selected N."""
    demand(len(xs) == len(ys) and len(xs) > 1, 'ORIGINAL_EVENT_COHORT_REQUIRED')
    with localcontext() as context:
        context.prec = 60
        x = [Decimal(str(a)) for a in xs]
        y = [Decimal(str(a)) for a in ys]
        n = Decimal(len(x))
        return float(n / (n - 1) * (sum((a*b for a,b in zip(x,y)), Decimal(0)) - sum(x)*sum(y)/n))


def summarize(mask, weights):
    demand(len(mask) == len(weights) and len(weights) > 1, 'ORIGINAL_EVENT_COHORT_REQUIRED')
    demand(all(math.isfinite(w) for w in weights), 'NONFINITE_SIGNED_WEIGHT')
    x = [w if bool(p) else 0. for p,w in zip(mask,weights)]
    n = len(weights); k = sum(map(bool,mask)); s = math.fsum(x); ss = math.fsum(a*a for a in x)
    variance = covariance(x,x)
    demand(variance >= -1e-25, 'NEGATIVE_VARIANCE')
    return {'original_N':n,'events':k,'sumw_pb':s,'sumw2_pb2':ss,
            'fixed_N_variance_pb2':max(0.,variance),
            'fixed_N_sampling_SE_pb':math.sqrt(max(0.,variance)),
            'ESS_signed_sum':s*s/ss if ss else None,
            'event_acceptance':k/n,
            'zero_one_sided95_acceptance_upper':-math.expm1(math.log(.05)/n) if k == 0 else None,
            'zero_scope':'UNWEIGHTED_IID_PROPOSAL_ACCEPTANCE_NOT_ZERO_PHYSICAL_BACKGROUND',
            'physical_normalization_uncertainty':None,
            'statistical_unit':'ORIGINAL_SOURCE_EVENT_ALL_JETS_CLUSTERED'}


def mass_region(value, config):
    if value is None:
        return config['undefined_region']
    demand(math.isfinite(value), 'NONFINITE_MASS')
    matches=[]
    for region in config['mass_regions']:
        lo = value >= region['min'] if region['min_inclusive'] else value > region['min']
        hi = value <= region['max'] if region['max_inclusive'] else value < region['max']
        if lo and hi:
            matches.append(region['id'])
    demand(len(matches) <= 1, 'OVERLAPPING_FROZEN_MASS_REGIONS')
    return matches[0] if matches else config['outside_region']


def event_features(event):
    h = event['heavy_flavour']; jets = h['jets']
    outgoing = {abs(int(x)) for x in event['hard_outgoing_pdg_ids']}
    expected = 'ME_BOTTOM' if 5 in outgoing else 'ME_CHARM' if 4 in outgoing else 'ME_LIGHT_OR_GLUON'
    demand(expected == h['hard_process_flavour'], 'PERSISTED_ME_FLAVOUR_MISMATCH')
    return {
        'ME_BOTTOM':5 in outgoing,
        'ME_CHARM_WITHOUT_BOTTOM':5 not in outgoing and 4 in outgoing,
        'ME_LIGHT_OR_GLUON':not (outgoing & {4,5}),
        'INITIAL_HEAVY_RECORD':h['heavy_quark_birth_counts'].get('ME_INITIAL_HEAVY_FLAVOUR_RECORD',0)>0,
        'SHOWER_BOTTOM_BIRTH':h['shower_bottom_births']>0,
        'SHOWER_CHARM_BIRTH':h['shower_charm_births']>0,
        'DIRECT_G_TO_HEAVY_PAIR':h['direct_gluon_splitting_count']>0,
        'TERMINAL_B_HADRON':h['terminal_b_hadrons']>0,
        'TERMINAL_C_HADRON':h['terminal_c_hadrons']>0,
        'NATIVE_BOTTOM_JET':any(j['native_flavour']==5 for j in jets),
        'NATIVE_CHARM_JET':any(j['native_flavour']==4 for j in jets),
        'UNKNOWN_QUARK_BIRTH':h['unclassified_quark_births']>0,
        'UNKNOWN_HADRON_ENDPOINT':any(j['sole_hadron_endpoint'].startswith('UNKNOWN') for j in jets),
        'AMBIGUOUS_HADRON_ASSIGNMENT':bool(h['ambiguous_hadron_assignment_ids']),
        'AMBIGUOUS_PYTHIA_TUPLE':(event.get('pythia_mapping') or {}).get('ambiguous_or_missing',0)>0,
    }


def derive_native_stages(event, selection):
    selected=[]
    for photon in sorted(event['photons'],key=lambda p:(-p['pt'],p['index'])):
        eta=abs(photon['eta'])
        accepted=photon['pt']>selection['photon_subleading_pt'] and eta<selection['photon_max_abs_eta'] and not selection['photon_crack_min']<eta<selection['photon_crack_max']
        demand(bool(photon['selected'])==accepted,'PHOTON_ACCEPTANCE_FLAG')
        if accepted:selected.append(photon)
    demand(len(selected)==event['selected_photon_multiplicity'],'SELECTED_PHOTON_MULTIPLICITY')
    pair=len(selected)>=2 and selected[0]['pt']>selection['photon_leading_pt']
    jets=event['eligible_jets']
    demand(all(j['pt']>selection['jet_min_pt'] and abs(j['eta'])<selection['jet_max_abs_eta'] for j in jets),'ELIGIBLE_JET_ACCEPTANCE')
    tags=sum(bool(j['native_btag_bits'] & selection['btag_mask']) for j in jets)
    jet_stage=pair and len(jets)>=2
    tag_stage=jet_stage and tags>=2
    mgg=event['observables']['m_gamma_gamma']
    final=tag_stage and mgg is not None and selection['mgg_min']<=mgg<=selection['mgg_max']
    return [True,bool(pair),bool(jet_stage),bool(tag_stage),bool(final)]


def joined_records(origins, native, selection=None):
    """One-to-one joins; reject duplicates, identity/stage/weight and jet mismatches."""
    if selection is None:
        selection=FIXTURE_SELECTION  # only standalone fixture callers; CLI supplies hash-bound frozen JSON.
    def index(rows, ordinal):
        answer={}
        for row in rows:
            key=(row['dataset_id'],row[ordinal])
            demand(key not in answer,'DUPLICATE_EVENT_KEY')
            answer[key]=row
        return answer
    a=index(origins,'source_event_index');b=index(native,'source_event_ordinal')
    demand(set(a)==set(b),'EVENT_KEY_SET_MISMATCH')
    output=[]
    for key in sorted(a):
        x,y=a[key],b[key]
        for field in ('source_event_sha256','hepmc_event_sha256','stages'):
            demand(x[field]==y[field],'EVENT_JOIN_'+field)
        demand(math.isclose(x['weight_pb'],y['source_weight_pb'],rel_tol=1e-14,abs_tol=1e-18),'WEIGHT_JOIN')
        if key[0] in HF:
            demand(x['model_br_factor']==1.,'HF_SOURCE_BR_MUST_REMAIN_ONE')
        demand(y['model_factor_applied']==0,'SOURCE_WEIGHT_MUST_NOT_HAVE_EXTRA_MODEL_FACTOR')
        stages=y['stages'];demand(len(stages)==5 and stages[0] and all(not stages[i] or stages[i-1] for i in range(1,5)),'NON_NESTED_STAGES')
        if key[0] in HF:
            ja={j['index']:j for j in x['heavy_flavour']['jets']};jb={j['index']:j for j in y['eligible_jets']}
            demand(set(ja)==set(jb),'ELIGIBLE_JET_KEYS')
            for i in ja:
                demand(ja[i]['native_flavour']==jb[i]['flavour'] and ja[i]['tagged']==jb[i]['tagged'],'NATIVE_JET_FIELDS')
                demand(bool(jb[i]['native_btag_bits'] & 1)==bool(jb[i]['tagged']),'OBSERVED_BIT0')
            tags=sum(bool(j['tagged']) for j in jb.values())
            demand(tags==y['native_btag_multiplicity'],'NATIVE_TAG_MULTIPLICITY')
            demand(stages==derive_native_stages(y,selection),'INDEPENDENT_NATIVE_STAGES')
        output.append((x,y))
    return output


def diagnose_events(pairs, config, require_full=True):
    summaries={};counts=[];migration=[];covrows=[]
    for dataset in HF:
        cohort=[p for p in pairs if p[0]['dataset_id']==dataset]
        if require_full:
            demand(len(cohort)==1000,'FULL_1000_EVENT_COHORT_REQUIRED')
            demand([x['source_event_index'] for x,y in cohort]==list(range(1,1001)),'CONTIGUOUS_ORIGINAL_IDS_REQUIRED')
            demand(len({x['source_event_sha256'] for x,y in cohort})==1000,'DUPLICATE_HARD_EVENT_IDENTITY')
        demand(len(cohort)>1,'FULL_ORIGINAL_N_REQUIRED')
        weights=[x['weight_pb'] for x,y in cohort];features=[event_features(x) for x,y in cohort]
        stage_masks={s:[x['stages'][i] for x,y in cohort] for i,s in enumerate(STAGES)}
        vectors={s:[w if p else 0. for w,p in zip(weights,mask)] for s,mask in stage_masks.items()}
        region_labels=[]
        for x,y in cohort:
            tag='TAG_0' if y['native_btag_multiplicity']==0 else 'TAG_1' if y['native_btag_multiplicity']==1 else 'TAG_GE2'
            mass=mass_region(y['observables']['m_gamma_gamma'],config)
            region_labels.append((tag,mass) if x['stages'][2] else ('NOT_ELIGIBLE','NOT_ELIGIBLE'))
        for name in sorted(features[0]):
            mask=[f[name] for f in features]
            vectors['ORIGIN:'+name]=[w if p else 0. for w,p in zip(weights,mask)]
            final=[p and x['stages'][4] for p,(x,y) in zip(mask,cohort)]
            vectors['FINAL_ORIGIN:'+name]=[w if p else 0. for w,p in zip(weights,final)]
            for i,stage in enumerate(STAGES):
                selected=[p and x['stages'][i] for p,(x,y) in zip(mask,cohort)]
                counts.append(dict(dataset_id=dataset,category=name,stage=stage,**summarize(selected,weights)))
            # One source event may enter several origin rows. Never sum the rows.
            for tag in TAGS:
                for mass in MASS_REGIONS:
                    selected=[p and label==(tag,mass) for p,label in zip(mask,region_labels)]
                    migration.append(dict(dataset_id=dataset,origin_flag=name,tag_category=tag,mgg_region=mass,**summarize(selected,weights)))
        region_counts={}
        for tag in TAGS:
            for mass in MASS_REGIONS:
                name=tag+':'+mass;mask=[label==(tag,mass) for label in region_labels]
                vectors['REGION:'+name]=[w if p else 0. for w,p in zip(weights,mask)]
                region_counts[name]=summarize(mask,weights)
        names=sorted(vectors)
        variances={name:covariance(vectors[name],vectors[name]) for name in names}
        # Store upper triangle; reverse pairs are exactly equal by definition.
        for i,a in enumerate(names):
            for b in names[i:]:
                cov=covariance(vectors[a],vectors[b]);va=variances[a];vb=variances[b]
                covrows.append(dict(dataset_id=dataset,vector_a=a,vector_b=b,original_N=len(cohort),fixed_N_covariance_pb2=cov,correlation=cov/math.sqrt(va*vb) if va>0 and vb>0 else None,triangle='UPPER_SYMMETRIC',statistical_unit='ORIGINAL_SOURCE_EVENT_ALL_JETS_CLUSTERED'))
        stage_results={s:summarize(stage_masks[s],weights) for s in STAGES}
        terminal=Counter('PASS_FINAL' if x['stages'][4] else 'FAIL_MGG' if x['stages'][3] else 'FAIL_TAGS' if x['stages'][2] else 'FAIL_JETS' if x['stages'][1] else 'FAIL_PHOTONS' for x,y in cohort)
        demand(sum(terminal.values())==len(cohort),'TERMINAL_PARTITION')
        demand(sum(v['events'] for v in region_counts.values())==sum(stage_masks[STAGES[2]]),'REGION_PARTITION')
        summaries[dataset]={'original_N':len(cohort),'stages':stage_results,'regions':region_counts,'exclusive_terminal_migration':dict(terminal),'origin_flag_counts':{name:sum(f[name] for f in features) for name in sorted(features[0])},'covariance_vectors':len(names),'covariance_formula':'N/(N-1) * [sum_i(x_i*y_i) - sum_i(x_i)*sum_i(y_i)/N]','covariance_scope':'FIXED_ORIGINAL_N_SAMPLING_ONLY; no unknown physical-normalization covariance set to zero','cross_dataset_covariance':None}
    return counts,migration,covrows,summaries


def static_detector_trace(card_path, source_dir):
    """Literal source witnesses, not a Tcl/C++ parser or native execution."""
    card=Path(card_path).read_text();base=Path(source_dir)
    paths={'card':Path(card_path),**{name:base/name for name in ('modules/Efficiency.cc','modules/Isolation.cc','modules/UniqueObjectFinder.cc','modules/TreeWriter.cc','classes/DelphesClasses.h','classes/DelphesClasses.cc')}}
    text={name:p.read_text() for name,p in paths.items()}
    execution=re.search(r'set ExecutionPath\s*\{([^}]+)\}',card,re.S)
    demand(execution is not None,'EXECUTION_PATH_NOT_FOUND')
    sequence=[s.strip() for s in execution.group(1).splitlines() if s.strip()]
    demand(sequence.index('PhotonEfficiency')<sequence.index('PhotonIsolation')<sequence.index('UniqueObjectFinder')<sequence.index('TreeWriter'),'DETECTOR_MODULE_ORDER')
    iso=text['modules/Isolation.cc'];writer=text['modules/TreeWriter.cc']
    assignment=max(iso.index('candidate->'+field+' =') for field in ISOLATION_FIELDS)
    demand(assignment<iso.index('if(fUsePTSum && sum > fPTSumMax) continue;'),'ISOLATION_ASSIGN_BEFORE_REJECTION')
    demand('fOutputArray->Add(candidate);' in iso and 'candidate->Clone' not in iso,'ISOLATION_POINTER_ALIAS')
    demand('fOutputArray->Add(candidate);' in text['modules/Efficiency.cc'],'EFFICIENCY_POINTER_ALIAS')
    pstart=writer.index('void TreeWriter::ProcessPhotons');pend=writer.index('void TreeWriter::ProcessElectrons',pstart)
    photon_writer=writer[pstart:pend]
    demand(all('entry->'+field+' = candidate->'+field+';' in photon_writer for field in ISOLATION_FIELDS),'ISOLATION_WRITER_FIELDS')
    demand('FillParticles(candidate, &entry->Particles);' in photon_writer,'PHOTON_SOURCE_REFS')
    demand('SetUniqueID' not in photon_writer,'NATIVE_PHOTON_UID_ASSUMPTION_CHANGED')
    demand('GetBool("UseUniqueID", false)' in text['modules/UniqueObjectFinder.cc'],'OVERLAP_DEFAULT_CHANGED')
    required=('set CandidateInputArray PhotonEfficiency/photons','set IsolationInputArray EFlowFilter/eflow','set PTRatioMax 0.12','add InputArray PhotonIsolation/photons photons','add Branch UniqueObjectFinder/photons Photon Photon','add Branch UniqueObjectFinder/electrons Electron Electron')
    demand(all(token in card for token in required),'HISTORICAL_CARD_BINDING')
    witness_tokens={'modules/Isolation.cc':['candidate->IsolationVar =','if(fUsePTSum && sum > fPTSumMax) continue;','fOutputArray->Add(candidate);'],'modules/Efficiency.cc':['fOutputArray->Add(candidate);'],'modules/TreeWriter.cc':['void TreeWriter::ProcessPhotons','void TreeWriter::ProcessElectrons','void TreeWriter::ProcessJets','void TreeWriter::FillParticles'],'modules/UniqueObjectFinder.cc':['GetBool("UseUniqueID", false)','candidate->Overlaps(previousCandidate)'],'classes/DelphesClasses.cc':['Bool_t Candidate::Overlaps'] }
    witnesses={name:[{'token':token,'line':text[name][:text[name].index(token)].count('\n')+1} for token in tokens] for name,tokens in witness_tokens.items()}
    return {'status':'SOURCE_SUPPORTED_PARSER_NOT_VALIDATED','execution_sequence':sequence,'source_witness_lines':witnesses,
            'source_identities':{name:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for name,p in paths.items()},
            'historical_photon_chain':['ECal/eflowPhotons','PhotonEfficiency/photons','PhotonIsolation/photons','UniqueObjectFinder/photons','TreeWriter:Photon'],
            'historical_electron_chain':['HCal/eflowTracks','ElectronFilter/electrons','ElectronEfficiency/electrons','ElectronIsolation/electrons','UniqueObjectFinder/electrons','TreeWriter:Electron'],
            'photon_isolation':{'DeltaRMax':.5,'PTMin':.5,'PTRatioMax':.12,'UsePTSum':False,'UseRhoCorrection':True,'RhoInputArray':None,'rho_effectively_zero_without_array':True,'self_exclusion':'candidate UniqueID != isolation UniqueID','components':list(ISOLATION_FIELDS)},
            'pre_isolation_collection_fields_at_treewriter':'ALL_CANDIDATES_MUTATED_BEFORE_REJECTION; not a snapshot before isolation calculation',
            'pointer_alias_source_supported':True,'native_pointer_lifetime_runtime_test_executed':False,
            'post_isolation_before_overlap_available_via_future_branch':True,
            'source_association':'Photon.Particles / Electron.Particle / Jet.Particles native TRefs; closure requires future reviewed readback',
            'overlap_algorithm':'UniqueObjectFinder earlier arrays take precedence; UseUniqueID=false -> recursive Candidate::Overlaps',
            'exact_overlap_graph_persisted_by_standard_treewriter':False,
            'exact_overlap_graph_status':'BLOCKED_REQUIRES_REVIEWED_CANDIDATE_UID_AND_OVERLAP_MAP_WRITER',
            'photon_status_not_calibrated_ID':True,'ATLAS_shower_shapes_available':False,'calibrated_fake_probability':None,
            'PHOTON_FAKE_RATE':'UNKNOWN','new_Delphes_events':0}
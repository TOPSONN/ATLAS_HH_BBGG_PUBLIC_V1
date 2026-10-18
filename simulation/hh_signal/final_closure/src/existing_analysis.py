"""Additive interpretation of actual B/C/D tables; never target-rate rescaling."""
import csv,math,collections
from .contracts import *
from simulation.hh_signal.integration_audit.audit import save

def table(path):
    with Path(path).open(newline='',encoding='utf-8') as stream:return list(csv.DictReader(stream))

def dump(path,rows):
    with Path(path).open('w',newline='',encoding='utf-8') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def derive(out):
    out=Path(out);out.mkdir(exist_ok=True);bindings=input_identity()
    scan=read_json(REPO/'metadata/phase7d_kappa_scan.json')
    rows=table(REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7d_klambda/event_reweights.csv')
    cuts=table(REPO/'metadata/phase7d_signal_background_cutflow.csv')
    hist=table(REPO/'metadata/phase7d_weighted_histograms.csv')
    require(len(rows)==6000,'MISSING_D6000_ROWS')
    groups=collections.defaultdict(dict)
    for row in rows:
        i=int(row['source_event_index']);k=float(row['kappa_lambda'])
        require(k not in groups[i],'DUPLICATE_SOURCE_KAPPA');groups[i][k]=row
    require(set(groups)==set(range(1,1001)),'WRONG_SOURCE_DENOMINATOR')
    ks=[-1.,0.,1.,2.,2.5,5.];columns={k:[] for k in ks}
    selected={int(r['source_event_index']) for r in table(HERE/'evidence/object_pt_features.csv')
        if r['process']=='S01' and r['cut_mgg']=='True'}
    require(len(selected)==143,'FULL1000_SELECTION_IDENTITY_DRIFT')
    for i,g in sorted(groups.items()):
        require(set(g)==set(ks) and len({r['source_event_sha256'] for r in g.values()})==1,'INVALID_SOURCE_LINEAGE')
        for k in ks:
            w=float(g[k]['source_contribution_pb']);factor=scan['model_BR_factor']
            require(math.isclose(float(g[k]['MODEL_BR_ONLY_weight_pb']),w*factor,rel_tol=1e-12,abs_tol=1e-18),'DOUBLE_BR_OR_WEIGHT_DRIFT')
            require(k!=1 or abs(float(g[k]['ratio'])-1)<1e-12,'SM_REWEIGHT_CLOSURE')
            columns[k].append(w)
    benchmark=[];low=[]
    for k in ks:
        name=format(k,'g');old=scan['summaries'][name];col=columns[k]
        s=math.fsum(col);q=math.fsum(x*x for x in col);ess=s*s/q
        require(math.isclose(ess,old['ESS'],rel_tol=1e-11),'INPUT_ESS_DRIFT')
        flags=[r for r in hist if r['process']=='S01' and float(r['kappa_lambda'])==k and r['bin_precision_status'] in ['LOW_ESS','EMPTY']]
        # Retain every original per-bin flag, including its exact vocabulary.
        all_bins=[r for r in hist if r['process']=='S01' and float(r['kappa_lambda'])==k]
        low_bins=[r for r in all_bins if float(r['ESS'])<10]
        for r in low_bins:low.append({key:r[key] for key in ['kappa_lambda','stage','observable','bin','flow','entries','ESS','bin_precision_status',
            'proposal_bin_acceptance_wilson95_low','proposal_bin_acceptance_wilson95_high','zero_proposal_count_one_sided95_upper','interval_scope']})
        benchmark.append({'kappa_lambda':k,'source_PDF':'NNPDF23_LO','alpha_s_order':2,
            'historical_raw_estimator_pb':s,'corrected_CTEQ6L1_estimate_pb':None,'absolute_rate_status':'INCONCLUSIVE_ABSOLUTE_NORMALIZATION',
            'relative_shape_status':'INCONCLUSIVE_REWEIGHTING' if k in [2.5,5.] else 'BOUNDED_DIAGNOSTIC_REQUIRES_PER_BIN_SUPPORT',
            'N_original':1000,'N_selected':old['N_selected_final'],'sum_w':s,'sum_w2':q,'sum_abs_w':math.fsum(abs(x) for x in col),
            'positive_weight_count':sum(x>0 for x in col),'negative_weight_count':sum(x<0 for x in col),'zero_weight_count':sum(x==0 for x in col),
            'input_ESS':ess,'final_ESS':old['final_ESS'],'max_event_fraction':max(abs(x) for x in col)/math.fsum(abs(x) for x in col),
            'final_max_event_fraction':max(abs(col[i-1]) for i in selected)/math.fsum(abs(col[i-1]) for i in selected),
            'bins_with_ESS_lt10':len(low_bins),'numerical_stability':'VALIDATED_EXISTING_ME_ROWS_WITH_CANCELLATION_FLAGS',
            'model_limitations':'LO finite mass; actual C proposal; no cross-PDF conversion, no target independent integral'})
    dump(out/'kappa_benchmarks.csv',benchmark);dump(out/'kappa_low_ESS_bins.csv',low)
    covariance=[]
    for k in ks:
        for l in ks:
            a,b=columns[k],columns[l];ma,mb=math.fsum(a)/1000,math.fsum(b)/1000
            v=1000/999*math.fsum((x-ma)*(y-mb) for x,y in zip(a,b))
            covariance.append({'kappa_a':k,'kappa_b':l,'input_sampling_covariance_pb2':v,'scope':'shared original C1000 events; not independent samples'})
    dump(out/'cross_kappa_input_covariance.csv',covariance)
    selected_covariance=[]
    for k in ks:
        for l in ks:
            a=[w*scan['model_BR_factor'] if i in selected else 0. for i,w in enumerate(columns[k],1)]
            b=[w*scan['model_BR_factor'] if i in selected else 0. for i,w in enumerate(columns[l],1)]
            ma,mb=math.fsum(a)/1000,math.fsum(b)/1000
            selected_covariance.append({'kappa_a':k,'kappa_b':l,
                'selected_model_weight_covariance_pb2':1000/999*math.fsum((x-ma)*(y-mb) for x,y in zip(a,b)),
                'scope':'shared C1000 source and realized detector/tag outcomes; no independent-statistics or physical-rate claim'})
    dump(out/'cross_kappa_selected_covariance.csv',selected_covariance)
    comparison=[]
    for r in cuts:
        if r['process']=='S01' and float(r['kappa_lambda'])!=1:continue
        comparison.append({'process':r['process'],'stage':r['stage'],'N_original':int(r['original_N']),'N_selected':int(r['observed_events']),
            'efficiency':int(r['observed_events'])/int(r['original_N']),'sum_w':float(r['sum_weight_pb']),'sum_w2':float(r['sumw2_pb2']),
            'sum_abs_w':float(r['sum_abs_w_pb']),'positive_weight_count':int(r['N_positive']),'negative_weight_count':int(r['N_negative']),
            'zero_weight_count':int(r['N_zero']),'source_sampling_variance':float(r['source_sampling_variance_pb2']),
            'weight_scope':r['weight_scope'],'absolute_rate_status':'HISTORICAL_MODEL_DIAGNOSTIC_ONLY',
            'zero_survivor_95_upper_proposal_acceptance':1-.05**(1/int(r['original_N'])) if int(r['observed_events'])==0 else None,
            'zero_interval_scope':'one-sided binomial fixed source-proposal probability only; not physical target rate'})
    require({r['process'] for r in comparison}=={'S01','B01','B02','B03','B04','B05','B06'},'MISSING_COMPARISON_PROCESS')
    dump(out/'process_cutflow.csv',comparison)
    shape=[]
    for r in hist:
        if r['process']=='S01' and float(r['kappa_lambda'])!=1:continue
        shape.append({key:r[key] for key in ['process','stage','observable','bin','low','high','flow','entries','sumw','sumw2','sum_abs_w',
            'N_positive','N_negative','N_zero','ESS','UNIT_AREA_SHAPE_ONLY','unit_area_source_sampling_variance','shape_status',
            'missing_pair_events','missing_pair_weight','original_N','weight_scope','bin_precision_status',
            'proposal_bin_acceptance_wilson95_low','proposal_bin_acceptance_wilson95_high','zero_proposal_count_one_sided95_upper','interval_scope']}
            |{'UNIT_AREA_SHAPE':r['UNIT_AREA_SHAPE_ONLY'],'PER_PROCESS_MODEL_WEIGHTED':r['sumw']})
    dump(out/'process_shapes.csv',shape)
    summary={'status':'PASS_ADDITIVE_EXISTING_SOURCE_ANALYSIS_WITH_LIMITS','historical_source':'C1000 NNPDF23 LO/two-loop, seed20261122',
        'source_sha256':scan['source_sha256'],'original_events':1000,'ME_rows':6000,'new_ME_calls':0,'new_integrals':0,'new_events':0,
        'benchmarks':benchmark,'corrected_target':{'status':'NOT_EXECUTED','benchmarks':None},
        'cross_kappa_covariance':'36 centered input RAW covariance and 36 centered selected MODEL_BR_ONLY covariance entries; same 1000 events, never treated independent',
        'BR_factor':scan['model_BR_factor'],'BR_factor_applications':1,'physical_BR_adopted':False,
        'uncertainties':{'integration':'historical within-run estimates only; matched target integration NOT_EXECUTED',
            'event_sampling':'existing event-level covariance; contains realized detector/tag sampling',
            'reweighting':'shared source covariance and ESS, not extra independent samples','tagging':'conditional model variance separate; do not double count observed tags',
            'BR':None,'PDF_scale':None,'detector_systematic':None,'combined_total':None},
        'background_limitations':{'B01_B03':'ME_PS_HEAVY_FLAVOUR_OVERLAP_UNRESOLVED','B04':'MODEL_BR_ONLY',
            'B05':'MODEL_BR_ONLY_SPIN_UNVALIDATED','B06':'ONE_BORN_PHOTON_NO_CALIBRATED_FAKE_RATE'},
        'combined_physical_background':None,'significance':None,'source_bindings':bindings}
    save(out/'existing_source_analysis.json',summary);return summary

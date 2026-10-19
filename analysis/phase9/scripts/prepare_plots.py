#!/usr/bin/env python3
"""Bind twelve ROOT figure recipes to actual frozen Phase8 histogram numerics."""
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
STAGES=('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')
P8_STAGE=dict(zip(STAGES,('INPUT','PHOTONS','JETS','TWO_BTAGS','FINAL_MGG')))
BACKGROUNDS=('B01','B02','B03','B04','B05','B06')
SIGNAL='S01_C1000'
def demand(ok,reason):
    if not ok:raise ValueError(reason)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def rows(p):
    with Path(p).open() as f:return list(csv.DictReader(f))
def close(a,b):return math.isclose(a,b,rel_tol=2e-10,abs_tol=2e-12)
def prepare(data_path,root_csv,hf_csv,output):
    demand(not Path(output).exists(),'FRESH_PLOT_SPEC_REQUIRED');data=load(data_path)
    demand(data['physical_total_background']=='BLOCKED','PHYSICAL_SUM_FORBIDDEN')
    hist={(h['dataset_id'],h['stage'],h['observable']):h for h in data['histograms']}
    native=defaultdict(dict)
    for row in rows(root_csv):
        if row['dimension']=='1' and row['normalization_mode']=='SOURCE_WEIGHTED':native[(row['dataset_id'],row['stage'],row['observable'])][int(row['bin_x'])]=row
    comparisons=0
    for (ds,stage,obs),h in hist.items():
        key=(ds,P8_STAGE[stage],obs);demand(key in native,'MISSING_ACTUAL_ROOT_HISTOGRAM');bins=native[key];hs=[h['underflow']]+h['bins']+[h['overflow']]
        demand(len(bins)==len(hs),'ROOT_BIN_CARDINALITY_CHANGED');total=math.fsum(float(r['content']) for r in bins.values())
        for i,b in enumerate(hs):
            r=bins[i];demand(close(b['sumw'],float(r['content'])) and close(b['sumw2'],float(r['sumw2'])),'ROOT_RAW_HISTOGRAM_NUMERICAL_MISMATCH')
            if total:
                demand(b['value'] is not None and close(b['value'],float(r['content'])/total),'ROOT_NORMALIZED_BIN_MISMATCH');demand(b['value']>=0 and b['variance']>=0,'CURRENT_POSITIVE_COHORT_PLOT_ONLY')
            else:demand(b['value'] is None and b['variance'] is None,'EMPTY_ROOT_SHAPE_NOT_UNDEFINED')
            comparisons+=3
    def series(ds,stage,obs):
        h=hist[ds,stage,obs];s={'label':ds+' (n='+str(h['N_defined'])+')','undefined':h['status'].startswith('UNDEFINED'),'source_histogram_key':[ds,P8_STAGE[stage],obs,'SOURCE_WEIGHTED'],'N_original':h['N_original'],'N_defined':h['N_defined'],'missing':h['missing'],'ESS':h['ESS'],'weight_scope':h['weight_scope'],'flow_denominator':True,'underflow_fraction':h['underflow']['value'],'overflow_fraction':h['overflow']['value']}
        if not s['undefined']:s.update(edges=h['edges'],values=[b['value'] for b in h['bins']],variances=[b['variance'] for b in h['bins']])
        return s
    axes={'m_gamma_gamma':('m_{#gamma#gamma} [GeV]',105,160),'m_bb':('m_{bb} [GeV]',0,500),'m_HH':('m_{HH} [GeV]',0,1500)}
    def panel(dslist,obs,stage,title):
        label,low,high=axes[obs];return {'title':title,'x_title':label,'y_title':'Fraction per bin','xmin':low,'xmax':high,'series':[series(ds,stage,obs) for ds in dslist],'note':'Flows in denominator; display range only'}
    def caption(inputs,stage,errors,weight='Raw-source shapes; flows included; own constant MODEL_BR factor cancels.'):
        return [inputs+' No luminosity scaling.', 'Stage: '+stage+'; frozen Phase8 selection and bin edges; candidate-defined denominators.', 'Weights: '+weight,'Errors: '+errors,'Limits: finite MC; exploratory signal normalization; HF exclusivity / fake and detector calibration unresolved.']
    plots=[]
    def add(id,title,panels,lines):plots.append({'id':id,'title':title,'panels':panels,'caption_lines':lines,'publication_status':'LOCAL_DRAFT','physical_total_background':'BLOCKED'})
    for number,obs,title in [(1,'m_gamma_gamma','Signal diphoton mass'),(2,'m_bb','Signal tagged dijet mass'),(3,'m_HH','Signal reconstructed HH mass')]:
        add(f'phase9_{number:02d}_signal_'+{'m_gamma_gamma':'mgg','m_bb':'mbb','m_HH':'mhh'}[obs],title,[panel([SIGNAL],obs,STAGES[0],SIGNAL+' | historical proposal')],caption('Input: S01_C1000, original N=1000.','INPUT (valid candidates only)','1 SE fixed-original-N delta; bin-total covariance included.'))
    add('phase9_04_signal_b01_mgg','Signal and continuum B01 diphoton shape',[panel([SIGNAL,'B01'],'m_gamma_gamma',STAGES[4],'Separate unit-area shapes')],caption('Inputs: S01_C1000 and B01, N=1000 each.','FINAL_MGG','1 SE fixed-N normalized-bin delta; sparse-bin limits retained.'))
    add('phase9_05_signal_b04_b05_mgg','Signal and separate single-Higgs diphoton shapes',[panel([SIGNAL,'B04','B05'],'m_gamma_gamma',STAGES[4],'B04 and B05 overlaid individually')],caption('Inputs: S01_C1000, B04, B05; N=1000 each.','FINAL_MGG','1 SE fixed-N normalized-bin delta; no summed background.'))
    for number,obs,suffix,title in [(6,'m_bb','mbb','Tagged dijet mass: each background separately'),(7,'m_HH','mhh','Reconstructed HH mass: each background separately')]:
        add(f'phase9_{number:02d}_signal_backgrounds_'+suffix,title,[panel([SIGNAL,ds],obs,STAGES[4],SIGNAL+' vs '+ds) for ds in BACKGROUNDS],caption('Inputs: S01_C1000 and B01-B06, N=1000 each.','FINAL_MGG','1 SE fixed-N normalized-bin delta; B03/B06 empty = undefined, B02 n=1 unsupported.'))
    hf=rows(hf_csv);flags=('HAS_NATIVE_BOTTOM_JET','HAS_NATIVE_CHARM_JET','HAS_DIRECT_G_TO_HEAVY_PAIR','NATIVE_TAGS_0','NATIVE_TAGS_1','NATIVE_TAGS_GE2');labels=('native b','native c','g to QQ','0 tags','1 tag','2+ tags');panels=[]
    for ds in BACKGROUNDS[:3]:
        matches={(r['category']):r for r in hf if r['dataset_id']==ds and r['stage']==STAGES[2] and r['classification_unit']=='SOURCE_EVENT_INDICATOR_NONEXCLUSIVE_ORIGIN_FLAGS'};points=[]
        for i,flag in enumerate(flags):
            row=matches[flag];p=float(row['event_fraction']);lo=float(row['fraction_wilson95_low']);hi=float(row['fraction_wilson95_high']);points.append([i+.5,p,0,0,max(0,p-lo),max(0,hi-p)])
        panels.append({'title':ds+' | photon/jet selection','x_title':'','y_title':'Fraction / original N','xmin':0,'xmax':6,'ymax':.32,'x_labels':labels,'hide_legend':True,'series':[{'label':'Event indicators','points':points,'draw':'P'}],'note':'g to QQ: proven direct heavy pair; tags are a partition'})
    add('phase9_08_heavy_flavour_tags','Heavy-flavour evidence and native bit0 tags',panels,caption('Inputs: B01, B02, B03; N=1000 each.','TWO_JETS; all eligible native jets','Pointwise Wilson 95% acceptance intervals; origin indicators overlap.','Unweighted event indicators; no physical HF sum.'))
    cf=[]
    for ds in ('S01_B100',SIGNAL,*BACKGROUNDS):
        subset=[r for r in data['cutflows'] if r['dataset_id']==ds];points=[[STAGES.index(r['stage'])+.5,r['efficiency'],0,0,r['efficiency']-r['wilson_lower'],r['wilson_upper']-r['efficiency']] for r in subset];cf.append({'label':ds+(' (N=100)' if ds=='S01_B100' else ' (N=1000)'),'points':points})
    add('phase9_09_cutflow_efficiency','Cumulative selection efficiency by source cohort',[{'title':'Eight historical cohorts; no pooling','x_title':'','y_title':'N pass / original N','xmin':0,'xmax':5,'ymax':1.35,'x_labels':['Input','2 photons','2 jets','2+ tags','105-160'],'series':cf}],caption('Inputs: S01_B100 N=100; other seven cohorts N=1000 each.','Cumulative frozen Phase8 baseline','Pointwise Wilson 95%; stages correlated, not independent tests.','Unweighted selection acceptance, including failed source events.'))
    groups=defaultdict(list)
    for row in data['kappa_weight_concentration']:groups[row['kappa_lambda']].append(row)
    ks=[]
    for k,values in sorted(groups.items()):ks.append({'label':'#kappa_{#lambda}='+format(k,'g'),'points':[[0,0,0,0,0,0]]+[[v['rank']/1000,v['cumulative_abs_fraction'],0,0,0,0] for v in values]})
    add('phase9_10_kappa_weight_concentration','Reweighting source concentration (first 10% of ranked events)',[{'title':'Same C1000 sources for every hypothesis','x_title':'Rank / 1000 (largest |w| first)','y_title':'Cumulative fraction of total |w|','xmin':0,'xmax':.10,'ymax':1.05,'series':ks}],caption('Input: S01_C1000 and frozen six-hypothesis reweight CSV; N=1000.','INPUT, ranked within each hypothesis','None: deterministic support diagnostic; hypotheses strongly correlated.','Raw source weight times frozen kappa ratio; denominator is all 1000 |w|.'))
    ess=[{'label':'Final ESS (143 source events pass)','points':[[r['kappa_lambda'],r['final_ESS'],0,0,0,0] for r in data['kappa_summary']],'draw':'LP'}]
    add('phase9_11_kappa_final_ess','Final reweighting effective sample size',[{'title':'#kappa_{#lambda}=2.5 and 5: INCONCLUSIVE_REWEIGHTING','x_title':'#kappa_{#lambda}','y_title':'(sum w)^{2} / sum w^{2}','xmin':-1.3,'xmax':5.3,'series':ess}],caption('Input: S01_C1000 N=1000, frozen ratios; no new generated events.','FINAL_MGG','None: deterministic weight-support metric; not a confidence interval.','Raw source weight times frozen kappa ratio; constant model BR cancels.'))
    rp=[];mass=('LOW','HIGGS','HIGH','OUTSIDE_MGG')
    for ds in BACKGROUNDS:
        ss=[]
        for tag in ('TAG_0','TAG_1','TAG_GE2'):
            rr=[next(r for r in data['regions'] if r['dataset_id']==ds and r['tag_region']==tag and r['mass_region']==m) for m in mass];points=[]
            for i,r in enumerate(rr):
                n=r['N_original'];k=r['N_region'];den=1+1.959963984540054**2/n;p=k/n;c=(p+1.959963984540054**2/(2*n))/den;hh=1.959963984540054*math.sqrt(p*(1-p)/n+1.959963984540054**2/(4*n*n))/den;lo=max(0,c-hh);hi=min(1,c+hh);points.append([i+.5,k,0,0,max(0,k-lo*n),max(0,hi*n-k)])
            ss.append({'label':tag.replace('TAG_','')+' tags','points':points,'draw':'P'})
        rp.append({'title':ds+' | no process sum','x_title':'','y_title':'Observed source events','xmin':0,'xmax':4,'x_labels':['Low','Higgs','High','Outside'],'series':ss,'note':'Undefined mgg: 0 in this eligible cohort'})
    add('phase9_12_background_regions','Background control-region counts in separate panels',rp,caption('Inputs: B01-B06, original N=1000 per source.','TWO_JETS; exclusive tags x frozen mgg bands','Pointwise Wilson 95% x original N; correlated partitions, zero has upper limit.','Raw event counts; no luminosity / physical summed background.'))
    demand(len(plots)==12,'EXACT_TWELVE_REQUIRED');out={'schema_version':1,'physical_total_background':'BLOCKED','physical_significance':'NOT_EVALUATED','figure_publication_authorized':False,'plots':plots,'source_numerics':{'phase9_plot_data_sha256':sha(data_path),'phase8_ROOT_histograms_csv_sha256':sha(root_csv),'heavy_flavour_csv_sha256':sha(hf_csv),'independent_ROOT_numerical_comparisons':comparisons,'histograms_compared':len(hist)},'uncertainty_contract':'Normalized fixed-original-N delta, with bin-total covariance; raw partition counts use pointwise Wilson95; weight support has no invented bands.'}
    Path(output).open('x').write(json.dumps(out,indent=2,allow_nan=False)+'\n');return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--root-csv',type=Path,required=True);p.add_argument('--hf-csv',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=prepare(a.data,a.root_csv,a.hf_csv,a.output);print(json.dumps({'status':'PASS_TWELVE_ROOT_FIGURE_PROVENANCE_RECIPES','numerics':r['source_numerics']}))
"""Parse retained evidence without importing a generator or evaluating an integral."""
import csv,gzip,hashlib,json,math,re
from pathlib import Path

BASE='a0e1539e56c122deb6b36a708a121d2098ad3220'
REPO=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
EVIDENCE=HERE/'evidence'

def require(value,message):
    if not value:raise ValueError(message)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def card_values(text):
    result={}
    for line in text.splitlines():
        code=line.split('!',1)[0].split('#',1)[0]
        match=re.match(r'\s*(.+?)\s*=\s*([A-Za-z][A-Za-z0-9_]*)\s*$',code)
        if match:
            value=match[1].strip().strip("'\"");key=match[2].lower()
            require(key not in result,'DUPLICATE_CARD_PARAMETER:'+key);result[key]=value
    return result

def include_values(text):
    result={}
    for line in text.splitlines():
        if not line.strip() or line[0] in 'cC*!':continue
        match=re.match(r'\s*([A-Za-z]\w*(?:\([0-9]+\))?)\s*=\s*(.*?)\s*$',line)
        if match:
            key=match[1].lower();require(key not in result,'DUPLICATE_INCLUDE_PARAMETER:'+key)
            result[key]=match[2].strip().strip("'\"")
    return result

def pdf_consistency(card,compiled,runtime):
    requested=card['pdlabel'];native=compiled['pdlabel']
    require(runtime in ['cteq6l1','nn23lo1'],'UNKNOWN_RUNTIME_PDF')
    coherent=requested==native==runtime
    return {'status':'PASS' if coherent else 'FAIL_EFFECTIVE_PDF_MISMATCH','requested':requested,
        'compiled_global':native,'compiled_beam_labels':[compiled.get('pdsublabel(1)'),compiled.get('pdsublabel(2)')],
        'native_log_PDF':runtime,'native_density_dispatch':'pdf.f uses global PDLABEL for these proton PDFs',
        'metadata_is_not_runtime_proof':True}

def log_diagnostics(text):
    runtime=re.search(r'New value of alpha_s from PDF\s+(\w+):\s*(\S+)',text)
    iterations=[]
    for match in re.finditer(r'(?m)^\s*(\d+)\s+(\S+)\s+(\S+)\s*\+-\s*(\S+)\s+(\S+)\s*$',text):
        i,mean,absolute,error,eff=match.groups()
        iterations.append({'iteration':int(i),'mean_pb':float(mean),'absolute_mean_pb':float(absolute),
            'printed_error_pb':float(error),'printed_primary_efficiency_percent':float(eff)})
    found=re.findall(r'Found\s+(\d+)\s+events',text);written=re.findall(r'Wrote\s+(\d+)\s+events',text)
    over=re.findall(r'Events wgts > 1:\s+(\d+)',text)
    tail=re.findall(r'% Cross section > 1:\s+(\S+)\s+(\S+)',text)
    sigma=re.findall(r'Std dev\s*=\s*(\S+)',text);chi=re.findall(r'Chi\*\*2 per DoF\.\s*=\s*(\S+)',text)
    require(runtime and iterations and found and written and sigma and chi,'INCOMPLETE_RETAINED_NATIVE_LOG')
    result={'runtime_PDF':runtime[1],'runtime_PDF_alpha_s_MZ':float(runtime[2]),'iterations':iterations,
        'found_candidate_buffer_count':int(found[-1]),'written_partially_unweighted_count':int(written[-1]),
        'overweight_candidates':int(over[-1]) if over else None,
        'tail_excess_internal_weight':float(tail[-1][0]) if tail else None,
        'tail_excess_percent_of_internal_abs_weight':float(tail[-1][1]) if tail else None,
        'last_summary_preinflation_error_pb':float(sigma[-1]),'last_summary_chi2_field':float(chi[-1]),
        'source_scope':'native printed summaries; rounded tokens, not independently seeded measurements',
        'new_integrals':0}
    result['reconstructed_error_after_native_inflation_pb']=float(sigma[-1])*math.sqrt(max(1.,float(chi[-1])))
    result['secondary_candidate_survival_fraction']=result['written_partially_unweighted_count']/result['found_candidate_buffer_count']
    return result

def numeric_log_projection(text):
    pattern=r'Process in group|alpha_s|NNPDFDriver|Grid:|Iteration\s|^\s*\d+\s+0\.|Accuracy:|Finished due|Accumulated results|Std dev|Cross sec|Chi\*\*2|Found\s+\d|Wrote\s+\d|Actual xsec|Correct abs|Event xsec|Events wgts|% Cross section|Results Last|Abs integral|^\s*Status'
    return '\n'.join(line for line in text.splitlines() if re.search(pattern,line))+'\n'

def weighted_support(table,selected,source_records):
    with Path(table).open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    result={}
    require(len(rows)==6000,'EXPECTED_6000_RETAINED_ME_ROWS')
    for k in [-1,0,1,2,2.5,5]:
        group=[r for r in rows if float(r['kappa_lambda'])==k];require(len(group)==1000,'INCOMPLETE_KAPPA_COLUMN')
        weights=[float(r['source_contribution_pb']) for r in group];total=math.fsum(weights);q=math.fsum(w*w for w in weights)
        require(all(math.isfinite(w) and w>=0 for w in weights) and total>0,'UNSUPPORTED_SIGN_OR_NONFINITE_WEIGHT')
        ranked=sorted(zip(weights,group),key=lambda p:p[0],reverse=True);chosen=[w for w,r in zip(weights,group) if selected[int(r['source_event_index'])]]
        st=math.fsum(chosen);sq=math.fsum(w*w for w in chosen);ess=total*total/q;finaless=st*st/sq if sq else 0
        top=[]
        for w,row in ranked[:10]:
            i=int(row['source_event_index']);event=source_records[i-1];require(row['source_event_sha256']==event['hash'],'DOMINANT_EVENT_IDENTITY')
            h=[a+b for a,b in zip(event['particles'][2]['p4'],event['particles'][3]['p4'])]
            mass=math.sqrt(max(0,h[3]*h[3]-sum(v*v for v in h[:3])))
            top.append({'source_index':i,'source_event_sha256':event['hash'],'ratio':float(row['ratio']),
                'normalized_contribution_fraction':w/total,'selected':selected[i],'mHH_GeV':mass,'ALPS':event['alpha_qcd'],'scale_GeV':event['scale']})
        result[str(k)]={'source_events':1000,'input_ESS':ess,'final_ESS':finaless,
            'max_contribution_fraction':ranked[0][0]/total,'top5_fraction':math.fsum(w for w,_ in ranked[:5])/total,
            'top10_fraction':math.fsum(w for w,_ in ranked[:10])/total,'dominant_events':top,
            'status':'INCONCLUSIVE_REWEIGHTING' if ess<100 or ranked[0][0]/total>.1 else 'BOUNDED_PILOT_DIAGNOSTIC',
            'actual_proposal':'effective C NNPDF23_lo_as_0130_qed_mem0, two-loop native alpha_s; NOT intended CTEQ6L1',
            'same_proposal_total_N_for_input_ESS100':math.ceil(1000*100/ess),
            'same_proposal_total_N_for_final_relative_MC_precision':{str(t):math.ceil(1000*max(0,1/finaless-1/1000)/(t*t)) if finaless else None for t in [.2,.1,.05]},
            'planning_scope':'pilot-based scaling only; not a tail-support guarantee or authorization',
            'new_physical_events':0}
    return result

def build_existing(base,output):
    """Copy only bounded read-only numeric evidence; never invoke MG5."""
    base=Path(base);output=Path(output);require(not output.exists(),'PRESERVE_EXISTING_AUDIT_OUTPUT');output.mkdir(parents=True)
    phases={};bindings=[]
    for phase,count in [('7b',100),('7c',1000)]:
        root=base/phase/'source';working=root/'process';records={}
        paths={'reviewed_run':root/'reviewed_run_card.dat','embedded_run':root/'embedded_run_card.dat',
            'embedded_param':root/'embedded_param_card.dat','working_run':working/'Cards/run_card.dat',
            'native_include':working/'Source/run_card.inc','native_run_config':working/'Source/run_config.inc',
            'process_card':working/'Cards/proc_card_mg5.dat','madloop_card':working/'Cards/MadLoopParams.dat'}
        for role,path in paths.items():
            records[role]={'sha256':sha(path),'bytes':path.stat().st_size}
            bindings.append({'role':phase+'/'+role,'path':str(path),'sha256':sha(path)})
        # Exact generated include/settings copies are small and contain no host paths.
        for role in ['native_include','native_run_config']:
            (output/(phase+'_'+role+'.inc')).write_bytes(paths[role].read_bytes())
        logs={};grid_files={}
        for channel in ['G1','G1_1']:
            folder=working/'SubProcesses/P0_gg_hh'/channel;p=folder/'run1_app.log'
            if not p.exists():continue
            text=p.read_text();logs[channel]=log_diagnostics(text)
            logs[channel]['original_log_sha256']=sha(p)
            (output/(phase+'_'+channel+'_numeric.log')).write_text(numeric_log_projection(text))
            bindings.append({'role':phase+'/'+channel+'/native_log','path':str(p),'sha256':sha(p)})
            grid_files[channel]=[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(folder.iterdir())
                if p.is_file() and not p.is_symlink() and p.name in ['ftn25','ftn26','grid_information','results.dat','input_app.txt','moffset.dat']]
        resultfile=working/'SubProcesses/P0_gg_hh/G1/results.dat'
        (output/(phase+'_results.dat')).write_bytes(resultfile.read_bytes())
        (output/(phase+'_input_app.txt')).write_bytes((working/'SubProcesses/P0_gg_hh/G1/input_app.txt').read_bytes())
        source_path=working/'Events'/('hh_'+phase)/'unweighted_events.lhe.gz'
        data=gzip.decompress(source_path.read_bytes())
        init_lines=re.search(rb'<init>\s*(.*?)</init>',data,re.S)[1].splitlines();init=init_lines[0].split()
        sigma,error=map(float,init_lines[1].split()[:2]);require(data.count(b'<event>')==count,'ORIGINAL_SOURCE_EVENT_COUNT')
        bindings.append({'role':phase+'/original_LHE','path':str(source_path),'sha256':sha(source_path)})
        effective=logs['G1']['runtime_PDF'];card=card_values(paths['embedded_run'].read_text());inc=include_values(paths['native_include'].read_text())
        phases[phase]={'source_events':count,'source_LHE_sha256':sha(source_path),'sigma_pb':sigma,'reported_error_pb':error,
            'cards':records,'embedded_card_values':card,'native_include_values':inc,
            'PDF_consistency':pdf_consistency(card,inc,effective),'LHE_init_PDFSUP':[int(init[6]),int(init[7])],
            'native_survey_and_refine':logs,'retained_grid_inventory':grid_files,
            'grid_history_status':'PARTIAL_ONLY; intermediate grids/candidate LHE cleaned by original native workflow',
            'requested_seed':int(card_values(paths['reviewed_run'].read_text())['iseed']),
            'effective_banner_seed':int(card['iseed']),'final_randinit':(working/'SubProcesses/randinit').read_text().strip()}
    require(phases['7b']['cards']['embedded_param']['sha256']==phases['7c']['cards']['embedded_param']['sha256'],'PARAM_CARDS_UNEXPECTEDLY_DIFFER')
    a,b=phases['7b']['native_include_values'],phases['7c']['native_include_values']
    differences={k:{'B':a.get(k),'C':b.get(k)} for k in set(a)|set(b) if a.get(k)!=b.get(k)}
    save(output/'source_audit.json',{'status':'EFFECTIVE_CONFIGURATION_MISMATCH_IDENTIFIED','base_head':BASE,'phases':phases,
        'native_include_differences':differences,'new_physical_events':0,'new_integrals':0,
        'independent_integration_status':'NOT_AUTHORIZED','source_model_scope':'same finite-MT/MB loop model; different effective PDF and alpha_s running',
        'reported_cross_run_error_units':(phases['7c']['sigma_pb']-phases['7b']['sigma_pb'])/math.hypot(phases['7b']['reported_error_pb'],phases['7c']['reported_error_pb']),
        'interpretation':'not a same-integrand across-seed pull; configuration mismatch invalidates that premise; PDF-versus-convergence contributions not quantitatively separated'})
    save(output/'local_bindings.json',bindings)
    return phases

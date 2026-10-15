"""Only card translation and coupling functions on existing LHE scales."""
import argparse,io,logging,subprocess,sys
from .audit import *
from simulation.hh_signal.campaign.common import mg_environment
from simulation.hh_signal.campaign.lhe import load_lhe

def run(output):
    output=Path(output);require(not output.exists(),'PRESERVE_EXISTING_NATIVE_CHECK_OUTPUT');output.mkdir(parents=True)
    cfg=read(REPO/'.local/mg5_installation.json');mg=Path(cfg['mg5_path']);env=mg_environment(cfg)
    base=Path.home()/'simulations/hh_signal_runs/campaign_01'
    source=base/'7c/source/process/Source/alfas_functions.f';program=HERE/'src/retained_alpha_probe.f90'
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran';exe=output/'retained_alpha_probe'
    result=subprocess.run([str(compiler),'-O0','-std=legacy',str(source),str(program),'-o',str(exe)],capture_output=True,text=True,env=env)
    require(result.returncode==0,'PURE_COUPLING_PROBE_COMPILE_FAILED:'+result.stderr)
    proofs=[]
    for phase,n,loops in [('7b',100,1),('7c',1000,2)]:
        path=base/phase/'source/process/Events'/('hh_'+phase)/'unweighted_events.lhe.gz';records=load_lhe(path)['records']
        require(len(records)==n,'RETAINED_SOURCE_COUNT')
        actual=subprocess.run([str(exe)],input=''.join(str(r['scale'])+'\n' for r in records),capture_output=True,text=True,env=env,check=True)
        (output/(phase+'_native_stdout.log')).write_text(actual.stdout)
        numbers=[]
        for line in actual.stdout.splitlines():
            try:values=list(map(float,line.split()))
            except ValueError:continue
            if len(values)==3:numbers.append(values)
        require(len(numbers)==n,'PURE_COUPLING_RESULT_COUNT')
        residuals={str(k):max(abs(v[k]-r['alpha_qcd'])/r['alpha_qcd'] for v,r in zip(numbers,records)) for k in [1,2]}
        require(residuals[str(loops)]<1e-6 and residuals[str(3-loops)]>1e-4,'RUNNING_ORDER_NOT_UNAMBIGUOUS')
        proofs.append({'phase':phase,'retained_source_events':n,'native_running_order_matching_all_retained_ALPS':loops,
            'max_relative_residual_by_order':residuals,'LHE_sha256':sha(path),
            'first10':[{'index':i+1,'scale':records[i]['scale'],'ALPS':records[i]['alpha_qcd'],
                'native1loop':numbers[i][1],'native2loop':numbers[i][2]} for i in range(10)]})
    alpha={'status':'PASS_NATIVE_ALPHA_RUNNING_READ_ONLY_EXISTING_SCALE_AUDIT','native_source_sha256':sha(source),
        'probe_source_sha256':sha(program),'executable_sha256':sha(exe),'results':proofs,'new_integrals':0,'new_physical_events':0,
        'scope':'pure native alpha_s function on all1100 existing scales; no PDF evaluation, ME calls, new kinematics or integrals'}
    save(output/'alpha_running_audit.json',alpha)
    sys.path.insert(0,str(mg));from madgraph.various.banner import RunCardLO
    translations=[];logging.disable(logging.CRITICAL)
    for phase in ['7b','7c']:
        for name in ['reviewed_run_card.dat','embedded_run_card.dat','process/Cards/run_card.dat']:
            card=RunCardLO(str(base/phase/'source'/name));proof={'phase':phase,'card':name,'passes':[]}
            for _ in range(3):
                stream=io.StringIO();card.write_include_file(None,output_file=stream)
                vals=dict(re.findall(r'(?im)^\s*(pdlabel|pdsublabel\([12]\))\s*=\s*([^\n]+)',stream.getvalue()))
                proof['passes'].append({'compiled_PDF_assignments':{k:v.strip().strip("'\"") for k,v in vals.items()},
                    'explicit_PDF_keys_after_write':sorted(k for k in card.user_set if 'pdlabel' in k)})
            translations.append(proof)
    require(any(p['passes'][1]['compiled_PDF_assignments']['pdlabel']=='nn23lo1' for p in translations if p['card']=='process/Cards/run_card.dat'),
        'EXPECTED_REPEAT_WRITER_FAILURE_NOT_REPRODUCED')
    save(output/'card_translation_probe.json',{'status':'REPRODUCED_REPEAT_WRITE_DEFAULT_RESET_WITHOUT_INTEGRATION',
        'native_writer_sha256':sha(mg/'madgraph/various/banner.py'),'cases':translations,'new_integrals':0,'new_physical_events':0,
        'causal_scope':'reproduces a matching failure mode; complete historical in-memory sequence is not retained and not claimed reconstructed'})
    print('PASS_NATIVE_ZERO_INTEGRAL_COUPLING_AND_TRANSLATION_CHECKS',1100)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    allowed=(Path.home()/'simulations/hh_integration_audit').resolve()
    require(args.output.is_absolute() and args.output.resolve().is_relative_to(allowed) and args.output.resolve()!=allowed and
        not any(p.is_symlink() for p in [args.output,*args.output.parents]),'UNSAFE_NATIVE_CHECK_OUTPUT')
    run(args.output)

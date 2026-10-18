"""Three-version scalar/RNG methods only. No HH, sampler or integration dispatch."""
import argparse,hashlib,json,math,os,re,shutil,subprocess
from decimal import Decimal,localcontext
from pathlib import Path
from .overlay import source,restore,sha,PREDICATES
from .diagnostics import parse_record
from ..stop92_diagnostic.overlay import exact_point,candidate
from ..stop92_diagnostic.methods import checked,run,scalars
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'stop92_diagnostic';RUNTIME=HERE.parent/'integration_runtime'
FORBIDDEN=re.compile(r'smatrix|sloopmatrix|madloop|sample_full|gen_mom|x_to_f_arg|dsig|sample_get|sample_put|unwgt|write_event|ntuple',re.I)
IDS=[p[1] for p in PREDICATES]
FROZEN={0:'PASS',1:0,2:0,3:0,4:1,5:'PASS',6:2,7:2,8:3,9:4,10:'PASS',11:2,12:2,13:'PASS',
 14:1,15:'COMPARE_ORIGINAL',16:'PASS',17:'PASS',18:'PASS',19:2,20:2,21:2,22:0,23:2,24:'PASS',25:'NONFINITE',
 26:1,27:'PASS',28:1,29:'NONFINITE',30:'COMPARE_ORIGINAL',31:'NONFINITE',32:1,33:1,34:1,35:'PASS',36:0,
 37:'NONFINITE',38:1,39:'PASS',40:'PASS',41:'NONFINITE',42:'NONFINITE',43:'PASS',44:2,45:'PASS',46:'PASS'}
CORRECTED={**FROZEN,**{i:'PASS' for i in [4,14,28,32,33,34]},**{i:1 for i in [5,23,27,40]},
 **{i:'NONFINITE' for i in [10,11,12,15,16,17,18,19,20,24,30]}}

def prepare(root,compiler,optimization):
    root=Path(root).absolute()
    if root.exists() or '..' in root.parts or any(p.is_symlink() for p in [root,*root.parents]):raise ValueError('FRESH_METHOD_ROOT_REQUIRED')
    if any(n in root.parts for n in ['hh_final_closure','hh_signal_runs']):raise ValueError('HISTORICAL_OR_PRODUCTION_ROOT_FORBIDDEN')
    if optimization not in ['-O0','-O2']:raise ValueError('OPTIMIZATION_NOT_REVIEWED')
    cc=shutil.which(compiler)
    if cc is None or not re.fullmatch(r'(?:[\w]+-)*gfortran(?:-[\d.]+)?',Path(cc).name):raise ValueError('EXISTING_GFORTRAN_REQUIRED')
    for folder in [HERE/'fixtures',OLD/'fixtures']:
        manifest=json.loads((folder/'manifest.json').read_text())
        for row in manifest['files']:
            data=(folder/row['path']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=row['sha256'] or len(data)!=row['bytes']:raise ValueError('FROZEN_SCALAR_FIXTURE_DRIFT')
    corrected=source();original=restore(corrected);diagnostic=candidate(original)
    if (HERE/'native_checks_corrected.f').read_text()!=corrected:raise ValueError('CORRECTED_NATIVE_SOURCE_DRIFT')
    root.mkdir(parents=True)
    (root/'statistics.f90').write_text((RUNTIME/'observers.f90').read_text().split('\nend module',1)[0]+'\nend module\n')
    flags=[cc,optimization,'-w','-std=legacy','-ffixed-line-length-none','-ffree-line-length-none',
        '-I'+str(OLD/'fixtures'),'-J'+str(root)]
    rng=[HERE/'fixtures'/n for n in ['ranmar.f','rmarin.f','ran1.f','xran1.f']]
    binaries={};symbols={}
    for name,text in [('original',original),('diagnostic',diagnostic),('corrected',corrected)]:
        folder=root/name;folder.mkdir();point=folder/'point.f';point.write_text(exact_point(text));exe=folder/'guard_method'
        checked([*flags,root/'statistics.f90',point,HERE/'probe.f',OLD/'fixtures/alfas_functions.f',
            OLD/'fixtures/sumdot.f',OLD/'fixtures/dot.f',*rng,'-o',exe],cwd=root);binaries[name]=exe
    exe=root/'scalar_method'
    checked([*flags,OLD/'fixtures/alfas_functions.f',OLD/'fixtures/sumdot.f',OLD/'fixtures/dot.f',OLD/'scalar_probe.f','-o',exe],cwd=root)
    binaries['scalar']=exe
    for name,exe in binaries.items():
        table=checked(['nm','--defined-only',exe]);names=[s.split()[-1] for s in table.splitlines() if s.split()]
        if any(FORBIDDEN.search(n) for n in names):raise ValueError('ME_SAMPLER_OR_WRITER_SYMBOL_FORBIDDEN')
        if name!='scalar' and not {'ranmar_','rmarin_','ran1_','xran1_'}<=set(names):raise ValueError('REAL_RNG_PROJECTIONS_REQUIRED')
        symbols[name]={'defined_symbols':len(names),'forbidden_ME_sampler_symbols':0,
            'RNG_symbols_present':name!='scalar','local_binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
    return binaries,{'compiler_name':Path(cc).name,'compiler_sha256':hashlib.sha256(Path(cc).read_bytes()).hexdigest(),
        'optimization':optimization,'original_sha256':sha(original),'diagnostic_sha256':sha(diagnostic),'corrected_sha256':sha(corrected),
        'production_libraries_linked':[],'local_only_binaries':symbols}

def records(output):return [s.strip() for s in output.splitlines() if s.strip().startswith('HI_FAILURE')]
def check_expected(result,expected,reader):
    rec=records(result.stdout)
    if expected=='PASS':
        if result.returncode!=0 or rec or 'METHOD_SUCCESS' not in result.stdout:raise ValueError('EXPECTED_METHOD_SUCCESS')
    elif expected=='NONFINITE':
        if result.returncode!=90 or rec!=['HI_FAILURE NONFINITE']:raise ValueError('EXPECTED_NONFINITE_STOP90')
    elif isinstance(expected,int):
        if result.returncode!=92 or len(rec)!=1 or reader(rec[0])['identifier']!=IDS[expected]:raise ValueError('EXPECTED_POINT92_ID')
    elif expected!='COMPARE_ORIGINAL':raise ValueError('UNKNOWN_EXPECTATION')
    return rec

def numeric_inputs(output):
    line=next(s for s in output.splitlines() if s.startswith('METHOD_INPUT'))
    labels=['target_q_GeV','computed_q_GeV','native_scale_GeV','model_MU_R_GeV','q2fact1_GeV2','q2fact2_GeV2','g1','g2','G']
    raw=line.split()[1:]
    if len(raw)!=len(labels):raise ValueError('SCALAR_INPUT_SCHEMA')
    return {key:({'value':float(s),'representation':s} if math.isfinite(float(s)) else {'value':None,'nonfinite':s}) for key,s in zip(labels,raw)}

def matrix(binaries):
    from ..stop92_diagnostic.diagnostics import parse_record as old_parse
    rows=[]
    for case in FROZEN:
        runs={name:run([binaries[name],case,0]) for name in ['original','diagnostic','corrected']}
        old=runs['original'];diag=runs['diagnostic'];new=runs['corrected']
        plain='\n'.join(s for s in diag.stdout.splitlines() if not s.strip().startswith('HI_FAILURE POINT92 '))
        if (old.returncode,old.stdout.strip(),old.stderr.strip())!=(diag.returncode,plain.strip(),diag.stderr.strip()):raise ValueError('DIAGNOSTIC_ONLY_DRIFT')
        # Frozen original emits bare STOP92; diagnose its predicate separately.
        expected=FROZEN[case]
        if isinstance(expected,int):
            if old.returncode!=92:raise ValueError('FROZEN_FAILURE_REPRODUCTION')
        else:check_expected(old,expected,old_parse)
        check_expected(diag,expected,old_parse);new_records=check_expected(new,CORRECTED[case],parse_record)
        state=None
        if new.returncode==0:
            control=run([binaries['corrected'],case,1])
            if control.returncode or control.stdout!=new.stdout or control.stderr!=new.stderr:raise ValueError('GUARD_VS_NO_GUARD_STATE_OR_RNG_DRIFT')
            if old.returncode==0 and (new.stdout,new.stderr)!=(old.stdout,old.stderr):raise ValueError('ORIGINALLY_SUCCESSFUL_STATE_DRIFT')
            rng='\n'.join(s for s in new.stdout.splitlines() if s.startswith('METHOD_RNG'))
            state=next(s for s in new.stdout.splitlines() if s.startswith('METHOD_STATE'))
            if len(rng.splitlines())!=64:raise ValueError('NATIVE_RNG_CONSUMPTION_COUNT')
            state={'rng_draws_per_routine_before_guard':7,'rng_draws_per_routine_after_guard':64,'RANMAR_ran1_xran1_bits_SHA256':hashlib.sha256(rng.encode()).hexdigest(),
                'bookkeeping_and_estimator_bits':state,'guard_equals_no_guard_bitwise':True}
        rows.append({'case':case,'inputs':numeric_inputs(new.stdout),'original_exit':old.returncode,'diagnostic_exit':diag.returncode,'corrected_exit':new.returncode,
            'original_failure_records':records(diag.stdout),'corrected_failure_records':new_records,
            'corrected_parsed':parse_record(new_records[0]) if new_records and new.returncode==92 else None,
            'successful_state':state,'intentional_failure_semantics_change':old.returncode!=new.returncode or records(diag.stdout)!=new_records})
    return rows

def receipts(binaries,root):
    from ..integration_runtime.containment import Budget,StageFailure,supervise
    from ..integration_runtime.contract import NAMED
    out=[]
    for case in [1,5,6,8,9,10,26]:
        work=Path(root)/('partial_'+str(case));work.mkdir();(work/'temporary').mkdir()
        for name in NAMED:(work/name).touch()
        try:supervise([binaries['corrected'],case,0],work,os.environ,'',Budget(work,wall=30,cpu=30),method_only=True)
        except StageFailure as exc:r=exc.receipt
        else:raise ValueError('FATAL_RECORD_MUST_STOP')
        if len(r['records'])!=1 or r['records'][0]!=r['failure'] or r['raw_streams_retained'] or not r['process_group_kill_cleanup']:
            raise ValueError('FIRST_FAILURE_RECEIPT')
        if case!=10:parse_record(r['failure'])
        if any((work/name).stat().st_size for name in NAMED) or list((work/'temporary').iterdir()):raise ValueError('RETENTION_FAILURE')
        out.append({k:r[k] for k in ['exit','execution_class','records','failure','raw_streams_retained','process_group_kill_cleanup']})
    return out

def independent_arithmetic():
    with localcontext() as ctx:
        ctx.prec=70
        # Algebraic scale-prefactor identity; no HH amplitude or loop integral.
        a=Decimal('3.125');L=Decimal(2).ln()
        zero_pole=a+L*0+L*L*0/2
        nonzero_pole=a+L*Decimal('.25')
        if zero_pole!=a or nonzero_pole==a:raise ValueError('LAURENT_SCALE_IDENTITY')
        weights=[Decimal(i%9-4)/16 for i in range(1,65)]
        sw=sum(weights);sw2=sum(w*w for w in weights);mean=sw/64;variance=(sw2/64-mean*mean)/64
        return {'scope':'Artificial Laurent coefficients and fixed bookkeeping weights, not an HH amplitude/integral.',
            'zero_pole_scale_cancellation':True,'nonzero_pole_counterexample_detected':True,
            'independent_sumw':str(sw),'independent_sumw2':str(sw2),'independent_mean':str(mean),'independent_variance_of_mean':str(variance)}

def execute(root,compiler='gfortran',optimization='-O0'):
    binaries,build=prepare(root,compiler,optimization);rows=matrix(binaries);independent=independent_arithmetic()
    # Independent dyadic arithmetic matches the native fixture's sums/means;
    # these are method bookkeeping, never cross sections or an integral.
    for row in rows:
        if row['successful_state']:
            import struct
            fields=row['successful_state']['bookkeeping_and_estimator_bits'].split()
            bits=fields[3:];values=[struct.unpack('>d',bytes.fromhex(s))[0] for s in bits]
            expected=[float(independent[k]) for k in ['independent_sumw','independent_sumw2','independent_mean','independent_variance_of_mean']]
            if [values[0],values[1],values[6],values[7]]!=expected:raise ValueError('INDEPENDENT_BOOKKEEPING_ARITHMETIC')
    return {'status':'PASS_NONPHYSICAL_THREE_VERSION_METHODS','build':build,'matrix':rows,'scalar_probes':scalars(binaries),
        'independent_arithmetic':independent,'partial_receipts':receipts(binaries,root),
        'production_build_executed':False,'physical_restart_executed':False,'new_genuine_ME_calls':0,'new_integrals':0,'new_independent_events':0,
        'genuine_runtime_equivalence':'NOT_EVALUATED_UNTIL_AUTHORIZED'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--compiler',default='gfortran');p.add_argument('--optimization',choices=['O0','O2'],default='O0');args=p.parse_args()
    r=execute(args.output,args.compiler,'-'+args.optimization)
    (Path(args.output)/'method_evidence.json').write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'status':r['status'],'cases':len(r['matrix']),'optimization':r['build']['optimization'],'new_genuine_ME_calls':0}))

"""Build and run fixed, isolated scalar fixtures. No production dispatch route."""
import argparse,hashlib,json,math,os,re,shutil,subprocess
from pathlib import Path
from .overlay import candidate,restore,exact_point,ORIGINAL_SHA256,PREDICATES
from .diagnostics import parse_record,MAX_RECORD_BYTES

HERE=Path(__file__).resolve().parent
RUNTIME=HERE.parent/'integration_runtime'
# No libraries, generated production programs, phase-space maps or ME routines
# are accepted as build inputs. The exact small fixture manifest is checked.
FORBIDDEN=re.compile(r'(?:smatrix|sloopmatrix|madloop|sample_full|x_to_f_arg|dsig|genps_|ranmar|unwgt)',re.I)
CASES={0:'PASS',1:0,2:0,3:0,4:1,5:2,6:2,7:3,8:4,9:'NONFINITE',
       10:'NONFINITE',11:'NONFINITE',12:'PASS',13:2,14:'PASS',15:0,16:1,
       17:2,18:'NONFINITE',19:'NONFINITE',20:'NONFINITE',21:'NONFINITE',22:'COMPARE_ORIGINAL',23:1}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run(argv,**kw):
    return subprocess.run(list(map(str,argv)),capture_output=True,text=True,timeout=30,**kw)
def checked(argv,**kw):
    p=run(argv,**kw)
    if p.returncode:raise ValueError('METHOD_COMMAND_FAILED:'+p.stderr[-2000:])
    return p.stdout

def prepare(root,compiler='gfortran',optimization='-O0'):
    root=Path(root).absolute()
    if root.exists() or any(p.is_symlink() for p in [root,*root.parents]):raise ValueError('FRESH_METHOD_DIRECTORY_REQUIRED')
    if optimization not in ('-O0','-O2'):raise ValueError('METHOD_OPTIMIZATION')
    cc=shutil.which(compiler)
    if cc is None:raise ValueError('EXISTING_GFORTRAN_REQUIRED_NO_INSTALL')
    original=(RUNTIME/'native_checks.f').read_text();proposed=candidate(original)
    if restore(proposed)!=original or (HERE/'native_checks_diagnostic.f').read_text()!=proposed:raise ValueError('OVERLAY_DRIFT')
    manifest=json.loads((HERE/'fixtures/manifest.json').read_text())
    for row in manifest['files']:
        p=HERE/'fixtures'/row['path']
        if sha(p)!=row['sha256'] or p.stat().st_size!=row['bytes']:raise ValueError('SCALAR_FIXTURE_DRIFT')
    root.mkdir(parents=True)
    module=(RUNTIME/'observers.f90').read_text().split('\nend module',1)[0]+'\nend module\n'
    # Use the complete unchanged statistics/finite module; omit all observers
    # with ME, writer or integrator entry points.
    (root/'statistics.f90').write_text(module)
    flags=[cc,optimization,'-w','-std=legacy','-ffixed-line-length-none','-ffree-line-length-none',
           '-I'+str(HERE/'fixtures'),'-J'+str(root)]
    binaries={};symbols={}
    for name,text in [('original',original),('diagnostic',proposed)]:
        folder=root/name;folder.mkdir();(folder/'point.f').write_text(exact_point(text))
        exe=folder/'point_method'
        checked([*flags,root/'statistics.f90',folder/'point.f',HERE/'probe.f','-o',exe],cwd=root)
        binaries[name]=exe
    exe=root/'scalar_method'
    checked([*flags,HERE/'fixtures/alfas_functions.f',HERE/'fixtures/sumdot.f',HERE/'fixtures/dot.f',
             HERE/'scalar_probe.f','-o',exe],cwd=root)
    binaries['scalar']=exe
    for name,exe in binaries.items():
        table=checked(['nm','--defined-only',exe])
        names=[line.split()[-1] for line in table.splitlines() if line.split()]
        if any(FORBIDDEN.search(n) for n in names):raise ValueError('ME_OR_SAMPLER_SYMBOL_FORBIDDEN')
        symbols[name]={'defined_symbols':len(names),'forbidden_ME_sampler_symbols':0,'sha256':sha(exe)}
    return binaries,{'execution_class':'NONPHYSICAL_FIXED_SCALAR_METHODS','optimization':optimization,
        'compiler_name':Path(cc).name,'compiler_sha256':sha(cc),'binaries_local_only':symbols,
        'original_guard_sha256':ORIGINAL_SHA256,'candidate_guard_sha256':hashlib.sha256(proposed.encode()).hexdigest(),
        'exact_original_restoration':True,'linked_production_libraries':[]}

def matrix(binaries):
    rows=[]
    for case,expected in CASES.items():
        old=run([binaries['original'],case]);new=run([binaries['diagnostic'],case])
        records=[s.strip() for s in new.stdout.splitlines() if s.strip().startswith('HI_FAILURE POINT92 ')]
        without='\n'.join(s for s in new.stdout.splitlines() if not s.strip().startswith('HI_FAILURE POINT92 '))
        if (old.returncode,old.stdout.strip(),old.stderr.strip())!=(new.returncode,without.strip(),new.stderr.strip()):
            raise ValueError('ORIGINAL_DIAGNOSTIC_SEMANTICS_DIFFER:'+str(case))
        if expected=='PASS' and new.returncode!=0:raise ValueError('EXPECTED_SUCCESS')
        if expected=='NONFINITE' and (new.returncode!=90 or records):raise ValueError('FINITE_SEMANTICS')
        if isinstance(expected,int) and (new.returncode!=92 or len(records)!=1 or
                parse_record(records[0])['identifier']!=PREDICATES[expected][1]):raise ValueError('BRANCH_MATRIX')
        if new.returncode==92 and len(records)!=1:raise ValueError('ONE_FAILURE_RECORD_REQUIRED')
        if new.returncode==0 and (records or not new.stdout.startswith('METHOD_STATE')):raise ValueError('SUCCESS_OUTPUT')
        rows.append({'case':case,'original_exit':old.returncode,'diagnostic_exit':new.returncode,
            'same_state_and_non_diagnostic_output':True,'diagnostic_record':records[0] if records else None,
            'parsed':parse_record(records[0]) if records else None})
    return rows

def alpha_reference(q):
    # Independent reciprocal-alpha implementation, not NEWTON1 copied code.
    def evolve(a,hi,lo,nf):return 1/(1/a+(33-2*nf)/(6*math.pi)*math.log(lo/hi))
    if q>=4.7:return evolve(.13,91.188,q,5)
    ab=evolve(.13,91.188,4.7,5)
    if q>=1.42:return evolve(ab,4.7,q,4)
    return evolve(evolve(ab,4.7,1.42,4),1.42,q,3)

def scalars(binaries):
    output=checked([binaries['scalar']]);alpha=[];scale=[]
    for row in output.splitlines():
        tag,x,y=row.split();x=float(x);y=float(y)
        if tag=='METHOD_ALPHA':
            ref=alpha_reference(x);guard=1/(1/.13+23/(6*math.pi)*math.log(x/91.188))
            error=abs(y/ref-1)
            if error>1e-12:raise ValueError('INDEPENDENT_PIECEWISE_ALPHA_CHECK')
            if x>=125 and abs(y/guard-1)>1e-10:raise ValueError('PHYSICAL_RANGE_ALPHA_REFERENCE')
            alpha.append({'q_GeV':x,'native_alpha':y,'independent_piecewise_alpha':ref,
                          'relative_residual':error,'fixed_nf5_guard_relative_residual':abs(y/guard-1)})
        elif tag=='METHOD_SCALE':scale.append((x,y))
        else:raise ValueError('UNREVIEWED_SCALAR_RECORD')
    if len(alpha)!=17 or len(scale)!=441:raise ValueError('SCALAR_GRID_COUNT')
    if max(max(t) for t in scale)>1e-10:raise ValueError('SCALE_EXPRESSION_RESIDUAL')
    return {'alpha_probes':alpha,'scale_expression_grid':{'points':len(scale),
        'max_mu_relative_residual':max(t[0] for t in scale),'max_q2_relative_residual':max(t[1] for t in scale),
        'scope':'Deterministic scalar beam pairs 125..6500 GeV; exact SumDot/dot, extracted choice4 expression. No phase-space sampling.'}}

def receipts(binaries,root):
    # Unmodified production supervisor: append the complete single-line record,
    # raise immediately, then kill the group and return a partial receipt.
    from ..integration_runtime.containment import Budget,StageFailure,supervise
    from ..integration_runtime.contract import NAMED
    rows=[]
    for case in [1,4,5,7,8,9]:
        work=Path(root)/('receipt_'+str(case));work.mkdir();(work/'temporary').mkdir()
        for name in NAMED:(work/name).touch()
        try:supervise([binaries['diagnostic'],case],work,os.environ,'',Budget(work,wall=30,cpu=30),method_only=True)
        except StageFailure as error:r=error.receipt
        else:raise ValueError('FAILURE_MUST_REMAIN_FATAL')
        failures=[s for s in r['records'] if s.startswith('HI_FAILURE')]
        if len(failures)!=1 or r['failure']!=failures[0] or r['raw_streams_retained'] or not r['process_group_kill_cleanup']:
            raise ValueError('PARTIAL_FAILURE_RECEIPT')
        if case!=9:parse_record(failures[0])
        if r['execution_class']!='METHOD_ONLY' or any(p.stat().st_size for p in work.iterdir() if p.is_file()) or list((work/'temporary').iterdir()):
            raise ValueError('METHOD_RETENTION')
        rows.append({'case':case,'exit':r['exit'],'failure':r['failure'],'records':r['records'],
            'execution_class':r['execution_class'],'process_group_kill_cleanup':True,'raw_streams_retained':False,
            'no_named_or_physical_output':True})
    return rows

def execute(root,compiler='gfortran',optimization='-O0',supervised=True):
    binaries,build=prepare(root,compiler,optimization)
    return {'status':'PASS_NONPHYSICAL_METHODS_ONLY','build':build,'predicate_matrix':matrix(binaries),
        'scalar_probes':scalars(binaries),'failure_receipts':receipts(binaries,root) if supervised else [],
        'actual_new_ME_calls':0,'actual_new_integrals':0,'actual_new_events':0,
        'genuine_native_equivalence':'NOT_EVALUATED_UNTIL_AUTHORIZED','production_rebuild':'NOT_EXECUTED',
        'max_record_bytes':MAX_RECORD_BYTES}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--compiler',default='gfortran')
    p.add_argument('--optimization',choices=['O0','O2'],default='O0');a=p.parse_args()
    result=execute(a.output,a.compiler,'-'+a.optimization)
    (Path(a.output)/'method_evidence.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'matrix_cases':len(result['predicate_matrix']),
        'supervised_failures':len(result['failure_receipts']),'actual_new_ME_calls':0}))

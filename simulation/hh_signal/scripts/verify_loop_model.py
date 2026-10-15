#!/usr/bin/env python3
"""Read-only installed-model audit or isolated fixed-point numerical validation.

No integration, unweighting, shower, detector, install or physical-event mode.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.hh_signal.contracts import REPO, MG5_COMMIT, read_json, require, sha, write_json

def inspect_installed_model(repo=REPO):
    cfg=read_json(repo/'.local/mg5_installation.json')
    sys.path.insert(0,str(repo/'simulation/mg5/scripts'))
    from installation import verify
    root, identity=verify(cfg)
    expected=read_json(repo/'metadata/phase7a_model_manifest.json')['installed_model_files']
    for name,digest in expected.items():
        require(sha(root/name)==digest, 'STALE_INSTALLED_MODEL_HASH: '+name)
    prefix=Path(cfg['toolchain_prefix'])
    for name in ('python3','x86_64-conda-linux-gnu-gfortran','x86_64-conda-linux-gnu-g++'):
        require((prefix/'bin'/name).is_file(), 'MISSING_EXISTING_COMPILER')
    return {'status':'PASS_RETAINED_MODEL_AND_TOOLCHAIN_FILES','model':'loop_sm',
            'mg5_version':'3.5.16','source_commit':MG5_COMMIT,
            'installed_source_files_checked':len(identity['retained_file_sha256']),
            'model_files_sha256':expected,'software_installed':False,'physical_events':0}

def fixed_point(energy, cosine=0.3, mass=125.0):
    require(energy>2*mass and -1<cosine<1, 'BELOW_PHYSICAL_HH_THRESHOLD_OR_ENDPOINT')
    e=energy/2; p=math.sqrt(e*e-mass*mass)
    x=p*math.sqrt(1-cosine*cosine); z=p*cosine
    return [[e,0.,0.,e],[e,0.,0.,-e],[e,x,0.,z],[e,-x,0.,-z]]

def modify_card(text, block, code, value):
    active=False; count=0; result=[]
    for line in text.splitlines():
        if line.lower().startswith('block '): active=line.split()[1].lower()==block.lower()
        elif line.lower().startswith('decay '): active=False
        if active and re.match(r'\s*'+str(code)+r'\s+',line) and not line.lstrip().startswith('#'):
            # Native LHA reader stores each value in CHARACTER*20. Keep the
            # complete exponent within that field (13 significant digits).
            line=re.sub(r'^(\s*\d+\s+)\S+',lambda m:m[1]+f'{value:.12e}',line);count+=1
        result.append(line)
    require(count==1, 'PARAMETER_CARD_MAPPING_NOT_UNIQUE')
    return '\n'.join(result)+'\n'

def summarize_diagrams(data):
    require(data['noborn']['diagrams']==data['sqrvirt']['diagrams'], 'DIAGRAM_EXPORT_MISMATCH')
    rows=data['noborn']['diagrams'];summary={'box':{},'triangle':{},'born':0,'UVCT':0}
    for d in rows:
        if d['kind']!='loop_diagrams':
            summary['born' if d['kind']=='born_diagrams' else 'UVCT']+=1
            continue
        triple=any(v['pdgs']==[25,25,25] for v in d['vertices']+d['tree_vertices'])
        quarks={abs(p) for v in d['vertices'] for p in v['leg_pdgs'] if abs(p) in (4,5,6)}
        require(len(quarks)==1 and next(iter(quarks)) in (5,6), 'UNEXPECTED_LOOP_FLAVOR')
        flavor=str(next(iter(quarks)));kind='triangle' if triple else 'box'
        summary[kind][flavor]=summary[kind].get(flavor,0)+1
    require(summary['born']==0 and all(summary[k].get(f,0)>0 for k in ('box','triangle') for f in ('5','6')),
            'MISSING_FULL_MASS_BOX_OR_TRIANGLE')
    return summary

def numerical(output, max_hours=2, max_disk_gb=5):
    require(os.name=='posix', 'LINUX_REQUIRED')
    require(math.isfinite(max_hours) and 0<max_hours<=2 and
            math.isfinite(max_disk_gb) and 0<max_disk_gb<=5, 'NUMERICAL_BUDGET_EXCEEDED')
    out=Path(output).expanduser();base=(Path.home()/'.local/share/atlas-hh-phase7a').resolve()
    require(out.is_absolute() and '..' not in out.parts and not out.exists() and not out.is_symlink(),
            'FRESH_NUMERICAL_SCRATCH_REQUIRED')
    require(out.resolve().is_relative_to(base) and out.resolve()!=base, 'UNSAFE_NUMERICAL_SCRATCH')
    for p in out.parents: require(not p.is_symlink(), 'SYMLINK_NUMERICAL_SCRATCH')
    installed=inspect_installed_model()
    cfg=read_json(REPO/'.local/mg5_installation.json');original=Path(cfg['mg5_path']).resolve()
    prefix=Path(cfg['toolchain_prefix']);started=time.monotonic()
    parent=out.parent
    while not parent.exists(): parent=parent.parent
    require(shutil.disk_usage(parent).free>(max_disk_gb+0.5)*1024**3,'DISK_PRECHECK_FAILED')
    out.mkdir(parents=True)
    env=dict(os.environ);env['PATH']=str(prefix/'bin')+os.pathsep+env['PATH']
    env['LD_LIBRARY_PATH']=str(prefix/'lib');env['TMPDIR']=str(out/'tmp');(out/'tmp').mkdir()
    from simulation.new_backgrounds.common import Monitor
    monitor=Monitor(out,{'max_hours':max_hours,'max_disk_gb':max_disk_gb},env=env,
                    started=started,readonly_roots=(original,prefix))
    receipt={'schema_version':1,'scope':'DETERMINISTIC_MATRIX_ELEMENT_ONLY',
             'physical_signal_events':0,'integration_invocations':0,'installed_model':installed,
             'attempt_policy':{'max_hours':max_hours,'max_disk_gib':max_disk_gb,'workers':1}}
    try:
        monitor.install_signals()
        # Private source copy: not a new installation and never published.
        shutil.copytree(original,out/'mg5',symlinks=True,
                        ignore=shutil.ignore_patterns('tests','__pycache__','*.pyc','*.pkl','*.pickle'))
        monitor.check()
        run=lambda argv,cwd,stage:monitor.run_command(argv,cwd,stage)
        run([str(prefix/'bin/python3'),'-B','-O',str(Path(__file__).with_name('mg5_model_adapter.py')),
             str(out/'mg5')],out,'export')
        data=read_json(out/'diagram_inspection.json');receipt['actual_diagram_summary']=summarize_diagrams(data)
        standalone=out/'standalone';work=standalone/'SubProcesses/P0_gg_hh'
        receipt['generated_couplings_sha256']={p.name:sha(p) for p in (standalone/'Source/MODEL').glob('couplings*.f')}
        couplings=(standalone/'Source/MODEL/couplings1.f').read_text()
        require('GC_30 = -6.000000D+00*MDL_COMPLEXI*MDL_LAM*MDL_V' in couplings and
                'GC_37 = -((MDL_COMPLEXI*MDL_YT)/MDL_SQRT__2)' in couplings,
                'ACTUAL_COUPLING_MAPPING_CHANGED')
        generated=(standalone/'SubProcesses/P0_gg_hh/loop_matrix.f').read_text()
        require('DATA IDEN/512/' in generated, 'IDENTICAL_H_SYMMETRY_FACTOR_CHANGED')
        receipt['symmetry_denominator']=512
        shutil.copyfile(REPO/'simulation/hh_signal/src/check_fixed_point.f',work/'check_sa.f')
        # Disable helicity filtering: the only evaluated kinematics are the
        # explicit PS.input points, six deterministic calls each. No RAMBO.
        ml=standalone/'Cards/MadLoopParams.dat';mltext=ml.read_text()
        for key,value in [('MLReductionLib','1'),('HelicityFilterLevel','0'),('WriteOutFilters','.false.'),
                          ('MLStabThres','1.000000d-09'),('CTStabThres','1.000000d-09')]:
            mltext,n=re.subn(r'(#'+key+r'\s*\n)[^\n]+',lambda m:m[1]+value,mltext)
            require(n==1,'MADLOOP_OPTION_MISSING')
        ml.write_text(mltext)
        run(['make','-j1','check'],work,'compile_fixed_driver')
        receipt['executable_sha256']=sha(work/'check')
        original_card=(standalone/'Cards/param_card.dat').read_text()
        cases=[]
        for energy in (250.001,300.,400.,800.):
            for kl in (-1.,0.,1.,2.):
                cases.append((f'e{energy:g}_kl{kl:g}'.replace('.','p').replace('-','m'),energy,kl,173.,173.,False))
        cases += [('repeat',400.,1.,173.,173.,False),('exchange',400.,1.,173.,173.,True),
                  ('mt180_fixed_yukawa',400.,1.,180.,173.,False),
                  ('yt_zero',400.,1.,173.,0.,False),('yt_double',400.,1.,173.,346.,False)]
        results=[]
        for label,energy,kl,mt,ymt,exchange in cases:
            p=fixed_point(energy)
            if exchange: p[2],p[3]=p[3],p[2]
            card=modify_card(original_card,'loop',1,energy/2)
            card=modify_card(card,'mass',6,mt);card=modify_card(card,'yukawa',6,ymt)
            (standalone/'Cards/param_card.dat').write_text(card)
            (work/'PS.input').write_text('\n'.join(' '.join(f'{x:.17e}' for x in v) for v in p)+'\n')
            stage=run([str(work/'check'),str(kl)],work,'eval_'+label)
            text=Path(stage['log_path']).read_text()
            match=re.search(r'PHASE7A_RESULT\s+([^\n]+)',text)
            require(match is not None,'NUMERICAL_RESULT_MISSING')
            fields=match[1].split();values=[float(v.replace('D','E')) for v in fields[:4]]
            require(len(values)==4 and all(math.isfinite(v) for v in values) and values[0]>=0,
                    'NONFINITE_OR_NEGATIVE_ME')
            rc=int(fields[4]);require(rc//100 in (2,3),'UNSTABLE_OR_UNKNOWN_MADLOOP_RETURN_CODE')
            results.append({'label':label,'momenta_E_px_py_pz_gev':p,'mHH_gev':energy,
                'kappa_lambda':kl,'MT_gev':mt,'YUKAWA6_gev':ymt,'mu_R_gev':energy/2,
                'alpha_s_fixed':0.118,'param_card_sha256':sha(standalone/'Cards/param_card.dat'),
                'finite_squared_me':values[0],'single_pole':values[1],'double_pole':values[2],
                'reported_precision':values[3],'return_code':rc,'log_sha256':stage['log_sha256'],
                'calls_at_same_explicit_point':6})
        receipt['evaluations']=results
        receipt.update(check_numerical_results(results))
        receipt['ward_identity']={'status':'NOT_EVALUATED','reason':
            'No reviewed Ward-polarization driver was executed; finiteness and symmetry do not establish gauge invariance.'}
        inspect_installed_model()  # prove original source unchanged
        forbidden=[p for p in out.rglob('*') if p.is_file() and (p.suffix.lower() in ('.lhe','.hepmc3','.root')
                    or any(token in p.name.lower() for token in ('unweighted_events','shower.hepmc')))]
        require(not forbidden,'FORBIDDEN_PHYSICAL_SIGNAL_OUTPUT')
        receipt['forbidden_signal_outputs']=0
        receipt['status']='PASS_BOUNDED_FULL_MT_MB_NUMERICAL_WITH_LIMITS'
    except BaseException as exc:
        receipt['status']='FAILED_NUMERICAL_ATTEMPT'
        receipt['failure_type']=type(exc).__name__
        raise
    finally:
        receipt['resource_metrics']=monitor.metrics()
        monitor.restore_signals()
        write_json(out/'numerical_receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'physical_events':0,'receipt':str(out/'numerical_receipt.json')}))
    return receipt

def check_numerical_results(results):
    by={r['label']:r for r in results};decomp=[]
    close=lambda a,b:abs(a-b)<=1e-7*max(abs(a),abs(b),1e-30)
    for energy in (250.001,300.,400.,800.):
        points=[r for r in results if r['mHH_gev']==energy and r['label'].startswith('e')]
        q={r['kappa_lambda']:r['finite_squared_me'] for r in points}
        require(set(q)=={-1.,0.,1.,2.},'INCOMPLETE_COMMON_POINT_KAPPA_SCAN')
        b=q[0];t=(q[1]+q[-1])/2-b;i=(q[1]-q[-1])/2
        prediction=b+2*i+4*t
        require(t>=0 and close(prediction,q[2]),'KAPPA_QUADRATIC_CLOSURE_FAILED')
        decomp.append({'mHH_gev':energy,'box_squared':b,'triangle_squared':t,
                       'interference_kl1':i,'kl2_prediction':prediction,'kl2_measured':q[2],
                       'relative_closure':abs(prediction-q[2])/max(q[2],1e-30)})
    base=next(r['finite_squared_me'] for r in results if r['mHH_gev']==400 and r['kappa_lambda']==1 and r['label'].startswith('e'))
    require(close(base,by['repeat']['finite_squared_me']),'NONREPRODUCIBLE_ME')
    require(close(base,by['exchange']['finite_squared_me']),'HIGGS_EXCHANGE_FAILED')
    require(not close(base,by['mt180_fixed_yukawa']['finite_squared_me']),'NO_FULL_MT_SENSITIVITY')
    require(not close(base,by['yt_zero']['finite_squared_me']) and
            not close(base,by['yt_double']['finite_squared_me']),'NO_TOP_YUKAWA_SENSITIVITY')
    for row in results:
        p=row['momenta_E_px_py_pz_gev']
        require(max(abs(p[0][i]+p[1][i]-p[2][i]-p[3][i]) for i in range(4))<1e-10,'MOMENTUM_FAILURE')
        require(all(abs(v[0]**2-sum(x*x for x in v[1:])-125**2)<1e-7 for v in p[2:]),'ONSHELL_FAILURE')
    return {'triangle_box_interference':decomp,'numerical_reproducibility':'PASS',
            'higgs_exchange':'PASS','momentum_and_onshell':'PASS',
            'finite_MT_at_fixed_YUKAWA6':'PASS','independent_YUKAWA6_sensitivity':'PASS',
            'threshold':'PHYSICAL_POINTS_ABOVE_250_GEV_BELOW_THRESHOLD_REJECTED_BY_DRIVER',
            'cross_section_pb':'NOT_EVALUATED_UNTIL_REAL_INTEGRATION'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--numerical',action='store_true')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--max-hours',type=float,default=2)
    parser.add_argument('--max-disk-gb',type=float,default=5)
    args=parser.parse_args()
    if args.numerical:
        require(args.output is not None,'NUMERICAL_OUTPUT_REQUIRED')
        numerical(args.output,args.max_hours,args.max_disk_gb)
    else: print(json.dumps(inspect_installed_model(),indent=2))
if __name__=='__main__': main()

"""Build/validate a reviewable integration-only plan. Execution is forbidden."""
import argparse,hashlib,io,json,math,re,sys
from pathlib import Path
from .audit import BASE,HERE,REPO,card_values,include_values,read,require,save,sha

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[910001,910019,910037,910061])
    p.add_argument('--points',type=int,default=250)
    p.add_argument('--iterations',type=int,default=5)
    p.add_argument('--accuracy',type=float,default=.005)
    p.add_argument('--max-hours',type=float,default=4)
    p.add_argument('--validate',action='store_true')
    p.add_argument('--execute',action='store_true',help='always rejected: independent integration requires separate authorization')
    return p

def safe_output(path):
    path=path.expanduser();allowed=Path.home()/'simulations/hh_integration_audit'
    require(path.is_absolute() and '..' not in path.parts and path.resolve().is_relative_to(allowed.resolve()) and
        path.resolve()!=allowed.resolve() and not any(p.is_symlink() for p in [path,*path.parents]),'UNSAFE_PREPARATION_OUTPUT')
    return path

def fresh_native_preview(text,mg):
    # Reconstruct each writer from exact card text. Reusing a mutated writer
    # is specifically tested as a failure mode on the preserved working cards.
    sys.path.insert(0,str(mg))
    from madgraph.various.banner import RunCardLO
    card=RunCardLO(io.StringIO(text));stream=io.StringIO();card.write_include_file(None,output_file=stream)
    preview=stream.getvalue()
    pdf=dict(re.findall(r'(?im)^\s*(pdlabel|pdsublabel\([12]\))\s*=\s*([^\n]+)',preview))
    require(set(pdf)=={'pdlabel','pdsublabel(1)','pdsublabel(2)'} and
        all(value.strip().strip("'\"")=='cteq6l1' for value in pdf.values()),'NATIVE_PREVIEW_PDF_MISMATCH')
    return preview

def validate_plan(out):
    out=Path(out);plan=read(out/'plan.json');manifest=read(out/'manifest.json')
    require(plan['independent_integration_status']=='NOT_AUTHORIZED' and plan['retained_LHE_target']==0 and
        plan['execution_enabled'] is False,'INVALID_AUTHORIZATION_OR_EVENT_TARGET')
    require(len(plan['seeds'])>=4 and len(set(plan['seeds']))==len(plan['seeds']),'INDEPENDENT_SEED_SET_REQUIRED')
    require({p.name for p in out.iterdir()}=={r['path'] for r in manifest['files']}|{'manifest.json'},'UNDECLARED_PLAN_FILE')
    for row in manifest['files']:
        require(Path(row['path']).name==row['path'] and sha(out/row['path'])==row['sha256'],'PLAN_FILE_CHANGED')
    for seed in plan['seeds']:
        card=card_values((out/f'run_{seed}.dat').read_text())
        require(int(card['nevents'])==0 and int(card['iseed'])==seed and card['pdlabel']=='cteq6l1','PLAN_CARD_SCOPE_CHANGED')
        compiled=include_values((out/f'include_preview_{seed}.txt').read_text())
        require(all(compiled.get(k)=='cteq6l1' for k in ['pdlabel','pdsublabel(1)','pdsublabel(2)']) and
            int(compiled['nevents'])==0 and int(compiled['iseed'])==seed,'NATIVE_PREVIEW_SCOPE_CHANGED')
    original=REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7b_100/cards/param_card.dat'
    require(sha(out/'param_card.dat')==plan['param_card_sha256']==sha(original),'PLAN_PARAM_CARD_CHANGED')
    require(plan['runtime_zero_retained_LHE_validation']=='BLOCKED_UNTIL_SEPARATELY_AUTHORIZED_NATIVE_EXECUTION',
        'MUST_NOT_CLAIM_ZERO_RETAINED_RUNTIME_VALIDATED')
    return {'status':'PASS_PREPARATION_AND_MANIFEST_ONLY','independent_integration_status':'NOT_AUTHORIZED',
        'new_integrals':0,'new_physical_events':0,'native_integral_runtime_validation':'NOT_EXECUTED'}

def main(argv=None):
    args=parser().parse_args(argv)
    if args.execute:
        print('NOT_AUTHORIZED: independent integration requires separate explicit authorization.',file=sys.stderr);return 2
    try:
        out=safe_output(args.output)
        if args.validate:
            print(json.dumps(validate_plan(out),indent=2));return 0
        require(not out.exists(),'PRESERVE_EXISTING_PLAN')
        require(len(args.seeds)>=4 and len(set(args.seeds))==len(args.seeds) and
            all(1<=s<=900000000 and s not in [21,20261121,20261122] for s in args.seeds),'INVALID_OR_REUSED_SEEDS')
        require(100<=args.points<=10000 and 5<=args.iterations<=12 and .001<=args.accuracy<=.02 and
            math.isfinite(args.max_hours) and 0<args.max_hours<=4,'UNREVIEWABLE_RESOURCE_OR_ACCURACY_REQUEST')
        # Advisory cost model from the actual B native evaluation timing;
        # the future runtime ceiling remains mandatory even if this is low.
        matrix_calls=len(args.seeds)*args.points*(2**args.iterations-1)*4
        estimated_seconds=matrix_calls*.0625797962206441
        require(estimated_seconds*1.5<=args.max_hours*3600,'PILOT_COST_EXCEEDS_PROPOSED_AGGREGATE_BUDGET')
        cfg=read(REPO/'.local/mg5_installation.json');mg=Path(cfg['mg5_path'])
        require(sha(mg/'madgraph/various/banner.py')==read(HERE/'evidence/native_source_identity.json')['files']['madgraph/various/banner.py'],
            'PINNED_NATIVE_WRITER_CHANGED')
        source=REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7b_100/cards/reviewed_run_card.dat'
        param=REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7b_100/cards/param_card.dat'
        text=source.read_text();out.mkdir(parents=True)
        for seed in args.seeds:
            card=text
            for key,value in [('nevents',0),('iseed',seed)]:
                card,count=re.subn(r'(?m)^([^\n=!]+)(\s*=\s*'+key+r'\b[^\n]*)$',lambda m:str(value)+m[2],card)
                require(count==1,'AMBIGUOUS_PREPARATION_CARD')
            (out/f'run_{seed}.dat').write_text(card)
            previews=[fresh_native_preview(card,mg) for _ in range(3)]
            require(previews[0]==previews[1]==previews[2],'NONDETERMINISTIC_FRESH_NATIVE_WRITER')
            (out/f'include_preview_{seed}.txt').write_text(previews[0])
        (out/'param_card.dat').write_bytes(param.read_bytes())
        plan={'schema_version':1,'base_head':BASE,'status':'PREPARED_NOT_EXECUTED','execution_enabled':False,
            'independent_integration_status':'NOT_AUTHORIZED','retained_LHE_target':0,'seeds':args.seeds,
            'survey_options':{'points':args.points,'iterations':args.iterations,'accuracy':args.accuracy},
            'native_command_design':[f'survey phase7e_seed_{seed} --points={args.points} --iterations={args.iterations} --accuracy={args.accuracy}' for seed in args.seeds],
            'forbidden_commands':['launch','generate_events','refine EVENT_TARGET','combine_events','store_events','shower','detector'],
            'max_aggregate_hours_requested':args.max_hours,'max_concurrent_jobs':1,'max_workers':1,'additional_disk_cap_GiB':5,
            'PDF':'cteq6l1','runtime_expected_alpha_s_MZ':.13,'runtime_expected_alpha_s_running_loops':1,
            'MH_GeV':125,'MT_GeV':173,'MB_GeV':4.7,'muR_muF':'mHH/2','kappa_lambda':1,'kappa_top':1,
            'param_card_sha256':sha(param),'runtime_zero_retained_LHE_validation':'BLOCKED_UNTIL_SEPARATELY_AUTHORIZED_NATIVE_EXECUTION',
            'zero_retained_design':'native survey can create internal weighted candidate scratch; nevents=0 alone is NOT proof. A separately reviewed writer-suppression/retention guard and runtime counters are required before execution.',
            'fresh_process_grid_policy':'independent seeds, fresh workspace and adaptation per replica; never import B/C grids',
            'stopping_policy':'require matched compiled/runtime PDF+alpha_s; >=4 independent replicas; assess between-replica CI, budget doubling and last-iteration drift. Target0.5% per-run and1% between-budget agreement is an assessment goal, never grounds for auto-expansion. Stop at aggregate4h regardless.',
            'budget_extension':'separate authorization required; points/iterations are limits, not guaranteed runtime or convergence',
            'pilot_cost_model':{'native_seconds_per_ME_evaluation':.0625797962206441,'assumed_exact_helicities':4,
                'assumed_iteration_point_growth':2,'estimated_matrix_calls':matrix_calls,'estimated_seconds':estimated_seconds,
                'planning_margin':1.5,'scope':'measured pilot extrapolation, not a runtime guarantee or new integration result'},
            'measurement_policy':'warmup/adaptation versus fixed-grid measurement must be distinguished; no same-grid stages counted independent',
            'paired_actual_NNPDF_arm':'NOT_AUTHORIZED; independently specify PDF/running consistently if a future factorial diagnosis is approved',
            'actual_new_integrals':0,'actual_new_physical_events':0}
        save(out/'plan.json',plan)
        (out/'EXECUTION_NOT_AUTHORIZED.sh').write_text('#!/usr/bin/env bash\nprintf "%s\\n" "NOT_AUTHORIZED: no independent integral has been approved." >&2\nexit 2\n')
        save(out/'manifest.json',{'files':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir())]})
        print(json.dumps(validate_plan(out),indent=2));return 0
    except Exception as exc:
        print('PREPARATION_BLOCKED: '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())

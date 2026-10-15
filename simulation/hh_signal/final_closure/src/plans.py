"""Concrete frozen preparation outputs. Neither mode starts physical tools."""
import re
from .contracts import *
from simulation.hh_signal.integration_audit.audit import save,card_values,include_values

def verify_model_sources(root,rows):
    require(rows,'MISSING_INSTALLED_MODEL_IDENTITY')
    for name,value in rows.items():require(sha(Path(root)/name)==value,'WRONG_MODEL_HASH:'+name)
    return {'status':'PASS_INSTALLED_MODEL_SOURCE_HASHES','files':len(rows)}

def prepare(out,corrected=False):
    out=Path(out);physics=read_json(HERE/'config/physics_contract.json')
    cfg=read_json(REPO/'.local/mg5_installation.json')
    require(cfg['source_commit']==physics['MG5_commit'],'WRONG_INSTALLED_MG5_COMMIT')
    checked=verify_model_sources(Path(cfg['mg5_path']),read_json(REPO/'metadata/phase7a_model_manifest.json')['installed_model_files'])
    writer=read_json(REPO/'simulation/hh_signal/integration_audit/evidence/native_source_identity.json')['files']
    for name,value in writer.items():require(sha(Path(cfg['mg5_path'])/name)==value,'WRONG_NATIVE_MG5_WRITER_SOURCE:'+name)
    if corrected:
        from simulation.hh_signal.config_lock.native import preview
        seed=20261123;text=(REPO/'simulation/hh_signal/config_lock/templates/run_card.dat').read_text()
        for key,value in [('nevents',1000),('iseed',seed)]:
            text,n=re.subn(r'(?m)^([^\n=!]+)(\s*=\s*'+key+r'\b[^\n]*)$',lambda m:str(value)+m[2],text)
            require(n==1,'AMBIGUOUS_CORRECTED_TEMPLATE')
        cards=out/'cards';cards.mkdir();(cards/'reviewed_run_card.dat').write_text(text)
        include=preview(text,Path(cfg['mg5_path']));(cards/'run_card.inc').write_text(include)
        (cards/'param_card.dat').write_bytes((REPO/'simulation/hh_signal/config_lock/templates/param_card.dat').read_bytes())
        values=include_values(include);require(all(values[k]=='cteq6l1' for k in ['pdlabel','pdsublabel(1)','pdsublabel(2)']) and
            values['iseed']==str(seed) and values['nevents']=='1000','CORRECTED_NATIVE_WRITER_DRIFT')
        plan={'status':'PREPARED_NOT_AUTHORIZED','authorization_request':'AUTHORIZE_PHASE7_FINAL_SM_1000',
            'physics':physics,'proposed_seed':seed,'requested_independent_events':1000,
            'ceilings':{'concurrent_sources':1,'generator_workers_max':2,'aggregate_wall_seconds':43200,'additional_disk_bytes':20*1024**3},
            'prerequisites':['Phase7I actual matched integration and scientific gates PASS','separate human approval of exact revision/config/seed/budget/retention'],
            'required_counts':{'source_LHE':1000,'HepMC3':1000,'ROOT':1000},
            'observed_counts':{'source_LHE':None,'HepMC3':None,'ROOT':None},
            'production_backend':'FAIL_CLOSED; no authorized dispatch in this revision','cards_scope':'fresh RunCardLO include only; not compiled runtime or generated-source proof',
            'BR_scope':'MODEL_BR_ONLY; verify missing 2*BRbb*BRgg exactly once; no automatic physical BR adoption',
            'detector_card_sha256':sha(REPO/'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl')}
    else:
        from simulation.hh_signal.matched_integration.contracts import plan_definition
        plan=plan_definition();plan.update(task='PHASE7I_MATCHED_CONFIG_INTEGRATION',authorization_status='NOT_GRANTED',
            authorization_request='AUTHORIZE_PHASE7_FINAL_INTEGRATION_ONLY',physics=physics,
            new_candidate_design='native bookkeeping retained; anonymous formatted scratch, descriptor lease/inode check; old F/G implementation unchanged',
            native_runtime='NOT_EVALUATED; no physical executor unlocked',semantics_gate='METHOD_LEVEL_ONLY_READY_FOR_AUTHORIZED_NATIVE_VALIDATION',
            required_pre_execution_review='exact final revision + H overlay + F effective config gates + resource watchdog + scratch containment; no CLI/env/file grant')
        for replica in plan['replicas']:
            replica['planned_source_id']='MATCHED_CTEQ6L1_LO_SEED_'+str(replica['seed'])
            replica['planned_result_id']=identity({'seed':replica['seed'],'physics':physics,'endpoints':plan['endpoints'],'sources':source_identity()})
            replica['actual_result_id']=None
            folder=out/replica['workspace'];folder.mkdir();cards=folder/'cards';cards.mkdir()
            source=REPO/'simulation/hh_signal/config_lock/evidence'/('seed_'+str(replica['seed']))/'cards'
            for name in ['reviewed_run_card.dat','param_card.dat','run_card.inc','MG5_banner.json']:(cards/name).write_bytes((source/name).read_bytes())
            for stage in ['adaptation','measurement']:
                e=plan['endpoints'][stage];work=folder/stage;work.mkdir()
                (work/'input_app.txt').write_text(f"250 {e['iterations']} {e['iterations']}\n0.0\n{e['grid_mode']}\n1\n0\n1\n")
                (work/'randinit').write_text('r='+str(replica['seed'])+'\n');(work/'iproc.dat').write_text('0\n')
                (work/'moffset.dat').write_text(str(e['moffset'])+'\n')
        from .native_preparation import prepare_native
        plan['actual_native_preparations']=[prepare_native(out/replica['workspace']) for replica in plan['replicas']]
    plan['closure_source_identity']=source_identity();plan['installed_model_source_check']=checked;save(out/'prepared_plan.json',plan)
    return {'status':'PASS_PREPARATION_ONLY','plan_sha256':sha(out/'prepared_plan.json'),'physical_execution':False}

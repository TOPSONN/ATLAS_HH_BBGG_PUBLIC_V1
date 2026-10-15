"""Bounded read-only ROOT object-pT and named-weight regression on old inputs."""
import argparse,json,shlex,subprocess,time
from .contracts import *
from .existing_analysis import dump
from simulation.hh_signal.campaign.common import native_environment,project_public
from simulation.hh_signal.campaign.analysis import backgrounds
from simulation.hh_signal.campaign.statistics import histogram
from simulation.hh_signal.semantics_recovery.runner import command
from simulation.hh_signal.integration_audit.audit import save

def readback(output):
    out=safe_output(output);require(not out.exists(),'PRESERVE_ROOT_READBACK');out.mkdir(parents=True)
    start=time.monotonic();dc,pc,env=native_environment();root=Path(dc['root_prefix'])
    require(dc['root_version']=='6.40.04','ROOT_VERSION_CHANGED')
    require(subprocess.check_output([str(root/'bin/root-config'),'--version'],env=env,text=True,timeout=30).strip()=='6.40.04','ACTUAL_ROOT_VERSION_CHANGED')
    flags=shlex.split(subprocess.check_output([str(root/'bin/root-config'),'--cflags','--libs'],env=env,text=True,timeout=30))
    exe=out/'extract_object_pt';source=HERE/'src/extract_object_pt.cxx'
    command([root/'bin/x86_64-conda-linux-gnu-c++','-std=c++20','-O2','-I'+str(REPO/'simulation/delphes/include'),
        '-I'+str(REPO/'simulation/pythia8/include'),'-I'+str(Path(dc['delphes_prefix'])/'include'),source,
        '-L'+str(Path(dc['delphes_prefix'])/'lib'),'-lDelphes',*flags,'-o',exe],out,env)
    original=Path.home()/'simulations/hh_signal_runs/campaign_01/7c';phase=read_json(original/'phase_receipt.json')
    stage=phase['stages']['full1000'];model=read_json(REPO/'metadata/phase7d_kappa_scan.json')
    signal={'code':'S01','root':Path(stage['artifacts']['ROOT']['path']),'index':Path(stage['artifacts']['input_index']['path']),
        'reco':Path(stage['artifacts']['reco']['path']),'source':Path(phase['source']['path']),'factor':model['model_BR_factor'],
        'scope':'HISTORICAL_C_NNPDF23LO_TWO_LOOP_MODEL_BR_ONLY'}
    data=[];receipts=[];hist=[]
    for stream in [signal,*backgrounds()]:
        code=stream['code'];before={key:sha(stream[key]) for key in ['root','index','reco','source']}
        p=out/(code+'_object_pt.jsonl');result,wall=command([exe,stream['root'],stream['index'],p,1000],out,env)
        rows=[json.loads(s) for s in p.read_text().splitlines()];old=[json.loads(s) for s in stream['reco'].read_text().splitlines()]
        require(len(rows)==len(old)==1000,'FULL_ROOT_READBACK_COUNT')
        for a,b in zip(rows,old):
            require(a['source_event_index']==b['source_event_index'] and
                a['source_event_sha256']==b.get('source_event_sha256',b.get('source_event_hash')),'ROOT_SOURCE_IDENTITY')
            cp=a['N_photons']>=2 and a['photon_pt_1']>35
            cj=cp and a['N_jets']>=2;ct=cj and a['N_btags']>=2
            require([cp,cj,ct]==[b['cut_photons'],b['cut_jets'],b['cut_two_btags']],'FROZEN_OBJECT_SELECTION_DRIFT')
            require(abs(a['source_contribution_pb']-b['source_contribution_pb'])<1e-12,'SOURCE_WEIGHT_TRANSFER_DRIFT')
            a.update(process=code,cut_mgg=b['cut_mgg'],model_weight_pb=a['source_contribution_pb']*stream['factor'],
                original_N=1000,weight_scope=stream['scope']);data.append(a)
        require(before=={key:sha(stream[key]) for key in before},'ROOT_READ_ONLY_INPUT_MODIFIED')
        receipts.append({'process':code,'events':1000,'input_sha256':before,'derived_pt_sha256':sha(p),
            'all_named_weight_values_verified':True,'frozen_object_selection_verified':True,'stdout':result.stdout,'wall_seconds':wall,
            'ROOT_version':'6.40.04','language':'C++20','new_detector_events':0})
        for field in ['photon_pt_1','photon_pt_2','jet_pt_1','jet_pt_2']:
            for stage in ['00_input','04_mgg_105_160']:
                active=[stage=='00_input' or r['cut_mgg'] for r in rows]
                values=[r[field] for r in rows];weights=[r['model_weight_pb'] if yes else 0. for r,yes in zip(rows,active)]
                for row in histogram(values,weights,[0,25,35,50,75,100,150,200,300,500,1000],1000,active):
                    row.update(process=code,observable=field,stage=stage,weight_scope=stream['scope'],
                        UNIT_AREA_SHAPE=row['UNIT_AREA_SHAPE_ONLY'],PER_PROCESS_MODEL_WEIGHTED=row['sumw']);hist.append(row)
    dump(out/'object_pt_features.csv',data);dump(out/'object_pt_shapes.csv',hist)
    receipt={'status':'PASS_READ_ONLY_EXISTING_7000_ROOT_ENTRIES','streams':receipts,'new_ME_calls':0,'new_integrals':0,
        'new_physical_events':0,'source_sha256':sha(source),'executable_sha256':sha(exe),
        'wall_seconds':time.monotonic()-start,'final_cut_uses':'unchanged prior actual mass selection; object cuts independently rechecked',
        'all_input_sources_unchanged':True}
    save(out/'readback.json',project_public(receipt));return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    result=readback(a.output);print(json.dumps({'status':result['status'],'new_physical_events':0}))

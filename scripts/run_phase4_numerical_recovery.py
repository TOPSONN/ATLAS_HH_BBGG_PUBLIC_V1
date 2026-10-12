#!/usr/bin/env python3
"""Run pinned DATA/MC numerical regressions into new local-only directories."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--history',type=Path,required=True)
    a=p.parse_args()
    assert os.environ.get('CONDA_DEFAULT_ENV')=='atlas-hh-root'
    assert subprocess.check_output(['root-config','--version'],text=True).strip()=='6.40.04'
    assert subprocess.check_output(['root-config','--cxxstandard'],text=True).strip()=='20'
    for app in ('phase4_numerical_regression','phase4_mc_reconstruction','phase2_diagnostics','phase3_cutflow'):
        assert (a.build_dir/app).is_file(),app
    subprocess.run(['python','scripts/freeze_phase4_history.py',str(a.history),'--verify'],check=True)
    history=json.loads(a.history.read_text())
    a.output_dir.mkdir(parents=True,exist_ok=False)
    commands=[]
    def run(arguments,name):
        log=a.output_dir/(name+'.log')
        with log.open('x') as f:
            process=subprocess.run([str(arg) for arg in arguments],stdout=f,stderr=subprocess.STDOUT,
                                   env={**os.environ,'DISPLAY':''})
        commands.append({'argv':[str(arg) for arg in arguments],'exit':process.returncode,
                         'log':str(log),'log_sha256':sha(log)})
        print(name,'ACTUAL_EXIT',process.returncode,flush=True)
        return process.returncode
    config=Path('metadata/phase3_selection_config.ini')
    for entry in history['inputs']:
        source=Path(entry['path']);assert source.stat().st_size==entry['bytes'] and sha(source)==entry['sha256']
        label=entry['sample'];mode='DATA' if label=='DATA93915' else 'MC';dsid=0 if mode=='DATA' else int(label)
        out=a.output_dir/label;out.mkdir()
        start,end=entry['range']
        run([a.build_dir/'phase4_numerical_regression',mode,source,out/'regression',dsid,start,end,1,'PROVISIONAL',config],label+'_regression')
        if mode=='DATA':
            exit_code=run([a.build_dir/'phase2_diagnostics',source,out/'phase2',start,end,1,'PROVISIONAL'],label+'_phase2')
            if exit_code==0:
                run([a.build_dir/'phase3_cutflow',out/'phase2/events.csv',config,out/'phase3','PROVISIONAL'],label+'_phase3')
        else:
            run([a.build_dir/'phase4_mc_reconstruction',source,out/'reconstruction',dsid,start,end,1,'PROVISIONAL',config],label+'_mc_driver')
        assert sha(source)==entry['sha256'],label
    subprocess.run(['python','scripts/freeze_phase4_history.py',str(a.history),'--verify'],check=True)
    manifest={'task':'PHASE4_NUMERICAL_RECOVERY_AND_DATA_MC_REGRESSION_V2','base_commit':history['base_commit'],
              'build_dir':str(a.build_dir),'input_files':history['inputs'],'commands':commands,
              'new_dataset_downloads':0,'source_sha256_lf':{},
              'figure_status':'LOCAL_DRAFT','figure_note':'legacy DATA drivers create local PNGs only; no visual QA/user approval implied',
              'all_processes_exit_zero':all(c['exit']==0 for c in commands)}
    for path in sorted(list(Path('include').glob('*.h'))+list(Path('src').glob('*.cxx'))+[Path('apps/phase4_numerical_regression.cxx'),Path('apps/phase4_mc_reconstruction.cxx'),Path('apps/phase2_diagnostics.cxx'),Path('apps/phase3_cutflow.cxx'),Path('CMakeLists.txt')]):
        manifest['source_sha256_lf'][str(path)]=hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    with (a.output_dir/'execution.json').open('x') as f:f.write(json.dumps(manifest,indent=2)+'\n')
    if not manifest['all_processes_exit_zero']:raise SystemExit(1)

if __name__=='__main__':main()

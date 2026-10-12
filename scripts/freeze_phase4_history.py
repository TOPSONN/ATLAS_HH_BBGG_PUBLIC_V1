#!/usr/bin/env python3
"""Hash historical scientific artifacts and verified cached inputs without mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE='d823593b42889592897263819138170470f4dc47'

def sha(path,lf=False):
    content=path.read_bytes()
    return hashlib.sha256(content.replace(b'\r\n',b'\n') if lf else content).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.verify:
        evidence=json.loads(args.output.read_text())
        for entry in evidence['tracked_scientific']:
            assert sha(Path(entry['path']),True)==entry['sha256_lf'],entry['path']
        for entry in evidence['local_historical']+evidence['inputs']:
            path=Path(entry['path'])
            assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],entry['path']
        print('PASS historical tracked/local/input preservation; files='+str(sum(len(evidence[k]) for k in ('tracked_scientific','local_historical','inputs'))))
        return
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'metadata','note','reports'],text=True).splitlines()
    tracked=[]
    for name in names:
        original=subprocess.check_output(['git','show',BASE+':'+name]).replace(b'\r\n',b'\n')
        expected=hashlib.sha256(original).hexdigest()
        assert sha(Path(name),True)==expected,name
        tracked.append({'path':name,'sha256_lf':expected})
    local=[]
    for directory in ('outputs/phase2_20261010T092242Z','outputs/phase3_20261010T092242Z','outputs/phase4_v1'):
        for path in sorted(Path(directory).rglob('*')):
            if path.is_file():local.append({'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)})
    data=Path('.local/phase1_access_20261009/ODEO_FEB2025_v0_GamGam_data15_periodD.GamGam.root')
    assert data.stat().st_size==17541818
    assert sha(data)=='01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7'
    inputs=[{'sample':'DATA93915','path':str(data),'bytes':data.stat().st_size,'sha256':sha(data),'range':[100,63195]}]
    ledger=json.loads(Path('metadata/phase4_transfer_ledger.json').read_text())
    for sample in ledger['files']:
        path=Path('.local/phase4_access_20261011')/sample['filename']
        assert path.stat().st_size==sample['size'] and sha(path)==sample['sha256']
        inputs.append({'sample':str(sample['dsid']),'path':str(path),'bytes':path.stat().st_size,'sha256':sample['sha256'],'range':[100,10000]})
    evidence={'base_commit':BASE,'tracked_scientific':tracked,'local_historical':local,'inputs':inputs,
              'scope':'original Phase2/3/4 science plus original DATA/MC cached files; source may be changed additively',
              'new_dataset_downloads':0}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as output:output.write(json.dumps(evidence,indent=2)+'\n')
    print('PASS frozen history: tracked='+str(len(tracked))+' local='+str(len(local))+' inputs=4')

if __name__=='__main__':main()

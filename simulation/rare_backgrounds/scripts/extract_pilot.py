#!/usr/bin/env python3
"""Extract bounded numerical pilot records from verified existing native ROOT.

The ROOT files and all historical sidecars are opened read-only. A preceding
compatible native readback receipt is required; no physics sample is generated.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[3]


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):
            digest.update(chunk)
    return digest.hexdigest()


def require(test,reason):
    if not test:
        raise ValueError(reason)


def validated_receipt(path):
    before = sha(path)
    verification = json.loads(path.read_text())
    require(verification['status']=='PASS' and verification['verification_scope']=='actual_ROOT_native_source_card_full_file_hash',
            'fresh native full-source verification missing')
    samples = verification['samples']
    require(len(samples)==3 and {row['process'] for row in samples}=={'bbgg','ccgg','jjgg'},
            'exactly three unique full1000 process receipts required')
    require(all(row['status']=='PASS' and row['events']==row['normalization_denominator']==1000 for row in samples),
            'incomplete full1000 process receipt')
    return verification, before


def check_source_index(directory, verified):
    require(sha(directory/'input_event_index.jsonl') == verified['source_files_sha256']['input_event_index.jsonl'],
            'exact source identity/weight index checksum mismatch')


def compact(profile,directory,verified,output,library):
    check_source_index(directory, verified)
    import ROOT
    require(ROOT.gROOT.GetVersion()=='6.40.04' and ROOT.gSystem.Load(str(library))>=0,'native ROOT/dictionary mismatch')
    before=sha(directory/'detector.root')
    require(before==verified['root_sha256'] and sha(directory/'reco_events.jsonl')==verified['native_scientific_content_sha256'],
            'verified ROOT/native reco bytes changed')
    root=ROOT.TFile.Open(str(directory/'detector.root'),'READ')
    require(root and not root.IsZombie() and not root.TestBit(ROOT.TFile.kRecovered),'invalid/recovered ROOT')
    tree=root.Get('Delphes')
    require(tree and tree.GetEntries()==1000,'not full1000 actual ROOT')
    target=output/(profile+'.jsonl')
    n=0
    with (directory/'reco_events.jsonl').open() as native_stream, (directory/'input_event_index.jsonl').open() as source_stream, target.open('x') as dest:
        for raw,source_raw in zip(native_stream,source_stream,strict=True):
            old=json.loads(raw)
            source=json.loads(source_raw,parse_float=Decimal)
            require(tree.GetEntry(n)>0,'ROOT physical entry read failed')
            require(tree.Event.GetEntriesFast()==1 and int(tree.Event.At(0).Number)==old['native_event_number']==n+1,'ROOT source event number mismatch')
            identity=source['source_identity']
            require(int(identity['source_event_index'])==old['source_event_index']==n+1 and
                    identity['source_event_content_hash']==old['source_event_hash'] and source['source_total_events']==1000,
                    'original source identity/count mismatch')
            require(float(source['weights'][0])==old['source_contribution_pb'],'nominal high-precision source weight mismatch')
            row={key:value for key,value in old.items() if key not in ('photons','jets','genjets','native_physics_branches_sha256')}
            row['source_count']=1000
            row['source_contribution_pb']=str(source['weights'][0])
            for branch,key in [('Photon','photons'),('Jet','jets')]:
                objects=getattr(tree,branch)
                require(objects.GetEntriesFast()==len(old[key]),'ROOT/native object count mismatch')
                values=[]
                for index in range(objects.GetEntriesFast()):
                    obj=objects.At(index)
                    value={'index':index,'pt':float(obj.PT),'eta':float(obj.Eta),'phi':float(obj.Phi),
                           'mass':0.0 if branch=='Photon' else float(obj.Mass),
                           'stored_energy':float(obj.E) if branch=='Photon' else float(obj.P4().E()),
                           'flavor':0 if branch=='Photon' else int(obj.Flavor),
                           'btag':0 if branch=='Photon' else int(obj.BTag)}
                    require(all(math.isfinite(value[k]) for k in ('pt','eta','phi','mass','stored_energy')),'nonfinite actual ROOT object')
                    values.append(value)
                values.sort(key=lambda v:(-v['pt'],v['index']))
                for actual,prior in zip(values,old[key],strict=True):
                    for field in ('index','pt','eta','phi','mass','flavor','btag'):
                        require(actual[field]==prior[field],'independent ROOT field disagrees with native source: '+field)
                    require(math.isclose(actual['stored_energy'],prior['stored_energy'],rel_tol=2e-13,abs_tol=2e-10),'energy-convention readback differs')
                row[key]=values
            dest.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')
            n+=1
    root.Close()
    check_source_index(directory, verified)
    require(n==1000 and sha(directory/'detector.root')==before and
            sha(directory/'reco_events.jsonl')==verified['native_scientific_content_sha256'],'input mutation/count mismatch')
    require(target.stat().st_size<=5*1024**2,'compact numerical evidence exceeds5MiB cap')
    binding={'schema_version':1,'process':profile,'events':1000,'normalization_denominator':1000,
             'verification_status':'PASS','verification_scope':'actual_ROOT_native_source_card_full_file_hash',
             'root_sha256':before,'native_report_sha256':verified['native_report_sha256'],
             'native_scientific_content_sha256':verified['native_scientific_content_sha256'],'reco_sha256':sha(target),
             'canonical_card_sha256':verified['canonical_card_sha256'],'runtime_card_sha256':verified['runtime_card_sha256'],
             'source_mg5_sha256':verified['source_mg5_sha256'],'source_pythia_run_id':verified['source_pythia_run_id'],
             'input_generator_cross_section_pb':verified['input_generator_cross_section_pb'],
             'numerical_input':str(target.relative_to(REPO)) if target.is_relative_to(REPO) else target.name,
             'transformation':'actual ROOT photon/jet fields independently extracted; original exact source identity/decimal nominal weight and validated cut scalars retained; GenJet omitted; no ROOT rewrite',
             'new_independent_physics_events':0}
    binding_target=output/(profile+'_binding.json')
    binding_target.write_text(json.dumps(binding,indent=2,allow_nan=False)+'\n')
    return {'process':profile,'input':binding['numerical_input'],'events':n,'bytes':target.stat().st_size,'sha256':binding['reco_sha256'],
            'ROOT_physical_readback':'PASS','binding_sha256':sha(binding_target)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    for profile in ('bbgg','ccgg','jjgg'):
        parser.add_argument('--'+profile+'-run',type=Path,default=Path.home()/('simulations/delphes_runs/stage_c_'+profile+'_1000'))
    args=parser.parse_args()
    args.output=args.output.resolve()
    require(not args.output.exists(),'numerical evidence output exists; no overwrite')
    verification, receipt_hash = validated_receipt(args.verification)
    args.output.mkdir(parents=True)
    samples=[compact(v['process'],getattr(args,v['process']+'_run'),v,args.output,args.library) for v in verification['samples']]
    actual = sum(sample['events'] for sample in samples)
    require(actual == 3000 and sha(args.verification) == receipt_hash, 'verification receipt changed / physical extraction count mismatch')
    receipt={'schema_version':1,'status':'PASS','verification_receipt_sha256':receipt_hash,
             'actual_ROOT_entries_read':actual,'samples':samples,'new_physics_events_generated':0}
    (args.output/'extraction.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,KeyError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        raise SystemExit(1)

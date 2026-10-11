#!/usr/bin/env python3
"""Numerical consistency of disjoint MC unit probes; exact producer stays unknown."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def audit(path, dsid):
    with path.open() as input_file:
        rows=list(csv.DictReader(input_file))
    if any(r['collection'] not in ('photon','jet') for r in rows):
        raise ValueError('Unexpected probe collection')
    if {int(r['entry']) for r in rows} != set(range(10,100)):
        raise ValueError('Required reco probe is precisely entries [10,100)')
    for entry in range(10,100):
        for kind in ('photon','jet'):
            objects=[r for r in rows if r['collection']==kind and int(r['entry'])==entry]
            if not objects:
                if kind=='photon': raise ValueError('Missing photon collection')
                continue  # Zero-jet rows are absent; native reader checks counts.
            counts={int(r['count']) for r in objects}
            if len(counts)!=1: raise ValueError('Inconsistent collection count')
            count=counts.pop()
            if count<=0 or count>100000 or len(objects)!=count or {int(r['index']) for r in objects}!=set(range(count)):
                raise ValueError('Incomplete/duplicate probe collection indices')
    statistics={}
    for kind in ('photon','jet'):
        selected=[r for r in rows if r['collection']==kind]
        if not selected: raise ValueError('Empty collection: '+kind)
        stats={}
        for field in ('pt','eta','phi','energy'):
            values=[float(r[field]) for r in selected]
            if not all(math.isfinite(v) for v in values): raise ValueError('Nonfinite probe')
            stats[field]={'min':min(values),'max':max(values)}
        relative=[]
        for r in selected:
            pt,eta,phi,energy=(float(r[field]) for field in ('pt','eta','phi','energy'))
            if pt<0 or energy<0 or energy>13000 or abs(phi)>math.pi+1e-5:
                raise ValueError('Contradicted proposed GeV/radian interpretation')
            momentum=pt*math.cosh(eta)
            relative.append((energy*energy-momentum*momentum)/max(energy*energy,momentum*momentum,1.))
        stats['minimum_relative_mass2']=min(relative)
        stats['negative_small_mass2_objects']=sum(v<0 for v in relative)
        if min(relative)<-1e-5: raise ValueError('Contradicted energy/momentum consistency')
        statistics[kind]=stats
    photons={i:sorted([float(r['pt']) for r in rows if r['collection']=='photon' and int(r['entry'])==i],reverse=True) for i in range(10,100)}
    if not all(len(v)>=2 and v[1]>=25-1e-4 for v in photons.values()):
        raise ValueError('Probe contradicts the published GamGam two-photon >=25 GeV skim')
    return {'dsid':dsid,'record':93922,'native_container':'ROOT::VecOps::RVec<float>',
            'numerical_consistency':'PASS','unit_status':'PROVISIONAL','scale_to_gev':1,
            'eta':'dimensionless','phi':'radians PROVISIONAL','range':[10,100],'unique_probe_entries':90,
            'probe_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'statistics':statistics,
            'exact_producer_association':'UNKNOWN','calibration_validation':'UNKNOWN',
            'evidence':'actual native reco values + published >=25GeV skim; later producer is supporting context only',
            'reference':'https://opendata.cern.ch/record/93922'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('probe',type=Path);parser.add_argument('dsid',type=int);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Refusing to replace unit evidence')
    result=audit(args.probe,args.dsid)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f"DSID={args.dsid} RECO_UNIT_NUMERICS=PASS UNIT_STATUS=PROVISIONAL")


if __name__=='__main__': main()

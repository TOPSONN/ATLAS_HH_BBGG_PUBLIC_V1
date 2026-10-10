"""Interpret bounded raw numeric evidence; never assert exact FEB2025 provenance."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('probe',type=Path); p.add_argument('output_csv',type=Path); p.add_argument('summary',type=Path)
    a=p.parse_args()
    if a.output_csv.exists() or a.summary.exists(): raise RuntimeError('Refusing to replace unit evidence')
    with a.probe.open() as f:
        rows=list(csv.DictReader(f))
    if not rows or {int(r['entry']) for r in rows} != set(range(10,100)):
        raise RuntimeError('Probe must cover precisely the new Stage A range [10,100)')
    groups={k:[r for r in rows if r['collection']==k] for k in ['photon','jet']}
    statistics={}
    for kind,values in groups.items():
        stats={}
        for field in ['pt','eta','phi','energy']:
            numbers=[float(r[field]) for r in values]
            if not numbers or not all(math.isfinite(v) for v in numbers): raise RuntimeError('Nonfinite/empty probe collection')
            stats[field]={'min':min(numbers),'max':max(numbers)}
        relative=[]
        for r in values:
            pt,eta,phi,energy=(float(r[f]) for f in ['pt','eta','phi','energy'])
            if pt<0 or energy<0 or abs(phi)>math.pi+1e-5 or energy>13000:
                raise RuntimeError('CONTRADICTED proposed GeV/radian interpretation')
            momentum=pt*math.cosh(eta)
            relative.append((energy*energy-momentum*momentum)/max(energy*energy,momentum*momentum,1.))
        stats['min_relative_mass2']=min(relative)
        stats['negative_roundoff_objects']=sum(v<0 for v in relative)
        if min(relative)<-1e-5: raise RuntimeError('CONTRADICTED energy/momentum consistency')
        statistics[kind]=stats
    # 25 GeV documented GamGam threshold plus pT on an O(10..1000) raw scale
    # supports GeV against a MeV hypothesis. It does not identify the producer.
    leading_by_entry={i:sorted([float(r['pt']) for r in groups['photon'] if int(r['entry'])==i],reverse=True) for i in range(10,100)}
    if not all(len(v)>=2 and v[1]>=25-1e-4 for v in leading_by_entry.values()):
        raise RuntimeError('Published GamGam >=2 photons >=25 GeV cannot be reconciled with the proposed scale')
    if min(v[1] for v in leading_by_entry.values())>10000: raise RuntimeError('MeV/GeV ambiguity remains UNKNOWN')
    photon='https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FPhotonInfo.cxx/raw?ref=v1.0.0'
    jet='https://gitlab.cern.ch/api/v4/projects/atlas-outreach-data-tools%2Fphyslitetoopendata/repository/files/Root%2FJetInfo.cxx/raw?ref=v1.0.0'
    hashes={'photon':'9a59853da9c04a428d1990320b680940480bdf723f8d299689ac3bc26e7a8569','jet':'01325c175a93676dea65f7946dba486bcc1e84c6f7168e694bc3362c05f3a5b5'}
    fields=['branch','unit','classification','scale_to_gev','physical_type','dictionary_url','versioned_producer_url','source_sha256','observed_min','observed_max','evidence_scope','limitation']
    a.output_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.output_csv.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); writer.writeheader()
        for kind in ['photon','jet']:
            for suffix,field in [('pt','pt'),('eta','eta'),('phi','phi'),('e','energy')]:
                writer.writerow({'branch':kind+'_'+suffix,'unit':{'pt':'GeV','energy':'GeV','eta':'dimensionless','phi':'radian'}[field],
                                 'classification':'PROVISIONAL','scale_to_gev':'1' if field in ['pt','energy'] else 'not_applicable',
                                 'physical_type':'ROOT::VecOps::RVec<float>','dictionary_url':'https://opendata.atlas.cern/docs/data/for_education/13TeV25_details',
                                 'versioned_producer_url':photon if kind=='photon' else jet,'source_sha256':hashes[kind],
                                 'observed_min':statistics[kind][field]['min'],'observed_max':statistics[kind][field]['max'],
                                 'evidence_scope':'record93915;entries10:100;native RVec;independent E^2-pt^2*cosh(eta)^2',
                                 'limitation':'v1.0.0 is later than FEB2025_v0; exact-production association UNKNOWN; numeric consistency does not establish calibration'})
    summary={'status':'PROVISIONAL','scale_to_gev':1,'angles':'PROVISIONAL radians; eta dimensionless',
             'probe_start':10,'probe_end_exclusive':100,'unique_probe_entries':90,
             'probe_sha256':hashlib.sha256(a.probe.read_bytes()).hexdigest(),'statistics':statistics,
             'producer_match':'UNKNOWN','real_diagnostics_permitted':'exploratory only; staged consistency gates required'}
    a.summary.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()

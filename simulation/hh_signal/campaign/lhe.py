"""Independent production/decayed LHE parsing, real records only."""
from __future__ import annotations
import gzip, hashlib, json, math, re
from pathlib import Path
from decimal import Decimal
from .common import require,sha,save_json

NUMBER=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?'
def real(token):
    v=float(token.replace('D','E').replace('d','e'));require(math.isfinite(v),'NONFINITE_LHE_NUMBER');return v

def load_lhe(path):
    path=Path(path);data=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
    require(len(data)<64*1024**2 and data.rstrip().endswith(b'</LesHouchesEvents>'),'LHE_ENVELOPE_OR_SIZE')
    header=data[:data.index(b'<event>')]
    blocks=re.findall(rb'<event>\s*\n.*?</event>',data,re.S)
    require(blocks and len(blocks)<=1100,'WRONG_OR_EXCESS_LHE_COUNT')
    init=re.search(rb'<init>\s*\n(.*?)</init>',header,re.S);require(init is not None,'MISSING_LHE_INIT')
    lines=[s.split(b'#')[0].strip() for s in init[1].splitlines() if s.split(b'#')[0].strip()]
    first=lines[0].decode().split();require(len(first)==10,'WRONG_INIT_FIELDS')
    require([int(first[0]),int(first[1])]==[2212,2212] and real(first[2])==real(first[3])==6500,'WRONG_BEAMS')
    require(int(first[8])==-4 and int(first[9])==1,'UNREVIEWED_WEIGHT_STRATEGY_OR_SUBPROCESS_COUNT')
    process=lines[1].decode().split();require(len(process)==4,'WRONG_PROCESS_INIT')
    sigma,error=map(real,process[:2]);require(sigma>0 and error>=0,'INVALID_INTEGRATED_CROSS_SECTION')
    records=[]
    for ordinal,block in enumerate(blocks,1):
        lines=[s.strip() for s in block.decode().splitlines()[1:] if s.strip() and not s.lstrip().startswith('#')]
        tok=lines[0].split();require(len(tok)==6,'WRONG_EVENT_HEADER')
        n=int(tok[0]);require(n in (4,8),'UNEXPECTED_HARD_PARTICLE_COUNT')
        particles=[]
        for line in lines[1:n+1]:
            f=line.split();require(len(f)==13,'WRONG_PARTICLE_FIELDS')
            particles.append({'id':int(f[0]),'status':int(f[1]),'m1':int(f[2]),'m2':int(f[3]),'c1':int(f[4]),'c2':int(f[5]),
               'p4':[real(x) for x in f[6:10]],'mass':real(f[10]),'tau':real(f[11]),'spin':real(f[12]),'line':line})
        records.append({'index':ordinal,'hash':hashlib.sha256(block).hexdigest(),'block':block,'nup':n,'process':int(tok[1]),
           'weight':real(tok[2]),'scale':real(tok[3]),'alpha_qed':real(tok[4]),'alpha_qcd':real(tok[5]),'particles':particles,
           'header_line':lines[0]})
    return {'header':header,'records':records,'sigma_pb':sigma,'error_pb':error,'idwtup':-4,
            'sha256':sha(path),'bytes':path.stat().st_size,'decompressed_sha256':hashlib.sha256(data).hexdigest(),
            'raw':data,'init':first}

def mass2(p):return p[3]*p[3]-sum(x*x for x in p[:3])
def validate_production(source,expected,seed=None,model_width=None):
    require(len(source['records'])==expected,'ACTUAL_LHE_COUNT_MISMATCH')
    text=source['header'].decode()
    require('loop_sm' in text and 'noborn=QCD' in text.replace(' ',''),'WRONG_LHE_MODEL_OR_PROCESS_CARD')
    max_closure=0.;max_shell=0.;max_scale=0.
    for r in source['records']:
        ps=r['particles'];require(r['nup']==4 and [p['id'] for p in ps]==[21,21,25,25], 'NOT_GENUINE_GG_HH')
        require([p['status'] for p in ps]==[-1,-1,1,1], 'WRONG_PRODUCTION_STATUSES')
        require(all(p['m1']==p['m2']==0 for p in ps[:2]) and all(p['m1']==1 and p['m2']==2 for p in ps[2:]),'WRONG_HARD_ANCESTRY')
        require(all(p['c1']==p['c2']==0 for p in ps[2:]),'COLORED_HIGGS')
        require(all(p['p4'][3]>0 for p in ps) and all(abs(p['mass']-125)<1e-7 for p in ps[2:]),'WRONG_SOURCE_MASS_ENERGY')
        for p in ps:
            q=p['p4'];delta=abs(mass2(q)-p['mass']**2);tol=1e-6+5e-9*max(q[3]**2,sum(x*x for x in q[:3]),1)
            require(delta<=tol,'ACTUAL_SOURCE_MASS_SHELL_FAILURE');max_shell=max(max_shell,delta/tol)
        for j in range(4):
            delta=abs(ps[0]['p4'][j]+ps[1]['p4'][j]-ps[2]['p4'][j]-ps[3]['p4'][j]);max_closure=max(max_closure,delta)
            require(delta<1e-5+5e-10*sum(abs(p['p4'][j]) for p in ps),'SOURCE_FOUR_MOMENTUM_FAILURE')
        hh=[ps[2]['p4'][j]+ps[3]['p4'][j] for j in range(4)];mhh=math.sqrt(mass2(hh))
        delta=abs(r['scale']-mhh/2);max_scale=max(max_scale,delta)
        require(delta<=1e-5+1e-9*mhh and r['alpha_qcd']>0,'ACTUAL_MHH_SCALE_OR_ALPHA_S_FAILURE')
        require(abs(r['weight']-source['sigma_pb'])<=1e-5*source['sigma_pb'], 'UNCERTIFIED_XWGTUP_PB_CONVENTION')
    # Exact card parse is delegated independently to the native MG readers by
    # the export/preparation gate; retained header tokens are checked here too.
    if seed is not None:
        match=re.findall(r'^\s*([0-9]+)\s*=\s*iseed\b',text,re.M)
        require(len(match)==1 and int(match[0])==seed,'SOURCE_SEED_MISMATCH')
    return {'status':'PASS_ACTUAL_FULL_MASS_HH_LHE','events':expected,'sigma_pb':source['sigma_pb'],
       'integration_error_pb':source['error_pb'],'LHE_IDWTUP':-4,'source_weight_convention':'XWGTUP_pb_average_original_N',
       'source_sha256':source['sha256'],'decompressed_sha256':source['decompressed_sha256'],
       'max_four_momentum_residual_gev':max_closure,'max_mass_shell_tolerance_fraction':max_shell,
       'max_scalup_minus_mHH_over2_gev':max_scale,'source_included_decays':[],
       'identical_H_production_divisor':2,'physical_normalization':'RAW_PRODUCTION_ONLY'}

def write_index(path,records):
    with Path(path).open('x') as out:
        for r in records:
            out.write('E '+str(r['index'])+' '+r['hash']+' '+str(r['nup'])+' '+str(r['process'])+' '+
               ' '.join(format(r[k],'.17g') for k in ('weight','scale','alpha_qed','alpha_qcd'))+'\n')
            for p in r['particles']:out.write('P '+p['line']+'\n')

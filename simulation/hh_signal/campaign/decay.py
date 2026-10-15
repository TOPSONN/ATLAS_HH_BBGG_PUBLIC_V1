"""A physical scalar two-body decayer applied to immutable genuine HH sources.

No source momentum repair, unweighting or replacement source generation.
The angular law is isotropic for an unpolarized spin-zero Higgs at this order.
"""
import hashlib,math,random,json
from pathlib import Path
from .common import require,save_json,sha
from .lhe import load_lhe,write_index,mass2

def direction(seed,index,lineage):
    digest=hashlib.sha256(f'HH-scalar-decay-v1:{seed}:{index}:{lineage}'.encode()).digest()
    rng=random.Random(int.from_bytes(digest,'big'));cost=2*rng.random()-1;phi=2*math.pi*rng.random()
    return cost,phi

def two_body(parent,mass,cost,phi):
    px,py,pz,e=parent;m2=mass2(parent)
    require(e>0 and m2>4*mass*mass and -1<=cost<=1,'INVALID_DECAY_KINEMATICS')
    m=math.sqrt(m2);q=math.sqrt(m2/4-mass*mass);st=math.sqrt(max(0,1-cost*cost))
    v=[q*st*math.cos(phi),q*st*math.sin(phi),q*cost];beta=[px/e,py/e,pz/e];b2=sum(x*x for x in beta);gamma=e/m
    def boost(p):
        dot=sum(a*b for a,b in zip(beta,p));f=(gamma-1)*dot/b2+gamma*m/2 if b2 else gamma*m/2
        return [p[j]+f*beta[j] for j in range(3)]+[gamma*(m/2+dot)]
    pair=[boost(v),boost([-x for x in v])]
    for j in range(4):require(abs(sum(p[j] for p in pair)-parent[j])<1e-9+2e-12*abs(parent[j]),'DECAY_MOMENTUM_FAILURE')
    for p in pair:require(abs(mass2(p)-mass*mass)<1e-7+2e-11*p[3]*p[3],'DAUGHTER_MASS_SHELL_FAILURE')
    return pair,m

def assignment(seed,index):
    bit=hashlib.sha256(f'HH-role-v1:{seed}:{index}'.encode()).digest()[0]&1
    return (3+bit,4-bit) # bb source index, gamma-gamma source index

def decay_source(source_path,output,seed,model):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);source=load_lhe(source_path)
    original_sha=sha(source_path);blocks=[];ledger=[]
    for r in source['records']:
        require(r['nup']==4,'DECAYER_REQUIRES_UNDECAYED_SOURCE')
        bb,gg=assignment(seed,r['index']);lines=[]
        for j,p in enumerate(r['particles'],1):
            f=p['line'].split()
            if j in (bb,gg):require(p['id']==25 and p['status']==1,'WRONG_OR_DUPLICATE_HIGGS');f[1]='2'
            lines.append(' '.join(f))
        roles=[];color=max(p['c1'] for p in r['particles'])+max(p['c2'] for p in r['particles'])+1
        for h,ids,mass in [(bb,[5,-5],model['bottom_kinematic_mass_gev']),(gg,[22,22],0.)]:
            cost,phi=direction(seed,r['index'],h);pair,m=two_body(r['particles'][h-1]['p4'],mass,cost,phi)
            daughters=[]
            for k,(pdg,p) in enumerate(zip(ids,pair)):
                daughters.append(len(lines)+1)
                fields=[str(pdg),'1',str(h),str(h),str(color if pdg==5 else 0),str(color if pdg==-5 else 0),
                    *[f'{x:.17e}' for x in p],f'{mass:.17e}','0.0','9.0']
                lines.append(' '.join(fields))
            roles.append({'source_Higgs_index':h,'mode':'bb' if h==bb else 'gammagamma',
              'daughter_LHE_indices':daughters,'cos_theta_rest':cost,'phi_rest':phi,'parent_invariant_mass_gev':m,
              'source_parent_p4_unchanged':True,'daughter_mass_gev':mass,'color_singlet_tag':color if h==bb else 0})
        header=r['header_line'].split();header[0]='8'
        block=('<event>\n'+' '.join(header)+'\n'+'\n'.join(lines)+'\n</event>').encode();blocks.append(block)
        ledger.append({'source_event_index':r['index'],'production_event_sha256':r['hash'],
          'decayed_event_sha256':hashlib.sha256(block).hexdigest(),'production_weight_pb':r['weight'],
          'source_original_count':len(source['records']),'assignment_seed':seed,'assignment_probability':0.5,'roles':roles})
    raw=source['header']+b'\n'.join(blocks)+b'\n</LesHouchesEvents>\n'
    (out/'decayed_source.lhe').write_bytes(raw)
    derived=load_lhe(out/'decayed_source.lhe')
    require(len(derived['records'])==len(source['records']) and sha(source_path)==original_sha,'SOURCE_DECAY_REWRITE_OR_COUNT')
    # Reparse the physically emitted file, independently checking every tuple.
    for s,d,row in zip(source['records'],derived['records'],ledger):
        require(d['weight']==s['weight'] and d['scale']==s['scale'],'DECAYER_CHANGED_SOURCE_WEIGHT_OR_SCALE')
        for j in range(4):
            a,b=s['particles'][j],d['particles'][j]
            require(a['p4']==b['p4'] and a['mass']==b['mass'] and a['id']==b['id'],'ORIGINAL_PARTICLE_MODIFIED')
        for role in row['roles']:
            h=role['source_Higgs_index'];children=[p for p in d['particles'][4:] if p['m1']==p['m2']==h]
            require(len(children)==2 and sorted(p['id'] for p in children)==([-5,5] if role['mode']=='bb' else [22,22]),'WRONG_EMITTED_MIXED_DECAY')
            for j in range(4):require(abs(sum(p['p4'][j] for p in children)-s['particles'][h-1]['p4'][j])<1e-8,'EMITTED_DECAY_MOMENTUM')
    write_index(out/'decayed_source_index.dat',derived['records']);write_index(out/'production_source_index.dat',source['records'])
    with (out/'decay_ledger.jsonl').open('x') as stream:
        for row in ledger:stream.write(json.dumps(row,allow_nan=False)+'\n')
    with (out/'roles.dat').open('x') as stream:
        for row in ledger:
            bb,gg=assignment(seed,row['source_event_index']);stream.write(f"{row['source_event_index']} {row['production_event_sha256']} {bb} {gg}\n")
    result={'status':'PASS_ACTUAL_SYMMETRIC_TWO_HIGGS_SCALAR_DECAYS','events':len(ledger),'assignment_seed':seed,
       'source_sha256':original_sha,'decayed_LHE_sha256':sha(out/'decayed_source.lhe'),
       'production_index_sha256':sha(out/'production_source_index.dat'),'decayed_index_sha256':sha(out/'decayed_source_index.dat'),
       'ledger_sha256':sha(out/'decay_ledger.jsonl'),'model':model,'source_decay_factors_in_nominal':[],
       'missing_mixed_decay_factor':model['mixed_decay_factor'],'normalization_scope':'MODEL_BR_ONLY',
       'assignment_counts':{str(h):sum(assignment(seed,r['index'])[1]==h for r in source['records']) for h in (3,4)},
       'all_original_momenta_preserved':True,'all_decay_vertices_closed':True,'kinematic_mass_uses_original_p4_virtuality':'no_repair_of_printed_source_Higgs_p4'}
    save_json(out/'validation.json',result);return result

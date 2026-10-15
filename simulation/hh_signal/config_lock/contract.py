"""Frozen effective configuration, provenance and seed contracts."""
import hashlib,json,math,re
from pathlib import Path
from simulation.hh_signal.contracts import require,sha,read_json
from simulation.hh_signal.integration_audit.audit import card_values,include_values

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE='28862bed06451723ba17c11fbca9f88b6abb8ee7'
SEEDS=(910001,910019,910037,910061)

def lock():return read_json(HERE/'configuration_lock.json')

def deny_execution(kind='integral'):
    # Neither a file, environment variable nor CLI token can grant permission.
    raise ValueError('NOT_AUTHORIZED_PHASE7F:'+kind+'; separate explicit authorization and reviewed runtime gate required')

def digest_bytes(data):return hashlib.sha256(data).hexdigest()

def verify_cards(reviewed,working,embedded,compiled,seed):
    require(type(seed) is int and seed in SEEDS,'UNREVIEWED_SEED')
    expected=lock()['card_contract']
    cards=[card_values(t) for t in [reviewed,working,embedded]]
    for c in cards:
        for key,value in expected.items():require(c.get(key)==value,'CARD_CONTRACT:'+key)
        require(c.get('iseed')==str(seed),'CARD_SEED_RESET_OR_MISMATCH')
    require(cards[0]==cards[1]==cards[2],'CARD_REPRESENTATIONS_DIFFER')
    values=include_values(compiled)
    for key in ['pdlabel','pdsublabel(1)','pdsublabel(2)']:
        require(values.get(key)=='cteq6l1','WRONG_OR_INCONSISTENT_COMPILED_PDF:'+key)
    require(values.get('iseed')==str(seed) and values.get('nevents')=='0','COMPILED_SEED_OR_EVENT_TARGET')
    def number(key):return float(values[key].lower().replace('d','e'))
    require(number('ebeam(1)')==number('ebeam(2)')==6500 and number('scalefact')==.5 and
        number('dynamical_scale_choice')==4 and values['fixed_ren_scale'].lower()=='.false.' and
        values['fixed_fac_scale1'].lower()==values['fixed_fac_scale2'].lower()=='.false.','COMPILED_ENERGY_OR_SCALE')
    return {'status':'PASS_REVIEWED_WORKING_EMBEDDED_COMPILED_CARDS','seed':seed}

def verify_runtime(runtime,seed):
    required={'PDF','PDSUBLABEL','alpha_s_MZ','running_loops','PDFSUP','requested_seed','native_base_seed',
        'compiled_seed','launch_seed','banner_seed','run_identity_seed','stage_offsets','alpha_values','probe_sha256','source_manifest_sha256'}
    require(required<=runtime.keys(),'MISSING_RUNTIME_EVIDENCE')
    require(runtime['PDF']=='cteq6l1' and runtime['PDSUBLABEL']==['cteq6l1']*2,'RUNTIME_PDF_MISMATCH')
    require(runtime['PDFSUP']==[10042,10042],'HEADER_RUNTIME_DISAGREEMENT')
    require(runtime['alpha_s_MZ']==.13 and runtime['running_loops']==1,'RUNTIME_ALPHA_RUNNING_MISMATCH')
    for key in ['requested_seed','compiled_seed','native_base_seed','launch_seed','banner_seed','run_identity_seed']:
        require(type(runtime[key]) is int and runtime[key]==seed,'EFFECTIVE_SEED_MISMATCH:'+key)
    offsets=runtime['stage_offsets']
    require(set(offsets)=={'iproc','moffset'} and all(type(v) is int and v==0 for v in offsets.values()),'UNVERIFIED_STAGE_OFFSETS')
    require(len(runtime['alpha_values'])>=5,'INSUFFICIENT_NUMERICAL_RUNNING_PROBE')
    for row in runtime['alpha_values']:
        q,a=row['Q_GeV'],row['alpha_s'];require(math.isfinite(q) and q>4.7 and math.isfinite(a),'NONFINITE_ALPHA_PROBE')
        expected=1/(1/.13+(23/3)/(2*math.pi)*math.log(q/91.188))
        require(abs(a-expected)<=1e-10*expected,'NUMERICAL_ALPHA_RUNNING_MISMATCH')
    for key in ['probe_sha256','source_manifest_sha256']:
        require(re.fullmatch('[0-9a-f]{64}',runtime[key]) is not None,'MISSING_BOUND_NATIVE_SOURCE')
    require(runtime['probe_sha256']==sha(HERE/'src/initialization_probe.f') and
        runtime['source_manifest_sha256']==sha(HERE/'configuration_lock.json'),'UNBOUND_NATIVE_PROBE_OR_LOCK')
    return {'status':'PASS_NO_INTEGRAL_NATIVE_INITIALIZATION_PROBE_ONLY','seed':seed,
        'eventual_integration_banner_and_runtime':'NOT_EVALUATED'}

def validate_source_inventory(rows,root):
    root=Path(root);require(rows and len({r['path'] for r in rows})==len(rows),'EMPTY_OR_DUPLICATE_SOURCE_INVENTORY')
    for r in rows:
        p=Path(r['path']);require(not p.is_absolute() and '..' not in p.parts,'UNSAFE_SOURCE_BINDING')
        path=root/p;require(path.is_file() and not path.is_symlink() and sha(path)==r['sha256'],'SOURCE_OR_CARD_CHANGED:'+r['path'])
    return True

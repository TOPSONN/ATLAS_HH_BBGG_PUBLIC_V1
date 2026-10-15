from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json, math, os, shutil, subprocess, time
from pathlib import Path
from simulation.hh_signal.contracts import sha, read_json, require
from simulation.new_backgrounds.common import Monitor, save_json

REPO=Path(__file__).resolve().parents[3]
PACKAGE=REPO/'simulation/hh_signal'
CAMPAIGN=PACKAGE/'campaign'
BASE='64353adfbbd3a28b13ddbdf761896c0a3fc6e680'
PHASE7A='d9fe33f97773367a41b8877568401af594eeb2a6'
ACK='PHASE7B_7C_7D_GGF_HH_SIGNAL_CAMPAIGN_V1'
LIMITS={'7b':(100,6,10),'7c':(1000,12,20),'7d':(1000,4,10)}
GIB=1024**3

def identity():
    paths=[p for p in CAMPAIGN.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
           p.suffix in ('.py','.cxx','.hxx','.f','.json','.cmnd','.dat','.mg5')]
    paths += [PACKAGE/'scripts/run_campaign.sh',PACKAGE/'scripts/run_campaign.py',
              REPO/'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl',
              REPO/'simulation/pythia8/config/baseline_shower.cmnd']
    rows=[{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted(paths)]
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),rows

def safe_output(raw):
    raw=Path(raw).expanduser()
    allowed=(Path.home()/'simulations/hh_signal_runs').resolve()
    require(raw.is_absolute() and '..' not in raw.parts and raw.resolve().is_relative_to(allowed)
            and raw.resolve()!=allowed,'UNSAFE_CAMPAIGN_OUTPUT')
    require(not any(p.is_symlink() for p in (raw,*raw.parents)),'SYMLINK_OUTPUT_FORBIDDEN')
    return raw.resolve()

def resources(out,disk_gib):
    p=Path(out)
    while not p.exists():p=p.parent
    mem=int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
    free=shutil.disk_usage(p).free
    require(mem>2*GIB and free>(disk_gib+.5)*GIB,'RESOURCE_PRECHECK_FAILED')
    return {'memory_available_bytes':mem,'disk_free_bytes':free,'cpu_affinity_count':len(os.sched_getaffinity(0)),
            'generator_workers':1,'concurrent_physics_jobs':1,'load_average':list(os.getloadavg()),
            'production_runtime_estimate':'UNKNOWN_UNTIL_ACTUAL_PILOT','disk_estimate':'UNKNOWN_UNTIL_ACTUAL_PILOT'}

def scientific_environment():
    from simulation.zh_pilot.scripts.check_environment import verify_environment
    actual=verify_environment()
    model=read_json(REPO/'metadata/phase7a_model_manifest.json')
    config=read_json(REPO/'.local/mg5_installation.json');mg=Path(config['mg5_path'])
    for path,h in model['installed_model_files'].items():require(sha(mg/path)==h,'STALE_FULL_MASS_MODEL')
    require(read_json(REPO/'metadata/phase7a_loop_validation.json')['status']=='PASS_BOUNDED_FULL_MT_MB_NUMERICAL_WITH_LIMITS',
            'BLOCKED_FULL_MASS_LOOP_VALIDATION')
    return actual

def mg_environment(config):
    env=dict(os.environ);p=Path(config['toolchain_prefix'])
    env['PATH']=str(p/'bin')+os.pathsep+env['PATH'];env['LD_LIBRARY_PATH']=str(p/'lib')
    return env

def native_environment():
    dc=read_json(REPO/'.local/delphes_installation.json');pc=read_json(REPO/'.local/pythia8_installation.json')
    from simulation.new_backgrounds.delphes_stage import native_environment as env
    result=env(dc,pc)
    # ROOT's environment also contains a different Pythia library. Match the
    # retained validated bridge: scientific Pythia/HepMC prefixes come first.
    result['LD_LIBRARY_PATH']=os.pathsep.join(str(Path(p)/'lib') for p in
        (pc['pythia_prefix'],pc['hepmc3_prefix'],dc['delphes_prefix'],dc['root_prefix']))
    result['PYTHIA8DATA']=pc['xml_path']
    return dc,pc,result

def project_public(value):
    """Retain hashes/data; replace only known local root locations by roles."""
    if isinstance(value,dict):return {k:project_public(v) for k,v in value.items()}
    if isinstance(value,list):return [project_public(v) for v in value]
    if isinstance(value,str):
        replacements={str(Path.home()):'LOCAL_HOME',str(REPO):'REPOSITORY'}
        for root,role in replacements.items():value=value.replace(root,role)
    return value

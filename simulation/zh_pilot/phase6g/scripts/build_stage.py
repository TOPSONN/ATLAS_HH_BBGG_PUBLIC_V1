#!/usr/bin/env python3
"""Build the guarded future ZH bridge with retained libraries; never process events."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[4]
PACKAGE = REPO/'simulation/zh_pilot/phase6g'
BASELINE = REPO/'simulation/pythia8/config/baseline_shower.cmnd'
OVERLAY = REPO/'simulation/zh_pilot/cards/preferred_higgs_decay.cmnd'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def source_bindings():
    names = ['include/Authorization.hxx','include/StrictJson.hxx','include/ZHAncestry.hxx','include/SourceAttempt.hxx',
             'src/zh_shower.cxx','src/validate_zh_hepmc3.cxx','src/test_zh_methods.cxx',
             'scripts/build_stage.py','scripts/shower_stage.py']
    paths = [PACKAGE/name for name in names]
    paths += [REPO/'simulation/pythia8/src/validate_hepmc3.cxx',
              REPO/'simulation/pythia8/include/TrackedLHA.hxx',
              REPO/'simulation/pythia8/include/Sha256.hxx', REPO/'simulation/pythia8/include/Json.hxx', BASELINE, OVERLAY]
    return {path.relative_to(REPO).as_posix(): digest(path) for path in paths}


def scoped_environment(config):
    env = dict(os.environ)
    env['PYTHIA8DATA'] = config['xml_path']
    env['LD_LIBRARY_PATH'] = os.pathsep.join([str(Path(config['pythia_prefix'])/'lib'), str(Path(config['hepmc3_prefix'])/'lib')])
    return env


def invoke(command, output, phase, env, run_command=None, timeout=180, expected_exit_code=0):
    require(re.fullmatch('[a-z0-9_]+',phase) is not None,'Unsafe supervised build stage label')
    require(type(expected_exit_code) is int and expected_exit_code in (0,2),'Invalid expected build/check exit code')
    if expected_exit_code:
        require(phase.endswith('_missing_authorization') and len(command)==1 and
                Path(command[0]).name in ('zh_shower','validate_zh_hepmc3'),
                'Expected nonzero is limited to native missing-authorization probes')
    if run_command is not None:
        result=run_command(command,output,phase,env=env,expected_exit_code=expected_exit_code)
        require(result['exit_code']==expected_exit_code, 'Guarded build/check failed: '+phase)
        return Path(result['log_path']).read_text(encoding='utf-8')
    result=subprocess.run(command,cwd=output,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    (output/(phase+'.log')).write_bytes(result.stdout.encode('utf-8'))
    require(result.returncode==expected_exit_code, 'Build/check failed: '+phase)
    return result.stdout


def verify_existing(config,run_command=None,output=None,phase_scope='prebuild'):
    if run_command is not None:
        require(config['pythia_version']=='8.317' and config['hepmc3_version']=='3.3.1' and
                config['pythia_source_commit']=='83a5c9986f30746cfb390435a9b10ac55a758fca' and
                config['hepmc3_source_commit']=='beb66aa1a2ac263066becdee26d18ead83edec95','Unverified installation identity')
        for table in ('library_sha256','header_sha256','xml_sha256'):
            require(config.get(table),'Missing pinned installation fingerprints')
            for name,expected in config[table].items():require(digest(name)==expected,'Existing installation file changed')
        env=scoped_environment(config)
        require(re.fullmatch('[a-z0-9_]+',phase_scope) is not None,'Unsafe installation-check namespace')
        label='existing_'+phase_scope+'_'
        info=json.loads(invoke([config['runner_path'],'--build-info'],output,label+'runner_build_info',env,run_command))
        require(info['pythia_version_integer']==8317 and info['hepmc3_version']=='3.03.01' and info['cxx_standard']>=202002,'Existing runner ABI mismatch')
        for key in ('runner_path','validator_path'):
            loaded=invoke(['ldd',config[key]],output,label+key+'_ldd',env,run_command)
            require('not found' not in loaded,'Existing native dependency missing')
            for line in loaded.splitlines():
                if 'libpythia8.so' in line or 'libHepMC3.so' in line:
                    path=Path(line.split('=>',1)[1].split()[0]).resolve()
                    require(path in {Path(p).resolve() for p in config['library_sha256']},'Existing binary loads unverified scientific library')
        return {'binary_build_info':info,'runner_sha256':digest(config['runner_path']),
                'reader_validator_sha256':digest(config['validator_path'])}
    sys.path.insert(0, str(REPO/'simulation/pythia8/scripts'))
    import shower_sample
    saved = dict(os.environ)
    try:
        os.environ.update(scoped_environment(config))
        result = shower_sample.verify_installation(config)
        return {key: value for key, value in result.items() if key != 'runtime_dependencies'}
    finally:
        os.environ.clear(); os.environ.update(saved)


def safe_build_output(output, config):
    output = Path(output).expanduser().resolve()
    require(not output.exists(), 'Build directory exists; preserve it and choose a new directory')
    for key in ('pythia_prefix', 'hepmc3_prefix', 'xml_path'):
        root = Path(config[key]).resolve()
        require(output != root and root not in output.parents and output not in root.parents, 'Build output overlaps existing installation')
    scratch = REPO/'.local/phase6g'
    require(output != REPO and output not in REPO.parents and (REPO not in output.parents or scratch in output.parents),
            'Build outside Git, or inside ignored .local/phase6g scratch')
    return output


def compile_bridge(output, config, run_command=None):
    output = safe_build_output(output, config)
    output.mkdir(parents=True)
    before = verify_existing(config,run_command,output,phase_scope='prebuild'); bindings = source_bindings(); env = scoped_environment(config)
    compiler = shutil.which('g++')
    require(compiler is not None, 'Existing g++ unavailable; no installation attempted')
    pythia, hepmc = Path(config['pythia_prefix']), Path(config['hepmc3_prefix'])
    binaries = {}
    for target in ('zh_shower', 'validate_zh_hepmc3', 'test_zh_methods'):
        binary = output/target
        command = [compiler, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Wpedantic', '-DGZIP',
                   '-I'+str(PACKAGE/'include'), '-I'+str(REPO/'simulation/pythia8/include'),
                   '-I'+str(pythia/'include'), '-I'+str(hepmc/'include'), str(PACKAGE/'src'/f'{target}.cxx'),
                   '-L'+str(pythia/'lib'), '-L'+str(hepmc/'lib'), '-Wl,-rpath,'+str(pythia/'lib'),
                   '-Wl,-rpath,'+str(hepmc/'lib'), '-lpythia8', '-lHepMC3', '-lz', '-ldl', '-o', str(binary)]
        invoke(command,output,target+'_build',env,run_command)
        loaded = invoke(['ldd', str(binary)],output,target+'_ldd',env,run_command)
        require('not found' not in loaded, 'Native runtime dependency missing')
        for line in loaded.splitlines():
            if 'libpythia8.so' in line or 'libHepMC3.so' in line:
                path = Path(line.split('=>',1)[1].split()[0]).resolve()
                allowed = {Path(name).resolve(): value for name,value in config['library_sha256'].items()}
                require(path in allowed and digest(path)==allowed[path], 'Unverified scientific library loaded')
        binaries[target] = {'path': str(binary), 'sha256': digest(binary)}
    build_info = {}
    for target in ('zh_shower','validate_zh_hepmc3'):
        value = json.loads(invoke([binaries[target]['path'],'--build-info'],output,target+'_build_info',env,run_command))
        require(value['pythia_version_integer']==8317 and value['hepmc3_version']=='3.03.01' and value['cxx_standard']>=202002,
                'Native version/ABI mismatch')
        build_info[target] = value
        rejected=invoke([binaries[target]['path']],output,target+'_missing_authorization',env,run_command,
                        timeout=10,expected_exit_code=2)
        require('BLOCKED_PHYSICAL_AUTHORIZATION' in rejected,'Missing native authorization guard did not reject')
    method = json.loads(invoke([binaries['test_zh_methods']['path']],output,'zh_method_fixtures',env,run_command))
    require(method['status']=='METHOD_ONLY' and method['new_physics_events']==0 and method['next_calls']==0, 'Synthetic method scope changed')
    preflight = json.loads(invoke([binaries['zh_shower']['path'], '--dry-run', '--xml', config['xml_path'],
        '--settings', str(BASELINE), '--overlay', str(OVERLAY), '--seed','20261104'],output,'zh_settings_preflight',env,run_command))
    require(preflight['events_processed']==0 and preflight['status']=='DRY_RUN', 'Native settings preflight changed scope')
    require(source_bindings()==bindings and verify_existing(config,run_command,output,phase_scope='postbuild')==before, 'Sources or retained installation changed during build')
    receipt = {'schema_version':1,'status':'PASS_BUILD_AND_METHODS_ONLY','physical_authorization':'NOT_AUTHORIZED',
               'new_physics_events':0,'next_calls':0,'binary_build_info':build_info,'binaries':binaries,
               'source_sha256':bindings,'method_tests':method,'settings_preflight':preflight,
               'runtime_environment':{key:env[key] for key in ('PYTHIA8DATA','LD_LIBRARY_PATH')},
               'installation_file_sha256':{name:sha for table in ('library_sha256','header_sha256','xml_sha256') for name,sha in config[table].items()},
               'installed_identity_unchanged':True,'existing_installation_config_sha256':None,
               'compiler_version':invoke([compiler,'--version'],output,'compiler_version',env,run_command).splitlines()[0]}
    (output/'build_receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation',type=Path,default=Path(os.environ.get('PYTHIA8_LOCAL_CONFIG',REPO/'.local/pythia8_installation.json')))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    config=json.loads(args.installation.read_text(encoding='utf-8'))
    result=compile_bridge(args.output,config)
    result['existing_installation_config_sha256']=digest(args.installation)
    Path(result['binaries']['zh_shower']['path']).parent.joinpath('build_receipt.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({'status':result['status'],'output':str(args.output),'new_physics_events':0,'next_calls':0},indent=2))


if __name__=='__main__':
    main()

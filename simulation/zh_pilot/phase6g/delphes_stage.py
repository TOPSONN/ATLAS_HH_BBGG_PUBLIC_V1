"""Future guarded Delphes execution and independent native ZH ROOT readback."""
from pathlib import Path
import json
import os
import shlex
import shutil
import subprocess

from .common import REPO, require, sha_file, save_json

CARD = REPO/'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl'
CARD_SHA = 'cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47'


def native_environment(config, pyconfig=None, mgconfig=None, output=None):
    env = dict(os.environ)
    roots = [config['root_prefix'], config['delphes_prefix']]
    if pyconfig:
        roots += [pyconfig['pythia_prefix'], pyconfig['hepmc3_prefix']]
    bins = [str(Path(config['root_prefix'])/'bin')]
    if mgconfig:
        bins.insert(0, str(Path(mgconfig['toolchain_prefix'])/'bin'))
        env['CONDA_PREFIX'] = mgconfig['toolchain_prefix']
    env['PATH'] = os.pathsep.join(bins+[env.get('PATH', '')])
    env['LD_LIBRARY_PATH'] = os.pathsep.join([str(Path(p)/'lib') for p in roots]+[env.get('LD_LIBRARY_PATH', '')])
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if output:
        env['PYTHONPYCACHEPREFIX'] = str(Path(output)/'runtime_cache')
        env['TMPDIR'] = str(Path(output)/'temporary')
        Path(env['TMPDIR']).mkdir(exist_ok=True)
    return env


def build_root_analyzer(output, config, run_command=None):
    """Compilation/build-info only. Does not open an event or call Delphes."""
    output = Path(output).resolve()
    require(not output.exists(), 'native build output exists')
    output.mkdir(parents=True)
    root = Path(config['root_prefix'])
    compiler = root/'bin/x86_64-conda-linux-gnu-c++'
    require(compiler.is_file(), 'retained ROOT compiler missing')
    env = native_environment(config)
    # These are read-only tool configuration queries, not a physical execution.
    config_argv = [str(root/'bin/root-config'), '--cflags', '--libs']
    if run_command:
        flags_receipt = run_command(config_argv, output, 'zh_root_compiler_flags', env=env)
        flags = shlex.split(Path(flags_receipt['log_path']).read_text())
    else:
        flags = shlex.split(subprocess.check_output(config_argv, env=env, text=True, timeout=30))
    binary = output/'analyze_zh_root'
    source = REPO/'simulation/zh_pilot/phase6g/src/analyze_zh_root.cxx'
    argv = [str(compiler), '-std=c++20', '-O2', '-Wall', '-Wextra', str(source),
            '-I'+str(REPO/'simulation/delphes/include'),
            '-I'+str(REPO/'simulation/pythia8/include'),
            '-I'+str(Path(config['delphes_prefix'])/'include'),
            '-L'+str(Path(config['delphes_prefix'])/'lib'), '-lDelphes',
            '-Wl,-rpath,'+str(Path(config['delphes_prefix'])/'lib'),
            '-Wl,-rpath,'+str(root/'lib'), *flags, '-o', str(binary)]
    if run_command:
        run_command(argv, output, 'build_zh_root_adapter', env=env)
        result = run_command([str(binary), '--build-info'], output, 'zh_root_build_info', env=env)
        info = json.loads(Path(result['log_path']).read_text())
        methods = run_command([str(binary), '--method-tests'], output, 'zh_root_method_tests', env=env)
        method_info = json.loads(Path(methods['log_path']).read_text())
    else:
        # Explicit developer/user build command only; root pipeline uses guard.
        subprocess.run(argv, cwd=output, env=env, check=True, timeout=300)
        info = json.loads(subprocess.check_output([str(binary), '--build-info'], env=env, text=True, timeout=30))
        method_info = json.loads(subprocess.check_output([str(binary), '--method-tests'], env=env, text=True, timeout=30))
    require(info['root_version'] == '6.40.04' and info['cpp_standard'] == 20 and info['events_processed'] == 0,
            'native adapter ROOT/C++ version mismatch')
    require(method_info['status'] == 'METHOD_ONLY' and method_info['checks'] == 3 and method_info['events_processed'] == 0,
            'derived-p4 numerical method checks failed')
    receipt = {'schema_version': 1, 'status': 'PASS_COMPILE_AND_BUILD_INFO_ONLY',
               'events_processed': 0, 'source_sha256': sha_file(source),
               'analyzer_path': str(binary), 'analyzer_sha256': sha_file(binary),
               'compiler_path': str(compiler), 'build_info': info, 'method_tests': method_info}
    save_json(output/'build_receipt.json', receipt)
    return receipt


def execute_delphes(output, shower, config, analyzer, seed, run_command):
    output = Path(output)
    require(not output.exists(), 'Delphes output already exists; no retries')
    require(shower['validated_events'] == 100 and shower['status'] == 'PASS_READER_ASCII_RECORDS',
            'actual full100 ReaderAscii validation required before Delphes')
    for key in ('hepmc_path', 'input_index_path', 'truth_index_path'):
        require(sha_file(shower[key]) == shower[key+'_sha256'], 'validated shower artifact changed: '+key)
    require(sha_file(CARD) == CARD_SHA, 'historical detector card changed')
    require(sha_file(analyzer['analyzer_path']) == analyzer['analyzer_sha256'], 'native analyzer changed')
    output.mkdir(parents=True)
    source = Path(shower['hepmc_path'])
    # Copy exact ReaderAscii-inspected bytes, no record transformation.
    shutil.copyfile(source, output/'input.hepmc3')
    raw = CARD.read_bytes();marker = b'set RandomSeed 610301'
    require(raw.count(marker) == 1 and type(seed) is int and 1 <= seed <= 900000000, 'unreviewed detector seed')
    (output/'detector_card.tcl').write_bytes(raw.replace(marker, f'set RandomSeed {seed}'.encode(), 1))
    command = [config['delphes_binary'], str(output/'detector_card.tcl'), 'detector.root', str(output/'input.hepmc3')]
    run_command(command, output, 'delphes_full100')
    require(sha_file(source) == shower['hepmc_path_sha256'] and
            sha_file(output/'input.hepmc3') == shower['hepmc_path_sha256'], 'Delphes input bytes changed')
    command = [analyzer['analyzer_path'], '--input', str(output/'detector.root'),
               '--input-index', shower['input_index_path'], '--truth-index', shower['truth_index_path'],
               '--card', str(output/'detector_card.tcl'), '--summary', str(output/'native_validation.json'),
               '--events-jsonl', str(output/'reco_events.jsonl'), '--cutflow', str(output/'cutflow.csv'), '--events', '100']
    run_command(command, output, 'independent_native_zh_root_readback')
    report = json.loads((output/'native_validation.json').read_text())
    require(report['status'] == 'PASS_NATIVE_ZH_RECORD_READBACK' and report['ROOT_entries'] == report['processed'] == 100
            and report['invalid'] == report['skipped'] == 0, 'native ROOT validation failed')
    require(report['root_sha256'] == sha_file(output/'detector.root') and
            report['input_index_sha256'] == sha_file(shower['input_index_path']) == shower['input_index_path_sha256'] and
            report['truth_index_sha256'] == sha_file(shower['truth_index_path']) == shower['truth_index_path_sha256'] and
            report['card_sha256'] == sha_file(output/'detector_card.tcl'), 'native report inspected different inputs')
    report['root_path'] = str(output/'detector.root')
    report['cutflow_path'] = str(output/'cutflow.csv')
    report['reco_events_path'] = str(output/'reco_events.jsonl')
    report['derived_files_sha256'] = {name:sha_file(output/name) for name in ('reco_events.jsonl','cutflow.csv')}
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Compile/read build-info only; never executes Delphes or opens an event')
    parser.add_argument('--build-only', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from importlib.util import spec_from_file_location, module_from_spec
    path = REPO/'simulation/zh_pilot/scripts/prepare_pilot.py'
    import sys
    sys.path.insert(0, str(path.parent))
    spec = spec_from_file_location('phase6g_build_paths', path)
    module = module_from_spec(spec);spec.loader.exec_module(module)
    output = module.safe_output(args.output, module.protected_paths())
    config = json.loads((REPO/'.local/delphes_installation.json').read_text())
    print(json.dumps(build_root_analyzer(output, config), indent=2))


if __name__ == '__main__':
    main()

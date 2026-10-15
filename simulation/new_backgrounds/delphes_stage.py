"""One guarded Delphes run per requested subset of the actual full shower.

The 10/100 subsets are byte prefixes of the validated full1000 shower, not
independent Pythia statistics. Native ROOT readback preserves source/N=1000.
"""
from pathlib import Path
import hashlib
import json
import os
import shlex
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[2]
CARD = REPO / 'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl'
CARD_SHA = 'cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47'
SEEDS = {'zh': 610501, 'tth': 610502, 'bbgj': 610503}
REUSE_MANIFEST_SHA = '494a1cc13ee5f0c6a271946b61ce8c1ab5e414a098c73aa1f5e4f5c7f7734dd7'
REUSE_FULL_SHOWER_SHA = 'ae2055e5738ea228b38927c4b4008b6cd2e3ba7acecb28276dd0acd4c38cd0f5'
REUSE_ROOT_SHA = {10: '52fac8ddb8582be0a918df7363372492b03df9ef17eeb437d19c419a3f5dfa68',
                  100: '490e39374e8a6dc9ffe626d2f97f0c07eba59786d03e98482b148c4326de0b3e'}
REUSE_NATIVE_SHA = {10: '2e675320361dcebb6e02da900f37d5e24d2eaa14d1ddb42e9a941f670d01f63a',
                    100: '7c214cd151d5e95ae83c2932f6eece3a960d4daedc02906bdb94dc636f39536f'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def native_environment(config, pyconfig=None, mgconfig=None, output=None):
    env = dict(os.environ)
    roots = [config['root_prefix'], config['delphes_prefix']]
    if pyconfig:
        roots += [pyconfig['pythia_prefix'], pyconfig['hepmc3_prefix']]
    bins = [str(Path(config['root_prefix']) / 'bin')]
    if mgconfig:
        bins.insert(0, str(Path(mgconfig['toolchain_prefix']) / 'bin'))
        env['CONDA_PREFIX'] = mgconfig['toolchain_prefix']
    env['PATH'] = os.pathsep.join(bins + [env.get('PATH', '')])
    env['LD_LIBRARY_PATH'] = os.pathsep.join([str(Path(p) / 'lib') for p in roots] + [env.get('LD_LIBRARY_PATH', '')])
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if output:
        env['PYTHONPYCACHEPREFIX'] = str(Path(output) / 'runtime_cache')
        env['TMPDIR'] = str(Path(output) / 'temporary')
        Path(env['TMPDIR']).mkdir(exist_ok=True)
    return env


def build_root_analyzer(output, config, run_command=None):
    """Compile, query build identity and run numerical checks; zero events."""
    output = Path(output).resolve()
    require(not output.exists(), 'native build output exists')
    output.mkdir(parents=True)
    root = Path(config['root_prefix'])
    compiler = root / 'bin/x86_64-conda-linux-gnu-c++'
    require(compiler.is_file(), 'retained ROOT compiler missing')
    env = native_environment(config)
    config_argv = [str(root / 'bin/root-config'), '--cflags', '--libs']
    if run_command:
        flag_result = run_command(config_argv, output, 'background_root_compiler_flags', env=env)
        flags = shlex.split(Path(flag_result['log_path']).read_text())
    else:
        flags = shlex.split(subprocess.check_output(config_argv, env=env, text=True, timeout=30))
    binary = output / 'analyze_background_root'
    source = REPO / 'simulation/new_backgrounds/src/analyze_background_root.cxx'
    argv = [str(compiler), '-std=c++20', '-O2', '-Wall', '-Wextra', str(source),
            '-I' + str(REPO / 'simulation/delphes/include'),
            '-I' + str(REPO / 'simulation/pythia8/include'),
            '-I' + str(Path(config['delphes_prefix']) / 'include'),
            '-L' + str(Path(config['delphes_prefix']) / 'lib'), '-lDelphes',
            '-Wl,-rpath,' + str(Path(config['delphes_prefix']) / 'lib'),
            '-Wl,-rpath,' + str(root / 'lib'), *flags, '-o', str(binary)]
    if run_command:
        run_command(argv, output, 'build_background_root_adapter', env=env)
        result = run_command([str(binary), '--build-info'], output, 'background_root_build_info', env=env)
        info = json.loads(Path(result['log_path']).read_text())
        result = run_command([str(binary), '--method-tests'], output, 'background_root_method_tests', env=env)
        method_info = json.loads(Path(result['log_path']).read_text())
    else:
        subprocess.run(argv, cwd=output, env=env, check=True, timeout=300)
        info = json.loads(subprocess.check_output([str(binary), '--build-info'], env=env, text=True, timeout=30))
        method_info = json.loads(subprocess.check_output([str(binary), '--method-tests'], env=env, text=True, timeout=30))
    require(info['root_version'] == '6.40.04' and info['cpp_standard'] == 20 and info['events_processed'] == 0,
            'native adapter ROOT/C++ version mismatch')
    require(method_info['status'] == 'METHOD_ONLY' and method_info['checks'] == 6 and method_info['events_processed'] == 0,
            'derived-p4 numerical checks failed')
    receipt = {'schema_version': 1, 'status': 'PASS_COMPILE_AND_BUILD_INFO_ONLY',
               'events_processed': 0, 'source_sha256': sha_file(source),
               'analyzer_path': str(binary), 'analyzer_sha256': sha_file(binary),
               'compiler_path': str(compiler), 'build_info': info, 'method_tests': method_info}
    save_json(output / 'build_receipt.json', receipt)
    return receipt


def _hepmc_subset(source, destination, events):
    """Preserve exact ASCII event blocks; inspect all1000 for truncation."""
    require(type(events) is int and events in (10, 100), 'bounded prefix10/100 required')
    blocks, prefix, block, ending = [], [], [], False
    with Path(source).open('rb') as stream:
        for line in stream:
            require(len(line) <= 8 * 1024 * 1024 and line.endswith(b'\n') and b'\r' not in line,
                    'invalid/bounded native ASCII line')
            if line.startswith(b'E '):
                require(not ending, 'event after HepMC trailer')
                if block:
                    blocks.append(hashlib.sha256(b''.join(block)).hexdigest())
                    if len(blocks) <= events:
                        prefix.extend(block)
                block = [line]
            elif line.strip() == b'HepMC::Asciiv3-END_EVENT_LISTING':
                require(not ending and block, 'missing/duplicate HepMC trailer')
                blocks.append(hashlib.sha256(b''.join(block)).hexdigest())
                if len(blocks) <= events:
                    prefix.extend(block)
                block = []
                ending = True
            elif ending:
                require(not line.strip(), 'content after HepMC trailer')
            elif block:
                block.append(line)
            else:
                prefix.append(line)
            require(len(blocks) <= 1000, 'excess original shower events')
    require(ending and not block and len(blocks) == 1000, 'complete full1000 shower required')
    require(b'HepMC::Asciiv3-START_EVENT_LISTING\n' in prefix, 'missing native HepMC header')
    with Path(destination).open('xb') as stream:
        stream.writelines(prefix)
        stream.write(b'HepMC::Asciiv3-END_EVENT_LISTING\n')
    return blocks[:events]


def _dat_subset(source, destination, events, magic, block_hashes=None):
    prefix, count, active = [], 0, False
    with Path(source).open('rb') as stream:
        first = stream.readline()
        require(first == magic.encode() + b'\n', 'wrong native sidecar magic')
        prefix.append(first)
        for line in stream:
            require(len(line) <= 8 * 1024 * 1024 and line.endswith(b'\n') and b'\r' not in line,
                    'invalid/bounded native sidecar line')
            if line.startswith(b'E '):
                count += 1
                fields = line.split()
                require(int(fields[1]) == count, 'unordered source prefix index')
                if block_hashes is not None and count <= events:
                    require(fields[3].decode() == block_hashes[count - 1], 'prefix raw HepMC/index block mismatch')
                active = count <= events
            require(count > 0 and count <= 1000, 'missing/excess sidecar source row')
            if active:
                prefix.append(line)
    require(count == 1000, 'full1000 source sidecar required')
    with Path(destination).open('xb') as stream:
        stream.writelines(prefix)


def prepare_delphes_input(output, shower, events):
    output = Path(output)
    require(type(events) is int and events in (10, 100, 1000), 'bounded detector10/100/1000 required')
    for key in ('hepmc_path', 'input_index_path', 'truth_index_path'):
        require(sha_file(shower[key]) == shower[key + '_sha256'], 'validated shower artifact changed: ' + key)
    if events == 1000:
        return {key: shower[key] for key in ('hepmc_path', 'input_index_path', 'truth_index_path')}
    hepmc, index, truth = output / 'input.hepmc3', output / 'input_event_index.dat', output / 'background_truth_index.dat'
    hashes = _hepmc_subset(shower['hepmc_path'], hepmc, events)
    _dat_subset(shower['input_index_path'], index, events, 'ATLAS_DELPHES_INPUT_V1', hashes)
    _dat_subset(shower['truth_index_path'], truth, events, 'ATLAS_NEW_BACKGROUND_TRUTH_V1')
    return {'hepmc_path': str(hepmc), 'input_index_path': str(index), 'truth_index_path': str(truth)}


def _check_reused_detector(reused, shower, inputs, runtime_card, output, process, events):
    """Only the exact diagnosed B04 detector stop; no detector executable."""
    require(process == 'zh' and events in (10, 100), 'unreviewed detector reuse process/count')
    require(reused['status'] == 'SOURCE_BOUND_READ_ONLY_DETECTOR_REUSE', 'unreviewed detector reuse status')
    original = Path(reused['original_directory']).resolve()
    manifest = Path(reused['source_manifest_path']).resolve()
    require(manifest.name == 'run_manifest.json' and original == manifest.parent / 'delphes' / f'prefix{events}',
            'reused detector is outside the preserved source run')
    require(not output.resolve().is_relative_to(manifest.parent) and not manifest.parent.is_relative_to(output.resolve()),
            'reused detector output overlaps preserved physical run')
    require(reused['source_manifest_sha256'] == REUSE_MANIFEST_SHA == sha_file(manifest),
            'only the known immutable detector stop may be reused')
    state = json.loads(manifest.read_text())
    require(state['status'] == 'PARTIAL_PHYSICAL_CHAIN' and state['request']['process'] == 'zh' and
            state['MG5_events_generated'] == state['Pythia_events_written'] == state['HepMC_validated_events'] == 1000,
            'preserved detector run lacks the genuine validated full1000 source')
    require(shower['hepmc_path_sha256'] == reused['source_full_shower_sha256'] == REUSE_FULL_SHOWER_SHA,
            'reused detector belongs to another full1000 shower')
    root = Path(reused['root_path']).resolve()
    native = Path(reused['old_native_validation_path']).resolve()
    require(root == original / 'detector.root' and native == original / 'native_validation.json',
            'reused detector ROOT/report path differs')
    require(reused['root_sha256'] == REUSE_ROOT_SHA[events] == sha_file(root) and
            reused['old_native_validation_sha256'] == REUSE_NATIVE_SHA[events] == sha_file(native),
            'known ROOT or immutable validation report changed')
    old = json.loads(native.read_text())
    if events == 10:
        require(old['status'] == 'PASS_NATIVE_BACKGROUND_RECORD_READBACK' and old['processed'] == old['read'] == 10 and
                old['invalid'] == old['skipped'] == 0, 'original prefix10 was not validated')
    else:
        require(old['status'] == 'FAILED_NATIVE_BACKGROUND_RECORD_READBACK' and old['ROOT_entries'] == 100 and
                old['events_assessed'] == old['read'] == 14 and old['processed'] == 13 and old['invalid'] == 1 and
                old['events_not_assessed'] == 86 and old['diagnostic'] == 'unphysical summed Cartesian four-vector',
                'prefix100 failure is not the diagnosed bounded signed native jet')
    expected_names = {'detector_card.tcl', 'input.hepmc3', 'input_event_index.dat', 'background_truth_index.dat'}
    require(set(reused['artifacts_sha256']) == expected_names, 'missing/excess original detector artifact bindings')
    before = {manifest: REUSE_MANIFEST_SHA, root: REUSE_ROOT_SHA[events], native: REUSE_NATIVE_SHA[events]}
    current = {'detector_card.tcl': runtime_card, 'input.hepmc3': inputs['hepmc_path'],
               'input_event_index.dat': inputs['input_index_path'], 'background_truth_index.dat': inputs['truth_index_path']}
    for name, digest in reused['artifacts_sha256'].items():
        original_file = original / name
        require(sha_file(original_file) == digest == sha_file(current[name]),
                'old detector artifact differs from exact full-shower prefix/card: ' + name)
        before[original_file] = digest
    return root, before


def execute_delphes(output, shower, config, analyzer, seed, run_command, process, events=1000, reused_detector=None):
    output = Path(output)
    require(process in SEEDS and seed == SEEDS[process], 'unreviewed detector process/seed')
    require(type(events) is int and events in (10, 100, 1000), 'unreviewed detector stage count')
    require(not output.exists(), 'Delphes output exists; no silent retry')
    require(shower['validated_events'] == 1000 and shower['status'] == 'PASS_READER_ASCII_RECORDS',
            'actual full1000 ReaderAscii validation required before all Delphes subsets')
    require(shower.get('source_events', shower.get('source_total_events')) == 1000,
            'original source denominator1000 required')
    require(sha_file(CARD) == CARD_SHA, 'historical detector card changed')
    require(sha_file(analyzer['analyzer_path']) == analyzer['analyzer_sha256'], 'native analyzer changed')
    output.mkdir(parents=True)
    inputs = prepare_delphes_input(output, shower, events)
    input_hashes = {key: sha_file(path) for key, path in inputs.items()}
    raw = CARD.read_bytes()
    marker = b'set RandomSeed 610301'
    require(raw.count(marker) == 1, 'historical seed marker changed')
    runtime_card = output / 'detector_card.tcl'
    runtime_card.write_bytes(raw.replace(marker, f'set RandomSeed {seed}'.encode(), 1))
    preserved = {}
    if reused_detector is None:
        run_command([config['delphes_binary'], str(runtime_card), 'detector.root', inputs['hepmc_path']],
                    output, f'delphes_{process}_{events}')
    else:
        root, preserved = _check_reused_detector(reused_detector, shower, inputs, runtime_card, output, process, events)
        with root.open('rb') as original, (output / 'detector.root').open('xb') as copy:
            shutil.copyfileobj(original, copy)
        require(sha_file(output / 'detector.root') == REUSE_ROOT_SHA[events], 'reused ROOT copy changed bytes')
    for key, path in inputs.items():
        require(sha_file(path) == input_hashes[key], 'Delphes input bytes changed: ' + key)
    command = [analyzer['analyzer_path'], '--input', str(output / 'detector.root'),
               '--input-index', inputs['input_index_path'], '--truth-index', inputs['truth_index_path'],
               '--card', str(runtime_card), '--summary', str(output / 'native_validation.json'),
               '--events-jsonl', str(output / 'reco_events.jsonl'), '--cutflow', str(output / 'cutflow.csv'),
               '--events', str(events), '--source-events', '1000', '--process', process]
    run_command(command, output, f'independent_native_root_{process}_{events}')
    require(all(sha_file(path) == digest for path, digest in preserved.items()),
            'original detector artifacts changed during read-only revalidation')
    report = json.loads((output / 'native_validation.json').read_text())
    require(report['status'] == 'PASS_NATIVE_BACKGROUND_RECORD_READBACK' and
            report['ROOT_entries'] == report['processed'] == events and report['invalid'] == report['skipped'] == 0,
            'native ROOT validation failed')
    require(report['root_sha256'] == sha_file(output / 'detector.root') and
            report['input_index_sha256'] == sha_file(inputs['input_index_path']) == input_hashes['input_index_path'] and
            report['truth_index_sha256'] == sha_file(inputs['truth_index_path']) == input_hashes['truth_index_path'] and
            report['card_sha256'] == sha_file(runtime_card), 'native report inspected different inputs')
    report.update({'root_path': str(output / 'detector.root'), 'cutflow_path': str(output / 'cutflow.csv'),
                   'reco_events_path': str(output / 'reco_events.jsonl'), 'delphes_seed': seed,
                   'source_full_shower_sha256': shower['hepmc_path_sha256'],
                   'subset_origin': 'FIRST_N_EXACT_RECORDS_OF_VALIDATED_FULL1000_SHOWER',
                   'inputs': inputs,
                   'derived_files_sha256': {name: sha_file(output / name) for name in ('reco_events.jsonl', 'cutflow.csv')}})
    if reused_detector is not None:
        report['detector_reuse'] = {'status': 'PASS_READ_ONLY_EXISTING_DETECTOR_REVALIDATION',
                                  'original_ROOT_sha256': REUSE_ROOT_SHA[events],
                                  'original_source_manifest_sha256': REUSE_MANIFEST_SHA,
                                  'original_native_report_sha256': REUSE_NATIVE_SHA[events],
                                  'Delphes_invocations_in_this_stage': 0,
                                  'new_MC_events': 0, 'independent_source_statistics_added': 0}
    save_json(output / 'delphes_execution.json', report)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Compile/read native build identity only; zero Delphes events')
    parser.add_argument('--build-only', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(REPO not in output.parents and output != REPO, 'build output must be outside Git')
    config = json.loads((REPO / '.local/delphes_installation.json').read_text())
    print(json.dumps(build_root_analyzer(output, config), indent=2))


if __name__ == '__main__':
    main()

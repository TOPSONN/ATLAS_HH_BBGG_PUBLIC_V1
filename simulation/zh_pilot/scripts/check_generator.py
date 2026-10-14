#!/usr/bin/env python3
"""Check frozen ZH cards with installed MG5; construct diagrams, never export/run."""
from __future__ import annotations

import argparse
import ast
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
CONTRACT = REPO / 'simulation/zh_pilot/config/generator_contract.json'
COMMIT = '3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7'
MODEL = 'import model sm-no_b_mass'
PROTON = 'define p = g u c d s b u~ c~ d~ s~ b~'
PROCESSES = {'ZH_STABLE': 'generate p p > z h QCD=0 QED=2',
             'ZH_ZBB_STABLE_H': 'generate p p > z h QCD=0 QED=2, z > b b~'}
REVIEWED_CARD_SHA256 = {
    'process_stable':'f124bd3050aa44466019ad0110836af5c9a113d5dadd9de39d715ff52b43826a',
    'process_zbb':'411bcfdc0320d9f969b53ef4a723e98ccb26710800687ea0049cc09e32ebc2ad',
    'run':'cbb6072adc7a708fd0b9d2a216cd421aa715244b367da27d9aaa8de668218e73',
    'param':'17ad8b7b95f1918b30771c3403c0e2961fa018ab3db97b10f7dc02ec992074d6',
}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def parse_run(text):
    values = {}
    for line in text.splitlines():
        line = line.split('#', 1)[0].split('!', 1)[0].strip()
        if not line or '=' not in line:
            continue
        value, key = (part.strip() for part in line.rsplit('=', 1))
        key = key.lower()
        if key in values:
            raise ValueError('Duplicate run-card key: ' + key)
        if key == 'custom_fcts' and not value:
            value = []  # RunCardLO standard serialization for an empty string list.
        elif value.lower() in ('true', '.true.', 'false', '.false.'):
            value = value.lower() in ('true', '.true.')
        else:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                try:
                    value = float(value.lower().replace('d', 'e'))
                except ValueError:
                    pass
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Nonfinite run-card value')
        values[key] = value
    return values


def parse_param(text):
    values = {}
    block = None
    for line in text.splitlines():
        words = line.split('#', 1)[0].split()
        if not words:
            continue
        if words[0].lower() == 'block':
            block = words[1].lower()
            continue
        if words[0].lower() == 'decay':
            key = ('decay', int(words[1]))
            block = None
            value = Decimal(words[2].replace('D', 'E').replace('d', 'e'))
        elif block and len(words) == 2:
            key = (block, int(words[0]))
            value = Decimal(words[1].replace('D', 'E').replace('d', 'e'))
        else:
            raise ValueError('Unexpected param-card line or decay branching table')
        if key in values or not value.is_finite():
            raise ValueError('Duplicate/nonfinite parameter')
        values[key] = value
    return values


def validate_bundle(contract=None, repo=REPO):
    """Portable integrity/physics guard. Returned contract has no execution authority."""
    if contract is None:
        contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    if contract.get('schema_version') != 1 or contract.get('preferred_profile') != 'ZH_ZBB_STABLE_H':
        raise ValueError('Unknown generator contract/preferred route')
    identity = contract['source_identity']
    if (identity['source_commit'], identity['source_tag'], identity['mg5_version'], identity['source_url']) != (COMMIT, 'v3.5.16', '3.5.16','https://github.com/mg5amcnlo/mg5amcnlo.git'):
        raise ValueError('Unreviewed MG5 source')
    policy = contract['pilot_policy']
    if policy['physical_events_authorized'] is not False or (policy['events'], policy['energy_gev'], policy['jobs']) != (100, 13000, 1):
        raise ValueError('Physical production or unsupported pilot policy')
    cards = {}
    for item in contract['cards']:
        path = (Path(repo) / item['path']).resolve()
        card_root = (Path(repo) / 'simulation/zh_pilot/cards').resolve()
        if card_root not in path.parents or item['id'] in cards:
            raise ValueError('Duplicate card or card path outside reviewed directory')
        if item['sha256'] != REVIEWED_CARD_SHA256.get(item['id']) or file_sha256(path) != item['sha256']:
            raise ValueError('Card SHA256 mismatch: ' + item['id'])
        cards[item['id']] = path
    if set(cards) != {'process_stable', 'process_zbb', 'run', 'param'}:
        raise ValueError('Incomplete frozen card bundle')
    if set(contract['profiles']) != set(PROCESSES):
        raise ValueError('Unreviewed generator profile')
    for profile, command in PROCESSES.items():
        info = contract['profiles'][profile]
        path = cards[info['process_card_id']]
        lines = [line.strip() for line in path.read_text(encoding='utf-8').splitlines()
                 if line.strip() and not line.lstrip().startswith('#')]
        if lines != [MODEL, PROTON, command]:
            raise ValueError('Only exact reviewed import/define/generate commands are allowed')
        if info['actual_production_amplitude_orders'] != {'QCD': 0, 'QED': 2}:
            raise ValueError('Unreviewed production coupling order')
        expected_decays = [] if profile == 'ZH_STABLE' else ['Z_to_b_bbar']
        expected_missing = ['Z_to_b_bbar', 'H_to_gamma_gamma'] if profile == 'ZH_STABLE' else ['H_to_gamma_gamma']
        if info['source_included_decay_ids'] != expected_decays or info['missing_decay_ids'] != expected_missing:
            raise ValueError('Decay inclusion/BR scope changed')
        expected_order = None if profile == 'ZH_STABLE' else {'QCD': 0, 'QED': 1}
        if info['actual_decay_amplitude_orders'] != expected_order:
            raise ValueError('Unreviewed decay coupling order')
        if profile == 'ZH_ZBB_STABLE_H' and info['factorized_chain_amplitude_orders'] != {'QCD':0,'QED':3}:
            raise ValueError('Production and decay order scopes must remain distinct')
    physics = contract['physics']
    if physics['model'] != 'sm-no_b_mass' or sorted(physics['proton_pdgs']) != [-5,-4,-3,-2,-1,1,2,3,4,5,21]:
        raise ValueError('Model/proton flavour scheme changed')
    if physics['sqrt_s_gev'] != 13000 or physics['loop_induced_gg_ZH_included'] is not False or physics['H_gamma_gamma_tree_decay_included'] is not False:
        raise ValueError('Unreviewed collision energy or production scope')
    params = parse_param(cards['param'].read_text(encoding='utf-8'))
    expected_params = {('mass',23):'91.188',('mass',25):'125',('mass',4):'0',('mass',5):'0',
                       ('decay',23):'2.441404',('decay',25):'0.00638233934',
                       ('sminputs',1):'132.507',('sminputs',2):'0.0000116639',('sminputs',3):'0.129783'}
    if any(params.get(k) != Decimal(v) for k,v in expected_params.items()):
        raise ValueError('Mass/width/EW/PDF alpha_s input changed')
    if any(params.get(('yukawa',pdg), Decimal(0)) != 0 for pdg in (4,5)):
        raise ValueError('Restricted b/c Yukawa must remain zero')
    if physics['masses_gev'] != {'Z':91.188,'H':125.0,'b':0.0,'c':0.0} or physics['widths_gev'] != {'Z':2.441404,'H':.00638233934}:
        raise ValueError('Physics manifest differs from exact mass/width cards')
    if (physics['electroweak_inputs']['aEWM1'],physics['electroweak_inputs']['Gf']) != (132.507,1.16639e-5):
        raise ValueError('Physics EW scheme differs from cards')
    run = parse_run(cards['run'].read_text(encoding='utf-8'))
    for key, value in physics['run_values'].items():
        if run.get(key) != value:
            raise ValueError('Frozen run value disagrees with contract: ' + key)
    scales = physics['scales']
    required = {'nevents':100,'iseed':620101,'ebeam1':6500.,'ebeam2':6500.,'lpp1':1,'lpp2':1,
                'pdlabel':'cteq6l1','lhaid':10042,'fixed_ren_scale':True,'fixed_fac_scale':True,
                'scale':216.188,'dsqrt_q2fact1':216.188,'dsqrt_q2fact2':216.188,'cut_decays':False,
                'bwcutoff':15.,'ickkw':0,'event_norm':'average','use_syst':False,'maxjetflavor':5,
                'ptheavy':0.,'dsqrt_shat':0.,'mmbb':0.,'mmbbmax':-1.,'ptb':0.,'etab':-1.,'drbb':0.,'custom_fcts':[]}
    if any(run.get(k) != v for k,v in required.items()):
        raise ValueError('Unreviewed PDF/scale/cut/event-normalization setting')
    if scales['prescription'] != 'FIXED_MZ_PLUS_MH' or any(scales[k] != 216.188 for k in ('muR_gev','muF1_gev','muF2_gev')):
        raise ValueError('ZH scale must equal reviewed MZ+MH')
    pdf = physics['pdf']
    if (pdf['pdlabel'],pdf['built_in_pdf_id'],pdf['active_flavours'],pdf['pdf_order'],pdf['lhaid_is_used']) != ('cteq6l1',10042,5,1,False):
        raise ValueError('Unreviewed PDF scheme')
    return contract


def installation(config_path):
    spec = importlib.util.spec_from_file_location('phase6f_mg5_installation', REPO/'simulation/mg5/scripts/installation.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    config = json.loads(config_path.read_text(encoding='utf-8'))
    mg5, identity = verifier.verify(config)
    return config, mg5, identity, verifier


def model_cache_snapshot(mg5):
    return {str(path.relative_to(mg5)):file_sha256(path) for path in (mg5/'models').rglob('*')
            if path.is_file() and path.suffix in ('.pkl','.pickle','.pyc')}


def amplitude_records(amplitude, model, scope='production'):
    if 'amplitudes' in amplitude:
        return [record for child in amplitude.get('amplitudes') for record in amplitude_records(child,model,scope)] + [
            record for child in amplitude.get('decay_chains') for record in amplitude_records(child,model,'Z_decay')]
    process = amplitude.get('process')
    diagrams = amplitude.get('diagrams')
    orders = set()
    for diagram in diagrams:
        diagram.calculate_orders(model)
        orders.add(tuple(sorted((key,val) for key,val in diagram.get('orders').items() if key != 'WEIGHTED')))
    return [{'scope':scope,'initial_pdgs':[leg.get('id') for leg in process.get('legs') if not leg.get('state')],
             'final_pdgs':[leg.get('id') for leg in process.get('legs') if leg.get('state')],
             'diagram_count':len(diagrams),'actual_amplitude_orders':[dict(order) for order in sorted(orders)]}]


def worker(request_path, result_path):
    request = json.loads(request_path.read_text(encoding='utf-8'))
    contract = validate_bundle()
    config, mg5, identity, verifier = installation(Path(request['installation']))
    if str(mg5) != request['mg5_path']:
        raise ValueError('Worker installation identity differs')
    sys.path.insert(0,str(mg5))
    import madgraph
    madgraph.ReadWrite = False  # before importing UFO loader: forbid new model pickle writes.
    from madgraph.interface.madgraph_interface import MadGraphCmd
    from madgraph.various.banner import RunCardLO
    from models.check_param_card import ParamCard
    from models.model_reader import ModelReader
    cards={item['id']:REPO/item['path'] for item in contract['cards']}
    run=RunCardLO(str(cards['run']))
    param=ParamCard(str(cards['param']))
    if any(run[key]!=val for key,val in contract['physics']['run_values'].items()):
        raise ValueError('Official RunCardLO differs from frozen contract')
    results=[]
    for profile, generate in PROCESSES.items():
        cmd=MadGraphCmd()
        cmd.options['auto_convert_model']=False
        cmd.options['auto_update']=0
        for line in (MODEL,PROTON,generate):
            cmd.exec_cmd(line,errorhandling=False,printcmd=False,precmd=True)
        if sorted(cmd._multiparticles['p']) != sorted(contract['physics']['proton_pdgs']):
            raise ValueError('Actual MG5 proton expansion changed')
        records=[record for amp in cmd._curr_amps for record in amplitude_records(amp,cmd._curr_model)]
        if not records or any(record['diagram_count']<=0 for record in records):
            raise ValueError('No nonzero retained tree diagrams')
        for record in records:
            order={'QCD':0,'QED':2} if record['scope']=='production' else {'QCD':0,'QED':1}
            if any(actual!=order for actual in record['actual_amplitude_orders']):
                raise ValueError('Actual production/decay order changed')
            if record['scope']=='production' and (sorted(record['final_pdgs']) != [23,25] or
                sorted(record['initial_pdgs']) not in [[-i,i] for i in range(1,6)]):
                raise ValueError('Retained Born component is not five-flavour qqbar->ZH')
            if record['scope']=='Z_decay' and (record['initial_pdgs']!=[23] or sorted(record['final_pdgs'])!=[-5,5]):
                raise ValueError('Retained Z decay differs from b bbar')
        if (profile=='ZH_ZBB_STABLE_H') != any(record['scope']=='Z_decay' for record in records):
            raise ValueError('Missing/unexpected decay chain')
        reader=ModelReader(cmd._curr_model)
        reader.set_parameters_and_couplings(param_card=param)
        values=reader['parameter_dict']
        actual={name:float(complex(values[name]).real) for name in
                ('mdl_MZ','mdl_MH','mdl_WZ','mdl_WH','aEWM1','mdl_Gf','aS','mdl_MW','mdl_sw2')}
        expected={'mdl_MZ':91.188,'mdl_MH':125.,'mdl_WZ':2.441404,'mdl_WH':.00638233934,
                  'aEWM1':132.507,'mdl_Gf':1.16639e-5,'aS':.129783}
        if any(actual[k] != v for k,v in expected.items()):
            raise ValueError('Actual restricted model parameters differ from cards')
        mass_symbols={str(pdg):cmd._curr_model.get_particle(pdg)['mass'] for pdg in (4,5)}
        if any(symbol!='ZERO' for symbol in mass_symbols.values()) or values['ZERO']!=0:
            raise ValueError('Actual restricted c/b particles are not massless')
        zero_yukawa_names={'mdl_ymc','mdl_ymb','mdl_yc','mdl_yb'}
        parameter_names={p.name for parameters in cmd._curr_model['parameters'].values() for p in parameters}
        if parameter_names & zero_yukawa_names:
            raise ValueError('Restricted c/b Yukawa parameters unexpectedly retained')
        if cmd._export_dir is not None or cmd._done_export:
            raise RuntimeError('Unexpected process export state')
        results.append({'profile':profile,'status':'PASS_PARSE_AND_TREE_DIAGRAM_CONSTRUCTION','commands':[MODEL,PROTON,generate],
                        'amplitude_records':records,'production_record_count':sum(r['scope']=='production' for r in records),
                        'decay_record_count':sum(r['scope']=='Z_decay' for r in records),'actual_parameters':actual,
                        'actual_restricted_mass_symbols':mass_symbols,'restricted_c_b_yukawa_parameters_removed':True,
                        'cross_section_pb':'UNKNOWN_NOT_INTEGRATED','events_generated':0})
    verifier.verify(config)
    result_path.write_text(json.dumps({'checks':results,'official_run_card_readback':dict(run),'official_pdf_id':run.get_pdf_id(run['pdlabel'])},indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation',type=Path,default=Path(os.environ.get('MG5_LOCAL_CONFIG',REPO/'.local/mg5_installation.json')))
    parser.add_argument('--output',type=Path,help='New local directory; no sample production')
    parser.add_argument('--worker-request',type=Path,help=argparse.SUPPRESS)
    parser.add_argument('--worker-result',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker_request:
        worker(args.worker_request,args.worker_result)
        return 0
    if not args.output:
        parser.error('--output NEW_LOCAL_DIRECTORY is required')
    initial_paths=[Path(__file__).resolve(),CONTRACT,args.installation.resolve(),REPO/'simulation/mg5/scripts/installation.py']
    protected={path:file_sha256(path) for path in initial_paths}
    contract=validate_bundle()
    protected.update({REPO/item['path']:item['sha256'] for item in contract['cards']})
    config,mg5,identity,verifier=installation(args.installation)
    cache_before=model_cache_snapshot(mg5)
    output=args.output.expanduser().resolve()
    scratch=REPO/'.local/phase6f'
    if output.exists() or output==REPO or (REPO in output.parents and scratch not in output.parents):
        raise ValueError('Use a new outside-repository output or ignored .local/phase6f scratch')
    if output==mg5 or mg5 in output.parents or output in mg5.parents:
        raise ValueError('Output must not be inside/above MG5 installation')
    output.mkdir(parents=True)
    request=output/'parser_request.local.json'
    result=output/'parser_result.json'
    request.write_text(json.dumps({'mg5_path':str(mg5),'installation':str(args.installation.resolve())},indent=2)+'\n',encoding='utf-8')
    try:
        with (output/'mg5_parse.log').open('wb') as stream:
            completed=subprocess.run([str(Path(config['toolchain_prefix'])/'bin/python'),'-B',str(Path(__file__).resolve()),
                                      '--worker-request',str(request),'--worker-result',str(result)],cwd=output,stdout=stream,stderr=subprocess.STDOUT,timeout=300)
        if completed.returncode:
            raise RuntimeError('MG5 worker failed; inspect retained local mg5_parse.log')
        verifier.verify(config)
        if model_cache_snapshot(mg5)!=cache_before:
            raise RuntimeError('Installed model cache changed during parsing')
        if any(file_sha256(path)!=digest for path,digest in protected.items()):
            raise RuntimeError('Source/configuration/card changed during parsing')
        parsed=json.loads(result.read_text(encoding='utf-8'))
        source_files=['models/sm/restrict_no_b_mass.dat','models/sm/parameters.py','models/model_reader.py','models/write_param_card.py',
                      'madgraph/various/banner.py','madgraph/interface/common_run_interface.py','Template/LO/Cards/run_card.dat',
                      'Template/LO/lib/Pdfdata/cteq6l1.tbl','Template/LO/Source/PDF/pdfwrap.f','Template/LO/SubProcesses/setcuts.f','Template/LO/SubProcesses/myamp.f']
        receipt={'schema_version':1,'status':'PASS_PARSE_AND_CARD_READBACK_ONLY','source_identity':contract['source_identity'],
                 'installation_retained_source_identity_verified_before_after':True,'installed_model_cache_unchanged':True,
                 'automatic_model_conversion_disabled':True,'model_cache_write_disabled':True,'python_bytecode_write_disabled':True,
                 'generator_contract_sha256':protected[CONTRACT],'checker_source_sha256':protected[Path(__file__).resolve()],
                 'cards':contract['cards'],'source_files_sha256':{name:file_sha256(mg5/name) for name in source_files},
                 'checks':parsed['checks'],'official_pdf_id':parsed['official_pdf_id'],
                 'official_run_card_readback':parsed['official_run_card_readback'],'events_generated':0,
                 'process_export_integration_launch_width_calculation_executed':False,
                 'physical_pilot':'NOT_AUTHORIZED','physical_cross_section_BR_decay_shower_closure':'NOT_EVALUATED'}
        (output/'generator_checks.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':receipt['status'],'profiles':len(receipt['checks']),'events_generated':0},indent=2))
        return 0
    except Exception as error:
        (output/'partial_status.json').write_text(json.dumps({'status':'PARTIAL_FAILED','events_generated':0,'error':type(error).__name__,'reason':str(error)},indent=2)+'\n',encoding='utf-8')
        raise


if __name__=='__main__':
    raise SystemExit(main())

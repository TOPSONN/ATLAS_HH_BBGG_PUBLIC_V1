"""Strict readiness contracts and portable method-level validation."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[1]
BASE = '64353adfbbd3a28b13ddbdf761896c0a3fc6e680'
MG5_COMMIT = '3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7'
DELPHES_CARD_SHA = 'cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47'

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()

def read_json(path):
    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, 'DUPLICATE_JSON_KEY')
            obj[key] = value
        return obj
    def invalid(_):
        raise ValueError('NONFINITE_JSON')
    result = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                        parse_constant=invalid)
    def finite(value):
        if isinstance(value, float):
            require(math.isfinite(value), 'NONFINITE_JSON')
        elif isinstance(value, dict):
            for item in value.values(): finite(item)
        elif isinstance(value, list):
            for item in value: finite(item)
    finite(result)
    return result

def write_json(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')

def validate_model(contract):
    require(contract['process_id'] == 'S01_GGF_HH_SM', 'WRONG_PROCESS')
    require(contract['model'] == 'loop_sm' and contract['mg5_commit'] == MG5_COMMIT,
            'WRONG_MODEL')
    require(contract['accuracy'] == 'LO_LOOP_INDUCED_FULL_MT_MB', 'HEFT_MISLABEL_OR_WRONG_ORDER')
    require(contract['finite_top_mass'] is True, 'MISSING_FULL_MT')
    require(set(contract['topologies']) == {'box', 'triangle', 'R2'}, 'MISSING_TOPOLOGY')
    require(contract['effective_contacts'] is False, 'UNEXPECTED_HEFT_CONTACT')
    require(contract['kappa_lambda'] == contract['kappa_top'] == 1, 'WRONG_SM_COUPLING')
    require(contract['sqrt_s_gev'] == 13000 and contract['MH_gev'] == 125 and
            contract['MT_gev'] == 173 and contract['MB_gev'] == 4.7, 'WRONG_BASELINE')
    require(contract['source_cross_section_pb'] == 'NOT_EVALUATED_UNTIL_REAL_INTEGRATION',
            'UNAUTHORIZED_CROSS_SECTION')
    require(contract['physical_events_authorized'] is False, 'UNAPPROVED_GENERATION')
    return 'PASS_MODEL_CONTRACT_ONLY'

def validate_couplings(contract):
    require(contract['lambda_mapping']['type'] == 'diagnostic_trilinear_coupling_rescale',
            'WRONG_KAPPA_LAMBDA_MAPPING')
    require(contract['lambda_mapping']['changes_Higgs_mass'] is False,
            'MASS_CHANGE_IS_NOT_KAPPA_LAMBDA')
    require(contract['top_mapping']['source'] == 'YUKAWA[6]', 'WRONG_YUKAWA_MAPPING')
    require(contract['top_mapping']['independent_of_propagator_MT'] is True,
            'YUKAWA_MASS_CONFLATION')
    require(contract['lambda_mapping']['production_scan_supported'] is False,
            'UNREVIEWED_BSM_PRODUCTION')
    return 'PASS_SM_AND_DIAGNOSTIC_MAPPING_ONLY'

def verify_bundle(repo=REPO):
    repo = Path(repo)
    manifest = read_json(repo/'metadata/phase7a_model_manifest.json')
    for entry in manifest['project_bindings']:
        p = repo/entry['path']
        require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(repo.resolve()),
                'UNSAFE_SOURCE_BINDING')
        require(sha(p) == entry['sha256'], 'STALE_SOURCE_HASH: '+entry['path'])
    validate_model(read_json(repo/'simulation/hh_signal/config/signal_model_contract.json'))
    validate_couplings(read_json(repo/'simulation/hh_signal/config/coupling_contract.json'))
    decay=read_json(repo/'simulation/hh_signal/cards/proposed_decay_contract.json')
    require(decay==read_json(repo/'metadata/phase7a_decay_contract.json'), 'DECAY_CONTRACT_COPY_MISMATCH')
    require(decay['original_higgs_pdgs']==[25,25] and decay['distinct_original_lineages']==2 and
            decay['final_modes']==['b bbar','gamma gamma'] and decay['kinematic_ranking_used'] is False and
            decay['global_PDG25_force_for_mixed_modes'] is False and
            decay['identical_H_factor']==2,'UNSAFE_DOUBLE_HIGGS_DECAY_CONTRACT')
    require(decay['ADOPTED_STUDY_BR']['H_bb'] is None and
            decay['ADOPTED_STUDY_BR']['H_gammagamma'] is None,'UNREVIEWED_BR_ADOPTION')
    weights=read_json(repo/'simulation/hh_signal/config/weight_contract.json')
    require(weights['normalization_status']=='NOT_EVALUATED' and
            weights['original_generated_event_count'] is None and weights['event_contribution_pb'] is None and
            weights['source_cross_section_pb'] is None and weights['identical_H_factor']==2 and
            weights['already_applied_decay_factors']==[], 'FABRICATED_OR_DOUBLE_COUNTED_WEIGHT_LEDGER')
    require(sha(repo/'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl') == DELPHES_CARD_SHA,
            'HISTORICAL_DELPHES_CARD_CHANGED')
    return manifest

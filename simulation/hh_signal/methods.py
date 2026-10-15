"""Algebra/lineage methods, never synthetic signal-event producers."""
from __future__ import annotations
import hashlib
import math
from .contracts import require

def assign_higgs_decays(lineages, seed, source_index):
    """Unbiased bit chooses gamma-gamma from two original, distinct PDG25 roots.

    Input contains lineage identifiers only. Does not make daughters or mutate
    momenta. A future native decay bridge must implement and validate the plan.
    The assignment seed is independent of the generator/shower seeds.
    """
    require(type(seed) is int and 1 <= seed <= 900000000, 'INVALID_ASSIGNMENT_SEED')
    require(type(source_index) is int and source_index >= 0, 'INVALID_SOURCE_INDEX')
    require(len(lineages) == 2, 'EXACTLY_TWO_ORIGINAL_HIGGS_REQUIRED')
    require(all(r['pdg_id'] == 25 and r['is_original'] is True for r in lineages),
            'ORIGINAL_PDG25_REQUIRED')
    ids = sorted(r['lineage_id'] for r in lineages)
    require(all(type(i) is int and i > 0 for i in ids) and len(set(ids)) == 2,
            'DUPLICATE_OR_INVALID_HIGGS_LINEAGE')
    token = f'S01-assignment-v1:{seed}:{source_index}'.encode('ascii')
    bit = hashlib.sha256(token).digest()[0] & 1
    return {'bb_lineage': ids[1-bit], 'gammagamma_lineage': ids[bit],
            'assignment_probability': 0.5, 'scope': 'METHOD_ONLY_NO_DAUGHTERS_CREATED'}

def validate_assignment(plan, lineages):
    ids = {r['lineage_id'] for r in lineages}
    require(len(ids) == 2 and {plan['bb_lineage'], plan['gammagamma_lineage']} == ids,
            'MISSING_DUPLICATE_OR_SAME_DECAY')
    require(plan['assignment_probability'] == 0.5, 'BIASED_ASSIGNMENT')

def missing_decay_factor(br_bb, br_gg, source_decay_ids, applied_factors,
                         identical_h_factor=2):
    require(all(type(x) in (int,float) and math.isfinite(x) and 0 < x < 1
                for x in (br_bb,br_gg)), 'INVALID_BR')
    require(source_decay_ids == [], 'SOURCE_DECAYS_REQUIRE_SEPARATE_REVIEW')
    require(applied_factors == [], 'BR_ALREADY_APPLIED')
    require(identical_h_factor == 2, 'MISSING_OR_WRONG_IDENTICAL_H_FACTOR')
    return 2*br_bb*br_gg

def contribution_pb(*, raw_weight, original_count, weight_semantics,
                    raw_unit, selected_count=None, cross_section_pb=None,
                    br_factor=1.0, sigma_over_n_already_applied=False):
    """Exactly-once algebra for two explicitly certified source conventions.

    No LHE convention is inferred solely from IDWTUP. Before real closure the
    production ledger stays UNKNOWN and must not call this as physical truth.
    """
    require(type(original_count) is int and original_count > 0, 'WRONG_ORIGINAL_N')
    require(selected_count is None, 'SELECTED_N_FORBIDDEN')
    require(not sigma_over_n_already_applied, 'DOUBLE_SIGMA_OVER_N')
    require(raw_unit == 'pb' if weight_semantics == 'cross_section_weight_pb'
            else raw_unit == 'dimensionless', 'WRONG_UNITS')
    require(math.isfinite(raw_weight) and math.isfinite(br_factor) and 0 < br_factor <= 1,
            'INVALID_WEIGHT')
    if weight_semantics == 'cross_section_weight_pb':
        require(cross_section_pb is None, 'DOUBLE_SIGMA_NORMALIZATION')
        return raw_weight*br_factor/original_count
    require(weight_semantics == 'unit_positive_sigma_pb' and raw_weight == 1 and
            cross_section_pb is not None and cross_section_pb > 0,
            'UNCERTIFIED_WEIGHT_CONVENTION')
    return cross_section_pb*br_factor/original_count

def cartesian_mass(vectors):
    require(vectors, 'EMPTY_PAIR')
    e, x, y, z = [sum(v[i] for v in vectors) for i in range(4)]
    value = e*e-x*x-y*y-z*z
    tolerance = 1e-12*max(e*e,x*x+y*y+z*z,1)
    require(value >= -tolerance, 'SPACELIKE_PAIR')
    return math.sqrt(max(value,0))

def pair_mass_or_none(vectors):
    return cartesian_mass(vectors[:2]) if len(vectors) >= 2 else None

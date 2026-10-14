"""Exactly-once BR algebra; mathematical checks never validate physical BR inputs."""
from decimal import Decimal, InvalidOperation, localcontext


def _probability(value):
    if isinstance(value, (bool, float)):
        raise ValueError('Supply a finite exact-decimal BR input, not bool/binary float')
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError('BR is UNKNOWN or not a finite decimal') from None
    if not result.is_finite() or not Decimal(0) <= result <= Decimal(1):
        raise ValueError('BR must be finite in [0,1]')
    return result


def _bool_flag(value, name):
    if type(value) is not bool:
        raise ValueError(name + ' requires a literal Boolean; UNKNOWN is not verified')
    return value


def _decay_ledger(values):
    if not isinstance(values, (list, tuple)):
        raise ValueError('Decay ledger must be an explicit list/tuple of IDs')
    if any(not isinstance(name, str) or not name.strip() or name != name.strip() for name in values):
        raise ValueError('Decay ledger contains empty/invalid ID')
    if len(set(values)) != len(values):
        raise ValueError('Duplicate ID in decay ledger')
    return set(values)


def normalization_factor(factors, *, source_included_decays=(), already_applied_decays=(),
                         external_forced_decay=False, external_weight_closure_verified=False):
    """Return missing BR product; reject repeated/source-included/unknown factors.

    Inputs are explicit missing decay channels, each with a decimal BR and a
    positive multiplicity. An exclusive matrix-element cross section must list
    its already-included channels rather than applying their BR again. The
    Boolean closure gate denotes an external evidence requirement; setting it
    in a unit test does not provide a physical external-LHE validation receipt.
    """
    _bool_flag(external_forced_decay, 'external_forced_decay')
    _bool_flag(external_weight_closure_verified, 'external_weight_closure_verified')
    if external_forced_decay and not external_weight_closure_verified:
        raise ValueError('External forced decay requires actual LHE/Info/converter normalization closure')
    included = _decay_ledger(source_included_decays)
    applied = _decay_ledger(already_applied_decays)
    if not isinstance(factors, (list, tuple)):
        raise ValueError('Factors require an explicit list/tuple')
    if included & applied:
        raise ValueError('BR already double-counted in source and applied-weight ledgers')
    seen = set()
    with localcontext() as context:
        context.prec = 50
        result = Decimal(1)
        for factor in factors:
            if not isinstance(factor, dict) or set(factor) != {'decay_id', 'branching_ratio', 'multiplicity'}:
                raise ValueError('Each factor requires exactly decay_id/branching_ratio/multiplicity')
            name = factor['decay_id']
            multiplicity = factor['multiplicity']
            if not isinstance(name, str) or not name.strip() or name != name.strip():
                raise ValueError('Explicit nonempty decay_id is required')
            if name in seen or name in included or name in applied:
                raise ValueError('Repeated or already-included decay BR: ' + name)
            if isinstance(multiplicity, bool) or not isinstance(multiplicity, int) or multiplicity <= 0:
                raise ValueError('Decay multiplicity must be a positive integer')
            seen.add(name)
            result *= _probability(factor['branching_ratio']) ** multiplicity
        return +result


def semileptonic_w_factor(leptonic_br, hadronic_br, *, channel_scope,
                         source_includes_charge_union=False):
    """NWA W-mode algebra for one charge assignment or an explicit two-charge union."""
    if channel_scope not in ('ONE_CHARGE_ASSIGNMENT', 'BOTH_CHARGE_ASSIGNMENTS'):
        raise ValueError('State one charge or both-charge union explicitly')
    _bool_flag(source_includes_charge_union, 'source_includes_charge_union')
    if source_includes_charge_union:
        raise ValueError('Charge union is already in source cross section; do not multiply it again')
    with localcontext() as context:
        context.prec = 50
        leptonic = _probability(leptonic_br)
        hadronic = _probability(hadronic_br)
        if leptonic + hadronic > Decimal(1):
            raise ValueError('Exclusive leptonic/hadronic W branching fractions overlap or sum above one')
        return (Decimal(2) if channel_scope == 'BOTH_CHARGE_ASSIGNMENTS' else Decimal(1)) * leptonic * hadronic

#!/usr/bin/env python3
"""Evidence-limited heavy-flavour diagnostics; never a matching/merging recipe."""
from __future__ import annotations
from collections import Counter, defaultdict
import math
from phase9_graph import ancestors, delta_r, historical, require

OVERLAP_STATUS = 'OVERLAP_UNRESOLVED_REQUIRES_MATCHED_GENERATION_OR_VALIDATED_EXCLUSIVE_DEFINITION'


def flavour_priority(particles):
    return historical.associated_label(particles)


def births(pygraph):
    """ME incoming/outgoing records and distinct shower heavy-line births.

    ME records are not particle-production births: incoming HF can come from
    the PDF and an outgoing same-flavour hard quark remains an ME final record.
    Shifted shower copies are suppressed only outside the ME record classes.
    """
    result = {}
    for pid, row in pygraph.items():
        flavour = abs(row['pdg_id'])
        if flavour not in (4, 5):
            continue
        mothers = [pygraph[m] for m in row['mothers'] if m]
        status = abs(row['status'])
        if status == 23:
            origin = 'ME_HEAVY_FLAVOUR_RECORD'
        elif status == 21:
            origin = 'ME_INITIAL_HEAVY_FLAVOUR_RECORD'
        elif any(m['pdg_id'] == row['pdg_id'] for m in mothers):
            continue
        elif 41 <= status <= 59:
            origin = 'SHOWER_HEAVY_FLAVOUR_BIRTH'
        elif any(m.get('is_hadron', False) for m in mothers):
            origin = 'HADRON_DECAY_HEAVY_QUARK'
        else:
            origin = 'OTHER_OR_UNCLASSIFIED_HEAVY_QUARK_BIRTH'
        gluons = []
        if 41 <= status <= 59:
            for mother in mothers:
                if mother['pdg_id'] != 21 or not (41 <= abs(mother['status']) <= 59):
                    continue
                direct = [pygraph[d] for d in mother['daughters']]
                if any(x['pdg_id'] == flavour and 41 <= abs(x['status']) <= 59 for x in direct) and any(x['pdg_id'] == -flavour and 41 <= abs(x['status']) <= 59 for x in direct):
                    gluons.append(mother['id'])
        result[pid] = dict(id=pid, flavour=flavour, signed_pdg_id=row['pdg_id'], original_status=row['status'],
                           origin=origin, direct_gluon_splitting_mothers=sorted(gluons))
    return result


def classify_heavy_flavour(graph, reco_event, lhe_event, pygraph):
    """Return one original event's classifications; geometric labels diagnostic."""
    jets = reco_event['eligible_jets']
    hard = [p for p in lhe_event['particles'] if p['status'] == 1 and abs(p['pdg_id']) in (1, 2, 3, 4, 5, 21)]
    hard_counts = Counter(abs(p['pdg_id']) for p in hard)
    hard_class = 'ME_BOTTOM' if hard_counts[5] else 'ME_CHARM' if hard_counts[4] else 'ME_LIGHT_OR_GLUON'
    origins = births(pygraph)
    shower_births = [p for p in origins.values() if p['origin'] == 'SHOWER_HEAVY_FLAVOUR_BIRTH']
    splitting_mothers = sorted({m for p in shower_births for m in p['direct_gluon_splitting_mothers']})
    terminal = [row for row in pygraph.values() if row.get('terminal_b_hadron') or row.get('terminal_c_hadron')]
    assigned, ambiguous = defaultdict(list), []
    for row in terminal:
        distances = sorted((delta_r(j, row), j['index']) for j in jets)
        if not distances or distances[0][0] >= .4:
            continue
        if len(distances) > 1 and abs(distances[0][0] - distances[1][0]) <= 1e-12:
            ambiguous.append(row['id'])
        else:
            assigned[distances[0][1]].append(row)
    shower = [p for p in pygraph.values() if abs(p['pdg_id']) in (1, 2, 3, 4, 5, 21) and 41 <= abs(p['status']) <= 59]
    annotated = []
    for jet in jets:
        native = int(jet.get('flavour', jet.get('flavor')))
        native_jet = dict(jet, flavor=native)
        native_check = historical.native_flavour(native_jet, graph['particles'])
        hard_matches = [p for p in hard if delta_r(jet, p) <= .4]
        shower_matches = [p for p in shower if delta_r(jet, p) <= .4]
        hadrons = assigned[jet['index']]
        hadron_label = 5 if any(p['terminal_b_hadron'] for p in hadrons) else 4 if any(p['terminal_c_hadron'] for p in hadrons) else 0
        # All ancestry endpoints are retained. A string with multiple ancestors
        # is never assigned to one privileged perturbative endpoint.
        relevant_ids = {p['id'] for p in shower_matches if abs(p['pdg_id']) in (4, 5)}
        relevant_ids |= {p['id'] for p in hadrons}
        birth_ids = set()
        for pid in relevant_ids:
            birth_ids |= (set(ancestors(pygraph, pid)) | {pid}) & set(origins)
        evidence = [origins[p] for p in sorted(birth_ids)]
        annotated.append(dict(index=jet['index'], pt=jet['pt'], eta=jet['eta'], phi=jet['phi'],
                              native_flavour=native, tagged=bool(jet['tagged']),
                              hard_cone_flavour=flavour_priority(hard_matches),
                              shower_record_cone_flavour=flavour_priority(shower_matches),
                              heavy_hadron_flavour=hadron_label,
                              terminal_b_hadrons=sum(bool(p['terminal_b_hadron']) for p in hadrons),
                              terminal_c_hadrons=sum(bool(p['terminal_c_hadron']) for p in hadrons),
                              hadron_ids=[p['id'] for p in hadrons],
                              origin_evidence=evidence,
                              sole_hadron_endpoint='UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED',
                              native_attainable_labels=native_check['attainable_labels'],
                              native_reproduction_pass=native_check['matches_native']))
    counts = Counter(p['origin'] for p in origins.values())
    return dict(hard_process_flavour=hard_class, hard_outgoing_flavour_counts=dict(hard_counts),
                heavy_quark_birth_counts=dict(counts),
                shower_bottom_births=sum(p['flavour'] == 5 for p in shower_births),
                shower_charm_births=sum(p['flavour'] == 4 for p in shower_births),
                direct_gluon_splitting_count=len(splitting_mothers),
                direct_gluon_splitting_mothers=splitting_mothers,
                terminal_b_hadrons=sum(bool(p['terminal_b_hadron']) for p in terminal),
                terminal_c_hadrons=sum(bool(p['terminal_c_hadron']) for p in terminal),
                ambiguous_hadron_assignment_ids=ambiguous,
                unclassified_quark_births=counts['OTHER_OR_UNCLASSIFIED_HEAVY_QUARK_BIRTH'],
                jets=annotated,
                native_reproduction_pass=all(j['native_reproduction_pass'] for j in annotated),
                no_physical_background_sum=True, overlap_status=OVERLAP_STATUS)


def event_flags(result):
    jets = result['jets']
    flags = {
        'ME_BOTTOM': result['hard_process_flavour'] == 'ME_BOTTOM',
        'ME_CHARM': result['hard_process_flavour'] == 'ME_CHARM',
        'ME_LIGHT_OR_GLUON': result['hard_process_flavour'] == 'ME_LIGHT_OR_GLUON',
        'HAS_ME_INITIAL_HEAVY_FLAVOUR_RECORD': result['heavy_quark_birth_counts'].get('ME_INITIAL_HEAVY_FLAVOUR_RECORD', 0) > 0,
        'HAS_SHOWER_BOTTOM_BIRTH': result['shower_bottom_births'] > 0,
        'HAS_SHOWER_CHARM_BIRTH': result['shower_charm_births'] > 0,
        'HAS_DIRECT_G_TO_HEAVY_PAIR': result['direct_gluon_splitting_count'] > 0,
        'HAS_TERMINAL_B_HADRON': result['terminal_b_hadrons'] > 0,
        'HAS_TERMINAL_C_HADRON': result['terminal_c_hadrons'] > 0,
        'HAS_UNCLASSIFIED_QUARK_BIRTH': result['unclassified_quark_births'] > 0,
        'HAS_AMBIGUOUS_HADRON_ASSIGNMENT': bool(result['ambiguous_hadron_assignment_ids']),
        'HAS_NATIVE_BOTTOM_JET': any(j['native_flavour'] == 5 for j in jets),
        'HAS_NATIVE_CHARM_JET': any(j['native_flavour'] == 4 for j in jets),
        'HAS_HEAVY_HADRON_ELIGIBLE_JET': any(j['heavy_hadron_flavour'] in (4, 5) for j in jets),
        'HARD_LIGHT_NATIVE_HEAVY': result['hard_process_flavour'] == 'ME_LIGHT_OR_GLUON' and any(j['native_flavour'] in (4, 5) for j in jets),
        'HAS_NATIVE_FLAVOUR_BOUNDARY_AMBIGUITY': any(len(j['native_attainable_labels']) > 1 for j in jets),
        'HAS_NATIVE_FLAVOUR_MISMATCH': not result['native_reproduction_pass'],
    }
    for tag in range(3):
        n = sum(j['tagged'] for j in jets)
        flags[f'NATIVE_TAGS_{tag if tag < 2 else "GE2"}'] = (n == tag if tag < 2 else n >= 2)
    return flags


def summarize_indicator(values, weights):
    """Original-N source-event units; no independent-jet error assumption."""
    n = len(values)
    require(n == len(weights) and n > 1, 'invalid complete-cohort indicator')
    xs = [w if flag else 0. for flag, w in zip(values, weights)]
    require(all(math.isfinite(x) for x in xs), 'nonfinite weighted indicator')
    total = math.fsum(xs)
    mean = total / n
    variance = n / (n - 1) * math.fsum((x - mean)**2 for x in xs)
    sumw2 = math.fsum(x*x for x in xs)
    k = sum(bool(x) for x in values)
    # Wilson 95% is descriptive; exact rare/zero intervals supplied separately.
    z = 1.959963984540054
    denom = 1 + z*z/n
    centre = (k/n + z*z/(2*n))/denom
    half = z*math.sqrt((k/n)*(1-k/n)/n + z*z/(4*n*n))/denom
    return dict(events=k, original_N=n, event_fraction=k/n, fraction_wilson95_low=centre-half,
                fraction_wilson95_high=centre+half, sumw_pb=total, sumw2_pb2=sumw2,
                source_sampling_variance_pb2=variance, source_sampling_se_pb=math.sqrt(variance),
                ESS=total*total/sumw2 if sumw2 else None,
                uncertainty_scope='FIXED_ORIGINAL_N_EVENT_UNITS_NOT_INDEPENDENT_JETS',
                interval_scope='UNWEIGHTED_PROPOSAL_EVENT_PROBABILITY_NOT_PHYSICAL_XSEC')
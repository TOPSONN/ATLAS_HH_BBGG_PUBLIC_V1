"""Versioned architecture review; never amend or authorize the old contract."""
from .device_policy import need, bounded, result, same

ORIGINAL = {'S4': {'CPU_seconds': 4, 'wall_seconds': 13,
                   'RAM_bytes': 536870912, 'swap_bytes': 0,
                   'disk_bytes': 16777216, 'jobs': 1, 'workers': 1},
            'BUILD': {'CPU_seconds': 14400, 'wall_seconds': 14400,
                      'RAM_bytes': 2147483648, 'swap_bytes': 0,
                      'disk_bytes': 5368709120, 'jobs': 1, 'workers': 1}}
ROLES = {'worker', 'controller', 'collector', 'manager_journal',
         'launcher', 'host_backing'}
TRUST = {'worker': 'untrusted', 'controller': 'trusted',
         'collector': 'trusted', 'manager_journal': 'trusted',
         'launcher': 'trusted', 'host_backing': 'trusted'}
WRITES = {'worker': {'work_tmpfs', 'private_tmpfs'},
          'controller': {'work_tmpfs', 'collector_protocol_pipe'},
          'collector': {'protected_evidence_slots'},
          'manager_journal': {'reviewed_control_state_and_logs'},
          'launcher': {'reviewed_launcher_state_and_logs'},
          'host_backing': {'reviewed_fixed_backing_and_metadata'}}
MANDATORY_GAPS = {'exact_device', 'host_allocated_blocks_and_metadata',
                  'cumulative_CPU_stop', 'whole_lifecycle_wall',
                  'RAM_semantics', 'collector_survival',
                  'output_routes', 'postmortem_retention',
                  'user_session_health'}


def review_architecture(proposal):
    digest = bounded(proposal)
    need(type(proposal) is dict and proposal.get('schema') == 'ADMIN_BOUNDARY_PROPOSAL_V1',
         'ARCHITECTURE_SCHEMA')
    need(proposal.get('architecture') in ('A', 'B') and
         same(proposal.get('unchanged_original_contract'), ORIGINAL), 'ORIGINAL_CAPS_CHANGED')
    need(proposal.get('status') == 'PROPOSED_NOT_ACCEPTED' and
         proposal.get('execution_authorized') is False, 'NO_SELF_AUTHORIZATION')
    rows = proposal.get('roles')
    need(type(rows) is list and len(rows) == len(ROLES) and
         {r.get('role') for r in rows if type(r) is dict} == ROLES, 'COMPLETE_ROLES_REQUIRED')
    outside = []
    original_owners = set()
    for row in rows:
        need(set(row) == {'role', 'trust', 'accounting_domain', 'writes',
                         'resource_owner', 'death_boundary', 'failure_behavior'},
             'ROLE_FIELDS')
        need(row['trust'] == TRUST[row['role']] and
             row['accounting_domain'] in ('original_aggregate', 'external_trusted'),
             'TRUST_OR_ACCOUNTING_DOMAIN')
        need(type(row['writes']) is list and row['writes'] and
             all(type(x) is str and x for x in row['writes']) and
             all(type(row[k]) is str and row[k] for k in
                 ('resource_owner', 'death_boundary', 'failure_behavior')), 'ROLE_BOUNDARY_MISSING')
        need(set(row['writes']) <= WRITES[row['role']], 'UNTRUSTED_OR_UNREVIEWED_WRITE_ROUTE')
        if row['role'] == 'collector':
            need(row['death_boundary'] ==
                 'survives_worker_and_controller_not_outer_budget_or_host_loss',
                 'COLLECTOR_SURVIVAL_DOMAIN_REQUIRED')
        if row['accounting_domain'] == 'external_trusted':
            outside.append(row['role'])
        else:
            original_owners.add(row['resource_owner'])
    need(len(original_owners) == 1, 'ONE_SHARED_AGGREGATE_NOT_PER_ROLE_CAPS')
    expected_outside = set() if proposal['architecture'] == 'A' else {
        'manager_journal', 'launcher', 'host_backing'}
    need(set(outside) == expected_outside, 'ARCHITECTURE_LABEL_ACCOUNTING_MISMATCH')
    amendment = proposal.get('amendment')
    if outside:
        need(type(amendment) is dict and set(amendment) ==
             {'version', 'status', 'excluded_roles', 'weaker_than_original', 'user_accepted'} and
             amendment['version'] == 'BOUNDARY_AMENDMENT_CANDIDATE_V2' and
             amendment['status'] == 'PROPOSED_NOT_ACCEPTED' and
             set(amendment['excluded_roles']) == set(outside) and
             amendment['weaker_than_original'] is True and
             amendment['user_accepted'] is False, 'EXTERNAL_COST_REQUIRES_EXPLICIT_UNACCEPTED_AMENDMENT')
    else:
        need(amendment is None, 'UNEXPECTED_AMENDMENT')
    need(type(proposal.get('remaining_gaps')) is list and
         set(proposal['remaining_gaps']) >= MANDATORY_GAPS,
         'RESOURCE_GAPS_HIDDEN')
    need(proposal.get('zero_overshoot_claim') is False and
         proposal.get('failure_store_preallocated') == 'REQUIRES_DEPLOYMENT_AND_PROOF',
         'UNPROVEN_ENFORCEMENT_OR_DURABILITY_CLAIM')
    return result('ARCHITECTURE_SOURCE_REVIEWABLE_NOT_APPROVED', digest,
                  original_contract_satisfied=False,
                  external_roles=sorted(outside),
                  provisioning_authorized=False,
                  S4_EXECUTED=False, BUILD_ONLY_AUTHORIZED=False)

import copy
import unittest
from .. import boundary_contract as c
from ..device_policy import PolicyError


def proposal(architecture='A'):
    rows=[dict(role=role,trust=c.TRUST[role],accounting_domain='original_aggregate',
        writes=sorted(c.WRITES[role]),resource_owner='bounded_parent',
        death_boundary=('survives_worker_and_controller_not_outer_budget_or_host_loss'
                        if role=='collector' else 'worker_subtree' if role=='worker'
                        else 'trusted_survival_domain'),
        failure_behavior='LAST_CHECKPOINT_AND_UNKNOWN_IF_CAPTURE_LOST') for role in sorted(c.ROLES)]
    if architecture=='B':
        for r in rows:
            if r['role'] in ('manager_journal','launcher','host_backing'):
                r['accounting_domain']='external_trusted'
    outside=[r['role'] for r in rows if r['accounting_domain']=='external_trusted']
    amendment=dict(version='BOUNDARY_AMENDMENT_CANDIDATE_V2',status='PROPOSED_NOT_ACCEPTED',
        excluded_roles=outside,weaker_than_original=True,user_accepted=False) if outside else None
    return dict(schema='ADMIN_BOUNDARY_PROPOSAL_V1',architecture=architecture,
        unchanged_original_contract=copy.deepcopy(c.ORIGINAL),status='PROPOSED_NOT_ACCEPTED',
        execution_authorized=False,roles=rows,amendment=amendment,
        remaining_gaps=sorted(c.MANDATORY_GAPS),zero_overshoot_claim=False,
        failure_store_preallocated='REQUIRES_DEPLOYMENT_AND_PROOF')


class BoundaryContractTests(unittest.TestCase):
    def test_A_reviewable_but_not_original_contract_pass(self):
        r=c.review_architecture(proposal())
        self.assertFalse(r['original_contract_satisfied']);self.assertFalse(r['provisioning_authorized'])

    def test_B_requires_explicit_weaker_unaccepted_amendment(self):
        p=proposal('B');r=c.review_architecture(p)
        self.assertEqual(len(r['external_roles']),3)
        p['amendment']=None
        with self.assertRaisesRegex(PolicyError,'AMENDMENT'):c.review_architecture(p)

    def test_every_original_CPU_wall_RAM_swap_disk_job_worker_cap_immutable(self):
        for stage in c.ORIGINAL:
            for key in c.ORIGINAL[stage]:
                p=proposal();p['unchanged_original_contract'][stage][key]+=1
                with self.assertRaisesRegex(PolicyError,'CAPS_CHANGED'):c.review_architecture(p)

    def test_boolean_aliases_do_not_rewrite_original_integer_caps(self):
        p=proposal();p['unchanged_original_contract']['S4']['jobs']=True
        with self.assertRaisesRegex(PolicyError,'CAPS_CHANGED'):c.review_architecture(p)

    def test_missing_roles_hidden_costs_and_self_acceptance_refused(self):
        p=proposal();p['roles'].pop()
        with self.assertRaisesRegex(PolicyError,'ROLES'):c.review_architecture(p)
        p=proposal('B');p['amendment']['user_accepted']=True
        with self.assertRaisesRegex(PolicyError,'AMENDMENT'):c.review_architecture(p)
        p=proposal();p['execution_authorized']=True
        with self.assertRaisesRegex(PolicyError,'AUTHORIZATION'):c.review_architecture(p)

    def test_resource_gaps_and_zero_overshoot_cannot_be_hidden(self):
        p=proposal();p['remaining_gaps'].remove('cumulative_CPU_stop')
        with self.assertRaisesRegex(PolicyError,'GAPS_HIDDEN'):c.review_architecture(p)
        p=proposal();p['zero_overshoot_claim']=True
        with self.assertRaisesRegex(PolicyError,'UNPROVEN'):c.review_architecture(p)

    def test_worker_cannot_write_protected_evidence_and_collector_survives_it(self):
        p=proposal();next(r for r in p['roles'] if r['role']=='worker')['writes']=['protected_evidence_slots']
        with self.assertRaisesRegex(PolicyError,'WRITE_ROUTE'):c.review_architecture(p)
        p=proposal();next(r for r in p['roles'] if r['role']=='collector')['death_boundary']='worker_subtree'
        with self.assertRaisesRegex(PolicyError,'SURVIVAL'):c.review_architecture(p)

    def test_CPU_and_disk_are_one_pool_not_full_caps_per_role(self):
        p=proposal();next(r for r in p['roles'] if r['role']=='controller')['resource_owner']='another_pool'
        with self.assertRaisesRegex(PolicyError,'ONE_SHARED'):c.review_architecture(p)

    def test_architecture_letters_cannot_relabel_weaker_external_costs(self):
        for original,changed in (('A','B'),('B','A')):
            p=proposal(original);p['architecture']=changed
            with self.assertRaisesRegex(PolicyError,'LABEL_ACCOUNTING'):c.review_architecture(p)

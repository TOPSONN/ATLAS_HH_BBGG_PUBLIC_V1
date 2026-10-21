"""PR36 delta publication: inspect every intermediate commit and changed index."""
from __future__ import annotations
import json
from unittest.mock import patch
from . import publication as original
from . import autonomous_publication as prior
from . import recovery_publication as privacy
BASE_VALIDATE = original.validate_payload
BASE = '61b32c0aa86456cf43051aa18a6ea692f9e22c7f'
PREFIX = 'simulation/hh_signal/final_closure/resource_closure/'
REPORTS = 'reports/phase7i_admin_architecture_p1_closure/'
ADMIN = 'reports/phase7i_s4_persistent_capacity_closure/ADMIN_ACTIONS_ZH_TW.md'
EXACT = {PREFIX+n for n in (
    'device_policy.py','instance_binding.py','evidence_slots.py','boundary_contract.py',
    'admin_review.py','admin_publication.py','offline_regression.py',
    'tests/test_admin_security.py','tests/test_evidence_protocol.py',
    'tests/test_boundary_contract.py','tests/test_admin_review_cli.py',
    'tests/test_admin_publication.py','config/admin_architecture_A.json',
    'config/admin_architecture_B.json')}
EXACT |= original.WORKFLOWS | {ADMIN}


def allowed(name):
    return name in EXACT or (name.startswith(REPORTS) and
        prior.allowed(name.replace(REPORTS, prior.REPORTS, 1)))


def validate(name, raw, mode='100644'):
    row = BASE_VALIDATE(name, raw, mode)
    if name.startswith(REPORTS) or name == ADMIN:
        privacy.reject_private_mount_capture(raw.decode('utf-8'))
        if name.lower().endswith('.json'):
            privacy.reject_private_mount_capture(json.loads(raw))
    return row


def audit(repo=original.REPO):
    with patch.object(original, 'allowed_path', allowed), \
         patch.object(original, 'validate_payload', validate):
        return original.audit(repo, base=BASE)


def main():
    try:
        result = audit()
    except (ValueError, OSError) as error:
        print(json.dumps({'status':'FAIL_ADMIN_PUBLICATION','reason':str(error)[:1024]}))
        return 2
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())


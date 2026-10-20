"""PR34 stacked source audit; all intermediate commits and the index count."""
from __future__ import annotations
import json
from unittest.mock import patch
from . import publication as original
from . import recovery_publication as prior

BASE = '5431e0b2efba20863cddaccc37679af32e13a7f4'
PREFIX = 'simulation/hh_signal/final_closure/resource_closure/'
REPORTS = 'reports/phase7i_autonomous_controller_recovery/'
EXACT = {PREFIX + n for n in (
    'full_controller.py', 'controller_io.py', 'controller_guard.py', 'mount_policy.py',
    'storage_transport.py', 'workflow_evidence.py', 'offline_regression.py',
    'autonomous_publication.py', 'config/mount_policy.json',
    'config/storage_contract.json', 'tests/test_full_controller.py',
    'tests/test_controller_io.py', 'tests/test_controller_guard.py', 'tests/test_mount_policy.py',
    'tests/test_storage_transport.py', 'tests/test_workflow_evidence.py',
    'tests/test_autonomous_publication.py')}
EXACT |= original.WORKFLOWS
BASE_VALIDATE = original.validate_payload


def allowed(name):
    return name in EXACT or (name.startswith(REPORTS) and
           prior.BASE_ALLOWED(name.replace(REPORTS, 'reports/phase7i_resource_closure/', 1)))


def validate(name, raw, mode='100644'):
    row = BASE_VALIDATE(name, raw, mode)
    if name.startswith(REPORTS):
        prior.reject_private_mount_capture(raw.decode('utf-8'))
        if name.lower().endswith('.json'):
            prior.reject_private_mount_capture(json.loads(raw))
    return row


def audit(repo=original.REPO):
    with patch.object(original, 'allowed_path', allowed), \
         patch.object(original, 'validate_payload', validate):
        return original.audit(repo, base=BASE)


def main():
    try:
        result = audit()
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'FAIL_AUTONOMOUS_PUBLICATION', 'reason': str(error)[:1024]}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
